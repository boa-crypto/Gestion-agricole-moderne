"""Règles métier du module CRM & Partenaires.

Ce module ne contient aucun composant visuel : uniquement les calculs et les
garde-fous persistants du socle CRM (codes automatiques, montants de lignes,
soldes, retards, statuts dérivés, archivage plutôt que suppression, contrôle
des doublons, validation des identifiants fiscaux, scoring et audit).

Toutes les fonctions qui touchent la base reçoivent une `Session` SQLAlchemy
synchrone : elles sont donc utilisables aussi bien depuis un `rx.session()`
que depuis un script de démonstration ou un test unitaire.
"""

from __future__ import annotations

import datetime
import logging
import re

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    CrmAuditLog,
    CrmDocument,
    CrmEvent,
    CrmEventKind,
    CrmInvoice,
    CrmInvoiceItem,
    CrmPartner,
    CrmPayable,
    CrmPayment,
    CrmPurchase,
    CrmPurchaseItem,
    CrmReceivable,
    CrmSale,
    CrmSaleItem,
    CrmScore,
    CrmScoreGrade,
    CrmScoreKind,
    InvoiceKind,
    InvoiceStatus,
    PartnerKind,
    PartnerStatus,
    PaymentDirection,
    PurchaseStatus,
    SaleStatus,
    SettlementStatus,
)

__all__ = [
    "AGING_BUCKETS",
    "CLIENT_KINDS",
    "SUPPLIER_KINDS",
    "aging_bucket",
    "apply_partner_score",
    "archive_partner",
    "can_delete_partner",
    "compute_line_amounts",
    "compute_partner_balances",
    "compute_score",
    "derive_invoice_status",
    "derive_purchase_status",
    "derive_sale_status",
    "derive_settlement_status",
    "find_duplicate_partner",
    "grade_for_score",
    "log_crm_action",
    "next_code",
    "next_partner_code",
    "normalize_identifier",
    "overdue_days",
    "record_event",
    "refresh_invoice_amounts",
    "refresh_purchase_totals",
    "refresh_sale_totals",
    "refresh_settlements",
    "validate_fiscal_identifiers",
]

# Familles de tiers considérées comme clientes / fournisseuses.
CLIENT_KINDS: tuple[PartnerKind, ...] = (
    PartnerKind.CLIENT,
    PartnerKind.MIXTE,
    PartnerKind.GROSSISTE,
    PartnerKind.DISTRIBUTEUR,
    PartnerKind.REVENDEUR,
    PartnerKind.COOPERATIVE,
)
SUPPLIER_KINDS: tuple[PartnerKind, ...] = (
    PartnerKind.FOURNISSEUR,
    PartnerKind.MIXTE,
    PartnerKind.TRANSPORTEUR,
    PartnerKind.PRESTATAIRE,
    PartnerKind.COOPERATIVE,
)

AGING_BUCKETS: tuple[str, ...] = ("0-30", "31-60", "61-90", "90+")

_PARTNER_PREFIXES: dict[PartnerKind, str] = {
    PartnerKind.CLIENT: "CLI",
    PartnerKind.GROSSISTE: "CLI",
    PartnerKind.DISTRIBUTEUR: "CLI",
    PartnerKind.REVENDEUR: "CLI",
    PartnerKind.FOURNISSEUR: "FRN",
    PartnerKind.TRANSPORTEUR: "FRN",
    PartnerKind.PRESTATAIRE: "FRN",
    PartnerKind.MIXTE: "PRT",
    PartnerKind.COOPERATIVE: "PRT",
    PartnerKind.AUTRE: "PRT",
}


# ---------------------------------------------------------------------------
# Codes automatiques
# ---------------------------------------------------------------------------


def _extract_sequence(code: str, prefix: str) -> int:
    """Retourne le compteur numérique final d'un code `PREFIX-...-0042`."""
    if not code or not code.startswith(prefix):
        return 0
    match = re.search(r"(\d+)$", code)
    return int(match.group(1)) if match else 0


def next_code(
    session: Session,
    model: type,
    prefix: str,
    *,
    year: int | None = None,
    width: int = 4,
) -> str:
    """Génère le prochain code séquentiel unique d'une entité CRM.

    Le format est `PREFIX-0001` ou `PREFIX-2026-0001` lorsqu'une année est
    fournie. La numérotation reprend toujours au dernier compteur observé afin
    de rester stable même après archivage de lignes.
    """
    full_prefix = f"{prefix}-{year}-" if year is not None else f"{prefix}-"
    try:
        codes = (
            session.execute(
                select(model.code).where(model.code.like(f"{full_prefix}%"))
            )
            .scalars()
            .all()
        )
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
        codes = []
    highest = max(
        (_extract_sequence(code, full_prefix) for code in codes),
        default=0,
    )
    return f"{full_prefix}{highest + 1:0{width}d}"


def next_partner_code(session: Session, kind: PartnerKind) -> str:
    """Code partenaire automatique dérivé de la nature du tiers."""
    prefix = _PARTNER_PREFIXES.get(kind, "PRT")
    return next_code(session, CrmPartner, prefix)


# ---------------------------------------------------------------------------
# Montants de lignes et totaux de transactions
# ---------------------------------------------------------------------------


def compute_line_amounts(
    quantity: float,
    unit_price: float,
    discount_percent: float = 0.0,
    vat_rate: float = 0.0,
) -> tuple[float, float, float]:
    """Calcule (HT, TVA, TTC) d'une ligne remisée, arrondis au centime."""
    gross = float(quantity or 0) * float(unit_price or 0)
    discount = gross * max(float(discount_percent or 0), 0) / 100
    amount_ht = round(gross - discount, 2)
    vat_amount = round(amount_ht * max(float(vat_rate or 0), 0) / 100, 2)
    return amount_ht, vat_amount, round(amount_ht + vat_amount, 2)


def _refresh_items(items: list, global_discount: float) -> tuple[float, float]:
    """Recalcule chaque ligne puis retourne les totaux (HT, TVA)."""
    total_ht = 0.0
    total_vat = 0.0
    for item in items:
        amount_ht, vat_amount, amount_ttc = compute_line_amounts(
            float(item.quantity or 0),
            float(item.unit_price or 0),
            float(item.discount_percent or 0),
            float(item.vat_rate or 0),
        )
        item.amount_ht = amount_ht
        item.vat_amount = vat_amount
        item.amount_ttc = amount_ttc
        total_ht += amount_ht
        total_vat += vat_amount
    rate = max(float(global_discount or 0), 0) / 100
    if rate:
        total_ht *= 1 - rate
        total_vat *= 1 - rate
    return round(total_ht, 2), round(total_vat, 2)


def refresh_sale_totals(session: Session, sale: CrmSale) -> CrmSale:
    """Recalcule les totaux d'une vente depuis ses lignes puis son statut."""
    items = list(
        session.execute(
            select(CrmSaleItem).where(CrmSaleItem.sale_id == sale.id)
        )
        .scalars()
        .all()
    )
    total_ht, total_vat = _refresh_items(items, float(sale.discount_percent))
    sale.amount_ht = total_ht
    sale.vat_amount = total_vat
    sale.amount_ttc = round(
        total_ht + total_vat + float(sale.transport_cost or 0), 2
    )
    sale.paid_amount = _paid_for(
        session, PaymentDirection.ENCAISSEMENT, sale_id=sale.id
    )
    sale.status = derive_sale_status(sale)
    return sale


def refresh_purchase_totals(
    session: Session, purchase: CrmPurchase
) -> CrmPurchase:
    """Recalcule les totaux d'un achat depuis ses lignes puis son statut."""
    items = list(
        session.execute(
            select(CrmPurchaseItem).where(
                CrmPurchaseItem.purchase_id == purchase.id
            )
        )
        .scalars()
        .all()
    )
    total_ht, total_vat = _refresh_items(
        items, float(purchase.discount_percent)
    )
    purchase.amount_ht = total_ht
    purchase.vat_amount = total_vat
    purchase.amount_ttc = round(
        total_ht + total_vat + float(purchase.transport_cost or 0), 2
    )
    purchase.paid_amount = _paid_for(
        session, PaymentDirection.DECAISSEMENT, purchase_id=purchase.id
    )
    purchase.status = derive_purchase_status(purchase)
    return purchase


def _paid_for(
    session: Session,
    direction: PaymentDirection,
    *,
    sale_id: int | None = None,
    purchase_id: int | None = None,
    invoice_id: int | None = None,
) -> float:
    """Somme des paiements non archivés rattachés à un objet donné."""
    query = select(func.coalesce(func.sum(CrmPayment.amount), 0)).where(
        CrmPayment.direction == direction,
        CrmPayment.is_archived.is_(False),
    )
    if sale_id is not None:
        query = query.where(CrmPayment.sale_id == sale_id)
    if purchase_id is not None:
        query = query.where(CrmPayment.purchase_id == purchase_id)
    if invoice_id is not None:
        query = query.where(CrmPayment.invoice_id == invoice_id)
    return round(float(session.execute(query).scalar() or 0), 2)


# ---------------------------------------------------------------------------
# Retards, soldes et statuts dérivés
# ---------------------------------------------------------------------------


def overdue_days(
    due_date: datetime.date | None,
    *,
    remaining: float = 0.0,
    today: datetime.date | None = None,
) -> int:
    """Nombre de jours de retard d'un règlement encore dû (0 si à jour)."""
    if due_date is None or float(remaining or 0) <= 0.005:
        return 0
    reference = today or datetime.date.today()
    return max((reference - due_date).days, 0)


def aging_bucket(days: int) -> str:
    """Tranche d'ancienneté normalisée d'un retard en jours."""
    if days <= 30:
        return AGING_BUCKETS[0]
    if days <= 60:
        return AGING_BUCKETS[1]
    if days <= 90:
        return AGING_BUCKETS[2]
    return AGING_BUCKETS[3]


def derive_settlement_status(
    amount_due: float,
    amount_paid: float,
    due_date: datetime.date | None,
    *,
    today: datetime.date | None = None,
    current: SettlementStatus | None = None,
) -> SettlementStatus:
    """Statut d'une créance ou d'une dette à partir des montants et du délai."""
    if current in (SettlementStatus.LITIGE, SettlementStatus.IRRECOUVRABLE):
        return current
    remaining = round(float(amount_due or 0) - float(amount_paid or 0), 2)
    if remaining <= 0.005:
        return SettlementStatus.REGLEE
    if overdue_days(due_date, remaining=remaining, today=today) > 0:
        return SettlementStatus.EN_RETARD
    if float(amount_paid or 0) > 0.005:
        return SettlementStatus.PARTIELLE
    return SettlementStatus.OUVERTE


def derive_invoice_status(
    invoice: CrmInvoice, *, today: datetime.date | None = None
) -> InvoiceStatus:
    """Statut d'une facture (annulation et brouillon toujours préservés)."""
    if invoice.status in (InvoiceStatus.ANNULEE, InvoiceStatus.BROUILLON):
        return invoice.status
    remaining = round(
        float(invoice.amount_ttc or 0) - float(invoice.paid_amount or 0), 2
    )
    if remaining <= 0.005:
        return InvoiceStatus.PAYEE
    if overdue_days(invoice.due_date, remaining=remaining, today=today) > 0:
        return InvoiceStatus.EN_RETARD
    if float(invoice.paid_amount or 0) > 0.005:
        return InvoiceStatus.PARTIELLEMENT_PAYEE
    return InvoiceStatus.EMISE


def derive_sale_status(sale: CrmSale) -> SaleStatus:
    """Statut d'une vente déduit des montants réglés et de la livraison."""
    if sale.status in (SaleStatus.ANNULEE, SaleStatus.BROUILLON):
        return sale.status
    total = float(sale.amount_ttc or 0)
    paid = float(sale.paid_amount or 0)
    if total > 0 and paid >= total - 0.005:
        return SaleStatus.PAYEE
    if paid > 0.005:
        return SaleStatus.PARTIELLEMENT_PAYEE
    if sale.status == SaleStatus.FACTUREE:
        return SaleStatus.FACTUREE
    if sale.delivery_date is not None:
        return SaleStatus.LIVREE
    return sale.status


def derive_purchase_status(purchase: CrmPurchase) -> PurchaseStatus:
    """Statut d'un achat déduit des montants réglés et de la réception."""
    if purchase.status in (PurchaseStatus.ANNULEE, PurchaseStatus.BROUILLON):
        return purchase.status
    total = float(purchase.amount_ttc or 0)
    paid = float(purchase.paid_amount or 0)
    if total > 0 and paid >= total - 0.005:
        return PurchaseStatus.PAYEE
    if paid > 0.005:
        return PurchaseStatus.PARTIELLEMENT_PAYEE
    if purchase.status == PurchaseStatus.FACTUREE:
        return PurchaseStatus.FACTUREE
    if purchase.received_date is not None:
        return PurchaseStatus.RECEPTIONNEE
    return purchase.status


def refresh_invoice_amounts(
    session: Session,
    invoice: CrmInvoice,
    *,
    today: datetime.date | None = None,
) -> CrmInvoice:
    """Recalcule totaux, encaissements, reste dû, retard et statut."""
    items = list(
        session.execute(
            select(CrmInvoiceItem).where(
                CrmInvoiceItem.invoice_id == invoice.id
            )
        )
        .scalars()
        .all()
    )
    if items:
        total_ht, total_vat = _refresh_items(items, 0)
        invoice.amount_ht = total_ht
        invoice.vat_amount = total_vat
        invoice.amount_ttc = round(total_ht + total_vat, 2)
    direction = (
        PaymentDirection.ENCAISSEMENT
        if invoice.kind in (InvoiceKind.VENTE, InvoiceKind.AVOIR_ACHAT)
        else PaymentDirection.DECAISSEMENT
    )
    invoice.paid_amount = _paid_for(session, direction, invoice_id=invoice.id)
    invoice.remaining_amount = round(
        max(float(invoice.amount_ttc or 0) - float(invoice.paid_amount), 0), 2
    )
    invoice.overdue_days = overdue_days(
        invoice.due_date, remaining=invoice.remaining_amount, today=today
    )
    invoice.status = derive_invoice_status(invoice, today=today)
    return invoice


def refresh_settlements(
    session: Session,
    invoice: CrmInvoice,
    *,
    today: datetime.date | None = None,
) -> CrmReceivable | CrmPayable:
    """Crée ou met à jour la créance/dette adossée à une facture."""
    refresh_invoice_amounts(session, invoice, today=today)
    is_sale = invoice.kind in (InvoiceKind.VENTE, InvoiceKind.AVOIR_VENTE)
    model = CrmReceivable if is_sale else CrmPayable
    row = session.execute(
        select(model).where(model.invoice_id == invoice.id)
    ).scalar_one_or_none()
    if row is None:
        row = model(partner_id=invoice.partner_id, invoice_id=invoice.id)
        if is_sale:
            row.sale_id = invoice.sale_id
        else:
            row.purchase_id = invoice.purchase_id
        session.add(row)
    row.issue_date = invoice.issue_date
    row.due_date = invoice.due_date
    row.amount_due = float(invoice.amount_ttc or 0)
    row.amount_paid = float(invoice.paid_amount or 0)
    row.amount_remaining = float(invoice.remaining_amount or 0)
    row.overdue_days = overdue_days(
        invoice.due_date, remaining=row.amount_remaining, today=today
    )
    row.aging_bucket = aging_bucket(row.overdue_days)
    row.status = derive_settlement_status(
        row.amount_due,
        row.amount_paid,
        row.due_date,
        today=today,
        current=row.status,
    )
    row.is_archived = bool(invoice.is_archived)
    return row


def compute_partner_balances(
    session: Session,
    partner_id: int,
    *,
    today: datetime.date | None = None,
) -> dict[str, float]:
    """Soldes consolidés d'un tiers (CA, achats, créances, dettes, retards)."""
    reference = today or datetime.date.today()

    def _sum(query) -> float:
        # `no_autoflush` : un calcul de solde ne doit jamais déclencher
        # l'écriture d'objets encore incomplets présents dans la session
        # (documents, liens documentaires, lignes en cours de construction).
        with session.no_autoflush:
            return round(float(session.execute(query).scalar() or 0), 2)

    turnover = _sum(
        select(func.coalesce(func.sum(CrmSale.amount_ttc), 0)).where(
            CrmSale.partner_id == partner_id,
            CrmSale.is_archived.is_(False),
            CrmSale.status != SaleStatus.ANNULEE,
        )
    )
    purchases = _sum(
        select(func.coalesce(func.sum(CrmPurchase.amount_ttc), 0)).where(
            CrmPurchase.partner_id == partner_id,
            CrmPurchase.is_archived.is_(False),
            CrmPurchase.status != PurchaseStatus.ANNULEE,
        )
    )
    received = _sum(
        select(func.coalesce(func.sum(CrmPayment.amount), 0)).where(
            CrmPayment.partner_id == partner_id,
            CrmPayment.is_archived.is_(False),
            CrmPayment.direction == PaymentDirection.ENCAISSEMENT,
        )
    )
    paid_out = _sum(
        select(func.coalesce(func.sum(CrmPayment.amount), 0)).where(
            CrmPayment.partner_id == partner_id,
            CrmPayment.is_archived.is_(False),
            CrmPayment.direction == PaymentDirection.DECAISSEMENT,
        )
    )
    receivable = _sum(
        select(
            func.coalesce(func.sum(CrmReceivable.amount_remaining), 0)
        ).where(
            CrmReceivable.partner_id == partner_id,
            CrmReceivable.is_archived.is_(False),
        )
    )
    payable = _sum(
        select(func.coalesce(func.sum(CrmPayable.amount_remaining), 0)).where(
            CrmPayable.partner_id == partner_id,
            CrmPayable.is_archived.is_(False),
        )
    )
    overdue_receivable = _sum(
        select(
            func.coalesce(func.sum(CrmReceivable.amount_remaining), 0)
        ).where(
            CrmReceivable.partner_id == partner_id,
            CrmReceivable.is_archived.is_(False),
            CrmReceivable.due_date.is_not(None),
            CrmReceivable.due_date < reference,
        )
    )
    overdue_payable = _sum(
        select(func.coalesce(func.sum(CrmPayable.amount_remaining), 0)).where(
            CrmPayable.partner_id == partner_id,
            CrmPayable.is_archived.is_(False),
            CrmPayable.due_date.is_not(None),
            CrmPayable.due_date < reference,
        )
    )
    return {
        "turnover": turnover,
        "purchases": purchases,
        "received": received,
        "paid_out": paid_out,
        "receivable": receivable,
        "payable": payable,
        "overdue_receivable": overdue_receivable,
        "overdue_payable": overdue_payable,
        "net_balance": round(receivable - payable, 2),
        "margin": round(turnover - purchases, 2),
    }


# ---------------------------------------------------------------------------
# Archivage, doublons et validation
# ---------------------------------------------------------------------------


def can_delete_partner(session: Session, partner_id: int) -> bool:
    """Un tiers porteur de transactions ne doit jamais être supprimé."""
    for model in (
        CrmSale,
        CrmPurchase,
        CrmInvoice,
        CrmPayment,
        CrmDocument,
    ):
        count = session.execute(
            select(func.count())
            .select_from(model)
            .where(model.partner_id == partner_id)
        ).scalar()
        if int(count or 0) > 0:
            return False
    return True


def archive_partner(
    session: Session,
    partner: CrmPartner,
    *,
    reason: str = "",
    author: str = "Système",
    today: datetime.date | None = None,
) -> CrmPartner:
    """Archive un tiers (jamais de suppression) et journalise l'action."""
    reference = today or datetime.date.today()
    previous = partner.status.value
    partner.is_archived = True
    partner.status = PartnerStatus.ARCHIVE
    partner.archived_on = reference
    partner.archive_reason = reason
    record_event(
        session,
        partner_id=partner.id,
        kind=CrmEventKind.ARCHIVAGE,
        title="Tiers archivé",
        summary=reason or "Archivage sans suppression des données liées.",
        occurred_on=reference,
        author=author,
    )
    log_crm_action(
        session,
        partner_id=partner.id,
        action="archivage",
        entity_type="crm_partner",
        entity_id=partner.id,
        entity_ref=partner.code,
        field_name="status",
        old_value=previous,
        new_value=PartnerStatus.ARCHIVE.value,
        summary=reason,
        actor_label=author,
        is_sensitive=True,
    )
    return partner


def normalize_identifier(value: str) -> str:
    """Normalise un identifiant fiscal (majuscules, sans séparateurs)."""
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def validate_fiscal_identifiers(
    *,
    tax_id: str = "",
    nif: str = "",
    nis: str = "",
    trade_register: str = "",
    email: str = "",
) -> list[str]:
    """Retourne la liste des anomalies détectées (vide si tout est valide)."""
    errors: list[str] = []
    for label, value, minimum in (
        ("Identifiant fiscal", tax_id, 8),
        ("NIF", nif, 10),
        ("NIS", nis, 10),
        ("Registre de commerce", trade_register, 6),
    ):
        cleaned = normalize_identifier(value)
        if cleaned and len(cleaned) < minimum:
            errors.append(f"{label} trop court ({len(cleaned)} caractères).")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}", email):
        errors.append("Adresse e-mail invalide.")
    return errors


def find_duplicate_partner(
    session: Session,
    *,
    legal_name: str = "",
    tax_id: str = "",
    nif: str = "",
    phone: str = "",
    email: str = "",
    exclude_id: int | None = None,
) -> CrmPartner | None:
    """Détecte un tiers existant susceptible d'être un doublon."""
    clauses = []
    if legal_name:
        clauses.append(func.lower(CrmPartner.legal_name) == legal_name.lower())
    for column, value in (
        (CrmPartner.tax_id, tax_id),
        (CrmPartner.nif, nif),
        (CrmPartner.phone, phone),
        (CrmPartner.email, email),
    ):
        if value:
            clauses.append(column == value)
    if not clauses:
        return None
    query = select(CrmPartner).where(or_(*clauses))
    if exclude_id is not None:
        query = query.where(CrmPartner.id != exclude_id)
    return session.execute(query.limit(1)).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def grade_for_score(total: int) -> CrmScoreGrade:
    """Appréciation qualitative associée à un score sur 100."""
    if total >= 85:
        return CrmScoreGrade.EXCELLENT
    if total >= 70:
        return CrmScoreGrade.BON
    if total >= 50:
        return CrmScoreGrade.MOYEN
    if total >= 30:
        return CrmScoreGrade.FRAGILE
    return CrmScoreGrade.RISQUE


def _clamp(value: float, maximum: int) -> int:
    return int(max(0, min(round(value), maximum)))


def compute_score(
    kind: CrmScoreKind,
    *,
    turnover_amount: float = 0.0,
    transaction_count: int = 0,
    seniority_days: int = 0,
    average_payment_delay_days: float = 0.0,
    agreed_delay_days: int = 30,
    margin_ratio: float = 0.0,
    growth_ratio: float = 0.0,
    quality_ratio: float = 1.0,
    lead_time_days: float = 0.0,
    incident_count: int = 0,
    turnover_reference: float = 5_000_000.0,
) -> dict[str, int]:
    """Calcule un score sur 100 et ses composantes, client ou fournisseur.

    Le score client valorise le volume, la fréquence, l'ancienneté, la
    ponctualité de paiement, la rentabilité et la croissance. Le score
    fournisseur valorise le volume, la fréquence, la qualité, le délai de
    livraison, la ponctualité et la fiabilité (absence d'incidents).
    """
    volume = _clamp(
        (float(turnover_amount or 0) / max(turnover_reference, 1)) * 25, 25
    )
    frequency = _clamp(int(transaction_count or 0) * 2.5, 15)
    seniority = _clamp(int(seniority_days or 0) / 365 * 5, 10)
    delay_gap = float(average_payment_delay_days or 0) - max(
        int(agreed_delay_days or 0), 0
    )
    punctuality = _clamp(20 - max(delay_gap, 0) * 0.6, 20)
    if kind == CrmScoreKind.CLIENT:
        profitability = _clamp(max(float(margin_ratio or 0), 0) * 100, 15)
        growth = _clamp(15 + float(growth_ratio or 0) * 100 * 0.15, 15)
        quality = 0
        lead_time = 0
        reliability = 0
        total = (
            volume
            + frequency
            + seniority
            + punctuality
            + profitability
            + growth
        )
    else:
        profitability = 0
        growth = 0
        quality = _clamp(max(min(float(quality_ratio or 0), 1), 0) * 20, 20)
        lead_time = _clamp(15 - max(float(lead_time_days or 0) - 3, 0), 15)
        reliability = _clamp(15 - int(incident_count or 0) * 3, 15)
        total = (
            volume
            + frequency
            + seniority
            + punctuality
            + quality
            + lead_time
            + reliability
        )
    return {
        "total_score": _clamp(total, 100),
        "volume_score": volume,
        "frequency_score": frequency,
        "seniority_score": seniority,
        "punctuality_score": punctuality,
        "profitability_score": profitability,
        "growth_score": growth,
        "quality_score": quality,
        "lead_time_score": lead_time,
        "reliability_score": reliability,
    }


def apply_partner_score(
    session: Session,
    partner: CrmPartner,
    *,
    kind: CrmScoreKind | None = None,
    season: str = "",
    today: datetime.date | None = None,
    average_payment_delay_days: float = 0.0,
    incident_count: int = 0,
    quality_ratio: float = 1.0,
    lead_time_days: float = 0.0,
    growth_ratio: float = 0.0,
) -> CrmScore:
    """Calcule et persiste le score d'un tiers depuis ses soldes réels."""
    reference = today or datetime.date.today()
    if not partner.id:
        raise RuntimeError(
            "Score impossible : le tiers doit être ajouté et flushé "
            "avant tout calcul de solde ou de score."
        )
    balances = compute_partner_balances(session, partner.id, today=reference)
    score_kind = kind or (
        CrmScoreKind.CLIENT
        if partner.kind in CLIENT_KINDS
        else CrmScoreKind.FOURNISSEUR
    )
    is_client = score_kind == CrmScoreKind.CLIENT
    turnover = balances["turnover"] if is_client else balances["purchases"]
    model = CrmSale if is_client else CrmPurchase
    with session.no_autoflush:
        transaction_count = int(
            session.execute(
                select(func.count())
                .select_from(model)
                .where(
                    model.partner_id == partner.id,
                    model.is_archived.is_(False),
                )
            ).scalar()
            or 0
        )
    seniority_days = (
        (reference - partner.first_deal_on).days if partner.first_deal_on else 0
    )
    margin_ratio = balances["margin"] / turnover if turnover > 0 else 0.0
    parts = compute_score(
        score_kind,
        turnover_amount=turnover,
        transaction_count=transaction_count,
        seniority_days=max(seniority_days, 0),
        average_payment_delay_days=average_payment_delay_days,
        agreed_delay_days=int(partner.payment_delay_days or 0),
        margin_ratio=margin_ratio,
        growth_ratio=growth_ratio,
        quality_ratio=quality_ratio,
        lead_time_days=lead_time_days,
        incident_count=incident_count,
    )
    score = CrmScore(
        partner_id=partner.id,
        kind=score_kind,
        grade=grade_for_score(parts["total_score"]),
        computed_on=reference,
        season=season,
        average_payment_delay_days=round(
            float(average_payment_delay_days or 0), 2
        ),
        turnover_amount=turnover,
        transaction_count=transaction_count,
        incident_count=int(incident_count or 0),
        **parts,
    )
    session.add(score)
    partner.score_value = parts["total_score"]
    return score


# ---------------------------------------------------------------------------
# Historique 360° et audit
# ---------------------------------------------------------------------------


def record_event(
    session: Session,
    *,
    partner_id: int,
    kind: CrmEventKind,
    title: str,
    summary: str = "",
    occurred_on: datetime.date | None = None,
    amount: float = 0.0,
    author: str = "Système",
    icon: str = "history",
    module_route: str = "/crm",
    **links: int | None,
) -> CrmEvent:
    """Ajoute un événement à la timeline 360° d'un tiers."""
    allowed = {
        "contact_id",
        "sale_id",
        "purchase_id",
        "invoice_id",
        "payment_id",
        "document_id",
        "parcel_id",
        "crop_id",
        "harvest_id",
    }
    event = CrmEvent(
        partner_id=partner_id,
        kind=kind,
        title=title,
        summary=summary,
        occurred_on=occurred_on or datetime.date.today(),
        amount=round(float(amount or 0), 2),
        author=author,
        icon=icon,
        module_route=module_route,
        **{k: v for k, v in links.items() if k in allowed},
    )
    session.add(event)
    return event


def log_crm_action(
    session: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: int = 0,
    entity_ref: str = "",
    partner_id: int | None = None,
    field_name: str = "",
    old_value: str = "",
    new_value: str = "",
    summary: str = "",
    actor_label: str = "Système",
    user_id: int | None = None,
    module_route: str = "/crm",
    ip_address: str = "",
    is_sensitive: bool = False,
) -> CrmAuditLog:
    """Journalise une action CRM avec ancienne et nouvelle valeur."""
    entry = CrmAuditLog(
        partner_id=partner_id,
        user_id=user_id,
        actor_label=actor_label,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_ref=entity_ref,
        field_name=field_name,
        old_value=str(old_value or ""),
        new_value=str(new_value or ""),
        summary=summary,
        module_route=module_route,
        ip_address=ip_address,
        is_sensitive=is_sensitive,
        occurred_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(entry)
    return entry

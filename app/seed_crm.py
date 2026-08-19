"""Données de démonstration du module CRM & Partenaires.

Le semis est strictement idempotent : si la table `crm_partner` contient déjà
au moins une ligne, rien n'est écrit. Aucune donnée agricole existante n'est
modifiée ni écrasée — les liens vers parcelles, cultures, récoltes, produits
et interventions sont résolus s'ils existent, et laissés à `None` sinon.
"""

from __future__ import annotations

import datetime
import logging

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.crm_rules import (
    apply_partner_score,
    log_crm_action,
    next_code,
    record_event,
    refresh_purchase_totals,
    refresh_sale_totals,
    refresh_settlements,
)
from app.local_db_env import SYNC_DB_URL, force_local_database_env
from app.models import (
    Crop,
    CrmAuditLog,
    CrmContact,
    CrmDocument,
    CrmDocumentKind,
    CrmDocumentLink,
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
    Harvest,
    Intervention,
    InvoiceKind,
    InvoiceStatus,
    Parcel,
    PartnerKind,
    PartnerLegalForm,
    PartnerStatus,
    PaymentDirection,
    PaymentMethod,
    Product,
    PurchaseStatus,
    SaleStatus,
    SupplierDomain,
)

__all__ = [
    "crm_is_seeded",
    "crm_integrity_report",
    "seed_crm",
    "seed_crm_if_empty",
]

_SEASON = "2025-2026"


def crm_is_seeded(session: Session) -> bool:
    """Indique si le CRM contient déjà au moins un tiers."""
    count = session.execute(
        select(func.count()).select_from(CrmPartner)
    ).scalar()
    return int(count or 0) > 0


def _first_id(session: Session, model: type) -> int | None:
    """Premier identifiant existant d'un modèle agricole (None si vide)."""
    return session.execute(select(model.id).limit(1)).scalar_one_or_none()


def _require_id(instance: object, label: str) -> int:
    """Retourne l'identifiant persistant d'une entité fraîchement flushée.

    Toute clé étrangère du CRM est renseignée depuis cette valeur : si le
    flush n'a pas encore attribué d'identifiant, mieux vaut échouer
    explicitement que d'écrire un `partner_id` (ou tout autre lien) nul.
    """
    value = getattr(instance, "id", None)
    if not value:
        raise RuntimeError(
            f"Identifiant manquant pour {label} : "
            "la ligne doit être ajoutée et flushée avant ses dépendances."
        )
    return int(value)


# (enfant, colonne FK, parent, colonne nullable ?)
_CRM_REFERENCES: tuple[tuple[type, str, type, bool], ...] = (
    (CrmContact, "partner_id", CrmPartner, False),
    (CrmSale, "partner_id", CrmPartner, False),
    (CrmSaleItem, "sale_id", CrmSale, False),
    (CrmPurchase, "partner_id", CrmPartner, False),
    (CrmPurchaseItem, "purchase_id", CrmPurchase, False),
    (CrmInvoice, "partner_id", CrmPartner, False),
    (CrmInvoice, "sale_id", CrmSale, True),
    (CrmInvoice, "purchase_id", CrmPurchase, True),
    (CrmInvoiceItem, "invoice_id", CrmInvoice, False),
    (CrmInvoiceItem, "sale_item_id", CrmSaleItem, True),
    (CrmInvoiceItem, "purchase_item_id", CrmPurchaseItem, True),
    (CrmPayment, "partner_id", CrmPartner, False),
    (CrmPayment, "invoice_id", CrmInvoice, True),
    (CrmPayment, "sale_id", CrmSale, True),
    (CrmPayment, "purchase_id", CrmPurchase, True),
    (CrmReceivable, "partner_id", CrmPartner, False),
    (CrmReceivable, "invoice_id", CrmInvoice, True),
    (CrmReceivable, "sale_id", CrmSale, True),
    (CrmPayable, "partner_id", CrmPartner, False),
    (CrmPayable, "invoice_id", CrmInvoice, True),
    (CrmPayable, "purchase_id", CrmPurchase, True),
    (CrmDocument, "partner_id", CrmPartner, False),
    (CrmDocumentLink, "document_id", CrmDocument, False),
    (CrmDocumentLink, "sale_id", CrmSale, True),
    (CrmDocumentLink, "purchase_id", CrmPurchase, True),
    (CrmDocumentLink, "invoice_id", CrmInvoice, True),
    (CrmDocumentLink, "payment_id", CrmPayment, True),
    (CrmDocumentLink, "contact_id", CrmContact, True),
    (CrmDocumentLink, "product_id", Product, True),
    (CrmDocumentLink, "intervention_id", Intervention, True),
    (CrmDocumentLink, "parcel_id", Parcel, True),
    (CrmDocumentLink, "crop_id", Crop, True),
    (CrmDocumentLink, "harvest_id", Harvest, True),
    (CrmEvent, "partner_id", CrmPartner, False),
    (CrmEvent, "contact_id", CrmContact, True),
    (CrmEvent, "sale_id", CrmSale, True),
    (CrmEvent, "purchase_id", CrmPurchase, True),
    (CrmEvent, "invoice_id", CrmInvoice, True),
    (CrmEvent, "payment_id", CrmPayment, True),
    (CrmEvent, "document_id", CrmDocument, True),
    (CrmEvent, "parcel_id", Parcel, True),
    (CrmEvent, "crop_id", Crop, True),
    (CrmEvent, "harvest_id", Harvest, True),
    (CrmScore, "partner_id", CrmPartner, False),
    (CrmAuditLog, "partner_id", CrmPartner, True),
    (CrmSale, "parcel_id", Parcel, True),
    (CrmSale, "crop_id", Crop, True),
    (CrmSale, "harvest_id", Harvest, True),
    (CrmSaleItem, "parcel_id", Parcel, True),
    (CrmSaleItem, "crop_id", Crop, True),
    (CrmSaleItem, "harvest_id", Harvest, True),
    (CrmSaleItem, "product_id", Product, True),
    (CrmPurchase, "parcel_id", Parcel, True),
    (CrmPurchase, "crop_id", Crop, True),
    (CrmPurchase, "intervention_id", Intervention, True),
    (CrmPurchaseItem, "parcel_id", Parcel, True),
    (CrmPurchaseItem, "crop_id", Crop, True),
    (CrmPurchaseItem, "intervention_id", Intervention, True),
    (CrmPurchaseItem, "product_id", Product, True),
    (CrmInvoiceItem, "product_id", Product, True),
)


def _crm_reference_anomalies(session: Session) -> list[str]:
    """Liste les anomalies de références du graphe CRM (vide si tout est sain).

    Contrôle, pour chaque lien du module (ventes, achats, factures, lignes,
    paiements, créances, dettes, documents, événements, scores, audits) :
    l'absence de clé étrangère obligatoire nulle et l'existence effective de
    la ligne parente référencée, y compris pour les ancrages agricoles
    (parcelles, cultures, récoltes, produits, interventions).
    """
    anomalies: list[str] = []
    # Aucun autoflush pendant le contrôle : on inspecte l'état déjà écrit.
    for child, field, parent, nullable in _CRM_REFERENCES:
        column = getattr(child, field)
        if not nullable:
            missing = int(
                session.execute(
                    select(func.count())
                    .select_from(child)
                    .where(column.is_(None))
                ).scalar()
                or 0
            )
            if missing:
                anomalies.append(
                    f"{child.__tablename__}.{field} nul sur {missing} ligne(s)."
                )
        dangling = int(
            session.execute(
                select(func.count())
                .select_from(child)
                .where(
                    column.is_not(None),
                    column.not_in(select(parent.id)),
                )
            ).scalar()
            or 0
        )
        if dangling:
            anomalies.append(
                f"{child.__tablename__}.{field} référence "
                f"{dangling} identifiant(s) inexistant(s) dans "
                f"{parent.__tablename__}."
            )
    return anomalies


def crm_integrity_report(session: Session) -> list[str]:
    """Rapport d'intégrité CRM, sans jamais déclencher d'écriture implicite."""
    with session.no_autoflush:
        return _crm_reference_anomalies(session)


def _partner(
    session: Session,
    *,
    kind: PartnerKind,
    legal_name: str,
    trade_name: str,
    prefix: str,
    wilaya: str,
    commune: str,
    phone: str,
    email: str,
    category: str,
    segment: str,
    domain: SupplierDomain,
    delay: int,
    credit_limit: float,
    first_deal_on: datetime.date,
    legal_form: PartnerLegalForm = PartnerLegalForm.ENTREPRISE,
) -> CrmPartner:
    partner = CrmPartner(
        code=next_code(session, CrmPartner, prefix),
        legal_name=legal_name,
        trade_name=trade_name,
        kind=kind,
        legal_form=legal_form,
        status=PartnerStatus.ACTIF,
        tax_id=f"{abs(hash(legal_name)) % 10**15:015d}",
        nif=f"{abs(hash(trade_name)) % 10**15:015d}",
        nis=f"{abs(hash(email)) % 10**15:015d}",
        trade_register=f"{abs(hash(phone)) % 10**10:010d}",
        address=f"Zone agricole, {commune}",
        wilaya=wilaya,
        commune=commune,
        country="Algérie",
        phone=phone,
        whatsapp=phone,
        email=email,
        category=category,
        segment=segment,
        supplier_domain=domain,
        payment_terms=f"{delay} jours fin de mois",
        payment_delay_days=delay,
        credit_limit=credit_limit,
        default_vat_rate=19,
        preferred_payment_method=PaymentMethod.VIREMENT,
        first_deal_on=first_deal_on,
        last_activity_on=first_deal_on,
    )
    session.add(partner)
    # Le partenaire est écrit immédiatement : toutes les dépendances
    # (contacts, transactions, événements, audits) exigent un `partner_id`.
    session.flush()
    partner_id = _require_id(partner, f"tiers {legal_name}")
    record_event(
        session,
        partner_id=partner_id,
        kind=CrmEventKind.CREATION,
        title="Fiche tiers créée",
        summary=f"{legal_name} enregistré comme {kind.value}.",
        occurred_on=first_deal_on,
        author="Direction",
        icon="user-plus",
    )
    log_crm_action(
        session,
        partner_id=partner_id,
        action="creation",
        entity_type="crm_partner",
        entity_id=partner_id,
        entity_ref=partner.code,
        summary=f"Création du tiers {legal_name}.",
        actor_label="Direction",
    )
    return partner


def _contact(
    session: Session,
    partner: CrmPartner,
    last_name: str,
    first_name: str,
    role: str,
    phone: str,
    email: str,
    *,
    primary: bool = True,
) -> CrmContact:
    contact = CrmContact(
        partner_id=_require_id(partner, "tiers du contact"),
        last_name=last_name,
        first_name=first_name,
        role=role,
        phone=phone,
        mobile=phone,
        whatsapp=phone,
        email=email,
        is_primary=primary,
    )
    session.add(contact)
    session.flush()
    if primary:
        partner.primary_contact_name = f"{first_name} {last_name}".strip()
        partner.primary_contact_role = role
    return contact


def _invoice_from_sale(
    session: Session,
    sale: CrmSale,
    items: list[CrmSaleItem],
    delay_days: int,
) -> CrmInvoice:
    issue = sale.delivery_date or sale.sale_date or datetime.date.today()
    sale_id = _require_id(sale, "vente à facturer")
    invoice = CrmInvoice(
        partner_id=int(sale.partner_id),
        code=next_code(session, CrmInvoice, "FAC", year=issue.year),
        kind=InvoiceKind.VENTE,
        status=InvoiceStatus.EMISE,
        sale_id=sale_id,
        issue_date=issue,
        due_date=issue + datetime.timedelta(days=delay_days),
        season=sale.season,
    )
    session.add(invoice)
    session.flush()
    invoice_id = _require_id(invoice, f"facture de vente {invoice.code}")
    for position, item in enumerate(items, start=1):
        session.add(
            CrmInvoiceItem(
                invoice_id=invoice_id,
                label=item.label,
                position=position,
                sale_item_id=_require_id(item, "ligne de vente"),
                product_id=item.product_id,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=item.unit_price,
                discount_percent=item.discount_percent,
                vat_rate=item.vat_rate,
            )
        )
    session.flush()
    return invoice


def _invoice_from_purchase(
    session: Session,
    purchase: CrmPurchase,
    items: list[CrmPurchaseItem],
    delay_days: int,
) -> CrmInvoice:
    issue = (
        purchase.received_date
        or purchase.purchase_date
        or datetime.date.today()
    )
    purchase_id = _require_id(purchase, "achat à facturer")
    invoice = CrmInvoice(
        partner_id=int(purchase.partner_id),
        code=next_code(session, CrmInvoice, "FAF", year=issue.year),
        kind=InvoiceKind.ACHAT,
        status=InvoiceStatus.EMISE,
        purchase_id=purchase_id,
        external_reference=purchase.receipt_reference,
        issue_date=issue,
        due_date=issue + datetime.timedelta(days=delay_days),
        season=purchase.season,
    )
    session.add(invoice)
    session.flush()
    invoice_id = _require_id(invoice, f"facture d'achat {invoice.code}")
    for position, item in enumerate(items, start=1):
        session.add(
            CrmInvoiceItem(
                invoice_id=invoice_id,
                label=item.label,
                position=position,
                purchase_item_id=_require_id(item, "ligne d'achat"),
                product_id=item.product_id,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=item.unit_price,
                discount_percent=item.discount_percent,
                vat_rate=item.vat_rate,
            )
        )
    session.flush()
    return invoice


def _payment(
    session: Session,
    partner: CrmPartner,
    invoice: CrmInvoice,
    amount: float,
    paid_on: datetime.date,
    direction: PaymentDirection,
    method: PaymentMethod,
) -> CrmPayment:
    invoice_id = _require_id(invoice, "facture réglée")
    payment = CrmPayment(
        partner_id=_require_id(partner, "tiers du paiement"),
        code=next_code(session, CrmPayment, "PAY", year=paid_on.year),
        direction=direction,
        invoice_id=invoice_id,
        sale_id=invoice.sale_id,
        purchase_id=invoice.purchase_id,
        paid_on=paid_on,
        amount=round(amount, 2),
        method=method,
        reference=f"{invoice.code}/REG",
        bank="Banque Agricole",
        recorded_by="Comptabilité",
    )
    session.add(payment)
    session.flush()
    payment_id = _require_id(payment, f"paiement {payment.code}")
    record_event(
        session,
        partner_id=int(payment.partner_id),
        kind=CrmEventKind.PAIEMENT,
        title=(
            "Paiement reçu"
            if direction == PaymentDirection.ENCAISSEMENT
            else "Paiement effectué"
        ),
        summary=f"{payment.code} sur facture {invoice.code}.",
        occurred_on=paid_on,
        amount=payment.amount,
        author="Comptabilité",
        icon="banknote",
        payment_id=payment_id,
        invoice_id=invoice_id,
    )
    return payment


def seed_crm(session: Session, *, today: datetime.date | None = None) -> None:
    """Insère un jeu de démonstration CRM cohérent (sans rien écraser)."""
    reference = today or datetime.date.today()
    parcel_id = _first_id(session, Parcel)
    crop_id = _first_id(session, Crop)
    harvest_id = _first_id(session, Harvest)
    product_id = _first_id(session, Product)
    intervention_id = _first_id(session, Intervention)

    # --- Clients --------------------------------------------------------
    client_specs = [
        {
            "legal_name": "Groupe Semoulerie du Sahel",
            "trade_name": "Sahel Semoule",
            "kind": PartnerKind.CLIENT,
            "wilaya": "Biskra",
            "commune": "Tolga",
            "phone": "+213661200101",
            "email": "achats@sahel-semoule.dz",
            "category": "Industriel",
            "segment": "Grands comptes",
            "delay": 45,
            "credit_limit": 8_000_000,
            "contact": ("Belkacem", "Yacine", "Directeur des achats"),
            "product_label": "Blé dur — récolte campagne",
            "quantity": 180,
            "unit": "t",
            "unit_price": 62_000,
            "paid_ratio": 0.6,
        },
        {
            "legal_name": "Coopérative Dattes El Oued",
            "trade_name": "CoopDattes",
            "kind": PartnerKind.COOPERATIVE,
            "wilaya": "El Oued",
            "commune": "Debila",
            "phone": "+213661200202",
            "email": "contact@coopdattes.dz",
            "category": "Coopérative",
            "segment": "Export",
            "delay": 30,
            "credit_limit": 4_500_000,
            "contact": ("Hamdi", "Nadia", "Responsable collecte"),
            "product_label": "Deglet Nour catégorie A",
            "quantity": 42,
            "unit": "t",
            "unit_price": 320_000,
            "paid_ratio": 1.0,
        },
        {
            "legal_name": "Marché de Gros Constantine",
            "trade_name": "MGC Primeurs",
            "kind": PartnerKind.GROSSISTE,
            "wilaya": "Constantine",
            "commune": "Hamma Bouziane",
            "phone": "+213661200303",
            "email": "commandes@mgc-primeurs.dz",
            "category": "Grossiste",
            "segment": "Marché local",
            "delay": 15,
            "credit_limit": 1_800_000,
            "contact": ("Saïdi", "Kamel", "Acheteur primeurs"),
            "product_label": "Tomate industrielle",
            "quantity": 65,
            "unit": "t",
            "unit_price": 48_000,
            "paid_ratio": 0.0,
        },
    ]

    for index, spec in enumerate(client_specs):
        first_deal = reference - datetime.timedelta(days=420 + index * 90)
        partner = _partner(
            session,
            kind=spec["kind"],
            legal_name=spec["legal_name"],
            trade_name=spec["trade_name"],
            prefix="CLI",
            wilaya=spec["wilaya"],
            commune=spec["commune"],
            phone=spec["phone"],
            email=spec["email"],
            category=spec["category"],
            segment=spec["segment"],
            domain=SupplierDomain.AUTRE,
            delay=spec["delay"],
            credit_limit=spec["credit_limit"],
            first_deal_on=first_deal,
        )
        partner_id = _require_id(partner, spec["legal_name"])
        last, first, role = spec["contact"]
        _contact(
            session,
            partner,
            last,
            first,
            role,
            spec["phone"],
            spec["email"],
        )
        sale_date = reference - datetime.timedelta(days=70 + index * 20)
        sale = CrmSale(
            partner_id=partner_id,
            code=next_code(session, CrmSale, "VTE", year=sale_date.year),
            status=SaleStatus.FACTUREE,
            sale_date=sale_date,
            delivery_date=sale_date + datetime.timedelta(days=4),
            season=_SEASON,
            label=f"Vente {spec['product_label']}",
            delivery_note=f"BL-{sale_date.year}-{index + 1:03d}",
            order_reference=f"CMD-{index + 1:04d}",
            parcel_id=parcel_id,
            crop_id=crop_id,
            harvest_id=harvest_id,
            payment_method=PaymentMethod.VIREMENT,
        )
        session.add(sale)
        session.flush()
        sale_id = _require_id(sale, f"vente {sale.code}")
        item = CrmSaleItem(
            sale_id=sale_id,
            label=spec["product_label"],
            position=1,
            harvest_id=harvest_id,
            crop_id=crop_id,
            parcel_id=parcel_id,
            quantity=spec["quantity"],
            unit=spec["unit"],
            unit_price=spec["unit_price"],
            discount_percent=2 if index == 0 else 0,
            vat_rate=19,
            quality_grade="A",
        )
        session.add(item)
        session.flush()
        refresh_sale_totals(session, sale)
        record_event(
            session,
            partner_id=partner_id,
            kind=CrmEventKind.VENTE,
            title="Vente enregistrée",
            summary=f"{sale.code} — {spec['product_label']}.",
            occurred_on=sale_date,
            amount=float(sale.amount_ttc or 0),
            author="Commercial",
            icon="shopping-cart",
            sale_id=sale_id,
            harvest_id=harvest_id,
        )
        invoice = _invoice_from_sale(session, sale, [item], spec["delay"])
        refresh_settlements(session, invoice, today=reference)
        ratio = float(spec["paid_ratio"])
        if ratio > 0:
            _payment(
                session,
                partner,
                invoice,
                float(invoice.amount_ttc or 0) * ratio,
                sale_date + datetime.timedelta(days=spec["delay"] // 2),
                PaymentDirection.ENCAISSEMENT,
                PaymentMethod.VIREMENT,
            )
            refresh_settlements(session, invoice, today=reference)
        refresh_sale_totals(session, sale)
        document = CrmDocument(
            partner_id=partner_id,
            title=f"Contrat de campagne {_SEASON}",
            kind=CrmDocumentKind.CONTRAT,
            reference=f"CTR-{partner.code}",
            issued_on=first_deal,
            expires_on=first_deal + datetime.timedelta(days=730),
            author="Direction",
        )
        # Le document est écrit avant son lien : `CrmDocumentLink.document_id`
        # est NOT NULL et ne peut être renseigné qu'après attribution de l'id.
        session.add(document)
        session.flush()
        document_id = _require_id(document, document.title)
        link = CrmDocumentLink(
            document_id=document_id,
            label=f"Vente {sale.code}",
            sale_id=sale_id,
            invoice_id=_require_id(invoice, f"facture {invoice.code}"),
            parcel_id=parcel_id,
            crop_id=crop_id,
            harvest_id=harvest_id,
            module_route="/crm",
        )
        session.add(link)
        # Flush immédiat : le lien est validé maintenant, jamais au détour
        # d'un autoflush déclenché par un calcul de solde ou de score.
        session.flush()
        _require_id(link, f"lien documentaire {document.title}")
        record_event(
            session,
            partner_id=partner_id,
            kind=CrmEventKind.DOCUMENT,
            title="Document ajouté",
            summary=document.title,
            occurred_on=first_deal,
            author="Direction",
            icon="file-text",
            document_id=document_id,
        )
        partner.last_activity_on = reference
        session.flush()
        with session.no_autoflush:
            apply_partner_score(
                session,
                partner,
                season=_SEASON,
                today=reference,
                average_payment_delay_days=float(spec["delay"])
                * (1.4 if ratio == 0 else 0.8),
                growth_ratio=0.12,
            )
        session.flush()

    # --- Fournisseurs ---------------------------------------------------
    supplier_specs = [
        {
            "legal_name": "Intrants Agricoles Nord SPA",
            "trade_name": "IAN Fertilisants",
            "kind": PartnerKind.FOURNISSEUR,
            "domain": SupplierDomain.ENGRAIS,
            "wilaya": "Alger",
            "commune": "Rouiba",
            "phone": "+213661300101",
            "email": "commercial@ian-fertilisants.dz",
            "category": "Engrais",
            "delay": 30,
            "item": ("Urée 46% — sac 50 kg", 240, "sac", 6_400),
            "paid_ratio": 1.0,
        },
        {
            "legal_name": "Semences du Hodna EURL",
            "trade_name": "Hodna Semences",
            "kind": PartnerKind.FOURNISSEUR,
            "domain": SupplierDomain.SEMENCES,
            "wilaya": "M'Sila",
            "commune": "Sidi Aïssa",
            "phone": "+213661300202",
            "email": "ventes@hodna-semences.dz",
            "category": "Semences",
            "delay": 45,
            "item": ("Semence blé dur certifiée", 90, "q", 9_800),
            "paid_ratio": 0.5,
        },
        {
            "legal_name": "Atelier Mécanique Batna SARL",
            "trade_name": "AMB Maintenance",
            "kind": PartnerKind.PRESTATAIRE,
            "domain": SupplierDomain.MAINTENANCE,
            "wilaya": "Batna",
            "commune": "Batna",
            "phone": "+213661300303",
            "email": "atelier@amb-maintenance.dz",
            "category": "Maintenance",
            "delay": 20,
            "item": ("Révision tracteur — forfait", 3, "u", 145_000),
            "paid_ratio": 0.0,
        },
        {
            "legal_name": "Transports Agro Sud",
            "trade_name": "TAS Logistique",
            "kind": PartnerKind.TRANSPORTEUR,
            "domain": SupplierDomain.TRANSPORT,
            "wilaya": "Ouargla",
            "commune": "Hassi Messaoud",
            "phone": "+213661300404",
            "email": "logistique@tas-sud.dz",
            "category": "Transport",
            "delay": 30,
            "item": ("Location camion frigorifique", 12, "jour", 38_000),
            "paid_ratio": 1.0,
        },
    ]

    for index, spec in enumerate(supplier_specs):
        first_deal = reference - datetime.timedelta(days=520 + index * 60)
        partner = _partner(
            session,
            kind=spec["kind"],
            legal_name=spec["legal_name"],
            trade_name=spec["trade_name"],
            prefix="FRN",
            wilaya=spec["wilaya"],
            commune=spec["commune"],
            phone=spec["phone"],
            email=spec["email"],
            category=spec["category"],
            segment="Approvisionnement",
            domain=spec["domain"],
            delay=spec["delay"],
            credit_limit=0,
            first_deal_on=first_deal,
        )
        partner_id = _require_id(partner, spec["legal_name"])
        _contact(
            session,
            partner,
            "Zerrouki",
            f"Responsable {index + 1}",
            "Chargé de compte",
            spec["phone"],
            spec["email"],
        )
        purchase_date = reference - datetime.timedelta(days=55 + index * 15)
        purchase = CrmPurchase(
            partner_id=partner_id,
            code=next_code(
                session, CrmPurchase, "ACH", year=purchase_date.year
            ),
            status=PurchaseStatus.FACTUREE,
            purchase_date=purchase_date,
            received_date=purchase_date + datetime.timedelta(days=5),
            season=_SEASON,
            label=f"Achat {spec['item'][0]}",
            order_reference=f"BC-{purchase_date.year}-{index + 1:03d}",
            receipt_reference=f"BR-{purchase_date.year}-{index + 1:03d}",
            domain=spec["domain"],
            parcel_id=parcel_id,
            crop_id=crop_id,
            intervention_id=intervention_id,
            payment_method=PaymentMethod.VIREMENT,
        )
        session.add(purchase)
        session.flush()
        label, quantity, unit, unit_price = spec["item"]
        purchase_id = _require_id(purchase, f"achat {purchase.code}")
        line = CrmPurchaseItem(
            purchase_id=purchase_id,
            label=label,
            position=1,
            product_id=product_id,
            parcel_id=parcel_id,
            crop_id=crop_id,
            intervention_id=intervention_id,
            domain=spec["domain"],
            quantity=quantity,
            unit=unit,
            unit_price=unit_price,
            vat_rate=19,
        )
        session.add(line)
        session.flush()
        refresh_purchase_totals(session, purchase)
        record_event(
            session,
            partner_id=partner_id,
            kind=CrmEventKind.ACHAT,
            title="Achat enregistré",
            summary=f"{purchase.code} — {label}.",
            occurred_on=purchase_date,
            amount=float(purchase.amount_ttc or 0),
            author="Service achats",
            icon="package",
            purchase_id=purchase_id,
        )
        invoice = _invoice_from_purchase(
            session, purchase, [line], spec["delay"]
        )
        refresh_settlements(session, invoice, today=reference)
        ratio = float(spec["paid_ratio"])
        if ratio > 0:
            _payment(
                session,
                partner,
                invoice,
                float(invoice.amount_ttc or 0) * ratio,
                purchase_date + datetime.timedelta(days=spec["delay"] // 2),
                PaymentDirection.DECAISSEMENT,
                PaymentMethod.VIREMENT,
            )
            refresh_settlements(session, invoice, today=reference)
        refresh_purchase_totals(session, purchase)
        partner.last_activity_on = reference
        session.flush()
        with session.no_autoflush:
            apply_partner_score(
                session,
                partner,
                season=_SEASON,
                today=reference,
                average_payment_delay_days=float(spec["delay"]),
                quality_ratio=0.9,
                lead_time_days=5 + index,
                incident_count=index % 2,
            )
        session.flush()

    # Dernier garde-fou : aucune clé étrangère nulle ou orpheline ne doit
    # être validée en base (ventes, achats, factures, lignes, paiements,
    # créances, dettes, documents, événements, scores et audits inclus).
    session.flush()
    anomalies = crm_integrity_report(session)
    if anomalies:
        session.rollback()
        raise RuntimeError("Semis CRM incohérent : " + " | ".join(anomalies))
    session.commit()


def seed_crm_if_empty(today: datetime.date | None = None) -> bool:
    """Sème le CRM uniquement s'il est vide. Retourne True si semé."""
    force_local_database_env()
    engine = create_engine(SYNC_DB_URL, future=True)
    seeded = False
    try:
        with Session(engine) as session:
            if crm_is_seeded(session):
                return False
            try:
                seed_crm(session, today=today)
            except Exception:
                # Aucun jeu partiel ne doit subsister : la table reste vide et
                # un prochain démarrage pourra re-tenter le semis proprement.
                logging.exception("Unexpected error")
                session.rollback()
                raise
            seeded = True
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
    finally:
        engine.dispose()
    return seeded

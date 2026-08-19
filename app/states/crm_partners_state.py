"""Espaces Clients, Fournisseurs et Partenaires du module CRM.

Toutes les lectures et écritures passent par `rx.asession()` en SQL brut
paramétré sur les tables CRM déjà créées (`crm_partner`, `crm_contact`,
`crm_sale`, `crm_purchase`, `crm_invoice`, `crm_payment`, `crm_receivable`,
`crm_payable`, `crm_document`, `crm_event`, `crm_score`, `crm_audit_log`).

Les liens agricoles (parcelles, cultures, produits, récoltes, campagnes) sont
résolus par jointures sur les tables existantes : aucune donnée agronomique
n'est dupliquée. Un tiers portant des transactions n'est jamais supprimé : il
est archivé (et peut être réactivé).
"""

from __future__ import annotations

import asyncio
import datetime
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.database import ensure_crm_tables, ensure_local_database
from app.seed_crm import seed_crm_if_empty
from app.states.crm_state import (
    CLIENT_KINDS_SQL,
    KIND_LABELS,
    STATUS_LABELS,
    SUPPLIER_KINDS_SQL,
)

# Les colonnes Enum SQLAlchemy sont persistées par NOM (majuscules).
PARTNER_KINDS: list[str] = [
    "CLIENT",
    "FOURNISSEUR",
    "MIXTE",
    "TRANSPORTEUR",
    "PRESTATAIRE",
    "COOPERATIVE",
    "GROSSISTE",
    "DISTRIBUTEUR",
    "REVENDEUR",
    "AUTRE",
]

PARTNER_STATUSES: list[str] = [
    "ACTIF",
    "INACTIF",
    "BLOQUE",
    "PROSPECT",
    "ARCHIVE",
]

LEGAL_FORMS: list[str] = [
    "PARTICULIER",
    "ENTREPRISE",
    "COOPERATIVE",
    "ASSOCIATION",
    "ADMINISTRATION",
    "AUTRE",
]

LEGAL_FORM_LABELS: dict[str, str] = {
    "PARTICULIER": "Particulier",
    "ENTREPRISE": "Entreprise",
    "COOPERATIVE": "Coopérative",
    "ASSOCIATION": "Association",
    "ADMINISTRATION": "Administration",
    "AUTRE": "Autre",
}

SUPPLIER_DOMAINS: list[str] = [
    "SEMENCES",
    "ENGRAIS",
    "PHYTOSANITAIRE",
    "MATERIEL",
    "PIECES",
    "CARBURANT",
    "IRRIGATION",
    "EMBALLAGE",
    "TRANSPORT",
    "SERVICES",
    "MAINTENANCE",
    "ENERGIE",
    "AUTRE",
]

PAYMENT_METHODS: list[str] = [
    "VIREMENT",
    "CHEQUE",
    "ESPECES",
    "CARTE",
    "PRELEVEMENT",
    "AUTRE",
]

DOCUMENT_KINDS: list[str] = [
    "CONTRAT",
    "FACTURE",
    "BON_COMMANDE",
    "BON_LIVRAISON",
    "DEVIS",
    "CERTIFICAT",
    "DOCUMENT_FISCAL",
    "REGISTRE_COMMERCE",
    "CONVENTION",
    "CORRESPONDANCE",
    "PHOTO",
    "AUTRE",
]

GRADE_LABELS: dict[str, str] = {
    "EXCELLENT": "Excellent",
    "BON": "Bon",
    "MOYEN": "Moyen",
    "FRAGILE": "Fragile",
    "RISQUE": "À risque",
}

SPACE_KINDS_SQL: dict[str, str] = {
    "clients": CLIENT_KINDS_SQL,
    "fournisseurs": SUPPLIER_KINDS_SQL,
}

SPACE_TITLES: dict[str, str] = {
    "clients": "Espace Clients",
    "fournisseurs": "Espace Fournisseurs",
    "partenaires": "Espace Partenaires",
}

CODE_PREFIXES: dict[str, str] = {
    "CLIENT": "CLI",
    "GROSSISTE": "CLI",
    "DISTRIBUTEUR": "CLI",
    "REVENDEUR": "CLI",
    "FOURNISSEUR": "FRN",
    "TRANSPORTEUR": "FRN",
    "PRESTATAIRE": "FRN",
}


class PartnerRow(TypedDict):
    id: int
    code: str
    name: str
    trade_name: str
    kind_label: str
    status: str
    status_label: str
    category: str
    city: str
    phone: str
    email: str
    score: int
    turnover: float
    purchases: float
    receivable: float
    payable: float
    deals: int
    last_activity: str
    is_archived: bool


class ContactRow(TypedDict):
    id: int
    name: str
    role: str
    phone: str
    mobile: str
    email: str
    whatsapp: str
    is_primary: bool
    notes: str


class TxRow(TypedDict):
    id: int
    code: str
    label: str
    status_label: str
    date: str
    season: str
    amount: float
    paid: float
    remaining: float
    links: list[str]


class InvoiceRow(TypedDict):
    id: int
    code: str
    kind_label: str
    status_label: str
    issue_date: str
    due_date: str
    amount: float
    paid: float
    remaining: float
    overdue_days: int


class PaymentRow(TypedDict):
    id: int
    code: str
    direction_label: str
    date: str
    amount: float
    method: str
    reference: str
    invoice_code: str


class SettlementRow(TypedDict):
    id: int
    invoice_code: str
    status_label: str
    due_date: str
    amount_due: float
    amount_paid: float
    remaining: float
    overdue_days: int
    bucket: str


class DocumentRow(TypedDict):
    id: int
    title: str
    kind_label: str
    reference: str
    issued_on: str
    author: str
    notes: str
    links: list[str]


class EventRow(TypedDict):
    id: int
    icon: str
    kind_label: str
    title: str
    summary: str
    date: str
    amount: float
    links: list[str]


class PartnerDetail(TypedDict):
    id: int
    code: str
    name: str
    trade_name: str
    kind: str
    kind_label: str
    legal_form_label: str
    status: str
    status_label: str
    category: str
    segment: str
    supplier_domain: str
    address: str
    city: str
    country: str
    phone: str
    phone_secondary: str
    whatsapp: str
    email: str
    website: str
    nif: str
    nis: str
    trade_register: str
    tax_id: str
    payment_terms: str
    payment_delay_days: int
    credit_limit: float
    discount_percent: float
    vat_rate: float
    currency: str
    payment_method: str
    primary_contact: str
    primary_contact_role: str
    first_deal: str
    last_activity: str
    notes: str
    tags: str
    is_archived: bool
    archive_reason: str
    main_parcel: str
    main_culture: str
    main_product: str


class ScoreCard(TypedDict):
    kind_label: str
    grade_label: str
    total: int
    volume: int
    frequency: int
    seniority: int
    punctuality: int
    profitability: int
    growth: int
    quality: int
    lead_time: int
    reliability: int
    average_delay: float
    turnover: float
    transactions: int
    incidents: int
    computed_on: str


EMPTY_DETAIL: PartnerDetail = {
    "id": 0,
    "code": "",
    "name": "",
    "trade_name": "",
    "kind": "CLIENT",
    "kind_label": "",
    "legal_form_label": "",
    "status": "ACTIF",
    "status_label": "",
    "category": "",
    "segment": "",
    "supplier_domain": "",
    "address": "",
    "city": "",
    "country": "",
    "phone": "",
    "phone_secondary": "",
    "whatsapp": "",
    "email": "",
    "website": "",
    "nif": "",
    "nis": "",
    "trade_register": "",
    "tax_id": "",
    "payment_terms": "",
    "payment_delay_days": 0,
    "credit_limit": 0.0,
    "discount_percent": 0.0,
    "vat_rate": 0.0,
    "currency": "DZD",
    "payment_method": "",
    "primary_contact": "",
    "primary_contact_role": "",
    "first_deal": "",
    "last_activity": "",
    "notes": "",
    "tags": "",
    "is_archived": False,
    "archive_reason": "",
    "main_parcel": "",
    "main_culture": "",
    "main_product": "",
}

EMPTY_SCORE: ScoreCard = {
    "kind_label": "",
    "grade_label": "",
    "total": 0,
    "volume": 0,
    "frequency": 0,
    "seniority": 0,
    "punctuality": 0,
    "profitability": 0,
    "growth": 0,
    "quality": 0,
    "lead_time": 0,
    "reliability": 0,
    "average_delay": 0.0,
    "turnover": 0.0,
    "transactions": 0,
    "incidents": 0,
    "computed_on": "",
}

EMPTY_STATS: dict[str, float] = {
    "turnover": 0.0,
    "purchases": 0.0,
    "receivable": 0.0,
    "receivable_overdue": 0.0,
    "payable": 0.0,
    "payable_overdue": 0.0,
    "received": 0.0,
    "paid_out": 0.0,
    "sales_count": 0.0,
    "purchases_count": 0.0,
    "invoices_count": 0.0,
    "documents_count": 0.0,
    "contacts_count": 0.0,
    "margin": 0.0,
    "credit_usage": 0.0,
}

EMPTY_FORM: dict[str, str] = {
    "legal_name": "",
    "trade_name": "",
    "kind": "CLIENT",
    "legal_form": "ENTREPRISE",
    "status": "ACTIF",
    "category": "",
    "segment": "",
    "supplier_domain": "AUTRE",
    "address": "",
    "wilaya": "",
    "commune": "",
    "postal_code": "",
    "country": "Algérie",
    "phone": "",
    "phone_secondary": "",
    "whatsapp": "",
    "email": "",
    "website": "",
    "nif": "",
    "nis": "",
    "trade_register": "",
    "tax_id": "",
    "payment_terms": "",
    "payment_delay_days": "30",
    "credit_limit": "0",
    "default_discount_percent": "0",
    "default_vat_rate": "19",
    "currency": "DZD",
    "preferred_payment_method": "VIREMENT",
    "primary_contact_name": "",
    "primary_contact_role": "",
    "tags": "",
    "notes": "",
}

EMPTY_CONTACT_FORM: dict[str, str] = {
    "last_name": "",
    "first_name": "",
    "role": "",
    "phone": "",
    "mobile": "",
    "whatsapp": "",
    "email": "",
    "language": "",
    "is_primary": "",
    "notes": "",
}

EMPTY_DOCUMENT_FORM: dict[str, str] = {
    "title": "",
    "kind": "CONTRAT",
    "reference": "",
    "author": "",
    "notes": "",
}


def _f(value: object) -> float:
    if value is None:
        return 0.0
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return 0.0


def _i(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _s(value: object) -> str:
    return "" if value is None else str(value)


def _date(value: object) -> str:
    text_value = _s(value)
    return text_value[:10]


def _label(mapping: dict[str, str], value: object, fallback: str = "") -> str:
    key = _s(value).upper()
    return mapping.get(key, fallback or key.replace("_", " ").capitalize())


def _links(pairs: list[tuple[str, str]]) -> list[str]:
    """Construit des libellés lisibles « Étiquette · Valeur » non vides."""
    return [f"{label} · {value}" for label, value in pairs if value]


class CrmPartnersState(rx.State):
    """Listes filtrables, fiches 360° et formulaires des tiers CRM."""

    space: str = "clients"
    is_loading: bool = False
    is_saving: bool = False
    kind_filter: str = ""
    status_filter: str = ""
    search: str = ""
    include_archived: bool = False

    partners: list[PartnerRow] = []
    selected_id: int = 0
    detail: PartnerDetail = EMPTY_DETAIL
    stats: dict[str, float] = EMPTY_STATS
    score: ScoreCard = EMPTY_SCORE
    contacts: list[ContactRow] = []
    sales: list[TxRow] = []
    purchases: list[TxRow] = []
    invoices: list[InvoiceRow] = []
    payments: list[PaymentRow] = []
    receivables: list[SettlementRow] = []
    payables: list[SettlementRow] = []
    documents: list[DocumentRow] = []
    events: list[EventRow] = []

    detail_tab: str = "identite"
    form_open: bool = False
    form_mode: str = "create"
    form_error: str = ""
    form: dict[str, str] = EMPTY_FORM
    contact_form_open: bool = False
    contact_form_mode: str = "create"
    contact_id: int = 0
    contact_form: dict[str, str] = EMPTY_CONTACT_FORM
    document_form_open: bool = False
    document_form: dict[str, str] = EMPTY_DOCUMENT_FORM

    kind_options: list[str] = PARTNER_KINDS
    status_options: list[str] = PARTNER_STATUSES
    legal_form_options: list[str] = LEGAL_FORMS
    domain_options: list[str] = SUPPLIER_DOMAINS
    payment_method_options: list[str] = PAYMENT_METHODS
    document_kind_options: list[str] = DOCUMENT_KINDS

    detail_tabs: list[dict[str, str]] = [
        {"key": "identite", "label": "Identité", "icon": "id-card"},
        {"key": "contacts", "label": "Contacts", "icon": "users-round"},
        {"key": "transactions", "label": "Transactions", "icon": "receipt"},
        {"key": "finance", "label": "Finance", "icon": "wallet"},
        {"key": "documents", "label": "Documents", "icon": "folder-open"},
        {"key": "historique", "label": "Historique", "icon": "history"},
    ]

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def space_title(self) -> str:
        return SPACE_TITLES.get(self.space, "Espace Partenaires")

    @rx.var
    def partner_count(self) -> int:
        return len(self.partners)

    @rx.var
    def has_selection(self) -> bool:
        return self.selected_id > 0

    @rx.var
    def has_transactions(self) -> bool:
        return (
            self.stats.get("sales_count", 0.0)
            + self.stats.get("purchases_count", 0.0)
            + self.stats.get("invoices_count", 0.0)
        ) > 0

    @rx.var
    def archive_hint(self) -> str:
        if self.detail["is_archived"]:
            return "Tiers archivé : réactivable à tout moment."
        if self.has_transactions:
            return (
                "Ce tiers porte des transactions : la suppression est interdite,"
                " seul l'archivage est possible."
            )
        return "Aucune transaction rattachée : archivage réversible."

    @rx.var
    def form_title(self) -> str:
        if self.form_mode == "edit":
            return f"Modifier le tiers {self.detail['code']}"
        return "Nouveau tiers commercial"

    @rx.var
    def score_label(self) -> str:
        if self.score["total"] <= 0:
            return "Score non encore calculé"
        return f"{self.score['total']}/100 — {self.score['grade_label']}"

    # ------------------------------------------------------------------
    # Chargement des listes
    # ------------------------------------------------------------------

    def _space_clause(self) -> str:
        kinds = SPACE_KINDS_SQL.get(self.space, "")
        if kinds:
            return f" AND UPPER(p.kind) IN {kinds}"
        return ""

    async def _fetch_partners(self) -> None:
        clauses = ["1 = 1"]
        params: dict[str, str] = {}
        if not self.include_archived:
            clauses.append("p.is_archived = false")
        if self.kind_filter:
            clauses.append("UPPER(p.kind) = :kind")
            params["kind"] = self.kind_filter
        if self.status_filter:
            clauses.append("UPPER(p.status) = :status")
            params["status"] = self.status_filter
        query = self.search.strip().lower()
        if query:
            clauses.append(
                "(LOWER(p.legal_name) LIKE :q OR LOWER(p.code) LIKE :q"
                " OR LOWER(COALESCE(p.trade_name, '')) LIKE :q"
                " OR LOWER(COALESCE(p.category, '')) LIKE :q"
                " OR LOWER(COALESCE(p.wilaya, '')) LIKE :q"
                " OR LOWER(COALESCE(p.commune, '')) LIKE :q"
                " OR LOWER(COALESCE(p.phone, '')) LIKE :q"
                " OR LOWER(COALESCE(p.email, '')) LIKE :q)"
            )
            params["q"] = f"%{query}%"
        where = " AND ".join(clauses) + self._space_clause()
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT p.id, p.code, p.legal_name,
                               COALESCE(p.trade_name, ''), UPPER(p.kind),
                               UPPER(p.status), COALESCE(p.category, ''),
                               TRIM(COALESCE(p.commune, '') || ' '
                                    || COALESCE(p.wilaya, '')),
                               COALESCE(p.phone, ''), COALESCE(p.email, ''),
                               COALESCE(p.score_value, 0),
                               p.last_activity_on, p.is_archived,
                               (SELECT COALESCE(SUM(s.amount_ttc), 0)
                                  FROM crm_sale s
                                  WHERE s.partner_id = p.id
                                    AND s.is_archived = false
                                    AND UPPER(s.status) <> 'ANNULEE'),
                               (SELECT COALESCE(SUM(a.amount_ttc), 0)
                                  FROM crm_purchase a
                                  WHERE a.partner_id = p.id
                                    AND a.is_archived = false
                                    AND UPPER(a.status) <> 'ANNULEE'),
                               (SELECT COALESCE(SUM(r.amount_remaining), 0)
                                  FROM crm_receivable r
                                  WHERE r.partner_id = p.id
                                    AND r.is_archived = false),
                               (SELECT COALESCE(SUM(d.amount_remaining), 0)
                                  FROM crm_payable d
                                  WHERE d.partner_id = p.id
                                    AND d.is_archived = false),
                               (SELECT COUNT(*) FROM crm_sale s2
                                  WHERE s2.partner_id = p.id)
                             + (SELECT COUNT(*) FROM crm_purchase a2
                                  WHERE a2.partner_id = p.id)
                        FROM crm_partner p
                        WHERE {where}
                        ORDER BY p.legal_name
                        LIMIT 80
                        """
                    ),
                    params,
                )
            ).all()

        self.partners = [
            {
                "id": _i(row[0]),
                "code": _s(row[1]),
                "name": _s(row[2]),
                "trade_name": _s(row[3]),
                "kind_label": _label(KIND_LABELS, row[4], "Partenaire"),
                "status": _s(row[5]).upper(),
                "status_label": _label(STATUS_LABELS, row[5], "Actif"),
                "category": _s(row[6]) or "Catégorie non renseignée",
                "city": _s(row[7]).strip() or "Localisation non précisée",
                "phone": _s(row[8]) or "—",
                "email": _s(row[9]) or "—",
                "score": _i(row[10]),
                "last_activity": _date(row[11]) or "—",
                "is_archived": bool(row[12]),
                "turnover": _f(row[13]),
                "purchases": _f(row[14]),
                "receivable": _f(row[15]),
                "payable": _f(row[16]),
                "deals": _i(row[17]),
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Fiche 360°
    # ------------------------------------------------------------------

    async def _fetch_detail(self) -> None:
        pid = self.selected_id
        if pid <= 0:
            self.detail = EMPTY_DETAIL
            self.stats = EMPTY_STATS
            self.score = EMPTY_SCORE
            self.contacts = []
            self.sales = []
            self.purchases = []
            self.invoices = []
            self.payments = []
            self.receivables = []
            self.payables = []
            self.documents = []
            self.events = []
            return
        params = {"pid": pid}
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT p.id, p.code, p.legal_name,
                               COALESCE(p.trade_name, ''), UPPER(p.kind),
                               UPPER(p.legal_form), UPPER(p.status),
                               COALESCE(p.category, ''),
                               COALESCE(p.segment, ''),
                               UPPER(COALESCE(p.supplier_domain, 'AUTRE')),
                               COALESCE(p.address, ''),
                               TRIM(COALESCE(p.commune, '') || ' '
                                    || COALESCE(p.wilaya, '')),
                               COALESCE(p.country, ''),
                               COALESCE(p.phone, ''),
                               COALESCE(p.phone_secondary, ''),
                               COALESCE(p.whatsapp, ''),
                               COALESCE(p.email, ''),
                               COALESCE(p.website, ''),
                               COALESCE(p.nif, ''), COALESCE(p.nis, ''),
                               COALESCE(p.trade_register, ''),
                               COALESCE(p.tax_id, ''),
                               COALESCE(p.payment_terms, ''),
                               COALESCE(p.payment_delay_days, 0),
                               COALESCE(p.credit_limit, 0),
                               COALESCE(p.default_discount_percent, 0),
                               COALESCE(p.default_vat_rate, 0),
                               COALESCE(p.currency, 'DZD'),
                               UPPER(COALESCE(p.preferred_payment_method, '')),
                               COALESCE(p.primary_contact_name, ''),
                               COALESCE(p.primary_contact_role, ''),
                               p.first_deal_on, p.last_activity_on,
                               COALESCE(p.notes, ''), COALESCE(p.tags, ''),
                               p.is_archived, COALESCE(p.archive_reason, ''),
                               COALESCE(par.name, ''), COALESCE(cu.name, ''),
                               COALESCE(pr.name, '')
                        FROM crm_partner p
                        LEFT JOIN parcel par ON par.id = p.main_parcel_id
                        LEFT JOIN crop_culture cu ON cu.id = p.main_culture_id
                        LEFT JOIN product pr ON pr.id = p.main_product_id
                        WHERE p.id = :pid
                        """
                    ),
                    params,
                )
            ).first()
            if row is None:
                self.selected_id = 0
                self.detail = EMPTY_DETAIL
                return
            totals = (
                await asession.execute(
                    text(
                        """
                        SELECT
                          (SELECT COALESCE(SUM(s.amount_ttc), 0) FROM crm_sale s
                             WHERE s.partner_id = :pid AND s.is_archived = false
                               AND UPPER(s.status) <> 'ANNULEE'),
                          (SELECT COALESCE(SUM(a.amount_ttc), 0)
                             FROM crm_purchase a
                             WHERE a.partner_id = :pid AND a.is_archived = false
                               AND UPPER(a.status) <> 'ANNULEE'),
                          (SELECT COALESCE(SUM(r.amount_remaining), 0)
                             FROM crm_receivable r
                             WHERE r.partner_id = :pid
                               AND r.is_archived = false),
                          (SELECT COALESCE(SUM(r.amount_remaining), 0)
                             FROM crm_receivable r
                             WHERE r.partner_id = :pid AND r.is_archived = false
                               AND UPPER(r.status) = 'EN_RETARD'),
                          (SELECT COALESCE(SUM(d.amount_remaining), 0)
                             FROM crm_payable d
                             WHERE d.partner_id = :pid
                               AND d.is_archived = false),
                          (SELECT COALESCE(SUM(d.amount_remaining), 0)
                             FROM crm_payable d
                             WHERE d.partner_id = :pid AND d.is_archived = false
                               AND UPPER(d.status) = 'EN_RETARD'),
                          (SELECT COALESCE(SUM(y.amount), 0) FROM crm_payment y
                             WHERE y.partner_id = :pid AND y.is_archived = false
                               AND UPPER(y.direction) = 'ENCAISSEMENT'),
                          (SELECT COALESCE(SUM(y.amount), 0) FROM crm_payment y
                             WHERE y.partner_id = :pid AND y.is_archived = false
                               AND UPPER(y.direction) = 'DECAISSEMENT'),
                          (SELECT COUNT(*) FROM crm_sale s2
                             WHERE s2.partner_id = :pid),
                          (SELECT COUNT(*) FROM crm_purchase a2
                             WHERE a2.partner_id = :pid),
                          (SELECT COUNT(*) FROM crm_invoice i
                             WHERE i.partner_id = :pid),
                          (SELECT COUNT(*) FROM crm_document dd
                             WHERE dd.partner_id = :pid
                               AND dd.is_archived = false),
                          (SELECT COUNT(*) FROM crm_contact c
                             WHERE c.partner_id = :pid
                               AND c.is_archived = false)
                        """
                    ),
                    params,
                )
            ).first()
            contacts = (
                await asession.execute(
                    text(
                        """
                        SELECT c.id, TRIM(COALESCE(c.first_name, '') || ' '
                                          || c.last_name),
                               COALESCE(c.role, ''), COALESCE(c.phone, ''),
                               COALESCE(c.mobile, ''), COALESCE(c.email, ''),
                               COALESCE(c.whatsapp, ''), c.is_primary,
                               COALESCE(c.notes, '')
                        FROM crm_contact c
                        WHERE c.partner_id = :pid AND c.is_archived = false
                        ORDER BY c.is_primary DESC, c.last_name
                        LIMIT 40
                        """
                    ),
                    params,
                )
            ).all()
            sales = (
                await asession.execute(
                    text(
                        """
                        SELECT s.id, s.code, COALESCE(s.label, ''),
                               UPPER(s.status), s.sale_date,
                               COALESCE(s.season, ''),
                               COALESCE(s.amount_ttc, 0),
                               COALESCE(s.paid_amount, 0),
                               COALESCE(par.name, ''), COALESCE(c.name, ''),
                               COALESCE(cu.name, ''), h.harvest_date,
                               COALESCE(h.quantity, 0), COALESCE(h.unit, ''),
                               (SELECT GROUP_CONCAT(
                                          COALESCE(NULLIF(pr.name, ''),
                                                   si.label), ', ')
                                  FROM crm_sale_item si
                                  LEFT JOIN product pr ON pr.id = si.product_id
                                  WHERE si.sale_id = s.id)
                        FROM crm_sale s
                        LEFT JOIN parcel par ON par.id = s.parcel_id
                        LEFT JOIN crop c ON c.id = s.crop_id
                        LEFT JOIN crop_culture cu ON cu.id = s.culture_id
                        LEFT JOIN harvest h ON h.id = s.harvest_id
                        WHERE s.partner_id = :pid
                        ORDER BY COALESCE(s.sale_date, '0001-01-01') DESC
                        LIMIT 30
                        """
                    ),
                    params,
                )
            ).all()
            purchases = (
                await asession.execute(
                    text(
                        """
                        SELECT a.id, a.code, COALESCE(a.label, ''),
                               UPPER(a.status), a.purchase_date,
                               COALESCE(a.season, ''),
                               COALESCE(a.amount_ttc, 0),
                               COALESCE(a.paid_amount, 0),
                               COALESCE(par.name, ''), COALESCE(c.name, ''),
                               UPPER(COALESCE(a.domain, 'AUTRE')),
                               (SELECT GROUP_CONCAT(
                                          COALESCE(NULLIF(pr.name, ''),
                                                   ai.label), ', ')
                                  FROM crm_purchase_item ai
                                  LEFT JOIN product pr ON pr.id = ai.product_id
                                  WHERE ai.purchase_id = a.id)
                        FROM crm_purchase a
                        LEFT JOIN parcel par ON par.id = a.parcel_id
                        LEFT JOIN crop c ON c.id = a.crop_id
                        WHERE a.partner_id = :pid
                        ORDER BY COALESCE(a.purchase_date, '0001-01-01') DESC
                        LIMIT 30
                        """
                    ),
                    params,
                )
            ).all()
            invoices = (
                await asession.execute(
                    text(
                        """
                        SELECT i.id, i.code, UPPER(i.kind), UPPER(i.status),
                               i.issue_date, i.due_date,
                               COALESCE(i.amount_ttc, 0),
                               COALESCE(i.paid_amount, 0),
                               COALESCE(i.remaining_amount, 0),
                               COALESCE(i.overdue_days, 0)
                        FROM crm_invoice i
                        WHERE i.partner_id = :pid AND i.is_archived = false
                        ORDER BY COALESCE(i.issue_date, '0001-01-01') DESC
                        LIMIT 30
                        """
                    ),
                    params,
                )
            ).all()
            payments = (
                await asession.execute(
                    text(
                        """
                        SELECT y.id, y.code, UPPER(y.direction), y.paid_on,
                               COALESCE(y.amount, 0), UPPER(y.method),
                               COALESCE(y.reference, ''),
                               COALESCE(i.code, '')
                        FROM crm_payment y
                        LEFT JOIN crm_invoice i ON i.id = y.invoice_id
                        WHERE y.partner_id = :pid AND y.is_archived = false
                        ORDER BY COALESCE(y.paid_on, '0001-01-01') DESC
                        LIMIT 30
                        """
                    ),
                    params,
                )
            ).all()
            receivables = (
                await asession.execute(
                    text(
                        """
                        SELECT r.id, COALESCE(i.code, ''), UPPER(r.status),
                               r.due_date, COALESCE(r.amount_due, 0),
                               COALESCE(r.amount_paid, 0),
                               COALESCE(r.amount_remaining, 0),
                               COALESCE(r.overdue_days, 0),
                               COALESCE(r.aging_bucket, '0-30')
                        FROM crm_receivable r
                        LEFT JOIN crm_invoice i ON i.id = r.invoice_id
                        WHERE r.partner_id = :pid AND r.is_archived = false
                        ORDER BY COALESCE(r.due_date, '0001-01-01')
                        LIMIT 30
                        """
                    ),
                    params,
                )
            ).all()
            payables = (
                await asession.execute(
                    text(
                        """
                        SELECT d.id, COALESCE(i.code, ''), UPPER(d.status),
                               d.due_date, COALESCE(d.amount_due, 0),
                               COALESCE(d.amount_paid, 0),
                               COALESCE(d.amount_remaining, 0),
                               COALESCE(d.overdue_days, 0),
                               COALESCE(d.aging_bucket, '0-30')
                        FROM crm_payable d
                        LEFT JOIN crm_invoice i ON i.id = d.invoice_id
                        WHERE d.partner_id = :pid AND d.is_archived = false
                        ORDER BY COALESCE(d.due_date, '0001-01-01')
                        LIMIT 30
                        """
                    ),
                    params,
                )
            ).all()
            documents = (
                await asession.execute(
                    text(
                        """
                        SELECT dd.id, dd.title, UPPER(dd.kind),
                               COALESCE(dd.reference, ''), dd.issued_on,
                               COALESCE(dd.author, ''), COALESCE(dd.notes, ''),
                               (SELECT GROUP_CONCAT(
                                          COALESCE(NULLIF(dl.label, ''),
                                                   dl.module_route), ' | ')
                                  FROM crm_document_link dl
                                  WHERE dl.document_id = dd.id)
                        FROM crm_document dd
                        WHERE dd.partner_id = :pid AND dd.is_archived = false
                        ORDER BY COALESCE(dd.issued_on, '0001-01-01') DESC,
                                 dd.id DESC
                        LIMIT 40
                        """
                    ),
                    params,
                )
            ).all()
            events = (
                await asession.execute(
                    text(
                        """
                        SELECT e.id, COALESCE(e.icon, 'history'),
                               UPPER(e.kind), COALESCE(e.title, ''),
                               COALESCE(e.summary, ''), e.occurred_on,
                               COALESCE(e.amount, 0),
                               COALESCE(par.name, ''), COALESCE(c.name, ''),
                               h.harvest_date, COALESCE(s.code, ''),
                               COALESCE(a.code, ''), COALESCE(i.code, ''),
                               COALESCE(y.code, '')
                        FROM crm_event e
                        LEFT JOIN parcel par ON par.id = e.parcel_id
                        LEFT JOIN crop c ON c.id = e.crop_id
                        LEFT JOIN harvest h ON h.id = e.harvest_id
                        LEFT JOIN crm_sale s ON s.id = e.sale_id
                        LEFT JOIN crm_purchase a ON a.id = e.purchase_id
                        LEFT JOIN crm_invoice i ON i.id = e.invoice_id
                        LEFT JOIN crm_payment y ON y.id = e.payment_id
                        WHERE e.partner_id = :pid
                        ORDER BY COALESCE(e.occurred_on, '0001-01-01') DESC,
                                 e.id DESC
                        LIMIT 40
                        """
                    ),
                    params,
                )
            ).all()
            score = (
                await asession.execute(
                    text(
                        """
                        SELECT UPPER(sc.kind), UPPER(sc.grade),
                               sc.total_score, sc.volume_score,
                               sc.frequency_score, sc.seniority_score,
                               sc.punctuality_score, sc.profitability_score,
                               sc.growth_score, sc.quality_score,
                               sc.lead_time_score, sc.reliability_score,
                               COALESCE(sc.average_payment_delay_days, 0),
                               COALESCE(sc.turnover_amount, 0),
                               COALESCE(sc.transaction_count, 0),
                               COALESCE(sc.incident_count, 0),
                               sc.computed_on
                        FROM crm_score sc
                        WHERE sc.partner_id = :pid
                        ORDER BY COALESCE(sc.computed_on, '0001-01-01') DESC,
                                 sc.id DESC
                        LIMIT 1
                        """
                    ),
                    params,
                )
            ).first()

        self.detail = {
            "id": _i(row[0]),
            "code": _s(row[1]),
            "name": _s(row[2]),
            "trade_name": _s(row[3]),
            "kind": _s(row[4]).upper(),
            "kind_label": _label(KIND_LABELS, row[4], "Partenaire"),
            "legal_form_label": _label(LEGAL_FORM_LABELS, row[5], "Entreprise"),
            "status": _s(row[6]).upper(),
            "status_label": _label(STATUS_LABELS, row[6], "Actif"),
            "category": _s(row[7]) or "—",
            "segment": _s(row[8]) or "—",
            "supplier_domain": _s(row[9]).replace("_", " ").capitalize(),
            "address": _s(row[10]) or "—",
            "city": _s(row[11]).strip() or "—",
            "country": _s(row[12]) or "—",
            "phone": _s(row[13]) or "—",
            "phone_secondary": _s(row[14]) or "—",
            "whatsapp": _s(row[15]) or "—",
            "email": _s(row[16]) or "—",
            "website": _s(row[17]) or "—",
            "nif": _s(row[18]) or "—",
            "nis": _s(row[19]) or "—",
            "trade_register": _s(row[20]) or "—",
            "tax_id": _s(row[21]) or "—",
            "payment_terms": _s(row[22]) or "—",
            "payment_delay_days": _i(row[23]),
            "credit_limit": _f(row[24]),
            "discount_percent": _f(row[25]),
            "vat_rate": _f(row[26]),
            "currency": _s(row[27]) or "DZD",
            "payment_method": _s(row[28]).capitalize() or "—",
            "primary_contact": _s(row[29]) or "—",
            "primary_contact_role": _s(row[30]) or "—",
            "first_deal": _date(row[31]) or "—",
            "last_activity": _date(row[32]) or "—",
            "notes": _s(row[33]),
            "tags": _s(row[34]),
            "is_archived": bool(row[35]),
            "archive_reason": _s(row[36]),
            "main_parcel": _s(row[37]),
            "main_culture": _s(row[38]),
            "main_product": _s(row[39]),
        }
        turnover = _f(totals[0] if totals else 0)
        purchases_total = _f(totals[1] if totals else 0)
        credit_limit = self.detail["credit_limit"]
        receivable = _f(totals[2] if totals else 0)
        self.stats = {
            "turnover": turnover,
            "purchases": purchases_total,
            "receivable": receivable,
            "receivable_overdue": _f(totals[3] if totals else 0),
            "payable": _f(totals[4] if totals else 0),
            "payable_overdue": _f(totals[5] if totals else 0),
            "received": _f(totals[6] if totals else 0),
            "paid_out": _f(totals[7] if totals else 0),
            "sales_count": _f(totals[8] if totals else 0),
            "purchases_count": _f(totals[9] if totals else 0),
            "invoices_count": _f(totals[10] if totals else 0),
            "documents_count": _f(totals[11] if totals else 0),
            "contacts_count": _f(totals[12] if totals else 0),
            "margin": round(turnover - purchases_total, 2),
            "credit_usage": (
                round(receivable / credit_limit * 100, 1)
                if credit_limit > 0
                else 0.0
            ),
        }
        self.contacts = [
            {
                "id": _i(c[0]),
                "name": _s(c[1]).strip() or "Contact",
                "role": _s(c[2]) or "Fonction non précisée",
                "phone": _s(c[3]) or "—",
                "mobile": _s(c[4]) or "—",
                "email": _s(c[5]) or "—",
                "whatsapp": _s(c[6]) or "—",
                "is_primary": bool(c[7]),
                "notes": _s(c[8]),
            }
            for c in contacts
        ]
        self.sales = [
            {
                "id": _i(s[0]),
                "code": _s(s[1]),
                "label": _s(s[2]) or "Vente",
                "status_label": _s(s[3]).replace("_", " ").capitalize(),
                "date": _date(s[4]) or "—",
                "season": _s(s[5]) or "—",
                "amount": _f(s[6]),
                "paid": _f(s[7]),
                "remaining": round(_f(s[6]) - _f(s[7]), 2),
                "links": _links(
                    [
                        ("Parcelle", _s(s[8])),
                        ("Culture", _s(s[9])),
                        ("Référentiel", _s(s[10])),
                        (
                            "Récolte",
                            (
                                f"{_date(s[11])} · {_f(s[12]):.1f} {_s(s[13])}"
                                if _s(s[11])
                                else ""
                            ),
                        ),
                        ("Produits", _s(s[14])),
                        ("Campagne", _s(s[5])),
                    ]
                ),
            }
            for s in sales
        ]
        self.purchases = [
            {
                "id": _i(a[0]),
                "code": _s(a[1]),
                "label": _s(a[2]) or "Achat",
                "status_label": _s(a[3]).replace("_", " ").capitalize(),
                "date": _date(a[4]) or "—",
                "season": _s(a[5]) or "—",
                "amount": _f(a[6]),
                "paid": _f(a[7]),
                "remaining": round(_f(a[6]) - _f(a[7]), 2),
                "links": _links(
                    [
                        ("Parcelle", _s(a[8])),
                        ("Culture", _s(a[9])),
                        (
                            "Filière",
                            _s(a[10]).replace("_", " ").capitalize(),
                        ),
                        ("Produits", _s(a[11])),
                        ("Campagne", _s(a[5])),
                    ]
                ),
            }
            for a in purchases
        ]
        self.invoices = [
            {
                "id": _i(i[0]),
                "code": _s(i[1]),
                "kind_label": _s(i[2]).replace("_", " ").capitalize(),
                "status_label": _s(i[3]).replace("_", " ").capitalize(),
                "issue_date": _date(i[4]) or "—",
                "due_date": _date(i[5]) or "—",
                "amount": _f(i[6]),
                "paid": _f(i[7]),
                "remaining": _f(i[8]),
                "overdue_days": _i(i[9]),
            }
            for i in invoices
        ]
        self.payments = [
            {
                "id": _i(y[0]),
                "code": _s(y[1]),
                "direction_label": (
                    "Encaissement"
                    if _s(y[2]) == "ENCAISSEMENT"
                    else "Décaissement"
                ),
                "date": _date(y[3]) or "—",
                "amount": _f(y[4]),
                "method": _s(y[5]).capitalize(),
                "reference": _s(y[6]) or "—",
                "invoice_code": _s(y[7]) or "—",
            }
            for y in payments
        ]
        self.receivables = [
            {
                "id": _i(r[0]),
                "invoice_code": _s(r[1]) or "—",
                "status_label": _s(r[2]).replace("_", " ").capitalize(),
                "due_date": _date(r[3]) or "—",
                "amount_due": _f(r[4]),
                "amount_paid": _f(r[5]),
                "remaining": _f(r[6]),
                "overdue_days": _i(r[7]),
                "bucket": _s(r[8]),
            }
            for r in receivables
        ]
        self.payables = [
            {
                "id": _i(d[0]),
                "invoice_code": _s(d[1]) or "—",
                "status_label": _s(d[2]).replace("_", " ").capitalize(),
                "due_date": _date(d[3]) or "—",
                "amount_due": _f(d[4]),
                "amount_paid": _f(d[5]),
                "remaining": _f(d[6]),
                "overdue_days": _i(d[7]),
                "bucket": _s(d[8]),
            }
            for d in payables
        ]
        self.documents = [
            {
                "id": _i(dd[0]),
                "title": _s(dd[1]),
                "kind_label": _s(dd[2]).replace("_", " ").capitalize(),
                "reference": _s(dd[3]) or "—",
                "issued_on": _date(dd[4]) or "—",
                "author": _s(dd[5]) or "—",
                "notes": _s(dd[6]),
                "links": [
                    part.strip()
                    for part in _s(dd[7]).split("|")
                    if part.strip()
                ],
            }
            for dd in documents
        ]
        self.events = [
            {
                "id": _i(e[0]),
                "icon": _s(e[1]) or "history",
                "kind_label": _s(e[2]).replace("_", " ").capitalize(),
                "title": _s(e[3]) or "Événement",
                "summary": _s(e[4]),
                "date": _date(e[5]) or "—",
                "amount": _f(e[6]),
                "links": _links(
                    [
                        ("Parcelle", _s(e[7])),
                        ("Culture", _s(e[8])),
                        ("Récolte", _date(e[9])),
                        ("Vente", _s(e[10])),
                        ("Achat", _s(e[11])),
                        ("Facture", _s(e[12])),
                        ("Paiement", _s(e[13])),
                    ]
                ),
            }
            for e in events
        ]
        if score is None:
            self.score = EMPTY_SCORE
        else:
            self.score = {
                "kind_label": _s(score[0]).capitalize(),
                "grade_label": _label(GRADE_LABELS, score[1], "Moyen"),
                "total": _i(score[2]),
                "volume": _i(score[3]),
                "frequency": _i(score[4]),
                "seniority": _i(score[5]),
                "punctuality": _i(score[6]),
                "profitability": _i(score[7]),
                "growth": _i(score[8]),
                "quality": _i(score[9]),
                "lead_time": _i(score[10]),
                "reliability": _i(score[11]),
                "average_delay": _f(score[12]),
                "turnover": _f(score[13]),
                "transactions": _i(score[14]),
                "incidents": _i(score[15]),
                "computed_on": _date(score[16]) or "—",
            }

    # ------------------------------------------------------------------
    # Écritures
    # ------------------------------------------------------------------

    async def _next_code(self, kind: str) -> str:
        prefix = CODE_PREFIXES.get(kind.upper(), "PRT")
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        "SELECT code FROM crm_partner WHERE code LIKE :pattern"
                    ),
                    {"pattern": f"{prefix}-%"},
                )
            ).all()
        highest = 0
        for row in rows:
            tail = _s(row[0]).rsplit("-", 1)[-1]
            if tail.isdigit():
                highest = max(highest, int(tail))
        return f"{prefix}-{highest + 1:04d}"

    async def _record_event(
        self,
        partner_id: int,
        *,
        kind: str,
        title: str,
        summary: str,
        icon: str,
        amount: float = 0.0,
    ) -> None:
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    INSERT INTO crm_event (partner_id, kind, title, summary,
                        occurred_on, amount, author, module_route, icon)
                    VALUES (:pid, :kind, :title, :summary, :day, :amount,
                        'Interface CRM', '/crm', :icon)
                    """
                ),
                {
                    "pid": partner_id,
                    "kind": kind,
                    "title": title,
                    "summary": summary,
                    "day": datetime.date.today(),
                    "amount": amount,
                    "icon": icon,
                },
            )
            await asession.execute(
                text(
                    """
                    INSERT INTO crm_audit_log (partner_id, actor_label, action,
                        entity_type, entity_id, entity_ref, field_name,
                        old_value, new_value, summary, module_route,
                        ip_address, is_sensitive, occurred_at)
                    VALUES (:pid, 'Interface CRM', :action, 'crm_partner',
                        :pid, :ref, '', '', '', :summary, '/crm', '', false,
                        :now)
                    """
                ),
                {
                    "pid": partner_id,
                    "action": kind.lower(),
                    "ref": title,
                    "summary": summary,
                    "now": datetime.datetime.now(),
                },
            )
            await asession.commit()

    def _validate(self, data: dict) -> str:
        name = _s(data.get("legal_name")).strip()
        if not name:
            return "La raison sociale est obligatoire."
        email = _s(data.get("email")).strip()
        if email and "@" not in email:
            return "L'adresse e-mail saisie est invalide."
        nif = _s(data.get("nif")).strip()
        if nif and (not nif.isdigit() or len(nif) < 8):
            return "Le NIF doit comporter au moins 8 chiffres."
        delay = _s(data.get("payment_delay_days")).strip()
        if delay and not delay.replace("-", "").isdigit():
            return "Le délai de paiement doit être un nombre de jours."
        return ""

    def _partner_params(self, data: dict) -> dict[str, object]:
        return {
            "legal_name": _s(data.get("legal_name")).strip(),
            "trade_name": _s(data.get("trade_name")).strip(),
            "kind": _s(data.get("kind")).upper() or "CLIENT",
            "legal_form": _s(data.get("legal_form")).upper() or "ENTREPRISE",
            "status": _s(data.get("status")).upper() or "ACTIF",
            "category": _s(data.get("category")).strip(),
            "segment": _s(data.get("segment")).strip(),
            "supplier_domain": (
                _s(data.get("supplier_domain")).upper() or "AUTRE"
            ),
            "address": _s(data.get("address")).strip(),
            "wilaya": _s(data.get("wilaya")).strip(),
            "commune": _s(data.get("commune")).strip(),
            "postal_code": _s(data.get("postal_code")).strip(),
            "country": _s(data.get("country")).strip() or "Algérie",
            "phone": _s(data.get("phone")).strip(),
            "phone_secondary": _s(data.get("phone_secondary")).strip(),
            "whatsapp": _s(data.get("whatsapp")).strip(),
            "email": _s(data.get("email")).strip(),
            "website": _s(data.get("website")).strip(),
            "nif": _s(data.get("nif")).strip(),
            "nis": _s(data.get("nis")).strip(),
            "trade_register": _s(data.get("trade_register")).strip(),
            "tax_id": _s(data.get("tax_id")).strip(),
            "payment_terms": _s(data.get("payment_terms")).strip(),
            "payment_delay_days": _i(
                _s(data.get("payment_delay_days")).strip() or 30
            ),
            "credit_limit": _f(_s(data.get("credit_limit")).strip() or 0),
            "default_discount_percent": _f(
                _s(data.get("default_discount_percent")).strip() or 0
            ),
            "default_vat_rate": _f(
                _s(data.get("default_vat_rate")).strip() or 19
            ),
            "currency": _s(data.get("currency")).strip() or "DZD",
            "preferred_payment_method": (
                _s(data.get("preferred_payment_method")).upper() or "VIREMENT"
            ),
            "primary_contact_name": _s(
                data.get("primary_contact_name")
            ).strip(),
            "primary_contact_role": _s(
                data.get("primary_contact_role")
            ).strip(),
            "tags": _s(data.get("tags")).strip(),
            "notes": _s(data.get("notes")).strip(),
        }

    # ------------------------------------------------------------------
    # Événements de navigation et filtres
    # ------------------------------------------------------------------

    @rx.event
    async def enter_space(self, space: str):
        self.space = space if space in SPACE_TITLES else "partenaires"
        self.kind_filter = ""
        self.status_filter = ""
        self.selected_id = 0
        yield CrmPartnersState.load_space

    @rx.event
    async def load_space(self):
        self.is_loading = True
        yield
        await ensure_local_database()
        await ensure_crm_tables()
        await asyncio.to_thread(seed_crm_if_empty)
        await self._fetch_partners()
        if self.selected_id == 0 and self.partners:
            self.selected_id = self.partners[0]["id"]
        await self._fetch_detail()
        self.is_loading = False

    @rx.event
    async def refresh(self):
        await self._fetch_partners()
        await self._fetch_detail()

    @rx.event
    async def set_kind_filter(self, value: str):
        self.kind_filter = value
        await self._fetch_partners()

    @rx.event
    async def set_status_filter(self, value: str):
        self.status_filter = value
        await self._fetch_partners()

    @rx.event
    async def set_search(self, value: str):
        self.search = value
        await self._fetch_partners()

    @rx.event
    async def toggle_archived(self):
        self.include_archived = not self.include_archived
        await self._fetch_partners()

    @rx.event
    async def clear_filters(self):
        self.kind_filter = ""
        self.status_filter = ""
        self.search = ""
        self.include_archived = False
        await self._fetch_partners()

    @rx.event
    async def select_partner(self, partner_id: int):
        self.selected_id = partner_id
        self.detail_tab = "identite"
        await self._fetch_detail()

    @rx.event
    def set_detail_tab(self, value: str):
        self.detail_tab = value

    # ------------------------------------------------------------------
    # Formulaire tiers
    # ------------------------------------------------------------------

    @rx.event
    def open_create(self):
        default_kind = {
            "clients": "CLIENT",
            "fournisseurs": "FOURNISSEUR",
        }.get(self.space, "MIXTE")
        self.form = {**EMPTY_FORM, "kind": default_kind}
        self.form_mode = "create"
        self.form_error = ""
        self.form_open = True

    @rx.event
    async def open_edit(self):
        if self.selected_id <= 0:
            return rx.toast("Sélectionnez d'abord un tiers.")
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT legal_name, COALESCE(trade_name, ''),
                               UPPER(kind), UPPER(legal_form), UPPER(status),
                               COALESCE(category, ''), COALESCE(segment, ''),
                               UPPER(COALESCE(supplier_domain, 'AUTRE')),
                               COALESCE(address, ''), COALESCE(wilaya, ''),
                               COALESCE(commune, ''),
                               COALESCE(postal_code, ''),
                               COALESCE(country, ''), COALESCE(phone, ''),
                               COALESCE(phone_secondary, ''),
                               COALESCE(whatsapp, ''), COALESCE(email, ''),
                               COALESCE(website, ''), COALESCE(nif, ''),
                               COALESCE(nis, ''),
                               COALESCE(trade_register, ''),
                               COALESCE(tax_id, ''),
                               COALESCE(payment_terms, ''),
                               COALESCE(payment_delay_days, 30),
                               COALESCE(credit_limit, 0),
                               COALESCE(default_discount_percent, 0),
                               COALESCE(default_vat_rate, 19),
                               COALESCE(currency, 'DZD'),
                               UPPER(COALESCE(preferred_payment_method,
                                              'VIREMENT')),
                               COALESCE(primary_contact_name, ''),
                               COALESCE(primary_contact_role, ''),
                               COALESCE(tags, ''), COALESCE(notes, '')
                        FROM crm_partner WHERE id = :pid
                        """
                    ),
                    {"pid": self.selected_id},
                )
            ).first()
        if row is None:
            return rx.toast("Tiers introuvable.")
        self.form = {
            "legal_name": _s(row[0]),
            "trade_name": _s(row[1]),
            "kind": _s(row[2]),
            "legal_form": _s(row[3]),
            "status": _s(row[4]),
            "category": _s(row[5]),
            "segment": _s(row[6]),
            "supplier_domain": _s(row[7]),
            "address": _s(row[8]),
            "wilaya": _s(row[9]),
            "commune": _s(row[10]),
            "postal_code": _s(row[11]),
            "country": _s(row[12]),
            "phone": _s(row[13]),
            "phone_secondary": _s(row[14]),
            "whatsapp": _s(row[15]),
            "email": _s(row[16]),
            "website": _s(row[17]),
            "nif": _s(row[18]),
            "nis": _s(row[19]),
            "trade_register": _s(row[20]),
            "tax_id": _s(row[21]),
            "payment_terms": _s(row[22]),
            "payment_delay_days": str(_i(row[23])),
            "credit_limit": f"{_f(row[24]):.2f}",
            "default_discount_percent": f"{_f(row[25]):.2f}",
            "default_vat_rate": f"{_f(row[26]):.2f}",
            "currency": _s(row[27]),
            "preferred_payment_method": _s(row[28]),
            "primary_contact_name": _s(row[29]),
            "primary_contact_role": _s(row[30]),
            "tags": _s(row[31]),
            "notes": _s(row[32]),
        }
        self.form_mode = "edit"
        self.form_error = ""
        self.form_open = True

    @rx.event
    def close_form(self):
        self.form_open = False
        self.form_error = ""

    @rx.event
    async def save_partner(self, form_data: dict):
        error = self._validate(form_data)
        if error:
            self.form_error = error
            return
        params = self._partner_params(form_data)
        self.is_saving = True
        yield
        if self.form_mode == "create":
            async with rx.asession() as asession:
                duplicate = (
                    await asession.execute(
                        text(
                            """
                            SELECT id FROM crm_partner
                            WHERE LOWER(legal_name) = :name
                               OR (:email <> '' AND LOWER(email) = :email)
                            LIMIT 1
                            """
                        ),
                        {
                            "name": params["legal_name"].lower(),
                            "email": str(params["email"]).lower(),
                        },
                    )
                ).first()
            if duplicate is not None:
                self.form_error = (
                    "Un tiers portant ce nom ou cet e-mail existe déjà."
                )
                self.is_saving = False
                return
            code = await self._next_code(params["kind"])
            params["code"] = code
            async with rx.asession() as asession:
                await asession.execute(
                    text(
                        """
                        INSERT INTO crm_partner (
                            code, legal_name, kind, legal_form, status,
                            trade_name, tax_id, trade_register, nif, nis,
                            address, wilaya, commune, postal_code, country,
                            phone, phone_secondary, whatsapp, email, website,
                            latitude, longitude, category, segment,
                            supplier_domain, payment_terms, payment_delay_days,
                            credit_limit, default_discount_percent,
                            default_vat_rate, currency,
                            preferred_payment_method, primary_contact_name,
                            primary_contact_role, score_value, is_archived,
                            archive_reason, tags, notes
                        ) VALUES (
                            :code, :legal_name, :kind, :legal_form, :status,
                            :trade_name, :tax_id, :trade_register, :nif, :nis,
                            :address, :wilaya, :commune, :postal_code,
                            :country, :phone, :phone_secondary, :whatsapp,
                            :email, :website, 0, 0, :category, :segment,
                            :supplier_domain, :payment_terms,
                            :payment_delay_days, :credit_limit,
                            :default_discount_percent, :default_vat_rate,
                            :currency, :preferred_payment_method,
                            :primary_contact_name, :primary_contact_role,
                            0, false, '', :tags, :notes
                        )
                        """
                    ),
                    params,
                )
                await asession.commit()
                created = (
                    await asession.execute(
                        text("SELECT id FROM crm_partner WHERE code = :code"),
                        {"code": code},
                    )
                ).first()
            new_id = _i(created[0]) if created else 0
            if new_id:
                await self._record_event(
                    new_id,
                    kind="CREATION",
                    title=f"Création du tiers {code}",
                    summary=(
                        f"{params['legal_name']} enregistré comme"
                        f" {_label(KIND_LABELS, params['kind'], 'partenaire')}."
                    ),
                    icon="user-round-plus",
                )
                self.selected_id = new_id
            message = f"Tiers {code} créé."
        else:
            params["pid"] = self.selected_id
            async with rx.asession() as asession:
                await asession.execute(
                    text(
                        """
                        UPDATE crm_partner SET
                            legal_name = :legal_name, kind = :kind,
                            legal_form = :legal_form, status = :status,
                            trade_name = :trade_name, tax_id = :tax_id,
                            trade_register = :trade_register, nif = :nif,
                            nis = :nis, address = :address, wilaya = :wilaya,
                            commune = :commune, postal_code = :postal_code,
                            country = :country, phone = :phone,
                            phone_secondary = :phone_secondary,
                            whatsapp = :whatsapp, email = :email,
                            website = :website, category = :category,
                            segment = :segment,
                            supplier_domain = :supplier_domain,
                            payment_terms = :payment_terms,
                            payment_delay_days = :payment_delay_days,
                            credit_limit = :credit_limit,
                            default_discount_percent =
                                :default_discount_percent,
                            default_vat_rate = :default_vat_rate,
                            currency = :currency,
                            preferred_payment_method =
                                :preferred_payment_method,
                            primary_contact_name = :primary_contact_name,
                            primary_contact_role = :primary_contact_role,
                            tags = :tags, notes = :notes
                        WHERE id = :pid
                        """
                    ),
                    params,
                )
                await asession.commit()
            await self._record_event(
                self.selected_id,
                kind="MISE_A_JOUR",
                title=f"Fiche mise à jour : {params['legal_name']}",
                summary="Modification des informations du tiers.",
                icon="pencil",
            )
            message = "Fiche du tiers mise à jour."
        self.form_open = False
        self.form_error = ""
        await self._fetch_partners()
        await self._fetch_detail()
        self.is_saving = False
        yield rx.toast(message)

    # ------------------------------------------------------------------
    # Archivage / réactivation
    # ------------------------------------------------------------------

    @rx.event
    async def archive_partner(self):
        if self.selected_id <= 0:
            return rx.toast("Sélectionnez d'abord un tiers.")
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE crm_partner
                    SET is_archived = true, status = 'ARCHIVE',
                        archived_on = :day,
                        archive_reason = 'Archivé depuis l''espace CRM'
                    WHERE id = :pid
                    """
                ),
                {"pid": self.selected_id, "day": datetime.date.today()},
            )
            await asession.commit()
        await self._record_event(
            self.selected_id,
            kind="ARCHIVAGE",
            title="Tiers archivé",
            summary=(
                "Archivage au lieu d'une suppression : l'historique des"
                " transactions reste intact."
            ),
            icon="archive",
        )
        await self._fetch_partners()
        await self._fetch_detail()
        return rx.toast("Tiers archivé (aucune donnée supprimée).")

    @rx.event
    async def restore_partner(self):
        if self.selected_id <= 0:
            return
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE crm_partner
                    SET is_archived = false, status = 'ACTIF',
                        archived_on = NULL, archive_reason = ''
                    WHERE id = :pid
                    """
                ),
                {"pid": self.selected_id},
            )
            await asession.commit()
        await self._record_event(
            self.selected_id,
            kind="MISE_A_JOUR",
            title="Tiers réactivé",
            summary="Le tiers est de nouveau actif dans le CRM.",
            icon="rotate-ccw",
        )
        await self._fetch_partners()
        await self._fetch_detail()
        return rx.toast("Tiers réactivé.")

    # ------------------------------------------------------------------
    # Contacts
    # ------------------------------------------------------------------

    @rx.event
    def open_contact_create(self):
        self.contact_form = dict(EMPTY_CONTACT_FORM)
        self.contact_form_mode = "create"
        self.contact_id = 0
        self.contact_form_open = True

    @rx.event
    async def open_contact_edit(self, contact_id: int):
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT last_name, COALESCE(first_name, ''),
                               COALESCE(role, ''), COALESCE(phone, ''),
                               COALESCE(mobile, ''), COALESCE(whatsapp, ''),
                               COALESCE(email, ''), COALESCE(language, ''),
                               is_primary, COALESCE(notes, '')
                        FROM crm_contact WHERE id = :cid
                        """
                    ),
                    {"cid": contact_id},
                )
            ).first()
        if row is None:
            return rx.toast("Contact introuvable.")
        self.contact_form = {
            "last_name": _s(row[0]),
            "first_name": _s(row[1]),
            "role": _s(row[2]),
            "phone": _s(row[3]),
            "mobile": _s(row[4]),
            "whatsapp": _s(row[5]),
            "email": _s(row[6]),
            "language": _s(row[7]),
            "is_primary": "on" if row[8] else "",
            "notes": _s(row[9]),
        }
        self.contact_id = contact_id
        self.contact_form_mode = "edit"
        self.contact_form_open = True

    @rx.event
    def close_contact_form(self):
        self.contact_form_open = False

    @rx.event
    async def save_contact(self, form_data: dict):
        if self.selected_id <= 0:
            return rx.toast("Sélectionnez d'abord un tiers.")
        last_name = _s(form_data.get("last_name")).strip()
        if not last_name:
            return rx.toast("Le nom du contact est obligatoire.")
        is_primary = bool(form_data.get("is_primary"))
        params = {
            "pid": self.selected_id,
            "cid": self.contact_id,
            "last_name": last_name,
            "first_name": _s(form_data.get("first_name")).strip(),
            "role": _s(form_data.get("role")).strip(),
            "phone": _s(form_data.get("phone")).strip(),
            "mobile": _s(form_data.get("mobile")).strip(),
            "whatsapp": _s(form_data.get("whatsapp")).strip(),
            "email": _s(form_data.get("email")).strip(),
            "language": _s(form_data.get("language")).strip(),
            "is_primary": is_primary,
            "notes": _s(form_data.get("notes")).strip(),
        }
        async with rx.asession() as asession:
            if is_primary:
                # Un seul contact principal par tiers : on libère la place.
                await asession.execute(
                    text(
                        "UPDATE crm_contact SET is_primary = false"
                        " WHERE partner_id = :pid"
                    ),
                    {"pid": self.selected_id},
                )
            if self.contact_form_mode == "create":
                await asession.execute(
                    text(
                        """
                        INSERT INTO crm_contact (partner_id, last_name,
                            first_name, role, phone, mobile, whatsapp, email,
                            is_primary, is_archived, language, notes)
                        VALUES (:pid, :last_name, :first_name, :role, :phone,
                            :mobile, :whatsapp, :email, :is_primary, false,
                            :language, :notes)
                        """
                    ),
                    params,
                )
            else:
                await asession.execute(
                    text(
                        """
                        UPDATE crm_contact SET last_name = :last_name,
                            first_name = :first_name, role = :role,
                            phone = :phone, mobile = :mobile,
                            whatsapp = :whatsapp, email = :email,
                            is_primary = :is_primary, language = :language,
                            notes = :notes
                        WHERE id = :cid
                        """
                    ),
                    params,
                )
            await asession.commit()
        await self._sync_primary_contact()
        await self._record_event(
            self.selected_id,
            kind="CONTACT",
            title=f"Contact {last_name} enregistré",
            summary=f"Fonction : {params['role'] or 'non précisée'}.",
            icon="user-round",
        )
        self.contact_form_open = False
        await self._fetch_detail()
        return rx.toast("Contact enregistré.")

    @rx.event
    async def set_primary_contact(self, contact_id: int):
        if self.selected_id <= 0:
            return
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE crm_contact
                    SET is_primary = CASE WHEN id = :cid THEN true
                                          ELSE false END
                    WHERE partner_id = :pid
                    """
                ),
                {"cid": contact_id, "pid": self.selected_id},
            )
            await asession.commit()
        await self._sync_primary_contact()
        await self._fetch_detail()
        return rx.toast("Contact principal mis à jour.")

    @rx.event
    async def archive_contact(self, contact_id: int):
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    "UPDATE crm_contact SET is_archived = true,"
                    " is_primary = false WHERE id = :cid"
                ),
                {"cid": contact_id},
            )
            await asession.commit()
        await self._fetch_detail()
        return rx.toast("Contact archivé.")

    async def _sync_primary_contact(self) -> None:
        """Recopie le contact principal sur la fiche du tiers."""
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT TRIM(COALESCE(first_name, '') || ' '
                                    || last_name), COALESCE(role, '')
                        FROM crm_contact
                        WHERE partner_id = :pid AND is_archived = false
                        ORDER BY is_primary DESC, id
                        LIMIT 1
                        """
                    ),
                    {"pid": self.selected_id},
                )
            ).first()
            await asession.execute(
                text(
                    """
                    UPDATE crm_partner
                    SET primary_contact_name = :name,
                        primary_contact_role = :role
                    WHERE id = :pid
                    """
                ),
                {
                    "pid": self.selected_id,
                    "name": _s(row[0]).strip() if row else "",
                    "role": _s(row[1]) if row else "",
                },
            )
            await asession.commit()

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    @rx.event
    def open_document_form(self):
        self.document_form = dict(EMPTY_DOCUMENT_FORM)
        self.document_form_open = True

    @rx.event
    def close_document_form(self):
        self.document_form_open = False

    @rx.event
    async def save_document(self, form_data: dict):
        if self.selected_id <= 0:
            return rx.toast("Sélectionnez d'abord un tiers.")
        title = _s(form_data.get("title")).strip()
        if not title:
            return rx.toast("Le titre du document est obligatoire.")
        params = {
            "pid": self.selected_id,
            "title": title,
            "kind": _s(form_data.get("kind")).upper() or "AUTRE",
            "reference": _s(form_data.get("reference")).strip(),
            "author": _s(form_data.get("author")).strip(),
            "notes": _s(form_data.get("notes")).strip(),
            "day": datetime.date.today(),
        }
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    INSERT INTO crm_document (partner_id, title, kind,
                        filename, mime_type, size_kb, reference, issued_on,
                        author, is_confidential, is_archived, tags, notes)
                    VALUES (:pid, :title, :kind, '', '', 0, :reference, :day,
                        :author, false, false, '', :notes)
                    """
                ),
                params,
            )
            await asession.commit()
        await self._record_event(
            self.selected_id,
            kind="DOCUMENT",
            title=f"Document ajouté : {title}",
            summary=params["reference"] or "Document classé dans la fiche.",
            icon="folder-plus",
        )
        self.document_form_open = False
        await self._fetch_detail()
        return rx.toast("Document enregistré.")

    @rx.event
    async def archive_document(self, document_id: int):
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    "UPDATE crm_document SET is_archived = true WHERE id = :did"
                ),
                {"did": document_id},
            )
            await asession.commit()
        await self._fetch_detail()
        return rx.toast("Document archivé.")

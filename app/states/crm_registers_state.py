"""Registres financiers CRM : Ventes, Achats, Créances, Dettes, Paiements,
Rapports.

Toutes les lectures et écritures passent par `rx.asession()` en SQL brut
paramétré sur les tables CRM déjà créées (`crm_sale`, `crm_purchase`,
`crm_invoice`, `crm_payment`, `crm_receivable`, `crm_payable`, `crm_event`,
`crm_audit_log`). Aucune modification de schéma n'est faite : les montants
HT / TVA / TTC, le restant dû et les retards sont calculés à l'écriture puis
persistés dans les colonnes existantes.

Règles métier appliquées :
- archivage plutôt que suppression (colonne `is_archived`) ;
- une pièce déjà réglée ne peut pas être archivée ;
- un tiers bloqué ou archivé ne peut pas porter de nouvelle opération ;
- un règlement ne peut jamais dépasser le restant dû de la facture ;
- chaque écriture est journalisée (`crm_event` + `crm_audit_log`).
"""

from __future__ import annotations

import asyncio
import datetime
import logging
from typing import Any, TypedDict

import reflex as rx
from sqlalchemy import text

from app.database import ensure_crm_tables, ensure_local_database
from app.exports import to_csv
from app.seed_crm import seed_crm_if_empty
from app.states.crm_state import MONTHS, _month_keys, _month_label

REGISTERS: list[str] = [
    "ventes",
    "achats",
    "creances",
    "dettes",
    "paiements",
    "rapports",
]

REGISTER_TABLES: dict[str, str] = {
    "ventes": "crm_sale",
    "achats": "crm_purchase",
    "creances": "crm_receivable",
    "dettes": "crm_payable",
    "paiements": "crm_payment",
}

REGISTER_TITLES: dict[str, str] = {
    "ventes": "Registre des ventes",
    "achats": "Registre des achats",
    "creances": "Créances clients",
    "dettes": "Dettes fournisseurs",
    "paiements": "Registre des paiements",
    "rapports": "Rapports commerciaux",
}

REGISTER_SUBTITLES: dict[str, str] = {
    "ventes": (
        "Ventes aux clients avec montants HT, TVA, TTC, encaissements et"
        " restant dû calculés automatiquement."
    ),
    "achats": (
        "Achats d'intrants, de matériel et de services auprès des"
        " fournisseurs, ventilés par filière."
    ),
    "creances": (
        "Balance âgée des créances clients : échéances, retards et tranches"
        " de vieillissement."
    ),
    "dettes": (
        "Dettes fournisseurs à régler : échéances, retards et tranches de"
        " vieillissement."
    ),
    "paiements": (
        "Registre centralisé des encaissements et des décaissements,"
        " rattachés aux factures."
    ),
    "rapports": (
        "Synthèses financières de la campagne : cadence mensuelle, marge,"
        " balance des tiers et exports."
    ),
}

SALE_STATUSES: list[str] = [
    "BROUILLON",
    "CONFIRMEE",
    "PREPAREE",
    "LIVREE",
    "FACTUREE",
    "PARTIELLEMENT_PAYEE",
    "PAYEE",
    "ANNULEE",
]

PURCHASE_STATUSES: list[str] = [
    "BROUILLON",
    "COMMANDEE",
    "RECEPTIONNEE",
    "FACTUREE",
    "PARTIELLEMENT_PAYEE",
    "PAYEE",
    "ANNULEE",
]

SETTLEMENT_STATUSES: list[str] = [
    "OUVERTE",
    "PARTIELLE",
    "REGLEE",
    "EN_RETARD",
    "LITIGE",
    "IRRECOUVRABLE",
]

PAYMENT_DIRECTIONS: list[str] = ["ENCAISSEMENT", "DECAISSEMENT"]

PAYMENT_METHODS: list[str] = [
    "VIREMENT",
    "CHEQUE",
    "ESPECES",
    "CARTE",
    "PRELEVEMENT",
    "AUTRE",
]

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

AGING_BUCKETS: list[str] = ["0-30", "31-60", "61-90", "90+"]

LABELS: dict[str, str] = {
    "BROUILLON": "Brouillon",
    "CONFIRMEE": "Confirmée",
    "PREPAREE": "Préparée",
    "LIVREE": "Livrée",
    "FACTUREE": "Facturée",
    "PARTIELLEMENT_PAYEE": "Partiellement payée",
    "PAYEE": "Payée",
    "ANNULEE": "Annulée",
    "COMMANDEE": "Commandée",
    "RECEPTIONNEE": "Réceptionnée",
    "OUVERTE": "Ouverte",
    "PARTIELLE": "Partielle",
    "REGLEE": "Réglée",
    "EN_RETARD": "En retard",
    "LITIGE": "En litige",
    "IRRECOUVRABLE": "Irrécouvrable",
    "EMISE": "Émise",
    "ENCAISSEMENT": "Encaissement",
    "DECAISSEMENT": "Décaissement",
    "VIREMENT": "Virement",
    "CHEQUE": "Chèque",
    "ESPECES": "Espèces",
    "CARTE": "Carte",
    "PRELEVEMENT": "Prélèvement",
    "AUTRE": "Autre",
    "SEMENCES": "Semences",
    "ENGRAIS": "Engrais",
    "PHYTOSANITAIRE": "Phytosanitaire",
    "MATERIEL": "Matériel",
    "PIECES": "Pièces détachées",
    "CARBURANT": "Carburant",
    "IRRIGATION": "Irrigation",
    "EMBALLAGE": "Emballage",
    "TRANSPORT": "Transport",
    "SERVICES": "Services",
    "MAINTENANCE": "Maintenance",
    "ENERGIE": "Énergie",
}

GOOD_STATUSES = {"PAYEE", "REGLEE", "LIVREE"}
BAD_STATUSES = {"EN_RETARD", "LITIGE", "IRRECOUVRABLE", "ANNULEE"}
WARN_STATUSES = {"PARTIELLEMENT_PAYEE", "PARTIELLE", "OUVERTE", "BROUILLON"}

PERIODS: list[tuple[str, str]] = [
    ("all", "Toute la période"),
    ("today", "Aujourd'hui"),
    ("week", "Cette semaine"),
    ("month", "Ce mois"),
    ("season", "Campagne en cours"),
    ("late", "En retard"),
    ("d30", "Retard 30 jours et +"),
    ("d60", "Retard 60 jours et +"),
    ("d90", "Retard 90 jours et +"),
]


class BusinessError(Exception):
    """Erreur de validation métier destinée à l'utilisateur."""


class RegisterRow(TypedDict):
    id: int
    code: str
    date: str
    partner_id: int
    partner: str
    title: str
    reference: str
    status: str
    status_label: str
    tone: str
    type_label: str
    amount_ht: float
    vat_amount: float
    amount_ttc: float
    paid: float
    remaining: float
    due_date: str
    overdue_days: int
    is_archived: bool
    links: list[str]


class ReportMonth(TypedDict):
    key: str
    label: str
    sales: float
    purchases: float
    margin: float
    sales_width: str
    purchases_width: str


class ReportPartner(TypedDict):
    id: int
    name: str
    kind_label: str
    sales: float
    purchases: float
    receivable: float
    payable: float
    margin: float


class OptionRow(TypedDict):
    id: int
    label: str
    kind: str
    remaining: float


EMPTY_TOTALS: dict[str, float] = {
    "count": 0.0,
    "amount_ht": 0.0,
    "vat_amount": 0.0,
    "amount_ttc": 0.0,
    "paid": 0.0,
    "remaining": 0.0,
    "overdue_count": 0.0,
    "overdue_amount": 0.0,
    "archived": 0.0,
}

EMPTY_REPORT: dict[str, float] = {
    "sales": 0.0,
    "purchases": 0.0,
    "margin": 0.0,
    "margin_rate": 0.0,
    "receivable": 0.0,
    "payable": 0.0,
    "received": 0.0,
    "paid_out": 0.0,
    "net_cash": 0.0,
    "sales_count": 0.0,
    "purchases_count": 0.0,
    "late_receivable": 0.0,
    "late_payable": 0.0,
}

EMPTY_FORM: dict[str, str] = {
    "partner_id": "",
    "operation_date": "",
    "label": "",
    "season": "",
    "quantity": "1",
    "unit": "t",
    "unit_price": "0",
    "discount_percent": "0",
    "vat_rate": "19",
    "payment_method": "VIREMENT",
    "status": "CONFIRMEE",
    "domain": "AUTRE",
    "direction": "ENCAISSEMENT",
    "invoice_id": "",
    "amount": "0",
    "reference": "",
    "bank": "",
    "notes": "",
}


def _s(value: object) -> str:
    return "" if value is None else str(value)


def _f(value: object) -> float:
    if value is None:
        return 0.0
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return 0.0


def _i(value: object) -> int:
    if value is None:
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _date(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime.date):
        return value.isoformat()
    return str(value)[:10]


def _label(value: object) -> str:
    key = _s(value).upper()
    return LABELS.get(key, key.replace("_", " ").capitalize() or "—")


def _tone(status: str, overdue: int, remaining: float) -> str:
    key = status.upper()
    if key in BAD_STATUSES or overdue > 0:
        return "bad"
    if key in GOOD_STATUSES and remaining <= 0.005:
        return "good"
    if key in WARN_STATUSES:
        return "warn"
    return "info"


def _season_start(today: datetime.date) -> datetime.date:
    return (
        today.replace(month=9, day=1)
        if today.month >= 9
        else today.replace(year=today.year - 1, month=9, day=1)
    )


def _season_end(start: datetime.date) -> datetime.date:
    """Dernier jour de la campagne agricole ouverte le 1er septembre."""
    return start.replace(year=start.year + 1, month=8, day=31)


def _season_label(start: datetime.date) -> str:
    return f"{start.year}/{start.year + 1}"


REPORT_SCOPES: dict[str, str] = {
    "season_current": "Campagne en cours",
    "season_last": "Dernière campagne disponible",
    "history": "Historique CRM complet",
    "empty": "Aucune donnée commerciale",
}


def _links(*values: object) -> list[str]:
    return [_s(value).strip() for value in values if _s(value).strip()]


def _amounts(data: dict) -> tuple[float, float, float]:
    """Calcule HT, TVA et TTC à partir de la ligne saisie."""
    quantity = _f(data.get("quantity"))
    price = _f(data.get("unit_price"))
    discount = _f(data.get("discount_percent"))
    vat = _f(data.get("vat_rate"))
    ht = round(quantity * price * (1 - discount / 100), 2)
    vat_amount = round(ht * vat / 100, 2)
    return ht, vat_amount, round(ht + vat_amount, 2)


def _bucket(overdue: int) -> str:
    if overdue <= 30:
        return "0-30"
    if overdue <= 60:
        return "31-60"
    if overdue <= 90:
        return "61-90"
    return "90+"


class CrmRegistersState(rx.State):
    """Registres Ventes / Achats / Créances / Dettes / Paiements / Rapports."""

    is_loading: bool = True
    is_saving: bool = False
    register: str = "ventes"
    search: str = ""
    status_filter: str = ""
    type_filter: str = ""
    period: str = "all"
    include_archived: bool = False

    rows: list[RegisterRow] = []
    totals: dict[str, float] = EMPTY_TOTALS
    report: dict[str, float] = EMPTY_REPORT
    report_months: list[ReportMonth] = []
    report_partners: list[ReportPartner] = []
    report_text: str = ""
    report_scope: str = "season_current"
    report_scope_label: str = REPORT_SCOPES["season_current"]
    report_period_label: str = ""
    report_from: str = ""
    report_to: str = ""
    report_is_fallback: bool = False

    partner_options: list[OptionRow] = []
    invoice_options: list[OptionRow] = []

    form_open: bool = False
    form_kind: str = "sale"
    form_error: str = ""
    form: dict[str, str] = EMPTY_FORM

    periods: list[list[str]] = [[key, label] for key, label in PERIODS]

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def register_title(self) -> str:
        return REGISTER_TITLES.get(self.register, "Registre CRM")

    @rx.var
    def register_subtitle(self) -> str:
        return REGISTER_SUBTITLES.get(self.register, "")

    @rx.var
    def row_count(self) -> int:
        return len(self.rows)

    @rx.var
    def is_report(self) -> bool:
        return self.register == "rapports"

    @rx.var
    def is_settlement(self) -> bool:
        return self.register in ("creances", "dettes")

    @rx.var
    def amount_header(self) -> str:
        if self.register in ("creances", "dettes"):
            return "Dû"
        if self.register == "paiements":
            return "Montant"
        return "HT"

    @rx.var
    def status_options(self) -> list[str]:
        if self.register == "ventes":
            return SALE_STATUSES
        if self.register == "achats":
            return PURCHASE_STATUSES
        if self.register in ("creances", "dettes"):
            return SETTLEMENT_STATUSES
        if self.register == "paiements":
            return PAYMENT_DIRECTIONS
        return []

    @rx.var
    def status_filter_label(self) -> str:
        return "Sens" if self.register == "paiements" else "Statut"

    @rx.var
    def type_options(self) -> list[str]:
        if self.register == "achats":
            return SUPPLIER_DOMAINS
        if self.register in ("creances", "dettes"):
            return AGING_BUCKETS
        if self.register in ("ventes", "paiements"):
            return PAYMENT_METHODS
        return []

    @rx.var
    def type_filter_label(self) -> str:
        if self.register == "achats":
            return "Filière"
        if self.register in ("creances", "dettes"):
            return "Tranche d'âge"
        return "Mode de règlement"

    @rx.var
    def method_options(self) -> list[str]:
        return PAYMENT_METHODS

    @rx.var
    def direction_options(self) -> list[str]:
        return PAYMENT_DIRECTIONS

    @rx.var
    def domain_options(self) -> list[str]:
        return SUPPLIER_DOMAINS

    @rx.var
    def create_label(self) -> str:
        return {
            "ventes": "Nouvelle vente",
            "achats": "Nouvel achat",
            "creances": "Encaisser un règlement",
            "dettes": "Régler un fournisseur",
            "paiements": "Nouveau paiement",
        }.get(self.register, "")

    @rx.var
    def can_create(self) -> bool:
        return self.register != "rapports"

    @rx.var
    def form_title(self) -> str:
        return {
            "sale": "Nouvelle vente client",
            "purchase": "Nouvel achat fournisseur",
            "payment": "Nouveau règlement",
        }.get(self.form_kind, "Nouvelle opération")

    @rx.var
    def form_is_payment(self) -> bool:
        return self.form_kind == "payment"

    @rx.var
    def form_is_purchase(self) -> bool:
        return self.form_kind == "purchase"

    @rx.var
    def form_status_options(self) -> list[str]:
        return SALE_STATUSES if self.form_kind == "sale" else PURCHASE_STATUSES

    @rx.var
    def form_preview(self) -> str:
        ht, vat_amount, ttc = _amounts(self.form)
        return f"HT {ht:.2f} DA · TVA {vat_amount:.2f} DA · TTC {ttc:.2f} DA"

    @rx.var
    def has_filters(self) -> bool:
        return bool(
            self.search
            or self.status_filter
            or self.type_filter
            or self.period != "all"
            or self.include_archived
        )

    # ------------------------------------------------------------------
    # Construction des filtres SQL
    # ------------------------------------------------------------------

    def _period_clause(
        self, date_col: str, overdue_col: str
    ) -> tuple[str, dict[str, object]]:
        today = datetime.date.today()
        params: dict[str, object] = {}
        period = self.period
        if period == "today":
            params["from_day"] = today
            return f" AND {date_col} = :from_day", params
        if period == "week":
            params["from_day"] = today - datetime.timedelta(
                days=today.weekday()
            )
            return f" AND {date_col} >= :from_day", params
        if period == "month":
            params["from_day"] = today.replace(day=1)
            return f" AND {date_col} >= :from_day", params
        if period == "season":
            params["from_day"] = _season_start(today)
            return f" AND {date_col} >= :from_day", params
        if period == "late":
            return f" AND COALESCE({overdue_col}, 0) > 0", params
        if period in ("d30", "d60", "d90"):
            params["late_days"] = int(period[1:])
            return f" AND COALESCE({overdue_col}, 0) >= :late_days", params
        return "", params

    def _base_clauses(
        self, alias: str, date_col: str, overdue_col: str
    ) -> tuple[str, dict[str, object]]:
        clauses = ""
        params: dict[str, object] = {}
        if not self.include_archived:
            clauses += f" AND {alias}.is_archived = false"
        if self.status_filter:
            column = "direction" if self.register == "paiements" else "status"
            clauses += f" AND UPPER({alias}.{column}) = :status"
            params["status"] = self.status_filter.upper()
        query = self.search.strip().lower()
        if query:
            params["q"] = f"%{query}%"
        period_clause, period_params = self._period_clause(
            date_col, overdue_col
        )
        clauses += period_clause
        params.update(period_params)
        return clauses, params

    # ------------------------------------------------------------------
    # Lectures des registres
    # ------------------------------------------------------------------

    async def _fetch_transactions(self, table: str) -> None:
        is_sale = table == "crm_sale"
        date_col = "s.sale_date" if is_sale else "s.purchase_date"
        link_col = "sale_id" if is_sale else "purchase_id"
        type_col = "payment_method" if is_sale else "domain"
        clauses, params = self._base_clauses("s", date_col, "i.overdue_days")
        if self.search.strip():
            clauses += (
                " AND (LOWER(s.code) LIKE :q OR LOWER(p.legal_name) LIKE :q"
                " OR LOWER(COALESCE(s.label, '')) LIKE :q"
                " OR LOWER(COALESCE(s.notes, '')) LIKE :q)"
            )
        if self.type_filter:
            clauses += f" AND UPPER(s.{type_col}) = :type_value"
            params["type_value"] = self.type_filter.upper()
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT s.id, s.code, {date_col}, p.id, p.legal_name,
                               COALESCE(s.label, ''), UPPER(s.status),
                               COALESCE(s.amount_ht, 0),
                               COALESCE(s.vat_amount, 0),
                               COALESCE(s.amount_ttc, 0),
                               COALESCE(s.paid_amount, 0),
                               s.is_archived, COALESCE(s.season, ''),
                               COALESCE(i.code, ''), i.due_date,
                               COALESCE(i.overdue_days, 0),
                               COALESCE(par.name, ''), COALESCE(c.name, ''),
                               UPPER(COALESCE(s.{type_col}, ''))
                        FROM {table} s
                        JOIN crm_partner p ON p.id = s.partner_id
                        LEFT JOIN crm_invoice i ON i.{link_col} = s.id
                        LEFT JOIN parcel par ON par.id = s.parcel_id
                        LEFT JOIN crop c ON c.id = s.crop_id
                        WHERE 1 = 1 {clauses}
                        ORDER BY COALESCE({date_col}, '0001-01-01') DESC,
                                 s.id DESC
                        LIMIT 200
                        """
                    ),
                    params,
                )
            ).all()

        register_rows: list[RegisterRow] = []
        for row in rows:
            amount_ttc = _f(row[9])
            paid = _f(row[10])
            overdue = _i(row[15])
            status = _s(row[6]).upper()
            remaining = round(max(amount_ttc - paid, 0.0), 2)
            register_rows.append(
                {
                    "id": _i(row[0]),
                    "code": _s(row[1]),
                    "date": _date(row[2]) or "—",
                    "partner_id": _i(row[3]),
                    "partner": _s(row[4]),
                    "title": _s(row[5]) or "Opération commerciale",
                    "reference": _s(row[13]) or "Sans facture",
                    "status": status,
                    "status_label": _label(status),
                    "tone": _tone(status, overdue, remaining),
                    "type_label": _label(row[18]),
                    "amount_ht": _f(row[7]),
                    "vat_amount": _f(row[8]),
                    "amount_ttc": amount_ttc,
                    "paid": paid,
                    "remaining": remaining,
                    "due_date": _date(row[14]) or "—",
                    "overdue_days": overdue,
                    "is_archived": bool(row[11]),
                    "links": _links(row[12], row[16], row[17]),
                }
            )
        self.rows = register_rows

    async def _fetch_settlements(self, table: str) -> None:
        clauses, params = self._base_clauses(
            "r", "r.due_date", "r.overdue_days"
        )
        if self.search.strip():
            clauses += (
                " AND (LOWER(p.legal_name) LIKE :q"
                " OR LOWER(COALESCE(i.code, '')) LIKE :q"
                " OR LOWER(COALESCE(r.notes, '')) LIKE :q)"
            )
        if self.type_filter:
            clauses += " AND r.aging_bucket = :type_value"
            params["type_value"] = self.type_filter
        is_receivable = table == "crm_receivable"
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT r.id, COALESCE(i.code, ''), r.issue_date,
                               p.id, p.legal_name, UPPER(r.status),
                               COALESCE(r.amount_due, 0),
                               COALESCE(r.amount_paid, 0),
                               COALESCE(r.amount_remaining, 0),
                               r.due_date, COALESCE(r.overdue_days, 0),
                               COALESCE(r.aging_bucket, '0-30'),
                               r.is_archived, COALESCE(r.notes, ''),
                               COALESCE(i.season, '')
                        FROM {table} r
                        JOIN crm_partner p ON p.id = r.partner_id
                        LEFT JOIN crm_invoice i ON i.id = r.invoice_id
                        WHERE 1 = 1 {clauses}
                        ORDER BY COALESCE(r.due_date, '9999-12-31') ASC,
                                 r.id DESC
                        LIMIT 200
                        """
                    ),
                    params,
                )
            ).all()

        register_rows: list[RegisterRow] = []
        for row in rows:
            status = _s(row[5]).upper()
            overdue = _i(row[10])
            remaining = _f(row[8])
            due = _f(row[6])
            register_rows.append(
                {
                    "id": _i(row[0]),
                    "code": _s(row[1]) or "Sans facture",
                    "date": _date(row[2]) or "—",
                    "partner_id": _i(row[3]),
                    "partner": _s(row[4]),
                    "title": (
                        "Créance client"
                        if is_receivable
                        else "Dette fournisseur"
                    ),
                    "reference": _s(row[1]) or "—",
                    "status": status,
                    "status_label": _label(status),
                    "tone": _tone(status, overdue, remaining),
                    "type_label": f"Tranche {_s(row[11])}",
                    "amount_ht": due,
                    "vat_amount": 0.0,
                    "amount_ttc": due,
                    "paid": _f(row[7]),
                    "remaining": remaining,
                    "due_date": _date(row[9]) or "—",
                    "overdue_days": overdue,
                    "is_archived": bool(row[12]),
                    "links": _links(row[14], row[13]),
                }
            )
        self.rows = register_rows

    async def _fetch_payments(self) -> None:
        clauses, params = self._base_clauses("y", "y.paid_on", "0")
        if self.search.strip():
            clauses += (
                " AND (LOWER(y.code) LIKE :q OR LOWER(p.legal_name) LIKE :q"
                " OR LOWER(COALESCE(y.reference, '')) LIKE :q"
                " OR LOWER(COALESCE(i.code, '')) LIKE :q)"
            )
        if self.type_filter:
            clauses += " AND UPPER(y.method) = :type_value"
            params["type_value"] = self.type_filter.upper()
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT y.id, y.code, y.paid_on, p.id, p.legal_name,
                               UPPER(y.direction), COALESCE(y.amount, 0),
                               UPPER(COALESCE(y.method, '')),
                               COALESCE(i.code, ''), i.due_date,
                               COALESCE(y.reference, ''),
                               COALESCE(y.bank, ''), y.is_archived,
                               COALESCE(y.recorded_by, ''),
                               COALESCE(y.comment, '')
                        FROM crm_payment y
                        JOIN crm_partner p ON p.id = y.partner_id
                        LEFT JOIN crm_invoice i ON i.id = y.invoice_id
                        WHERE 1 = 1 {clauses}
                        ORDER BY COALESCE(y.paid_on, '0001-01-01') DESC,
                                 y.id DESC
                        LIMIT 200
                        """
                    ),
                    params,
                )
            ).all()

        register_rows: list[RegisterRow] = []
        for row in rows:
            direction = _s(row[5]).upper()
            amount = _f(row[6])
            register_rows.append(
                {
                    "id": _i(row[0]),
                    "code": _s(row[1]),
                    "date": _date(row[2]) or "—",
                    "partner_id": _i(row[3]),
                    "partner": _s(row[4]),
                    "title": _label(direction),
                    "reference": _s(row[8]) or "Sans facture",
                    "status": direction,
                    "status_label": _label(direction),
                    "tone": "good" if direction == "ENCAISSEMENT" else "info",
                    "type_label": _label(row[7]),
                    "amount_ht": amount,
                    "vat_amount": 0.0,
                    "amount_ttc": amount,
                    "paid": amount,
                    "remaining": 0.0,
                    "due_date": _date(row[9]) or "—",
                    "overdue_days": 0,
                    "is_archived": bool(row[12]),
                    "links": _links(row[10], row[11], row[13], row[14]),
                }
            )
        self.rows = register_rows

    def _compute_totals(self) -> None:
        totals = dict(EMPTY_TOTALS)
        totals["count"] = float(len(self.rows))
        for row in self.rows:
            totals["amount_ht"] += row["amount_ht"]
            totals["vat_amount"] += row["vat_amount"]
            totals["amount_ttc"] += row["amount_ttc"]
            totals["paid"] += row["paid"]
            totals["remaining"] += row["remaining"]
            if row["overdue_days"] > 0:
                totals["overdue_count"] += 1
                totals["overdue_amount"] += row["remaining"]
            if row["is_archived"]:
                totals["archived"] += 1
        self.totals = {key: round(value, 2) for key, value in totals.items()}

    # ------------------------------------------------------------------
    # Rapports
    # ------------------------------------------------------------------

    async def _resolve_report_period(
        self, asession
    ) -> tuple[datetime.date | None, datetime.date | None, str, datetime.date]:
        """Détermine la période exploitable du rapport CRM.

        Bascule automatiquement de la campagne en cours vers la dernière
        campagne réellement documentée, puis vers tout l'historique CRM,
        afin que les cartes et les exports ne restent jamais à zéro lorsque
        les données sont datées d'une campagne antérieure.
        """
        today = datetime.date.today()
        bounds = (
            await asession.execute(
                text(
                    """
                    SELECT
                        (SELECT MIN(sale_date) FROM crm_sale
                          WHERE is_archived = false
                            AND UPPER(status) <> 'ANNULEE'
                            AND sale_date IS NOT NULL),
                        (SELECT MAX(sale_date) FROM crm_sale
                          WHERE is_archived = false
                            AND UPPER(status) <> 'ANNULEE'
                            AND sale_date IS NOT NULL),
                        (SELECT MIN(purchase_date) FROM crm_purchase
                          WHERE is_archived = false
                            AND UPPER(status) <> 'ANNULEE'
                            AND purchase_date IS NOT NULL),
                        (SELECT MAX(purchase_date) FROM crm_purchase
                          WHERE is_archived = false
                            AND UPPER(status) <> 'ANNULEE'
                            AND purchase_date IS NOT NULL)
                    """
                )
            )
        ).first()

        def _as_date(value: object) -> datetime.date | None:
            raw = _date(value)
            if not raw:
                return None
            try:
                return datetime.date.fromisoformat(raw)
            except ValueError:
                return None

        firsts = [
            day
            for day in (
                _as_date(bounds[0] if bounds else None),
                _as_date(bounds[2] if bounds else None),
            )
            if day is not None
        ]
        lasts = [
            day
            for day in (
                _as_date(bounds[1] if bounds else None),
                _as_date(bounds[3] if bounds else None),
            )
            if day is not None
        ]
        if not lasts:
            return None, None, "empty", today

        latest = max(lasts)
        earliest = min(firsts) if firsts else latest
        current_start = _season_start(today)
        if latest >= current_start:
            return current_start, None, "season_current", today

        fallback_start = _season_start(latest)
        fallback_end = _season_end(fallback_start)
        if earliest >= fallback_start:
            # Tout l'historique tient dans cette campagne : on l'affiche en
            # entier plutôt que de restreindre inutilement la fenêtre.
            return None, None, "history", latest
        return fallback_start, fallback_end, "season_last", latest

    async def _fetch_report(self) -> None:
        async with rx.asession() as asession:
            (
                period_from,
                period_to,
                scope,
                reference,
            ) = await self._resolve_report_period(asession)
            keys = _month_keys(reference)
            since = datetime.date.fromisoformat(f"{keys[0]}-01")
            sales_clause = ""
            purchases_clause = ""
            params: dict[str, object] = {}
            if period_from is not None:
                params["from_day"] = period_from
                sales_clause += " AND sale_date >= :from_day"
                purchases_clause += " AND purchase_date >= :from_day"
            if period_to is not None:
                params["to_day"] = period_to
                sales_clause += " AND sale_date <= :to_day"
                purchases_clause += " AND purchase_date <= :to_day"
            self.report_scope = scope
            self.report_scope_label = REPORT_SCOPES.get(scope, "")
            self.report_is_fallback = scope in ("season_last", "history")
            self.report_from = (
                period_from.isoformat() if period_from is not None else ""
            )
            self.report_to = (
                period_to.isoformat() if period_to is not None else ""
            )
            if scope == "season_current":
                self.report_period_label = (
                    f"Campagne {_season_label(_season_start(reference))}"
                )
            elif scope == "season_last":
                self.report_period_label = (
                    f"Campagne {_season_label(_season_start(reference))}"
                    " (dernière campagne documentée)"
                )
            elif scope == "history":
                self.report_period_label = (
                    "Historique CRM complet (aucune vente ni achat sur la"
                    " campagne en cours)"
                )
            else:
                self.report_period_label = (
                    "Aucune vente ni achat enregistré à ce jour"
                )
            head = (
                await asession.execute(
                    text(
                        f"""
                        SELECT
                            (SELECT COALESCE(SUM(amount_ttc), 0)
                               FROM crm_sale
                              WHERE is_archived = false
                                AND UPPER(status) <> 'ANNULEE'
                                {sales_clause}),
                            (SELECT COUNT(*) FROM crm_sale
                              WHERE is_archived = false
                                AND UPPER(status) <> 'ANNULEE'
                                {sales_clause}),
                            (SELECT COALESCE(SUM(amount_ttc), 0)
                               FROM crm_purchase
                              WHERE is_archived = false
                                AND UPPER(status) <> 'ANNULEE'
                                {purchases_clause}),
                            (SELECT COUNT(*) FROM crm_purchase
                              WHERE is_archived = false
                                AND UPPER(status) <> 'ANNULEE'
                                {purchases_clause}),
                            (SELECT COALESCE(SUM(amount_remaining), 0)
                               FROM crm_receivable WHERE is_archived = false),
                            (SELECT COALESCE(SUM(amount_remaining), 0)
                               FROM crm_payable WHERE is_archived = false),
                            (SELECT COALESCE(SUM(amount), 0)
                               FROM crm_payment
                              WHERE is_archived = false
                                AND UPPER(direction) = 'ENCAISSEMENT'),
                            (SELECT COALESCE(SUM(amount), 0)
                               FROM crm_payment
                              WHERE is_archived = false
                                AND UPPER(direction) = 'DECAISSEMENT'),
                            (SELECT COALESCE(SUM(amount_remaining), 0)
                               FROM crm_receivable
                              WHERE is_archived = false AND overdue_days > 0),
                            (SELECT COALESCE(SUM(amount_remaining), 0)
                               FROM crm_payable
                              WHERE is_archived = false AND overdue_days > 0)
                        """
                    ),
                    params,
                )
            ).first()
            sales_months = (
                await asession.execute(
                    text(
                        """
                        SELECT strftime('%Y-%m', sale_date) AS m,
                               COALESCE(SUM(amount_ttc), 0)
                        FROM crm_sale
                        WHERE is_archived = false
                          AND UPPER(status) <> 'ANNULEE'
                          AND sale_date IS NOT NULL AND sale_date >= :since
                        GROUP BY m
                        """
                    ),
                    {"since": since},
                )
            ).all()
            purchase_months = (
                await asession.execute(
                    text(
                        """
                        SELECT strftime('%Y-%m', purchase_date) AS m,
                               COALESCE(SUM(amount_ttc), 0)
                        FROM crm_purchase
                        WHERE is_archived = false
                          AND UPPER(status) <> 'ANNULEE'
                          AND purchase_date IS NOT NULL
                          AND purchase_date >= :since
                        GROUP BY m
                        """
                    ),
                    {"since": since},
                )
            ).all()
            partners = (
                await asession.execute(
                    text(
                        """
                        SELECT p.id, p.legal_name, UPPER(p.kind),
                               (SELECT COALESCE(SUM(s.amount_ttc), 0)
                                  FROM crm_sale s
                                 WHERE s.partner_id = p.id
                                   AND s.is_archived = false
                                   AND UPPER(s.status) <> 'ANNULEE') AS ca,
                               (SELECT COALESCE(SUM(a.amount_ttc), 0)
                                  FROM crm_purchase a
                                 WHERE a.partner_id = p.id
                                   AND a.is_archived = false
                                   AND UPPER(a.status) <> 'ANNULEE') AS ach,
                               (SELECT COALESCE(SUM(r.amount_remaining), 0)
                                  FROM crm_receivable r
                                 WHERE r.partner_id = p.id
                                   AND r.is_archived = false),
                               (SELECT COALESCE(SUM(d.amount_remaining), 0)
                                  FROM crm_payable d
                                 WHERE d.partner_id = p.id
                                   AND d.is_archived = false)
                        FROM crm_partner p
                        WHERE p.is_archived = false
                        ORDER BY (ca + ach) DESC
                        LIMIT 15
                        """
                    )
                )
            ).all()

        sales_season = _f(head[0] if head else 0)
        purchases_season = _f(head[2] if head else 0)
        if sales_season <= 0 and purchases_season <= 0:
            # Ultime filet de sécurité : si la fenêtre retenue reste vide,
            # on rebascule sur la totalité de l'historique CRM.
            async with rx.asession() as asession:
                fallback = (
                    await asession.execute(
                        text(
                            """
                            SELECT
                                (SELECT COALESCE(SUM(amount_ttc), 0)
                                   FROM crm_sale
                                  WHERE is_archived = false
                                    AND UPPER(status) <> 'ANNULEE'),
                                (SELECT COUNT(*) FROM crm_sale
                                  WHERE is_archived = false
                                    AND UPPER(status) <> 'ANNULEE'),
                                (SELECT COALESCE(SUM(amount_ttc), 0)
                                   FROM crm_purchase
                                  WHERE is_archived = false
                                    AND UPPER(status) <> 'ANNULEE'),
                                (SELECT COUNT(*) FROM crm_purchase
                                  WHERE is_archived = false
                                    AND UPPER(status) <> 'ANNULEE')
                            """
                        )
                    )
                ).first()
            if fallback is not None and (
                _f(fallback[0]) > 0 or _f(fallback[2]) > 0
            ):
                sales_season = _f(fallback[0])
                purchases_season = _f(fallback[2])
                head = (
                    fallback[0],
                    fallback[1],
                    fallback[2],
                    fallback[3],
                    *(head[4:] if head else (0,) * 6),
                )
                self.report_scope = "history"
                self.report_scope_label = REPORT_SCOPES["history"]
                self.report_is_fallback = True
                self.report_from = ""
                self.report_to = ""
                self.report_period_label = (
                    "Historique CRM complet (aucune vente ni achat sur la"
                    " campagne en cours)"
                )
        margin = round(sales_season - purchases_season, 2)
        receivable = _f(head[4] if head else 0)
        payable = _f(head[5] if head else 0)
        self.report = {
            "sales": sales_season,
            "purchases": purchases_season,
            "margin": margin,
            "margin_rate": (
                round(margin / sales_season * 100, 1)
                if sales_season > 0
                else 0.0
            ),
            "receivable": receivable,
            "payable": payable,
            "received": _f(head[6] if head else 0),
            "paid_out": _f(head[7] if head else 0),
            "net_cash": round(receivable - payable, 2),
            "sales_count": _f(head[1] if head else 0),
            "purchases_count": _f(head[3] if head else 0),
            "late_receivable": _f(head[8] if head else 0),
            "late_payable": _f(head[9] if head else 0),
        }

        sales_map = {_s(row[0]): _f(row[1]) for row in sales_months}
        purchases_map = {_s(row[0]): _f(row[1]) for row in purchase_months}
        top = max([*sales_map.values(), *purchases_map.values(), 1.0])
        months: list[ReportMonth] = []
        for key in keys:
            sales = sales_map.get(key, 0.0)
            purchases = purchases_map.get(key, 0.0)
            months.append(
                {
                    "key": key,
                    "label": _month_label(key),
                    "sales": sales,
                    "purchases": purchases,
                    "margin": round(sales - purchases, 2),
                    "sales_width": f"{sales / top * 100:.0f}%",
                    "purchases_width": f"{purchases / top * 100:.0f}%",
                }
            )
        self.report_months = months

        self.report_partners = [
            {
                "id": _i(row[0]),
                "name": _s(row[1]),
                "kind_label": _label(row[2]),
                "sales": _f(row[3]),
                "purchases": _f(row[4]),
                "receivable": _f(row[5]),
                "payable": _f(row[6]),
                "margin": round(_f(row[3]) - _f(row[4]), 2),
            }
            for row in partners
        ]
        self.report_text = self._build_report_text()

    def _build_report_text(self) -> str:
        r = self.report
        lines = [
            "AGRIPRO — RAPPORT CRM & PARTENAIRES",
            f"Édité le {datetime.date.today().isoformat()}",
            f"Périmètre : {self.report_scope_label}"
            f" — {self.report_period_label}",
            "",
            f"Ventes de la campagne : {r['sales']:.2f} DA"
            f" ({r['sales_count']:.0f} opération(s))",
            f"Achats de la campagne : {r['purchases']:.2f} DA"
            f" ({r['purchases_count']:.0f} opération(s))",
            f"Marge commerciale : {r['margin']:.2f} DA"
            f" ({r['margin_rate']:.1f} %)",
            f"Créances clients ouvertes : {r['receivable']:.2f} DA"
            f" dont {r['late_receivable']:.2f} DA en retard",
            f"Dettes fournisseurs restantes : {r['payable']:.2f} DA"
            f" dont {r['late_payable']:.2f} DA en retard",
            f"Encaissements cumulés : {r['received']:.2f} DA",
            f"Décaissements cumulés : {r['paid_out']:.2f} DA",
            f"Position nette : {r['net_cash']:.2f} DA",
            "",
            "CADENCE MENSUELLE (ventes / achats)",
        ]
        for month in self.report_months:
            lines.append(
                f"- {month['label']} : {month['sales']:.2f} DA /"
                f" {month['purchases']:.2f} DA"
                f" (marge {month['margin']:.2f} DA)"
            )
        lines.append("")
        lines.append("BALANCE DES TIERS")
        for partner in self.report_partners:
            lines.append(
                f"- {partner['name']} ({partner['kind_label']}) :"
                f" ventes {partner['sales']:.2f} DA,"
                f" achats {partner['purchases']:.2f} DA,"
                f" créances {partner['receivable']:.2f} DA,"
                f" dettes {partner['payable']:.2f} DA"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Options des formulaires
    # ------------------------------------------------------------------

    async def _fetch_options(self) -> None:
        async with rx.asession() as asession:
            partners = (
                await asession.execute(
                    text(
                        """
                        SELECT id, code, legal_name, UPPER(kind), UPPER(status)
                        FROM crm_partner
                        WHERE is_archived = false
                        ORDER BY legal_name
                        LIMIT 300
                        """
                    )
                )
            ).all()
            invoices = (
                await asession.execute(
                    text(
                        """
                        SELECT i.id, i.code, UPPER(i.kind), p.legal_name,
                               COALESCE(i.remaining_amount, 0)
                        FROM crm_invoice i
                        JOIN crm_partner p ON p.id = i.partner_id
                        WHERE i.is_archived = false
                          AND COALESCE(i.remaining_amount, 0) > 0.005
                          AND UPPER(i.status) <> 'ANNULEE'
                        ORDER BY COALESCE(i.due_date, '9999-12-31')
                        LIMIT 200
                        """
                    )
                )
            ).all()
        self.partner_options = [
            {
                "id": _i(row[0]),
                "label": f"{_s(row[2])} · {_s(row[1])}",
                "kind": _s(row[3]),
                "remaining": 0.0,
            }
            for row in partners
            if _s(row[4]) != "BLOQUE"
        ]
        self.invoice_options = [
            {
                "id": _i(row[0]),
                "label": (
                    f"{_s(row[1])} · {_s(row[3])} · reste {_f(row[4]):.0f} DA"
                ),
                "kind": _s(row[2]),
                "remaining": _f(row[4]),
            }
            for row in invoices
        ]

    # ------------------------------------------------------------------
    # Journalisation CRM
    # ------------------------------------------------------------------

    async def _journal(
        self,
        asession,
        *,
        partner_id: int,
        kind: str,
        title: str,
        summary: str,
        icon: str,
        amount: float,
        entity_type: str,
        entity_id: int,
        entity_ref: str,
        action: str,
        old_value: str = "",
        new_value: str = "",
    ) -> None:
        await asession.execute(
            text(
                """
                INSERT INTO crm_event (partner_id, kind, title, summary,
                    occurred_on, amount, author, module_route, icon)
                VALUES (:pid, :kind, :title, :summary, :day, :amount,
                    'Registres CRM', '/crm', :icon)
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
                VALUES (:pid, 'Registres CRM', :action, :entity_type,
                    :entity_id, :ref, '', :old_value, :new_value, :summary,
                    '/crm', '', false, :now)
                """
            ),
            {
                "pid": partner_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "ref": entity_ref,
                "old_value": old_value,
                "new_value": new_value,
                "summary": summary,
                "now": datetime.datetime.now(),
            },
        )

    # ------------------------------------------------------------------
    # Chargement et filtres
    # ------------------------------------------------------------------

    async def _refresh_rows(self) -> None:
        if self.register == "rapports":
            await self._fetch_report()
            self.rows = []
            self.totals = EMPTY_TOTALS
            return
        table = REGISTER_TABLES.get(self.register, "crm_sale")
        if self.register in ("ventes", "achats"):
            await self._fetch_transactions(table)
        elif self.register in ("creances", "dettes"):
            await self._fetch_settlements(table)
        else:
            await self._fetch_payments()
        self._compute_totals()

    @rx.event
    async def load_registers(self):
        self.is_loading = True
        yield
        await ensure_local_database()
        await ensure_crm_tables()
        await asyncio.to_thread(seed_crm_if_empty)
        await self._refresh_rows()
        await self._fetch_options()
        self.is_loading = False

    @rx.event
    async def enter_register(self, register: str):
        target = register if register in REGISTERS else "ventes"
        if target != self.register:
            self.status_filter = ""
            self.type_filter = ""
            self.period = "all"
            self.search = ""
        self.register = target
        yield CrmRegistersState.load_registers

    @rx.event
    async def refresh(self):
        await self._refresh_rows()

    @rx.event
    async def set_search(self, value: str):
        self.search = value
        await self._refresh_rows()

    @rx.event
    async def set_status_filter(self, value: str):
        self.status_filter = value
        await self._refresh_rows()

    @rx.event
    async def set_type_filter(self, value: str):
        self.type_filter = value
        await self._refresh_rows()

    @rx.event
    async def set_period(self, value: str):
        self.period = value if value else "all"
        await self._refresh_rows()

    @rx.event
    async def toggle_archived(self):
        self.include_archived = not self.include_archived
        await self._refresh_rows()

    @rx.event
    async def clear_filters(self):
        self.search = ""
        self.status_filter = ""
        self.type_filter = ""
        self.period = "all"
        self.include_archived = False
        await self._refresh_rows()

    # ------------------------------------------------------------------
    # Intégration avec les fiches partenaires
    # ------------------------------------------------------------------

    @rx.event
    async def open_partner(self, partner_id: int):
        from app.states.crm_partners_state import CrmPartnersState
        from app.states.crm_state import CrmState

        crm = await self.get_state(CrmState)
        crm.active_tab = "partenaires"
        partners = await self.get_state(CrmPartnersState)
        partners.space = "partenaires"
        yield CrmPartnersState.select_partner(partner_id)

    # ------------------------------------------------------------------
    # Archivage (jamais de suppression)
    # ------------------------------------------------------------------

    def _row_by_id(self, row_id: int) -> RegisterRow | None:
        for row in self.rows:
            if row["id"] == row_id:
                return row
        return None

    @rx.event
    async def archive_row(self, row_id: int):
        table = REGISTER_TABLES.get(self.register, "")
        row = self._row_by_id(row_id)
        if not table or row is None:
            return rx.toast("Opération introuvable dans ce registre.")
        if self.register in ("ventes", "achats") and row["paid"] > 0.005:
            return rx.toast(
                "Impossible d'archiver une pièce déjà réglée : annulez"
                " d'abord les règlements rattachés."
            )
        if self.register == "paiements":
            return rx.toast(
                "Un règlement enregistré n'est jamais supprimé :"
                " saisissez un règlement correctif."
            )
        async with rx.asession() as asession:
            await asession.execute(
                text(f"UPDATE {table} SET is_archived = true WHERE id = :rid"),
                {"rid": row_id},
            )
            await self._journal(
                asession,
                partner_id=row["partner_id"],
                kind="ARCHIVAGE",
                title=f"Archivage {row['code']}",
                summary=(
                    f"{REGISTER_TITLES.get(self.register, '')} :"
                    f" {row['code']} archivé(e) au lieu d'être supprimé(e)."
                ),
                icon="archive",
                amount=row["amount_ttc"],
                entity_type=table,
                entity_id=row_id,
                entity_ref=row["code"],
                action="archivage",
                old_value="actif",
                new_value="archive",
            )
            await asession.commit()
        await self._refresh_rows()
        return rx.toast(f"{row['code']} archivé(e).")

    @rx.event
    async def restore_row(self, row_id: int):
        table = REGISTER_TABLES.get(self.register, "")
        row = self._row_by_id(row_id)
        if not table or row is None:
            return rx.toast("Opération introuvable dans ce registre.")
        async with rx.asession() as asession:
            await asession.execute(
                text(f"UPDATE {table} SET is_archived = false WHERE id = :rid"),
                {"rid": row_id},
            )
            await self._journal(
                asession,
                partner_id=row["partner_id"],
                kind="MISE_A_JOUR",
                title=f"Réactivation {row['code']}",
                summary=f"{row['code']} réintégré(e) au registre actif.",
                icon="rotate-ccw",
                amount=row["amount_ttc"],
                entity_type=table,
                entity_id=row_id,
                entity_ref=row["code"],
                action="restauration",
                old_value="archive",
                new_value="actif",
            )
            await asession.commit()
        await self._refresh_rows()
        return rx.toast(f"{row['code']} réactivé(e).")

    # ------------------------------------------------------------------
    # Formulaires d'écriture
    # ------------------------------------------------------------------

    @rx.event
    async def open_form(self):
        kind = {
            "ventes": "sale",
            "achats": "purchase",
            "creances": "payment",
            "dettes": "payment",
            "paiements": "payment",
        }.get(self.register, "sale")
        today = datetime.date.today()
        season = _season_start(today)
        self.form_kind = kind
        self.form_error = ""
        self.form = {
            **EMPTY_FORM,
            "operation_date": today.isoformat(),
            "season": f"{season.year}/{season.year + 1}",
            "status": "CONFIRMEE" if kind == "sale" else "COMMANDEE",
            "direction": (
                "DECAISSEMENT" if self.register == "dettes" else "ENCAISSEMENT"
            ),
            "unit": "t" if kind == "sale" else "u",
        }
        await self._fetch_options()
        self.form_open = True

    @rx.event
    def close_form(self):
        self.form_open = False
        self.form_error = ""

    @rx.event
    def update_form(self, field: str, value: str):
        self.form = {**self.form, field: value}

    async def _next_code(self, table: str, prefix: str) -> str:
        year = datetime.date.today().year
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(f"SELECT code FROM {table} WHERE code LIKE :pattern"),
                    {"pattern": f"{prefix}-{year}-%"},
                )
            ).all()
        highest = 0
        for row in rows:
            tail = _s(row[0]).rsplit("-", 1)[-1]
            if tail.isdigit():
                highest = max(highest, int(tail))
        return f"{prefix}-{year}-{highest + 1:04d}"

    def _validate_transaction(self, data: dict) -> str:
        if _i(data.get("partner_id")) <= 0:
            return "Sélectionnez le tiers concerné par l'opération."
        if not _s(data.get("operation_date")).strip():
            return "La date de l'opération est obligatoire."
        if _f(data.get("quantity")) <= 0:
            return "La quantité doit être strictement positive."
        if _f(data.get("unit_price")) <= 0:
            return "Le prix unitaire doit être strictement positif."
        discount = _f(data.get("discount_percent"))
        if discount < 0 or discount > 100:
            return "La remise doit être comprise entre 0 et 100 %."
        vat = _f(data.get("vat_rate"))
        if vat < 0 or vat > 100:
            return "Le taux de TVA doit être compris entre 0 et 100 %."
        return ""

    def _validate_payment(self, data: dict) -> str:
        if _i(data.get("partner_id")) <= 0:
            return "Sélectionnez le tiers réglé ou payeur."
        if _f(data.get("amount")) <= 0:
            return "Le montant du règlement doit être strictement positif."
        if not _s(data.get("operation_date")).strip():
            return "La date du règlement est obligatoire."
        invoice_id = _i(data.get("invoice_id"))
        if invoice_id > 0:
            option = next(
                (o for o in self.invoice_options if o["id"] == invoice_id),
                None,
            )
            if option is None:
                return "La facture sélectionnée n'est plus réglable."
            if _f(data.get("amount")) > option["remaining"] + 0.01:
                return (
                    "Le règlement dépasse le restant dû de la facture"
                    f" ({option['remaining']:.2f} DA)."
                )
        return ""

    @rx.event
    async def save_operation(self, form_data: dict[str, Any]):
        self.form_error = ""
        self.is_saving = True
        try:
            error = (
                self._validate_payment(form_data)
                if self.form_kind == "payment"
                else self._validate_transaction(form_data)
            )
            if error:
                self.form_error = error
                return
            if self.form_kind == "payment":
                message = await self._save_payment(form_data)
            else:
                message = await self._save_transaction(form_data)
        except BusinessError as e:
            logging.exception("Unexpected error")
            self.form_error = str(e)
            return
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Error: {e}")
            self.form_error = (
                "L'enregistrement a échoué : vérifiez les données saisies."
            )
            return
        finally:
            self.is_saving = False
        self.form_open = False
        await self._refresh_rows()
        await self._fetch_options()
        return rx.toast(message)

    async def _check_partner(self, asession, partner_id: int) -> None:
        row = (
            await asession.execute(
                text(
                    """
                    SELECT UPPER(status), is_archived
                    FROM crm_partner WHERE id = :pid
                    """
                ),
                {"pid": partner_id},
            )
        ).first()
        if row is None:
            raise BusinessError("Ce tiers n'existe plus dans le référentiel.")
        if bool(row[1]) or _s(row[0]) == "BLOQUE":
            raise BusinessError(
                "Ce tiers est bloqué ou archivé : aucune nouvelle opération"
                " ne peut lui être rattachée."
            )

    async def _save_transaction(self, data: dict) -> str:
        is_sale = self.form_kind == "sale"
        table = "crm_sale" if is_sale else "crm_purchase"
        code = await self._next_code(table, "VTE" if is_sale else "ACH")
        ht, vat_amount, ttc = _amounts(data)
        partner_id = _i(data.get("partner_id"))
        params = {
            "pid": partner_id,
            "code": code,
            "status": (
                _s(data.get("status")).upper()
                or ("CONFIRMEE" if is_sale else "COMMANDEE")
            ),
            "day": _s(data.get("operation_date")).strip(),
            "season": _s(data.get("season")).strip(),
            "label": _s(data.get("label")).strip() or code,
            "method": _s(data.get("payment_method")).upper() or "VIREMENT",
            "discount": _f(data.get("discount_percent")),
            "ht": ht,
            "vat": vat_amount,
            "ttc": ttc,
            "notes": _s(data.get("notes")).strip(),
            "domain": _s(data.get("domain")).upper() or "AUTRE",
        }
        async with rx.asession() as asession:
            await self._check_partner(asession, partner_id)
            if is_sale:
                await asession.execute(
                    text(
                        """
                        INSERT INTO crm_sale (partner_id, code, status,
                            sale_date, season, label, currency, payment_method,
                            discount_percent, amount_ht, vat_amount,
                            amount_ttc, paid_amount, transport_cost,
                            is_archived, notes, delivery_note, order_reference)
                        VALUES (:pid, :code, :status, :day, :season, :label,
                            'DZD', :method, :discount, :ht, :vat, :ttc, 0, 0,
                            false, :notes, '', '')
                        """
                    ),
                    params,
                )
            else:
                await asession.execute(
                    text(
                        """
                        INSERT INTO crm_purchase (partner_id, code, status,
                            purchase_date, season, label, currency,
                            payment_method, domain, discount_percent,
                            amount_ht, vat_amount, amount_ttc, paid_amount,
                            transport_cost, is_archived, notes,
                            order_reference, receipt_reference)
                        VALUES (:pid, :code, :status, :day, :season, :label,
                            'DZD', :method, :domain, :discount, :ht, :vat,
                            :ttc, 0, 0, false, :notes, '', '')
                        """
                    ),
                    params,
                )
            new_id = _i(
                (
                    await asession.execute(
                        text(f"SELECT id FROM {table} WHERE code = :code"),
                        {"code": code},
                    )
                ).scalar()
            )
            await self._journal(
                asession,
                partner_id=partner_id,
                kind="VENTE" if is_sale else "ACHAT",
                title=f"{'Vente' if is_sale else 'Achat'} {code}",
                summary=(
                    f"{params['label']} · HT {ht:.2f} DA ·"
                    f" TVA {vat_amount:.2f} DA · TTC {ttc:.2f} DA"
                ),
                icon="trending-up" if is_sale else "truck",
                amount=ttc,
                entity_type=table,
                entity_id=new_id,
                entity_ref=code,
                action="creation",
                new_value=f"{ttc:.2f} DA",
            )
            await asession.commit()
        return f"{code} enregistré(e) : {ttc:.2f} DA TTC."

    async def _save_payment(self, data: dict) -> str:
        partner_id = _i(data.get("partner_id"))
        invoice_id = _i(data.get("invoice_id"))
        amount = _f(data.get("amount"))
        direction = _s(data.get("direction")).upper() or "ENCAISSEMENT"
        code = await self._next_code("crm_payment", "PAY")
        async with rx.asession() as asession:
            await self._check_partner(asession, partner_id)
            await asession.execute(
                text(
                    """
                    INSERT INTO crm_payment (partner_id, code, direction,
                        invoice_id, paid_on, amount, currency, method,
                        reference, bank, cash_desk, recorded_by, is_archived,
                        comment)
                    VALUES (:pid, :code, :direction, :invoice_id, :day,
                        :amount, 'DZD', :method, :reference, :bank, '',
                        'Registres CRM', false, :comment)
                    """
                ),
                {
                    "pid": partner_id,
                    "code": code,
                    "direction": direction,
                    "invoice_id": invoice_id or None,
                    "day": _s(data.get("operation_date")).strip(),
                    "amount": amount,
                    "method": (
                        _s(data.get("payment_method")).upper() or "VIREMENT"
                    ),
                    "reference": _s(data.get("reference")).strip(),
                    "bank": _s(data.get("bank")).strip(),
                    "comment": _s(data.get("notes")).strip(),
                },
            )
            payment_id = _i(
                (
                    await asession.execute(
                        text("SELECT id FROM crm_payment WHERE code = :code"),
                        {"code": code},
                    )
                ).scalar()
            )
            if invoice_id > 0:
                await self._settle_invoice(asession, invoice_id)
            await self._journal(
                asession,
                partner_id=partner_id,
                kind="PAIEMENT",
                title=f"Règlement {code}",
                summary=(
                    f"{_label(direction)} de {amount:.2f} DA"
                    f" ({_label(data.get('payment_method'))})."
                ),
                icon="banknote",
                amount=amount,
                entity_type="crm_payment",
                entity_id=payment_id,
                entity_ref=code,
                action="paiement",
                new_value=f"{amount:.2f} DA",
            )
            await asession.commit()
        return f"Règlement {code} enregistré : {amount:.2f} DA."

    async def _settle_invoice(self, asession, invoice_id: int) -> None:
        """Recalcule payé, restant dû, retard et statuts d'une facture."""
        today = datetime.date.today()
        invoice = (
            await asession.execute(
                text(
                    """
                    SELECT COALESCE(amount_ttc, 0), due_date, sale_id,
                           purchase_id
                    FROM crm_invoice WHERE id = :iid
                    """
                ),
                {"iid": invoice_id},
            )
        ).first()
        if invoice is None:
            return
        total = _f(invoice[0])
        paid = _f(
            (
                await asession.execute(
                    text(
                        """
                        SELECT COALESCE(SUM(amount), 0) FROM crm_payment
                        WHERE invoice_id = :iid AND is_archived = false
                        """
                    ),
                    {"iid": invoice_id},
                )
            ).scalar()
        )
        paid = min(paid, total) if total > 0 else paid
        remaining = round(max(total - paid, 0.0), 2)
        overdue = 0
        due_raw = _date(invoice[1])
        if due_raw and remaining > 0.005:
            try:
                due = datetime.date.fromisoformat(due_raw)
                overdue = max((today - due).days, 0)
            except ValueError:
                overdue = 0
        if remaining <= 0.005:
            status = "PAYEE"
            settlement = "REGLEE"
        elif overdue > 0:
            status = "EN_RETARD"
            settlement = "EN_RETARD"
        elif paid > 0.005:
            status = "PARTIELLEMENT_PAYEE"
            settlement = "PARTIELLE"
        else:
            status = "EMISE"
            settlement = "OUVERTE"
        common = {
            "iid": invoice_id,
            "paid": paid,
            "remaining": remaining,
            "overdue": overdue,
            "status": status,
            "bucket": _bucket(overdue),
            "settlement": settlement,
        }
        await asession.execute(
            text(
                """
                UPDATE crm_invoice
                SET paid_amount = :paid, remaining_amount = :remaining,
                    overdue_days = :overdue, status = :status
                WHERE id = :iid
                """
            ),
            common,
        )
        await asession.execute(
            text(
                """
                UPDATE crm_receivable
                SET amount_paid = :paid, amount_remaining = :remaining,
                    overdue_days = :overdue, aging_bucket = :bucket,
                    status = :settlement
                WHERE invoice_id = :iid
                """
            ),
            common,
        )
        await asession.execute(
            text(
                """
                UPDATE crm_payable
                SET amount_paid = :paid, amount_remaining = :remaining,
                    overdue_days = :overdue, aging_bucket = :bucket,
                    status = :settlement
                WHERE invoice_id = :iid
                """
            ),
            common,
        )
        tx_status = (
            "PAYEE"
            if remaining <= 0.005
            else "PARTIELLEMENT_PAYEE"
            if paid > 0.005
            else "FACTUREE"
        )
        if _i(invoice[2]) > 0:
            await asession.execute(
                text(
                    """
                    UPDATE crm_sale
                    SET paid_amount = :paid, status = :tx_status
                    WHERE id = :sid
                    """
                ),
                {"paid": paid, "tx_status": tx_status, "sid": _i(invoice[2])},
            )
        if _i(invoice[3]) > 0:
            await asession.execute(
                text(
                    """
                    UPDATE crm_purchase
                    SET paid_amount = :paid, status = :tx_status
                    WHERE id = :aid
                    """
                ),
                {"paid": paid, "tx_status": tx_status, "aid": _i(invoice[3])},
            )

    # ------------------------------------------------------------------
    # Exports internes (CSV / texte)
    # ------------------------------------------------------------------

    @rx.event
    def export_csv(self):
        if self.register == "rapports":
            content = to_csv(
                ["Mois", "Ventes TTC", "Achats TTC", "Marge"],
                [
                    [
                        month["label"],
                        f"{month['sales']:.2f}",
                        f"{month['purchases']:.2f}",
                        f"{month['margin']:.2f}",
                    ]
                    for month in self.report_months
                ],
            )
            return rx.download(data=content, filename="agripro-crm-rapport.csv")
        headers = [
            "Pièce",
            "Date",
            "Tiers",
            "Objet",
            "Référence",
            "Type",
            self.amount_header,
            "TVA",
            "TTC",
            "Payé",
            "Restant dû",
            "Échéance",
            "Retard (j)",
            "Statut",
            "Archivé",
        ]
        rows = [
            [
                row["code"],
                row["date"],
                row["partner"],
                row["title"],
                row["reference"],
                row["type_label"],
                f"{row['amount_ht']:.2f}",
                f"{row['vat_amount']:.2f}",
                f"{row['amount_ttc']:.2f}",
                f"{row['paid']:.2f}",
                f"{row['remaining']:.2f}",
                row["due_date"],
                str(row["overdue_days"]),
                row["status_label"],
                "oui" if row["is_archived"] else "non",
            ]
            for row in self.rows
        ]
        return rx.download(
            data=to_csv(headers, rows),
            filename=f"agripro-crm-{self.register}.csv",
        )

    @rx.event
    def export_text(self):
        if self.register == "rapports":
            return rx.download(
                data=self.report_text or "Aucune donnée disponible.",
                filename="agripro-crm-rapport.txt",
            )
        month = MONTHS[datetime.date.today().month - 1]
        lines = [
            f"AGRIPRO — {REGISTER_TITLES.get(self.register, '')} ({month})",
            f"{len(self.rows)} ligne(s) ·"
            f" TTC {self.totals['amount_ttc']:.2f} DA ·"
            f" restant dû {self.totals['remaining']:.2f} DA",
            "",
        ]
        for row in self.rows:
            late = (
                f" · {row['overdue_days']} j de retard"
                if row["overdue_days"] > 0
                else ""
            )
            lines.append(
                f"- {row['code']} · {row['date']} · {row['partner']} ·"
                f" {row['status_label']} · TTC {row['amount_ttc']:.2f} DA ·"
                f" restant {row['remaining']:.2f} DA{late}"
            )
        return rx.download(
            data="\n".join(lines),
            filename=f"agripro-crm-{self.register}.txt",
        )

"""État de la vue générale CRM & Partenaires.

Toutes les lectures passent par `rx.asession()` en SQL brut paramétré. Les
agrégations (KPIs clients / fournisseurs / commerciaux, cadence mensuelle du
chiffre d'affaires et des achats, balance âgée des créances et des dettes, top
tiers, alertes d'échéance et de limite de crédit, recherche centralisée) sont
faites côté base : l'état ne conserve que des résultats prêts à afficher.

La synthèse « intelligente » est calculée localement à partir de ces agrégats,
sans aucun service externe.
"""

from __future__ import annotations

import datetime
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.states.dashboard_state import MONTHS, WEEKDAYS_SHORT

# Les colonnes Enum sont stockées par nom SQLAlchemy : on compare toujours en
# majuscules pour rester robuste quelle que soit la casse persistée.
CLIENT_KINDS_SQL = (
    "('CLIENT', 'MIXTE', 'GROSSISTE', 'DISTRIBUTEUR', 'REVENDEUR',"
    " 'COOPERATIVE')"
)
SUPPLIER_KINDS_SQL = (
    "('FOURNISSEUR', 'MIXTE', 'TRANSPORTEUR', 'PRESTATAIRE', 'COOPERATIVE')"
)

AGING_BUCKETS: list[str] = ["0-30", "31-60", "61-90", "90+"]

KIND_LABELS: dict[str, str] = {
    "CLIENT": "Client",
    "FOURNISSEUR": "Fournisseur",
    "MIXTE": "Client + Fournisseur",
    "TRANSPORTEUR": "Transporteur",
    "PRESTATAIRE": "Prestataire",
    "COOPERATIVE": "Coopérative",
    "GROSSISTE": "Grossiste",
    "DISTRIBUTEUR": "Distributeur",
    "REVENDEUR": "Revendeur",
    "AUTRE": "Autre partenaire",
}

STATUS_LABELS: dict[str, str] = {
    "ACTIF": "Actif",
    "INACTIF": "Inactif",
    "BLOQUE": "Bloqué",
    "PROSPECT": "Prospect",
    "ARCHIVE": "Archivé",
}


class Tab(TypedDict):
    key: str
    label: str
    icon: str


class MonthPoint(TypedDict):
    key: str
    label: str
    sales: float
    purchases: float
    sales_width: str
    purchases_width: str


class AgingPoint(TypedDict):
    bucket: str
    label: str
    amount: float
    count: int
    width: str


class PartnerRank(TypedDict):
    id: int
    code: str
    name: str
    kind_label: str
    amount: float
    deals: int
    outstanding: float
    score: int
    share: str
    width: str


class AlertRow(TypedDict):
    key: str
    icon: str
    tone: str
    title: str
    partner: str
    detail: str
    amount: float
    badge: str


class PartnerHit(TypedDict):
    id: int
    code: str
    name: str
    kind_label: str
    status_label: str
    city: str
    phone: str
    email: str
    turnover: float
    purchases: float
    outstanding: float
    debt: float
    score: int


class Insight(TypedDict):
    icon: str
    tone: str
    title: str
    detail: str


EMPTY_KPIS: dict[str, float] = {
    "partners": 0.0,
    "clients": 0.0,
    "clients_active": 0.0,
    "clients_new": 0.0,
    "clients_inactive": 0.0,
    "clients_blocked": 0.0,
    "suppliers": 0.0,
    "suppliers_active": 0.0,
    "suppliers_new": 0.0,
    "turnover": 0.0,
    "turnover_month": 0.0,
    "turnover_season": 0.0,
    "purchases": 0.0,
    "purchases_month": 0.0,
    "purchases_season": 0.0,
    "margin": 0.0,
    "margin_rate": 0.0,
    "receivable": 0.0,
    "receivable_overdue": 0.0,
    "payable": 0.0,
    "payable_overdue": 0.0,
    "received": 0.0,
    "paid_out": 0.0,
    "sales_count": 0.0,
    "purchases_count": 0.0,
    "unpaid_sales_invoices": 0.0,
    "late_sales_invoices": 0.0,
    "unpaid_purchase_invoices": 0.0,
    "late_purchase_invoices": 0.0,
    "due_soon": 0.0,
    "credit_alerts": 0.0,
    "net_cash": 0.0,
}


def _f(value: object) -> float:
    if value is None:
        return 0.0
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return 0.0


def _month_label(key: str) -> str:
    if len(key) == 7:
        index = int(key[5:7])
        return f"{MONTHS[index - 1]} {key[2:4]}"
    return key


def _build_aging_points(
    rows: list[tuple[object, object, object]],
) -> list[AgingPoint]:
    """Construit la balance âgée affichable (fonction privée de module)."""
    data = {
        str(row[0] or "0-30"): (_f(row[1]), int(row[2] or 0)) for row in rows
    }
    top = max([v[0] for v in data.values()] + [1.0])
    points: list[AgingPoint] = []
    for bucket in AGING_BUCKETS:
        amount, count = data.get(bucket, (0.0, 0))
        points.append(
            {
                "bucket": bucket,
                "label": f"{bucket} jours"
                if bucket != "90+"
                else "Plus de 90 jours",
                "amount": amount,
                "count": count,
                "width": f"{amount / top * 100:.0f}%",
            }
        )
    return points


def _build_partner_ranks(
    rows: list[
        tuple[object, object, object, object, object, object, object, object]
    ],
) -> list[PartnerRank]:
    """Construit le classement des tiers (fonction privée de module)."""
    amounts = [_f(row[4]) for row in rows]
    total = sum(amounts)
    top = max(amounts + [1.0])
    ranks: list[PartnerRank] = []
    for row in rows:
        amount = _f(row[4])
        ranks.append(
            {
                "id": int(row[0]),
                "code": str(row[1] or ""),
                "name": str(row[2] or ""),
                "kind_label": KIND_LABELS.get(row[3] or "", "Partenaire"),
                "amount": amount,
                "deals": int(row[5] or 0),
                "score": int(row[6] or 0),
                "outstanding": _f(row[7]),
                "share": f"{amount / total * 100:.0f}%" if total > 0 else "—",
                "width": f"{amount / top * 100:.0f}%",
            }
        )
    return ranks


def _month_keys(today: datetime.date, count: int = 12) -> list[str]:
    keys: list[str] = []
    year = today.year
    month = today.month
    for _ in range(count):
        keys.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(keys))


class CrmState(rx.State):
    """Cockpit commercial CRM : KPIs, graphiques, alertes, recherche."""

    is_loading: bool = True
    today_label: str = ""
    season_label: str = ""
    active_tab: str = "synthese"
    search: str = ""

    tabs: list[Tab] = [
        {
            "key": "synthese",
            "label": "Vue générale",
            "icon": "layout-dashboard",
        },
        {
            "key": "graphiques",
            "label": "Flux financiers",
            "icon": "bar-chart-3",
        },
        {"key": "clients", "label": "Clients", "icon": "users-round"},
        {
            "key": "fournisseurs",
            "label": "Fournisseurs",
            "icon": "truck",
        },
        {
            "key": "partenaires",
            "label": "Partenaires",
            "icon": "handshake",
        },
        {"key": "ventes", "label": "Ventes", "icon": "trending-up"},
        {"key": "achats", "label": "Achats", "icon": "shopping-cart"},
        {"key": "creances", "label": "Créances", "icon": "hand-coins"},
        {"key": "dettes", "label": "Dettes", "icon": "wallet"},
        {"key": "paiements", "label": "Paiements", "icon": "banknote"},
        {"key": "rapports", "label": "Rapports", "icon": "file-chart-column"},
        {"key": "tiers", "label": "Top tiers", "icon": "trophy"},
        {"key": "alertes", "label": "Échéances & risques", "icon": "bell-ring"},
        {"key": "recherche", "label": "Recherche tiers", "icon": "search"},
    ]

    kpis: dict[str, float] = EMPTY_KPIS
    months: list[MonthPoint] = []
    receivable_aging: list[AgingPoint] = []
    payable_aging: list[AgingPoint] = []
    top_clients: list[PartnerRank] = []
    top_suppliers: list[PartnerRank] = []
    alerts: list[AlertRow] = []
    search_results: list[PartnerHit] = []
    insights: list[Insight] = []

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def alert_count(self) -> int:
        return len(self.alerts)

    @rx.var
    def critical_alerts(self) -> int:
        return len([a for a in self.alerts if a["tone"] == "bad"])

    @rx.var
    def has_alerts(self) -> bool:
        return len(self.alerts) > 0

    @rx.var
    def result_count(self) -> int:
        return len(self.search_results)

    @rx.var
    def cash_label(self) -> str:
        net = self.kpis.get("net_cash", 0.0)
        if net > 0:
            return "Position nette favorable"
        if net < 0:
            return "Position nette à surveiller"
        return "Position nette équilibrée"

    @rx.var
    def margin_label(self) -> str:
        rate = self.kpis.get("margin_rate", 0.0)
        if rate >= 30:
            return "Marge commerciale confortable"
        if rate >= 15:
            return "Marge commerciale correcte"
        if rate > 0:
            return "Marge commerciale sous tension"
        return "Marge commerciale négative"

    # ------------------------------------------------------------------
    # Requêtes
    # ------------------------------------------------------------------

    async def _fetch_kpis(self, today: datetime.date) -> None:
        month_start = today.replace(day=1)
        season_start = (
            today.replace(month=9, day=1)
            if today.month >= 9
            else today.replace(year=today.year - 1, month=9, day=1)
        )
        recent = today - datetime.timedelta(days=90)
        params = {
            "month_start": month_start,
            "season_start": season_start,
            "recent": recent,
            "today": today,
        }
        async with rx.asession() as asession:
            partners = (
                await asession.execute(
                    text(
                        f"""
                        SELECT
                            COUNT(*),
                            SUM(CASE WHEN UPPER(kind) IN {CLIENT_KINDS_SQL}
                                THEN 1 ELSE 0 END),
                            SUM(CASE WHEN UPPER(kind) IN {CLIENT_KINDS_SQL}
                                AND UPPER(status) = 'ACTIF' THEN 1 ELSE 0 END),
                            SUM(CASE WHEN UPPER(kind) IN {CLIENT_KINDS_SQL}
                                AND first_deal_on IS NOT NULL
                                AND first_deal_on >= :recent THEN 1 ELSE 0 END),
                            SUM(CASE WHEN UPPER(kind) IN {CLIENT_KINDS_SQL}
                                AND UPPER(status) = 'INACTIF'
                                THEN 1 ELSE 0 END),
                            SUM(CASE WHEN UPPER(status) = 'BLOQUE'
                                THEN 1 ELSE 0 END),
                            SUM(CASE WHEN UPPER(kind) IN {SUPPLIER_KINDS_SQL}
                                THEN 1 ELSE 0 END),
                            SUM(CASE WHEN UPPER(kind) IN {SUPPLIER_KINDS_SQL}
                                AND UPPER(status) = 'ACTIF' THEN 1 ELSE 0 END),
                            SUM(CASE WHEN UPPER(kind) IN {SUPPLIER_KINDS_SQL}
                                AND first_deal_on IS NOT NULL
                                AND first_deal_on >= :recent THEN 1 ELSE 0 END)
                        FROM crm_partner
                        WHERE is_archived = false
                        """
                    ),
                    params,
                )
            ).first()
            sales = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            COALESCE(SUM(amount_ttc), 0),
                            COALESCE(SUM(CASE WHEN sale_date >= :month_start
                                THEN amount_ttc ELSE 0 END), 0),
                            COALESCE(SUM(CASE WHEN sale_date >= :season_start
                                THEN amount_ttc ELSE 0 END), 0),
                            COUNT(*)
                        FROM crm_sale
                        WHERE is_archived = false
                          AND UPPER(status) <> 'ANNULEE'
                        """
                    ),
                    params,
                )
            ).first()
            purchases = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            COALESCE(SUM(amount_ttc), 0),
                            COALESCE(SUM(CASE WHEN purchase_date >= :month_start
                                THEN amount_ttc ELSE 0 END), 0),
                            COALESCE(SUM(CASE WHEN purchase_date >= :season_start
                                THEN amount_ttc ELSE 0 END), 0),
                            COUNT(*)
                        FROM crm_purchase
                        WHERE is_archived = false
                          AND UPPER(status) <> 'ANNULEE'
                        """
                    ),
                    params,
                )
            ).first()
            settle = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            COALESCE(SUM(r.amount_remaining), 0),
                            COALESCE(SUM(CASE WHEN r.due_date IS NOT NULL
                                AND r.due_date < :today
                                THEN r.amount_remaining ELSE 0 END), 0),
                            COALESCE(SUM(CASE WHEN r.due_date IS NOT NULL
                                AND r.due_date >= :today
                                AND r.due_date <= :horizon
                                AND r.amount_remaining > 0.005
                                THEN 1 ELSE 0 END), 0)
                        FROM crm_receivable r
                        WHERE r.is_archived = false
                        """
                    ),
                    {
                        "today": today,
                        "horizon": today + datetime.timedelta(days=15),
                    },
                )
            ).first()
            debts = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            COALESCE(SUM(amount_remaining), 0),
                            COALESCE(SUM(CASE WHEN due_date IS NOT NULL
                                AND due_date < :today
                                THEN amount_remaining ELSE 0 END), 0)
                        FROM crm_payable
                        WHERE is_archived = false
                        """
                    ),
                    {"today": today},
                )
            ).first()
            payments = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            COALESCE(SUM(CASE WHEN UPPER(direction) =
                                'ENCAISSEMENT' THEN amount ELSE 0 END), 0),
                            COALESCE(SUM(CASE WHEN UPPER(direction) =
                                'DECAISSEMENT' THEN amount ELSE 0 END), 0)
                        FROM crm_payment
                        WHERE is_archived = false
                        """
                    )
                )
            ).first()
            invoices = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            SUM(CASE WHEN UPPER(kind) IN ('VENTE', 'AVOIR_VENTE')
                                AND UPPER(status) NOT IN
                                    ('PAYEE', 'ANNULEE', 'BROUILLON')
                                THEN 1 ELSE 0 END),
                            SUM(CASE WHEN UPPER(kind) IN ('VENTE', 'AVOIR_VENTE')
                                AND UPPER(status) = 'EN_RETARD'
                                THEN 1 ELSE 0 END),
                            SUM(CASE WHEN UPPER(kind) IN ('ACHAT', 'AVOIR_ACHAT')
                                AND UPPER(status) NOT IN
                                    ('PAYEE', 'ANNULEE', 'BROUILLON')
                                THEN 1 ELSE 0 END),
                            SUM(CASE WHEN UPPER(kind) IN ('ACHAT', 'AVOIR_ACHAT')
                                AND UPPER(status) = 'EN_RETARD'
                                THEN 1 ELSE 0 END)
                        FROM crm_invoice
                        WHERE is_archived = false
                        """
                    )
                )
            ).first()
            credit = (
                await asession.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM crm_partner p
                        WHERE p.is_archived = false
                          AND p.credit_limit > 0
                          AND (
                            SELECT COALESCE(SUM(r.amount_remaining), 0)
                            FROM crm_receivable r
                            WHERE r.partner_id = p.id
                              AND r.is_archived = false
                          ) > p.credit_limit
                        """
                    )
                )
            ).first()

        turnover_season = _f(sales[2] if sales else 0)
        purchases_season = _f(purchases[2] if purchases else 0)
        margin = round(turnover_season - purchases_season, 2)
        receivable = _f(settle[0] if settle else 0)
        payable = _f(debts[0] if debts else 0)
        async with self:
            self.kpis = {
                "partners": _f(partners[0] if partners else 0),
                "clients": _f(partners[1] if partners else 0),
                "clients_active": _f(partners[2] if partners else 0),
                "clients_new": _f(partners[3] if partners else 0),
                "clients_inactive": _f(partners[4] if partners else 0),
                "clients_blocked": _f(partners[5] if partners else 0),
                "suppliers": _f(partners[6] if partners else 0),
                "suppliers_active": _f(partners[7] if partners else 0),
                "suppliers_new": _f(partners[8] if partners else 0),
                "turnover": _f(sales[0] if sales else 0),
                "turnover_month": _f(sales[1] if sales else 0),
                "turnover_season": turnover_season,
                "sales_count": _f(sales[3] if sales else 0),
                "purchases": _f(purchases[0] if purchases else 0),
                "purchases_month": _f(purchases[1] if purchases else 0),
                "purchases_season": purchases_season,
                "purchases_count": _f(purchases[3] if purchases else 0),
                "margin": margin,
                "margin_rate": (
                    round(margin / turnover_season * 100, 1)
                    if turnover_season > 0
                    else 0.0
                ),
                "receivable": receivable,
                "receivable_overdue": _f(settle[1] if settle else 0),
                "due_soon": _f(settle[2] if settle else 0),
                "payable": payable,
                "payable_overdue": _f(debts[1] if debts else 0),
                "received": _f(payments[0] if payments else 0),
                "paid_out": _f(payments[1] if payments else 0),
                "unpaid_sales_invoices": _f(invoices[0] if invoices else 0),
                "late_sales_invoices": _f(invoices[1] if invoices else 0),
                "unpaid_purchase_invoices": _f(invoices[2] if invoices else 0),
                "late_purchase_invoices": _f(invoices[3] if invoices else 0),
                "credit_alerts": _f(credit[0] if credit else 0),
                "net_cash": round(receivable - payable, 2),
            }

    async def _fetch_months(self, today: datetime.date) -> None:
        keys = _month_keys(today)
        since = datetime.date.fromisoformat(f"{keys[0]}-01")
        async with rx.asession() as asession:
            sales = (
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
            purchases = (
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

        sales_map = {str(row[0]): _f(row[1]) for row in sales}
        purchases_map = {str(row[0]): _f(row[1]) for row in purchases}
        top = max(
            [*sales_map.values(), *purchases_map.values(), 1.0],
        )
        async with self:
            self.months = [
                {
                    "key": key,
                    "label": _month_label(key),
                    "sales": sales_map.get(key, 0.0),
                    "purchases": purchases_map.get(key, 0.0),
                    "sales_width": f"{sales_map.get(key, 0.0) / top * 100:.0f}%",
                    "purchases_width": (
                        f"{purchases_map.get(key, 0.0) / top * 100:.0f}%"
                    ),
                }
                for key in keys
            ]

    async def _fetch_aging(self) -> None:
        async with rx.asession() as asession:
            receivables = (
                await asession.execute(
                    text(
                        """
                        SELECT aging_bucket,
                               COALESCE(SUM(amount_remaining), 0),
                               COUNT(*)
                        FROM crm_receivable
                        WHERE is_archived = false
                          AND amount_remaining > 0.005
                        GROUP BY aging_bucket
                        """
                    )
                )
            ).all()
            payables = (
                await asession.execute(
                    text(
                        """
                        SELECT aging_bucket,
                               COALESCE(SUM(amount_remaining), 0),
                               COUNT(*)
                        FROM crm_payable
                        WHERE is_archived = false
                          AND amount_remaining > 0.005
                        GROUP BY aging_bucket
                        """
                    )
                )
            ).all()

        async with self:
            self.receivable_aging = _build_aging_points(receivables)
            self.payable_aging = _build_aging_points(payables)

    async def _fetch_tops(self) -> None:
        async with rx.asession() as asession:
            clients = (
                await asession.execute(
                    text(
                        f"""
                        SELECT p.id, p.code, p.legal_name, UPPER(p.kind),
                               COALESCE(SUM(s.amount_ttc), 0) AS ca,
                               COUNT(s.id),
                               COALESCE(p.score_value, 0),
                               (SELECT COALESCE(SUM(r.amount_remaining), 0)
                                  FROM crm_receivable r
                                  WHERE r.partner_id = p.id
                                    AND r.is_archived = false)
                        FROM crm_partner p
                        JOIN crm_sale s ON s.partner_id = p.id
                          AND s.is_archived = false
                          AND UPPER(s.status) <> 'ANNULEE'
                        WHERE p.is_archived = false
                          AND UPPER(p.kind) IN {CLIENT_KINDS_SQL}
                        GROUP BY p.id, p.code, p.legal_name, p.kind,
                                 p.score_value
                        ORDER BY ca DESC
                        LIMIT 10
                        """
                    )
                )
            ).all()
            suppliers = (
                await asession.execute(
                    text(
                        f"""
                        SELECT p.id, p.code, p.legal_name, UPPER(p.kind),
                               COALESCE(SUM(a.amount_ttc), 0) AS total,
                               COUNT(a.id),
                               COALESCE(p.score_value, 0),
                               (SELECT COALESCE(SUM(d.amount_remaining), 0)
                                  FROM crm_payable d
                                  WHERE d.partner_id = p.id
                                    AND d.is_archived = false)
                        FROM crm_partner p
                        JOIN crm_purchase a ON a.partner_id = p.id
                          AND a.is_archived = false
                          AND UPPER(a.status) <> 'ANNULEE'
                        WHERE p.is_archived = false
                          AND UPPER(p.kind) IN {SUPPLIER_KINDS_SQL}
                        GROUP BY p.id, p.code, p.legal_name, p.kind,
                                 p.score_value
                        ORDER BY total DESC
                        LIMIT 10
                        """
                    )
                )
            ).all()

        async with self:
            self.top_clients = _build_partner_ranks(clients)
            self.top_suppliers = _build_partner_ranks(suppliers)

    async def _fetch_alerts(self, today: datetime.date) -> None:
        horizon = today + datetime.timedelta(days=15)
        async with rx.asession() as asession:
            receivables = (
                await asession.execute(
                    text(
                        """
                        SELECT r.id, p.legal_name, i.code, r.due_date,
                               r.amount_remaining, r.overdue_days,
                               r.aging_bucket
                        FROM crm_receivable r
                        JOIN crm_partner p ON p.id = r.partner_id
                        LEFT JOIN crm_invoice i ON i.id = r.invoice_id
                        WHERE r.is_archived = false
                          AND r.amount_remaining > 0.005
                          AND r.due_date IS NOT NULL
                          AND r.due_date <= :horizon
                        ORDER BY r.due_date
                        LIMIT 25
                        """
                    ),
                    {"horizon": horizon},
                )
            ).all()
            payables = (
                await asession.execute(
                    text(
                        """
                        SELECT d.id, p.legal_name, i.code, d.due_date,
                               d.amount_remaining, d.overdue_days
                        FROM crm_payable d
                        JOIN crm_partner p ON p.id = d.partner_id
                        LEFT JOIN crm_invoice i ON i.id = d.invoice_id
                        WHERE d.is_archived = false
                          AND d.amount_remaining > 0.005
                          AND d.due_date IS NOT NULL
                          AND d.due_date <= :horizon
                        ORDER BY d.due_date
                        LIMIT 25
                        """
                    ),
                    {"horizon": horizon},
                )
            ).all()
            credit = (
                await asession.execute(
                    text(
                        """
                        SELECT p.id, p.legal_name, p.credit_limit,
                               (SELECT COALESCE(SUM(r.amount_remaining), 0)
                                  FROM crm_receivable r
                                  WHERE r.partner_id = p.id
                                    AND r.is_archived = false) AS encours
                        FROM crm_partner p
                        WHERE p.is_archived = false AND p.credit_limit > 0
                        ORDER BY encours DESC
                        LIMIT 25
                        """
                    )
                )
            ).all()

        alerts: list[AlertRow] = []
        for row in receivables:
            late = int(row[5] or 0)
            due = str(row[3] or "")
            alerts.append(
                {
                    "key": f"rec-{int(row[0])}",
                    "icon": "hand-coins",
                    "tone": "bad" if late > 0 else "warn",
                    "title": (
                        "Créance client en retard"
                        if late > 0
                        else "Créance client à échéance proche"
                    ),
                    "partner": str(row[1] or ""),
                    "detail": (
                        f"Facture {row[2] or '—'} · échéance {due}"
                        f" · tranche {row[6] or '0-30'}"
                    ),
                    "amount": _f(row[4]),
                    "badge": (
                        f"{late} j de retard" if late > 0 else "À encaisser"
                    ),
                }
            )
        for row in payables:
            late = int(row[5] or 0)
            due = str(row[3] or "")
            alerts.append(
                {
                    "key": f"pay-{int(row[0])}",
                    "icon": "wallet",
                    "tone": "bad" if late > 0 else "info",
                    "title": (
                        "Dette fournisseur en retard"
                        if late > 0
                        else "Dette fournisseur à régler"
                    ),
                    "partner": str(row[1] or ""),
                    "detail": f"Facture {row[2] or '—'} · échéance {due}",
                    "amount": _f(row[4]),
                    "badge": f"{late} j de retard"
                    if late > 0
                    else "À décaisser",
                }
            )
        for row in credit:
            limit = _f(row[2])
            outstanding = _f(row[3])
            if limit <= 0 or outstanding < limit * 0.8:
                continue
            exceeded = outstanding > limit
            alerts.append(
                {
                    "key": f"cred-{int(row[0])}",
                    "icon": "shield-alert",
                    "tone": "bad" if exceeded else "warn",
                    "title": (
                        "Limite de crédit dépassée"
                        if exceeded
                        else "Limite de crédit bientôt atteinte"
                    ),
                    "partner": str(row[1] or ""),
                    "detail": (
                        f"Encours {outstanding:.0f} DA pour une limite de"
                        f" {limit:.0f} DA"
                    ),
                    "amount": outstanding,
                    "badge": f"{outstanding / limit * 100:.0f}% de la limite",
                }
            )
        order = {"bad": 0, "warn": 1, "info": 2}
        alerts.sort(key=lambda a: (order.get(a["tone"], 3), -a["amount"]))
        async with self:
            self.alerts = alerts[:24]

    async def _fetch_partners(self) -> None:
        query = self.search.strip().lower()
        clauses = ["p.is_archived = false"]
        params: dict[str, str] = {}
        if query:
            clauses.append(
                "(LOWER(p.legal_name) LIKE :q OR LOWER(p.code) LIKE :q"
                " OR LOWER(COALESCE(p.trade_name, '')) LIKE :q"
                " OR LOWER(COALESCE(p.wilaya, '')) LIKE :q"
                " OR LOWER(COALESCE(p.commune, '')) LIKE :q"
                " OR LOWER(COALESCE(p.phone, '')) LIKE :q"
                " OR LOWER(COALESCE(p.email, '')) LIKE :q"
                " OR LOWER(COALESCE(p.category, '')) LIKE :q)"
            )
            params["q"] = f"%{query}%"
        where = " AND ".join(clauses)
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT p.id, p.code, p.legal_name, UPPER(p.kind),
                               UPPER(p.status),
                               TRIM(COALESCE(p.commune, '') || ' '
                                    || COALESCE(p.wilaya, '')),
                               COALESCE(p.phone, ''), COALESCE(p.email, ''),
                               COALESCE(p.score_value, 0),
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
                                    AND d.is_archived = false)
                        FROM crm_partner p
                        WHERE {where}
                        ORDER BY p.legal_name
                        LIMIT 40
                        """
                    ),
                    params,
                )
            ).all()

        async with self:
            self.search_results = [
                {
                    "id": int(row[0]),
                    "code": str(row[1] or ""),
                    "name": str(row[2] or ""),
                    "kind_label": KIND_LABELS.get(row[3] or "", "Partenaire"),
                    "status_label": STATUS_LABELS.get(row[4] or "", "Actif"),
                    "city": str(row[5] or "").strip()
                    or "Localisation non précisée",
                    "phone": str(row[6] or "") or "—",
                    "email": str(row[7] or "") or "—",
                    "score": int(row[8] or 0),
                    "turnover": _f(row[9]),
                    "purchases": _f(row[10]),
                    "outstanding": _f(row[11]),
                    "debt": _f(row[12]),
                }
                for row in rows
            ]

    async def _build_insights(self) -> None:
        """Synthèse intelligente locale, déduite des agrégats déjà chargés."""
        k = self.kpis
        insights: list[Insight] = []
        turnover = k.get("turnover_season", 0.0)
        purchases = k.get("purchases_season", 0.0)
        insights.append(
            {
                "icon": "sparkles",
                "tone": "good" if k.get("margin", 0.0) >= 0 else "bad",
                "title": "Équilibre commercial de la campagne",
                "detail": (
                    f"{turnover:.0f} DA de ventes contre {purchases:.0f} DA"
                    f" d'achats, soit une marge de {k.get('margin', 0.0):.0f} DA"
                    f" ({k.get('margin_rate', 0.0):.1f} %)."
                ),
            }
        )
        if self.top_clients:
            first = self.top_clients[0]
            insights.append(
                {
                    "icon": "crown",
                    "tone": "info",
                    "title": "Concentration du chiffre d'affaires",
                    "detail": (
                        f"{first['name']} pèse {first['share']} du CA suivi"
                        f" ({first['amount']:.0f} DA sur {first['deals']}"
                        " transaction(s)). Une dépendance à surveiller."
                    ),
                }
            )
        if self.top_suppliers:
            first = self.top_suppliers[0]
            insights.append(
                {
                    "icon": "truck",
                    "tone": "info",
                    "title": "Fournisseur critique",
                    "detail": (
                        f"{first['name']} concentre {first['share']} des achats"
                        f" ({first['amount']:.0f} DA) : sécuriser une source"
                        " alternative pour cette famille d'intrants."
                    ),
                }
            )
        overdue = k.get("receivable_overdue", 0.0)
        receivable = k.get("receivable", 0.0)
        if receivable > 0:
            insights.append(
                {
                    "icon": "hand-coins",
                    "tone": "bad" if overdue > 0 else "good",
                    "title": "Recouvrement clients",
                    "detail": (
                        f"{receivable:.0f} DA de créances ouvertes dont"
                        f" {overdue:.0f} DA échues"
                        f" ({(overdue / receivable * 100):.0f} % du poste)."
                        f" {k.get('due_soon', 0.0):.0f} échéance(s) tombent"
                        " sous 15 jours."
                    ),
                }
            )
        payable = k.get("payable", 0.0)
        if payable > 0:
            insights.append(
                {
                    "icon": "wallet",
                    "tone": (
                        "warn" if k.get("payable_overdue", 0.0) > 0 else "info"
                    ),
                    "title": "Trésorerie fournisseurs",
                    "detail": (
                        f"{payable:.0f} DA de dettes restantes dont"
                        f" {k.get('payable_overdue', 0.0):.0f} DA en retard."
                        f" Position nette : {k.get('net_cash', 0.0):.0f} DA."
                    ),
                }
            )
        if k.get("credit_alerts", 0.0) > 0:
            insights.append(
                {
                    "icon": "shield-alert",
                    "tone": "bad",
                    "title": "Limites de crédit",
                    "detail": (
                        f"{k.get('credit_alerts', 0.0):.0f} tiers dépassent"
                        " leur limite de crédit autorisée : bloquer les"
                        " nouvelles livraisons ou renégocier les conditions."
                    ),
                }
            )
        if k.get("clients_inactive", 0.0) > 0:
            insights.append(
                {
                    "icon": "search",
                    "tone": "warn",
                    "title": "Réactivation commerciale",
                    "detail": (
                        f"{k.get('clients_inactive', 0.0):.0f} client(s)"
                        " inactif(s) pour"
                        f" {k.get('clients_active', 0.0):.0f} actif(s) :"
                        " relancer les comptes dormants avant la prochaine"
                        " campagne."
                    ),
                }
            )
        best_month = ""
        best_amount = 0.0
        for point in self.months:
            if point["sales"] > best_amount:
                best_amount = point["sales"]
                best_month = point["label"]
        if best_amount > 0:
            insights.append(
                {
                    "icon": "trending-up",
                    "tone": "good",
                    "title": "Saisonnalité des ventes",
                    "detail": (
                        f"Le pic de ventes est observé en {best_month} avec"
                        f" {best_amount:.0f} DA. Anticiper stocks et logistique"
                        " sur cette fenêtre."
                    ),
                }
            )
        async with self:
            self.insights = insights

    # ------------------------------------------------------------------
    # Événements
    # ------------------------------------------------------------------

    @rx.event(background=True)
    async def load_crm(self):
        async with self:
            self.is_loading = True
        today = datetime.date.today()
        await self._fetch_kpis(today)
        await self._fetch_months(today)
        await self._fetch_aging()
        await self._fetch_tops()
        await self._fetch_alerts(today)
        await self._fetch_partners()
        await self._build_insights()
        async with self:
            self.today_label = (
                f"{WEEKDAYS_SHORT[today.weekday()]}. {today.day} "
                f"{MONTHS[today.month - 1]} {today.year}"
            )
            start = today.year if today.month >= 9 else today.year - 1
            self.season_label = f"Campagne {start}/{start + 1}"
            self.is_loading = False

    @rx.event
    def set_tab(self, value: str):
        self.active_tab = value

    @rx.event
    async def set_search(self, value: str):
        self.search = value
        await self._fetch_partners()

    @rx.event
    async def clear_search(self):
        self.search = ""
        await self._fetch_partners()

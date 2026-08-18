"""État du registre des charges et dépenses.

Types de dépenses personnalisables, dépenses libres rattachables à un actif
métier (parcelle, culture, salarié, engin, intervention, maintenance), filtres
multicritères, synthèses mensuelle et par type. Toutes les lectures et
écritures passent par `rx.asession()` en SQL brut paramétré.
"""

from __future__ import annotations

import datetime
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.date_utils import as_date, iso_or_empty
from app.seed import seed_dashboard_data
from app.seed_employees import seed_employee_data
from app.seed_equipment import seed_equipment_data
from app.seed_expenses import seed_expense_data
from app.seed_operations import seed_operations_data
from app.states.dashboard_state import MONTHS, WEEKDAYS_SHORT

EXPENSE_STATUS_KEYS: list[str] = ["BROUILLON", "ENGAGEE", "PAYEE", "ANNULEE"]

EXPENSE_STATUS_LABELS: dict[str, str] = {
    "BROUILLON": "Brouillon",
    "ENGAGEE": "Engagée",
    "PAYEE": "Payée",
    "ANNULEE": "Annulée",
}

EXPENSE_STATUS_TONES: dict[str, str] = {
    "BROUILLON": "muted",
    "ENGAGEE": "warn",
    "PAYEE": "good",
    "ANNULEE": "bad",
}

PAYMENT_KEYS: list[str] = [
    "VIREMENT",
    "PRELEVEMENT",
    "CARTE",
    "CHEQUE",
    "ESPECES",
    "AUTRE",
]

PAYMENT_LABELS: dict[str, str] = {
    "VIREMENT": "Virement",
    "PRELEVEMENT": "Prélèvement",
    "CARTE": "Carte bancaire",
    "CHEQUE": "Chèque",
    "ESPECES": "Espèces",
    "AUTRE": "Autre moyen",
}

LINK_KEYS: list[str] = [
    "PARCELLE",
    "CULTURE",
    "EMPLOYE",
    "ENGIN",
    "INTERVENTION",
    "MAINTENANCE",
    "AUCUN",
]

LINK_LABELS: dict[str, str] = {
    "PARCELLE": "Parcelle",
    "CULTURE": "Culture",
    "EMPLOYE": "Salarié",
    "ENGIN": "Engin",
    "INTERVENTION": "Intervention",
    "MAINTENANCE": "Maintenance",
    "AUCUN": "Sans rattachement",
}

LINK_ICONS: dict[str, str] = {
    "PARCELLE": "map",
    "CULTURE": "sprout",
    "EMPLOYE": "users-round",
    "ENGIN": "tractor",
    "INTERVENTION": "spray-can",
    "MAINTENANCE": "wrench",
    "AUCUN": "circle-dashed",
}

LINK_CLAUSES: dict[str, str] = {
    "PARCELLE": "x.parcel_id IS NOT NULL",
    "CULTURE": "x.crop_id IS NOT NULL",
    "EMPLOYE": "x.employee_id IS NOT NULL",
    "ENGIN": "x.equipment_id IS NOT NULL",
    "INTERVENTION": "x.intervention_id IS NOT NULL",
    "MAINTENANCE": "x.maintenance_id IS NOT NULL",
    "AUCUN": (
        "x.parcel_id IS NULL AND x.crop_id IS NULL AND x.employee_id IS NULL"
        " AND x.equipment_id IS NULL AND x.intervention_id IS NULL"
        " AND x.maintenance_id IS NULL"
    ),
}

PERIODS: list[tuple[str, str, int]] = [
    ("30", "30 j", 30),
    ("90", "90 j", 90),
    ("180", "6 mois", 180),
    ("365", "12 mois", 365),
    ("TOUT", "Tout", 0),
]


class Option(TypedDict):
    value: str
    label: str


class ExpenseRow(TypedDict):
    id: int
    label: str
    reference: str
    supplier: str
    invoice: str
    type_name: str
    type_color: str
    type_icon: str
    status: str
    status_label: str
    status_tone: str
    payment_label: str
    quantity: float
    unit: str
    amount_ht: float
    vat_rate: float
    amount_ttc: float
    date_label: str
    due_label: str
    paid_label: str
    link_kind: str
    link_label: str
    link_icon: str
    link_target: str
    notes: str
    is_archived: bool
    is_cancelled: bool


class TypeRow(TypedDict):
    id: int
    name: str
    code: str
    category: str
    description: str
    color: str
    icon: str
    is_active: bool
    is_archived: bool
    payment_label: str
    vat_rate: float
    expense_count: int
    total_ttc: float
    share: str


class MonthPoint(TypedDict):
    key: str
    label: str
    amount: float
    count: int
    width: str


EMPTY_EXPENSE_FORM: dict[str, str] = {
    "expense_type_id": "",
    "label": "",
    "reference": "",
    "supplier": "",
    "invoice_reference": "",
    "status": "ENGAGEE",
    "payment_method": "VIREMENT",
    "quantity": "1",
    "unit": "u",
    "amount_ht": "0",
    "vat_rate": "20",
    "incurred_on": "",
    "due_date": "",
    "paid_on": "",
    "parcel_id": "",
    "crop_id": "",
    "employee_id": "",
    "equipment_id": "",
    "intervention_id": "",
    "maintenance_id": "",
    "notes": "",
}

EMPTY_TYPE_FORM: dict[str, str] = {
    "name": "",
    "code": "",
    "category": "",
    "description": "",
    "color_hex": "#a3e635",
    "icon": "receipt-text",
    "default_payment_method": "VIREMENT",
    "default_vat_rate": "20",
    "notes": "",
}


def _fmt_date(value: object) -> str:
    day = as_date(value)
    if day is None:
        return "—"
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _to_float(raw: object, default: float = 0.0) -> float:
    if raw is None:
        return default
    value = str(raw).strip().replace(",", ".").replace(" ", "")
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _to_date(raw: object) -> datetime.date | None:
    if raw is None:
        return None
    value = str(raw).strip()
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


def _options(keys: list[str], labels: dict[str, str]) -> list[Option]:
    return [{"value": key, "label": labels.get(key, key)} for key in keys]


class ExpensesState(rx.State):
    """Registre financier agricole : types, dépenses, synthèses et KPIs."""

    is_loading: bool = True
    today_label: str = ""
    error: str = ""

    search: str = ""
    type_filter: str = "TOUS"
    status_filter: str = "TOUS"
    payment_filter: str = "TOUS"
    link_filter: str = "TOUS"
    start_date: str = ""
    end_date: str = ""
    period: str = "TOUT"
    include_archived: bool = False

    kpis: dict[str, float] = {
        "count": 0.0,
        "total_ttc": 0.0,
        "total_ht": 0.0,
        "paid": 0.0,
        "pending": 0.0,
        "month_total": 0.0,
        "year_total": 0.0,
        "average": 0.0,
        "cancelled": 0.0,
        "archived": 0.0,
        "types": 0.0,
        "active_types": 0.0,
        "overdue": 0.0,
        "filtered_total": 0.0,
    }

    expenses: list[ExpenseRow] = []
    types: list[TypeRow] = []
    months: list[MonthPoint] = []

    type_options: list[Option] = []
    parcel_options: list[Option] = []
    crop_options: list[Option] = []
    employee_options: list[Option] = []
    equipment_options: list[Option] = []
    intervention_options: list[Option] = []
    maintenance_options: list[Option] = []

    status_options: list[Option] = _options(
        EXPENSE_STATUS_KEYS, EXPENSE_STATUS_LABELS
    )
    payment_options: list[Option] = _options(PAYMENT_KEYS, PAYMENT_LABELS)
    link_options: list[Option] = _options(LINK_KEYS, LINK_LABELS)
    period_chips: list[Option] = [
        {"value": key, "label": label} for key, label, _ in PERIODS
    ]

    show_expense_form: bool = False
    expense_form_mode: str = "create"
    editing_expense_id: int = 0
    expense_form: dict[str, str] = EMPTY_EXPENSE_FORM
    expense_error: str = ""

    show_type_form: bool = False
    type_form_mode: str = "create"
    editing_type_id: int = 0
    type_form: dict[str, str] = EMPTY_TYPE_FORM
    type_error: str = ""

    form_key: int = 0

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def expense_count(self) -> int:
        return len(self.expenses)

    @rx.var
    def type_count(self) -> int:
        return len(self.types)

    @rx.var
    def shown_total(self) -> float:
        return round(sum(e["amount_ttc"] for e in self.expenses), 2)

    @rx.var
    def has_expenses(self) -> bool:
        return len(self.expenses) > 0

    @rx.var
    def range_label(self) -> str:
        start = _to_date(self.start_date)
        end = _to_date(self.end_date)
        if start and end:
            return f"{_fmt_date(start)} → {_fmt_date(end)}"
        if start:
            return f"Depuis le {_fmt_date(start)}"
        if end:
            return f"Jusqu'au {_fmt_date(end)}"
        return "Tout l'historique"

    @rx.var
    def scope_label(self) -> str:
        if self.type_filter == "TOUS":
            return "Tous les types de charges"
        for item in self.types:
            if str(item["id"]) == self.type_filter:
                return f"Filtré sur : {item['name']}"
        return "Périmètre filtré"

    @rx.var
    def expense_form_title(self) -> str:
        if self.expense_form_mode == "edit":
            return "Modifier la dépense"
        return "Nouvelle dépense"

    @rx.var
    def type_form_title(self) -> str:
        if self.type_form_mode == "edit":
            return "Modifier le type de dépense"
        return "Nouveau type de dépense"

    # ------------------------------------------------------------------
    # Requêtes
    # ------------------------------------------------------------------

    def _filters(self) -> tuple[str, dict[str, str | int | datetime.date]]:
        clauses = ["1=1"]
        params: dict[str, str | int | datetime.date] = {}
        if not self.include_archived:
            clauses.append("x.is_archived = false")
        query = self.search.strip().lower()
        if query:
            clauses.append(
                "(LOWER(x.label) LIKE :q OR LOWER(COALESCE(x.supplier, '')) LIKE :q"
                " OR LOWER(COALESCE(x.reference, '')) LIKE :q"
                " OR LOWER(COALESCE(x.invoice_reference, '')) LIKE :q"
                " OR LOWER(COALESCE(x.notes, '')) LIKE :q"
                " OR LOWER(t.name) LIKE :q)"
            )
            params["q"] = f"%{query}%"
        if self.type_filter != "TOUS":
            clauses.append("x.expense_type_id = :tid")
            params["tid"] = int(self.type_filter)
        if self.status_filter != "TOUS":
            clauses.append("x.status = :status")
            params["status"] = self.status_filter
        if self.payment_filter != "TOUS":
            clauses.append("x.payment_method = :payment")
            params["payment"] = self.payment_filter
        if self.link_filter != "TOUS":
            clauses.append(f"({LINK_CLAUSES[self.link_filter]})")
        start = _to_date(self.start_date)
        end = _to_date(self.end_date)
        if start is not None:
            clauses.append("x.incurred_on >= :start")
            params["start"] = start
        if end is not None:
            clauses.append("x.incurred_on <= :end")
            params["end"] = end
        return " AND ".join(clauses), params

    async def _fetch_kpis(self) -> None:
        today = datetime.date.today()
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)
        where, params = self._filters()
        full: dict[str, str | int | datetime.date] = dict(params)
        full["month_start"] = month_start
        full["year_start"] = year_start
        full["today"] = today
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        f"""
                        SELECT
                            COUNT(*),
                            COALESCE(SUM(CASE WHEN x.status <> 'ANNULEE'
                                THEN x.amount_ttc ELSE 0 END), 0),
                            COALESCE(SUM(CASE WHEN x.status <> 'ANNULEE'
                                THEN x.amount_ht ELSE 0 END), 0),
                            COALESCE(SUM(CASE WHEN x.status = 'PAYEE'
                                THEN x.amount_ttc ELSE 0 END), 0),
                            COALESCE(SUM(CASE WHEN x.status IN ('ENGAGEE', 'BROUILLON')
                                THEN x.amount_ttc ELSE 0 END), 0),
                            SUM(CASE WHEN x.status = 'ANNULEE' THEN 1 ELSE 0 END),
                            SUM(CASE WHEN x.is_archived THEN 1 ELSE 0 END),
                            SUM(CASE WHEN x.status IN ('ENGAGEE', 'BROUILLON')
                                AND x.due_date IS NOT NULL AND x.due_date < :today
                                THEN 1 ELSE 0 END)
                        FROM expense x
                        JOIN expense_type t ON t.id = x.expense_type_id
                        WHERE {where}
                        """
                    ),
                    full,
                )
            ).first()
            glob = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            COALESCE(SUM(CASE WHEN incurred_on >= :month_start
                                AND status <> 'ANNULEE' AND is_archived = false
                                THEN amount_ttc ELSE 0 END), 0),
                            COALESCE(SUM(CASE WHEN incurred_on >= :year_start
                                AND status <> 'ANNULEE' AND is_archived = false
                                THEN amount_ttc ELSE 0 END), 0)
                        FROM expense
                        """
                    ),
                    {"month_start": month_start, "year_start": year_start},
                )
            ).first()
            type_row = (
                await asession.execute(
                    text(
                        """
                        SELECT COUNT(*),
                               SUM(CASE WHEN is_active AND NOT is_archived
                                   THEN 1 ELSE 0 END)
                        FROM expense_type
                        """
                    )
                )
            ).first()

        count = float(row[0] or 0) if row else 0.0
        total = float(row[1] or 0) if row else 0.0
        self.kpis = {
            "count": count,
            "total_ttc": total,
            "total_ht": float(row[2] or 0) if row else 0.0,
            "paid": float(row[3] or 0) if row else 0.0,
            "pending": float(row[4] or 0) if row else 0.0,
            "cancelled": float(row[5] or 0) if row else 0.0,
            "archived": float(row[6] or 0) if row else 0.0,
            "overdue": float(row[7] or 0) if row else 0.0,
            "month_total": float(glob[0] or 0) if glob else 0.0,
            "year_total": float(glob[1] or 0) if glob else 0.0,
            "average": round(total / count, 2) if count else 0.0,
            "types": float(type_row[0] or 0) if type_row else 0.0,
            "active_types": float(type_row[1] or 0) if type_row else 0.0,
            "filtered_total": total,
        }

    async def _fetch_expenses(self) -> None:
        where, params = self._filters()
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT x.id, x.label, COALESCE(x.reference, ''),
                               COALESCE(x.supplier, ''),
                               COALESCE(x.invoice_reference, ''),
                               t.name, COALESCE(t.color_hex, '#a3e635'),
                               COALESCE(t.icon, 'receipt-text'),
                               x.status, x.payment_method,
                               COALESCE(x.quantity, 0), COALESCE(x.unit, ''),
                               COALESCE(x.amount_ht, 0), COALESCE(x.vat_rate, 0),
                               COALESCE(x.amount_ttc, 0),
                               x.incurred_on, x.due_date, x.paid_on,
                               COALESCE(x.notes, ''), x.is_archived,
                               COALESCE(p.name, ''), COALESCE(c.name, ''),
                               COALESCE(e.first_name || ' ' || e.last_name, ''),
                               COALESCE(eq.name, ''), COALESCE(i.title, ''),
                               COALESCE(o.title, '')
                        FROM expense x
                        JOIN expense_type t ON t.id = x.expense_type_id
                        LEFT JOIN parcel p ON p.id = x.parcel_id
                        LEFT JOIN crop c ON c.id = x.crop_id
                        LEFT JOIN employee e ON e.id = x.employee_id
                        LEFT JOIN equipment eq ON eq.id = x.equipment_id
                        LEFT JOIN intervention i ON i.id = x.intervention_id
                        LEFT JOIN maintenance_operation o ON o.id = x.maintenance_id
                        WHERE {where}
                        ORDER BY x.incurred_on DESC NULLS LAST, x.id DESC
                        LIMIT 120
                        """
                    ),
                    params,
                )
            ).all()

        expenses: list[ExpenseRow] = []
        for row in rows:
            status = str(row[8])
            payment = str(row[9])
            link_kind = "AUCUN"
            link_target = ""
            for kind, index in (
                ("PARCELLE", 20),
                ("CULTURE", 21),
                ("EMPLOYE", 22),
                ("ENGIN", 23),
                ("INTERVENTION", 24),
                ("MAINTENANCE", 25),
            ):
                value = str(row[index] or "").strip()
                if value:
                    link_kind = kind
                    link_target = value
                    break
            expenses.append(
                {
                    "id": int(row[0]),
                    "label": str(row[1]),
                    "reference": str(row[2]) or "—",
                    "supplier": str(row[3]) or "Fournisseur non précisé",
                    "invoice": str(row[4]) or "—",
                    "type_name": str(row[5]),
                    "type_color": str(row[6]),
                    "type_icon": str(row[7]),
                    "status": status,
                    "status_label": EXPENSE_STATUS_LABELS.get(status, status),
                    "status_tone": EXPENSE_STATUS_TONES.get(status, "muted"),
                    "payment_label": PAYMENT_LABELS.get(payment, payment),
                    "quantity": float(row[10] or 0),
                    "unit": str(row[11]) or "u",
                    "amount_ht": float(row[12] or 0),
                    "vat_rate": float(row[13] or 0),
                    "amount_ttc": float(row[14] or 0),
                    "date_label": _fmt_date(row[15]),
                    "due_label": _fmt_date(row[16]),
                    "paid_label": _fmt_date(row[17]),
                    "notes": str(row[18]) or "Aucun commentaire consigné.",
                    "is_archived": bool(row[19]),
                    "is_cancelled": status == "ANNULEE",
                    "link_kind": link_kind,
                    "link_label": LINK_LABELS[link_kind],
                    "link_icon": LINK_ICONS[link_kind],
                    "link_target": link_target or "Charge de structure",
                }
            )
        self.expenses = expenses

    async def _fetch_types(self) -> None:
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT t.id, t.name, COALESCE(t.code, ''),
                               COALESCE(t.category, ''),
                               COALESCE(t.description, ''),
                               COALESCE(t.color_hex, '#a3e635'),
                               COALESCE(t.icon, 'receipt-text'),
                               t.is_active, t.is_archived,
                               t.default_payment_method,
                               COALESCE(t.default_vat_rate, 0),
                               (SELECT COUNT(*) FROM expense x
                                  WHERE x.expense_type_id = t.id
                                    AND x.is_archived = false),
                               (SELECT COALESCE(SUM(x.amount_ttc), 0) FROM expense x
                                  WHERE x.expense_type_id = t.id
                                    AND x.is_archived = false
                                    AND x.status <> 'ANNULEE')
                        FROM expense_type t
                        ORDER BY t.is_archived, t.name
                        LIMIT 60
                        """
                    )
                )
            ).all()

        totals = [float(row[12] or 0) for row in rows]
        top = max(totals) if totals else 0.0
        types: list[TypeRow] = []
        for row in rows:
            total = float(row[12] or 0)
            payment = str(row[9])
            types.append(
                {
                    "id": int(row[0]),
                    "name": str(row[1]),
                    "code": str(row[2]) or "—",
                    "category": str(row[3]) or "Sans catégorie",
                    "description": str(row[4]) or "Aucune description.",
                    "color": str(row[5]),
                    "icon": str(row[6]),
                    "is_active": bool(row[7]),
                    "is_archived": bool(row[8]),
                    "payment_label": PAYMENT_LABELS.get(payment, payment),
                    "vat_rate": float(row[10] or 0),
                    "expense_count": int(row[11] or 0),
                    "total_ttc": total,
                    "share": f"{(total / top * 100) if top else 0:.0f}%",
                }
            )
        self.types = types
        self.type_options = [
            {"value": str(t["id"]), "label": f"{t['code']} · {t['name']}"}
            for t in types
            if t["is_active"] and not t["is_archived"]
        ]

    async def _fetch_months(self) -> None:
        today = datetime.date.today()
        since = (today.replace(day=1) - datetime.timedelta(days=340)).replace(
            day=1
        )
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT strftime('%Y-%m', incurred_on) AS m,
                               COALESCE(SUM(amount_ttc), 0), COUNT(*)
                        FROM expense
                        WHERE is_archived = false AND status <> 'ANNULEE'
                          AND incurred_on IS NOT NULL AND incurred_on >= :since
                        GROUP BY m
                        ORDER BY m
                        """
                    ),
                    {"since": since},
                )
            ).all()

        amounts = [float(row[1] or 0) for row in rows]
        top = max(amounts) if amounts else 0.0
        months: list[MonthPoint] = []
        for row in rows:
            key = str(row[0] or "")
            amount = float(row[1] or 0)
            label = key
            if len(key) == 7:
                month_index = int(key[5:7])
                label = f"{MONTHS[month_index - 1]} {key[2:4]}"
            months.append(
                {
                    "key": key,
                    "label": label,
                    "amount": amount,
                    "count": int(row[2] or 0),
                    "width": f"{(amount / top * 100) if top else 0:.0f}%",
                }
            )
        self.months = months

    async def _fetch_reference(self) -> None:
        async with rx.asession() as asession:
            parcels = (
                await asession.execute(
                    text(
                        "SELECT id, COALESCE(code, ''), name FROM parcel"
                        " ORDER BY code, name LIMIT 200"
                    )
                )
            ).all()
            crops = (
                await asession.execute(
                    text(
                        "SELECT id, name, COALESCE(season, '') FROM crop"
                        " ORDER BY name LIMIT 200"
                    )
                )
            ).all()
            employees = (
                await asession.execute(
                    text(
                        "SELECT id, first_name, last_name FROM employee"
                        " WHERE status <> 'SORTI' ORDER BY last_name LIMIT 200"
                    )
                )
            ).all()
            equipments = (
                await asession.execute(
                    text(
                        "SELECT id, COALESCE(code, ''), name FROM equipment"
                        " ORDER BY code, name LIMIT 200"
                    )
                )
            ).all()
            interventions = (
                await asession.execute(
                    text(
                        "SELECT id, title FROM intervention"
                        " ORDER BY COALESCE(done_date, scheduled_date) DESC"
                        " LIMIT 120"
                    )
                )
            ).all()
            maintenances = (
                await asession.execute(
                    text(
                        "SELECT id, title FROM maintenance_operation"
                        " ORDER BY COALESCE(done_date, scheduled_date) DESC"
                        " LIMIT 120"
                    )
                )
            ).all()

        self.parcel_options = [
            {"value": str(int(r[0])), "label": f"{r[1]} · {r[2]}"}
            for r in parcels
        ]
        self.crop_options = [
            {"value": str(int(r[0])), "label": f"{r[1]} ({r[2]})"}
            for r in crops
        ]
        self.employee_options = [
            {"value": str(int(r[0])), "label": f"{r[1]} {r[2]}"}
            for r in employees
        ]
        self.equipment_options = [
            {"value": str(int(r[0])), "label": f"{r[1]} · {r[2]}"}
            for r in equipments
        ]
        self.intervention_options = [
            {"value": str(int(r[0])), "label": str(r[1])} for r in interventions
        ]
        self.maintenance_options = [
            {"value": str(int(r[0])), "label": str(r[1])} for r in maintenances
        ]

    async def _refresh(self) -> None:
        await self._fetch_types()
        await self._fetch_expenses()
        await self._fetch_kpis()
        await self._fetch_months()

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    @rx.event
    async def load_expenses(self):
        self.is_loading = True
        yield
        await seed_dashboard_data()
        await seed_operations_data()
        await seed_employee_data()
        await seed_equipment_data()
        await seed_expense_data()
        await self._fetch_reference()
        await self._refresh()
        today = datetime.date.today()
        self.today_label = (
            f"{WEEKDAYS_SHORT[today.weekday()]}. {today.day} "
            f"{MONTHS[today.month - 1]} {today.year}"
        )
        self.is_loading = False

    # ------------------------------------------------------------------
    # Filtres
    # ------------------------------------------------------------------

    @rx.event
    async def set_search(self, value: str):
        self.search = value
        await self._fetch_expenses()
        await self._fetch_kpis()

    @rx.event
    async def set_type_filter(self, value: str):
        self.type_filter = value
        await self._fetch_expenses()
        await self._fetch_kpis()

    @rx.event
    async def set_status_filter(self, value: str):
        self.status_filter = value
        await self._fetch_expenses()
        await self._fetch_kpis()

    @rx.event
    async def set_payment_filter(self, value: str):
        self.payment_filter = value
        await self._fetch_expenses()
        await self._fetch_kpis()

    @rx.event
    async def set_link_filter(self, value: str):
        self.link_filter = value
        await self._fetch_expenses()
        await self._fetch_kpis()

    @rx.event
    async def set_start_date(self, value: str):
        self.start_date = value
        self.period = "PERSO"
        self.error = self._validate_range()
        await self._fetch_expenses()
        await self._fetch_kpis()

    @rx.event
    async def set_end_date(self, value: str):
        self.end_date = value
        self.period = "PERSO"
        self.error = self._validate_range()
        await self._fetch_expenses()
        await self._fetch_kpis()

    @rx.event
    async def set_period(self, value: str):
        self.period = value
        today = datetime.date.today()
        days = 0
        for key, _label, span in PERIODS:
            if key == value:
                days = span
        if days > 0:
            self.start_date = (
                today - datetime.timedelta(days=days)
            ).isoformat()
            self.end_date = today.isoformat()
        else:
            self.start_date = ""
            self.end_date = ""
        self.error = ""
        self.form_key += 1
        await self._fetch_expenses()
        await self._fetch_kpis()

    @rx.event
    async def toggle_archived(self):
        self.include_archived = not self.include_archived
        await self._fetch_expenses()
        await self._fetch_kpis()

    @rx.event
    async def reset_filters(self):
        self.search = ""
        self.type_filter = "TOUS"
        self.status_filter = "TOUS"
        self.payment_filter = "TOUS"
        self.link_filter = "TOUS"
        self.start_date = ""
        self.end_date = ""
        self.period = "TOUT"
        self.include_archived = False
        self.error = ""
        self.form_key += 1
        await self._fetch_expenses()
        await self._fetch_kpis()

    def _validate_range(self) -> str:
        start = _to_date(self.start_date)
        end = _to_date(self.end_date)
        if self.start_date and start is None:
            return "Date de début invalide."
        if self.end_date and end is None:
            return "Date de fin invalide."
        if start and end and end < start:
            return "La date de fin doit suivre la date de début."
        return ""

    # ------------------------------------------------------------------
    # Formulaire dépense
    # ------------------------------------------------------------------

    @rx.event
    def open_expense_create(self):
        form = dict(EMPTY_EXPENSE_FORM)
        form["incurred_on"] = datetime.date.today().isoformat()
        if self.type_options:
            form["expense_type_id"] = self.type_options[0]["value"]
        self.expense_form = form
        self.expense_form_mode = "create"
        self.editing_expense_id = 0
        self.expense_error = ""
        self.form_key += 1
        self.show_expense_form = True

    @rx.event
    async def open_expense_edit(self, expense_id: int):
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT expense_type_id, label, COALESCE(reference, ''),
                               COALESCE(supplier, ''),
                               COALESCE(invoice_reference, ''), status,
                               payment_method, COALESCE(quantity, 0),
                               COALESCE(unit, ''), COALESCE(amount_ht, 0),
                               COALESCE(vat_rate, 0), incurred_on, due_date,
                               paid_on, parcel_id, crop_id, employee_id,
                               equipment_id, intervention_id, maintenance_id,
                               COALESCE(notes, '')
                        FROM expense WHERE id = :xid
                        """
                    ),
                    {"xid": expense_id},
                )
            ).first()
        if row is None:
            return rx.toast("Dépense introuvable.")
        self.expense_form = {
            "expense_type_id": str(int(row[0])),
            "label": str(row[1]),
            "reference": str(row[2]),
            "supplier": str(row[3]),
            "invoice_reference": str(row[4]),
            "status": str(row[5]),
            "payment_method": str(row[6]),
            "quantity": f"{float(row[7]):.2f}",
            "unit": str(row[8]) or "u",
            "amount_ht": f"{float(row[9]):.2f}",
            "vat_rate": f"{float(row[10]):.2f}",
            "incurred_on": iso_or_empty(row[11]),
            "due_date": iso_or_empty(row[12]),
            "paid_on": iso_or_empty(row[13]),
            "parcel_id": str(int(row[14])) if row[14] else "",
            "crop_id": str(int(row[15])) if row[15] else "",
            "employee_id": str(int(row[16])) if row[16] else "",
            "equipment_id": str(int(row[17])) if row[17] else "",
            "intervention_id": str(int(row[18])) if row[18] else "",
            "maintenance_id": str(int(row[19])) if row[19] else "",
            "notes": str(row[20]),
        }
        self.expense_form_mode = "edit"
        self.editing_expense_id = expense_id
        self.expense_error = ""
        self.form_key += 1
        self.show_expense_form = True

    @rx.event
    def close_expense_form(self):
        self.show_expense_form = False
        self.expense_error = ""

    def _validate_expense(self, data: dict) -> str:
        label = str(data.get("label", "")).strip()
        type_raw = str(data.get("expense_type_id", "")).strip()
        amount = _to_float(data.get("amount_ht"), -1.0)
        vat = _to_float(data.get("vat_rate"), -1.0)
        quantity = _to_float(data.get("quantity"), -1.0)
        incurred = _to_date(data.get("incurred_on"))
        due = _to_date(data.get("due_date"))
        paid = _to_date(data.get("paid_on"))
        status = str(data.get("status", "ENGAGEE"))
        limit = datetime.date.today() + datetime.timedelta(days=730)
        if len(label) < 3:
            return "L'intitulé doit contenir au moins 3 caractères."
        if not type_raw:
            return "Sélectionnez un type de dépense."
        if amount <= 0:
            return "Le montant HT doit être strictement positif."
        if amount > 5_000_000:
            return "Le montant HT semble erroné (plafond 5 000 000 €)."
        if vat < 0 or vat > 100:
            return "Le taux de TVA doit être compris entre 0 et 100 %."
        if quantity <= 0:
            return "La quantité doit être strictement positive."
        if incurred is None:
            return "La date d'engagement est obligatoire."
        if incurred > limit:
            return "La date d'engagement est trop éloignée dans le futur."
        if due is not None and due < incurred:
            return "L'échéance de règlement doit suivre la date d'engagement."
        if paid is not None and paid < incurred:
            return "La date de paiement doit suivre la date d'engagement."
        if status == "PAYEE" and paid is None and due is None:
            return "Renseignez la date de paiement pour une dépense payée."
        return ""

    @rx.event
    async def submit_expense(self, form_data: dict):
        error = self._validate_expense(form_data)
        if error:
            self.expense_error = error
            return
        amount_ht = _to_float(form_data.get("amount_ht"))
        vat = _to_float(form_data.get("vat_rate"))
        incurred = _to_date(form_data.get("incurred_on"))
        status = str(form_data.get("status", "ENGAGEE"))
        paid = _to_date(form_data.get("paid_on"))
        if status == "PAYEE" and paid is None:
            paid = incurred
        if status != "PAYEE":
            paid = None

        @rx.event
        def link(name: str) -> int | None:
            raw = str(form_data.get(name, "")).strip()
            return int(raw) if raw else None

        params: dict[str, str | int | float | datetime.date | None] = {
            "expense_type_id": int(form_data.get("expense_type_id")),
            "label": str(form_data.get("label", "")).strip(),
            "reference": str(form_data.get("reference", "")).strip(),
            "supplier": str(form_data.get("supplier", "")).strip(),
            "invoice_reference": str(
                form_data.get("invoice_reference", "")
            ).strip(),
            "status": status,
            "payment_method": str(form_data.get("payment_method", "VIREMENT")),
            "quantity": _to_float(form_data.get("quantity"), 1.0),
            "unit": str(form_data.get("unit", "u")).strip() or "u",
            "amount_ht": amount_ht,
            "vat_rate": vat,
            "amount_ttc": round(amount_ht * (1 + vat / 100.0), 2),
            "incurred_on": incurred,
            "due_date": _to_date(form_data.get("due_date")),
            "paid_on": paid,
            "parcel_id": link("parcel_id"),
            "crop_id": link("crop_id"),
            "employee_id": link("employee_id"),
            "equipment_id": link("equipment_id"),
            "intervention_id": link("intervention_id"),
            "maintenance_id": link("maintenance_id"),
            "notes": str(form_data.get("notes", "")).strip(),
        }

        async with rx.asession() as asession:
            if self.expense_form_mode == "edit" and self.editing_expense_id > 0:
                params["xid"] = self.editing_expense_id
                await asession.execute(
                    text(
                        """
                        UPDATE expense SET
                            expense_type_id = :expense_type_id, label = :label,
                            reference = :reference, supplier = :supplier,
                            invoice_reference = :invoice_reference,
                            status = :status, payment_method = :payment_method,
                            quantity = :quantity, unit = :unit,
                            amount_ht = :amount_ht, vat_rate = :vat_rate,
                            amount_ttc = :amount_ttc, incurred_on = :incurred_on,
                            due_date = :due_date, paid_on = :paid_on,
                            parcel_id = :parcel_id, crop_id = :crop_id,
                            employee_id = :employee_id,
                            equipment_id = :equipment_id,
                            intervention_id = :intervention_id,
                            maintenance_id = :maintenance_id, notes = :notes
                        WHERE id = :xid
                        """
                    ),
                    params,
                )
                message = "Dépense mise à jour."
            else:
                await asession.execute(
                    text(
                        """
                        INSERT INTO expense (
                            expense_type_id, label, reference, supplier,
                            invoice_reference, status, payment_method, quantity,
                            unit, amount_ht, vat_rate, amount_ttc, incurred_on,
                            due_date, paid_on, parcel_id, crop_id, employee_id,
                            equipment_id, intervention_id, maintenance_id,
                            is_archived, notes
                        ) VALUES (
                            :expense_type_id, :label, :reference, :supplier,
                            :invoice_reference, :status, :payment_method, :quantity,
                            :unit, :amount_ht, :vat_rate, :amount_ttc, :incurred_on,
                            :due_date, :paid_on, :parcel_id, :crop_id, :employee_id,
                            :equipment_id, :intervention_id, :maintenance_id,
                            false, :notes
                        )
                        """
                    ),
                    params,
                )
                message = "Dépense enregistrée au registre."
            await asession.commit()

        self.show_expense_form = False
        self.expense_error = ""
        self.form_key += 1
        await self._refresh()
        return rx.toast(message, duration=4000)

    # ------------------------------------------------------------------
    # Cycle de vie d'une dépense
    # ------------------------------------------------------------------

    @rx.event
    async def mark_paid(self, expense_id: int):
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE expense
                    SET status = 'PAYEE',
                        paid_on = COALESCE(paid_on, :today)
                    WHERE id = :xid AND status IN ('BROUILLON', 'ENGAGEE')
                    """
                ),
                {"today": datetime.date.today(), "xid": expense_id},
            )
            await asession.commit()
        await self._refresh()
        return rx.toast("Dépense marquée comme payée.", duration=3000)

    @rx.event
    async def cancel_expense(self, expense_id: int):
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text("SELECT status FROM expense WHERE id = :xid"),
                    {"xid": expense_id},
                )
            ).first()
            if row is None:
                return rx.toast("Dépense introuvable.")
            if str(row[0]) == "ANNULEE":
                return rx.toast("Cette dépense est déjà annulée.")
            await asession.execute(
                text(
                    """
                    UPDATE expense SET status = 'ANNULEE', paid_on = NULL
                    WHERE id = :xid
                    """
                ),
                {"xid": expense_id},
            )
            await asession.commit()
        await self._refresh()
        return rx.toast(
            "Dépense annulée, la ligne reste tracée au registre.",
            duration=4000,
        )

    @rx.event
    async def archive_expense(self, expense_id: int):
        async with rx.asession() as asession:
            await asession.execute(
                text("UPDATE expense SET is_archived = true WHERE id = :xid"),
                {"xid": expense_id},
            )
            await asession.commit()
        await self._refresh()
        return rx.toast("Dépense archivée.", duration=3000)

    @rx.event
    async def restore_expense(self, expense_id: int):
        async with rx.asession() as asession:
            await asession.execute(
                text("UPDATE expense SET is_archived = false WHERE id = :xid"),
                {"xid": expense_id},
            )
            await asession.commit()
        await self._refresh()
        return rx.toast("Dépense réintégrée au registre actif.", duration=3000)

    # ------------------------------------------------------------------
    # Formulaire type de dépense
    # ------------------------------------------------------------------

    @rx.event
    def open_type_create(self):
        self.type_form = dict(EMPTY_TYPE_FORM)
        self.type_form_mode = "create"
        self.editing_type_id = 0
        self.type_error = ""
        self.form_key += 1
        self.show_type_form = True

    @rx.event
    def open_type_edit(self, type_id: int):
        for item in self.types:
            if item["id"] == type_id:
                self.type_form = {
                    "name": item["name"],
                    "code": "" if item["code"] == "—" else item["code"],
                    "category": item["category"],
                    "description": item["description"],
                    "color_hex": item["color"],
                    "icon": item["icon"],
                    "default_payment_method": "VIREMENT",
                    "default_vat_rate": f"{item['vat_rate']:.2f}",
                    "notes": "",
                }
                self.type_form_mode = "edit"
                self.editing_type_id = type_id
                self.type_error = ""
                self.form_key += 1
                self.show_type_form = True
                return
        return rx.toast("Type de dépense introuvable.")

    @rx.event
    def close_type_form(self):
        self.show_type_form = False
        self.type_error = ""

    def _validate_type(self, data: dict) -> str:
        name = str(data.get("name", "")).strip()
        vat = _to_float(data.get("default_vat_rate"), -1.0)
        color = str(data.get("color_hex", "")).strip()
        if len(name) < 2:
            return "Le nom du type doit contenir au moins 2 caractères."
        if vat < 0 or vat > 100:
            return "Le taux de TVA par défaut doit être entre 0 et 100 %."
        if color and not color.startswith("#"):
            return "La couleur doit être au format hexadécimal (#a3e635)."
        return ""

    @rx.event
    async def submit_type(self, form_data: dict):
        error = self._validate_type(form_data)
        if error:
            self.type_error = error
            return
        params: dict[str, str | float | int] = {
            "name": str(form_data.get("name", "")).strip(),
            "code": str(form_data.get("code", "")).strip().upper(),
            "category": str(form_data.get("category", "")).strip(),
            "description": str(form_data.get("description", "")).strip(),
            "color_hex": str(form_data.get("color_hex", "#a3e635")).strip()
            or "#a3e635",
            "icon": str(form_data.get("icon", "receipt-text")).strip()
            or "receipt-text",
            "default_payment_method": str(
                form_data.get("default_payment_method", "VIREMENT")
            ),
            "default_vat_rate": _to_float(
                form_data.get("default_vat_rate"), 20.0
            ),
            "notes": str(form_data.get("notes", "")).strip(),
        }
        async with rx.asession() as asession:
            duplicate = (
                await asession.execute(
                    text(
                        "SELECT id FROM expense_type"
                        " WHERE LOWER(name) = LOWER(:name)"
                    ),
                    {"name": params["name"]},
                )
            ).first()
            if (
                duplicate is not None
                and int(duplicate[0]) != self.editing_type_id
            ):
                self.type_error = "Un type portant ce nom existe déjà."
                return
            if self.type_form_mode == "edit" and self.editing_type_id > 0:
                params["tid"] = self.editing_type_id
                await asession.execute(
                    text(
                        """
                        UPDATE expense_type SET
                            name = :name, code = :code, category = :category,
                            description = :description, color_hex = :color_hex,
                            icon = :icon,
                            default_payment_method = :default_payment_method,
                            default_vat_rate = :default_vat_rate, notes = :notes
                        WHERE id = :tid
                        """
                    ),
                    params,
                )
                message = "Type de dépense mis à jour."
            else:
                await asession.execute(
                    text(
                        """
                        INSERT INTO expense_type (
                            name, code, category, description, color_hex, icon,
                            default_payment_method, default_vat_rate,
                            is_active, is_archived, notes
                        ) VALUES (
                            :name, :code, :category, :description, :color_hex,
                            :icon, :default_payment_method, :default_vat_rate,
                            true, false, :notes
                        )
                        """
                    ),
                    params,
                )
                message = "Type de dépense créé."
            await asession.commit()

        self.show_type_form = False
        self.type_error = ""
        self.form_key += 1
        await self._refresh()
        return rx.toast(message, duration=4000)

    @rx.event
    async def toggle_type_active(self, type_id: int):
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE expense_type
                    SET is_active = CASE WHEN is_active THEN false ELSE true END
                    WHERE id = :tid
                    """
                ),
                {"tid": type_id},
            )
            await asession.commit()
        await self._refresh()
        return rx.toast("Disponibilité du type mise à jour.", duration=3000)

    @rx.event
    async def archive_type(self, type_id: int):
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE expense_type
                    SET is_archived = CASE WHEN is_archived THEN false ELSE true END,
                        is_active = CASE WHEN is_archived THEN true ELSE false END
                    WHERE id = :tid
                    """
                ),
                {"tid": type_id},
            )
            await asession.commit()
        await self._refresh()
        return rx.toast(
            "Archivage du type basculé (aucune donnée supprimée).",
            duration=4000,
        )

"""État de l'espace maintenance des engins.

Flotte filtrable, cartographie de santé, planning d'échéances, journal
d'opérations préventives/correctives, coûts, relevés d'usage et affectation
des responsables. Toutes les lectures et écritures passent par
`rx.asession()` en SQL brut.
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
from app.states.dashboard_state import MONTHS, WEEKDAYS_SHORT

CATEGORY_KEYS: list[str] = [
    "TRACTEUR",
    "MOISSONNEUSE",
    "PULVERISATEUR",
    "SEMOIR",
    "OUTIL_TRAVAIL_SOL",
    "REMORQUE",
    "IRRIGATION",
    "MANUTENTION",
    "VEHICULE",
    "AUTRE",
]

CATEGORY_LABELS: dict[str, str] = {
    "TRACTEUR": "Tracteur",
    "MOISSONNEUSE": "Moissonneuse",
    "PULVERISATEUR": "Pulvérisateur",
    "SEMOIR": "Semoir",
    "OUTIL_TRAVAIL_SOL": "Travail du sol",
    "REMORQUE": "Remorque",
    "IRRIGATION": "Irrigation",
    "MANUTENTION": "Manutention",
    "VEHICULE": "Véhicule",
    "AUTRE": "Autre",
}

CATEGORY_ICONS: dict[str, str] = {
    "TRACTEUR": "tractor",
    "MOISSONNEUSE": "wheat",
    "PULVERISATEUR": "spray-can",
    "SEMOIR": "sprout",
    "OUTIL_TRAVAIL_SOL": "shovel",
    "REMORQUE": "truck",
    "IRRIGATION": "droplets",
    "MANUTENTION": "forklift",
    "VEHICULE": "car",
    "AUTRE": "cog",
}

EQUIPMENT_STATUS_KEYS: list[str] = [
    "DISPONIBLE",
    "EN_SERVICE",
    "EN_MAINTENANCE",
    "HORS_SERVICE",
    "RESERVE",
    "CEDE",
]

EQUIPMENT_STATUS_LABELS: dict[str, str] = {
    "DISPONIBLE": "Disponible",
    "EN_SERVICE": "En service",
    "EN_MAINTENANCE": "En maintenance",
    "HORS_SERVICE": "Hors service",
    "RESERVE": "Réservé",
    "CEDE": "Cédé",
}

EQUIPMENT_STATUS_TONES: dict[str, str] = {
    "DISPONIBLE": "good",
    "EN_SERVICE": "info",
    "EN_MAINTENANCE": "warn",
    "HORS_SERVICE": "bad",
    "RESERVE": "info",
    "CEDE": "muted",
}

OWNERSHIP_KEYS: list[str] = [
    "PROPRIETE",
    "LEASING",
    "LOCATION",
    "COPROPRIETE",
    "PRESTATION",
]

OWNERSHIP_LABELS: dict[str, str] = {
    "PROPRIETE": "Propriété",
    "LEASING": "Leasing",
    "LOCATION": "Location",
    "COPROPRIETE": "Copropriété",
    "PRESTATION": "Prestation",
}

USAGE_UNIT_KEYS: list[str] = ["HEURES", "KILOMETRES", "HECTARES"]

USAGE_UNIT_LABELS: dict[str, str] = {
    "HEURES": "heures",
    "KILOMETRES": "km",
    "HECTARES": "ha",
}

KIND_KEYS: list[str] = [
    "PREVENTIVE",
    "CORRECTIVE",
    "REGLEMENTAIRE",
    "AMELIORATION",
]

KIND_LABELS: dict[str, str] = {
    "PREVENTIVE": "Préventive",
    "CORRECTIVE": "Corrective",
    "REGLEMENTAIRE": "Réglementaire",
    "AMELIORATION": "Amélioration",
}

MAINTENANCE_STATUS_KEYS: list[str] = [
    "PLANIFIEE",
    "EN_COURS",
    "REALISEE",
    "REPORTEE",
    "ANNULEE",
]

MAINTENANCE_STATUS_LABELS: dict[str, str] = {
    "PLANIFIEE": "Planifiée",
    "EN_COURS": "En cours",
    "REALISEE": "Réalisée",
    "REPORTEE": "Reportée",
    "ANNULEE": "Annulée",
}

MAINTENANCE_STATUS_TONES: dict[str, str] = {
    "PLANIFIEE": "planned",
    "EN_COURS": "running",
    "REALISEE": "done",
    "REPORTEE": "late",
    "ANNULEE": "cancelled",
}

PRIORITY_KEYS: list[str] = ["BASSE", "NORMALE", "HAUTE", "URGENTE"]

PRIORITY_LABELS: dict[str, str] = {
    "BASSE": "Basse",
    "NORMALE": "Normale",
    "HAUTE": "Haute",
    "URGENTE": "Urgente",
}

COST_TYPE_KEYS: list[str] = [
    "PIECE",
    "MAIN_OEUVRE",
    "CONSOMMABLE",
    "SOUS_TRAITANCE",
    "TRANSPORT",
    "AUTRE",
]

COST_TYPE_LABELS: dict[str, str] = {
    "PIECE": "Pièce",
    "MAIN_OEUVRE": "Main d'œuvre",
    "CONSOMMABLE": "Consommable",
    "SOUS_TRAITANCE": "Sous-traitance",
    "TRANSPORT": "Transport",
    "AUTRE": "Autre",
}

BASIS_LABELS: dict[str, str] = {
    "CALENDRIER": "Calendaire",
    "COMPTEUR": "Compteur",
    "MIXTE": "Mixte",
}

HORIZON_DAYS: int = 90


class Option(TypedDict):
    value: str
    label: str


class EquipmentRow(TypedDict):
    id: int
    name: str
    code: str
    category: str
    category_label: str
    icon: str
    status: str
    status_label: str
    status_tone: str
    ownership_label: str
    brand_model: str
    usage_counter: float
    usage_unit_label: str
    hourly_cost: float
    responsible: str
    next_service_label: str
    days_to_service: int
    open_ops: int
    overdue_ops: int
    cost_year: float
    health: int
    health_pct: str
    health_label: str
    health_tone: str
    location: str


class DeadlineRow(TypedDict):
    key: str
    equipment_id: int
    equipment: str
    code: str
    title: str
    kind_label: str
    date_label: str
    days_left: int
    tone: str
    left: str
    overdue: bool


class FleetAlert(TypedDict):
    key: str
    equipment_id: int
    equipment: str
    level: str
    category: str
    title: str
    message: str
    date_label: str


class ScheduleRow(TypedDict):
    id: int
    title: str
    kind_label: str
    basis_label: str
    interval_days: int
    interval_counter: float
    last_done_label: str
    next_due_label: str
    next_due_counter: float
    days_left: int
    tone: str
    estimated_cost: float
    estimated_hours: float
    responsible: str
    checklist: str
    is_active: bool


class OperationRow(TypedDict):
    id: int
    equipment_id: int
    equipment: str
    code: str
    title: str
    kind: str
    kind_label: str
    status: str
    status_label: str
    tone: str
    priority: str
    priority_label: str
    scheduled_label: str
    due_label: str
    done_label: str
    days_delta: int
    is_overdue: bool
    is_closed: bool
    downtime: float
    labor_hours: float
    total_cost: float
    provider: str
    responsible: str
    is_internal: bool
    failure: str
    work: str


class CostRow(TypedDict):
    id: int
    operation: str
    type: str
    type_label: str
    label: str
    reference: str
    supplier: str
    quantity: float
    unit: str
    unit_price: float
    amount: float
    date_label: str


class UsageRow(TypedDict):
    id: int
    date_label: str
    operator: str
    counter_start: float
    counter_end: float
    hours_used: float
    fuel_liters: float
    notes: str


EMPTY_EQUIPMENT_DETAIL: dict[str, str] = {
    "id": "0",
    "name": "Aucun engin sélectionné",
    "code": "—",
    "category_label": "—",
    "icon": "cog",
    "status_label": "—",
    "status_tone": "muted",
    "ownership_label": "—",
    "brand": "—",
    "model": "—",
    "serial_number": "—",
    "registration": "—",
    "year": "—",
    "power": "0",
    "width": "0",
    "usage_counter": "0",
    "usage_unit_label": "heures",
    "purchase_label": "—",
    "purchase_price": "0",
    "residual_value": "0",
    "hourly_cost": "0",
    "fuel": "0",
    "location": "—",
    "responsible": "Non affecté",
    "insurance_label": "—",
    "inspection_label": "—",
    "next_service_label": "—",
    "next_service_counter": "0",
    "interval_days": "0",
    "interval_counter": "0",
    "notes": "—",
    "health": "0",
    "health_pct": "0%",
    "health_label": "—",
    "health_tone": "muted",
    "open_ops": "0",
    "cost_year": "0",
    "downtime_year": "0",
    "hours_30": "0",
    "fuel_30": "0",
}

EMPTY_EQUIPMENT_FORM: dict[str, str] = {
    "name": "",
    "code": "",
    "category": "TRACTEUR",
    "status": "DISPONIBLE",
    "ownership": "PROPRIETE",
    "brand": "",
    "model": "",
    "serial_number": "",
    "registration": "",
    "year": "",
    "power_hp": "0",
    "working_width_m": "0",
    "usage_unit": "HEURES",
    "usage_counter": "0",
    "purchase_date": "",
    "purchase_price": "0",
    "residual_value": "0",
    "hourly_cost": "0",
    "fuel_consumption_l_h": "0",
    "storage_location": "",
    "responsible_id": "",
    "insurance_expiry": "",
    "inspection_expiry": "",
    "next_service_date": "",
    "next_service_counter": "0",
    "service_interval_days": "180",
    "service_interval_counter": "500",
    "notes": "",
}

EMPTY_OPERATION_FORM: dict[str, str] = {
    "equipment_id": "",
    "schedule_id": "",
    "title": "",
    "kind": "PREVENTIVE",
    "status": "PLANIFIEE",
    "priority": "NORMALE",
    "scheduled_date": "",
    "due_date": "",
    "done_date": "",
    "counter_at_service": "0",
    "downtime_hours": "0",
    "labor_hours": "0",
    "labor_cost": "0",
    "parts_cost": "0",
    "external_cost": "0",
    "is_internal": "1",
    "provider": "",
    "invoice_reference": "",
    "responsible_id": "",
    "failure_description": "",
    "work_performed": "",
    "notes": "",
}


def _fmt_date(value: object) -> str:
    day = as_date(value)
    if day is None:
        return "—"
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _iso(value: object) -> str:
    return iso_or_empty(value)


def _to_float(raw: str | None, default: float = 0.0) -> float:
    if raw is None:
        return default
    value = str(raw).strip().replace(",", ".")
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _to_int(raw: str | None, default: int = 0) -> int:
    return int(_to_float(raw, float(default)))


def _to_date(raw: str | None) -> datetime.date | None:
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


def _health_tone(score: int) -> str:
    if score >= 80:
        return "good"
    if score >= 55:
        return "warn"
    return "bad"


def _health_label(score: int) -> str:
    if score >= 80:
        return "Opérationnel"
    if score >= 55:
        return "À surveiller"
    return "Critique"


def _deadline_tone(days: int) -> str:
    if days < 0:
        return "bad"
    if days <= 14:
        return "warn"
    return "good"


class MaintenanceState(rx.State):
    """Flotte d'engins, échéances, opérations, coûts et usage."""

    is_loading: bool = True
    today_label: str = ""

    search: str = ""
    category_filter: str = "TOUTES"
    status_filter: str = "TOUS"
    health_filter: str = "TOUS"

    journal_search: str = ""
    kind_filter: str = "TOUS"
    op_status_filter: str = "TOUS"
    equipment_filter: str = "TOUS"

    kpis: dict[str, float] = {
        "fleet": 0.0,
        "available": 0.0,
        "in_maintenance": 0.0,
        "out_of_service": 0.0,
        "open_ops": 0.0,
        "overdue_ops": 0.0,
        "cost_year": 0.0,
        "downtime_year": 0.0,
        "fleet_value": 0.0,
        "due_soon": 0.0,
    }

    equipments: list[EquipmentRow] = []
    deadlines: list[DeadlineRow] = []
    fleet_alerts: list[FleetAlert] = []
    operations: list[OperationRow] = []

    selected_equipment_id: int = 0
    equipment_detail: dict[str, str] = EMPTY_EQUIPMENT_DETAIL
    schedules: list[ScheduleRow] = []
    costs: list[CostRow] = []
    usage_logs: list[UsageRow] = []

    employee_options: list[Option] = []
    equipment_options: list[Option] = []
    schedule_options: list[Option] = []
    operation_options: list[Option] = []

    category_options: list[Option] = _options(CATEGORY_KEYS, CATEGORY_LABELS)
    status_options: list[Option] = _options(
        EQUIPMENT_STATUS_KEYS, EQUIPMENT_STATUS_LABELS
    )
    ownership_options: list[Option] = _options(OWNERSHIP_KEYS, OWNERSHIP_LABELS)
    usage_unit_options: list[Option] = _options(
        USAGE_UNIT_KEYS, USAGE_UNIT_LABELS
    )
    kind_options: list[Option] = _options(KIND_KEYS, KIND_LABELS)
    op_status_options: list[Option] = _options(
        MAINTENANCE_STATUS_KEYS, MAINTENANCE_STATUS_LABELS
    )
    priority_options: list[Option] = _options(PRIORITY_KEYS, PRIORITY_LABELS)
    cost_type_options: list[Option] = _options(COST_TYPE_KEYS, COST_TYPE_LABELS)
    health_options: list[Option] = [
        {"value": "CRITIQUE", "label": "Santé critique"},
        {"value": "SURVEILLER", "label": "À surveiller"},
        {"value": "OK", "label": "Opérationnels"},
    ]

    show_equipment_form: bool = False
    equipment_form_mode: str = "create"
    editing_equipment_id: int = 0
    equipment_form: dict[str, str] = EMPTY_EQUIPMENT_FORM

    show_operation_form: bool = False
    operation_form_mode: str = "create"
    editing_operation_id: int = 0
    operation_form: dict[str, str] = EMPTY_OPERATION_FORM

    form_error: str = ""
    operation_error: str = ""
    cost_error: str = ""
    usage_error: str = ""
    form_key: int = 0

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def equipment_count(self) -> int:
        return len(self.equipments)

    @rx.var
    def has_selection(self) -> bool:
        return self.selected_equipment_id > 0

    @rx.var
    def fleet_health_average(self) -> float:
        if not self.equipments:
            return 0.0
        return round(
            sum(e["health"] for e in self.equipments) / len(self.equipments), 0
        )

    @rx.var
    def critical_count(self) -> int:
        return len([e for e in self.equipments if e["health_tone"] == "bad"])

    @rx.var
    def counter_shown(self) -> float:
        return round(sum(e["usage_counter"] for e in self.equipments), 0)

    @rx.var
    def operation_count(self) -> int:
        return len(self.operations)

    @rx.var
    def operation_cost_shown(self) -> float:
        return round(sum(o["total_cost"] for o in self.operations), 0)

    @rx.var
    def overdue_deadlines(self) -> int:
        return len([d for d in self.deadlines if d["overdue"]])

    @rx.var
    def equipment_form_title(self) -> str:
        if self.equipment_form_mode == "edit":
            return "Modifier la fiche engin"
        return "Nouvel engin"

    @rx.var
    def operation_form_title(self) -> str:
        if self.operation_form_mode == "edit":
            return "Modifier l'opération"
        return "Planifier une opération"

    # ------------------------------------------------------------------
    # KPIs & référentiels
    # ------------------------------------------------------------------

    async def _fetch_kpis(self) -> None:
        today = datetime.date.today()
        since = today - datetime.timedelta(days=365)
        horizon = today + datetime.timedelta(days=30)
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            (SELECT COUNT(*) FROM equipment WHERE status <> 'CEDE'),
                            (SELECT COUNT(*) FROM equipment WHERE status = 'DISPONIBLE'),
                            (SELECT COUNT(*) FROM equipment WHERE status = 'EN_MAINTENANCE'),
                            (SELECT COUNT(*) FROM equipment WHERE status = 'HORS_SERVICE'),
                            (SELECT COUNT(*) FROM maintenance_operation
                               WHERE status IN ('PLANIFIEE', 'EN_COURS', 'REPORTEE')),
                            (SELECT COUNT(*) FROM maintenance_operation
                               WHERE status IN ('PLANIFIEE', 'EN_COURS', 'REPORTEE')
                                 AND COALESCE(due_date, scheduled_date) < :today),
                            (SELECT COALESCE(SUM(total_cost), 0) FROM maintenance_operation
                               WHERE done_date >= :since),
                            (SELECT COALESCE(SUM(downtime_hours), 0) FROM maintenance_operation
                               WHERE done_date >= :since),
                            (SELECT COALESCE(SUM(purchase_price), 0) FROM equipment
                               WHERE status <> 'CEDE'),
                            (SELECT COUNT(*) FROM equipment
                               WHERE (insurance_expiry IS NOT NULL AND insurance_expiry <= :horizon)
                                  OR (inspection_expiry IS NOT NULL AND inspection_expiry <= :horizon)
                                  OR (next_service_date IS NOT NULL AND next_service_date <= :horizon))
                        """
                    ),
                    {"today": today, "since": since, "horizon": horizon},
                )
            ).first()
        self.kpis = {
            "fleet": float(row[0] or 0) if row else 0.0,
            "available": float(row[1] or 0) if row else 0.0,
            "in_maintenance": float(row[2] or 0) if row else 0.0,
            "out_of_service": float(row[3] or 0) if row else 0.0,
            "open_ops": float(row[4] or 0) if row else 0.0,
            "overdue_ops": float(row[5] or 0) if row else 0.0,
            "cost_year": float(row[6] or 0) if row else 0.0,
            "downtime_year": float(row[7] or 0) if row else 0.0,
            "fleet_value": float(row[8] or 0) if row else 0.0,
            "due_soon": float(row[9] or 0) if row else 0.0,
        }

    async def _fetch_reference(self) -> None:
        async with rx.asession() as asession:
            employee_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT id, first_name, last_name, COALESCE(team, '')
                        FROM employee
                        WHERE status <> 'SORTI'
                        ORDER BY last_name, first_name
                        LIMIT 100
                        """
                    )
                )
            ).all()
            equipment_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT id, COALESCE(code, ''), name
                        FROM equipment ORDER BY code, name LIMIT 200
                        """
                    )
                )
            ).all()
        self.employee_options = [
            {
                "value": str(int(row[0])),
                "label": f"{row[1]} {row[2]} · {row[3]}",
            }
            for row in employee_rows
        ]
        self.equipment_options = [
            {"value": str(int(row[0])), "label": f"{row[1]} · {row[2]}"}
            for row in equipment_rows
        ]

    # ------------------------------------------------------------------
    # Flotte & santé
    # ------------------------------------------------------------------

    def _fleet_filters(self) -> tuple[str, dict[str, str]]:
        clauses = ["e.status <> 'CEDE'"]
        params: dict[str, str] = {}
        query = self.search.strip().lower()
        if query:
            clauses.append(
                "(LOWER(e.name) LIKE :q OR LOWER(e.code) LIKE :q"
                " OR LOWER(e.brand) LIKE :q OR LOWER(e.model) LIKE :q"
                " OR LOWER(e.registration) LIKE :q"
                " OR LOWER(e.storage_location) LIKE :q)"
            )
            params["q"] = f"%{query}%"
        if self.category_filter != "TOUTES":
            clauses.append("e.category = :category")
            params["category"] = self.category_filter
        if self.status_filter != "TOUS":
            clauses.append("e.status = :status")
            params["status"] = self.status_filter
        return " AND ".join(clauses), params

    async def _fetch_fleet(self) -> None:
        today = datetime.date.today()
        since = today - datetime.timedelta(days=365)
        where, params = self._fleet_filters()
        full_params: dict[str, str | datetime.date] = dict(params)
        full_params["today"] = today
        full_params["since"] = since

        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT e.id, e.name, COALESCE(e.code, ''), e.category,
                               e.status, e.ownership, COALESCE(e.brand, ''),
                               COALESCE(e.model, ''), e.usage_unit,
                               COALESCE(e.usage_counter, 0),
                               COALESCE(e.hourly_cost, 0),
                               COALESCE(emp.first_name || ' ' || emp.last_name, ''),
                               e.next_service_date, e.insurance_expiry,
                               e.inspection_expiry,
                               COALESCE(e.storage_location, ''),
                               (SELECT COUNT(*) FROM maintenance_operation o
                                  WHERE o.equipment_id = e.id
                                    AND o.status IN ('PLANIFIEE', 'EN_COURS', 'REPORTEE')),
                               (SELECT COUNT(*) FROM maintenance_operation o
                                  WHERE o.equipment_id = e.id
                                    AND o.status IN ('PLANIFIEE', 'EN_COURS', 'REPORTEE')
                                    AND COALESCE(o.due_date, o.scheduled_date) < :today),
                               (SELECT COALESCE(SUM(o.total_cost), 0)
                                  FROM maintenance_operation o
                                  WHERE o.equipment_id = e.id AND o.done_date >= :since)
                        FROM equipment e
                        LEFT JOIN employee emp ON emp.id = e.responsible_id
                        WHERE {where}
                        ORDER BY e.code, e.name
                        LIMIT 120
                        """
                    ),
                    full_params,
                )
            ).all()

            deadline_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT s.id, e.id, e.name, COALESCE(e.code, ''),
                               s.title, s.kind, s.next_due_on
                        FROM maintenance_schedule s
                        JOIN equipment e ON e.id = s.equipment_id
                        WHERE s.is_active = true AND s.next_due_on IS NOT NULL
                        ORDER BY s.next_due_on
                        LIMIT 40
                        """
                    )
                )
            ).all()

        equipments: list[EquipmentRow] = []
        for row in rows:
            status = str(row[4])
            category = str(row[3])
            unit = str(row[8])
            next_service = as_date(row[12])
            insurance = as_date(row[13])
            inspection = as_date(row[14])
            open_ops = int(row[16] or 0)
            overdue_ops = int(row[17] or 0)
            days_to_service = (
                (next_service - today).days if next_service else 999
            )
            score = 100
            if next_service and days_to_service < 0:
                score -= 30
            elif next_service and days_to_service <= 14:
                score -= 12
            if insurance and insurance < today:
                score -= 22
            elif insurance and (insurance - today).days <= 30:
                score -= 8
            if inspection and inspection < today:
                score -= 20
            elif inspection and (inspection - today).days <= 30:
                score -= 7
            score -= overdue_ops * 12
            score -= max(open_ops - overdue_ops, 0) * 4
            if status == "HORS_SERVICE":
                score -= 40
            elif status == "EN_MAINTENANCE":
                score -= 15
            score = max(0, min(100, score))
            equipments.append(
                {
                    "id": int(row[0]),
                    "name": str(row[1]),
                    "code": str(row[2]) or "—",
                    "category": category,
                    "category_label": CATEGORY_LABELS.get(category, category),
                    "icon": CATEGORY_ICONS.get(category, "cog"),
                    "status": status,
                    "status_label": EQUIPMENT_STATUS_LABELS.get(status, status),
                    "status_tone": EQUIPMENT_STATUS_TONES.get(status, "muted"),
                    "ownership_label": OWNERSHIP_LABELS.get(row[5], row[5]),
                    "brand_model": f"{row[6]} {row[7]}".strip()
                    or "Modèle non précisé",
                    "usage_counter": float(row[9] or 0),
                    "usage_unit_label": USAGE_UNIT_LABELS.get(unit, unit),
                    "hourly_cost": float(row[10] or 0),
                    "responsible": str(row[11]) or "Non affecté",
                    "next_service_label": _fmt_date(next_service),
                    "days_to_service": days_to_service,
                    "open_ops": open_ops,
                    "overdue_ops": overdue_ops,
                    "cost_year": float(row[18] or 0),
                    "health": score,
                    "health_pct": f"{score}%",
                    "health_label": _health_label(score),
                    "health_tone": _health_tone(score),
                    "location": str(row[15]) or "Emplacement non précisé",
                }
            )

        if self.health_filter == "CRITIQUE":
            equipments = [e for e in equipments if e["health_tone"] == "bad"]
        elif self.health_filter == "SURVEILLER":
            equipments = [e for e in equipments if e["health_tone"] == "warn"]
        elif self.health_filter == "OK":
            equipments = [e for e in equipments if e["health_tone"] == "good"]

        self.equipments = equipments

        ids = [e["id"] for e in equipments]
        if self.selected_equipment_id not in ids:
            self.selected_equipment_id = ids[0] if ids else 0

        deadlines: list[DeadlineRow] = []
        for row in deadline_rows:
            due = as_date(row[6])
            if due is None:
                continue
            days_left = (due - today).days
            if days_left > HORIZON_DAYS:
                continue
            ratio = max(0.0, min(1.0, days_left / HORIZON_DAYS))
            kind = str(row[5])
            deadlines.append(
                {
                    "key": f"s{int(row[0])}",
                    "equipment_id": int(row[1]),
                    "equipment": str(row[2]),
                    "code": str(row[3]) or "—",
                    "title": str(row[4]),
                    "kind_label": KIND_LABELS.get(kind, kind),
                    "date_label": _fmt_date(due),
                    "days_left": days_left,
                    "tone": _deadline_tone(days_left),
                    "left": f"{ratio * 100:.0f}%",
                    "overdue": days_left < 0,
                }
            )
        self.deadlines = deadlines

    async def _fetch_alerts(self) -> None:
        today = datetime.date.today()
        horizon = today + datetime.timedelta(days=45)
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT e.id, e.name, COALESCE(e.code, ''),
                               e.insurance_expiry, e.inspection_expiry,
                               e.next_service_date,
                               (SELECT COUNT(*) FROM maintenance_operation o
                                  WHERE o.equipment_id = e.id
                                    AND o.status IN ('PLANIFIEE', 'EN_COURS', 'REPORTEE')
                                    AND COALESCE(o.due_date, o.scheduled_date) < :today)
                        FROM equipment e
                        WHERE e.status <> 'CEDE'
                          AND (
                            (e.insurance_expiry IS NOT NULL AND e.insurance_expiry <= :horizon)
                            OR (e.inspection_expiry IS NOT NULL AND e.inspection_expiry <= :horizon)
                            OR (e.next_service_date IS NOT NULL AND e.next_service_date <= :horizon)
                          )
                        ORDER BY e.code
                        LIMIT 40
                        """
                    ),
                    {"today": today, "horizon": horizon},
                )
            ).all()

        alerts: list[FleetAlert] = []
        for row in rows:
            equipment_id = int(row[0])
            name = str(row[1])
            code = str(row[2]) or "—"
            checks = [
                ("Assurance", as_date(row[3]), "assurance"),
                ("Contrôle réglementaire", as_date(row[4]), "controle"),
                ("Entretien préventif", as_date(row[5]), "entretien"),
            ]
            for label, due, slug in checks:
                if due is None or due > horizon:
                    continue
                days = (due - today).days
                level = (
                    "CRITIQUE"
                    if days < 0
                    else ("ATTENTION" if days <= 21 else "INFO")
                )
                message = (
                    f"Échéance dépassée de {abs(days)} j sur {name}."
                    if days < 0
                    else f"Échéance dans {days} j sur {name}."
                )
                alerts.append(
                    {
                        "key": f"{slug}-{equipment_id}",
                        "equipment_id": equipment_id,
                        "equipment": f"{code} · {name}",
                        "level": level,
                        "category": label,
                        "title": f"{label} — {code}",
                        "message": message,
                        "date_label": _fmt_date(due),
                    }
                )
            overdue_ops = int(row[6] or 0)
            if overdue_ops > 0:
                alerts.append(
                    {
                        "key": f"ops-{equipment_id}",
                        "equipment_id": equipment_id,
                        "equipment": f"{code} · {name}",
                        "level": "CRITIQUE",
                        "category": "Maintenance",
                        "title": f"Opérations en retard — {code}",
                        "message": f"{overdue_ops} opération(s) de maintenance non réalisée(s).",
                        "date_label": _fmt_date(today),
                    }
                )
        order = {"CRITIQUE": 0, "ATTENTION": 1, "INFO": 2}
        alerts.sort(key=lambda a: order.get(a["level"], 3))
        self.fleet_alerts = alerts[:10]

    # ------------------------------------------------------------------
    # Journal des opérations
    # ------------------------------------------------------------------

    async def _fetch_operations(self) -> None:
        today = datetime.date.today()
        clauses = ["1=1"]
        params: dict[str, str | int | datetime.date] = {}
        query = self.journal_search.strip().lower()
        if query:
            clauses.append(
                "(LOWER(o.title) LIKE :q OR LOWER(e.name) LIKE :q"
                " OR LOWER(e.code) LIKE :q OR LOWER(o.provider) LIKE :q"
                " OR LOWER(o.failure_description) LIKE :q)"
            )
            params["q"] = f"%{query}%"
        if self.kind_filter != "TOUS":
            clauses.append("o.kind = :kind")
            params["kind"] = self.kind_filter
        if self.op_status_filter != "TOUS":
            clauses.append("o.status = :ostatus")
            params["ostatus"] = self.op_status_filter
        if self.equipment_filter != "TOUS":
            clauses.append("o.equipment_id = :eid")
            params["eid"] = int(self.equipment_filter)
        where = " AND ".join(clauses)

        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT o.id, o.equipment_id, e.name, COALESCE(e.code, ''),
                               o.title, o.kind, o.status, o.priority,
                               o.scheduled_date, o.due_date, o.done_date,
                               COALESCE(o.downtime_hours, 0),
                               COALESCE(o.labor_hours, 0),
                               COALESCE(o.total_cost, 0),
                               COALESCE(o.provider, ''),
                               COALESCE(emp.first_name || ' ' || emp.last_name, ''),
                               o.is_internal, COALESCE(o.failure_description, ''),
                               COALESCE(o.work_performed, '')
                        FROM maintenance_operation o
                        JOIN equipment e ON e.id = o.equipment_id
                        LEFT JOIN employee emp ON emp.id = o.responsible_id
                        WHERE {where}
                        ORDER BY COALESCE(o.due_date, o.scheduled_date) DESC, o.id DESC
                        LIMIT 60
                        """
                    ),
                    params,
                )
            ).all()

        operations: list[OperationRow] = []
        for row in rows:
            kind = str(row[5])
            status = str(row[6])
            priority = str(row[7])
            reference = as_date(row[9]) or as_date(row[8])
            days_delta = (reference - today).days if reference else 0
            closed = status in ("REALISEE", "ANNULEE")
            operations.append(
                {
                    "id": int(row[0]),
                    "equipment_id": int(row[1]),
                    "equipment": str(row[2]),
                    "code": str(row[3]) or "—",
                    "title": str(row[4]),
                    "kind": kind,
                    "kind_label": KIND_LABELS.get(kind, kind),
                    "status": status,
                    "status_label": MAINTENANCE_STATUS_LABELS.get(
                        status, status
                    ),
                    "tone": MAINTENANCE_STATUS_TONES.get(status, "planned"),
                    "priority": priority,
                    "priority_label": PRIORITY_LABELS.get(priority, priority),
                    "scheduled_label": _fmt_date(row[8]),
                    "due_label": _fmt_date(row[9]),
                    "done_label": _fmt_date(row[10]),
                    "days_delta": days_delta,
                    "is_overdue": bool(
                        reference and reference < today and not closed
                    ),
                    "is_closed": closed,
                    "downtime": float(row[11] or 0),
                    "labor_hours": float(row[12] or 0),
                    "total_cost": float(row[13] or 0),
                    "provider": str(row[14]) or "Atelier interne",
                    "responsible": str(row[15]) or "Non affecté",
                    "is_internal": bool(row[16]),
                    "failure": str(row[17]) or "—",
                    "work": str(row[18]) or "—",
                }
            )
        self.operations = operations

    # ------------------------------------------------------------------
    # Fiche engin
    # ------------------------------------------------------------------

    async def _fetch_detail(self) -> None:
        equipment_id = self.selected_equipment_id
        if equipment_id == 0:
            self.equipment_detail = EMPTY_EQUIPMENT_DETAIL
            self.schedules = []
            self.costs = []
            self.usage_logs = []
            self.schedule_options = []
            self.operation_options = []
            return

        today = datetime.date.today()
        since = today - datetime.timedelta(days=365)
        since_30 = today - datetime.timedelta(days=30)

        async with rx.asession() as asession:
            detail = (
                await asession.execute(
                    text(
                        """
                        SELECT e.id, e.name, COALESCE(e.code, ''), e.category,
                               e.status, e.ownership, COALESCE(e.brand, ''),
                               COALESCE(e.model, ''), COALESCE(e.serial_number, ''),
                               COALESCE(e.registration, ''), COALESCE(e.year, 0),
                               COALESCE(e.power_hp, 0), COALESCE(e.working_width_m, 0),
                               e.usage_unit, COALESCE(e.usage_counter, 0),
                               e.purchase_date, COALESCE(e.purchase_price, 0),
                               COALESCE(e.residual_value, 0),
                               COALESCE(e.hourly_cost, 0),
                               COALESCE(e.fuel_consumption_l_h, 0),
                               COALESCE(e.storage_location, ''),
                               COALESCE(emp.first_name || ' ' || emp.last_name, ''),
                               e.insurance_expiry, e.inspection_expiry,
                               e.next_service_date,
                               COALESCE(e.next_service_counter, 0),
                               COALESCE(e.service_interval_days, 0),
                               COALESCE(e.service_interval_counter, 0),
                               COALESCE(e.notes, ''),
                               (SELECT COUNT(*) FROM maintenance_operation o
                                  WHERE o.equipment_id = e.id
                                    AND o.status IN ('PLANIFIEE', 'EN_COURS', 'REPORTEE')),
                               (SELECT COALESCE(SUM(o.total_cost), 0)
                                  FROM maintenance_operation o
                                  WHERE o.equipment_id = e.id AND o.done_date >= :since),
                               (SELECT COALESCE(SUM(o.downtime_hours), 0)
                                  FROM maintenance_operation o
                                  WHERE o.equipment_id = e.id AND o.done_date >= :since),
                               (SELECT COALESCE(SUM(u.hours_used), 0)
                                  FROM equipment_usage_log u
                                  WHERE u.equipment_id = e.id AND u.used_on >= :since30),
                               (SELECT COALESCE(SUM(u.fuel_liters), 0)
                                  FROM equipment_usage_log u
                                  WHERE u.equipment_id = e.id AND u.used_on >= :since30)
                        FROM equipment e
                        LEFT JOIN employee emp ON emp.id = e.responsible_id
                        WHERE e.id = :eid
                        """
                    ),
                    {"eid": equipment_id, "since": since, "since30": since_30},
                )
            ).first()

            schedule_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT s.id, s.title, s.kind, s.trigger_basis,
                               COALESCE(s.interval_days, 0),
                               COALESCE(s.interval_counter, 0),
                               s.last_done_on, s.next_due_on,
                               COALESCE(s.next_due_counter, 0),
                               COALESCE(s.estimated_cost, 0),
                               COALESCE(s.estimated_hours, 0),
                               COALESCE(emp.first_name || ' ' || emp.last_name, ''),
                               COALESCE(s.checklist, ''), s.is_active
                        FROM maintenance_schedule s
                        LEFT JOIN employee emp ON emp.id = s.responsible_id
                        WHERE s.equipment_id = :eid
                        ORDER BY s.next_due_on NULLS LAST, s.id
                        LIMIT 20
                        """
                    ),
                    {"eid": equipment_id},
                )
            ).all()

            cost_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT c.id, o.title, c.type, COALESCE(c.label, ''),
                               COALESCE(c.reference, ''), COALESCE(c.supplier, ''),
                               COALESCE(c.quantity, 0), COALESCE(c.unit, ''),
                               COALESCE(c.unit_price, 0), COALESCE(c.amount, 0),
                               c.incurred_on
                        FROM maintenance_cost c
                        JOIN maintenance_operation o ON o.id = c.maintenance_id
                        WHERE o.equipment_id = :eid
                        ORDER BY c.incurred_on DESC NULLS LAST, c.id DESC
                        LIMIT 24
                        """
                    ),
                    {"eid": equipment_id},
                )
            ).all()

            usage_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT u.id, u.used_on,
                               COALESCE(emp.first_name || ' ' || emp.last_name, ''),
                               COALESCE(u.counter_start, 0), COALESCE(u.counter_end, 0),
                               COALESCE(u.hours_used, 0), COALESCE(u.fuel_liters, 0),
                               COALESCE(u.notes, '')
                        FROM equipment_usage_log u
                        LEFT JOIN employee emp ON emp.id = u.employee_id
                        WHERE u.equipment_id = :eid
                        ORDER BY u.used_on DESC NULLS LAST, u.id DESC
                        LIMIT 16
                        """
                    ),
                    {"eid": equipment_id},
                )
            ).all()

            operation_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT id, title FROM maintenance_operation
                        WHERE equipment_id = :eid
                        ORDER BY COALESCE(due_date, scheduled_date) DESC, id DESC
                        LIMIT 30
                        """
                    ),
                    {"eid": equipment_id},
                )
            ).all()

        if detail is None:
            self.equipment_detail = EMPTY_EQUIPMENT_DETAIL
            self.schedules = []
            self.costs = []
            self.usage_logs = []
            self.schedule_options = []
            self.operation_options = []
            return

        status = str(detail[4])
        category = str(detail[3])
        unit = str(detail[13])
        health = 0
        health_tone = "muted"
        health_label = "—"
        for item in self.equipments:
            if item["id"] == equipment_id:
                health = item["health"]
                health_tone = item["health_tone"]
                health_label = item["health_label"]

        self.equipment_detail = {
            "id": str(int(detail[0])),
            "name": str(detail[1]),
            "code": str(detail[2]) or "—",
            "category_label": CATEGORY_LABELS.get(category, category),
            "icon": CATEGORY_ICONS.get(category, "cog"),
            "status_label": EQUIPMENT_STATUS_LABELS.get(status, status),
            "status_tone": EQUIPMENT_STATUS_TONES.get(status, "muted"),
            "ownership_label": OWNERSHIP_LABELS.get(detail[5], detail[5]),
            "brand": str(detail[6]) or "—",
            "model": str(detail[7]) or "—",
            "serial_number": str(detail[8]) or "—",
            "registration": str(detail[9]) or "Non immatriculé",
            "year": str(int(detail[10] or 0)) if detail[10] else "—",
            "power": f"{float(detail[11] or 0):.0f}",
            "width": f"{float(detail[12] or 0):.1f}",
            "usage_counter": f"{float(detail[14] or 0):.0f}",
            "usage_unit_label": USAGE_UNIT_LABELS.get(unit, unit),
            "purchase_label": _fmt_date(detail[15]),
            "purchase_price": f"{float(detail[16] or 0):.0f}",
            "residual_value": f"{float(detail[17] or 0):.0f}",
            "hourly_cost": f"{float(detail[18] or 0):.2f}",
            "fuel": f"{float(detail[19] or 0):.1f}",
            "location": str(detail[20]) or "Emplacement non précisé",
            "responsible": str(detail[21]) or "Non affecté",
            "insurance_label": _fmt_date(detail[22]),
            "inspection_label": _fmt_date(detail[23]),
            "next_service_label": _fmt_date(detail[24]),
            "next_service_counter": f"{float(detail[25] or 0):.0f}",
            "interval_days": str(int(detail[26] or 0)),
            "interval_counter": f"{float(detail[27] or 0):.0f}",
            "notes": str(detail[28]) or "Aucune note atelier.",
            "health": str(health),
            "health_pct": f"{health}%",
            "health_label": health_label,
            "health_tone": health_tone,
            "open_ops": str(int(detail[29] or 0)),
            "cost_year": f"{float(detail[30] or 0):.0f}",
            "downtime_year": f"{float(detail[31] or 0):.1f}",
            "hours_30": f"{float(detail[32] or 0):.1f}",
            "fuel_30": f"{float(detail[33] or 0):.0f}",
        }

        schedules: list[ScheduleRow] = []
        for row in schedule_rows:
            due = as_date(row[7])
            days_left = (due - today).days if due else 999
            kind = str(row[2])
            basis = str(row[3])
            schedules.append(
                {
                    "id": int(row[0]),
                    "title": str(row[1]),
                    "kind_label": KIND_LABELS.get(kind, kind),
                    "basis_label": BASIS_LABELS.get(basis, basis),
                    "interval_days": int(row[4] or 0),
                    "interval_counter": float(row[5] or 0),
                    "last_done_label": _fmt_date(row[6]),
                    "next_due_label": _fmt_date(due),
                    "next_due_counter": float(row[8] or 0),
                    "days_left": days_left,
                    "tone": _deadline_tone(days_left),
                    "estimated_cost": float(row[9] or 0),
                    "estimated_hours": float(row[10] or 0),
                    "responsible": str(row[11]) or "Non affecté",
                    "checklist": str(row[12]) or "—",
                    "is_active": bool(row[13]),
                }
            )
        self.schedules = schedules
        self.schedule_options = [
            {"value": str(s["id"]), "label": s["title"]} for s in schedules
        ]

        self.costs = [
            {
                "id": int(row[0]),
                "operation": str(row[1]),
                "type": str(row[2]),
                "type_label": COST_TYPE_LABELS.get(row[2], row[2]),
                "label": str(row[3]) or "—",
                "reference": str(row[4]) or "—",
                "supplier": str(row[5]) or "—",
                "quantity": float(row[6] or 0),
                "unit": str(row[7]) or "u",
                "unit_price": float(row[8] or 0),
                "amount": float(row[9] or 0),
                "date_label": _fmt_date(row[10]),
            }
            for row in cost_rows
        ]

        self.usage_logs = [
            {
                "id": int(row[0]),
                "date_label": _fmt_date(row[1]),
                "operator": str(row[2]) or "Opérateur non précisé",
                "counter_start": float(row[3] or 0),
                "counter_end": float(row[4] or 0),
                "hours_used": float(row[5] or 0),
                "fuel_liters": float(row[6] or 0),
                "notes": str(row[7]) or "—",
            }
            for row in usage_rows
        ]

        self.operation_options = [
            {"value": str(int(row[0])), "label": str(row[1])}
            for row in operation_rows
        ]

    async def _refresh_all(self) -> None:
        await self._fetch_kpis()
        await self._fetch_fleet()
        await self._fetch_alerts()
        await self._fetch_operations()
        await self._fetch_detail()

    @rx.event
    async def load_fleet(self):
        self.is_loading = True
        yield
        await seed_dashboard_data()
        await seed_employee_data()
        await seed_equipment_data()
        await self._fetch_reference()
        await self._refresh_all()
        today = datetime.date.today()
        self.today_label = (
            f"{WEEKDAYS_SHORT[today.weekday()]}. {today.day} "
            f"{MONTHS[today.month - 1]} {today.year}"
        )
        self.is_loading = False

    # ------------------------------------------------------------------
    # Filtres & sélection
    # ------------------------------------------------------------------

    @rx.event
    async def set_search(self, value: str):
        self.search = value
        await self._fetch_fleet()
        await self._fetch_detail()

    @rx.event
    async def set_category_filter(self, value: str):
        self.category_filter = value
        await self._fetch_fleet()
        await self._fetch_detail()

    @rx.event
    async def set_status_filter(self, value: str):
        self.status_filter = value
        await self._fetch_fleet()
        await self._fetch_detail()

    @rx.event
    async def set_health_filter(self, value: str):
        self.health_filter = value
        await self._fetch_fleet()
        await self._fetch_detail()

    @rx.event
    async def reset_filters(self):
        self.search = ""
        self.category_filter = "TOUTES"
        self.status_filter = "TOUS"
        self.health_filter = "TOUS"
        self.form_key += 1
        await self._fetch_fleet()
        await self._fetch_detail()

    @rx.event
    async def set_journal_search(self, value: str):
        self.journal_search = value
        await self._fetch_operations()

    @rx.event
    async def set_kind_filter(self, value: str):
        self.kind_filter = value
        await self._fetch_operations()

    @rx.event
    async def set_op_status_filter(self, value: str):
        self.op_status_filter = value
        await self._fetch_operations()

    @rx.event
    async def set_equipment_filter(self, value: str):
        self.equipment_filter = value
        await self._fetch_operations()

    @rx.event
    async def reset_journal_filters(self):
        self.journal_search = ""
        self.kind_filter = "TOUS"
        self.op_status_filter = "TOUS"
        self.equipment_filter = "TOUS"
        self.form_key += 1
        await self._fetch_operations()

    @rx.event
    async def select_equipment(self, equipment_id: int):
        self.selected_equipment_id = equipment_id
        self.cost_error = ""
        self.usage_error = ""
        await self._fetch_detail()

    # ------------------------------------------------------------------
    # Formulaire engin
    # ------------------------------------------------------------------

    @rx.event
    def open_equipment_create(self):
        self.equipment_form = dict(EMPTY_EQUIPMENT_FORM)
        self.equipment_form_mode = "create"
        self.editing_equipment_id = 0
        self.form_error = ""
        self.form_key += 1
        self.show_equipment_form = True

    @rx.event
    async def open_equipment_edit(self):
        if self.selected_equipment_id == 0:
            return rx.toast("Sélectionnez d'abord un engin.")
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT name, COALESCE(code, ''), category, status, ownership,
                               COALESCE(brand, ''), COALESCE(model, ''),
                               COALESCE(serial_number, ''), COALESCE(registration, ''),
                               COALESCE(year, 0), COALESCE(power_hp, 0),
                               COALESCE(working_width_m, 0), usage_unit,
                               COALESCE(usage_counter, 0), purchase_date,
                               COALESCE(purchase_price, 0), COALESCE(residual_value, 0),
                               COALESCE(hourly_cost, 0),
                               COALESCE(fuel_consumption_l_h, 0),
                               COALESCE(storage_location, ''), responsible_id,
                               insurance_expiry, inspection_expiry, next_service_date,
                               COALESCE(next_service_counter, 0),
                               COALESCE(service_interval_days, 0),
                               COALESCE(service_interval_counter, 0),
                               COALESCE(notes, '')
                        FROM equipment WHERE id = :eid
                        """
                    ),
                    {"eid": self.selected_equipment_id},
                )
            ).first()
        if row is None:
            return rx.toast("Engin introuvable.")
        self.equipment_form = {
            "name": str(row[0]),
            "code": str(row[1]),
            "category": str(row[2]),
            "status": str(row[3]),
            "ownership": str(row[4]),
            "brand": str(row[5]),
            "model": str(row[6]),
            "serial_number": str(row[7]),
            "registration": str(row[8]),
            "year": str(int(row[9] or 0)) if row[9] else "",
            "power_hp": f"{float(row[10]):.0f}",
            "working_width_m": f"{float(row[11]):.2f}",
            "usage_unit": str(row[12]),
            "usage_counter": f"{float(row[13]):.1f}",
            "purchase_date": _iso(row[14]),
            "purchase_price": f"{float(row[15]):.2f}",
            "residual_value": f"{float(row[16]):.2f}",
            "hourly_cost": f"{float(row[17]):.2f}",
            "fuel_consumption_l_h": f"{float(row[18]):.2f}",
            "storage_location": str(row[19]),
            "responsible_id": str(int(row[20])) if row[20] else "",
            "insurance_expiry": _iso(row[21]),
            "inspection_expiry": _iso(row[22]),
            "next_service_date": _iso(row[23]),
            "next_service_counter": f"{float(row[24]):.1f}",
            "service_interval_days": str(int(row[25] or 0)),
            "service_interval_counter": f"{float(row[26]):.0f}",
            "notes": str(row[27]),
        }
        self.equipment_form_mode = "edit"
        self.editing_equipment_id = self.selected_equipment_id
        self.form_error = ""
        self.form_key += 1
        self.show_equipment_form = True

    @rx.event
    def close_equipment_form(self):
        self.show_equipment_form = False
        self.form_error = ""

    def _validate_equipment(self, data: dict) -> str:
        name = str(data.get("name", "")).strip()
        code = str(data.get("code", "")).strip()
        year = _to_int(data.get("year"))
        counter = _to_float(data.get("usage_counter"), -1.0)
        price = _to_float(data.get("purchase_price"), -1.0)
        residual = _to_float(data.get("residual_value"), -1.0)
        hourly = _to_float(data.get("hourly_cost"), -1.0)
        interval_days = _to_int(data.get("service_interval_days"), -1)
        current = datetime.date.today().year
        if len(name) < 2:
            return "Le nom de l'engin doit contenir au moins 2 caractères."
        if not code:
            return "Le code de l'engin est obligatoire (ex. M09)."
        if year != 0 and (year < 1950 or year > current + 1):
            return f"L'année doit être comprise entre 1950 et {current + 1}."
        if counter < 0:
            return "Le compteur ne peut pas être négatif."
        if price < 0 or residual < 0:
            return "Les montants d'acquisition ne peuvent pas être négatifs."
        if hourly < 0:
            return "Le coût horaire ne peut pas être négatif."
        if interval_days < 0:
            return "L'intervalle d'entretien ne peut pas être négatif."
        return ""

    @rx.event
    async def submit_equipment(self, form_data: dict):
        error = self._validate_equipment(form_data)
        if error:
            self.form_error = error
            return
        responsible_raw = str(form_data.get("responsible_id", "")).strip()
        params: dict[str, str | int | float | bool | datetime.date | None] = {
            "name": str(form_data.get("name", "")).strip(),
            "code": str(form_data.get("code", "")).strip().upper(),
            "category": str(form_data.get("category", "AUTRE")),
            "status": str(form_data.get("status", "DISPONIBLE")),
            "ownership": str(form_data.get("ownership", "PROPRIETE")),
            "brand": str(form_data.get("brand", "")).strip(),
            "model": str(form_data.get("model", "")).strip(),
            "serial_number": str(form_data.get("serial_number", "")).strip(),
            "registration": str(form_data.get("registration", "")).strip(),
            "year": _to_int(form_data.get("year")),
            "power_hp": _to_float(form_data.get("power_hp")),
            "working_width_m": _to_float(form_data.get("working_width_m")),
            "usage_unit": str(form_data.get("usage_unit", "HEURES")),
            "usage_counter": _to_float(form_data.get("usage_counter")),
            "purchase_date": _to_date(form_data.get("purchase_date")),
            "purchase_price": _to_float(form_data.get("purchase_price")),
            "residual_value": _to_float(form_data.get("residual_value")),
            "hourly_cost": _to_float(form_data.get("hourly_cost")),
            "fuel_consumption_l_h": _to_float(
                form_data.get("fuel_consumption_l_h")
            ),
            "storage_location": str(
                form_data.get("storage_location", "")
            ).strip(),
            "responsible_id": int(responsible_raw) if responsible_raw else None,
            "insurance_expiry": _to_date(form_data.get("insurance_expiry")),
            "inspection_expiry": _to_date(form_data.get("inspection_expiry")),
            "next_service_date": _to_date(form_data.get("next_service_date")),
            "next_service_counter": _to_float(
                form_data.get("next_service_counter")
            ),
            "service_interval_days": _to_int(
                form_data.get("service_interval_days")
            ),
            "service_interval_counter": _to_float(
                form_data.get("service_interval_counter")
            ),
            "notes": str(form_data.get("notes", "")).strip(),
        }

        async with rx.asession() as asession:
            if (
                self.equipment_form_mode == "edit"
                and self.editing_equipment_id > 0
            ):
                params["eid"] = self.editing_equipment_id
                await asession.execute(
                    text(
                        """
                        UPDATE equipment SET
                            name = :name, code = :code, category = :category,
                            status = :status, ownership = :ownership, brand = :brand,
                            model = :model, serial_number = :serial_number,
                            registration = :registration, year = :year,
                            power_hp = :power_hp, working_width_m = :working_width_m,
                            usage_unit = :usage_unit, usage_counter = :usage_counter,
                            purchase_date = :purchase_date,
                            purchase_price = :purchase_price,
                            residual_value = :residual_value,
                            hourly_cost = :hourly_cost,
                            fuel_consumption_l_h = :fuel_consumption_l_h,
                            storage_location = :storage_location,
                            responsible_id = :responsible_id,
                            insurance_expiry = :insurance_expiry,
                            inspection_expiry = :inspection_expiry,
                            next_service_date = :next_service_date,
                            next_service_counter = :next_service_counter,
                            service_interval_days = :service_interval_days,
                            service_interval_counter = :service_interval_counter,
                            notes = :notes
                        WHERE id = :eid
                        """
                    ),
                    params,
                )
                new_id = self.editing_equipment_id
                message = "Fiche engin mise à jour."
            else:
                new_id = int(
                    (
                        await asession.execute(
                            text(
                                """
                                INSERT INTO equipment (
                                    name, code, category, status, ownership, brand,
                                    model, serial_number, registration, year, power_hp,
                                    working_width_m, usage_unit, usage_counter,
                                    purchase_date, purchase_price, residual_value,
                                    hourly_cost, fuel_consumption_l_h, storage_location,
                                    responsible_id, insurance_expiry, inspection_expiry,
                                    next_service_date, next_service_counter,
                                    service_interval_days, service_interval_counter, notes
                                ) VALUES (
                                    :name, :code, :category, :status, :ownership, :brand,
                                    :model, :serial_number, :registration, :year, :power_hp,
                                    :working_width_m, :usage_unit, :usage_counter,
                                    :purchase_date, :purchase_price, :residual_value,
                                    :hourly_cost, :fuel_consumption_l_h, :storage_location,
                                    :responsible_id, :insurance_expiry, :inspection_expiry,
                                    :next_service_date, :next_service_counter,
                                    :service_interval_days, :service_interval_counter, :notes
                                ) RETURNING id
                                """
                            ),
                            params,
                        )
                    ).scalar()
                    or 0
                )
                message = "Engin ajouté à la flotte."
            await asession.commit()

        self.show_equipment_form = False
        self.form_error = ""
        self.form_key += 1
        self.selected_equipment_id = new_id
        await self._fetch_reference()
        await self._refresh_all()
        return rx.toast(message, duration=4000)

    # ------------------------------------------------------------------
    # Opérations de maintenance
    # ------------------------------------------------------------------

    @rx.event
    def open_operation_create(self):
        form = dict(EMPTY_OPERATION_FORM)
        today = datetime.date.today().isoformat()
        form["scheduled_date"] = today
        form["due_date"] = today
        if self.selected_equipment_id > 0:
            form["equipment_id"] = str(self.selected_equipment_id)
        elif self.equipment_options:
            form["equipment_id"] = self.equipment_options[0]["value"]
        self.operation_form = form
        self.operation_form_mode = "create"
        self.editing_operation_id = 0
        self.operation_error = ""
        self.form_key += 1
        self.show_operation_form = True

    @rx.event
    def open_schedule_operation(self, schedule_id: int):
        for schedule in self.schedules:
            if schedule["id"] == schedule_id:
                form = dict(EMPTY_OPERATION_FORM)
                today = datetime.date.today().isoformat()
                form["equipment_id"] = str(self.selected_equipment_id)
                form["schedule_id"] = str(schedule_id)
                form["title"] = schedule["title"]
                form["kind"] = "PREVENTIVE"
                form["priority"] = (
                    "URGENTE" if schedule["days_left"] < 0 else "NORMALE"
                )
                form["scheduled_date"] = today
                form["due_date"] = today
                form["labor_hours"] = f"{schedule['estimated_hours']:.1f}"
                form["labor_cost"] = f"{schedule['estimated_cost']:.2f}"
                form["counter_at_service"] = self.equipment_detail[
                    "usage_counter"
                ]
                self.operation_form = form
                self.operation_form_mode = "create"
                self.editing_operation_id = 0
                self.operation_error = ""
                self.form_key += 1
                self.show_operation_form = True
                return
        return rx.toast("Plan d'entretien introuvable.")

    @rx.event
    async def open_operation_edit(self, operation_id: int):
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT equipment_id, schedule_id, title, kind, status,
                               priority, scheduled_date, due_date, done_date,
                               COALESCE(counter_at_service, 0),
                               COALESCE(downtime_hours, 0), COALESCE(labor_hours, 0),
                               COALESCE(labor_cost, 0), COALESCE(parts_cost, 0),
                               COALESCE(external_cost, 0), is_internal,
                               COALESCE(provider, ''), COALESCE(invoice_reference, ''),
                               responsible_id, COALESCE(failure_description, ''),
                               COALESCE(work_performed, ''), COALESCE(notes, '')
                        FROM maintenance_operation WHERE id = :oid
                        """
                    ),
                    {"oid": operation_id},
                )
            ).first()
        if row is None:
            return rx.toast("Opération introuvable.")
        self.selected_equipment_id = int(row[0])
        await self._fetch_detail()
        self.operation_form = {
            "equipment_id": str(int(row[0])),
            "schedule_id": str(int(row[1])) if row[1] else "",
            "title": str(row[2]),
            "kind": str(row[3]),
            "status": str(row[4]),
            "priority": str(row[5]),
            "scheduled_date": _iso(row[6]),
            "due_date": _iso(row[7]),
            "done_date": _iso(row[8]),
            "counter_at_service": f"{float(row[9]):.1f}",
            "downtime_hours": f"{float(row[10]):.1f}",
            "labor_hours": f"{float(row[11]):.1f}",
            "labor_cost": f"{float(row[12]):.2f}",
            "parts_cost": f"{float(row[13]):.2f}",
            "external_cost": f"{float(row[14]):.2f}",
            "is_internal": "1" if bool(row[15]) else "0",
            "provider": str(row[16]),
            "invoice_reference": str(row[17]),
            "responsible_id": str(int(row[18])) if row[18] else "",
            "failure_description": str(row[19]),
            "work_performed": str(row[20]),
            "notes": str(row[21]),
        }
        self.operation_form_mode = "edit"
        self.editing_operation_id = operation_id
        self.operation_error = ""
        self.form_key += 1
        self.show_operation_form = True

    @rx.event
    def close_operation_form(self):
        self.show_operation_form = False
        self.operation_error = ""

    def _validate_operation(self, data: dict) -> str:
        title = str(data.get("title", "")).strip()
        equipment_raw = str(data.get("equipment_id", "")).strip()
        scheduled = _to_date(data.get("scheduled_date"))
        done = _to_date(data.get("done_date"))
        status = str(data.get("status", "PLANIFIEE"))
        labor = _to_float(data.get("labor_cost"), -1.0)
        parts = _to_float(data.get("parts_cost"), -1.0)
        external = _to_float(data.get("external_cost"), -1.0)
        hours = _to_float(data.get("labor_hours"), -1.0)
        downtime = _to_float(data.get("downtime_hours"), -1.0)
        internal = bool(data.get("is_internal"))
        provider = str(data.get("provider", "")).strip()
        if len(title) < 3:
            return "L'intitulé doit contenir au moins 3 caractères."
        if not equipment_raw:
            return "Sélectionnez l'engin concerné."
        if scheduled is None:
            return "La date planifiée est obligatoire."
        if labor < 0 or parts < 0 or external < 0:
            return "Les coûts ne peuvent pas être négatifs."
        if hours < 0 or downtime < 0:
            return "Les durées ne peuvent pas être négatives."
        if status == "REALISEE" and done is not None and done < scheduled:
            return "La date de réalisation doit suivre la date planifiée."
        if not internal and not provider:
            return "Renseignez le prestataire pour une opération externalisée."
        return ""

    @rx.event
    async def submit_operation(self, form_data: dict):
        error = self._validate_operation(form_data)
        if error:
            self.operation_error = error
            return
        scheduled = _to_date(form_data.get("scheduled_date"))
        due = _to_date(form_data.get("due_date")) or scheduled
        status = str(form_data.get("status", "PLANIFIEE"))
        done = _to_date(form_data.get("done_date"))
        if status == "REALISEE" and done is None:
            done = scheduled
        labor_cost = _to_float(form_data.get("labor_cost"))
        parts_cost = _to_float(form_data.get("parts_cost"))
        external_cost = _to_float(form_data.get("external_cost"))
        schedule_raw = str(form_data.get("schedule_id", "")).strip()
        responsible_raw = str(form_data.get("responsible_id", "")).strip()
        equipment_id = int(str(form_data.get("equipment_id")).strip())
        labor_hours = _to_float(form_data.get("labor_hours"))

        params: dict[str, str | int | float | bool | datetime.date | None] = {
            "equipment_id": equipment_id,
            "schedule_id": int(schedule_raw) if schedule_raw else None,
            "title": str(form_data.get("title", "")).strip(),
            "kind": str(form_data.get("kind", "PREVENTIVE")),
            "status": status,
            "priority": str(form_data.get("priority", "NORMALE")),
            "scheduled_date": scheduled,
            "due_date": due,
            "done_date": done,
            "counter_at_service": _to_float(
                form_data.get("counter_at_service")
            ),
            "downtime_hours": _to_float(form_data.get("downtime_hours")),
            "labor_hours": labor_hours,
            "labor_cost": labor_cost,
            "parts_cost": parts_cost,
            "external_cost": external_cost,
            "total_cost": round(labor_cost + parts_cost + external_cost, 2),
            "is_internal": bool(form_data.get("is_internal")),
            "provider": str(form_data.get("provider", "")).strip(),
            "invoice_reference": str(
                form_data.get("invoice_reference", "")
            ).strip(),
            "responsible_id": int(responsible_raw) if responsible_raw else None,
            "failure_description": str(
                form_data.get("failure_description", "")
            ).strip(),
            "work_performed": str(form_data.get("work_performed", "")).strip(),
            "notes": str(form_data.get("notes", "")).strip(),
        }

        async with rx.asession() as asession:
            if (
                self.operation_form_mode == "edit"
                and self.editing_operation_id > 0
            ):
                params["oid"] = self.editing_operation_id
                await asession.execute(
                    text(
                        """
                        UPDATE maintenance_operation SET
                            equipment_id = :equipment_id, schedule_id = :schedule_id,
                            title = :title, kind = :kind, status = :status,
                            priority = :priority, scheduled_date = :scheduled_date,
                            due_date = :due_date, done_date = :done_date,
                            counter_at_service = :counter_at_service,
                            downtime_hours = :downtime_hours,
                            labor_hours = :labor_hours, labor_cost = :labor_cost,
                            parts_cost = :parts_cost, external_cost = :external_cost,
                            total_cost = :total_cost, is_internal = :is_internal,
                            provider = :provider,
                            invoice_reference = :invoice_reference,
                            responsible_id = :responsible_id,
                            failure_description = :failure_description,
                            work_performed = :work_performed, notes = :notes
                        WHERE id = :oid
                        """
                    ),
                    params,
                )
                operation_id = self.editing_operation_id
                message = "Opération de maintenance mise à jour."
            else:
                operation_id = int(
                    (
                        await asession.execute(
                            text(
                                """
                                INSERT INTO maintenance_operation (
                                    equipment_id, schedule_id, title, kind, status,
                                    priority, scheduled_date, due_date, done_date,
                                    counter_at_service, downtime_hours, labor_hours,
                                    labor_cost, parts_cost, external_cost, total_cost,
                                    is_internal, provider, invoice_reference,
                                    responsible_id, failure_description,
                                    work_performed, notes
                                ) VALUES (
                                    :equipment_id, :schedule_id, :title, :kind, :status,
                                    :priority, :scheduled_date, :due_date, :done_date,
                                    :counter_at_service, :downtime_hours, :labor_hours,
                                    :labor_cost, :parts_cost, :external_cost, :total_cost,
                                    :is_internal, :provider, :invoice_reference,
                                    :responsible_id, :failure_description,
                                    :work_performed, :notes
                                ) RETURNING id
                                """
                            ),
                            params,
                        )
                    ).scalar()
                    or 0
                )
                message = "Opération de maintenance planifiée."

            if params["responsible_id"] is not None:
                await self._sync_assignment(
                    asession,
                    operation_id,
                    int(params["responsible_id"]),
                    equipment_id,
                    params["title"],
                    scheduled,
                    due,
                    labor_hours,
                    status,
                )
            if status == "REALISEE":
                await self._close_maintenance(
                    asession, operation_id, equipment_id, done
                )
            await asession.commit()

        self.show_operation_form = False
        self.operation_error = ""
        self.form_key += 1
        self.selected_equipment_id = equipment_id
        await self._refresh_all()
        return rx.toast(message, duration=4000)

    async def _sync_assignment(
        self,
        asession,
        operation_id: int,
        employee_id: int,
        equipment_id: int,
        title: str,
        start: datetime.date | None,
        end: datetime.date | None,
        hours: float,
        status: str,
    ) -> None:
        """Crée ou met à jour l'affectation du responsable de l'opération."""
        existing = (
            await asession.execute(
                text(
                    """
                    SELECT id FROM assignment
                    WHERE maintenance_id = :oid AND role = 'RESPONSABLE'
                    ORDER BY id LIMIT 1
                    """
                ),
                {"oid": operation_id},
            )
        ).first()
        assignment_status = "TERMINEE" if status == "REALISEE" else "CONFIRMEE"
        payload = {
            "employee_id": employee_id,
            "equipment_id": equipment_id,
            "maintenance_id": operation_id,
            "title": f"Maintenance · {title}",
            "start_date": start,
            "end_date": end or start,
            "planned_hours": hours,
            "actual_hours": hours if status == "REALISEE" else 0.0,
            "status": assignment_status,
        }
        if existing is None:
            await asession.execute(
                text(
                    """
                    INSERT INTO assignment (
                        employee_id, intervention_id, parcel_id, equipment_id,
                        maintenance_id, role, status, title, start_date, end_date,
                        planned_hours, actual_hours, labor_cost, notes
                    ) VALUES (
                        :employee_id, NULL, NULL, :equipment_id,
                        :maintenance_id, 'RESPONSABLE', :status, :title,
                        :start_date, :end_date, :planned_hours, :actual_hours,
                        0, 'Affectation liée à une opération de maintenance.'
                    )
                    """
                ),
                payload,
            )
        else:
            payload["aid"] = int(existing[0])
            await asession.execute(
                text(
                    """
                    UPDATE assignment SET
                        employee_id = :employee_id, equipment_id = :equipment_id,
                        status = :status, title = :title, start_date = :start_date,
                        end_date = :end_date, planned_hours = :planned_hours,
                        actual_hours = :actual_hours
                    WHERE id = :aid
                    """
                ),
                payload,
            )

    async def _close_maintenance(
        self,
        asession,
        operation_id: int,
        equipment_id: int,
        done: datetime.date | None,
    ) -> None:
        """Met à jour le plan d'entretien et les échéances de l'engin."""
        done_date = done or datetime.date.today()
        row = (
            await asession.execute(
                text(
                    """
                    SELECT o.schedule_id, COALESCE(o.counter_at_service, 0),
                           COALESCE(e.service_interval_days, 0),
                           COALESCE(e.service_interval_counter, 0)
                    FROM maintenance_operation o
                    JOIN equipment e ON e.id = o.equipment_id
                    WHERE o.id = :oid
                    """
                ),
                {"oid": operation_id},
            )
        ).first()
        if row is None:
            return
        interval_days = int(row[2] or 0) or 180
        interval_counter = float(row[3] or 0)
        counter = float(row[1] or 0)
        next_date = done_date + datetime.timedelta(days=interval_days)
        await asession.execute(
            text(
                """
                UPDATE equipment SET
                    next_service_date = :next_date,
                    next_service_counter = :next_counter,
                    status = CASE WHEN status = 'EN_MAINTENANCE'
                        THEN 'DISPONIBLE' ELSE status END
                WHERE id = :eid
                """
            ),
            {
                "next_date": next_date,
                "next_counter": counter + interval_counter,
                "eid": equipment_id,
            },
        )
        if row[0] is not None:
            await asession.execute(
                text(
                    """
                    UPDATE maintenance_schedule SET
                        last_done_on = :done_date,
                        last_done_counter = :counter,
                        next_due_on = :next_date,
                        next_due_counter = :next_counter
                    WHERE id = :sid
                    """
                ),
                {
                    "done_date": done_date,
                    "counter": counter,
                    "next_date": next_date,
                    "next_counter": counter + interval_counter,
                    "sid": int(row[0]),
                },
            )

    @rx.event
    async def mark_operation_done(self, operation_id: int):
        today = datetime.date.today()
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT status, equipment_id
                        FROM maintenance_operation WHERE id = :oid
                        """
                    ),
                    {"oid": operation_id},
                )
            ).first()
            if row is None:
                return rx.toast("Opération introuvable.")
            if str(row[0]) == "REALISEE":
                return rx.toast("Cette opération est déjà réalisée.")
            await asession.execute(
                text(
                    """
                    UPDATE maintenance_operation
                    SET status = 'REALISEE', done_date = :d
                    WHERE id = :oid
                    """
                ),
                {"d": today, "oid": operation_id},
            )
            await asession.execute(
                text(
                    """
                    UPDATE assignment
                    SET status = 'TERMINEE',
                        actual_hours = CASE WHEN COALESCE(actual_hours, 0) > 0
                            THEN actual_hours ELSE COALESCE(planned_hours, 0) END
                    WHERE maintenance_id = :oid
                    """
                ),
                {"oid": operation_id},
            )
            await self._close_maintenance(
                asession, operation_id, int(row[1]), today
            )
            await asession.commit()
        await self._refresh_all()
        return rx.toast(
            "Opération réalisée, échéances recalculées.", duration=4000
        )

    @rx.event
    async def start_operation(self, operation_id: int):
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE maintenance_operation
                    SET status = 'EN_COURS'
                    WHERE id = :oid AND status IN ('PLANIFIEE', 'REPORTEE')
                    """
                ),
                {"oid": operation_id},
            )
            await asession.execute(
                text(
                    """
                    UPDATE equipment SET status = 'EN_MAINTENANCE'
                    WHERE id = (SELECT equipment_id FROM maintenance_operation
                                WHERE id = :oid)
                      AND status IN ('DISPONIBLE', 'RESERVE')
                    """
                ),
                {"oid": operation_id},
            )
            await asession.commit()
        await self._refresh_all()
        return rx.toast("Opération démarrée à l'atelier.", duration=3000)

    @rx.event
    async def postpone_operation(self, operation_id: int):
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT scheduled_date, due_date, status
                        FROM maintenance_operation WHERE id = :oid
                        """
                    ),
                    {"oid": operation_id},
                )
            ).first()
            if row is None:
                return rx.toast("Opération introuvable.")
            if str(row[2]) == "REALISEE":
                return rx.toast(
                    "Une opération réalisée ne peut pas être reportée."
                )
            base = as_date(row[0]) or datetime.date.today()
            due = as_date(row[1]) or base
            await asession.execute(
                text(
                    """
                    UPDATE maintenance_operation
                    SET scheduled_date = :s, due_date = :d, status = 'REPORTEE'
                    WHERE id = :oid
                    """
                ),
                {
                    "s": base + datetime.timedelta(days=7),
                    "d": due + datetime.timedelta(days=7),
                    "oid": operation_id,
                },
            )
            await asession.commit()
        await self._refresh_all()
        return rx.toast("Opération reportée de 7 jours.", duration=3000)

    @rx.event
    async def cancel_operation(self, operation_id: int):
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE maintenance_operation SET status = 'ANNULEE'
                    WHERE id = :oid
                    """
                ),
                {"oid": operation_id},
            )
            await asession.execute(
                text(
                    """
                    UPDATE assignment SET status = 'ANNULEE'
                    WHERE maintenance_id = :oid
                    """
                ),
                {"oid": operation_id},
            )
            await asession.commit()
        await self._refresh_all()
        return rx.toast("Opération annulée.", duration=3000)

    # ------------------------------------------------------------------
    # Lignes de coût
    # ------------------------------------------------------------------

    @rx.event
    async def submit_cost(self, form_data: dict):
        self.cost_error = ""
        operation_raw = str(form_data.get("maintenance_id", "")).strip()
        label = str(form_data.get("label", "")).strip()
        quantity = _to_float(form_data.get("quantity"), -1.0)
        unit_price = _to_float(form_data.get("unit_price"), -1.0)
        incurred = _to_date(form_data.get("incurred_on"))
        if not operation_raw:
            self.cost_error = "Choisissez l'opération de maintenance."
            return
        if len(label) < 2:
            self.cost_error = "Le libellé de la ligne est obligatoire."
            return
        if quantity <= 0:
            self.cost_error = "La quantité doit être strictement positive."
            return
        if unit_price < 0:
            self.cost_error = "Le prix unitaire ne peut pas être négatif."
            return

        operation_id = int(operation_raw)
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    INSERT INTO maintenance_cost (
                        maintenance_id, type, label, reference, supplier,
                        quantity, unit, unit_price, amount, incurred_on, notes
                    ) VALUES (
                        :mid, :type, :label, :reference, :supplier,
                        :quantity, :unit, :unit_price, :amount, :incurred_on, ''
                    )
                    """
                ),
                {
                    "mid": operation_id,
                    "type": str(form_data.get("type", "PIECE")),
                    "label": label,
                    "reference": str(form_data.get("reference", "")).strip(),
                    "supplier": str(form_data.get("supplier", "")).strip(),
                    "quantity": quantity,
                    "unit": str(form_data.get("unit", "u")).strip() or "u",
                    "unit_price": unit_price,
                    "amount": round(quantity * unit_price, 2),
                    "incurred_on": incurred or datetime.date.today(),
                },
            )
            await self._recompute_costs(asession, operation_id)
            await asession.commit()

        self.form_key += 1
        await self._refresh_all()
        return rx.toast("Ligne de coût enregistrée.", duration=3000)

    @rx.event
    async def remove_cost(self, cost_id: int):
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        "SELECT maintenance_id FROM maintenance_cost WHERE id = :cid"
                    ),
                    {"cid": cost_id},
                )
            ).first()
            if row is None:
                return rx.toast("Ligne introuvable.")
            await asession.execute(
                text("DELETE FROM maintenance_cost WHERE id = :cid"),
                {"cid": cost_id},
            )
            await self._recompute_costs(asession, int(row[0]))
            await asession.commit()
        await self._refresh_all()
        return rx.toast("Ligne de coût supprimée.", duration=3000)

    async def _recompute_costs(self, asession, operation_id: int) -> None:
        """Reventile les lignes de coût sur l'opération de maintenance."""
        await asession.execute(
            text(
                """
                UPDATE maintenance_operation SET
                    parts_cost = COALESCE((
                        SELECT SUM(amount) FROM maintenance_cost
                        WHERE maintenance_id = :oid
                          AND type IN ('PIECE', 'CONSOMMABLE')), 0),
                    labor_cost = COALESCE((
                        SELECT SUM(amount) FROM maintenance_cost
                        WHERE maintenance_id = :oid
                          AND type = 'MAIN_OEUVRE'), 0),
                    external_cost = COALESCE((
                        SELECT SUM(amount) FROM maintenance_cost
                        WHERE maintenance_id = :oid
                          AND type IN ('SOUS_TRAITANCE', 'TRANSPORT', 'AUTRE')), 0),
                    total_cost = COALESCE((
                        SELECT SUM(amount) FROM maintenance_cost
                        WHERE maintenance_id = :oid), 0)
                WHERE id = :oid
                """
            ),
            {"oid": operation_id},
        )

    # ------------------------------------------------------------------
    # Relevés d'usage
    # ------------------------------------------------------------------

    @rx.event
    async def submit_usage(self, form_data: dict):
        self.usage_error = ""
        if self.selected_equipment_id == 0:
            self.usage_error = "Sélectionnez un engin."
            return
        used_on = _to_date(form_data.get("used_on"))
        start = _to_float(form_data.get("counter_start"), -1.0)
        end = _to_float(form_data.get("counter_end"), -1.0)
        fuel = _to_float(form_data.get("fuel_liters"), -1.0)
        if used_on is None:
            self.usage_error = "La date du relevé est obligatoire."
            return
        if used_on > datetime.date.today() + datetime.timedelta(days=1):
            self.usage_error = "La date du relevé ne peut pas être future."
            return
        if start < 0 or end < 0:
            self.usage_error = "Les compteurs ne peuvent pas être négatifs."
            return
        if end < start:
            self.usage_error = (
                "Le compteur de fin doit être supérieur au compteur de début."
            )
            return
        if fuel < 0:
            self.usage_error = "Le carburant ne peut pas être négatif."
            return
        employee_raw = str(form_data.get("employee_id", "")).strip()

        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    INSERT INTO equipment_usage_log (
                        equipment_id, employee_id, intervention_id, used_on,
                        counter_start, counter_end, hours_used, fuel_liters, notes
                    ) VALUES (
                        :eid, :employee_id, NULL, :used_on,
                        :start, :end, :hours, :fuel, :notes
                    )
                    """
                ),
                {
                    "eid": self.selected_equipment_id,
                    "employee_id": int(employee_raw) if employee_raw else None,
                    "used_on": used_on,
                    "start": start,
                    "end": end,
                    "hours": round(end - start, 2),
                    "fuel": fuel,
                    "notes": str(form_data.get("notes", "")).strip(),
                },
            )
            await asession.execute(
                text(
                    """
                    UPDATE equipment SET usage_counter = :end
                    WHERE id = :eid AND COALESCE(usage_counter, 0) < :end
                    """
                ),
                {"end": end, "eid": self.selected_equipment_id},
            )
            await asession.commit()

        self.form_key += 1
        await self._fetch_fleet()
        await self._fetch_detail()
        return rx.toast("Relevé d'usage enregistré.", duration=3000)

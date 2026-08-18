"""État de l'espace traitements & récoltes.

Journal des interventions, planification, stocks d'intrants, saisie des
récoltes et comparaison des rendements. Toutes les lectures et écritures
passent par `rx.asession()` en SQL brut.
"""

from __future__ import annotations

import datetime
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.date_utils import as_date, iso_or_empty
from app.seed import seed_dashboard_data
from app.seed_operations import seed_operations_data
from app.states.dashboard_state import (
    INTERVENTION_LABELS,
    INTERVENTION_STATUS_LABELS,
    MONTHS,
    WEEKDAYS_SHORT,
)

INTERVENTION_TYPE_KEYS: list[str] = [
    "SEMIS",
    "PLANTATION",
    "FERTILISATION",
    "TRAITEMENT_PHYTO",
    "DESHERBAGE",
    "IRRIGATION",
    "TRAVAIL_DU_SOL",
    "OBSERVATION",
    "RECOLTE",
    "AUTRE",
]

INTERVENTION_STATUS_KEYS: list[str] = [
    "PLANIFIEE",
    "EN_COURS",
    "REALISEE",
    "REPORTEE",
    "ANNULEE",
]

MOVEMENT_TYPE_KEYS: list[str] = ["ENTREE", "SORTIE", "INVENTAIRE", "PERTE"]

QUALITY_KEYS: list[str] = ["A", "B", "C", "DECLASSEE"]

MOVEMENT_LABELS: dict[str, str] = {
    "ENTREE": "Entrée en stock",
    "SORTIE": "Sortie / application",
    "INVENTAIRE": "Inventaire",
    "PERTE": "Perte",
}

CATEGORY_LABELS: dict[str, str] = {
    "ENGRAIS": "Engrais",
    "FONGICIDE": "Fongicide",
    "HERBICIDE": "Herbicide",
    "INSECTICIDE": "Insecticide",
    "SEMENCE": "Semence",
    "AMENDEMENT": "Amendement",
    "BIOSTIMULANT": "Biostimulant",
    "AUTRE": "Autre",
}

QUALITY_LABELS: dict[str, str] = {
    "A": "Qualité A",
    "B": "Qualité B",
    "C": "Qualité C",
    "DECLASSEE": "Déclassée",
}

PERIOD_OPTIONS: list[tuple[str, str, int]] = [
    ("7", "7 derniers jours", 7),
    ("30", "30 derniers jours", 30),
    ("90", "90 derniers jours", 90),
    ("365", "Campagne (365 j)", 365),
    ("TOUT", "Tout l'historique", 0),
]


class Option(TypedDict):
    value: str
    label: str


class JournalRow(TypedDict):
    id: int
    title: str
    type: str
    type_label: str
    status: str
    status_label: str
    tone: str
    parcel: str
    crop_name: str
    scheduled_label: str
    done_label: str
    operator: str
    equipment: str
    target: str
    notes: str
    area_ha: float
    cost: float
    water: float
    duration: float
    product_label: str
    product_count: int
    days_delta: int
    is_overdue: bool
    is_done: bool


class ProductRow(TypedDict):
    id: int
    name: str
    category: str
    category_label: str
    supplier: str
    reference: str
    substance: str
    unit: str
    unit_price: float
    stock: float
    threshold: float
    ratio_pct: str
    ratio: int
    tone: str
    is_critical: bool
    location: str
    expiry_label: str
    organic: bool
    value: float
    reentry: int
    preharvest: int


class MovementRow(TypedDict):
    id: int
    product_name: str
    type: str
    type_label: str
    quantity: float
    unit: str
    date_label: str
    reference: str
    notes: str
    amount: float


class HarvestRow(TypedDict):
    id: int
    crop_name: str
    parcel: str
    species: str
    date_label: str
    quantity: float
    unit: str
    area_ha: float
    yield_t_ha: float
    expected_yield: float
    performance: int
    performance_pct: str
    tone: str
    moisture: float
    quality_label: str
    loss: float
    unit_price: float
    revenue: float
    storage: str
    operator: str
    notes: str


class YieldRow(TypedDict):
    label: str
    sublabel: str
    actual: float
    expected: float
    actual_width: str
    expected_width: str
    quantity: float
    revenue: float
    delta: int
    tone: str


EMPTY_INTERVENTION_FORM: dict[str, str] = {
    "parcel_id": "",
    "crop_id": "",
    "type": "TRAITEMENT_PHYTO",
    "status": "PLANIFIEE",
    "title": "",
    "scheduled_date": "",
    "done_date": "",
    "operator": "",
    "equipment": "",
    "area_treated_ha": "0",
    "water_volume_l_ha": "0",
    "duration_hours": "0",
    "cost": "0",
    "weather_conditions": "",
    "temperature_c": "0",
    "wind_speed_kmh": "0",
    "target": "",
    "notes": "",
    "product_id": "",
    "dose_per_ha": "0",
}

EMPTY_HARVEST_FORM: dict[str, str] = {
    "crop_id": "",
    "harvest_date": "",
    "quantity": "",
    "unit": "t",
    "area_harvested_ha": "",
    "moisture_percent": "14",
    "quality": "A",
    "loss_percent": "0",
    "storage_location": "",
    "unit_price": "0",
    "operator": "",
    "notes": "",
}

EMPTY_MOVEMENT_FORM: dict[str, str] = {
    "product_id": "",
    "type": "ENTREE",
    "quantity": "",
    "unit_price": "0",
    "movement_date": "",
    "reference": "",
    "notes": "",
}

STATUS_TONES: dict[str, str] = {
    "PLANIFIEE": "planned",
    "EN_COURS": "running",
    "REALISEE": "done",
    "REPORTEE": "late",
    "ANNULEE": "cancelled",
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


class OperationsState(rx.State):
    """Traitements, intrants et récoltes de l'exploitation."""

    is_loading: bool = True
    today_label: str = ""

    search: str = ""
    type_filter: str = "TOUS"
    status_filter: str = "TOUS"
    parcel_filter: str = "TOUS"
    period_filter: str = "90"
    stock_view: str = "TOUS"
    yield_mode: str = "PARCELLE"

    kpis: dict[str, float] = {
        "planned": 0.0,
        "done_30": 0.0,
        "overdue": 0.0,
        "cost_30": 0.0,
        "products": 0.0,
        "critical": 0.0,
        "stock_value": 0.0,
        "harvest_qty": 0.0,
        "revenue": 0.0,
        "avg_yield": 0.0,
    }

    journal: list[JournalRow] = []
    products: list[ProductRow] = []
    movements: list[MovementRow] = []
    harvests: list[HarvestRow] = []
    yields_by_parcel: list[YieldRow] = []
    yields_by_crop: list[YieldRow] = []

    parcel_options: list[Option] = []
    crop_options: list[Option] = []
    product_options: list[Option] = []

    type_options: list[Option] = _options(
        INTERVENTION_TYPE_KEYS, INTERVENTION_LABELS
    )
    status_options: list[Option] = _options(
        INTERVENTION_STATUS_KEYS, INTERVENTION_STATUS_LABELS
    )
    movement_options: list[Option] = _options(
        MOVEMENT_TYPE_KEYS, MOVEMENT_LABELS
    )
    quality_options: list[Option] = _options(QUALITY_KEYS, QUALITY_LABELS)
    period_options: list[Option] = [
        {"value": key, "label": label} for key, label, _ in PERIOD_OPTIONS
    ]

    show_intervention_form: bool = False
    intervention_form_mode: str = "create"
    editing_intervention_id: int = 0
    intervention_form: dict[str, str] = EMPTY_INTERVENTION_FORM

    show_harvest_form: bool = False
    harvest_form: dict[str, str] = EMPTY_HARVEST_FORM

    show_movement_form: bool = False
    movement_form: dict[str, str] = EMPTY_MOVEMENT_FORM

    form_error: str = ""
    harvest_error: str = ""
    movement_error: str = ""
    form_key: int = 0

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def journal_count(self) -> int:
        return len(self.journal)

    @rx.var
    def planned_count(self) -> int:
        return len([r for r in self.journal if not r["is_done"]])

    @rx.var
    def journal_cost(self) -> float:
        return round(sum(r["cost"] for r in self.journal), 0)

    @rx.var
    def critical_products(self) -> list[ProductRow]:
        return [p for p in self.products if p["is_critical"]][:4]

    @rx.var
    def visible_products(self) -> list[ProductRow]:
        if self.stock_view == "CRITIQUE":
            return [p for p in self.products if p["is_critical"]]
        if self.stock_view == "BIO":
            return [p for p in self.products if p["organic"]]
        return self.products

    @rx.var
    def yield_rows(self) -> list[YieldRow]:
        if self.yield_mode == "CULTURE":
            return self.yields_by_crop
        return self.yields_by_parcel

    @rx.var
    def intervention_form_title(self) -> str:
        if self.intervention_form_mode == "edit":
            return "Modifier l'intervention"
        return "Planifier une intervention"

    @rx.var
    def harvest_count(self) -> int:
        return len(self.harvests)

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    def _period_start(self) -> datetime.date | None:
        for key, _label, days in PERIOD_OPTIONS:
            if key == self.period_filter and days > 0:
                return datetime.date.today() - datetime.timedelta(days=days)
        return None

    async def _fetch_kpis(self) -> None:
        today = datetime.date.today()
        since = today - datetime.timedelta(days=30)
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            (SELECT COUNT(*) FROM intervention
                               WHERE status IN ('PLANIFIEE', 'EN_COURS', 'REPORTEE')
                                 AND scheduled_date >= :today),
                            (SELECT COUNT(*) FROM intervention
                               WHERE status = 'REALISEE' AND done_date >= :since),
                            (SELECT COUNT(*) FROM intervention
                               WHERE status IN ('PLANIFIEE', 'EN_COURS', 'REPORTEE')
                                 AND scheduled_date < :today),
                            (SELECT COALESCE(SUM(cost), 0) FROM intervention
                               WHERE scheduled_date >= :since),
                            (SELECT COUNT(*) FROM product),
                            (SELECT COUNT(*) FROM product
                               WHERE quantity_in_stock <= reorder_threshold),
                            (SELECT COALESCE(SUM(quantity_in_stock * unit_price), 0)
                               FROM product),
                            (SELECT COALESCE(SUM(quantity), 0) FROM harvest),
                            (SELECT COALESCE(SUM(revenue), 0) FROM harvest),
                            (SELECT COALESCE(AVG(yield_t_ha), 0) FROM harvest)
                        """
                    ),
                    {"today": today, "since": since},
                )
            ).first()
        self.kpis = {
            "planned": float(row[0] or 0) if row else 0.0,
            "done_30": float(row[1] or 0) if row else 0.0,
            "overdue": float(row[2] or 0) if row else 0.0,
            "cost_30": float(row[3] or 0) if row else 0.0,
            "products": float(row[4] or 0) if row else 0.0,
            "critical": float(row[5] or 0) if row else 0.0,
            "stock_value": float(row[6] or 0) if row else 0.0,
            "harvest_qty": float(row[7] or 0) if row else 0.0,
            "revenue": float(row[8] or 0) if row else 0.0,
            "avg_yield": float(row[9] or 0) if row else 0.0,
        }

    async def _fetch_journal(self) -> None:
        today = datetime.date.today()
        clauses = ["1=1"]
        params: dict[str, str | datetime.date | int] = {}
        query = self.search.strip().lower()
        if query:
            clauses.append(
                "(LOWER(i.title) LIKE :q OR LOWER(i.operator) LIKE :q"
                " OR LOWER(i.target) LIKE :q OR LOWER(i.equipment) LIKE :q"
                " OR LOWER(p.name) LIKE :q OR LOWER(COALESCE(c.name, '')) LIKE :q)"
            )
            params["q"] = f"%{query}%"
        if self.type_filter != "TOUS":
            clauses.append("i.type = :itype")
            params["itype"] = self.type_filter
        if self.status_filter != "TOUS":
            clauses.append("i.status = :istatus")
            params["istatus"] = self.status_filter
        if self.parcel_filter != "TOUS":
            clauses.append("i.parcel_id = :pid")
            params["pid"] = int(self.parcel_filter)
        start = self._period_start()
        if start is not None:
            clauses.append("i.scheduled_date >= :start")
            params["start"] = start
        where = " AND ".join(clauses)

        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT i.id, i.title, i.type, i.status, i.scheduled_date,
                               i.done_date, p.name, COALESCE(c.name, ''),
                               COALESCE(i.operator, ''), COALESCE(i.equipment, ''),
                               COALESCE(i.target, ''), COALESCE(i.notes, ''),
                               COALESCE(i.area_treated_ha, 0), COALESCE(i.cost, 0),
                               COALESCE(i.water_volume_l_ha, 0),
                               COALESCE(i.duration_hours, 0),
                               (SELECT COUNT(*) FROM intervention_product ip
                                  WHERE ip.intervention_id = i.id),
                               (SELECT pr.name FROM intervention_product ip
                                  JOIN product pr ON pr.id = ip.product_id
                                  WHERE ip.intervention_id = i.id
                                  ORDER BY ip.id LIMIT 1)
                        FROM intervention i
                        JOIN parcel p ON p.id = i.parcel_id
                        LEFT JOIN crop c ON c.id = i.crop_id
                        WHERE {where}
                        ORDER BY i.scheduled_date DESC, i.id DESC
                        LIMIT 60
                        """
                    ),
                    params,
                )
            ).all()

        journal: list[JournalRow] = []
        for row in rows:
            i_type = str(row[2])
            i_status = str(row[3])
            scheduled = as_date(row[4])
            count = int(row[16] or 0)
            first_product = str(row[17]) if row[17] else ""
            if count == 0:
                product_label = "Aucun intrant"
            elif count == 1:
                product_label = first_product
            else:
                product_label = f"{first_product} +{count - 1}"
            journal.append(
                {
                    "id": int(row[0]),
                    "title": str(row[1]),
                    "type": i_type,
                    "type_label": INTERVENTION_LABELS.get(i_type, i_type),
                    "status": i_status,
                    "status_label": INTERVENTION_STATUS_LABELS.get(
                        i_status, i_status
                    ),
                    "tone": STATUS_TONES.get(i_status, "planned"),
                    "parcel": str(row[6]),
                    "crop_name": str(row[7]) or "Sans culture liée",
                    "scheduled_label": _fmt_date(scheduled),
                    "done_label": _fmt_date(row[5]),
                    "operator": str(row[8]) or "Non affecté",
                    "equipment": str(row[9]) or "—",
                    "target": str(row[10]) or "—",
                    "notes": str(row[11]) or "—",
                    "area_ha": float(row[12] or 0),
                    "cost": float(row[13] or 0),
                    "water": float(row[14] or 0),
                    "duration": float(row[15] or 0),
                    "product_label": product_label,
                    "product_count": count,
                    "days_delta": (scheduled - today).days if scheduled else 0,
                    "is_overdue": bool(
                        scheduled
                        and scheduled < today
                        and i_status in ("PLANIFIEE", "EN_COURS", "REPORTEE")
                    ),
                    "is_done": i_status in ("REALISEE", "ANNULEE"),
                }
            )
        self.journal = journal

    async def _fetch_stock(self) -> None:
        today = datetime.date.today()
        async with rx.asession() as asession:
            product_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT id, name, category, COALESCE(supplier, ''),
                               COALESCE(reference, ''), COALESCE(active_substance, ''),
                               COALESCE(unit, ''), COALESCE(unit_price, 0),
                               COALESCE(quantity_in_stock, 0),
                               COALESCE(reorder_threshold, 0),
                               COALESCE(storage_location, ''), expiry_date,
                               is_organic_approved, COALESCE(reentry_delay_hours, 0),
                               COALESCE(preharvest_delay_days, 0)
                        FROM product
                        ORDER BY (COALESCE(quantity_in_stock, 0)
                                  - COALESCE(reorder_threshold, 0)) ASC, name
                        LIMIT 40
                        """
                    )
                )
            ).all()

            movement_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT m.id, pr.name, m.type, COALESCE(m.quantity, 0),
                               COALESCE(pr.unit, ''), m.movement_date,
                               COALESCE(m.reference, ''), COALESCE(m.notes, ''),
                               COALESCE(m.quantity, 0) * COALESCE(m.unit_price, 0)
                        FROM stock_movement m
                        JOIN product pr ON pr.id = m.product_id
                        ORDER BY m.movement_date DESC NULLS LAST, m.id DESC
                        LIMIT 12
                        """
                    )
                )
            ).all()

        products: list[ProductRow] = []
        for row in product_rows:
            category = str(row[2])
            stock = float(row[8] or 0)
            threshold = float(row[9] or 0)
            reference = max(threshold * 2.0, stock, 1.0)
            ratio = int(min(100.0, stock / reference * 100.0))
            is_critical = stock <= threshold
            if is_critical:
                tone = "bad"
            elif stock <= threshold * 1.5:
                tone = "warn"
            else:
                tone = "good"
            expiry = as_date(row[11])
            if expiry is None:
                expiry_label = "Sans péremption"
            elif expiry < today:
                expiry_label = f"Périmé le {_fmt_date(expiry)}"
            else:
                expiry_label = f"Péremption {_fmt_date(expiry)}"
            products.append(
                {
                    "id": int(row[0]),
                    "name": str(row[1]),
                    "category": category,
                    "category_label": CATEGORY_LABELS.get(category, category),
                    "supplier": str(row[3]) or "Fournisseur non précisé",
                    "reference": str(row[4]) or "—",
                    "substance": str(row[5]) or "—",
                    "unit": str(row[6]) or "u",
                    "unit_price": float(row[7] or 0),
                    "stock": stock,
                    "threshold": threshold,
                    "ratio_pct": f"{ratio}%",
                    "ratio": ratio,
                    "tone": tone,
                    "is_critical": is_critical,
                    "location": str(row[10]) or "Emplacement non précisé",
                    "expiry_label": expiry_label,
                    "organic": bool(row[12]),
                    "value": stock * float(row[7] or 0),
                    "reentry": int(row[13] or 0),
                    "preharvest": int(row[14] or 0),
                }
            )
        self.products = products

        self.movements = [
            {
                "id": int(row[0]),
                "product_name": str(row[1]),
                "type": str(row[2]),
                "type_label": MOVEMENT_LABELS.get(row[2], row[2]),
                "quantity": float(row[3] or 0),
                "unit": str(row[4]) or "u",
                "date_label": _fmt_date(row[5]),
                "reference": str(row[6]) or "—",
                "notes": str(row[7]) or "—",
                "amount": float(row[8] or 0),
            }
            for row in movement_rows
        ]

    async def _fetch_harvests(self) -> None:
        async with rx.asession() as asession:
            harvest_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT h.id, c.name, p.name, COALESCE(v.species, ''),
                               h.harvest_date, COALESCE(h.quantity, 0),
                               COALESCE(h.unit, 't'), COALESCE(h.area_harvested_ha, 0),
                               COALESCE(h.yield_t_ha, 0),
                               COALESCE(c.expected_yield_t_ha, 0),
                               COALESCE(h.moisture_percent, 0), h.quality,
                               COALESCE(h.loss_percent, 0), COALESCE(h.unit_price, 0),
                               COALESCE(h.revenue, 0),
                               COALESCE(h.storage_location, ''),
                               COALESCE(h.operator, ''), COALESCE(h.notes, '')
                        FROM harvest h
                        JOIN crop c ON c.id = h.crop_id
                        JOIN parcel p ON p.id = c.parcel_id
                        LEFT JOIN crop_variety v ON v.id = c.variety_id
                        ORDER BY h.harvest_date DESC NULLS LAST, h.id DESC
                        LIMIT 24
                        """
                    )
                )
            ).all()

            parcel_yield_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT p.name, p.code,
                               COALESCE(AVG(h.yield_t_ha), 0),
                               COALESCE(AVG(c.expected_yield_t_ha), 0),
                               COALESCE(SUM(h.quantity), 0),
                               COALESCE(SUM(h.revenue), 0)
                        FROM harvest h
                        JOIN crop c ON c.id = h.crop_id
                        JOIN parcel p ON p.id = c.parcel_id
                        GROUP BY p.name, p.code
                        ORDER BY AVG(h.yield_t_ha) DESC
                        LIMIT 10
                        """
                    )
                )
            ).all()

            crop_yield_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT c.name, COALESCE(v.species, ''),
                               COALESCE(AVG(h.yield_t_ha), 0),
                               COALESCE(AVG(c.expected_yield_t_ha), 0),
                               COALESCE(SUM(h.quantity), 0),
                               COALESCE(SUM(h.revenue), 0)
                        FROM harvest h
                        JOIN crop c ON c.id = h.crop_id
                        LEFT JOIN crop_variety v ON v.id = c.variety_id
                        GROUP BY c.name, COALESCE(v.species, '')
                        ORDER BY AVG(h.yield_t_ha) DESC
                        LIMIT 10
                        """
                    )
                )
            ).all()

        harvests: list[HarvestRow] = []
        for row in harvest_rows:
            actual = float(row[8] or 0)
            expected = float(row[9] or 0)
            performance = int(actual / expected * 100) if expected > 0 else 0
            if performance >= 95:
                tone = "good"
            elif performance >= 80:
                tone = "warn"
            else:
                tone = "bad"
            quality = str(row[11])
            harvests.append(
                {
                    "id": int(row[0]),
                    "crop_name": str(row[1]),
                    "parcel": str(row[2]),
                    "species": str(row[3]) or "Espèce non renseignée",
                    "date_label": _fmt_date(row[4]),
                    "quantity": float(row[5] or 0),
                    "unit": str(row[6]) or "t",
                    "area_ha": float(row[7] or 0),
                    "yield_t_ha": actual,
                    "expected_yield": expected,
                    "performance": performance,
                    "performance_pct": f"{min(performance, 130)}%",
                    "tone": tone,
                    "moisture": float(row[10] or 0),
                    "quality_label": QUALITY_LABELS.get(quality, quality),
                    "loss": float(row[12] or 0),
                    "unit_price": float(row[13] or 0),
                    "revenue": float(row[14] or 0),
                    "storage": str(row[15]) or "—",
                    "operator": str(row[16]) or "—",
                    "notes": str(row[17]) or "—",
                }
            )
        self.harvests = harvests

        self.yields_by_parcel = self._build_yield_rows(
            [
                (str(row[0]), f"Îlot {row[1]}", row[2], row[3], row[4], row[5])
                for row in parcel_yield_rows
            ]
        )
        self.yields_by_crop = self._build_yield_rows(
            [
                (
                    str(row[0]),
                    str(row[1]) or "Espèce non renseignée",
                    row[2],
                    row[3],
                    row[4],
                    row[5],
                )
                for row in crop_yield_rows
            ]
        )

    def _build_yield_rows(self, raw: list[tuple]) -> list[YieldRow]:
        peak = 1.0
        for item in raw:
            peak = max(peak, float(item[2] or 0), float(item[3] or 0))
        rows: list[YieldRow] = []
        for label, sublabel, actual_raw, expected_raw, qty, revenue in raw:
            actual = float(actual_raw or 0)
            expected = float(expected_raw or 0)
            delta = (
                int((actual - expected) / expected * 100) if expected > 0 else 0
            )
            if delta >= -5:
                tone = "good"
            elif delta >= -20:
                tone = "warn"
            else:
                tone = "bad"
            rows.append(
                {
                    "label": label,
                    "sublabel": sublabel,
                    "actual": actual,
                    "expected": expected,
                    "actual_width": f"{min(100.0, actual / peak * 100.0):.0f}%",
                    "expected_width": f"{min(100.0, expected / peak * 100.0):.0f}%",
                    "quantity": float(qty or 0),
                    "revenue": float(revenue or 0),
                    "delta": delta,
                    "tone": tone,
                }
            )
        return rows

    async def _fetch_reference(self) -> None:
        async with rx.asession() as asession:
            parcel_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT id, name, COALESCE(code, '')
                        FROM parcel ORDER BY code, name LIMIT 200
                        """
                    )
                )
            ).all()
            crop_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT c.id, c.name, p.name
                        FROM crop c JOIN parcel p ON p.id = c.parcel_id
                        ORDER BY p.code, c.name LIMIT 200
                        """
                    )
                )
            ).all()
            product_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT id, name, COALESCE(unit, '')
                        FROM product ORDER BY name LIMIT 200
                        """
                    )
                )
            ).all()

        self.parcel_options = [
            {"value": str(int(row[0])), "label": f"{row[2]} · {row[1]}"}
            for row in parcel_rows
        ]
        self.crop_options = [
            {"value": str(int(row[0])), "label": f"{row[1]} · {row[2]}"}
            for row in crop_rows
        ]
        self.product_options = [
            {"value": str(int(row[0])), "label": f"{row[1]} ({row[2]})"}
            for row in product_rows
        ]

    async def _refresh_all(self) -> None:
        await self._fetch_kpis()
        await self._fetch_journal()
        await self._fetch_stock()
        await self._fetch_harvests()

    @rx.event
    async def load_operations(self):
        self.is_loading = True
        yield
        await seed_dashboard_data()
        await seed_operations_data()
        await self._fetch_reference()
        await self._refresh_all()
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
        await self._fetch_journal()

    @rx.event
    async def set_type_filter(self, value: str):
        self.type_filter = value
        await self._fetch_journal()

    @rx.event
    async def set_status_filter(self, value: str):
        self.status_filter = value
        await self._fetch_journal()

    @rx.event
    async def set_parcel_filter(self, value: str):
        self.parcel_filter = value
        await self._fetch_journal()

    @rx.event
    async def set_period_filter(self, value: str):
        self.period_filter = value
        await self._fetch_journal()

    @rx.event
    async def reset_filters(self):
        self.search = ""
        self.type_filter = "TOUS"
        self.status_filter = "TOUS"
        self.parcel_filter = "TOUS"
        self.period_filter = "90"
        self.form_key += 1
        await self._fetch_journal()

    @rx.event
    def set_stock_view(self, value: str):
        self.stock_view = value

    @rx.event
    def set_yield_mode(self, value: str):
        self.yield_mode = value

    # ------------------------------------------------------------------
    # Interventions
    # ------------------------------------------------------------------

    @rx.event
    def open_intervention_create(self):
        form = dict(EMPTY_INTERVENTION_FORM)
        form["scheduled_date"] = datetime.date.today().isoformat()
        if self.parcel_options:
            form["parcel_id"] = self.parcel_options[0]["value"]
        self.intervention_form = form
        self.intervention_form_mode = "create"
        self.editing_intervention_id = 0
        self.form_error = ""
        self.form_key += 1
        self.show_intervention_form = True

    @rx.event
    async def open_intervention_edit(self, intervention_id: int):
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT parcel_id, crop_id, type, status, title,
                               scheduled_date, done_date, COALESCE(operator, ''),
                               COALESCE(equipment, ''), COALESCE(area_treated_ha, 0),
                               COALESCE(water_volume_l_ha, 0),
                               COALESCE(duration_hours, 0), COALESCE(cost, 0),
                               COALESCE(weather_conditions, ''),
                               COALESCE(temperature_c, 0), COALESCE(wind_speed_kmh, 0),
                               COALESCE(target, ''), COALESCE(notes, '')
                        FROM intervention WHERE id = :iid
                        """
                    ),
                    {"iid": intervention_id},
                )
            ).first()
        if row is None:
            return rx.toast("Intervention introuvable.")
        self.intervention_form = {
            "parcel_id": str(int(row[0])),
            "crop_id": str(int(row[1])) if row[1] else "",
            "type": str(row[2]),
            "status": str(row[3]),
            "title": str(row[4]),
            "scheduled_date": _iso(row[5]),
            "done_date": _iso(row[6]),
            "operator": str(row[7]),
            "equipment": str(row[8]),
            "area_treated_ha": f"{float(row[9]):.2f}",
            "water_volume_l_ha": f"{float(row[10]):.2f}",
            "duration_hours": f"{float(row[11]):.2f}",
            "cost": f"{float(row[12]):.2f}",
            "weather_conditions": str(row[13]),
            "temperature_c": f"{float(row[14]):.1f}",
            "wind_speed_kmh": f"{float(row[15]):.1f}",
            "target": str(row[16]),
            "notes": str(row[17]),
            "product_id": "",
            "dose_per_ha": "0",
        }
        self.intervention_form_mode = "edit"
        self.editing_intervention_id = intervention_id
        self.form_error = ""
        self.form_key += 1
        self.show_intervention_form = True

    @rx.event
    def close_intervention_form(self):
        self.show_intervention_form = False
        self.form_error = ""

    def _validate_intervention(self, data: dict) -> str:
        title = str(data.get("title", "")).strip()
        parcel_raw = str(data.get("parcel_id", "")).strip()
        scheduled = _to_date(data.get("scheduled_date"))
        area = _to_float(data.get("area_treated_ha"))
        cost = _to_float(data.get("cost"))
        dose = _to_float(data.get("dose_per_ha"))
        product_raw = str(data.get("product_id", "")).strip()
        status = str(data.get("status", "PLANIFIEE"))
        done = _to_date(data.get("done_date"))
        if len(title) < 3:
            return "L'intitulé doit contenir au moins 3 caractères."
        if not parcel_raw:
            return "Sélectionnez la parcelle concernée."
        if scheduled is None:
            return "La date planifiée est obligatoire."
        if area < 0 or area > 5000:
            return "La surface traitée doit être comprise entre 0 et 5000 ha."
        if cost < 0:
            return "Le coût ne peut pas être négatif."
        if product_raw and dose <= 0:
            return "Indiquez une dose par hectare pour l'intrant choisi."
        if product_raw and area <= 0:
            return "Une surface traitée est nécessaire pour calculer la dose."
        if status == "REALISEE" and done is not None and done < scheduled:
            return "La date de réalisation doit suivre la date planifiée."
        return ""

    @rx.event
    async def submit_intervention(self, form_data: dict):
        error = self._validate_intervention(form_data)
        if error:
            self.form_error = error
            return
        scheduled = _to_date(form_data.get("scheduled_date"))
        status = str(form_data.get("status", "PLANIFIEE"))
        done = _to_date(form_data.get("done_date"))
        if status == "REALISEE" and done is None:
            done = scheduled
        crop_raw = str(form_data.get("crop_id", "")).strip()
        area = _to_float(form_data.get("area_treated_ha"))
        params: dict[str, str | int | float | None | datetime.date] = {
            "parcel_id": int(str(form_data.get("parcel_id")).strip()),
            "crop_id": int(crop_raw) if crop_raw else None,
            "type": str(form_data.get("type", "OBSERVATION")),
            "status": status,
            "title": str(form_data.get("title", "")).strip(),
            "scheduled_date": scheduled,
            "done_date": done,
            "operator": str(form_data.get("operator", "")).strip(),
            "equipment": str(form_data.get("equipment", "")).strip(),
            "area_treated_ha": area,
            "water_volume_l_ha": _to_float(form_data.get("water_volume_l_ha")),
            "duration_hours": _to_float(form_data.get("duration_hours")),
            "cost": _to_float(form_data.get("cost")),
            "weather_conditions": str(
                form_data.get("weather_conditions", "")
            ).strip(),
            "temperature_c": _to_float(form_data.get("temperature_c")),
            "wind_speed_kmh": _to_float(form_data.get("wind_speed_kmh")),
            "target": str(form_data.get("target", "")).strip(),
            "notes": str(form_data.get("notes", "")).strip(),
        }
        product_raw = str(form_data.get("product_id", "")).strip()
        dose = _to_float(form_data.get("dose_per_ha"))

        async with rx.asession() as asession:
            if (
                self.intervention_form_mode == "edit"
                and self.editing_intervention_id > 0
            ):
                params["iid"] = self.editing_intervention_id
                await asession.execute(
                    text(
                        """
                        UPDATE intervention SET
                            parcel_id = :parcel_id, crop_id = :crop_id,
                            type = :type, status = :status, title = :title,
                            scheduled_date = :scheduled_date, done_date = :done_date,
                            operator = :operator, equipment = :equipment,
                            area_treated_ha = :area_treated_ha,
                            water_volume_l_ha = :water_volume_l_ha,
                            duration_hours = :duration_hours, cost = :cost,
                            weather_conditions = :weather_conditions,
                            temperature_c = :temperature_c,
                            wind_speed_kmh = :wind_speed_kmh,
                            target = :target, notes = :notes
                        WHERE id = :iid
                        """
                    ),
                    params,
                )
                intervention_id = self.editing_intervention_id
                message = "Intervention mise à jour."
            else:
                intervention_id = int(
                    (
                        await asession.execute(
                            text(
                                """
                                INSERT INTO intervention (
                                    parcel_id, crop_id, type, status, title,
                                    scheduled_date, done_date, operator, equipment,
                                    area_treated_ha, water_volume_l_ha, duration_hours,
                                    cost, weather_conditions, temperature_c,
                                    wind_speed_kmh, target, notes
                                ) VALUES (
                                    :parcel_id, :crop_id, :type, :status, :title,
                                    :scheduled_date, :done_date, :operator, :equipment,
                                    :area_treated_ha, :water_volume_l_ha, :duration_hours,
                                    :cost, :weather_conditions, :temperature_c,
                                    :wind_speed_kmh, :target, :notes
                                ) RETURNING id
                                """
                            ),
                            params,
                        )
                    ).scalar()
                    or 0
                )
                message = "Intervention planifiée."

            if product_raw and dose > 0 and area > 0:
                product_id = int(product_raw)
                product = (
                    await asession.execute(
                        text(
                            """
                            SELECT COALESCE(unit, ''), COALESCE(unit_price, 0)
                            FROM product WHERE id = :pid
                            """
                        ),
                        {"pid": product_id},
                    )
                ).first()
                unit = str(product[0]) if product else ""
                price = float(product[1] or 0) if product else 0.0
                total = round(dose * area, 3)
                await asession.execute(
                    text(
                        """
                        INSERT INTO intervention_product (
                            intervention_id, product_id, dose_per_ha,
                            total_quantity, unit, cost, notes
                        ) VALUES (
                            :iid, :pid, :dose, :total, :unit, :cost, :notes
                        )
                        """
                    ),
                    {
                        "iid": intervention_id,
                        "pid": product_id,
                        "dose": dose,
                        "total": total,
                        "unit": unit,
                        "cost": round(total * price, 2),
                        "notes": f"{dose} {unit}/ha sur {area:.1f} ha.",
                    },
                )
                if status == "REALISEE":
                    await self._consume_product(
                        asession,
                        product_id,
                        total,
                        price,
                        intervention_id,
                        done or scheduled,
                    )
            await asession.commit()

        self.show_intervention_form = False
        self.form_error = ""
        self.form_key += 1
        await self._refresh_all()
        return rx.toast(message, duration=4000)

    async def _consume_product(
        self,
        asession,
        product_id: int,
        quantity: float,
        unit_price: float,
        intervention_id: int,
        movement_date: datetime.date | None,
    ) -> None:
        await asession.execute(
            text(
                """
                INSERT INTO stock_movement (
                    product_id, type, quantity, unit_price, movement_date,
                    reference, intervention_id, notes
                ) VALUES (
                    :pid, 'SORTIE', :qty, :price, :mdate, :ref, :iid, :notes
                )
                """
            ),
            {
                "pid": product_id,
                "qty": quantity,
                "price": unit_price,
                "mdate": movement_date or datetime.date.today(),
                "ref": f"INT-{intervention_id}",
                "iid": intervention_id,
                "notes": "Sortie automatique liée à une intervention réalisée.",
            },
        )
        await asession.execute(
            text(
                """
                UPDATE product SET quantity_in_stock =
                    CASE WHEN COALESCE(quantity_in_stock, 0) - :qty < 0 THEN 0
                         ELSE COALESCE(quantity_in_stock, 0) - :qty END
                WHERE id = :pid
                """
            ),
            {"qty": quantity, "pid": product_id},
        )

    @rx.event
    async def mark_done(self, intervention_id: int):
        today = datetime.date.today()
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text("SELECT status FROM intervention WHERE id = :iid"),
                    {"iid": intervention_id},
                )
            ).first()
            if row is None:
                return rx.toast("Intervention introuvable.")
            if str(row[0]) == "REALISEE":
                return rx.toast("Cette intervention est déjà réalisée.")
            await asession.execute(
                text(
                    """
                    UPDATE intervention
                    SET status = 'REALISEE', done_date = :d
                    WHERE id = :iid
                    """
                ),
                {"d": today, "iid": intervention_id},
            )
            applied = (
                await asession.execute(
                    text(
                        """
                        SELECT ip.product_id, COALESCE(ip.total_quantity, 0),
                               COALESCE(pr.unit_price, 0)
                        FROM intervention_product ip
                        JOIN product pr ON pr.id = ip.product_id
                        WHERE ip.intervention_id = :iid
                        """
                    ),
                    {"iid": intervention_id},
                )
            ).all()
            for item in applied:
                quantity = float(item[1] or 0)
                if quantity <= 0:
                    continue
                await self._consume_product(
                    asession,
                    int(item[0]),
                    quantity,
                    float(item[2] or 0),
                    intervention_id,
                    today,
                )
            await asession.commit()

        await self._refresh_all()
        return rx.toast(
            "Intervention réalisée, stocks mis à jour.", duration=4000
        )

    @rx.event
    async def postpone(self, intervention_id: int):
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        "SELECT scheduled_date, status FROM intervention WHERE id = :iid"
                    ),
                    {"iid": intervention_id},
                )
            ).first()
            if row is None:
                return rx.toast("Intervention introuvable.")
            if str(row[1]) == "REALISEE":
                return rx.toast(
                    "Une intervention réalisée ne peut pas être reportée."
                )
            base = as_date(row[0]) or datetime.date.today()
            await asession.execute(
                text(
                    """
                    UPDATE intervention
                    SET scheduled_date = :d, status = 'REPORTEE'
                    WHERE id = :iid
                    """
                ),
                {
                    "d": base + datetime.timedelta(days=7),
                    "iid": intervention_id,
                },
            )
            await asession.commit()
        await self._refresh_all()
        return rx.toast("Chantier reporté de 7 jours.", duration=4000)

    @rx.event
    async def cancel_intervention(self, intervention_id: int):
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    "UPDATE intervention SET status = 'ANNULEE' WHERE id = :iid"
                ),
                {"iid": intervention_id},
            )
            await asession.commit()
        await self._refresh_all()
        return rx.toast("Intervention annulée.", duration=4000)

    # ------------------------------------------------------------------
    # Récoltes
    # ------------------------------------------------------------------

    @rx.event
    def open_harvest_form(self):
        form = dict(EMPTY_HARVEST_FORM)
        form["harvest_date"] = datetime.date.today().isoformat()
        if self.crop_options:
            form["crop_id"] = self.crop_options[0]["value"]
        self.harvest_form = form
        self.harvest_error = ""
        self.form_key += 1
        self.show_harvest_form = True

    @rx.event
    def close_harvest_form(self):
        self.show_harvest_form = False
        self.harvest_error = ""

    def _validate_harvest(self, data: dict) -> str:
        crop_raw = str(data.get("crop_id", "")).strip()
        harvest_date = _to_date(data.get("harvest_date"))
        quantity = _to_float(data.get("quantity"), -1.0)
        area = _to_float(data.get("area_harvested_ha"), -1.0)
        moisture = _to_float(data.get("moisture_percent"))
        loss = _to_float(data.get("loss_percent"))
        price = _to_float(data.get("unit_price"))
        if not crop_raw:
            return "Sélectionnez la culture récoltée."
        if harvest_date is None:
            return "La date de récolte est obligatoire."
        if harvest_date > datetime.date.today() + datetime.timedelta(days=1):
            return "La date de récolte ne peut pas être future."
        if quantity <= 0:
            return "La quantité récoltée doit être strictement positive."
        if area <= 0:
            return "La surface récoltée doit être strictement positive."
        if moisture < 0 or moisture > 45:
            return "L'humidité doit être comprise entre 0 et 45 %."
        if loss < 0 or loss > 100:
            return "Les pertes doivent être comprises entre 0 et 100 %."
        if price < 0:
            return "Le prix unitaire ne peut pas être négatif."
        return ""

    @rx.event
    async def submit_harvest(self, form_data: dict):
        error = self._validate_harvest(form_data)
        if error:
            self.harvest_error = error
            return
        crop_id = int(str(form_data.get("crop_id")).strip())
        quantity = _to_float(form_data.get("quantity"))
        area = _to_float(form_data.get("area_harvested_ha"))
        price = _to_float(form_data.get("unit_price"))
        harvest_date = _to_date(form_data.get("harvest_date"))
        close_crop = bool(form_data.get("close_crop"))

        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    INSERT INTO harvest (
                        crop_id, harvest_date, quantity, unit, area_harvested_ha,
                        yield_t_ha, moisture_percent, quality, loss_percent,
                        storage_location, unit_price, revenue, operator, notes
                    ) VALUES (
                        :crop_id, :harvest_date, :quantity, :unit, :area,
                        :yield_t_ha, :moisture, :quality, :loss,
                        :storage, :unit_price, :revenue, :operator, :notes
                    )
                    """
                ),
                {
                    "crop_id": crop_id,
                    "harvest_date": harvest_date,
                    "quantity": quantity,
                    "unit": str(form_data.get("unit", "t")).strip() or "t",
                    "area": area,
                    "yield_t_ha": round(quantity / area, 2),
                    "moisture": _to_float(form_data.get("moisture_percent")),
                    "quality": str(form_data.get("quality", "A")),
                    "loss": _to_float(form_data.get("loss_percent")),
                    "storage": str(
                        form_data.get("storage_location", "")
                    ).strip(),
                    "unit_price": price,
                    "revenue": round(quantity * price, 2),
                    "operator": str(form_data.get("operator", "")).strip(),
                    "notes": str(form_data.get("notes", "")).strip(),
                },
            )
            if close_crop:
                await asession.execute(
                    text(
                        """
                        UPDATE crop SET status = 'RECOLTEE', stage = 'RECOLTE',
                               progress_percent = 100, actual_harvest_date = :d
                        WHERE id = :cid
                        """
                    ),
                    {"d": harvest_date, "cid": crop_id},
                )
            await asession.commit()

        self.show_harvest_form = False
        self.harvest_error = ""
        self.form_key += 1
        await self._refresh_all()
        return rx.toast("Récolte enregistrée.", duration=4000)

    # ------------------------------------------------------------------
    # Mouvements de stock
    # ------------------------------------------------------------------

    @rx.event
    def open_movement_form(self, product_id: int = 0):
        form = dict(EMPTY_MOVEMENT_FORM)
        form["movement_date"] = datetime.date.today().isoformat()
        if product_id > 0:
            form["product_id"] = str(product_id)
        elif self.product_options:
            form["product_id"] = self.product_options[0]["value"]
        self.movement_form = form
        self.movement_error = ""
        self.form_key += 1
        self.show_movement_form = True

    @rx.event
    def close_movement_form(self):
        self.show_movement_form = False
        self.movement_error = ""

    def _validate_movement(self, data: dict) -> str:
        product_raw = str(data.get("product_id", "")).strip()
        quantity = _to_float(data.get("quantity"), -1.0)
        price = _to_float(data.get("unit_price"))
        movement_date = _to_date(data.get("movement_date"))
        kind = str(data.get("type", "ENTREE"))
        if not product_raw:
            return "Sélectionnez le produit concerné."
        if movement_date is None:
            return "La date du mouvement est obligatoire."
        if quantity < 0:
            return "La quantité ne peut pas être négative."
        if kind != "INVENTAIRE" and quantity <= 0:
            return "La quantité doit être strictement positive."
        if price < 0:
            return "Le prix unitaire ne peut pas être négatif."
        return ""

    @rx.event
    async def submit_movement(self, form_data: dict):
        error = self._validate_movement(form_data)
        if error:
            self.movement_error = error
            return
        product_id = int(str(form_data.get("product_id")).strip())
        kind = str(form_data.get("type", "ENTREE"))
        quantity = _to_float(form_data.get("quantity"))
        price = _to_float(form_data.get("unit_price"))
        movement_date = _to_date(form_data.get("movement_date"))

        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    INSERT INTO stock_movement (
                        product_id, type, quantity, unit_price, movement_date,
                        reference, intervention_id, notes
                    ) VALUES (
                        :pid, :type, :qty, :price, :mdate, :ref, NULL, :notes
                    )
                    """
                ),
                {
                    "pid": product_id,
                    "type": kind,
                    "qty": quantity,
                    "price": price,
                    "mdate": movement_date,
                    "ref": str(form_data.get("reference", "")).strip(),
                    "notes": str(form_data.get("notes", "")).strip(),
                },
            )
            if kind == "ENTREE":
                await asession.execute(
                    text(
                        """
                        UPDATE product
                        SET quantity_in_stock = COALESCE(quantity_in_stock, 0) + :qty
                        WHERE id = :pid
                        """
                    ),
                    {"qty": quantity, "pid": product_id},
                )
            elif kind == "INVENTAIRE":
                await asession.execute(
                    text(
                        "UPDATE product SET quantity_in_stock = :qty WHERE id = :pid"
                    ),
                    {"qty": quantity, "pid": product_id},
                )
            else:
                await asession.execute(
                    text(
                        """
                        UPDATE product SET quantity_in_stock =
                            CASE WHEN COALESCE(quantity_in_stock, 0) - :qty < 0 THEN 0
                                 ELSE COALESCE(quantity_in_stock, 0) - :qty END
                        WHERE id = :pid
                        """
                    ),
                    {"qty": quantity, "pid": product_id},
                )
            await asession.commit()

        self.show_movement_form = False
        self.movement_error = ""
        self.form_key += 1
        await self._fetch_kpis()
        await self._fetch_stock()
        return rx.toast("Mouvement de stock enregistré.", duration=4000)

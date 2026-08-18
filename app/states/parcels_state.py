"""État de l'espace parcelles & cultures.

Lectures et écritures en SQL brut via `rx.asession()`.
Gère la recherche, les filtres, la sélection, les formulaires de création /
modification des parcelles et cultures, ainsi que le suivi des stades.
"""

from __future__ import annotations

import datetime
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.catalog_link import (
    CATALOG_HIERARCHY_SQL,
    CATALOG_OPTION_SQL,
    materialize_catalog_varieties,
)
from app.catalog_reference import (
    cycle_label,
    cycle_tone,
    water_short_label,
    water_tone,
)
from app.date_utils import as_date, iso_or_empty
from app.seed import seed_dashboard_data
from app.seed_catalog import link_legacy_varieties, seed_catalog_data
from app.seed_corrections import seed_coherence_data
from app.states.dashboard_state import (
    CROP_STATUS_LABELS,
    HEALTH_LABELS,
    HEALTH_TONES,
    IRRIGATION_LABELS,
    MONTHS,
    PARCEL_STATUS_LABELS,
    SOIL_LABELS,
    STAGE_LABELS,
    WEEKDAYS_SHORT,
)

STAGE_SEQUENCE: list[str] = [
    "SEMIS",
    "LEVEE",
    "TALLAGE",
    "CROISSANCE",
    "FLORAISON",
    "FRUCTIFICATION",
    "MATURATION",
    "RECOLTE",
    "TERMINEE",
]

PARCEL_STATUS_KEYS: list[str] = [
    "EN_CULTURE",
    "JACHERE",
    "PREPARATION",
    "RECOLTEE",
    "INACTIVE",
]

SOIL_KEYS: list[str] = [
    "ARGILEUX",
    "LIMONEUX",
    "SABLEUX",
    "ARGILO_CALCAIRE",
    "LIMONO_SABLEUX",
    "HUMIFERE",
    "AUTRE",
]

IRRIGATION_KEYS: list[str] = [
    "AUCUNE",
    "ASPERSION",
    "GOUTTE_A_GOUTTE",
    "PIVOT",
    "GRAVITAIRE",
]

CROP_STATUS_KEYS: list[str] = [
    "PLANIFIEE",
    "EN_COURS",
    "RECOLTEE",
    "ABANDONNEE",
]

HEALTH_KEYS: list[str] = ["EXCELLENT", "BON", "MOYEN", "FAIBLE", "CRITIQUE"]


class Option(TypedDict):
    value: str
    label: str


class RailStep(TypedDict):
    label: str
    state: str


class ParcelRow(TypedDict):
    id: int
    name: str
    code: str
    area_ha: float
    status: str
    status_label: str
    soil_label: str
    irrigation_label: str
    locality: str
    is_organic: bool
    crop_count: int
    active_crop: str
    progress: int
    progress_pct: str
    color: str


class CropRow(TypedDict):
    id: int
    name: str
    species: str
    variety_id: str
    season: str
    stage: str
    stage_label: str
    status: str
    status_label: str
    health: str
    health_label: str
    health_tone: str
    area_ha: float
    progress: int
    progress_pct: str
    sowing_date: str
    harvest_date: str
    actual_harvest_date: str
    sowing_label: str
    harvest_label: str
    days_left: int
    seed_density: str
    expected_yield: str
    notes: str
    color: str
    rail: list[RailStep]
    has_catalog: bool
    catalog_path: str
    catalog_category: str
    catalog_category_color: str
    catalog_culture: str
    catalog_culture_icon: str
    catalog_species: str
    catalog_scientific: str
    catalog_variety: str
    catalog_maturity: str
    catalog_quality: str
    catalog_cycle_label: str
    catalog_cycle_tone: str
    catalog_water_label: str
    catalog_water_tone: str
    catalog_yield: str
    catalog_is_reference: bool


class StageLogRow(TypedDict):
    id: int
    crop_id: int
    crop_name: str
    stage: str
    stage_label: str
    observed_label: str
    observer: str
    comment: str


# Valeurs de repli quand une culture n'est pas reliée au référentiel structuré.
EMPTY_CATALOG: dict[str, str] = {
    "path": "",
    "category": "Hors référentiel",
    "category_color": "#64748b",
    "culture": "Culture non reliée",
    "culture_icon": "sprout",
    "species": "Espèce non précisée",
    "scientific": "",
    "variety": "Sans variété",
    "maturity": "",
    "quality": "Qualité non précisée",
    "cycle_label": "Cycle non précisé",
    "cycle_tone": "muted",
    "water_label": "Besoin en eau inconnu",
    "water_tone": "muted",
    "yield": "0.0",
    "reference": "0",
}

EMPTY_DETAIL: dict[str, str] = {
    "id": "0",
    "name": "Aucune parcelle sélectionnée",
    "code": "—",
    "area_ha": "0.0",
    "status_label": "—",
    "soil_label": "—",
    "irrigation_label": "—",
    "locality": "—",
    "coordinates": "—",
    "slope": "0.0",
    "ph": "0.0",
    "organic_matter": "0.0",
    "organic_label": "Conventionnel",
    "notes": "—",
    "crop_count": "0",
    "active_crops": "0",
    "area_active": "0.0",
    "avg_progress": "0",
}

EMPTY_PARCEL_FORM: dict[str, str] = {
    "name": "",
    "code": "",
    "area_ha": "",
    "soil_type": "LIMONEUX",
    "irrigation": "AUCUNE",
    "status": "PREPARATION",
    "locality": "",
    "latitude": "0",
    "longitude": "0",
    "map_x": "6",
    "map_y": "6",
    "map_w": "24",
    "map_h": "26",
    "slope_percent": "0",
    "ph": "7",
    "organic_matter_percent": "0",
    "is_organic": "0",
    "notes": "",
}


def _empty_crop_form() -> dict[str, str]:
    year = datetime.date.today().year
    return {
        "name": "",
        "variety_id": "",
        "season": str(year),
        "stage": "SEMIS",
        "status": "PLANIFIEE",
        "health": "BON",
        "area_ha": "",
        "sowing_date": "",
        "expected_harvest_date": "",
        "actual_harvest_date": "",
        "seed_density": "0",
        "expected_yield_t_ha": "0",
        "progress_percent": "0",
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
    text_value = str(raw).strip().replace(",", ".")
    if not text_value:
        return default
    try:
        return float(text_value)
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


def _build_rail(stage: str) -> list[RailStep]:
    steps: list[RailStep] = []
    current_index = (
        STAGE_SEQUENCE.index(stage) if stage in STAGE_SEQUENCE else 0
    )
    for index, key in enumerate(STAGE_SEQUENCE):
        if index < current_index:
            state = "done"
        elif index == current_index:
            state = "current"
        else:
            state = "todo"
        steps.append({"label": STAGE_LABELS.get(key, key), "state": state})
    return steps


def _options(keys: list[str], labels: dict[str, str]) -> list[Option]:
    return [{"value": key, "label": labels.get(key, key)} for key in keys]


class ParcelsState(rx.State):
    """Espace de gestion des parcelles, cultures et stades."""

    is_loading: bool = True
    today_label: str = ""

    search: str = ""
    status_filter: str = "TOUS"
    species_filter: str = "TOUTES"
    crop_status_filter: str = "TOUS"

    parcels: list[ParcelRow] = []
    selected_parcel_id: int = 0
    parcel_detail: dict[str, str] = EMPTY_DETAIL
    parcel_crops: list[CropRow] = []
    stage_logs: list[StageLogRow] = []

    species_options: list[str] = []
    variety_options: list[Option] = []
    crop_name_options: list[Option] = []

    # Référentiel structuré Catégorie → Culture → Espèce → Variété.
    catalog_totals: dict[str, int] = {
        "categories": 0,
        "cultures": 0,
        "species": 0,
        "varieties": 0,
        "linked": 0,
    }
    catalog_variety_count: int = 0
    # Index hiérarchique (variété historique -> fiche référentiel), non
    # sérialisé vers le frontend : il ne sert qu'à enrichir les fiches.
    _catalog_index: dict[str, dict[str, str]] = {}

    status_options: list[Option] = _options(
        PARCEL_STATUS_KEYS, PARCEL_STATUS_LABELS
    )
    soil_options: list[Option] = _options(SOIL_KEYS, SOIL_LABELS)
    irrigation_options: list[Option] = _options(
        IRRIGATION_KEYS, IRRIGATION_LABELS
    )
    crop_status_options: list[Option] = _options(
        CROP_STATUS_KEYS, CROP_STATUS_LABELS
    )
    stage_options: list[Option] = _options(STAGE_SEQUENCE, STAGE_LABELS)
    health_options: list[Option] = _options(HEALTH_KEYS, HEALTH_LABELS)

    show_parcel_form: bool = False
    parcel_form_mode: str = "create"
    editing_parcel_id: int = 0
    parcel_form: dict[str, str] = EMPTY_PARCEL_FORM

    show_crop_form: bool = False
    crop_form_mode: str = "create"
    editing_crop_id: int = 0
    crop_form: dict[str, str] = _empty_crop_form()

    form_error: str = ""
    stage_error: str = ""
    form_key: int = 0

    @rx.var
    def parcel_count(self) -> int:
        return len(self.parcels)

    @rx.var
    def filtered_area(self) -> float:
        return round(sum(p["area_ha"] for p in self.parcels), 1)

    @rx.var
    def organic_area(self) -> float:
        return round(
            sum(p["area_ha"] for p in self.parcels if p["is_organic"]), 1
        )

    @rx.var
    def crops_shown(self) -> int:
        return len(self.parcel_crops)

    @rx.var
    def parcel_form_title(self) -> str:
        if self.parcel_form_mode == "edit":
            return "Modifier la parcelle"
        return "Nouvelle parcelle"

    @rx.var
    def crop_form_title(self) -> str:
        if self.crop_form_mode == "edit":
            return "Modifier la culture"
        return "Nouvelle culture"

    @rx.var
    def has_selection(self) -> bool:
        return self.selected_parcel_id > 0

    @rx.var
    def catalog_linked_crops(self) -> list[CropRow]:
        """Cultures de la parcelle reliées au référentiel structuré."""
        return [crop for crop in self.parcel_crops if crop["has_catalog"]]

    @rx.var
    def catalog_unlinked_crops(self) -> list[CropRow]:
        return [crop for crop in self.parcel_crops if not crop["has_catalog"]]

    @rx.var
    def has_catalog_links(self) -> bool:
        return len(self.catalog_linked_crops) > 0

    @rx.var
    def has_catalog_gaps(self) -> bool:
        return len(self.catalog_unlinked_crops) > 0

    @rx.var
    def catalog_link_label(self) -> str:
        total = len(self.parcel_crops)
        linked = len(self.catalog_linked_crops)
        if total == 0:
            return "Aucune culture sur cette parcelle"
        return f"{linked} culture(s) reliée(s) sur {total}"

    @rx.var
    def catalog_coverage_label(self) -> str:
        return (
            f"{self.catalog_totals['categories']} catégories · "
            f"{self.catalog_totals['cultures']} cultures · "
            f"{self.catalog_totals['species']} espèces · "
            f"{self.catalog_totals['varieties']} variétés"
        )

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    async def _fetch_parcels(self) -> None:
        clauses = ["1=1"]
        params: dict[str, str] = {}
        query = self.search.strip().lower()
        if query:
            clauses.append(
                "(LOWER(p.name) LIKE :q OR LOWER(p.code) LIKE :q"
                " OR LOWER(p.locality) LIKE :q"
                " OR EXISTS (SELECT 1 FROM crop cs WHERE cs.parcel_id = p.id"
                " AND LOWER(cs.name) LIKE :q))"
            )
            params["q"] = f"%{query}%"
        if self.status_filter != "TOUS":
            clauses.append("p.status = :status")
            params["status"] = self.status_filter
        if self.species_filter != "TOUTES":
            clauses.append(
                "EXISTS (SELECT 1 FROM crop cf"
                " JOIN crop_variety vf ON vf.id = cf.variety_id"
                " WHERE cf.parcel_id = p.id AND vf.species = :species)"
            )
            params["species"] = self.species_filter
        where = " AND ".join(clauses)

        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT p.id, p.name, p.code, COALESCE(p.area_ha, 0),
                               p.status, p.soil_type, p.irrigation,
                               COALESCE(p.locality, ''), p.is_organic,
                               (SELECT COUNT(*) FROM crop cc
                                  WHERE cc.parcel_id = p.id),
                               (SELECT cc.name FROM crop cc
                                  WHERE cc.parcel_id = p.id
                                    AND cc.status = 'EN_COURS'
                                  ORDER BY cc.id LIMIT 1),
                               (SELECT COALESCE(cc.progress_percent, 0) FROM crop cc
                                  WHERE cc.parcel_id = p.id
                                    AND cc.status = 'EN_COURS'
                                  ORDER BY cc.id LIMIT 1),
                               (SELECT COALESCE(vv.color_hex, '#4ade80')
                                  FROM crop cc
                                  LEFT JOIN crop_variety vv ON vv.id = cc.variety_id
                                  WHERE cc.parcel_id = p.id
                                    AND cc.status = 'EN_COURS'
                                  ORDER BY cc.id LIMIT 1)
                        FROM parcel p
                        WHERE {where}
                        ORDER BY p.code, p.name
                        LIMIT 200
                        """
                    ),
                    params,
                )
            ).all()

        parcels: list[ParcelRow] = []
        for row in rows:
            status = str(row[4])
            progress = int(row[11] or 0)
            parcels.append(
                {
                    "id": int(row[0]),
                    "name": str(row[1]),
                    "code": str(row[2]) or "—",
                    "area_ha": float(row[3] or 0),
                    "status": status,
                    "status_label": PARCEL_STATUS_LABELS.get(status, status),
                    "soil_label": SOIL_LABELS.get(row[5], row[5]),
                    "irrigation_label": IRRIGATION_LABELS.get(row[6], row[6]),
                    "locality": str(row[7]) or "Localité non renseignée",
                    "is_organic": bool(row[8]),
                    "crop_count": int(row[9] or 0),
                    "active_crop": str(row[10])
                    if row[10]
                    else "Sans culture active",
                    "progress": progress,
                    "progress_pct": f"{progress}%",
                    "color": str(row[12]) if row[12] else "#4ade80",
                }
            )
        self.parcels = parcels

        ids = [p["id"] for p in parcels]
        if self.selected_parcel_id not in ids:
            self.selected_parcel_id = ids[0] if ids else 0

    async def _fetch_detail(self) -> None:
        parcel_id = self.selected_parcel_id
        if parcel_id == 0:
            self.parcel_detail = EMPTY_DETAIL
            self.parcel_crops = []
            self.stage_logs = []
            self.crop_name_options = []
            return

        crop_clause = ""
        crop_params: dict[str, str | int] = {"pid": parcel_id}
        if self.crop_status_filter != "TOUS":
            crop_clause = " AND c.status = :cstatus"
            crop_params["cstatus"] = self.crop_status_filter

        async with rx.asession() as asession:
            detail = (
                await asession.execute(
                    text(
                        """
                        SELECT p.id, p.name, p.code, COALESCE(p.area_ha, 0),
                               p.status, p.soil_type, p.irrigation,
                               COALESCE(p.locality, ''),
                               COALESCE(p.latitude, 0), COALESCE(p.longitude, 0),
                               COALESCE(p.slope_percent, 0), COALESCE(p.ph, 0),
                               COALESCE(p.organic_matter_percent, 0),
                               p.is_organic, COALESCE(p.notes, ''),
                               (SELECT COUNT(*) FROM crop cc WHERE cc.parcel_id = p.id),
                               (SELECT COUNT(*) FROM crop cc
                                  WHERE cc.parcel_id = p.id AND cc.status = 'EN_COURS'),
                               (SELECT COALESCE(SUM(cc.area_ha), 0) FROM crop cc
                                  WHERE cc.parcel_id = p.id AND cc.status = 'EN_COURS'),
                               (SELECT COALESCE(AVG(cc.progress_percent), 0) FROM crop cc
                                  WHERE cc.parcel_id = p.id AND cc.status = 'EN_COURS')
                        FROM parcel p
                        WHERE p.id = :pid
                        """
                    ),
                    {"pid": parcel_id},
                )
            ).first()

            crop_rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT c.id, c.name, COALESCE(v.species, ''),
                               c.variety_id, COALESCE(c.season, ''), c.stage,
                               c.status, c.health, COALESCE(c.area_ha, 0),
                               COALESCE(c.progress_percent, 0), c.sowing_date,
                               c.expected_harvest_date, c.actual_harvest_date,
                               COALESCE(c.seed_density, 0),
                               COALESCE(c.expected_yield_t_ha, 0),
                               COALESCE(c.notes, ''),
                               COALESCE(v.color_hex, '#4ade80')
                        FROM crop c
                        LEFT JOIN crop_variety v ON v.id = c.variety_id
                        WHERE c.parcel_id = :pid{crop_clause}
                        ORDER BY
                            CASE c.status WHEN 'EN_COURS' THEN 1
                                          WHEN 'PLANIFIEE' THEN 2
                                          ELSE 3 END,
                            c.expected_harvest_date
                        LIMIT 40
                        """
                    ),
                    crop_params,
                )
            ).all()

            log_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT l.id, l.crop_id, c.name, l.stage, l.observed_on,
                               COALESCE(l.observer, ''), COALESCE(l.comment, '')
                        FROM crop_stage_log l
                        JOIN crop c ON c.id = l.crop_id
                        WHERE c.parcel_id = :pid
                        ORDER BY l.observed_on DESC, l.id DESC
                        LIMIT 24
                        """
                    ),
                    {"pid": parcel_id},
                )
            ).all()

        if detail is None:
            self.parcel_detail = EMPTY_DETAIL
            self.parcel_crops = []
            self.stage_logs = []
            self.crop_name_options = []
            return

        status = str(detail[4])
        self.parcel_detail = {
            "id": str(int(detail[0])),
            "name": str(detail[1]),
            "code": str(detail[2]) or "—",
            "area_ha": f"{float(detail[3] or 0):.1f}",
            "status_label": PARCEL_STATUS_LABELS.get(status, status),
            "soil_label": SOIL_LABELS.get(detail[5], detail[5]),
            "irrigation_label": IRRIGATION_LABELS.get(detail[6], detail[6]),
            "locality": str(detail[7]) or "Localité non renseignée",
            "coordinates": f"{float(detail[8] or 0):.4f} / {float(detail[9] or 0):.4f}",
            "slope": f"{float(detail[10] or 0):.1f}",
            "ph": f"{float(detail[11] or 0):.1f}",
            "organic_matter": f"{float(detail[12] or 0):.1f}",
            "organic_label": "Conduite bio"
            if bool(detail[13])
            else "Conventionnel",
            "notes": str(detail[14]) or "Aucune note agronomique.",
            "crop_count": str(int(detail[15] or 0)),
            "active_crops": str(int(detail[16] or 0)),
            "area_active": f"{float(detail[17] or 0):.1f}",
            "avg_progress": f"{float(detail[18] or 0):.0f}",
        }

        today = datetime.date.today()
        crops: list[CropRow] = []
        for row in crop_rows:
            stage = str(row[5])
            crop_status = str(row[6])
            health = str(row[7])
            progress = int(row[9] or 0)
            harvest = as_date(row[11])
            variety_key = str(int(row[3])) if row[3] else ""
            info = self._catalog_index.get(variety_key, EMPTY_CATALOG)
            crops.append(
                {
                    "id": int(row[0]),
                    "name": str(row[1]),
                    "species": str(row[2]) or "Espèce non renseignée",
                    "variety_id": str(int(row[3])) if row[3] else "",
                    "season": str(row[4]) or "—",
                    "stage": stage,
                    "stage_label": STAGE_LABELS.get(stage, stage),
                    "status": crop_status,
                    "status_label": CROP_STATUS_LABELS.get(
                        crop_status, crop_status
                    ),
                    "health": health,
                    "health_label": HEALTH_LABELS.get(health, health),
                    "health_tone": HEALTH_TONES.get(health, "good"),
                    "area_ha": float(row[8] or 0),
                    "progress": progress,
                    "progress_pct": f"{progress}%",
                    "sowing_date": _iso(row[10]),
                    "harvest_date": _iso(harvest),
                    "actual_harvest_date": _iso(row[12]),
                    "sowing_label": _fmt_date(row[10]),
                    "harvest_label": _fmt_date(harvest),
                    "days_left": (harvest - today).days if harvest else 0,
                    "seed_density": f"{float(row[13] or 0):.0f}",
                    "expected_yield": f"{float(row[14] or 0):.1f}",
                    "notes": str(row[15]) or "Aucune observation consignée.",
                    "color": str(row[16]) if row[16] else "#4ade80",
                    "rail": _build_rail(stage),
                    "has_catalog": info["path"] != "",
                    "catalog_path": info["path"],
                    "catalog_category": info["category"],
                    "catalog_category_color": info["category_color"],
                    "catalog_culture": info["culture"],
                    "catalog_culture_icon": info["culture_icon"],
                    "catalog_species": info["species"],
                    "catalog_scientific": info["scientific"],
                    "catalog_variety": info["variety"],
                    "catalog_maturity": info["maturity"],
                    "catalog_quality": info["quality"],
                    "catalog_cycle_label": info["cycle_label"],
                    "catalog_cycle_tone": info["cycle_tone"],
                    "catalog_water_label": info["water_label"],
                    "catalog_water_tone": info["water_tone"],
                    "catalog_yield": info["yield"],
                    "catalog_is_reference": info["reference"] == "1",
                }
            )
        self.parcel_crops = crops
        self.crop_name_options = [
            {"value": str(c["id"]), "label": c["name"]} for c in crops
        ]

        self.stage_logs = [
            {
                "id": int(row[0]),
                "crop_id": int(row[1]),
                "crop_name": str(row[2]),
                "stage": str(row[3]),
                "stage_label": STAGE_LABELS.get(row[3], row[3]),
                "observed_label": _fmt_date(row[4]),
                "observer": str(row[5]) or "Opérateur non précisé",
                "comment": str(row[6]) or "—",
            }
            for row in log_rows
        ]

    async def _load_catalog_context(self) -> None:
        """Charge l'index hiérarchique du référentiel et ses volumes."""
        async with rx.asession() as asession:
            rows = (await asession.execute(text(CATALOG_HIERARCHY_SQL))).all()
            totals = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            (SELECT COUNT(*) FROM crop_category),
                            (SELECT COUNT(*) FROM crop_culture),
                            (SELECT COUNT(*) FROM crop_species),
                            (SELECT COUNT(*) FROM crop_catalog_variety),
                            (SELECT COUNT(*) FROM crop_catalog_variety
                               WHERE crop_variety_id IS NOT NULL)
                        """
                    )
                )
            ).first()

        index: dict[str, dict[str, str]] = {}
        for row in rows:
            category = str(row[1])
            culture = str(row[3])
            species = str(row[7])
            variety = str(row[9])
            cycle_key = str(row[5] or "")
            water_key = str(row[6] or "")
            index[str(int(row[0]))] = {
                "path": f"{category} → {culture} → {species} → {variety}",
                "category": category,
                "category_color": str(row[2]) or "#a3e635",
                "culture": culture,
                "culture_icon": str(row[4]) or "sprout",
                "species": species,
                "scientific": str(row[8]) or species,
                "variety": variety,
                "maturity": str(row[10]),
                "quality": str(row[11]) or "Qualité non précisée",
                "cycle_label": cycle_label(cycle_key),
                "cycle_tone": cycle_tone(cycle_key),
                "water_label": water_short_label(water_key),
                "water_tone": water_tone(water_key),
                "yield": f"{float(row[12] or 0):.1f}",
                "reference": "1" if bool(row[13]) else "0",
            }
        self._catalog_index = index
        self.catalog_totals = {
            "categories": int(totals[0] or 0) if totals else 0,
            "cultures": int(totals[1] or 0) if totals else 0,
            "species": int(totals[2] or 0) if totals else 0,
            "varieties": int(totals[3] or 0) if totals else 0,
            "linked": int(totals[4] or 0) if totals else 0,
        }

    async def _fetch_reference(self) -> None:
        """Options variétales issues du référentiel structuré."""
        async with rx.asession() as asession:
            catalog_rows = (
                await asession.execute(text(CATALOG_OPTION_SQL))
            ).all()
            legacy_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT id, name, species
                        FROM crop_variety
                        ORDER BY species, name
                        """
                    )
                )
            ).all()

        options: list[Option] = []
        seen_values: list[str] = []
        for row in catalog_rows:
            value = str(int(row[0]))
            if value in seen_values:
                continue
            seen_values.append(value)
            maturity = str(row[5])
            suffix = f" ({maturity})" if maturity else ""
            options.append(
                {
                    "value": value,
                    "label": (
                        f"{row[1]} · {row[2]} · {row[3]} — {row[4]}{suffix}"
                    ),
                }
            )
        if not options:
            # Repli : référentiel variétal historique seul.
            options = [
                {"value": str(int(row[0])), "label": f"{row[2]} · {row[1]}"}
                for row in legacy_rows
            ]
        self.variety_options = options
        self.catalog_variety_count = len(options)

        species_seen: list[str] = []
        for row in legacy_rows:
            species = str(row[2])
            if species and species not in species_seen:
                species_seen.append(species)
        self.species_options = species_seen

    @rx.event
    async def load_space(self):
        self.is_loading = True
        yield
        await seed_dashboard_data()
        # Analyses de sol et journaux de stades : amorçage idempotent.
        await seed_coherence_data()
        # Référentiel structuré : amorçage puis matérialisation des liens vers
        # le référentiel variétal historique (idempotent).
        await seed_catalog_data()
        await link_legacy_varieties()
        await materialize_catalog_varieties()
        await self._load_catalog_context()
        await self._fetch_reference()
        await self._fetch_parcels()
        await self._fetch_detail()
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
        await self._fetch_parcels()
        await self._fetch_detail()

    @rx.event
    async def set_status_filter(self, value: str):
        self.status_filter = value
        await self._fetch_parcels()
        await self._fetch_detail()

    @rx.event
    async def set_species_filter(self, value: str):
        self.species_filter = value
        await self._fetch_parcels()
        await self._fetch_detail()

    @rx.event
    async def set_crop_status_filter(self, value: str):
        self.crop_status_filter = value
        await self._fetch_detail()

    @rx.event
    async def reset_filters(self):
        self.search = ""
        self.status_filter = "TOUS"
        self.species_filter = "TOUTES"
        self.crop_status_filter = "TOUS"
        self.form_key += 1
        await self._fetch_parcels()
        await self._fetch_detail()

    @rx.event
    async def select_parcel(self, parcel_id: int):
        from app.states.phenology_state import PhenologyState

        self.selected_parcel_id = parcel_id
        await self._fetch_detail()
        yield PhenologyState.load_phenology

    # ------------------------------------------------------------------
    # Formulaire parcelle
    # ------------------------------------------------------------------

    @rx.event
    def open_parcel_create(self):
        self.parcel_form_mode = "create"
        self.editing_parcel_id = 0
        self.parcel_form = dict(EMPTY_PARCEL_FORM)
        self.form_error = ""
        self.form_key += 1
        self.show_parcel_form = True

    @rx.event
    async def open_parcel_edit(self):
        if self.selected_parcel_id == 0:
            return rx.toast("Sélectionnez d'abord une parcelle.")
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT name, code, COALESCE(area_ha, 0), soil_type,
                               irrigation, status, COALESCE(locality, ''),
                               COALESCE(latitude, 0), COALESCE(longitude, 0),
                               COALESCE(map_x, 0), COALESCE(map_y, 0),
                               COALESCE(map_w, 0), COALESCE(map_h, 0),
                               COALESCE(slope_percent, 0), COALESCE(ph, 0),
                               COALESCE(organic_matter_percent, 0),
                               is_organic, COALESCE(notes, '')
                        FROM parcel WHERE id = :pid
                        """
                    ),
                    {"pid": self.selected_parcel_id},
                )
            ).first()
        if row is None:
            return rx.toast("Parcelle introuvable.")
        self.parcel_form = {
            "name": str(row[0]),
            "code": str(row[1]),
            "area_ha": f"{float(row[2]):.2f}",
            "soil_type": str(row[3]),
            "irrigation": str(row[4]),
            "status": str(row[5]),
            "locality": str(row[6]),
            "latitude": f"{float(row[7]):.6f}",
            "longitude": f"{float(row[8]):.6f}",
            "map_x": f"{float(row[9]):.2f}",
            "map_y": f"{float(row[10]):.2f}",
            "map_w": f"{float(row[11]):.2f}",
            "map_h": f"{float(row[12]):.2f}",
            "slope_percent": f"{float(row[13]):.2f}",
            "ph": f"{float(row[14]):.2f}",
            "organic_matter_percent": f"{float(row[15]):.2f}",
            "is_organic": "1" if bool(row[16]) else "0",
            "notes": str(row[17]),
        }
        self.parcel_form_mode = "edit"
        self.editing_parcel_id = self.selected_parcel_id
        self.form_error = ""
        self.form_key += 1
        self.show_parcel_form = True

    @rx.event
    def close_parcel_form(self):
        self.show_parcel_form = False
        self.form_error = ""

    def _validate_parcel(self, data: dict) -> str:
        name = str(data.get("name", "")).strip()
        code = str(data.get("code", "")).strip()
        area = _to_float(data.get("area_ha"), -1.0)
        ph = _to_float(data.get("ph"), 7.0)
        if len(name) < 2:
            return "Le nom de la parcelle doit contenir au moins 2 caractères."
        if not code:
            return "Le code de parcelle est obligatoire (ex. P08)."
        if area <= 0:
            return "La surface doit être un nombre strictement positif."
        if area > 5000:
            return "La surface saisie semble irréaliste (max 5000 ha)."
        if ph < 3 or ph > 10:
            return "Le pH doit être compris entre 3 et 10."
        return ""

    @rx.event
    async def submit_parcel(self, form_data: dict):
        error = self._validate_parcel(form_data)
        if error:
            self.form_error = error
            return
        params = {
            "name": str(form_data.get("name", "")).strip(),
            "code": str(form_data.get("code", "")).strip().upper(),
            "area_ha": _to_float(form_data.get("area_ha")),
            "soil_type": str(form_data.get("soil_type", "LIMONEUX")),
            "irrigation": str(form_data.get("irrigation", "AUCUNE")),
            "status": str(form_data.get("status", "PREPARATION")),
            "locality": str(form_data.get("locality", "")).strip(),
            "latitude": _to_float(form_data.get("latitude")),
            "longitude": _to_float(form_data.get("longitude")),
            "map_x": min(92.0, max(0.0, _to_float(form_data.get("map_x"), 6))),
            "map_y": min(92.0, max(0.0, _to_float(form_data.get("map_y"), 6))),
            "map_w": min(96.0, max(6.0, _to_float(form_data.get("map_w"), 24))),
            "map_h": min(96.0, max(6.0, _to_float(form_data.get("map_h"), 26))),
            "slope_percent": _to_float(form_data.get("slope_percent")),
            "ph": _to_float(form_data.get("ph"), 7.0),
            "organic_matter_percent": _to_float(
                form_data.get("organic_matter_percent")
            ),
            "is_organic": bool(form_data.get("is_organic")),
            "notes": str(form_data.get("notes", "")).strip(),
        }

        async with rx.asession() as asession:
            if self.parcel_form_mode == "edit" and self.editing_parcel_id > 0:
                params["pid"] = self.editing_parcel_id
                await asession.execute(
                    text(
                        """
                        UPDATE parcel SET
                            name = :name, code = :code, area_ha = :area_ha,
                            soil_type = :soil_type, irrigation = :irrigation,
                            status = :status, locality = :locality,
                            latitude = :latitude, longitude = :longitude,
                            map_x = :map_x, map_y = :map_y,
                            map_w = :map_w, map_h = :map_h,
                            slope_percent = :slope_percent, ph = :ph,
                            organic_matter_percent = :organic_matter_percent,
                            is_organic = :is_organic, notes = :notes
                        WHERE id = :pid
                        """
                    ),
                    params,
                )
                new_id = self.editing_parcel_id
                message = "Parcelle mise à jour."
            else:
                new_id = (
                    await asession.execute(
                        text(
                            """
                            INSERT INTO parcel (
                                name, code, area_ha, soil_type, irrigation, status,
                                locality, latitude, longitude, map_x, map_y, map_w,
                                map_h, slope_percent, ph, organic_matter_percent,
                                is_organic, notes
                            ) VALUES (
                                :name, :code, :area_ha, :soil_type, :irrigation, :status,
                                :locality, :latitude, :longitude, :map_x, :map_y, :map_w,
                                :map_h, :slope_percent, :ph, :organic_matter_percent,
                                :is_organic, :notes
                            ) RETURNING id
                            """
                        ),
                        params,
                    )
                ).scalar()
                message = "Parcelle créée."
            await asession.commit()

        self.show_parcel_form = False
        self.form_error = ""
        self.selected_parcel_id = int(new_id or 0)
        await self._fetch_parcels()
        await self._fetch_detail()
        return rx.toast(message, duration=4000)

    # ------------------------------------------------------------------
    # Formulaire culture
    # ------------------------------------------------------------------

    @rx.event
    def open_crop_create(self):
        if self.selected_parcel_id == 0:
            return rx.toast("Sélectionnez d'abord une parcelle.")
        self.crop_form_mode = "create"
        self.editing_crop_id = 0
        self.crop_form = _empty_crop_form()
        self.form_error = ""
        self.form_key += 1
        self.show_crop_form = True

    @rx.event
    def open_crop_edit(self, crop_id: int):
        for crop in self.parcel_crops:
            if crop["id"] == crop_id:
                self.crop_form = {
                    "name": crop["name"],
                    "variety_id": crop["variety_id"],
                    "season": crop["season"],
                    "stage": crop["stage"],
                    "status": crop["status"],
                    "health": crop["health"],
                    "area_ha": f"{crop['area_ha']:.2f}",
                    "sowing_date": crop["sowing_date"],
                    "expected_harvest_date": crop["harvest_date"],
                    "actual_harvest_date": crop["actual_harvest_date"],
                    "seed_density": crop["seed_density"],
                    "expected_yield_t_ha": crop["expected_yield"],
                    "progress_percent": str(crop["progress"]),
                    "notes": crop["notes"],
                }
                self.crop_form_mode = "edit"
                self.editing_crop_id = crop_id
                self.form_error = ""
                self.form_key += 1
                self.show_crop_form = True
                return
        return rx.toast("Culture introuvable.")

    @rx.event
    def close_crop_form(self):
        self.show_crop_form = False
        self.form_error = ""

    def _validate_crop(self, data: dict) -> str:
        name = str(data.get("name", "")).strip()
        area = _to_float(data.get("area_ha"), -1.0)
        progress = _to_int(data.get("progress_percent"), -1)
        sowing = _to_date(data.get("sowing_date"))
        harvest = _to_date(data.get("expected_harvest_date"))
        parcel_area = _to_float(self.parcel_detail.get("area_ha"), 0.0)
        if len(name) < 2:
            return "Le nom de la culture doit contenir au moins 2 caractères."
        if area <= 0:
            return "La surface implantée doit être strictement positive."
        if parcel_area > 0 and area > parcel_area + 0.01:
            return (
                "La surface implantée dépasse la surface de la parcelle "
                f"({parcel_area:.1f} ha)."
            )
        if progress < 0 or progress > 100:
            return "L'avancement doit être compris entre 0 et 100 %."
        if sowing and harvest and harvest < sowing:
            return "La date de récolte doit suivre la date de semis."
        return ""

    @rx.event
    async def submit_crop(self, form_data: dict):
        if self.selected_parcel_id == 0:
            self.form_error = "Aucune parcelle sélectionnée."
            return
        error = self._validate_crop(form_data)
        if error:
            self.form_error = error
            return

        variety_raw = str(form_data.get("variety_id", "")).strip()
        stage = str(form_data.get("stage", "SEMIS"))
        params: dict[str, str | int | float | None | datetime.date] = {
            "parcel_id": self.selected_parcel_id,
            "variety_id": int(variety_raw) if variety_raw else None,
            "name": str(form_data.get("name", "")).strip(),
            "season": str(form_data.get("season", "")).strip(),
            "stage": stage,
            "status": str(form_data.get("status", "PLANIFIEE")),
            "health": str(form_data.get("health", "BON")),
            "area_ha": _to_float(form_data.get("area_ha")),
            "sowing_date": _to_date(form_data.get("sowing_date")),
            "expected_harvest_date": _to_date(
                form_data.get("expected_harvest_date")
            ),
            "actual_harvest_date": _to_date(
                form_data.get("actual_harvest_date")
            ),
            "seed_density": _to_float(form_data.get("seed_density")),
            "expected_yield_t_ha": _to_float(
                form_data.get("expected_yield_t_ha")
            ),
            "progress_percent": _to_int(form_data.get("progress_percent")),
            "notes": str(form_data.get("notes", "")).strip(),
        }
        today = datetime.date.today()

        async with rx.asession() as asession:
            if self.crop_form_mode == "edit" and self.editing_crop_id > 0:
                previous = (
                    await asession.execute(
                        text("SELECT stage FROM crop WHERE id = :cid"),
                        {"cid": self.editing_crop_id},
                    )
                ).scalar()
                params["cid"] = self.editing_crop_id
                await asession.execute(
                    text(
                        """
                        UPDATE crop SET
                            variety_id = :variety_id, name = :name, season = :season,
                            stage = :stage, status = :status, health = :health,
                            area_ha = :area_ha, sowing_date = :sowing_date,
                            expected_harvest_date = :expected_harvest_date,
                            actual_harvest_date = :actual_harvest_date,
                            seed_density = :seed_density,
                            expected_yield_t_ha = :expected_yield_t_ha,
                            progress_percent = :progress_percent, notes = :notes
                        WHERE id = :cid
                        """
                    ),
                    params,
                )
                if str(previous) != stage:
                    await asession.execute(
                        text(
                            """
                            INSERT INTO crop_stage_log (
                                crop_id, stage, observed_on, observer, comment
                            ) VALUES (
                                :crop_id, :stage, :observed_on, :observer, :comment
                            )
                            """
                        ),
                        {
                            "crop_id": self.editing_crop_id,
                            "stage": stage,
                            "observed_on": today,
                            "observer": "Saisie fiche culture",
                            "comment": "Changement de stade enregistré depuis la fiche.",
                        },
                    )
                message = "Culture mise à jour."
            else:
                new_id = (
                    await asession.execute(
                        text(
                            """
                            INSERT INTO crop (
                                parcel_id, variety_id, name, season, stage, status,
                                health, area_ha, sowing_date, expected_harvest_date,
                                actual_harvest_date, seed_density,
                                expected_yield_t_ha, progress_percent, notes
                            ) VALUES (
                                :parcel_id, :variety_id, :name, :season, :stage, :status,
                                :health, :area_ha, :sowing_date, :expected_harvest_date,
                                :actual_harvest_date, :seed_density,
                                :expected_yield_t_ha, :progress_percent, :notes
                            ) RETURNING id
                            """
                        ),
                        params,
                    )
                ).scalar()
                await asession.execute(
                    text(
                        """
                        INSERT INTO crop_stage_log (
                            crop_id, stage, observed_on, observer, comment
                        ) VALUES (
                            :crop_id, :stage, :observed_on, :observer, :comment
                        )
                        """
                    ),
                    {
                        "crop_id": int(new_id or 0),
                        "stage": stage,
                        "observed_on": today,
                        "observer": "Saisie fiche culture",
                        "comment": "Implantation enregistrée.",
                    },
                )
                message = "Culture créée."
            await asession.commit()

        self.show_crop_form = False
        self.form_error = ""
        await self._fetch_parcels()
        await self._fetch_detail()
        return rx.toast(message, duration=4000)

    # ------------------------------------------------------------------
    # Suivi des stades
    # ------------------------------------------------------------------

    @rx.event
    async def submit_stage_log(self, form_data: dict):
        self.stage_error = ""
        crop_raw = str(form_data.get("crop_id", "")).strip()
        if not crop_raw:
            self.stage_error = "Choisissez la culture observée."
            return
        observed = _to_date(form_data.get("observed_on"))
        if observed is None:
            self.stage_error = "La date d'observation est obligatoire."
            return
        if observed > datetime.date.today() + datetime.timedelta(days=1):
            self.stage_error = "La date d'observation ne peut pas être future."
            return
        stage = str(form_data.get("stage", "SEMIS"))
        observer = str(form_data.get("observer", "")).strip()
        if len(observer) < 2:
            self.stage_error = "Indiquez le nom de l'observateur."
            return

        crop_id = int(crop_raw)
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    INSERT INTO crop_stage_log (
                        crop_id, stage, observed_on, observer, comment
                    ) VALUES (
                        :crop_id, :stage, :observed_on, :observer, :comment
                    )
                    """
                ),
                {
                    "crop_id": crop_id,
                    "stage": stage,
                    "observed_on": observed,
                    "observer": observer,
                    "comment": str(form_data.get("comment", "")).strip(),
                },
            )
            await asession.execute(
                text("UPDATE crop SET stage = :stage WHERE id = :cid"),
                {"stage": stage, "cid": crop_id},
            )
            await asession.commit()

        self.form_key += 1
        await self._fetch_parcels()
        await self._fetch_detail()
        return rx.toast("Observation de stade enregistrée.", duration=4000)

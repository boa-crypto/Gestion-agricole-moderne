"""État de consultation et de pilotage du référentiel cultures.

Lecture seule sur les tables `crop_category`, `crop_culture`, `crop_species` et
`crop_catalog_variety`, en SQL brut via `rx.asession()`. L'amorçage idempotent
existant (`seed_catalog_data`, `link_legacy_varieties`) garantit la présence du
référentiel avant toute lecture.

Ce module porte :

* les indicateurs de couverture (catégories, cultures, espèces, variétés,
  liens vers le référentiel variétal historique, cultures pérennes) ;
* le radar agronomique / herbier : une position calculée par catégorie, en
  Python, pour le centerpiece visuel de la page ;
* la navigation par catégories, la recherche plein texte et les filtres de
  cycle et de besoin en eau ;
* la fiche détaillée culture → espèces → variétés ;
* les usages par module consommateur (parcelles, campagnes, itinéraires,
  irrigation, fertilisation, traitements, récoltes, statistiques) ;
* le focus Dattes / palmier dattier.
"""

from __future__ import annotations

import math
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.catalog_reference import (
    CATALOG_CONSUMERS,
    CYCLE_KEYS,
    DATE_CATEGORY_KEY,
    DATE_CONSISTENCIES,
    WATER_KEYS,
    cycle_icon,
    cycle_label,
    cycle_tone,
    cycle_weeks,
    fertilisation_profile,
    irrigation_profile,
    tolerance_label,
    tolerance_tone,
    water_label,
    water_short_label,
    water_tone,
)
from app.seed import seed_dashboard_data
from app.seed_catalog import link_legacy_varieties, seed_catalog_data

CULTURE_LIMIT: int = 240


# ---------------------------------------------------------------------------
# Structures exposées au frontend
# ---------------------------------------------------------------------------


class CoverageMetric(TypedDict):
    key: str
    label: str
    value: int
    unit: str
    icon: str


class CategoryNode(TypedDict):
    key: str
    name: str
    tagline: str
    icon: str
    color: str
    accent: str
    cultures: int
    species: int
    varieties: int
    perennial: int
    linked: int
    share_pct: float
    angle: float
    spoke_pct: float
    x_pct: float
    y_pct: float
    dot_size: float


class CultureRow(TypedDict):
    key: str
    name: str
    common_name: str
    family: str
    category_key: str
    category_name: str
    category_color: str
    cycle_key: str
    cycle_label: str
    cycle_tone: str
    cycle_icon: str
    water_key: str
    water_label: str
    water_short: str
    water_tone: str
    icon: str
    color: str
    usage: str
    description: str
    species_count: int
    variety_count: int
    yield_max: float
    cycle_range: str


class VarietyRow(TypedDict):
    key: str
    name: str
    local_name: str
    maturity: str
    cycle_days: int
    yield_t_ha: float
    quality: str
    color: str
    sowing: str
    harvest: str
    drought_label: str
    drought_tone: str
    is_reference: bool
    is_linked: bool
    consistency: str
    notes: str


class SpeciesCard(TypedDict):
    key: str
    name: str
    scientific_name: str
    family: str
    cycle_weeks: str
    cycle_days_label: str
    sowing: str
    harvest: str
    water_mm: float
    root_cm: float
    base_temp: float
    ph_label: str
    salinity_label: str
    salinity_tone: str
    nitrogen: float
    phosphorus: float
    potassium: float
    density: str
    pests: str
    diseases: str
    notes: str
    variety_count: int
    varieties: list[VarietyRow]


class ConsumerHint(TypedDict):
    key: str
    label: str
    route: str
    icon: str
    usage: str
    detail: str


class ChipOption(TypedDict):
    value: str
    label: str
    icon: str


EMPTY_CULTURE: CultureRow = {
    "key": "",
    "name": "",
    "common_name": "",
    "family": "",
    "category_key": "",
    "category_name": "",
    "category_color": "#a3e635",
    "cycle_key": "",
    "cycle_label": "",
    "cycle_tone": "muted",
    "cycle_icon": "sprout",
    "water_key": "",
    "water_label": "",
    "water_short": "",
    "water_tone": "muted",
    "icon": "sprout",
    "color": "#a3e635",
    "usage": "",
    "description": "",
    "species_count": 0,
    "variety_count": 0,
    "yield_max": 0.0,
    "cycle_range": "—",
}

EMPTY_PALM: dict[str, str] = {
    "name": "",
    "scientific_name": "",
    "sowing": "",
    "harvest": "",
    "water_mm": "0",
    "npk": "0 / 0 / 0",
    "density": "",
    "pests": "",
    "diseases": "",
    "notes": "",
    "salinity_label": "",
    "salinity_tone": "muted",
    "culture_key": "",
}


# ---------------------------------------------------------------------------
# Utilitaires purs
# ---------------------------------------------------------------------------


def _text(value: object) -> str:
    return str(value or "").strip()


def _consistency(quality: str) -> str:
    low = quality.lower()
    if "demi-molle" in low:
        return DATE_CONSISTENCIES["DEMI_MOLLE"]
    if "molle" in low:
        return DATE_CONSISTENCIES["MOLLE"]
    if "sèche" in low or "seche" in low:
        return DATE_CONSISTENCIES["SECHE"]
    return ""


def _variety_row(row: object) -> VarietyRow:
    quality = _text(row[7])
    return {
        "key": _text(row[1]),
        "name": _text(row[2]),
        "local_name": _text(row[3]),
        "maturity": _text(row[4]) or "Précocité non précisée",
        "cycle_days": int(row[5] or 0),
        "yield_t_ha": float(row[6] or 0),
        "quality": quality or "Qualité non précisée",
        "color": _text(row[8]) or "#a3e635",
        "sowing": _text(row[9]) or "—",
        "harvest": _text(row[10]) or "—",
        "drought_label": tolerance_label(_text(row[11])),
        "drought_tone": tolerance_tone(_text(row[11])),
        "is_reference": bool(row[12]),
        "is_linked": bool(row[14]),
        "consistency": _consistency(quality),
        "notes": _text(row[13]),
    }


_VARIETY_SELECT: str = """
    SELECT v.species_id, v.key, v.name, v.local_name, v.maturity_group,
           v.cycle_days, v.expected_yield_t_ha, v.quality_grade, v.color_hex,
           v.sowing_window, v.harvest_window, v.drought_tolerance,
           v.is_reference, v.notes,
           CASE WHEN v.crop_variety_id IS NOT NULL THEN 1 ELSE 0 END
    FROM crop_catalog_variety v
    JOIN crop_species s ON s.id = v.species_id
    JOIN crop_culture cu ON cu.id = s.culture_id
"""


class CatalogBrowserState(rx.State):
    """Consultation complète du référentiel Catégorie → Culture → Espèce → Variété."""

    is_loading: bool = True
    is_filtering: bool = False

    # --- Couverture ----------------------------------------------------
    totals: dict[str, int] = {
        "categories": 0,
        "cultures": 0,
        "species": 0,
        "varieties": 0,
        "linked": 0,
        "perennial": 0,
        "date_varieties": 0,
        "reference": 0,
    }
    coverage: list[CoverageMetric] = []
    nodes: list[CategoryNode] = []

    # --- Navigation et filtres ----------------------------------------
    search_term: str = ""
    category_filter: str = "TOUS"
    cycle_filter: str = "TOUS"
    water_filter: str = "TOUS"
    form_key: int = 0

    cycle_chips: list[ChipOption] = [
        {"value": "TOUS", "label": "Tous les cycles", "icon": "infinity"},
    ] + [
        {"value": key, "label": cycle_label(key), "icon": cycle_icon(key)}
        for key in CYCLE_KEYS
    ]

    water_chips: list[ChipOption] = [
        {"value": "TOUS", "label": "Tous les besoins", "icon": "droplets"},
    ] + [
        {"value": key, "label": water_short_label(key), "icon": "droplet"}
        for key in WATER_KEYS
    ]

    # --- Résultats -----------------------------------------------------
    cultures: list[CultureRow] = []
    selected_culture: str = ""
    culture: CultureRow = EMPTY_CULTURE
    species: list[SpeciesCard] = []
    consumers: list[ConsumerHint] = []

    # --- Focus dattes --------------------------------------------------
    palm: dict[str, str] = EMPTY_PALM
    date_varieties: list[VarietyRow] = []

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def has_cultures(self) -> bool:
        return len(self.cultures) > 0

    @rx.var
    def has_selection(self) -> bool:
        return self.selected_culture != ""

    @rx.var
    def coverage_label(self) -> str:
        return (
            f"{self.totals['categories']} catégories · "
            f"{self.totals['cultures']} cultures · "
            f"{self.totals['species']} espèces · "
            f"{self.totals['varieties']} variétés"
        )

    @rx.var
    def result_label(self) -> str:
        count = len(self.cultures)
        if count == 0:
            return "Aucune culture ne correspond"
        if count == 1:
            return "1 culture correspondante"
        return f"{count} cultures correspondantes"

    @rx.var
    def has_filters(self) -> bool:
        return bool(
            self.search_term.strip()
            or self.category_filter != "TOUS"
            or self.cycle_filter != "TOUS"
            or self.water_filter != "TOUS"
        )

    @rx.var
    def scope_label(self) -> str:
        if self.category_filter == "TOUS":
            return "Toutes les familles cultivées"
        for node in self.nodes:
            if node["key"] == self.category_filter:
                return node["name"]
        return "Périmètre filtré"

    @rx.var
    def has_date_focus(self) -> bool:
        return len(self.date_varieties) > 0

    # ------------------------------------------------------------------
    # Lecture des données
    # ------------------------------------------------------------------

    async def _load_coverage(self) -> None:
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            (SELECT COUNT(*) FROM crop_category),
                            (SELECT COUNT(*) FROM crop_culture),
                            (SELECT COUNT(*) FROM crop_species),
                            (SELECT COUNT(*) FROM crop_catalog_variety),
                            (SELECT COUNT(*) FROM crop_catalog_variety
                               WHERE crop_variety_id IS NOT NULL),
                            (SELECT COUNT(*) FROM crop_culture
                               WHERE cycle = 'PERENNE'),
                            (SELECT COUNT(*) FROM crop_catalog_variety v
                               JOIN crop_species s ON s.id = v.species_id
                               JOIN crop_culture c ON c.id = s.culture_id
                               JOIN crop_category cat ON cat.id = c.category_id
                               WHERE cat.key = :date_key),
                            (SELECT COUNT(*) FROM crop_catalog_variety
                               WHERE is_reference <> 0)
                        """
                    ),
                    {"date_key": DATE_CATEGORY_KEY},
                )
            ).first()

            node_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT cat.key, cat.name, cat.tagline, cat.icon,
                               cat.color_hex, cat.accent_hex,
                               COUNT(DISTINCT cu.id),
                               COUNT(DISTINCT s.id),
                               COUNT(DISTINCT v.id),
                               COUNT(DISTINCT CASE WHEN cu.cycle = 'PERENNE'
                                                   THEN cu.id END),
                               COUNT(DISTINCT CASE WHEN v.crop_variety_id
                                                        IS NOT NULL
                                                   THEN v.id END)
                        FROM crop_category cat
                        LEFT JOIN crop_culture cu ON cu.category_id = cat.id
                        LEFT JOIN crop_species s ON s.culture_id = cu.id
                        LEFT JOIN crop_catalog_variety v
                               ON v.species_id = s.id
                        GROUP BY cat.id, cat.key, cat.name, cat.tagline,
                                 cat.icon, cat.color_hex, cat.accent_hex,
                                 cat.position
                        ORDER BY cat.position, cat.key
                        """
                    )
                )
            ).all()

        self.totals = {
            "categories": int(row[0] or 0) if row else 0,
            "cultures": int(row[1] or 0) if row else 0,
            "species": int(row[2] or 0) if row else 0,
            "varieties": int(row[3] or 0) if row else 0,
            "linked": int(row[4] or 0) if row else 0,
            "perennial": int(row[5] or 0) if row else 0,
            "date_varieties": int(row[6] or 0) if row else 0,
            "reference": int(row[7] or 0) if row else 0,
        }

        self.coverage = [
            {
                "key": "categories",
                "label": "Catégories",
                "value": self.totals["categories"],
                "unit": "familles cultivées",
                "icon": "layers",
            },
            {
                "key": "cultures",
                "label": "Cultures",
                "value": self.totals["cultures"],
                "unit": "conduites décrites",
                "icon": "sprout",
            },
            {
                "key": "species",
                "label": "Espèces",
                "value": self.totals["species"],
                "unit": "repères agronomiques",
                "icon": "leaf",
            },
            {
                "key": "varieties",
                "label": "Variétés",
                "value": self.totals["varieties"],
                "unit": "fiches variétales",
                "icon": "flower-2",
            },
            {
                "key": "linked",
                "label": "Variétés reliées",
                "value": self.totals["linked"],
                "unit": "au référentiel historique",
                "icon": "link",
            },
            {
                "key": "perennial",
                "label": "Cultures pérennes",
                "value": self.totals["perennial"],
                "unit": "vergers, palmeraies, prairies",
                "icon": "trees",
            },
        ]

        nodes: list[CategoryNode] = []
        for db_row in node_rows:
            nodes.append(
                {
                    "key": _text(db_row[0]),
                    "name": _text(db_row[1]),
                    "tagline": _text(db_row[2]),
                    "icon": _text(db_row[3]) or "sprout",
                    "color": _text(db_row[4]) or "#a3e635",
                    "accent": _text(db_row[5]) or "#fbbf24",
                    "cultures": int(db_row[6] or 0),
                    "species": int(db_row[7] or 0),
                    "varieties": int(db_row[8] or 0),
                    "perennial": int(db_row[9] or 0),
                    "linked": int(db_row[10] or 0),
                    "share_pct": 0.0,
                    "angle": 0.0,
                    "spoke_pct": 0.0,
                    "x_pct": 50.0,
                    "y_pct": 50.0,
                    "dot_size": 12.0,
                }
            )

        # Radar agronomique : une branche d'herbier par catégorie, longueur
        # proportionnelle au nombre de variétés décrites.
        peak = max((node["varieties"] for node in nodes), default=0) or 1
        count = len(nodes) or 1
        for index, node in enumerate(nodes):
            angle = -90.0 + 360.0 * index / count
            radians = math.radians(angle)
            share = node["varieties"] / peak
            radius = 15.0 + 29.0 * share
            node["share_pct"] = round(share * 100.0, 1)
            node["angle"] = round(angle, 2)
            node["spoke_pct"] = round(radius, 2)
            node["x_pct"] = round(50.0 + radius * math.cos(radians), 2)
            node["y_pct"] = round(50.0 + radius * math.sin(radians), 2)
            node["dot_size"] = round(9.0 + 13.0 * share, 1)
        self.nodes = nodes

    async def _load_dates(self) -> None:
        async with rx.asession() as asession:
            palm = (
                await asession.execute(
                    text(
                        """
                        SELECT s.name, s.scientific_name, s.sowing_window,
                               s.harvest_window, s.water_requirement_mm,
                               s.nitrogen_need_kg_ha, s.phosphorus_need_kg_ha,
                               s.potassium_need_kg_ha, s.default_density,
                               s.main_pests, s.main_diseases, s.notes,
                               s.salinity_tolerance, cu.key
                        FROM crop_species s
                        JOIN crop_culture cu ON cu.id = s.culture_id
                        JOIN crop_category cat ON cat.id = cu.category_id
                        WHERE cat.key = :date_key
                        ORDER BY s.position, s.id
                        LIMIT 1
                        """
                    ),
                    {"date_key": DATE_CATEGORY_KEY},
                )
            ).first()

            variety_rows = (
                await asession.execute(
                    text(
                        _VARIETY_SELECT
                        + """
                        JOIN crop_category cat ON cat.id = cu.category_id
                        WHERE cat.key = :date_key
                        ORDER BY v.position, v.id
                        """
                    ),
                    {"date_key": DATE_CATEGORY_KEY},
                )
            ).all()

        if palm is None:
            self.palm = EMPTY_PALM
            self.date_varieties = []
            return

        self.palm = {
            "name": _text(palm[0]),
            "scientific_name": _text(palm[1]),
            "sowing": _text(palm[2]) or "—",
            "harvest": _text(palm[3]) or "—",
            "water_mm": f"{float(palm[4] or 0):.0f}",
            "npk": (
                f"{float(palm[5] or 0):.0f} / {float(palm[6] or 0):.0f} / "
                f"{float(palm[7] or 0):.0f}"
            ),
            "density": _text(palm[8]) or "—",
            "pests": _text(palm[9]) or "—",
            "diseases": _text(palm[10]) or "—",
            "notes": _text(palm[11]),
            "salinity_label": tolerance_label(_text(palm[12])),
            "salinity_tone": tolerance_tone(_text(palm[12])),
            "culture_key": _text(palm[13]),
        }
        self.date_varieties = [_variety_row(row) for row in variety_rows]

    async def _refresh_cultures(self) -> None:
        term = self.search_term.strip().lower()
        params: dict[str, str] = {}
        clauses = ["1=1"]
        if term:
            params["q"] = f"%{term}%"
            clauses.append(
                """(
                    LOWER(cu.name) LIKE :q
                    OR LOWER(COALESCE(cu.common_name, '')) LIKE :q
                    OR LOWER(COALESCE(cu.botanical_family, '')) LIKE :q
                    OR LOWER(COALESCE(cu.usage, '')) LIKE :q
                    OR LOWER(COALESCE(cu.description, '')) LIKE :q
                    OR LOWER(cat.name) LIKE :q
                    OR EXISTS (
                        SELECT 1 FROM crop_species sq
                        WHERE sq.culture_id = cu.id
                          AND (LOWER(sq.name) LIKE :q
                               OR LOWER(COALESCE(sq.scientific_name, ''))
                                  LIKE :q
                               OR LOWER(COALESCE(sq.main_pests, '')) LIKE :q
                               OR LOWER(COALESCE(sq.main_diseases, ''))
                                  LIKE :q)
                    )
                    OR EXISTS (
                        SELECT 1 FROM crop_catalog_variety vq
                        JOIN crop_species sv ON sv.id = vq.species_id
                        WHERE sv.culture_id = cu.id
                          AND (LOWER(vq.name) LIKE :q
                               OR LOWER(COALESCE(vq.local_name, '')) LIKE :q
                               OR LOWER(COALESCE(vq.quality_grade, ''))
                                  LIKE :q)
                    )
                )"""
            )
        if self.category_filter != "TOUS":
            params["category"] = self.category_filter
            clauses.append("cat.key = :category")
        if self.cycle_filter != "TOUS":
            params["cycle"] = self.cycle_filter
            clauses.append("cu.cycle = :cycle")
        if self.water_filter != "TOUS":
            params["water"] = self.water_filter
            clauses.append("cu.water_need = :water")
        where = " AND ".join(clauses)

        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT cu.key, cu.name, cu.common_name,
                               cu.botanical_family, cu.cycle, cu.water_need,
                               cu.icon, cu.color_hex, cu.usage, cu.description,
                               cat.key, cat.name, cat.color_hex,
                               (SELECT COUNT(*) FROM crop_species s
                                  WHERE s.culture_id = cu.id),
                               (SELECT COUNT(*) FROM crop_catalog_variety v
                                  JOIN crop_species s2 ON s2.id = v.species_id
                                  WHERE s2.culture_id = cu.id),
                               (SELECT COALESCE(MAX(v2.expected_yield_t_ha), 0)
                                  FROM crop_catalog_variety v2
                                  JOIN crop_species s3 ON s3.id = v2.species_id
                                  WHERE s3.culture_id = cu.id),
                               (SELECT COALESCE(MIN(s4.cycle_days_min), 0)
                                  FROM crop_species s4
                                  WHERE s4.culture_id = cu.id),
                               (SELECT COALESCE(MAX(s5.cycle_days_max), 0)
                                  FROM crop_species s5
                                  WHERE s5.culture_id = cu.id)
                        FROM crop_culture cu
                        JOIN crop_category cat ON cat.id = cu.category_id
                        WHERE {where}
                        ORDER BY cat.position, cu.position, cu.name
                        LIMIT {CULTURE_LIMIT}
                        """
                    ),
                    params,
                )
            ).all()

        cultures: list[CultureRow] = []
        for row in rows:
            cycle_key = _text(row[4])
            water_key = _text(row[5])
            cultures.append(
                {
                    "key": _text(row[0]),
                    "name": _text(row[1]),
                    "common_name": _text(row[2]) or _text(row[1]),
                    "family": _text(row[3]) or "Famille non précisée",
                    "category_key": _text(row[10]),
                    "category_name": _text(row[11]),
                    "category_color": _text(row[12]) or "#a3e635",
                    "cycle_key": cycle_key,
                    "cycle_label": cycle_label(cycle_key),
                    "cycle_tone": cycle_tone(cycle_key),
                    "cycle_icon": cycle_icon(cycle_key),
                    "water_key": water_key,
                    "water_label": water_label(water_key),
                    "water_short": water_short_label(water_key),
                    "water_tone": water_tone(water_key),
                    "icon": _text(row[6]) or "sprout",
                    "color": _text(row[7]) or "#4ade80",
                    "usage": _text(row[8]) or "Débouché non précisé",
                    "description": _text(row[9]),
                    "species_count": int(row[13] or 0),
                    "variety_count": int(row[14] or 0),
                    "yield_max": float(row[15] or 0),
                    "cycle_range": cycle_weeks(
                        int(row[16] or 0), int(row[17] or 0)
                    ),
                }
            )
        self.cultures = cultures

        keys = [item["key"] for item in cultures]
        if self.selected_culture not in keys:
            self.selected_culture = keys[0] if keys else ""
        await self._load_detail()

    async def _load_detail(self) -> None:
        key = self.selected_culture
        if not key:
            self.culture = EMPTY_CULTURE
            self.species = []
            self.consumers = []
            return

        current = EMPTY_CULTURE
        for item in self.cultures:
            if item["key"] == key:
                current = item

        async with rx.asession() as asession:
            species_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT s.id, s.key, s.name, s.scientific_name,
                               s.botanical_family, s.cycle_days_min,
                               s.cycle_days_max, s.sowing_window,
                               s.harvest_window, s.water_requirement_mm,
                               s.rooting_depth_cm, s.base_temperature_c,
                               s.optimal_ph_min, s.optimal_ph_max,
                               s.salinity_tolerance, s.nitrogen_need_kg_ha,
                               s.phosphorus_need_kg_ha,
                               s.potassium_need_kg_ha, s.default_density,
                               s.main_pests, s.main_diseases, s.notes
                        FROM crop_species s
                        JOIN crop_culture cu ON cu.id = s.culture_id
                        WHERE cu.key = :key
                        ORDER BY s.position, s.id
                        """
                    ),
                    {"key": key},
                )
            ).all()

            variety_rows = (
                await asession.execute(
                    text(
                        _VARIETY_SELECT
                        + """
                        WHERE cu.key = :key
                        ORDER BY s.position, v.position, v.id
                        """
                    ),
                    {"key": key},
                )
            ).all()

        grouped: dict[int, list[VarietyRow]] = {}
        for row in variety_rows:
            grouped.setdefault(int(row[0]), []).append(_variety_row(row))

        species: list[SpeciesCard] = []
        for row in species_rows:
            species_id = int(row[0])
            varieties = grouped.get(species_id, [])
            days_min = int(row[5] or 0)
            days_max = int(row[6] or 0)
            species.append(
                {
                    "key": _text(row[1]),
                    "name": _text(row[2]),
                    "scientific_name": _text(row[3]) or "—",
                    "family": _text(row[4]) or current["family"],
                    "cycle_weeks": cycle_weeks(days_min, days_max),
                    "cycle_days_label": f"{days_min} à {days_max} jours",
                    "sowing": _text(row[7]) or "—",
                    "harvest": _text(row[8]) or "—",
                    "water_mm": float(row[9] or 0),
                    "root_cm": float(row[10] or 0),
                    "base_temp": float(row[11] or 0),
                    "ph_label": (
                        f"{float(row[12] or 0):.1f} – {float(row[13] or 0):.1f}"
                    ),
                    "salinity_label": tolerance_label(_text(row[14])),
                    "salinity_tone": tolerance_tone(_text(row[14])),
                    "nitrogen": float(row[15] or 0),
                    "phosphorus": float(row[16] or 0),
                    "potassium": float(row[17] or 0),
                    "density": _text(row[18]) or "—",
                    "pests": _text(row[19]) or "Aucun ravageur dominant noté.",
                    "diseases": _text(row[20])
                    or "Aucune maladie dominante notée.",
                    "notes": _text(row[21]),
                    "variety_count": len(varieties),
                    "varieties": varieties,
                }
            )

        self.culture = current
        self.species = species
        self.consumers = self._build_consumers(current, species)

    def _build_consumers(
        self, culture: CultureRow, species: list[SpeciesCard]
    ) -> list[ConsumerHint]:
        """Traduit la fiche en consignes pour chaque module consommateur."""
        if not culture["key"]:
            return []

        first = species[0] if species else None
        water = irrigation_profile(culture["water_key"])
        fumure = fertilisation_profile(culture["category_key"])
        pests = first["pests"] if first is not None else "—"
        diseases = first["diseases"] if first is not None else "—"
        sowing = first["sowing"] if first is not None else "—"
        harvest = first["harvest"] if first is not None else "—"
        npk = (
            f"{first['nitrogen']:.0f} N / {first['phosphorus']:.0f} P / "
            f"{first['potassium']:.0f} K kg/ha"
            if first is not None
            else "—"
        )
        best = ""
        for item in species:
            for variety in item["varieties"]:
                if not best or variety["yield_t_ha"] >= culture["yield_max"]:
                    best = f"{variety['name']} — {variety['quality']}"

        details: dict[str, str] = {
            "parcelles": (
                f"{culture['species_count']} espèce(s) et "
                f"{culture['variety_count']} variété(s) sélectionnables sur "
                f"l'îlot, famille {culture['family']}."
            ),
            "campagnes": (
                f"Fenêtre de semis / plantation : {sowing}. "
                f"Fenêtre de récolte : {harvest}. Cycle {culture['cycle_range']}."
            ),
            "itineraires": (
                f"{culture['cycle_label']} : dérouler les chantiers types sur "
                f"{culture['cycle_range']} de végétation."
            ),
            "irrigation": (
                f"Déclenchement à {water['trigger_kpa']:.0f} kPa, dose de "
                f"{water['dose_mm']:.0f} mm tous les "
                f"{water['interval_days']} jours (Kc {water['kc_mid']:.2f}). "
                f"{water['comment']}"
            ),
            "fertilisation": (
                f"{npk} en {fumure['splits']} apport(s). {fumure['strategy']}"
            ),
            "traitements": (
                f"Ravageurs dominants : {pests}. Maladies dominantes : "
                f"{diseases}."
            ),
            "recoltes": (
                f"Rendement de référence jusqu'à {culture['yield_max']:.1f} t/ha."
                + (f" Variété repère : {best}." if best else "")
            ),
            "statistiques": (
                f"Agrégation par catégorie « {culture['category_name']} » : "
                f"surfaces, rendements et coûts comparables entre îlots."
            ),
        }

        hints: list[ConsumerHint] = []
        for consumer in CATALOG_CONSUMERS:
            hints.append(
                {
                    "key": consumer["key"],
                    "label": consumer["label"],
                    "route": consumer["route"],
                    "icon": consumer["icon"],
                    "usage": consumer["usage"],
                    "detail": details.get(consumer["key"], consumer["usage"]),
                }
            )
        return hints

    # ------------------------------------------------------------------
    # Événements
    # ------------------------------------------------------------------

    @rx.event
    async def load_referentiel(self):
        """Amorce le référentiel si besoin puis charge tout l'écran."""
        self.is_loading = True
        yield

        await seed_dashboard_data()
        await seed_catalog_data()
        await link_legacy_varieties()

        await self._load_coverage()
        await self._load_dates()
        await self._refresh_cultures()
        self.is_loading = False

    @rx.event
    async def set_search(self, value: str):
        self.search_term = value
        self.is_filtering = True
        yield
        await self._refresh_cultures()
        self.is_filtering = False

    @rx.event
    async def select_category(self, value: str):
        self.category_filter = value
        self.is_filtering = True
        yield
        await self._refresh_cultures()
        self.is_filtering = False

    @rx.event
    async def set_cycle(self, value: str):
        self.cycle_filter = value
        self.is_filtering = True
        yield
        await self._refresh_cultures()
        self.is_filtering = False

    @rx.event
    async def set_water(self, value: str):
        self.water_filter = value
        self.is_filtering = True
        yield
        await self._refresh_cultures()
        self.is_filtering = False

    @rx.event
    async def select_culture(self, value: str):
        self.selected_culture = value
        self.is_filtering = True
        yield
        await self._load_detail()
        self.is_filtering = False

    @rx.event
    async def focus_dates(self):
        """Ouvre la fiche du palmier dattier depuis le focus Dattes."""
        self.category_filter = DATE_CATEGORY_KEY
        self.search_term = ""
        self.cycle_filter = "TOUS"
        self.water_filter = "TOUS"
        self.selected_culture = self.palm.get("culture_key", "")
        self.form_key += 1
        self.is_filtering = True
        yield
        await self._refresh_cultures()
        self.is_filtering = False

    @rx.event
    async def reset_filters(self):
        self.search_term = ""
        self.category_filter = "TOUS"
        self.cycle_filter = "TOUS"
        self.water_filter = "TOUS"
        self.form_key += 1
        self.is_filtering = True
        yield
        await self._refresh_cultures()
        self.is_filtering = False

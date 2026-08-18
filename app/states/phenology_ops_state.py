"""État de pilotage opérationnel du suivi phénologique.

Alimente les lectures contextuelles de stade dans les modules existants :
cartographie, audit, rapports et écrans de travaux. Aucune écriture, aucune
création automatique d'intervention, aucune recommandation de produit
phytosanitaire non sourcée.
"""

from __future__ import annotations

import datetime
from typing import TypedDict

import reflex as rx

from app.phenology_ops import (
    AlertRow,
    PlannedRow,
    RecoRow,
    StageContextRow,
    contextual_alerts,
    phenology_counters,
    planned_vs_actual,
    stage_context_rows,
    stage_filter_options,
    stage_incoherences,
    stage_recommendations_for,
)
from app.seed_phenology import seed_phenology_data
from app.states.dashboard_state import MONTHS, WEEKDAYS_SHORT


class Option(TypedDict):
    value: str
    label: str


class IncoherenceRow(TypedDict):
    id: str
    parcel_code: str
    crop_name: str
    stage_name: str
    date_label: str
    reason: str


EMPTY_COUNTERS: dict[str, int] = {
    "profiles": 0,
    "active_profiles": 0,
    "stages": 0,
    "active_stages": 0,
    "critical_stages": 0,
    "recommendations": 0,
    "advisory_recommendations": 0,
    "observations": 0,
    "changes": 0,
    "media": 0,
    "cultures": 0,
    "cultures_with_profile": 0,
    "cultures_total": 0,
    "cultures_without_profile": 0,
    "profiles_without_stages": 0,
    "crops_without_observation": 0,
    "invalid_observations": 0,
    "prescriptive_recommendations": 0,
}


EMPTY_KPIS: dict[str, int] = {
    "profiles": 0,
    "stages": 0,
    "observations": 0,
    "critical_stages": 0,
    "recommendations": 0,
    "alerts": 0,
    "reports": 0,
    "cultures": 0,
    "changes": 0,
    "crops_tracked": 0,
    "incoherences": 0,
}


class PhenologyOpsState(rx.State):
    """Lectures phénologiques transverses aux modules opérationnels."""

    is_loading: bool = True
    today_label: str = ""

    stage_filter: str = "TOUS"
    domain_filter: str = "TOUS"
    search: str = ""

    # Compteurs stables consommés par l'UI, l'audit et les tests.
    kpis: dict[str, int] = EMPTY_KPIS

    rows: list[StageContextRow] = []
    alerts: list[AlertRow] = []
    recommendations: list[RecoRow] = []
    planned: list[PlannedRow] = []
    incoherences: list[IncoherenceRow] = []
    counters: dict[str, int] = EMPTY_COUNTERS
    stage_options: list[Option] = []

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def stage_rows(self) -> list[StageContextRow]:
        """Alias stable des lignes de stade affichées."""
        return self.rows

    @rx.var
    def recommendation_rows(self) -> list[RecoRow]:
        """Recommandations indicatives, filtrées par domaine si demandé."""
        if self.domain_filter == "TOUS":
            return self.recommendations
        return [
            item
            for item in self.recommendations
            if item["domain"] == self.domain_filter
        ]

    @rx.var
    def report_rows(self) -> list[PlannedRow]:
        """Alias stable de la comparaison prévu / réel."""
        return self.planned

    @rx.var
    def row_count(self) -> int:
        return len(self.rows)

    @rx.var
    def alert_count(self) -> int:
        return len(self.alerts)

    @rx.var
    def observed_count(self) -> int:
        return len([row for row in self.rows if row["has_observation"]])

    @rx.var
    def missing_observation_count(self) -> int:
        return len([row for row in self.rows if not row["has_observation"]])

    @rx.var
    def critical_count(self) -> int:
        return len([row for row in self.rows if row["is_critical"]])

    @rx.var
    def harvest_soon_count(self) -> int:
        return len(
            [row for row in self.rows if 0 < row["days_to_harvest"] <= 21]
        )

    @rx.var
    def average_progress(self) -> float:
        observed = [
            row["progress"] for row in self.rows if row["has_observation"]
        ]
        if not observed:
            return 0.0
        return round(sum(observed) / len(observed), 1)

    @rx.var
    def late_count(self) -> int:
        return len([item for item in self.planned if item["delta_days"] > 3])

    @rx.var
    def early_count(self) -> int:
        return len([item for item in self.planned if item["delta_days"] < -3])

    @rx.var
    def has_planned_data(self) -> bool:
        return len(self.planned) > 0

    @rx.var
    def incoherence_count(self) -> int:
        return len(self.incoherences)

    @rx.var
    def irrigation_recommendations(self) -> list[RecoRow]:
        return [r for r in self.recommendations if r["domain"] == "IRRIGATION"]

    @rx.var
    def fertilisation_recommendations(self) -> list[RecoRow]:
        return [
            r for r in self.recommendations if r["domain"] == "FERTILISATION"
        ]

    @rx.var
    def treatment_recommendations(self) -> list[RecoRow]:
        return [
            r
            for r in self.recommendations
            if r["domain"] in ("TRAITEMENT", "SURVEILLANCE")
        ]

    @rx.var
    def harvest_recommendations(self) -> list[RecoRow]:
        return [
            r
            for r in self.recommendations
            if r["domain"] in ("RECOLTE", "TRAVAIL_DU_SOL", "AUTRE")
        ]

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    async def _refresh(self) -> None:
        rows = await stage_context_rows(self.stage_filter, self.search)
        self.rows = rows
        self.alerts = contextual_alerts(rows)
        self.recommendations = await stage_recommendations_for(
            [row["stage_id"] for row in rows]
        )

    @rx.event
    async def load_operational(self):
        self.is_loading = True
        yield
        await seed_phenology_data()
        self.stage_options = [
            {"value": item["value"], "label": item["label"]}
            for item in await stage_filter_options()
        ]
        await self._refresh()
        self.planned = await planned_vs_actual()
        self.counters = await phenology_counters()
        self.incoherences = [
            {
                "id": item["id"],
                "parcel_code": item["parcel_code"],
                "crop_name": item["crop_name"],
                "stage_name": item["stage_name"],
                "date_label": item["date_label"],
                "reason": item["reason"],
            }
            for item in await stage_incoherences()
        ]
        self._sync_kpis()
        today = datetime.date.today()
        self.today_label = (
            f"{WEEKDAYS_SHORT[today.weekday()]}. {today.day} "
            f"{MONTHS[today.month - 1]} {today.year}"
        )
        self.is_loading = False

    def _sync_kpis(self) -> None:
        """Recalcule le dictionnaire stable de compteurs phénologiques."""
        counters = self.counters or EMPTY_KPIS
        self.kpis = {
            "profiles": int(counters.get("active_profiles", 0))
            or int(counters.get("profiles", 0)),
            "stages": int(counters.get("active_stages", 0))
            or int(counters.get("stages", 0)),
            "observations": int(counters.get("observations", 0)),
            "critical_stages": int(counters.get("critical_stages", 0)),
            "recommendations": int(counters.get("recommendations", 0)),
            "alerts": len(self.alerts),
            "reports": len(self.planned),
            "cultures": int(counters.get("cultures", 0)),
            "changes": int(counters.get("changes", 0)),
            "crops_tracked": len(self.rows),
            "incoherences": len(self.incoherences),
        }

    @rx.event
    async def set_stage_filter(self, value: str):
        self.stage_filter = value
        await self._refresh()
        self._sync_kpis()

    @rx.event
    def set_domain_filter(self, value: str):
        self.domain_filter = value

    @rx.event
    async def set_search(self, value: str):
        self.search = value
        await self._refresh()
        self._sync_kpis()

    @rx.event
    async def reset_filters(self):
        self.stage_filter = "TOUS"
        self.domain_filter = "TOUS"
        self.search = ""
        await self._refresh()
        self._sync_kpis()

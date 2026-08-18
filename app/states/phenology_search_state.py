"""État d'indexation phénologique de la recherche globale.

Indexe profils, stades, observations, recommandations indicatives et
changements de stade, en SQL brut, sans écriture.
"""

from __future__ import annotations

from typing import TypedDict

import reflex as rx

from app.phenology_ops import SearchHit, search_phenology
from app.seed_phenology import phenology_totals, seed_phenology_data


class SearchSection(TypedDict):
    kind: str
    kind_label: str
    icon: str
    count: int
    hits: list[SearchHit]


KINDS: list[tuple[str, str, str]] = [
    ("profil", "Profils phénologiques", "git-branch"),
    ("stade", "Stades du référentiel", "sprout"),
    ("observation", "Observations de stade", "clipboard-pen"),
    ("recommandation", "Opérations associées (indicatives)", "list-checks"),
    ("changement", "Changements de stade", "history"),
]

# Toutes les clés lues par l'UI et les contrôles sont pré-amorcées : un accès
# à une clé absente casserait le rendu au premier paint.
EMPTY_TOTALS: dict[str, int] = {
    "hits": 0,
    "profiles": 0,
    "stages": 0,
    "observations": 0,
    "recommendations": 0,
    "changes": 0,
    "media": 0,
    "cultures": 0,
    "sections": 0,
}


class PhenologySearchState(rx.State):
    """Balayage transversal du suivi phénologique."""

    is_loading: bool = True
    term: str = ""
    kind_filter: str = "TOUS"
    hits: list[SearchHit] = []
    # Compteurs stables du périmètre indexé (jamais partiellement peuplés).
    totals: dict[str, int] = EMPTY_TOTALS
    # Volumes du référentiel, rafraîchis au chargement uniquement.
    _reference_totals: dict[str, int] = {}

    @rx.var
    def total_hits(self) -> int:
        return len(self.hits)

    @rx.var
    def sections(self) -> list[SearchSection]:
        sections: list[SearchSection] = []
        for kind, label, icon in KINDS:
            if self.kind_filter != "TOUS" and self.kind_filter != kind:
                continue
            hits = [hit for hit in self.hits if hit["kind"] == kind]
            if not hits:
                continue
            sections.append(
                {
                    "kind": kind,
                    "kind_label": label,
                    "icon": icon,
                    "count": len(hits),
                    "hits": hits,
                }
            )
        return sections

    async def _run(self) -> None:
        self.hits = await search_phenology(self.term)
        self._sync_totals()

    def _sync_totals(self) -> None:
        """Recalcule le dictionnaire stable de compteurs."""
        totals = dict(EMPTY_TOTALS)
        totals.update(self._reference_totals)
        totals["hits"] = len(self.hits)
        kinds = {
            hit["kind"]
            for hit in self.hits
            if self.kind_filter in ("TOUS", hit["kind"])
        }
        totals["sections"] = len(kinds)
        self.totals = totals

    @rx.event
    async def load_index(self):
        self.is_loading = True
        yield
        await seed_phenology_data()
        reference = await phenology_totals()
        self._reference_totals = {
            key: int(value)
            for key, value in reference.items()
            if key in EMPTY_TOTALS
        }
        await self._run()
        self.is_loading = False

    @rx.event
    async def set_term(self, value: str):
        self.term = value
        await self._run()

    @rx.event
    async def set_query(self, value: str):
        """Alias stable de `set_term` (API attendue par les contrôles)."""
        self.term = value
        await self._run()

    @rx.event
    def set_kind_filter(self, value: str):
        self.kind_filter = value
        self._sync_totals()

    @rx.event
    async def reset_index(self):
        self.term = ""
        self.kind_filter = "TOUS"
        await self._run()

"""État de chargement du référentiel Catégorie → Culture → Espèce → Variété.

Ce module ne fait que garantir la présence du référentiel (amorçage idempotent)
et exposer ses volumes consolidés, afin que les écrans à venir (consultation du
référentiel, parcelles, campagnes, itinéraires, irrigation, fertilisation,
traitements, récoltes, statistiques) puissent s'appuyer sur des données réelles.

Toutes les lectures se font en SQL brut via `rx.asession()`.
"""

from __future__ import annotations

import reflex as rx
from sqlalchemy import text

from app.catalog_reference import (
    CATALOG_METRICS,
    DATE_CATEGORY_KEY,
    MetricSpec,
)
from app.seed_catalog import link_legacy_varieties, seed_catalog_data


class CatalogState(rx.State):
    """Volumes du référentiel cultures, prêts pour les statistiques."""

    is_loading: bool = True

    totals: dict[str, int] = {
        "categories": 0,
        "cultures": 0,
        "species": 0,
        "varieties": 0,
        "linked": 0,
        "perennial": 0,
        "date_varieties": 0,
    }

    metrics: list[MetricSpec] = CATALOG_METRICS

    @rx.var
    def is_ready(self) -> bool:
        """Le référentiel est exploitable dès qu'il porte des variétés."""
        return self.totals["varieties"] > 0

    @rx.var
    def coverage_label(self) -> str:
        return (
            f"{self.totals['categories']} catégories · "
            f"{self.totals['cultures']} cultures · "
            f"{self.totals['species']} espèces · "
            f"{self.totals['varieties']} variétés"
        )

    @rx.event
    async def load_catalog(self):
        """Amorce le référentiel si nécessaire puis recharge ses volumes."""
        self.is_loading = True
        yield

        await seed_catalog_data()
        # Rattrapage des correspondances avec le référentiel variétal existant.
        await link_legacy_varieties()

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
                               WHERE cat.key = :date_key)
                        """
                    ),
                    {"date_key": DATE_CATEGORY_KEY},
                )
            ).first()

        self.totals = {
            "categories": int(row[0] or 0) if row else 0,
            "cultures": int(row[1] or 0) if row else 0,
            "species": int(row[2] or 0) if row else 0,
            "varieties": int(row[3] or 0) if row else 0,
            "linked": int(row[4] or 0) if row else 0,
            "perennial": int(row[5] or 0) if row else 0,
            "date_varieties": int(row[6] or 0) if row else 0,
        }
        self.is_loading = False

"""Passerelle entre le référentiel structuré et le référentiel variétal historique.

Le référentiel `Catégorie → Culture → Espèce → Variété` (tables `crop_category`,
`crop_culture`, `crop_species`, `crop_catalog_variety`) décrit l'herbier de
l'exploitation. Les fiches culturales (`crop.variety_id`) pointent, elles, vers
le référentiel variétal historique `crop_variety`.

Ce module matérialise la correspondance manquante, de façon **idempotente** et
en SQL brut via `rx.asession()` :

* toute variété du référentiel déjà présente dans `crop_variety` (même espèce,
  même nom) est simplement reliée ;
* toute variété absente est créée dans `crop_variety` avec ses constantes
  agronomiques (cycle, rendement visé, fenêtres, couleur, notes) puis reliée.

Résultat : les parcelles peuvent proposer, à la création comme à l'édition d'une
culture, **toutes** les variétés du référentiel structuré, et l'audit peut
contrôler la cohérence des liens.

Aucune migration protégée n'est touchée : les tables locales existent déjà.
"""

from __future__ import annotations

import logging

import reflex as rx
from sqlalchemy import text

from app.database import init_catalog_tables, init_local_database

__all__ = [
    "CATALOG_HIERARCHY_SQL",
    "CATALOG_OPTION_SQL",
    "catalog_totals",
    "materialize_catalog_varieties",
]

_materialized: bool = False


# Hiérarchie complète d'une variété reliée : réutilisée par les parcelles.
CATALOG_HIERARCHY_SQL: str = """
    SELECT v.crop_variety_id, cat.name, cat.color_hex, cu.name, cu.icon,
           cu.cycle, cu.water_need, s.name,
           COALESCE(s.scientific_name, ''), v.name,
           COALESCE(v.maturity_group, ''), COALESCE(v.quality_grade, ''),
           COALESCE(v.expected_yield_t_ha, 0), v.is_reference
    FROM crop_catalog_variety v
    JOIN crop_species s ON s.id = v.species_id
    JOIN crop_culture cu ON cu.id = s.culture_id
    JOIN crop_category cat ON cat.id = cu.category_id
    WHERE v.crop_variety_id IS NOT NULL
    ORDER BY cat.position, cu.position, s.position, v.position
"""

# Options de sélection « Catégorie · Culture · Espèce — Variété ».
CATALOG_OPTION_SQL: str = """
    SELECT v.crop_variety_id, cat.name, cu.name, s.name, v.name,
           COALESCE(v.maturity_group, '')
    FROM crop_catalog_variety v
    JOIN crop_species s ON s.id = v.species_id
    JOIN crop_culture cu ON cu.id = s.culture_id
    JOIN crop_category cat ON cat.id = cu.category_id
    WHERE v.crop_variety_id IS NOT NULL
    ORDER BY cat.position, cu.position, s.position, v.position
"""

_TOTALS_SQL: str = """
    SELECT
        (SELECT COUNT(*) FROM crop_category),
        (SELECT COUNT(*) FROM crop_culture),
        (SELECT COUNT(*) FROM crop_species),
        (SELECT COUNT(*) FROM crop_catalog_variety),
        (SELECT COUNT(*) FROM crop_catalog_variety
           WHERE crop_variety_id IS NOT NULL)
"""

_PENDING_SQL: str = """
    SELECT v.id, v.name, COALESCE(v.cycle_days, 0),
           COALESCE(v.expected_yield_t_ha, 0),
           COALESCE(v.sowing_window, ''), COALESCE(v.harvest_window, ''),
           COALESCE(v.color_hex, '#a3e635'), COALESCE(v.quality_grade, ''),
           COALESCE(v.notes, ''), s.name,
           COALESCE(s.botanical_family, ''), COALESCE(cu.icon, 'sprout'),
           COALESCE(s.cycle_days_max, 0)
    FROM crop_catalog_variety v
    JOIN crop_species s ON s.id = v.species_id
    JOIN crop_culture cu ON cu.id = s.culture_id
    WHERE v.crop_variety_id IS NULL
    ORDER BY s.position, v.position, v.id
"""

_LINK_BY_NAME_SQL: str = """
    UPDATE crop_catalog_variety
    SET crop_variety_id = (
        SELECT l.id FROM crop_variety l
        WHERE l.name = crop_catalog_variety.name
        LIMIT 1
    )
    WHERE crop_variety_id IS NULL
      AND EXISTS (
        SELECT 1 FROM crop_variety l
        WHERE l.name = crop_catalog_variety.name
      )
"""


async def catalog_totals() -> dict[str, int]:
    """Volumes consolidés du référentiel (lecture seule)."""
    init_local_database()
    init_catalog_tables()
    async with rx.asession() as asession:
        row = (await asession.execute(text(_TOTALS_SQL))).first()
    return {
        "categories": int(row[0] or 0) if row else 0,
        "cultures": int(row[1] or 0) if row else 0,
        "species": int(row[2] or 0) if row else 0,
        "varieties": int(row[3] or 0) if row else 0,
        "linked": int(row[4] or 0) if row else 0,
    }


async def materialize_catalog_varieties() -> int:
    """Rend chaque variété du référentiel sélectionnable sur une parcelle.

    Retourne le nombre de variétés historiques créées. L'opération est
    idempotente : rejouée, elle ne crée rien et ne duplique aucun lien.
    """
    global _materialized
    if _materialized:
        return 0

    init_local_database()
    init_catalog_tables()

    created = 0
    try:
        async with rx.asession() as asession:
            # 1. Correspondance immédiate par nom exact.
            await asession.execute(text(_LINK_BY_NAME_SQL))

            pending = (await asession.execute(text(_PENDING_SQL))).all()
            existing_rows = (
                await asession.execute(
                    text("SELECT id, species, name FROM crop_variety")
                )
            ).all()
            existing: dict[tuple[str, str], int] = {
                (str(row[1]), str(row[2])): int(row[0]) for row in existing_rows
            }

            for row in pending:
                species_name = str(row[9])
                variety_name = str(row[1])
                key = (species_name, variety_name)
                legacy_id = existing.get(key)
                if legacy_id is None:
                    cycle_days = int(row[2] or 0) or int(row[12] or 0)
                    legacy_id = int(
                        (
                            await asession.execute(
                                text(
                                    """
                                    INSERT INTO crop_variety (
                                        name, species, family, cycle_days,
                                        expected_yield_t_ha, sowing_window,
                                        harvest_window, color_hex, icon, notes
                                    ) VALUES (
                                        :name, :species, :family, :cycle_days,
                                        :yield_t_ha, :sowing, :harvest,
                                        :color, :icon, :notes
                                    ) RETURNING id
                                    """
                                ),
                                {
                                    "name": variety_name,
                                    "species": species_name,
                                    "family": str(row[10]),
                                    "cycle_days": cycle_days,
                                    "yield_t_ha": float(row[3] or 0),
                                    "sowing": str(row[4]),
                                    "harvest": str(row[5]),
                                    "color": str(row[6]),
                                    "icon": str(row[11]),
                                    "notes": str(row[8])
                                    or str(row[7])
                                    or "Variété issue du référentiel agronomique.",
                                },
                            )
                        ).scalar()
                        or 0
                    )
                    existing[key] = legacy_id
                    created += 1

                await asession.execute(
                    text(
                        """
                        UPDATE crop_catalog_variety
                        SET crop_variety_id = :legacy_id
                        WHERE id = :vid AND crop_variety_id IS NULL
                        """
                    ),
                    {"legacy_id": legacy_id, "vid": int(row[0])},
                )

            await asession.commit()
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
        return created

    _materialized = True
    return created

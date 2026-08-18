"""Amorçage idempotent du suivi phénologique multicultures.

Insère, en SQL brut via `rx.asession()`, les profils phénologiques et leurs
stades ordonnés décrits dans `app/phenology_reference.py`, ainsi que les
recommandations non prescriptives associées. Chaque culture possède son propre
cycle : il n'existe aucune liste globale unique de stades.

L'amorçage :

* réutilise le référentiel structuré existant (`crop_culture`, `crop_species`,
  `crop_catalog_variety`) pour rattacher chaque profil ;
* est **idempotent** : rejoué, il ne crée ni ne duplique rien ;
* ne supprime jamais de données existantes et ne touche à aucune migration
  protégée (les tables locales sont créées par `init_phenology_tables()`).
"""

from __future__ import annotations

import logging

import reflex as rx
from sqlalchemy import text

from app.database import init_local_database, init_phenology_tables
from app.phenology_reference import (
    CONFIDENCE_INDICATIVE,
    PHENOLOGY_PROFILES,
    SYSTEM_LOCAL,
)
from app.seed_catalog import seed_catalog_data

__all__ = ["phenology_totals", "seed_phenology_data"]

_seeded: bool = False

_TOTALS_SQL: str = """
    SELECT
        (SELECT COUNT(*) FROM crop_phenology_profile),
        (SELECT COUNT(*) FROM crop_phenology_stage),
        (SELECT COUNT(*) FROM crop_stage_recommendation),
        (SELECT COUNT(*) FROM crop_stage_observation),
        (SELECT COUNT(*) FROM crop_stage_change),
        (SELECT COUNT(*) FROM crop_stage_media),
        (SELECT COUNT(DISTINCT culture_id) FROM crop_phenology_profile)
"""


async def phenology_totals() -> dict[str, int]:
    """Volumes consolidés du suivi phénologique (lecture seule)."""
    init_local_database()
    init_phenology_tables()
    async with rx.asession() as asession:
        row = (await asession.execute(text(_TOTALS_SQL))).first()
    return {
        "profiles": int(row[0] or 0) if row else 0,
        "stages": int(row[1] or 0) if row else 0,
        "recommendations": int(row[2] or 0) if row else 0,
        "observations": int(row[3] or 0) if row else 0,
        "changes": int(row[4] or 0) if row else 0,
        "media": int(row[5] or 0) if row else 0,
        "cultures": int(row[6] or 0) if row else 0,
    }


async def _keys(asession, table: str) -> dict[str, int]:
    rows = (await asession.execute(text(f"SELECT key, id FROM {table}"))).all()
    return {str(row[0]): int(row[1]) for row in rows}


async def seed_phenology_data() -> None:
    """Amorce profils, stades et recommandations phénologiques (idempotent)."""
    global _seeded
    if _seeded:
        return

    init_local_database()
    init_phenology_tables()
    # Le référentiel Catégorie → Culture → Espèce → Variété porte les clés
    # auxquelles les profils se rattachent.
    await seed_catalog_data()

    try:
        async with rx.asession() as asession:
            cultures = await _keys(asession, "crop_culture")
            species = await _keys(asession, "crop_species")
            varieties = await _keys(asession, "crop_catalog_variety")
            profiles = await _keys(asession, "crop_phenology_profile")

            for index, spec in enumerate(PHENOLOGY_PROFILES, start=1):
                culture_key = str(spec.get("culture_key", ""))
                culture_id = cultures.get(culture_key)
                if culture_id is None:
                    logging.warning(
                        "Profil phénologique ignoré : culture inconnue '%s'.",
                        culture_key,
                    )
                    continue

                profile_key = str(spec["key"])
                profile_id = profiles.get(profile_key)
                if profile_id is None:
                    await asession.execute(
                        text(
                            """
                            INSERT INTO crop_phenology_profile (
                                culture_id, species_id, catalog_variety_id, key,
                                name, phenological_system, summary, source,
                                is_default, is_active, position
                            ) VALUES (
                                :culture_id, :species_id, :variety_id, :key,
                                :name, :system, :summary, :source,
                                :is_default, 1, :position
                            )
                            """
                        ),
                        {
                            "culture_id": culture_id,
                            "species_id": species.get(spec.get("species_key")),
                            "variety_id": varieties.get(
                                spec.get("variety_key")
                            ),
                            "key": profile_key,
                            "name": str(spec["name"]),
                            "system": str(spec.get("system", SYSTEM_LOCAL)),
                            "summary": str(spec.get("summary", "")),
                            "source": str(spec.get("source", "")),
                            "is_default": bool(spec.get("is_default", False)),
                            "position": index,
                        },
                    )
                    profile_id = int(
                        (
                            await asession.execute(
                                text(
                                    """
                                    SELECT id FROM crop_phenology_profile
                                    WHERE key = :key
                                    """
                                ),
                                {"key": profile_key},
                            )
                        ).scalar()
                        or 0
                    )
                    profiles[profile_key] = profile_id

                existing_stages = {
                    str(row[0]): int(row[1])
                    for row in (
                        await asession.execute(
                            text(
                                """
                                SELECT key, id FROM crop_phenology_stage
                                WHERE profile_id = :profile_id
                                """
                            ),
                            {"profile_id": profile_id},
                        )
                    ).all()
                }

                for position, stage in enumerate(
                    spec.get("stages", []), start=1
                ):
                    stage_key = str(stage["key"])
                    stage_id = existing_stages.get(stage_key)
                    if stage_id is None:
                        await asession.execute(
                            text(
                                """
                                INSERT INTO crop_phenology_stage (
                                    profile_id, key, name, position, bbch_code,
                                    phenological_system, description,
                                    recognition, watchpoints, common_errors,
                                    duration_days_min, duration_days_max,
                                    is_critical, is_active, icon, color_hex,
                                    guide_article_slug, guide_term_slug
                                ) VALUES (
                                    :profile_id, :key, :name, :position, :bbch,
                                    :system, :description,
                                    :recognition, :watchpoints, :common_errors,
                                    :days_min, :days_max,
                                    :is_critical, 1, :icon, :color,
                                    :guide_article_slug, :guide_term_slug
                                )
                                """
                            ),
                            {
                                "profile_id": profile_id,
                                "key": stage_key,
                                "name": str(stage["name"]),
                                "position": position,
                                "bbch": str(stage.get("bbch", "")),
                                "system": str(spec.get("system", SYSTEM_LOCAL)),
                                "description": str(
                                    stage.get("description", "")
                                ),
                                "recognition": str(
                                    stage.get("recognition", "")
                                ),
                                "watchpoints": str(
                                    stage.get("watchpoints", "")
                                ),
                                "common_errors": str(
                                    stage.get("common_errors", "")
                                ),
                                "days_min": int(stage.get("days_min", 0)),
                                "days_max": int(stage.get("days_max", 0)),
                                "is_critical": bool(
                                    stage.get("is_critical", False)
                                ),
                                "icon": str(stage.get("icon", "sprout")),
                                "color": str(stage.get("color_hex", "#a3e635")),
                                # Colonnes NOT NULL sans valeur par défaut en
                                # base : chaîne vide si aucun lien Guide.
                                "guide_article_slug": str(
                                    stage.get("guide_article_slug", "")
                                ),
                                "guide_term_slug": str(
                                    stage.get("guide_term_slug", "")
                                ),
                            },
                        )
                        stage_id = int(
                            (
                                await asession.execute(
                                    text(
                                        """
                                        SELECT id FROM crop_phenology_stage
                                        WHERE profile_id = :profile_id
                                          AND key = :key
                                        """
                                    ),
                                    {
                                        "profile_id": profile_id,
                                        "key": stage_key,
                                    },
                                )
                            ).scalar()
                            or 0
                        )
                        existing_stages[stage_key] = stage_id

                    recommendations = stage.get("recommendations", [])
                    if not recommendations:
                        continue
                    known = [
                        str(row[0])
                        for row in (
                            await asession.execute(
                                text(
                                    """
                                    SELECT title FROM crop_stage_recommendation
                                    WHERE stage_id = :stage_id
                                    """
                                ),
                                {"stage_id": stage_id},
                            )
                        ).all()
                    ]
                    for reco_index, reco in enumerate(recommendations, start=1):
                        title = str(reco["title"])
                        if title in known:
                            continue
                        await asession.execute(
                            text(
                                """
                                INSERT INTO crop_stage_recommendation (
                                    stage_id, domain, title, statement,
                                    confidence, source, is_advisory,
                                    guide_article_slug, position
                                ) VALUES (
                                    :stage_id, :domain, :title, :statement,
                                    :confidence, :source, 1,
                                    :guide_article_slug, :position
                                )
                                """
                            ),
                            {
                                "stage_id": stage_id,
                                "domain": str(reco["domain"]),
                                "title": title,
                                "statement": str(reco.get("statement", "")),
                                "confidence": str(
                                    reco.get(
                                        "confidence", CONFIDENCE_INDICATIVE
                                    )
                                ),
                                "source": str(reco.get("source", "")),
                                "guide_article_slug": str(
                                    reco.get("guide_article_slug", "")
                                ),
                                "position": reco_index,
                            },
                        )

            await asession.commit()
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
        raise

    _seeded = True

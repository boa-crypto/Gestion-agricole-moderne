"""Administration du référentiel phénologique : écritures SQL brutes.

Ce module porte toutes les opérations d'administration demandées par le prompt
(section 37) : créer et modifier un profil ou un stade, réordonner, désactiver,
associer un code BBCH, ajouter une définition, une recommandation, marquer les
stades critiques et relier le Guide Agricole.

Règles :

* **rien n'est jamais supprimé** : la désactivation (`is_active = 0`) remplace
  toute suppression, profils comme stades ;
* les recommandations restent **non prescriptives** : `is_advisory` est forcé à
  vrai et la source est obligatoire ;
* import CSV / JSON **additif** : un stade existant est enrichi, jamais écrasé
  par des valeurs vides ;
* export JSON / CSV des profils, stades et recommandations ;
* SQL brut via `rx.asession()`, sur le fichier SQLite local déjà créé de façon
  idempotente. Aucune migration protégée n'est touchée.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import re
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.database import ensure_local_database
from app.phenology_reference import (
    CONFIDENCE_KEYS,
    RECOMMENDATION_DOMAIN_KEYS,
    SYSTEM_KEYS,
    SYSTEM_LOCAL,
    confidence_label,
    normalize_stage_label,
    recommendation_domain_icon,
    recommendation_domain_label,
    system_label,
)

__all__ = [
    "CultureOption",
    "ProfileAdminRow",
    "RecoAdminRow",
    "StageAdminRow",
    "admin_profiles",
    "admin_recommendations",
    "admin_stages",
    "culture_options",
    "export_phenology_csv",
    "export_phenology_json",
    "import_stages",
    "move_stage",
    "save_profile",
    "save_recommendation",
    "save_stage",
    "set_profile_active",
    "set_stage_active",
    "set_stage_critical",
]

KEY_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Colonnes acceptées par l'import CSV / JSON des stades.
IMPORT_FIELDS: list[str] = [
    "key",
    "name",
    "position",
    "bbch_code",
    "description",
    "recognition",
    "watchpoints",
    "common_errors",
    "duration_days_min",
    "duration_days_max",
    "is_critical",
    "icon",
    "color_hex",
    "guide_article_slug",
    "guide_term_slug",
]


class CultureOption(TypedDict):
    value: str
    label: str


class ProfileAdminRow(TypedDict):
    id: int
    key: str
    name: str
    culture_id: int
    culture_name: str
    culture_key: str
    system: str
    system_label: str
    summary: str
    source: str
    is_default: bool
    is_active: bool
    stage_count: int
    active_stages: int
    critical_stages: int
    recommendation_count: int
    scope_label: str


class StageAdminRow(TypedDict):
    id: int
    profile_id: int
    key: str
    name: str
    position: int
    bbch_code: str
    description: str
    recognition: str
    watchpoints: str
    common_errors: str
    duration_days_min: int
    duration_days_max: int
    duration_label: str
    is_critical: bool
    is_active: bool
    icon: str
    color_hex: str
    guide_article_slug: str
    guide_term_slug: str
    recommendation_count: int


class RecoAdminRow(TypedDict):
    id: int
    stage_id: int
    domain: str
    domain_label: str
    icon: str
    title: str
    statement: str
    confidence: str
    confidence_label: str
    source: str
    is_advisory: bool
    guide_article_slug: str
    position: int


def _duration_label(days_min: int, days_max: int) -> str:
    if days_min <= 0 and days_max <= 0:
        return "Durée non renseignée"
    if days_min <= 0:
        return f"≤ {days_max} j"
    if days_max <= 0:
        return f"≥ {days_min} j"
    return f"{days_min}–{days_max} j"


def _as_int(value: object, fallback: int = 0) -> int:
    try:
        return int(float(str(value).strip().replace(",", ".")))
    except (TypeError, ValueError):
        return fallback


def _flag(value: object) -> bool:
    return str(value).strip().lower() in ("1", "on", "true", "oui", "yes", "x")


def _slug(value: str) -> str:
    return normalize_stage_label(value)


# ---------------------------------------------------------------------------
# Lectures d'administration
# ---------------------------------------------------------------------------

_CULTURES_SQL: str = """
    SELECT cu.id, cu.name, COALESCE(cat.name, '')
    FROM crop_culture cu
    LEFT JOIN crop_category cat ON cat.id = cu.category_id
    WHERE cu.is_active = 1
    ORDER BY cat.position, cu.position, cu.name
    LIMIT 200
"""

_PROFILES_SQL: str = """
    SELECT p.id, p.key, p.name, p.culture_id, COALESCE(cu.name, ''),
           COALESCE(cu.key, ''), p.phenological_system, COALESCE(p.summary, ''),
           COALESCE(p.source, ''), p.is_default, p.is_active,
           (SELECT COUNT(*) FROM crop_phenology_stage s
              WHERE s.profile_id = p.id),
           (SELECT COUNT(*) FROM crop_phenology_stage s
              WHERE s.profile_id = p.id AND s.is_active = 1),
           (SELECT COUNT(*) FROM crop_phenology_stage s
              WHERE s.profile_id = p.id AND s.is_critical = 1),
           (SELECT COUNT(*) FROM crop_stage_recommendation r
              JOIN crop_phenology_stage s2 ON s2.id = r.stage_id
              WHERE s2.profile_id = p.id),
           p.species_id, p.catalog_variety_id
    FROM crop_phenology_profile p
    LEFT JOIN crop_culture cu ON cu.id = p.culture_id
    ORDER BY cu.name, p.is_default DESC, p.id
    LIMIT 200
"""

_STAGES_ADMIN_SQL: str = """
    SELECT st.id, st.profile_id, st.key, st.name, st.position,
           COALESCE(st.bbch_code, ''), COALESCE(st.description, ''),
           COALESCE(st.recognition, ''), COALESCE(st.watchpoints, ''),
           COALESCE(st.common_errors, ''), COALESCE(st.duration_days_min, 0),
           COALESCE(st.duration_days_max, 0), st.is_critical, st.is_active,
           COALESCE(st.icon, 'sprout'), COALESCE(st.color_hex, '#a3e635'),
           COALESCE(st.guide_article_slug, ''),
           COALESCE(st.guide_term_slug, ''),
           (SELECT COUNT(*) FROM crop_stage_recommendation r
              WHERE r.stage_id = st.id)
    FROM crop_phenology_stage st
    WHERE st.profile_id = :profile_id
    ORDER BY st.position, st.id
"""

_RECOS_ADMIN_SQL: str = """
    SELECT r.id, r.stage_id, r.domain, r.title, COALESCE(r.statement, ''),
           r.confidence, COALESCE(r.source, ''), r.is_advisory,
           COALESCE(r.guide_article_slug, ''), COALESCE(r.position, 0)
    FROM crop_stage_recommendation r
    WHERE r.stage_id = :stage_id
    ORDER BY r.position, r.id
"""


async def culture_options() -> list[CultureOption]:
    """Cultures du référentiel structuré, rattachables à un profil."""
    await ensure_local_database()
    async with rx.asession() as asession:
        rows = (await asession.execute(text(_CULTURES_SQL))).all()
    options: list[CultureOption] = []
    for row in rows:
        category = str(row[2])
        prefix = f"{category} · " if category else ""
        options.append(
            {"value": str(int(row[0])), "label": f"{prefix}{row[1]}"}
        )
    return options


async def admin_profiles() -> list[ProfileAdminRow]:
    """Profils phénologiques avec leurs volumes de stades et recommandations."""
    await ensure_local_database()
    async with rx.asession() as asession:
        rows = (await asession.execute(text(_PROFILES_SQL))).all()
    profiles: list[ProfileAdminRow] = []
    for row in rows:
        if row[16] is not None:
            scope = "Profil variétal"
        elif row[15] is not None:
            scope = "Profil d'espèce"
        else:
            scope = "Profil de culture"
        profiles.append(
            {
                "id": int(row[0]),
                "key": str(row[1]),
                "name": str(row[2]),
                "culture_id": int(row[3] or 0),
                "culture_name": str(row[4]) or "Culture non reliée",
                "culture_key": str(row[5]),
                "system": str(row[6]),
                "system_label": system_label(row[6]),
                "summary": str(row[7]),
                "source": str(row[8]) or "Source non précisée",
                "is_default": bool(row[9]),
                "is_active": bool(row[10]),
                "stage_count": int(row[11] or 0),
                "active_stages": int(row[12] or 0),
                "critical_stages": int(row[13] or 0),
                "recommendation_count": int(row[14] or 0),
                "scope_label": scope,
            }
        )
    return profiles


async def admin_stages(profile_id: int) -> list[StageAdminRow]:
    """Stades d'un profil, actifs ET désactivés (rien n'est supprimé)."""
    if int(profile_id) <= 0:
        return []
    await ensure_local_database()
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(_STAGES_ADMIN_SQL), {"profile_id": int(profile_id)}
            )
        ).all()
    return [
        {
            "id": int(row[0]),
            "profile_id": int(row[1]),
            "key": str(row[2]),
            "name": str(row[3]),
            "position": int(row[4] or 0),
            "bbch_code": str(row[5]),
            "description": str(row[6]),
            "recognition": str(row[7]),
            "watchpoints": str(row[8]),
            "common_errors": str(row[9]),
            "duration_days_min": int(row[10] or 0),
            "duration_days_max": int(row[11] or 0),
            "duration_label": _duration_label(
                int(row[10] or 0), int(row[11] or 0)
            ),
            "is_critical": bool(row[12]),
            "is_active": bool(row[13]),
            "icon": str(row[14]),
            "color_hex": str(row[15]),
            "guide_article_slug": str(row[16]),
            "guide_term_slug": str(row[17]),
            "recommendation_count": int(row[18] or 0),
        }
        for row in rows
    ]


async def admin_recommendations(stage_id: int) -> list[RecoAdminRow]:
    """Recommandations d'un stade (toujours indicatives)."""
    if int(stage_id) <= 0:
        return []
    await ensure_local_database()
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(_RECOS_ADMIN_SQL), {"stage_id": int(stage_id)}
            )
        ).all()
    return [
        {
            "id": int(row[0]),
            "stage_id": int(row[1]),
            "domain": str(row[2]),
            "domain_label": recommendation_domain_label(row[2]),
            "icon": recommendation_domain_icon(row[2]),
            "title": str(row[3]),
            "statement": str(row[4]),
            "confidence": str(row[5]),
            "confidence_label": confidence_label(row[5]),
            "source": str(row[6]) or "Référentiel agronomique AgriPro",
            "is_advisory": bool(row[7]),
            "guide_article_slug": str(row[8]),
            "position": int(row[9] or 0),
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Écritures : profils
# ---------------------------------------------------------------------------


def _validate_profile(data: dict[str, str]) -> list[str]:
    errors: list[str] = []
    key = str(data.get("key", "")).strip()
    if not KEY_PATTERN.fullmatch(key):
        errors.append(
            "L'identifiant du profil doit être en minuscules, chiffres et tirets."
        )
    if len(str(data.get("name", "")).strip()) < 4:
        errors.append("Le nom du profil doit comporter au moins 4 caractères.")
    if _as_int(data.get("culture_id"), 0) <= 0:
        errors.append("Le profil doit être rattaché à une culture.")
    if str(data.get("system", "")) not in SYSTEM_KEYS:
        errors.append("Le système phénologique est invalide.")
    if len(str(data.get("source", "")).strip()) < 4:
        errors.append(
            "La source du référentiel est obligatoire : aucune donnée "
            "agronomique ne doit être inventée."
        )
    return errors


async def save_profile(
    data: dict[str, str], profile_id: int = 0
) -> dict[str, str | int | bool | list[str]]:
    """Crée ou met à jour un profil phénologique (jamais de suppression)."""
    errors = _validate_profile(data)
    if errors:
        return {"ok": False, "errors": errors, "profile_id": int(profile_id)}

    await ensure_local_database()
    params = {
        "culture_id": _as_int(data.get("culture_id"), 0),
        "key": str(data.get("key", "")).strip(),
        "name": str(data.get("name", "")).strip(),
        "system": str(data.get("system", SYSTEM_LOCAL)),
        "summary": str(data.get("summary", "")).strip(),
        "source": str(data.get("source", "")).strip(),
        "is_default": _flag(data.get("is_default")),
        "is_active": _flag(data.get("is_active", "1")),
        "pid": int(profile_id),
    }
    async with rx.asession() as asession:
        clash = (
            await asession.execute(
                text(
                    """
                    SELECT COUNT(*) FROM crop_phenology_profile
                    WHERE key = :key AND id <> :pid
                    """
                ),
                {"key": params["key"], "pid": int(profile_id)},
            )
        ).scalar()
        if int(clash or 0) > 0:
            return {
                "ok": False,
                "errors": [
                    f"L'identifiant « {params['key']} » est déjà utilisé."
                ],
                "profile_id": int(profile_id),
            }

        if int(profile_id) > 0:
            await asession.execute(
                text(
                    """
                    UPDATE crop_phenology_profile SET
                        culture_id = :culture_id, key = :key, name = :name,
                        phenological_system = :system, summary = :summary,
                        source = :source, is_default = :is_default,
                        is_active = :is_active
                    WHERE id = :pid
                    """
                ),
                params,
            )
            new_id = int(profile_id)
            message = "Profil phénologique mis à jour."
        else:
            position = int(
                (
                    await asession.execute(
                        text(
                            "SELECT COALESCE(MAX(position), 0) + 1 "
                            "FROM crop_phenology_profile"
                        )
                    )
                ).scalar()
                or 1
            )
            params["position"] = position
            await asession.execute(
                text(
                    """
                    INSERT INTO crop_phenology_profile (
                        culture_id, species_id, catalog_variety_id, key, name,
                        phenological_system, summary, source, is_default,
                        is_active, position
                    ) VALUES (
                        :culture_id, NULL, NULL, :key, :name,
                        :system, :summary, :source, :is_default,
                        :is_active, :position
                    )
                    """
                ),
                params,
            )
            new_id = int(
                (
                    await asession.execute(
                        text(
                            "SELECT id FROM crop_phenology_profile "
                            "WHERE key = :key"
                        ),
                        {"key": params["key"]},
                    )
                ).scalar()
                or 0
            )
            message = "Profil phénologique créé."
        await asession.commit()
    return {
        "ok": True,
        "errors": [],
        "profile_id": new_id,
        "message": message,
    }


async def set_profile_active(profile_id: int, active: bool) -> str:
    """Active ou désactive un profil sans jamais le supprimer."""
    await ensure_local_database()
    async with rx.asession() as asession:
        await asession.execute(
            text(
                "UPDATE crop_phenology_profile SET is_active = :active "
                "WHERE id = :pid"
            ),
            {"active": bool(active), "pid": int(profile_id)},
        )
        await asession.commit()
    return (
        "Profil réactivé : il redevient utilisable."
        if active
        else "Profil désactivé : les données restent conservées."
    )


# ---------------------------------------------------------------------------
# Écritures : stades
# ---------------------------------------------------------------------------


def _validate_stage(data: dict[str, str]) -> list[str]:
    errors: list[str] = []
    if len(str(data.get("name", "")).strip()) < 3:
        errors.append("Le nom du stade doit comporter au moins 3 caractères.")
    key = str(data.get("key", "")).strip() or _slug(data.get("name"))
    if not KEY_PATTERN.fullmatch(key):
        errors.append(
            "L'identifiant du stade doit être en minuscules, chiffres et tirets."
        )
    days_min = _as_int(data.get("duration_days_min"), 0)
    days_max = _as_int(data.get("duration_days_max"), 0)
    if days_min < 0 or days_max < 0:
        errors.append("Les durées indicatives ne peuvent pas être négatives.")
    if days_min > 0 and days_max > 0 and days_min > days_max:
        errors.append(
            "La durée minimale doit être inférieure ou égale à la durée maximale."
        )
    if days_max > 400:
        errors.append("La durée maximale d'un stade paraît irréaliste.")
    color = str(data.get("color_hex", "")).strip()
    if color and not re.fullmatch(r"#[0-9a-fA-F]{3,8}", color):
        errors.append("La couleur doit être un code hexadécimal (ex. #a3e635).")
    return errors


def _stage_params(profile_id: int, data: dict[str, str]) -> dict[str, object]:
    name = str(data.get("name", "")).strip()
    key = str(data.get("key", "")).strip() or _slug(name)
    return {
        "profile_id": int(profile_id),
        "key": key,
        "name": name,
        "bbch": str(data.get("bbch_code", "")).strip(),
        "description": str(data.get("description", "")).strip(),
        "recognition": str(data.get("recognition", "")).strip(),
        "watchpoints": str(data.get("watchpoints", "")).strip(),
        "common_errors": str(data.get("common_errors", "")).strip(),
        "days_min": _as_int(data.get("duration_days_min"), 0),
        "days_max": _as_int(data.get("duration_days_max"), 0),
        "is_critical": _flag(data.get("is_critical")),
        "is_active": _flag(data.get("is_active", "1")),
        "icon": str(data.get("icon", "")).strip() or "sprout",
        "color": str(data.get("color_hex", "")).strip() or "#a3e635",
        "guide_article_slug": str(data.get("guide_article_slug", "")).strip(),
        "guide_term_slug": str(data.get("guide_term_slug", "")).strip(),
    }


_STAGE_INSERT_SQL: str = """
    INSERT INTO crop_phenology_stage (
        profile_id, key, name, position, bbch_code, phenological_system,
        description, recognition, watchpoints, common_errors,
        duration_days_min, duration_days_max, is_critical, is_active,
        icon, color_hex, guide_article_slug, guide_term_slug
    ) VALUES (
        :profile_id, :key, :name, :position, :bbch, :system,
        :description, :recognition, :watchpoints, :common_errors,
        :days_min, :days_max, :is_critical, :is_active,
        :icon, :color, :guide_article_slug, :guide_term_slug
    )
"""

_STAGE_UPDATE_SQL: str = """
    UPDATE crop_phenology_stage SET
        key = :key, name = :name, bbch_code = :bbch,
        description = :description, recognition = :recognition,
        watchpoints = :watchpoints, common_errors = :common_errors,
        duration_days_min = :days_min, duration_days_max = :days_max,
        is_critical = :is_critical, is_active = :is_active,
        icon = :icon, color_hex = :color,
        guide_article_slug = :guide_article_slug,
        guide_term_slug = :guide_term_slug
    WHERE id = :sid
"""


async def save_stage(
    profile_id: int, data: dict[str, str], stage_id: int = 0
) -> dict[str, str | int | bool | list[str]]:
    """Crée ou met à jour un stade d'un profil (BBCH, définition, criticité)."""
    if int(profile_id) <= 0:
        return {
            "ok": False,
            "errors": ["Sélectionnez d'abord un profil phénologique."],
            "stage_id": int(stage_id),
        }
    errors = _validate_stage(data)
    if errors:
        return {"ok": False, "errors": errors, "stage_id": int(stage_id)}

    await ensure_local_database()
    params = _stage_params(profile_id, data)
    async with rx.asession() as asession:
        profile = (
            await asession.execute(
                text(
                    "SELECT phenological_system FROM crop_phenology_profile "
                    "WHERE id = :pid"
                ),
                {"pid": int(profile_id)},
            )
        ).first()
        params["system"] = str(profile[0]) if profile else SYSTEM_LOCAL

        clash = (
            await asession.execute(
                text(
                    """
                    SELECT COUNT(*) FROM crop_phenology_stage
                    WHERE profile_id = :profile_id AND key = :key
                      AND id <> :sid
                    """
                ),
                {
                    "profile_id": int(profile_id),
                    "key": params["key"],
                    "sid": int(stage_id),
                },
            )
        ).scalar()
        if int(clash or 0) > 0:
            return {
                "ok": False,
                "errors": [
                    f"Le stade « {params['key']} » existe déjà dans ce profil."
                ],
                "stage_id": int(stage_id),
            }

        if int(stage_id) > 0:
            params["sid"] = int(stage_id)
            await asession.execute(text(_STAGE_UPDATE_SQL), params)
            new_id = int(stage_id)
            message = "Stade mis à jour."
        else:
            params["position"] = int(
                (
                    await asession.execute(
                        text(
                            """
                            SELECT COALESCE(MAX(position), 0) + 1
                            FROM crop_phenology_stage
                            WHERE profile_id = :profile_id
                            """
                        ),
                        {"profile_id": int(profile_id)},
                    )
                ).scalar()
                or 1
            )
            await asession.execute(text(_STAGE_INSERT_SQL), params)
            new_id = int(
                (
                    await asession.execute(
                        text(
                            """
                            SELECT id FROM crop_phenology_stage
                            WHERE profile_id = :profile_id AND key = :key
                            """
                        ),
                        {"profile_id": int(profile_id), "key": params["key"]},
                    )
                ).scalar()
                or 0
            )
            message = "Stade ajouté au cycle."
        await asession.commit()
    return {
        "ok": True,
        "errors": [],
        "stage_id": new_id,
        "message": message,
    }


async def set_stage_active(stage_id: int, active: bool) -> str:
    """Désactive (ou réactive) un stade : les observations sont conservées."""
    await ensure_local_database()
    async with rx.asession() as asession:
        await asession.execute(
            text(
                "UPDATE crop_phenology_stage SET is_active = :active "
                "WHERE id = :sid"
            ),
            {"active": bool(active), "sid": int(stage_id)},
        )
        await asession.commit()
    return (
        "Stade réactivé dans le cycle."
        if active
        else "Stade désactivé : l'historique reste intact."
    )


async def set_stage_critical(stage_id: int, critical: bool) -> str:
    """Marque ou démarque un stade comme sensible."""
    await ensure_local_database()
    async with rx.asession() as asession:
        await asession.execute(
            text(
                "UPDATE crop_phenology_stage SET is_critical = :critical "
                "WHERE id = :sid"
            ),
            {"critical": bool(critical), "sid": int(stage_id)},
        )
        await asession.commit()
    return (
        "Stade signalé comme sensible."
        if critical
        else "Stade retiré des stades sensibles."
    )


async def move_stage(stage_id: int, direction: int) -> str:
    """Réordonne un stade dans son profil puis renumérote les positions."""
    await ensure_local_database()
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text(
                    "SELECT profile_id FROM crop_phenology_stage "
                    "WHERE id = :sid"
                ),
                {"sid": int(stage_id)},
            )
        ).first()
        if row is None:
            return "Stade introuvable."
        profile_id = int(row[0])
        rows = (
            await asession.execute(
                text(
                    """
                    SELECT id FROM crop_phenology_stage
                    WHERE profile_id = :pid
                    ORDER BY position, id
                    """
                ),
                {"pid": profile_id},
            )
        ).all()
        ids = [int(item[0]) for item in rows]
        if int(stage_id) not in ids:
            return "Stade introuvable dans ce profil."
        index = ids.index(int(stage_id))
        target = index + (1 if int(direction) > 0 else -1)
        if target < 0 or target >= len(ids):
            return "Le stade est déjà à cette extrémité du cycle."
        ids[index], ids[target] = ids[target], ids[index]
        for position, identifier in enumerate(ids, start=1):
            await asession.execute(
                text(
                    "UPDATE crop_phenology_stage SET position = :position "
                    "WHERE id = :sid"
                ),
                {"position": position, "sid": identifier},
            )
        await asession.commit()
    return "Ordre du cycle mis à jour."


# ---------------------------------------------------------------------------
# Écritures : recommandations (toujours indicatives)
# ---------------------------------------------------------------------------


def _validate_reco(data: dict[str, str]) -> list[str]:
    errors: list[str] = []
    if str(data.get("domain", "")) not in RECOMMENDATION_DOMAIN_KEYS:
        errors.append("Le domaine de la recommandation est invalide.")
    if str(data.get("confidence", "")) not in CONFIDENCE_KEYS:
        errors.append("Le niveau de confiance est invalide.")
    if len(str(data.get("title", "")).strip()) < 5:
        errors.append("Le titre de la recommandation est trop court.")
    if len(str(data.get("statement", "")).strip()) < 20:
        errors.append(
            "L'énoncé doit rester descriptif et explicite (20 caractères)."
        )
    if len(str(data.get("source", "")).strip()) < 4:
        errors.append(
            "La source est obligatoire : aucune donnée agronomique inventée."
        )
    statement = str(data.get("statement", "")).lower()
    for forbidden in (" l/ha", " kg/ha", " g/ha", " doses de "):
        if forbidden in statement:
            errors.append(
                "Une recommandation ne peut pas porter de dose chiffrée : "
                "restez sur une information générale à vérifier."
            )
            break
    return errors


async def save_recommendation(
    stage_id: int, data: dict[str, str], reco_id: int = 0
) -> dict[str, str | int | bool | list[str]]:
    """Ajoute ou met à jour une recommandation NON prescriptive d'un stade."""
    if int(stage_id) <= 0:
        return {
            "ok": False,
            "errors": ["Sélectionnez d'abord un stade."],
            "reco_id": int(reco_id),
        }
    errors = _validate_reco(data)
    if errors:
        return {"ok": False, "errors": errors, "reco_id": int(reco_id)}

    await ensure_local_database()
    params = {
        "stage_id": int(stage_id),
        "domain": str(data.get("domain", "SURVEILLANCE")),
        "title": str(data.get("title", "")).strip(),
        "statement": str(data.get("statement", "")).strip(),
        "confidence": str(data.get("confidence", "INDICATIVE")),
        "source": str(data.get("source", "")).strip(),
        "guide_article_slug": str(data.get("guide_article_slug", "")).strip(),
        "rid": int(reco_id),
    }
    async with rx.asession() as asession:
        if int(reco_id) > 0:
            await asession.execute(
                text(
                    """
                    UPDATE crop_stage_recommendation SET
                        domain = :domain, title = :title,
                        statement = :statement, confidence = :confidence,
                        source = :source, is_advisory = 1,
                        guide_article_slug = :guide_article_slug
                    WHERE id = :rid
                    """
                ),
                params,
            )
            message = "Recommandation indicative mise à jour."
        else:
            params["position"] = int(
                (
                    await asession.execute(
                        text(
                            """
                            SELECT COALESCE(MAX(position), 0) + 1
                            FROM crop_stage_recommendation
                            WHERE stage_id = :stage_id
                            """
                        ),
                        {"stage_id": int(stage_id)},
                    )
                ).scalar()
                or 1
            )
            await asession.execute(
                text(
                    """
                    INSERT INTO crop_stage_recommendation (
                        stage_id, domain, title, statement, confidence,
                        source, is_advisory, guide_article_slug, position
                    ) VALUES (
                        :stage_id, :domain, :title, :statement, :confidence,
                        :source, 1, :guide_article_slug, :position
                    )
                    """
                ),
                params,
            )
            message = "Recommandation indicative ajoutée."
        await asession.commit()
    return {"ok": True, "errors": [], "message": message}


# ---------------------------------------------------------------------------
# Import CSV / JSON (additif, jamais destructif)
# ---------------------------------------------------------------------------


def _parse_payload(payload: str, fmt: str) -> list[dict[str, str]]:
    raw = payload.strip()
    if not raw:
        return []
    if fmt.upper() == "JSON":
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            parsed = parsed.get("stages", [])
        if not isinstance(parsed, list):
            raise ValueError("Le JSON doit contenir une liste de stades.")
        return [
            {str(k): "" if v is None else str(v) for k, v in item.items()}
            for item in parsed
            if isinstance(item, dict)
        ]
    reader = csv.DictReader(io.StringIO(raw))
    rows: list[dict[str, str]] = []
    for item in reader:
        rows.append(
            {
                str(k).strip(): ("" if v is None else str(v).strip())
                for k, v in item.items()
                if k
            }
        )
    return rows


async def import_stages(
    profile_id: int, payload: str, fmt: str = "CSV"
) -> dict[str, int | list[str] | bool]:
    """Enrichit les stades d'un profil depuis un CSV ou un JSON.

    Import **additif** : un stade existant est complété (les champs vides de la
    source n'écrasent rien), un stade inconnu est créé à la suite du cycle.
    Aucune ligne existante n'est supprimée.
    """
    if int(profile_id) <= 0:
        return {
            "ok": False,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": ["Sélectionnez d'abord un profil phénologique."],
        }
    try:
        rows = _parse_payload(payload, fmt)
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
        return {
            "ok": False,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": [f"Contenu {fmt.upper()} illisible : {e}"],
        }
    if not rows:
        return {
            "ok": False,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": ["Aucune ligne exploitable dans le contenu fourni."],
        }

    await ensure_local_database()
    existing = {stage["key"]: stage for stage in await admin_stages(profile_id)}
    created = 0
    updated = 0
    skipped = 0
    errors: list[str] = []

    for index, item in enumerate(rows, start=1):
        data = {field: item.get(field, "") for field in IMPORT_FIELDS}
        name = str(data.get("name", "")).strip()
        key = str(data.get("key", "")).strip() or _slug(name)
        if not name and key in existing:
            name = existing[key]["name"]
        data["name"] = name
        data["key"] = key
        current = existing.get(key)
        if current is not None:
            merged = {
                "key": key,
                "name": name or current["name"],
                "bbch_code": data["bbch_code"] or current["bbch_code"],
                "description": data["description"] or current["description"],
                "recognition": data["recognition"] or current["recognition"],
                "watchpoints": data["watchpoints"] or current["watchpoints"],
                "common_errors": data["common_errors"]
                or current["common_errors"],
                "duration_days_min": data["duration_days_min"]
                or str(current["duration_days_min"]),
                "duration_days_max": data["duration_days_max"]
                or str(current["duration_days_max"]),
                "is_critical": "1"
                if (
                    _flag(data["is_critical"])
                    or (data["is_critical"] == "" and current["is_critical"])
                )
                else "0",
                "is_active": "1",
                "icon": data["icon"] or current["icon"],
                "color_hex": data["color_hex"] or current["color_hex"],
                "guide_article_slug": data["guide_article_slug"]
                or current["guide_article_slug"],
                "guide_term_slug": data["guide_term_slug"]
                or current["guide_term_slug"],
            }
            result = await save_stage(profile_id, merged, current["id"])
            if result["ok"]:
                updated += 1
            else:
                skipped += 1
                errors.append(
                    f"Ligne {index} ({key}) : "
                    f"{'; '.join(str(m) for m in result['errors'])}"
                )
            continue

        data["is_critical"] = "1" if _flag(data["is_critical"]) else "0"
        data["is_active"] = "1"
        result = await save_stage(profile_id, data)
        if result["ok"]:
            created += 1
            refreshed = await admin_stages(profile_id)
            existing = {stage["key"]: stage for stage in refreshed}
        else:
            skipped += 1
            errors.append(
                f"Ligne {index} ({key or 'sans clé'}) : "
                f"{'; '.join(str(m) for m in result['errors'])}"
            )

    return {
        "ok": created + updated > 0,
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Export JSON / CSV
# ---------------------------------------------------------------------------

_EXPORT_SQL: str = """
    SELECT p.id, p.key, p.name, COALESCE(cu.name, ''),
           p.phenological_system, COALESCE(p.summary, ''),
           COALESCE(p.source, ''), p.is_default, p.is_active
    FROM crop_phenology_profile p
    LEFT JOIN crop_culture cu ON cu.id = p.culture_id
    WHERE (:pid = 0 OR p.id = :pid)
    ORDER BY cu.name, p.id
"""


async def _export_tree(profile_id: int = 0) -> list[dict]:
    await ensure_local_database()
    async with rx.asession() as asession:
        profiles = (
            await asession.execute(text(_EXPORT_SQL), {"pid": int(profile_id)})
        ).all()
        tree: list[dict] = []
        for profile in profiles:
            stages = (
                await asession.execute(
                    text(_STAGES_ADMIN_SQL), {"profile_id": int(profile[0])}
                )
            ).all()
            stage_items: list[dict] = []
            for stage in stages:
                recos = (
                    await asession.execute(
                        text(_RECOS_ADMIN_SQL), {"stage_id": int(stage[0])}
                    )
                ).all()
                stage_items.append(
                    {
                        "key": str(stage[2]),
                        "name": str(stage[3]),
                        "position": int(stage[4] or 0),
                        "bbch_code": str(stage[5]),
                        "description": str(stage[6]),
                        "recognition": str(stage[7]),
                        "watchpoints": str(stage[8]),
                        "common_errors": str(stage[9]),
                        "duration_days_min": int(stage[10] or 0),
                        "duration_days_max": int(stage[11] or 0),
                        "is_critical": bool(stage[12]),
                        "is_active": bool(stage[13]),
                        "icon": str(stage[14]),
                        "color_hex": str(stage[15]),
                        "guide_article_slug": str(stage[16]),
                        "guide_term_slug": str(stage[17]),
                        "recommendations": [
                            {
                                "domain": str(item[2]),
                                "title": str(item[3]),
                                "statement": str(item[4]),
                                "confidence": str(item[5]),
                                "source": str(item[6]),
                                "is_advisory": bool(item[7]),
                                "guide_article_slug": str(item[8]),
                            }
                            for item in recos
                        ],
                    }
                )
            tree.append(
                {
                    "key": str(profile[1]),
                    "name": str(profile[2]),
                    "culture": str(profile[3]),
                    "phenological_system": str(profile[4]),
                    "summary": str(profile[5]),
                    "source": str(profile[6]),
                    "is_default": bool(profile[7]),
                    "is_active": bool(profile[8]),
                    "stages": stage_items,
                }
            )
    return tree


async def export_phenology_json(profile_id: int = 0) -> str:
    """Export JSON des profils, stades et recommandations."""
    tree = await _export_tree(profile_id)
    payload = {
        "format": "agripro-phenology",
        "version": 1,
        "advisory_only": True,
        "profiles": tree,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


async def export_phenology_csv(profile_id: int = 0) -> str:
    """Export CSV à plat des stades et de leurs recommandations."""
    tree = await _export_tree(profile_id)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "profile_key",
            "profile_name",
            "culture",
            "stage_key",
            "stage_name",
            "position",
            "bbch_code",
            "duration_days_min",
            "duration_days_max",
            "is_critical",
            "is_active",
            "description",
            "recognition",
            "watchpoints",
            "common_errors",
            "guide_article_slug",
            "recommendation_domain",
            "recommendation_title",
            "recommendation_confidence",
            "recommendation_source",
            "advisory_only",
        ]
    )
    for profile in tree:
        for stage in profile["stages"]:
            recos = stage["recommendations"] or [None]
            for reco in recos:
                writer.writerow(
                    [
                        profile["key"],
                        profile["name"],
                        profile["culture"],
                        stage["key"],
                        stage["name"],
                        stage["position"],
                        stage["bbch_code"],
                        stage["duration_days_min"],
                        stage["duration_days_max"],
                        "1" if stage["is_critical"] else "0",
                        "1" if stage["is_active"] else "0",
                        stage["description"],
                        stage["recognition"],
                        stage["watchpoints"],
                        stage["common_errors"],
                        stage["guide_article_slug"],
                        reco["domain"] if reco else "",
                        reco["title"] if reco else "",
                        reco["confidence"] if reco else "",
                        reco["source"] if reco else "",
                        "1",
                    ]
                )
    return buffer.getvalue()

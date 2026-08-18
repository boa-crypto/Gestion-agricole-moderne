"""Validation et lecture du suivi phénologique (SQL brut + fonctions pures).

Ce module expose les briques réutilisables par les étapes suivantes du plan :

* résolution du **profil phénologique applicable** à une culture de parcelle
  (variété → espèce → culture, avec repli sur le profil de la culture) ;
* contrôle de **cohérence stade ↔ culture** : « Blé + Tallage » est valide,
  « Olivier + Tallage » ne l'est pas ;
* validation complète d'une observation (culture, parcelle, campagne, date,
  stade appartenant au référentiel de la culture) ;
* écriture traçable d'une observation : la table d'historique conserve
  l'ancien et le nouveau stade, sans jamais purger le passé ;
* lecture du cycle, de la progression et des recommandations non prescriptives.

Toutes les requêtes sont écrites en SQL brut via `rx.asession()`.
"""

from __future__ import annotations

import dataclasses
import datetime
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.database import ensure_local_database
from app.date_utils import as_date
from app.phenology_reference import (
    SOURCE_HUMAINE,
    STATUS_CONFIRME,
    normalize_stage_label,
    stage_duration_status,
    stage_progress_percent,
)

__all__ = [
    "PhenologyStage",
    "ProfileResolution",
    "StageValidation",
    "StageValidationResult",
    "culture_profile_candidates",
    "culture_stage_labels",
    "phenology_audit_matrix",
    "validate_stage_for_crop",
    "validate_stage_for_crop_name",
    "phenology_audit_report",
    "observation_history",
    "profile_for_crop",
    "profile_for_culture_key",
    "profile_stages",
    "record_stage_observation",
    "stage_recommendations",
    "validate_observation",
    "validate_stage_for_culture",
]


# ---------------------------------------------------------------------------
# Types de retour
# ---------------------------------------------------------------------------


class PhenologyStage(TypedDict):
    id: int
    key: str
    name: str
    position: int
    bbch_code: str
    description: str
    recognition: str
    watchpoints: str
    common_errors: str
    days_min: int
    days_max: int
    is_critical: bool
    icon: str
    color_hex: str
    progress: int


class ProfileResolution(TypedDict):
    found: bool
    profile_id: int
    profile_key: str
    profile_name: str
    system: str
    summary: str
    scope: str
    culture_key: str
    culture_name: str
    stage_count: int


class StageValidation(TypedDict):
    valid: bool
    reason: str
    stage_id: int
    stage_key: str
    stage_name: str
    position: int
    progress: int
    profile_id: int
    profile_key: str
    culture_key: str
    allowed: list[str]


EMPTY_PROFILE: ProfileResolution = {
    "found": False,
    "profile_id": 0,
    "profile_key": "",
    "profile_name": "",
    "system": "",
    "summary": "",
    "scope": "",
    "culture_key": "",
    "culture_name": "",
    "stage_count": 0,
}


# ---------------------------------------------------------------------------
# Requêtes SQL réutilisables
# ---------------------------------------------------------------------------

# Profil applicable à une culture de parcelle : la spécialisation la plus fine
# gagne (variété du référentiel, puis espèce, puis culture).
PROFILE_FOR_CROP_SQL: str = """
    SELECT p.id, p.key, p.name, p.phenological_system, COALESCE(p.summary, ''),
           cu.key, cu.name,
           CASE
               WHEN p.catalog_variety_id IS NOT NULL
                    AND p.catalog_variety_id = ccv.id THEN 'VARIETE'
               WHEN p.species_id IS NOT NULL
                    AND p.species_id = s.id THEN 'ESPECE'
               ELSE 'CULTURE'
           END AS scope,
           (SELECT COUNT(*) FROM crop_phenology_stage st
              WHERE st.profile_id = p.id AND st.is_active = 1)
    FROM crop c
    LEFT JOIN crop_catalog_variety ccv ON ccv.crop_variety_id = c.variety_id
    LEFT JOIN crop_species s ON s.id = ccv.species_id
    LEFT JOIN crop_culture cu ON cu.id = COALESCE(s.culture_id, 0)
    JOIN crop_phenology_profile p ON (
            (p.catalog_variety_id IS NOT NULL AND p.catalog_variety_id = ccv.id)
         OR (p.species_id IS NOT NULL AND p.species_id = s.id)
         OR (p.species_id IS NULL AND p.catalog_variety_id IS NULL
             AND p.culture_id = s.culture_id)
    )
    WHERE c.id = :crop_id AND p.is_active = 1
    ORDER BY
        CASE
            WHEN p.catalog_variety_id IS NOT NULL THEN 0
            WHEN p.species_id IS NOT NULL THEN 1
            ELSE 2
        END,
        p.id
    LIMIT 1
"""

PROFILE_FOR_CULTURE_SQL: str = """
    SELECT p.id, p.key, p.name, p.phenological_system, COALESCE(p.summary, ''),
           cu.key, cu.name, 'CULTURE',
           (SELECT COUNT(*) FROM crop_phenology_stage st
              WHERE st.profile_id = p.id AND st.is_active = 1)
    FROM crop_phenology_profile p
    JOIN crop_culture cu ON cu.id = p.culture_id
    WHERE cu.key = :culture_key
      AND p.is_active = 1
      AND p.species_id IS NULL
      AND p.catalog_variety_id IS NULL
    ORDER BY p.is_default DESC, p.id
    LIMIT 1
"""

PROFILE_STAGES_SQL: str = """
    SELECT st.id, st.key, st.name, st.position, COALESCE(st.bbch_code, ''),
           COALESCE(st.description, ''), COALESCE(st.recognition, ''),
           COALESCE(st.watchpoints, ''), COALESCE(st.common_errors, ''),
           COALESCE(st.duration_days_min, 0), COALESCE(st.duration_days_max, 0),
           st.is_critical, COALESCE(st.icon, 'sprout'),
           COALESCE(st.color_hex, '#a3e635')
    FROM crop_phenology_stage st
    WHERE st.profile_id = :profile_id AND st.is_active = 1
    ORDER BY st.position, st.id
"""

# Tous les stades déclarés pour une culture, quel que soit le profil : c'est la
# base du contrôle de cohérence « stade appartenant au référentiel ».
CULTURE_STAGES_SQL: str = """
    SELECT st.id, st.key, st.name, st.position, p.id, p.key,
           (SELECT COUNT(*) FROM crop_phenology_stage s2
              WHERE s2.profile_id = p.id AND s2.is_active = 1)
    FROM crop_phenology_stage st
    JOIN crop_phenology_profile p ON p.id = st.profile_id
    JOIN crop_culture cu ON cu.id = p.culture_id
    WHERE cu.key = :culture_key AND st.is_active = 1 AND p.is_active = 1
    ORDER BY p.is_default DESC, p.id, st.position
"""

STAGE_RECOMMENDATIONS_SQL: str = """
    SELECT r.id, r.domain, r.title, COALESCE(r.statement, ''),
           r.confidence, COALESCE(r.source, ''), r.is_advisory
    FROM crop_stage_recommendation r
    WHERE r.stage_id = :stage_id
    ORDER BY r.position, r.id
"""

OBSERVATION_HISTORY_SQL: str = """
    SELECT h.id, h.changed_on, COALESCE(h.author, ''), COALESCE(h.comment, ''),
           COALESCE(prev.name, ''), COALESCE(next.name, ''),
           COALESCE(h.observation_id, 0)
    FROM crop_stage_change h
    LEFT JOIN crop_phenology_stage prev ON prev.id = h.previous_stage_id
    LEFT JOIN crop_phenology_stage next ON next.id = h.new_stage_id
    WHERE h.crop_id = :crop_id
    ORDER BY h.changed_on DESC, h.id DESC
    LIMIT :limit
"""


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------


def _profile_row(row) -> ProfileResolution:
    return {
        "found": True,
        "profile_id": int(row[0]),
        "profile_key": str(row[1]),
        "profile_name": str(row[2]),
        "system": str(row[3]),
        "summary": str(row[4]),
        "scope": str(row[7]),
        "culture_key": str(row[5] or ""),
        "culture_name": str(row[6] or ""),
        "stage_count": int(row[8] or 0),
    }


async def profile_for_crop(crop_id: int) -> ProfileResolution:
    """Profil phénologique applicable à une culture de parcelle."""
    await ensure_local_database()
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text(PROFILE_FOR_CROP_SQL), {"crop_id": int(crop_id)}
            )
        ).first()
    return _profile_row(row) if row is not None else dict(EMPTY_PROFILE)


async def profile_for_culture_key(culture_key: str) -> ProfileResolution:
    """Profil par défaut d'une culture du référentiel structuré."""
    await ensure_local_database()
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text(PROFILE_FOR_CULTURE_SQL), {"culture_key": culture_key}
            )
        ).first()
    return _profile_row(row) if row is not None else dict(EMPTY_PROFILE)


async def profile_stages(profile_id: int) -> list[PhenologyStage]:
    """Stades ordonnés d'un profil, avec progression calculée."""
    await ensure_local_database()
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(PROFILE_STAGES_SQL), {"profile_id": int(profile_id)}
            )
        ).all()
    total = len(rows)
    stages: list[PhenologyStage] = []
    for row in rows:
        position = int(row[3] or 0)
        stages.append(
            {
                "id": int(row[0]),
                "key": str(row[1]),
                "name": str(row[2]),
                "position": position,
                "bbch_code": str(row[4]),
                "description": str(row[5]),
                "recognition": str(row[6]),
                "watchpoints": str(row[7]),
                "common_errors": str(row[8]),
                "days_min": int(row[9] or 0),
                "days_max": int(row[10] or 0),
                "is_critical": bool(row[11]),
                "icon": str(row[12]),
                "color_hex": str(row[13]),
                "progress": stage_progress_percent(position, total),
            }
        )
    return stages


async def culture_stage_labels(culture_key: str) -> list[str]:
    """Libellés de stades déclarés pour une culture (tous profils confondus)."""
    await ensure_local_database()
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(CULTURE_STAGES_SQL), {"culture_key": culture_key}
            )
        ).all()
    labels: list[str] = []
    for row in rows:
        label = str(row[2])
        if label not in labels:
            labels.append(label)
    return labels


async def stage_recommendations(
    stage_id: int,
) -> list[dict[str, str | bool | int]]:
    """Recommandations rattachées à un stade (toujours non prescriptives)."""
    await ensure_local_database()
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(STAGE_RECOMMENDATIONS_SQL), {"stage_id": int(stage_id)}
            )
        ).all()
    return [
        {
            "id": int(row[0]),
            "domain": str(row[1]),
            "title": str(row[2]),
            "statement": str(row[3]),
            "confidence": str(row[4]),
            "source": str(row[5]),
            "is_advisory": bool(row[6]),
        }
        for row in rows
    ]


async def observation_history(
    crop_id: int, limit: int = 40
) -> list[dict[str, str | int]]:
    """Historique des changements de stade d'une culture (jamais purgé)."""
    await ensure_local_database()
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(OBSERVATION_HISTORY_SQL),
                {"crop_id": int(crop_id), "limit": int(limit)},
            )
        ).all()
    return [
        {
            "id": int(row[0]),
            "changed_on": str(as_date(row[1]) or ""),
            "author": str(row[2]),
            "comment": str(row[3]),
            "previous_stage": str(row[4]),
            "new_stage": str(row[5]),
            "observation_id": int(row[6] or 0),
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _invalid(
    reason: str, culture_key: str, allowed: list[str]
) -> StageValidation:
    return {
        "valid": False,
        "reason": reason,
        "stage_id": 0,
        "stage_key": "",
        "stage_name": "",
        "position": 0,
        "progress": 0,
        "profile_id": 0,
        "profile_key": "",
        "culture_key": culture_key,
        "allowed": allowed,
    }


async def validate_stage_for_culture(
    culture_key: str, stage_label: str
) -> StageValidation:
    """Le stade appartient-il au référentiel phénologique de la culture ?

    Contrôle central du plan : « cereales--ble » + « Tallage » est valide,
    « arboriculture--olivier » + « Tallage » est refusé.
    """
    await ensure_local_database()
    target = normalize_stage_label(stage_label)
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(CULTURE_STAGES_SQL), {"culture_key": culture_key}
            )
        ).all()

    if not rows:
        return _invalid(
            f"Aucun référentiel phénologique déclaré pour « {culture_key} ».",
            culture_key,
            [],
        )

    allowed = [str(row[2]) for row in rows]
    if not target:
        return _invalid(
            "Le stade observé est obligatoire.", culture_key, allowed
        )

    for row in rows:
        if target in (
            normalize_stage_label(row[2]),
            normalize_stage_label(row[1]),
        ):
            position = int(row[3] or 0)
            return {
                "valid": True,
                "reason": "",
                "stage_id": int(row[0]),
                "stage_key": str(row[1]),
                "stage_name": str(row[2]),
                "position": position,
                "progress": stage_progress_percent(position, int(row[6] or 0)),
                "profile_id": int(row[4]),
                "profile_key": str(row[5]),
                "culture_key": culture_key,
                "allowed": allowed,
            }

    return _invalid(
        (
            f"Le stade « {stage_label} » n'existe pas dans le référentiel de "
            "cette culture."
        ),
        culture_key,
        allowed,
    )


async def validate_observation(
    crop_id: int,
    stage_label: str,
    observed_on: datetime.date | str | None,
    observer: str = "",
    season: str = "",
) -> dict[str, str | int | bool | list[str]]:
    """Valide une observation complète avant écriture.

    Contrôles : culture existante et rattachée à une parcelle, campagne,
    date d'observation renseignée et non future, observateur nommé, stade
    appartenant au référentiel de la culture.
    """
    await ensure_local_database()
    errors: list[str] = []
    day = as_date(observed_on)
    today = datetime.date.today()

    async with rx.asession() as asession:
        crop = (
            await asession.execute(
                text(
                    """
                    SELECT c.id, c.parcel_id, COALESCE(c.season, ''),
                           c.sowing_date, COALESCE(c.name, '')
                    FROM crop c WHERE c.id = :crop_id
                    """
                ),
                {"crop_id": int(crop_id)},
            )
        ).first()

    if crop is None:
        return {
            "valid": False,
            "errors": ["La culture observée est introuvable."],
            "stage_id": 0,
            "stage_name": "",
            "profile_id": 0,
            "progress": 0,
            "culture_key": "",
            "allowed": [],
        }

    if int(crop[1] or 0) <= 0:
        errors.append("L'observation doit être rattachée à une parcelle.")
    campaign = season.strip() or str(crop[2])
    if not campaign:
        errors.append("La campagne est obligatoire.")
    if day is None:
        errors.append("La date d'observation est obligatoire.")
    elif day > today:
        errors.append("La date d'observation ne peut pas être future.")
    else:
        sowing = as_date(crop[3])
        if sowing is not None and day < sowing:
            errors.append(
                "La date d'observation précède la date de semis de la culture."
            )
    if len(observer.strip()) < 2:
        errors.append("Le nom de l'observateur est obligatoire.")

    resolution = await profile_for_crop(int(crop_id))
    if not resolution["found"]:
        errors.append(
            "Aucun profil phénologique n'est rattaché à cette culture : "
            "reliez-la à une variété du référentiel."
        )
        return {
            "valid": False,
            "errors": errors,
            "stage_id": 0,
            "stage_name": "",
            "profile_id": 0,
            "progress": 0,
            "culture_key": resolution["culture_key"],
            "allowed": [],
        }

    stage = await validate_stage_for_culture(
        resolution["culture_key"], stage_label
    )
    if not stage["valid"]:
        errors.append(stage["reason"])

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "stage_id": stage["stage_id"],
        "stage_name": stage["stage_name"],
        "profile_id": resolution["profile_id"],
        "progress": stage["progress"],
        "culture_key": resolution["culture_key"],
        "allowed": stage["allowed"],
    }


# ---------------------------------------------------------------------------
# Écriture traçable
# ---------------------------------------------------------------------------


async def record_stage_observation(
    crop_id: int,
    stage_label: str,
    observed_on: datetime.date | str | None,
    observer: str,
    comment: str = "",
    status: str = STATUS_CONFIRME,
    source: str = SOURCE_HUMAINE,
    vigour: str = "",
    homogeneity: str = "",
    anomalies: str = "",
    season: str = "",
) -> dict[str, str | int | bool | list[str]]:
    """Enregistre une observation validée et trace le changement de stade.

    Ne supprime jamais l'historique : la table `crop_stage_change` conserve
    l'ancien et le nouveau stade. Le stade courant de `crop` et le journal
    historique `crop_stage_log` restent alimentés pour ne rien casser dans les
    écrans existants.
    """
    check = await validate_observation(
        crop_id=crop_id,
        stage_label=stage_label,
        observed_on=observed_on,
        observer=observer,
        season=season,
    )
    if not check["valid"]:
        return {"ok": False, "errors": check["errors"], "observation_id": 0}

    day = as_date(observed_on) or datetime.date.today()
    stage_id = int(check["stage_id"])

    async with rx.asession() as asession:
        crop = (
            await asession.execute(
                text(
                    """
                    SELECT c.parcel_id, COALESCE(c.season, '')
                    FROM crop c WHERE c.id = :crop_id
                    """
                ),
                {"crop_id": int(crop_id)},
            )
        ).first()
        previous = (
            await asession.execute(
                text(
                    """
                    SELECT stage_id FROM crop_stage_observation
                    WHERE crop_id = :crop_id
                    ORDER BY observed_on DESC, id DESC LIMIT 1
                    """
                ),
                {"crop_id": int(crop_id)},
            )
        ).scalar()

        observation_id = int(
            (
                await asession.execute(
                    text(
                        """
                        INSERT INTO crop_stage_observation (
                            crop_id, parcel_id, profile_id, stage_id, season,
                            observed_on, observed_at_time, observer, status,
                            source, vigour, homogeneity, anomalies,
                            diseases_observed, pests_observed, water_stress,
                            thermal_stress, comment, progress_percent
                        ) VALUES (
                            :crop_id, :parcel_id, :profile_id, :stage_id, :season,
                            :observed_on, :observed_at_time, :observer, :status,
                            :source, :vigour, :homogeneity, :anomalies,
                            :diseases_observed, :pests_observed, :water_stress,
                            :thermal_stress, :comment, :progress
                        ) RETURNING id
                        """
                    ),
                    {
                        "crop_id": int(crop_id),
                        "parcel_id": int(crop[0]) if crop else 0,
                        "profile_id": int(check["profile_id"]),
                        "stage_id": stage_id,
                        "season": season.strip()
                        or (str(crop[1]) if crop else ""),
                        "observed_on": day,
                        # Colonnes NOT NULL sans défaut serveur : valeurs
                        # neutres explicites si l'information est absente.
                        "observed_at_time": "",
                        "observer": observer.strip(),
                        "status": status,
                        "source": source,
                        "vigour": vigour,
                        "homogeneity": homogeneity,
                        "anomalies": anomalies,
                        "diseases_observed": "",
                        "pests_observed": "",
                        "water_stress": False,
                        "thermal_stress": False,
                        "comment": comment,
                        "progress": int(check["progress"]),
                    },
                )
            ).scalar()
            or 0
        )

        await asession.execute(
            text(
                """
                INSERT INTO crop_stage_change (
                    crop_id, observation_id, previous_stage_id, new_stage_id,
                    changed_on, author, comment
                ) VALUES (
                    :crop_id, :observation_id, :previous_stage_id, :new_stage_id,
                    :changed_on, :author, :comment
                )
                """
            ),
            {
                "crop_id": int(crop_id),
                "observation_id": observation_id,
                "previous_stage_id": int(previous) if previous else None,
                "new_stage_id": stage_id,
                "changed_on": day,
                "author": observer.strip(),
                "comment": comment,
            },
        )
        await asession.commit()

    return {
        "ok": True,
        "errors": [],
        "observation_id": observation_id,
        "stage_id": stage_id,
        "stage_name": str(check["stage_name"]),
        "progress": int(check["progress"]),
    }


# ---------------------------------------------------------------------------
# API stable de validation par NOM de culture (SQL brut, session fournie)
# ---------------------------------------------------------------------------


@dataclasses.dataclass(slots=True)
class StageValidationResult:
    """Résultat exploitable d'un contrôle « stade appartient-il à la culture ? ».

    Exposé volontairement sous forme d'objet stable : `is_valid`, `message` et
    `available_stages` sont les trois attributs contractuels attendus par les
    tests et les étapes suivantes. Les autres champs enrichissent la trace.
    """

    is_valid: bool = False
    message: str = ""
    available_stages: list[str] = dataclasses.field(default_factory=list)
    culture_query: str = ""
    culture_key: str = ""
    culture_name: str = ""
    matched_on: str = ""
    profile_id: int = 0
    profile_key: str = ""
    profile_name: str = ""
    stage_id: int = 0
    stage_key: str = ""
    stage_name: str = ""
    position: int = 0
    stage_count: int = 0
    progress: int = 0
    is_critical: bool = False
    bbch_code: str = ""

    def __bool__(self) -> bool:
        return self.is_valid

    def to_dict(self) -> dict[str, str | int | bool | list[str]]:
        return dataclasses.asdict(self)


# Profils actifs et tous les libellés auxquels ils peuvent être rattachés
# (culture, nom commun, espèce, nom scientifique, variété du référentiel).
PROFILE_CANDIDATES_SQL: str = """
    SELECT p.id, p.key, p.name, p.is_default,
           cu.key, cu.name, COALESCE(cu.common_name, ''),
           COALESCE(s.name, ''), COALESCE(s.scientific_name, ''),
           COALESCE(cv.name, ''),
           CASE
               WHEN p.catalog_variety_id IS NOT NULL THEN 'VARIETE'
               WHEN p.species_id IS NOT NULL THEN 'ESPECE'
               ELSE 'CULTURE'
           END AS scope
    FROM crop_phenology_profile p
    JOIN crop_culture cu ON cu.id = p.culture_id
    LEFT JOIN crop_species s ON s.id = p.species_id
    LEFT JOIN crop_catalog_variety cv ON cv.id = p.catalog_variety_id
    WHERE p.is_active = 1
    ORDER BY p.is_default DESC, p.id
"""

PROFILE_STAGE_ROWS_SQL: str = """
    SELECT st.id, st.key, st.name, st.position,
           COALESCE(st.bbch_code, ''), st.is_critical
    FROM crop_phenology_stage st
    WHERE st.profile_id = :profile_id AND st.is_active = 1
    ORDER BY st.position, st.id
"""

# Observations incohérentes : stade absent, stade rattaché à un autre profil,
# ou stade n'appartenant pas au référentiel de la culture réellement implantée.
INVALID_OBSERVATIONS_SQL: str = """
    SELECT COUNT(*)
    FROM crop_stage_observation o
    LEFT JOIN crop_phenology_stage st ON st.id = o.stage_id
    LEFT JOIN crop_phenology_profile sp ON sp.id = st.profile_id
    LEFT JOIN crop c ON c.id = o.crop_id
    LEFT JOIN crop_catalog_variety ccv ON ccv.crop_variety_id = c.variety_id
    LEFT JOIN crop_species cs ON cs.id = ccv.species_id
    WHERE o.stage_id IS NULL
       OR st.id IS NULL
       OR (o.profile_id IS NOT NULL AND st.profile_id <> o.profile_id)
       OR (cs.culture_id IS NOT NULL AND sp.culture_id <> cs.culture_id)
"""

AUDIT_MATRIX_SQL: str = """
    SELECT
        (SELECT COUNT(*) FROM crop_phenology_profile),
        (SELECT COUNT(*) FROM crop_phenology_profile WHERE is_active = 1),
        (SELECT COUNT(*) FROM crop_phenology_stage),
        (SELECT COUNT(*) FROM crop_phenology_stage WHERE is_active = 1),
        (SELECT COUNT(*) FROM crop_phenology_stage WHERE is_critical = 1),
        (SELECT COUNT(*) FROM crop_stage_recommendation),
        (SELECT COUNT(*) FROM crop_stage_recommendation WHERE is_advisory = 1),
        (SELECT COUNT(*) FROM crop_stage_observation),
        (SELECT COUNT(*) FROM crop_stage_change),
        (SELECT COUNT(*) FROM crop_stage_media),
        (SELECT COUNT(DISTINCT culture_id) FROM crop_phenology_profile),
        (SELECT COUNT(*) FROM crop_culture),
        (SELECT COUNT(*) FROM crop_phenology_profile p
           WHERE NOT EXISTS (
               SELECT 1 FROM crop_phenology_stage st
               WHERE st.profile_id = p.id AND st.is_active = 1
           )),
        (SELECT COUNT(*) FROM crop c
           WHERE NOT EXISTS (
               SELECT 1 FROM crop_stage_observation o WHERE o.crop_id = c.id
           ))
"""


async def culture_profile_candidates(
    asession, culture_name: str
) -> list[dict[str, str | int | bool]]:
    """Profils phénologiques correspondant à un libellé de culture.

    Le rapprochement est insensible à la casse et aux accents et accepte le nom
    de la culture, son nom commun, le nom de l'espèce, son nom scientifique ou
    le nom d'une variété du référentiel (« Blé dur », « Tomate », « Olivier »).
    """
    target = normalize_stage_label(culture_name)
    if not target:
        return []

    rows = (await asession.execute(text(PROFILE_CANDIDATES_SQL))).all()
    exact: list[dict[str, str | int | bool]] = []
    partial: list[dict[str, str | int | bool]] = []
    for row in rows:
        fields = {
            "CULTURE": str(row[5]),
            "NOM_COMMUN": str(row[6]),
            "ESPECE": str(row[7]),
            "NOM_SCIENTIFIQUE": str(row[8]),
            "VARIETE": str(row[9]),
            "CLE": str(row[4]),
        }
        matched_on = ""
        loose_on = ""
        for label, value in fields.items():
            normalized = normalize_stage_label(value)
            if not normalized:
                continue
            if normalized == target:
                matched_on = label
                break
            if not loose_on and (target in normalized or normalized in target):
                loose_on = label
        if not matched_on and not loose_on:
            continue
        entry: dict[str, str | int | bool] = {
            "profile_id": int(row[0]),
            "profile_key": str(row[1]),
            "profile_name": str(row[2]),
            "is_default": bool(row[3]),
            "culture_key": str(row[4]),
            "culture_name": str(row[5]),
            "scope": str(row[10]),
            "matched_on": matched_on or loose_on,
        }
        (exact if matched_on else partial).append(entry)

    ordered = exact or partial
    # La spécialisation la plus fine d'abord (variété, puis espèce, puis
    # culture), le profil par défaut ensuite.
    rank = {"VARIETE": 0, "ESPECE": 1, "CULTURE": 2}
    ordered.sort(
        key=lambda item: (
            rank.get(item["scope"], 3),
            0 if item["is_default"] else 1,
            int(item["profile_id"]),
        )
    )
    return ordered


async def _profile_stage_rows(asession, profile_id: int):
    return (
        await asession.execute(
            text(PROFILE_STAGE_ROWS_SQL), {"profile_id": int(profile_id)}
        )
    ).all()


async def validate_stage_for_crop(
    asession, culture_name: str, stage_name: str
) -> StageValidationResult:
    """Le stade demandé appartient-il au profil de la culture demandée ?

    Contrôle central du suivi phénologique, en SQL brut, sur une session
    fournie par l'appelant : « Blé dur + Tallage » est valide, « Tomate +
    Nouaison » est valide, « Olivier + Tallage » est refusé.
    """
    result = StageValidationResult(culture_query=str(culture_name).strip())
    candidates = await culture_profile_candidates(asession, culture_name)
    if not candidates:
        result.message = (
            f"Aucun profil phénologique n'est déclaré pour la culture "
            f"« {culture_name} »."
        )
        return result

    primary = candidates[0]
    result.profile_id = int(primary["profile_id"])
    result.profile_key = str(primary["profile_key"])
    result.profile_name = str(primary["profile_name"])
    result.culture_key = str(primary["culture_key"])
    result.culture_name = str(primary["culture_name"])
    result.matched_on = str(primary["matched_on"])

    stage_rows = await _profile_stage_rows(asession, result.profile_id)
    result.stage_count = len(stage_rows)
    result.available_stages = [str(row[2]) for row in stage_rows]

    target = normalize_stage_label(stage_name)
    if not target:
        result.message = "Le stade observé est obligatoire."
        return result

    for row in stage_rows:
        if target not in (
            normalize_stage_label(row[2]),
            normalize_stage_label(row[1]),
        ):
            continue
        position = int(row[3] or 0)
        result.is_valid = True
        result.stage_id = int(row[0])
        result.stage_key = str(row[1])
        result.stage_name = str(row[2])
        result.position = position
        result.progress = stage_progress_percent(position, len(stage_rows))
        result.bbch_code = str(row[4])
        result.is_critical = bool(row[5])
        result.message = (
            f"Stade « {result.stage_name} » valide pour "
            f"« {result.culture_name} » (étape {position} sur "
            f"{len(stage_rows)})."
        )
        return result

    # Repli : le stade peut appartenir à un autre profil de la même culture.
    for other in candidates[1:]:
        rows = await _profile_stage_rows(asession, int(other["profile_id"]))
        for label in (str(row[2]) for row in rows):
            if label not in result.available_stages:
                result.available_stages.append(label)
        for row in rows:
            if target in (
                normalize_stage_label(row[2]),
                normalize_stage_label(row[1]),
            ):
                position = int(row[3] or 0)
                result.is_valid = True
                result.profile_id = int(other["profile_id"])
                result.profile_key = str(other["profile_key"])
                result.profile_name = str(other["profile_name"])
                result.stage_id = int(row[0])
                result.stage_key = str(row[1])
                result.stage_name = str(row[2])
                result.position = position
                result.stage_count = len(rows)
                result.progress = stage_progress_percent(position, len(rows))
                result.bbch_code = str(row[4])
                result.is_critical = bool(row[5])
                result.message = (
                    f"Stade « {result.stage_name} » valide pour "
                    f"« {result.culture_name} » via le profil "
                    f"« {result.profile_name} »."
                )
                return result

    result.message = (
        f"Le stade « {stage_name} » n'appartient pas au référentiel "
        f"phénologique de « {result.culture_name} »."
    )
    return result


async def validate_stage_for_crop_name(
    culture_name: str, stage_name: str
) -> StageValidationResult:
    """Variante autonome : ouvre sa propre session locale."""
    await ensure_local_database()
    async with rx.asession() as asession:
        return await validate_stage_for_crop(asession, culture_name, stage_name)


async def phenology_audit_matrix(asession) -> dict[str, int]:
    """Compteurs d'audit du suivi phénologique (SQL brut, session fournie).

    Fournit notamment le nombre de profils, de stades et d'observations
    incohérentes (`invalid_observations`), attendu par les contrôles de
    cohérence des étapes suivantes.
    """
    row = (await asession.execute(text(AUDIT_MATRIX_SQL))).first()
    invalid = (await asession.execute(text(INVALID_OBSERVATIONS_SQL))).scalar()
    values = [int(value or 0) for value in (row or [0] * 14)]
    profiles = values[0]
    cultures_with_profile = values[10]
    cultures_total = values[11]
    return {
        "profiles": profiles,
        "active_profiles": values[1],
        "stages": values[2],
        "active_stages": values[3],
        "critical_stages": values[4],
        "recommendations": values[5],
        "advisory_recommendations": values[6],
        "observations": values[7],
        "changes": values[8],
        "media": values[9],
        "cultures_with_profile": cultures_with_profile,
        "cultures": cultures_with_profile,
        "cultures_total": cultures_total,
        "cultures_without_profile": max(
            0, cultures_total - cultures_with_profile
        ),
        "profiles_without_stages": values[12],
        "crops_without_observation": values[13],
        "invalid_observations": int(invalid or 0),
        "prescriptive_recommendations": max(0, values[5] - values[6]),
    }


async def phenology_audit_report() -> dict[str, int]:
    """Variante autonome de `phenology_audit_matrix`."""
    await ensure_local_database()
    async with rx.asession() as asession:
        return await phenology_audit_matrix(asession)


async def stage_duration_report(crop_id: int) -> dict[str, str | int]:
    """Durée passée dans le stade courant, qualifiée sans conclure."""
    await ensure_local_database()
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text(
                    """
                    SELECT o.observed_on, st.name, st.position,
                           COALESCE(st.duration_days_min, 0),
                           COALESCE(st.duration_days_max, 0),
                           o.progress_percent
                    FROM crop_stage_observation o
                    JOIN crop_phenology_stage st ON st.id = o.stage_id
                    WHERE o.crop_id = :crop_id
                    ORDER BY o.observed_on DESC, o.id DESC LIMIT 1
                    """
                ),
                {"crop_id": int(crop_id)},
            )
        ).first()
    if row is None:
        return {
            "has_observation": 0,
            "stage_name": "",
            "days_in_stage": 0,
            "status": "INCONNU",
            "progress": 0,
        }
    day = as_date(row[0]) or datetime.date.today()
    days = (datetime.date.today() - day).days
    return {
        "has_observation": 1,
        "stage_name": str(row[1]),
        "days_in_stage": max(0, days),
        "status": stage_duration_status(
            max(0, days), int(row[3] or 0), int(row[4] or 0)
        ),
        "progress": int(row[5] or 0),
    }

"""API internes Python réutilisables du suivi phénologique AgriPro.

Ces fonctions correspondent aux besoins exprimés dans le prompt d'intégration
(section 29 « API ») mais restent des fonctions Python appelables depuis les
états Reflex, les scripts d'administration et les tests :

* `get_culture_stages(culture)` — stades du référentiel d'une culture ;
* `get_parcel_phenology(parcel_id)` — phénologie des cultures d'une parcelle ;
* `get_crop_phenology(crop_id)` — phénologie d'une culture précise ;
* `post_observation(...)` — publication traçable d'une observation ;
* `get_phenology_history(crop_id)` — historique conservé des changements ;
* `get_phenology_calendar(crop_id)` — calendrier prévu / réel ;
* `get_stage_detail(stage_id)` — détail d'un stade (définition, surveillance,
  erreurs fréquentes, recommandations indicatives, liens Guide).

Toutes les lectures/écritures passent par du SQL brut via `rx.asession()` sur le
fichier SQLite local. Aucune recommandation n'est prescriptive : `is_advisory`
reste vrai et la source est toujours exposée.
"""

from __future__ import annotations

import datetime
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.database import ensure_local_database
from app.date_utils import as_date
from app.phenology_ops import StageContextRow, stage_context_rows
from app.phenology_reference import (
    confidence_label,
    recommendation_domain_icon,
    recommendation_domain_label,
    stage_progress_percent,
    system_label,
)
from app.phenology_validation import (
    culture_profile_candidates,
    observation_history,
    record_stage_observation,
)
from app.states.dashboard_state import MONTHS

__all__ = [
    "CalendarEntry",
    "StageDetail",
    "StageSummary",
    "get_crop_phenology",
    "get_culture_stages",
    "get_parcel_phenology",
    "get_phenology_calendar",
    "get_phenology_history",
    "get_stage_detail",
    "post_observation",
]


class StageSummary(TypedDict):
    id: int
    key: str
    name: str
    position: int
    bbch_code: str
    system_label: str
    duration_days_min: int
    duration_days_max: int
    is_critical: bool
    is_active: bool
    progress: int
    profile_id: int
    profile_name: str
    culture_name: str


class CalendarEntry(TypedDict):
    stage_id: int
    stage_name: str
    position: int
    expected_start: str
    expected_end: str
    expected_label: str
    observed_label: str
    duration_days: int
    delta_days: int
    delta_label: str
    tone: str
    state: str


class StageDetail(TypedDict):
    found: bool
    id: int
    key: str
    name: str
    position: int
    stage_count: int
    bbch_code: str
    system_label: str
    description: str
    recognition: str
    watchpoints: str
    common_errors: str
    duration_label: str
    is_critical: bool
    is_active: bool
    icon: str
    color_hex: str
    profile_id: int
    profile_name: str
    culture_name: str
    guide_article_slug: str
    guide_term_slug: str
    recommendations: list[dict[str, str | bool]]


EMPTY_STAGE_DETAIL: StageDetail = {
    "found": False,
    "id": 0,
    "key": "",
    "name": "Stade introuvable",
    "position": 0,
    "stage_count": 0,
    "bbch_code": "",
    "system_label": "",
    "description": "",
    "recognition": "",
    "watchpoints": "",
    "common_errors": "",
    "duration_label": "Durée indicative non renseignée",
    "is_critical": False,
    "is_active": False,
    "icon": "sprout",
    "color_hex": "#a3e635",
    "profile_id": 0,
    "profile_name": "",
    "culture_name": "",
    "guide_article_slug": "",
    "guide_term_slug": "",
    "recommendations": [],
}


def _fmt_date(value: object) -> str:
    day = as_date(value)
    if day is None:
        return "—"
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _duration_label(days_min: int, days_max: int) -> str:
    if days_min <= 0 and days_max <= 0:
        return "Durée indicative non renseignée"
    if days_min <= 0:
        return f"jusqu'à {days_max} j"
    if days_max <= 0:
        return f"à partir de {days_min} j"
    return f"{days_min} à {days_max} j"


def _mid_duration(days_min: int, days_max: int) -> int:
    if days_min > 0 and days_max > 0:
        return int(round((days_min + days_max) / 2))
    return max(days_min, days_max)


# ---------------------------------------------------------------------------
# GET /cultures/{id}/stages
# ---------------------------------------------------------------------------

_STAGES_SQL: str = """
    SELECT st.id, st.key, st.name, st.position, COALESCE(st.bbch_code, ''),
           st.phenological_system, COALESCE(st.duration_days_min, 0),
           COALESCE(st.duration_days_max, 0), st.is_critical, st.is_active,
           p.id, p.name, COALESCE(cu.name, '')
    FROM crop_phenology_stage st
    JOIN crop_phenology_profile p ON p.id = st.profile_id
    LEFT JOIN crop_culture cu ON cu.id = p.culture_id
    WHERE st.profile_id = :profile_id
    ORDER BY st.position, st.id
"""


# Profil actif le plus pertinent pour une culture identifiée par son id :
# 1. profil par défaut de la culture (sans spécialisation),
# 2. profil de culture sans spécialisation,
# 3. profil d'espèce rattaché à la culture,
# 4. premier profil actif de la culture (variété comprise).
_PROFILE_FOR_CULTURE_ID_SQL: str = """
    SELECT p.id
    FROM crop_phenology_profile p
    LEFT JOIN crop_species s ON s.id = p.species_id
    LEFT JOIN crop_catalog_variety cv ON cv.id = p.catalog_variety_id
    LEFT JOIN crop_species vs ON vs.id = cv.species_id
    WHERE p.is_active = 1
      AND (
            p.culture_id = :culture_id
         OR s.culture_id = :culture_id
         OR vs.culture_id = :culture_id
      )
    ORDER BY
        CASE
            WHEN p.species_id IS NULL AND p.catalog_variety_id IS NULL
                 AND p.is_default = 1 THEN 0
            WHEN p.species_id IS NULL AND p.catalog_variety_id IS NULL THEN 1
            WHEN p.species_id IS NOT NULL
                 AND p.catalog_variety_id IS NULL THEN 2
            ELSE 3
        END,
        p.id
    LIMIT 1
"""

# Repli par libellé exact ou partiel de culture (nom ou nom commun).
_CULTURE_ID_BY_NAME_SQL: str = """
    SELECT cu.id
    FROM crop_culture cu
    WHERE LOWER(cu.name) = :exact
       OR LOWER(COALESCE(cu.common_name, '')) = :exact
       OR cu.key = :exact
       OR LOWER(cu.name) LIKE :loose
       OR LOWER(COALESCE(cu.common_name, '')) LIKE :loose
    ORDER BY
        CASE WHEN LOWER(cu.name) = :exact THEN 0 ELSE 1 END,
        cu.position, cu.id
    LIMIT 1
"""


async def _resolve_profile_id(asession, culture: str | int) -> int:
    """Identifie le profil phénologique actif le plus pertinent d'une culture.

    Accepte un identifiant de culture (`int` ou chaîne numérique) comme un
    libellé (nom de culture, d'espèce ou de variété). Lecture seule : aucune
    donnée n'est créée ni dupliquée.
    """
    raw = str(culture).strip()
    culture_id = 0
    if raw.isdigit():
        culture_id = int(raw)
    else:
        candidates = await culture_profile_candidates(asession, raw)
        if candidates:
            # Le rapprochement par libellé a déjà classé variété → espèce →
            # culture : on conserve sa décision.
            return int(candidates[0]["profile_id"])
        lowered = raw.lower()
        found = (
            await asession.execute(
                text(_CULTURE_ID_BY_NAME_SQL),
                {"exact": lowered, "loose": f"%{lowered}%"},
            )
        ).scalar()
        culture_id = int(found or 0)

    if culture_id <= 0:
        return 0
    profile_id = (
        await asession.execute(
            text(_PROFILE_FOR_CULTURE_ID_SQL), {"culture_id": culture_id}
        )
    ).scalar()
    return int(profile_id or 0)


async def get_culture_stages(
    culture: str | int, include_inactive: bool = False
) -> list[StageSummary]:
    """Stades phénologiques d'une culture, par identifiant ou par libellé.

    Le profil retenu est le profil actif le plus pertinent, même lorsque seule
    une spécialisation espèce ou variété existe.
    """
    await ensure_local_database()
    async with rx.asession() as asession:
        profile_id = await _resolve_profile_id(asession, culture)
        if profile_id <= 0:
            return []
        rows = (
            await asession.execute(
                text(_STAGES_SQL), {"profile_id": profile_id}
            )
        ).all()

    active_total = len([row for row in rows if bool(row[9])])
    stages: list[StageSummary] = []
    for row in rows:
        if not bool(row[9]) and not include_inactive:
            continue
        position = int(row[3] or 0)
        stages.append(
            {
                "id": int(row[0]),
                "key": str(row[1]),
                "name": str(row[2]),
                "position": position,
                "bbch_code": str(row[4]),
                "system_label": system_label(row[5]),
                "duration_days_min": int(row[6] or 0),
                "duration_days_max": int(row[7] or 0),
                "is_critical": bool(row[8]),
                "is_active": bool(row[9]),
                "progress": stage_progress_percent(position, active_total),
                "profile_id": int(row[10]),
                "profile_name": str(row[11]),
                "culture_name": str(row[12]),
            }
        )
    return stages


# ---------------------------------------------------------------------------
# GET /parcelles/{id}/phenology
# ---------------------------------------------------------------------------


async def get_parcel_phenology(parcel_id: int) -> list[StageContextRow]:
    """Phénologie de toutes les cultures suivies d'une parcelle."""
    return await stage_context_rows(parcel_id=int(parcel_id))


async def get_crop_phenology(crop_id: int) -> StageContextRow | None:
    """Phénologie d'une culture précise (stade actuel, suivant, progression)."""
    rows = await stage_context_rows()
    for row in rows:
        if row["crop_id"] == int(crop_id):
            return row
    return None


# ---------------------------------------------------------------------------
# POST /parcelles/{id}/phenology
# ---------------------------------------------------------------------------


async def post_observation(
    crop_id: int,
    stage_label: str,
    observed_on: datetime.date | str | None,
    observer: str,
    comment: str = "",
    vigour: str = "",
    homogeneity: str = "",
    anomalies: str = "",
    season: str = "",
) -> dict[str, str | int | bool | list[str]]:
    """Publie une observation validée et trace le changement de stade.

    L'historique n'est jamais purgé : le stade précédent est conservé dans
    `crop_stage_change`. Une observation invalide (stade étranger au cycle de
    la culture, date future, observateur manquant) n'écrit rien.
    """
    return await record_stage_observation(
        crop_id=int(crop_id),
        stage_label=stage_label,
        observed_on=observed_on,
        observer=observer,
        comment=comment,
        vigour=vigour,
        homogeneity=homogeneity,
        anomalies=anomalies,
        season=season,
    )


# ---------------------------------------------------------------------------
# GET /parcelles/{id}/phenology/history
# ---------------------------------------------------------------------------


async def get_phenology_history(
    crop_id: int, limit: int = 60
) -> list[dict[str, str | int]]:
    """Historique conservé des changements de stade d'une culture."""
    return await observation_history(int(crop_id), limit=limit)


# ---------------------------------------------------------------------------
# GET /cultures/{id}/phenology/calendar
# ---------------------------------------------------------------------------

_CALENDAR_CROP_SQL: str = """
    SELECT c.sowing_date, COALESCE(c.name, '')
    FROM crop c WHERE c.id = :crop_id
"""

_CALENDAR_OBS_SQL: str = """
    SELECT o.stage_id, MIN(o.observed_on)
    FROM crop_stage_observation o
    WHERE o.crop_id = :crop_id AND o.stage_id IS NOT NULL
    GROUP BY o.stage_id
"""


async def get_phenology_calendar(crop_id: int) -> list[CalendarEntry]:
    """Calendrier phénologique prévu / réel d'une culture de parcelle."""
    from app.phenology_validation import profile_for_crop, profile_stages

    await ensure_local_database()
    resolution = await profile_for_crop(int(crop_id))
    if not resolution["found"]:
        return []
    stages = await profile_stages(resolution["profile_id"])
    if not stages:
        return []

    async with rx.asession() as asession:
        crop = (
            await asession.execute(
                text(_CALENDAR_CROP_SQL), {"crop_id": int(crop_id)}
            )
        ).first()
        obs_rows = (
            await asession.execute(
                text(_CALENDAR_OBS_SQL), {"crop_id": int(crop_id)}
            )
        ).all()

    observed: dict[int, datetime.date] = {}
    for row in obs_rows:
        day = as_date(row[1])
        if day is not None:
            observed[int(row[0])] = day

    sowing = as_date(crop[0]) if crop else None
    cursor = sowing
    entries: list[CalendarEntry] = []
    last_observed_position = max(
        (stage["position"] for stage in stages if stage["id"] in observed),
        default=0,
    )
    for stage in stages:
        duration = _mid_duration(stage["days_min"], stage["days_max"])
        expected_start = cursor
        expected_end = (
            cursor + datetime.timedelta(days=duration)
            if cursor is not None and duration > 0
            else cursor
        )
        cursor = expected_end
        real = observed.get(stage["id"])
        delta = 0
        label = "Sans repère de comparaison"
        tone = "muted"
        if real is not None and expected_start is not None:
            delta = (real - expected_start).days
            if delta > 3:
                tone = "warn"
                label = f"Retard de {delta} j"
            elif delta < -3:
                tone = "info"
                label = f"Avance de {abs(delta)} j"
            else:
                tone = "good"
                label = "Conforme au repère"
        if real is not None:
            state = (
                "current"
                if stage["position"] == last_observed_position
                else "done"
            )
        else:
            state = "todo"
        entries.append(
            {
                "stage_id": stage["id"],
                "stage_name": stage["name"],
                "position": stage["position"],
                "expected_start": expected_start.isoformat()
                if expected_start
                else "",
                "expected_end": expected_end.isoformat()
                if expected_end
                else "",
                "expected_label": _fmt_date(expected_start),
                "observed_label": _fmt_date(real),
                "duration_days": duration,
                "delta_days": delta,
                "delta_label": label,
                "tone": tone,
                "state": state,
            }
        )
    return entries


# ---------------------------------------------------------------------------
# GET /phenology/stages/{id}
# ---------------------------------------------------------------------------

_STAGE_DETAIL_SQL: str = """
    SELECT st.id, st.key, st.name, st.position, COALESCE(st.bbch_code, ''),
           st.phenological_system, COALESCE(st.description, ''),
           COALESCE(st.recognition, ''), COALESCE(st.watchpoints, ''),
           COALESCE(st.common_errors, ''), COALESCE(st.duration_days_min, 0),
           COALESCE(st.duration_days_max, 0), st.is_critical, st.is_active,
           COALESCE(st.icon, 'sprout'), COALESCE(st.color_hex, '#a3e635'),
           COALESCE(st.guide_article_slug, ''), COALESCE(st.guide_term_slug, ''),
           p.id, p.name, COALESCE(cu.name, ''),
           (SELECT COUNT(*) FROM crop_phenology_stage s2
              WHERE s2.profile_id = p.id AND s2.is_active = 1)
    FROM crop_phenology_stage st
    JOIN crop_phenology_profile p ON p.id = st.profile_id
    LEFT JOIN crop_culture cu ON cu.id = p.culture_id
    WHERE st.id = :stage_id
"""

_STAGE_RECO_SQL: str = """
    SELECT r.id, r.domain, r.title, COALESCE(r.statement, ''), r.confidence,
           COALESCE(r.source, ''), r.is_advisory,
           COALESCE(r.guide_article_slug, '')
    FROM crop_stage_recommendation r
    WHERE r.stage_id = :stage_id
    ORDER BY r.position, r.id
"""


async def get_stage_detail(stage_id: int) -> StageDetail:
    """Détail complet d'un stade, recommandations indicatives incluses."""
    await ensure_local_database()
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text(_STAGE_DETAIL_SQL), {"stage_id": int(stage_id)}
            )
        ).first()
        if row is None:
            return dict(EMPTY_STAGE_DETAIL)  # type: ignore[return-value]
        recos = (
            await asession.execute(
                text(_STAGE_RECO_SQL), {"stage_id": int(stage_id)}
            )
        ).all()

    return {
        "found": True,
        "id": int(row[0]),
        "key": str(row[1]),
        "name": str(row[2]),
        "position": int(row[3] or 0),
        "stage_count": int(row[21] or 0),
        "bbch_code": str(row[4]),
        "system_label": system_label(row[5]),
        "description": str(row[6]),
        "recognition": str(row[7]),
        "watchpoints": str(row[8]),
        "common_errors": str(row[9]),
        "duration_label": _duration_label(int(row[10] or 0), int(row[11] or 0)),
        "is_critical": bool(row[12]),
        "is_active": bool(row[13]),
        "icon": str(row[14]),
        "color_hex": str(row[15]),
        "profile_id": int(row[18]),
        "profile_name": str(row[19]),
        "culture_name": str(row[20]),
        "guide_article_slug": str(row[16]),
        "guide_term_slug": str(row[17]),
        "recommendations": [
            {
                "id": int(item[0]),
                "domain": str(item[1]),
                "domain_label": recommendation_domain_label(item[1]),
                "icon": recommendation_domain_icon(item[1]),
                "title": str(item[2]),
                "statement": str(item[3]),
                "confidence_label": confidence_label(item[4]),
                "source": str(item[5]) or "Référentiel agronomique AgriPro",
                "is_advisory": bool(item[6]),
                "guide_article_slug": str(item[7]),
            }
            for item in recos
        ],
    }

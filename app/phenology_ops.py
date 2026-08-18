"""Lectures opérationnelles du suivi phénologique (SQL brut, non prescriptif).

Ce module fournit aux modules existants (traitements/interventions, irrigation,
fertilisation, récoltes, cartographie, recherche globale, audit et rapports) des
lectures contextuelles du stade actuel :

* stade actuel, stade précédent, prochain stade, progression, durée dans le
  stade et campagne, par parcelle et par culture ;
* recommandations **indicatives** rattachées au stade (jamais prescriptives,
  jamais transformées en intervention, jamais de produit phytosanitaire non
  sourcé) ;
* alertes contextuelles « à vérifier » : absence d'observation, stade critique,
  durée inhabituelle, récolte proche ;
* comparaison prévu / réel quand les dates de semis et les repères de durée
  existent ;
* index de recherche transversal (profils, stades, observations,
  recommandations, changements) ;
* compteurs d'audit et incohérences de stade.

Aucune écriture ici : uniquement des lectures via `rx.asession()`.
"""

from __future__ import annotations

import datetime
from typing import TypedDict

import reflex as rx
from sqlalchemy import bindparam, text

from app.database import ensure_local_database
from app.date_utils import as_date
from app.phenology_reference import (
    DEVIATION_INCONNU,
    confidence_label,
    deviation_label,
    deviation_tone,
    observation_status_label,
    observation_status_tone,
    recommendation_domain_icon,
    recommendation_domain_label,
    stage_duration_status,
    stage_progress_percent,
)
from app.phenology_validation import phenology_audit_matrix
from app.states.dashboard_state import MONTHS

__all__ = [
    "AlertRow",
    "PlannedRow",
    "RecoRow",
    "SearchHit",
    "StageContextRow",
    "contextual_alerts",
    "parcel_stage_map",
    "phenology_counters",
    "planned_vs_actual",
    "search_phenology",
    "stage_context_rows",
    "stage_filter_options",
    "stage_incoherences",
    "stage_recommendations_for",
]


# ---------------------------------------------------------------------------
# Types exposés au frontend
# ---------------------------------------------------------------------------


class StageContextRow(TypedDict):
    crop_id: int
    parcel_id: int
    parcel_code: str
    parcel_name: str
    crop_name: str
    season: str
    culture_name: str
    profile_name: str
    stage_id: int
    stage_name: str
    stage_position: int
    stage_count: int
    bbch: str
    previous_stage: str
    next_stage: str
    is_critical: bool
    progress: int
    progress_pct: str
    observed_label: str
    observer: str
    status_label: str
    status_tone: str
    has_observation: bool
    days_in_stage: int
    duration_label: str
    duration_tone: str
    duration_hint: str
    harvest_label: str
    days_to_harvest: int
    color: str


class RecoRow(TypedDict):
    id: int
    stage_id: int
    stage_name: str
    domain: str
    domain_label: str
    icon: str
    title: str
    statement: str
    confidence_label: str
    source: str
    is_advisory: bool


class AlertRow(TypedDict):
    key: str
    kind: str
    kind_label: str
    tone: str
    icon: str
    title: str
    message: str
    parcel_code: str
    crop_name: str
    stage_name: str
    route: str


class PlannedRow(TypedDict):
    key: str
    parcel_code: str
    crop_name: str
    stage_name: str
    expected_label: str
    observed_label: str
    delta_days: int
    delta_label: str
    tone: str


class SearchHit(TypedDict):
    kind: str
    kind_label: str
    icon: str
    title: str
    subtitle: str
    detail: str
    # Alias stable de `detail`, attendu par les consommateurs transverses.
    excerpt: str
    route: str


ALERT_LABELS: dict[str, str] = {
    "SANS_OBSERVATION": "Absence d'observation",
    "STADE_CRITIQUE": "Stade critique",
    "DUREE_INHABITUELLE": "Durée inhabituelle",
    "RECOLTE_PROCHE": "Récolte proche",
}

ALERT_ICONS: dict[str, str] = {
    "SANS_OBSERVATION": "eye-off",
    "STADE_CRITIQUE": "triangle-alert",
    "DUREE_INHABITUELLE": "timer",
    "RECOLTE_PROCHE": "wheat",
}


def _fmt_date(value: object) -> str:
    day = as_date(value)
    if day is None:
        return "—"
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


# ---------------------------------------------------------------------------
# Requêtes
# ---------------------------------------------------------------------------

# Dernière observation par culture, avec profil applicable (repli sur le profil
# de la culture du référentiel structuré) et stade suivant.
CONTEXT_SQL: str = """
    SELECT p.id, COALESCE(p.code, ''), p.name,
           c.id, COALESCE(c.name, ''), COALESCE(c.season, ''),
           c.expected_harvest_date, c.sowing_date,
           COALESCE(o.id, 0), o.observed_on, COALESCE(o.observer, ''),
           COALESCE(o.status, ''),
           COALESCE(st.id, 0), COALESCE(st.name, ''),
           COALESCE(st.position, 0), COALESCE(st.bbch_code, ''),
           COALESCE(st.is_critical, 0),
           COALESCE(st.duration_days_min, 0), COALESCE(st.duration_days_max, 0),
           COALESCE(st.color_hex, '#a3e635'),
           COALESCE(pr.id, 0), COALESCE(pr.name, ''), COALESCE(cu.name, ''),
           (SELECT COUNT(*) FROM crop_phenology_stage s2
              WHERE s2.profile_id = pr.id AND s2.is_active = 1),
           (SELECT s3.name FROM crop_phenology_stage s3
              WHERE s3.profile_id = pr.id AND s3.is_active = 1
                AND s3.position > COALESCE(st.position, 0)
              ORDER BY s3.position LIMIT 1),
           (SELECT s4.name FROM crop_phenology_stage s4
              WHERE s4.profile_id = pr.id AND s4.is_active = 1
                AND s4.position < COALESCE(st.position, 0)
              ORDER BY s4.position DESC LIMIT 1)
    FROM crop c
    JOIN parcel p ON p.id = c.parcel_id
    LEFT JOIN crop_stage_observation o ON o.id = (
        SELECT o2.id FROM crop_stage_observation o2
        WHERE o2.crop_id = c.id
        ORDER BY o2.observed_on DESC, o2.id DESC LIMIT 1
    )
    LEFT JOIN crop_phenology_stage st ON st.id = o.stage_id
    LEFT JOIN crop_catalog_variety ccv ON ccv.crop_variety_id = c.variety_id
    LEFT JOIN crop_species cs ON cs.id = ccv.species_id
    LEFT JOIN crop_phenology_profile pr ON pr.id = COALESCE(
        o.profile_id,
        (SELECT p2.id FROM crop_phenology_profile p2
           WHERE p2.is_active = 1 AND p2.culture_id = cs.culture_id
           ORDER BY p2.is_default DESC, p2.id LIMIT 1)
    )
    LEFT JOIN crop_culture cu ON cu.id = pr.culture_id
    WHERE c.status IN ('EN_COURS', 'PLANIFIEE')
    ORDER BY p.code, c.name
    LIMIT 200
"""

STAGE_OPTIONS_SQL: str = """
    SELECT st.name, COUNT(DISTINCT o.crop_id)
    FROM crop_phenology_stage st
    LEFT JOIN crop_stage_observation o ON o.stage_id = st.id
    WHERE st.is_active = 1
    GROUP BY st.name
    ORDER BY st.name
"""

PARCEL_STAGE_SQL: str = """
    SELECT p.id, COALESCE(st.name, '')
    FROM parcel p
    LEFT JOIN crop c ON c.id = (
        SELECT c2.id FROM crop c2
        WHERE c2.parcel_id = p.id AND c2.status IN ('EN_COURS', 'PLANIFIEE')
        ORDER BY CASE c2.status WHEN 'EN_COURS' THEN 0 ELSE 1 END, c2.id
        LIMIT 1
    )
    LEFT JOIN crop_stage_observation o ON o.id = (
        SELECT o2.id FROM crop_stage_observation o2
        WHERE o2.crop_id = c.id
        ORDER BY o2.observed_on DESC, o2.id DESC LIMIT 1
    )
    LEFT JOIN crop_phenology_stage st ON st.id = o.stage_id
"""

PLANNED_SQL: str = """
    SELECT COALESCE(p.code, ''), COALESCE(c.name, ''), c.sowing_date,
           st.name, o.observed_on, o.id,
           (SELECT COALESCE(SUM(
                    CASE
                        WHEN s.duration_days_min > 0 AND s.duration_days_max > 0
                            THEN (s.duration_days_min + s.duration_days_max) / 2.0
                        WHEN s.duration_days_max > 0 THEN s.duration_days_max
                        ELSE s.duration_days_min
                    END), 0)
              FROM crop_phenology_stage s
              WHERE s.profile_id = st.profile_id AND s.is_active = 1
                AND s.position <= st.position)
    FROM crop_stage_observation o
    JOIN crop c ON c.id = o.crop_id
    JOIN parcel p ON p.id = c.parcel_id
    JOIN crop_phenology_stage st ON st.id = o.stage_id
    WHERE c.sowing_date IS NOT NULL AND o.observed_on IS NOT NULL
    ORDER BY o.observed_on DESC, o.id DESC
    LIMIT 60
"""

INCOHERENCE_SQL: str = """
    SELECT COALESCE(o.id, 0), COALESCE(p.code, ''), COALESCE(c.name, ''),
           COALESCE(st.name, ''), COALESCE(spcu.name, ''), COALESCE(cu.name, ''),
           o.observed_on
    FROM crop_stage_observation o
    LEFT JOIN crop c ON c.id = o.crop_id
    LEFT JOIN parcel p ON p.id = c.parcel_id
    LEFT JOIN crop_phenology_stage st ON st.id = o.stage_id
    LEFT JOIN crop_phenology_profile sp ON sp.id = st.profile_id
    LEFT JOIN crop_culture spcu ON spcu.id = sp.culture_id
    LEFT JOIN crop_catalog_variety ccv ON ccv.crop_variety_id = c.variety_id
    LEFT JOIN crop_species cs ON cs.id = ccv.species_id
    LEFT JOIN crop_culture cu ON cu.id = cs.culture_id
    WHERE o.stage_id IS NULL
       OR st.id IS NULL
       OR (o.profile_id IS NOT NULL AND st.profile_id <> o.profile_id)
       OR (cs.culture_id IS NOT NULL AND sp.culture_id <> cs.culture_id)
    ORDER BY o.observed_on DESC, o.id DESC
    LIMIT 50
"""


async def stage_context_rows(
    stage_filter: str = "TOUS",
    search: str = "",
    parcel_id: int = 0,
) -> list[StageContextRow]:
    """Lecture contextuelle du stade par parcelle et par culture."""
    await ensure_local_database()
    async with rx.asession() as asession:
        rows = (await asession.execute(text(CONTEXT_SQL))).all()

    today = datetime.date.today()
    query = search.strip().lower()
    context: list[StageContextRow] = []
    for row in rows:
        stage_name = str(row[13])
        has_observation = int(row[12] or 0) > 0 and stage_name != ""
        if stage_filter != "TOUS":
            if stage_filter == "SANS_OBSERVATION":
                if has_observation:
                    continue
            elif stage_name != stage_filter:
                continue
        if parcel_id > 0 and int(row[0]) != parcel_id:
            continue
        haystack = " ".join(
            [
                str(row[1]),
                str(row[2]),
                str(row[4]),
                stage_name,
                str(row[22]),
            ]
        ).lower()
        if query and query not in haystack:
            continue

        position = int(row[14] or 0)
        stage_count = int(row[23] or 0)
        days_min = int(row[17] or 0)
        days_max = int(row[18] or 0)
        observed = as_date(row[9])
        days_in_stage = (today - observed).days if observed else 0
        harvest = as_date(row[6])
        deviation = (
            stage_duration_status(max(0, days_in_stage), days_min, days_max)
            if has_observation
            else DEVIATION_INCONNU
        )
        status = str(row[11])
        context.append(
            {
                "crop_id": int(row[3]),
                "parcel_id": int(row[0]),
                "parcel_code": str(row[1]) or "—",
                "parcel_name": str(row[2]),
                "crop_name": str(row[4]) or "Culture sans nom",
                "season": str(row[5]) or "—",
                "culture_name": str(row[22]) or "Culture non reliée",
                "profile_name": str(row[21]) or "Aucun profil rattaché",
                "stage_id": int(row[12] or 0),
                "stage_name": stage_name or "Aucune observation",
                "stage_position": position,
                "stage_count": stage_count,
                "bbch": str(row[15]),
                "previous_stage": str(row[25] or "") or "Début de cycle",
                "next_stage": str(row[24] or "") or "Fin de cycle",
                "is_critical": bool(row[16]),
                "progress": stage_progress_percent(position, stage_count),
                "progress_pct": f"{stage_progress_percent(position, stage_count)}%",
                "observed_label": _fmt_date(row[9]),
                "observer": str(row[10]) or "Observateur non précisé",
                "status_label": observation_status_label(status)
                if status
                else "Non observé",
                "status_tone": observation_status_tone(status)
                if status
                else "muted",
                "has_observation": has_observation,
                "days_in_stage": max(0, days_in_stage),
                "duration_label": deviation_label(deviation),
                "duration_tone": deviation_tone(deviation),
                "duration_hint": (
                    f"Repère {days_min} à {days_max} j"
                    if days_min > 0 or days_max > 0
                    else "Repère de durée non renseigné"
                ),
                "harvest_label": _fmt_date(row[6]),
                "days_to_harvest": (harvest - today).days if harvest else 0,
                "color": str(row[19]) or "#a3e635",
            }
        )
    return context


async def stage_filter_options() -> list[dict[str, str]]:
    """Options de filtre « Afficher par stade » (cartographie et rapports)."""
    await ensure_local_database()
    async with rx.asession() as asession:
        rows = (await asession.execute(text(STAGE_OPTIONS_SQL))).all()
    options: list[dict[str, str]] = [
        {"value": "SANS_OBSERVATION", "label": "Sans observation de stade"}
    ]
    for row in rows:
        name = str(row[0])
        count = int(row[1] or 0)
        options.append({"value": name, "label": f"{name} · {count}"})
    return options


async def parcel_stage_map() -> dict[str, str]:
    """Stade courant lisible par parcelle (clé = identifiant en texte)."""
    await ensure_local_database()
    async with rx.asession() as asession:
        rows = (await asession.execute(text(PARCEL_STAGE_SQL))).all()
    return {
        str(int(row[0])): (str(row[1]) or "Sans observation") for row in rows
    }


async def stage_recommendations_for(stage_ids: list[int]) -> list[RecoRow]:
    """Recommandations indicatives des stades courants (jamais prescriptives)."""
    ids = sorted({int(value) for value in stage_ids if int(value) > 0})
    if not ids:
        return []
    await ensure_local_database()
    statement = text(
        """
        SELECT r.id, r.stage_id, st.name, r.domain, r.title,
               COALESCE(r.statement, ''), r.confidence, COALESCE(r.source, ''),
               r.is_advisory
        FROM crop_stage_recommendation r
        JOIN crop_phenology_stage st ON st.id = r.stage_id
        WHERE r.stage_id IN :ids
        ORDER BY st.position, r.position, r.id
        LIMIT 60
        """
    ).bindparams(bindparam("ids", expanding=True))
    async with rx.asession() as asession:
        rows = (await asession.execute(statement, {"ids": ids})).all()
    return [
        {
            "id": int(row[0]),
            "stage_id": int(row[1]),
            "stage_name": str(row[2]),
            "domain": str(row[3]),
            "domain_label": recommendation_domain_label(row[3]),
            "icon": recommendation_domain_icon(row[3]),
            "title": str(row[4]),
            "statement": str(row[5]),
            "confidence_label": confidence_label(row[6]),
            "source": str(row[7]) or "Référentiel agronomique AgriPro",
            "is_advisory": bool(row[8]),
        }
        for row in rows
    ]


def contextual_alerts(rows: list[StageContextRow]) -> list[AlertRow]:
    """Alertes « à vérifier », sans conclusion agronomique automatique."""
    alerts: list[AlertRow] = []
    for row in rows:
        base = f"{row['parcel_code']} · {row['crop_name']}"
        if not row["has_observation"]:
            alerts.append(
                {
                    "key": f"obs-{row['crop_id']}",
                    "kind": "SANS_OBSERVATION",
                    "kind_label": ALERT_LABELS["SANS_OBSERVATION"],
                    "tone": "muted",
                    "icon": ALERT_ICONS["SANS_OBSERVATION"],
                    "title": f"{base} — aucune observation de stade",
                    "message": (
                        "Le stade réel n'est pas connu : consignez une "
                        "observation de terrain depuis la fiche parcellaire."
                    ),
                    "parcel_code": row["parcel_code"],
                    "crop_name": row["crop_name"],
                    "stage_name": row["stage_name"],
                    "route": "/parcelles",
                }
            )
        else:
            if row["is_critical"]:
                alerts.append(
                    {
                        "key": f"crit-{row['crop_id']}",
                        "kind": "STADE_CRITIQUE",
                        "kind_label": ALERT_LABELS["STADE_CRITIQUE"],
                        "tone": "warn",
                        "icon": ALERT_ICONS["STADE_CRITIQUE"],
                        "title": f"{base} — stade sensible « {row['stage_name']} »",
                        "message": (
                            "Stade signalé sensible dans le référentiel : "
                            "surveillance renforcée à apprécier sur le terrain."
                        ),
                        "parcel_code": row["parcel_code"],
                        "crop_name": row["crop_name"],
                        "stage_name": row["stage_name"],
                        "route": "/traitements",
                    }
                )
            if row["duration_tone"] in ("warn", "info"):
                alerts.append(
                    {
                        "key": f"dur-{row['crop_id']}",
                        "kind": "DUREE_INHABITUELLE",
                        "kind_label": ALERT_LABELS["DUREE_INHABITUELLE"],
                        "tone": "info",
                        "icon": ALERT_ICONS["DUREE_INHABITUELLE"],
                        "title": (
                            f"{base} — {row['days_in_stage']} j au stade "
                            f"« {row['stage_name']} »"
                        ),
                        "message": (
                            f"{row['duration_label']} ({row['duration_hint']}) : "
                            "anomalie à vérifier, aucune conclusion "
                            "agronomique automatique."
                        ),
                        "parcel_code": row["parcel_code"],
                        "crop_name": row["crop_name"],
                        "stage_name": row["stage_name"],
                        "route": "/parcelles",
                    }
                )
        if 0 < row["days_to_harvest"] <= 21:
            alerts.append(
                {
                    "key": f"harv-{row['crop_id']}",
                    "kind": "RECOLTE_PROCHE",
                    "kind_label": ALERT_LABELS["RECOLTE_PROCHE"],
                    "tone": "good",
                    "icon": ALERT_ICONS["RECOLTE_PROCHE"],
                    "title": (
                        f"{base} — récolte prévue dans "
                        f"{row['days_to_harvest']} j"
                    ),
                    "message": (
                        f"Échéance {row['harvest_label']} : vérifiez les délais "
                        "avant récolte des intrants déjà appliqués."
                    ),
                    "parcel_code": row["parcel_code"],
                    "crop_name": row["crop_name"],
                    "stage_name": row["stage_name"],
                    "route": "/traitements",
                }
            )
    return alerts


async def planned_vs_actual() -> list[PlannedRow]:
    """Comparaison prévu / réel des stades observés, quand les données existent."""
    await ensure_local_database()
    async with rx.asession() as asession:
        rows = (await asession.execute(text(PLANNED_SQL))).all()

    planned: list[PlannedRow] = []
    for row in rows:
        sowing = as_date(row[2])
        observed = as_date(row[4])
        cumulative = float(row[6] or 0)
        if sowing is None or observed is None or cumulative <= 0:
            continue
        expected = sowing + datetime.timedelta(days=int(round(cumulative)))
        delta = (observed - expected).days
        if delta > 3:
            tone = "warn"
            label = f"Retard de {delta} j"
        elif delta < -3:
            tone = "info"
            label = f"Avance de {abs(delta)} j"
        else:
            tone = "good"
            label = "Conforme au repère"
        planned.append(
            {
                "key": f"plan-{int(row[5])}",
                "parcel_code": str(row[0]) or "—",
                "crop_name": str(row[1]) or "Culture sans nom",
                "stage_name": str(row[3]),
                "expected_label": _fmt_date(expected),
                "observed_label": _fmt_date(observed),
                "delta_days": delta,
                "delta_label": label,
                "tone": tone,
            }
        )
    return planned


async def phenology_counters() -> dict[str, int]:
    """Compteurs phénologiques pour l'audit fonctionnel."""
    await ensure_local_database()
    async with rx.asession() as asession:
        return await phenology_audit_matrix(asession)


async def stage_incoherences() -> list[dict[str, str]]:
    """Incohérences de stade détectées (stade étranger au profil, etc.)."""
    await ensure_local_database()
    async with rx.asession() as asession:
        rows = (await asession.execute(text(INCOHERENCE_SQL))).all()
    issues: list[dict[str, str]] = []
    for row in rows:
        stage = str(row[3])
        profile_culture = str(row[4])
        crop_culture = str(row[5])
        if not stage:
            reason = "Observation sans stade rattaché au référentiel."
        elif (
            profile_culture and crop_culture and profile_culture != crop_culture
        ):
            reason = (
                f"Stade « {stage} » rattaché à « {profile_culture} » alors que "
                f"la culture implantée est « {crop_culture} »."
            )
        else:
            reason = (
                f"Stade « {stage} » incohérent avec le profil de l'observation."
            )
        issues.append(
            {
                "id": str(int(row[0])),
                "parcel_code": str(row[1]) or "—",
                "crop_name": str(row[2]) or "Culture inconnue",
                "stage_name": stage or "Stade absent",
                "date_label": _fmt_date(row[6]),
                "reason": reason,
            }
        )
    return issues


# ---------------------------------------------------------------------------
# Index de recherche globale
# ---------------------------------------------------------------------------

_SEARCH_QUERIES: list[tuple[str, str, str, str]] = [
    (
        "profil",
        "Profils phénologiques",
        "git-branch",
        """
        SELECT pr.name, COALESCE(cu.name, ''), COALESCE(pr.summary, '')
        FROM crop_phenology_profile pr
        LEFT JOIN crop_culture cu ON cu.id = pr.culture_id
        WHERE :all = 1
           OR LOWER(pr.name) LIKE :q OR LOWER(COALESCE(cu.name, '')) LIKE :q
           OR LOWER(COALESCE(pr.summary, '')) LIKE :q
        ORDER BY pr.id LIMIT :limit
        """,
    ),
    (
        "stade",
        "Stades du référentiel",
        "sprout",
        """
        SELECT st.name, COALESCE(pr.name, ''),
               COALESCE(NULLIF(st.description, ''), COALESCE(st.recognition, ''))
        FROM crop_phenology_stage st
        LEFT JOIN crop_phenology_profile pr ON pr.id = st.profile_id
        WHERE :all = 1
           OR LOWER(st.name) LIKE :q OR LOWER(COALESCE(st.bbch_code, '')) LIKE :q
           OR LOWER(COALESCE(st.description, '')) LIKE :q
        ORDER BY st.profile_id, st.position LIMIT :limit
        """,
    ),
    (
        "observation",
        "Observations de stade",
        "clipboard-pen",
        """
        SELECT COALESCE(st.name, 'Stade absent'),
               COALESCE(p.code, '') || ' · ' || COALESCE(c.name, ''),
               COALESCE(o.comment, '')
        FROM crop_stage_observation o
        LEFT JOIN crop_phenology_stage st ON st.id = o.stage_id
        LEFT JOIN crop c ON c.id = o.crop_id
        LEFT JOIN parcel p ON p.id = c.parcel_id
        WHERE :all = 1
           OR LOWER(COALESCE(st.name, '')) LIKE :q
           OR LOWER(COALESCE(c.name, '')) LIKE :q
           OR LOWER(COALESCE(p.code, '')) LIKE :q
           OR LOWER(COALESCE(o.observer, '')) LIKE :q
           OR LOWER(COALESCE(o.comment, '')) LIKE :q
        ORDER BY o.observed_on DESC, o.id DESC LIMIT :limit
        """,
    ),
    (
        "recommandation",
        "Opérations associées (indicatives)",
        "list-checks",
        """
        SELECT r.title, COALESCE(st.name, ''), COALESCE(r.statement, '')
        FROM crop_stage_recommendation r
        LEFT JOIN crop_phenology_stage st ON st.id = r.stage_id
        WHERE :all = 1
           OR LOWER(r.title) LIKE :q OR LOWER(COALESCE(r.statement, '')) LIKE :q
           OR LOWER(COALESCE(st.name, '')) LIKE :q
        ORDER BY r.stage_id, r.position LIMIT :limit
        """,
    ),
    (
        "changement",
        "Changements de stade",
        "history",
        """
        SELECT COALESCE(nxt.name, '') , COALESCE(prev.name, 'Premier stade'),
               COALESCE(h.comment, '')
        FROM crop_stage_change h
        LEFT JOIN crop_phenology_stage prev ON prev.id = h.previous_stage_id
        LEFT JOIN crop_phenology_stage nxt ON nxt.id = h.new_stage_id
        WHERE :all = 1
           OR LOWER(COALESCE(nxt.name, '')) LIKE :q
           OR LOWER(COALESCE(prev.name, '')) LIKE :q
           OR LOWER(COALESCE(h.author, '')) LIKE :q
           OR LOWER(COALESCE(h.comment, '')) LIKE :q
        ORDER BY h.changed_on DESC, h.id DESC LIMIT :limit
        """,
    ),
]

_SEARCH_ROUTES: dict[str, str] = {
    "profil": "/referentiel",
    "stade": "/referentiel",
    "observation": "/parcelles",
    "recommandation": "/traitements",
    "changement": "/parcelles",
}


async def search_phenology(term: str, limit: int = 12) -> list[SearchHit]:
    """Indexe profils, stades, observations, recommandations et changements."""
    await ensure_local_database()
    query = term.strip().lower()
    params = {
        "q": f"%{query}%",
        "all": 1 if not query else 0,
        "limit": int(limit),
    }
    hits: list[SearchHit] = []
    async with rx.asession() as asession:
        for kind, kind_label, icon, sql in _SEARCH_QUERIES:
            rows = (await asession.execute(text(sql), params)).all()
            for row in rows:
                detail = str(row[2]) or "Aucun détail consigné."
                hits.append(
                    {
                        "kind": kind,
                        "kind_label": kind_label,
                        "icon": icon,
                        "title": str(row[0]) or "—",
                        "subtitle": str(row[1]) or "—",
                        "detail": detail,
                        "excerpt": detail,
                        "route": _SEARCH_ROUTES.get(kind, "/parcelles"),
                    }
                )
    return hits

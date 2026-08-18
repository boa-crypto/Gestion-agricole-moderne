"""Organisation opérationnelle du module utilisateurs AgriPro.

Couche de données (aucun composant visuel) de l'organigramme agricole, de
l'espace personnel, des affectations parcelles / cultures / équipes / activités,
des workflows de validation et des permissions temporaires (délégations).

Toutes les lectures passent par le socle `agripro_*` et les tables métier
existantes (`parcel`, `crop`, `intervention`, `farm_team`) en SQL brut via
`rx.asession()`. Les écritures visent les tables physiques (`intervention`,
`role_delegation`) et sont systématiquement journalisées dans
`agripro_activity_log` après un contrôle serveur `can_user(...)`.

Convention de workflow : une intervention est considérée « validée » lorsqu'un
évènement `VALIDER` la concernant existe dans le journal d'activité. Aucune
colonne n'est ajoutée au modèle et aucune migration protégée n'est touchée.
"""

from __future__ import annotations

import datetime
import logging
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.access_control import (
    can_user,
    log_activity,
    scope_kind_icon,
    scope_kind_label,
    user_scope_summary,
)
from app.admin_users import MONTHS, Option

__all__ = [
    "AssignmentDetailRow",
    "DelegationRow",
    "OrgLevel",
    "OrgNode",
    "PersonalSummary",
    "ResponsibilityRow",
    "TaskRow",
    "TeamMemberRow",
    "complete_task",
    "create_delegation",
    "empty_node",
    "empty_personal",
    "load_assignment_filters",
    "load_assignments",
    "load_delegation_options",
    "load_delegations",
    "load_org_levels",
    "load_org_node",
    "load_pending_validations",
    "load_personal_summary",
    "load_responsibilities",
    "load_tasks",
    "load_team_members",
    "revoke_delegation",
    "validate_task",
]


INTERVENTION_STATUS_LABELS: dict[str, str] = {
    "PLANIFIEE": "Planifiée",
    "EN_COURS": "En cours",
    "REALISEE": "Terminée",
    "ANNULEE": "Annulée",
    "REPORTEE": "Reportée",
}

INTERVENTION_STATUS_TONES: dict[str, str] = {
    "PLANIFIEE": "info",
    "EN_COURS": "warn",
    "REALISEE": "good",
    "ANNULEE": "bad",
    "REPORTEE": "muted",
}

INTERVENTION_TYPE_LABELS: dict[str, str] = {
    "SEMIS": "Semis",
    "PLANTATION": "Plantation",
    "FERTILISATION": "Fertilisation",
    "TRAITEMENT_PHYTO": "Traitement phytosanitaire",
    "DESHERBAGE": "Désherbage",
    "IRRIGATION": "Irrigation",
    "TRAVAIL_DU_SOL": "Travail du sol",
    "OBSERVATION": "Observation",
    "RECOLTE": "Récolte",
    "AUTRE": "Autre",
}

INTERVENTION_TYPE_ICONS: dict[str, str] = {
    "SEMIS": "sprout",
    "PLANTATION": "shovel",
    "FERTILISATION": "flask-conical",
    "TRAITEMENT_PHYTO": "spray-can",
    "DESHERBAGE": "scissors",
    "IRRIGATION": "droplets",
    "TRAVAIL_DU_SOL": "tractor",
    "OBSERVATION": "eye",
    "RECOLTE": "wheat",
    "AUTRE": "clipboard-list",
}

DELEGATION_STATUS_LABELS: dict[str, str] = {
    "PLANIFIEE": "Planifiée",
    "ACTIVE": "Active",
    "EXPIREE": "Expirée",
    "REVOQUEE": "Révoquée",
}

DELEGATION_STATUS_TONES: dict[str, str] = {
    "PLANIFIEE": "info",
    "ACTIVE": "good",
    "EXPIREE": "muted",
    "REVOQUEE": "bad",
}

# Étiquettes de rang de l'organigramme agricole (du sommet au terrain).
LEVEL_LABELS: dict[int, str] = {
    0: "Direction de l'exploitation",
    1: "Encadrement & responsables",
    2: "Chefs d'équipe",
    3: "Terrain",
}


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class OrgNode(TypedDict):
    id: int
    matricule: str
    name: str
    initials: str
    seed: str
    role_label: str
    role_icon: str
    role_color: str
    role_level: int
    function_label: str
    team_label: str
    sector: str
    status: str
    status_tone: str
    manager_id: int
    manager_label: str
    depth: int
    reports: int
    parcels: int


class OrgLevel(TypedDict):
    depth: int
    label: str
    count: int
    nodes: list[OrgNode]


class TaskRow(TypedDict):
    id: int
    title: str
    type_label: str
    icon: str
    status: str
    status_label: str
    tone: str
    parcel: str
    crop: str
    operator: str
    when: str
    area: float
    validated: bool
    can_close: bool
    can_validate: bool


class TeamMemberRow(TypedDict):
    id: int
    name: str
    seed: str
    initials: str
    role_in_team: str
    role_label: str
    status_tone: str


class ResponsibilityRow(TypedDict):
    label: str
    icon: str
    detail: str
    kind: str


class AssignmentDetailRow(TypedDict):
    id: int
    user_id: int
    user_label: str
    seed: str
    initials: str
    role_label: str
    parcel: str
    crop: str
    team: str
    team_key: str
    activity: str
    sector: str
    season: str
    responsible: bool
    period: str


class DelegationRow(TypedDict):
    id: int
    delegator_label: str
    delegate_label: str
    delegate_seed: str
    role_label: str
    scope_label: str
    scope_icon: str
    target: str
    reason: str
    authorized_by: str
    start_label: str
    end_label: str
    status: str
    status_label: str
    tone: str
    days_left: int
    is_open: bool


class PersonalSummary(TypedDict):
    # `id` est un alias stable de `user_id` : le frontend et les contrôles
    # d'organisation s'appuient toujours sur la présence de cette clé.
    id: int
    user_id: int
    matricule: str
    name: str
    initials: str
    seed: str
    role_label: str
    function_label: str
    team_label: str
    sector: str
    farm_key: str
    scope_label: str
    has_full_scope: bool
    tasks_total: int
    tasks_open: int
    tasks_done: int
    validations_pending: int
    parcels: int
    crops: int
    teams: int
    activities: int
    delegations: int


def empty_node() -> OrgNode:
    return {
        "id": 0,
        "matricule": "—",
        "name": "Aucun collaborateur sélectionné",
        "initials": "AG",
        "seed": "agripro",
        "role_label": "—",
        "role_icon": "shield",
        "role_color": "#a3e635",
        "role_level": 0,
        "function_label": "—",
        "team_label": "—",
        "sector": "—",
        "status": "INACTIF",
        "status_tone": "muted",
        "manager_id": 0,
        "manager_label": "—",
        "depth": 0,
        "reports": 0,
        "parcels": 0,
    }


def empty_personal() -> PersonalSummary:
    return {
        "id": 0,
        "user_id": 0,
        "matricule": "—",
        "name": "Aucun profil chargé",
        "initials": "AG",
        "seed": "agripro",
        "role_label": "—",
        "function_label": "—",
        "team_label": "—",
        "sector": "—",
        "farm_key": "—",
        "scope_label": "—",
        "has_full_scope": False,
        "tasks_total": 0,
        "tasks_open": 0,
        "tasks_done": 0,
        "validations_pending": 0,
        "parcels": 0,
        "crops": 0,
        "teams": 0,
        "activities": 0,
        "delegations": 0,
    }


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------


def _fmt_day(value: object) -> str:
    from app.date_utils import as_date

    day = as_date(value)
    if day is None:
        return "—"
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _text(value: object, fallback: str = "—") -> str:
    cleaned = str(value or "").strip()
    return cleaned or fallback


def _initials(name: str) -> str:
    parts = [p for p in str(name or "").split(" ") if p]
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[1][0]}".upper()
    if parts:
        return parts[0][:2].upper()
    return "AG"


async def _scope(user_id: int) -> tuple[bool, list[int]]:
    """(périmètre global, identifiants de parcelles autorisées)."""
    if user_id <= 0:
        return False, []
    summary = await user_scope_summary(user_id)
    return bool(summary["has_full_scope"]), [int(p) for p in summary["parcels"]]


def _parcel_clause(full_scope: bool, parcels: list[int]) -> str:
    if full_scope:
        return "1=1"
    if not parcels:
        return "1=0"
    ids = ",".join(str(int(pid)) for pid in parcels)
    return f"i.parcel_id IN ({ids})"


_VALIDATED_SQL: str = """
    (SELECT COUNT(*) FROM agripro_activity_log l
      WHERE l.object_type = 'INTERVENTION' AND l.action = 'VALIDER'
        AND l.object_id = i.id)
"""


# ---------------------------------------------------------------------------
# Organigramme agricole
# ---------------------------------------------------------------------------

_ORG_SQL: str = """
    SELECT u.id, COALESCE(u.matricule, ''), u.full_name,
           COALESCE(u.manager_id, 0), COALESCE(r.label, ''),
           COALESCE(r.icon, 'shield'), COALESCE(r.color_hex, '#a3e635'),
           COALESCE(r.level, 0), COALESCE(f.label, ''),
           COALESCE(t.name, ''), COALESCE(u.sector, ''), u.status,
           COALESCE(u.photo_seed, u.matricule),
           (SELECT COUNT(*) FROM agripro_user c WHERE c.manager_id = u.id),
           (SELECT COUNT(DISTINCT a.parcel_id) FROM agripro_assignment a
             WHERE a.user_id = u.id AND a.parcel_id IS NOT NULL)
    FROM agripro_user u
    LEFT JOIN agripro_role r ON r.id = u.role_id
    LEFT JOIN agripro_function f ON f.id = u.function_id
    LEFT JOIN agripro_team t ON t.id = u.team_id
    ORDER BY COALESCE(r.level, 0) DESC, u.full_name
"""

_STATUS_TONES: dict[str, str] = {
    "ACTIF": "good",
    "INACTIF": "muted",
    "SUSPENDU": "bad",
    "ARCHIVE": "muted",
    "EN_ATTENTE": "warn",
}


async def _org_nodes() -> list[OrgNode]:
    async with rx.asession() as asession:
        rows = (await asession.execute(text(_ORG_SQL))).all()

    names = {int(row[0]): str(row[2]).strip() for row in rows}
    managers = {int(row[0]): int(row[3] or 0) for row in rows}

    def depth_of(node_id: int) -> int:
        depth = 0
        current = managers.get(node_id, 0)
        seen: set[int] = {node_id}
        while current and current not in seen and depth < 8:
            seen.add(current)
            depth += 1
            current = managers.get(current, 0)
        return depth

    nodes: list[OrgNode] = []
    for row in rows:
        node_id = int(row[0])
        status = str(row[11] or "INACTIF")
        nodes.append(
            {
                "id": node_id,
                "matricule": _text(row[1]),
                "name": _text(row[2]),
                "initials": _initials(row[2] or ""),
                "seed": _text(row[12], row[1] or "agripro"),
                "role_label": _text(row[4]),
                "role_icon": str(row[5] or "shield"),
                "role_color": str(row[6] or "#a3e635"),
                "role_level": int(row[7] or 0),
                "function_label": _text(row[8]),
                "team_label": _text(row[9], "Sans équipe"),
                "sector": _text(row[10], "Siège"),
                "status": status,
                "status_tone": _STATUS_TONES.get(status, "muted"),
                "manager_id": int(row[3] or 0),
                "manager_label": names.get(int(row[3] or 0), "—") or "—",
                "depth": depth_of(node_id),
                "reports": int(row[13] or 0),
                "parcels": int(row[14] or 0),
            }
        )
    return nodes


async def load_org_levels() -> list[OrgLevel]:
    """Organigramme agricole regroupé par rang hiérarchique."""
    nodes = await _org_nodes()
    grouped: dict[int, list[OrgNode]] = {}
    for node in nodes:
        grouped.setdefault(node["depth"], []).append(node)
    levels: list[OrgLevel] = []
    for depth in sorted(grouped.keys()):
        items = sorted(
            grouped[depth],
            key=lambda item: (-item["role_level"], item["name"]),
        )
        levels.append(
            {
                "depth": depth,
                "label": LEVEL_LABELS.get(depth, f"Niveau {depth + 1}"),
                "count": len(items),
                "nodes": items,
            }
        )
    return levels


async def load_org_node(user_id: int) -> OrgNode:
    """Nœud unique de l'organigramme (fiche condensée).

    La clé `id` est toujours présente et cohérente avec l'identifiant demandé :
    si le collaborateur est introuvable, un nœud vide est renvoyé en conservant
    l'identifiant sollicité afin que l'interface reste synchronisée.
    """
    if user_id <= 0:
        return empty_node()
    for node in await _org_nodes():
        if node["id"] == int(user_id):
            return node
    fallback = empty_node()
    fallback["id"] = int(user_id)
    return fallback


# ---------------------------------------------------------------------------
# Espace personnel : tâches, validations, équipe, responsabilités
# ---------------------------------------------------------------------------


async def load_tasks(user_id: int, limit: int = 24) -> list[TaskRow]:
    """Tâches et interventions du périmètre agricole d'un utilisateur."""
    if user_id <= 0:
        return []
    full_scope, parcels = await _scope(user_id)
    clause = _parcel_clause(full_scope, parcels)
    if clause == "1=0":
        return []
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(
                    f"""
                    SELECT i.id, COALESCE(i.title, ''), i.type, i.status,
                           i.scheduled_date, i.done_date,
                           COALESCE(p.code, ''), COALESCE(p.name, ''),
                           COALESCE(c.name, ''), COALESCE(i.operator, ''),
                           COALESCE(i.area_treated_ha, 0),
                           {_VALIDATED_SQL}
                    FROM intervention i
                    LEFT JOIN parcel p ON p.id = i.parcel_id
                    LEFT JOIN crop c ON c.id = i.crop_id
                    WHERE {clause}
                    ORDER BY COALESCE(i.scheduled_date, i.done_date) DESC,
                             i.id DESC
                    LIMIT {int(limit)}
                    """
                )
            )
        ).all()
    return [_task_row(row) for row in rows]


def _task_row(row) -> TaskRow:
    status = str(row[3] or "PLANIFIEE")
    kind = str(row[2] or "AUTRE")
    validated = int(row[11] or 0) > 0
    return {
        "id": int(row[0]),
        "title": _text(row[1], "Intervention"),
        "type_label": INTERVENTION_TYPE_LABELS.get(kind, kind),
        "icon": INTERVENTION_TYPE_ICONS.get(kind, "clipboard-list"),
        "status": status,
        "status_label": INTERVENTION_STATUS_LABELS.get(status, status),
        "tone": INTERVENTION_STATUS_TONES.get(status, "muted"),
        "parcel": _text(f"{row[6]} · {row[7]}".strip(" ·"), "Sans parcelle"),
        "crop": _text(row[8], "Sans culture"),
        "operator": _text(row[9], "Non affecté"),
        "when": _fmt_day(row[4] or row[5]),
        "area": float(row[10] or 0),
        "validated": validated,
        "can_close": status in ("PLANIFIEE", "EN_COURS"),
        "can_validate": status == "REALISEE" and not validated,
    }


async def load_pending_validations(
    user_id: int = 0, limit: int = 24
) -> list[TaskRow]:
    """Interventions terminées attendant une validation hiérarchique."""
    clause = "1=1"
    if user_id > 0:
        full_scope, parcels = await _scope(user_id)
        clause = _parcel_clause(full_scope, parcels)
        if clause == "1=0":
            return []
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(
                    f"""
                    SELECT i.id, COALESCE(i.title, ''), i.type, i.status,
                           i.scheduled_date, i.done_date,
                           COALESCE(p.code, ''), COALESCE(p.name, ''),
                           COALESCE(c.name, ''), COALESCE(i.operator, ''),
                           COALESCE(i.area_treated_ha, 0),
                           {_VALIDATED_SQL}
                    FROM intervention i
                    LEFT JOIN parcel p ON p.id = i.parcel_id
                    LEFT JOIN crop c ON c.id = i.crop_id
                    WHERE {clause} AND i.status = 'REALISEE'
                      AND {_VALIDATED_SQL} = 0
                    ORDER BY COALESCE(i.done_date, i.scheduled_date) DESC,
                             i.id DESC
                    LIMIT {int(limit)}
                    """
                )
            )
        ).all()
    return [_task_row(row) for row in rows]


async def load_team_members(team_id: int) -> list[TeamMemberRow]:
    """Membres de l'équipe agricole d'un utilisateur."""
    if team_id <= 0:
        return []
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(
                    """
                    SELECT u.id, u.full_name,
                           COALESCE(u.photo_seed, u.matricule),
                           COALESCE(m.role_in_team, 'Membre'),
                           COALESCE(r.label, ''), u.status
                    FROM agripro_team_member m
                    JOIN agripro_user u ON u.id = m.user_id
                    LEFT JOIN agripro_role r ON r.id = u.role_id
                    WHERE m.team_id = :tid
                    ORDER BY COALESCE(r.level, 0) DESC, u.full_name
                    LIMIT 40
                    """
                ),
                {"tid": team_id},
            )
        ).all()
    return [
        {
            "id": int(row[0]),
            "name": _text(row[1]),
            "seed": _text(row[2], "agripro"),
            "initials": _initials(row[1] or ""),
            "role_in_team": _text(row[3], "Membre"),
            "role_label": _text(row[4]),
            "status_tone": _STATUS_TONES.get(row[5] or "", "muted"),
        }
        for row in rows
    ]


async def load_responsibilities(user_id: int) -> list[ResponsibilityRow]:
    """Responsabilités agricoles : périmètres, équipes menées, affectations."""
    if user_id <= 0:
        return []
    items: list[ResponsibilityRow] = []
    async with rx.asession() as asession:
        function = (
            await asession.execute(
                text(
                    """
                    SELECT COALESCE(f.label, ''), COALESCE(f.mission, ''),
                           COALESCE(f.responsibilities, ''),
                           COALESCE(f.icon, 'briefcase')
                    FROM agripro_user u
                    LEFT JOIN agripro_function f ON f.id = u.function_id
                    WHERE u.id = :uid
                    """
                ),
                {"uid": user_id},
            )
        ).first()
        led_teams = (
            await asession.execute(
                text(
                    """
                    SELECT name, COALESCE(activity, ''), COALESCE(icon, 'users')
                    FROM agripro_team WHERE leader_id = :uid
                    """
                ),
                {"uid": user_id},
            )
        ).all()
        owned = (
            await asession.execute(
                text(
                    """
                    SELECT COALESCE(p.code, ''), COALESCE(p.name, ''),
                           COALESCE(a.activity, ''), COALESCE(a.season, '')
                    FROM agripro_assignment a
                    LEFT JOIN parcel p ON p.id = a.parcel_id
                    WHERE a.user_id = :uid AND a.is_responsible = 1
                    LIMIT 20
                    """
                ),
                {"uid": user_id},
            )
        ).all()
        scopes = (
            await asession.execute(
                text(
                    """
                    SELECT scope_kind, COALESCE(sector, ''),
                           COALESCE(activity, ''), COALESCE(site, '')
                    FROM agripro_scope WHERE user_id = :uid
                    LIMIT 20
                    """
                ),
                {"uid": user_id},
            )
        ).all()

    if function is not None and str(function[0]):
        items.append(
            {
                "label": _text(function[0]),
                "icon": str(function[3] or "briefcase"),
                "detail": _text(
                    function[2] or function[1], "Mission non précisée"
                ),
                "kind": "FONCTION",
            }
        )
    for row in led_teams:
        items.append(
            {
                "label": f"Responsable · {_text(row[0])}",
                "icon": str(row[2] or "users"),
                "detail": _text(row[1], "Encadrement de l'équipe"),
                "kind": "EQUIPE",
            }
        )
    for row in owned:
        items.append(
            {
                "label": _text(
                    f"{row[0]} · {row[1]}".strip(" ·"), "Parcelle confiée"
                ),
                "icon": "map",
                "detail": _text(row[2], "Activité non précisée")
                + " · campagne "
                + _text(row[3], "en cours"),
                "kind": "PARCELLE",
            }
        )
    for row in scopes:
        kind = str(row[0] or "")
        detail = " · ".join(
            [p for p in (str(row[3]), str(row[1]), str(row[2])) if p.strip()]
        )
        items.append(
            {
                "label": scope_kind_label(kind),
                "icon": scope_kind_icon(kind),
                "detail": detail or "Toute l'exploitation",
                "kind": "PERIMETRE",
            }
        )
    return items


async def load_personal_summary(user_id: int) -> PersonalSummary:
    """Synthèse de l'espace personnel d'un profil utilisateur."""
    if user_id <= 0:
        return empty_personal()
    summary = empty_personal()
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text(
                    """
                    SELECT u.id, COALESCE(u.matricule, ''), u.full_name,
                           COALESCE(u.photo_seed, u.matricule),
                           COALESCE(r.label, ''), COALESCE(f.label, ''),
                           COALESCE(t.name, ''), COALESCE(u.sector, ''),
                           COALESCE(u.farm_key, ''), COALESCE(t.id, 0)
                    FROM agripro_user u
                    LEFT JOIN agripro_role r ON r.id = u.role_id
                    LEFT JOIN agripro_function f ON f.id = u.function_id
                    LEFT JOIN agripro_team t ON t.id = u.team_id
                    WHERE u.id = :uid
                    """
                ),
                {"uid": user_id},
            )
        ).first()
        if row is None:
            return summary
        delegations = int(
            (
                await asession.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM agripro_delegation
                        WHERE delegate_id = :uid AND status = 'ACTIVE'
                        """
                    ),
                    {"uid": user_id},
                )
            ).scalar()
            or 0
        )
        crops = int(
            (
                await asession.execute(
                    text(
                        """
                        SELECT COUNT(DISTINCT crop_id)
                        FROM agripro_assignment
                        WHERE user_id = :uid AND crop_id IS NOT NULL
                        """
                    ),
                    {"uid": user_id},
                )
            ).scalar()
            or 0
        )
        activities = int(
            (
                await asession.execute(
                    text(
                        """
                        SELECT COUNT(DISTINCT activity)
                        FROM agripro_assignment
                        WHERE user_id = :uid AND COALESCE(activity, '') <> ''
                        """
                    ),
                    {"uid": user_id},
                )
            ).scalar()
            or 0
        )

    scope = await user_scope_summary(user_id)
    tasks = await load_tasks(user_id, 60)
    pending = await load_pending_validations(user_id, 60)
    summary.update(
        {
            "id": int(row[0]),
            "user_id": int(row[0]),
            "matricule": _text(row[1]),
            "name": _text(row[2]),
            "initials": _initials(row[2] or ""),
            "seed": _text(row[3], "agripro"),
            "role_label": _text(row[4]),
            "function_label": _text(row[5]),
            "team_label": _text(row[6], "Sans équipe"),
            "sector": _text(row[7], "Siège"),
            "farm_key": _text(row[8]),
            "scope_label": str(scope["scope_label"]),
            "has_full_scope": bool(scope["has_full_scope"]),
            "tasks_total": len(tasks),
            "tasks_open": len(
                [t for t in tasks if t["status"] in ("PLANIFIEE", "EN_COURS")]
            ),
            "tasks_done": len([t for t in tasks if t["validated"]]),
            "validations_pending": len(pending),
            "parcels": int(scope["parcel_count"]),
            "crops": crops,
            "teams": int(scope["team_count"]),
            "activities": activities,
            "delegations": delegations,
        }
    )
    return summary


# ---------------------------------------------------------------------------
# Workflows de validation agricoles
# ---------------------------------------------------------------------------


async def _intervention_context(
    intervention_id: int,
) -> tuple[int, str, str, str] | None:
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text(
                    """
                    SELECT COALESCE(i.parcel_id, 0), COALESCE(i.title, ''),
                           i.status, COALESCE(p.code, '')
                    FROM intervention i
                    LEFT JOIN parcel p ON p.id = i.parcel_id
                    WHERE i.id = :iid
                    """
                ),
                {"iid": intervention_id},
            )
        ).first()
    if row is None:
        return None
    return int(row[0] or 0), str(row[1]), str(row[2]), str(row[3])


async def complete_task(
    actor_id: int, intervention_id: int
) -> tuple[bool, str]:
    """Clôture une intervention (Planifiée / En cours → Terminée à valider)."""
    context = await _intervention_context(intervention_id)
    if context is None:
        return False, "Intervention introuvable."
    parcel_id, title, status, code = context
    if status not in ("PLANIFIEE", "EN_COURS"):
        return False, f"« {title} » n'est pas un chantier en cours."

    decision = await can_user(
        actor_id,
        "interventions",
        "CLOTURER",
        parcel_id=parcel_id,
        object_type="INTERVENTION",
        object_ref=str(intervention_id),
    )
    if not decision.allowed:
        return False, decision.message

    today = datetime.date.today()
    try:
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE intervention
                    SET status = 'REALISEE',
                        done_date = COALESCE(done_date, :today)
                    WHERE id = :iid
                    """
                ),
                {"iid": intervention_id, "today": today},
            )
            await asession.commit()
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
        return False, "La clôture du chantier a échoué."

    await log_activity(
        actor_id,
        "MODIFICATION",
        module="interventions",
        action="CLOTURER",
        object_type="INTERVENTION",
        object_ref=_text(code, title),
        object_id=intervention_id,
        summary=f"Clôture du chantier « {title} » : en attente de validation.",
        parcel_id=parcel_id,
    )
    return True, f"Chantier clôturé : {title}."


async def validate_task(
    actor_id: int, intervention_id: int
) -> tuple[bool, str]:
    """Valide une intervention terminée et journalise la décision."""
    context = await _intervention_context(intervention_id)
    if context is None:
        return False, "Intervention introuvable."
    parcel_id, title, status, code = context
    if status != "REALISEE":
        return (
            False,
            f"« {title} » doit d'abord être clôturée avant validation.",
        )

    async with rx.asession() as asession:
        already = int(
            (
                await asession.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM agripro_activity_log
                        WHERE object_type = 'INTERVENTION'
                          AND action = 'VALIDER' AND object_id = :iid
                        """
                    ),
                    {"iid": intervention_id},
                )
            ).scalar()
            or 0
        )
    if already:
        return False, f"« {title} » est déjà validée."

    decision = await can_user(
        actor_id,
        "interventions",
        "VALIDER",
        parcel_id=parcel_id,
        object_type="INTERVENTION",
        object_ref=str(intervention_id),
    )
    if not decision.allowed:
        return False, decision.message

    await log_activity(
        actor_id,
        "VALIDATION",
        module="interventions",
        action="VALIDER",
        object_type="INTERVENTION",
        object_ref=_text(code, title),
        object_id=intervention_id,
        summary=f"Validation du chantier « {title} » par le responsable.",
        parcel_id=parcel_id,
        is_sensitive=True,
    )
    return True, f"Intervention validée : {title}."


# ---------------------------------------------------------------------------
# Permissions temporaires (délégations)
# ---------------------------------------------------------------------------


async def load_delegations(limit: int = 40) -> list[DelegationRow]:
    """Toutes les délégations, actives, planifiées, expirées ou révoquées."""
    today = datetime.date.today()
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(
                    """
                    SELECT d.id, COALESCE(du.full_name, ''),
                           COALESCE(tu.full_name, ''),
                           COALESCE(tu.photo_seed, tu.matricule),
                           COALESCE(r.label, ''), COALESCE(d.scope_kind, ''),
                           COALESCE(p.code, ''), COALESCE(t.name, ''),
                           COALESCE(d.reason, ''),
                           COALESCE(d.authorized_by, ''),
                           d.start_date, d.end_date, d.status
                    FROM agripro_delegation d
                    LEFT JOIN agripro_user du ON du.id = d.delegator_id
                    LEFT JOIN agripro_user tu ON tu.id = d.delegate_id
                    LEFT JOIN agripro_role r ON r.id = d.role_id
                    LEFT JOIN parcel p ON p.id = d.parcel_id
                    LEFT JOIN agripro_team t ON t.id = d.team_id
                    ORDER BY CASE d.status WHEN 'ACTIVE' THEN 0
                                           WHEN 'PLANIFIEE' THEN 1
                                           ELSE 2 END,
                             d.end_date DESC
                    LIMIT :limit
                    """
                ),
                {"limit": int(limit)},
            )
        ).all()

    from app.date_utils import as_date

    items: list[DelegationRow] = []
    for row in rows:
        status = str(row[12] or "PLANIFIEE")
        end = as_date(row[11])
        kind = str(row[5] or "")
        target = " · ".join(
            [p for p in (str(row[6]), str(row[7])) if p.strip()]
        )
        items.append(
            {
                "id": int(row[0]),
                "delegator_label": _text(row[1]),
                "delegate_label": _text(row[2]),
                "delegate_seed": _text(row[3], "agripro"),
                "role_label": _text(row[4], "Permission unitaire"),
                "scope_label": scope_kind_label(kind),
                "scope_icon": scope_kind_icon(kind),
                "target": target or "Toute l'exploitation",
                "reason": _text(row[8], "Motif non précisé"),
                "authorized_by": _text(row[9], "Direction"),
                "start_label": _fmt_day(row[10]),
                "end_label": _fmt_day(row[11]),
                "status": status,
                "status_label": DELEGATION_STATUS_LABELS.get(status, status),
                "tone": DELEGATION_STATUS_TONES.get(status, "muted"),
                "days_left": (end - today).days if end is not None else 0,
                "is_open": status in ("ACTIVE", "PLANIFIEE"),
            }
        )
    return items


async def load_delegation_options() -> tuple[
    list[Option], list[Option], list[Option]
]:
    """Options du formulaire : utilisateurs, rôles, équipes."""
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(
                    """
                    SELECT 'user' AS kind, CAST(u.id AS TEXT),
                           u.full_name || ' · ' || COALESCE(u.matricule, '')
                    FROM agripro_user u WHERE u.status = 'ACTIF'
                    UNION ALL
                    SELECT 'role', CAST(r.id AS TEXT), r.label
                    FROM agripro_role r
                    UNION ALL
                    SELECT 'team', CAST(t.id AS TEXT), t.name
                    FROM agripro_team t
                    """
                )
            )
        ).all()
    users: list[Option] = []
    roles: list[Option] = []
    teams: list[Option] = []
    for row in rows:
        option: Option = {"value": str(row[1]), "label": str(row[2] or "")}
        if str(row[0]) == "user":
            users.append(option)
        elif str(row[0]) == "role":
            roles.append(option)
        else:
            teams.append(option)
    users.sort(key=lambda item: item["label"])
    roles.sort(key=lambda item: item["label"])
    teams.sort(key=lambda item: item["label"])
    return users, roles, teams


async def create_delegation(
    actor_id: int,
    delegator_id: int,
    delegate_id: int,
    role_id: int,
    scope_kind: str,
    team_id: int,
    reason: str,
    start_date: datetime.date | None,
    end_date: datetime.date | None,
) -> tuple[bool, str]:
    """Crée une permission temporaire bornée dans le temps."""
    if delegate_id <= 0 or delegator_id <= 0:
        return False, "Sélectionnez le délégant et le délégataire."
    if delegate_id == delegator_id:
        return False, "Le délégataire doit être différent du délégant."
    if role_id <= 0:
        return False, "Choisissez le rôle à déléguer."
    if start_date is None or end_date is None:
        return False, "Renseignez les dates de début et de fin."
    if end_date < start_date:
        return False, "La date de fin doit suivre la date de début."
    if not str(reason).strip():
        return False, "Le motif de la délégation est obligatoire."

    decision = await can_user(
        actor_id,
        "utilisateurs",
        "AFFECTER",
        object_type="DELEGATION",
        object_ref=str(delegate_id),
    )
    if not decision.allowed:
        return False, decision.message

    today = datetime.date.today()
    status = "ACTIVE" if start_date <= today <= end_date else "PLANIFIEE"
    if end_date < today:
        status = "EXPIREE"

    try:
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    INSERT INTO role_delegation (
                        delegator_id, delegate_id, role_id, permission_id,
                        scope_kind, parcel_id, team_id, reason, authorized_by,
                        start_date, end_date, status, notes
                    ) VALUES (
                        :did, :tid, :rid, NULL,
                        :scope_kind, NULL, :team_id, :reason, :authorized_by,
                        :start, :end, :status, ''
                    )
                    """
                ),
                {
                    "did": delegator_id,
                    "tid": delegate_id,
                    "rid": role_id,
                    "scope_kind": str(scope_kind or "EXPLOITATION"),
                    "team_id": team_id if team_id > 0 else None,
                    "reason": str(reason).strip(),
                    "authorized_by": "Administration AgriPro",
                    "start": start_date,
                    "end": end_date,
                    "status": status,
                },
            )
            names = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            (SELECT full_name FROM agripro_user WHERE id = :did),
                            (SELECT full_name FROM agripro_user WHERE id = :tid),
                            (SELECT label FROM agripro_role WHERE id = :rid)
                        """
                    ),
                    {"did": delegator_id, "tid": delegate_id, "rid": role_id},
                )
            ).first()
            await asession.commit()
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
        return False, "La création de la délégation a échoué."

    delegator = _text(names[0] if names else "")
    delegate = _text(names[1] if names else "")
    role_label = _text(names[2] if names else "")
    await log_activity(
        actor_id,
        "DELEGATION",
        module="utilisateurs",
        action="AFFECTER",
        object_type="DELEGATION",
        object_ref=delegate,
        object_id=delegate_id,
        summary=(
            f"Délégation du rôle {role_label} de {delegator} vers {delegate} "
            f"du {start_date.isoformat()} au {end_date.isoformat()} "
            f"({str(reason).strip()})."
        ),
        scope_label=scope_kind_label(scope_kind),
        team_id=team_id,
        is_sensitive=True,
    )
    return True, f"Délégation accordée à {delegate}."


async def revoke_delegation(
    actor_id: int, delegation_id: int
) -> tuple[bool, str]:
    """Révoque immédiatement une permission temporaire."""
    if delegation_id <= 0:
        return False, "Délégation inconnue."
    decision = await can_user(
        actor_id,
        "utilisateurs",
        "AFFECTER",
        object_type="DELEGATION",
        object_ref=str(delegation_id),
    )
    if not decision.allowed:
        return False, decision.message

    try:
        async with rx.asession() as asession:
            # `app_user` ne possède pas de colonne `full_name` : le nom est
            # composé depuis `first_name` / `last_name` (repli sur le matricule).
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT COALESCE(
                                   NULLIF(TRIM(COALESCE(u.first_name, '') || ' '
                                          || COALESCE(u.last_name, '')), ''),
                                   COALESCE(u.matricule, '')
                               ) AS delegate_label,
                               d.status
                        FROM role_delegation d
                        LEFT JOIN app_user u ON u.id = d.delegate_id
                        WHERE d.id = :did
                        """
                    ),
                    {"did": delegation_id},
                )
            ).first()
            if row is None:
                return False, "Délégation introuvable."
            if str(row[1]) not in ("ACTIVE", "PLANIFIEE"):
                return False, "Cette délégation n'est plus en vigueur."
            await asession.execute(
                text(
                    """
                    UPDATE role_delegation SET status = 'REVOQUEE',
                        end_date = :today
                    WHERE id = :did
                    """
                ),
                {"did": delegation_id, "today": datetime.date.today()},
            )
            await asession.commit()
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
        return False, "La révocation a échoué."

    delegate = _text(row[0])
    await log_activity(
        actor_id,
        "DELEGATION",
        module="utilisateurs",
        action="SUPPRIMER",
        object_type="DELEGATION",
        object_ref=delegate,
        object_id=delegation_id,
        summary=f"Révocation de la permission temporaire de {delegate}.",
        is_sensitive=True,
    )
    return True, f"Délégation révoquée pour {delegate}."


# ---------------------------------------------------------------------------
# Affectations parcelles / cultures / équipes / activités
# ---------------------------------------------------------------------------


async def load_assignment_filters() -> tuple[list[Option], list[Option]]:
    """Options de filtres : équipes et activités réellement affectées."""
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(
                    """
                    SELECT 'team' AS kind, t.key, t.name
                    FROM agripro_team t
                    UNION ALL
                    SELECT 'activity', a.activity, a.activity
                    FROM agripro_assignment a
                    WHERE COALESCE(a.activity, '') <> ''
                    GROUP BY a.activity
                    """
                )
            )
        ).all()
    teams: list[Option] = []
    activities: list[Option] = []
    for row in rows:
        option: Option = {
            "value": str(row[1] or ""),
            "label": str(row[2] or ""),
        }
        if not option["value"]:
            continue
        if str(row[0]) == "team":
            teams.append(option)
        else:
            activities.append(option)
    teams.sort(key=lambda item: item["label"])
    activities.sort(key=lambda item: item["label"])
    return teams, activities


async def load_assignments(
    team_key: str = "TOUTES",
    activity: str = "TOUTES",
    user_id: int = 0,
    limit: int = 80,
) -> list[AssignmentDetailRow]:
    """Affectations visibles : exploitation → secteur → parcelle → équipe."""
    clauses = ["1=1"]
    params: dict[str, str | int] = {}
    if team_key != "TOUTES":
        clauses.append("COALESCE(t.key, '') = :team_key")
        params["team_key"] = team_key
    if activity != "TOUTES":
        clauses.append("COALESCE(a.activity, '') = :activity")
        params["activity"] = activity
    if user_id > 0:
        clauses.append("a.user_id = :uid")
        params["uid"] = user_id
    where = " AND ".join(clauses)

    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(
                    f"""
                    SELECT a.id, u.id, u.full_name,
                           COALESCE(u.photo_seed, u.matricule),
                           COALESCE(r.label, ''), COALESCE(p.code, ''),
                           COALESCE(p.name, ''), COALESCE(c.name, ''),
                           COALESCE(t.name, ''), COALESCE(t.key, ''),
                           COALESCE(a.activity, ''), COALESCE(a.sector, ''),
                           COALESCE(a.season, ''), a.is_responsible,
                           a.start_date, a.end_date
                    FROM agripro_assignment a
                    JOIN agripro_user u ON u.id = a.user_id
                    LEFT JOIN agripro_role r ON r.id = u.role_id
                    LEFT JOIN parcel p ON p.id = a.parcel_id
                    LEFT JOIN crop c ON c.id = a.crop_id
                    LEFT JOIN agripro_team t ON t.id = a.team_id
                    WHERE {where}
                    ORDER BY u.full_name, a.id
                    LIMIT {int(limit)}
                    """
                ),
                params,
            )
        ).all()

    return [
        {
            "id": int(row[0]),
            "user_id": int(row[1]),
            "user_label": _text(row[2]),
            "seed": _text(row[3], "agripro"),
            "initials": _initials(row[2] or ""),
            "role_label": _text(row[4]),
            "parcel": _text(
                f"{row[5]} · {row[6]}".strip(" ·"), "Sans parcelle"
            ),
            "crop": _text(row[7], "Sans culture"),
            "team": _text(row[8], "Sans équipe"),
            "team_key": str(row[9] or ""),
            "activity": _text(row[10], "Activité non précisée"),
            "sector": _text(row[11], "Tous secteurs"),
            "season": _text(row[12], "—"),
            "responsible": bool(row[13]),
            "period": f"{_fmt_day(row[14])} → {_fmt_day(row[15])}",
        }
        for row in rows
    ]

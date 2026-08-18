"""Couche de données de l'administration des utilisateurs AgriPro.

Toutes les lectures passent par le socle `agripro_*` (vues canoniques créées par
`app/access_schema.py`) en SQL brut via `rx.asession()`. Les écritures de statut
visent la table physique `app_user` (les vues SQLite sont en lecture seule) et
sont systématiquement journalisées dans `agripro_activity_log` après un contrôle
serveur `can_user(...)`.

Ce module ne contient AUCUN composant visuel : il est directement testable.
"""

from __future__ import annotations

import datetime
import logging
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.access_control import (
    can_user,
    effective_permissions,
    expire_stale_delegations,
    log_activity,
    scope_kind_icon,
    scope_kind_label,
    user_scope_summary,
)
from app.access_reference import (
    ACCESS_MODULES,
    ACTIVITY_KINDS,
    ACTIVITY_TONES,
    FAMILY_COLORS,
    FAMILY_LABELS,
    MFA_LABELS,
    MODULE_BY_KEY,
    USER_STATUS_LABELS,
    USER_STATUS_TONES,
    action_label,
    module_label,
    role_permission_pairs,
)
from app.database import ensure_local_database
from app.seed_access import seed_access_data

__all__ = [
    "ActivityRow",
    "AdminOverview",
    "AssignmentRow",
    "FunctionRow",
    "Option",
    "PermGroup",
    "RbacRow",
    "RoleRow",
    "ScopeRow",
    "STATUS_ACTIONS",
    "TeamRow",
    "UserDetail",
    "UserRow",
    "change_user_status",
    "empty_detail",
    "empty_overview",
    "ensure_admin_data",
    "load_activity",
    "load_journal",
    "journal_kind_options",
    "load_functions",
    "load_options",
    "load_overview",
    "load_rbac",
    "load_teams",
    "load_user_detail",
    "load_users",
]

MONTHS: list[str] = [
    "janv.",
    "févr.",
    "mars",
    "avr.",
    "mai",
    "juin",
    "juil.",
    "août",
    "sept.",
    "oct.",
    "nov.",
    "déc.",
]

# Action d'administration → (statut cible, verbe journalisé, résumé).
STATUS_ACTIONS: dict[str, tuple[str, str, str]] = {
    "DESACTIVER": ("INACTIF", "Désactivation", "Compte désactivé"),
    "REACTIVER": ("ACTIF", "Réactivation", "Compte réactivé"),
    "SUSPENDRE": ("SUSPENDU", "Suspension", "Compte suspendu"),
    "ARCHIVER": ("ARCHIVE", "Archivage", "Compte archivé"),
}


class Option(TypedDict):
    value: str
    label: str


class AdminOverview(TypedDict):
    users: int
    active: int
    inactive: int
    suspended: int
    pending: int
    archived: int
    teams: int
    functions: int
    roles: int
    permissions: int
    grants: int
    sensitive: int
    parcels: int
    delegations: int
    mfa: int
    activities: int
    sensitive_events: int


class UserRow(TypedDict):
    id: int
    matricule: str
    name: str
    initials: str
    seed: str
    function_label: str
    family_label: str
    family_color: str
    role_label: str
    role_color: str
    role_icon: str
    team_label: str
    status: str
    status_label: str
    status_tone: str
    sector: str
    email: str
    phone: str
    mfa_label: str
    mfa_enabled: bool
    last_login: str
    roles_count: int
    assignments: int
    scopes: int


class UserDetail(UserRow):
    hired_on: str
    address: str
    manager_label: str
    farm_key: str
    function_mission: str
    function_responsibilities: str
    notes: str
    permission_count: int
    parcel_count: int
    team_count: int
    scope_label: str
    has_full_scope: bool
    delegation_count: int


class RoleRow(TypedDict):
    label: str
    icon: str
    color: str
    is_primary: bool
    granted_by: str
    granted_on: str


class PermGroup(TypedDict):
    module: str
    label: str
    icon: str
    route: str
    actions: list[str]
    count: int
    sensitive: bool


class ScopeRow(TypedDict):
    kind: str
    label: str
    icon: str
    detail: str
    readonly: bool


class AssignmentRow(TypedDict):
    parcel: str
    team: str
    activity: str
    sector: str
    season: str
    responsible: bool


class ActivityRow(TypedDict):
    id: int
    actor: str
    kind: str
    kind_label: str
    tone: str
    module_label: str
    action_label: str
    object_ref: str
    summary: str
    when: str
    sensitive: bool


class FunctionRow(TypedDict):
    id: int
    key: str
    label: str
    family: str
    family_label: str
    color: str
    icon: str
    mission: str
    responsibilities: str
    default_role: str
    users: int


class TeamRow(TypedDict):
    id: int
    key: str
    name: str
    code: str
    leader: str
    activity: str
    schedule: str
    sector: str
    status: str
    icon: str
    color: str
    members: int
    parcels: int


class RbacRow(TypedDict):
    module: str
    label: str
    icon: str
    route: str
    granted: list[str]
    granted_count: int
    total: int
    coverage: int
    sensitive: bool


def empty_overview() -> AdminOverview:
    return {
        "users": 0,
        "active": 0,
        "inactive": 0,
        "suspended": 0,
        "pending": 0,
        "archived": 0,
        "teams": 0,
        "functions": 0,
        "roles": 0,
        "permissions": 0,
        "grants": 0,
        "sensitive": 0,
        "parcels": 0,
        "delegations": 0,
        "mfa": 0,
        "activities": 0,
        "sensitive_events": 0,
    }


def empty_detail() -> UserDetail:
    return {
        "id": 0,
        "matricule": "—",
        "name": "Aucun utilisateur sélectionné",
        "initials": "AG",
        "seed": "agripro",
        "function_label": "—",
        "family_label": "—",
        "family_color": "#a3e635",
        "role_label": "—",
        "role_color": "#a3e635",
        "role_icon": "shield",
        "team_label": "—",
        "status": "INACTIF",
        "status_label": "Inactif",
        "status_tone": "muted",
        "sector": "—",
        "email": "—",
        "phone": "—",
        "mfa_label": "Sans MFA",
        "mfa_enabled": False,
        "last_login": "—",
        "roles_count": 0,
        "assignments": 0,
        "scopes": 0,
        "hired_on": "—",
        "address": "—",
        "manager_label": "—",
        "farm_key": "—",
        "function_mission": "",
        "function_responsibilities": "",
        "notes": "",
        "permission_count": 0,
        "parcel_count": 0,
        "team_count": 0,
        "scope_label": "—",
        "has_full_scope": False,
        "delegation_count": 0,
    }


# ---------------------------------------------------------------------------
# Utilitaires de formatage
# ---------------------------------------------------------------------------


def _fmt_day(value: object) -> str:
    from app.date_utils import as_date

    day = as_date(value)
    if day is None:
        return "—"
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _fmt_when(value: object) -> str:
    from app.date_utils import as_datetime

    moment = as_datetime(value)
    if moment is None:
        return "—"
    return (
        f"{moment.day} {MONTHS[moment.month - 1]} {moment.year} · "
        f"{moment.hour:02d}h{moment.minute:02d}"
    )


def _initials(name: str) -> str:
    parts = [p for p in str(name or "").split(" ") if p]
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[1][0]}".upper()
    if parts:
        return parts[0][:2].upper()
    return "AG"


def _text(value: object, fallback: str = "—") -> str:
    cleaned = str(value or "").strip()
    return cleaned or fallback


async def ensure_admin_data() -> None:
    """Garantit la base locale, le socle `agripro_*` et l'amorçage idempotent."""
    await ensure_local_database()
    await seed_access_data()
    await expire_stale_delegations()


# ---------------------------------------------------------------------------
# Tableau de bord
# ---------------------------------------------------------------------------

_OVERVIEW_SQL: str = """
    SELECT
        (SELECT COUNT(*) FROM agripro_user),
        (SELECT COUNT(*) FROM agripro_user WHERE status = 'ACTIF'),
        (SELECT COUNT(*) FROM agripro_user WHERE status = 'INACTIF'),
        (SELECT COUNT(*) FROM agripro_user WHERE status = 'SUSPENDU'),
        (SELECT COUNT(*) FROM agripro_user WHERE status = 'EN_ATTENTE'),
        (SELECT COUNT(*) FROM agripro_user WHERE status = 'ARCHIVE'),
        (SELECT COUNT(*) FROM agripro_team),
        (SELECT COUNT(*) FROM agripro_function),
        (SELECT COUNT(*) FROM agripro_role),
        (SELECT COUNT(*) FROM agripro_permission),
        (SELECT COUNT(*) FROM agripro_role_permission WHERE is_granted = 1),
        (SELECT COUNT(*) FROM agripro_permission WHERE is_sensitive = 1),
        (SELECT COUNT(DISTINCT parcel_id) FROM agripro_assignment
          WHERE parcel_id IS NOT NULL),
        (SELECT COUNT(*) FROM agripro_delegation WHERE status = 'ACTIVE'),
        (SELECT COUNT(*) FROM agripro_user WHERE mfa_enabled = 1),
        (SELECT COUNT(*) FROM agripro_activity_log),
        (SELECT COUNT(*) FROM agripro_activity_log WHERE is_sensitive = 1)
"""


async def load_overview() -> AdminOverview:
    """Indicateurs consolidés du socle utilisateurs (une seule requête)."""
    overview = empty_overview()
    async with rx.asession() as asession:
        row = (await asession.execute(text(_OVERVIEW_SQL))).first()
    if row is None:
        return overview
    keys = list(overview.keys())
    for index, key in enumerate(keys):
        overview[key] = int(row[index] or 0)  # type: ignore[literal-required]
    return overview


# ---------------------------------------------------------------------------
# Utilisateurs
# ---------------------------------------------------------------------------

_USER_COLUMNS: str = """
    u.id, u.matricule, u.full_name,
    COALESCE(f.label, ''), COALESCE(f.family, ''),
    COALESCE(r.label, ''), COALESCE(r.color_hex, '#a3e635'),
    COALESCE(r.icon, 'shield'), COALESCE(t.name, ''),
    u.status, COALESCE(u.sector, ''), COALESCE(u.email, ''),
    COALESCE(u.phone, ''), u.mfa_enabled, COALESCE(u.mfa_method, 'AUCUNE'),
    u.last_login_at, COALESCE(u.photo_seed, ''),
    (SELECT COUNT(*) FROM agripro_user_role ur WHERE ur.user_id = u.id),
    (SELECT COUNT(*) FROM agripro_assignment a WHERE a.user_id = u.id),
    (SELECT COUNT(*) FROM agripro_scope s WHERE s.user_id = u.id)
"""

_USER_SOURCE: str = """
    FROM agripro_user u
    LEFT JOIN agripro_function f ON f.id = u.function_id
    LEFT JOIN agripro_role r ON r.id = u.role_id
    LEFT JOIN agripro_team t ON t.id = u.team_id
"""


def _user_row(row) -> UserRow:
    family = str(row[4] or "")
    status = str(row[9] or "INACTIF")
    return {
        "id": int(row[0]),
        "matricule": _text(row[1]),
        "name": _text(row[2]),
        "initials": _initials(row[2] or ""),
        "seed": _text(row[16], row[1] or "agripro"),
        "function_label": _text(row[3]),
        "family_label": FAMILY_LABELS.get(family, "Transverse"),
        "family_color": FAMILY_COLORS.get(family, "#a3e635"),
        "role_label": _text(row[5]),
        "role_color": str(row[6] or "#a3e635"),
        "role_icon": str(row[7] or "shield"),
        "team_label": _text(row[8], "Sans équipe"),
        "status": status,
        "status_label": USER_STATUS_LABELS.get(status, status),
        "status_tone": USER_STATUS_TONES.get(status, "muted"),
        "sector": _text(row[10], "Siège"),
        "email": _text(row[11]),
        "phone": _text(row[12]),
        "mfa_label": MFA_LABELS.get(row[14] or "AUCUNE", "Sans MFA"),
        "mfa_enabled": bool(row[13]),
        "last_login": _fmt_when(row[15]),
        "roles_count": int(row[17] or 0),
        "assignments": int(row[18] or 0),
        "scopes": int(row[19] or 0),
    }


async def load_users(
    search: str = "",
    status: str = "TOUS",
    role_key: str = "TOUS",
    team_key: str = "TOUTES",
    limit: int = 120,
) -> list[UserRow]:
    """Registre filtré des utilisateurs du socle `agripro_user`."""
    clauses = ["1=1"]
    params: dict[str, str] = {}
    term = str(search or "").strip().lower()
    if term:
        clauses.append(
            "(LOWER(u.full_name) LIKE :q OR LOWER(u.matricule) LIKE :q"
            " OR LOWER(COALESCE(u.email, '')) LIKE :q"
            " OR LOWER(COALESCE(u.sector, '')) LIKE :q"
            " OR LOWER(COALESCE(f.label, '')) LIKE :q"
            " OR LOWER(COALESCE(r.label, '')) LIKE :q"
            " OR LOWER(COALESCE(t.name, '')) LIKE :q)"
        )
        params["q"] = f"%{term}%"
    if status != "TOUS":
        clauses.append("u.status = :status")
        params["status"] = status
    if role_key != "TOUS":
        clauses.append(
            "EXISTS (SELECT 1 FROM agripro_user_role ur2"
            " JOIN agripro_role r2 ON r2.id = ur2.role_id"
            " WHERE ur2.user_id = u.id AND r2.key = :role_key)"
        )
        params["role_key"] = role_key
    if team_key != "TOUTES":
        clauses.append("COALESCE(t.key, '') = :team_key")
        params["team_key"] = team_key
    where = " AND ".join(clauses)
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(
                    f"""
                    SELECT {_USER_COLUMNS}
                    {_USER_SOURCE}
                    WHERE {where}
                    ORDER BY COALESCE(r.level, 0) DESC, u.full_name
                    LIMIT {int(limit)}
                    """
                ),
                params,
            )
        ).all()
    return [_user_row(row) for row in rows]


async def load_options() -> tuple[list[Option], list[Option], list[Option]]:
    """Options de filtres : statuts, rôles, équipes (une seule requête)."""
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(
                    """
                    SELECT 'status' AS kind, status AS value, status AS label
                    FROM agripro_user GROUP BY status
                    UNION ALL
                    SELECT 'role', r.key, r.label FROM agripro_role r
                    UNION ALL
                    SELECT 'team', t.key, t.name FROM agripro_team t
                    """
                )
            )
        ).all()
    statuses: list[Option] = []
    roles: list[Option] = []
    teams: list[Option] = []
    for row in rows:
        kind = str(row[0])
        value = str(row[1] or "")
        if not value:
            continue
        if kind == "status":
            statuses.append(
                {
                    "value": value,
                    "label": USER_STATUS_LABELS.get(value, value),
                }
            )
        elif kind == "role":
            roles.append({"value": value, "label": str(row[2] or value)})
        else:
            teams.append({"value": value, "label": str(row[2] or value)})
    statuses.sort(key=lambda item: item["label"])
    roles.sort(key=lambda item: item["label"])
    teams.sort(key=lambda item: item["label"])
    return statuses, roles, teams


async def load_user_detail(
    user_id: int,
) -> tuple[
    UserDetail,
    list[RoleRow],
    list[PermGroup],
    list[ScopeRow],
    list[AssignmentRow],
]:
    """Fiche premium consolidée d'un utilisateur du socle."""
    if user_id <= 0:
        return empty_detail(), [], [], [], []

    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text(
                    f"""
                    SELECT {_USER_COLUMNS},
                           u.hired_on, COALESCE(u.address, ''),
                           COALESCE(m.full_name, ''), COALESCE(u.farm_key, ''),
                           COALESCE(f.mission, ''),
                           COALESCE(f.responsibilities, ''),
                           COALESCE(u.notes, '')
                    {_USER_SOURCE}
                    LEFT JOIN agripro_user m ON m.id = u.manager_id
                    WHERE u.id = :uid
                    """
                ),
                {"uid": user_id},
            )
        ).first()
        if row is None:
            return empty_detail(), [], [], [], []

        role_rows = (
            await asession.execute(
                text(
                    """
                    SELECT r.label, COALESCE(r.icon, 'shield'),
                           COALESCE(r.color_hex, '#a3e635'), ur.is_primary,
                           COALESCE(ur.granted_by, ''), ur.granted_on
                    FROM agripro_user_role ur
                    JOIN agripro_role r ON r.id = ur.role_id
                    WHERE ur.user_id = :uid
                    ORDER BY COALESCE(r.level, 0) DESC
                    """
                ),
                {"uid": user_id},
            )
        ).all()
        scope_rows = (
            await asession.execute(
                text(
                    """
                    SELECT s.scope_kind, COALESCE(p.code, ''),
                           COALESCE(p.name, ''), COALESCE(t.name, ''),
                           COALESCE(s.sector, ''), COALESCE(s.site, ''),
                           COALESCE(s.activity, ''), s.is_readonly
                    FROM agripro_scope s
                    LEFT JOIN parcel p ON p.id = s.parcel_id
                    LEFT JOIN agripro_team t ON t.id = s.team_id
                    WHERE s.user_id = :uid
                    ORDER BY s.scope_kind
                    """
                ),
                {"uid": user_id},
            )
        ).all()
        assign_rows = (
            await asession.execute(
                text(
                    """
                    SELECT COALESCE(p.code, ''), COALESCE(p.name, ''),
                           COALESCE(t.name, ''), COALESCE(a.activity, ''),
                           COALESCE(a.sector, ''), COALESCE(a.season, ''),
                           a.is_responsible
                    FROM agripro_assignment a
                    LEFT JOIN parcel p ON p.id = a.parcel_id
                    LEFT JOIN agripro_team t ON t.id = a.team_id
                    WHERE a.user_id = :uid
                    ORDER BY a.id
                    """
                ),
                {"uid": user_id},
            )
        ).all()

    detail: UserDetail = {
        **_user_row(row),
        "hired_on": _fmt_day(row[20]),
        "address": _text(row[21]),
        "manager_label": _text(row[22], "Sans responsable direct"),
        "farm_key": _text(row[23]),
        "function_mission": _text(row[24], ""),
        "function_responsibilities": _text(row[25], ""),
        "notes": _text(row[26], ""),
        "permission_count": 0,
        "parcel_count": 0,
        "team_count": 0,
        "scope_label": "—",
        "has_full_scope": False,
        "delegation_count": 0,
    }

    permissions = await effective_permissions(user_id)
    summary = await user_scope_summary(user_id)
    detail["permission_count"] = len(permissions)
    detail["parcel_count"] = int(summary["parcel_count"])
    detail["team_count"] = int(summary["team_count"])
    detail["scope_label"] = str(summary["scope_label"])
    detail["has_full_scope"] = bool(summary["has_full_scope"])

    async with rx.asession() as asession:
        detail["delegation_count"] = int(
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

    roles: list[RoleRow] = [
        {
            "label": _text(item[0]),
            "icon": str(item[1] or "shield"),
            "color": str(item[2] or "#a3e635"),
            "is_primary": bool(item[3]),
            "granted_by": _text(item[4], "Amorçage AgriPro"),
            "granted_on": _fmt_day(item[5]),
        }
        for item in role_rows
    ]

    grouped: dict[str, list[str]] = {}
    for key in permissions:
        module, _, action = str(key).partition(":")
        grouped.setdefault(module, []).append(action)
    groups: list[PermGroup] = []
    for spec in ACCESS_MODULES:
        actions = grouped.get(spec["key"], [])
        if not actions:
            continue
        groups.append(
            {
                "module": spec["key"],
                "label": spec["label"],
                "icon": spec["icon"],
                "route": spec["route"],
                "actions": [action_label(a) for a in actions],
                "count": len(actions),
                "sensitive": bool(spec["is_sensitive"]),
            }
        )

    scopes: list[ScopeRow] = []
    for item in scope_rows:
        kind = str(item[0] or "")
        pieces = [
            f"{item[1]} · {item[2]}" if str(item[1] or item[2]) else "",
            str(item[3] or ""),
            str(item[4] or ""),
            str(item[5] or ""),
            str(item[6] or ""),
        ]
        detail_label = (
            " · ".join([p for p in pieces if p]) or "Toute l'exploitation"
        )
        scopes.append(
            {
                "kind": kind,
                "label": scope_kind_label(kind),
                "icon": scope_kind_icon(kind),
                "detail": detail_label,
                "readonly": bool(item[7]),
            }
        )

    assignments: list[AssignmentRow] = [
        {
            "parcel": _text(
                f"{item[0]} · {item[1]}".strip(" ·"), "Sans parcelle"
            ),
            "team": _text(item[2], "Sans équipe"),
            "activity": _text(item[3], "Activité non précisée"),
            "sector": _text(item[4], "—"),
            "season": _text(item[5], "—"),
            "responsible": bool(item[6]),
        }
        for item in assign_rows
    ]

    return detail, roles, groups, scopes, assignments


# ---------------------------------------------------------------------------
# Fonctions agricoles, équipes, matrice RBAC, journal
# ---------------------------------------------------------------------------


async def load_functions(family: str = "TOUTES") -> list[FunctionRow]:
    """Bibliothèque des fonctions agricoles et leur effectif rattaché."""
    clause = "1=1" if family == "TOUTES" else "f.family = :family"
    params = {} if family == "TOUTES" else {"family": family}
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(
                    f"""
                    SELECT f.id, f.key, f.label, COALESCE(f.family, ''),
                           COALESCE(f.mission, ''),
                           COALESCE(f.responsibilities, ''),
                           COALESCE(f.default_role_key, ''),
                           COALESCE(f.icon, 'user'),
                           COALESCE(f.color_hex, '#a3e635'),
                           (SELECT COUNT(*) FROM agripro_user u
                             WHERE u.function_id = f.id)
                    FROM agripro_function f
                    WHERE {clause}
                    ORDER BY f.position, f.label
                    """
                ),
                params,
            )
        ).all()
    items: list[FunctionRow] = []
    for row in rows:
        fam = str(row[3] or "")
        items.append(
            {
                "id": int(row[0]),
                "key": str(row[1]),
                "label": _text(row[2]),
                "family": fam,
                "family_label": FAMILY_LABELS.get(fam, "Transverse"),
                "color": str(row[8] or FAMILY_COLORS.get(fam, "#a3e635")),
                "icon": str(row[7] or "user"),
                "mission": _text(row[4], ""),
                "responsibilities": _text(row[5], ""),
                "default_role": _text(row[6], "—"),
                "users": int(row[9] or 0),
            }
        )
    return items


async def load_teams() -> list[TeamRow]:
    """Cartes des équipes agricoles, responsable et parcelles couvertes."""
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(
                    """
                    SELECT t.id, t.key, t.name, COALESCE(t.code, ''),
                           COALESCE(l.full_name, ''), COALESCE(t.activity, ''),
                           COALESCE(t.schedule, ''), COALESCE(t.sector, ''),
                           t.status, COALESCE(t.icon, 'users'),
                           COALESCE(t.color_hex, '#a3e635'),
                           (SELECT COUNT(*) FROM agripro_team_member m
                             WHERE m.team_id = t.id),
                           (SELECT COUNT(DISTINCT a.parcel_id)
                             FROM agripro_assignment a
                             WHERE a.team_id = t.id AND a.parcel_id IS NOT NULL)
                    FROM agripro_team t
                    LEFT JOIN agripro_user l ON l.id = t.leader_id
                    ORDER BY t.name
                    """
                )
            )
        ).all()
    return [
        {
            "id": int(row[0]),
            "key": str(row[1]),
            "name": _text(row[2]),
            "code": _text(row[3], "—"),
            "leader": _text(row[4], "Responsable à désigner"),
            "activity": _text(row[5], "Activité non précisée"),
            "schedule": _text(row[6], "Horaires libres"),
            "sector": _text(row[7], "Tous secteurs"),
            "status": str(row[8] or "ACTIVE"),
            "icon": str(row[9] or "users"),
            "color": str(row[10] or "#a3e635"),
            "members": int(row[11] or 0),
            "parcels": int(row[12] or 0),
        }
        for row in rows
    ]


async def load_rbac(role_key: str) -> list[RbacRow]:
    """Matrice module × action réellement accordée à un rôle."""
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(
                    """
                    SELECT p.module, p.action
                    FROM agripro_role_permission rp
                    JOIN agripro_permission p ON p.id = rp.permission_id
                    JOIN agripro_role r ON r.id = rp.role_id
                    WHERE r.key = :role AND rp.is_granted = 1
                    """
                ),
                {"role": role_key},
            )
        ).all()
    granted: dict[str, set[str]] = {}
    for row in rows:
        granted.setdefault(row[0], set()).add(str(row[1]))
    matrix: list[RbacRow] = []
    for spec in ACCESS_MODULES:
        actions = granted.get(spec["key"], set())
        total = len(spec["actions"])
        ordered = [a for a in spec["actions"] if a in actions]
        matrix.append(
            {
                "module": spec["key"],
                "label": spec["label"],
                "icon": spec["icon"],
                "route": spec["route"],
                "granted": [action_label(a) for a in ordered],
                "granted_count": len(ordered),
                "total": total,
                "coverage": int(round(100 * len(ordered) / total))
                if total
                else 0,
                "sensitive": bool(spec["is_sensitive"]),
            }
        )
    return matrix


async def load_activity(user_id: int = 0, limit: int = 16) -> list[ActivityRow]:
    """Journal d'activité : utilisateur → action → objet → date."""
    clause = "1=1" if user_id <= 0 else "l.user_id = :uid"
    params = {} if user_id <= 0 else {"uid": user_id}
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(
                    f"""
                    SELECT l.id, COALESCE(l.actor_label, 'Système'), l.kind,
                           COALESCE(l.module, ''), COALESCE(l.action, ''),
                           COALESCE(l.object_ref, ''), COALESCE(l.summary, ''),
                           COALESCE(l.occurred_at, l.created_at),
                           l.is_sensitive
                    FROM agripro_activity_log l
                    WHERE {clause}
                    ORDER BY COALESCE(l.occurred_at, l.created_at) DESC,
                             l.id DESC
                    LIMIT {int(limit)}
                    """
                ),
                params,
            )
        ).all()
    items: list[ActivityRow] = []
    for row in rows:
        kind = str(row[2] or "CONSULTATION")
        module = str(row[3] or "")
        action = str(row[4] or "")
        items.append(
            {
                "id": int(row[0]),
                "actor": _text(row[1], "Système"),
                "kind": kind,
                "kind_label": ACTIVITY_KINDS.get(kind, kind),
                "tone": ACTIVITY_TONES.get(kind, "muted"),
                "module_label": module_label(module)
                if module
                else "Transverse",
                "action_label": action_label(action) if action else "—",
                "object_ref": _text(row[5], "—"),
                "summary": _text(row[6], "Aucun détail consigné."),
                "when": _fmt_when(row[7]),
                "sensitive": bool(row[8]),
            }
        )
    return items


# ---------------------------------------------------------------------------
# Actions de statut (contrôle serveur + journal)
# ---------------------------------------------------------------------------


async def change_user_status(
    actor_id: int, user_id: int, action: str
) -> tuple[bool, str]:
    """Applique une action de statut après contrôle serveur, et la journalise."""
    key = str(action or "").strip().upper()
    if key not in STATUS_ACTIONS:
        return False, "Action de statut inconnue."
    if user_id <= 0:
        return False, "Sélectionnez d'abord un utilisateur."
    if user_id == actor_id:
        return False, "Vous ne pouvez pas modifier votre propre compte."

    target_status, verb, summary = STATUS_ACTIONS[key]

    decision = await can_user(
        actor_id,
        "utilisateurs",
        "MODIFIER",
        object_type="UTILISATEUR",
        object_ref=str(user_id),
    )
    if not decision.allowed:
        return False, decision.message

    try:
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT u.matricule, u.full_name, u.status,
                               COALESCE(r.level, 0)
                        FROM app_user u
                        LEFT JOIN app_role r ON r.id = u.primary_role_id
                        WHERE u.id = :uid
                        """
                    ),
                    {"uid": user_id},
                )
            ).first()
            if row is None:
                return False, "Utilisateur introuvable."
            matricule = str(row[0])
            full_name = str(row[1])
            current = str(row[2])
            level = int(row[3] or 0)
            if current == target_status:
                return (
                    False,
                    f"{full_name} est déjà au statut "
                    f"« {USER_STATUS_LABELS.get(current, current)} ».",
                )
            if level >= 100 and key in ("SUSPENDRE", "ARCHIVER", "DESACTIVER"):
                return (
                    False,
                    "Le compte propriétaire ne peut pas être suspendu, "
                    "désactivé ni archivé.",
                )
            await asession.execute(
                text("UPDATE app_user SET status = :s WHERE id = :uid"),
                {"s": target_status, "uid": user_id},
            )
            await asession.commit()
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
        return False, "La mise à jour du statut a échoué."

    await log_activity(
        actor_id,
        "MODIFICATION",
        module="utilisateurs",
        action="MODIFIER",
        object_type="UTILISATEUR",
        object_ref=matricule,
        object_id=user_id,
        summary=(
            f"{verb} du compte {full_name} ({matricule}) : "
            f"{USER_STATUS_LABELS.get(current, current)} → "
            f"{USER_STATUS_LABELS.get(target_status, target_status)}."
        ),
        scope_label="Toute l'exploitation",
        is_sensitive=True,
    )
    return True, f"{summary} : {full_name}."


# ---------------------------------------------------------------------------
# Journal d'activité consultable et filtrable
# ---------------------------------------------------------------------------


def journal_kind_options() -> list[Option]:
    """Types d'évènements du journal, prêts pour un sélecteur."""
    return [
        {"value": key, "label": label} for key, label in ACTIVITY_KINDS.items()
    ]


def _activity_row(row) -> ActivityRow:
    kind = str(row[2] or "CONSULTATION")
    module = str(row[3] or "")
    action = str(row[4] or "")
    return {
        "id": int(row[0]),
        "actor": _text(row[1], "Système"),
        "kind": kind,
        "kind_label": ACTIVITY_KINDS.get(kind, kind),
        "tone": ACTIVITY_TONES.get(kind, "muted"),
        "module_label": module_label(module) if module else "Transverse",
        "action_label": action_label(action) if action else "—",
        "object_ref": _text(row[5], "—"),
        "summary": _text(row[6], "Aucun détail consigné."),
        "when": _fmt_when(row[7]),
        "sensitive": bool(row[8]),
    }


async def load_journal(
    kind: str = "TOUS",
    module: str = "TOUS",
    search: str = "",
    sensitive_only: bool = False,
    user_id: int = 0,
    limit: int = 60,
) -> list[ActivityRow]:
    """Journal d'activité filtré : type, module, recherche, audit sensible."""
    clauses = ["1=1"]
    params: dict[str, str | int] = {}
    if kind != "TOUS":
        clauses.append("l.kind = :kind")
        params["kind"] = kind
    if module != "TOUS":
        clauses.append("COALESCE(l.module, '') = :module")
        params["module"] = module
    if sensitive_only:
        clauses.append("l.is_sensitive = 1")
    if user_id > 0:
        clauses.append("l.user_id = :uid")
        params["uid"] = user_id
    term = str(search or "").strip().lower()
    if term:
        clauses.append(
            "(LOWER(COALESCE(l.actor_label, '')) LIKE :q"
            " OR LOWER(COALESCE(l.summary, '')) LIKE :q"
            " OR LOWER(COALESCE(l.object_ref, '')) LIKE :q"
            " OR LOWER(COALESCE(l.module, '')) LIKE :q"
            " OR LOWER(COALESCE(l.action, '')) LIKE :q)"
        )
        params["q"] = f"%{term}%"
    where = " AND ".join(clauses)
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(
                    f"""
                    SELECT l.id, COALESCE(l.actor_label, 'Système'), l.kind,
                           COALESCE(l.module, ''), COALESCE(l.action, ''),
                           COALESCE(l.object_ref, ''), COALESCE(l.summary, ''),
                           COALESCE(l.occurred_at, l.created_at),
                           l.is_sensitive
                    FROM agripro_activity_log l
                    WHERE {where}
                    ORDER BY COALESCE(l.occurred_at, l.created_at) DESC,
                             l.id DESC
                    LIMIT {int(limit)}
                    """
                ),
                params,
            )
        ).all()
    return [_activity_row(row) for row in rows]


async def today_label() -> str:
    today = datetime.date.today()
    return f"{today.day} {MONTHS[today.month - 1]} {today.year}"

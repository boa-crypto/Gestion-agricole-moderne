"""Contrôles serveur RBAC et périmètre agricole de CMS² AgriPro.

Toutes les fonctions de ce module sont **asynchrones**, écrites en SQL brut via
`rx.asession()`, et destinées à être appelées depuis les gestionnaires
d'événements Reflex : le frontend n'est jamais considéré comme une protection.

Elles répondent aux questions de sécurité du module utilisateurs :

* `effective_permissions()` : permissions effectives (rôles + délégations) ;
* `has_permission()` : une action est-elle autorisée sur un module ?
* `parcel_ids_in_scope()` / `scope_allows_parcel()` : périmètre parcellaire ;
* `scope_allows_team()` / `scope_allows_farm()` : périmètre équipe/exploitation ;
* `active_delegations()` : délégations temporaires en cours de validité ;
* `authorize()` : décision unique permission + périmètre, journalisée ;
* `log_activity()` : écriture du journal d'activité ;
* `resolve_session()` / `touch_session()` : session et MFA représentées ;
* `user_security_profile()` : synthèse prête pour les futurs écrans AgriPro.

Aucune migration protégée n'est touchée : les tables sont créées par
`init_access_tables()` sur le fichier SQLite local du projet.
"""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import logging
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.access_reference import (
    DENY_INACTIVE_USER,
    DENY_NO_PERMISSION,
    DENY_OUT_OF_SCOPE,
    DENY_REASONS,
    DENY_UNKNOWN_USER,
    SCOPE_ACTIVITE,
    SCOPE_EXPLOITATION,
    SCOPE_ICONS,
    SCOPE_LABELS,
    SCOPE_PERSONNEL,
    SCOPE_SECTEUR,
    permission_key,
)

# Libellé de repli si une clé de périmètre inconnue remonte de la base.
_FULL_SCOPE_LABEL: str = SCOPE_LABELS.get(
    SCOPE_EXPLOITATION, "Toute l'exploitation"
)
from app.database import ensure_access_tables

__all__ = [
    "AccessDecision",
    "AuthorizationResult",
    "DelegationInfo",
    "PermissionDeniedError",
    "ScopeSummary",
    "SecurityProfile",
    "active_delegations",
    "active_delegations_for_user",
    "assert_user_can",
    "authorize",
    "can_user",
    "log_access_event",
    "user_effective_permissions",
    "user_scope_summary",
    "effective_permissions",
    "expire_stale_delegations",
    "has_permission",
    "hash_token",
    "log_activity",
    "scope_kind_icon",
    "scope_kind_label",
    "parcel_ids_in_scope",
    "resolve_session",
    "scope_allows_farm",
    "scope_allows_parcel",
    "scope_allows_team",
    "touch_session",
    "user_by_matricule",
    "user_security_profile",
]

ACTIVE_STATUSES: tuple[str, ...] = ("ACTIF",)


class AuthorizationResult(TypedDict):
    """Décision de sécurité serveur, exploitable telle quelle par l'UI."""

    allowed: bool
    reason: str
    message: str
    module: str
    action: str
    permission: str
    user_id: int
    via_delegation: bool
    scope_label: str


class DelegationInfo(TypedDict):
    id: int
    delegator_id: int
    delegator_label: str
    delegate_id: int
    delegate_label: str
    role_key: str
    role_label: str
    permission_key: str
    scope_kind: str
    parcel_id: int
    team_id: int
    reason: str
    authorized_by: str
    start_label: str
    end_label: str
    days_left: int


class SecurityProfile(TypedDict):
    user_id: int
    matricule: str
    full_name: str
    email: str
    status: str
    function_key: str
    function_label: str
    role_keys: list[str]
    role_labels: list[str]
    team_key: str
    team_label: str
    farm_key: str
    sector: str
    mfa_enabled: bool
    mfa_method: str
    permission_count: int
    permissions: list[str]
    scope_kinds: list[str]
    parcel_ids: list[int]
    has_full_scope: bool
    delegation_count: int
    last_login_label: str


class PermissionDeniedError(PermissionError):
    """Refus serveur explicite d'une action AgriPro (permission ou périmètre)."""

    def __init__(self, decision: "AccessDecision") -> None:
        super().__init__(decision.message)
        self.decision = decision


@dataclasses.dataclass(frozen=True, slots=True)
class AccessDecision:
    """Décision d'accès exploitable par attribut (`.allowed`) ou par clé."""

    allowed: bool
    reason: str
    message: str
    module: str
    action: str
    permission: str
    user_id: int
    via_delegation: bool
    scope_label: str
    parcel_id: int = 0
    team_id: int = 0
    farm_key: str = ""

    def __bool__(self) -> bool:
        return self.allowed

    def __getitem__(self, key: str) -> object:
        return getattr(self, key)

    def get(self, key: str, default: object = None) -> object:
        return getattr(self, key, default)

    def as_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)


class ScopeSummary(TypedDict):
    """Synthèse stable du périmètre agricole d'un utilisateur."""

    user_id: int
    has_full_scope: bool
    farm_key: str
    farm_keys: list[str]
    sectors: list[str]
    scope_kinds: list[str]
    parcels: list[int]
    parcel_count: int
    teams: list[int]
    team_count: int
    crops: list[int]
    activities: list[str]
    scope_label: str


def _normalize_action(action: str) -> str:
    """Normalise une action (`modifier` → `MODIFIER`)."""
    return str(action or "").strip().upper().replace("-", "_")


def _normalize_module(module: str) -> str:
    """Normalise une clé de module (`Parcelles` → `parcelles`)."""
    return str(module or "").strip().lower()


def scope_kind_label(scope_kind: str) -> str:
    """Libellé lisible d'un type de périmètre agricole."""
    key = str(scope_kind or "").strip().upper()
    return SCOPE_LABELS.get(key, key or _FULL_SCOPE_LABEL)


def scope_kind_icon(scope_kind: str) -> str:
    """Icône associée à un type de périmètre agricole."""
    key = str(scope_kind or "").strip().upper()
    return SCOPE_ICONS.get(key, "shield-check")


def hash_token(raw_token: str) -> str:
    """Empreinte SHA-256 d'un jeton de session (jamais stocké en clair)."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _fmt(value: object) -> str:
    from app.date_utils import as_date

    day = as_date(value)
    return "—" if day is None else day.isoformat()


# ---------------------------------------------------------------------------
# Permissions effectives
# ---------------------------------------------------------------------------

_ROLE_PERMISSIONS_SQL: str = """
    SELECT DISTINCT p.key
    FROM app_permission p
    JOIN role_permission rp ON rp.permission_id = p.id
    JOIN user_role ur ON ur.role_id = rp.role_id
    JOIN app_user u ON u.id = ur.user_id
    WHERE ur.user_id = :uid
      AND rp.is_granted = 1
      AND u.status = 'ACTIF'
"""

# Délégations : soit un rôle entier, soit une permission unitaire.
_DELEGATED_PERMISSIONS_SQL: str = """
    SELECT DISTINCT p.key
    FROM role_delegation d
    JOIN role_permission rp ON rp.role_id = d.role_id
    JOIN app_permission p ON p.id = rp.permission_id
    WHERE d.delegate_id = :uid
      AND d.status = 'ACTIVE'
      AND rp.is_granted = 1
      AND (d.start_date IS NULL OR d.start_date <= :today)
      AND (d.end_date IS NULL OR d.end_date >= :today)
    UNION
    SELECT DISTINCT p.key
    FROM role_delegation d
    JOIN app_permission p ON p.id = d.permission_id
    WHERE d.delegate_id = :uid
      AND d.status = 'ACTIVE'
      AND (d.start_date IS NULL OR d.start_date <= :today)
      AND (d.end_date IS NULL OR d.end_date >= :today)
"""


async def _user_status(asession, user_id: int) -> str | None:
    row = (
        await asession.execute(
            text("SELECT status FROM app_user WHERE id = :uid"),
            {"uid": user_id},
        )
    ).first()
    return str(row[0]) if row is not None else None


async def effective_permissions(
    user_id: int, include_delegations: bool = True
) -> list[str]:
    """Permissions effectives (`module:ACTION`) d'un utilisateur actif."""
    await ensure_access_tables()
    today = datetime.date.today()
    async with rx.asession() as asession:
        status = await _user_status(asession, user_id)
        if status not in ACTIVE_STATUSES:
            return []
        keys = {
            str(row[0])
            for row in (
                await asession.execute(
                    text(_ROLE_PERMISSIONS_SQL), {"uid": user_id}
                )
            ).all()
        }
        if include_delegations:
            keys.update(
                str(row[0])
                for row in (
                    await asession.execute(
                        text(_DELEGATED_PERMISSIONS_SQL),
                        {"uid": user_id, "today": today},
                    )
                ).all()
            )
    return sorted(keys)


async def has_permission(user_id: int, module: str, action: str) -> bool:
    """Contrôle RBAC unitaire, délégations actives incluses."""
    wanted = permission_key(module, action)
    return wanted in await effective_permissions(user_id)


async def _has_permission_detail(
    asession, user_id: int, module: str, action: str, today: datetime.date
) -> tuple[bool, bool]:
    """(autorisé, via délégation) sans rouvrir de session."""
    wanted = permission_key(module, action)
    direct = {
        str(row[0])
        for row in (
            await asession.execute(
                text(_ROLE_PERMISSIONS_SQL), {"uid": user_id}
            )
        ).all()
    }
    if wanted in direct:
        return True, False
    delegated = {
        str(row[0])
        for row in (
            await asession.execute(
                text(_DELEGATED_PERMISSIONS_SQL),
                {"uid": user_id, "today": today},
            )
        ).all()
    }
    return wanted in delegated, wanted in delegated


# ---------------------------------------------------------------------------
# Périmètre agricole
# ---------------------------------------------------------------------------

_FULL_SCOPE_SQL: str = """
    SELECT 1 FROM access_scope
    WHERE user_id = :uid AND scope_kind = 'EXPLOITATION'
    LIMIT 1
"""

_SCOPE_PARCELS_SQL: str = """
    -- Périmètre parcellaire explicite
    SELECT s.parcel_id AS pid
    FROM access_scope s
    WHERE s.user_id = :uid AND s.parcel_id IS NOT NULL
    UNION
    -- Périmètre par secteur (localité de l'îlot)
    SELECT p.id
    FROM access_scope s
    JOIN parcel p ON LOWER(COALESCE(p.locality, '')) LIKE
                     '%' || LOWER(COALESCE(s.sector, '@@')) || '%'
    WHERE s.user_id = :uid AND s.scope_kind = 'SECTEUR'
      AND COALESCE(s.sector, '') <> ''
    UNION
    -- Périmètre par culture du référentiel de campagne
    SELECT c.parcel_id
    FROM access_scope s
    JOIN crop c ON c.id = s.crop_id
    WHERE s.user_id = :uid AND s.crop_id IS NOT NULL
    UNION
    -- Périmètre par équipe : parcelles affectées à l'équipe
    SELECT a.parcel_id
    FROM access_scope s
    JOIN user_assignment a ON a.team_id = s.team_id
    WHERE s.user_id = :uid AND s.team_id IS NOT NULL
      AND a.parcel_id IS NOT NULL
    UNION
    -- Affectations personnelles de l'utilisateur
    SELECT a.parcel_id
    FROM user_assignment a
    WHERE a.user_id = :uid AND a.parcel_id IS NOT NULL
    UNION
    -- Parcelles ouvertes par une délégation active
    SELECT d.parcel_id
    FROM role_delegation d
    WHERE d.delegate_id = :uid AND d.status = 'ACTIVE'
      AND d.parcel_id IS NOT NULL
      AND (d.start_date IS NULL OR d.start_date <= :today)
      AND (d.end_date IS NULL OR d.end_date >= :today)
"""


async def _has_full_scope(asession, user_id: int) -> bool:
    row = (
        await asession.execute(text(_FULL_SCOPE_SQL), {"uid": user_id})
    ).first()
    if row is not None:
        return True
    delegated = (
        await asession.execute(
            text(
                """
                SELECT 1 FROM role_delegation
                WHERE delegate_id = :uid AND status = 'ACTIVE'
                  AND scope_kind = 'EXPLOITATION'
                LIMIT 1
                """
            ),
            {"uid": user_id},
        )
    ).first()
    return delegated is not None


async def parcel_ids_in_scope(user_id: int) -> list[int]:
    """Identifiants de parcelles accessibles, ou `[]` si périmètre global."""
    await ensure_access_tables()
    today = datetime.date.today()
    async with rx.asession() as asession:
        if await _has_full_scope(asession, user_id):
            rows = (
                await asession.execute(
                    text("SELECT id FROM parcel ORDER BY id")
                )
            ).all()
            return [int(row[0]) for row in rows]
        rows = (
            await asession.execute(
                text(_SCOPE_PARCELS_SQL), {"uid": user_id, "today": today}
            )
        ).all()
    return sorted({int(row[0]) for row in rows if row[0] is not None})


async def scope_allows_parcel(user_id: int, parcel_id: int) -> bool:
    """Vrai si l'utilisateur peut accéder à cette parcelle."""
    if parcel_id <= 0:
        return True
    await ensure_access_tables()
    today = datetime.date.today()
    async with rx.asession() as asession:
        if await _has_full_scope(asession, user_id):
            return True
        row = (
            await asession.execute(
                text(
                    f"SELECT 1 FROM ({_SCOPE_PARCELS_SQL}) scoped "
                    "WHERE scoped.pid = :pid LIMIT 1"
                ),
                {"uid": user_id, "today": today, "pid": parcel_id},
            )
        ).first()
    return row is not None


async def scope_allows_team(user_id: int, team_id: int) -> bool:
    """Vrai si l'utilisateur peut agir sur cette équipe agricole."""
    if team_id <= 0:
        return True
    await ensure_access_tables()
    async with rx.asession() as asession:
        if await _has_full_scope(asession, user_id):
            return True
        row = (
            await asession.execute(
                text(
                    """
                    SELECT 1 FROM access_scope
                    WHERE user_id = :uid AND team_id = :tid
                    UNION
                    SELECT 1 FROM team_member
                    WHERE user_id = :uid AND team_id = :tid
                    UNION
                    SELECT 1 FROM user_assignment
                    WHERE user_id = :uid AND team_id = :tid
                    UNION
                    SELECT 1 FROM farm_team
                    WHERE id = :tid AND leader_id = :uid
                    UNION
                    SELECT 1 FROM role_delegation
                    WHERE delegate_id = :uid AND status = 'ACTIVE'
                      AND team_id = :tid
                    LIMIT 1
                    """
                ),
                {"uid": user_id, "tid": team_id},
            )
        ).first()
    return row is not None


async def scope_allows_farm(user_id: int, farm_key: str) -> bool:
    """Vrai si l'utilisateur est rattaché à cette exploitation."""
    await ensure_access_tables()
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text(
                    """
                    SELECT 1 FROM app_user
                    WHERE id = :uid AND status = 'ACTIF'
                      AND (COALESCE(farm_key, '') = :farm
                           OR COALESCE(farm_key, '') = '')
                    UNION
                    SELECT 1 FROM access_scope
                    WHERE user_id = :uid AND COALESCE(farm_key, '') = :farm
                    LIMIT 1
                    """
                ),
                {"uid": user_id, "farm": farm_key},
            )
        ).first()
    return row is not None


# ---------------------------------------------------------------------------
# Délégations temporaires
# ---------------------------------------------------------------------------


async def expire_stale_delegations() -> int:
    """Passe en `EXPIREE` les délégations dont la date de fin est dépassée."""
    await ensure_access_tables()
    today = datetime.date.today()
    async with rx.asession() as asession:
        result = await asession.execute(
            text(
                """
                UPDATE role_delegation
                SET status = 'EXPIREE'
                WHERE status IN ('ACTIVE', 'PLANIFIEE')
                  AND end_date IS NOT NULL AND end_date < :today
                """
            ),
            {"today": today},
        )
        await asession.execute(
            text(
                """
                UPDATE role_delegation
                SET status = 'ACTIVE'
                WHERE status = 'PLANIFIEE'
                  AND (start_date IS NULL OR start_date <= :today)
                  AND (end_date IS NULL OR end_date >= :today)
                """
            ),
            {"today": today},
        )
        await asession.commit()
    return int(result.rowcount or 0)


async def active_delegations(
    user_id: int = 0, as_delegate: bool = True
) -> list[DelegationInfo]:
    """Délégations actives, reçues (`as_delegate`) ou accordées."""
    await ensure_access_tables()
    today = datetime.date.today()
    column = "d.delegate_id" if as_delegate else "d.delegator_id"
    clause = "1=1" if user_id <= 0 else f"{column} = :uid"
    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(
                    f"""
                    SELECT d.id, d.delegator_id,
                           COALESCE(du.first_name || ' ' || du.last_name, ''),
                           d.delegate_id,
                           COALESCE(tu.first_name || ' ' || tu.last_name, ''),
                           COALESCE(r.key, ''), COALESCE(r.name, ''),
                           COALESCE(p.key, ''), COALESCE(d.scope_kind, ''),
                           COALESCE(d.parcel_id, 0), COALESCE(d.team_id, 0),
                           COALESCE(d.reason, ''), COALESCE(d.authorized_by, ''),
                           d.start_date, d.end_date
                    FROM role_delegation d
                    LEFT JOIN app_user du ON du.id = d.delegator_id
                    LEFT JOIN app_user tu ON tu.id = d.delegate_id
                    LEFT JOIN app_role r ON r.id = d.role_id
                    LEFT JOIN app_permission p ON p.id = d.permission_id
                    WHERE {clause}
                      AND d.status = 'ACTIVE'
                      AND (d.start_date IS NULL OR d.start_date <= :today)
                      AND (d.end_date IS NULL OR d.end_date >= :today)
                    ORDER BY d.end_date
                    LIMIT 50
                    """
                ),
                {"uid": user_id, "today": today},
            )
        ).all()

    from app.date_utils import as_date

    items: list[DelegationInfo] = []
    for row in rows:
        end = as_date(row[14])
        items.append(
            {
                "id": int(row[0]),
                "delegator_id": int(row[1]),
                "delegator_label": str(row[2]).strip(),
                "delegate_id": int(row[3]),
                "delegate_label": str(row[4]).strip(),
                "role_key": str(row[5]),
                "role_label": str(row[6]),
                "permission_key": str(row[7]),
                "scope_kind": str(row[8]),
                "parcel_id": int(row[9] or 0),
                "team_id": int(row[10] or 0),
                "reason": str(row[11]),
                "authorized_by": str(row[12]),
                "start_label": _fmt(row[13]),
                "end_label": _fmt(row[14]),
                "days_left": (end - today).days if end is not None else 0,
            }
        )
    return items


# ---------------------------------------------------------------------------
# Journal d'activité
# ---------------------------------------------------------------------------


async def log_activity(
    user_id: int,
    kind: str,
    module: str = "",
    action: str = "",
    object_type: str = "",
    object_ref: str = "",
    object_id: int = 0,
    summary: str = "",
    scope_label: str = "",
    parcel_id: int = 0,
    team_id: int = 0,
    ip_address: str = "",
    is_sensitive: bool = False,
) -> int:
    """Consigne une action importante et retourne l'identifiant du journal."""
    await ensure_access_tables()
    now = datetime.datetime.now(datetime.timezone.utc)
    async with rx.asession() as asession:
        actor = (
            await asession.execute(
                text(
                    """
                    SELECT COALESCE(first_name || ' ' || last_name, matricule)
                    FROM app_user WHERE id = :uid
                    """
                ),
                {"uid": user_id},
            )
        ).first()
        await asession.execute(
            text(
                """
                INSERT INTO activity_log (
                    user_id, actor_label, kind, module, action, object_type,
                    object_ref, object_id, summary, scope_label, parcel_id,
                    team_id, ip_address, is_sensitive, occurred_at
                ) VALUES (
                    :user_id, :actor_label, :kind, :module, :action, :object_type,
                    :object_ref, :object_id, :summary, :scope_label, :parcel_id,
                    :team_id, :ip_address, :is_sensitive, :occurred_at
                )
                """
            ),
            {
                "user_id": user_id if user_id > 0 else None,
                "actor_label": str(actor[0])
                if actor is not None
                else "Système",
                "kind": kind,
                "module": module,
                "action": action,
                "object_type": object_type,
                "object_ref": object_ref,
                "object_id": object_id,
                "summary": summary,
                "scope_label": scope_label,
                "parcel_id": parcel_id if parcel_id > 0 else None,
                "team_id": team_id if team_id > 0 else None,
                "ip_address": ip_address,
                "is_sensitive": 1 if is_sensitive else 0,
                "occurred_at": now,
            },
        )
        new_id = int(
            (
                await asession.execute(
                    text("SELECT COALESCE(MAX(id), 0) FROM activity_log")
                )
            ).scalar()
            or 0
        )
        await asession.commit()
    return new_id


# ---------------------------------------------------------------------------
# Décision unique : permission + périmètre + journal
# ---------------------------------------------------------------------------


async def authorize(
    user_id: int,
    module: str,
    action: str,
    parcel_id: int = 0,
    team_id: int = 0,
    farm_key: str = "",
    object_type: str = "",
    object_ref: str = "",
    log_denials: bool = True,
) -> AuthorizationResult:
    """Contrôle serveur complet avant toute écriture métier.

    Vérifie successivement : existence et activité du compte, permission
    effective (rôles puis délégations actives), puis périmètre parcelle,
    équipe et exploitation. Les refus sont journalisés pour l'audit sécurité.
    """
    await ensure_access_tables()
    today = datetime.date.today()
    result: AuthorizationResult = {
        "allowed": False,
        "reason": DENY_UNKNOWN_USER,
        "message": DENY_REASONS[DENY_UNKNOWN_USER],
        "module": module,
        "action": action,
        "permission": permission_key(module, action),
        "user_id": user_id,
        "via_delegation": False,
        "scope_label": SCOPE_EXPLOITATION,
    }

    try:
        async with rx.asession() as asession:
            status = await _user_status(asession, user_id)
            if status is None:
                pass
            elif status not in ACTIVE_STATUSES:
                result["reason"] = DENY_INACTIVE_USER
                result["message"] = DENY_REASONS[DENY_INACTIVE_USER]
            else:
                granted, via = await _has_permission_detail(
                    asession, user_id, module, action, today
                )
                result["via_delegation"] = via
                if not granted:
                    result["reason"] = DENY_NO_PERMISSION
                    result["message"] = DENY_REASONS[DENY_NO_PERMISSION]
                else:
                    result["reason"] = ""
                    result["message"] = "Action autorisée."
                    result["allowed"] = True
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
        raise

    if result["allowed"] and parcel_id > 0:
        if not await scope_allows_parcel(user_id, parcel_id):
            result["allowed"] = False
            result["reason"] = DENY_OUT_OF_SCOPE
            result["message"] = DENY_REASONS[DENY_OUT_OF_SCOPE]
    if result["allowed"] and team_id > 0:
        if not await scope_allows_team(user_id, team_id):
            result["allowed"] = False
            result["reason"] = DENY_OUT_OF_SCOPE
            result["message"] = DENY_REASONS[DENY_OUT_OF_SCOPE]
    if result["allowed"] and farm_key:
        if not await scope_allows_farm(user_id, farm_key):
            result["allowed"] = False
            result["reason"] = DENY_OUT_OF_SCOPE
            result["message"] = DENY_REASONS[DENY_OUT_OF_SCOPE]

    if not result["allowed"] and log_denials:
        await log_activity(
            user_id,
            "REFUS",
            module=module,
            action=action,
            object_type=object_type,
            object_ref=object_ref,
            summary=f"Accès refusé ({result['reason']}) sur {module}:{action}.",
            parcel_id=parcel_id,
            team_id=team_id,
            is_sensitive=True,
        )
    return result


# ---------------------------------------------------------------------------
# Sessions et MFA
# ---------------------------------------------------------------------------


async def resolve_session(raw_token: str) -> int:
    """Retourne l'identifiant utilisateur d'une session valide, sinon 0."""
    if not raw_token:
        return 0
    await ensure_access_tables()
    now = datetime.datetime.now(datetime.timezone.utc)
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text(
                    """
                    SELECT s.user_id, s.mfa_passed, s.expires_at, u.status
                    FROM user_session s
                    JOIN app_user u ON u.id = s.user_id
                    WHERE s.token_hash = :token AND s.status = 'ACTIVE'
                    LIMIT 1
                    """
                ),
                {"token": hash_token(raw_token)},
            )
        ).first()
    if row is None:
        return 0
    if str(row[3]) not in ACTIVE_STATUSES:
        return 0
    if not bool(row[1]):
        return 0
    from app.date_utils import as_datetime

    expires = as_datetime(row[2])
    if expires is not None:
        reference = (
            now if expires.tzinfo is not None else now.replace(tzinfo=None)
        )
        if expires < reference:
            return 0
    return int(row[0])


async def touch_session(raw_token: str) -> bool:
    """Rafraîchit la dernière activité d'une session (garde-fou de sécurité)."""
    if not raw_token:
        return False
    await ensure_access_tables()
    now = datetime.datetime.now(datetime.timezone.utc)
    async with rx.asession() as asession:
        result = await asession.execute(
            text(
                """
                UPDATE user_session SET last_seen_at = :now
                WHERE token_hash = :token AND status = 'ACTIVE'
                """
            ),
            {"now": now, "token": hash_token(raw_token)},
        )
        await asession.commit()
    return int(result.rowcount or 0) > 0


# ---------------------------------------------------------------------------
# Profil de sécurité consolidé (préparation de l'UI Administration)
# ---------------------------------------------------------------------------


async def user_by_matricule(matricule: str) -> int:
    """Identifiant d'un utilisateur depuis son matricule, 0 si inconnu."""
    await ensure_access_tables()
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text("SELECT id FROM app_user WHERE matricule = :m"),
                {"m": matricule},
            )
        ).first()
    return int(row[0]) if row is not None else 0


async def user_security_profile(user_id: int) -> SecurityProfile:
    """Synthèse sécurité d'un utilisateur, prête pour les futurs écrans."""
    await ensure_access_tables()
    empty: SecurityProfile = {
        "user_id": 0,
        "matricule": "",
        "full_name": "—",
        "email": "",
        "status": "INACTIF",
        "function_key": "",
        "function_label": "—",
        "role_keys": [],
        "role_labels": [],
        "team_key": "",
        "team_label": "—",
        "farm_key": "",
        "sector": "",
        "mfa_enabled": False,
        "mfa_method": "AUCUNE",
        "permission_count": 0,
        "permissions": [],
        "scope_kinds": [],
        "parcel_ids": [],
        "has_full_scope": False,
        "delegation_count": 0,
        "last_login_label": "—",
    }
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text(
                    """
                    SELECT u.id, u.matricule, u.first_name, u.last_name,
                           COALESCE(u.email, ''), u.status,
                           COALESCE(f.key, ''), COALESCE(f.name, ''),
                           COALESCE(t.key, ''), COALESCE(t.name, ''),
                           COALESCE(u.farm_key, ''), COALESCE(u.sector, ''),
                           u.mfa_enabled, COALESCE(u.mfa_method, 'AUCUNE'),
                           u.last_login_at
                    FROM app_user u
                    LEFT JOIN app_function f ON f.id = u.function_id
                    LEFT JOIN farm_team t ON t.id = u.team_id
                    WHERE u.id = :uid
                    """
                ),
                {"uid": user_id},
            )
        ).first()
        if row is None:
            return empty
        role_rows = (
            await asession.execute(
                text(
                    """
                    SELECT r.key, r.name FROM user_role ur
                    JOIN app_role r ON r.id = ur.role_id
                    WHERE ur.user_id = :uid
                    ORDER BY r.level DESC
                    """
                ),
                {"uid": user_id},
            )
        ).all()
        scope_rows = (
            await asession.execute(
                text(
                    """
                    SELECT DISTINCT scope_kind FROM access_scope
                    WHERE user_id = :uid ORDER BY scope_kind
                    """
                ),
                {"uid": user_id},
            )
        ).all()
        full_scope = await _has_full_scope(asession, user_id)

    permissions = await effective_permissions(user_id)
    parcels = await parcel_ids_in_scope(user_id)
    delegations = await active_delegations(user_id)
    return {
        "user_id": int(row[0]),
        "matricule": str(row[1]),
        "full_name": f"{row[2]} {row[3]}".strip(),
        "email": str(row[4]),
        "status": str(row[5]),
        "function_key": str(row[6]),
        "function_label": str(row[7]) or "—",
        "role_keys": [str(r[0]) for r in role_rows],
        "role_labels": [str(r[1]) for r in role_rows],
        "team_key": str(row[8]),
        "team_label": str(row[9]) or "—",
        "farm_key": str(row[10]),
        "sector": str(row[11]),
        "mfa_enabled": bool(row[12]),
        "mfa_method": str(row[13]),
        "permission_count": len(permissions),
        "permissions": permissions,
        "scope_kinds": [str(r[0]) for r in scope_rows],
        "parcel_ids": parcels,
        "has_full_scope": full_scope,
        "delegation_count": len(delegations),
        "last_login_label": _fmt(row[14]),
    }


# ---------------------------------------------------------------------------
# API publique de contrôle d'accès (noms attendus par les validations)
# ---------------------------------------------------------------------------


async def user_effective_permissions(
    user_id: int, include_delegations: bool = True
) -> list[str]:
    """Permissions effectives (`module:ACTION`), triées et stables.

    Alias public de `effective_permissions` : aucune logique dupliquée.
    """
    return await effective_permissions(
        user_id, include_delegations=include_delegations
    )


async def can_user(
    user_id: int,
    module: str,
    action: str,
    parcel_id: int = 0,
    team_id: int = 0,
    farm_key: str = "",
    object_type: str = "",
    object_ref: str = "",
    log_denials: bool = True,
) -> AccessDecision:
    """Contrôle serveur complet : module, action et périmètre agricole.

    Enveloppe `authorize()` (RBAC + délégations + périmètre parcelle, équipe et
    exploitation) et renvoie une décision exploitable par attribut
    (`decision.allowed`), par clé (`decision["reason"]`) ou en booléen.
    Les actions et modules sont normalisés (`"modifier"` → `"MODIFIER"`).
    """
    module_key = _normalize_module(module)
    action_key = _normalize_action(action)
    result = await authorize(
        user_id,
        module_key,
        action_key,
        parcel_id=parcel_id,
        team_id=team_id,
        farm_key=farm_key,
        object_type=object_type,
        object_ref=object_ref,
        log_denials=log_denials,
    )
    return AccessDecision(
        allowed=bool(result["allowed"]),
        reason=str(result["reason"]),
        message=str(result["message"]),
        module=module_key,
        action=action_key,
        permission=str(result["permission"]),
        user_id=int(user_id),
        via_delegation=bool(result["via_delegation"]),
        scope_label=str(result["scope_label"]),
        parcel_id=int(parcel_id or 0),
        team_id=int(team_id or 0),
        farm_key=str(farm_key or ""),
    )


async def assert_user_can(
    user_id: int,
    module: str,
    action: str,
    parcel_id: int = 0,
    team_id: int = 0,
    farm_key: str = "",
    object_type: str = "",
    object_ref: str = "",
) -> bool:
    """Garde-fou serveur : retourne `True` ou lève `PermissionDeniedError`.

    À appeler au tout début d'un gestionnaire d'événement avant toute écriture
    métier : le frontend n'est jamais considéré comme une protection.
    """
    decision = await can_user(
        user_id,
        module,
        action,
        parcel_id=parcel_id,
        team_id=team_id,
        farm_key=farm_key,
        object_type=object_type,
        object_ref=object_ref,
    )
    if not decision.allowed:
        raise PermissionDeniedError(decision)
    return True


async def user_scope_summary(user_id: int) -> ScopeSummary:
    """Synthèse du périmètre agricole : parcelles, équipes, secteurs, cultures.

    Le résultat est toujours complet (aucune clé manquante) et trié, y compris
    pour un utilisateur inconnu ou inactif.
    """
    await ensure_access_tables()
    today = datetime.date.today()
    summary: ScopeSummary = {
        "user_id": int(user_id),
        "has_full_scope": False,
        "farm_key": "",
        "farm_keys": [],
        "sectors": [],
        "scope_kinds": [],
        "parcels": [],
        "parcel_count": 0,
        "teams": [],
        "team_count": 0,
        "crops": [],
        "activities": [],
        "scope_label": _FULL_SCOPE_LABEL,
    }
    try:
        async with rx.asession() as asession:
            user = (
                await asession.execute(
                    text(
                        """
                        SELECT COALESCE(farm_key, ''), COALESCE(sector, '')
                        FROM app_user WHERE id = :uid
                        """
                    ),
                    {"uid": user_id},
                )
            ).first()
            if user is None:
                return summary
            summary["farm_key"] = str(user[0])
            summary["has_full_scope"] = await _has_full_scope(asession, user_id)
            scope_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT COALESCE(scope_kind, ''), COALESCE(farm_key, ''),
                               COALESCE(sector, ''), COALESCE(activity, ''),
                               COALESCE(crop_id, 0)
                        FROM access_scope WHERE user_id = :uid
                        """
                    ),
                    {"uid": user_id},
                )
            ).all()
            team_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT team_id FROM access_scope
                        WHERE user_id = :uid AND team_id IS NOT NULL
                        UNION
                        SELECT team_id FROM team_member WHERE user_id = :uid
                        UNION
                        SELECT team_id FROM user_assignment
                        WHERE user_id = :uid AND team_id IS NOT NULL
                        UNION
                        SELECT id FROM farm_team WHERE leader_id = :uid
                        UNION
                        SELECT team_id FROM role_delegation
                        WHERE delegate_id = :uid AND status = 'ACTIVE'
                          AND team_id IS NOT NULL
                          AND (start_date IS NULL OR start_date <= :today)
                          AND (end_date IS NULL OR end_date >= :today)
                        """
                    ),
                    {"uid": user_id, "today": today},
                )
            ).all()
            assignment_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT COALESCE(farm_key, ''), COALESCE(sector, ''),
                               COALESCE(activity, ''), COALESCE(crop_id, 0)
                        FROM user_assignment WHERE user_id = :uid
                        """
                    ),
                    {"uid": user_id},
                )
            ).all()
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
        raise

    farms = {summary["farm_key"]} if summary["farm_key"] else set()
    sectors = {str(user[1])} if str(user[1]) else set()
    kinds: set[str] = set()
    activities: set[str] = set()
    crops: set[int] = set()
    for row in scope_rows:
        if str(row[0]):
            kinds.add(row[0])
        if str(row[1]):
            farms.add(row[1])
        if str(row[2]):
            sectors.add(row[2])
        if str(row[3]):
            activities.add(row[3])
        if int(row[4] or 0) > 0:
            crops.add(int(row[4]))
    for row in assignment_rows:
        if str(row[0]):
            farms.add(row[0])
        if str(row[1]):
            sectors.add(row[1])
        if str(row[2]):
            activities.add(row[2])
        if int(row[3] or 0) > 0:
            crops.add(int(row[3]))

    parcels = await parcel_ids_in_scope(user_id)
    teams = sorted(
        {
            int(row[0])
            for row in team_rows
            if row[0] is not None and int(row[0]) > 0
        }
    )
    summary["farm_keys"] = sorted(farms)
    summary["sectors"] = sorted(sectors)
    summary["scope_kinds"] = sorted(kinds)
    summary["parcels"] = parcels
    summary["parcel_count"] = len(parcels)
    summary["teams"] = teams
    summary["team_count"] = len(teams)
    summary["crops"] = sorted(crops)
    summary["activities"] = sorted(activities)
    if summary["has_full_scope"]:
        summary["scope_label"] = _FULL_SCOPE_LABEL
    elif parcels:
        summary["scope_label"] = f"{len(parcels)} parcelle(s) autorisée(s)"
    elif teams:
        summary["scope_label"] = f"{len(teams)} équipe(s) autorisée(s)"
    elif summary["crops"]:
        summary["scope_label"] = (
            f"{len(summary['crops'])} culture(s) autorisée(s)"
        )
    elif summary["activities"]:
        summary["scope_label"] = scope_kind_label(SCOPE_ACTIVITE)
    elif summary["sectors"]:
        summary["scope_label"] = scope_kind_label(SCOPE_SECTEUR)
    else:
        summary["scope_label"] = SCOPE_LABELS.get(
            SCOPE_PERSONNEL, "Données personnelles"
        )
    return summary


async def log_access_event(
    user_id: int,
    kind: str,
    object_type: str = "",
    object_id: int = 0,
    summary: str = "",
    module: str = "",
    action: str = "",
    object_ref: str = "",
    scope_label: str = "",
    parcel_id: int = 0,
    team_id: int = 0,
    ip_address: str = "",
    is_sensitive: bool = False,
) -> int:
    """Consigne un évènement d'accès et retourne l'identifiant du journal.

    Signature orientée audit (`utilisateur → action → objet → date`) reposant
    sur `log_activity`, sans dupliquer l'écriture SQL.
    """
    return await log_activity(
        user_id,
        str(kind or "CONSULTATION").strip().upper(),
        module=_normalize_module(module),
        action=_normalize_action(action),
        object_type=str(object_type or "").strip(),
        object_ref=object_ref or (summary[:200] if summary else ""),
        object_id=int(object_id or 0),
        summary=summary,
        scope_label=scope_label,
        parcel_id=int(parcel_id or 0),
        team_id=int(team_id or 0),
        ip_address=ip_address,
        is_sensitive=is_sensitive,
    )


async def active_delegations_for_user(
    user_id: int, as_delegate: bool = True
) -> list[DelegationInfo]:
    """Délégations temporaires actives reçues (ou accordées) par un utilisateur.

    Alias public de `active_delegations`, toujours une liste (vide si aucune).
    """
    if user_id <= 0:
        return []
    await expire_stale_delegations()
    return await active_delegations(user_id, as_delegate=as_delegate)

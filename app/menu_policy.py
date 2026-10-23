import reflex as rx

"""Navigation policy on existing menu settings; no identity or schema creation.

Boolean keys:
policy:account:<id>:role:<registered-role> assigns/removes a role;
policy:role:<role>:permission:<module>:<ACTION> overrides static role grants;
policy:account:<id>:permission:<module>:<ACTION> grants/denies individually;
policy:account:<id>:active disables the account's navigation.

The earliest durable account's existing is_admin bootstraps proprietaire only.
An explicit false owner assignment removes that bootstrap. No other admin flag
or unmatched email grants rights. Denials from any assigned role or account
win over all grants, including owner grants. Global parent/child disables apply
last. Every resolution reads current rows; no permission-result cache is used.
This is navigation policy, not complete business action/API authorization.
"""

import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import TypedDict

from sqlalchemy import text

from app.access_reference import (
    ROLES,
    ROLE_MATRIX,
    all_permissions,
    permission_key,
)
from app.local_db_env import DB_PATH
from app.navigation import COCKPITS, NAVIGATION, Cockpit, NavigationEntry

ROLE_KEYS = frozenset(role["key"] for role in ROLES)
PERMISSIONS = frozenset(
    permission_key(module, action) for module, action in all_permissions()
)
GLOBAL_KEYS = frozenset(
    item["key"] for item in COCKPITS if item["available"]
) | frozenset(entry["key"] for entry in NAVIGATION)

# No new module registry: CRM destinations use the existing commercial modules.
ENTRY_MODULES: dict[str, tuple[str, ...]] = {
    "configuration.menus": ("parametres",),
    "global.overview": ("dashboard",),
    "global.search": ("dashboard",),
    "agricole.parcelles": ("parcelles",),
    "agricole.referentiel": ("semences",),
    "agricole.traitements": ("traitements",),
    "agricole.phenologie": ("parametres",),
    "agricole.rapports": ("rapports",),
    "commercial.overview": ("ventes", "achats", "comptabilite"),
    "commercial.clients": ("ventes",),
    "commercial.ventes": ("ventes",),
    "commercial.rapports": ("rapports", "comptabilite"),
    "stocks.magasin": ("stocks",),
    "materiel.flotte": ("materiel",),
    "rh.employes": ("rh",),
    "financier.charges": ("comptabilite",),
    "financier.creances": ("comptabilite",),
    "financier.dettes": ("comptabilite",),
    "financier.paiements": ("comptabilite",),
    "achats.achats": ("achats",),
    "achats.fournisseurs": ("achats",),
    "documentaire.guide": ("documents",),
    "analytics.rapports": ("rapports",),
    "analytics.audit": ("utilisateurs",),
    "cartographique.carte": ("cartographie",),
    "planification.chantiers": ("interventions",),
    "planification.maintenance": ("maintenance",),
    "planification.calendrier": ("dashboard",),
    "partenaires.tiers": ("ventes", "achats"),
    "partenaires.clients": ("ventes",),
    "partenaires.fournisseurs": ("achats",),
    "administration.acces": ("utilisateurs",),
    "administration.phenologie": ("parametres",),
    "administration.audit": ("utilisateurs",),
}


class Policy(TypedDict):
    id: int
    email: str
    admin: bool
    active: bool
    roles: list[str]
    permissions: list[str]
    settings: dict[str, bool]
    cockpits: list[Cockpit]
    navigation: list[NavigationEntry]
    crm_tabs: list[str]


class LocalRights(TypedDict):
    active: bool
    roles: list[str]
    overrides: dict[str, dict[str, bool]]


def validate_policy_key(key: str) -> bool:
    parts = key.split(":")
    if len(parts) < 4 or parts[0] != "policy":
        return False
    if parts[1] == "account":
        if (
            not parts[2].isascii()
            or not parts[2].isdigit()
            or str(int(parts[2])) != parts[2]
            or int(parts[2]) < 1
        ):
            return False
        if len(parts) == 4:
            return parts[3] == "active"
        if len(parts) == 5:
            return parts[3] == "role" and parts[4] in ROLE_KEYS
        return (
            len(parts) == 6
            and parts[3] == "permission"
            and permission_key(parts[4], parts[5]) in PERMISSIONS
        )
    return (
        parts[1] == "role"
        and parts[2] in ROLE_KEYS
        and len(parts) == 6
        and parts[3] == "permission"
        and permission_key(parts[4], parts[5]) in PERMISSIONS
    )


def static_permissions(role: str) -> set[str]:
    matrix = ROLE_MATRIX.get(role, {})
    result: set[str] = set()
    for module, action in all_permissions():
        actions = matrix.get(module, matrix.get("*", []))
        if actions == "*" or action in actions:
            result.add(permission_key(module, action))
    return result


def visible_entries(
    permissions: set[str], settings: dict[str, bool], active: bool = True
) -> list[NavigationEntry]:
    entries: list[NavigationEntry] = []
    if not active:
        return entries
    for entry in NAVIGATION:
        required = {
            permission_key(module, "CONSULTER")
            for module in ENTRY_MODULES[entry["key"]]
        }
        if entry["key"] == "configuration.menus":
            required.add(permission_key("parametres", "MODIFIER"))
        if (
            required <= permissions
            and settings.get(entry["cockpit"], True)
            and settings.get(entry["key"], True)
        ):
            entries.append(entry)
    return entries


def evaluate_policy(
    account: dict[str, str | int | bool],
    rows: dict[str, bool],
    *,
    first_account_id: int = 0,
    local: LocalRights | None = None,
) -> Policy:
    account_id = int(account.get("id", 0))
    prefix = f"policy:account:{account_id}"
    local = local or {"active": True, "roles": [], "overrides": {}}
    roles = (set(local["roles"]) & ROLE_KEYS) if account_id > 0 else set()
    # Only the earliest durable account's existing admin flag bootstraps owner.
    if (
        account_id > 0
        and account_id == first_account_id
        and bool(account.get("admin", False))
    ):
        roles.add("proprietaire")
    valid = {
        key: value for key, value in rows.items() if validate_policy_key(key)
    }
    for role in ROLE_KEYS:
        key = f"{prefix}:role:{role}"
        if key in valid:
            if valid[key]:
                roles.add(role)
            else:
                roles.discard(role)
    grants: set[str] = set()
    denies: set[str] = set()
    for role in roles:
        grants.update(static_permissions(role))
        overrides = dict(local["overrides"].get(role, {}))
        for permission in PERMISSIONS:
            key = f"policy:role:{role}:permission:{permission}"
            if key in valid:
                overrides[permission] = valid[key]
        for permission, granted in overrides.items():
            if permission in PERMISSIONS:
                (grants if granted else denies).add(permission)
    for permission in PERMISSIONS:
        key = f"{prefix}:permission:{permission}"
        if key in valid:
            (grants if valid[key] else denies).add(permission)
    active = (
        account_id > 0
        and local["active"]
        and valid.get(f"{prefix}:active", True)
    )
    permissions = (grants - denies) if active else set()
    settings = {key: value for key, value in rows.items() if key in GLOBAL_KEYS}
    navigation = visible_entries(permissions, settings, active)
    parents = {entry["cockpit"] for entry in navigation}
    cockpits = [
        item
        for item in COCKPITS
        if item["available"] and item["key"] in parents
    ]
    tabs = {entry["tab"] for entry in navigation if entry["page"] == "crm"}
    if "synthese" in tabs:
        tabs.update({"graphiques", "tiers", "alertes", "recherche"})
    return {
        "id": account_id,
        "email": str(account.get("email", "")),
        "admin": active
        and {"parametres:CONSULTER", "parametres:MODIFIER"} <= permissions,
        "active": active,
        "roles": sorted(roles) if account_id > 0 else [],
        "permissions": sorted(permissions),
        "settings": settings,
        "cockpits": cockpits,
        "navigation": navigation,
        "crm_tabs": sorted(tabs - {""}),
    }


def read_local_rights(email: str, path: Path = DB_PATH) -> LocalRights:
    empty: LocalRights = {"active": True, "roles": [], "overrides": {}}
    if not email.strip() or not path.exists():
        return empty
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        connection.execute("BEGIN")
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "app_user" not in tables:
            return empty
        matches = connection.execute(
            "SELECT id, status FROM app_user WHERE lower(trim(email)) = ? LIMIT 2",
            (email.strip().lower(),),
        ).fetchall()
        if len(matches) != 1:
            return empty
        user_id, status = matches[0]
        empty["active"] = str(status).upper() == "ACTIF"
        if not {"user_role", "app_role"} <= tables:
            return empty
        roles = connection.execute(
            "SELECT r.key FROM user_role ur JOIN app_role r ON r.id=ur.role_id WHERE ur.user_id=? AND r.is_active=1",
            (user_id,),
        ).fetchall()
        empty["roles"] = [str(row[0]) for row in roles if row[0] in ROLE_KEYS]
        if {"role_permission", "app_permission"} <= tables:
            rows = connection.execute(
                "SELECT r.key, p.key, rp.is_granted FROM user_role ur JOIN app_role r ON r.id=ur.role_id JOIN role_permission rp ON rp.role_id=r.id JOIN app_permission p ON p.id=rp.permission_id WHERE ur.user_id=? AND r.is_active=1",
                (user_id,),
            ).fetchall()
            for role, permission, granted in rows:
                if role in ROLE_KEYS and permission in PERMISSIONS:
                    overrides = empty["overrides"].setdefault(str(role), {})
                    overrides[str(permission)] = overrides.get(
                        str(permission), True
                    ) and bool(granted)
        return empty
    except Exception as e:
        logging.exception(f"Error: {e}")
        raise RuntimeError(
            "La vérification des droits existants est indisponible."
        ) from None
    finally:
        connection.close()


async def policy_in_session(
    session, account: dict[str, str | int | bool]
) -> Policy:
    rows = (
        await session.execute(
            text(
                "SELECT navigation_key, enabled FROM menu_setting WHERE navigation_key LIKE 'policy:%' OR navigation_key NOT LIKE '%:%'"
            )
        )
    ).all()
    first_id = int(
        (
            await session.execute(text("SELECT MIN(id) FROM menu_auth_account"))
        ).scalar()
        or 0
    )
    local = await asyncio.to_thread(read_local_rights, str(account["email"]))
    return evaluate_policy(
        account,
        {str(key): bool(value) for key, value in rows},
        first_account_id=first_id,
        local=local,
    )


async def resolve_policy(token: str) -> Policy:
    from app import menu_service

    if not token:
        return evaluate_policy({"id": 0, "email": "", "admin": False}, {})
    await menu_service.ensure_menu_database()
    async with menu_service.menu_session() as session:
        account = await menu_service.account_in_session(session, token)
        return await policy_in_session(session, account)

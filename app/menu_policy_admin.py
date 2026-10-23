import reflex as rx

import asyncio
import datetime as dt
import sqlite3
import uuid
from typing import TypedDict

from sqlalchemy import text

from app import menu_service
from app.access_reference import ROLES
from app.local_db_env import DB_PATH
from app.menu_policy import (
    GLOBAL_KEYS,
    PERMISSIONS,
    ROLE_KEYS,
    Policy,
    policy_in_session,
    evaluate_policy,
    read_local_rights,
    static_permissions,
    validate_policy_key,
)


class SessionExpired(PermissionError):
    pass


class ConfigurationDenied(PermissionError):
    pass


class PermissionRow(TypedDict):
    key: str
    target: str
    explicit: str
    inherited: bool
    effective: bool
    source: str


class RoleRow(TypedDict):
    key: str
    label: str
    note: str
    overrides: int


class AccountRow(TypedDict):
    id: str
    email: str
    active: bool
    admin: bool
    roles: list[str]
    local_match: str


class AssignmentRow(TypedDict):
    key: str
    label: str
    target: str
    assigned: bool
    explicit: str


class AuditRow(TypedDict):
    id: str
    target: str
    actor: str
    date: str
    before: str
    after: str


class AdministrationData(TypedDict):
    settings: dict[str, bool]
    roles: list[RoleRow]
    accounts: list[AccountRow]
    permissions: list[PermissionRow]
    assignments: list[AssignmentRow]
    audit: list[AuditRow]
    selected_email: str
    selected_active: bool
    active_explicit: str
    active_target: str
    account_total: int
    audit_total: int


def canonical_id(value: str) -> int:
    if (
        not isinstance(value, str)
        or not value.isascii()
        or not value.isdigit()
        or len(value) > 19
    ):
        raise ValueError("Identifiant de compte invalide.")
    number = int(value)
    if number < 1 or number > 9223372036854775807 or str(number) != value:
        raise ValueError("Identifiant de compte invalide.")
    return number


def validated_target(key: str) -> str:
    if not isinstance(key, str) or not 1 <= len(key) <= 200:
        raise ValueError(
            "Clé de configuration invalide (200 caractères maximum)."
        )
    if key not in GLOBAL_KEYS and not validate_policy_key(key):
        raise ValueError("Rôle, permission ou menu non enregistré.")
    if key.startswith("policy:account:"):
        canonical_id(key.split(":")[2])
    return key


def value_code(value: bool | None) -> str:
    return "n" if value is None else ("1" if value else "0")


def value_label(code: str) -> str:
    return {
        "n": "Hériter",
        "1": "Accorder / activer",
        "0": "Refuser / désactiver",
    }[code]


def audit_key(target: str, before: bool | None, after: bool | None) -> str:
    validated_target(target)
    key = f"audit:{uuid.uuid4().hex}:{value_code(before)}:{value_code(after)}:{target}"
    if len(key) > 200:
        raise ValueError("Clé de journal trop longue (200 caractères maximum).")
    return key


async def require_configuration(
    session, token: str
) -> tuple[menu_service.Account, Policy]:
    try:
        account = await menu_service.account_in_session(session, token)
    except PermissionError as e:
        raise SessionExpired(
            "Votre session a expiré. Veuillez vous reconnecter."
        ) from e
    policy = await policy_in_session(session, account)
    if not policy["admin"] or not any(
        e["key"] == "configuration.menus" for e in policy["navigation"]
    ):
        raise ConfigurationDenied(
            "Droits de consultation et de modification de la Configuration requis."
        )
    return account, policy


async def existing_account(session, account_id: str) -> menu_service.Account:
    number = canonical_id(account_id)
    row = (
        await session.execute(
            text(
                "SELECT id, email, is_admin FROM menu_auth_account WHERE id=:id"
            ),
            {"id": number},
        )
    ).first()
    if row is None:
        raise ValueError("Ce compte connecté n’existe pas.")
    return {"id": int(row[0]), "email": str(row[1]), "admin": bool(row[2])}


def local_match(email: str) -> str:
    if not DB_PATH.exists():
        return "Aucune correspondance locale"
    connection = sqlite3.connect(
        f"{DB_PATH.resolve().as_uri()}?mode=ro", uri=True
    )
    try:
        present = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='app_user'"
        ).fetchone()
        if not present:
            return "Aucune correspondance locale"
        rows = connection.execute(
            "SELECT id, status FROM app_user WHERE lower(trim(email))=? LIMIT 2",
            (email.strip().lower(),),
        ).fetchall()
        if len(rows) != 1:
            return (
                "Correspondance ambiguë"
                if rows
                else "Aucune correspondance locale"
            )
        return f"Utilisateur local #{rows[0][0]} · {rows[0][1]}"
    finally:
        connection.close()


async def read_administration(
    token: str,
    *,
    role: str = "",
    account_id: str = "",
    search: str = "",
    account_filter: str = "Tous",
    offset: int = 0,
    audit_offset: int = 0,
) -> AdministrationData:
    async with menu_service.menu_session() as session:
        _, actor_policy = await require_configuration(session, token)
        if role and role not in ROLE_KEYS:
            raise ValueError("Rôle non enregistré.")
        if (
            type(offset) is not int
            or type(audit_offset) is not int
            or offset < 0
            or audit_offset < 0
        ):
            raise ValueError("Pagination invalide.")
        if account_filter not in {
            "Tous",
            "Actifs",
            "Désactivés",
            "Administrateurs",
        }:
            raise ValueError("Filtre invalide.")
        rows = dict(
            (str(r[0]), bool(r[1]))
            for r in (
                await session.execute(
                    text(
                        "SELECT navigation_key, enabled FROM menu_setting WHERE navigation_key LIKE 'policy:%'"
                    )
                )
            ).all()
        )
        roles: list[RoleRow] = [
            {
                "key": r["key"],
                "label": r["name"],
                "note": r["tagline"],
                "overrides": sum(
                    k.startswith(f"policy:role:{r['key']}:permission:")
                    for k in rows
                ),
            }
            for r in ROLES
        ]
        count = int(
            (
                await session.execute(
                    text(
                        "SELECT COUNT(*) FROM menu_auth_account WHERE lower(email) LIKE :term"
                    ),
                    {"term": f"%{search.strip().lower()[:320]}%"},
                )
            ).scalar()
            or 0
        )
        first_id = int(
            (
                await session.execute(
                    text("SELECT MIN(id) FROM menu_auth_account")
                )
            ).scalar()
            or 0
        )
        accounts: list[AccountRow] = []
        scan_offset = offset if account_filter == "Tous" else 0
        matched = 0
        while True:
            batch = (
                await session.execute(
                    text(
                        "SELECT id, email, is_admin FROM menu_auth_account WHERE lower(email) LIKE :term ORDER BY id LIMIT :limit OFFSET :offset"
                    ),
                    {
                        "term": f"%{search.strip().lower()[:320]}%",
                        "offset": scan_offset,
                        "limit": 25 if account_filter == "Tous" else 100,
                    },
                )
            ).all()
            if not batch:
                break
            for row in batch:
                account = {
                    "id": int(row[0]),
                    "email": str(row[1]),
                    "admin": bool(row[2]),
                }
                local = await asyncio.to_thread(read_local_rights, str(row[1]))
                policy = evaluate_policy(
                    account,
                    {**actor_policy["settings"], **rows},
                    first_account_id=first_id,
                    local=local,
                )
                if (
                    (account_filter == "Actifs" and not policy["active"])
                    or (account_filter == "Désactivés" and policy["active"])
                    or (
                        account_filter == "Administrateurs"
                        and not policy["admin"]
                    )
                ):
                    continue
                position = matched
                matched += 1
                if (
                    account_filter != "Tous"
                    and not offset <= position < offset + 25
                ):
                    continue
                accounts.append(
                    {
                        "id": str(row[0]),
                        "email": str(row[1]),
                        "active": policy["active"],
                        "admin": policy["admin"],
                        "roles": policy["roles"],
                        "local_match": await asyncio.to_thread(
                            local_match, str(row[1])
                        ),
                    }
                )
            if account_filter == "Tous":
                break
            scan_offset += len(batch)
        if account_filter != "Tous":
            count = matched
        permissions: list[PermissionRow] = []
        assignments: list[AssignmentRow] = []
        selected_email = ""
        selected_active = False
        active_target = ""
        active_explicit = "n"
        if account_id:
            account = await existing_account(session, account_id)
            policy = await policy_in_session(session, account)
            prefix = f"policy:account:{account_id}"
            selected_email = str(account["email"])
            selected_active = policy["active"]
            active_target = f"{prefix}:active"
            active_explicit = value_code(rows.get(active_target))
            for spec in ROLES:
                target = f"{prefix}:role:{spec['key']}"
                assignments.append(
                    {
                        "key": spec["key"],
                        "label": spec["name"],
                        "target": target,
                        "assigned": spec["key"] in policy["roles"],
                        "explicit": value_code(rows.get(target)),
                    }
                )
            # Remove only account permission overrides for the inherited comparison.
            inherited_rows = {
                k: v
                for k, v in rows.items()
                if not k.startswith(f"{prefix}:permission:")
            }
            first = int(
                (
                    await session.execute(
                        text("SELECT MIN(id) FROM menu_auth_account")
                    )
                ).scalar()
                or 0
            )
            local = await asyncio.to_thread(read_local_rights, selected_email)
            inherited = evaluate_policy(
                account,
                {**actor_policy["settings"], **inherited_rows},
                first_account_id=first,
                local=local,
            )
            for permission in sorted(PERMISSIONS):
                target = f"{prefix}:permission:{permission}"
                sources = [
                    r
                    for r in policy["roles"]
                    if permission in static_permissions(r)
                    or f"policy:role:{r}:permission:{permission}" in rows
                    or permission in local["overrides"].get(r, {})
                ]
                permissions.append(
                    {
                        "key": permission,
                        "target": target,
                        "explicit": value_code(rows.get(target)),
                        "inherited": permission in inherited["permissions"],
                        "effective": permission in policy["permissions"],
                        "source": f"Rôles : {', '.join(sources) or 'aucun'} · refus prioritaire · compte {'actif' if policy['active'] else 'désactivé'}",
                    }
                )
        elif role:
            static = static_permissions(role)
            for permission in sorted(PERMISSIONS):
                target = f"policy:role:{role}:permission:{permission}"
                permissions.append(
                    {
                        "key": permission,
                        "target": target,
                        "explicit": value_code(rows.get(target)),
                        "inherited": permission in static,
                        "effective": rows.get(target, permission in static),
                        "source": "Matrice du rôle enregistré (les refus des autres rôles restent prioritaires).",
                    }
                )
        audit_total = int(
            (
                await session.execute(
                    text(
                        "SELECT COUNT(*) FROM menu_setting WHERE navigation_key LIKE 'audit:%'"
                    )
                )
            ).scalar()
            or 0
        )
        audit_raw = (
            await session.execute(
                text(
                    "SELECT m.navigation_key, m.enabled, m.updated_at, m.updated_by_account_id, a.email FROM menu_setting m LEFT JOIN menu_auth_account a ON a.id=m.updated_by_account_id WHERE m.navigation_key LIKE 'audit:%' ORDER BY m.updated_at DESC, m.id DESC LIMIT 50 OFFSET :offset"
                ),
                {"offset": audit_offset},
            )
        ).all()
        audit: list[AuditRow] = []
        for key, enabled, date, actor_id, email in audit_raw:
            parts = str(key).split(":", 4)
            if (
                len(parts) != 5
                or len(str(key)) > 200
                or parts[2] not in {"n", "0", "1"}
                or parts[3] not in {"n", "0", "1"}
            ):
                continue
            try:
                uuid.UUID(hex=parts[1])
                validated_target(parts[4])
            except ValueError:
                continue
            if bool(enabled) != (parts[3] == "1"):
                continue
            audit.append(
                {
                    "id": str(key),
                    "target": parts[4],
                    "actor": f"{email or 'Compte indisponible'} · #{actor_id}",
                    "date": str(date),
                    "before": value_label(parts[2]),
                    "after": value_label(parts[3]),
                }
            )
        return {
            "settings": actor_policy["settings"],
            "roles": roles,
            "accounts": accounts,
            "permissions": permissions,
            "assignments": assignments,
            "audit": audit,
            "selected_email": selected_email,
            "selected_active": selected_active,
            "active_target": active_target,
            "active_explicit": active_explicit,
            "account_total": count,
            "audit_total": audit_total,
        }


async def edit_policy(token: str, key: str, mode: str) -> None:
    async with menu_service.menu_session() as session:
        await menu_service.lock_menu_transaction(session)
        actor, _ = await require_configuration(session, token)
        validated_target(key)
        if mode not in {"grant", "deny", "inherit", "toggle"}:
            raise ValueError("Choix de permission invalide.")
        if key in menu_service.PROTECTED_KEYS:
            raise ValueError("La Configuration reste toujours accessible.")
        if key.startswith("policy:account:"):
            await existing_account(session, key.split(":")[2])
        if mode == "toggle" and key not in GLOBAL_KEYS:
            raise ValueError("Bascule réservée aux menus.")
        previous = (
            await session.execute(
                text(
                    "SELECT enabled FROM menu_setting WHERE navigation_key=:key"
                ),
                {"key": key},
            )
        ).first()
        before = bool(previous[0]) if previous else None
        after = (
            (not (before if before is not None else True))
            if mode == "toggle"
            else {"grant": True, "deny": False, "inherit": None}[mode]
        )
        if before == after:
            return
        record_key = audit_key(key, before, after)
        now = menu_service.session_timestamp(session, dt.datetime.now(dt.UTC))
        params = {"key": key, "value": after, "now": now, "actor": actor["id"]}
        if after is None:
            await session.execute(
                text("DELETE FROM menu_setting WHERE navigation_key=:key"),
                {"key": key},
            )
        else:
            await session.execute(
                text(
                    "INSERT INTO menu_setting (navigation_key, enabled, updated_at, updated_by_account_id) VALUES (:key, :value, :now, :actor) ON CONFLICT(navigation_key) DO UPDATE SET enabled=:value, updated_at=:now, updated_by_account_id=:actor"
                ),
                params,
            )
        # Check all durable accounts, not just the actor or the visible list page.
        candidates = (
            await session.execute(
                text(
                    "SELECT id, email, is_admin FROM menu_auth_account ORDER BY id"
                )
            )
        ).all()
        retained = False
        for row in candidates:
            policy = await policy_in_session(
                session,
                {
                    "id": int(row[0]),
                    "email": str(row[1]),
                    "admin": bool(row[2]),
                },
            )
            if policy["admin"] and any(
                e["key"] == "configuration.menus" for e in policy["navigation"]
            ):
                retained = True
                break
        if not retained:
            raise ValueError(
                "Modification refusée : au moins un administrateur actif doit conserver l’accès à la Configuration."
            )
        await session.execute(
            text(
                "INSERT INTO menu_setting (navigation_key, enabled, updated_at, updated_by_account_id) VALUES (:key, :value, :now, :actor)"
            ),
            {
                "key": record_key,
                "value": after is True,
                "now": now,
                "actor": actor["id"],
            },
        )
        await session.commit()

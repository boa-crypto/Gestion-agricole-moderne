import reflex as rx

import asyncio
import datetime as dt
import hashlib
import logging
import re
import secrets
import unicodedata
from typing import TypedDict

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.menu_database import (
    ensure_menu_database,
    lock_menu_transaction,
    menu_session,
)
from app.navigation import COCKPITS, NAVIGATION

SESSION_SECONDS = 60 * 60 * 24 * 7
PASSWORD_ROUNDS = 600_000
PROTECTED_KEYS = frozenset({"configuration", "configuration.menus"})


class MenuRow(TypedDict):
    key: str
    label: str
    parent: str
    level: int
    enabled: bool
    effective: bool
    protected: bool


class Account(TypedDict):
    id: int
    email: str
    admin: bool


def normalize_search(value: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(c)
    )


def menu_catalog(overrides: dict[str, bool]) -> list[MenuRow]:
    rows: list[MenuRow] = []
    for cockpit in COCKPITS:
        if not cockpit["available"]:
            continue
        key = cockpit["key"]
        enabled = key in PROTECTED_KEYS or overrides.get(key, True)
        rows.append(
            {
                "key": key,
                "label": cockpit["label"],
                "parent": "",
                "level": 0,
                "enabled": enabled,
                "effective": enabled,
                "protected": key in PROTECTED_KEYS,
            }
        )
        for entry in NAVIGATION:
            if entry["cockpit"] == key:
                individual = entry["key"] in PROTECTED_KEYS or overrides.get(
                    entry["key"], True
                )
                rows.append(
                    {
                        "key": entry["key"],
                        "label": entry["label"],
                        "parent": key,
                        "level": 1,
                        "enabled": individual,
                        "effective": enabled and individual,
                        "protected": entry["key"] in PROTECTED_KEYS,
                    }
                )
    return rows


def filter_catalog(
    rows: list[MenuRow], search: str, status: str, level: str
) -> list[MenuRow]:
    term = normalize_search(search.strip())
    return [
        row
        for row in rows
        if (
            not term or term in normalize_search(f"{row['label']} {row['key']}")
        )
        and (status == "Tous" or row["effective"] == (status == "Activés"))
        and (
            level == "Tous"
            or row["level"] == (0 if level == "Principaux" else 1)
        )
    ]


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(32)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, PASSWORD_ROUNDS
    )
    return f"pbkdf2_sha256${PASSWORD_ROUNDS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt, expected = encoded.split("$")
        iterations = int(rounds)
        if (
            algorithm != "pbkdf2_sha256"
            or not 100_000 <= iterations <= 1_000_000
        ):
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt), iterations
        )
        return secrets.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def session_timestamp(session, value: dt.datetime) -> dt.datetime | str:
    if session.get_bind().dialect.name == "sqlite":
        return value.replace(tzinfo=None).isoformat(
            sep=" ", timespec="microseconds"
        )
    return value.astimezone(dt.UTC)


async def account_in_session(
    session, token: str, admin: bool = False
) -> Account:
    row = (
        await session.execute(
            text("""
        SELECT a.id, a.email, a.is_admin FROM menu_auth_account a
        JOIN menu_auth_session s ON s.account_id = a.id
        WHERE s.token_hash = :token AND s.is_revoked = FALSE
          AND s.expires_at > :now LIMIT 1
    """),
            {
                "token": token_hash(token),
                "now": session_timestamp(session, dt.datetime.now(dt.UTC)),
            },
        )
    ).first()
    if row is None or not token or (admin and not bool(row[2])):
        raise PermissionError("Connexion administrateur requise.")
    return {"id": int(row[0]), "email": str(row[1]), "admin": bool(row[2])}


async def resolve_account(token: str) -> Account:
    await ensure_menu_database()
    async with menu_session() as session:
        return await account_in_session(session, token)


async def authenticate(
    email: str, password: str, signup: bool, old_token: str = ""
) -> tuple[str, Account]:
    email = email.strip().lower()
    if len(email) > 320 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValueError("Veuillez saisir une adresse e-mail valide.")
    if not 12 <= len(password) <= 256:
        raise ValueError(
            "Le mot de passe doit contenir entre 12 et 256 caractères."
        )
    await ensure_local_database()
    encoded = await asyncio.to_thread(hash_password, password) if signup else ""
    async with rx.asession() as session:
        if signup:
            await lock_menu_transaction(session)
            count = int(
                (
                    await session.execute(
                        text("SELECT COUNT(*) FROM menu_auth_account")
                    )
                ).scalar()
                or 0
            )
            try:
                result = await session.execute(
                    text(
                        "INSERT INTO menu_auth_account (email, password_hash, is_admin) VALUES (:email, :hash, :admin) RETURNING id"
                    ),
                    {"email": email, "hash": encoded, "admin": count == 0},
                )
                account: Account = {
                    "id": int(result.scalar_one()),
                    "email": email,
                    "admin": count == 0,
                }
            except IntegrityError as e:
                logging.exception("Error: menu account creation failed")
                await session.rollback()
                raise ValueError(
                    "Impossible de créer ce compte. Utilisez la connexion si vous êtes déjà inscrit."
                ) from e
        else:
            row = (
                await session.execute(
                    text(
                        "SELECT id, email, password_hash, is_admin FROM menu_auth_account WHERE email = :email LIMIT 1"
                    ),
                    {"email": email},
                )
            ).first()
            # Même coût de dérivation pour une adresse inconnue.
            fallback = (
                f"pbkdf2_sha256${PASSWORD_ROUNDS}${'00' * 32}${'00' * 32}"
            )
            valid = await asyncio.to_thread(
                verify_password, password, str(row[2]) if row else fallback
            )
            if row is None or not valid:
                raise ValueError("Adresse e-mail ou mot de passe incorrect.")
            account = {
                "id": int(row[0]),
                "email": str(row[1]),
                "admin": bool(row[3]),
            }
        token = secrets.token_urlsafe(48)
        expires = session_timestamp(
            session,
            dt.datetime.now(dt.UTC) + dt.timedelta(seconds=SESSION_SECONDS),
        )
        if old_token:
            await session.execute(
                text(
                    "UPDATE menu_auth_session SET is_revoked = TRUE WHERE token_hash = :token"
                ),
                {"token": token_hash(old_token)},
            )
        await session.execute(
            text(
                "INSERT INTO menu_auth_session (account_id, token_hash, expires_at, is_revoked) VALUES (:id, :token, :expires, FALSE)"
            ),
            {
                "id": account["id"],
                "token": token_hash(token),
                "expires": expires,
            },
        )
        await session.commit()
        return token, account


async def revoke_session(token: str) -> None:
    await ensure_local_database()
    async with rx.asession() as session:
        await session.execute(
            text(
                "UPDATE menu_auth_session SET is_revoked = TRUE WHERE token_hash = :token"
            ),
            {"token": token_hash(token)},
        )
        await session.commit()


async def read_settings(
    token: str = "", require_admin: bool = False
) -> dict[str, bool]:
    await ensure_local_database()
    async with rx.asession() as session:
        if require_admin:
            await account_in_session(session, token, admin=True)
        rows = (
            await session.execute(
                text(
                    "SELECT navigation_key, enabled FROM menu_setting LIMIT 10000"
                )
            )
        ).all()
    return {str(row[0]): bool(row[1]) for row in rows}


async def toggle_setting(token: str, key: str) -> dict[str, bool]:
    await ensure_local_database()
    async with rx.asession() as session:
        await session.execute(text("BEGIN IMMEDIATE"))
        account = await account_in_session(session, token, admin=True)
        allowed = {row["key"] for row in menu_catalog({})}
        if key not in allowed or key in PROTECTED_KEYS:
            raise ValueError("Ce menu ne peut pas être modifié.")
        await session.execute(
            text("""
            INSERT INTO menu_setting (navigation_key, enabled, updated_at, updated_by_account_id)
            VALUES (:key, FALSE, :now, :account)
            ON CONFLICT(navigation_key) DO UPDATE SET enabled = NOT menu_setting.enabled,
                updated_at = :now, updated_by_account_id = :account
        """),
            {
                "key": key,
                "now": session_timestamp(session, dt.datetime.now(dt.UTC)),
                "account": account["id"],
            },
        )
        rows = (
            await session.execute(
                text(
                    "SELECT navigation_key, enabled FROM menu_setting LIMIT 10000"
                )
            )
        ).all()
        await session.commit()
    return {str(row[0]): bool(row[1]) for row in rows}

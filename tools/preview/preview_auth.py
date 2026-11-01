"""Socle d'authentification local de l'aperçu (SQLite).

La base de comptes de production est un service PostgreSQL managé, absent d'un
environnement de prévisualisation hors ligne. Ce module la remplace, pour la
seule copie d'aperçu, par un magasin SQLite appliquant les mêmes règles :
mot de passe de 12 à 256 caractères, dérivation PBKDF2 réutilisée depuis
`app.menu_service`, jeton de session en cookie, premier compte promu
administrateur.

Il n'est jamais importé par l'application du dépôt : `patch_preview.py` le
copie dans la copie d'aperçu, où `menu_service` et `menu_policy` le délèguent.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import os
import pathlib
import secrets
import sqlite3
from typing import Any

DB_PATH = pathlib.Path(
    os.environ.get(
        "AGRI_PRO_PREVIEW_AUTH_DB",
        "/home/user/Gestion-agricole-moderne/.preview/data/preview_auth.db",
    )
)
SESSION_SECONDS = 60 * 60 * 12


def _connect() -> sqlite3.Connection:
    """Ouvre la base locale des comptes (créée au besoin)."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_schema() -> None:
    """Crée les tables de comptes et de sessions (idempotent)."""
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS preview_account (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS preview_session (
                token TEXT PRIMARY KEY,
                account_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                is_revoked INTEGER NOT NULL DEFAULT 0
            );
            """
        )


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def _authenticate_sync(
    email: str, password: str, signup: bool, old_token: str = ""
) -> tuple[str, dict[str, Any]]:
    """Crée ou vérifie un compte, puis ouvre une session."""
    from app.menu_service import hash_password, verify_password

    email = email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValueError("Veuillez saisir une adresse e-mail valide.")
    if not 12 <= len(password) <= 256:
        raise ValueError("Le mot de passe doit contenir entre 12 et 256 caractères.")
    ensure_schema()
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, email, password_hash, is_admin FROM preview_account"
            " WHERE email = ?",
            (email,),
        ).fetchone()
        if signup:
            if row is not None:
                raise ValueError(
                    "Un compte existe déjà avec cette adresse : utilisez la connexion."
                )
            count = connection.execute(
                "SELECT COUNT(*) FROM preview_account"
            ).fetchone()[0]
            admin = 1 if count == 0 else 0
            cursor = connection.execute(
                "INSERT INTO preview_account (email, password_hash, is_admin, created_at)"
                " VALUES (?, ?, ?, ?)",
                (email, hash_password(password), admin, _now().isoformat()),
            )
            account_id, is_admin = int(cursor.lastrowid), bool(admin)
        else:
            if row is None or not verify_password(password, str(row["password_hash"])):
                raise ValueError("Adresse e-mail ou mot de passe incorrect.")
            account_id, is_admin = int(row["id"]), bool(row["is_admin"])
        if old_token:
            connection.execute(
                "UPDATE preview_session SET is_revoked = 1 WHERE token = ?",
                (old_token,),
            )
        token = secrets.token_urlsafe(48)
        connection.execute(
            "INSERT INTO preview_session (token, account_id, expires_at)"
            " VALUES (?, ?, ?)",
            (
                token,
                account_id,
                (_now() + dt.timedelta(seconds=SESSION_SECONDS)).isoformat(),
            ),
        )
        connection.commit()
    return token, {"id": account_id, "email": email, "admin": is_admin}


async def authenticate(
    email: str, password: str, signup: bool, old_token: str = ""
) -> tuple[str, dict[str, Any]]:
    """Version awaitable : la dérivation du mot de passe est bloquante."""
    return await asyncio.to_thread(
        _authenticate_sync, email, password, signup, old_token
    )


def _revoke_sync(token: str) -> None:
    ensure_schema()
    with _connect() as connection:
        connection.execute(
            "UPDATE preview_session SET is_revoked = 1 WHERE token = ?", (token,)
        )
        connection.commit()


async def revoke(token: str) -> None:
    """Révoque une session (déconnexion)."""
    await asyncio.to_thread(_revoke_sync, token)


def account_for(token: str) -> dict[str, Any] | None:
    """Compte associé à un jeton valide, ou None."""
    if not token:
        return None
    ensure_schema()
    with _connect() as connection:
        row = connection.execute(
            "SELECT a.id, a.email, a.is_admin, s.expires_at, s.is_revoked"
            " FROM preview_session s JOIN preview_account a ON a.id = s.account_id"
            " WHERE s.token = ?",
            (token,),
        ).fetchone()
    if row is None or row["is_revoked"]:
        return None
    try:
        expires = dt.datetime.fromisoformat(str(row["expires_at"]))
    except ValueError:
        return None
    if expires <= _now():
        return None
    return {
        "id": int(row["id"]),
        "email": str(row["email"]),
        "admin": bool(row["is_admin"]),
    }


def policy_for(token: str) -> dict[str, Any] | None:
    """Politique d'accès complète pour un jeton valide, sinon None."""
    from app.menu_policy import COCKPITS, GLOBAL_KEYS, PERMISSIONS, visible_entries

    account = account_for(token)
    if account is None:
        return None
    settings = {key: True for key in GLOBAL_KEYS}
    permissions = set(PERMISSIONS)
    navigation = visible_entries(permissions, settings, True)
    parents = {entry["cockpit"] for entry in navigation}
    cockpits = [
        item for item in COCKPITS if item["available"] and item["key"] in parents
    ]
    tabs = sorted(
        {entry["tab"] for entry in navigation if entry["page"] == "crm"} - {""}
    )
    return {
        "id": account["id"],
        "email": account["email"],
        "admin": account["admin"],
        "active": True,
        "roles": ["Administrateur"] if account["admin"] else ["Exploitant"],
        "permissions": sorted(permissions),
        "settings": settings,
        "cockpits": cockpits,
        "navigation": navigation,
        "crm_tabs": tabs,
    }

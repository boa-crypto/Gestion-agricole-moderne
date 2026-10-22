import reflex as rx

import asyncio
import datetime as dt
import os
import logging
import re
import sqlite3
import threading
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path

from sqlalchemy import MetaData, create_engine, select, text
from sqlalchemy.engine import Connection, URL, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.local_db_env import DB_PATH
from app.models import MenuAuthAccount, MenuAuthSession, MenuSetting

MENU_LOCK_ID = 714026839102
MENU_MODELS = (MenuAuthAccount, MenuAuthSession, MenuSetting)
_bootstrap_lock = threading.Lock()


def managed_menu_url(environ: Mapping[str, str] | None = None) -> URL:
    source = os.environ if environ is None else environ
    value = source.get("REFLEX_DB_DIRECT_URL") or source.get(
        "REFLEX_DEV_DB_DIRECT_URL"
    )
    if not value:
        raise RuntimeError(
            "La connexion persistante des menus est indisponible."
        )
    try:
        url = make_url(value)
        if url.drivername.split("+")[0] not in {"postgresql", "postgres"}:
            raise ValueError("Unsupported database")
        if not url.host or not url.database:
            raise ValueError("Incomplete database URL")
        return url.set(drivername="postgresql+psycopg")
    except (ValueError, TypeError, ArgumentError):
        raise RuntimeError(
            "La connexion persistante des menus est invalide."
        ) from None


def menu_metadata() -> MetaData:
    metadata = MetaData()
    for model in MENU_MODELS:
        model.__table__.to_metadata(metadata)
    return metadata


def _utc_timestamp(value: object) -> dt.datetime:
    stamp = (
        value
        if isinstance(value, dt.datetime)
        else dt.datetime.fromisoformat(str(value))
    )
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=dt.UTC)
    return stamp.astimezone(dt.UTC)


def _local_menu_snapshot(path: Path) -> dict[str, list[dict[str, object]]]:
    """Read only, one SQLite snapshot; never initialize the legacy database."""
    if not path.exists():
        return {}
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("BEGIN")
        present = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='menu_auth_account'"
        ).fetchone()
        if not present:
            return {}
        if not connection.execute(
            "SELECT COUNT(*) FROM menu_auth_account"
        ).fetchone()[0]:
            return {}
        result: dict[str, list[dict[str, object]]] = {}
        for model in MENU_MODELS:
            table = model.__table__
            columns = ", ".join(column.name for column in table.columns)
            result[table.name] = [
                dict(row)
                for row in connection.execute(
                    f"SELECT {columns} FROM {table.name} ORDER BY id"
                ).fetchall()
            ]
        return result
    finally:
        connection.close()


def import_local_menu_data(
    connection: Connection, metadata: MetaData, path: Path
) -> None:
    account_table = metadata.tables["menu_auth_account"]
    if (
        connection.execute(select(account_table.c.id).limit(1)).first()
        is not None
    ):
        return
    snapshot = _local_menu_snapshot(path)
    if not snapshot:
        return
    # No merging into a partially populated destination: ambiguity must fail closed.
    for name in ("menu_auth_session", "menu_setting"):
        if (
            connection.execute(
                select(metadata.tables[name].c.id).limit(1)
            ).first()
            is not None
        ):
            raise RuntimeError(
                "Import des identités impossible : destination incohérente."
            )
    account_ids: dict[int, int] = {}
    for original in snapshot["menu_auth_account"]:
        values = dict(original)
        old_id = int(values.pop("id"))
        encoded = str(values["password_hash"])
        if not re.fullmatch(
            r"pbkdf2_sha256\$[0-9]+\$[0-9a-f]{64}\$[0-9a-f]{64}", encoded
        ):
            raise RuntimeError(
                "Import des identités impossible : empreinte invalide."
            )
        rounds = int(encoded.split("$")[1])
        if not 100_000 <= rounds <= 1_000_000:
            raise RuntimeError(
                "Import des identités impossible : empreinte invalide."
            )
        values["is_admin"] = bool(values["is_admin"])
        values["created_at"] = _utc_timestamp(values["created_at"])
        account_ids[old_id] = int(
            connection.execute(
                account_table.insert()
                .values(**values)
                .returning(account_table.c.id)
            ).scalar_one()
        )
    for original in snapshot["menu_auth_session"]:
        values = dict(original)
        values.pop("id")
        if not re.fullmatch(r"[0-9a-f]{64}", str(values["token_hash"])):
            raise RuntimeError(
                "Import des sessions impossible : empreinte invalide."
            )
        values["account_id"] = account_ids[int(values["account_id"])]
        values["is_revoked"] = bool(values["is_revoked"])
        values["expires_at"] = _utc_timestamp(values["expires_at"])
        values["created_at"] = _utc_timestamp(values["created_at"])
        connection.execute(
            metadata.tables["menu_auth_session"].insert().values(**values)
        )
    for original in snapshot["menu_setting"]:
        values = dict(original)
        values.pop("id")
        owner = values["updated_by_account_id"]
        values["updated_by_account_id"] = (
            account_ids[int(owner)] if owner is not None else None
        )
        values["enabled"] = bool(values["enabled"])
        values["updated_at"] = _utc_timestamp(values["updated_at"])
        connection.execute(
            metadata.tables["menu_setting"].insert().values(**values)
        )


def bootstrap_menu_database(*, import_local: bool = True) -> None:
    """Exactly three tables, atomic DDL/import, same lock as first-admin claim."""
    url = managed_menu_url()
    with _bootstrap_lock:
        _bootstrap_menu_database(url, import_local)


@lru_cache(maxsize=4)
def _bootstrap_menu_database(url: URL, import_local: bool) -> None:
    engine = create_engine(
        url,
        pool_pre_ping=True,
        hide_parameters=True,
        connect_args={"connect_timeout": 10},
    )
    try:
        with engine.begin() as connection:
            connection.execute(
                text("SELECT pg_advisory_xact_lock(:key)"),
                {"key": MENU_LOCK_ID},
            )
            metadata = menu_metadata()
            metadata.create_all(connection, checkfirst=True)
            if import_local:
                import_local_menu_data(connection, metadata, DB_PATH)
    except Exception:
        # Sanitize both the propagated exception and its logged traceback.
        try:
            raise RuntimeError(
                "La persistance des menus est indisponible. Aucune identité réinitialisée."
            ) from None
        except RuntimeError as e:
            logging.exception(f"Error: {e}")
            raise
    finally:
        engine.dispose()


async def ensure_menu_database() -> None:
    await asyncio.to_thread(bootstrap_menu_database)


@lru_cache(maxsize=4)
def _managed_session_factory(url: URL) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(
        url,
        pool_pre_ping=True,
        hide_parameters=True,
        connect_args={"connect_timeout": 10},
    )
    return async_sessionmaker(engine, expire_on_commit=False)


def menu_session() -> AsyncSession:
    return _managed_session_factory(managed_menu_url())()


@asynccontextmanager
async def menu_database_lifespan(app: rx.App) -> AsyncIterator[None]:
    await ensure_menu_database()
    try:
        yield
    finally:
        factory = _managed_session_factory(managed_menu_url())
        await factory.kw["bind"].dispose()
        _managed_session_factory.cache_clear()


async def lock_menu_transaction(session: AsyncSession) -> None:
    dialect = session.get_bind().dialect.name
    if dialect == "postgresql":
        await session.execute(
            text("SELECT pg_advisory_xact_lock(:key)"), {"key": MENU_LOCK_ID}
        )
    elif dialect == "sqlite":
        # Only reachable through a substituted session factory in isolated tests.
        await session.execute(text("BEGIN IMMEDIATE"))
    else:
        raise RuntimeError(
            "Dialecte de persistance des menus non pris en charge."
        )

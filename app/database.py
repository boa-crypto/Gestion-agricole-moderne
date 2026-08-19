"""Base de données locale SQLite de l'application.

L'exploitation fonctionne désormais entièrement sur un fichier SQLite
persistant stocké dans le projet. Ce module centralise :

* le chemin du fichier de base et les URL de connexion (synchrone et async),
* la création des tables du modèle métier au démarrage si elles n'existent pas,
* les réglages SQLite utiles (WAL, clés étrangères).

Aucune base externe n'est utilisée ni écrite.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine

from app.local_db_env import (
    ASYNC_DB_URL,
    DATA_DIR,
    DB_PATH,
    PROJECT_ROOT,
    SYNC_DB_URL,
    force_local_database_env,
)
from app.models import (
    AccessScope,
    ActivityLog,
    AppFunction,
    AppPermission,
    AppRole,
    AppUser,
    Base,
    CropCatalogVariety,
    CropCategory,
    CropCulture,
    CropPhenologyProfile,
    CropPhenologyStage,
    CropSpecies,
    CropStageChange,
    CropStageMedia,
    CropStageObservation,
    CropStageRecommendation,
    CrmAuditLog,
    CrmContact,
    CrmDocument,
    CrmDocumentLink,
    CrmEvent,
    CrmInvoice,
    CrmInvoiceItem,
    CrmPartner,
    CrmPayable,
    CrmPayment,
    CrmPurchase,
    CrmPurchaseItem,
    CrmReceivable,
    CrmSale,
    CrmSaleItem,
    CrmScore,
    FarmTeam,
    RemediationLog,
    RoleDelegation,
    RolePermission,
    TeamMember,
    UserAssignment,
    UserRole,
    UserSession,
)

__all__ = [
    "AGRIPRO_ACCESS_TABLES",
    "ASYNC_DB_URL",
    "ensure_agripro_access_tables",
    "init_agripro_access_tables",
    "DATA_DIR",
    "DB_PATH",
    "PROJECT_ROOT",
    "SYNC_DB_URL",
    "ensure_access_tables",
    "ensure_catalog_tables",
    "ensure_crm_tables",
    "ensure_local_database",
    "ensure_phenology_tables",
    "ensure_remediation_log_table",
    "init_access_tables",
    "init_catalog_tables",
    "init_crm_tables",
    "init_local_database",
    "CRM_MODELS",
    "init_phenology_tables",
    "init_remediation_log_table",
    "local_table_exists",
    "local_table_exists_async",
]

# Réexport du DDL idempotent des objets `agripro_*` (socle utilisateurs/RBAC).
from app.access_schema import (  # noqa: E402
    AGRIPRO_ACCESS_TABLES,
    ensure_agripro_access_tables,
    init_agripro_access_tables,
)

_initialized: bool = False


@event.listens_for(Engine, "connect")
def _sqlite_pragmas(dbapi_connection, connection_record) -> None:
    """Active les clés étrangères et le mode WAL sur chaque connexion SQLite.

    Les PRAGMA ne sont émis que si le moteur est réellement SQLite : toute
    autre base (PostgreSQL managé, ...) est laissée intacte.
    """
    module = type(dbapi_connection).__module__ or ""
    engine = getattr(connection_record, "engine", None)
    dialect_name = getattr(getattr(engine, "dialect", None), "name", "")
    if "sqlite" not in module and dialect_name != "sqlite":
        return
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=8000")
        cursor.close()
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")


def init_local_database() -> None:
    """Crée le fichier SQLite et les tables manquantes (idempotent)."""
    global _initialized
    if _initialized:
        return
    force_local_database_env()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(SYNC_DB_URL, future=True)
    try:
        Base.metadata.create_all(engine)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
        raise
    finally:
        engine.dispose()
    _initialized = True


def init_remediation_log_table() -> None:
    """Crée la table locale `remediation_log` si elle manque (idempotent).

    L'initialisation SQLite globale crée déjà toutes les tables du modèle,
    mais un fichier de base antérieur à l'ajout de la traçabilité de
    remédiation peut ne pas la contenir. `create_all(checkfirst=True)` ne
    recrée rien d'existant : l'appel est sans effet une fois la table en place.
    """
    force_local_database_env()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(SYNC_DB_URL, future=True)
    try:
        RemediationLog.__table__.create(bind=engine, checkfirst=True)
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
    finally:
        engine.dispose()


def init_catalog_tables() -> None:
    """Crée les tables du référentiel cultures si elles manquent (idempotent).

    Le référentiel Catégorie → Culture → Espèce → Variété est postérieur au
    fichier SQLite d'origine : `create_all(checkfirst=True)` ne recrée rien
    d'existant, l'appel est donc sans effet une fois les tables en place.
    Aucune migration protégée n'est touchée.
    """
    force_local_database_env()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(SYNC_DB_URL, future=True)
    try:
        for model in (
            CropCategory,
            CropCulture,
            CropSpecies,
            CropCatalogVariety,
        ):
            model.__table__.create(bind=engine, checkfirst=True)
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
    finally:
        engine.dispose()


def init_phenology_tables() -> None:
    """Crée les tables du suivi phénologique si elles manquent (idempotent).

    Le suivi phénologique est postérieur au fichier SQLite d'origine :
    `create_all(checkfirst=True)` ne recrée rien d'existant et ne réinitialise
    jamais la base. Aucune migration protégée n'est touchée.
    """
    force_local_database_env()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(SYNC_DB_URL, future=True)
    try:
        # Les profils dépendent du référentiel structuré des cultures.
        for model in (
            CropCategory,
            CropCulture,
            CropSpecies,
            CropCatalogVariety,
            CropPhenologyProfile,
            CropPhenologyStage,
            CropStageObservation,
            CropStageChange,
            CropStageRecommendation,
            CropStageMedia,
        ):
            model.__table__.create(bind=engine, checkfirst=True)
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
    finally:
        engine.dispose()


def init_access_tables() -> None:
    """Crée les tables du socle utilisateurs/sécurité si elles manquent.

    Le module de gestion des utilisateurs, rôles, permissions, périmètres,
    équipes, affectations, délégations, sessions et journal d'activité est
    postérieur au fichier SQLite d'origine : `create_all(checkfirst=True)` ne
    recrée rien d'existant et ne réinitialise jamais la base. Aucune migration
    protégée n'est touchée.
    """
    force_local_database_env()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(SYNC_DB_URL, future=True)
    try:
        # L'ordre respecte les dépendances de clés étrangères.
        for model in (
            AppFunction,
            AppRole,
            AppPermission,
            RolePermission,
            FarmTeam,
            AppUser,
            UserRole,
            AccessScope,
            TeamMember,
            UserAssignment,
            RoleDelegation,
            UserSession,
            ActivityLog,
        ):
            model.__table__.create(bind=engine, checkfirst=True)
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
    finally:
        engine.dispose()
    # Noms canoniques attendus par l'API RBAC publique (`agripro_*`).
    init_agripro_access_tables()


# Ordre de création respectant les dépendances de clés étrangères du CRM.
CRM_MODELS: tuple[type, ...] = (
    CrmPartner,
    CrmContact,
    CrmSale,
    CrmSaleItem,
    CrmPurchase,
    CrmPurchaseItem,
    CrmInvoice,
    CrmInvoiceItem,
    CrmPayment,
    CrmReceivable,
    CrmPayable,
    CrmDocument,
    CrmDocumentLink,
    CrmEvent,
    CrmScore,
    CrmAuditLog,
)


def init_crm_tables() -> None:
    """Crée les tables du module CRM & Partenaires si elles manquent.

    Le socle CRM (tiers, contacts, ventes, achats, factures, paiements,
    créances, dettes, documents, historique 360°, scores, audit) est postérieur
    au fichier SQLite d'origine : `create(checkfirst=True)` ne recrée rien
    d'existant et ne réinitialise jamais la base. Aucune migration protégée
    n'est touchée.
    """
    force_local_database_env()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(SYNC_DB_URL, future=True)
    try:
        for model in CRM_MODELS:
            model.__table__.create(bind=engine, checkfirst=True)
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
    finally:
        engine.dispose()


async def ensure_crm_tables() -> None:
    """Version awaitable et non bloquante de `init_crm_tables`."""
    await asyncio.to_thread(init_crm_tables)


async def ensure_access_tables() -> None:
    """Version awaitable et non bloquante de `init_access_tables`."""
    await asyncio.to_thread(init_access_tables)


async def ensure_phenology_tables() -> None:
    """Version awaitable et non bloquante de `init_phenology_tables`."""
    await asyncio.to_thread(init_phenology_tables)


async def ensure_catalog_tables() -> None:
    """Version awaitable et non bloquante de `init_catalog_tables`."""
    await asyncio.to_thread(init_catalog_tables)


async def ensure_remediation_log_table() -> None:
    """Version awaitable et non bloquante de `init_remediation_log_table`."""
    await asyncio.to_thread(init_remediation_log_table)


async def ensure_local_database() -> None:
    """Version awaitable de `init_local_database` (idempotente, non bloquante).

    À appeler au début de tout gestionnaire d'événement asynchrone susceptible
    d'interroger la base **avant** que la page d'accueil n'ait initialisé le
    fichier SQLite (chargement direct d'une page, rechargement à chaud, test
    unitaire isolé...). La création des tables se fait dans un thread pour ne
    pas bloquer la boucle d'événements.
    """
    if _initialized:
        return
    await asyncio.to_thread(init_local_database)
    await asyncio.to_thread(init_remediation_log_table)
    await asyncio.to_thread(init_catalog_tables)
    await asyncio.to_thread(init_phenology_tables)
    await asyncio.to_thread(init_access_tables)
    await asyncio.to_thread(init_crm_tables)


# Introspection portable sans PRAGMA
# `information_schema` ailleurs. Cela évite les `disk I/O error` observés lors
# d'accès concurrents en mode WAL.
_SQLITE_TABLE_QUERY = (
    "SELECT 1 FROM sqlite_master "
    "WHERE type IN ('table', 'view') AND name = :name LIMIT 1"
)
_GENERIC_TABLE_QUERY = (
    "SELECT 1 FROM information_schema.tables WHERE table_name = :name LIMIT 1"
)


def _table_query(dialect_name: str) -> str:
    if dialect_name == "sqlite":
        return _SQLITE_TABLE_QUERY
    return _GENERIC_TABLE_QUERY


def local_table_exists(table_name: str) -> bool | None:
    """Indique si une table existe dans la base locale.

    Retourne `True`/`False` si l'introspection aboutit, et `None` lorsque le
    moteur refuse temporairement l'accès (verrou, WAL, `disk I/O error`,
    volume en lecture seule...). Aucune exception n'est propagée et aucune
    trace ERROR n'est émise : l'appelant décide du repli.
    """
    engine = create_engine(SYNC_DB_URL, future=True)
    try:
        with engine.connect() as connection:
            dialect = getattr(connection.dialect, "name", "")
            row = connection.execute(
                text(_table_query(dialect)), {"name": table_name}
            ).first()
        return row is not None
    except Exception as e:  # noqa: BLE001
        logging.exception("Unexpected error")
        logging.warning(
            "Introspection locale indisponible pour la table '%s' (%s) : "
            "résultat indéterminé.",
            table_name,
            e,
        )
        return None
    finally:
        try:
            engine.dispose()
        except Exception as e:  # noqa: BLE001
            logging.exception("Unexpected error")
            logging.debug(f"Moteur SQLite non libéré proprement: {e}")


async def local_table_exists_async(table_name: str) -> bool | None:
    """Version asynchrone de `local_table_exists` via `rx.asession()`.

    Retourne `None` si l'introspection échoue (base verrouillée, erreur d'E/S,
    session indisponible), afin que l'appelant puisse se replier sans jamais
    bloquer le chargement de l'application.
    """
    import reflex as rx  # import local : évite un import circulaire

    try:
        async with rx.asession() as asession:
            connection = await asession.connection()
            dialect = getattr(connection.dialect, "name", "")
            row = (
                await asession.execute(
                    text(_table_query(dialect)), {"name": table_name}
                )
            ).first()
        return row is not None
    except Exception as e:  # noqa: BLE001
        logging.exception("Unexpected error")
        logging.warning(
            "Introspection asynchrone indisponible pour la table '%s' (%s).",
            table_name,
            e,
        )
        return None

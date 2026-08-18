"""DDL idempotent du socle utilisateurs / RBAC sous les noms `agripro_*`.

Le socle sécurité est physiquement stocké dans les tables locales déjà créées
par `app/database.py` (`app_user`, `app_role`, `app_permission`, `farm_team`,
`user_role`, `role_permission`, `user_assignment`, `role_delegation`,
`activity_log`, ...). L'API publique et les contrôles serveur attendent
toutefois de pouvoir interroger ce socle sous les noms canoniques
`agripro_user`, `agripro_function`, `agripro_role`, `agripro_permission`,
`agripro_team`, `agripro_user_role`, `agripro_role_permission`,
`agripro_assignment`, `agripro_delegation` et `agripro_activity_log`.

Ce module crée ces objets **de façon idempotente et en SQL brut**, sous forme de
vues nommées adossées aux tables physiques : aucune donnée n'est dupliquée,
aucune migration protégée n'est touchée, et les colonnes historiques sont
exposées avec leurs alias attendus (`matricule` → `employee_code`,
`primary_role_id` → `role_id`, ...).

Deux points d'entrée :

* `init_agripro_access_tables()` — synchrone, appelée par
  `app.database.init_access_tables()` (et donc par `ensure_local_database()`) ;
* `ensure_agripro_access_tables()` — variante awaitable non bloquante, appelée
  par `app.seed_access.seed_access_data()` avant toute insertion ou lecture.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import create_engine, text

from app.local_db_env import DATA_DIR, SYNC_DB_URL, force_local_database_env

__all__ = [
    "AGRIPRO_ACCESS_OBJECTS",
    "AGRIPRO_ACCESS_TABLES",
    "ensure_agripro_access_tables",
    "ensure_agripro_tables",
    "init_agripro_access_tables",
]

# Ordre d'exposition : les noms exigés par le socle RBAC public.
AGRIPRO_ACCESS_TABLES: tuple[str, ...] = (
    "agripro_function",
    "agripro_role",
    "agripro_permission",
    "agripro_team",
    "agripro_user",
    "agripro_user_role",
    "agripro_role_permission",
    "agripro_assignment",
    "agripro_delegation",
    "agripro_activity_log",
)

# Objets complémentaires, utiles aux écrans sécurité (périmètres, sessions,
# appartenance aux équipes) : créés dans la même passe idempotente.
_EXTRA_OBJECTS: tuple[str, ...] = (
    "agripro_scope",
    "agripro_team_member",
    "agripro_session",
)

AGRIPRO_ACCESS_OBJECTS: tuple[str, ...] = AGRIPRO_ACCESS_TABLES + _EXTRA_OBJECTS

# Chaque définition est un SELECT complet sur la table physique existante.
_DEFINITIONS: dict[str, str] = {
    "agripro_function": """
        SELECT f.id AS id,
               f.key AS key,
               f.name AS name,
               f.name AS label,
               f.family AS family,
               COALESCE(f.mission, '') AS mission,
               COALESCE(f.responsibilities, '') AS responsibilities,
               COALESCE(f.default_role_key, '') AS default_role_key,
               COALESCE(f.icon, 'user') AS icon,
               COALESCE(f.color_hex, '#a3e635') AS color_hex,
               COALESCE(f.position, 0) AS position,
               f.is_active AS is_active,
               f.created_at AS created_at
        FROM app_function f
    """,
    "agripro_role": """
        SELECT r.id AS id,
               r.key AS key,
               r.name AS name,
               r.name AS label,
               COALESCE(r.level, 0) AS level,
               COALESCE(r.tagline, '') AS tagline,
               COALESCE(r.description, '') AS description,
               COALESCE(r.icon, 'shield') AS icon,
               COALESCE(r.color_hex, '#a3e635') AS color_hex,
               r.is_system AS is_system,
               COALESCE(r.position, 0) AS position,
               r.is_active AS is_active,
               r.created_at AS created_at
        FROM app_role r
    """,
    "agripro_permission": """
        SELECT p.id AS id,
               p.key AS key,
               p.module AS module,
               p.action AS action,
               COALESCE(p.label, p.key) AS label,
               COALESCE(p.description, '') AS description,
               COALESCE(p.module_route, '/') AS module_route,
               COALESCE(p.icon, 'key-round') AS icon,
               p.is_sensitive AS is_sensitive,
               COALESCE(p.position, 0) AS position,
               p.created_at AS created_at
        FROM app_permission p
    """,
    "agripro_team": """
        SELECT t.id AS id,
               t.key AS key,
               t.name AS name,
               COALESCE(t.code, '') AS code,
               t.leader_id AS leader_id,
               t.function_id AS function_id,
               COALESCE(t.activity, '') AS activity,
               COALESCE(t.schedule, '') AS schedule,
               COALESCE(t.farm_key, '') AS farm_key,
               COALESCE(t.sector, '') AS sector,
               t.status AS status,
               COALESCE(t.icon, 'users') AS icon,
               COALESCE(t.color_hex, '#a3e635') AS color_hex,
               COALESCE(t.notes, '') AS notes,
               t.created_at AS created_at
        FROM farm_team t
    """,
    "agripro_user": """
        SELECT u.id AS id,
               u.matricule AS matricule,
               u.matricule AS employee_code,
               u.first_name AS first_name,
               u.last_name AS last_name,
               (u.first_name || ' ' || u.last_name) AS full_name,
               COALESCE(u.email, '') AS email,
               COALESCE(u.phone, '') AS phone,
               COALESCE(u.address, '') AS address,
               COALESCE(u.photo_seed, '') AS photo_seed,
               u.function_id AS function_id,
               u.primary_role_id AS primary_role_id,
               u.primary_role_id AS role_id,
               u.team_id AS team_id,
               u.manager_id AS manager_id,
               u.employee_id AS employee_id,
               COALESCE(u.farm_key, '') AS farm_key,
               COALESCE(u.sector, '') AS sector,
               u.status AS status,
               u.hired_on AS hired_on,
               u.last_login_at AS last_login_at,
               u.mfa_enabled AS mfa_enabled,
               COALESCE(u.mfa_method, 'AUCUNE') AS mfa_method,
               COALESCE(u.notes, '') AS notes,
               u.created_at AS created_at
        FROM app_user u
    """,
    "agripro_user_role": """
        SELECT ur.id AS id,
               ur.user_id AS user_id,
               ur.role_id AS role_id,
               ur.is_primary AS is_primary,
               COALESCE(ur.granted_by, '') AS granted_by,
               ur.granted_on AS granted_on,
               COALESCE(ur.notes, '') AS notes
        FROM user_role ur
    """,
    "agripro_role_permission": """
        SELECT rp.id AS id,
               rp.role_id AS role_id,
               rp.permission_id AS permission_id,
               rp.scope_kind AS scope_kind,
               rp.is_granted AS is_granted,
               COALESCE(rp.notes, '') AS notes
        FROM role_permission rp
    """,
    "agripro_assignment": """
        SELECT a.id AS id,
               a.user_id AS user_id,
               COALESCE(a.farm_key, '') AS farm_key,
               COALESCE(a.sector, '') AS sector,
               a.parcel_id AS parcel_id,
               a.crop_id AS crop_id,
               a.team_id AS team_id,
               COALESCE(a.activity, '') AS activity,
               COALESCE(a.season, '') AS season,
               a.is_responsible AS is_responsible,
               a.start_date AS start_date,
               a.end_date AS end_date,
               COALESCE(a.notes, '') AS notes,
               a.created_at AS created_at
        FROM user_assignment a
    """,
    "agripro_delegation": """
        SELECT d.id AS id,
               d.delegator_id AS delegator_id,
               d.delegate_id AS delegate_id,
               d.role_id AS role_id,
               d.permission_id AS permission_id,
               d.scope_kind AS scope_kind,
               d.parcel_id AS parcel_id,
               d.team_id AS team_id,
               COALESCE(d.reason, '') AS reason,
               COALESCE(d.authorized_by, '') AS authorized_by,
               d.start_date AS start_date,
               d.end_date AS end_date,
               d.status AS status,
               COALESCE(d.notes, '') AS notes,
               d.created_at AS created_at
        FROM role_delegation d
    """,
    "agripro_activity_log": """
        SELECT l.id AS id,
               l.user_id AS user_id,
               COALESCE(l.actor_label, 'Système') AS actor_label,
               l.kind AS kind,
               COALESCE(l.module, '') AS module,
               COALESCE(l.action, '') AS action,
               COALESCE(l.object_type, '') AS object_type,
               COALESCE(l.object_ref, '') AS object_ref,
               COALESCE(l.object_id, 0) AS object_id,
               COALESCE(l.summary, '') AS summary,
               COALESCE(l.scope_label, '') AS scope_label,
               l.parcel_id AS parcel_id,
               l.team_id AS team_id,
               COALESCE(l.ip_address, '') AS ip_address,
               l.is_sensitive AS is_sensitive,
               l.occurred_at AS occurred_at,
               l.created_at AS created_at
        FROM activity_log l
    """,
    "agripro_scope": """
        SELECT s.id AS id,
               s.user_id AS user_id,
               s.scope_kind AS scope_kind,
               COALESCE(s.farm_key, '') AS farm_key,
               COALESCE(s.site, '') AS site,
               COALESCE(s.sector, '') AS sector,
               s.parcel_id AS parcel_id,
               s.crop_id AS crop_id,
               s.team_id AS team_id,
               COALESCE(s.activity, '') AS activity,
               COALESCE(s.season, '') AS season,
               s.is_readonly AS is_readonly,
               COALESCE(s.note, '') AS note,
               s.created_at AS created_at
        FROM access_scope s
    """,
    "agripro_team_member": """
        SELECT m.id AS id,
               m.team_id AS team_id,
               m.user_id AS user_id,
               COALESCE(m.role_in_team, 'Membre') AS role_in_team,
               m.joined_on AS joined_on,
               COALESCE(m.notes, '') AS notes
        FROM team_member m
    """,
    "agripro_session": """
        SELECT s.id AS id,
               s.user_id AS user_id,
               s.token_hash AS token_hash,
               COALESCE(s.device, '') AS device,
               COALESCE(s.ip_address, '') AS ip_address,
               COALESCE(s.user_agent, '') AS user_agent,
               s.mfa_passed AS mfa_passed,
               COALESCE(s.mfa_method, 'AUCUNE') AS mfa_method,
               s.status AS status,
               s.started_at AS started_at,
               s.last_seen_at AS last_seen_at,
               s.expires_at AS expires_at,
               COALESCE(s.notes, '') AS notes
        FROM user_session s
    """,
}

_initialized: bool = False


def _existing_objects(connection, dialect: str) -> set[str]:
    """Noms des tables et vues déjà présentes dans la base locale."""
    if dialect == "sqlite":
        statement = text(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
        )
    else:
        statement = text(
            "SELECT table_name FROM information_schema.tables "
            "UNION SELECT table_name FROM information_schema.views"
        )
    return {str(row[0]) for row in connection.execute(statement).all()}


def init_agripro_access_tables(force: bool = False) -> list[str]:
    """Crée les objets `agripro_*` manquants (idempotent, SQL brut).

    Retourne la liste des noms effectivement créés lors de l'appel. Rejouée,
    la fonction ne recrée rien et ne supprime jamais un objet existant : un
    `agripro_user` déjà matérialisé sous forme de table physique est conservé
    tel quel.
    """
    global _initialized
    if _initialized and not force:
        return []

    force_local_database_env()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(SYNC_DB_URL, future=True)
    created: list[str] = []
    try:
        with engine.begin() as connection:
            dialect = getattr(connection.dialect, "name", "")
            existing = _existing_objects(connection, dialect)
            for name in AGRIPRO_ACCESS_OBJECTS:
                if name in existing:
                    continue
                definition = _DEFINITIONS[name].strip()
                connection.execute(text(f"CREATE VIEW {name} AS {definition}"))
                created.append(name)
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
        return created
    finally:
        engine.dispose()

    _initialized = True
    return created


async def ensure_agripro_access_tables(force: bool = False) -> list[str]:
    """Variante awaitable et non bloquante de `init_agripro_access_tables`."""
    return await asyncio.to_thread(init_agripro_access_tables, force)


# Alias court, utilisé par les amorçages et les contrôles serveur.
ensure_agripro_tables = ensure_agripro_access_tables

"""Amorçage idempotent du socle utilisateurs, rôles et sécurité AgriPro.

Insère, en SQL brut via `rx.asession()` :

* les fonctions agricoles (direction, production, terrain, logistique,
  administration) décrites dans `app/access_reference.py` ;
* les rôles applicatifs (propriétaire, chef d'exploitation, responsable
  irrigation / stock / matériel, chef d'équipe, ouvrier, comptable,
  consultation) ;
* la matrice de permissions granulaires module × action et son affectation aux
  rôles (RBAC) ;
* des utilisateurs d'exemple réalistes, reliés quand c'est possible au registre
  du personnel existant (`employee`) ;
* les équipes agricoles, leurs membres, les périmètres et les affectations
  rattachés aux **parcelles et cultures réellement présentes** en base ;
* une délégation temporaire active, une délégation expirée, des sessions avec
  MFA représentée et quelques entrées du journal d'activité.

L'amorçage n'insère que ce qui manque : il peut être rejoué sans dupliquer une
ligne. Aucune migration protégée n'est touchée ; les tables locales sont créées
par `init_access_tables()`.
"""

from __future__ import annotations

import datetime
import logging

import reflex as rx
from sqlalchemy import text

from app.access_reference import (
    ACCESS_MODULES,
    ACTION_LABELS,
    FAMILY_COLORS,
    FARM_KEY,
    FUNCTIONS,
    MODULE_BY_KEY,
    ROLES,
    is_sensitive_permission,
    permission_key,
    role_permission_pairs,
)
from app.access_control import hash_token, log_activity
from app.access_schema import ensure_agripro_access_tables
from app.database import init_access_tables, init_local_database
from app.seed import seed_dashboard_data
from app.seed_employees import seed_employee_data

__all__ = ["access_totals", "seed_access_data"]

_seeded: bool = False


# (clé, nom, code, activité, horaires, secteur, couleur, icône)
TEAMS: list[tuple[str, str, str, str, str, str, str, str]] = [
    (
        "equipe-irrigation",
        "Équipe Irrigation",
        "EQ-IRR",
        "Tours d'eau, réseau et sondes",
        "05h00 - 13h00",
        "Nord",
        "#38bdf8",
        "droplets",
    ),
    (
        "equipe-recolte",
        "Équipe Récolte",
        "EQ-REC",
        "Chantiers de récolte et transport",
        "06h00 - 20h00 en campagne",
        "Centre",
        "#fbbf24",
        "wheat",
    ),
    (
        "equipe-traitement",
        "Équipe Traitement",
        "EQ-TRT",
        "Applications phytosanitaires habilitées",
        "05h30 - 12h00",
        "Sud",
        "#a3e635",
        "spray-can",
    ),
    (
        "equipe-maintenance",
        "Équipe Maintenance",
        "EQ-MNT",
        "Atelier, entretien préventif et curatif",
        "08h00 - 17h00",
        "Centre",
        "#f97316",
        "wrench",
    ),
    (
        "equipe-plantation",
        "Équipe Plantation",
        "EQ-PLT",
        "Semis, plantation et travail du sol",
        "07h00 - 16h00",
        "Nord",
        "#4ade80",
        "sprout",
    ),
]


USERS: list[dict] = [
    {
        "matricule": "U001",
        "first_name": "Mohamed",
        "last_name": "Benali",
        "email": "mohamed.benali@agripro.farm",
        "phone": "06 11 22 33 44",
        "function": "proprietaire",
        "roles": ["proprietaire"],
        "team": "",
        "manager": "",
        "sector": "",
        "employee_code": "",
        "status": "ACTIF",
        "hired_offset": 5200,
        "mfa": "CLE_MATERIELLE",
        "notes": "Détient l'exploitation et la gouvernance des accès AgriPro.",
        "scopes": [{"kind": "EXPLOITATION"}],
        "assignments": [],
    },
    {
        "matricule": "U002",
        "first_name": "Karim",
        "last_name": "Haddad",
        "email": "karim.haddad@agripro.farm",
        "phone": "06 22 44 66 88",
        "function": "directeur-exploitation",
        "roles": ["chef-exploitation"],
        "team": "",
        "manager": "U001",
        "sector": "Centre",
        "employee_code": "",
        "status": "ACTIF",
        "hired_offset": 3100,
        "mfa": "APPLICATION",
        "notes": "Pilote la campagne, valide les chantiers et les achats.",
        "scopes": [{"kind": "EXPLOITATION"}],
        "assignments": [],
    },
    {
        "matricule": "U003",
        "first_name": "Camille",
        "last_name": "Roux",
        "email": "camille.roux@agripro.farm",
        "phone": "06 12 45 78 03",
        "function": "agronome",
        "roles": ["responsable-production"],
        "team": "equipe-traitement",
        "manager": "U002",
        "sector": "Sud",
        "employee_code": "E01",
        "status": "ACTIF",
        "hired_offset": 2600,
        "mfa": "APPLICATION",
        "notes": "Référente protection des cultures et notations sanitaires.",
        "scopes": [
            {"kind": "PARCELLE", "parcel": "P01"},
            {"kind": "PARCELLE", "parcel": "P04"},
            {"kind": "EQUIPE", "team": "equipe-traitement"},
            {"kind": "ACTIVITE", "activity": "Protection des cultures"},
        ],
        "assignments": [
            {
                "parcel": "P01",
                "team": "equipe-traitement",
                "activity": "Protection des cultures",
                "responsible": True,
            },
            {
                "parcel": "P04",
                "team": "equipe-traitement",
                "activity": "Protection des cultures",
                "responsible": True,
            },
        ],
    },
    {
        "matricule": "U004",
        "first_name": "Ahmed",
        "last_name": "Benali",
        "email": "ahmed.benali@agripro.farm",
        "phone": "07 33 55 77 99",
        "function": "chef-equipe-irrigation",
        "roles": ["responsable-irrigation"],
        "team": "equipe-irrigation",
        "manager": "U002",
        "sector": "Nord",
        "employee_code": "",
        "status": "ACTIF",
        "hired_offset": 1800,
        "mfa": "SMS",
        "notes": "Conduit les tours d'eau sur les îlots P01, P02 et P05.",
        "scopes": [
            {"kind": "PARCELLE", "parcel": "P01"},
            {"kind": "PARCELLE", "parcel": "P02"},
            {"kind": "PARCELLE", "parcel": "P05"},
            {"kind": "EQUIPE", "team": "equipe-irrigation"},
            {"kind": "ACTIVITE", "activity": "Irrigation"},
        ],
        "assignments": [
            {
                "parcel": "P01",
                "team": "equipe-irrigation",
                "activity": "Irrigation",
                "responsible": True,
            },
            {
                "parcel": "P02",
                "team": "equipe-irrigation",
                "activity": "Irrigation",
                "responsible": True,
            },
            {
                "parcel": "P05",
                "team": "equipe-irrigation",
                "activity": "Irrigation",
                "responsible": True,
            },
        ],
    },
    {
        "matricule": "U005",
        "first_name": "Marc",
        "last_name": "Delaunay",
        "email": "marc.delaunay@agripro.farm",
        "phone": "06 77 30 19 42",
        "function": "chef-equipe",
        "roles": ["chef-equipe"],
        "team": "equipe-recolte",
        "manager": "U002",
        "sector": "Centre",
        "employee_code": "E02",
        "status": "ACTIF",
        "hired_offset": 4100,
        "mfa": "SMS",
        "notes": "Chef de plaine, encadre les chantiers de semis et de récolte.",
        "scopes": [
            {"kind": "SECTEUR", "sector": "Plateau"},
            {"kind": "PARCELLE", "parcel": "P05"},
            {"kind": "PARCELLE", "parcel": "P06"},
            {"kind": "EQUIPE", "team": "equipe-recolte"},
        ],
        "assignments": [
            {
                "parcel": "P05",
                "team": "equipe-recolte",
                "activity": "Travail du sol",
                "responsible": True,
            },
            {
                "parcel": "P06",
                "team": "equipe-plantation",
                "activity": "Semis",
                "responsible": True,
            },
        ],
    },
    {
        "matricule": "U006",
        "first_name": "Yanis",
        "last_name": "Berger",
        "email": "yanis.berger@agripro.farm",
        "phone": "07 61 22 88 14",
        "function": "agent-irrigation",
        "roles": ["ouvrier"],
        "team": "equipe-irrigation",
        "manager": "U004",
        "sector": "Nord",
        "employee_code": "E03",
        "status": "ACTIF",
        "hired_offset": 1450,
        "mfa": "AUCUNE",
        "notes": "Applique les consignes d'irrigation sur la Prairie du Moulin.",
        "scopes": [
            {"kind": "PARCELLE", "parcel": "P03"},
            {"kind": "PERSONNEL"},
        ],
        "assignments": [
            {
                "parcel": "P03",
                "team": "equipe-irrigation",
                "activity": "Irrigation",
                "responsible": False,
            }
        ],
    },
    {
        "matricule": "U007",
        "first_name": "Thomas",
        "last_name": "Guerin",
        "email": "thomas.guerin@agripro.farm",
        "phone": "06 38 55 90 27",
        "function": "responsable-materiel",
        "roles": ["responsable-materiel"],
        "team": "equipe-maintenance",
        "manager": "U002",
        "sector": "Centre",
        "employee_code": "E05",
        "status": "ACTIF",
        "hired_offset": 3200,
        "mfa": "APPLICATION",
        "notes": "Responsable de l'atelier et des échéances réglementaires.",
        "scopes": [
            {"kind": "EQUIPE", "team": "equipe-maintenance"},
            {"kind": "ACTIVITE", "activity": "Maintenance"},
        ],
        "assignments": [
            {
                "parcel": "",
                "team": "equipe-maintenance",
                "activity": "Maintenance",
                "responsible": True,
            }
        ],
    },
    {
        "matricule": "U008",
        "first_name": "Sonia",
        "last_name": "Amrani",
        "email": "sonia.amrani@agripro.farm",
        "phone": "07 12 90 44 08",
        "function": "responsable-stock",
        "roles": ["responsable-stock"],
        "team": "",
        "manager": "U002",
        "sector": "Centre",
        "employee_code": "",
        "status": "ACTIF",
        "hired_offset": 900,
        "mfa": "APPLICATION",
        "notes": "Tient le magasin d'intrants et les seuils de réapprovisionnement.",
        "scopes": [
            {"kind": "SITE", "site": "Magasin d'intrants"},
            {"kind": "ACTIVITE", "activity": "Stocks"},
        ],
        "assignments": [],
    },
    {
        "matricule": "U009",
        "first_name": "Latifa",
        "last_name": "Cherif",
        "email": "latifa.cherif@agripro.farm",
        "phone": "06 45 12 78 30",
        "function": "comptable",
        "roles": ["comptable"],
        "team": "",
        "manager": "U001",
        "sector": "",
        "employee_code": "",
        "status": "ACTIF",
        "hired_offset": 2200,
        "mfa": "EMAIL",
        "notes": "Suit les charges, les ventes et les marges par îlot.",
        "scopes": [{"kind": "EXPLOITATION", "readonly": True}],
        "assignments": [],
    },
    {
        "matricule": "U010",
        "first_name": "Laura",
        "last_name": "Fontaine",
        "email": "laura.fontaine@agripro.farm",
        "phone": "07 45 63 12 78",
        "function": "technicien-agricole",
        "roles": ["consultation"],
        "team": "equipe-traitement",
        "manager": "U003",
        "sector": "Sud",
        "employee_code": "E06",
        "status": "EN_ATTENTE",
        "hired_offset": 330,
        "mfa": "AUCUNE",
        "notes": "Apprentie agronomie, accès en lecture le temps de la formation.",
        "scopes": [{"kind": "PERSONNEL"}],
        "assignments": [],
    },
]


async def _keys(asession, table: str, column: str = "key") -> dict[str, int]:
    rows = (
        await asession.execute(text(f"SELECT {column}, id FROM {table}"))
    ).all()
    return {str(row[0]): int(row[1]) for row in rows}


async def _scalar(asession, sql: str, params: dict) -> int:
    value = (await asession.execute(text(sql), params)).scalar()
    return int(value or 0)


async def access_totals() -> dict[str, int]:
    """Volumes consolidés du socle sécurité (lecture seule)."""
    init_local_database()
    init_access_tables()
    await ensure_agripro_access_tables()
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text(
                    """
                    SELECT
                        (SELECT COUNT(*) FROM app_function),
                        (SELECT COUNT(*) FROM app_role),
                        (SELECT COUNT(*) FROM app_permission),
                        (SELECT COUNT(*) FROM role_permission),
                        (SELECT COUNT(*) FROM app_user),
                        (SELECT COUNT(*) FROM user_role),
                        (SELECT COUNT(*) FROM access_scope),
                        (SELECT COUNT(*) FROM farm_team),
                        (SELECT COUNT(*) FROM team_member),
                        (SELECT COUNT(*) FROM user_assignment),
                        (SELECT COUNT(*) FROM role_delegation),
                        (SELECT COUNT(*) FROM user_session),
                        (SELECT COUNT(*) FROM activity_log)
                    """
                )
            )
        ).first()
    labels = [
        "functions",
        "roles",
        "permissions",
        "role_permissions",
        "users",
        "user_roles",
        "scopes",
        "teams",
        "team_members",
        "assignments",
        "delegations",
        "sessions",
        "activities",
    ]
    return {
        label: int(row[index] or 0) if row else 0
        for index, label in enumerate(labels)
    }


async def seed_access_data() -> None:
    """Amorce le socle utilisateurs et sécurité AgriPro (idempotent)."""
    global _seeded
    if _seeded:
        return

    init_local_database()
    init_access_tables()
    # Garantit la présence des objets `agripro_*` avant toute écriture/lecture.
    await ensure_agripro_access_tables()
    # Les affectations et périmètres s'appuient sur le foncier et le personnel.
    await seed_dashboard_data()
    await seed_employee_data()

    today = datetime.date.today()
    now = datetime.datetime.now(datetime.timezone.utc)

    try:
        async with rx.asession() as asession:
            # --- 1) Fonctions agricoles --------------------------------
            functions = await _keys(asession, "app_function")
            for position, spec in enumerate(FUNCTIONS, start=1):
                if spec["key"] in functions:
                    continue
                await asession.execute(
                    text(
                        """
                        INSERT INTO app_function (
                            key, name, family, mission, responsibilities,
                            default_role_key, icon, color_hex, position, is_active
                        ) VALUES (
                            :key, :name, :family, :mission, :responsibilities,
                            :default_role_key, :icon, :color_hex, :position, 1
                        )
                        """
                    ),
                    {
                        "key": spec["key"],
                        "name": spec["name"],
                        "family": spec["family"],
                        "mission": spec["mission"],
                        "responsibilities": spec["responsibilities"],
                        "default_role_key": spec["default_role"],
                        "icon": spec["icon"],
                        "color_hex": FAMILY_COLORS.get(
                            spec["family"], "#a3e635"
                        ),
                        "position": position,
                    },
                )
            functions = await _keys(asession, "app_function")

            # --- 2) Rôles applicatifs ----------------------------------
            roles = await _keys(asession, "app_role")
            for position, role in enumerate(ROLES, start=1):
                if role["key"] in roles:
                    continue
                await asession.execute(
                    text(
                        """
                        INSERT INTO app_role (
                            key, name, level, tagline, description, icon,
                            color_hex, is_system, position, is_active
                        ) VALUES (
                            :key, :name, :level, :tagline, :description, :icon,
                            :color_hex, :is_system, :position, 1
                        )
                        """
                    ),
                    {
                        "key": role["key"],
                        "name": role["name"],
                        "level": role["level"],
                        "tagline": role["tagline"],
                        "description": role["tagline"],
                        "icon": role["icon"],
                        "color_hex": role["color_hex"],
                        "is_system": 1 if role["is_system"] else 0,
                        "position": position,
                    },
                )
            roles = await _keys(asession, "app_role")

            # --- 3) Permissions granulaires module × action -------------
            permissions = await _keys(asession, "app_permission")
            position = 0
            for spec in ACCESS_MODULES:
                for action in spec["actions"]:
                    position += 1
                    key = permission_key(spec["key"], action)
                    if key in permissions:
                        continue
                    await asession.execute(
                        text(
                            """
                            INSERT INTO app_permission (
                                key, module, action, label, description,
                                module_route, icon, is_sensitive, position
                            ) VALUES (
                                :key, :module, :action, :label, :description,
                                :route, :icon, :is_sensitive, :position
                            )
                            """
                        ),
                        {
                            "key": key,
                            "module": spec["key"],
                            "action": action,
                            "label": (
                                f"{ACTION_LABELS.get(action, action)} · "
                                f"{spec['label']}"
                            ),
                            "description": (
                                f"Autorise l'action « "
                                f"{ACTION_LABELS.get(action, action)} » sur le "
                                f"module {spec['label']}."
                            ),
                            "route": spec["route"],
                            "icon": spec["icon"],
                            "is_sensitive": 1
                            if is_sensitive_permission(spec["key"], action)
                            else 0,
                            "position": position,
                        },
                    )
            permissions = await _keys(asession, "app_permission")

            # --- 4) Matrice RBAC rôle → permissions ---------------------
            existing_pairs = {
                (int(row[0]), int(row[1]))
                for row in (
                    await asession.execute(
                        text(
                            "SELECT role_id, permission_id FROM role_permission"
                        )
                    )
                ).all()
            }
            for role in ROLES:
                role_id = roles.get(role["key"])
                if role_id is None:
                    continue
                for module_key, action in role_permission_pairs(role["key"]):
                    permission_id = permissions.get(
                        permission_key(module_key, action)
                    )
                    if permission_id is None:
                        continue
                    if (role_id, permission_id) in existing_pairs:
                        continue
                    spec = MODULE_BY_KEY.get(module_key)
                    await asession.execute(
                        text(
                            """
                            INSERT INTO role_permission (
                                role_id, permission_id, scope_kind, is_granted,
                                notes
                            ) VALUES (
                                :role_id, :permission_id, :scope_kind, 1, :notes
                            )
                            """
                        ),
                        {
                            "role_id": role_id,
                            "permission_id": permission_id,
                            "scope_kind": "EXPLOITATION"
                            if role["level"] >= 70
                            else "PARCELLE",
                            "notes": (
                                f"Accordé par la matrice RBAC "
                                f"({role['name']} → "
                                f"{spec['label'] if spec else module_key})."
                            ),
                        },
                    )
                    existing_pairs.add((role_id, permission_id))

            # --- 5) Équipes agricoles -----------------------------------
            teams = await _keys(asession, "farm_team")
            for (
                key,
                name,
                code,
                activity,
                schedule,
                sector,
                color,
                icon,
            ) in TEAMS:
                if key in teams:
                    continue
                await asession.execute(
                    text(
                        """
                        INSERT INTO farm_team (
                            key, name, code, leader_id, function_id, activity,
                            schedule, farm_key, sector, status, icon, color_hex,
                            notes
                        ) VALUES (
                            :key, :name, :code, NULL, NULL, :activity,
                            :schedule, :farm_key, :sector, 'ACTIVE', :icon,
                            :color_hex, :notes
                        )
                        """
                    ),
                    {
                        "key": key,
                        "name": name,
                        "code": code,
                        "activity": activity,
                        "schedule": schedule,
                        "farm_key": FARM_KEY,
                        "sector": sector,
                        "icon": icon,
                        "color_hex": color,
                        "notes": f"Équipe {name.lower()} du {FARM_KEY}.",
                    },
                )
            teams = await _keys(asession, "farm_team")

            # --- 6) Utilisateurs ----------------------------------------
            parcels = {
                str(row[0]): int(row[1])
                for row in (
                    await asession.execute(
                        text("SELECT COALESCE(code, ''), id FROM parcel")
                    )
                ).all()
            }
            crops_by_parcel = {
                int(row[0]): int(row[1])
                for row in (
                    await asession.execute(
                        text(
                            """
                            SELECT parcel_id, MIN(id) FROM crop
                            WHERE status = 'EN_COURS' GROUP BY parcel_id
                            """
                        )
                    )
                ).all()
            }
            employees = {
                str(row[0]): int(row[1])
                for row in (
                    await asession.execute(
                        text("SELECT employee_code, id FROM employee")
                    )
                ).all()
            }

            users = await _keys(asession, "app_user", "matricule")
            for spec in USERS:
                if spec["matricule"] in users:
                    continue
                await asession.execute(
                    text(
                        """
                        INSERT INTO app_user (
                            matricule, first_name, last_name, email, phone,
                            address, photo_seed, function_id, primary_role_id,
                            team_id, manager_id, employee_id, farm_key, sector,
                            status, hired_on, last_login_at, mfa_enabled,
                            mfa_method, notes
                        ) VALUES (
                            :matricule, :first_name, :last_name, :email, :phone,
                            :address, :photo_seed, :function_id, :role_id,
                            :team_id, NULL, :employee_id, :farm_key, :sector,
                            :status, :hired_on, :last_login_at, :mfa_enabled,
                            :mfa_method, :notes
                        )
                        """
                    ),
                    {
                        "matricule": spec["matricule"],
                        "first_name": spec["first_name"],
                        "last_name": spec["last_name"],
                        "email": spec["email"],
                        "phone": spec["phone"],
                        "address": f"{FARM_KEY} · secteur {spec['sector'] or 'siège'}",
                        "photo_seed": spec["email"],
                        "function_id": functions.get(spec["function"]),
                        "role_id": roles.get(spec["roles"][0]),
                        "team_id": teams.get(spec["team"]),
                        "employee_id": employees.get(spec["employee_code"]),
                        "farm_key": FARM_KEY,
                        "sector": spec["sector"],
                        "status": spec["status"],
                        "hired_on": today
                        - datetime.timedelta(days=int(spec["hired_offset"])),
                        "last_login_at": now
                        - datetime.timedelta(hours=6 + len(spec["matricule"])),
                        "mfa_enabled": 0 if spec["mfa"] == "AUCUNE" else 1,
                        "mfa_method": spec["mfa"],
                        "notes": spec["notes"],
                    },
                )
            users = await _keys(asession, "app_user", "matricule")

            # Hiérarchie (responsable direct) : mise à jour idempotente.
            for spec in USERS:
                manager = spec.get("manager", "")
                if not manager:
                    continue
                await asession.execute(
                    text(
                        """
                        UPDATE app_user SET manager_id = :manager_id
                        WHERE matricule = :matricule AND manager_id IS NULL
                        """
                    ),
                    {
                        "manager_id": users.get(manager),
                        "matricule": spec["matricule"],
                    },
                )

            # --- 7) Rôles attribués, périmètres, équipes, affectations ---
            for spec in USERS:
                user_id = users.get(spec["matricule"])
                if user_id is None:
                    continue

                for index, role_key in enumerate(spec["roles"]):
                    role_id = roles.get(role_key)
                    if role_id is None:
                        continue
                    exists = await _scalar(
                        asession,
                        """
                        SELECT COUNT(*) FROM user_role
                        WHERE user_id = :uid AND role_id = :rid
                        """,
                        {"uid": user_id, "rid": role_id},
                    )
                    if exists:
                        continue
                    await asession.execute(
                        text(
                            """
                            INSERT INTO user_role (
                                user_id, role_id, is_primary, granted_by,
                                granted_on, notes
                            ) VALUES (
                                :uid, :rid, :is_primary, 'Amorçage AgriPro',
                                :granted_on, :notes
                            )
                            """
                        ),
                        {
                            "uid": user_id,
                            "rid": role_id,
                            "is_primary": 1 if index == 0 else 0,
                            "granted_on": today,
                            "notes": f"Rôle {role_key} attribué à l'ouverture du module.",
                        },
                    )

                for scope in spec["scopes"]:
                    kind = str(scope.get("kind", "EXPLOITATION"))
                    parcel_id = parcels.get(scope.get("parcel"))
                    team_id = teams.get(scope.get("team"))
                    sector = str(scope.get("sector", ""))
                    site = str(scope.get("site", ""))
                    activity = str(scope.get("activity", ""))
                    exists = await _scalar(
                        asession,
                        """
                        SELECT COUNT(*) FROM access_scope
                        WHERE user_id = :uid AND scope_kind = :kind
                          AND COALESCE(parcel_id, 0) = :pid
                          AND COALESCE(team_id, 0) = :tid
                          AND COALESCE(sector, '') = :sector
                          AND COALESCE(activity, '') = :activity
                          AND COALESCE(site, '') = :site
                        """,
                        {
                            "uid": user_id,
                            "kind": kind,
                            "pid": parcel_id or 0,
                            "tid": team_id or 0,
                            "sector": sector,
                            "activity": activity,
                            "site": site,
                        },
                    )
                    if exists:
                        continue
                    await asession.execute(
                        text(
                            """
                            INSERT INTO access_scope (
                                user_id, scope_kind, farm_key, site, sector,
                                parcel_id, crop_id, team_id, activity, season,
                                is_readonly, note
                            ) VALUES (
                                :uid, :kind, :farm_key, :site, :sector,
                                :pid, :cid, :tid, :activity, :season,
                                :readonly, :note
                            )
                            """
                        ),
                        {
                            "uid": user_id,
                            "kind": kind,
                            "farm_key": FARM_KEY,
                            "site": site,
                            "sector": sector,
                            "pid": parcel_id,
                            "cid": crops_by_parcel.get(parcel_id or 0),
                            "tid": team_id,
                            "activity": activity,
                            "season": str(today.year),
                            "readonly": 1
                            if bool(scope.get("readonly", False))
                            else 0,
                            "note": (
                                "Périmètre amorcé depuis le référentiel "
                                "sécurité AgriPro."
                            ),
                        },
                    )

                team_id = teams.get(spec["team"])
                if team_id is not None:
                    exists = await _scalar(
                        asession,
                        """
                        SELECT COUNT(*) FROM team_member
                        WHERE team_id = :tid AND user_id = :uid
                        """,
                        {"tid": team_id, "uid": user_id},
                    )
                    if not exists:
                        await asession.execute(
                            text(
                                """
                                INSERT INTO team_member (
                                    team_id, user_id, role_in_team, joined_on,
                                    notes
                                ) VALUES (
                                    :tid, :uid, :role_in_team, :joined_on, ''
                                )
                                """
                            ),
                            {
                                "tid": team_id,
                                "uid": user_id,
                                "role_in_team": "Responsable"
                                if spec["roles"][0]
                                in (
                                    "responsable-irrigation",
                                    "responsable-materiel",
                                    "responsable-production",
                                    "chef-equipe",
                                )
                                else "Membre",
                                "joined_on": today
                                - datetime.timedelta(days=120),
                            },
                        )

                for item in spec["assignments"]:
                    parcel_id = parcels.get(item.get("parcel"))
                    assign_team = teams.get(item.get("team"))
                    exists = await _scalar(
                        asession,
                        """
                        SELECT COUNT(*) FROM user_assignment
                        WHERE user_id = :uid
                          AND COALESCE(parcel_id, 0) = :pid
                          AND COALESCE(team_id, 0) = :tid
                          AND COALESCE(activity, '') = :activity
                        """,
                        {
                            "uid": user_id,
                            "pid": parcel_id or 0,
                            "tid": assign_team or 0,
                            "activity": str(item.get("activity", "")),
                        },
                    )
                    if exists:
                        continue
                    await asession.execute(
                        text(
                            """
                            INSERT INTO user_assignment (
                                user_id, farm_key, sector, parcel_id, crop_id,
                                team_id, activity, season, is_responsible,
                                start_date, end_date, notes
                            ) VALUES (
                                :uid, :farm_key, :sector, :pid, :cid,
                                :tid, :activity, :season, :responsible,
                                :start_date, NULL, :notes
                            )
                            """
                        ),
                        {
                            "uid": user_id,
                            "farm_key": FARM_KEY,
                            "sector": spec["sector"],
                            "pid": parcel_id,
                            "cid": crops_by_parcel.get(parcel_id or 0),
                            "tid": assign_team,
                            "activity": str(item.get("activity", "")),
                            "season": str(today.year),
                            "responsible": 1
                            if bool(item.get("responsible", False))
                            else 0,
                            "start_date": today - datetime.timedelta(days=30),
                            "notes": (
                                "Affectation opérationnelle amorcée "
                                "(exploitation → secteur → parcelle → équipe)."
                            ),
                        },
                    )

            # Responsables d'équipe (idempotent, sans écraser un choix humain).
            leaders = {
                "equipe-irrigation": "U004",
                "equipe-recolte": "U005",
                "equipe-traitement": "U003",
                "equipe-maintenance": "U007",
                "equipe-plantation": "U005",
            }
            for team_key, matricule in leaders.items():
                await asession.execute(
                    text(
                        """
                        UPDATE farm_team SET leader_id = :uid
                        WHERE key = :key AND leader_id IS NULL
                        """
                    ),
                    {"uid": users.get(matricule), "key": team_key},
                )

            # --- 8) Délégations temporaires -----------------------------
            delegations = [
                {
                    "delegator": "U004",
                    "delegate": "U005",
                    "role": "responsable-irrigation",
                    "scope_kind": "PARCELLE",
                    "parcel": "P01",
                    "reason": "Absence du responsable irrigation (congés).",
                    "authorized_by": "Karim Haddad",
                    "start": -2,
                    "end": 8,
                    "status": "ACTIVE",
                },
                {
                    "delegator": "U003",
                    "delegate": "U010",
                    "role": "responsable-production",
                    "scope_kind": "EQUIPE",
                    "team": "equipe-traitement",
                    "reason": "Renfort ponctuel pendant les notations sanitaires.",
                    "authorized_by": "Karim Haddad",
                    "start": -40,
                    "end": -25,
                    "status": "EXPIREE",
                },
            ]
            for item in delegations:
                delegator = users.get(item["delegator"])
                delegate = users.get(item["delegate"])
                role_id = roles.get(item["role"])
                if delegator is None or delegate is None or role_id is None:
                    continue
                exists = await _scalar(
                    asession,
                    """
                    SELECT COUNT(*) FROM role_delegation
                    WHERE delegator_id = :did AND delegate_id = :tid
                      AND role_id = :rid AND start_date = :start
                    """,
                    {
                        "did": delegator,
                        "tid": delegate,
                        "rid": role_id,
                        "start": today
                        + datetime.timedelta(days=int(item["start"])),
                    },
                )
                if exists:
                    continue
                await asession.execute(
                    text(
                        """
                        INSERT INTO role_delegation (
                            delegator_id, delegate_id, role_id, permission_id,
                            scope_kind, parcel_id, team_id, reason,
                            authorized_by, start_date, end_date, status, notes
                        ) VALUES (
                            :did, :tid, :rid, NULL,
                            :scope_kind, :pid, :team_id, :reason,
                            :authorized_by, :start, :end, :status, ''
                        )
                        """
                    ),
                    {
                        "did": delegator,
                        "tid": delegate,
                        "rid": role_id,
                        "scope_kind": item["scope_kind"],
                        "pid": parcels.get(item.get("parcel")),
                        "team_id": teams.get(item.get("team")),
                        "reason": item["reason"],
                        "authorized_by": item["authorized_by"],
                        "start": today
                        + datetime.timedelta(days=int(item["start"])),
                        "end": today
                        + datetime.timedelta(days=int(item["end"])),
                        "status": item["status"],
                    },
                )

            # --- 9) Sessions et MFA représentées ------------------------
            sessions = [
                ("U001", "Poste bureau exploitation", "CLE_MATERIELLE", True),
                ("U002", "Tablette de plaine", "APPLICATION", True),
                ("U004", "Smartphone terrain", "SMS", True),
                ("U006", "Smartphone terrain", "AUCUNE", False),
            ]
            for matricule, device, method, mfa_passed in sessions:
                user_id = users.get(matricule)
                if user_id is None:
                    continue
                token_hash = hash_token(f"agripro-demo-{matricule}")
                exists = await _scalar(
                    asession,
                    "SELECT COUNT(*) FROM user_session WHERE token_hash = :t",
                    {"t": token_hash},
                )
                if exists:
                    continue
                await asession.execute(
                    text(
                        """
                        INSERT INTO user_session (
                            user_id, token_hash, device, ip_address, user_agent,
                            mfa_passed, mfa_method, status, started_at,
                            last_seen_at, expires_at, notes
                        ) VALUES (
                            :uid, :token, :device, '10.0.0.12', 'AgriPro Mobile',
                            :mfa_passed, :method, 'ACTIVE', :started,
                            :seen, :expires, 'Session d''exemple amorcée.'
                        )
                        """
                    ),
                    {
                        "uid": user_id,
                        "token": token_hash,
                        "device": device,
                        "mfa_passed": 1 if mfa_passed else 0,
                        "method": method,
                        "started": now - datetime.timedelta(hours=3),
                        "seen": now - datetime.timedelta(minutes=12),
                        "expires": now + datetime.timedelta(hours=9),
                    },
                )

            await asession.commit()
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
        raise

    # --- 10) Journal d'activité : quelques traces initiales -------------
    async with rx.asession() as asession:
        already = await _scalar(
            asession,
            "SELECT COUNT(*) FROM activity_log WHERE object_type = 'SOCLE'",
            {},
        )
        user_ids = await _keys(asession, "app_user", "matricule")
    if not already:
        await log_activity(
            user_ids.get("U001", 0),
            "PERMISSION",
            module="utilisateurs",
            action="CREER",
            object_type="SOCLE",
            object_ref="socle-securite",
            summary=(
                "Ouverture du socle utilisateurs, rôles, permissions et "
                "périmètres agricoles."
            ),
            scope_label="Toute l'exploitation",
            is_sensitive=True,
        )
        await log_activity(
            user_ids.get("U002", 0),
            "AFFECTATION",
            module="equipes",
            action="AFFECTER",
            object_type="SOCLE",
            object_ref="equipes-initiales",
            summary="Constitution des équipes et des affectations parcellaires.",
            scope_label="Toute l'exploitation",
        )
        await log_activity(
            user_ids.get("U004", 0),
            "CONNEXION",
            module="dashboard",
            action="CONSULTER",
            object_type="SOCLE",
            object_ref="session-terrain",
            summary="Connexion terrain avec second facteur par SMS.",
            scope_label="Secteur Nord",
        )

    _seeded = True

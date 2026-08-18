"""Vérifie l'administration des utilisateurs AgriPro (socle `agripro_*`)."""

import asyncio

import reflex as rx
from sqlalchemy import text

from app.access_control import user_by_matricule
from app.admin_users import (
    change_user_status,
    ensure_admin_data,
    load_activity,
    load_functions,
    load_options,
    load_overview,
    load_rbac,
    load_teams,
    load_user_detail,
    load_users,
)


async def status_of(matricule: str) -> str:
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text("SELECT status FROM agripro_user WHERE matricule = :m"),
                {"m": matricule},
            )
        ).first()
    return str(row[0]) if row is not None else ""


async def main():
    print("=== Test administration utilisateurs AgriPro ===")
    await ensure_admin_data()

    overview = await load_overview()
    assert overview["users"] >= 10, overview
    assert overview["roles"] >= 6 and overview["functions"] >= 10, overview
    assert overview["permissions"] > 100 and overview["grants"] > 0, overview

    statuses, roles, teams = await load_options()
    assert statuses and roles and teams

    users = await load_users()
    assert len(users) == overview["users"], (len(users), overview["users"])
    filtered = await load_users(search="ahmed")
    assert len(filtered) >= 1 and len(filtered) < len(users)
    actives = await load_users(status="ACTIF")
    assert all(u["status"] == "ACTIF" for u in actives)
    irrigation = await load_users(role_key="responsable-irrigation")
    assert len(irrigation) >= 1

    owner = await user_by_matricule("U001")
    target = await user_by_matricule("U006")
    assert owner > 0 and target > 0

    detail, user_roles, perms, scopes, assignments = await load_user_detail(
        await user_by_matricule("U004")
    )
    assert detail["matricule"] == "U004"
    assert detail["permission_count"] > 0
    assert len(user_roles) >= 1
    assert len(perms) >= 1 and perms[0]["actions"]
    assert len(scopes) >= 1 and len(assignments) >= 1
    assert detail["has_full_scope"] is False

    functions = await load_functions()
    assert len(functions) >= 20
    direction = await load_functions("DIRECTION")
    assert 0 < len(direction) < len(functions)

    farm_teams = await load_teams()
    assert len(farm_teams) >= 5
    assert any(t["members"] > 0 for t in farm_teams)

    owner_matrix = await load_rbac("proprietaire")
    worker_matrix = await load_rbac("ouvrier")
    assert sum(r["granted_count"] for r in owner_matrix) > sum(
        r["granted_count"] for r in worker_matrix
    )
    assert all(r["granted_count"] == r["total"] for r in owner_matrix)

    # --- Actions de statut : contrôle serveur + journal -------------------
    before = len(await load_activity(0, 200))
    ok, message = await change_user_status(owner, target, "SUSPENDRE")
    assert ok, message
    assert await status_of("U006") == "SUSPENDU"
    ok, message = await change_user_status(owner, target, "REACTIVER")
    assert ok, message
    assert await status_of("U006") == "ACTIF"
    after = len(await load_activity(0, 200))
    assert after >= before + 2, (before, after)

    # Garde-fous
    refused, msg = await change_user_status(owner, owner, "SUSPENDRE")
    assert refused is False and "propre compte" in msg
    protected, msg = await change_user_status(target, owner, "ARCHIVER")
    assert protected is False, msg
    same, msg = await change_user_status(owner, target, "REACTIVER")
    assert same is False and "déjà" in msg

    print(
        f"✓ {overview['users']} utilisateurs, {overview['functions']} fonctions, "
        f"{overview['roles']} rôles, {overview['permissions']} permissions, "
        f"{overview['teams']} équipes, journal {after} entrées"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

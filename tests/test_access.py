"""Vérifie le socle utilisateurs, RBAC et périmètre agricole AgriPro."""

import asyncio

import reflex as rx
from sqlalchemy import text

from app.access_control import (
    active_delegations,
    authorize,
    effective_permissions,
    expire_stale_delegations,
    has_permission,
    hash_token,
    log_activity,
    parcel_ids_in_scope,
    resolve_session,
    scope_allows_farm,
    scope_allows_parcel,
    scope_allows_team,
    touch_session,
    user_by_matricule,
    user_security_profile,
)
from app.access_reference import (
    ACCESS_MODULES,
    DENY_NO_PERMISSION,
    DENY_OUT_OF_SCOPE,
    FARM_KEY,
    FUNCTIONS,
    ROLES,
    all_permissions,
    permission_key,
)
from app.seed_access import access_totals, seed_access_data


async def parcel_id(code: str) -> int:
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text("SELECT id FROM parcel WHERE code = :c"), {"c": code}
            )
        ).first()
    return int(row[0]) if row is not None else 0


async def team_id(key: str) -> int:
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text("SELECT id FROM farm_team WHERE key = :k"), {"k": key}
            )
        ).first()
    return int(row[0]) if row is not None else 0


async def activity_count() -> int:
    async with rx.asession() as asession:
        return int(
            (
                await asession.execute(
                    text("SELECT COUNT(*) FROM activity_log")
                )
            ).scalar()
            or 0
        )


async def main():
    print("=== Test socle sécurité utilisateurs AgriPro ===")

    await seed_access_data()
    first = await access_totals()

    # --- Idempotence : rejouer l'amorçage ne duplique rien ---------------
    import app.seed_access as seed_module

    seed_module._seeded = False
    await seed_access_data()
    second = await access_totals()
    for key in first:
        assert first[key] == second[key], (
            f"Amorçage non idempotent sur {key} : {first[key]} → {second[key]}"
        )

    assert first["functions"] == len(FUNCTIONS), (
        "Toutes les fonctions attendues"
    )
    assert first["roles"] == len(ROLES), "Tous les rôles applicatifs attendus"
    assert first["permissions"] == len(all_permissions()), (
        "La matrice module × action doit être complète"
    )
    assert first["role_permissions"] > first["permissions"], (
        "Les rôles doivent porter des permissions"
    )
    assert first["users"] >= 10, "Des utilisateurs d'exemple sont attendus"
    assert first["teams"] >= 5, "Des équipes agricoles sont attendues"
    assert first["assignments"] > 0, "Des affectations parcellaires attendues"
    assert first["scopes"] > 0, "Des périmètres agricoles attendus"
    assert first["sessions"] > 0, "Des sessions représentées attendues"

    owner = await user_by_matricule("U001")
    manager = await user_by_matricule("U002")
    irrigation = await user_by_matricule("U004")
    field_leader = await user_by_matricule("U005")
    worker = await user_by_matricule("U006")
    accountant = await user_by_matricule("U009")
    pending = await user_by_matricule("U010")
    assert min(owner, manager, irrigation, worker, accountant) > 0

    # --- RBAC : permissions effectives -----------------------------------
    owner_perms = await effective_permissions(owner)
    assert len(owner_perms) == len(all_permissions()), (
        "Le propriétaire dispose de toutes les permissions"
    )
    assert await has_permission(owner, "utilisateurs", "SUPPRIMER")
    assert not await has_permission(worker, "parcelles", "SUPPRIMER"), (
        "Un ouvrier ne doit pas pouvoir supprimer une parcelle"
    )
    assert await has_permission(worker, "interventions", "CLOTURER")
    assert await has_permission(accountant, "comptabilite", "VALIDER")
    assert not await has_permission(accountant, "traitements", "CREER")
    assert not await has_permission(manager, "utilisateurs", "SUPPRIMER"), (
        "Protection contre l'escalade de privilèges"
    )

    # Un compte non actif n'a aucune permission effective.
    assert await effective_permissions(pending) == [], (
        "Un compte en attente ne doit porter aucune permission"
    )

    # --- Périmètre agricole ----------------------------------------------
    p01 = await parcel_id("P01")
    p03 = await parcel_id("P03")
    p07 = await parcel_id("P07")
    assert await scope_allows_parcel(irrigation, p01)
    assert not await scope_allows_parcel(irrigation, p07), (
        "Ahmed ne doit pas accéder à un îlot hors de son périmètre"
    )
    assert await scope_allows_parcel(owner, p07), (
        "Périmètre global du propriétaire"
    )
    assert await scope_allows_parcel(worker, p03)
    assert not await scope_allows_parcel(worker, p01)

    scoped = await parcel_ids_in_scope(irrigation)
    assert p01 in scoped and p07 not in scoped
    assert len(await parcel_ids_in_scope(owner)) >= len(scoped)

    irr_team = await team_id("equipe-irrigation")
    maint_team = await team_id("equipe-maintenance")
    assert await scope_allows_team(irrigation, irr_team)
    assert not await scope_allows_team(worker, maint_team)
    assert await scope_allows_farm(irrigation, FARM_KEY)
    assert not await scope_allows_farm(irrigation, "autre-exploitation")

    # --- Décision unique : permission + périmètre + journal ---------------
    ok = await authorize(
        irrigation, "irrigation", "PLANIFIER", parcel_id=p01, farm_key=FARM_KEY
    )
    assert ok["allowed"] is True and ok["reason"] == ""

    before = await activity_count()
    refused_scope = await authorize(
        irrigation, "irrigation", "PLANIFIER", parcel_id=p07
    )
    assert refused_scope["allowed"] is False
    assert refused_scope["reason"] == DENY_OUT_OF_SCOPE
    refused_perm = await authorize(worker, "utilisateurs", "MODIFIER")
    assert refused_perm["reason"] == DENY_NO_PERMISSION
    assert await activity_count() == before + 2, (
        "Chaque refus doit être consigné dans le journal d'audit"
    )

    # --- Délégations temporaires -----------------------------------------
    await expire_stale_delegations()
    received = await active_delegations(field_leader)
    assert len(received) >= 1, "Une délégation active est attendue"
    assert received[0]["days_left"] >= 0
    delegated = await authorize(
        field_leader, "irrigation", "VALIDER", parcel_id=p01
    )
    assert delegated["allowed"] is True, (
        "La délégation active doit ouvrir l'action déléguée"
    )
    granted = await active_delegations(irrigation, as_delegate=False)
    assert len(granted) >= 1
    expired = [
        d
        for d in await active_delegations(pending)
        if d["delegate_id"] == pending
    ]
    assert expired == [], "Une délégation expirée ne doit plus rien ouvrir"

    # --- Sessions et MFA --------------------------------------------------
    assert await resolve_session("agripro-demo-U001") == owner
    assert await resolve_session("agripro-demo-U006") == 0, (
        "Sans second facteur validé, la session est refusée"
    )
    assert await resolve_session("jeton-inconnu") == 0
    assert await touch_session("agripro-demo-U002") is True
    assert hash_token("abc") != "abc", "Le jeton n'est jamais stocké en clair"

    # --- Journal d'activité ------------------------------------------------
    count_before = await activity_count()
    log_id = await log_activity(
        manager,
        "VALIDATION",
        module="interventions",
        action="VALIDER",
        object_type="INTERVENTION",
        object_ref="Protection mildiou",
        object_id=1,
        summary="Validation du chantier de protection.",
        parcel_id=p01,
    )
    assert log_id > 0 and await activity_count() == count_before + 1

    # --- Profil de sécurité (préparation UI) -------------------------------
    profile = await user_security_profile(irrigation)
    assert profile["full_name"] == "Ahmed Benali"
    assert profile["role_keys"] == ["responsable-irrigation"]
    assert profile["team_label"] != "—"
    assert profile["mfa_enabled"] is True
    assert profile["permission_count"] > 0
    assert profile["has_full_scope"] is False
    assert p01 in profile["parcel_ids"]
    owner_profile = await user_security_profile(owner)
    assert owner_profile["has_full_scope"] is True

    modules = [spec["key"] for spec in ACCESS_MODULES]
    assert permission_key("parcelles", "CONSULTER") in owner_perms
    assert "utilisateurs" in modules

    print(
        f"✓ {first['users']} utilisateurs, {first['roles']} rôles, "
        f"{first['permissions']} permissions ({first['role_permissions']} "
        f"liaisons RBAC), {first['teams']} équipes, "
        f"{first['assignments']} affectations, {first['scopes']} périmètres, "
        f"{first['delegations']} délégations, {first['sessions']} sessions"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

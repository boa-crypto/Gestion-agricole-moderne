"""Vérifie la création idempotente du socle `agripro_*` (utilisateurs / RBAC)."""

import asyncio

import reflex as rx
from sqlalchemy import text

from app.access_control import can_user, user_by_matricule
from app.access_schema import (
    AGRIPRO_ACCESS_TABLES,
    ensure_agripro_access_tables,
    init_agripro_access_tables,
)
from app.database import ensure_local_database
from app.seed_access import seed_access_data


async def main():
    print("=== Test socle agripro_* (DDL idempotent) ===")

    # Le socle doit exister sans qu'aucune page n'ait été chargée.
    await ensure_local_database()
    await ensure_agripro_access_tables()
    # Rejeu forcé : rien n'est recréé ni supprimé.
    assert init_agripro_access_tables(force=True) == [], (
        "La création des objets agripro_* doit être idempotente"
    )

    await seed_access_data()

    async with rx.asession() as asession:
        counts: dict[str, int] = {}
        for table in AGRIPRO_ACCESS_TABLES:
            counts[table] = int(
                (
                    await asession.execute(
                        text(f"SELECT COUNT(*) FROM {table}")
                    )
                ).scalar()
                or 0
            )
        owner = int(
            (
                await asession.execute(
                    text(
                        "SELECT id FROM agripro_user WHERE employee_code = 'U001'"
                    )
                )
            ).scalar()
            or 0
        )
        parcel = int(
            (
                await asession.execute(
                    text("SELECT id FROM parcel ORDER BY id LIMIT 1")
                )
            ).scalar()
            or 0
        )

    assert counts["agripro_user"] >= 6, counts
    assert counts["agripro_function"] >= 10, counts
    assert counts["agripro_role"] >= 6, counts
    assert counts["agripro_permission"] >= 20, counts
    assert counts["agripro_team"] >= 3, counts
    assert counts["agripro_user_role"] > 0, counts
    assert counts["agripro_role_permission"] > 0, counts
    assert counts["agripro_assignment"] > 0, counts
    assert counts["agripro_delegation"] > 0, counts
    assert counts["agripro_activity_log"] > 0, counts
    assert owner > 0 and parcel > 0

    # L'API RBAC publique reste inchangée et exploitable.
    assert await user_by_matricule("U001") == owner
    decision = await can_user(owner, "parcelles", "modifier", parcel_id=parcel)
    assert decision.allowed is True, decision.message

    print(
        f"✓ {len(AGRIPRO_ACCESS_TABLES)} objets agripro_* disponibles: {counts}"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

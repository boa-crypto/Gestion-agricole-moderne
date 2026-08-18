"""Vérifie les collections stables exposées par `AdministrationState`."""

import asyncio

import reflex as rx
from sqlalchemy import text
from test_utils import run_event

from app.states.administration_state import AdministrationState


async def main():
    print("=== Test état administration utilisateurs ===")
    state = AdministrationState()
    await run_event(state.load_administration)

    assert state.is_loading is False
    assert state.kpis["users"] >= 6
    assert state.kpis["roles"] >= 6
    assert state.users.length() >= 6
    assert state.visible_users.length() == state.users.length()
    assert state.functions.length() >= 10
    assert state.roles.length() >= 6
    assert state.teams.length() >= 3
    assert state.permission_matrix.length() >= 10

    user_id = state.selected_user_id
    assert user_id > 0
    assert state.selected_user["id"] == user_id
    assert state.effective_permissions.length() >= 1
    assert isinstance(state.scope_parcels, list)

    await run_event(state.set_query, "irrigation")
    assert (state.query == "irrigation") & (state.search == "irrigation")
    assert state.visible_users.length() >= 1
    await run_event(state.reset_filters)
    assert (state.query == "") & (state.users.length() >= 6)

    await run_event(state.select_user, user_id)
    assert state.selected_user_id == user_id

    await run_event(state.set_user_status, user_id, "SUSPENDU")
    assert state.selected_user["status"] == "SUSPENDU"
    await run_event(state.set_user_status, user_id, "ACTIF")
    assert state.selected_user["status"] == "ACTIF"

    async with rx.asession() as asession:
        logged = int(
            (
                await asession.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM agripro_activity_log
                        WHERE action IN ('SUSPEND_USER', 'ACTIVATE_USER')
                        """
                    )
                )
            ).scalar()
            or 0
        )
    assert logged >= 2, logged

    print(
        f"✓ {state.users.length()} utilisateurs, {state.roles.length()} rôles, {state.permission_matrix.length()} modules, {logged} changement(s) tracé(s)"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

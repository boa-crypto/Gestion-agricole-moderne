"""Vérifie la révocation/expiration d'une délégation sans erreur SQL.

Reproduit le scénario qui déclenchait `OperationalError: no such column:
u.full_name` : `expire_delegation` (état Reflex) → `revoke_delegation`
(couche de données). Le test contrôle que la délégation passe bien en
`REVOQUEE`, que la liste `delegations` est rafraîchie et que l'évènement
`EXPIRE_DELEGATION` reste journalisé.
"""

import asyncio
import datetime

import reflex as rx
from sqlalchemy import text
from test_utils import run_event

from app.access_control import user_by_matricule
from app.admin_operations import (
    create_delegation,
    load_delegations,
    revoke_delegation,
)
from app.admin_users import ensure_admin_data
from app.states.administration_state import AdministrationState


async def status_of(delegation_id: int) -> str:
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text("SELECT status FROM role_delegation WHERE id = :did"),
                {"did": delegation_id},
            )
        ).first()
    return str(row[0]) if row is not None else ""


async def logged(action: str) -> int:
    async with rx.asession() as asession:
        return int(
            (
                await asession.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM agripro_activity_log
                        WHERE action = :a
                        """
                    ),
                    {"a": action},
                )
            ).scalar()
            or 0
        )


async def main():
    print("=== Test expiration des permissions temporaires ===")
    await ensure_admin_data()

    owner = await user_by_matricule("U001")
    irrigation = await user_by_matricule("U004")
    worker = await user_by_matricule("U006")
    assert min(owner, irrigation, worker) > 0

    today = datetime.date.today()

    # --- Couche de données : plus aucune requête sur `full_name` ----------
    ok, message = await create_delegation(
        owner,
        irrigation,
        worker,
        1,
        "EXPLOITATION",
        0,
        "Test révocation sans full_name",
        today,
        today + datetime.timedelta(days=4),
    )
    assert ok, message
    created = [
        d
        for d in await load_delegations(80)
        if d["reason"] == "Test révocation sans full_name"
    ]
    assert created, "La délégation de test doit être créée"
    target = created[0]["id"]

    ok, message = await revoke_delegation(owner, target)
    assert ok, message
    assert "None" not in message and message.strip() != ""
    assert await status_of(target) == "REVOQUEE"
    again, message = await revoke_delegation(owner, target)
    assert again is False and "vigueur" in message
    assert await revoke_delegation(owner, 9_000_000) == (
        False,
        "Délégation introuvable.",
    )

    # --- État Reflex : `expire_delegation` journalise et rafraîchit -------
    state = AdministrationState()
    await run_event(state.load_administration)

    ok, message = await create_delegation(
        owner,
        irrigation,
        worker,
        1,
        "EXPLOITATION",
        0,
        "Test expiration depuis l'état",
        today,
        today + datetime.timedelta(days=6),
    )
    assert ok, message
    fresh = [
        d
        for d in await load_delegations(80)
        if d["reason"] == "Test expiration depuis l'état"
    ]
    assert fresh
    delegation_id = fresh[0]["id"]

    before = await logged("EXPIRE_DELEGATION")
    await run_event(state.expire_delegation, delegation_id)
    assert state.delegation_error == "", state.delegation_error
    assert await status_of(delegation_id) == "REVOQUEE"
    assert await logged("EXPIRE_DELEGATION") == before + 1
    refreshed = [d for d in state.delegations if d["id"] == delegation_id]
    assert refreshed & (refreshed[0]["status"] == "REVOQUEE"), refreshed
    assert refreshed[0]["is_open"] is False

    print(
        f"✓ délégations {state.delegations.length()}, EXPIRE_DELEGATION journalisé ({before + 1})"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

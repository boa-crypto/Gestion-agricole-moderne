"""Vérifie l'organisation opérationnelle du module utilisateurs AgriPro."""

import asyncio
import datetime

import reflex as rx
from sqlalchemy import text
from test_utils import run_event

from app.access_control import user_by_matricule
from app.admin_operations import (
    complete_task,
    create_delegation,
    load_assignments,
    load_delegations,
    load_org_levels,
    load_pending_validations,
    load_personal_summary,
    load_responsibilities,
    load_tasks,
    revoke_delegation,
    validate_task,
)
from app.admin_users import ensure_admin_data
from app.states.administration_state import AdministrationState


async def one_open_intervention() -> int:
    async with rx.asession() as asession:
        return int(
            (
                await asession.execute(
                    text(
                        """
                        SELECT id FROM intervention
                        WHERE status IN ('PLANIFIEE', 'EN_COURS')
                        ORDER BY id LIMIT 1
                        """
                    )
                )
            ).scalar()
            or 0
        )


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
    print("=== Test organisation opérationnelle AgriPro ===")
    await ensure_admin_data()

    owner = await user_by_matricule("U001")
    irrigation = await user_by_matricule("U004")
    worker = await user_by_matricule("U006")
    assert min(owner, irrigation, worker) > 0

    # --- Organigramme ----------------------------------------------------
    levels = await load_org_levels()
    assert len(levels) >= 2, levels
    assert levels[0]["depth"] == 0 and levels[0]["count"] >= 1
    top = levels[0]["nodes"][0]
    assert top["manager_id"] == 0 and top["reports"] >= 1

    # --- Espace personnel ------------------------------------------------
    personal = await load_personal_summary(irrigation)
    assert personal["user_id"] == irrigation
    assert personal["parcels"] >= 1
    assert personal["team_label"] != "—"
    tasks = await load_tasks(irrigation, 30)
    assert len(tasks) >= 1, tasks
    assert await load_responsibilities(irrigation)

    owner_personal = await load_personal_summary(owner)
    assert owner_personal["has_full_scope"] is True
    assert owner_personal["tasks_total"] >= personal["tasks_total"]

    # --- Workflow de validation ------------------------------------------
    intervention = await one_open_intervention()
    assert intervention > 0
    ok, message = await complete_task(owner, intervention)
    assert ok, message
    pending_ids = [t["id"] for t in await load_pending_validations(0, 60)]
    assert intervention in pending_ids, pending_ids
    ok, message = await validate_task(owner, intervention)
    assert ok, message
    again, message = await validate_task(owner, intervention)
    assert again is False and "déjà" in message
    assert await logged("VALIDER") >= 1
    assert await logged("CLOTURER") >= 1
    still_pending = [t["id"] for t in await load_pending_validations(0, 60)]
    assert intervention not in still_pending

    refused, message = await validate_task(worker, intervention)
    assert refused is False, message

    # --- Permissions temporaires -----------------------------------------
    today = datetime.date.today()
    ok, message = await create_delegation(
        owner,
        irrigation,
        worker,
        1,
        "EQUIPE",
        0,
        "Test automatisé de délégation",
        today,
        today + datetime.timedelta(days=5),
    )
    assert ok, message
    delegations = await load_delegations(60)
    created = [
        d for d in delegations if d["reason"] == "Test automatisé de délégation"
    ]
    assert created and created[0]["status"] == "ACTIVE"
    bad, message = await create_delegation(
        owner, irrigation, irrigation, 1, "EQUIPE", 0, "x", today, today
    )
    assert bad is False, message
    ok, message = await revoke_delegation(owner, created[0]["id"])
    assert ok, message
    revoked = [
        d for d in await load_delegations(60) if d["id"] == created[0]["id"]
    ]
    assert revoked and revoked[0]["status"] == "REVOQUEE"

    # --- Affectations ----------------------------------------------------
    assignments = await load_assignments()
    assert len(assignments) >= 5
    scoped = await load_assignments(user_id=irrigation)
    assert 0 < len(scoped) <= len(assignments)

    # --- État Reflex -----------------------------------------------------
    state = AdministrationState()
    await run_event(state.load_administration)
    assert state.org_levels.length() >= 2
    assert state.assignments.length() >= 5
    assert state.delegations.length() >= 1
    assert state.personal["user_id"] > 0

    await run_event(state.select_org_node, irrigation)
    assert (state.org_selected_id == irrigation) & (
        state.org_node["id"] == irrigation
    )
    await run_event(state.open_personal_space, irrigation)
    assert (state.section == "espace") & (state.personal_user_id == irrigation)
    assert state.personal_tasks.length() >= 1
    assert state.personal_responsibilities.length() >= 1

    second = await one_open_intervention()
    if second > 0:
        await run_event(state.complete_intervention, second)
        await run_event(state.validate_intervention, second)
        assert state.error == "", state.error

    await run_event(state.set_assignment_team, "equipe-irrigation")
    assert state.assignments.length() >= 1
    await run_event(state.reset_assignment_filters)
    assert state.assignment_team == "TOUTES"
    await run_event(state.expire_temporary_permissions)

    print(
        f"✓ {len(levels)} niveaux d'organigramme, {len(assignments)} affectations, "
        f"{len(delegations)} délégations, validations tracées"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

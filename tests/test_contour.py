"""Vérifie le workflow de contrôle des contours parcellaires."""

import asyncio

import reflex as rx
from sqlalchemy import text
from test_utils import run_event

from app.states.contour_state import (
    CONTROL_ORDER,
    VALIDATION_A_RELEVER,
    VALIDATION_NONE,
    VALIDATION_VERIFIE,
    ContourState,
)


async def log_count() -> int:
    async with rx.asession() as asession:
        return int(
            (
                await asession.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM remediation_log
                        WHERE domain = 'CONTOUR'
                        """
                    )
                )
            ).scalar()
            or 0
        )


async def main():
    print("=== Test contrôle des contours parcellaires ===")
    state = ContourState()
    await run_event(state.load_contours)
    assert state.is_loading is False, "Le chargement doit être terminé"
    assert state.today_label != "", "La date doit être calculée"
    assert state.rows.length() > 0, "Des îlots doivent être audités"

    for row in state.rows:
        assert CONTROL_ORDER.count(row["control"]) == 1, (
            f"Statut de contrôle inconnu : {row['control']}"
        )
        assert row["control_label"] != ""
        assert row["recommendation"] != "", "Une recommandation est requise"
        assert row["validation_label"] != ""
        assert row["gap_pct"] >= 0

    assert state.kpis["parcels"] == state.rows.length()
    assert (state.control_rate >= 0) & (state.control_rate <= 100)
    assert state.verdict_label != ""

    target = state.rows[0]
    parcel_id = target["id"]

    await run_event(state.set_author_draft, "Test automatique")
    await run_event(state.set_note_draft, "Contrôle visuel réalisé.")

    before = await log_count()
    await run_event(state.verify_contour, parcel_id)
    assert await log_count() == before + 1, "La décision doit être consignée"
    updated = [row for row in state.rows if row["id"] == parcel_id]
    assert updated.length() == 1
    assert updated[0]["validation"] == VALIDATION_VERIFIE
    assert updated[0]["decision_count"] > 0

    await run_event(state.verify_contour, parcel_id)
    assert await log_count() == before + 1, "La vérification est idempotente"

    await run_event(state.survey_contour, parcel_id)
    assert await log_count() == before + 2, "Un changement doit être tracé"
    updated = [row for row in state.rows if row["id"] == parcel_id]
    assert updated[0]["validation"] == VALIDATION_A_RELEVER

    assert state.logs.length() > 0, "Le journal doit être alimenté"
    for entry in state.logs:
        assert entry["action_label"] != ""
        assert entry["label"] != ""

    # Filtres : statut de contrôle et validation.
    await run_event(state.set_validation_filter, VALIDATION_A_RELEVER)
    for row in state.visible_rows:
        assert row["validation"] == VALIDATION_A_RELEVER
    await run_event(state.set_validation_filter, VALIDATION_NONE)
    for row in state.visible_rows:
        assert row["validation"] == VALIDATION_NONE
    await run_event(state.reset_filters)
    assert state.visible_count == state.rows.length()

    control_key = state.rows[0]["control"]
    await run_event(state.focus_control, control_key)
    for row in state.visible_rows:
        assert row["control"] == control_key
    await run_event(state.reset_filters)

    await run_event(state.set_search, state.rows[0]["name"][:5])
    assert state.rows.length() >= 1, "La recherche doit trouver un îlot"
    await run_event(state.reset_filters)

    total = state.kpis["conforme"] + state.kpis["a_verifier"]
    total += state.kpis["ecart"] + state.kpis["sans_contour"]
    assert total == state.kpis["parcels"], (
        "Chaque îlot doit porter un statut de contrôle unique"
    )

    print(
        f"✓ {state.kpis['parcels']:.0f} îlot(s), taux de contrôle {state.control_rate_pct}, "
        f"{state.kpis['ecart']:.0f} écart(s), {state.kpis['decisions']:.0f} décision(s)"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

"""Vérifie l'API stable de ContourState (résumé, listes, sélection, alias)."""

import asyncio

from test_utils import run_event

from app.states.audit_state import AuditState
from app.states.contour_state import (
    VALIDATION_A_RELEVER,
    VALIDATION_VERIFIE,
    ContourState,
)


async def main():
    print("=== Test API contrôle des contours ===")
    state = ContourState()
    await run_event(state.load_contours)
    assert state.is_loading is False, "Le chargement doit être terminé"
    assert state.notice == "", "Aucun message au chargement"
    assert state.error == "", "Aucune erreur au chargement"

    for key in (
        "total",
        "generated",
        "verified",
        "to_survey",
        "decisions",
        "open_total",
        "control_rate",
    ):
        assert state.summary[key] >= 0, f"Compteur manquant : {key}"
    assert state.summary["total"] == state.kpis["parcels"]
    assert state.has_items != None
    assert state.item_count == state.items.length()

    if state.items:
        row = state.items[0]
        await run_event(state.select_contour, row["id"])
        assert state.selected_id == row["id"], "La sélection doit être ciblée"
        assert state.has_selection is True
        assert state.selected_label != "", "Un libellé doit être exposé"

        await run_event(
            state.mark_to_survey,
            row["id"],
            "Test automatique: relevé terrain demandé",
        )
        assert state.notice != "", "Un message doit être exposé"
        found = [item for item in state.items if item["id"] == row["id"]]
        if found:
            assert found[0]["decision"] == VALIDATION_A_RELEVER
            assert found[0]["validation"] == VALIDATION_A_RELEVER

        await run_event(
            state.mark_verified, row["id"], "Test automatique: vérifié"
        )
        assert state.notice != ""
        found = [item for item in state.items if item["id"] == row["id"]]
        if found:
            assert found[0]["decision"] == VALIDATION_VERIFIE

        # Idempotence : la même décision ne rejoue pas de message d'erreur.
        await run_event(
            state.mark_verified, row["id"], "Test automatique: vérifié"
        )
        assert state.error == ""

        await run_event(state.load_contours)
        again = [item for item in state.items if item["id"] == row["id"]]
        if again:
            assert again[0]["decision"] == VALIDATION_VERIFIE
            assert again[0]["decision_count"] > 0

    for item in state.items:
        assert item["decision"] in (
            "",
            VALIDATION_VERIFIE,
            VALIDATION_A_RELEVER,
        )
        assert item["recommendation"] != ""

    # L'audit reste opérationnel et documenté.
    audit = AuditState()
    await run_event(audit.load_audit)
    for issue in audit.issues:
        assert issue["recommendation"] != "", "Chaque constat doit guider"

    print(
        f"✓ total={state.summary['total']:.0f}, générés={state.summary['generated']:.0f}, "
        f"vérifiés={state.summary['verified']:.0f}, relevés={state.summary['to_survey']:.0f}, "
        f"décisions={state.summary['decisions']:.0f}"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

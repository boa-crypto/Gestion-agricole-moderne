"""Vérifie les sous-modules de remédiation des états d'exploitation."""

import asyncio

import reflex as rx
from sqlalchemy import text
from test_utils import run_event

from app.states.remediation_state import RemediationState
from app.states.search_state import SearchState


async def log_count() -> int:
    async with rx.asession() as asession:
        return int(
            (
                await asession.execute(
                    text("SELECT COUNT(*) FROM remediation_log")
                )
            ).scalar()
            or 0
        )


async def main():
    print("=== Test remédiation AgriPro ===")
    state = RemediationState()
    await run_event(state.load_remediation)
    assert state.is_loading is False, "Le chargement doit être terminé"
    assert state.today_label != "", "La date doit être calculée"

    # --- 1) Alertes : clôture idempotente --------------------------------
    if state.alerts.length() > 0:
        alert = state.alerts[0]
        alert_id = alert["id"]
        await run_event(state.set_author_draft, "Test automatique")
        await run_event(state.set_note_draft, "Contrôle terrain effectué.")
        before = await log_count()
        await run_event(state.resolve_alert, alert_id)
        after = await log_count()
        assert after == before + 1, "La décision doit être consignée"
        remaining = [a for a in state.alerts if a["id"] == alert_id]
        assert remaining.length() == 0, "L'alerte clôturée sort de la liste"
        await run_event(state.resolve_alert, alert_id)
        assert await log_count() == after, "La clôture doit être idempotente"

    # --- 2) Stocks : recommandation et décision ---------------------------
    if state.stocks.length() > 0:
        product = state.stocks[0]
        assert product["recommendation"] != "", "Une recommandation est requise"
        assert product["order_quantity"] > 0, "Une quantité doit être proposée"
        before = await log_count()
        await run_event(state.decide_stock, product["id"], "COMMANDE")
        assert await log_count() == before + 1
        await run_event(state.decide_stock, product["id"], "COMMANDE")
        assert await log_count() == before + 1, "Décision idempotente"
        updated = [s for s in state.stocks if s["id"] == product["id"]]
        assert updated.length() == 1
        assert updated[0]["is_documented"] is True
        assert updated[0]["action"] == "COMMANDE"

    # --- 3) Contours : validation ou relevé -------------------------------
    if state.contours.length() > 0:
        contour = state.contours[0]
        assert contour["recommendation"] != ""
        before = await log_count()
        await run_event(state.decide_contour, contour["id"], "VERIFIE")
        assert await log_count() == before + 1
        await run_event(state.decide_contour, contour["id"], "VERIFIE")
        assert await log_count() == before + 1, "Validation idempotente"
        updated = [c for c in state.contours if c["id"] == contour["id"]]
        assert updated[0]["action"] == "VERIFIE"
        await run_event(state.decide_contour, contour["id"], "A_RELEVER")
        assert await log_count() == before + 2, "Un changement doit être tracé"

    assert state.history.length() > 0, "Le journal doit être alimenté"
    for entry in state.history:
        assert entry["action_label"] != ""
        assert entry["module_route"] != ""

    # --- Recherche globale ------------------------------------------------
    search = SearchState()
    await run_event(search.load_search)
    assert search.error == ""
    kinds = [section["kind"] for section in search.sections]
    assert kinds.contains("remediation"), (
        "Les décisions doivent être trouvables dans la recherche globale"
    )

    print(
        f"✓ {state.counters['decisions']:.0f} décision(s), "
        f"{state.open_total} état(s) ouvert(s), verdict : {state.verdict_label}"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

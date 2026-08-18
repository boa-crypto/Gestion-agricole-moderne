"""Vérifie le sous-module Stocks : impact, recommandations et décisions."""

import asyncio

import reflex as rx
from sqlalchemy import text
from test_utils import run_event

from app.states.operations_state import OperationsState
from app.states.remediation_state import RemediationState
from app.states.stock_state import StockState


async def stock_log_count() -> int:
    async with rx.asession() as asession:
        return int(
            (
                await asession.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM remediation_log
                        WHERE domain = 'STOCK'
                        """
                    )
                )
            ).scalar()
            or 0
        )


async def main():
    print("=== Test sous-module Stocks AgriPro ===")
    state = StockState()
    await run_event(state.load_stocks)
    assert state.is_loading is False, "Le chargement doit être terminé"
    assert state.today_label != "", "La date doit être calculée"
    assert state.error == ""
    for key in (
        "total",
        "rupture",
        "below",
        "open",
        "documented",
        "order_quantity",
        "order_cost",
        "jobs_at_risk",
        "decisions",
        "stock_value",
    ):
        assert state.summary[key] >= 0, f"Compteur manquant : {key}"
    assert state.verdict_label != ""
    assert state.verdict_detail != ""

    for item in state.items:
        assert item["recommendation"] != "", "Une recommandation est requise"
        assert item["impact"] != "", "L'impact chantier doit être expliqué"
        assert item["order_quantity"] > 0, "Une quantité doit être proposée"
        assert item["coverage_pct"] != ""
        assert item["severity"] in ("bad", "warn", "info")

    if state.items:
        row = state.items[0]
        product_id = row["id"]

        # Détail : chantiers exposés et historique de l'intrant.
        await run_event(state.select_product, product_id)
        assert state.selected_id == product_id
        assert state.selected_label != ""

        await run_event(state.set_author_draft, "Test automatique")
        before = await stock_log_count()
        await run_event(
            state.order_stock, product_id, "Commande passée au fournisseur."
        )
        assert await stock_log_count() == before + 1, "Décision consignée"
        assert state.notice != ""
        updated = [i for i in state.items if i["id"] == product_id]
        assert updated[0]["decision"] == "COMMANDE"
        assert updated[0]["is_documented"] is True
        assert updated[0]["decision_count"] > 0

        # Idempotence : même décision et même note ne dupliquent rien.
        await run_event(
            state.order_stock, product_id, "Commande passée au fournisseur."
        )
        assert await stock_log_count() == before + 1, "Décision idempotente"

        # Changement d'arbitrage : nouvelle ligne de journal.
        await run_event(
            state.defer_stock, product_id, "Chantier décalé d'une semaine."
        )
        assert await stock_log_count() == before + 2
        updated = [i for i in state.items if i["id"] == product_id]
        assert updated[0]["decision"] == "REPORT"

        await run_event(state.accept_stock, product_id, "Comptage local revu.")
        assert await stock_log_count() == before + 3

        await run_event(state.decide_stock, product_id, "INCONNU")
        assert state.error != "", "Une décision inconnue doit être refusée"

        # Vues du poste de contrôle.
        await run_event(state.set_view, "DOCUMENTE")
        assert [
            i for i in state.visible_items if not i["is_documented"]
        ].length() == 0
        await run_event(state.set_view, "A_ARBITRER")
        assert [
            i for i in state.visible_items if i["is_documented"]
        ].length() == 0
        await run_event(state.set_view, "TOUS")
        assert state.visible_items.length() == state.items.length()

        await run_event(state.clear_selection)
        assert state.selected_id == 0

    assert state.has_history, "Le journal doit être alimenté"
    for entry in state.history:
        assert entry["action_label"] != ""
        assert entry["target_label"] != ""

    # Les modules existants restent opérationnels.
    remediation = RemediationState()
    await run_event(remediation.load_remediation)
    assert remediation.error == ""
    assert remediation.counters["decisions"] >= state.summary["decisions"]

    operations = OperationsState()
    await run_event(operations.load_operations)
    assert operations.is_loading is False
    assert operations.kpis["products"] > 0

    print(
        f"✓ intrants={state.summary['total']:.0f}, ruptures={state.summary['rupture']:.0f}, "
        f"chantiers exposés={state.summary['jobs_at_risk']:.0f}, "
        f"commande={state.summary['order_cost']:.0f} €, décisions={state.summary['decisions']:.0f}"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

"""Vérifie l'API stable de RemediationState (résumé, listes, logs, messages)."""

import asyncio

from test_utils import run_event

from app.database import init_remediation_log_table, local_table_exists
from app.states.audit_state import AuditState
from app.states.remediation_state import RemediationState
from app.states.search_state import SearchState


async def main():
    print("=== Test API remédiation opérationnelle ===")

    # La table de traçabilité est créée de façon idempotente.
    init_remediation_log_table()
    init_remediation_log_table()
    assert local_table_exists("remediation_log") is not False

    state = RemediationState()
    await run_event(state.load_remediation)
    assert state.is_loading is False
    for key in (
        "alerts",
        "stock",
        "contours",
        "decisions",
        "open_total",
        "documented",
    ):
        assert state.summary[key] >= 0, f"Compteur manquant : {key}"
    assert state.recent_logs != None
    assert state.notice == ""
    assert state.error == ""

    if state.alert_actions:
        row = state.alert_actions[0]
        await run_event(
            state.resolve_alert, row["id"], "Test automatique: alerte traitée"
        )
        assert state.notice != ""
        ids = [item["id"] for item in state.alert_actions]
        assert ~ids.contains(row["id"]), "L'alerte clôturée sort de la liste"

    if state.stock_actions:
        row = state.stock_actions[0]
        await run_event(
            state.defer_stock, row["id"], "Test automatique: stock à suivre"
        )
        assert state.notice != ""
        await run_event(state.order_stock, row["id"], "Commande engagée")
        assert state.notice != ""

    if state.contour_actions:
        row = state.contour_actions[0]
        await run_event(
            state.mark_contour_to_survey,
            row["id"],
            "Test automatique: contour à relever",
        )
        assert state.notice != ""
        await run_event(state.mark_contour_verified, row["id"], "Vérifié")
        assert state.notice != ""

    assert state.recent_logs.length() > 0, "Le journal doit être alimenté"

    # L'audit et la recherche globale restent opérationnels.
    audit = AuditState()
    await run_event(audit.load_audit)
    assert audit.structural_issue_count >= 0
    for item in audit.operational_issues:
        assert item["domain"] == "exploitation"

    search = SearchState()
    await run_event(search.load_search)
    assert search.error == ""
    assert search.total_results > 0

    print(
        f"✓ alertes={state.summary['alerts']:.0f}, stocks={state.summary['stock']:.0f}, contours={state.summary['contours']:.0f}, logs={state.recent_logs.length()}"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

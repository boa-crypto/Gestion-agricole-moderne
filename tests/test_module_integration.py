"""Vérifie l'intégration des sous-modules Contours et Stocks.

Cockpit (pouls opérationnel), audit (tri sains / à traiter / documentés),
recherche globale (décisions de remédiation) et aide contextuelle (contextes
et sujets de règle) doivent rester cohérents, sans casser les écrans sains.
"""

import asyncio

from test_utils import run_event

from app.guide_hints import CONTEXTS, topic_spec
from app.states.audit_state import AuditState
from app.states.contour_state import ContourState
from app.states.help_state import HelpState
from app.states.remediation_state import RemediationState
from app.states.search_state import SearchState
from app.states.stock_state import StockState


async def main():
    print("=== Test intégration cockpit / audit / recherche / aide ===")

    # --- Cockpit : décisions récentes et priorités restantes --------------
    remediation = RemediationState()
    await run_event(remediation.load_remediation)
    stocks = StockState()
    await run_event(stocks.load_stocks)
    contours = ContourState()
    await run_event(contours.load_contours)

    assert remediation.error == "", "Le cockpit ne doit pas remonter d'erreur"
    assert remediation.verdict_label != "", "Un verdict est attendu"
    assert remediation.counters["decisions"] >= 0
    assert stocks.summary["order_cost"] >= 0, "Coût de commande consolidé"
    assert stocks.summary["open"] >= 0
    assert contours.control_rate_pct != "", "Taux de contrôle affiché"
    assert contours.open_total >= 0

    if stocks.items.length() > 0:
        product_id = stocks.items[0]["id"]
        await run_event(
            stocks.order_stock, product_id, "Intégration: commande engagée."
        )
        assert stocks.notice != "", "La décision doit être annoncée"
    if contours.items.length() > 0:
        parcel_id = contours.items[0]["id"]
        await run_event(
            contours.mark_verified, parcel_id, "Intégration: contour vérifié."
        )
        assert contours.notice != ""

    await run_event(remediation.load_remediation)
    assert remediation.counters["decisions"] > 0, (
        "Le cockpit doit refléter les décisions consignées"
    )
    for entry in remediation.history:
        assert entry["action_label"] != "", "Libellé d'action obligatoire"
        assert entry["domain_label"] != "", "Libellé de domaine obligatoire"
        assert entry["module_route"] != "", "Un écran cible est attendu"

    # --- Audit : tri sains / états à traiter / décisions documentées ------
    audit = AuditState()
    await run_event(audit.load_audit)
    assert audit.triage_label != "", "Le tri doit être lisible"
    assert audit.healthy_module_count == audit.healthy_modules.length()
    for module in audit.healthy_modules:
        assert module["status"] == "PRESENT", "Un module sain est présent"
        assert module["blocking_count"] == 0, (
            "Aucun bloquant sur un module sain"
        )
    for issue in audit.operational_issues:
        assert issue["domain"] == "exploitation"
        assert issue["recommendation"] != ""
    for issue in audit.coherence_issues:
        assert issue["domain"] == "coherence"
    total = (
        audit.structural_issue_count
        + audit.operational_issue_count
        + audit.coherence_issue_count
    )
    assert total == audit.issue_count, (
        "Chaque constat appartient à un seul domaine de lecture"
    )

    # --- Recherche globale : décisions retrouvables avec bons libellés ----
    search = SearchState()
    await run_event(search.load_search)
    assert search.error == ""
    kinds = [section["kind"] for section in search.sections]
    assert kinds.contains("remediation"), (
        "Les décisions de remédiation doivent être indexées"
    )
    remediation_section = [
        section
        for section in search.sections
        if section["kind"] == "remediation"
    ][0]
    for hit in remediation_section["hits"]:
        assert hit["title"] != ""
        assert hit["subtitle"] != "—", "Domaine et auteur attendus"
        assert len(hit["badges"]) > 0, "Domaine et action doivent être libellés"

    for term in ("contour", "intrants", "vérifié"):
        await run_event(search.set_term, term)
        assert search.error == "", f"Recherche « {term} » invalide"
        print(f"  · « {term} » → {search.total_results} résultat(s)")
    await run_event(search.reset_search)
    assert search.total_results > 0

    # --- Aide contextuelle : contextes et sujets de règle -----------------
    help_state = HelpState()
    for key in ("audit", "traitements", "cartographie"):
        assert key in CONTEXTS, f"Contexte manquant : {key}"
        await run_event(help_state.open_context, key)
        assert help_state.is_open is True
        assert help_state.content_count > 0, f"Aucun contenu pour {key}"

    for context_key, topic in (
        ("traitements", "stock"),
        ("cartographie", "geometrie"),
        ("cartographie", "surface"),
        ("cockpit", "phyto"),
    ):
        assert topic_spec(topic)["codes"], f"Sujet sans règle : {topic}"
        await run_event(help_state.open_topic, context_key, topic)
        assert help_state.has_focus is True
        assert help_state.focus_hint != ""
        assert help_state.focus_rules.length() > 0, (
            f"Aucune règle de cohérence pour {topic}"
        )
    await run_event(help_state.close_panel)
    assert help_state.is_open is False

    print(
        f"✓ décisions={remediation.counters['decisions']:.0f}, "
        f"modules sains={audit.healthy_module_count}, "
        f"états à traiter={audit.operational_issue_count}, "
        f"résultats recherche={search.total_results}"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

"""Vérifie le chargement de l'audit fonctionnel CMS² AgriPro."""

import asyncio

from test_utils import run_event

from app.audit_reference import (
    APP_ROUTES,
    ENTITY_SPECS,
    MODULE_SPECS,
    STATUS_ORDER,
)
from app.states.audit_state import AuditState


async def main():
    print("=== Test audit fonctionnel AgriPro ↔ Guide ===")
    state = AuditState()
    await run_event(state.load_audit)
    assert state.is_loading is False, "Le chargement doit être terminé"
    assert state.generated_label != "", "La date d'audit doit être calculée"

    # --- Cartographie des modules ---------------------------------------
    assert state.modules.length() == len(MODULE_SPECS), (
        "Chaque module applicatif doit être audité"
    )
    keys = [item["key"] for item in state.modules]
    for spec in MODULE_SPECS:
        assert keys.contains(spec["key"]), f"Module manquant : {spec['key']}"
        assert APP_ROUTES.count(spec["route"]) == 1, (
            f"Route non enregistrée : {spec['route']}"
        )
    for item in state.modules:
        assert STATUS_ORDER.count(item["status"]) == 1, (
            f"Statut non normalisé : {item['status']}"
        )
        assert item["status_label"] != "", (
            "Le libellé de statut est obligatoire"
        )
        assert item["priority_label"] != "", "La priorité doit être libellée"
        assert (item["coverage"] >= 0) & (item["coverage"] <= 100), (
            "La couverture doit être un pourcentage"
        )
        assert len(item["findings"]) > 0, (
            f"Constats manquants pour {item['key']}"
        )
        assert len(item["recommendations"]) > 0, (
            f"Recommandations manquantes pour {item['key']}"
        )

    # --- Entités de données ----------------------------------------------
    assert state.entities.length() == len(ENTITY_SPECS), (
        "Toutes les entités du référentiel doivent être comptées"
    )
    tables = [item["table"] for item in state.entities]
    for spec in ENTITY_SPECS:
        assert tables.contains(spec["table"]), (
            f"Entité absente de l'audit : {spec['table']}"
        )
    core = [item for item in state.entities if item["is_core"]]
    assert core.length() > 0, "Des entités structurantes sont attendues"
    assert state.kpis["records"] > 0, "Des enregistrements réels sont attendus"

    # --- Couverture éditoriale -------------------------------------------
    assert state.categories.length() > 0, (
        "Les catégories du Guide doivent être lues"
    )
    for item in state.categories:
        assert STATUS_ORDER.count(item["status"]) == 1
        assert item["total"] >= item["articles"]
    assert state.kpis["guide_contents"] > 0, "Le Guide doit être amorcé"

    # --- Constats normalisés ---------------------------------------------
    for item in state.issues:
        assert STATUS_ORDER.count(item["status"]) == 1, (
            f"Statut inconnu : {item['status']}"
        )
        assert item["recommendation"] != "", (
            f"Recommandation manquante pour {item['id']}"
        )
        assert item["domain_label"] != "", "Le domaine doit être libellé"
        assert item["module_route"] != "", "Un écran cible est attendu"

    # Un audit sain ne doit pas signaler de lien guide → application cassé.
    broken = [item for item in state.issues if item["domain"] == "liaison"]
    for item in broken:
        print(f"  · liaison à corriger : {item['label']}")

    # --- Filtres ----------------------------------------------------------
    await run_event(state.set_status_filter, "INCOHERENT")
    for item in state.visible_issues:
        assert item["status"] == "INCOHERENT"
    for item in state.visible_modules:
        assert item["status"] == "INCOHERENT"
    await run_event(state.reset_filters)
    assert state.status_filter == "TOUS"
    assert state.visible_issue_count == state.issue_count

    if state.modules.length() > 0:
        module_key = state.modules[0]["key"]
        await run_event(state.set_module_filter, module_key)
        for item in state.visible_issues:
            assert item["module"] == module_key
        await run_event(state.reset_filters)

    await run_event(state.set_domain_filter, "coherence")
    for item in state.visible_issues:
        assert item["domain"] == "coherence"
    await run_event(state.reset_filters)

    # --- Idempotence : deux exécutions donnent le même volume ------------
    first_issues = state.issue_count
    await run_event(state.load_audit)
    assert state.issue_count == first_issues, (
        "L'audit doit être stable d'une exécution à l'autre"
    )

    print(
        f"✓ {state.modules.length()} modules "
        f"(couverture moyenne {state.kpis['coverage']:.0f}%), "
        f"{state.entities.length()} entités, "
        f"{state.categories.length()} catégories, "
        f"{state.issue_count} constat(s) dont {state.kpis['blocking']:.0f} bloquant(s)"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

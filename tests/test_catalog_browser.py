"""Vérifie l'écran de consultation du référentiel cultures.

Contrôles : chargement complet (couverture, radar, liste, fiche détaillée,
focus dattes), recherche, filtres cycle et besoin en eau, navigation par
catégorie, sélection d'une culture, usages par module consommateur et
réinitialisation des filtres.
"""

import asyncio

from test_utils import run_event

from app.catalog_reference import (
    CATALOG_CONSUMERS,
    CYCLE_PERENNE,
    DATE_CATEGORY_KEY,
    DATE_VARIETY_NAMES,
    WATER_TRES_ELEVEE,
)
from app.states.catalog_browser_state import CatalogBrowserState


async def main():
    print("=== Test écran référentiel cultures ===")
    state = CatalogBrowserState()
    await run_event(state.load_referentiel)

    assert state.is_loading is False, "Le chargement doit être terminé"
    assert state.totals["categories"] >= 12, "Catégories manquantes"
    assert state.totals["varieties"] > 100, "Variétés manquantes"
    assert state.coverage.length() == 6, "Six indicateurs de couverture"
    assert state.nodes.length() == state.totals["categories"], (
        "Le radar doit porter une branche par catégorie"
    )
    for node in state.nodes:
        assert 0.0 < node["x_pct"] < 100.0, "Position radar hors cadre"
        assert 0.0 < node["y_pct"] < 100.0, "Position radar hors cadre"
        assert node["dot_size"] > 0, "Bourgeon de radar invisible"

    assert state.has_cultures is True, "La liste des cultures doit être remplie"
    assert state.has_selection is True, "Une culture doit être présélectionnée"
    assert state.species.length() > 0, "La fiche doit porter des espèces"
    assert state.consumers.length() == len(CATALOG_CONSUMERS), (
        "Chaque module consommateur doit recevoir une consigne"
    )
    for consumer in state.consumers:
        assert consumer["detail"] != "", "Consigne de module vide"

    # --- Focus dattes ---------------------------------------------------
    assert state.has_date_focus is True, "Le focus dattes doit être alimenté"
    assert state.palm["scientific_name"].startswith("Phoenix dactylifera"), (
        "Le focus doit porter le palmier dattier"
    )
    date_names = [v["name"] for v in state.date_varieties]
    for name in DATE_VARIETY_NAMES:
        assert date_names.contains(name), f"Variété de datte manquante : {name}"
    for variety in state.date_varieties:
        assert variety["consistency"] != "", (
            f"Consistance non classée pour {variety['name']}"
        )

    total_cultures = state.cultures.length()

    # --- Recherche -------------------------------------------------------
    await run_event(state.set_search, "palmier")
    assert state.cultures.length() >= 1, "La recherche doit trouver le palmier"
    assert state.cultures.length() < total_cultures, (
        "La recherche doit restreindre la liste"
    )

    await run_event(state.set_search, "zzzz-inexistant")
    assert state.cultures.length() == 0, "Aucun résultat attendu"
    assert state.has_selection is False, "Aucune fiche ne doit rester ouverte"
    assert state.consumers.length() == 0, "Aucune consigne sans sélection"

    await run_event(state.reset_filters)
    assert state.cultures.length() == total_cultures, (
        "La réinitialisation doit rétablir la liste complète"
    )
    assert state.has_filters is False, "Aucun filtre ne doit rester actif"

    # --- Filtres cycle et eau -------------------------------------------
    await run_event(state.set_cycle, CYCLE_PERENNE)
    assert state.cultures.length() > 0, "Des cultures pérennes doivent exister"
    for culture in state.cultures:
        assert culture["cycle_key"] == CYCLE_PERENNE, "Filtre de cycle ignoré"

    await run_event(state.set_water, WATER_TRES_ELEVEE)
    for culture in state.cultures:
        assert culture["water_key"] == WATER_TRES_ELEVEE, "Filtre d'eau ignoré"

    await run_event(state.reset_filters)

    # --- Navigation par catégorie ---------------------------------------
    await run_event(state.select_category, DATE_CATEGORY_KEY)
    assert state.cultures.length() == 1, "Une seule culture dans les dattes"
    assert state.culture["category_key"] == DATE_CATEGORY_KEY
    assert state.culture["cycle_key"] == CYCLE_PERENNE
    assert state.species.length() == 1, "Une espèce de palmier dattier"
    assert state.species[0]["variety_count"] >= len(DATE_VARIETY_NAMES)

    # --- Sélection explicite --------------------------------------------
    await run_event(state.reset_filters)
    target = state.cultures[3]["key"]
    await run_event(state.select_culture, target)
    assert state.selected_culture == target
    assert state.culture["key"] == target
    assert state.species.length() > 0

    # --- Raccourci focus dattes -----------------------------------------
    await run_event(state.focus_dates)
    assert state.category_filter == DATE_CATEGORY_KEY
    assert state.culture["category_key"] == DATE_CATEGORY_KEY

    print(
        f"✓ {state.coverage_label} · "
        f"{state.totals['date_varieties']} variétés de dattes · "
        f"{len(CATALOG_CONSUMERS)} modules consommateurs servis"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

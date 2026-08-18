"""Vérifie la base persistante et l'amorçage du Guide Agricole."""

import asyncio

from test_utils import run_event

from app.seed_guide import (
    ARTICLES,
    CATEGORIES,
    FAQ,
    PATHS,
    PROCEDURES,
    RULES,
    TERMS,
    seed_guide_data,
)
from app.states.guide_state import GuideState

EXPECTED_KEYS: list[str] = [
    "fondamentaux",
    "parcelles",
    "cultures",
    "travaux",
    "irrigation",
    "fertilisation",
    "phytosanitaire",
    "stocks",
    "materiel",
    "personnel",
    "recolte",
    "economie",
]


async def main():
    print("=== Test Guide Agricole (base + amorçage) ===")

    # Amorçage idempotent : deux appels ne doivent rien dupliquer.
    await seed_guide_data()
    await seed_guide_data()

    state = GuideState()
    await run_event(state.load_guide)
    assert state.is_loading is False, "Le chargement doit être terminé"

    assert state.totals["categories"] == len(CATEGORIES), (
        "Toutes les catégories doivent être amorcées une seule fois"
    )
    assert state.totals["articles"] == len(ARTICLES), (
        "Tous les articles doivent être publiés une seule fois"
    )
    assert state.totals["procedures"] == len(PROCEDURES), (
        "Toutes les procédures doivent être amorcées"
    )
    assert state.totals["terms"] == len(TERMS), (
        "Le dictionnaire doit être complet"
    )
    assert state.totals["faq"] == len(FAQ), (
        "Les questions fréquentes doivent être amorcées"
    )
    assert state.totals["rules"] == len(RULES), (
        "Les règles de cohérence doivent être amorcées"
    )
    assert state.totals["paths"] == len(PATHS), (
        "Les parcours d'apprentissage doivent être amorcés"
    )
    assert state.totals["versions"] == 1, "Une seule version publiée attendue"
    assert state.totals["steps"] > 0, "Les procédures doivent avoir des étapes"

    keys = [category["key"] for category in state.categories]
    for expected in EXPECTED_KEYS:
        assert keys.contains(expected), f"Catégorie manquante : {expected}"

    for article in state.articles:
        assert article["body_farmer"] != "", (
            "Chaque article doit avoir sa lecture agricole"
        )
        assert article["body_pro"] != "", (
            "Chaque article doit avoir sa lecture AgriPro"
        )

    assert state.featured_articles.length() > 0, (
        "Des articles mis en avant doivent exister"
    )
    assert state.why_rules.length() > 0, "Des règles « Pourquoi ? » attendues"
    assert state.warning_rules.length() > 0, (
        "Des règles « Attention » attendues"
    )
    assert state.frequent_questions.length() > 0, (
        "Des questions fréquentes doivent être marquées"
    )
    assert state.current_version["entry_count"] > 0, (
        "Le changelog de la version doit être renseigné"
    )

    print(
        f"✓ {state.totals['categories']} catégories, "
        f"{state.totals['articles']} articles, "
        f"{state.totals['procedures']} procédures "
        f"({state.totals['steps']} étapes), {state.totals['terms']} termes, "
        f"{state.totals['faq']} questions, {state.totals['rules']} règles, "
        f"{state.totals['paths']} parcours"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

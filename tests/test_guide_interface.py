"""Vérifie les interactions de l'interface du Guide Agricole."""

import asyncio

from test_utils import run_event

from app.states.guide_state import GuideState


async def main():
    print("=== Test interface Guide Agricole ===")
    state = GuideState()
    await run_event(state.load_guide)
    assert state.is_loading is False, "Le chargement doit être terminé"

    # Un article clé est ouvert par défaut avec sa double lecture.
    assert state.active_article_slug != "", (
        "Un article doit être présélectionné"
    )
    assert state.farmer_paragraphs.length() > 0, "Lecture agricole attendue"
    assert state.pro_paragraphs.length() > 0, "Lecture AgriPro attendue"
    assert state.article_links.length() > 0, (
        "Des liens modules doivent être chargés"
    )
    assert state.related_procedures.length() > 0, "Procédures liées attendues"
    assert state.related_scope_label != "", (
        "Le périmètre des procédures doit être annoncé"
    )

    # Chaque article doit rester exploitable par « Comment faire dans AgriPro ? ».
    for article in state.articles:
        await run_event(state.select_article, article["slug"])
        assert state.related_procedures.length() > 0, (
            f"Aucune procédure exploitable pour {article['slug']}"
        )
    await run_event(state.select_article, state.articles[0]["slug"])

    # Recherche globale groupée par type.
    await run_event(state.set_query, "azote")
    assert state.search_groups.length() > 0, (
        "La recherche doit remonter des groupes"
    )
    kinds = [group["kind"] for group in state.search_groups]
    unique_kinds: list[str] = []
    for kind in kinds:
        if kind not in unique_kinds:
            unique_kinds.append(kind)
    assert len(unique_kinds) == kinds.length(), "Un groupe par type de contenu"
    assert state.search_total > 0, "Des résultats doivent être comptés"

    # Ouverture d'un résultat de type article depuis la recherche.
    article_groups = [g for g in state.search_groups if g["kind"] == "article"]
    if article_groups:
        hit = article_groups[0]["hits"][0]
        await run_event(state.open_hit, hit["kind"], hit["ref"])
        assert state.active_article_slug == hit["ref"], (
            "Le clic sur un résultat doit ouvrir l'article"
        )
        assert state.active_section == "bibliotheque"

    await run_event(state.clear_query)
    assert (state.query == "") & (state.search_groups == [])

    # Procédures interactives : étapes + progression.
    await run_event(state.open_related_procedures)
    slug = state.related_procedures[0]["slug"]
    await run_event(state.start_procedure, slug)
    assert state.procedure_steps.length() > 0, (
        "Les étapes doivent être chargées"
    )
    assert state.step_progress == 0
    first_step = state.procedure_steps[0]["id"]
    await run_event(state.toggle_step, first_step)
    assert state.done_steps.contains(first_step)
    assert state.step_progress > 0, "La progression doit augmenter"
    await run_event(state.toggle_step, first_step)
    assert ~state.done_steps.contains(first_step)
    await run_event(state.close_procedure)
    assert state.open_procedure_slug == ""

    # Catégories : filtrage des articles, FAQ et règles.
    category = state.categories[1]["key"]
    await run_event(state.select_category, category)
    assert state.selected_category == category
    for item in state.category_articles:
        assert item["category_key"] == category
    for item in state.visible_faq:
        assert item["category_key"] == category
    await run_event(state.select_category, "TOUS")

    # Dictionnaire interactif.
    await run_event(state.set_term_query, "azote")
    assert state.visible_terms.length() > 0, (
        "Le filtre du dictionnaire doit trouver"
    )
    await run_event(state.select_term, state.visible_terms[0]["slug"])
    assert state.active_section == "dictionnaire"
    assert state.active_term["definition_pro"] != ""
    await run_event(state.set_term_query, "")

    # FAQ intelligente : accordéon.
    faq_id = state.faq[0]["id"]
    await run_event(state.toggle_faq, faq_id)
    assert state.open_faq_id == faq_id
    await run_event(state.toggle_faq, faq_id)
    assert state.open_faq_id == 0

    # Règles Pourquoi / Attention.
    await run_event(state.set_rule_filter, "ATTENTION")
    for rule in state.visible_rules:
        assert rule["kind"] == "ATTENTION"
    await run_event(state.set_rule_filter, "TOUS")
    assert (state.why_rules.length() > 0) & (state.warning_rules.length() > 0)

    # Parcours d'apprentissage.
    assert state.farmer_paths.length() > 0, "Parcours agricole attendu"
    assert state.pro_paths.length() > 0, "Parcours AgriPro attendu"
    await run_event(state.select_path, state.paths[-1]["slug"])
    assert state.path_steps.length() > 0, (
        "Les étapes du parcours doivent charger"
    )

    # Carte des relations de données.
    keys = [node["key"] for node in state.relation_chain]
    for expected in [
        "exploitation",
        "parcelle",
        "culture",
        "campagne",
        "intervention",
        "intrants",
        "main_oeuvre",
        "materiel",
        "cout",
        "recolte",
        "rendement",
        "vente",
        "resultat",
    ]:
        assert keys.contains(expected), f"Maillon manquant : {expected}"
    await run_event(state.select_relation, "recolte")
    assert state.active_relation_node["label"] == "Récolte"
    assert state.active_section == "relations"

    print(
        f"✓ {state.totals['articles']} articles, {state.totals['procedures']} procédures, {state.relation_chain.length()} maillons de la carte de données"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

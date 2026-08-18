"""Vérifie le pupitre éditorial du Guide Agricole (administration)."""

import asyncio

from test_utils import run_event

from app.states.guide_admin_state import GuideAdminState


async def main():
    print("=== Test administration éditoriale du Guide ===")
    state = GuideAdminState()
    await run_event(state.load_admin)
    assert state.is_loading is False, "Le chargement doit être terminé"
    assert state.categories.length() > 0, "Les catégories doivent être chargées"
    assert state.versions.length() > 0, "Une version doit exister"
    assert state.has_current_version is True, "Une version courante attendue"
    assert state.changelog.length() > 0, "Le changelog doit être lisible"
    assert state.items.length() > 0, "Le registre des articles doit être rempli"
    assert state.status_totals["TOTAL"] > 0, (
        "Les compteurs doivent être calculés"
    )

    # --- Navigation par type de contenu ---------------------------------
    for kind, _label, _icon in state.kind_tabs:
        await run_event(state.set_content_kind, kind)
        assert state.content_kind == kind
        assert state.items.length() > 0, f"Registre vide pour {kind}"
        for item in state.items:
            assert item["kind"] == kind

    # --- Filtrage par statut, catégorie et recherche ---------------------
    await run_event(state.set_content_kind, "article")
    await run_event(state.set_filter_status, "PUBLIE")
    for item in state.items:
        assert item["status"] == "PUBLIE"
    category = state.items[0]["category_key"]
    await run_event(state.set_filter_category, category)
    for item in state.items:
        assert item["category_key"] == category
    await run_event(state.reset_filters)
    assert state.filter_status == "TOUS"
    await run_event(state.set_search, "parcelle")
    assert state.items.length() > 0, "La recherche éditoriale doit trouver"
    await run_event(state.reset_filters)

    # --- Validation : une création incomplète est refusée ----------------
    await run_event(state.start_create, "article")
    assert state.editor_open is True
    await run_event(
        state.save_content,
        {
            "slug": "Mauvais Slug",
            "title": "x",
            "body_farmer": "trop court",
            "body_pro": "trop court",
            "status": "BROUILLON",
            "version_label": "abc",
            "category_key": "",
            "reading_minutes": "0",
            "audience": "MIXTE",
            "difficulty": "DECOUVERTE",
        },
    )
    assert state.has_errors is True, "La validation doit bloquer la fiche"
    assert state.editor_open is True, "La fiche reste ouverte pour correction"

    # --- Création valide d'un article en brouillon -----------------------
    slug = "fiche-editoriale-de-test"
    await run_event(
        state.save_content,
        {
            "slug": slug,
            "title": "Fiche éditoriale de test",
            "subtitle": "Contrôle du pupitre éditorial",
            "summary": "Fiche créée par le test d'administration éditoriale.",
            "body_farmer": (
                "Cette fiche vérifie que la lecture agricole est bien "
                "enregistrée dans la base locale du guide."
            ),
            "body_pro": (
                "Cette fiche vérifie que la lecture AgriPro est bien "
                "persistée avec ses métadonnées éditoriales."
            ),
            "status": "BROUILLON",
            "version_label": state.current_version["version_label"],
            "category_key": state.categories[0]["key"],
            "reading_minutes": "4",
            "audience": "MIXTE",
            "difficulty": "DECOUVERTE",
            "author": "Test éditorial",
            "keywords": "test, pupitre",
            "module_route": "/guide",
        },
    )
    assert state.has_errors is False, "La fiche valide doit être acceptée"
    assert state.editor_open is False, "La fiche se referme après succès"

    await run_event(state.set_content_kind, "article")
    await run_event(state.set_search, "fiche éditoriale de test")
    matches = [item for item in state.items if item["ref"] == slug]
    assert matches.length() == 1, "La fiche créée doit apparaître au registre"
    created = matches[0]
    assert created["status"] == "BROUILLON"

    # --- Doublon d'identifiant refusé ------------------------------------
    await run_event(state.start_create, "article")
    await run_event(
        state.save_content,
        {
            "slug": slug,
            "title": "Doublon éditorial",
            "summary": "Doublon volontaire pour contrôler l'unicité.",
            "body_farmer": (
                "Texte agricole suffisamment long pour passer la validation "
                "de longueur minimale."
            ),
            "body_pro": (
                "Texte AgriPro suffisamment long pour passer la validation "
                "de longueur minimale."
            ),
            "status": "BROUILLON",
            "version_label": state.current_version["version_label"],
            "category_key": state.categories[0]["key"],
            "reading_minutes": "3",
            "audience": "MIXTE",
            "difficulty": "DECOUVERTE",
        },
    )
    assert state.has_errors is True, "Un slug en doublon doit être refusé"
    await run_event(state.close_editor)

    # --- Édition, aperçu et cycle de statut ------------------------------
    await run_event(state.start_edit, "article", created["id"])
    assert state.draft["slug"] == slug
    assert state.editor_mode == "edit"
    await run_event(state.close_editor)

    await run_event(state.open_preview, "article", created["id"])
    assert state.preview_open is True
    assert state.preview["body_farmer"] != ""
    await run_event(state.close_preview)

    await run_event(
        state.set_content_status, "article", created["id"], "RELECTURE"
    )
    await run_event(
        state.set_content_status, "article", created["id"], "PUBLIE"
    )
    await run_event(state.set_search, "fiche éditoriale de test")
    published = [item for item in state.items if item["ref"] == slug][0]
    assert published["status"] == "PUBLIE", "La fiche doit être publiée"

    # --- Archivage plutôt que suppression --------------------------------
    await run_event(state.archive_content, "article", created["id"])
    await run_event(state.set_search, "fiche éditoriale de test")
    archived = [item for item in state.items if item["ref"] == slug][0]
    assert archived["status"] == "ARCHIVE", "La fiche doit être archivée"
    await run_event(state.reset_filters)

    # --- Versions : création, publication, dépublication -----------------
    label = state.next_version_suggestion
    previous_id = state.current_version["id"]
    await run_event(
        state.create_version,
        {
            "version_label": label,
            "title": "Guide Agricole — version de test",
            "summary": "Version ouverte par le test d'administration éditoriale.",
            "author": "Test éditorial",
        },
    )
    assert state.has_errors is False, "La version doit être créée"
    new_versions = [v for v in state.versions if v["version_label"] == label]
    assert new_versions.length() == 1, "La nouvelle version doit apparaître"
    new_version = new_versions[0]
    assert new_version["status"] == "BROUILLON"
    assert new_version["entry_count"] > 0, "Le changelog doit être amorcé"

    await run_event(state.publish_version, new_version["id"])
    assert state.current_version["version_label"] == label, (
        "La version publiée devient courante"
    )
    assert state.current_version["status"] == "PUBLIE"

    await run_event(state.unpublish_version, new_version["id"])
    dep = [v for v in state.versions if v["version_label"] == label][0]
    assert dep["status"] == "RELECTURE", "La dépublication repasse en relecture"
    assert dep["is_current"] is False

    await run_event(state.archive_version, new_version["id"])
    arch = [v for v in state.versions if v["version_label"] == label][0]
    assert arch["status"] == "ARCHIVE", "La version doit être archivable"

    # Restauration de la version d'origine comme version courante.
    await run_event(state.publish_version, previous_id)
    assert state.current_version["id"] == previous_id

    # Doublon de version refusé.
    await run_event(
        state.create_version,
        {
            "version_label": state.current_version["version_label"],
            "title": "Doublon de version éditoriale",
            "summary": "Doublon volontaire pour contrôler l'unicité des versions.",
            "author": "Test éditorial",
        },
    )
    assert state.has_errors is True, "Une version en doublon doit être refusée"

    print(
        f"✓ Pupitre éditorial : {state.versions.length()} version(s), "
        f"{state.status_totals['TOTAL']} fiches articles, "
        f"{state.changelog.length()} entrée(s) de changelog"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

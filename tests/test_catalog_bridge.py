"""Vérifie la liaison du référentiel cultures aux modules existants.

Contrôles :

* matérialisation idempotente des variétés du référentiel dans le référentiel
  variétal historique (`crop_variety`) ;
* parcelles : options variétales issues du référentiel structuré et lecture
  Catégorie → Culture → Espèce → Variété sur les fiches culturales ;
* recherche globale : catégories, cultures, espèces et variétés retrouvées avec
  un lien vers `/referentiel` ;
* audit : module « Référentiel cultures » couvert, avec ses entités et la
  cohérence des liens historiques ;
* aide contextuelle : accès au référentiel depuis parcelles, traitements, audit.
"""

import asyncio

import reflex as rx
from sqlalchemy import text
from test_utils import run_event

from app.catalog_link import catalog_totals, materialize_catalog_varieties
from app.guide_hints import CONTEXT_SHORTCUTS, shortcut_spec
from app.states.audit_state import AuditState
from app.states.parcels_state import ParcelsState
from app.states.search_state import SearchState

CATALOG_SEARCH_KINDS: list[str] = [
    "categorie_referentiel",
    "culture_referentiel",
    "espece_referentiel",
    "variete_referentiel",
]


async def main():
    print("=== Test liaison référentiel ↔ modules ===")

    # --- Parcelles : amorce tout (référentiel + matérialisation) ----------
    parcels = ParcelsState()
    await run_event(parcels.load_space)
    assert parcels.is_loading is False, "Le chargement doit être terminé"

    # --- Matérialisation idempotente -------------------------------------
    again = await materialize_catalog_varieties()
    assert again == 0, "La matérialisation doit être idempotente"
    totals = await catalog_totals()
    assert totals["varieties"] > 100, "Référentiel variétal incomplet"
    assert totals["linked"] == totals["varieties"], (
        "Chaque variété du référentiel doit être reliée au référentiel "
        f"historique ({totals['linked']}/{totals['varieties']})"
    )

    async with rx.asession() as asession:
        unlinked = (
            await asession.execute(
                text(
                    "SELECT COUNT(*) FROM crop_catalog_variety "
                    "WHERE crop_variety_id IS NULL"
                )
            )
        ).scalar()
    assert int(unlinked or 0) == 0, "Variétés non reliées restantes"

    # --- Options variétales du référentiel structuré ----------------------
    assert parcels.variety_options.length() > 100, (
        "Les parcelles doivent proposer les variétés du référentiel"
    )
    assert parcels.catalog_variety_count == parcels.variety_options.length()
    for option in parcels.variety_options[:20]:
        assert option["label"].count("·") >= 2, (
            f"Libellé non hiérarchisé : {option['label']}"
        )
        assert "—" in option["label"], (
            f"Variété absente du libellé : {option['label']}"
        )
    assert parcels.catalog_totals["categories"] >= 12
    assert parcels.catalog_coverage_label.contains("catégories")

    # --- Lecture référentielle des fiches culturales ----------------------
    assert parcels.parcel_crops.length() > 0, (
        "La parcelle doit porter des cultures"
    )
    assert parcels.has_catalog_links is True, (
        "Au moins une culture doit être reliée au référentiel"
    )
    for crop in parcels.catalog_linked_crops:
        assert crop["catalog_path"].count("→") == 3, (
            f"Chemin référentiel incomplet : {crop['catalog_path']}"
        )
        assert crop["catalog_category"] != ""
        assert crop["catalog_culture"] != ""
        assert crop["catalog_species"] != ""
        assert crop["catalog_variety"] != ""
        assert crop["catalog_cycle_label"] != ""
        assert crop["catalog_water_label"] != ""
        assert crop["catalog_cycle_tone"] != ""
    assert parcels.catalog_link_label.contains("reliée")

    # --- Recherche globale ------------------------------------------------
    search = SearchState()
    await run_event(search.load_search)
    assert search.error == "", "Aucune erreur au chargement de la recherche"
    kinds = [chip["value"] for chip in search.chips]
    for kind in CATALOG_SEARCH_KINDS:
        assert kinds.contains(kind), f"Type de recherche manquant : {kind}"

    await run_event(search.set_term, "Deglet")
    found = [section["kind"] for section in search.sections]
    assert found.contains("variete_referentiel"), (
        "Les variétés du référentiel doivent être retrouvées"
    )
    for section in search.sections:
        if section["kind"] in CATALOG_SEARCH_KINDS:
            assert section["href"] == "/referentiel", (
                "Le référentiel doit être accessible depuis la recherche"
            )
            for hit in section["hits"]:
                assert hit["title"] != ""
                assert hit["subtitle"] != "—"

    await run_event(search.set_term, "palmier dattier")
    catalog_sections = [
        section
        for section in search.sections
        if section["kind"] in CATALOG_SEARCH_KINDS
    ]
    assert catalog_sections.length() >= 2, (
        "Cultures et espèces du référentiel doivent remonter"
    )

    await run_event(search.set_entity_filter, "categorie_referentiel")
    assert search.sections.length() == 1
    assert search.sections[0]["count"] >= 1

    await run_event(search.reset_search)

    # --- Audit ------------------------------------------------------------
    audit = AuditState()
    await run_event(audit.load_audit)
    assert audit.is_loading is False
    modules = {item["key"]: item for item in audit.modules}
    assert modules.contains("referentiel"), "Le référentiel doit être audité"
    referentiel = modules["referentiel"]
    assert referentiel["route"] == "/referentiel"
    assert referentiel["records"] > 100, "Volumes du référentiel non comptés"
    assert referentiel["tables"] == 4
    assert referentiel["empty_tables"].length() == 0, (
        f"Entités vides : {referentiel['empty_tables']}"
    )
    assert referentiel["status"] != "MANQUANT", (
        "Le référentiel doit être présent dans l'audit"
    )
    assert referentiel["coverage"] >= 70, (
        f"Couverture trop faible : {referentiel['coverage']}"
    )
    tables = [entity["table"] for entity in audit.entities]
    for table in (
        "crop_category",
        "crop_culture",
        "crop_species",
        "crop_catalog_variety",
    ):
        assert tables.contains(table), f"Entité absente de l'audit : {table}"
    unlinked_issues = [
        issue
        for issue in audit.issues
        if issue["id"] == "catalog-variete-non-liee"
    ]
    assert unlinked_issues.length() == 0, (
        "Aucun lien historique ne doit manquer après matérialisation"
    )

    # --- Aide contextuelle ------------------------------------------------
    for context in ("parcelles", "traitements", "audit"):
        assert context in CONTEXT_SHORTCUTS, f"Raccourci manquant : {context}"
        spec = shortcut_spec(context)
        assert spec["route"] == "/referentiel"
        assert spec["title"] != "" and spec["detail"] != ""

    print(
        f"✓ {totals['varieties']} variétés reliées · {parcels.variety_options.length()} options parcellaires · {parcels.catalog_linked_crops.length()} culture(s) documentée(s) · module d'audit « {referentiel['label']} » à {referentiel['coverage_pct']}"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

"""Vérifie l'API stable de validation phénologique par nom de culture.

Contrôles :

* `validate_stage_for_crop(asession, culture_name, stage_name)` accepte une
  session fournie, n'utilise que du SQL brut et retourne un objet exploitable
  (`is_valid`, `message`, `available_stages`) ;
* cohérence métier : Blé dur / Tallage valide, Tomate / Nouaison valide,
  Olivier / Tallage refusé avec la liste des stades réellement disponibles ;
* `phenology_audit_matrix(asession)` fournit les compteurs de profils, de
  stades et d'observations invalides.
"""

import asyncio

import reflex as rx

from app.catalog_link import materialize_catalog_varieties
from app.database import init_local_database, init_phenology_tables
from app.phenology_validation import (
    culture_profile_candidates,
    phenology_audit_matrix,
    phenology_audit_report,
    validate_stage_for_crop,
    validate_stage_for_crop_name,
)
from app.seed_catalog import link_legacy_varieties, seed_catalog_data
from app.seed_phenology import seed_phenology_data


async def main():
    print("=== Test validation phénologique par culture ===")
    init_local_database()
    init_phenology_tables()
    await seed_catalog_data()
    await link_legacy_varieties()
    await materialize_catalog_varieties()
    await seed_phenology_data()

    async with rx.asession() as asession:
        candidates = await culture_profile_candidates(asession, "Blé dur")
        assert candidates, "Aucun profil rapproché pour « Blé dur »"

        wheat = await validate_stage_for_crop(asession, "Blé dur", "Tallage")
        tomato = await validate_stage_for_crop(asession, "Tomate", "Nouaison")
        olive = await validate_stage_for_crop(asession, "Olivier", "Tallage")

        assert wheat.is_valid, wheat.message
        assert wheat.stage_name == "Tallage"
        assert wheat.progress > 0
        assert wheat.available_stages

        assert tomato.is_valid, tomato.message
        assert tomato.stage_name == "Nouaison"

        assert not olive.is_valid, "Olivier + Tallage doit être refusé"
        assert olive.message != ""
        assert olive.available_stages, "Les stades disponibles sont attendus"
        assert "Tallage" not in olive.available_stages

        empty = await validate_stage_for_crop(asession, "Culture X", "Tallage")
        assert not empty.is_valid
        assert empty.available_stages == []

        no_stage = await validate_stage_for_crop(asession, "Tomate", "")
        assert not no_stage.is_valid
        assert no_stage.available_stages

        matrix = await phenology_audit_matrix(asession)
        assert matrix["profiles"] >= 4, matrix
        assert matrix["stages"] >= 25, matrix
        assert matrix["invalid_observations"] == 0, matrix
        assert matrix["prescriptive_recommendations"] == 0, matrix

    standalone = await validate_stage_for_crop_name("Tomate", "Véraison")
    assert standalone.is_valid, standalone.message
    report = await phenology_audit_report()
    assert report["profiles"] >= 4

    print(
        f"✓ {report['profiles']} profils, {report['stages']} stades, "
        f"{report['invalid_observations']} observation(s) invalide(s) ; "
        "Blé dur/Tallage valide, Tomate/Nouaison valide, Olivier/Tallage refusé"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

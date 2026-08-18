"""Vérifie la modélisation et l'amorçage du suivi phénologique multicultures.

Contrôles :

* création idempotente des tables locales et de l'amorçage ;
* cycles DISTINCTS par culture (aucune liste globale unique) ;
* cohérence stade ↔ culture : Blé/Tallage valide, Tomate/Nouaison valide,
  Olivier/Tallage invalide ;
* résolution du profil applicable à une culture de parcelle (avec priorité de
  l'espèce sur la culture) ;
* observation traçable : historique conservé, progression calculée ;
* recommandations toujours non prescriptives.
"""

import asyncio
import datetime

import reflex as rx
from sqlalchemy import text

from app.database import init_phenology_tables
from app.phenology_reference import (
    CONFIDENCE_KEYS,
    DEVIATION_LONG,
    DEVIATION_NORMAL,
    RECOMMENDATION_DOMAIN_KEYS,
    SYSTEM_KEYS,
    is_stage_declared,
    normalize_stage_label,
    stage_duration_status,
    stage_progress_percent,
)
from app.phenology_validation import (
    culture_stage_labels,
    observation_history,
    profile_for_crop,
    profile_for_culture_key,
    profile_stages,
    record_stage_observation,
    stage_duration_report,
    stage_recommendations,
    validate_observation,
    validate_stage_for_culture,
)
from app.seed import seed_dashboard_data
from app.seed_phenology import phenology_totals, seed_phenology_data

EXPECTED_CULTURES: list[str] = [
    "cereales--ble",
    "cereales--mais",
    "maraichage--tomate",
    "maraichage--oignon",
    "tubercules--pomme-de-terre",
    "arboriculture--olivier",
    "agrumes--oranger",
    "vigne--raisin-de-table",
    "dattes--palmier-dattier",
    "legumineuses--pois-chiche",
]


async def main():
    print("=== Test suivi phénologique multicultures ===")

    # --- Fonctions pures --------------------------------------------------
    assert normalize_stage_label("Tallage") == "tallage"
    assert normalize_stage_label("  ÉPIAISON ") == "epiaison"
    assert normalize_stage_label("Grain laiteux") == "grain-laiteux"
    assert stage_progress_percent(3, 8) == 38
    assert stage_progress_percent(8, 8) == 100
    assert stage_progress_percent(0, 8) == 0
    assert stage_progress_percent(2, 0) == 0
    assert stage_duration_status(12, 5, 15) == DEVIATION_NORMAL
    assert stage_duration_status(22, 5, 15) == DEVIATION_LONG
    assert is_stage_declared("cereales--ble", "Tallage") is True
    assert is_stage_declared("maraichage--tomate", "Nouaison") is True
    assert is_stage_declared("arboriculture--olivier", "Tallage") is False

    # --- Tables locales et amorçage idempotent ----------------------------
    init_phenology_tables()
    await seed_dashboard_data()
    await seed_phenology_data()
    first = await phenology_totals()

    import app.seed_phenology as seed_module

    seed_module._seeded = False
    await seed_phenology_data()
    second = await phenology_totals()
    for key in ("profiles", "stages", "recommendations"):
        assert first[key] == second[key], (
            f"Amorçage non idempotent sur {key} : {first[key]} → {second[key]}"
        )
    assert first["profiles"] >= 10, "Profils phénologiques incomplets"
    assert first["stages"] >= 80, "Stades phénologiques incomplets"
    assert first["recommendations"] > 0, "Recommandations manquantes"

    # --- Un cycle par culture, sans liste globale unique -------------------
    signatures: dict[str, str] = {}
    for culture_key in EXPECTED_CULTURES:
        resolution = await profile_for_culture_key(culture_key)
        assert resolution["found"], f"Profil manquant : {culture_key}"
        assert resolution["system"] in SYSTEM_KEYS
        stages = await profile_stages(resolution["profile_id"])
        assert len(stages) >= 7, f"Cycle trop court : {culture_key}"
        positions = [stage["position"] for stage in stages]
        assert positions == sorted(positions), (
            f"Stades non ordonnés pour {culture_key}"
        )
        assert positions[0] == 1
        assert stages[-1]["progress"] == 100
        signatures[culture_key] = "|".join(
            normalize_stage_label(stage["name"]) for stage in stages
        )
    assert len(set(signatures.values())) == len(signatures), (
        "Deux cultures partagent le même cycle : un référentiel global unique "
        "est interdit"
    )

    # --- Cohérence stade ↔ culture ----------------------------------------
    wheat = await validate_stage_for_culture("cereales--ble", "Tallage")
    assert wheat["valid"] is True, wheat["reason"]
    assert wheat["stage_name"] == "Tallage"
    assert wheat["progress"] > 0

    tomato = await validate_stage_for_culture("maraichage--tomate", "Nouaison")
    assert tomato["valid"] is True, tomato["reason"]
    assert tomato["stage_name"] == "Nouaison"

    olive = await validate_stage_for_culture(
        "arboriculture--olivier", "Tallage"
    )
    assert olive["valid"] is False, (
        "Olivier + Tallage doit être refusé par le contrôle de cohérence"
    )
    assert olive["reason"] != ""
    assert "Tallage" not in olive["allowed"]

    olive_ok = await validate_stage_for_culture(
        "arboriculture--olivier", "nouaison"
    )
    assert olive_ok["valid"] is True, "La nouaison existe chez l'olivier"

    olive_labels = await culture_stage_labels("arboriculture--olivier")
    assert "Repos végétatif" in olive_labels
    assert "Tallage" not in olive_labels

    # --- Résolution du profil pour une culture de parcelle -----------------
    async with rx.asession() as asession:
        crop_row = (
            await asession.execute(
                text(
                    """
                    SELECT c.id, c.name FROM crop c
                    JOIN crop_variety v ON v.id = c.variety_id
                    WHERE v.name = 'Rubisko' LIMIT 1
                    """
                )
            )
        ).first()
    assert crop_row is not None, "La culture de blé amorcée est introuvable"
    crop_id = int(crop_row[0])

    resolved = await profile_for_crop(crop_id)
    assert resolved["found"], "Le blé doit résoudre un profil phénologique"
    assert resolved["culture_key"] == "cereales--ble"
    assert resolved["scope"] in ("ESPECE", "CULTURE", "VARIETE")
    assert resolved["stage_count"] >= 8

    # --- Validation d'une observation --------------------------------------
    today = datetime.date.today()
    bad_date = await validate_observation(
        crop_id, "Tallage", today + datetime.timedelta(days=3), "Technicien X"
    )
    assert bad_date["valid"] is False, "Une date future doit être refusée"

    bad_observer = await validate_observation(crop_id, "Tallage", today, "")
    assert bad_observer["valid"] is False, "L'observateur est obligatoire"

    bad_stage = await validate_observation(
        crop_id, "Véraison", today, "Technicien X"
    )
    assert bad_stage["valid"] is False, (
        "La véraison n'appartient pas au cycle du blé"
    )

    good = await validate_observation(crop_id, "Tallage", today, "Technicien X")
    assert good["valid"] is True, good["errors"]

    # --- Écriture traçable -------------------------------------------------
    before = len(await observation_history(crop_id))
    written = await record_stage_observation(
        crop_id=crop_id,
        stage_label="Tallage",
        observed_on=today,
        observer="Technicien X",
        comment="Tallage homogène sur cinq placettes.",
    )
    assert written["ok"] is True, written["errors"]
    assert int(written["observation_id"]) > 0
    second_write = await record_stage_observation(
        crop_id=crop_id,
        stage_label="Montaison",
        observed_on=today,
        observer="Technicien X",
        comment="Épi 1 cm atteint.",
    )
    assert second_write["ok"] is True, second_write["errors"]
    history = await observation_history(crop_id)
    assert len(history) == before + 2, (
        "L'historique doit conserver les deux pas"
    )
    assert history[0]["new_stage"] == "Montaison"
    assert history[0]["previous_stage"] == "Tallage", (
        "L'ancien stade doit être conservé dans l'historique"
    )

    refused = await record_stage_observation(
        crop_id=crop_id,
        stage_label="Tallage",
        observed_on=today + datetime.timedelta(days=5),
        observer="Technicien X",
    )
    assert refused["ok"] is False, (
        "Une observation invalide ne doit rien écrire"
    )
    assert len(await observation_history(crop_id)) == before + 2

    report = await stage_duration_report(crop_id)
    assert int(report["has_observation"]) == 1
    assert report["stage_name"] == "Montaison"
    assert int(report["progress"]) > 0

    # --- Recommandations non prescriptives ---------------------------------
    stages = await profile_stages(resolved["profile_id"])
    checked = 0
    for stage in stages:
        for reco in await stage_recommendations(stage["id"]):
            assert reco["is_advisory"] is True, (
                "Aucune recommandation ne doit être prescriptive"
            )
            assert reco["domain"] in RECOMMENDATION_DOMAIN_KEYS
            assert reco["confidence"] in CONFIDENCE_KEYS
            assert reco["title"] != "" and reco["statement"] != ""
            assert reco["source"] != ""
            checked += 1
    assert checked > 0, "Le cycle du blé doit porter des recommandations"

    print(
        f"✓ {first['profiles']} profils sur {first['cultures']} cultures, "
        f"{first['stages']} stades, {first['recommendations']} recommandations "
        f"indicatives ; Blé/Tallage valide, Tomate/Nouaison valide, "
        f"Olivier/Tallage refusé ; {len(history)} changement(s) tracé(s)"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

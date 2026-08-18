"""Vérifie l'administration, l'import/export et les validations finales.

Contrôles :

* administration : création/modification de profil et de stade, réordonnancement,
  désactivation non destructive, criticité, liens Guide, recommandations
  toujours indicatives ;
* import CSV et JSON additif : enrichissement sans suppression ;
* export JSON et CSV des profils / stades / recommandations ;
* API internes : stades d'une culture, phénologie d'une parcelle et d'une
  culture, publication d'observation, historique, calendrier, détail d'un stade ;
* validations finales : Blé + Tallage valide, Tomate + Nouaison valide,
  Olivier + Tallage invalide, historique conservé, recommandations non
  prescriptives.
"""

import asyncio
import datetime
import json

import reflex as rx
from sqlalchemy import text
from test_utils import run_event

from app.phenology_admin import (
    admin_profiles,
    admin_recommendations,
    admin_stages,
    culture_options,
    export_phenology_csv,
    export_phenology_json,
    import_stages,
    move_stage,
    save_profile,
    save_recommendation,
    save_stage,
    set_stage_active,
    set_stage_critical,
)
from app.phenology_api import (
    get_crop_phenology,
    get_culture_stages,
    get_parcel_phenology,
    get_phenology_calendar,
    get_phenology_history,
    get_stage_detail,
    post_observation,
)
from app.seed import seed_dashboard_data
from app.seed_phenology import seed_phenology_data
from app.states.phenology_admin_state import PhenologyAdminState


async def main():
    print("=== Test administration phénologique AgriPro ===")
    await seed_dashboard_data()
    await seed_phenology_data()

    # --- Administration : profils ----------------------------------------
    cultures = await culture_options()
    assert cultures, "Le référentiel structuré doit exposer des cultures"

    profiles = await admin_profiles()
    assert profiles, "Des profils phénologiques doivent exister"
    for profile in profiles:
        assert profile["source"] != "", "Chaque profil doit porter sa source"

    draft = {
        "key": "phen-test-admin",
        "name": "Cycle de contrôle administration",
        "culture_id": cultures[0]["value"],
        "system": "LOCAL",
        "summary": "Profil créé par le contrôle d'administration.",
        "source": "Contrôle interne AgriPro",
        "is_default": "0",
        "is_active": "1",
    }
    created = await save_profile(draft)
    assert created["ok"] is True, created["errors"]
    profile_id = int(created["profile_id"])

    duplicate = await save_profile(draft)
    assert duplicate["ok"] is False, "Un identifiant dupliqué doit être refusé"

    invalid = await save_profile({**draft, "key": "Phen Test", "source": ""})
    assert invalid["ok"] is False
    assert len(invalid["errors"]) >= 2, invalid["errors"]

    # --- Administration : stades -----------------------------------------
    first = await save_stage(
        profile_id,
        {
            "name": "Germination",
            "bbch_code": "BBCH 00-09",
            "description": "Imbibition puis sortie de la radicelle.",
            "recognition": "Radicelle visible.",
            "duration_days_min": "5",
            "duration_days_max": "12",
            "is_critical": "0",
            "is_active": "1",
            "guide_article_slug": "suivre-les-stades",
        },
    )
    assert first["ok"] is True, first["errors"]
    second = await save_stage(
        profile_id,
        {
            "name": "Levée",
            "duration_days_min": "8",
            "duration_days_max": "18",
            "is_active": "1",
        },
    )
    assert second["ok"] is True, second["errors"]

    bad_duration = await save_stage(
        profile_id,
        {
            "name": "Stade incohérent",
            "duration_days_min": "40",
            "duration_days_max": "10",
        },
    )
    assert bad_duration["ok"] is False, "Durées incohérentes refusées"

    stages = await admin_stages(profile_id)
    assert [s["name"] for s in stages] == ["Germination", "Levée"]
    assert [s["position"] for s in stages] == [1, 2]

    message = await move_stage(int(second["stage_id"]), -1)
    assert message != ""
    stages = await admin_stages(profile_id)
    assert [s["name"] for s in stages] == ["Levée", "Germination"], (
        "Le réordonnancement doit renuméroter le cycle"
    )
    edge = await move_stage(stages[0]["id"], -1)
    assert "extrémité" in edge

    # Désactivation non destructive.
    await set_stage_active(int(first["stage_id"]), False)
    kept = await admin_stages(profile_id)
    assert len(kept) == 2, "Un stade désactivé n'est jamais supprimé"
    assert any(not s["is_active"] for s in kept)
    await set_stage_active(int(first["stage_id"]), True)
    await set_stage_critical(int(first["stage_id"]), True)
    assert any(s["is_critical"] for s in await admin_stages(profile_id))

    # --- Recommandations non prescriptives -------------------------------
    prescriptive = await save_recommendation(
        int(first["stage_id"]),
        {
            "domain": "FERTILISATION",
            "title": "Apporter de l'azote",
            "statement": "Appliquer 120 kg/ha d'azote sur la parcelle entière.",
            "confidence": "INDICATIVE",
            "source": "Contrôle interne",
        },
    )
    assert prescriptive["ok"] is False, (
        "Une dose chiffrée ne peut pas être enregistrée"
    )

    advisory = await save_recommendation(
        int(first["stage_id"]),
        {
            "domain": "SURVEILLANCE",
            "title": "Contrôler la régularité de la levée",
            "statement": (
                "Compter les pieds sur plusieurs placettes pour apprécier le "
                "peuplement réellement implanté."
            ),
            "confidence": "INDICATIVE",
            "source": "Contrôle interne AgriPro",
        },
    )
    assert advisory["ok"] is True, advisory["errors"]
    recos = await admin_recommendations(int(first["stage_id"]))
    assert recos and all(item["is_advisory"] for item in recos)
    assert all(item["source"] != "" for item in recos)

    # --- Import CSV additif ------------------------------------------------
    csv_payload = (
        "key,name,bbch_code,duration_days_min,duration_days_max,is_critical,"
        "description\n"
        "germination,Germination,BBCH 00-09,6,14,1,Description enrichie par import.\n"
        "croissance,Croissance,BBCH 30-39,20,40,0,Élongation des entre-nœuds.\n"
    )
    report = await import_stages(profile_id, csv_payload, "CSV")
    assert report["ok"] is True, report["errors"]
    assert int(report["created"]) == 1, report
    assert int(report["updated"]) == 1, report
    stages = await admin_stages(profile_id)
    assert len(stages) == 3, "L'import est additif, jamais destructif"
    enriched = next(s for s in stages if s["key"] == "germination")
    assert enriched["description"] == "Description enrichie par import."
    assert enriched["guide_article_slug"] == "suivre-les-stades", (
        "Un champ vide de l'import ne doit rien écraser"
    )

    json_payload = json.dumps(
        {
            "stages": [
                {
                    "key": "maturation",
                    "name": "Maturation",
                    "duration_days_min": 10,
                    "duration_days_max": 25,
                    "is_critical": True,
                }
            ]
        }
    )
    report = await import_stages(profile_id, json_payload, "JSON")
    assert report["ok"] is True, report["errors"]
    assert len(await admin_stages(profile_id)) == 4

    broken = await import_stages(profile_id, "{ ceci n'est pas du json", "JSON")
    assert broken["ok"] is False and broken["errors"]

    # --- Export JSON / CSV -------------------------------------------------
    exported = json.loads(await export_phenology_json(profile_id))
    assert exported["advisory_only"] is True
    assert exported["profiles"], exported
    exported_stages = exported["profiles"][0]["stages"]
    assert len(exported_stages) == 4
    csv_export = await export_phenology_csv(profile_id)
    assert "profile_key" in csv_export.splitlines()[0]
    assert "Maturation" in csv_export
    full_export = json.loads(await export_phenology_json(0))
    assert len(full_export["profiles"]) >= len(profiles)

    # --- API internes ------------------------------------------------------
    wheat_stages = await get_culture_stages("Blé dur")
    assert wheat_stages, "Les stades du blé doivent être exposés"
    assert any(s["name"] == "Tallage" for s in wheat_stages)
    assert wheat_stages[-1]["progress"] == 100
    assert not await get_culture_stages("Culture inexistante")

    async with rx.asession() as asession:
        crop_row = (
            await asession.execute(
                text(
                    """
                    SELECT c.id, c.parcel_id FROM crop c
                    JOIN crop_variety v ON v.id = c.variety_id
                    WHERE v.name = 'Rubisko' LIMIT 1
                    """
                )
            )
        ).first()
    assert crop_row is not None
    crop_id = int(crop_row[0])
    parcel_id = int(crop_row[1])

    parcel_phenology = await get_parcel_phenology(parcel_id)
    assert parcel_phenology, "La parcelle doit exposer sa phénologie"
    assert all(row["parcel_id"] == parcel_id for row in parcel_phenology)

    crop_phenology = await get_crop_phenology(crop_id)
    assert crop_phenology is not None
    assert crop_phenology["next_stage"] != ""

    history_before = len(await get_phenology_history(crop_id))
    published = await post_observation(
        crop_id=crop_id,
        stage_label="Tallage",
        observed_on=datetime.date.today(),
        observer="Technicien contrôle",
        comment="Tallage homogène constaté sur cinq placettes.",
    )
    assert published["ok"] is True, published["errors"]
    refused = await post_observation(
        crop_id=crop_id,
        stage_label="Véraison",
        observed_on=datetime.date.today(),
        observer="Technicien contrôle",
    )
    assert refused["ok"] is False, "Un stade étranger au blé doit être refusé"
    history = await get_phenology_history(crop_id)
    assert len(history) == history_before + 1, (
        "L'historique conserve chaque changement et rien n'est purgé"
    )

    calendar = await get_phenology_calendar(crop_id)
    assert calendar, "Le calendrier phénologique doit être calculable"
    assert any(item["observed_label"] != "—" for item in calendar)
    assert all(item["stage_name"] != "" for item in calendar)

    detail = await get_stage_detail(wheat_stages[0]["id"])
    assert detail["found"] is True
    assert detail["culture_name"] != ""
    for reco in detail["recommendations"]:
        assert reco["is_advisory"] is True
        assert reco["source"] != ""
    missing = await get_stage_detail(0)
    assert missing["found"] is False

    # --- État d'administration et validations finales ---------------------
    state = PhenologyAdminState()
    await run_event(state.load_admin)
    assert state.is_loading is False
    assert state.profile_count >= 1
    assert state.stage_count >= 1
    assert state.totals["prescriptive_recommendations"] == 0

    await run_event(state.select_profile, profile_id)
    assert state.selected_profile["key"] == "phen-test-admin"
    assert state.stage_count == 4
    await run_event(state.select_stage, int(first["stage_id"]))
    assert state.stage_preview["name"] != ""
    assert state.recommendations

    await run_event(state.set_export_format, "CSV")
    await run_event(state.run_export)
    assert state.export_payload.contains("profile_key")

    await run_event(state.run_checks)
    assert state.checks, "Les validations finales doivent être exposées"
    by_id = {item["id"]: item for item in state.checks}
    for key in (
        "stage-ble",
        "stage-tomate",
        "stage-olivier",
        "history",
        "advisory",
    ):
        assert by_id.contains(key), by_id.keys()
        assert by_id[key]["ok"] is True, by_id[key]["message"]
    assert state.failed_checks == 0
    assert state.checks_passed is True

    print(
        f"✓ {state.profile_count} profil(s) administrables, {state.stage_count} stade(s) sur le profil de contrôle, import additif (1 créé / 1 enrichi), export JSON+CSV, {len(history)} changement(s) conservé(s), {state.checks.length()} validation(s) conforme(s)"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

"""Vérifie les corrections d'audit : idempotence et baisse des écarts."""

import asyncio

import reflex as rx
from sqlalchemy import text
from test_utils import run_event

from app.audit_reference import STRUCTURAL_DOMAINS
from app.seed import seed_dashboard_data
from app.seed_corrections import (
    PROCEDURES,
    RULE_FIELD_FIXES,
    apply_audit_corrections,
)
from app.seed_guide import seed_guide_data
from app.states.audit_state import AuditState
from app.states.guide_state import GuideState
from app.states.parcels_state import ParcelsState

MISSING_CATEGORIES: list[str] = [
    "fondamentaux",
    "cultures",
    "travaux",
    "irrigation",
    "fertilisation",
    "personnel",
]


async def counts() -> dict[str, int]:
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text(
                    """
                    SELECT
                        (SELECT COUNT(*) FROM guide_procedure),
                        (SELECT COUNT(*) FROM guide_procedure_step),
                        (SELECT COUNT(*) FROM soil_analysis),
                        (SELECT COUNT(*) FROM crop_stage_log),
                        (SELECT COUNT(*) FROM guide_rule
                           WHERE COALESCE(field_reference, '') = '')
                    """
                )
            )
        ).first()
    return {
        "procedures": int(row[0] or 0),
        "steps": int(row[1] or 0),
        "soil": int(row[2] or 0),
        "logs": int(row[3] or 0),
        "orphan_rules": int(row[4] or 0),
    }


async def main():
    print("=== Test corrections d'audit AgriPro ===")
    await seed_dashboard_data()
    await seed_guide_data()

    await apply_audit_corrections()
    first = await counts()

    # --- Idempotence : deux applications ne dupliquent rien ---------------
    import app.seed_corrections as corrections

    corrections._guide_done = False
    corrections._data_done = False
    await apply_audit_corrections()
    second = await counts()
    for key in first:
        assert first[key] == second[key], (
            f"Correction non idempotente sur {key} : {first[key]} → {second[key]}"
        )

    assert first["soil"] > 0, "Des analyses de sol doivent être amorcées"
    assert first["logs"] > 0, "Des journaux de stades doivent être amorcés"
    assert first["orphan_rules"] == 0, (
        "Toute règle publiée doit être rattachée à un champ"
    )

    # --- Couverture éditoriale : plus aucune catégorie sans procédure -----
    guide = GuideState()
    await run_event(guide.load_guide)
    slugs = [item["slug"] for item in guide.procedures]
    for item in PROCEDURES:
        assert slugs.count(item["slug"]) == 1, (
            f"Procédure manquante ou dupliquée : {item['slug']}"
        )
    for key in MISSING_CATEGORIES:
        matched = [p for p in guide.procedures if p["category_key"] == key]
        assert matched.length() > 0, f"Catégorie sans procédure : {key}"

    # Les règles corrigées sont exploitables par l'aide contextuelle.
    codes = [fix["code"] for fix in RULE_FIELD_FIXES]
    for rule in guide.rules:
        if rule["code"] in codes:
            assert rule["field_reference"] != "", (
                f"Règle non rattachée : {rule['code']}"
            )

    # --- Audit : écarts structurels résorbés ------------------------------
    audit = AuditState()
    await run_event(audit.load_audit)
    structural = audit.structural_issues
    for item in structural:
        assert item["domain"] in STRUCTURAL_DOMAINS
    guide_gaps = [item for item in structural if item["domain"] == "guide"]
    assert guide_gaps.length() == 0, (
        f"Écarts éditoriaux restants : {[i['id'] for i in guide_gaps]}"
    )
    liaison = [item for item in structural if item["domain"] == "liaison"]
    assert liaison.length() == 0, (
        "Aucun lien guide → application ne doit être cassé"
    )
    empty_data = [item for item in structural if item["domain"] == "donnees"]
    assert empty_data.length() == 0, (
        f"Sous-entités encore vides : {[i['reference'] for i in empty_data]}"
    )

    # Les alertes et stocks restent visibles, classés « état d'exploitation ».
    operational_refs = [item["id"] for item in audit.operational_issues]
    for item in audit.operational_issues:
        assert item["domain"] == "exploitation"
        assert item["recommendation"] != ""
    assert audit.issue_count == (
        audit.structural_issue_count
        + audit.operational_issue_count
        + [i for i in audit.issues if i["domain"] == "coherence"].length()
    ), "Chaque constat doit appartenir à un domaine connu"

    # --- Modules parcelles / cultures alimentés ---------------------------
    parcels = ParcelsState()
    await run_event(parcels.load_space)
    assert parcels.parcel_count > 0
    assert parcels.stage_logs.length() > 0, (
        "La timeline végétale doit afficher des stades consignés"
    )

    print(
        f"✓ {first['procedures']} procédures ({first['steps']} étapes), {first['soil']} analyses de sol, {first['logs']} stades consignés, {audit.structural_issue_count} écart(s) structurel(s) restant(s), {operational_refs.length()} état(s) d'exploitation à traiter"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

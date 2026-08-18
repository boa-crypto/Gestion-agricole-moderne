"""Vérifie le référentiel Catégorie → Culture → Espèce → Variété.

Contrôles : amorçage idempotent, complétude des familles, catégorie dédiée aux
dattes avec ses cinq variétés exigées, liens avec le référentiel variétal
historique et cohérence des constantes métier.
"""

import asyncio

import reflex as rx
from sqlalchemy import text
from test_utils import run_event

from app.catalog_reference import (
    CATALOG_CATEGORY_KEYS,
    CROSS_CATEGORY_CULTURES,
    CYCLE_KEYS,
    DATE_CATEGORY_KEY,
    DATE_VARIETY_NAMES,
    TOLERANCE_KEYS,
    WATER_KEYS,
    fertilisation_profile,
    irrigation_profile,
)
from app.seed import seed_dashboard_data
from app.seed_catalog import CATALOG, link_legacy_varieties, seed_catalog_data
from app.states.catalog_state import CatalogState

EXPECTED_CATEGORIES: list[str] = CATALOG_CATEGORY_KEYS

# Cultures explicitement exigées par le cahier des charges, repérées par un
# fragment de leur nom (en minuscules) dans la catégorie attendue.
REQUIRED_CULTURES: dict[str, list[str]] = {
    "cereales": [
        "blé",
        "orge",
        "maïs",
        "avoine",
        "triticale",
        "sorgho",
        "riz",
        "seigle",
    ],
    "legumineuses": [
        "pois",
        "féverole",
        "lentille",
        "pois chiche",
        "haricot",
        "soja",
        "fève",
        "lupin",
    ],
    "oleagineux": [
        "colza",
        "tournesol",
        "lin",
        "arachide",
        "sésame",
        "carthame",
        "soja",
        "olivier",
    ],
    "fourrages": [
        "luzerne",
        "trèfle",
        "ray-grass",
        "vesce",
        "sainfoin",
        "dactyle",
        "fétuque",
        "maïs",
    ],
    "maraichage": [
        "tomate",
        "pomme de terre",
        "carotte",
        "oignon",
        "ail",
        "poivron",
        "piment",
        "aubergine",
        "concombre",
        "courgette",
        "courge",
        "citrouille",
        "melon",
        "pastèque",
        "laitue",
        "chou",
        "chou-fleur",
        "brocoli",
        "épinard",
        "artichaut",
        "haricot vert",
        "pois vert",
        "navet",
        "betterave",
        "radis",
        "céleri",
        "fenouil",
        "poireau",
    ],
    "tubercules": ["pomme de terre", "carotte", "patate douce"],
    "dattes": ["palmier dattier"],
    "arboriculture": [
        "olivier",
        "amandier",
        "abricotier",
        "pommier",
        "figuier",
        "poirier",
        "pêcher",
        "cerisier",
        "prunier",
        "grenadier",
        "noyer",
        "pistachier",
        "cognassier",
    ],
    "agrumes": [
        "oranger",
        "clémentinier",
        "citronnier",
        "mandarinier",
        "pomelo",
    ],
    "vigne": ["raisin de table", "raisin de cuve"],
    "industrielles": [
        "betterave sucrière",
        "canne à sucre",
        "coton",
        "tabac",
        "lin textile",
        "chanvre",
    ],
    "aromatiques": [
        "menthe",
        "coriandre",
        "cumin",
        "basilic",
        "romarin",
        "thym",
        "lavande",
        "sauge",
        "origan",
        "camomille",
        "persil",
        "fenouil",
    ],
    "epices": [
        "safran",
        "anis",
        "fenugrec",
        "carvi",
        "nigelle",
        "curcuma",
        "gingembre",
        "coriandre",
        "piment",
    ],
    "tropicales": [
        "bananier",
        "avocatier",
        "manguier",
        "papayer",
        "goyavier",
        "ananas",
        "passion",
        "caféier",
    ],
}

LEGACY_NAMES: list[str] = [
    "Rubisko",
    "Architect",
    "Kilomeris",
    "Planet",
    "ES Bella",
    "Timbale",
    "Agata",
]


async def counts() -> dict[str, int]:
    async with rx.asession() as asession:
        row = (
            await asession.execute(
                text(
                    """
                    SELECT
                        (SELECT COUNT(*) FROM crop_category),
                        (SELECT COUNT(*) FROM crop_culture),
                        (SELECT COUNT(*) FROM crop_species),
                        (SELECT COUNT(*) FROM crop_catalog_variety),
                        (SELECT COUNT(*) FROM crop_catalog_variety
                           WHERE crop_variety_id IS NOT NULL)
                    """
                )
            )
        ).first()
    return {
        "categories": int(row[0] or 0),
        "cultures": int(row[1] or 0),
        "species": int(row[2] or 0),
        "varieties": int(row[3] or 0),
        "linked": int(row[4] or 0),
    }


async def main():
    print("=== Test référentiel cultures AgriPro ===")

    # Le référentiel variétal historique doit exister pour tester les liens.
    await seed_dashboard_data()

    await seed_catalog_data()
    await link_legacy_varieties()
    first = await counts()

    # --- Idempotence : un second amorçage ne duplique rien ---------------
    import app.seed_catalog as catalog_seed

    catalog_seed._seeded = False
    await seed_catalog_data()
    await link_legacy_varieties()
    second = await counts()
    for key in first:
        assert first[key] == second[key], (
            f"Amorçage non idempotent sur {key} : {first[key]} → {second[key]}"
        )

    # --- Complétude structurelle ----------------------------------------
    expected_cultures = sum(len(c["cultures"]) for c in CATALOG)
    expected_species = sum(
        len(s["species"]) for c in CATALOG for s in c["cultures"]
    )
    expected_varieties = sum(
        len(v["varieties"])
        for c in CATALOG
        for cu in c["cultures"]
        for v in cu["species"]
    )
    assert first["categories"] == len(CATALOG), "Catégories incomplètes"
    assert first["cultures"] == expected_cultures, "Cultures incomplètes"
    assert first["species"] == expected_species, "Espèces incomplètes"
    assert first["varieties"] == expected_varieties, "Variétés incomplètes"

    async with rx.asession() as asession:
        keys = [
            str(row[0])
            for row in (
                await asession.execute(text("SELECT key FROM crop_category"))
            ).all()
        ]
        for expected in EXPECTED_CATEGORIES:
            assert expected in keys, f"Catégorie manquante : {expected}"

        # --- Complétude : chaque culture exigée est présente -------------
        culture_rows = (
            await asession.execute(
                text(
                    """
                    SELECT cat.key, cu.key, cu.name,
                           (SELECT COUNT(*) FROM crop_species s
                              WHERE s.culture_id = cu.id),
                           (SELECT COUNT(*) FROM crop_catalog_variety v
                              JOIN crop_species s2 ON s2.id = v.species_id
                              WHERE s2.culture_id = cu.id)
                    FROM crop_culture cu
                    JOIN crop_category cat ON cat.id = cu.category_id
                    ORDER BY cat.position, cu.position
                    """
                )
            )
        ).all()
        assert len(culture_rows) == first["cultures"]
        names_by_category: dict[str, str] = {}
        for row in culture_rows:
            assert int(row[3] or 0) > 0, f"Culture sans espèce : {row[1]}"
            assert int(row[4] or 0) > 0, (
                f"Culture sans variété exploitable : {row[1]}"
            )
            cat_key = str(row[0])
            names_by_category[cat_key] = (
                names_by_category.get(cat_key, "") + " | " + str(row[2]).lower()
            )
        for cat_key, tokens in REQUIRED_CULTURES.items():
            blob = names_by_category.get(cat_key, "")
            for token in tokens:
                assert token in blob, (
                    f"Culture manquante dans « {cat_key} » : {token}"
                )

        # --- Doublons volontaires entre catégories ------------------------
        for token, cat_keys in CROSS_CATEGORY_CULTURES:
            for cat_key in cat_keys:
                blob = names_by_category.get(cat_key, "")
                assert token in blob, (
                    f"Doublon attendu manquant : « {token} » doit aussi "
                    f"exister dans la catégorie « {cat_key} »"
                )

        # --- Catégorie dédiée aux dattes --------------------------------
        date_rows = (
            await asession.execute(
                text(
                    """
                    SELECT v.name, v.quality_grade, v.harvest_window,
                           s.scientific_name, cu.cycle, cu.water_need
                    FROM crop_catalog_variety v
                    JOIN crop_species s ON s.id = v.species_id
                    JOIN crop_culture cu ON cu.id = s.culture_id
                    JOIN crop_category cat ON cat.id = cu.category_id
                    WHERE cat.key = :date_key
                    ORDER BY v.position
                    """
                ),
                {"date_key": DATE_CATEGORY_KEY},
            )
        ).all()
        date_names = [str(row[0]) for row in date_rows]
        for name in DATE_VARIETY_NAMES:
            assert name in date_names, f"Variété de datte manquante : {name}"
        for row in date_rows:
            assert str(row[1]) != "", f"Qualité manquante pour {row[0]}"
            assert str(row[2]) != "", f"Fenêtre de récolte manquante : {row[0]}"
            assert str(row[3]).startswith("Phoenix dactylifera"), (
                "Le palmier dattier doit être rattaché à son espèce botanique"
            )
            assert str(row[4]) == "PERENNE", "Le palmier dattier est pérenne"

        # --- Liens avec le référentiel variétal historique ---------------
        linked = (
            await asession.execute(
                text(
                    """
                    SELECT v.name FROM crop_catalog_variety v
                    JOIN crop_variety l ON l.id = v.crop_variety_id
                    WHERE l.name = v.name
                    """
                )
            )
        ).all()
        linked_names = [str(row[0]) for row in linked]
        for name in LEGACY_NAMES:
            assert name in linked_names, (
                f"Variété non reliée au référentiel historique : {name}"
            )

        # --- Constantes agronomiques exploitables ------------------------
        bad = (
            await asession.execute(
                text(
                    """
                    SELECT COUNT(*) FROM crop_species
                    WHERE COALESCE(cycle_days_max, 0) <= 0
                       OR COALESCE(water_requirement_mm, 0) <= 0
                       OR COALESCE(scientific_name, '') = ''
                       OR COALESCE(sowing_window, '') = ''
                       OR COALESCE(harvest_window, '') = ''
                    """
                )
            )
        ).scalar()
        assert int(bad or 0) == 0, (
            "Chaque espèce doit porter cycle, besoin en eau, nom latin et fenêtres"
        )

        enum_bad = (
            await asession.execute(
                text(
                    """
                    SELECT COUNT(*) FROM crop_culture
                    WHERE cycle NOT IN ('ANNUELLE', 'BISANNUELLE', 'PERENNE')
                       OR water_need NOT IN
                          ('FAIBLE', 'MODEREE', 'ELEVEE', 'TRES_ELEVEE')
                    """
                )
            )
        ).scalar()
        assert int(enum_bad or 0) == 0, (
            "Vocabulaire de cycle / eau non normalisé"
        )

    # --- Constantes métier ------------------------------------------------
    for key in WATER_KEYS:
        profile = irrigation_profile(key)
        assert profile["dose_mm"] > 0
        assert profile["interval_days"] > 0
    for category in EXPECTED_CATEGORIES:
        assert fertilisation_profile(category)["splits"] > 0
    assert len(CYCLE_KEYS) == 3
    assert len(TOLERANCE_KEYS) == 4

    # --- État de chargement ----------------------------------------------
    state = CatalogState()
    await run_event(state.load_catalog)
    assert state.is_loading is False
    assert state.is_ready is True
    assert state.totals["varieties"] == first["varieties"]
    assert state.totals["date_varieties"] >= len(DATE_VARIETY_NAMES)
    assert state.totals["perennial"] > 0

    print(
        f"✓ {first['categories']} catégories, {first['cultures']} cultures, "
        f"{first['species']} espèces, {first['varieties']} variétés dont "
        f"{first['linked']} reliées au référentiel historique et "
        f"{state.totals['date_varieties']} variétés de palmier dattier"
    )
    print("=== Test réussi ===")


if __name__ == "__main__":
    asyncio.run(main())

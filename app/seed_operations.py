"""Amorçage idempotent du volet intrants & stocks.

Insère un référentiel produits, des mouvements de stock et les produits
appliqués sur les interventions existantes UNIQUEMENT si la table `product`
est vide. Toutes les requêtes sont écrites en SQL brut.
"""

from __future__ import annotations

import datetime

import reflex as rx
from sqlalchemy import text

from app.database import init_local_database

PRODUCTS: list[dict[str, str | float | int | bool | datetime.date | None]] = [
    {
        "name": "Solution azotée 39",
        "category": "ENGRAIS",
        "supplier": "Coopérative Beauce Agro",
        "reference": "AZ39-1000",
        "active_substance": "Azote uréique et ammoniacal",
        "unit": "L",
        "unit_price": 0.42,
        "quantity_in_stock": 4200.0,
        "reorder_threshold": 1500.0,
        "storage_location": "Cuve extérieure 1",
        "reentry_delay_hours": 6,
        "preharvest_delay_days": 0,
        "is_organic_approved": False,
        "expiry_date": None,
        "notes": "Cuve principale, jauge relevée chaque semaine.",
    },
    {
        "name": "Ammonitrate 33,5",
        "category": "ENGRAIS",
        "supplier": "Coopérative Beauce Agro",
        "reference": "AMN-335",
        "active_substance": "Nitrate d'ammonium",
        "unit": "kg",
        "unit_price": 0.38,
        "quantity_in_stock": 620.0,
        "reorder_threshold": 800.0,
        "storage_location": "Hangar A - palettier 2",
        "reentry_delay_hours": 0,
        "preharvest_delay_days": 0,
        "is_organic_approved": False,
        "expiry_date": None,
        "notes": "Stock bas avant la prochaine campagne d'apports.",
    },
    {
        "name": "Fongicide céréales Prosalis",
        "category": "FONGICIDE",
        "supplier": "AgroDistrib Centre",
        "reference": "PRS-5L",
        "active_substance": "Prothioconazole + tébuconazole",
        "unit": "L",
        "unit_price": 46.5,
        "quantity_in_stock": 38.0,
        "reorder_threshold": 20.0,
        "storage_location": "Local phyto - étagère 1",
        "reentry_delay_hours": 48,
        "preharvest_delay_days": 35,
        "is_organic_approved": False,
        "expiry_date": datetime.date.today() + datetime.timedelta(days=420),
        "notes": "Protection épis blé, respecter la ZNT de 5 m.",
    },
    {
        "name": "Anti-mildiou Cupralis",
        "category": "FONGICIDE",
        "supplier": "BioIntrants Loire",
        "reference": "CUP-10K",
        "active_substance": "Hydroxyde de cuivre",
        "unit": "kg",
        "unit_price": 12.9,
        "quantity_in_stock": 14.0,
        "reorder_threshold": 25.0,
        "storage_location": "Local phyto - étagère 2",
        "reentry_delay_hours": 24,
        "preharvest_delay_days": 21,
        "is_organic_approved": True,
        "expiry_date": datetime.date.today() + datetime.timedelta(days=300),
        "notes": "Homologué AB, dose cuivre métal plafonnée à 4 kg/ha/an.",
    },
    {
        "name": "Herbicide maïs Adenzo",
        "category": "HERBICIDE",
        "supplier": "AgroDistrib Centre",
        "reference": "ADZ-5L",
        "active_substance": "Thiencarbazone + isoxaflutole",
        "unit": "L",
        "unit_price": 68.0,
        "quantity_in_stock": 22.0,
        "reorder_threshold": 10.0,
        "storage_location": "Local phyto - étagère 3",
        "reentry_delay_hours": 24,
        "preharvest_delay_days": 60,
        "is_organic_approved": False,
        "expiry_date": datetime.date.today() + datetime.timedelta(days=520),
        "notes": "Post-levée précoce, hygrométrie supérieure à 70 %.",
    },
    {
        "name": "Insecticide Karatex",
        "category": "INSECTICIDE",
        "supplier": "AgroDistrib Centre",
        "reference": "KTX-1L",
        "active_substance": "Lambda-cyhalothrine",
        "unit": "L",
        "unit_price": 82.0,
        "quantity_in_stock": 3.5,
        "reorder_threshold": 6.0,
        "storage_location": "Local phyto - armoire sécurisée",
        "reentry_delay_hours": 48,
        "preharvest_delay_days": 30,
        "is_organic_approved": False,
        "expiry_date": datetime.date.today() + datetime.timedelta(days=180),
        "notes": "Interdit en floraison, surveiller les auxiliaires.",
    },
    {
        "name": "Semence blé Rubisko",
        "category": "SEMENCE",
        "supplier": "Semences du Perche",
        "reference": "SEM-RBK",
        "active_substance": "—",
        "unit": "kg",
        "unit_price": 0.85,
        "quantity_in_stock": 5400.0,
        "reorder_threshold": 1200.0,
        "storage_location": "Hangar B - big bags",
        "reentry_delay_hours": 0,
        "preharvest_delay_days": 0,
        "is_organic_approved": False,
        "expiry_date": None,
        "notes": "Lot certifié, PMG 46 g.",
    },
    {
        "name": "Chaux magnésienne",
        "category": "AMENDEMENT",
        "supplier": "Carrières de la Conie",
        "reference": "CHX-MG",
        "active_substance": "Carbonate de calcium et magnésium",
        "unit": "t",
        "unit_price": 74.0,
        "quantity_in_stock": 6.0,
        "reorder_threshold": 8.0,
        "storage_location": "Plateforme extérieure",
        "reentry_delay_hours": 0,
        "preharvest_delay_days": 0,
        "is_organic_approved": True,
        "expiry_date": None,
        "notes": "Chantier de chaulage prévu après récolte.",
    },
    {
        "name": "Biostimulant Algalys",
        "category": "BIOSTIMULANT",
        "supplier": "BioIntrants Loire",
        "reference": "ALG-20L",
        "active_substance": "Extrait d'algues Ascophyllum",
        "unit": "L",
        "unit_price": 9.4,
        "quantity_in_stock": 96.0,
        "reorder_threshold": 30.0,
        "storage_location": "Local phyto - étagère 4",
        "reentry_delay_hours": 0,
        "preharvest_delay_days": 0,
        "is_organic_approved": True,
        "expiry_date": datetime.date.today() + datetime.timedelta(days=610),
        "notes": "Associable aux passages fongicides.",
    },
]


async def seed_operations_data() -> None:
    """Insère le référentiel intrants si la table produit est vide."""
    init_local_database()
    async with rx.asession() as asession:
        existing = await asession.execute(text("SELECT COUNT(*) FROM product"))
        if int(existing.scalar() or 0) > 0:
            return

        await asession.execute(
            text(
                """
                INSERT INTO product (
                    name, category, supplier, reference, active_substance, unit,
                    unit_price, quantity_in_stock, reorder_threshold,
                    storage_location, reentry_delay_hours, preharvest_delay_days,
                    is_organic_approved, expiry_date, notes
                ) VALUES (
                    :name, :category, :supplier, :reference, :active_substance, :unit,
                    :unit_price, :quantity_in_stock, :reorder_threshold,
                    :storage_location, :reentry_delay_hours, :preharvest_delay_days,
                    :is_organic_approved, :expiry_date, :notes
                )
                """
            ),
            PRODUCTS,
        )

        product_rows = (
            await asession.execute(text("SELECT id, name, unit FROM product"))
        ).all()
        product_ids = {str(row[1]): int(row[0]) for row in product_rows}
        product_units = {str(row[1]): str(row[2]) for row in product_rows}

        today = datetime.date.today()
        movements = [
            {
                "product_id": product_ids["Solution azotée 39"],
                "type": "ENTREE",
                "quantity": 6000.0,
                "unit_price": 0.42,
                "movement_date": today - datetime.timedelta(days=48),
                "reference": "BL-2291",
                "notes": "Livraison cuve, jauge contrôlée.",
            },
            {
                "product_id": product_ids["Solution azotée 39"],
                "type": "SORTIE",
                "quantity": 1800.0,
                "unit_price": 0.42,
                "movement_date": today - datetime.timedelta(days=12),
                "reference": "APP-N3",
                "notes": "Troisième apport azoté sur blé.",
            },
            {
                "product_id": product_ids["Ammonitrate 33,5"],
                "type": "SORTIE",
                "quantity": 980.0,
                "unit_price": 0.38,
                "movement_date": today - datetime.timedelta(days=20),
                "reference": "APP-MAIS",
                "notes": "Apport de couverture maïs.",
            },
            {
                "product_id": product_ids["Anti-mildiou Cupralis"],
                "type": "SORTIE",
                "quantity": 11.0,
                "unit_price": 12.9,
                "movement_date": today - datetime.timedelta(days=7),
                "reference": "PROT-PDT-2",
                "notes": "Deuxième passage pomme de terre.",
            },
            {
                "product_id": product_ids["Fongicide céréales Prosalis"],
                "type": "ENTREE",
                "quantity": 50.0,
                "unit_price": 46.5,
                "movement_date": today - datetime.timedelta(days=35),
                "reference": "BL-2304",
                "notes": "Approvisionnement campagne céréales.",
            },
            {
                "product_id": product_ids["Insecticide Karatex"],
                "type": "PERTE",
                "quantity": 0.5,
                "unit_price": 82.0,
                "movement_date": today - datetime.timedelta(days=15),
                "reference": "INC-04",
                "notes": "Bidon percé lors de la manutention.",
            },
            {
                "product_id": product_ids["Biostimulant Algalys"],
                "type": "INVENTAIRE",
                "quantity": 96.0,
                "unit_price": 9.4,
                "movement_date": today - datetime.timedelta(days=3),
                "reference": "INV-T2",
                "notes": "Inventaire trimestriel du local phyto.",
            },
        ]
        for movement in movements:
            movement.setdefault("intervention_id", None)

        await asession.execute(
            text(
                """
                INSERT INTO stock_movement (
                    product_id, type, quantity, unit_price, movement_date,
                    reference, intervention_id, notes
                ) VALUES (
                    :product_id, :type, :quantity, :unit_price, :movement_date,
                    :reference, :intervention_id, :notes
                )
                """
            ),
            movements,
        )

        intervention_rows = (
            await asession.execute(
                text(
                    "SELECT id, title, COALESCE(area_treated_ha, 0) FROM intervention"
                )
            )
        ).all()
        intervention_by_title = {
            str(row[1]): (int(row[0]), float(row[2] or 0))
            for row in intervention_rows
        }

        planned_applications = [
            (
                "Protection mildiou - relais fongicide",
                "Anti-mildiou Cupralis",
                1.5,
            ),
            ("Troisième apport azoté", "Solution azotée 39", 42.0),
            ("Désherbage de post-levée", "Herbicide maïs Adenzo", 0.5),
            ("Notation sanitaire épis", "Biostimulant Algalys", 0.0),
        ]
        applications: list[dict[str, str | float | int]] = []
        for title, product_name, dose in planned_applications:
            if title not in intervention_by_title or dose <= 0:
                continue
            intervention_id, area = intervention_by_title[title]
            unit = product_units[product_name]
            total = round(dose * area, 3)
            applications.append(
                {
                    "intervention_id": intervention_id,
                    "product_id": product_ids[product_name],
                    "dose_per_ha": dose,
                    "total_quantity": total,
                    "unit": unit,
                    "cost": round(total * 1.0, 2),
                    "notes": f"{dose} {unit}/ha appliqué sur {area:.1f} ha.",
                }
            )

        if applications:
            await asession.execute(
                text(
                    """
                    INSERT INTO intervention_product (
                        intervention_id, product_id, dose_per_ha, total_quantity,
                        unit, cost, notes
                    ) VALUES (
                        :intervention_id, :product_id, :dose_per_ha, :total_quantity,
                        :unit, :cost, :notes
                    )
                    """
                ),
                applications,
            )

        await asession.commit()

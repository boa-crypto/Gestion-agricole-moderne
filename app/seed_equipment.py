"""Amorçage idempotent de la flotte d'engins et de sa maintenance.

Insère engins, plans d'entretien préventif, opérations de maintenance,
lignes de coût et relevés d'usage UNIQUEMENT si la table `equipment` est vide.
Toutes les requêtes sont écrites en SQL brut.
"""

from __future__ import annotations

import datetime

import reflex as rx
from sqlalchemy import text

from app.database import init_local_database
from app.date_utils import as_date

# (code, nom, catégorie, statut, propriété, marque, modèle, année, puissance,
#  largeur, unité, compteur, prix achat, coût horaire, conso, resp. code,
#  assurance (j), contrôle (j), prochain entretien (j), intervalle j, intervalle compteur)
EQUIPMENTS: list[dict[str, str | float | int]] = [
    {
        "code": "M01",
        "name": "Tracteur de tête John Deere 6155R",
        "category": "TRACTEUR",
        "status": "EN_SERVICE",
        "ownership": "PROPRIETE",
        "brand": "John Deere",
        "model": "6155R",
        "serial_number": "JD6155R-88421",
        "registration": "AE-441-KL",
        "year": 2019,
        "power_hp": 155.0,
        "working_width_m": 0.0,
        "usage_unit": "HEURES",
        "usage_counter": 4820.0,
        "purchase_price": 128000.0,
        "residual_value": 62000.0,
        "hourly_cost": 34.5,
        "fuel_consumption_l_h": 17.5,
        "storage_location": "Hangar A - travée 1",
        "responsible": "E02",
        "insurance_offset": 128,
        "inspection_offset": 210,
        "service_offset": 12,
        "service_interval_days": 180,
        "service_interval_counter": 500.0,
        "notes": "Engin polyvalent, attelage avant, GPS RTK.",
    },
    {
        "code": "M02",
        "name": "Tracteur New Holland T5.120",
        "category": "TRACTEUR",
        "status": "DISPONIBLE",
        "ownership": "LEASING",
        "brand": "New Holland",
        "model": "T5.120",
        "serial_number": "NHT5-20194",
        "registration": "BQ-902-TR",
        "year": 2021,
        "power_hp": 117.0,
        "working_width_m": 0.0,
        "usage_unit": "HEURES",
        "usage_counter": 2140.0,
        "purchase_price": 82000.0,
        "residual_value": 51000.0,
        "hourly_cost": 27.0,
        "fuel_consumption_l_h": 12.4,
        "storage_location": "Hangar A - travée 2",
        "responsible": "E04",
        "insurance_offset": 24,
        "inspection_offset": 95,
        "service_offset": 46,
        "service_interval_days": 180,
        "service_interval_counter": 400.0,
        "notes": "Leasing 5 ans, restitution prévue en 2027.",
    },
    {
        "code": "M03",
        "name": "Pulvérisateur porté Berthoud 1200 L",
        "category": "PULVERISATEUR",
        "status": "EN_MAINTENANCE",
        "ownership": "PROPRIETE",
        "brand": "Berthoud",
        "model": "Elyte 1200",
        "serial_number": "BTH-1200-5512",
        "registration": "",
        "year": 2018,
        "power_hp": 0.0,
        "working_width_m": 18.0,
        "usage_unit": "HECTARES",
        "usage_counter": 9640.0,
        "purchase_price": 34000.0,
        "residual_value": 12500.0,
        "hourly_cost": 11.0,
        "fuel_consumption_l_h": 0.0,
        "storage_location": "Local phyto - aire de remplissage",
        "responsible": "E05",
        "insurance_offset": 300,
        "inspection_offset": -8,
        "service_offset": -3,
        "service_interval_days": 365,
        "service_interval_counter": 2500.0,
        "notes": "Contrôle pulvé obligatoire dépassé, buses à remplacer.",
    },
    {
        "code": "M04",
        "name": "Moissonneuse Claas Lexion 6800",
        "category": "MOISSONNEUSE",
        "status": "DISPONIBLE",
        "ownership": "COPROPRIETE",
        "brand": "Claas",
        "model": "Lexion 6800",
        "serial_number": "CLX6800-3390",
        "registration": "CF-118-MO",
        "year": 2017,
        "power_hp": 400.0,
        "working_width_m": 7.5,
        "usage_unit": "HEURES",
        "usage_counter": 1980.0,
        "purchase_price": 265000.0,
        "residual_value": 145000.0,
        "hourly_cost": 118.0,
        "fuel_consumption_l_h": 42.0,
        "storage_location": "Hangar C",
        "responsible": "E05",
        "insurance_offset": 61,
        "inspection_offset": 400,
        "service_offset": 21,
        "service_interval_days": 365,
        "service_interval_counter": 300.0,
        "notes": "Copropriété avec le GAEC des Fontaines, révision avant moisson.",
    },
    {
        "code": "M05",
        "name": "Semoir monograine Monosem NG Plus 6 rangs",
        "category": "SEMOIR",
        "status": "DISPONIBLE",
        "ownership": "PROPRIETE",
        "brand": "Monosem",
        "model": "NG Plus 6",
        "serial_number": "MNS-NG6-7741",
        "registration": "",
        "year": 2016,
        "power_hp": 0.0,
        "working_width_m": 4.5,
        "usage_unit": "HECTARES",
        "usage_counter": 3260.0,
        "purchase_price": 28500.0,
        "residual_value": 9800.0,
        "hourly_cost": 8.5,
        "fuel_consumption_l_h": 0.0,
        "storage_location": "Hangar B - travée 3",
        "responsible": "E02",
        "insurance_offset": 210,
        "inspection_offset": 0,
        "service_offset": 5,
        "service_interval_days": 240,
        "service_interval_counter": 600.0,
        "notes": "Disques de semis à contrôler avant campagne tournesol.",
    },
    {
        "code": "M06",
        "name": "Chargeur télescopique Manitou MLT 635",
        "category": "MANUTENTION",
        "status": "EN_SERVICE",
        "ownership": "PROPRIETE",
        "brand": "Manitou",
        "model": "MLT 635-130",
        "serial_number": "MLT635-2298",
        "registration": "DH-773-PZ",
        "year": 2020,
        "power_hp": 130.0,
        "working_width_m": 0.0,
        "usage_unit": "HEURES",
        "usage_counter": 3410.0,
        "purchase_price": 74000.0,
        "residual_value": 44000.0,
        "hourly_cost": 29.0,
        "fuel_consumption_l_h": 9.8,
        "storage_location": "Cour de ferme",
        "responsible": "E05",
        "insurance_offset": 15,
        "inspection_offset": 34,
        "service_offset": -1,
        "service_interval_days": 120,
        "service_interval_counter": 250.0,
        "notes": "VGP annuelle obligatoire, fourches et godet grain.",
    },
    {
        "code": "M07",
        "name": "Enrouleur d'irrigation Irrifrance Optima",
        "category": "IRRIGATION",
        "status": "RESERVE",
        "ownership": "PROPRIETE",
        "brand": "Irrifrance",
        "model": "Optima 3000",
        "serial_number": "IRF-OPT-1180",
        "registration": "",
        "year": 2015,
        "power_hp": 0.0,
        "working_width_m": 0.0,
        "usage_unit": "HEURES",
        "usage_counter": 5290.0,
        "purchase_price": 41000.0,
        "residual_value": 11000.0,
        "hourly_cost": 6.5,
        "fuel_consumption_l_h": 0.0,
        "storage_location": "Prairie du Moulin",
        "responsible": "E03",
        "insurance_offset": 175,
        "inspection_offset": 0,
        "service_offset": 30,
        "service_interval_days": 200,
        "service_interval_counter": 800.0,
        "notes": "Réservé aux tours d'eau de la Prairie du Moulin.",
    },
    {
        "code": "M08",
        "name": "Herse rotative Kuhn HR 4004",
        "category": "OUTIL_TRAVAIL_SOL",
        "status": "HORS_SERVICE",
        "ownership": "PROPRIETE",
        "brand": "Kuhn",
        "model": "HR 4004 D",
        "serial_number": "KHN-HR4-9932",
        "registration": "",
        "year": 2014,
        "power_hp": 0.0,
        "working_width_m": 4.0,
        "usage_unit": "HECTARES",
        "usage_counter": 7120.0,
        "purchase_price": 22000.0,
        "residual_value": 5400.0,
        "hourly_cost": 7.0,
        "fuel_consumption_l_h": 0.0,
        "storage_location": "Hangar B - travée 5",
        "responsible": "E05",
        "insurance_offset": 240,
        "inspection_offset": 0,
        "service_offset": -14,
        "service_interval_days": 300,
        "service_interval_counter": 1200.0,
        "notes": "Boîtier d'entraînement en panne, immobilisée à l'atelier.",
    },
]

# (code engin, titre, nature, base, intervalle j, intervalle compteur,
#  dernier fait (j), prochain dû (j), coût estimé, heures, resp.)
SCHEDULES: list[
    tuple[str, str, str, str, int, float, int, int, float, float, str]
] = [
    (
        "M01",
        "Vidange moteur et filtres 500 h",
        "PREVENTIVE",
        "MIXTE",
        180,
        500.0,
        168,
        12,
        620.0,
        4.0,
        "E05",
    ),
    (
        "M01",
        "Contrôle réglementaire freinage et attelage",
        "REGLEMENTAIRE",
        "CALENDRIER",
        365,
        0.0,
        155,
        210,
        280.0,
        2.5,
        "E05",
    ),
    (
        "M02",
        "Entretien 400 h transmission",
        "PREVENTIVE",
        "COMPTEUR",
        180,
        400.0,
        134,
        46,
        480.0,
        3.5,
        "E05",
    ),
    (
        "M03",
        "Contrôle pulvérisateur obligatoire",
        "REGLEMENTAIRE",
        "CALENDRIER",
        1095,
        0.0,
        1103,
        -8,
        195.0,
        2.0,
        "E01",
    ),
    (
        "M03",
        "Rinçage circuit et jeu de buses",
        "PREVENTIVE",
        "CALENDRIER",
        90,
        0.0,
        93,
        -3,
        340.0,
        3.0,
        "E05",
    ),
    (
        "M04",
        "Grande révision avant moisson",
        "PREVENTIVE",
        "MIXTE",
        365,
        300.0,
        344,
        21,
        2450.0,
        14.0,
        "E05",
    ),
    (
        "M05",
        "Contrôle disques et distribution",
        "PREVENTIVE",
        "CALENDRIER",
        240,
        0.0,
        235,
        5,
        260.0,
        2.5,
        "E02",
    ),
    (
        "M06",
        "VGP chargeur télescopique",
        "REGLEMENTAIRE",
        "CALENDRIER",
        365,
        0.0,
        366,
        -1,
        410.0,
        3.0,
        "E05",
    ),
    (
        "M07",
        "Graissage enrouleur et contrôle turbine",
        "PREVENTIVE",
        "CALENDRIER",
        200,
        800.0,
        170,
        30,
        180.0,
        2.0,
        "E03",
    ),
    (
        "M08",
        "Contrôle boîtier et cardan",
        "CORRECTIVE",
        "CALENDRIER",
        300,
        0.0,
        314,
        -14,
        1250.0,
        8.0,
        "E05",
    ),
]

# (code engin, titre plan ou "", titre, nature, statut, priorité,
#  prévue (j), échéance (j), faite (j) ou None, compteur, immobilisation,
#  heures MO, coût MO, pièces, externe, interne, prestataire, resp., panne, travaux)
OPERATIONS: list[tuple] = [
    (
        "M03",
        "Contrôle pulvérisateur obligatoire",
        "Contrôle pulvé périodique en retard",
        "REGLEMENTAIRE",
        "PLANIFIEE",
        "URGENTE",
        1,
        -8,
        None,
        9640.0,
        4.0,
        2.0,
        0.0,
        0.0,
        195.0,
        False,
        "GIP Pulvé Centre",
        "E01",
        "Contrôle périodique dépassé de 8 jours.",
        "",
    ),
    (
        "M06",
        "VGP chargeur télescopique",
        "Vérification générale périodique chargeur",
        "REGLEMENTAIRE",
        "PLANIFIEE",
        "HAUTE",
        2,
        -1,
        None,
        3410.0,
        3.0,
        3.0,
        0.0,
        0.0,
        410.0,
        False,
        "Apave",
        "E05",
        "VGP annuelle échue.",
        "",
    ),
    (
        "M08",
        "Contrôle boîtier et cardan",
        "Remplacement boîtier d'entraînement",
        "CORRECTIVE",
        "EN_COURS",
        "URGENTE",
        -6,
        -14,
        None,
        7120.0,
        48.0,
        9.0,
        225.0,
        980.0,
        0.0,
        True,
        "",
        "E05",
        "Bruit anormal puis blocage du boîtier central.",
        "Dépose du boîtier, pièces commandées.",
    ),
    (
        "M01",
        "Vidange moteur et filtres 500 h",
        "Vidange 5000 h et filtration",
        "PREVENTIVE",
        "PLANIFIEE",
        "NORMALE",
        12,
        12,
        None,
        4820.0,
        5.0,
        4.0,
        100.0,
        390.0,
        0.0,
        True,
        "",
        "E05",
        "",
        "",
    ),
    (
        "M04",
        "Grande révision avant moisson",
        "Révision complète avant moisson",
        "PREVENTIVE",
        "PLANIFIEE",
        "HAUTE",
        21,
        21,
        None,
        1980.0,
        16.0,
        14.0,
        350.0,
        1450.0,
        650.0,
        False,
        "Claas Service Beauce",
        "E05",
        "",
        "",
    ),
    (
        "M02",
        "Entretien 400 h transmission",
        "Entretien 2000 h transmission",
        "PREVENTIVE",
        "REALISEE",
        "NORMALE",
        -34,
        -34,
        -34,
        2100.0,
        6.0,
        3.5,
        87.5,
        302.0,
        0.0,
        True,
        "",
        "E05",
        "",
        "Vidange transmission, filtres hydrauliques remplacés.",
    ),
    (
        "M01",
        "",
        "Réparation flexible hydraulique arrière",
        "CORRECTIVE",
        "REALISEE",
        "HAUTE",
        -18,
        -18,
        -18,
        4705.0,
        7.0,
        2.0,
        50.0,
        148.0,
        0.0,
        True,
        "",
        "E05",
        "Fuite d'huile sur le distributeur arrière.",
        "Flexible et raccord remplacés, mise à niveau huile.",
    ),
    (
        "M07",
        "Graissage enrouleur et contrôle turbine",
        "Graissage et contrôle turbine",
        "PREVENTIVE",
        "REALISEE",
        "BASSE",
        -30,
        -30,
        -29,
        5240.0,
        2.0,
        2.0,
        43.0,
        26.0,
        0.0,
        True,
        "",
        "E03",
        "",
        "Graissage complet, joints de turbine vérifiés.",
    ),
    (
        "M05",
        "",
        "Remplacement socs et disques ouvreurs",
        "CORRECTIVE",
        "REPORTEE",
        "NORMALE",
        18,
        5,
        None,
        3260.0,
        4.0,
        4.0,
        92.0,
        410.0,
        0.0,
        True,
        "",
        "E02",
        "Usure marquée des disques ouvreurs.",
        "",
    ),
]

# (code engin, titre opération, type coût, libellé, référence, fournisseur,
#  quantité, unité, prix unitaire, jours)
COSTS: list[tuple[str, str, str, str, str, str, float, str, float, int]] = [
    (
        "M02",
        "Entretien 2000 h transmission",
        "CONSOMMABLE",
        "Huile transmission 20 L",
        "HT-20L",
        "AgriParts Centre",
        1.0,
        "bidon",
        182.0,
        -34,
    ),
    (
        "M02",
        "Entretien 2000 h transmission",
        "PIECE",
        "Filtres hydrauliques",
        "FH-2214",
        "AgriParts Centre",
        2.0,
        "u",
        60.0,
        -34,
    ),
    (
        "M02",
        "Entretien 2000 h transmission",
        "MAIN_OEUVRE",
        "Main d'œuvre atelier",
        "MO-ATL",
        "Atelier interne",
        3.5,
        "h",
        25.0,
        -34,
    ),
    (
        "M01",
        "Réparation flexible hydraulique arrière",
        "PIECE",
        "Flexible hydraulique 3/8",
        "FLX-38",
        "AgriParts Centre",
        1.0,
        "u",
        98.0,
        -18,
    ),
    (
        "M01",
        "Réparation flexible hydraulique arrière",
        "PIECE",
        "Raccord et joints",
        "RCJ-14",
        "AgriParts Centre",
        2.0,
        "u",
        25.0,
        -18,
    ),
    (
        "M01",
        "Réparation flexible hydraulique arrière",
        "MAIN_OEUVRE",
        "Main d'œuvre atelier",
        "MO-ATL",
        "Atelier interne",
        2.0,
        "h",
        25.0,
        -18,
    ),
    (
        "M08",
        "Remplacement boîtier d'entraînement",
        "PIECE",
        "Boîtier d'entraînement central",
        "BTE-HR4",
        "Kuhn Service",
        1.0,
        "u",
        860.0,
        -4,
    ),
    (
        "M08",
        "Remplacement boîtier d'entraînement",
        "TRANSPORT",
        "Transport pièce express",
        "TR-EXP",
        "Kuhn Service",
        1.0,
        "u",
        120.0,
        -4,
    ),
    (
        "M07",
        "Graissage et contrôle turbine",
        "CONSOMMABLE",
        "Graisse haute pression",
        "GR-HP",
        "AgriParts Centre",
        2.0,
        "cartouche",
        13.0,
        -29,
    ),
]

# (code engin, code employé, jours, compteur début, compteur fin, carburant)
USAGE: list[tuple[str, str, int, float, float, float]] = [
    ("M01", "E02", -1, 4802.0, 4820.0, 296.0),
    ("M01", "E02", -4, 4788.0, 4802.0, 231.0),
    ("M02", "E04", -2, 2131.0, 2140.0, 108.0),
    ("M04", "E05", -12, 1972.0, 1980.0, 322.0),
    ("M06", "E05", -1, 3402.0, 3410.0, 74.0),
    ("M03", "E01", -7, 9630.0, 9640.0, 0.0),
    ("M07", "E03", -3, 5284.0, 5290.0, 0.0),
]


async def seed_equipment_data() -> None:
    """Insère la flotte et sa maintenance si la table engin est vide."""
    init_local_database()
    async with rx.asession() as asession:
        existing = await asession.execute(
            text("SELECT COUNT(*) FROM equipment")
        )
        if int(existing.scalar() or 0) > 0:
            return

        today = datetime.date.today()
        employee_rows = (
            await asession.execute(
                text("SELECT id, employee_code FROM employee")
            )
        ).all()
        employees = {str(row[1]): int(row[0]) for row in employee_rows}

        equipment_params: list[dict] = []
        for item in EQUIPMENTS:
            service_offset = int(item["service_offset"])
            equipment_params.append(
                {
                    "name": item["name"],
                    "code": item["code"],
                    "category": item["category"],
                    "status": item["status"],
                    "ownership": item["ownership"],
                    "brand": item["brand"],
                    "model": item["model"],
                    "serial_number": item["serial_number"],
                    "registration": item["registration"],
                    "year": item["year"],
                    "power_hp": item["power_hp"],
                    "working_width_m": item["working_width_m"],
                    "usage_unit": item["usage_unit"],
                    "usage_counter": item["usage_counter"],
                    "purchase_date": today
                    - datetime.timedelta(
                        days=(today.year - int(item["year"])) * 365
                    ),
                    "purchase_price": item["purchase_price"],
                    "residual_value": item["residual_value"],
                    "hourly_cost": item["hourly_cost"],
                    "fuel_consumption_l_h": item["fuel_consumption_l_h"],
                    "storage_location": item["storage_location"],
                    "responsible_id": employees.get(item["responsible"]),
                    "insurance_expiry": today
                    + datetime.timedelta(days=int(item["insurance_offset"])),
                    "inspection_expiry": (
                        today
                        + datetime.timedelta(
                            days=int(item["inspection_offset"])
                        )
                        if int(item["inspection_offset"]) != 0
                        else None
                    ),
                    "next_service_date": today
                    + datetime.timedelta(days=service_offset),
                    "next_service_counter": float(item["usage_counter"])
                    + float(item["service_interval_counter"]) * 0.2,
                    "service_interval_days": item["service_interval_days"],
                    "service_interval_counter": item[
                        "service_interval_counter"
                    ],
                    "notes": item["notes"],
                }
            )

        await asession.execute(
            text(
                """
                INSERT INTO equipment (
                    name, code, category, status, ownership, brand, model,
                    serial_number, registration, year, power_hp, working_width_m,
                    usage_unit, usage_counter, purchase_date, purchase_price,
                    residual_value, hourly_cost, fuel_consumption_l_h,
                    storage_location, responsible_id, insurance_expiry,
                    inspection_expiry, next_service_date, next_service_counter,
                    service_interval_days, service_interval_counter, notes
                ) VALUES (
                    :name, :code, :category, :status, :ownership, :brand, :model,
                    :serial_number, :registration, :year, :power_hp, :working_width_m,
                    :usage_unit, :usage_counter, :purchase_date, :purchase_price,
                    :residual_value, :hourly_cost, :fuel_consumption_l_h,
                    :storage_location, :responsible_id, :insurance_expiry,
                    :inspection_expiry, :next_service_date, :next_service_counter,
                    :service_interval_days, :service_interval_counter, :notes
                )
                """
            ),
            equipment_params,
        )

        equipment_rows = (
            await asession.execute(
                text(
                    "SELECT id, code, COALESCE(usage_counter, 0) FROM equipment"
                )
            )
        ).all()
        equipment_ids = {str(row[1]): int(row[0]) for row in equipment_rows}
        counters = {str(row[1]): float(row[2] or 0) for row in equipment_rows}

        schedule_params: list[dict] = []
        for (
            code,
            title,
            kind,
            basis,
            interval_days,
            interval_counter,
            last_offset,
            next_offset,
            cost,
            hours,
            responsible,
        ) in SCHEDULES:
            if code not in equipment_ids:
                continue
            counter = counters.get(code, 0.0)
            schedule_params.append(
                {
                    "equipment_id": equipment_ids[code],
                    "title": title,
                    "kind": kind,
                    "trigger_basis": basis,
                    "interval_days": interval_days,
                    "interval_counter": interval_counter,
                    "tolerance_days": 7,
                    "last_done_on": today
                    - datetime.timedelta(days=last_offset),
                    "last_done_counter": max(counter - interval_counter, 0.0),
                    "next_due_on": today + datetime.timedelta(days=next_offset),
                    "next_due_counter": counter + interval_counter * 0.15,
                    "estimated_cost": cost,
                    "estimated_hours": hours,
                    "responsible_id": employees.get(responsible),
                    "is_active": True,
                    "checklist": "Contrôle visuel · niveaux · serrages · essai de fonctionnement",
                    "notes": "",
                }
            )

        await asession.execute(
            text(
                """
                INSERT INTO maintenance_schedule (
                    equipment_id, title, kind, trigger_basis, interval_days,
                    interval_counter, tolerance_days, last_done_on,
                    last_done_counter, next_due_on, next_due_counter,
                    estimated_cost, estimated_hours, responsible_id, is_active,
                    checklist, notes
                ) VALUES (
                    :equipment_id, :title, :kind, :trigger_basis, :interval_days,
                    :interval_counter, :tolerance_days, :last_done_on,
                    :last_done_counter, :next_due_on, :next_due_counter,
                    :estimated_cost, :estimated_hours, :responsible_id, :is_active,
                    :checklist, :notes
                )
                """
            ),
            schedule_params,
        )

        schedule_rows = (
            await asession.execute(
                text("SELECT id, equipment_id, title FROM maintenance_schedule")
            )
        ).all()
        schedules = {
            (int(row[1]), str(row[2])): int(row[0]) for row in schedule_rows
        }

        operation_params: list[dict] = []
        for item in OPERATIONS:
            (
                code,
                schedule_title,
                title,
                kind,
                status,
                priority,
                scheduled,
                due,
                done,
                counter,
                downtime,
                labor_hours,
                labor_cost,
                parts_cost,
                external_cost,
                is_internal,
                provider,
                responsible,
                failure,
                work,
            ) = item
            if code not in equipment_ids:
                continue
            equipment_id = equipment_ids[code]
            operation_params.append(
                {
                    "equipment_id": equipment_id,
                    "schedule_id": schedules.get(
                        (equipment_id, schedule_title)
                    ),
                    "title": title,
                    "kind": kind,
                    "status": status,
                    "priority": priority,
                    "scheduled_date": today
                    + datetime.timedelta(days=scheduled),
                    "due_date": today + datetime.timedelta(days=due),
                    "done_date": (
                        today + datetime.timedelta(days=done)
                        if done is not None
                        else None
                    ),
                    "counter_at_service": counter,
                    "downtime_hours": downtime,
                    "labor_hours": labor_hours,
                    "labor_cost": labor_cost,
                    "parts_cost": parts_cost,
                    "external_cost": external_cost,
                    "total_cost": labor_cost + parts_cost + external_cost,
                    "is_internal": is_internal,
                    "provider": provider,
                    "invoice_reference": "",
                    "responsible_id": employees.get(responsible),
                    "failure_description": failure,
                    "work_performed": work,
                    "notes": "",
                }
            )

        await asession.execute(
            text(
                """
                INSERT INTO maintenance_operation (
                    equipment_id, schedule_id, title, kind, status, priority,
                    scheduled_date, due_date, done_date, counter_at_service,
                    downtime_hours, labor_hours, labor_cost, parts_cost,
                    external_cost, total_cost, is_internal, provider,
                    invoice_reference, responsible_id, failure_description,
                    work_performed, notes
                ) VALUES (
                    :equipment_id, :schedule_id, :title, :kind, :status, :priority,
                    :scheduled_date, :due_date, :done_date, :counter_at_service,
                    :downtime_hours, :labor_hours, :labor_cost, :parts_cost,
                    :external_cost, :total_cost, :is_internal, :provider,
                    :invoice_reference, :responsible_id, :failure_description,
                    :work_performed, :notes
                )
                """
            ),
            operation_params,
        )

        operation_rows = (
            await asession.execute(
                text(
                    """
                    SELECT o.id, e.code, o.title, o.responsible_id,
                           o.equipment_id, o.scheduled_date, o.due_date,
                           COALESCE(o.labor_hours, 0), o.status
                    FROM maintenance_operation o
                    JOIN equipment e ON e.id = o.equipment_id
                    """
                )
            )
        ).all()
        operations = {
            (str(row[1]), str(row[2])): int(row[0]) for row in operation_rows
        }

        cost_params: list[dict] = []
        for (
            code,
            op_title,
            cost_type,
            label,
            reference,
            supplier,
            quantity,
            unit,
            unit_price,
            offset,
        ) in COSTS:
            key = (code, op_title)
            if key not in operations:
                continue
            cost_params.append(
                {
                    "maintenance_id": operations[key],
                    "type": cost_type,
                    "label": label,
                    "reference": reference,
                    "supplier": supplier,
                    "quantity": quantity,
                    "unit": unit,
                    "unit_price": unit_price,
                    "amount": round(quantity * unit_price, 2),
                    "incurred_on": today + datetime.timedelta(days=offset),
                    "notes": "",
                }
            )
        if cost_params:
            await asession.execute(
                text(
                    """
                    INSERT INTO maintenance_cost (
                        maintenance_id, type, label, reference, supplier,
                        quantity, unit, unit_price, amount, incurred_on, notes
                    ) VALUES (
                        :maintenance_id, :type, :label, :reference, :supplier,
                        :quantity, :unit, :unit_price, :amount, :incurred_on, :notes
                    )
                    """
                ),
                cost_params,
            )

        usage_params: list[dict] = []
        for code, employee_code, offset, start, end, fuel in USAGE:
            if code not in equipment_ids:
                continue
            usage_params.append(
                {
                    "equipment_id": equipment_ids[code],
                    "employee_id": employees.get(employee_code),
                    "intervention_id": None,
                    "used_on": today + datetime.timedelta(days=offset),
                    "counter_start": start,
                    "counter_end": end,
                    "hours_used": round(end - start, 2),
                    "fuel_liters": fuel,
                    "notes": "Relevé de chantier.",
                }
            )
        if usage_params:
            await asession.execute(
                text(
                    """
                    INSERT INTO equipment_usage_log (
                        equipment_id, employee_id, intervention_id, used_on,
                        counter_start, counter_end, hours_used, fuel_liters, notes
                    ) VALUES (
                        :equipment_id, :employee_id, :intervention_id, :used_on,
                        :counter_start, :counter_end, :hours_used, :fuel_liters, :notes
                    )
                    """
                ),
                usage_params,
            )

        assignment_params: list[dict] = []
        for row in operation_rows:
            if row[3] is None:
                continue
            hours = float(row[7] or 0)
            assignment_params.append(
                {
                    "employee_id": int(row[3]),
                    "intervention_id": None,
                    "parcel_id": None,
                    "equipment_id": int(row[4]),
                    "maintenance_id": int(row[0]),
                    "role": "RESPONSABLE",
                    "status": (
                        "TERMINEE" if str(row[8]) == "REALISEE" else "CONFIRMEE"
                    ),
                    "title": f"Maintenance · {row[2]}",
                    "start_date": as_date(row[5]),
                    "end_date": as_date(row[6]) or as_date(row[5]),
                    "planned_hours": hours,
                    "actual_hours": hours if str(row[8]) == "REALISEE" else 0.0,
                    "labor_cost": 0.0,
                    "notes": "Affectation générée avec l'opération de maintenance.",
                }
            )
        if assignment_params:
            await asession.execute(
                text(
                    """
                    INSERT INTO assignment (
                        employee_id, intervention_id, parcel_id, equipment_id,
                        maintenance_id, role, status, title, start_date, end_date,
                        planned_hours, actual_hours, labor_cost, notes
                    ) VALUES (
                        :employee_id, :intervention_id, :parcel_id, :equipment_id,
                        :maintenance_id, :role, :status, :title, :start_date, :end_date,
                        :planned_hours, :actual_hours, :labor_cost, :notes
                    )
                    """
                ),
                assignment_params,
            )

        await asession.commit()

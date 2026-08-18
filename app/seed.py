"""Amorçage idempotent des données d'exploitation.

Insère un jeu de données réaliste UNIQUEMENT si la table `parcel` est vide.
Toutes les requêtes sont écrites en SQL brut via une session asynchrone.
"""

from __future__ import annotations

import datetime

import reflex as rx
from sqlalchemy import text

from app.database import init_local_database
from app.geometry import seed_parcel_geometry

PARCELS: list[dict[str, str | float | bool]] = [
    {
        "name": "Les Grands Champs",
        "code": "P01",
        "area_ha": 42.5,
        "soil_type": "ARGILO_CALCAIRE",
        "irrigation": "PIVOT",
        "status": "EN_CULTURE",
        "locality": "Plateau de Beauce",
        "latitude": 48.234512,
        "longitude": 1.845233,
        "map_x": 4,
        "map_y": 6,
        "map_w": 40,
        "map_h": 30,
        "slope_percent": 1.5,
        "ph": 7.8,
        "organic_matter_percent": 2.4,
        "is_organic": False,
        "notes": "Îlot principal, bonne réserve utile, drainage 2019.",
    },
    {
        "name": "Coteau Sud",
        "code": "P02",
        "area_ha": 18.2,
        "soil_type": "LIMONO_SABLEUX",
        "irrigation": "ASPERSION",
        "status": "EN_CULTURE",
        "locality": "Coteaux de la Conie",
        "latitude": 48.221004,
        "longitude": 1.861007,
        "map_x": 47,
        "map_y": 6,
        "map_w": 26,
        "map_h": 30,
        "slope_percent": 6.5,
        "ph": 6.9,
        "organic_matter_percent": 1.9,
        "is_organic": False,
        "notes": "Exposition sud, sensible au stress hydrique estival.",
    },
    {
        "name": "Prairie du Moulin",
        "code": "P03",
        "area_ha": 12.8,
        "soil_type": "HUMIFERE",
        "irrigation": "GRAVITAIRE",
        "status": "EN_CULTURE",
        "locality": "Vallée du Moulin",
        "latitude": 48.240221,
        "longitude": 1.878441,
        "map_x": 76,
        "map_y": 6,
        "map_w": 20,
        "map_h": 30,
        "slope_percent": 2.0,
        "ph": 6.4,
        "organic_matter_percent": 4.8,
        "is_organic": True,
        "notes": "Conversion bio achevée, forte activité biologique.",
    },
    {
        "name": "Clos des Fontaines",
        "code": "P04",
        "area_ha": 9.6,
        "soil_type": "LIMONEUX",
        "irrigation": "GOUTTE_A_GOUTTE",
        "status": "EN_CULTURE",
        "locality": "Les Fontaines",
        "latitude": 48.228991,
        "longitude": 1.832118,
        "map_x": 4,
        "map_y": 40,
        "map_w": 24,
        "map_h": 26,
        "slope_percent": 3.2,
        "ph": 7.1,
        "organic_matter_percent": 3.1,
        "is_organic": True,
        "notes": "Parcelle maraîchère irriguée au goutte-à-goutte.",
    },
    {
        "name": "Plateau Nord",
        "code": "P05",
        "area_ha": 36.4,
        "soil_type": "ARGILEUX",
        "irrigation": "AUCUNE",
        "status": "EN_CULTURE",
        "locality": "Plateau Nord",
        "latitude": 48.252873,
        "longitude": 1.851992,
        "map_x": 31,
        "map_y": 40,
        "map_w": 42,
        "map_h": 26,
        "slope_percent": 0.8,
        "ph": 8.0,
        "organic_matter_percent": 2.1,
        "is_organic": False,
        "notes": "Sol lourd, ressuyage lent au printemps.",
    },
    {
        "name": "Terres Basses",
        "code": "P06",
        "area_ha": 14.1,
        "soil_type": "SABLEUX",
        "irrigation": "ASPERSION",
        "status": "PREPARATION",
        "locality": "Terres Basses",
        "latitude": 48.219442,
        "longitude": 1.889003,
        "map_x": 76,
        "map_y": 40,
        "map_w": 20,
        "map_h": 26,
        "slope_percent": 1.1,
        "ph": 6.2,
        "organic_matter_percent": 1.4,
        "is_organic": False,
        "notes": "Faux-semis en cours, implantation prévue sous 10 jours.",
    },
    {
        "name": "Grand Verger",
        "code": "P07",
        "area_ha": 21.7,
        "soil_type": "LIMONEUX",
        "irrigation": "GOUTTE_A_GOUTTE",
        "status": "JACHERE",
        "locality": "Route de Chartres",
        "latitude": 48.244118,
        "longitude": 1.842220,
        "map_x": 4,
        "map_y": 70,
        "map_w": 92,
        "map_h": 22,
        "slope_percent": 2.6,
        "ph": 7.0,
        "organic_matter_percent": 3.6,
        "is_organic": True,
        "notes": "Jachère mellifère, couvert semé en septembre.",
    },
]

VARIETIES: list[dict[str, str | int | float]] = [
    {
        "name": "Rubisko",
        "species": "Blé tendre d'hiver",
        "family": "Poaceae",
        "cycle_days": 250,
        "expected_yield_t_ha": 8.4,
        "sowing_window": "Octobre - Novembre",
        "harvest_window": "Juillet",
        "color_hex": "#f59e0b",
        "icon": "wheat",
        "notes": "Variété rustique, bonne tolérance à la septoriose.",
    },
    {
        "name": "Architect",
        "species": "Colza d'hiver",
        "family": "Brassicaceae",
        "cycle_days": 300,
        "expected_yield_t_ha": 4.1,
        "sowing_window": "Août",
        "harvest_window": "Juillet",
        "color_hex": "#eab308",
        "icon": "flower-2",
        "notes": "Vigueur d'automne élevée, tolérance TuYV.",
    },
    {
        "name": "Kilomeris",
        "species": "Maïs grain",
        "family": "Poaceae",
        "cycle_days": 165,
        "expected_yield_t_ha": 12.6,
        "sowing_window": "Avril - Mai",
        "harvest_window": "Octobre",
        "color_hex": "#84cc16",
        "icon": "corn",
        "notes": "Indice précoce, bon stay-green.",
    },
    {
        "name": "Planet",
        "species": "Orge de printemps",
        "family": "Poaceae",
        "cycle_days": 130,
        "expected_yield_t_ha": 7.2,
        "sowing_window": "Février - Mars",
        "harvest_window": "Juillet",
        "color_hex": "#a3e635",
        "icon": "sprout",
        "notes": "Débouché brassicole, calibrage régulier.",
    },
    {
        "name": "ES Bella",
        "species": "Tournesol",
        "family": "Asteraceae",
        "cycle_days": 145,
        "expected_yield_t_ha": 3.3,
        "sowing_window": "Avril",
        "harvest_window": "Septembre",
        "color_hex": "#fb923c",
        "icon": "sun",
        "notes": "Bonne tenue de tige, résistance mildiou.",
    },
    {
        "name": "Timbale",
        "species": "Luzerne",
        "family": "Fabaceae",
        "cycle_days": 1095,
        "expected_yield_t_ha": 13.5,
        "sowing_window": "Mars - Avril",
        "harvest_window": "Mai à Septembre",
        "color_hex": "#22c55e",
        "icon": "leaf",
        "notes": "Trois à quatre coupes annuelles.",
    },
    {
        "name": "Agata",
        "species": "Pomme de terre",
        "family": "Solanaceae",
        "cycle_days": 110,
        "expected_yield_t_ha": 38.0,
        "sowing_window": "Mars - Avril",
        "harvest_window": "Juillet - Août",
        "color_hex": "#14b8a6",
        "icon": "carrot",
        "notes": "Chair ferme, sensible au mildiou.",
    },
]


async def seed_dashboard_data() -> None:
    """Insère un jeu de données réaliste si l'exploitation est vide."""
    # Garantit que le fichier SQLite local et ses tables existent avant lecture.
    init_local_database()
    async with rx.asession() as asession:
        existing = await asession.execute(text("SELECT COUNT(*) FROM parcel"))
        if int(existing.scalar() or 0) > 0:
            await seed_parcel_geometry()
            return

        await asession.execute(
            text(
                """
                INSERT INTO parcel (
                    name, code, area_ha, soil_type, irrigation, status, locality,
                    latitude, longitude, map_x, map_y, map_w, map_h,
                    slope_percent, ph, organic_matter_percent, is_organic, notes
                ) VALUES (
                    :name, :code, :area_ha, :soil_type, :irrigation, :status, :locality,
                    :latitude, :longitude, :map_x, :map_y, :map_w, :map_h,
                    :slope_percent, :ph, :organic_matter_percent, :is_organic, :notes
                )
                """
            ),
            PARCELS,
        )
        await asession.execute(
            text(
                """
                INSERT INTO crop_variety (
                    name, species, family, cycle_days, expected_yield_t_ha,
                    sowing_window, harvest_window, color_hex, icon, notes
                ) VALUES (
                    :name, :species, :family, :cycle_days, :expected_yield_t_ha,
                    :sowing_window, :harvest_window, :color_hex, :icon, :notes
                )
                """
            ),
            VARIETIES,
        )

        parcel_rows = (
            await asession.execute(text("SELECT id, code FROM parcel"))
        ).all()
        parcel_ids = {str(row[1]): int(row[0]) for row in parcel_rows}
        variety_rows = (
            await asession.execute(text("SELECT id, name FROM crop_variety"))
        ).all()
        variety_ids = {str(row[1]): int(row[0]) for row in variety_rows}

        today = datetime.date.today()
        season = f"{today.year}"

        crops = [
            {
                "parcel_id": parcel_ids["P01"],
                "variety_id": variety_ids["Rubisko"],
                "name": "Blé tendre Rubisko",
                "season": season,
                "stage": "FLORAISON",
                "status": "EN_COURS",
                "health": "BON",
                "area_ha": 42.5,
                "sowing_date": today - datetime.timedelta(days=210),
                "expected_harvest_date": today + datetime.timedelta(days=38),
                "seed_density": 320,
                "expected_yield_t_ha": 8.4,
                "progress_percent": 78,
                "notes": "Dernier apport azoté réalisé, pression septoriose modérée.",
            },
            {
                "parcel_id": parcel_ids["P02"],
                "variety_id": variety_ids["Architect"],
                "name": "Colza Architect",
                "season": season,
                "stage": "MATURATION",
                "status": "EN_COURS",
                "health": "MOYEN",
                "area_ha": 18.2,
                "sowing_date": today - datetime.timedelta(days=265),
                "expected_harvest_date": today + datetime.timedelta(days=21),
                "seed_density": 45,
                "expected_yield_t_ha": 4.1,
                "progress_percent": 88,
                "notes": "Foyers de méligèthes observés en bordure sud.",
            },
            {
                "parcel_id": parcel_ids["P03"],
                "variety_id": variety_ids["Timbale"],
                "name": "Luzerne Timbale (2e coupe)",
                "season": season,
                "stage": "CROISSANCE",
                "status": "EN_COURS",
                "health": "EXCELLENT",
                "area_ha": 12.8,
                "sowing_date": today - datetime.timedelta(days=420),
                "expected_harvest_date": today + datetime.timedelta(days=12),
                "seed_density": 25,
                "expected_yield_t_ha": 13.5,
                "progress_percent": 62,
                "notes": "Deuxième coupe prévue au stade bourgeonnement.",
            },
            {
                "parcel_id": parcel_ids["P04"],
                "variety_id": variety_ids["Agata"],
                "name": "Pomme de terre Agata",
                "season": season,
                "stage": "FRUCTIFICATION",
                "status": "EN_COURS",
                "health": "FAIBLE",
                "area_ha": 9.6,
                "sowing_date": today - datetime.timedelta(days=72),
                "expected_harvest_date": today + datetime.timedelta(days=40),
                "seed_density": 42000,
                "expected_yield_t_ha": 38.0,
                "progress_percent": 55,
                "notes": "Risque mildiou élevé, cadence de protection resserrée.",
            },
            {
                "parcel_id": parcel_ids["P05"],
                "variety_id": variety_ids["Kilomeris"],
                "name": "Maïs grain Kilomeris",
                "season": season,
                "stage": "CROISSANCE",
                "status": "EN_COURS",
                "health": "BON",
                "area_ha": 36.4,
                "sowing_date": today - datetime.timedelta(days=48),
                "expected_harvest_date": today + datetime.timedelta(days=118),
                "seed_density": 88000,
                "expected_yield_t_ha": 12.6,
                "progress_percent": 34,
                "notes": "Stade 8 feuilles, désherbage de rattrapage effectué.",
            },
            {
                "parcel_id": parcel_ids["P06"],
                "variety_id": variety_ids["ES Bella"],
                "name": "Tournesol ES Bella",
                "season": season,
                "stage": "SEMIS",
                "status": "PLANIFIEE",
                "health": "BON",
                "area_ha": 14.1,
                "sowing_date": today + datetime.timedelta(days=9),
                "expected_harvest_date": today + datetime.timedelta(days=154),
                "seed_density": 62000,
                "expected_yield_t_ha": 3.3,
                "progress_percent": 0,
                "notes": "Semis conditionné au ressuyage des Terres Basses.",
            },
            {
                "parcel_id": parcel_ids["P01"],
                "variety_id": variety_ids["Planet"],
                "name": "Orge de printemps Planet",
                "season": str(today.year - 1),
                "stage": "TERMINEE",
                "status": "RECOLTEE",
                "health": "BON",
                "area_ha": 22.0,
                "sowing_date": today - datetime.timedelta(days=430),
                "expected_harvest_date": today - datetime.timedelta(days=300),
                "actual_harvest_date": today - datetime.timedelta(days=298),
                "seed_density": 280,
                "expected_yield_t_ha": 7.2,
                "progress_percent": 100,
                "notes": "Campagne précédente, calibrage brassicole atteint.",
            },
        ]
        for crop in crops:
            crop.setdefault("actual_harvest_date", None)

        await asession.execute(
            text(
                """
                INSERT INTO crop (
                    parcel_id, variety_id, name, season, stage, status, health, area_ha,
                    sowing_date, expected_harvest_date, actual_harvest_date,
                    seed_density, expected_yield_t_ha, progress_percent, notes
                ) VALUES (
                    :parcel_id, :variety_id, :name, :season, :stage, :status, :health, :area_ha,
                    :sowing_date, :expected_harvest_date, :actual_harvest_date,
                    :seed_density, :expected_yield_t_ha, :progress_percent, :notes
                )
                """
            ),
            crops,
        )

        crop_rows = (
            await asession.execute(text("SELECT id, name FROM crop"))
        ).all()
        crop_ids = {str(row[1]): int(row[0]) for row in crop_rows}

        interventions = [
            {
                "parcel_id": parcel_ids["P04"],
                "crop_id": crop_ids["Pomme de terre Agata"],
                "type": "TRAITEMENT_PHYTO",
                "status": "PLANIFIEE",
                "title": "Protection mildiou - relais fongicide",
                "scheduled_date": today + datetime.timedelta(days=1),
                "done_date": None,
                "operator": "Camille Roux",
                "equipment": "Pulvérisateur porté 1200 L",
                "area_treated_ha": 9.6,
                "water_volume_l_ha": 180,
                "duration_hours": 2.5,
                "cost": 486.0,
                "weather_conditions": "Couvert, vent faible",
                "temperature_c": 18.5,
                "wind_speed_kmh": 9.0,
                "target": "Phytophthora infestans",
                "notes": "Fenêtre d'application tôt le matin.",
            },
            {
                "parcel_id": parcel_ids["P03"],
                "crop_id": crop_ids["Luzerne Timbale (2e coupe)"],
                "type": "IRRIGATION",
                "status": "PLANIFIEE",
                "title": "Tour d'eau gravitaire",
                "scheduled_date": today + datetime.timedelta(days=2),
                "done_date": None,
                "operator": "Yanis Berger",
                "equipment": "Vanne principale ouest",
                "area_treated_ha": 12.8,
                "water_volume_l_ha": 220,
                "duration_hours": 6.0,
                "cost": 210.0,
                "weather_conditions": "Sec",
                "temperature_c": 24.0,
                "wind_speed_kmh": 12.0,
                "target": "Réserve utile",
                "notes": "Après contrôle des sondes tensiométriques.",
            },
            {
                "parcel_id": parcel_ids["P06"],
                "crop_id": crop_ids["Tournesol ES Bella"],
                "type": "TRAVAIL_DU_SOL",
                "status": "PLANIFIEE",
                "title": "Préparation de lit de semence",
                "scheduled_date": today + datetime.timedelta(days=4),
                "done_date": None,
                "operator": "Marc Delaunay",
                "equipment": "Herse rotative 4 m",
                "area_treated_ha": 14.1,
                "water_volume_l_ha": 0,
                "duration_hours": 5.5,
                "cost": 395.0,
                "weather_conditions": "Sol ressuyé",
                "temperature_c": 21.0,
                "wind_speed_kmh": 15.0,
                "target": "Lit de semence",
                "notes": "Passage croisé si battance.",
            },
            {
                "parcel_id": parcel_ids["P06"],
                "crop_id": crop_ids["Tournesol ES Bella"],
                "type": "SEMIS",
                "status": "PLANIFIEE",
                "title": "Semis tournesol 62 000 gr/ha",
                "scheduled_date": today + datetime.timedelta(days=9),
                "done_date": None,
                "operator": "Marc Delaunay",
                "equipment": "Semoir monograine 6 rangs",
                "area_treated_ha": 14.1,
                "water_volume_l_ha": 0,
                "duration_hours": 7.0,
                "cost": 1120.0,
                "weather_conditions": "Sol réchauffé",
                "temperature_c": 22.5,
                "wind_speed_kmh": 10.0,
                "target": "Implantation",
                "notes": "Contrôle de la profondeur à 3 cm.",
            },
            {
                "parcel_id": parcel_ids["P01"],
                "crop_id": crop_ids["Blé tendre Rubisko"],
                "type": "OBSERVATION",
                "status": "PLANIFIEE",
                "title": "Notation sanitaire épis",
                "scheduled_date": today + datetime.timedelta(days=6),
                "done_date": None,
                "operator": "Camille Roux",
                "equipment": "Grille de notation",
                "area_treated_ha": 42.5,
                "water_volume_l_ha": 0,
                "duration_hours": 1.5,
                "cost": 0.0,
                "weather_conditions": "Variable",
                "temperature_c": 20.0,
                "wind_speed_kmh": 14.0,
                "target": "Fusariose / septoriose",
                "notes": "Cinq placettes de 20 épis.",
            },
            {
                "parcel_id": parcel_ids["P02"],
                "crop_id": crop_ids["Colza Architect"],
                "type": "RECOLTE",
                "status": "PLANIFIEE",
                "title": "Chantier de récolte colza",
                "scheduled_date": today + datetime.timedelta(days=13),
                "done_date": None,
                "operator": "ETA Vallée",
                "equipment": "Moissonneuse 7,5 m",
                "area_treated_ha": 18.2,
                "water_volume_l_ha": 0,
                "duration_hours": 8.0,
                "cost": 1830.0,
                "weather_conditions": "Sec attendu",
                "temperature_c": 27.0,
                "wind_speed_kmh": 8.0,
                "target": "Récolte",
                "notes": "Objectif humidité 9 %.",
            },
            {
                "parcel_id": parcel_ids["P05"],
                "crop_id": crop_ids["Maïs grain Kilomeris"],
                "type": "DESHERBAGE",
                "status": "REALISEE",
                "title": "Désherbage de post-levée",
                "scheduled_date": today - datetime.timedelta(days=5),
                "done_date": today - datetime.timedelta(days=5),
                "operator": "Yanis Berger",
                "equipment": "Pulvérisateur traîné 3000 L",
                "area_treated_ha": 36.4,
                "water_volume_l_ha": 150,
                "duration_hours": 4.0,
                "cost": 1240.0,
                "weather_conditions": "Doux, humide",
                "temperature_c": 17.0,
                "wind_speed_kmh": 7.0,
                "target": "Chénopode, morelle",
                "notes": "Efficacité satisfaisante à J+5.",
            },
            {
                "parcel_id": parcel_ids["P01"],
                "crop_id": crop_ids["Blé tendre Rubisko"],
                "type": "FERTILISATION",
                "status": "REALISEE",
                "title": "Troisième apport azoté",
                "scheduled_date": today - datetime.timedelta(days=12),
                "done_date": today - datetime.timedelta(days=12),
                "operator": "Marc Delaunay",
                "equipment": "Distributeur 24 m",
                "area_treated_ha": 42.5,
                "water_volume_l_ha": 0,
                "duration_hours": 3.0,
                "cost": 2650.0,
                "weather_conditions": "Pluie annoncée",
                "temperature_c": 14.0,
                "wind_speed_kmh": 11.0,
                "target": "Remplissage du grain",
                "notes": "60 unités d'azote, valorisation optimale.",
            },
            {
                "parcel_id": parcel_ids["P03"],
                "crop_id": crop_ids["Luzerne Timbale (2e coupe)"],
                "type": "RECOLTE",
                "status": "REALISEE",
                "title": "Première coupe de luzerne",
                "scheduled_date": today - datetime.timedelta(days=26),
                "done_date": today - datetime.timedelta(days=25),
                "operator": "ETA Vallée",
                "equipment": "Faucheuse conditionneuse",
                "area_treated_ha": 12.8,
                "water_volume_l_ha": 0,
                "duration_hours": 5.0,
                "cost": 640.0,
                "weather_conditions": "Séchant",
                "temperature_c": 23.0,
                "wind_speed_kmh": 16.0,
                "target": "Fourrage",
                "notes": "Fanage sur deux jours.",
            },
        ]
        await asession.execute(
            text(
                """
                INSERT INTO intervention (
                    parcel_id, crop_id, type, status, title, scheduled_date, done_date,
                    operator, equipment, area_treated_ha, water_volume_l_ha, duration_hours,
                    cost, weather_conditions, temperature_c, wind_speed_kmh, target, notes
                ) VALUES (
                    :parcel_id, :crop_id, :type, :status, :title, :scheduled_date, :done_date,
                    :operator, :equipment, :area_treated_ha, :water_volume_l_ha, :duration_hours,
                    :cost, :weather_conditions, :temperature_c, :wind_speed_kmh, :target, :notes
                )
                """
            ),
            interventions,
        )

        alerts = [
            {
                "parcel_id": parcel_ids["P04"],
                "level": "CRITIQUE",
                "title": "Risque mildiou très élevé",
                "message": "Modèle épidémiologique en zone rouge sur Clos des Fontaines : intervenir sous 24 h.",
                "category": "Sanitaire",
                "is_resolved": False,
                "triggered_on": today,
            },
            {
                "parcel_id": parcel_ids["P02"],
                "level": "ATTENTION",
                "title": "Pression méligèthes en bordure",
                "message": "Comptage à 4 insectes par plante sur la bordure sud du Coteau Sud.",
                "category": "Ravageurs",
                "is_resolved": False,
                "triggered_on": today - datetime.timedelta(days=1),
            },
            {
                "parcel_id": parcel_ids["P03"],
                "level": "ATTENTION",
                "title": "Réserve utile sous le seuil",
                "message": "Tensiomètres à -68 kPa : déclencher le tour d'eau gravitaire.",
                "category": "Hydrique",
                "is_resolved": False,
                "triggered_on": today - datetime.timedelta(days=2),
            },
            {
                "parcel_id": parcel_ids["P05"],
                "level": "INFO",
                "title": "Fenêtre de désherbage favorable",
                "message": "Hygrométrie supérieure à 70 % et vent inférieur à 12 km/h sur 48 h.",
                "category": "Météo",
                "is_resolved": False,
                "triggered_on": today - datetime.timedelta(days=3),
            },
            {
                "parcel_id": parcel_ids["P06"],
                "level": "INFO",
                "title": "Ressuyage à vérifier avant semis",
                "message": "Contrôler la portance des Terres Basses avant le passage de la herse.",
                "category": "Agronomie",
                "is_resolved": False,
                "triggered_on": today - datetime.timedelta(days=4),
            },
            {
                "parcel_id": parcel_ids["P01"],
                "level": "INFO",
                "title": "Apport azoté valorisé",
                "message": "Les 12 mm de pluie ont permis une bonne valorisation du dernier apport.",
                "category": "Fertilisation",
                "is_resolved": True,
                "triggered_on": today - datetime.timedelta(days=11),
            },
        ]
        await asession.execute(
            text(
                """
                INSERT INTO alert (
                    parcel_id, level, title, message, category, is_resolved, triggered_on
                ) VALUES (
                    :parcel_id, :level, :title, :message, :category, :is_resolved, :triggered_on
                )
                """
            ),
            alerts,
        )

        harvests = [
            {
                "crop_id": crop_ids["Orge de printemps Planet"],
                "harvest_date": today - datetime.timedelta(days=298),
                "quantity": 158.4,
                "unit": "t",
                "area_harvested_ha": 22.0,
                "yield_t_ha": 7.2,
                "moisture_percent": 13.5,
                "quality": "A",
                "loss_percent": 1.8,
                "storage_location": "Cellule 3",
                "unit_price": 232.0,
                "revenue": 36748.8,
                "operator": "ETA Vallée",
                "notes": "Calibrage brassicole 92 %.",
            },
            {
                "crop_id": crop_ids["Luzerne Timbale (2e coupe)"],
                "harvest_date": today - datetime.timedelta(days=25),
                "quantity": 52.6,
                "unit": "t",
                "area_harvested_ha": 12.8,
                "yield_t_ha": 4.1,
                "moisture_percent": 16.0,
                "quality": "A",
                "loss_percent": 3.2,
                "storage_location": "Hangar fourrage",
                "unit_price": 165.0,
                "revenue": 8679.0,
                "operator": "ETA Vallée",
                "notes": "Première coupe, valeur azotée élevée.",
            },
            {
                "crop_id": crop_ids["Blé tendre Rubisko"],
                "harvest_date": today - datetime.timedelta(days=350),
                "quantity": 340.0,
                "unit": "t",
                "area_harvested_ha": 42.5,
                "yield_t_ha": 8.0,
                "moisture_percent": 14.2,
                "quality": "B",
                "loss_percent": 2.4,
                "storage_location": "Cellule 1",
                "unit_price": 214.0,
                "revenue": 72760.0,
                "operator": "ETA Vallée",
                "notes": "Campagne précédente sur le même îlot.",
            },
        ]
        await asession.execute(
            text(
                """
                INSERT INTO harvest (
                    crop_id, harvest_date, quantity, unit, area_harvested_ha, yield_t_ha,
                    moisture_percent, quality, loss_percent, storage_location,
                    unit_price, revenue, operator, notes
                ) VALUES (
                    :crop_id, :harvest_date, :quantity, :unit, :area_harvested_ha, :yield_t_ha,
                    :moisture_percent, :quality, :loss_percent, :storage_location,
                    :unit_price, :revenue, :operator, :notes
                )
                """
            ),
            harvests,
        )

        await asession.commit()

    await seed_parcel_geometry()

"""Amorçage idempotent du registre humain de l'exploitation.

Insère employés, référentiel de compétences, niveaux de maîtrise,
disponibilités et affectations UNIQUEMENT si la table `employee` est vide.
Toutes les requêtes sont écrites en SQL brut.
"""

from __future__ import annotations

import datetime

import reflex as rx
from sqlalchemy import text

from app.database import init_local_database

EMPLOYEES: list[dict[str, str | float | bool | int]] = [
    {
        "first_name": "Camille",
        "last_name": "Roux",
        "employee_code": "E01",
        "job_title": "Responsable cultures",
        "contract_type": "CDI",
        "status": "ACTIF",
        "email": "camille.roux@domaine-vegetal.fr",
        "phone": "06 12 45 78 03",
        "weekly_hours": 39.0,
        "hourly_cost": 28.5,
        "team": "Agronomie",
        "has_driving_licence": True,
        "has_phyto_certificate": True,
        "emergency_contact": "Paul Roux · 06 88 21 04 55",
        "notes": "Référente protection des cultures et notations sanitaires.",
        "hired_offset": 2600,
        "phyto_offset": 240,
    },
    {
        "first_name": "Marc",
        "last_name": "Delaunay",
        "employee_code": "E02",
        "job_title": "Chef de plaine",
        "contract_type": "CDI",
        "status": "ACTIF",
        "email": "marc.delaunay@domaine-vegetal.fr",
        "phone": "06 77 30 19 42",
        "weekly_hours": 42.0,
        "hourly_cost": 26.0,
        "team": "Plaine",
        "has_driving_licence": True,
        "has_phyto_certificate": True,
        "emergency_contact": "Hélène Delaunay · 06 45 77 12 90",
        "notes": "Pilote les chantiers de semis et de travail du sol.",
        "hired_offset": 4100,
        "phyto_offset": 95,
    },
    {
        "first_name": "Yanis",
        "last_name": "Berger",
        "employee_code": "E03",
        "job_title": "Agent d'irrigation",
        "contract_type": "CDI",
        "status": "ACTIF",
        "email": "yanis.berger@domaine-vegetal.fr",
        "phone": "07 61 22 88 14",
        "weekly_hours": 35.0,
        "hourly_cost": 21.5,
        "team": "Irrigation",
        "has_driving_licence": True,
        "has_phyto_certificate": True,
        "emergency_contact": "Nora Berger · 07 12 65 33 08",
        "notes": "Gère les tours d'eau et le pilotage des sondes.",
        "hired_offset": 1450,
        "phyto_offset": 480,
    },
    {
        "first_name": "Élodie",
        "last_name": "Marchand",
        "employee_code": "E04",
        "job_title": "Conductrice d'engins",
        "contract_type": "CDD",
        "status": "ACTIF",
        "email": "elodie.marchand@domaine-vegetal.fr",
        "phone": "06 94 11 27 65",
        "weekly_hours": 38.0,
        "hourly_cost": 23.0,
        "team": "Plaine",
        "has_driving_licence": True,
        "has_phyto_certificate": False,
        "emergency_contact": "Luc Marchand · 06 20 44 71 12",
        "notes": "Renfort récolte et transport, habilitée chargeur télescopique.",
        "hired_offset": 210,
        "phyto_offset": 0,
    },
    {
        "first_name": "Thomas",
        "last_name": "Guerin",
        "employee_code": "E05",
        "job_title": "Mécanicien atelier",
        "contract_type": "CDI",
        "status": "ACTIF",
        "email": "thomas.guerin@domaine-vegetal.fr",
        "phone": "06 38 55 90 27",
        "weekly_hours": 37.0,
        "hourly_cost": 25.0,
        "team": "Atelier",
        "has_driving_licence": True,
        "has_phyto_certificate": False,
        "emergency_contact": "Sarah Guerin · 06 71 08 42 33",
        "notes": "Entretien préventif de la flotte et soudure.",
        "hired_offset": 3200,
        "phyto_offset": 0,
    },
    {
        "first_name": "Laura",
        "last_name": "Fontaine",
        "employee_code": "E06",
        "job_title": "Apprentie agronomie",
        "contract_type": "APPRENTI",
        "status": "FORMATION",
        "email": "laura.fontaine@domaine-vegetal.fr",
        "phone": "07 45 63 12 78",
        "weekly_hours": 32.0,
        "hourly_cost": 12.5,
        "team": "Agronomie",
        "has_driving_licence": False,
        "has_phyto_certificate": False,
        "emergency_contact": "Claire Fontaine · 06 33 90 55 21",
        "notes": "Alternance BTS APV, suivi des essais variétaux.",
        "hired_offset": 330,
        "phyto_offset": 0,
    },
    {
        "first_name": "Ibrahim",
        "last_name": "Sow",
        "employee_code": "E07",
        "job_title": "Ouvrier saisonnier maraîchage",
        "contract_type": "SAISONNIER",
        "status": "CONGE",
        "email": "ibrahim.sow@domaine-vegetal.fr",
        "phone": "07 88 41 06 59",
        "weekly_hours": 35.0,
        "hourly_cost": 15.0,
        "team": "Maraîchage",
        "has_driving_licence": True,
        "has_phyto_certificate": False,
        "emergency_contact": "Awa Sow · 07 55 21 88 40",
        "notes": "Récolte et conditionnement pomme de terre.",
        "hired_offset": 120,
        "phyto_offset": 0,
    },
]

SKILLS: list[dict[str, str | bool]] = [
    {
        "name": "Conduite de tracteur",
        "category": "Machinisme",
        "description": "Attelage, réglages et conduite en plaine.",
        "requires_certification": False,
        "icon": "tractor",
    },
    {
        "name": "Application phytosanitaire",
        "category": "Protection",
        "description": "Préparation de bouillie et pulvérisation raisonnée.",
        "requires_certification": True,
        "icon": "spray-can",
    },
    {
        "name": "Réglage semoir",
        "category": "Machinisme",
        "description": "Densité, profondeur et contrôle de débit.",
        "requires_certification": False,
        "icon": "sprout",
    },
    {
        "name": "Pilotage irrigation",
        "category": "Hydrique",
        "description": "Tours d'eau, tensiométrie et maintenance réseau.",
        "requires_certification": False,
        "icon": "droplets",
    },
    {
        "name": "Maintenance mécanique",
        "category": "Atelier",
        "description": "Entretien préventif, hydraulique et soudure.",
        "requires_certification": False,
        "icon": "wrench",
    },
    {
        "name": "Observation sanitaire",
        "category": "Agronomie",
        "description": "Comptages, notations et seuils d'intervention.",
        "requires_certification": False,
        "icon": "eye",
    },
    {
        "name": "Conduite moissonneuse",
        "category": "Machinisme",
        "description": "Récolte, réglages de battage et qualité de grain.",
        "requires_certification": False,
        "icon": "wheat",
    },
    {
        "name": "Manutention chargeur",
        "category": "Logistique",
        "description": "Chargeur télescopique et gestion des big bags.",
        "requires_certification": True,
        "icon": "forklift",
    },
]

# (code employé, compétence, niveau, années, certifié il y a n jours, expire dans n jours)
EMPLOYEE_SKILLS: list[tuple[str, str, str, float, int, int]] = [
    ("E01", "Application phytosanitaire", "EXPERT", 11.0, 400, 240),
    ("E01", "Observation sanitaire", "EXPERT", 12.0, 0, 0),
    ("E01", "Conduite de tracteur", "INTERMEDIAIRE", 6.0, 0, 0),
    ("E02", "Conduite de tracteur", "EXPERT", 18.0, 0, 0),
    ("E02", "Réglage semoir", "EXPERT", 15.0, 0, 0),
    ("E02", "Application phytosanitaire", "AVANCE", 9.0, 900, 95),
    ("E02", "Conduite moissonneuse", "AVANCE", 10.0, 0, 0),
    ("E03", "Pilotage irrigation", "EXPERT", 8.0, 0, 0),
    ("E03", "Conduite de tracteur", "AVANCE", 7.0, 0, 0),
    ("E03", "Application phytosanitaire", "INTERMEDIAIRE", 4.0, 300, 480),
    ("E04", "Conduite de tracteur", "AVANCE", 5.0, 0, 0),
    ("E04", "Conduite moissonneuse", "INTERMEDIAIRE", 3.0, 0, 0),
    ("E04", "Manutention chargeur", "AVANCE", 4.0, 200, 900),
    ("E05", "Maintenance mécanique", "EXPERT", 16.0, 0, 0),
    ("E05", "Conduite de tracteur", "AVANCE", 12.0, 0, 0),
    ("E05", "Manutention chargeur", "INTERMEDIAIRE", 6.0, 500, 610),
    ("E06", "Observation sanitaire", "DEBUTANT", 0.5, 0, 0),
    ("E06", "Réglage semoir", "DEBUTANT", 0.5, 0, 0),
    ("E07", "Manutention chargeur", "DEBUTANT", 1.0, 0, 0),
]

# (code employé, type, début (offset), fin (offset), heures/j, motif)
AVAILABILITIES: list[tuple[str, str, int, int, float, str]] = [
    ("E01", "DISPONIBLE", -3, 21, 8.0, "Semaine de suivi cultures"),
    ("E01", "FORMATION", 24, 25, 7.0, "Recyclage Certiphyto décideur"),
    ("E02", "DISPONIBLE", -3, 14, 8.5, "Chantiers de plaine"),
    ("E02", "ASTREINTE", 15, 17, 4.0, "Astreinte irrigation week-end"),
    ("E03", "DISPONIBLE", -2, 10, 7.5, "Tours d'eau programmés"),
    ("E03", "CONGE", 12, 19, 0.0, "Congés annuels"),
    ("E04", "DISPONIBLE", 0, 30, 8.0, "Renfort récolte"),
    ("E05", "DISPONIBLE", -5, 25, 7.5, "Atelier maintenance"),
    ("E06", "FORMATION", -1, 6, 7.0, "Semaine au CFA"),
    ("E06", "DISPONIBLE", 7, 20, 6.5, "Retour en exploitation"),
    ("E07", "CONGE", -4, 9, 0.0, "Congé sans solde"),
]

# (code employé, titre intervention ou "", rôle, statut, début, fin, heures prévues, titre)
ASSIGNMENTS: list[tuple[str, str, str, str, int, int, float, str]] = [
    (
        "E01",
        "Protection mildiou - relais fongicide",
        "RESPONSABLE",
        "CONFIRMEE",
        1,
        1,
        3.0,
        "Encadrement du passage fongicide",
    ),
    (
        "E03",
        "Tour d'eau gravitaire",
        "OPERATEUR",
        "CONFIRMEE",
        2,
        2,
        6.0,
        "Ouverture des vannes ouest",
    ),
    (
        "E02",
        "Préparation de lit de semence",
        "CONDUCTEUR",
        "CONFIRMEE",
        4,
        4,
        5.5,
        "Herse rotative Terres Basses",
    ),
    (
        "E02",
        "Semis tournesol 62 000 gr/ha",
        "CONDUCTEUR",
        "PROPOSEE",
        9,
        9,
        7.0,
        "Semis monograine tournesol",
    ),
    (
        "E06",
        "Notation sanitaire épis",
        "AIDE",
        "PROPOSEE",
        6,
        6,
        1.5,
        "Comptage placettes blé",
    ),
    (
        "E04",
        "Chantier de récolte colza",
        "CONDUCTEUR",
        "PROPOSEE",
        13,
        13,
        8.0,
        "Transport bennes colza",
    ),
    (
        "E05",
        "",
        "RESPONSABLE",
        "EN_COURS",
        -1,
        2,
        9.0,
        "Révision pulvérisateur avant campagne",
    ),
    (
        "E01",
        "Désherbage de post-levée",
        "OBSERVATEUR",
        "TERMINEE",
        -5,
        -5,
        1.0,
        "Contrôle d'efficacité J+5",
    ),
]


async def seed_employee_data() -> None:
    """Insère le registre humain si la table employé est vide."""
    init_local_database()
    async with rx.asession() as asession:
        existing = await asession.execute(text("SELECT COUNT(*) FROM employee"))
        if int(existing.scalar() or 0) > 0:
            return

        today = datetime.date.today()
        employee_params: list[dict[str, str | float | bool | None]] = []
        for item in EMPLOYEES:
            hired = today - datetime.timedelta(days=int(item["hired_offset"]))
            phyto_offset = int(item["phyto_offset"])
            employee_params.append(
                {
                    "first_name": item["first_name"],
                    "last_name": item["last_name"],
                    "employee_code": item["employee_code"],
                    "job_title": item["job_title"],
                    "contract_type": item["contract_type"],
                    "status": item["status"],
                    "email": item["email"],
                    "phone": item["phone"],
                    "hired_on": hired,
                    "contract_end_on": (
                        today + datetime.timedelta(days=150)
                        if item["contract_type"]
                        in ("CDD", "SAISONNIER", "APPRENTI")
                        else None
                    ),
                    "weekly_hours": item["weekly_hours"],
                    "hourly_cost": item["hourly_cost"],
                    "team": item["team"],
                    "has_driving_licence": item["has_driving_licence"],
                    "has_phyto_certificate": item["has_phyto_certificate"],
                    "phyto_certificate_expiry": (
                        today + datetime.timedelta(days=phyto_offset)
                        if phyto_offset > 0
                        else None
                    ),
                    "emergency_contact": item["emergency_contact"],
                    "notes": item["notes"],
                }
            )

        await asession.execute(
            text(
                """
                INSERT INTO employee (
                    first_name, last_name, employee_code, job_title, contract_type,
                    status, email, phone, hired_on, contract_end_on, weekly_hours,
                    hourly_cost, team, has_driving_licence, has_phyto_certificate,
                    phyto_certificate_expiry, emergency_contact, notes
                ) VALUES (
                    :first_name, :last_name, :employee_code, :job_title, :contract_type,
                    :status, :email, :phone, :hired_on, :contract_end_on, :weekly_hours,
                    :hourly_cost, :team, :has_driving_licence, :has_phyto_certificate,
                    :phyto_certificate_expiry, :emergency_contact, :notes
                )
                """
            ),
            employee_params,
        )

        skill_rows_existing = int(
            (
                await asession.execute(text("SELECT COUNT(*) FROM skill"))
            ).scalar()
            or 0
        )
        if skill_rows_existing == 0:
            await asession.execute(
                text(
                    """
                    INSERT INTO skill (
                        name, category, description, requires_certification, icon
                    ) VALUES (
                        :name, :category, :description, :requires_certification, :icon
                    )
                    """
                ),
                SKILLS,
            )

        employee_rows = (
            await asession.execute(
                text("SELECT id, employee_code FROM employee")
            )
        ).all()
        employee_ids = {str(row[1]): int(row[0]) for row in employee_rows}
        skill_rows = (
            await asession.execute(text("SELECT id, name FROM skill"))
        ).all()
        skill_ids = {str(row[1]): int(row[0]) for row in skill_rows}

        skill_params: list[dict[str, str | float | int | None]] = []
        for (
            code,
            skill_name,
            level,
            years,
            certified,
            expiry,
        ) in EMPLOYEE_SKILLS:
            if code not in employee_ids or skill_name not in skill_ids:
                continue
            skill_params.append(
                {
                    "employee_id": employee_ids[code],
                    "skill_id": skill_ids[skill_name],
                    "level": level,
                    "years_experience": years,
                    "certified_on": (
                        today - datetime.timedelta(days=certified)
                        if certified > 0
                        else None
                    ),
                    "certificate_expiry": (
                        today + datetime.timedelta(days=expiry)
                        if expiry > 0
                        else None
                    ),
                    "notes": "",
                }
            )
        if skill_params:
            await asession.execute(
                text(
                    """
                    INSERT INTO employee_skill (
                        employee_id, skill_id, level, years_experience,
                        certified_on, certificate_expiry, notes
                    ) VALUES (
                        :employee_id, :skill_id, :level, :years_experience,
                        :certified_on, :certificate_expiry, :notes
                    )
                    """
                ),
                skill_params,
            )

        availability_params: list[dict[str, str | float | bool | int]] = []
        for code, kind, start, end, hours, reason in AVAILABILITIES:
            if code not in employee_ids:
                continue
            availability_params.append(
                {
                    "employee_id": employee_ids[code],
                    "type": kind,
                    "start_date": today + datetime.timedelta(days=start),
                    "end_date": today + datetime.timedelta(days=end),
                    "hours_per_day": hours,
                    "is_all_day": True,
                    "reason": reason,
                    "notes": "",
                }
            )
        if availability_params:
            await asession.execute(
                text(
                    """
                    INSERT INTO employee_availability (
                        employee_id, type, start_date, end_date, hours_per_day,
                        is_all_day, reason, notes
                    ) VALUES (
                        :employee_id, :type, :start_date, :end_date, :hours_per_day,
                        :is_all_day, :reason, :notes
                    )
                    """
                ),
                availability_params,
            )

        intervention_rows = (
            await asession.execute(
                text("SELECT id, title, parcel_id FROM intervention")
            )
        ).all()
        interventions = {
            str(row[1]): (int(row[0]), int(row[2])) for row in intervention_rows
        }

        assignment_params: list[dict[str, str | float | int | None]] = []
        for (
            code,
            intervention_title,
            role,
            status,
            start,
            end,
            hours,
            title,
        ) in ASSIGNMENTS:
            if code not in employee_ids:
                continue
            link = interventions.get(intervention_title)
            cost = 0.0
            for item in EMPLOYEES:
                if item["employee_code"] == code:
                    cost = round(float(item["hourly_cost"]) * hours, 2)
            assignment_params.append(
                {
                    "employee_id": employee_ids[code],
                    "intervention_id": link[0] if link else None,
                    "parcel_id": link[1] if link else None,
                    "equipment_id": None,
                    "maintenance_id": None,
                    "role": role,
                    "status": status,
                    "title": title,
                    "start_date": today + datetime.timedelta(days=start),
                    "end_date": today + datetime.timedelta(days=end),
                    "planned_hours": hours,
                    "actual_hours": hours if status == "TERMINEE" else 0.0,
                    "labor_cost": cost,
                    "notes": "",
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

"""Amorçage idempotent des charges et dépenses de l'exploitation.

Insère un référentiel de types de dépenses puis un jeu de dépenses réalistes
rattachées aux parcelles, cultures, salariés, engins, interventions et
opérations de maintenance existantes, UNIQUEMENT si les tables sont vides.
Toutes les requêtes sont écrites en SQL brut.
"""

from __future__ import annotations

import datetime

import reflex as rx
from sqlalchemy import text

from app.database import init_local_database

TYPES: list[dict[str, str | float | bool]] = [
    {
        "name": "Intrants et semences",
        "code": "INTR",
        "category": "Production végétale",
        "description": "Engrais, produits de protection, semences et biostimulants.",
        "color_hex": "#a3e635",
        "icon": "flask-conical",
        "default_payment_method": "VIREMENT",
        "default_vat_rate": 20.0,
        "notes": "Charges opérationnelles directement affectables aux parcelles.",
    },
    {
        "name": "Carburant et lubrifiants",
        "code": "CARB",
        "category": "Mécanisation",
        "description": "GNR, essence, huiles et graisses de la flotte.",
        "color_hex": "#fbbf24",
        "icon": "fuel",
        "default_payment_method": "PRELEVEMENT",
        "default_vat_rate": 20.0,
        "notes": "Suivi par engin pour calculer le coût horaire réel.",
    },
    {
        "name": "Entretien du matériel",
        "code": "ENTR",
        "category": "Mécanisation",
        "description": "Pièces, main d'œuvre atelier et prestations extérieures.",
        "color_hex": "#38bdf8",
        "icon": "wrench",
        "default_payment_method": "VIREMENT",
        "default_vat_rate": 20.0,
        "notes": "À rapprocher des opérations de maintenance.",
    },
    {
        "name": "Main d'œuvre et charges sociales",
        "code": "SALA",
        "category": "Ressources humaines",
        "description": "Salaires, cotisations et frais de personnel saisonnier.",
        "color_hex": "#c4b5fd",
        "icon": "users-round",
        "default_payment_method": "VIREMENT",
        "default_vat_rate": 0.0,
        "notes": "Rattachement possible à un salarié précis.",
    },
    {
        "name": "Travaux par tiers",
        "code": "ETA",
        "category": "Prestations",
        "description": "Entreprises de travaux agricoles et sous-traitance de chantier.",
        "color_hex": "#f472b6",
        "icon": "handshake",
        "default_payment_method": "CHEQUE",
        "default_vat_rate": 20.0,
        "notes": "Facturation à l'hectare ou à l'heure de chantier.",
    },
    {
        "name": "Assurances et cotisations",
        "code": "ASSU",
        "category": "Charges de structure",
        "description": "Multirisque récolte, flotte, responsabilité civile, MSA.",
        "color_hex": "#fca5a5",
        "icon": "shield-check",
        "default_payment_method": "PRELEVEMENT",
        "default_vat_rate": 0.0,
        "notes": "Échéances annuelles à provisionner.",
    },
    {
        "name": "Énergie et fluides",
        "code": "ENER",
        "category": "Charges de structure",
        "description": "Électricité des bâtiments, irrigation, eau et télécoms.",
        "color_hex": "#5eead4",
        "icon": "zap",
        "default_payment_method": "PRELEVEMENT",
        "default_vat_rate": 20.0,
        "notes": "Forte saisonnalité liée à l'irrigation.",
    },
    {
        "name": "Frais administratifs",
        "code": "ADMI",
        "category": "Charges de structure",
        "description": "Comptabilité, conseil agronomique, certifications, logiciels.",
        "color_hex": "#e5e7eb",
        "icon": "file-text",
        "default_payment_method": "CARTE",
        "default_vat_rate": 20.0,
        "notes": "Charges fixes de l'exploitation.",
    },
]

# (type, libellé, fournisseur, référence, statut, paiement, quantité, unité,
#  montant HT, TVA, jours (négatif = passé), lien type, lien clé, notes)
EXPENSES: list[tuple] = [
    (
        "Intrants et semences",
        "Solution azotée 39 - livraison cuve",
        "Coopérative Beauce Agro",
        "BL-2291",
        "PAYEE",
        "VIREMENT",
        6000.0,
        "L",
        2520.0,
        20.0,
        -48,
        "parcelle",
        "P01",
        "Approvisionnement de la cuve principale.",
    ),
    (
        "Intrants et semences",
        "Fongicide céréales Prosalis",
        "AgroDistrib Centre",
        "BL-2304",
        "PAYEE",
        "VIREMENT",
        50.0,
        "L",
        2325.0,
        20.0,
        -35,
        "culture",
        "Blé tendre Rubisko",
        "Protection des épis, campagne en cours.",
    ),
    (
        "Intrants et semences",
        "Anti-mildiou Cupralis",
        "BioIntrants Loire",
        "BL-2318",
        "ENGAGEE",
        "VIREMENT",
        25.0,
        "kg",
        322.5,
        20.0,
        -6,
        "culture",
        "Pomme de terre Agata",
        "Cadence de protection resserrée sur pomme de terre.",
    ),
    (
        "Carburant et lubrifiants",
        "GNR - remplissage cuve ferme",
        "Énergies du Perche",
        "FACT-7741",
        "PAYEE",
        "PRELEVEMENT",
        4000.0,
        "L",
        4360.0,
        20.0,
        -22,
        "engin",
        "M01",
        "Consommation flotte, relevé compteur cuve.",
    ),
    (
        "Carburant et lubrifiants",
        "Huile moteur et graisses atelier",
        "AgriParts Centre",
        "FACT-7752",
        "PAYEE",
        "CARTE",
        3.0,
        "bidon",
        286.0,
        20.0,
        -14,
        "engin",
        "M06",
        "Stock atelier pour entretiens courants.",
    ),
    (
        "Entretien du matériel",
        "Entretien 2000 h transmission",
        "AgriParts Centre",
        "FACT-7728",
        "PAYEE",
        "VIREMENT",
        1.0,
        "forfait",
        389.5,
        20.0,
        -34,
        "maintenance",
        "Entretien 2000 h transmission",
        "Pièces et main d'œuvre atelier interne.",
    ),
    (
        "Entretien du matériel",
        "Boîtier d'entraînement herse rotative",
        "Kuhn Service",
        "FACT-8890",
        "ENGAGEE",
        "VIREMENT",
        1.0,
        "u",
        980.0,
        20.0,
        -4,
        "maintenance",
        "Remplacement boîtier d'entraînement",
        "Pièce commandée en express, engin immobilisé.",
    ),
    (
        "Travaux par tiers",
        "Chantier de fauche luzerne",
        "ETA Vallée",
        "FACT-1180",
        "PAYEE",
        "CHEQUE",
        12.8,
        "ha",
        640.0,
        20.0,
        -25,
        "intervention",
        "Première coupe de luzerne",
        "Fauchage et conditionnement première coupe.",
    ),
    (
        "Travaux par tiers",
        "Acompte chantier de récolte colza",
        "ETA Vallée",
        "DEV-1194",
        "ENGAGEE",
        "VIREMENT",
        18.2,
        "ha",
        915.0,
        20.0,
        3,
        "intervention",
        "Chantier de récolte colza",
        "Acompte 50 % à la réservation du chantier.",
    ),
    (
        "Main d'œuvre et charges sociales",
        "Salaire mensuel - conducteur d'engins",
        "Exploitation",
        "PAIE-05",
        "PAYEE",
        "VIREMENT",
        151.67,
        "h",
        2480.0,
        0.0,
        -18,
        "employe",
        "E02",
        "Paie du mois, heures supplémentaires incluses.",
    ),
    (
        "Main d'œuvre et charges sociales",
        "Cotisations MSA trimestrielles",
        "MSA Beauce Cœur de Loire",
        "MSA-T2",
        "ENGAGEE",
        "PRELEVEMENT",
        1.0,
        "forfait",
        3180.0,
        0.0,
        9,
        "aucun",
        "",
        "Appel de cotisations du deuxième trimestre.",
    ),
    (
        "Assurances et cotisations",
        "Multirisque climatique récolte",
        "Groupama Centre",
        "POL-4471",
        "PAYEE",
        "PRELEVEMENT",
        1.0,
        "an",
        4260.0,
        0.0,
        -61,
        "aucun",
        "",
        "Couverture grêle et sécheresse campagne en cours.",
    ),
    (
        "Assurances e cotisations placeholder",
        "",
        "",
        "",
        "ENGAGEE",
        "VIREMENT",
        0.0,
        "u",
        0.0,
        0.0,
        0,
        "aucun",
        "",
        "",
    ),
    (
        "Énergie et fluides",
        "Électricité station de pompage",
        "EDF Entreprises",
        "ELEC-0421",
        "PAYEE",
        "PRELEVEMENT",
        1.0,
        "mois",
        742.0,
        20.0,
        -12,
        "parcelle",
        "P03",
        "Tours d'eau gravitaires de la Prairie du Moulin.",
    ),
    (
        "Énergie et fluides",
        "Redevance eau d'irrigation",
        "Syndicat de la Conie",
        "EAU-2210",
        "ENGAGEE",
        "VIREMENT",
        1.0,
        "trimestre",
        528.0,
        20.0,
        6,
        "parcelle",
        "P04",
        "Volume prélevé déclaré sur le trimestre.",
    ),
    (
        "Frais administratifs",
        "Honoraires comptables et fiscaux",
        "Cabinet Agri Conseil",
        "HON-0912",
        "PAYEE",
        "VIREMENT",
        1.0,
        "forfait",
        1180.0,
        20.0,
        -40,
        "aucun",
        "",
        "Clôture d'exercice et liasse fiscale.",
    ),
    (
        "Frais administratifs",
        "Abonnement outil de pilotage parcellaire",
        "AgriData",
        "ABO-3312",
        "PAYEE",
        "CARTE",
        12.0,
        "mois",
        468.0,
        20.0,
        -75,
        "aucun",
        "",
        "Licence annuelle, cartographie et traçabilité.",
    ),
    (
        "Frais administratifs",
        "Audit de certification bio",
        "Ecocert",
        "AUD-1120",
        "ANNULEE",
        "VIREMENT",
        1.0,
        "audit",
        620.0,
        20.0,
        -8,
        "parcelle",
        "P07",
        "Audit reporté à la demande de l'organisme.",
    ),
]


async def seed_expense_data() -> None:
    """Insère types et dépenses si le registre des charges est vide."""
    init_local_database()
    async with rx.asession() as asession:
        existing = await asession.execute(
            text("SELECT COUNT(*) FROM expense_type")
        )
        if int(existing.scalar() or 0) > 0:
            return

        await asession.execute(
            text(
                """
                INSERT INTO expense_type (
                    name, code, category, description, color_hex, icon,
                    default_payment_method, default_vat_rate, is_active,
                    is_archived, notes
                ) VALUES (
                    :name, :code, :category, :description, :color_hex, :icon,
                    :default_payment_method, :default_vat_rate, true,
                    false, :notes
                )
                """
            ),
            TYPES,
        )

        type_rows = (
            await asession.execute(text("SELECT id, name FROM expense_type"))
        ).all()
        types = {str(row[1]): int(row[0]) for row in type_rows}

        parcels = {
            str(row[1]): int(row[0])
            for row in (
                await asession.execute(text("SELECT id, code FROM parcel"))
            ).all()
        }
        crops = {
            str(row[1]): int(row[0])
            for row in (
                await asession.execute(text("SELECT id, name FROM crop"))
            ).all()
        }
        employees = {
            str(row[1]): int(row[0])
            for row in (
                await asession.execute(
                    text("SELECT id, employee_code FROM employee")
                )
            ).all()
        }
        equipments = {
            str(row[1]): int(row[0])
            for row in (
                await asession.execute(text("SELECT id, code FROM equipment"))
            ).all()
        }
        interventions = {
            str(row[1]): int(row[0])
            for row in (
                await asession.execute(
                    text("SELECT id, title FROM intervention")
                )
            ).all()
        }
        maintenances = {
            str(row[1]): int(row[0])
            for row in (
                await asession.execute(
                    text("SELECT id, title FROM maintenance_operation")
                )
            ).all()
        }

        today = datetime.date.today()
        params: list[dict] = []
        for item in EXPENSES:
            (
                type_name,
                label,
                supplier,
                reference,
                status,
                payment,
                quantity,
                unit,
                amount_ht,
                vat_rate,
                offset,
                link_kind,
                link_key,
                notes,
            ) = item
            if type_name not in types or not label:
                continue
            incurred = today + datetime.timedelta(days=int(offset))
            amount_ttc = round(amount_ht * (1 + vat_rate / 100.0), 2)
            params.append(
                {
                    "expense_type_id": types[type_name],
                    "label": label,
                    "reference": reference,
                    "supplier": supplier,
                    "invoice_reference": reference,
                    "status": status,
                    "payment_method": payment,
                    "quantity": quantity,
                    "unit": unit,
                    "amount_ht": amount_ht,
                    "vat_rate": vat_rate,
                    "amount_ttc": amount_ttc,
                    "incurred_on": incurred,
                    "due_date": incurred + datetime.timedelta(days=30),
                    "paid_on": incurred if status == "PAYEE" else None,
                    "parcel_id": parcels.get(link_key)
                    if link_kind == "parcelle"
                    else None,
                    "crop_id": crops.get(link_key)
                    if link_kind == "culture"
                    else None,
                    "employee_id": employees.get(link_key)
                    if link_kind == "employe"
                    else None,
                    "equipment_id": equipments.get(link_key)
                    if link_kind == "engin"
                    else None,
                    "intervention_id": interventions.get(link_key)
                    if link_kind == "intervention"
                    else None,
                    "maintenance_id": maintenances.get(link_key)
                    if link_kind == "maintenance"
                    else None,
                    "notes": notes,
                }
            )

        if params:
            await asession.execute(
                text(
                    """
                    INSERT INTO expense (
                        expense_type_id, label, reference, supplier,
                        invoice_reference, status, payment_method, quantity,
                        unit, amount_ht, vat_rate, amount_ttc, incurred_on,
                        due_date, paid_on, parcel_id, crop_id, employee_id,
                        equipment_id, intervention_id, maintenance_id,
                        is_archived, notes
                    ) VALUES (
                        :expense_type_id, :label, :reference, :supplier,
                        :invoice_reference, :status, :payment_method, :quantity,
                        :unit, :amount_ht, :vat_rate, :amount_ttc, :incurred_on,
                        :due_date, :paid_on, :parcel_id, :crop_id, :employee_id,
                        :equipment_id, :intervention_id, :maintenance_id,
                        false, :notes
                    )
                    """
                ),
                params,
            )

        await asession.commit()

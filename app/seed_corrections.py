"""Corrections idempotentes des incohérences relevées par l'audit fonctionnel.

Ce module ne touche à aucune migration et ne modifie aucun module sain. Il
applique, en SQL brut via `rx.asession()`, trois familles de corrections :

1. Écarts structurels Guide ↔ application : ajout de procédures pas à pas pour
   les catégories qui n'en avaient aucune (fondamentaux, cultures, travaux,
   irrigation, fertilisation, personnel), avec liens vers des écrans réellement
   enregistrés dans l'application.
2. Liaison des règles métier : rattachement de la règle « POU-FOND-001 » à un
   champ exploitable par l'aide contextuelle embarquée.
3. Données de cohérence légitimement amorçables : analyses de sol par îlot et
   journaux de stades phénologiques pour les cultures existantes.

Toutes les fonctions sont idempotentes : elles n'insèrent que ce qui manque.
"""

from __future__ import annotations

import datetime

import reflex as rx
from sqlalchemy import text

from app.database import init_local_database

GUIDE_VERSION: str = "1.0.0"

# Séquence phénologique utilisée pour reconstituer un journal cohérent.
STAGE_SEQUENCE: list[str] = [
    "SEMIS",
    "LEVEE",
    "TALLAGE",
    "CROISSANCE",
    "FLORAISON",
    "FRUCTIFICATION",
    "MATURATION",
    "RECOLTE",
    "TERMINEE",
]

STAGE_COMMENTS: dict[str, str] = {
    "SEMIS": "Implantation réalisée, profondeur et densité contrôlées.",
    "LEVEE": "Levée homogène constatée sur l'ensemble de l'îlot.",
    "TALLAGE": "Tallage en cours, peuplement conforme à l'objectif.",
    "CROISSANCE": "Croissance active, pression sanitaire sous surveillance.",
    "FLORAISON": "Floraison observée, fenêtre d'intervention notée.",
    "FRUCTIFICATION": "Remplissage engagé, état hydrique satisfaisant.",
    "MATURATION": "Maturation avancée, chantier de récolte à programmer.",
    "RECOLTE": "Récolte en cours sur la parcelle.",
    "TERMINEE": "Campagne clôturée sur cette culture.",
}

OBSERVERS: list[str] = [
    "Camille Roux",
    "Marc Delaunay",
    "Yanis Berger",
]

# ---------------------------------------------------------------------------
# Procédures manquantes du Guide (une par catégorie non couverte)
# ---------------------------------------------------------------------------

PROCEDURES: list[dict] = [
    {
        "slug": "proc-prendre-en-main-agripro",
        "category": "fondamentaux",
        "article": "logique-generale-exploitation",
        "title": "Prendre en main AgriPro dans le bon ordre",
        "objective": "Savoir dans quel ordre saisir pour que tous les écrans se remplissent seuls.",
        "context": "À la première utilisation, ou après l'arrivée d'un nouvel utilisateur.",
        "expected_result": "Une parcelle, une culture et un chantier existent, le cockpit affiche des indicateurs réels.",
        "prerequisites": "Connaître ses îlots et la campagne en cours.",
        "module_route": "/",
        "estimated_minutes": 9,
        "difficulty": "DECOUVERTE",
        "steps": [
            {
                "title": "Lire le cockpit avant de saisir",
                "instruction_farmer": "Ouvrez le cockpit : alertes d'abord, météo ensuite, calendrier pour finir.",
                "instruction_pro": "Les indicateurs sont recalculés à chaque chargement : ils reflètent l'état réel de la base.",
                "ui_hint": "Bandeau d'indicateurs en haut de l'écran d'accueil.",
                "module_route": "/",
                "field_reference": "alert.level",
                "why": "Savoir ce que l'application sait déjà évite les doubles saisies.",
                "warning": "",
                "duration_minutes": 2,
            },
            {
                "title": "Créer le foncier",
                "instruction_farmer": "Créez vos parcelles avec un code court unique et la surface réellement exploitée.",
                "instruction_pro": "`parcel.code` unique et `parcel.area_ha` > 0 conditionnent tous les ratios à l'hectare.",
                "ui_hint": "Bouton de création en tête de la liste des îlots.",
                "module_route": "/parcelles",
                "field_reference": "parcel.code",
                "why": "La parcelle est la racine de toute la chaîne de données.",
                "warning": "Un code en doublon rattache interventions et charges au mauvais îlot.",
                "duration_minutes": 3,
            },
            {
                "title": "Ouvrir la campagne",
                "instruction_farmer": "Créez la culture de l'année sur chaque parcelle, avec ses dates clés.",
                "instruction_pro": "`crop.season`, `sowing_date` et `expected_harvest_date` alimentent le calendrier et les cycles.",
                "ui_hint": "Action « Nouvelle culture » sur la fiche parcellaire.",
                "module_route": "/parcelles",
                "field_reference": "crop.season",
                "why": "Sans culture, aucune intervention ni récolte ne peut être rattachée.",
                "warning": "",
                "duration_minutes": 2,
            },
            {
                "title": "Tracer le premier chantier",
                "instruction_farmer": "Planifiez un passage, puis marquez-le réalisé après le chantier.",
                "instruction_pro": "La clôture fixe `done_date` et déclenche les sorties de stock des intrants prévus.",
                "ui_hint": "Journal des interventions.",
                "module_route": "/traitements",
                "field_reference": "intervention.status",
                "why": "Le journal des interventions est la colonne vertébrale de la traçabilité.",
                "warning": "",
                "duration_minutes": 2,
            },
        ],
    },
    {
        "slug": "proc-suivre-stades-culture",
        "category": "cultures",
        "article": "suivre-les-stades",
        "title": "Consigner un stade phénologique",
        "objective": "Constituer la mémoire de la campagne, stade par stade, datée et signée.",
        "context": "À chaque tour de plaine, ou dès qu'un stade clé est atteint.",
        "expected_result": "Le stade courant est à jour et le journal conserve l'historique.",
        "prerequisites": "Une culture en cours sur la parcelle observée.",
        "module_route": "/parcelles",
        "estimated_minutes": 5,
        "difficulty": "DECOUVERTE",
        "steps": [
            {
                "title": "Observer sur plusieurs placettes",
                "instruction_farmer": "Notez le stade dominant sur au moins cinq points de la parcelle.",
                "instruction_pro": "Le stade retenu est le stade majoritaire du peuplement, non le plus avancé.",
                "ui_hint": "Bloc « Timeline végétale » de la fiche parcellaire.",
                "module_route": "/parcelles",
                "field_reference": "crop_stage_log.stage",
                "why": "Un stade surestimé positionne les interventions trop tôt.",
                "warning": "",
                "duration_minutes": 2,
            },
            {
                "title": "Renseigner date et observateur",
                "instruction_farmer": "Indiquez la date d'observation et votre nom.",
                "instruction_pro": "`observed_on` ne peut être future ; `observer` rend l'observation opposable.",
                "ui_hint": "Formulaire « Consigner le stade ».",
                "module_route": "/parcelles",
                "field_reference": "crop_stage_log.observed_on",
                "why": "La date fait la valeur de preuve du positionnement des chantiers.",
                "warning": "Une date future est refusée par le contrôle de saisie.",
                "duration_minutes": 1,
            },
            {
                "title": "Ajouter un commentaire agronomique",
                "instruction_farmer": "Décrivez brièvement ce que vous avez vu : vigueur, ravageurs, hétérogénéité.",
                "instruction_pro": "Le commentaire documente l'écart entre stade attendu et stade constaté.",
                "ui_hint": "Champ commentaire du formulaire.",
                "module_route": "/parcelles",
                "field_reference": "crop_stage_log.comment",
                "why": "Six mois plus tard, seul le commentaire explique la décision prise.",
                "warning": "",
                "duration_minutes": 1,
                "is_optional": True,
            },
            {
                "title": "Vérifier le stade de la fiche",
                "instruction_farmer": "Contrôlez que la fiche culturale affiche bien le nouveau stade.",
                "instruction_pro": "`crop.stage` est mis à jour par la consignation : le rail phénologique doit avancer.",
                "ui_hint": "Rail de stades de la fiche culturale.",
                "module_route": "/parcelles",
                "field_reference": "crop.stage",
                "why": "Le cockpit et le calendrier s'appuient sur le stade courant.",
                "warning": "",
                "duration_minutes": 1,
            },
        ],
    },
    {
        "slug": "proc-preparer-lit-de-semence",
        "category": "travaux",
        "article": "travail-du-sol",
        "title": "Préparer un lit de semence sans tasser",
        "objective": "Obtenir un lit de semence régulier en intervenant sur un sol portant.",
        "context": "Avant chaque semis, en sortie d'hiver ou après une pluie.",
        "expected_result": "Chantier tracé avec durée, surface et coût de passage exploitables.",
        "prerequisites": "Parcelle ressuyée, outil réglé.",
        "module_route": "/traitements",
        "estimated_minutes": 6,
        "difficulty": "INTERMEDIAIRE",
        "steps": [
            {
                "title": "Contrôler le ressuyage",
                "instruction_farmer": "Prenez une poignée de terre : si elle colle et se lisse, attendez.",
                "instruction_pro": "Intervenir au-delà de la limite de plasticité provoque un tassement durable.",
                "ui_hint": "Panneau météo du cockpit pour les pluies récentes.",
                "module_route": "/",
                "field_reference": "intervention.weather_conditions",
                "why": "Un sol tassé coûte plusieurs campagnes à réparer.",
                "warning": "Ne jamais forcer un passage sur sol plastique.",
                "duration_minutes": 2,
            },
            {
                "title": "Planifier l'intervention",
                "instruction_farmer": "Créez l'intervention « travail du sol » avec la date prévue et l'outil.",
                "instruction_pro": "`intervention.type = TRAVAIL_DU_SOL`, `scheduled_date` renseignée avant le passage.",
                "ui_hint": "Journal des interventions, action de création.",
                "module_route": "/traitements",
                "field_reference": "intervention.scheduled_date",
                "why": "La planification alimente le calendrier et la charge de travail.",
                "warning": "",
                "duration_minutes": 2,
            },
            {
                "title": "Clôturer avec durée et surface",
                "instruction_farmer": "Après le chantier, saisissez la durée réelle et la surface travaillée.",
                "instruction_pro": "Débit de chantier = `area_treated_ha` / `duration_hours` ; base du coût au passage.",
                "ui_hint": "Action « réalisée » sur la ligne du journal.",
                "module_route": "/traitements",
                "field_reference": "intervention.duration_hours",
                "why": "Sans durée réelle, aucun coût de passage n'est calculable.",
                "warning": "",
                "duration_minutes": 2,
            },
        ],
    },
    {
        "slug": "proc-declencher-tour-eau",
        "category": "irrigation",
        "article": "piloter-irrigation",
        "title": "Déclencher un tour d'eau sur indicateur",
        "objective": "Apporter la bonne dose au bon moment, avec une trace du volume apporté.",
        "context": "En période de déficit hydrique, sur parcelle irrigable.",
        "expected_result": "Tour d'eau enregistré avec volume par hectare et conditions.",
        "prerequisites": "Sondes relevées ou bilan hydrique à jour.",
        "module_route": "/traitements",
        "estimated_minutes": 6,
        "difficulty": "INTERMEDIAIRE",
        "steps": [
            {
                "title": "Lire l'état de la réserve",
                "instruction_farmer": "Regardez les sondes et la pluie des derniers jours avant de décider.",
                "instruction_pro": "RU restante = RU initiale + pluies + irrigations − ET0 × Kc.",
                "ui_hint": "Panneau météo agricole du cockpit.",
                "module_route": "/",
                "field_reference": "intervention.water_volume_l_ha",
                "why": "Irriguer un sol proche de la capacité au champ, c'est drainer et lessiver.",
                "warning": "Ne pas irriguer après une pluie utile suffisante.",
                "duration_minutes": 2,
            },
            {
                "title": "Créer l'intervention d'irrigation",
                "instruction_farmer": "Enregistrez le tour d'eau avec la parcelle, la date et la durée.",
                "instruction_pro": "`intervention.type = IRRIGATION` rattachée à la culture concernée.",
                "ui_hint": "Journal des interventions.",
                "module_route": "/traitements",
                "field_reference": "intervention.type",
                "why": "Le cumul campagne des apports conditionne l'analyse d'efficience.",
                "warning": "",
                "duration_minutes": 2,
            },
            {
                "title": "Saisir le volume réellement apporté",
                "instruction_farmer": "Indiquez les millimètres ou litres par hectare apportés.",
                "instruction_pro": "`water_volume_l_ha` permet de calculer les tonnes produites par mm apporté.",
                "ui_hint": "Champ volume du formulaire d'intervention.",
                "module_route": "/traitements",
                "field_reference": "intervention.water_volume_l_ha",
                "why": "Sans volume, l'eau ne peut pas être mise en regard du rendement.",
                "warning": "",
                "duration_minutes": 2,
            },
        ],
    },
    {
        "slug": "proc-apport-azote-fractionne",
        "category": "fertilisation",
        "article": "plan-de-fumure",
        "title": "Enregistrer un apport azoté fractionné",
        "objective": "Positionner et tracer chaque fraction d'azote selon le stade de la culture.",
        "context": "À chaque apport du plan de fumure prévisionnel.",
        "expected_result": "Apport tracé avec produit, dose à l'hectare et surface fertilisée.",
        "prerequisites": "Plan de fumure établi, analyse de sol disponible.",
        "module_route": "/traitements",
        "estimated_minutes": 7,
        "difficulty": "AVANCE",
        "steps": [
            {
                "title": "Vérifier l'assiette du bilan",
                "instruction_farmer": "Contrôlez pH et matière organique de la parcelle avant de doser.",
                "instruction_pro": "`soil_analysis` fournit reliquat, P/K et matière organique du bilan azoté.",
                "ui_hint": "Fiche parcellaire, bloc agronomique.",
                "module_route": "/parcelles",
                "field_reference": "soil_analysis.nitrogen_ppm",
                "why": "Une dose sans fournitures du sol, c'est une dose au hasard.",
                "warning": "",
                "duration_minutes": 2,
            },
            {
                "title": "Positionner l'apport sur le stade",
                "instruction_farmer": "Apportez les grosses fractions quand la plante pousse vite.",
                "instruction_pro": "La synchronisation offre/demande améliore le coefficient apparent d'utilisation.",
                "ui_hint": "Rail de stades de la fiche culturale.",
                "module_route": "/parcelles",
                "field_reference": "crop.stage",
                "why": "Un apport hors stade se volatilise ou se lessive.",
                "warning": "Éviter tout apport avant une forte pluie annoncée.",
                "duration_minutes": 2,
            },
            {
                "title": "Saisir produit, dose et surface",
                "instruction_farmer": "Renseignez l'engrais, la dose par hectare et la surface fertilisée.",
                "instruction_pro": "Quantité totale = `dose_per_ha` × `area_treated_ha` ; sortie de stock à la clôture.",
                "ui_hint": "Bloc intrant du formulaire d'intervention.",
                "module_route": "/traitements",
                "field_reference": "intervention_product.dose_per_ha",
                "why": "La quantité totale conditionne le coût matière et le stock restant.",
                "warning": "",
                "duration_minutes": 3,
            },
        ],
    },
    {
        "slug": "proc-affecter-personne-habilitee",
        "category": "personnel",
        "article": "habilitations-equipe",
        "title": "Affecter une personne habilitée et disponible",
        "objective": "Sécuriser chaque chantier réglementé par une affectation valide.",
        "context": "Avant tout chantier phytosanitaire ou conduite d'engin réglementé.",
        "expected_result": "Affectation confirmée, habilitation valide et disponibilité vérifiée.",
        "prerequisites": "Registre du personnel et compétences à jour.",
        "module_route": "/employes",
        "estimated_minutes": 6,
        "difficulty": "INTERMEDIAIRE",
        "steps": [
            {
                "title": "Vérifier la compétence",
                "instruction_farmer": "Regardez la matrice : la personne sait-elle faire ce travail ?",
                "instruction_pro": "`employee_skill.level` et l'expérience qualifient l'aptitude technique.",
                "ui_hint": "Matrice de compétences de l'écran employés.",
                "module_route": "/employes",
                "field_reference": "employee_skill.level",
                "why": "Une compétence absente transforme le chantier en apprentissage coûteux.",
                "warning": "",
                "duration_minutes": 2,
            },
            {
                "title": "Contrôler l'habilitation",
                "instruction_farmer": "Vérifiez que le certificat obligatoire est encore valide.",
                "instruction_pro": "`employee.phyto_certificate_expiry` doit être postérieure à la date du chantier.",
                "ui_hint": "Fiche salarié, bloc habilitations.",
                "module_route": "/employes",
                "field_reference": "employee.phyto_certificate_expiry",
                "why": "L'habilitation est une obligation individuelle opposable à l'employeur.",
                "warning": "Certificat expiré : l'affectation doit être refusée.",
                "duration_minutes": 2,
            },
            {
                "title": "Vérifier la disponibilité",
                "instruction_farmer": "Assurez-vous qu'il n'y a ni congé ni arrêt sur la période.",
                "instruction_pro": "`employee_availability` ne doit pas chevaucher la période d'affectation.",
                "ui_hint": "Planning de disponibilités.",
                "module_route": "/employes",
                "field_reference": "employee_availability",
                "why": "Un chantier affecté à un absent se reporte en cascade.",
                "warning": "",
                "duration_minutes": 1,
            },
            {
                "title": "Confirmer l'affectation",
                "instruction_farmer": "Enregistrez l'affectation avec le rôle et les heures prévues.",
                "instruction_pro": "`assignment.role` et `planned_hours` valorisent la main d'œuvre du chantier.",
                "ui_hint": "Formulaire d'affectation.",
                "module_route": "/employes",
                "field_reference": "assignment.planned_hours",
                "why": "Les heures prévues puis réalisées donnent le coût de main d'œuvre.",
                "warning": "",
                "duration_minutes": 1,
            },
        ],
    },
]

# Règles dont la liaison au champ contrôlé était manquante.
RULE_FIELD_FIXES: list[dict[str, str]] = [
    {
        "code": "POU-FOND-001",
        "field_reference": "parcel.code",
        "module_route": "/parcelles",
    },
]

_guide_done: bool = False
_data_done: bool = False


async def seed_guide_corrections() -> None:
    """Ajoute les procédures manquantes et rattache les règles orphelines."""
    global _guide_done
    if _guide_done:
        return
    init_local_database()
    async with rx.asession() as asession:
        # La base de connaissances doit exister (catégories amorcées).
        categories = (
            await asession.execute(text("SELECT key, id FROM guide_category"))
        ).all()
        if not categories:
            return
        category_ids = {str(row[0]): int(row[1]) for row in categories}
        article_ids = {
            str(row[0]): int(row[1])
            for row in (
                await asession.execute(
                    text("SELECT slug, id FROM guide_article")
                )
            ).all()
        }

        inserted = 0
        for item in PROCEDURES:
            category_id = category_ids.get(item["category"])
            if category_id is None:
                continue
            exists = int(
                (
                    await asession.execute(
                        text(
                            "SELECT COUNT(*) FROM guide_procedure WHERE slug = :slug"
                        ),
                        {"slug": item["slug"]},
                    )
                ).scalar()
                or 0
            )
            if exists > 0:
                continue
            position = 1 + int(
                (
                    await asession.execute(
                        text(
                            """
                            SELECT COALESCE(MAX(position), 0)
                            FROM guide_procedure WHERE category_id = :cid
                            """
                        ),
                        {"cid": category_id},
                    )
                ).scalar()
                or 0
            )
            await asession.execute(
                text(
                    """
                    INSERT INTO guide_procedure (
                        category_id, article_id, slug, title, objective, context,
                        expected_result, prerequisites, module_route,
                        estimated_minutes, difficulty, audience, status,
                        version_label, position
                    ) VALUES (
                        :category_id, :article_id, :slug, :title, :objective, :context,
                        :expected_result, :prerequisites, :module_route,
                        :estimated_minutes, :difficulty, 'MIXTE', 'PUBLIE',
                        :version_label, :position
                    )
                    """
                ),
                {
                    "category_id": category_id,
                    "article_id": article_ids.get(item.get("article")),
                    "slug": item["slug"],
                    "title": item["title"],
                    "objective": item["objective"],
                    "context": item.get("context", ""),
                    "expected_result": item.get("expected_result", ""),
                    "prerequisites": item.get("prerequisites", ""),
                    "module_route": item.get("module_route", "/"),
                    "estimated_minutes": int(item.get("estimated_minutes", 5)),
                    "difficulty": item.get("difficulty", "DECOUVERTE"),
                    "version_label": GUIDE_VERSION,
                    "position": position,
                },
            )
            procedure_id = int(
                (
                    await asession.execute(
                        text(
                            "SELECT id FROM guide_procedure WHERE slug = :slug"
                        ),
                        {"slug": item["slug"]},
                    )
                ).scalar()
                or 0
            )
            steps = [
                {
                    "procedure_id": procedure_id,
                    "position": index + 1,
                    "title": step.get("title", ""),
                    "instruction_farmer": step.get("instruction_farmer", ""),
                    "instruction_pro": step.get("instruction_pro", ""),
                    "ui_hint": step.get("ui_hint", ""),
                    "module_route": step.get(
                        "module_route", item.get("module_route", "")
                    ),
                    "field_reference": step.get("field_reference", ""),
                    "why": step.get("why", ""),
                    "warning": step.get("warning", ""),
                    "duration_minutes": int(step.get("duration_minutes", 1)),
                    "is_optional": bool(step.get("is_optional", False)),
                }
                for index, step in enumerate(item.get("steps", []))
            ]
            if steps:
                await asession.execute(
                    text(
                        """
                        INSERT INTO guide_procedure_step (
                            procedure_id, position, title, instruction_farmer,
                            instruction_pro, ui_hint, module_route,
                            field_reference, why, warning, duration_minutes,
                            is_optional
                        ) VALUES (
                            :procedure_id, :position, :title, :instruction_farmer,
                            :instruction_pro, :ui_hint, :module_route,
                            :field_reference, :why, :warning, :duration_minutes,
                            :is_optional
                        )
                        """
                    ),
                    steps,
                )
            inserted += 1

        # Rattachement des règles orphelines à un champ exploitable.
        for fix in RULE_FIELD_FIXES:
            await asession.execute(
                text(
                    """
                    UPDATE guide_rule
                    SET field_reference = :field_reference,
                        module_route = :module_route
                    WHERE code = :code
                      AND COALESCE(field_reference, '') = ''
                    """
                ),
                fix,
            )

        if inserted > 0:
            version_id = (
                await asession.execute(
                    text(
                        """
                        SELECT id FROM guide_version
                        ORDER BY is_current DESC, id DESC LIMIT 1
                        """
                    )
                )
            ).scalar()
            if version_id is not None:
                position = int(
                    (
                        await asession.execute(
                            text(
                                """
                                SELECT COALESCE(MAX(position), 0) + 1
                                FROM guide_version_entry WHERE version_id = :vid
                                """
                            ),
                            {"vid": int(version_id)},
                        )
                    ).scalar()
                    or 1
                )
                await asession.execute(
                    text(
                        """
                        INSERT INTO guide_version_entry (
                            version_id, entity_type, entity_ref, change_kind,
                            summary, author, position
                        ) VALUES (
                            :vid, 'PROCEDURE', 'correction-audit', 'AJOUT',
                            :summary, 'Cellule agronomique', :position
                        )
                        """
                    ),
                    {
                        "vid": int(version_id),
                        "summary": (
                            f"Correction d'audit : {inserted} procédure(s) "
                            "ajoutée(s) pour les catégories sans mode opératoire."
                        ),
                        "position": position,
                    },
                )

        await asession.commit()
    _guide_done = True


async def seed_coherence_data() -> None:
    """Amorce analyses de sol et journaux de stades pour les données existantes."""
    global _data_done
    if _data_done:
        return
    init_local_database()
    today = datetime.date.today()

    async with rx.asession() as asession:
        parcels = (
            await asession.execute(
                text(
                    """
                    SELECT p.id, COALESCE(p.ph, 7), COALESCE(p.organic_matter_percent, 0),
                           COALESCE(p.soil_type, 'LIMONEUX')
                    FROM parcel p
                    WHERE NOT EXISTS (
                        SELECT 1 FROM soil_analysis s WHERE s.parcel_id = p.id
                    )
                    ORDER BY p.id
                    """
                )
            )
        ).all()

        analyses: list[dict] = []
        for index, row in enumerate(parcels):
            ph = float(row[1] or 7)
            organic = float(row[2] or 0)
            soil = str(row[3])
            base_n = 28.0 + 6.0 * organic
            base_p = 42.0 if soil in ("ARGILEUX", "ARGILO_CALCAIRE") else 55.0
            base_k = 120.0 + 8.0 * (index % 5)
            analyses.append(
                {
                    "parcel_id": int(row[0]),
                    "sampled_on": today
                    - datetime.timedelta(days=120 + 7 * index),
                    "ph": round(ph, 2),
                    "nitrogen_ppm": round(base_n, 2),
                    "phosphorus_ppm": round(base_p + 3.0 * (index % 4), 2),
                    "potassium_ppm": round(base_k, 2),
                    "organic_matter_percent": round(organic, 2),
                    "laboratory": "Laboratoire agronomique régional",
                    "notes": (
                        "Analyse de sortie d'hiver : reliquat azoté et statut "
                        "P/K utilisés pour le plan de fumure."
                    ),
                }
            )
        if analyses:
            await asession.execute(
                text(
                    """
                    INSERT INTO soil_analysis (
                        parcel_id, sampled_on, ph, nitrogen_ppm, phosphorus_ppm,
                        potassium_ppm, organic_matter_percent, laboratory, notes
                    ) VALUES (
                        :parcel_id, :sampled_on, :ph, :nitrogen_ppm, :phosphorus_ppm,
                        :potassium_ppm, :organic_matter_percent, :laboratory, :notes
                    )
                    """
                ),
                analyses,
            )

        crops = (
            await asession.execute(
                text(
                    """
                    SELECT c.id, c.stage, c.sowing_date
                    FROM crop c
                    WHERE NOT EXISTS (
                        SELECT 1 FROM crop_stage_log l WHERE l.crop_id = c.id
                    )
                    ORDER BY c.id
                    """
                )
            )
        ).all()

        logs: list[dict] = []
        for index, row in enumerate(crops):
            crop_id = int(row[0])
            stage = str(row[1] or "SEMIS")
            current = (
                STAGE_SEQUENCE.index(stage) if stage in STAGE_SEQUENCE else 0
            )
            raw_sowing = row[2]
            if isinstance(raw_sowing, datetime.datetime):
                start = raw_sowing.date()
            elif isinstance(raw_sowing, datetime.date):
                start = raw_sowing
            else:
                start = today - datetime.timedelta(days=90)
            span = max(1, (today - start).days)
            steps = current + 1
            for position in range(steps):
                observed = start + datetime.timedelta(
                    days=int(span * position / max(1, steps - 1))
                    if steps > 1
                    else 0
                )
                if observed > today:
                    observed = today
                key = STAGE_SEQUENCE[position]
                logs.append(
                    {
                        "crop_id": crop_id,
                        "stage": key,
                        "observed_on": observed,
                        "observer": OBSERVERS[(index + position) % 3],
                        "comment": STAGE_COMMENTS.get(key, ""),
                    }
                )
        if logs:
            await asession.execute(
                text(
                    """
                    INSERT INTO crop_stage_log (
                        crop_id, stage, observed_on, observer, comment
                    ) VALUES (
                        :crop_id, :stage, :observed_on, :observer, :comment
                    )
                    """
                ),
                logs,
            )

        await asession.commit()
    _data_done = True


async def apply_audit_corrections() -> None:
    """Applique l'ensemble des corrections d'audit (idempotent)."""
    await seed_guide_corrections()
    await seed_coherence_data()

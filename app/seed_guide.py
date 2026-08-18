"""Amorçage idempotent de la base de connaissances « Guide Agricole ».

Insère le référentiel éditorial complet (modules ciblés, catégories, articles en
double lecture agricole / AgriPro, procédures pas à pas, dictionnaire, FAQ,
règles « Pourquoi ? » et « Attention », parcours d'apprentissage, version
publiée et changelog) UNIQUEMENT si la table `guide_category` est vide.

Toutes les requêtes sont écrites en SQL brut via `rx.asession()`.
Les tables sont créées par l'initialisation SQLite locale existante
(`init_local_database`), aucune migration n'est touchée ici.
"""

from __future__ import annotations

import datetime

import reflex as rx
from sqlalchemy import text

from app.database import init_local_database

GUIDE_VERSION: str = "1.0.0"
GUIDE_AUTHOR: str = "Cellule agronomique"

# ---------------------------------------------------------------------------
# Modules applicatifs pouvant être ciblés par un contenu du guide
# ---------------------------------------------------------------------------

MODULES: list[dict[str, str | int]] = [
    {
        "key": "cockpit",
        "label": "Cockpit agronomique",
        "route": "/",
        "icon": "layout-dashboard",
        "description": "Vue instantanée des parcelles, alertes, météo et chantiers.",
        "position": 1,
    },
    {
        "key": "parcelles",
        "label": "Parcelles & cultures",
        "route": "/parcelles",
        "icon": "map",
        "description": "Fiches parcellaires, fiches culturales et stades phénologiques.",
        "position": 2,
    },
    {
        "key": "cartographie",
        "label": "Cartographie interactive",
        "route": "/cartographie",
        "icon": "map-pinned",
        "description": "Contours réels des îlots, sélection au clic et métadonnées de géométrie.",
        "position": 3,
    },
    {
        "key": "traitements",
        "label": "Traitements & récoltes",
        "route": "/traitements",
        "icon": "spray-can",
        "description": "Journal des interventions, intrants, stocks et rendements.",
        "position": 4,
    },
    {
        "key": "employes",
        "label": "Employés & compétences",
        "route": "/employes",
        "icon": "users-round",
        "description": "Registre du personnel, habilitations, disponibilités et affectations.",
        "position": 5,
    },
    {
        "key": "maintenance",
        "label": "Engins & maintenance",
        "route": "/maintenance",
        "icon": "wrench",
        "description": "Flotte, plans d'entretien, opérations et coûts atelier.",
        "position": 6,
    },
    {
        "key": "charges",
        "label": "Charges & dépenses",
        "route": "/charges",
        "icon": "coins",
        "description": "Types de dépenses, registre des charges et synthèses.",
        "position": 7,
    },
    {
        "key": "recherche",
        "label": "Recherche globale",
        "route": "/recherche",
        "icon": "radar",
        "description": "Balayage transversal de toutes les tables métier avec filtres de dates.",
        "position": 8,
    },
]

# ---------------------------------------------------------------------------
# Catégories thématiques du guide
# ---------------------------------------------------------------------------

CATEGORIES: list[dict[str, str | int]] = [
    {
        "key": "fondamentaux",
        "name": "Fondamentaux de l'exploitation",
        "tagline": "Comprendre la logique générale avant de saisir quoi que ce soit.",
        "description": (
            "Vocabulaire de base, enchaînement parcelle → culture → intervention → "
            "récolte → charge, et rôle de chaque module du cockpit."
        ),
        "icon": "compass",
        "color_hex": "#a3e635",
        "accent_hex": "#fbbf24",
        "module_route": "/",
        "position": 1,
    },
    {
        "key": "parcelles",
        "name": "Parcelles & cartographie",
        "tagline": "Décrire le foncier une fois, bien, pour tout le reste.",
        "description": (
            "Création des îlots, codes parcellaires, surfaces, sols, irrigation, "
            "coordonnées et contours cartographiques."
        ),
        "icon": "map",
        "color_hex": "#4ade80",
        "accent_hex": "#a3e635",
        "module_route": "/parcelles",
        "position": 2,
    },
    {
        "key": "cultures",
        "name": "Cultures & assolement",
        "tagline": "Une culture par campagne et par parcelle, suivie de bout en bout.",
        "description": (
            "Fiches culturales, variétés du référentiel, stades phénologiques, "
            "avancement et état sanitaire."
        ),
        "icon": "sprout",
        "color_hex": "#22c55e",
        "accent_hex": "#facc15",
        "module_route": "/parcelles",
        "position": 3,
    },
    {
        "key": "travaux",
        "name": "Travaux & chantiers",
        "tagline": "Planifier, réaliser, tracer chaque passage.",
        "description": (
            "Travail du sol, semis, observations, planification des chantiers et "
            "clôture des interventions."
        ),
        "icon": "clipboard-list",
        "color_hex": "#84cc16",
        "accent_hex": "#fb923c",
        "module_route": "/traitements",
        "position": 4,
    },
    {
        "key": "irrigation",
        "name": "Irrigation & bilan hydrique",
        "tagline": "Apporter la bonne dose au bon moment.",
        "description": (
            "Tours d'eau, réserve utile, ET0, volumes apportés et suivi des "
            "équipements d'irrigation."
        ),
        "icon": "droplets",
        "color_hex": "#38bdf8",
        "accent_hex": "#a3e635",
        "module_route": "/traitements",
        "position": 5,
    },
    {
        "key": "fertilisation",
        "name": "Fertilisation & sols",
        "tagline": "Nourrir la culture sans nourrir les pertes.",
        "description": (
            "Analyses de sol, plan de fumure, fractionnement des apports azotés, "
            "amendements et matière organique."
        ),
        "icon": "flask-conical",
        "color_hex": "#f59e0b",
        "accent_hex": "#a3e635",
        "module_route": "/traitements",
        "position": 6,
    },
    {
        "key": "phytosanitaire",
        "name": "Protection phytosanitaire",
        "tagline": "Tracer chaque traitement, respecter chaque délai.",
        "description": (
            "Seuils d'intervention, conditions d'application, ZNT, délais de "
            "rentrée et avant récolte, registre phytosanitaire."
        ),
        "icon": "shield-check",
        "color_hex": "#f97316",
        "accent_hex": "#fde68a",
        "module_route": "/traitements",
        "position": 7,
    },
    {
        "key": "stocks",
        "name": "Stocks & intrants",
        "tagline": "Le stock informatique doit refléter le local phyto.",
        "description": (
            "Entrées, sorties, inventaires, pertes, seuils de réapprovisionnement "
            "et valorisation du stock."
        ),
        "icon": "package",
        "color_hex": "#14b8a6",
        "accent_hex": "#a3e635",
        "module_route": "/traitements",
        "position": 8,
    },
    {
        "key": "materiel",
        "name": "Matériel & maintenance",
        "tagline": "Un engin entretenu est un chantier qui part à l'heure.",
        "description": (
            "Flotte, compteurs, plans d'entretien préventif, contrôles "
            "réglementaires et coûts d'atelier."
        ),
        "icon": "wrench",
        "color_hex": "#94a3b8",
        "accent_hex": "#fbbf24",
        "module_route": "/maintenance",
        "position": 9,
    },
    {
        "key": "personnel",
        "name": "Personnel & compétences",
        "tagline": "La bonne personne, habilitée, disponible.",
        "description": (
            "Contrats, habilitations (dont Certiphyto), disponibilités, "
            "affectations et heures réalisées."
        ),
        "icon": "users-round",
        "color_hex": "#c084fc",
        "accent_hex": "#a3e635",
        "module_route": "/employes",
        "position": 10,
    },
    {
        "key": "recolte",
        "name": "Récolte & rendements",
        "tagline": "Mesurer pour comparer, comparer pour progresser.",
        "description": (
            "Saisie des récoltes, humidité, pertes, qualité, rendement réalisé "
            "face au rendement visé et valorisation."
        ),
        "icon": "wheat",
        "color_hex": "#eab308",
        "accent_hex": "#a3e635",
        "module_route": "/traitements",
        "position": 11,
    },
    {
        "key": "economie",
        "name": "Gestion économique",
        "tagline": "Chaque euro rattaché à un actif devient une décision.",
        "description": (
            "Types de dépenses, charges opérationnelles et de structure, marge "
            "brute par parcelle et pilotage de trésorerie."
        ),
        "icon": "coins",
        "color_hex": "#fbbf24",
        "accent_hex": "#a3e635",
        "module_route": "/charges",
        "position": 12,
    },
]

# ---------------------------------------------------------------------------
# Articles en double lecture (agricole / AgriPro)
# ---------------------------------------------------------------------------

ARTICLES: list[dict] = [
    {
        "slug": "logique-generale-exploitation",
        "category": "fondamentaux",
        "title": "Comment l'application suit votre exploitation",
        "subtitle": "De la parcelle à la marge, une seule chaîne de données",
        "summary": (
            "La parcelle porte les cultures, la culture porte les interventions et "
            "les récoltes, et tout peut recevoir des dépenses."
        ),
        "body_farmer": (
            "Tout part de la parcelle : c'est le morceau de terre que vous "
            "reconnaissez sur le terrain, avec son nom et son code (P01, P02...). "
            "Sur cette parcelle, vous implantez une culture pour une campagne. "
            "Chaque passage sur la parcelle (travail du sol, semis, traitement, "
            "irrigation, observation) devient une intervention. Quand vous "
            "moissonnez, vous saisissez une récolte rattachée à la culture. Enfin, "
            "toutes les factures peuvent être rattachées à une parcelle, une "
            "culture, un engin ou un salarié.\n\n"
            "Si vous respectez cet ordre, tous les écrans se remplissent seuls : le "
            "cockpit, la carte, les rendements et les charges."
        ),
        "body_pro": (
            "Le modèle de données est hiérarchique : `parcel` (1) → `crop` (n) par "
            "campagne, `intervention` rattachée à la parcelle et éventuellement à la "
            "culture, `harvest` rattachée à la culture, `expense` rattachable à "
            "n'importe quel actif (parcelle, culture, salarié, engin, intervention, "
            "opération de maintenance).\n\n"
            "Les indicateurs agrégés (surface active, avancement moyen, coût sur "
            "30 jours, rendement moyen) sont recalculés par requête et non stockés : "
            "la qualité de la saisie détermine directement la fiabilité du pilotage."
        ),
        "audience": "MIXTE",
        "difficulty": "DECOUVERTE",
        "reading_minutes": 4,
        "keywords": "parcelle, culture, intervention, récolte, dépense, modèle",
        "tags": "fondamentaux, prise en main",
        "module_route": "/",
        "is_featured": True,
        "position": 1,
        "links": [
            (
                "Ouvrir le cockpit",
                "cockpit",
                "Vérifier les indicateurs consolidés.",
            ),
            ("Ouvrir les parcelles", "parcelles", "Créer le premier îlot."),
        ],
    },
    {
        "slug": "vocabulaire-de-base",
        "category": "fondamentaux",
        "title": "Le vocabulaire indispensable",
        "subtitle": "Îlot, campagne, itinéraire technique, stade, marge brute",
        "summary": "Les dix mots qui reviennent dans tous les écrans, expliqués simplement.",
        "body_farmer": (
            "Îlot : votre parcelle telle qu'elle est déclarée. Campagne : l'année "
            "culturale (souvent semis d'automne à récolte d'été). Itinéraire "
            "technique : la suite des travaux prévus sur une culture. Stade : où en "
            "est la plante (levée, floraison, maturation). Marge brute : ce qui "
            "reste de la vente une fois les charges directes payées."
        ),
        "body_pro": (
            "Îlot ≈ unité de gestion cadastrale/PAC ; campagne = millésime de "
            "référence stocké dans `crop.season` ; itinéraire technique = séquence "
            "d'`intervention` typées ; stade = échelle phénologique simplifiée "
            "(`crop.stage`) historisée dans `crop_stage_log` ; marge brute = produit "
            "(`harvest.revenue`) − charges opérationnelles affectées (`expense`, "
            "`intervention.cost`)."
        ),
        "audience": "MIXTE",
        "difficulty": "DECOUVERTE",
        "reading_minutes": 3,
        "keywords": "vocabulaire, îlot, campagne, stade, marge brute",
        "tags": "fondamentaux, dictionnaire",
        "module_route": "/",
        "is_featured": False,
        "position": 2,
        "links": [
            (
                "Rechercher un terme",
                "recherche",
                "Retrouver une instance dans toutes les tables.",
            ),
        ],
    },
    {
        "slug": "creer-une-parcelle",
        "category": "parcelles",
        "title": "Créer et décrire une parcelle",
        "subtitle": "Code, surface, sol, irrigation : la fiche qui sert partout",
        "summary": "Une fiche parcellaire propre évite des dizaines de corrections plus tard.",
        "body_farmer": (
            "Donnez un nom que vous utilisez sur le terrain (« Les Grands Champs ») "
            "et un code court unique (P08). Saisissez la surface exploitée réelle, "
            "pas la surface cadastrale si elle diffère. Choisissez le type de sol "
            "dominant et le mode d'irrigation. Ajoutez la localité et, si vous les "
            "connaissez, la latitude et la longitude : la carte se positionnera "
            "toute seule."
        ),
        "body_pro": (
            "Champs structurants : `code` (clé de lecture humaine, unique), "
            "`area_ha` (base de tous les ratios /ha), `soil_type`, `irrigation`, "
            "`status`. Les valeurs agronomiques (`ph`, `organic_matter_percent`, "
            "`slope_percent`) alimentent les recommandations de fumure et le risque "
            "de ruissellement. `latitude`/`longitude` amorcent la géométrie "
            "cartographique si aucun contour n'est encore tracé."
        ),
        "audience": "MIXTE",
        "difficulty": "DECOUVERTE",
        "reading_minutes": 4,
        "keywords": "parcelle, code, surface, sol, irrigation, ph",
        "tags": "parcelles, saisie",
        "module_route": "/parcelles",
        "is_featured": True,
        "position": 1,
        "links": [
            (
                "Ouvrir les parcelles",
                "parcelles",
                "Créer ou modifier une fiche parcellaire.",
            ),
            (
                "Ouvrir la cartographie",
                "cartographie",
                "Vérifier le contour de l'îlot.",
            ),
        ],
    },
    {
        "slug": "contours-cartographiques",
        "category": "parcelles",
        "title": "Comprendre les contours cartographiques",
        "subtitle": "Contour généré, contour enregistré, surface calculée",
        "summary": "Pourquoi la surface calculée depuis le contour peut différer de la surface déclarée.",
        "body_farmer": (
            "Au démarrage, l'application dessine un contour approximatif autour du "
            "point de la parcelle pour que vous voyiez quelque chose sur la carte. "
            "Ce contour est affiché en pointillés : il n'est pas fiable pour un "
            "calcul de surface. Dès que vous enregistrez un vrai contour, il "
            "s'affiche en trait plein et la surface calculée apparaît."
        ),
        "body_pro": (
            "Le contour est stocké en GeoJSON texte (`boundary_geojson`, SRID 4326) "
            "avec centre, bbox, nombre de sommets, surface calculée "
            "(`geometry_area_ha`) et origine (`geometry_source` : AUCUNE, GENEREE, "
            "DESSINEE, IMPORTEE, CADASTRE). Un écart supérieur à 5 % entre "
            "`geometry_area_ha` et `area_ha` doit être arbitré : soit le contour est "
            "incomplet, soit la surface déclarée est obsolète."
        ),
        "audience": "AGRIPRO",
        "difficulty": "INTERMEDIAIRE",
        "reading_minutes": 5,
        "keywords": "géométrie, geojson, contour, surface, srid",
        "tags": "cartographie, géomatique",
        "module_route": "/cartographie",
        "is_featured": False,
        "position": 2,
        "links": [
            (
                "Ouvrir la cartographie",
                "cartographie",
                "Sélectionner un îlot et lire sa géométrie.",
            ),
        ],
    },
    {
        "slug": "implanter-une-culture",
        "category": "cultures",
        "title": "Implanter une culture sur une parcelle",
        "subtitle": "Variété, campagne, surface implantée, rendement visé",
        "summary": "La fiche culturale relie la variété du référentiel à une parcelle et une campagne.",
        "body_farmer": (
            "Choisissez d'abord la parcelle, puis créez la culture : nom parlant "
            "(« Blé tendre Rubisko »), campagne, surface réellement implantée et "
            "date de semis. Reliez si possible la variété du référentiel : vous "
            "récupérez alors sa couleur sur la carte, son cycle et son rendement "
            "habituel."
        ),
        "body_pro": (
            "`crop.area_ha` ne peut excéder `parcel.area_ha` (contrôle bloquant). "
            "`variety_id` apporte `cycle_days`, `expected_yield_t_ha` et "
            "`color_hex`, réutilisés pour l'assolement graphique et le calcul de "
            "performance de récolte. Renseigner `expected_harvest_date` alimente le "
            "calendrier des chantiers et les alertes d'échéance."
        ),
        "audience": "MIXTE",
        "difficulty": "DECOUVERTE",
        "reading_minutes": 4,
        "keywords": "culture, variété, semis, campagne, rendement visé",
        "tags": "cultures, saisie",
        "module_route": "/parcelles",
        "is_featured": True,
        "position": 1,
        "links": [
            ("Ouvrir les cultures", "parcelles", "Créer une fiche culturale."),
        ],
    },
    {
        "slug": "suivre-les-stades",
        "category": "cultures",
        "title": "Suivre les stades phénologiques",
        "subtitle": "Du semis à la récolte, un historique qui explique les décisions",
        "summary": "Chaque changement de stade est daté et signé : c'est la mémoire de la campagne.",
        "body_farmer": (
            "À chaque tour de plaine, notez le stade observé et qui l'a observé. "
            "L'application garde l'historique : vous pourrez expliquer pourquoi vous "
            "avez traité ce jour-là plutôt qu'un autre."
        ),
        "body_pro": (
            "Le stade courant (`crop.stage`) est doublé d'un journal "
            "(`crop_stage_log`) contenant stade, date d'observation, observateur et "
            "commentaire. Ce journal sert de preuve de positionnement pour les "
            "interventions à stade réglementé (régulateurs, fongicides épis) et "
            "permet de recalculer des sommes de températures a posteriori."
        ),
        "audience": "MIXTE",
        "difficulty": "INTERMEDIAIRE",
        "reading_minutes": 3,
        "keywords": "stade, phénologie, observation, journal",
        "tags": "cultures, observation",
        "module_route": "/parcelles",
        "is_featured": False,
        "position": 2,
        "links": [
            (
                "Ouvrir le suivi des stades",
                "parcelles",
                "Consigner une observation.",
            ),
        ],
    },
    {
        "slug": "planifier-un-chantier",
        "category": "travaux",
        "title": "Planifier et clôturer un chantier",
        "subtitle": "Une intervention planifiée, réalisée puis tracée",
        "summary": "Le journal des interventions est la colonne vertébrale de la traçabilité.",
        "body_farmer": (
            "Créez l'intervention avant le passage : type de travaux, parcelle, "
            "date prévue, opérateur et matériel. Après le passage, marquez-la "
            "réalisée : la date de réalisation est enregistrée et les intrants "
            "prévus sortent automatiquement du stock."
        ),
        "body_pro": (
            "`intervention.status` suit le cycle PLANIFIEE → EN_COURS → REALISEE, "
            "avec REPORTEE et ANNULEE comme sorties. La clôture déclenche un "
            "`stock_movement` de type SORTIE pour chaque `intervention_product` et "
            "décrémente `product.quantity_in_stock` sans jamais passer sous zéro. "
            "`area_treated_ha` × `dose_per_ha` donne la quantité totale appliquée."
        ),
        "audience": "MIXTE",
        "difficulty": "DECOUVERTE",
        "reading_minutes": 4,
        "keywords": "intervention, chantier, planification, clôture, stock",
        "tags": "travaux, traçabilité",
        "module_route": "/traitements",
        "is_featured": True,
        "position": 1,
        "links": [
            (
                "Ouvrir le journal",
                "traitements",
                "Planifier ou clôturer une intervention.",
            ),
            (
                "Voir le calendrier",
                "cockpit",
                "Contrôler la charge de travail de la semaine.",
            ),
        ],
    },
    {
        "slug": "travail-du-sol",
        "category": "travaux",
        "title": "Travail du sol et lit de semence",
        "subtitle": "Portance, ressuyage, profondeur",
        "summary": "Intervenir sur un sol ressuyé évite le tassement et les faux départs.",
        "body_farmer": (
            "Avant de sortir la herse, vérifiez que le sol est ressuyé : une poignée "
            "de terre qui colle et se lisse annonce du tassement. Notez la durée "
            "réelle du chantier, elle sert à calculer le coût de passage."
        ),
        "body_pro": (
            "Consigner `duration_hours` et `area_treated_ha` permet de calculer un "
            "débit de chantier (ha/h) et un coût de passage (€/ha) via "
            "`intervention.cost`. Croisé avec `equipment_usage_log` (heures et "
            "carburant), l'écart révèle les pertes de temps logistiques."
        ),
        "audience": "MIXTE",
        "difficulty": "INTERMEDIAIRE",
        "reading_minutes": 3,
        "keywords": "travail du sol, ressuyage, tassement, débit de chantier",
        "tags": "travaux, agronomie",
        "module_route": "/traitements",
        "is_featured": False,
        "position": 2,
        "links": [
            (
                "Ouvrir le journal",
                "traitements",
                "Enregistrer un passage d'outil.",
            ),
        ],
    },
    {
        "slug": "piloter-irrigation",
        "category": "irrigation",
        "title": "Piloter un tour d'eau",
        "subtitle": "Réserve utile, ET0 et volume apporté",
        "summary": "Un tour d'eau se déclenche sur un indicateur, pas sur une impression.",
        "body_farmer": (
            "Regardez la réserve d'eau du sol et la pluie des jours passés. Si les "
            "sondes descendent trop bas, déclenchez le tour d'eau et notez le volume "
            "apporté par hectare. Vous saurez ensuite combien d'eau la culture a "
            "réellement reçu."
        ),
        "body_pro": (
            "Le déclenchement s'appuie sur la tension hydrique (kPa) ou le bilan "
            "hydrique : RU restante = RU initiale + pluies + irrigations − ET0 × Kc. "
            "Le champ `water_volume_l_ha` de l'intervention cumule les apports "
            "campagne et permet de calculer une efficience (t de grain par mm "
            "apporté)."
        ),
        "audience": "MIXTE",
        "difficulty": "INTERMEDIAIRE",
        "reading_minutes": 5,
        "keywords": "irrigation, réserve utile, et0, kc, tour d'eau",
        "tags": "irrigation, bilan hydrique",
        "module_route": "/traitements",
        "is_featured": True,
        "position": 1,
        "links": [
            ("Ouvrir le journal", "traitements", "Enregistrer un tour d'eau."),
            (
                "Voir la météo",
                "cockpit",
                "Contrôler pluie et ET0 de la semaine.",
            ),
        ],
    },
    {
        "slug": "plan-de-fumure",
        "category": "fertilisation",
        "title": "Construire un plan de fumure",
        "subtitle": "Analyse de sol, objectif de rendement, fractionnement",
        "summary": "L'azote se raisonne par bilan et se fractionne selon les stades.",
        "body_farmer": (
            "Partez de l'analyse de sol et de votre objectif de rendement. Divisez "
            "l'azote en plusieurs apports : un petit au démarrage, les plus gros "
            "quand la plante pousse vite. Notez chaque apport comme une "
            "intervention de fertilisation."
        ),
        "body_pro": (
            "Méthode du bilan : besoins (objectif × besoin unitaire) − fournitures "
            "du sol (reliquat, minéralisation de l'humus, arrière-effets) = dose "
            "prévisionnelle, fractionnée selon le stade. Les analyses sont stockées "
            "dans `soil_analysis` (pH, N/P/K, matière organique) et les apports dans "
            "`intervention` de type FERTILISATION avec produit et dose/ha."
        ),
        "audience": "AGRIPRO",
        "difficulty": "AVANCE",
        "reading_minutes": 6,
        "keywords": "fumure, azote, bilan, analyse de sol, fractionnement",
        "tags": "fertilisation, agronomie",
        "module_route": "/traitements",
        "is_featured": True,
        "position": 1,
        "links": [
            (
                "Ouvrir le journal",
                "traitements",
                "Saisir un apport de fertilisation.",
            ),
            (
                "Ouvrir la parcelle",
                "parcelles",
                "Vérifier pH et matière organique.",
            ),
        ],
    },
    {
        "slug": "registre-phytosanitaire",
        "category": "phytosanitaire",
        "title": "Tenir un registre phytosanitaire irréprochable",
        "subtitle": "Cible, dose, conditions, délais",
        "summary": "Chaque traitement doit être justifié, daté et complet dans le journal.",
        "body_farmer": (
            "Notez toujours : la cible visée, le produit, la dose par hectare, la "
            "surface traitée, la date et les conditions (vent, température). Sans "
            "ces informations, le traitement n'est pas traçable en cas de contrôle."
        ),
        "body_pro": (
            "Le registre repose sur `intervention` (type TRAITEMENT_PHYTO) + "
            "`intervention_product` (dose/ha, quantité totale, unité, coût). "
            "Contrôlez la conformité : vent < 19 km/h, respect des ZNT, délai de "
            "rentrée (`product.reentry_delay_hours`) et délai avant récolte "
            "(`preharvest_delay_days`) compatible avec "
            "`crop.expected_harvest_date`."
        ),
        "audience": "MIXTE",
        "difficulty": "INTERMEDIAIRE",
        "reading_minutes": 5,
        "keywords": "phytosanitaire, registre, znt, délai de rentrée, dar",
        "tags": "phytosanitaire, réglementaire",
        "module_route": "/traitements",
        "is_featured": True,
        "position": 1,
        "links": [
            (
                "Ouvrir le journal",
                "traitements",
                "Créer un traitement traçable.",
            ),
            (
                "Ouvrir les habilitations",
                "employes",
                "Vérifier le Certiphyto de l'applicateur.",
            ),
        ],
    },
    {
        "slug": "gerer-le-stock-intrants",
        "category": "stocks",
        "title": "Garder un stock d'intrants fiable",
        "subtitle": "Entrée, sortie, inventaire, perte",
        "summary": "Quatre types de mouvements suffisent à expliquer tout écart de stock.",
        "body_farmer": (
            "Une livraison = une entrée. Un traitement = une sortie (souvent "
            "automatique). Un comptage dans le local = un inventaire, qui remet le "
            "chiffre à la valeur réelle. Un bidon percé = une perte, à déclarer pour "
            "que les comptes restent justes."
        ),
        "body_pro": (
            "`stock_movement.type` ∈ {ENTREE, SORTIE, INVENTAIRE, PERTE}. ENTREE "
            "incrémente, SORTIE et PERTE décrémentent avec plancher à zéro, "
            "INVENTAIRE écrase la quantité. Le seuil "
            "`product.reorder_threshold` déclenche l'affichage critique ; la "
            "valorisation du stock = Σ quantité × prix unitaire."
        ),
        "audience": "MIXTE",
        "difficulty": "DECOUVERTE",
        "reading_minutes": 4,
        "keywords": "stock, mouvement, inventaire, seuil, valorisation",
        "tags": "stocks, intrants",
        "module_route": "/traitements",
        "is_featured": False,
        "position": 1,
        "links": [
            ("Ouvrir les stocks", "traitements", "Enregistrer un mouvement."),
        ],
    },
    {
        "slug": "entretien-preventif",
        "category": "materiel",
        "title": "Organiser l'entretien préventif",
        "subtitle": "Échéance calendaire, échéance compteur, échéance mixte",
        "summary": "Un plan d'entretien évite la panne au pire moment de la campagne.",
        "body_farmer": (
            "Pour chaque engin, définissez ce qu'il faut faire et à quel rythme : "
            "tous les six mois, toutes les 500 heures, ou les deux. L'application "
            "vous prévient quand l'échéance approche ou est dépassée."
        ),
        "body_pro": (
            "`maintenance_schedule.trigger_basis` ∈ {CALENDRIER, COMPTEUR, MIXTE} "
            "avec `interval_days`, `interval_counter` et `tolerance_days`. Le "
            "dépassement se calcule en comparant `next_due_on` à la date du jour et "
            "`next_due_counter` à `equipment.usage_counter`, alimenté par "
            "`equipment_usage_log`."
        ),
        "audience": "MIXTE",
        "difficulty": "INTERMEDIAIRE",
        "reading_minutes": 5,
        "keywords": "maintenance, préventif, compteur, échéance, vgp",
        "tags": "matériel, atelier",
        "module_route": "/maintenance",
        "is_featured": True,
        "position": 1,
        "links": [
            (
                "Ouvrir la maintenance",
                "maintenance",
                "Créer un plan d'entretien.",
            ),
        ],
    },
    {
        "slug": "habilitations-equipe",
        "category": "personnel",
        "title": "Affecter la bonne personne au bon chantier",
        "subtitle": "Compétence, habilitation, disponibilité",
        "summary": "Une affectation valide croise compétence, habilitation à jour et disponibilité.",
        "body_farmer": (
            "Avant d'affecter quelqu'un, vérifiez trois choses : sait-il faire, a-t-il "
            "le papier obligatoire s'il en faut un, et est-il disponible ce jour-là. "
            "Les congés et arrêts sont visibles dans le planning."
        ),
        "body_pro": (
            "Croisez `employee_skill` (niveau, expérience, expiration de "
            "certification), `employee_availability` (type DISPONIBLE/CONGE/ARRET/"
            "FORMATION/ASTREINTE) et `assignment` (rôle, heures prévues et "
            "réalisées). Une habilitation expirée doit bloquer l'affectation sur les "
            "chantiers réglementés (application phytosanitaire notamment)."
        ),
        "audience": "MIXTE",
        "difficulty": "INTERMEDIAIRE",
        "reading_minutes": 4,
        "keywords": "personnel, compétence, certiphyto, disponibilité, affectation",
        "tags": "personnel, organisation",
        "module_route": "/employes",
        "is_featured": False,
        "position": 1,
        "links": [
            (
                "Ouvrir les employés",
                "employes",
                "Consulter la matrice de compétences.",
            ),
        ],
    },
    {
        "slug": "saisir-une-recolte",
        "category": "recolte",
        "title": "Saisir une récolte et lire son rendement",
        "subtitle": "Quantité, surface, humidité, qualité",
        "summary": "Le rendement se calcule seul dès que quantité et surface sont exactes.",
        "body_farmer": (
            "Notez la quantité récoltée, la surface effectivement moissonnée, "
            "l'humidité et la qualité. Le rendement par hectare est calculé "
            "automatiquement, puis comparé au rendement que vous visiez."
        ),
        "body_pro": (
            "`yield_t_ha` = quantité / surface récoltée. La performance affichée est "
            "le rapport au `crop.expected_yield_t_ha`. Pensez à normaliser à "
            "l'humidité de référence (par exemple 15 % en blé) avant toute "
            "comparaison pluriannuelle ; renseignez `loss_percent` pour distinguer "
            "pertes au champ et pertes de stockage."
        ),
        "audience": "MIXTE",
        "difficulty": "DECOUVERTE",
        "reading_minutes": 4,
        "keywords": "récolte, rendement, humidité, qualité, pertes",
        "tags": "récolte, mesure",
        "module_route": "/traitements",
        "is_featured": True,
        "position": 1,
        "links": [
            ("Ouvrir les récoltes", "traitements", "Saisir une récolte."),
        ],
    },
    {
        "slug": "charges-et-marge",
        "category": "economie",
        "title": "Rattacher les charges pour obtenir une marge",
        "subtitle": "Type de dépense, actif rattaché, statut de paiement",
        "summary": "Une dépense rattachée à une parcelle devient un coût à l'hectare.",
        "body_farmer": (
            "Chaque facture se saisit une fois : type de dépense, montant, "
            "fournisseur, date. Rattachez-la à ce qu'elle concerne (parcelle, "
            "culture, engin, salarié) : vous verrez ensuite le coût réel de chaque "
            "îlot."
        ),
        "body_pro": (
            "`expense` porte `amount_ht`, `vat_rate`, `amount_ttc`, un `status` "
            "(BROUILLON, ENGAGEE, PAYEE, ANNULEE) et jusqu'à six rattachements "
            "(parcelle, culture, salarié, engin, intervention, maintenance). Marge "
            "brute par îlot = Σ `harvest.revenue` − Σ charges opérationnelles "
            "rattachées, ramenée à `parcel.area_ha`."
        ),
        "audience": "MIXTE",
        "difficulty": "INTERMEDIAIRE",
        "reading_minutes": 5,
        "keywords": "charges, dépense, tva, marge brute, coût à l'hectare",
        "tags": "économie, gestion",
        "module_route": "/charges",
        "is_featured": True,
        "position": 1,
        "links": [
            (
                "Ouvrir les charges",
                "charges",
                "Créer un type de dépense ou une dépense.",
            ),
            (
                "Ouvrir les récoltes",
                "traitements",
                "Contrôler le produit de la campagne.",
            ),
        ],
    },
    {
        "slug": "lire-le-cockpit",
        "category": "fondamentaux",
        "title": "Lire le cockpit en trente secondes",
        "subtitle": "Alertes d'abord, météo ensuite, chantiers pour finir",
        "summary": "Un ordre de lecture simple pour décider vite le matin.",
        "body_farmer": (
            "Commencez par les alertes critiques : elles demandent une décision dans "
            "les 24 heures. Regardez ensuite la météo et la fenêtre de traitement. "
            "Terminez par le calendrier : ce qui est prévu aujourd'hui et cette "
            "semaine."
        ),
        "body_pro": (
            "Les indicateurs sont recalculés à chaque chargement : surface active, "
            "avancement moyen des cultures EN_COURS, alertes non résolues, chantiers "
            "planifiés à 7 jours, quantité récoltée et produit cumulé. La fenêtre de "
            "traitement combine vent (< 19 km/h) et pluie attendue (< 2 mm)."
        ),
        "audience": "MIXTE",
        "difficulty": "DECOUVERTE",
        "reading_minutes": 3,
        "keywords": "cockpit, alerte, météo, calendrier, indicateurs",
        "tags": "fondamentaux, pilotage",
        "module_route": "/",
        "is_featured": False,
        "position": 3,
        "links": [
            ("Ouvrir le cockpit", "cockpit", "Lire les indicateurs du jour."),
        ],
    },
]

# ---------------------------------------------------------------------------
# Procédures interactives pas à pas
# ---------------------------------------------------------------------------

PROCEDURES: list[dict] = [
    {
        "slug": "proc-creer-parcelle",
        "category": "parcelles",
        "article": "creer-une-parcelle",
        "title": "Créer une parcelle de A à Z",
        "objective": "Obtenir une fiche parcellaire exploitable par tous les modules.",
        "context": "À faire une seule fois par îtinéraire foncier, puis à corriger si la surface change.",
        "expected_result": "La parcelle apparaît dans la liste, sur la carte et dans les filtres.",
        "prerequisites": "Connaître le code d'îlot, la surface exploitée et la localité.",
        "module_route": "/parcelles",
        "estimated_minutes": 6,
        "difficulty": "DECOUVERTE",
        "position": 1,
        "steps": [
            {
                "title": "Ouvrir le formulaire de parcelle",
                "instruction_farmer": "Allez dans « Parcelles & cultures » et cliquez sur la création de parcelle.",
                "instruction_pro": "Écran /parcelles, action d'ouverture du modal de fiche parcellaire.",
                "ui_hint": "Bouton de création en tête de la liste des îlots.",
                "field_reference": "parcel",
                "why": "Le formulaire contrôle les valeurs à la saisie et évite les doublons de code.",
                "warning": "",
                "duration_minutes": 1,
            },
            {
                "title": "Saisir identité et surface",
                "instruction_farmer": "Nom parlant, code court unique (P08) et surface réellement exploitée.",
                "instruction_pro": "`name` ≥ 2 caractères, `code` unique, `area_ha` > 0 et ≤ 5000.",
                "ui_hint": "Trois premiers champs du formulaire.",
                "field_reference": "parcel.code, parcel.area_ha",
                "why": "La surface sert de base à tous les ratios /ha : dose, coût, rendement.",
                "warning": "Une surface fausse faussera toutes les doses et tous les coûts à l'hectare.",
                "duration_minutes": 2,
            },
            {
                "title": "Décrire sol et irrigation",
                "instruction_farmer": "Choisissez le sol dominant, le mode d'irrigation et le statut de la parcelle.",
                "instruction_pro": "`soil_type`, `irrigation`, `status` ; renseigner `ph` et matière organique si connus.",
                "ui_hint": "Listes déroulantes du bloc agronomique.",
                "field_reference": "parcel.soil_type, parcel.ph",
                "why": "Le sol conditionne la réserve utile, le ressuyage et le raisonnement de fumure.",
                "warning": "",
                "duration_minutes": 2,
            },
            {
                "title": "Positionner la parcelle",
                "instruction_farmer": "Ajoutez latitude et longitude, ou la position sur la carte d'assolement.",
                "instruction_pro": "`latitude`/`longitude` (WGS84) amorcent la géométrie ; `map_x/y/w/h` pilotent la carte stylisée.",
                "ui_hint": "Bloc « Position sur la carte d'assolement ».",
                "module_route": "/cartographie",
                "field_reference": "parcel.latitude, parcel.longitude",
                "why": "Sans coordonnées, le contour cartographique reste approximatif et en pointillés.",
                "warning": "",
                "duration_minutes": 1,
                "is_optional": True,
            },
            {
                "title": "Enregistrer et vérifier",
                "instruction_farmer": "Enregistrez, puis vérifiez la fiche et la carte.",
                "instruction_pro": "Contrôler l'écart entre `geometry_area_ha` et `area_ha` après amorçage du contour.",
                "ui_hint": "Fiche détaillée à droite de la liste.",
                "module_route": "/cartographie",
                "field_reference": "parcel.geometry_area_ha",
                "why": "Le contrôle immédiat évite de propager une erreur sur toute la campagne.",
                "warning": "Un écart de surface supérieur à 5 % doit être arbitré tout de suite.",
                "duration_minutes": 1,
            },
        ],
    },
    {
        "slug": "proc-traitement-conforme",
        "category": "phytosanitaire",
        "article": "registre-phytosanitaire",
        "title": "Enregistrer un traitement conforme",
        "objective": "Produire une ligne de registre complète et défendable en contrôle.",
        "context": "À chaque application de produit phytopharmaceutique.",
        "expected_result": "Intervention réalisée, produit sorti du stock, registre complet.",
        "prerequisites": "Applicateur habilité, produit en stock, seuil d'intervention atteint.",
        "module_route": "/traitements",
        "estimated_minutes": 8,
        "difficulty": "INTERMEDIAIRE",
        "position": 1,
        "steps": [
            {
                "title": "Vérifier la justification",
                "instruction_farmer": "Notez ce que vous avez observé : la cible et son niveau de présence.",
                "instruction_pro": "Documenter le seuil atteint dans `target` et `notes` ; s'appuyer sur le journal de stades.",
                "ui_hint": "Champs « Cible » et « Observations » du formulaire d'intervention.",
                "field_reference": "intervention.target",
                "why": "Un traitement sans justification agronomique est un coût et un risque de résistance.",
                "warning": "",
                "duration_minutes": 2,
            },
            {
                "title": "Contrôler l'habilitation",
                "instruction_farmer": "Assurez-vous que l'applicateur a son certificat en cours de validité.",
                "instruction_pro": "Vérifier `employee.has_phyto_certificate` et `phyto_certificate_expiry`.",
                "ui_hint": "Fiche salarié, bloc habilitations.",
                "module_route": "/employes",
                "field_reference": "employee.phyto_certificate_expiry",
                "why": "L'application par une personne non habilitée est une infraction.",
                "warning": "Certificat expiré : l'affectation doit être refusée.",
                "duration_minutes": 1,
            },
            {
                "title": "Renseigner produit et dose",
                "instruction_farmer": "Choisissez le produit, la dose par hectare et la surface traitée.",
                "instruction_pro": "`intervention_product.dose_per_ha` × `area_treated_ha` = quantité totale ; comparer à la dose homologuée.",
                "ui_hint": "Bloc intrant du formulaire d'intervention.",
                "field_reference": "intervention_product.dose_per_ha",
                "why": "La quantité totale conditionne la sortie de stock et le coût réel du passage.",
                "warning": "Ne jamais dépasser la dose homologuée, même en rattrapage.",
                "duration_minutes": 2,
            },
            {
                "title": "Consigner les conditions",
                "instruction_farmer": "Notez vent, température et état du ciel au moment du passage.",
                "instruction_pro": "`wind_speed_kmh`, `temperature_c`, `weather_conditions` ; refuser au-delà de 19 km/h.",
                "ui_hint": "Bloc conditions météo du formulaire.",
                "field_reference": "intervention.wind_speed_kmh",
                "why": "La dérive dépend du vent : c'est la première question posée en contrôle.",
                "warning": "Vent supérieur à 19 km/h : reporter le chantier.",
                "duration_minutes": 1,
            },
            {
                "title": "Clôturer et vérifier le stock",
                "instruction_farmer": "Marquez l'intervention réalisée, puis contrôlez le stock du produit.",
                "instruction_pro": "La clôture crée un `stock_movement` SORTIE et décrémente `product.quantity_in_stock`.",
                "ui_hint": "Action « réalisée » sur la ligne du journal.",
                "field_reference": "stock_movement",
                "why": "Le stock informatique doit toujours refléter le local phyto.",
                "warning": "Vérifiez ensuite le délai avant récolte face à la date de moisson prévue.",
                "duration_minutes": 2,
            },
        ],
    },
    {
        "slug": "proc-saisir-recolte",
        "category": "recolte",
        "article": "saisir-une-recolte",
        "title": "Saisir une récolte et clôturer la culture",
        "objective": "Obtenir un rendement fiable et clore proprement la campagne de la parcelle.",
        "context": "Au fur et à mesure des bennes, ou en fin de chantier.",
        "expected_result": "Récolte enregistrée, rendement calculé, culture passée en RECOLTEE.",
        "prerequisites": "Pesées disponibles, surface moissonnée connue, humidité mesurée.",
        "module_route": "/traitements",
        "estimated_minutes": 5,
        "difficulty": "DECOUVERTE",
        "position": 1,
        "steps": [
            {
                "title": "Choisir la culture récoltée",
                "instruction_farmer": "Sélectionnez la culture concernée, pas seulement la parcelle.",
                "instruction_pro": "`harvest.crop_id` : la récolte est rattachée à la culture pour comparer au rendement visé.",
                "ui_hint": "Première liste du formulaire de récolte.",
                "field_reference": "harvest.crop_id",
                "why": "Sans culture, impossible de comparer réalisé et objectif.",
                "warning": "",
                "duration_minutes": 1,
            },
            {
                "title": "Saisir quantité et surface",
                "instruction_farmer": "Quantité totale récoltée et surface réellement moissonnée.",
                "instruction_pro": "Rendement = quantité / `area_harvested_ha` ; les deux doivent être > 0.",
                "ui_hint": "Champs quantité, unité et surface récoltée.",
                "field_reference": "harvest.area_harvested_ha",
                "why": "Le rendement est calculé, jamais saisi : il ne peut être juste que si ces deux valeurs le sont.",
                "warning": "Ne comptez pas la surface non moissonnée (tournières abîmées, zones grêlées).",
                "duration_minutes": 2,
            },
            {
                "title": "Qualité, humidité, pertes",
                "instruction_farmer": "Notez l'humidité, la qualité et les pertes estimées.",
                "instruction_pro": "Normaliser à l'humidité de référence avant comparaison pluriannuelle ; `loss_percent` isole les pertes.",
                "ui_hint": "Bloc qualité du formulaire.",
                "field_reference": "harvest.moisture_percent",
                "why": "Deux récoltes à humidités différentes ne sont pas comparables telles quelles.",
                "warning": "",
                "duration_minutes": 1,
            },
            {
                "title": "Valoriser et clôturer",
                "instruction_farmer": "Indiquez le prix unitaire, puis cochez la clôture de la culture si le chantier est fini.",
                "instruction_pro": "`revenue` = quantité × prix ; la clôture passe `crop.status` à RECOLTEE et fixe `actual_harvest_date`.",
                "ui_hint": "Case de clôture en bas du formulaire.",
                "field_reference": "crop.status",
                "why": "Une culture clôturée sort des indicateurs de cultures en cours et fiabilise le cockpit.",
                "warning": "Ne clôturez pas s'il reste des hectares à moissonner.",
                "duration_minutes": 1,
            },
        ],
    },
    {
        "slug": "proc-mouvement-stock",
        "category": "stocks",
        "article": "gerer-le-stock-intrants",
        "title": "Régulariser un stock après inventaire",
        "objective": "Aligner le stock informatique sur le comptage physique du local.",
        "context": "À chaque inventaire trimestriel ou après un écart constaté.",
        "expected_result": "Quantité en stock égale au comptage, écart documenté.",
        "prerequisites": "Comptage physique réalisé et daté.",
        "module_route": "/traitements",
        "estimated_minutes": 4,
        "difficulty": "DECOUVERTE",
        "position": 1,
        "steps": [
            {
                "title": "Compter puis comparer",
                "instruction_farmer": "Comptez ce qui est réellement dans le local et comparez à l'écran.",
                "instruction_pro": "Écart = comptage − `product.quantity_in_stock` ; qualifier la cause avant de corriger.",
                "ui_hint": "Colonne stock de la liste des produits.",
                "field_reference": "product.quantity_in_stock",
                "why": "Corriger sans comprendre l'écart efface l'information utile.",
                "warning": "",
                "duration_minutes": 2,
            },
            {
                "title": "Choisir le bon type de mouvement",
                "instruction_farmer": "Bidon percé ou produit périmé : perte. Simple erreur de comptage : inventaire.",
                "instruction_pro": "PERTE décrémente et documente ; INVENTAIRE écrase la quantité à la valeur comptée.",
                "ui_hint": "Liste « type » du formulaire de mouvement.",
                "field_reference": "stock_movement.type",
                "why": "Les pertes doivent rester visibles : elles ont un coût et parfois une cause à traiter.",
                "warning": "N'utilisez pas l'inventaire pour masquer une perte.",
                "duration_minutes": 1,
            },
            {
                "title": "Documenter et enregistrer",
                "instruction_farmer": "Indiquez la date, une référence et une note explicative, puis enregistrez.",
                "instruction_pro": "`movement_date`, `reference`, `notes` : ce triplet rend l'écart auditable.",
                "ui_hint": "Bas du formulaire de mouvement.",
                "field_reference": "stock_movement.reference",
                "why": "Un mouvement sans explication devient incompréhensible six mois plus tard.",
                "warning": "",
                "duration_minutes": 1,
            },
        ],
    },
    {
        "slug": "proc-echeance-maintenance",
        "category": "materiel",
        "article": "entretien-preventif",
        "title": "Traiter une échéance de maintenance dépassée",
        "objective": "Remettre un engin en conformité et à jour de son plan d'entretien.",
        "context": "Dès qu'une échéance apparaît en retard sur le tableau de la flotte.",
        "expected_result": "Opération réalisée, coûts saisis, prochaine échéance recalculée.",
        "prerequisites": "Compteur de l'engin relevé, responsable désigné.",
        "module_route": "/maintenance",
        "estimated_minutes": 7,
        "difficulty": "INTERMEDIAIRE",
        "position": 1,
        "steps": [
            {
                "title": "Identifier l'échéance en retard",
                "instruction_farmer": "Repérez les engins signalés en retard sur le tableau de la flotte.",
                "instruction_pro": "Comparer `next_due_on` à aujourd'hui et `next_due_counter` à `usage_counter`.",
                "ui_hint": "Bloc des échéances de la page maintenance.",
                "field_reference": "maintenance_schedule.next_due_on",
                "why": "Une échéance réglementaire dépassée peut immobiliser l'engin en contrôle.",
                "warning": "Un contrôle pulvérisateur ou une VGP échue interdit l'usage de l'engin.",
                "duration_minutes": 1,
            },
            {
                "title": "Créer ou compléter l'opération",
                "instruction_farmer": "Créez l'opération d'entretien liée au plan et affectez un responsable.",
                "instruction_pro": "`maintenance_operation` avec `schedule_id`, `kind`, `priority` et `responsible_id`.",
                "ui_hint": "Formulaire d'opération de maintenance.",
                "field_reference": "maintenance_operation.schedule_id",
                "why": "Relier l'opération au plan permet de recalculer automatiquement la prochaine échéance.",
                "warning": "",
                "duration_minutes": 2,
            },
            {
                "title": "Saisir les coûts réels",
                "instruction_farmer": "Ajoutez les pièces, la main d'œuvre et les factures extérieures.",
                "instruction_pro": "Lignes `maintenance_cost` typées ; `total_cost` = main d'œuvre + pièces + externe.",
                "ui_hint": "Bloc coûts de l'opération.",
                "field_reference": "maintenance_cost.amount",
                "why": "Le coût horaire d'un engin ne vaut rien sans historique de coûts réels.",
                "warning": "",
                "duration_minutes": 2,
            },
            {
                "title": "Clôturer et relever le compteur",
                "instruction_farmer": "Marquez l'opération réalisée et relevez le compteur au moment de l'entretien.",
                "instruction_pro": "`done_date` + `counter_at_service` alimentent `last_done_on`/`last_done_counter` du plan.",
                "ui_hint": "Action de clôture sur l'opération.",
                "field_reference": "maintenance_operation.counter_at_service",
                "why": "Sans compteur au service, l'échéance suivante est décalée et le préventif se dérègle.",
                "warning": "",
                "duration_minutes": 2,
            },
        ],
    },
    {
        "slug": "proc-charge-parcelle",
        "category": "economie",
        "article": "charges-et-marge",
        "title": "Rattacher une facture à une parcelle",
        "objective": "Faire remonter une charge dans le coût à l'hectare de l'îlot concerné.",
        "context": "À la réception de chaque facture d'intrant, de prestation ou de réparation.",
        "expected_result": "Dépense enregistrée, rattachée, avec statut de paiement à jour.",
        "prerequisites": "Type de dépense existant, montant HT et TVA connus.",
        "module_route": "/charges",
        "estimated_minutes": 5,
        "difficulty": "DECOUVERTE",
        "position": 1,
        "steps": [
            {
                "title": "Vérifier le type de dépense",
                "instruction_farmer": "Choisissez un type existant ; créez-en un seulement s'il manque vraiment.",
                "instruction_pro": "`expense_type` porte le mode de paiement et la TVA par défaut : éviter les doublons de libellé.",
                "ui_hint": "Plan de charges, liste des types.",
                "field_reference": "expense_type.name",
                "why": "Des types stables rendent les synthèses comparables d'une année sur l'autre.",
                "warning": "",
                "duration_minutes": 1,
            },
            {
                "title": "Saisir montants et dates",
                "instruction_farmer": "Montant hors taxes, TVA, date de la facture et échéance de paiement.",
                "instruction_pro": "`amount_ht`, `vat_rate`, `amount_ttc` cohérents ; `incurred_on` ≤ `due_date`.",
                "ui_hint": "Bloc montants du formulaire de dépense.",
                "field_reference": "expense.amount_ht",
                "why": "La date d'engagement pilote les synthèses par période, la date d'échéance la trésorerie.",
                "warning": "Un TTC incohérent avec le HT et la TVA fausse toutes les synthèses.",
                "duration_minutes": 2,
            },
            {
                "title": "Rattacher à l'actif concerné",
                "instruction_farmer": "Indiquez la parcelle, la culture, l'engin ou le salarié concerné.",
                "instruction_pro": "Rattachements facultatifs mais décisifs : sans eux, la charge reste en frais généraux.",
                "ui_hint": "Bloc rattachements du formulaire.",
                "field_reference": "expense.parcel_id",
                "why": "Une charge non rattachée ne pourra jamais entrer dans une marge par parcelle.",
                "warning": "",
                "duration_minutes": 1,
            },
            {
                "title": "Suivre le paiement",
                "instruction_farmer": "Passez la dépense en payée le jour du règlement.",
                "instruction_pro": "`status` PAYEE + `paid_on` : l'écart engagé/payé constitue l'encours fournisseurs.",
                "ui_hint": "Statut sur la ligne du registre.",
                "field_reference": "expense.status",
                "why": "Distinguer engagé et payé est indispensable pour piloter la trésorerie.",
                "warning": "",
                "duration_minutes": 1,
            },
        ],
    },
]

# ---------------------------------------------------------------------------
# Dictionnaire agricole
# ---------------------------------------------------------------------------

TERMS: list[dict[str, str]] = [
    {
        "term": "Îlot",
        "slug": "ilot",
        "category": "parcelles",
        "definition_farmer": "Le morceau de terre que vous cultivez et reconnaissez sur le terrain.",
        "definition_pro": "Unité de gestion foncière homogène, identifiée par un code unique et une surface exploitée.",
        "unit": "ha",
        "example": "P01 · Les Grands Champs, 42,5 ha.",
        "synonyms": "parcelle, îlot PAC",
        "related_terms": "surface exploitée, contour",
        "module_route": "/parcelles",
    },
    {
        "term": "Campagne",
        "slug": "campagne",
        "category": "cultures",
        "definition_farmer": "L'année de culture, du semis à la récolte.",
        "definition_pro": "Millésime de référence rattaché à la fiche culturale, servant d'axe de comparaison pluriannuelle.",
        "unit": "année",
        "example": "Campagne 2026 pour un blé semé en octobre 2025.",
        "synonyms": "millésime",
        "related_terms": "assolement, rotation",
        "module_route": "/parcelles",
    },
    {
        "term": "Stade phénologique",
        "slug": "stade-phenologique",
        "category": "cultures",
        "definition_farmer": "Où en est la plante : levée, tallage, floraison, maturation.",
        "definition_pro": "Repère de développement utilisé pour positionner les interventions à fenêtre étroite.",
        "unit": "",
        "example": "Fongicide épis positionné à la floraison.",
        "synonyms": "stade",
        "related_terms": "somme de températures",
        "module_route": "/parcelles",
    },
    {
        "term": "Réserve utile",
        "slug": "reserve-utile",
        "acronym": "RU",
        "category": "irrigation",
        "definition_farmer": "La quantité d'eau que le sol peut garder et rendre à la plante.",
        "definition_pro": "Différence entre capacité au champ et point de flétrissement, sur la profondeur d'enracinement.",
        "unit": "mm",
        "formula": "RU = (θcc − θpf) × profondeur",
        "example": "Un limon profond peut stocker 150 à 180 mm.",
        "synonyms": "RU",
        "related_terms": "ET0, bilan hydrique",
        "module_route": "/traitements",
    },
    {
        "term": "Évapotranspiration de référence",
        "slug": "et0",
        "acronym": "ET0",
        "category": "irrigation",
        "definition_farmer": "La quantité d'eau que le temps fait perdre chaque jour à une culture de référence.",
        "definition_pro": "Demande climatique calculée à partir du rayonnement, de la température, de l'humidité et du vent.",
        "unit": "mm/j",
        "formula": "ETc = ET0 × Kc",
        "example": "ET0 de 5 mm/j en juillet avec un Kc de 1,1 : 5,5 mm consommés.",
        "synonyms": "évapotranspiration",
        "related_terms": "coefficient cultural, réserve utile",
        "module_route": "/traitements",
    },
    {
        "term": "Coefficient cultural",
        "slug": "coefficient-cultural",
        "acronym": "Kc",
        "category": "irrigation",
        "definition_farmer": "Un chiffre qui dit si la culture boit plus ou moins que la référence.",
        "definition_pro": "Ratio ETc/ET0 dépendant de l'espèce et du stade, utilisé dans le bilan hydrique.",
        "unit": "",
        "example": "Kc du maïs proche de 1,2 en pleine croissance.",
        "synonyms": "Kc",
        "related_terms": "ET0",
        "module_route": "/traitements",
    },
    {
        "term": "Plan de fumure",
        "slug": "plan-de-fumure",
        "category": "fertilisation",
        "definition_farmer": "Le programme des apports d'engrais prévu pour la culture.",
        "definition_pro": "Prévisionnel des apports établi par bilan, fractionné par stade et documenté par analyse de sol.",
        "unit": "unités/ha",
        "formula": "Dose = besoins − fournitures du sol",
        "example": "180 u d'azote fractionnées en trois apports.",
        "synonyms": "plan prévisionnel de fumure",
        "related_terms": "reliquat azoté, minéralisation",
        "module_route": "/traitements",
    },
    {
        "term": "Reliquat azoté",
        "slug": "reliquat-azote",
        "category": "fertilisation",
        "definition_farmer": "L'azote qui reste dans le sol en sortie d'hiver.",
        "definition_pro": "Azote minéral mesuré par horizon en sortie d'hiver, déduit des besoins dans la méthode du bilan.",
        "unit": "kg N/ha",
        "example": "Reliquat de 45 kg N/ha sur trois horizons.",
        "synonyms": "azote résiduel",
        "related_terms": "plan de fumure, analyse de sol",
        "module_route": "/traitements",
    },
    {
        "term": "Matière organique",
        "slug": "matiere-organique",
        "acronym": "MO",
        "category": "fertilisation",
        "definition_farmer": "L'humus du sol : il retient l'eau et nourrit la vie du sol.",
        "definition_pro": "Fraction organique du sol conditionnant CEC, structure, réserve utile et minéralisation azotée.",
        "unit": "%",
        "example": "2,4 % de MO sur un argilo-calcaire de plateau.",
        "synonyms": "humus",
        "related_terms": "minéralisation, structure",
        "module_route": "/parcelles",
    },
    {
        "term": "Zone non traitée",
        "slug": "znt",
        "acronym": "ZNT",
        "category": "phytosanitaire",
        "definition_farmer": "La bande le long des cours d'eau et des habitations où l'on ne traite pas.",
        "definition_pro": "Largeur minimale non traitée fixée par l'autorisation de mise sur le marché du produit.",
        "unit": "m",
        "example": "ZNT de 5 m au bord d'un cours d'eau.",
        "synonyms": "zone tampon",
        "related_terms": "dérive, délai de rentrée",
        "module_route": "/traitements",
    },
    {
        "term": "Délai avant récolte",
        "slug": "delai-avant-recolte",
        "acronym": "DAR",
        "category": "phytosanitaire",
        "definition_farmer": "Le nombre de jours à attendre entre le dernier traitement et la récolte.",
        "definition_pro": "Intervalle minimal réglementaire garantissant le respect des limites maximales de résidus.",
        "unit": "jours",
        "example": "DAR de 35 jours pour un fongicide céréales.",
        "synonyms": "DAR",
        "related_terms": "LMR, délai de rentrée",
        "module_route": "/traitements",
    },
    {
        "term": "Délai de rentrée",
        "slug": "delai-de-rentree",
        "category": "phytosanitaire",
        "definition_farmer": "Le temps à attendre avant de retourner dans la parcelle traitée.",
        "definition_pro": "Durée minimale avant réentrée du personnel dans la culture après application.",
        "unit": "heures",
        "example": "48 heures après un fongicide classé.",
        "synonyms": "réentrée",
        "related_terms": "ZNT, EPI",
        "module_route": "/traitements",
    },
    {
        "term": "Certiphyto",
        "slug": "certiphyto",
        "category": "personnel",
        "definition_farmer": "Le certificat obligatoire pour acheter et appliquer les produits.",
        "definition_pro": "Certificat individuel de produits phytopharmaceutiques, à renouveler périodiquement.",
        "unit": "",
        "example": "Certificat arrivant à échéance dans 90 jours : planifier le renouvellement.",
        "synonyms": "certificat phytosanitaire",
        "related_terms": "habilitation, affectation",
        "module_route": "/employes",
    },
    {
        "term": "Débit de chantier",
        "slug": "debit-de-chantier",
        "category": "travaux",
        "definition_farmer": "Le nombre d'hectares que vous faites en une heure.",
        "definition_pro": "Surface travaillée par unité de temps, incluant ou non les temps morts selon la convention retenue.",
        "unit": "ha/h",
        "formula": "Débit = surface / durée",
        "example": "36 ha en 4 h : 9 ha/h.",
        "synonyms": "rendement de chantier",
        "related_terms": "coût de passage",
        "module_route": "/traitements",
    },
    {
        "term": "Rendement",
        "slug": "rendement",
        "category": "recolte",
        "definition_farmer": "Ce que la parcelle a produit par hectare.",
        "definition_pro": "Quantité récoltée rapportée à la surface moissonnée, à normaliser à l'humidité de référence.",
        "unit": "t/ha",
        "formula": "Rendement = quantité / surface récoltée",
        "example": "340 t sur 42,5 ha : 8 t/ha.",
        "synonyms": "rendement réalisé",
        "related_terms": "humidité, pertes",
        "module_route": "/traitements",
    },
    {
        "term": "Marge brute",
        "slug": "marge-brute",
        "category": "economie",
        "definition_farmer": "Ce qui reste de la vente après avoir payé semences, engrais, traitements et travaux.",
        "definition_pro": "Produit brut moins charges opérationnelles affectées, rapporté à l'hectare.",
        "unit": "€/ha",
        "formula": "Marge brute = produit − charges opérationnelles",
        "example": "1 710 €/ha de produit − 690 €/ha de charges = 1 020 €/ha.",
        "synonyms": "MB",
        "related_terms": "charges opérationnelles, coût de production",
        "module_route": "/charges",
    },
    {
        "term": "Charges opérationnelles",
        "slug": "charges-operationnelles",
        "category": "economie",
        "definition_farmer": "Les dépenses qui varient avec ce que vous cultivez.",
        "definition_pro": "Intrants et prestations directement affectables à une culture ou une parcelle.",
        "unit": "€",
        "example": "Semences, engrais, produits, travaux par tiers.",
        "synonyms": "charges variables",
        "related_terms": "charges de structure, marge brute",
        "module_route": "/charges",
    },
    {
        "term": "Inventaire",
        "slug": "inventaire",
        "category": "stocks",
        "definition_farmer": "Le comptage réel du local, qui remet le stock à la bonne valeur.",
        "definition_pro": "Mouvement de régularisation écrasant la quantité en stock par la quantité comptée.",
        "unit": "",
        "example": "Inventaire trimestriel du local phyto.",
        "synonyms": "régularisation",
        "related_terms": "perte, seuil de réapprovisionnement",
        "module_route": "/traitements",
    },
    {
        "term": "Compteur d'engin",
        "slug": "compteur-engin",
        "category": "materiel",
        "definition_farmer": "Les heures ou les kilomètres affichés par la machine.",
        "definition_pro": "Index d'usage servant de base aux échéances d'entretien par compteur et au coût horaire.",
        "unit": "h ou km",
        "example": "4 820 h au tracteur de tête.",
        "synonyms": "index horaire",
        "related_terms": "entretien préventif, coût horaire",
        "module_route": "/maintenance",
    },
    {
        "term": "Vérification générale périodique",
        "slug": "vgp",
        "acronym": "VGP",
        "category": "materiel",
        "definition_farmer": "Le contrôle obligatoire des engins de levage, tous les ans.",
        "definition_pro": "Contrôle réglementaire périodique des appareils de levage, tracé et opposable.",
        "unit": "",
        "example": "VGP du chargeur télescopique.",
        "synonyms": "contrôle réglementaire",
        "related_terms": "entretien préventif",
        "module_route": "/maintenance",
    },
    {
        "term": "Contour cartographique",
        "slug": "contour-cartographique",
        "category": "parcelles",
        "definition_farmer": "Le tracé de la parcelle sur la carte.",
        "definition_pro": "Polygone GeoJSON en SRID 4326 avec centre, emprise, sommets et surface calculée.",
        "unit": "",
        "example": "Contour enregistré : trait plein ; contour généré : pointillés.",
        "synonyms": "géométrie",
        "related_terms": "surface exploitée",
        "module_route": "/cartographie",
    },
]

# ---------------------------------------------------------------------------
# Questions fréquentes (exemples de questions posées par les utilisateurs)
# ---------------------------------------------------------------------------

FAQ: list[dict] = [
    {
        "category": "fondamentaux",
        "question": "Par où commencer quand l'exploitation est vide ?",
        "answer_farmer": "Créez d'abord vos parcelles, puis les cultures de la campagne, puis vos chantiers.",
        "answer_pro": "Ordre de saisie : parcelles → cultures → interventions → récoltes → charges. Les indicateurs se recalculent ensuite automatiquement.",
        "keywords": "démarrage, ordre de saisie",
        "module_route": "/parcelles",
        "is_frequent": True,
        "position": 1,
    },
    {
        "category": "fondamentaux",
        "question": "Pourquoi mon cockpit affiche-t-il des zéros ?",
        "answer_farmer": "Aucune culture n'est encore en cours ou aucune récolte n'a été saisie.",
        "answer_pro": "Les KPI portent sur les cultures au statut EN_COURS et les récoltes enregistrées : sans données, les agrégats valent 0.",
        "keywords": "cockpit, indicateurs vides",
        "module_route": "/",
        "is_frequent": True,
        "position": 2,
    },
    {
        "category": "parcelles",
        "question": "Puis-je modifier la surface d'une parcelle après coup ?",
        "answer_farmer": "Oui, mais vérifiez ensuite les cultures : leur surface ne doit pas dépasser la nouvelle valeur.",
        "answer_pro": "La modification de `area_ha` n'ajuste pas les `crop.area_ha` existants : contrôlez la cohérence pour éviter des ratios /ha faux.",
        "keywords": "surface, modification",
        "module_route": "/parcelles",
        "is_frequent": True,
        "position": 1,
    },
    {
        "category": "parcelles",
        "question": "Pourquoi le contour de ma parcelle est-il en pointillés ?",
        "answer_farmer": "Parce qu'il a été généré automatiquement : il faut encore enregistrer le vrai tracé.",
        "answer_pro": "`geometry_source` = GENEREE : le contour est dérivé des coordonnées et de la surface, non exploitable pour un calcul de surface.",
        "keywords": "contour, pointillés, géométrie",
        "module_route": "/cartographie",
        "is_frequent": False,
        "position": 2,
    },
    {
        "category": "cultures",
        "question": "Puis-je mettre deux cultures sur la même parcelle ?",
        "answer_farmer": "Oui, sur des campagnes différentes, ou en même temps si vous partagez la surface.",
        "answer_pro": "Plusieurs `crop` par `parcel` sont autorisées ; la somme des surfaces des cultures simultanées ne doit pas dépasser la surface de la parcelle.",
        "keywords": "deux cultures, campagne, surface",
        "module_route": "/parcelles",
        "is_frequent": True,
        "position": 1,
    },
    {
        "category": "cultures",
        "question": "À quoi sert de relier une variété du référentiel ?",
        "answer_farmer": "À récupérer la couleur sur la carte, la durée du cycle et le rendement habituel.",
        "answer_pro": "`variety_id` fournit `cycle_days`, `expected_yield_t_ha` et `color_hex`, réutilisés par l'assolement et le calcul de performance.",
        "keywords": "variété, référentiel",
        "module_route": "/parcelles",
        "is_frequent": False,
        "position": 2,
    },
    {
        "category": "travaux",
        "question": "Que se passe-t-il quand je marque une intervention réalisée ?",
        "answer_farmer": "La date du jour est enregistrée et les produits prévus sortent du stock.",
        "answer_pro": "Clôture = `status` REALISEE + `done_date`, puis création d'un `stock_movement` SORTIE par intrant et décrément du stock.",
        "keywords": "clôture, réalisée, stock",
        "module_route": "/traitements",
        "is_frequent": True,
        "position": 1,
    },
    {
        "category": "travaux",
        "question": "Comment reporter un chantier à cause de la météo ?",
        "answer_farmer": "Utilisez le report : la date recule d'une semaine et le statut passe en reporté.",
        "answer_pro": "L'action de report avance `scheduled_date` de 7 jours et bascule `status` en REPORTEE ; une intervention REALISEE ne peut plus être reportée.",
        "keywords": "report, météo",
        "module_route": "/traitements",
        "is_frequent": False,
        "position": 2,
    },
    {
        "category": "irrigation",
        "question": "Quand déclencher un tour d'eau ?",
        "answer_farmer": "Quand les sondes descendent sous le seuil et qu'aucune pluie utile n'est annoncée.",
        "answer_pro": "Déclenchement sur tension hydrique ou bilan hydrique : RU restante inférieure à la réserve de sécurité et ET0 cumulée supérieure aux pluies.",
        "keywords": "tour d'eau, seuil, sondes",
        "module_route": "/traitements",
        "is_frequent": True,
        "position": 1,
    },
    {
        "category": "fertilisation",
        "question": "Faut-il tout apporter en une fois ?",
        "answer_farmer": "Non : fractionnez, la plante en profite mieux et vous perdez moins d'azote.",
        "answer_pro": "Le fractionnement synchronise l'offre avec la demande, limite la volatilisation et le lessivage, et améliore le coefficient apparent d'utilisation.",
        "keywords": "fractionnement, azote",
        "module_route": "/traitements",
        "is_frequent": True,
        "position": 1,
    },
    {
        "category": "phytosanitaire",
        "question": "Puis-je traiter avec du vent ?",
        "answer_farmer": "Non au-delà de vent moyen : reportez, la dérive vous coûte le produit et l'efficacité.",
        "answer_pro": "Au-delà d'environ 19 km/h, la dérive devient réglementairement et techniquement inacceptable : reporter ou adapter la buse.",
        "keywords": "vent, dérive, traitement",
        "module_route": "/traitements",
        "is_frequent": True,
        "position": 1,
    },
    {
        "category": "phytosanitaire",
        "question": "Comment vérifier que je pourrai récolter à temps ?",
        "answer_farmer": "Comparez le délai avant récolte du produit avec la date de moisson prévue.",
        "answer_pro": "Date d'application + `preharvest_delay_days` doit rester antérieure à `crop.expected_harvest_date`.",
        "keywords": "dar, récolte, délai",
        "module_route": "/traitements",
        "is_frequent": True,
        "position": 2,
    },
    {
        "category": "stocks",
        "question": "Mon stock est négatif ou faux, que faire ?",
        "answer_farmer": "Comptez le local et enregistrez un inventaire à la valeur réelle.",
        "answer_pro": "Le stock est plafonné à zéro en sortie ; un INVENTAIRE daté et référencé rétablit la quantité et documente l'écart.",
        "keywords": "stock faux, inventaire",
        "module_route": "/traitements",
        "is_frequent": True,
        "position": 1,
    },
    {
        "category": "materiel",
        "question": "Pourquoi relever le compteur à chaque entretien ?",
        "answer_farmer": "Parce que la prochaine échéance se calcule à partir de ce chiffre.",
        "answer_pro": "`counter_at_service` met à jour `last_done_counter` et donc `next_due_counter` : sans lui, le préventif se dérègle.",
        "keywords": "compteur, échéance, préventif",
        "module_route": "/maintenance",
        "is_frequent": False,
        "position": 1,
    },
    {
        "category": "personnel",
        "question": "Un salarié peut-il appliquer un produit sans certificat ?",
        "answer_farmer": "Non, jamais : l'application exige un certificat valide.",
        "answer_pro": "Habilitation expirée ou absente : l'affectation sur un chantier phytosanitaire doit être refusée et documentée.",
        "keywords": "certiphyto, habilitation",
        "module_route": "/employes",
        "is_frequent": True,
        "position": 1,
    },
    {
        "category": "recolte",
        "question": "Pourquoi mon rendement paraît-il trop élevé ?",
        "answer_farmer": "Souvent la surface récoltée saisie est plus petite que la surface réellement moissonnée.",
        "answer_pro": "Rendement = quantité / surface récoltée : vérifier `area_harvested_ha` et l'humidité, puis normaliser avant comparaison.",
        "keywords": "rendement, surface, humidité",
        "module_route": "/traitements",
        "is_frequent": True,
        "position": 1,
    },
    {
        "category": "economie",
        "question": "Où voir le coût réel d'une parcelle ?",
        "answer_farmer": "Dans les charges, à condition d'avoir rattaché les factures à la parcelle.",
        "answer_pro": "Seules les `expense` avec `parcel_id` renseigné remontent dans le coût à l'hectare de l'îlot ; les autres restent en frais généraux.",
        "keywords": "coût parcelle, rattachement",
        "module_route": "/charges",
        "is_frequent": True,
        "position": 1,
    },
    {
        "category": "economie",
        "question": "Quelle différence entre engagé et payé ?",
        "answer_farmer": "Engagé, c'est la facture reçue ; payé, c'est l'argent sorti.",
        "answer_pro": "ENGAGEE alimente les charges de la période, PAYEE avec `paid_on` alimente la trésorerie : l'écart est l'encours fournisseurs.",
        "keywords": "engagé, payé, trésorerie",
        "module_route": "/charges",
        "is_frequent": False,
        "position": 2,
    },
]

# ---------------------------------------------------------------------------
# Règles de cohérence, « Pourquoi ? » et « Attention »
# ---------------------------------------------------------------------------

RULES: list[dict] = [
    {
        "code": "COH-PARC-001",
        "category": "parcelles",
        "kind": "COHERENCE",
        "severity": "CRITIQUE",
        "title": "Le code de parcelle doit être unique",
        "statement": "Deux parcelles ne peuvent pas partager le même code d'îlot.",
        "rationale": "Le code est la clé de lecture humaine utilisée dans les filtres, la carte et les exports.",
        "consequence": "Des interventions et des charges seraient rattachées au mauvais îlot.",
        "remediation": "Renommer l'un des deux codes avant toute autre saisie.",
        "module_route": "/parcelles",
        "field_reference": "parcel.code",
        "is_blocking": True,
        "position": 1,
    },
    {
        "code": "COH-PARC-002",
        "category": "parcelles",
        "kind": "COHERENCE",
        "severity": "CRITIQUE",
        "title": "La surface doit être strictement positive et réaliste",
        "statement": "La surface d'une parcelle est comprise entre 0 (exclu) et 5 000 ha.",
        "rationale": "Toute dose, tout coût et tout rendement sont ramenés à l'hectare.",
        "consequence": "Une surface nulle rend impossible le calcul des ratios, une surface aberrante fausse tous les indicateurs.",
        "remediation": "Corriger la surface exploitée à partir du contour ou de la déclaration.",
        "module_route": "/parcelles",
        "field_reference": "parcel.area_ha",
        "is_blocking": True,
        "position": 2,
    },
    {
        "code": "ATT-PARC-003",
        "category": "parcelles",
        "kind": "ATTENTION",
        "severity": "ATTENTION",
        "title": "Écart entre surface déclarée et surface du contour",
        "statement": "Un écart supérieur à 5 % entre surface déclarée et surface calculée doit être arbitré.",
        "rationale": "Les deux valeurs servent d'assiette à des calculs différents et doivent converger.",
        "consequence": "Doses et marges à l'hectare divergent selon l'écran consulté.",
        "remediation": "Reprendre le contour ou mettre à jour la surface exploitée.",
        "module_route": "/cartographie",
        "field_reference": "parcel.geometry_area_ha",
        "is_blocking": False,
        "position": 3,
    },
    {
        "code": "COH-CULT-001",
        "category": "cultures",
        "kind": "COHERENCE",
        "severity": "CRITIQUE",
        "title": "La surface implantée ne dépasse pas la parcelle",
        "statement": "La surface d'une culture est inférieure ou égale à la surface de sa parcelle.",
        "rationale": "On ne peut pas semer plus d'hectares que la parcelle n'en compte.",
        "consequence": "Le rendement et les doses par hectare deviennent invérifiables.",
        "remediation": "Réduire la surface de la culture ou corriger la surface de la parcelle.",
        "module_route": "/parcelles",
        "field_reference": "crop.area_ha",
        "is_blocking": True,
        "position": 1,
    },
    {
        "code": "COH-CULT-002",
        "category": "cultures",
        "kind": "COHERENCE",
        "severity": "ATTENTION",
        "title": "La récolte prévue suit le semis",
        "statement": "La date de récolte prévue est postérieure à la date de semis.",
        "rationale": "L'ordre chronologique conditionne le calendrier et le calcul du cycle.",
        "consequence": "Le calendrier des chantiers affiche des échéances incohérentes.",
        "remediation": "Corriger l'une des deux dates, en s'appuyant sur le cycle de la variété.",
        "module_route": "/parcelles",
        "field_reference": "crop.expected_harvest_date",
        "is_blocking": True,
        "position": 2,
    },
    {
        "code": "POU-CULT-003",
        "category": "cultures",
        "kind": "POURQUOI",
        "severity": "INFO",
        "title": "Pourquoi historiser les stades ?",
        "statement": "Chaque changement de stade est daté, signé et conservé.",
        "rationale": "Le stade justifie le positionnement des interventions à fenêtre étroite et documente la campagne.",
        "consequence": "Sans historique, impossible d'expliquer une décision de traitement six mois plus tard.",
        "remediation": "Consigner une observation à chaque tour de plaine.",
        "module_route": "/parcelles",
        "field_reference": "crop_stage_log",
        "is_blocking": False,
        "position": 3,
    },
    {
        "code": "POU-TRAV-001",
        "category": "travaux",
        "kind": "POURQUOI",
        "severity": "INFO",
        "title": "Pourquoi planifier avant d'intervenir ?",
        "statement": "Une intervention est créée avant le passage, puis clôturée après.",
        "rationale": "La planification alimente le calendrier, la charge de travail et la réservation implicite du matériel.",
        "consequence": "Saisir après coup fait perdre la vision de la semaine et le pilotage de la main d'œuvre.",
        "remediation": "Créer l'intervention dès la décision, même sans tous les détails.",
        "module_route": "/traitements",
        "field_reference": "intervention.scheduled_date",
        "is_blocking": False,
        "position": 1,
    },
    {
        "code": "COH-TRAV-002",
        "category": "travaux",
        "kind": "COHERENCE",
        "severity": "ATTENTION",
        "title": "La réalisation suit la planification",
        "statement": "La date de réalisation ne peut pas précéder la date planifiée.",
        "rationale": "L'écart entre prévu et réalisé mesure la réactivité et la charge réelle.",
        "consequence": "Des durées négatives faussent les analyses de délais.",
        "remediation": "Corriger la date planifiée si le chantier a été avancé.",
        "module_route": "/traitements",
        "field_reference": "intervention.done_date",
        "is_blocking": True,
        "position": 2,
    },
    {
        "code": "ATT-PHY-001",
        "category": "phytosanitaire",
        "kind": "ATTENTION",
        "severity": "CRITIQUE",
        "title": "Vent trop fort : ne pas appliquer",
        "statement": "Au-delà d'environ 19 km/h de vent, l'application est reportée.",
        "rationale": "La dérive expose les tiers, les cours d'eau et diminue l'efficacité du traitement.",
        "consequence": "Non-conformité réglementaire et perte de produit.",
        "remediation": "Reporter le chantier ou adapter buses et volume de bouillie.",
        "module_route": "/traitements",
        "field_reference": "intervention.wind_speed_kmh",
        "is_blocking": False,
        "position": 1,
    },
    {
        "code": "ATT-PHY-002",
        "category": "phytosanitaire",
        "kind": "ATTENTION",
        "severity": "CRITIQUE",
        "title": "Délai avant récolte incompatible",
        "statement": "La date d'application plus le délai avant récolte doit rester antérieure à la récolte prévue.",
        "rationale": "Le délai garantit le respect des limites maximales de résidus.",
        "consequence": "Récolte non commercialisable et sanction possible.",
        "remediation": "Choisir un produit à délai plus court ou décaler la récolte.",
        "module_route": "/traitements",
        "field_reference": "product.preharvest_delay_days",
        "is_blocking": False,
        "position": 2,
    },
    {
        "code": "COH-PHY-003",
        "category": "phytosanitaire",
        "kind": "COHERENCE",
        "severity": "ATTENTION",
        "title": "Une dose exige une surface traitée",
        "statement": "Un intrant avec dose par hectare nécessite une surface traitée strictement positive.",
        "rationale": "La quantité totale appliquée est le produit de la dose et de la surface.",
        "consequence": "Sans surface, la sortie de stock et le coût du passage sont impossibles à calculer.",
        "remediation": "Renseigner la surface réellement traitée avant d'enregistrer.",
        "module_route": "/traitements",
        "field_reference": "intervention.area_treated_ha",
        "is_blocking": True,
        "position": 3,
    },
    {
        "code": "POU-STOCK-001",
        "category": "stocks",
        "kind": "POURQUOI",
        "severity": "INFO",
        "title": "Pourquoi déclarer les pertes ?",
        "statement": "Un produit détruit ou périmé se déclare en perte, pas en inventaire.",
        "rationale": "La perte reste visible, chiffrable et permet d'agir sur sa cause.",
        "consequence": "Masquer une perte par un inventaire efface un coût réel et une anomalie de stockage.",
        "remediation": "Utiliser le type PERTE avec une note explicative.",
        "module_route": "/traitements",
        "field_reference": "stock_movement.type",
        "is_blocking": False,
        "position": 1,
    },
    {
        "code": "ATT-STOCK-002",
        "category": "stocks",
        "kind": "ATTENTION",
        "severity": "ATTENTION",
        "title": "Stock sous le seuil de réapprovisionnement",
        "statement": "Un produit dont le stock est inférieur ou égal à son seuil est signalé critique.",
        "rationale": "Le seuil anticipe le délai de livraison au regard des chantiers programmés.",
        "consequence": "Rupture d'intrant au moment où la fenêtre d'intervention s'ouvre.",
        "remediation": "Commander ou reporter le chantier concerné.",
        "module_route": "/traitements",
        "field_reference": "product.reorder_threshold",
        "is_blocking": False,
        "position": 2,
    },
    {
        "code": "ATT-MAT-001",
        "category": "materiel",
        "kind": "ATTENTION",
        "severity": "CRITIQUE",
        "title": "Contrôle réglementaire échu",
        "statement": "Un engin dont le contrôle réglementaire est dépassé ne doit pas être utilisé.",
        "rationale": "Le contrôle conditionne la conformité de l'engin et la couverture assurantielle.",
        "consequence": "Immobilisation en contrôle, refus de prise en charge en cas de sinistre.",
        "remediation": "Planifier immédiatement l'opération réglementaire et suspendre l'usage.",
        "module_route": "/maintenance",
        "field_reference": "equipment.inspection_expiry",
        "is_blocking": False,
        "position": 1,
    },
    {
        "code": "POU-MAT-002",
        "category": "materiel",
        "kind": "POURQUOI",
        "severity": "INFO",
        "title": "Pourquoi saisir les coûts d'atelier ?",
        "statement": "Chaque opération de maintenance reçoit ses lignes de coût réelles.",
        "rationale": "Le coût horaire d'un engin ne peut être fiable qu'avec un historique de coûts constaté.",
        "consequence": "Les arbitrages achat/location et les prix de prestation reposent sur des estimations fausses.",
        "remediation": "Saisir pièces, main d'œuvre et factures externes à la clôture.",
        "module_route": "/maintenance",
        "field_reference": "maintenance_cost.amount",
        "is_blocking": False,
        "position": 2,
    },
    {
        "code": "COH-PERS-001",
        "category": "personnel",
        "kind": "COHERENCE",
        "severity": "CRITIQUE",
        "title": "Habilitation valide pour les chantiers réglementés",
        "statement": "L'affectation à une application phytosanitaire exige un certificat en cours de validité.",
        "rationale": "L'habilitation est une obligation individuelle opposable à l'employeur.",
        "consequence": "Infraction, responsabilité engagée et intervention non défendable.",
        "remediation": "Affecter une personne habilitée ou renouveler le certificat avant le chantier.",
        "module_route": "/employes",
        "field_reference": "employee.phyto_certificate_expiry",
        "is_blocking": True,
        "position": 1,
    },
    {
        "code": "ATT-PERS-002",
        "category": "personnel",
        "kind": "ATTENTION",
        "severity": "ATTENTION",
        "title": "Affectation pendant une absence",
        "statement": "Une affectation ne doit pas chevaucher un congé ou un arrêt déclaré.",
        "rationale": "Le planning sert à sécuriser la faisabilité du chantier.",
        "consequence": "Chantier non réalisé, report en cascade des travaux suivants.",
        "remediation": "Déplacer l'affectation ou désigner un autre opérateur.",
        "module_route": "/employes",
        "field_reference": "employee_availability",
        "is_blocking": False,
        "position": 2,
    },
    {
        "code": "COH-RECO-001",
        "category": "recolte",
        "kind": "COHERENCE",
        "severity": "CRITIQUE",
        "title": "Quantité et surface récoltée positives",
        "statement": "Une récolte exige une quantité et une surface récoltée strictement positives.",
        "rationale": "Le rendement est calculé par division : les deux valeurs sont indispensables.",
        "consequence": "Rendement nul ou infini, comparaisons inexploitables.",
        "remediation": "Compléter les pesées et la surface effectivement moissonnée.",
        "module_route": "/traitements",
        "field_reference": "harvest.area_harvested_ha",
        "is_blocking": True,
        "position": 1,
    },
    {
        "code": "ATT-RECO-002",
        "category": "recolte",
        "kind": "ATTENTION",
        "severity": "ATTENTION",
        "title": "Comparer à humidité comparable",
        "statement": "Les rendements ne se comparent qu'à humidité normalisée.",
        "rationale": "Deux points d'humidité représentent plusieurs quintaux apparents à l'hectare.",
        "consequence": "Classements de parcelles et de variétés erronés.",
        "remediation": "Renseigner l'humidité et normaliser avant analyse pluriannuelle.",
        "module_route": "/traitements",
        "field_reference": "harvest.moisture_percent",
        "is_blocking": False,
        "position": 2,
    },
    {
        "code": "COH-ECO-001",
        "category": "economie",
        "kind": "COHERENCE",
        "severity": "ATTENTION",
        "title": "Cohérence HT, TVA et TTC",
        "statement": "Le montant TTC doit correspondre au montant HT majoré de la TVA appliquée.",
        "rationale": "Les synthèses mélangent des montants HT et TTC selon l'usage : ils doivent être cohérents.",
        "consequence": "Charges surévaluées ou sous-évaluées, marge faussée.",
        "remediation": "Recalculer le TTC ou corriger le taux de TVA saisi.",
        "module_route": "/charges",
        "field_reference": "expense.amount_ttc",
        "is_blocking": False,
        "position": 1,
    },
    {
        "code": "POU-ECO-002",
        "category": "economie",
        "kind": "POURQUOI",
        "severity": "INFO",
        "title": "Pourquoi rattacher chaque dépense ?",
        "statement": "Une dépense est rattachée à la parcelle, la culture, l'engin ou le salarié concerné.",
        "rationale": "Le rattachement transforme une facture en coût à l'hectare et en marge par îlot.",
        "consequence": "Sans rattachement, la charge reste en frais généraux et n'éclaire aucune décision.",
        "remediation": "Compléter les rattachements au moment de la saisie, pas en fin d'exercice.",
        "module_route": "/charges",
        "field_reference": "expense.parcel_id",
        "is_blocking": False,
        "position": 2,
    },
    {
        "code": "POU-FOND-001",
        "category": "fondamentaux",
        "kind": "POURQUOI",
        "severity": "INFO",
        "title": "Pourquoi respecter l'ordre de saisie ?",
        "statement": "Parcelle, puis culture, puis intervention, puis récolte, puis charge.",
        "rationale": "Chaque objet a besoin du précédent pour exister et pour être comparable.",
        "consequence": "Saisir à l'envers oblige à recréer et rattacher manuellement des dizaines de lignes.",
        "remediation": "Créer la parcelle manquante avant toute autre saisie.",
        "module_route": "/",
        "field_reference": "",
        "is_blocking": False,
        "position": 1,
    },
    {
        "code": "ATT-IRR-001",
        "category": "irrigation",
        "kind": "ATTENTION",
        "severity": "ATTENTION",
        "title": "Irrigation sur sol saturé",
        "statement": "Ne pas irriguer après une pluie utile suffisante.",
        "rationale": "Au-delà de la capacité au champ, l'eau apportée est perdue par drainage et entraîne les nitrates.",
        "consequence": "Coût d'eau et d'énergie inutile, risque de lessivage.",
        "remediation": "Recalculer le bilan hydrique en intégrant la pluie des derniers jours.",
        "module_route": "/traitements",
        "field_reference": "intervention.water_volume_l_ha",
        "is_blocking": False,
        "position": 1,
    },
    {
        "code": "POU-FERT-001",
        "category": "fertilisation",
        "kind": "POURQUOI",
        "severity": "INFO",
        "title": "Pourquoi fractionner l'azote ?",
        "statement": "L'azote est apporté en plusieurs fois selon les stades.",
        "rationale": "Le fractionnement cale l'offre sur la demande de la plante et limite volatilisation et lessivage.",
        "consequence": "Un apport unique augmente les pertes et l'irrégularité de la protéine.",
        "remediation": "Découper la dose prévisionnelle en apports positionnés par stade.",
        "module_route": "/traitements",
        "field_reference": "intervention.type",
        "is_blocking": False,
        "position": 1,
    },
]

# ---------------------------------------------------------------------------
# Parcours d'apprentissage
# ---------------------------------------------------------------------------

PATHS: list[dict] = [
    {
        "slug": "parcours-prise-en-main",
        "title": "Prise en main en une heure",
        "subtitle": "De la parcelle vide au premier chantier tracé",
        "objective": "Savoir créer une parcelle, une culture et une intervention, et lire le cockpit.",
        "audience": "AGRICOLE",
        "difficulty": "DECOUVERTE",
        "estimated_minutes": 55,
        "icon": "graduation-cap",
        "color_hex": "#a3e635",
        "position": 1,
        "steps": [
            {
                "title": "Comprendre la chaîne de données",
                "description": "Lire comment parcelle, culture, intervention, récolte et charge s'enchaînent.",
                "article": "logique-generale-exploitation",
                "category": "fondamentaux",
                "milestone": "Vous savez dans quel ordre saisir.",
                "duration_minutes": 8,
            },
            {
                "title": "Créer sa première parcelle",
                "description": "Suivre la procédure complète de création d'un îlot.",
                "procedure": "proc-creer-parcelle",
                "category": "parcelles",
                "module_route": "/parcelles",
                "milestone": "Un îlot existe, visible sur la carte.",
                "duration_minutes": 12,
            },
            {
                "title": "Implanter une culture",
                "description": "Relier une variété du référentiel et fixer les dates clés.",
                "article": "implanter-une-culture",
                "category": "cultures",
                "module_route": "/parcelles",
                "milestone": "La campagne est ouverte sur la parcelle.",
                "duration_minutes": 10,
            },
            {
                "title": "Planifier puis clôturer un chantier",
                "description": "Créer une intervention, la réaliser et vérifier l'effet sur le stock.",
                "article": "planifier-un-chantier",
                "category": "travaux",
                "module_route": "/traitements",
                "milestone": "Un chantier tracé de bout en bout.",
                "duration_minutes": 15,
            },
            {
                "title": "Lire le cockpit",
                "description": "Alertes, météo, calendrier : l'ordre de lecture du matin.",
                "article": "lire-le-cockpit",
                "category": "fondamentaux",
                "module_route": "/",
                "milestone": "Vous décidez en trente secondes.",
                "duration_minutes": 10,
            },
        ],
    },
    {
        "slug": "parcours-tracabilite-phyto",
        "title": "Traçabilité phytosanitaire sans faille",
        "subtitle": "Registre, habilitations, délais et stocks",
        "objective": "Produire un registre complet, défendable en contrôle, avec des stocks justes.",
        "audience": "MIXTE",
        "difficulty": "INTERMEDIAIRE",
        "estimated_minutes": 50,
        "icon": "shield-check",
        "color_hex": "#f97316",
        "position": 2,
        "steps": [
            {
                "title": "Les exigences du registre",
                "description": "Ce qui doit figurer dans chaque ligne de traitement.",
                "article": "registre-phytosanitaire",
                "category": "phytosanitaire",
                "milestone": "Vous connaissez les champs obligatoires.",
                "duration_minutes": 10,
            },
            {
                "title": "Vérifier les habilitations",
                "description": "Croiser compétence, certificat et disponibilité avant d'affecter.",
                "article": "habilitations-equipe",
                "category": "personnel",
                "module_route": "/employes",
                "milestone": "Aucune affectation non habilitée.",
                "duration_minutes": 10,
            },
            {
                "title": "Enregistrer un traitement conforme",
                "description": "Dérouler la procédure pas à pas, conditions météo comprises.",
                "procedure": "proc-traitement-conforme",
                "category": "phytosanitaire",
                "module_route": "/traitements",
                "milestone": "Une ligne de registre complète.",
                "duration_minutes": 18,
            },
            {
                "title": "Fiabiliser le stock",
                "description": "Comprendre entrées, sorties, inventaires et pertes.",
                "article": "gerer-le-stock-intrants",
                "category": "stocks",
                "module_route": "/traitements",
                "milestone": "Le stock écran reflète le local phyto.",
                "duration_minutes": 12,
            },
        ],
    },
    {
        "slug": "parcours-pilotage-economique",
        "title": "Piloter la marge de chaque îlot",
        "subtitle": "Récoltes, charges rattachées et coût à l'hectare",
        "objective": "Passer d'une comptabilité globale à une marge brute lisible par parcelle.",
        "audience": "AGRIPRO",
        "difficulty": "AVANCE",
        "estimated_minutes": 45,
        "icon": "coins",
        "color_hex": "#fbbf24",
        "position": 3,
        "steps": [
            {
                "title": "Mesurer la récolte proprement",
                "description": "Quantité, surface, humidité, pertes : les bases d'un rendement fiable.",
                "article": "saisir-une-recolte",
                "category": "recolte",
                "module_route": "/traitements",
                "milestone": "Des rendements comparables entre îlots.",
                "duration_minutes": 12,
            },
            {
                "title": "Rattacher les charges",
                "description": "Types de dépenses stables et rattachement systématique.",
                "article": "charges-et-marge",
                "category": "economie",
                "module_route": "/charges",
                "milestone": "Chaque facture porte un actif.",
                "duration_minutes": 13,
            },
            {
                "title": "Enregistrer une facture rattachée",
                "description": "Dérouler la procédure de saisie et de suivi du paiement.",
                "procedure": "proc-charge-parcelle",
                "category": "economie",
                "module_route": "/charges",
                "milestone": "Un coût à l'hectare qui se met à jour.",
                "duration_minutes": 10,
            },
            {
                "title": "Contrôler le coût du matériel",
                "description": "Relier coûts d'atelier et heures d'usage pour un coût horaire juste.",
                "article": "entretien-preventif",
                "category": "materiel",
                "module_route": "/maintenance",
                "milestone": "Un coût horaire d'engin défendable.",
                "duration_minutes": 10,
                "is_optional": True,
            },
        ],
    },
]

VERSION_SUMMARY: str = (
    "Première publication de la base de connaissances Guide Agricole : douze "
    "catégories, articles en double lecture agricole et AgriPro, procédures pas "
    "à pas, dictionnaire, questions fréquentes, règles de cohérence et parcours "
    "d'apprentissage."
)


async def seed_guide_data() -> None:
    """Insère l'intégralité du guide si la table `guide_category` est vide."""
    init_local_database()
    async with rx.asession() as asession:
        existing = await asession.execute(
            text("SELECT COUNT(*) FROM guide_category")
        )
        if int(existing.scalar() or 0) > 0:
            return

        today = datetime.date.today()

        # --- Modules ciblés ------------------------------------------------
        await asession.execute(
            text(
                """
                INSERT INTO guide_module (
                    key, label, route, icon, description, position
                ) VALUES (
                    :key, :label, :route, :icon, :description, :position
                )
                """
            ),
            MODULES,
        )
        module_rows = (
            await asession.execute(
                text("SELECT id, key, route FROM guide_module")
            )
        ).all()
        module_ids = {str(row[1]): int(row[0]) for row in module_rows}
        module_routes = {str(row[1]): str(row[2]) for row in module_rows}

        # --- Catégories ----------------------------------------------------
        await asession.execute(
            text(
                """
                INSERT INTO guide_category (
                    key, name, tagline, description, icon, color_hex,
                    accent_hex, module_route, position, is_active
                ) VALUES (
                    :key, :name, :tagline, :description, :icon, :color_hex,
                    :accent_hex, :module_route, :position, 1
                )
                """
            ),
            CATEGORIES,
        )
        category_rows = (
            await asession.execute(text("SELECT id, key FROM guide_category"))
        ).all()
        category_ids = {str(row[1]): int(row[0]) for row in category_rows}

        # --- Articles ------------------------------------------------------
        article_params: list[dict] = []
        for item in ARTICLES:
            article_params.append(
                {
                    "category_id": category_ids[str(item["category"])],
                    "slug": item["slug"],
                    "title": item["title"],
                    "subtitle": item.get("subtitle", ""),
                    "summary": item.get("summary", ""),
                    "body_farmer": item.get("body_farmer", ""),
                    "body_pro": item.get("body_pro", ""),
                    "audience": item.get("audience", "MIXTE"),
                    "status": "PUBLIE",
                    "difficulty": item.get("difficulty", "DECOUVERTE"),
                    "reading_minutes": int(item.get("reading_minutes", 3)),
                    "keywords": item.get("keywords", ""),
                    "tags": item.get("tags", ""),
                    "author": GUIDE_AUTHOR,
                    "version_label": GUIDE_VERSION,
                    "module_route": item.get("module_route", ""),
                    "published_on": today,
                    "reviewed_on": today,
                    "is_featured": bool(item.get("is_featured", False)),
                    "position": int(item.get("position", 0)),
                }
            )
        await asession.execute(
            text(
                """
                INSERT INTO guide_article (
                    category_id, slug, title, subtitle, summary, body_farmer,
                    body_pro, audience, status, difficulty, reading_minutes,
                    keywords, tags, author, version_label, module_route,
                    published_on, reviewed_on, is_featured, position
                ) VALUES (
                    :category_id, :slug, :title, :subtitle, :summary, :body_farmer,
                    :body_pro, :audience, :status, :difficulty, :reading_minutes,
                    :keywords, :tags, :author, :version_label, :module_route,
                    :published_on, :reviewed_on, :is_featured, :position
                )
                """
            ),
            article_params,
        )
        article_rows = (
            await asession.execute(text("SELECT id, slug FROM guide_article"))
        ).all()
        article_ids = {str(row[1]): int(row[0]) for row in article_rows}

        # --- Liens des articles vers les modules ---------------------------
        link_params: list[dict] = []
        for item in ARTICLES:
            for index, (label, module_key, description) in enumerate(
                item.get("links", [])
            ):
                link_params.append(
                    {
                        "article_id": article_ids[str(item["slug"])],
                        "module_id": module_ids.get(module_key),
                        "label": label,
                        "route": module_routes.get(module_key, "/"),
                        "icon": "arrow-right",
                        "description": description,
                        "position": index + 1,
                    }
                )
        if link_params:
            await asession.execute(
                text(
                    """
                    INSERT INTO guide_article_link (
                        article_id, module_id, label, route, icon,
                        description, position
                    ) VALUES (
                        :article_id, :module_id, :label, :route, :icon,
                        :description, :position
                    )
                    """
                ),
                link_params,
            )

        # --- Procédures et étapes ------------------------------------------
        procedure_params: list[dict] = []
        for item in PROCEDURES:
            procedure_params.append(
                {
                    "category_id": category_ids[str(item["category"])],
                    "article_id": article_ids.get(item.get("article")),
                    "slug": item["slug"],
                    "title": item["title"],
                    "objective": item.get("objective", ""),
                    "context": item.get("context", ""),
                    "expected_result": item.get("expected_result", ""),
                    "prerequisites": item.get("prerequisites", ""),
                    "module_route": item.get("module_route", "/"),
                    "estimated_minutes": int(item.get("estimated_minutes", 5)),
                    "difficulty": item.get("difficulty", "DECOUVERTE"),
                    "audience": item.get("audience", "MIXTE"),
                    "status": "PUBLIE",
                    "version_label": GUIDE_VERSION,
                    "position": int(item.get("position", 0)),
                }
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
                    :estimated_minutes, :difficulty, :audience, :status,
                    :version_label, :position
                )
                """
            ),
            procedure_params,
        )
        procedure_rows = (
            await asession.execute(text("SELECT id, slug FROM guide_procedure"))
        ).all()
        procedure_ids = {str(row[1]): int(row[0]) for row in procedure_rows}

        step_params: list[dict] = []
        for item in PROCEDURES:
            for index, step in enumerate(item.get("steps", [])):
                step_params.append(
                    {
                        "procedure_id": procedure_ids[str(item["slug"])],
                        "position": index + 1,
                        "title": step.get("title", ""),
                        "instruction_farmer": step.get(
                            "instruction_farmer", ""
                        ),
                        "instruction_pro": step.get("instruction_pro", ""),
                        "ui_hint": step.get("ui_hint", ""),
                        "module_route": step.get(
                            "module_route", item.get("module_route", "")
                        ),
                        "field_reference": step.get("field_reference", ""),
                        "why": step.get("why", ""),
                        "warning": step.get("warning", ""),
                        "duration_minutes": int(
                            step.get("duration_minutes", 1)
                        ),
                        "is_optional": bool(step.get("is_optional", False)),
                    }
                )
        await asession.execute(
            text(
                """
                INSERT INTO guide_procedure_step (
                    procedure_id, position, title, instruction_farmer,
                    instruction_pro, ui_hint, module_route, field_reference,
                    why, warning, duration_minutes, is_optional
                ) VALUES (
                    :procedure_id, :position, :title, :instruction_farmer,
                    :instruction_pro, :ui_hint, :module_route, :field_reference,
                    :why, :warning, :duration_minutes, :is_optional
                )
                """
            ),
            step_params,
        )

        # --- Dictionnaire ---------------------------------------------------
        term_params: list[dict] = []
        for item in TERMS:
            term_params.append(
                {
                    "category_id": category_ids.get(item.get("category")),
                    "slug": item["slug"],
                    "term": item["term"],
                    "acronym": item.get("acronym", ""),
                    "definition_farmer": item.get("definition_farmer", ""),
                    "definition_pro": item.get("definition_pro", ""),
                    "unit": item.get("unit", ""),
                    "formula": item.get("formula", ""),
                    "example": item.get("example", ""),
                    "synonyms": item.get("synonyms", ""),
                    "related_terms": item.get("related_terms", ""),
                    "module_route": item.get("module_route", ""),
                    "status": "PUBLIE",
                    "version_label": GUIDE_VERSION,
                }
            )
        await asession.execute(
            text(
                """
                INSERT INTO guide_term (
                    category_id, slug, term, acronym, definition_farmer,
                    definition_pro, unit, formula, example, synonyms,
                    related_terms, module_route, status, version_label
                ) VALUES (
                    :category_id, :slug, :term, :acronym, :definition_farmer,
                    :definition_pro, :unit, :formula, :example, :synonyms,
                    :related_terms, :module_route, :status, :version_label
                )
                """
            ),
            term_params,
        )

        # --- Questions fréquentes -------------------------------------------
        faq_params: list[dict] = []
        for item in FAQ:
            faq_params.append(
                {
                    "category_id": category_ids[str(item["category"])],
                    "article_id": article_ids.get(item.get("article")),
                    "question": item["question"],
                    "answer_farmer": item.get("answer_farmer", ""),
                    "answer_pro": item.get("answer_pro", ""),
                    "audience": item.get("audience", "MIXTE"),
                    "status": "PUBLIE",
                    "keywords": item.get("keywords", ""),
                    "module_route": item.get("module_route", ""),
                    "is_frequent": bool(item.get("is_frequent", False)),
                    "position": int(item.get("position", 0)),
                    "version_label": GUIDE_VERSION,
                }
            )
        await asession.execute(
            text(
                """
                INSERT INTO guide_faq (
                    category_id, article_id, question, answer_farmer,
                    answer_pro, audience, status, keywords, module_route,
                    is_frequent, position, version_label
                ) VALUES (
                    :category_id, :article_id, :question, :answer_farmer,
                    :answer_pro, :audience, :status, :keywords, :module_route,
                    :is_frequent, :position, :version_label
                )
                """
            ),
            faq_params,
        )

        # --- Règles « Pourquoi ? » / « Attention » / cohérence ---------------
        rule_params: list[dict] = []
        for item in RULES:
            rule_params.append(
                {
                    "category_id": category_ids.get(item.get("category")),
                    "article_id": article_ids.get(item.get("article")),
                    "code": item["code"],
                    "kind": item.get("kind", "COHERENCE"),
                    "severity": item.get("severity", "INFO"),
                    "title": item.get("title", ""),
                    "statement": item.get("statement", ""),
                    "rationale": item.get("rationale", ""),
                    "consequence": item.get("consequence", ""),
                    "remediation": item.get("remediation", ""),
                    "module_route": item.get("module_route", ""),
                    "field_reference": item.get("field_reference", ""),
                    "is_blocking": bool(item.get("is_blocking", False)),
                    "status": "PUBLIE",
                    "version_label": GUIDE_VERSION,
                    "position": int(item.get("position", 0)),
                }
            )
        await asession.execute(
            text(
                """
                INSERT INTO guide_rule (
                    category_id, article_id, code, kind, severity, title,
                    statement, rationale, consequence, remediation,
                    module_route, field_reference, is_blocking, status,
                    version_label, position
                ) VALUES (
                    :category_id, :article_id, :code, :kind, :severity, :title,
                    :statement, :rationale, :consequence, :remediation,
                    :module_route, :field_reference, :is_blocking, :status,
                    :version_label, :position
                )
                """
            ),
            rule_params,
        )

        # --- Parcours d'apprentissage ---------------------------------------
        path_params: list[dict] = []
        for item in PATHS:
            path_params.append(
                {
                    "slug": item["slug"],
                    "title": item["title"],
                    "subtitle": item.get("subtitle", ""),
                    "objective": item.get("objective", ""),
                    "audience": item.get("audience", "AGRICOLE"),
                    "difficulty": item.get("difficulty", "DECOUVERTE"),
                    "status": "PUBLIE",
                    "estimated_minutes": int(item.get("estimated_minutes", 30)),
                    "icon": item.get("icon", "graduation-cap"),
                    "color_hex": item.get("color_hex", "#a3e635"),
                    "version_label": GUIDE_VERSION,
                    "position": int(item.get("position", 0)),
                }
            )
        await asession.execute(
            text(
                """
                INSERT INTO guide_learning_path (
                    slug, title, subtitle, objective, audience, difficulty,
                    status, estimated_minutes, icon, color_hex, version_label,
                    position
                ) VALUES (
                    :slug, :title, :subtitle, :objective, :audience, :difficulty,
                    :status, :estimated_minutes, :icon, :color_hex, :version_label,
                    :position
                )
                """
            ),
            path_params,
        )
        path_rows = (
            await asession.execute(
                text("SELECT id, slug FROM guide_learning_path")
            )
        ).all()
        path_ids = {str(row[1]): int(row[0]) for row in path_rows}

        path_step_params: list[dict] = []
        for item in PATHS:
            for index, step in enumerate(item.get("steps", [])):
                path_step_params.append(
                    {
                        "path_id": path_ids[str(item["slug"])],
                        "category_id": category_ids.get(step.get("category")),
                        "article_id": article_ids.get(step.get("article")),
                        "procedure_id": procedure_ids.get(
                            step.get("procedure")
                        ),
                        "position": index + 1,
                        "title": step.get("title", ""),
                        "description": step.get("description", ""),
                        "milestone": step.get("milestone", ""),
                        "module_route": step.get("module_route", ""),
                        "duration_minutes": int(
                            step.get("duration_minutes", 5)
                        ),
                        "is_optional": bool(step.get("is_optional", False)),
                    }
                )
        await asession.execute(
            text(
                """
                INSERT INTO guide_learning_step (
                    path_id, category_id, article_id, procedure_id, position,
                    title, description, milestone, module_route,
                    duration_minutes, is_optional
                ) VALUES (
                    :path_id, :category_id, :article_id, :procedure_id, :position,
                    :title, :description, :milestone, :module_route,
                    :duration_minutes, :is_optional
                )
                """
            ),
            path_step_params,
        )

        # --- Version publiée et changelog -----------------------------------
        await asession.execute(
            text(
                """
                INSERT INTO guide_version (
                    version_label, title, summary, changelog, author, status,
                    published_on, is_current
                ) VALUES (
                    :version_label, :title, :summary, :changelog, :author,
                    :status, :published_on, 1
                )
                """
            ),
            {
                "version_label": GUIDE_VERSION,
                "title": "Guide Agricole — publication initiale",
                "summary": VERSION_SUMMARY,
                "changelog": (
                    f"{len(CATEGORIES)} catégories, {len(ARTICLES)} articles, "
                    f"{len(PROCEDURES)} procédures, {len(TERMS)} entrées de "
                    f"dictionnaire, {len(FAQ)} questions fréquentes, "
                    f"{len(RULES)} règles et {len(PATHS)} parcours."
                ),
                "author": GUIDE_AUTHOR,
                "status": "PUBLIE",
                "published_on": today,
            },
        )
        version_id = int(
            (
                await asession.execute(
                    text(
                        "SELECT id FROM guide_version WHERE version_label = :v"
                    ),
                    {"v": GUIDE_VERSION},
                )
            ).scalar()
            or 0
        )

        entry_params: list[dict] = []
        position = 0
        for item in CATEGORIES:
            position += 1
            entry_params.append(
                {
                    "version_id": version_id,
                    "entity_type": "CATEGORIE",
                    "entity_ref": str(item["key"]),
                    "change_kind": "AJOUT",
                    "summary": f"Création de la catégorie « {item['name']} ».",
                    "author": GUIDE_AUTHOR,
                    "position": position,
                }
            )
        for item in ARTICLES:
            position += 1
            entry_params.append(
                {
                    "version_id": version_id,
                    "entity_type": "ARTICLE",
                    "entity_ref": str(item["slug"]),
                    "change_kind": "AJOUT",
                    "summary": f"Publication de l'article « {item['title']} ».",
                    "author": GUIDE_AUTHOR,
                    "position": position,
                }
            )
        for item in PROCEDURES:
            position += 1
            entry_params.append(
                {
                    "version_id": version_id,
                    "entity_type": "PROCEDURE",
                    "entity_ref": str(item["slug"]),
                    "change_kind": "AJOUT",
                    "summary": f"Publication de la procédure « {item['title']} ».",
                    "author": GUIDE_AUTHOR,
                    "position": position,
                }
            )
        for item in RULES:
            position += 1
            entry_params.append(
                {
                    "version_id": version_id,
                    "entity_type": "REGLE",
                    "entity_ref": str(item["code"]),
                    "change_kind": "AJOUT",
                    "summary": f"Ajout de la règle « {item['title']} ».",
                    "author": GUIDE_AUTHOR,
                    "position": position,
                }
            )
        for item in PATHS:
            position += 1
            entry_params.append(
                {
                    "version_id": version_id,
                    "entity_type": "PARCOURS",
                    "entity_ref": str(item["slug"]),
                    "change_kind": "AJOUT",
                    "summary": f"Publication du parcours « {item['title']} ».",
                    "author": GUIDE_AUTHOR,
                    "position": position,
                }
            )
        await asession.execute(
            text(
                """
                INSERT INTO guide_version_entry (
                    version_id, entity_type, entity_ref, change_kind, summary,
                    author, position
                ) VALUES (
                    :version_id, :entity_type, :entity_ref, :change_kind,
                    :summary, :author, :position
                )
                """
            ),
            entry_params,
        )

        await asession.commit()

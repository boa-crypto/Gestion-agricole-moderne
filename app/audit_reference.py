"""Référentiel statique de l'audit fonctionnel CMS² AgriPro.

Ce module ne contient QUE des constantes Python : la cartographie des modules
applicatifs réellement présents (route, écran, entités de données portées,
catégories du Guide Agricole censées les documenter), la liste des entités
persistantes attendues, ainsi que les référentiels normalisés de statut et de
priorité réutilisables par le futur module de diagnostic.

Aucune lecture de base ici : les comptages, les liens guide → application et
les incohérences sont lus en SQL brut dans `app/states/audit_state.py`.
"""

from __future__ import annotations

from typing import TypedDict

# ---------------------------------------------------------------------------
# Statuts normalisés et priorités
# ---------------------------------------------------------------------------

# Vocabulaire unique de l'audit, partagé avec le futur diagnostic.
STATUS_PRESENT: str = "PRESENT"
STATUS_INCOMPLETE: str = "INCOMPLET"
STATUS_INCOHERENT: str = "INCOHERENT"
STATUS_MISSING: str = "MANQUANT"

STATUS_ORDER: list[str] = [
    STATUS_MISSING,
    STATUS_INCOHERENT,
    STATUS_INCOMPLETE,
    STATUS_PRESENT,
]

STATUS_LABELS: dict[str, str] = {
    STATUS_PRESENT: "Présent",
    STATUS_INCOMPLETE: "Incomplet",
    STATUS_INCOHERENT: "Incohérent",
    STATUS_MISSING: "Manquant",
}

STATUS_TONES: dict[str, str] = {
    STATUS_PRESENT: "good",
    STATUS_INCOMPLETE: "warn",
    STATUS_INCOHERENT: "bad",
    STATUS_MISSING: "muted",
}

STATUS_ICONS: dict[str, str] = {
    STATUS_PRESENT: "circle-check",
    STATUS_INCOMPLETE: "circle-dashed",
    STATUS_INCOHERENT: "octagon-alert",
    STATUS_MISSING: "circle-slash",
}

PRIORITY_CRITICAL: str = "CRITIQUE"
PRIORITY_HIGH: str = "HAUTE"
PRIORITY_NORMAL: str = "NORMALE"
PRIORITY_LOW: str = "BASSE"

PRIORITY_LABELS: dict[str, str] = {
    PRIORITY_CRITICAL: "Critique",
    PRIORITY_HIGH: "Haute",
    PRIORITY_NORMAL: "Normale",
    PRIORITY_LOW: "Basse",
}

PRIORITY_TONES: dict[str, str] = {
    PRIORITY_CRITICAL: "bad",
    PRIORITY_HIGH: "warn",
    PRIORITY_NORMAL: "info",
    PRIORITY_LOW: "muted",
}

PRIORITY_WEIGHT: dict[str, int] = {
    PRIORITY_CRITICAL: 0,
    PRIORITY_HIGH: 1,
    PRIORITY_NORMAL: 2,
    PRIORITY_LOW: 3,
}

# Domaines d'audit : d'où vient le constat.
DOMAIN_LABELS: dict[str, str] = {
    "guide": "Contenu du Guide",
    "liaison": "Liaison guide → application",
    "donnees": "Données métier",
    "coherence": "Cohérence fonctionnelle",
    "exploitation": "État d'exploitation à traiter",
    "module": "Couverture de module",
}

# Domaines qui traduisent un écart structurel (liaison ou contenu cassé),
# par opposition aux états d'exploitation normaux à traiter au quotidien.
STRUCTURAL_DOMAINS: list[str] = ["guide", "liaison", "donnees", "module"]


# ---------------------------------------------------------------------------
# Cartographie des modules applicatifs
# ---------------------------------------------------------------------------


class ModuleSpec(TypedDict):
    """Module applicatif existant et ses attentes documentaires."""

    key: str
    label: str
    route: str
    icon: str
    mission: str
    categories: list[str]
    tables: list[str]
    features: list[str]


class EntitySpec(TypedDict):
    """Entité persistante attendue, rattachée à un module."""

    table: str
    label: str
    module: str
    role: str
    is_core: bool


# Routes réellement enregistrées dans `app/app.py` (plus la route d'audit).
APP_ROUTES: list[str] = [
    "/",
    "/parcelles",
    "/referentiel",
    "/traitements",
    "/employes",
    "/cartographie",
    "/maintenance",
    "/charges",
    "/recherche",
    "/guide",
    "/audit",
]

MODULE_SPECS: list[ModuleSpec] = [
    {
        "key": "cockpit",
        "label": "Cockpit agronomique",
        "route": "/",
        "icon": "layout-dashboard",
        "mission": "Lecture instantanée : indicateurs, alertes, météo, calendrier, assolement.",
        "categories": ["fondamentaux", "cultures", "travaux"],
        "tables": ["parcel", "crop", "alert", "intervention", "harvest"],
        "features": [
            "Bandeau d'indicateurs consolidés",
            "Carte d'assolement stylisée",
            "Panneau météo agricole et fenêtre de traitement",
            "Calendrier des chantiers à trois semaines",
        ],
    },
    {
        "key": "parcelles",
        "label": "Parcelles & cultures",
        "route": "/parcelles",
        "icon": "map",
        "mission": "Décrire le foncier et l'assolement : fiches parcellaires et culturales.",
        "categories": ["parcelles", "cultures"],
        "tables": ["parcel", "crop", "crop_variety", "crop_stage_log"],
        "features": [
            "Création et édition d'un îlot",
            "Fiche culturale reliée au référentiel variétal",
            "Journal des stades phénologiques",
            "Filtres statut, sol, irrigation et recherche",
        ],
    },
    {
        "key": "referentiel",
        "label": "Référentiel cultures",
        "route": "/referentiel",
        "icon": "sprout",
        "mission": (
            "Catégorie → Culture → Espèce → Variété : l'herbier agronomique "
            "consommé par les parcelles, l'irrigation et les récoltes."
        ),
        "categories": ["cultures", "parcelles"],
        "tables": [
            "crop_category",
            "crop_culture",
            "crop_species",
            "crop_catalog_variety",
        ],
        "features": [
            "Radar de couverture des familles cultivées",
            "Repères agronomiques par espèce (cycle, eau, N/P/K, pH)",
            "Fiches variétales et focus palmier dattier",
            "Liens vers le référentiel variétal historique",
        ],
    },
    {
        "key": "cartographie",
        "label": "Cartographie interactive",
        "route": "/cartographie",
        "icon": "map-pinned",
        "mission": "Contours réels des îlots, sélection au clic et historique parcellaire.",
        "categories": ["parcelles", "fondamentaux"],
        "tables": ["parcel", "intervention"],
        "features": [
            "Fond cartographique et polygones GeoJSON",
            "Éditeur de contour et métadonnées de géométrie",
            "Historique intégral des interventions de l'îlot",
        ],
    },
    {
        "key": "traitements",
        "label": "Traitements, stocks & récoltes",
        "route": "/traitements",
        "icon": "spray-can",
        "mission": "Planifier, tracer, sortir le stock et mesurer le rendement.",
        "categories": [
            "travaux",
            "phytosanitaire",
            "stocks",
            "irrigation",
            "fertilisation",
            "recolte",
        ],
        "tables": [
            "intervention",
            "intervention_product",
            "product",
            "stock_movement",
            "harvest",
        ],
        "features": [
            "Journal des interventions et clôture avec sortie de stock",
            "Magasin d'intrants et mouvements typés",
            "Saisie des récoltes et rendement calculé",
            "Comparaison rendement réalisé / visé",
        ],
    },
    {
        "key": "employes",
        "label": "Employés & compétences",
        "route": "/employes",
        "icon": "users-round",
        "mission": "La bonne personne, habilitée et disponible, sur le bon chantier.",
        "categories": ["personnel", "travaux"],
        "tables": [
            "employee",
            "skill",
            "employee_skill",
            "employee_availability",
            "assignment",
        ],
        "features": [
            "Registre du personnel et contrats",
            "Matrice de compétences et habilitations",
            "Disponibilités et absences",
            "Affectations aux chantiers et aux engins",
        ],
    },
    {
        "key": "maintenance",
        "label": "Engins & maintenance",
        "route": "/maintenance",
        "icon": "wrench",
        "mission": "Échéances, compteurs et coûts d'atelier de la flotte.",
        "categories": ["materiel", "economie"],
        "tables": [
            "equipment",
            "maintenance_schedule",
            "maintenance_operation",
            "maintenance_cost",
            "equipment_usage_log",
        ],
        "features": [
            "Fiche engin et compteur d'usage",
            "Plans d'entretien préventif calendaire et compteur",
            "Opérations, lignes de coût et clôture",
        ],
    },
    {
        "key": "charges",
        "label": "Charges & dépenses",
        "route": "/charges",
        "icon": "coins",
        "mission": "Rattacher chaque euro à un actif pour obtenir un coût à l'hectare.",
        "categories": ["economie", "stocks"],
        "tables": ["expense_type", "expense"],
        "features": [
            "Types de dépenses personnalisables",
            "Registre des charges et rattachements multiples",
            "Synthèses par type, par période et par actif",
        ],
    },
    {
        "key": "recherche",
        "label": "Recherche globale",
        "route": "/recherche",
        "icon": "radar",
        "mission": "Retrouver une instance dans toutes les tables métier.",
        "categories": ["fondamentaux", "cultures"],
        "tables": ["parcel", "crop", "intervention", "employee", "equipment"],
        "features": [
            "Balayage transversal des tables métier",
            "Filtres de période et de type d'entité",
        ],
    },
    {
        "key": "guide",
        "label": "Guide Agricole",
        "route": "/guide",
        "icon": "book-open",
        "mission": "Bibliothèque embarquée en double lecture agricole / AgriPro.",
        "categories": ["fondamentaux"],
        "tables": [
            "guide_category",
            "guide_article",
            "guide_procedure",
            "guide_term",
            "guide_faq",
            "guide_rule",
            "guide_learning_path",
            "guide_version",
        ],
        "features": [
            "Bibliothèque, dictionnaire, FAQ, parcours et règles",
            "Procédures interactives pas à pas",
            "Pupitre éditorial et versionnage",
            "Aide contextuelle embarquée par écran",
        ],
    },
]

MODULE_BY_KEY: dict[str, ModuleSpec] = {
    spec["key"]: spec for spec in MODULE_SPECS
}
MODULE_BY_ROUTE: dict[str, ModuleSpec] = {
    spec["route"]: spec for spec in MODULE_SPECS
}

ENTITY_SPECS: list[EntitySpec] = [
    # --- Foncier et végétal --------------------------------------------
    {
        "table": "parcel",
        "label": "Parcelles",
        "module": "parcelles",
        "role": "Unité foncière racine de toute la chaîne de données.",
        "is_core": True,
    },
    {
        "table": "crop",
        "label": "Cultures",
        "module": "parcelles",
        "role": "Fiche culturale d'une campagne sur une parcelle.",
        "is_core": True,
    },
    {
        "table": "crop_variety",
        "label": "Référentiel variétal",
        "module": "parcelles",
        "role": "Espèces et variétés cultivables (cycle, rendement, couleur).",
        "is_core": True,
    },
    {
        "table": "crop_stage_log",
        "label": "Journal des stades",
        "module": "parcelles",
        "role": "Historique phénologique daté et signé.",
        "is_core": False,
    },
    {
        "table": "soil_analysis",
        "label": "Analyses de sol",
        "module": "parcelles",
        "role": "Analyses pH, N/P/K et matière organique par îlot.",
        "is_core": False,
    },
    # --- Référentiel structuré des cultures ----------------------------
    {
        "table": "crop_category",
        "label": "Catégories du référentiel",
        "module": "referentiel",
        "role": "Familles cultivées racines de l'herbier agronomique.",
        "is_core": True,
    },
    {
        "table": "crop_culture",
        "label": "Cultures du référentiel",
        "module": "referentiel",
        "role": "Conduite d'une culture : cycle, besoin en eau, débouché.",
        "is_core": True,
    },
    {
        "table": "crop_species",
        "label": "Espèces du référentiel",
        "module": "referentiel",
        "role": "Constantes agronomiques : cycle, eau, pH, N/P/K, ravageurs.",
        "is_core": True,
    },
    {
        "table": "crop_catalog_variety",
        "label": "Variétés du référentiel",
        "module": "referentiel",
        "role": "Précocité, rendement visé, qualité et tolérances.",
        "is_core": True,
    },
    # --- Chantiers et intrants -----------------------------------------
    {
        "table": "intervention",
        "label": "Interventions",
        "module": "traitements",
        "role": "Chantier planifié puis clôturé, base de la traçabilité.",
        "is_core": True,
    },
    {
        "table": "intervention_product",
        "label": "Intrants appliqués",
        "module": "traitements",
        "role": "Produit dosé à l'hectare rattaché à une intervention.",
        "is_core": True,
    },
    {
        "table": "product",
        "label": "Produits & stocks",
        "module": "traitements",
        "role": "Intrants du magasin, seuils et valorisation.",
        "is_core": True,
    },
    {
        "table": "stock_movement",
        "label": "Mouvements de stock",
        "module": "traitements",
        "role": "Entrées, sorties, inventaires et pertes.",
        "is_core": True,
    },
    {
        "table": "harvest",
        "label": "Récoltes",
        "module": "traitements",
        "role": "Quantité, surface, humidité, qualité et valorisation.",
        "is_core": True,
    },
    {
        "table": "alert",
        "label": "Alertes agronomiques",
        "module": "cockpit",
        "role": "Signaux sanitaires, hydriques et météo non résolus.",
        "is_core": True,
    },
    # --- Personnel ------------------------------------------------------
    {
        "table": "employee",
        "label": "Employés",
        "module": "employes",
        "role": "Salariés et intervenants de l'exploitation.",
        "is_core": True,
    },
    {
        "table": "skill",
        "label": "Référentiel de compétences",
        "module": "employes",
        "role": "Compétences mobilisables, certifiantes ou non.",
        "is_core": True,
    },
    {
        "table": "employee_skill",
        "label": "Compétences détenues",
        "module": "employes",
        "role": "Niveau, expérience et validité de certification.",
        "is_core": True,
    },
    {
        "table": "employee_availability",
        "label": "Disponibilités",
        "module": "employes",
        "role": "Créneaux disponibles, congés, arrêts et formations.",
        "is_core": False,
    },
    {
        "table": "assignment",
        "label": "Affectations",
        "module": "employes",
        "role": "Rattachement d'un salarié à un chantier ou un engin.",
        "is_core": True,
    },
    # --- Flotte ---------------------------------------------------------
    {
        "table": "equipment",
        "label": "Engins",
        "module": "maintenance",
        "role": "Flotte, compteurs d'usage et échéances réglementaires.",
        "is_core": True,
    },
    {
        "table": "maintenance_schedule",
        "label": "Plans d'entretien",
        "module": "maintenance",
        "role": "Échéances calendaires, compteur ou mixtes.",
        "is_core": True,
    },
    {
        "table": "maintenance_operation",
        "label": "Opérations d'atelier",
        "module": "maintenance",
        "role": "Préventif, correctif et réglementaire.",
        "is_core": True,
    },
    {
        "table": "maintenance_cost",
        "label": "Coûts d'atelier",
        "module": "maintenance",
        "role": "Pièces, main d'œuvre et sous-traitance.",
        "is_core": False,
    },
    {
        "table": "equipment_usage_log",
        "label": "Relevés d'usage",
        "module": "maintenance",
        "role": "Compteurs, heures et carburant par chantier.",
        "is_core": False,
    },
    # --- Économie -------------------------------------------------------
    {
        "table": "expense_type",
        "label": "Types de dépenses",
        "module": "charges",
        "role": "Plan de charges personnalisable de l'exploitation.",
        "is_core": True,
    },
    {
        "table": "expense",
        "label": "Dépenses",
        "module": "charges",
        "role": "Charges rattachables à tout actif de l'exploitation.",
        "is_core": True,
    },
    # --- Guide ----------------------------------------------------------
    {
        "table": "guide_category",
        "label": "Catégories du Guide",
        "module": "guide",
        "role": "Carte de connaissances thématique.",
        "is_core": True,
    },
    {
        "table": "guide_article",
        "label": "Articles du Guide",
        "module": "guide",
        "role": "Fiches en double lecture agricole / AgriPro.",
        "is_core": True,
    },
    {
        "table": "guide_article_link",
        "label": "Liens guide → module",
        "module": "guide",
        "role": "Accès direct depuis un article vers un écran.",
        "is_core": True,
    },
    {
        "table": "guide_procedure",
        "label": "Procédures",
        "module": "guide",
        "role": "Modes opératoires pas à pas.",
        "is_core": True,
    },
    {
        "table": "guide_procedure_step",
        "label": "Étapes de procédure",
        "module": "guide",
        "role": "Gestes détaillés avec « Pourquoi ? » et « Attention ».",
        "is_core": True,
    },
    {
        "table": "guide_term",
        "label": "Dictionnaire",
        "module": "guide",
        "role": "Entrées de vocabulaire en double lecture.",
        "is_core": True,
    },
    {
        "table": "guide_faq",
        "label": "Questions fréquentes",
        "module": "guide",
        "role": "Réponses aux questions de terrain.",
        "is_core": True,
    },
    {
        "table": "guide_rule",
        "label": "Règles métier",
        "module": "guide",
        "role": "Cohérence, « Pourquoi ? » et avertissements.",
        "is_core": True,
    },
    {
        "table": "guide_learning_path",
        "label": "Parcours guidés",
        "module": "guide",
        "role": "Progressions d'apprentissage agricole et AgriPro.",
        "is_core": False,
    },
    {
        "table": "guide_learning_step",
        "label": "Étapes de parcours",
        "module": "guide",
        "role": "Jalons d'un parcours d'apprentissage.",
        "is_core": False,
    },
    {
        "table": "guide_version",
        "label": "Versions éditoriales",
        "module": "guide",
        "role": "Versionnage consultable du Guide.",
        "is_core": True,
    },
    {
        "table": "guide_version_entry",
        "label": "Changelog éditorial",
        "module": "guide",
        "role": "Lignes de changement par version.",
        "is_core": False,
    },
    {
        "table": "guide_module",
        "label": "Modules ciblés",
        "module": "guide",
        "role": "Écrans de l'application référencés par le Guide.",
        "is_core": False,
    },
]

ENTITY_TABLES: list[str] = [spec["table"] for spec in ENTITY_SPECS]
ENTITY_BY_TABLE: dict[str, EntitySpec] = {
    spec["table"]: spec for spec in ENTITY_SPECS
}


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def status_tone(status: str) -> str:
    return STATUS_TONES.get(status, "muted")


def priority_label(priority: str) -> str:
    return PRIORITY_LABELS.get(priority, priority)


def priority_tone(priority: str) -> str:
    return PRIORITY_TONES.get(priority, "muted")


def module_label(key: str) -> str:
    spec = MODULE_BY_KEY.get(key)
    return spec["label"] if spec is not None else "Transverse"


def module_route(key: str) -> str:
    spec = MODULE_BY_KEY.get(key)
    return spec["route"] if spec is not None else "/"


def module_of_route(route: str) -> str:
    spec = MODULE_BY_ROUTE.get(route)
    return spec["key"] if spec is not None else ""


def module_of_table(table: str) -> str:
    spec = ENTITY_BY_TABLE.get(table)
    return spec["module"] if spec is not None else ""

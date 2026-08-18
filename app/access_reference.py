"""Référentiel statique de la sécurité utilisateur CMS² AgriPro.

Ce module ne contient QUE des constantes Python : familles de fonctions
agricoles, rôles applicatifs, modules et actions permissionnables, matrice RBAC
par rôle, types de périmètre agricole, statuts d'utilisateur, méthodes MFA et
vocabulaire du journal d'activité.

Aucune lecture de base ici : l'amorçage se fait dans `app/seed_access.py` et les
contrôles serveur dans `app/access_control.py`.

Direction visuelle à préserver pour les futurs écrans : vert nuit AgriPro,
accents chlorophylle et ambre, surfaces vitrées, badges lumineux, typographie
Instrument Serif / Inter. Les couleurs et icônes déclarées ici alimentent
directement ces badges (aucune interface back-office générique).
"""

from __future__ import annotations

from typing import TypedDict

# ---------------------------------------------------------------------------
# Exploitation de référence et secteurs
# ---------------------------------------------------------------------------

FARM_KEY: str = "domaine-el-bahia"
FARM_LABEL: str = "Domaine El Bahia"

SECTORS: list[str] = ["Nord", "Centre", "Sud"]

# ---------------------------------------------------------------------------
# Actions permissionnables
# ---------------------------------------------------------------------------

ACTION_CONSULTER: str = "CONSULTER"
ACTION_CREER: str = "CREER"
ACTION_MODIFIER: str = "MODIFIER"
ACTION_SUPPRIMER: str = "SUPPRIMER"
ACTION_VALIDER: str = "VALIDER"
ACTION_AFFECTER: str = "AFFECTER"
ACTION_PLANIFIER: str = "PLANIFIER"
ACTION_CLOTURER: str = "CLOTURER"
ACTION_EXPORTER: str = "EXPORTER"
ACTION_IMPRIMER: str = "IMPRIMER"

ACTION_LABELS: dict[str, str] = {
    ACTION_CONSULTER: "Consulter",
    ACTION_CREER: "Créer",
    ACTION_MODIFIER: "Modifier",
    ACTION_SUPPRIMER: "Supprimer",
    ACTION_VALIDER: "Valider",
    ACTION_AFFECTER: "Affecter",
    ACTION_PLANIFIER: "Planifier",
    ACTION_CLOTURER: "Clôturer",
    ACTION_EXPORTER: "Exporter",
    ACTION_IMPRIMER: "Imprimer",
}

ACTION_ORDER: list[str] = list(ACTION_LABELS.keys())

# Actions considérées comme sensibles : elles alimentent l'audit sécurité.
SENSITIVE_ACTIONS: list[str] = [ACTION_SUPPRIMER, ACTION_AFFECTER]

FULL_ACTIONS: list[str] = ACTION_ORDER
READ_ACTIONS: list[str] = [ACTION_CONSULTER]
READ_EXPORT: list[str] = [ACTION_CONSULTER, ACTION_EXPORTER, ACTION_IMPRIMER]
WRITE_ACTIONS: list[str] = [
    ACTION_CONSULTER,
    ACTION_CREER,
    ACTION_MODIFIER,
    ACTION_EXPORTER,
]
FIELD_ACTIONS: list[str] = [
    ACTION_CONSULTER,
    ACTION_CREER,
    ACTION_MODIFIER,
    ACTION_PLANIFIER,
    ACTION_CLOTURER,
]


# ---------------------------------------------------------------------------
# Modules permissionnables
# ---------------------------------------------------------------------------


class ModulePermSpec(TypedDict):
    key: str
    label: str
    icon: str
    route: str
    actions: list[str]
    is_sensitive: bool


ACCESS_MODULES: list[ModulePermSpec] = [
    {
        "key": "dashboard",
        "label": "Cockpit",
        "icon": "layout-dashboard",
        "route": "/",
        "actions": READ_EXPORT,
        "is_sensitive": False,
    },
    {
        "key": "exploitations",
        "label": "Exploitations",
        "icon": "building-2",
        "route": "/",
        "actions": FULL_ACTIONS,
        "is_sensitive": True,
    },
    {
        "key": "parcelles",
        "label": "Parcelles",
        "icon": "map",
        "route": "/parcelles",
        "actions": FULL_ACTIONS,
        "is_sensitive": False,
    },
    {
        "key": "cultures",
        "label": "Cultures",
        "icon": "sprout",
        "route": "/parcelles",
        "actions": FULL_ACTIONS,
        "is_sensitive": False,
    },
    {
        "key": "semences",
        "label": "Semences & variétés",
        "icon": "wheat",
        "route": "/referentiel",
        "actions": WRITE_ACTIONS,
        "is_sensitive": False,
    },
    {
        "key": "interventions",
        "label": "Interventions",
        "icon": "clipboard-list",
        "route": "/traitements",
        "actions": FULL_ACTIONS,
        "is_sensitive": False,
    },
    {
        "key": "irrigation",
        "label": "Irrigation",
        "icon": "droplets",
        "route": "/traitements",
        "actions": FIELD_ACTIONS + [ACTION_VALIDER],
        "is_sensitive": False,
    },
    {
        "key": "fertilisation",
        "label": "Fertilisation",
        "icon": "flask-conical",
        "route": "/traitements",
        "actions": FIELD_ACTIONS + [ACTION_VALIDER],
        "is_sensitive": False,
    },
    {
        "key": "traitements",
        "label": "Traitements phytosanitaires",
        "icon": "spray-can",
        "route": "/traitements",
        "actions": FIELD_ACTIONS + [ACTION_VALIDER],
        "is_sensitive": True,
    },
    {
        "key": "recoltes",
        "label": "Récoltes",
        "icon": "tractor",
        "route": "/traitements",
        "actions": FIELD_ACTIONS + [ACTION_VALIDER, ACTION_EXPORTER],
        "is_sensitive": False,
    },
    {
        "key": "stocks",
        "label": "Stocks",
        "icon": "package",
        "route": "/traitements",
        "actions": FULL_ACTIONS,
        "is_sensitive": False,
    },
    {
        "key": "intrants",
        "label": "Intrants",
        "icon": "flask-round",
        "route": "/traitements",
        "actions": WRITE_ACTIONS + [ACTION_SUPPRIMER],
        "is_sensitive": False,
    },
    {
        "key": "materiel",
        "label": "Matériel & engins",
        "icon": "wrench",
        "route": "/maintenance",
        "actions": FULL_ACTIONS,
        "is_sensitive": False,
    },
    {
        "key": "maintenance",
        "label": "Maintenance",
        "icon": "settings",
        "route": "/maintenance",
        "actions": FIELD_ACTIONS + [ACTION_VALIDER, ACTION_AFFECTER],
        "is_sensitive": False,
    },
    {
        "key": "carburant",
        "label": "Carburant",
        "icon": "fuel",
        "route": "/maintenance",
        "actions": WRITE_ACTIONS,
        "is_sensitive": False,
    },
    {
        "key": "rh",
        "label": "Ressources humaines",
        "icon": "users-round",
        "route": "/employes",
        "actions": FULL_ACTIONS,
        "is_sensitive": True,
    },
    {
        "key": "equipes",
        "label": "Équipes",
        "icon": "users",
        "route": "/employes",
        "actions": FULL_ACTIONS,
        "is_sensitive": False,
    },
    {
        "key": "achats",
        "label": "Achats",
        "icon": "shopping-cart",
        "route": "/charges",
        "actions": FULL_ACTIONS,
        "is_sensitive": True,
    },
    {
        "key": "ventes",
        "label": "Ventes",
        "icon": "hand-coins",
        "route": "/charges",
        "actions": FULL_ACTIONS,
        "is_sensitive": True,
    },
    {
        "key": "comptabilite",
        "label": "Comptabilité",
        "icon": "coins",
        "route": "/charges",
        "actions": FULL_ACTIONS,
        "is_sensitive": True,
    },
    {
        "key": "documents",
        "label": "Documents",
        "icon": "folder",
        "route": "/guide",
        "actions": WRITE_ACTIONS + [ACTION_SUPPRIMER, ACTION_IMPRIMER],
        "is_sensitive": False,
    },
    {
        "key": "rapports",
        "label": "Rapports",
        "icon": "chart-column",
        "route": "/rapports",
        "actions": READ_EXPORT,
        "is_sensitive": False,
    },
    {
        "key": "cartographie",
        "label": "Cartographie",
        "icon": "map-pinned",
        "route": "/cartographie",
        "actions": WRITE_ACTIONS,
        "is_sensitive": False,
    },
    {
        "key": "meteo",
        "label": "Météo",
        "icon": "cloud-sun",
        "route": "/",
        "actions": READ_ACTIONS,
        "is_sensitive": False,
    },
    {
        "key": "parametres",
        "label": "Paramètres",
        "icon": "sliders-horizontal",
        "route": "/",
        "actions": [ACTION_CONSULTER, ACTION_MODIFIER],
        "is_sensitive": True,
    },
    {
        "key": "utilisateurs",
        "label": "Utilisateurs & sécurité",
        "icon": "shield-check",
        "route": "/administration",
        "actions": FULL_ACTIONS,
        "is_sensitive": True,
    },
]

MODULE_BY_KEY: dict[str, ModulePermSpec] = {
    spec["key"]: spec for spec in ACCESS_MODULES
}
MODULE_KEYS: list[str] = [spec["key"] for spec in ACCESS_MODULES]


def permission_key(module: str, action: str) -> str:
    """Clé canonique d'une permission : `module:ACTION`."""
    return f"{module}:{action}"


def is_sensitive_permission(module: str, action: str) -> bool:
    spec = MODULE_BY_KEY.get(module)
    module_sensitive = bool(spec["is_sensitive"]) if spec is not None else False
    return action in SENSITIVE_ACTIONS or (
        module_sensitive and action != ACTION_CONSULTER
    )


def all_permissions() -> list[tuple[str, str]]:
    """Couples (module, action) permissionnables de l'application."""
    pairs: list[tuple[str, str]] = []
    for spec in ACCESS_MODULES:
        for action in spec["actions"]:
            pairs.append((spec["key"], action))
    return pairs


# ---------------------------------------------------------------------------
# Familles de fonctions agricoles
# ---------------------------------------------------------------------------

FAMILY_DIRECTION: str = "DIRECTION"
FAMILY_PRODUCTION: str = "PRODUCTION"
FAMILY_TERRAIN: str = "TERRAIN"
FAMILY_LOGISTIQUE: str = "LOGISTIQUE"
FAMILY_ADMINISTRATION: str = "ADMINISTRATION"

FAMILY_LABELS: dict[str, str] = {
    FAMILY_DIRECTION: "Direction & gestion",
    FAMILY_PRODUCTION: "Production",
    FAMILY_TERRAIN: "Terrain",
    FAMILY_LOGISTIQUE: "Logistique",
    FAMILY_ADMINISTRATION: "Administration",
}

FAMILY_COLORS: dict[str, str] = {
    FAMILY_DIRECTION: "#fbbf24",
    FAMILY_PRODUCTION: "#a3e635",
    FAMILY_TERRAIN: "#4ade80",
    FAMILY_LOGISTIQUE: "#38bdf8",
    FAMILY_ADMINISTRATION: "#c084fc",
}


class FunctionSpec(TypedDict):
    key: str
    name: str
    family: str
    mission: str
    responsibilities: str
    default_role: str
    icon: str


FUNCTIONS: list[FunctionSpec] = [
    # --- Direction / gestion -------------------------------------------
    {
        "key": "proprietaire",
        "name": "Propriétaire",
        "family": FAMILY_DIRECTION,
        "mission": "Détient l'exploitation et arbitre les décisions stratégiques.",
        "responsibilities": "Stratégie · investissements · gouvernance des accès",
        "default_role": "proprietaire",
        "icon": "crown",
    },
    {
        "key": "exploitant",
        "name": "Exploitant",
        "family": FAMILY_DIRECTION,
        "mission": "Conduit l'exploitation au quotidien et engage les moyens.",
        "responsibilities": "Assolement · budget · encadrement",
        "default_role": "chef-exploitation",
        "icon": "user-check",
    },
    {
        "key": "gerant",
        "name": "Gérant",
        "family": FAMILY_DIRECTION,
        "mission": "Représente juridiquement et administrativement l'exploitation.",
        "responsibilities": "Contrats · conformité · relations bancaires",
        "default_role": "chef-exploitation",
        "icon": "briefcase",
    },
    {
        "key": "directeur-exploitation",
        "name": "Directeur d'exploitation",
        "family": FAMILY_DIRECTION,
        "mission": "Pilote la performance agronomique et économique.",
        "responsibilities": "Objectifs de campagne · arbitrages · reporting",
        "default_role": "chef-exploitation",
        "icon": "target",
    },
    {
        "key": "responsable-administratif",
        "name": "Responsable administratif",
        "family": FAMILY_DIRECTION,
        "mission": "Organise l'administration et les obligations déclaratives.",
        "responsibilities": "Registres · dossiers PAC · archivage",
        "default_role": "comptable",
        "icon": "file-text",
    },
    # --- Production -----------------------------------------------------
    {
        "key": "chef-exploitation",
        "name": "Chef d'exploitation",
        "family": FAMILY_PRODUCTION,
        "mission": "Organise les chantiers, les équipes et les moyens.",
        "responsibilities": "Planification · validation · sécurité au travail",
        "default_role": "chef-exploitation",
        "icon": "clipboard-check",
    },
    {
        "key": "responsable-production",
        "name": "Responsable de production",
        "family": FAMILY_PRODUCTION,
        "mission": "Garantit le rendement et la qualité des productions.",
        "responsibilities": "Itinéraires techniques · suivi des rendements",
        "default_role": "responsable-production",
        "icon": "trending-up",
    },
    {
        "key": "chef-culture",
        "name": "Chef de culture",
        "family": FAMILY_PRODUCTION,
        "mission": "Suit une culture de la mise en place à la récolte.",
        "responsibilities": "Stades · interventions · notation sanitaire",
        "default_role": "responsable-production",
        "icon": "sprout",
    },
    {
        "key": "agronome",
        "name": "Agronome",
        "family": FAMILY_PRODUCTION,
        "mission": "Établit les recommandations agronomiques.",
        "responsibilities": "Plan de fumure · protection · essais",
        "default_role": "responsable-production",
        "icon": "microscope",
    },
    {
        "key": "technicien-agricole",
        "name": "Technicien agricole",
        "family": FAMILY_PRODUCTION,
        "mission": "Réalise les observations et le suivi de terrain.",
        "responsibilities": "Comptages · relevés · saisie des observations",
        "default_role": "consultation",
        "icon": "search",
    },
    # --- Terrain ---------------------------------------------------------
    {
        "key": "chef-equipe",
        "name": "Chef d'équipe",
        "family": FAMILY_TERRAIN,
        "mission": "Encadre une équipe sur les parcelles affectées.",
        "responsibilities": "Missions du jour · sécurité · compte rendu",
        "default_role": "chef-equipe",
        "icon": "users",
    },
    {
        "key": "chef-equipe-irrigation",
        "name": "Chef d'équipe irrigation",
        "family": FAMILY_TERRAIN,
        "mission": "Conduit les tours d'eau sur son secteur.",
        "responsibilities": "Tours d'eau · réseau · relevés de sondes",
        "default_role": "responsable-irrigation",
        "icon": "droplets",
    },
    {
        "key": "ouvrier-agricole",
        "name": "Ouvrier agricole",
        "family": FAMILY_TERRAIN,
        "mission": "Exécute les travaux confiés sur ses parcelles.",
        "responsibilities": "Tâches affectées · déclaration de travail",
        "default_role": "ouvrier",
        "icon": "shovel",
    },
    {
        "key": "conducteur-engins",
        "name": "Conducteur d'engins",
        "family": FAMILY_TERRAIN,
        "mission": "Conduit les engins et outils attelés.",
        "responsibilities": "Réglages · compteurs · entretien courant",
        "default_role": "ouvrier",
        "icon": "tractor",
    },
    {
        "key": "agent-irrigation",
        "name": "Agent d'irrigation",
        "family": FAMILY_TERRAIN,
        "mission": "Applique les consignes d'irrigation.",
        "responsibilities": "Ouverture des vannes · relevés · incidents",
        "default_role": "ouvrier",
        "icon": "waves",
    },
    {
        "key": "agent-phytosanitaire",
        "name": "Agent phytosanitaire",
        "family": FAMILY_TERRAIN,
        "mission": "Réalise les applications sous habilitation.",
        "responsibilities": "Bouillie · ZNT · registre phytosanitaire",
        "default_role": "ouvrier",
        "icon": "spray-can",
    },
    {
        "key": "agent-maintenance",
        "name": "Agent de maintenance",
        "family": FAMILY_TERRAIN,
        "mission": "Assure l'entretien préventif et curatif.",
        "responsibilities": "Plans d'entretien · pièces · atelier",
        "default_role": "responsable-materiel",
        "icon": "wrench",
    },
    # --- Logistique ------------------------------------------------------
    {
        "key": "responsable-stock",
        "name": "Responsable stock",
        "family": FAMILY_LOGISTIQUE,
        "mission": "Garantit la disponibilité et la traçabilité des intrants.",
        "responsibilities": "Seuils · inventaires · conformité du local phyto",
        "default_role": "responsable-stock",
        "icon": "package",
    },
    {
        "key": "magasinier",
        "name": "Magasinier",
        "family": FAMILY_LOGISTIQUE,
        "mission": "Enregistre les entrées et sorties du magasin.",
        "responsibilities": "Réception · sorties · rangement",
        "default_role": "responsable-stock",
        "icon": "boxes",
    },
    {
        "key": "responsable-materiel",
        "name": "Responsable matériel",
        "family": FAMILY_LOGISTIQUE,
        "mission": "Maintient la flotte disponible et conforme.",
        "responsibilities": "Échéances · coûts d'atelier · affectations",
        "default_role": "responsable-materiel",
        "icon": "settings",
    },
    {
        "key": "chauffeur",
        "name": "Chauffeur",
        "family": FAMILY_LOGISTIQUE,
        "mission": "Assure les transports de récolte et d'intrants.",
        "responsibilities": "Tournées · bons de livraison",
        "default_role": "ouvrier",
        "icon": "truck",
    },
    {
        "key": "responsable-recolte",
        "name": "Responsable récolte",
        "family": FAMILY_LOGISTIQUE,
        "mission": "Organise les chantiers de récolte et le stockage.",
        "responsibilities": "Fenêtres de récolte · qualité · cellules",
        "default_role": "chef-equipe",
        "icon": "wheat",
    },
    # --- Administration --------------------------------------------------
    {
        "key": "comptable",
        "name": "Comptable",
        "family": FAMILY_ADMINISTRATION,
        "mission": "Tient la comptabilité et suit les marges.",
        "responsibilities": "Charges · recettes · clôtures",
        "default_role": "comptable",
        "icon": "calculator",
    },
    {
        "key": "responsable-achats",
        "name": "Responsable achats",
        "family": FAMILY_ADMINISTRATION,
        "mission": "Négocie et engage les achats d'intrants.",
        "responsibilities": "Commandes · fournisseurs · prix",
        "default_role": "responsable-stock",
        "icon": "shopping-cart",
    },
    {
        "key": "responsable-ventes",
        "name": "Responsable ventes",
        "family": FAMILY_ADMINISTRATION,
        "mission": "Commercialise les productions.",
        "responsibilities": "Contrats · livraisons · prix de vente",
        "default_role": "comptable",
        "icon": "hand-coins",
    },
    {
        "key": "assistant-administratif",
        "name": "Assistant administratif",
        "family": FAMILY_ADMINISTRATION,
        "mission": "Appuie l'administration et le classement.",
        "responsibilities": "Saisie · documents · courriers",
        "default_role": "consultation",
        "icon": "file-plus",
    },
]

FUNCTION_BY_KEY: dict[str, FunctionSpec] = {
    spec["key"]: spec for spec in FUNCTIONS
}


# ---------------------------------------------------------------------------
# Rôles applicatifs et matrice RBAC
# ---------------------------------------------------------------------------


class RoleSpec(TypedDict):
    key: str
    name: str
    level: int
    tagline: str
    icon: str
    color_hex: str
    is_system: bool


ROLES: list[RoleSpec] = [
    {
        "key": "proprietaire",
        "name": "Propriétaire",
        "level": 100,
        "tagline": "Accès complet, y compris la gouvernance des accès.",
        "icon": "crown",
        "color_hex": "#fbbf24",
        "is_system": True,
    },
    {
        "key": "chef-exploitation",
        "name": "Chef d'exploitation",
        "level": 80,
        "tagline": "Pilote toute la production et valide les chantiers.",
        "icon": "clipboard-check",
        "color_hex": "#a3e635",
        "is_system": True,
    },
    {
        "key": "responsable-production",
        "name": "Responsable production",
        "level": 70,
        "tagline": "Conduit cultures, interventions et récoltes.",
        "icon": "sprout",
        "color_hex": "#4ade80",
        "is_system": False,
    },
    {
        "key": "responsable-irrigation",
        "name": "Responsable irrigation",
        "level": 60,
        "tagline": "Planifie, exécute et valide les tours d'eau.",
        "icon": "droplets",
        "color_hex": "#38bdf8",
        "is_system": False,
    },
    {
        "key": "responsable-stock",
        "name": "Responsable stock",
        "level": 60,
        "tagline": "Magasin d'intrants, seuils et mouvements.",
        "icon": "package",
        "color_hex": "#c084fc",
        "is_system": False,
    },
    {
        "key": "responsable-materiel",
        "name": "Responsable matériel",
        "level": 60,
        "tagline": "Flotte, maintenance et carburant.",
        "icon": "wrench",
        "color_hex": "#f97316",
        "is_system": False,
    },
    {
        "key": "chef-equipe",
        "name": "Chef d'équipe",
        "level": 45,
        "tagline": "Équipe, missions et parcelles affectées.",
        "icon": "users",
        "color_hex": "#22c55e",
        "is_system": False,
    },
    {
        "key": "ouvrier",
        "name": "Ouvrier agricole",
        "level": 20,
        "tagline": "Tâches et parcelles personnellement affectées.",
        "icon": "shovel",
        "color_hex": "#84cc16",
        "is_system": False,
    },
    {
        "key": "comptable",
        "name": "Comptable",
        "level": 50,
        "tagline": "Achats, ventes, charges et rapports financiers.",
        "icon": "calculator",
        "color_hex": "#facc15",
        "is_system": False,
    },
    {
        "key": "consultation",
        "name": "Consultation",
        "level": 10,
        "tagline": "Lecture seule sur l'exploitation.",
        "icon": "eye",
        "color_hex": "#94a3b8",
        "is_system": True,
    },
]

ROLE_BY_KEY: dict[str, RoleSpec] = {spec["key"]: spec for spec in ROLES}

# Matrice RBAC : rôle → module → actions autorisées.
# La clé "*" en module signifie « tous les modules », la valeur "*" en actions
# signifie « toutes les actions déclarées pour ce module ».
ROLE_MATRIX: dict[str, dict[str, list[str] | str]] = {
    "proprietaire": {"*": "*"},
    "chef-exploitation": {
        "dashboard": "*",
        "exploitations": [ACTION_CONSULTER, ACTION_MODIFIER, ACTION_EXPORTER],
        "parcelles": "*",
        "cultures": "*",
        "semences": "*",
        "interventions": "*",
        "irrigation": "*",
        "fertilisation": "*",
        "traitements": "*",
        "recoltes": "*",
        "stocks": WRITE_ACTIONS + [ACTION_VALIDER],
        "intrants": WRITE_ACTIONS,
        "materiel": WRITE_ACTIONS + [ACTION_AFFECTER],
        "maintenance": "*",
        "carburant": WRITE_ACTIONS,
        "rh": [
            ACTION_CONSULTER,
            ACTION_CREER,
            ACTION_MODIFIER,
            ACTION_AFFECTER,
            ACTION_EXPORTER,
        ],
        "equipes": "*",
        "achats": WRITE_ACTIONS + [ACTION_VALIDER],
        "ventes": [ACTION_CONSULTER, ACTION_EXPORTER],
        "comptabilite": [ACTION_CONSULTER, ACTION_EXPORTER],
        "documents": "*",
        "rapports": "*",
        "cartographie": "*",
        "meteo": "*",
        "parametres": [ACTION_CONSULTER],
        "utilisateurs": [ACTION_CONSULTER, ACTION_AFFECTER, ACTION_EXPORTER],
    },
    "responsable-production": {
        "dashboard": "*",
        "parcelles": WRITE_ACTIONS,
        "cultures": "*",
        "semences": "*",
        "interventions": "*",
        "irrigation": FIELD_ACTIONS,
        "fertilisation": "*",
        "traitements": "*",
        "recoltes": "*",
        "stocks": [ACTION_CONSULTER, ACTION_EXPORTER],
        "intrants": [ACTION_CONSULTER],
        "materiel": [ACTION_CONSULTER],
        "equipes": [ACTION_CONSULTER, ACTION_AFFECTER],
        "documents": WRITE_ACTIONS,
        "rapports": "*",
        "cartographie": WRITE_ACTIONS,
        "meteo": "*",
    },
    "responsable-irrigation": {
        "dashboard": "*",
        "parcelles": [ACTION_CONSULTER],
        "cultures": [ACTION_CONSULTER],
        "interventions": FIELD_ACTIONS + [ACTION_VALIDER],
        "irrigation": "*",
        "equipes": [ACTION_CONSULTER, ACTION_AFFECTER],
        "materiel": [ACTION_CONSULTER],
        "maintenance": [ACTION_CONSULTER, ACTION_CREER],
        "rapports": "*",
        "cartographie": [ACTION_CONSULTER],
        "meteo": "*",
        "documents": [ACTION_CONSULTER],
    },
    "responsable-stock": {
        "dashboard": "*",
        "stocks": "*",
        "intrants": "*",
        "achats": WRITE_ACTIONS,
        "interventions": [ACTION_CONSULTER],
        "traitements": [ACTION_CONSULTER],
        "documents": WRITE_ACTIONS,
        "rapports": "*",
        "meteo": "*",
    },
    "responsable-materiel": {
        "dashboard": "*",
        "materiel": "*",
        "maintenance": "*",
        "carburant": WRITE_ACTIONS,
        "equipes": [ACTION_CONSULTER],
        "interventions": [ACTION_CONSULTER],
        "documents": WRITE_ACTIONS,
        "rapports": "*",
        "meteo": "*",
    },
    "chef-equipe": {
        "dashboard": "*",
        "parcelles": [ACTION_CONSULTER],
        "cultures": [ACTION_CONSULTER],
        "interventions": FIELD_ACTIONS,
        "irrigation": FIELD_ACTIONS,
        "traitements": [ACTION_CONSULTER, ACTION_CREER, ACTION_MODIFIER],
        "recoltes": FIELD_ACTIONS,
        "equipes": [ACTION_CONSULTER, ACTION_AFFECTER],
        "materiel": [ACTION_CONSULTER],
        "meteo": "*",
        "rapports": [ACTION_CONSULTER],
    },
    "ouvrier": {
        "dashboard": [ACTION_CONSULTER],
        "parcelles": [ACTION_CONSULTER],
        "cultures": [ACTION_CONSULTER],
        "interventions": [ACTION_CONSULTER, ACTION_MODIFIER, ACTION_CLOTURER],
        "irrigation": [ACTION_CONSULTER, ACTION_MODIFIER],
        "meteo": "*",
    },
    "comptable": {
        "dashboard": "*",
        "achats": "*",
        "ventes": "*",
        "comptabilite": "*",
        "stocks": [ACTION_CONSULTER, ACTION_EXPORTER],
        "materiel": [ACTION_CONSULTER],
        "rh": [ACTION_CONSULTER, ACTION_EXPORTER],
        "documents": WRITE_ACTIONS,
        "rapports": "*",
    },
    "consultation": {
        "dashboard": [ACTION_CONSULTER],
        "parcelles": [ACTION_CONSULTER],
        "cultures": [ACTION_CONSULTER],
        "interventions": [ACTION_CONSULTER],
        "recoltes": [ACTION_CONSULTER],
        "stocks": [ACTION_CONSULTER],
        "materiel": [ACTION_CONSULTER],
        "rapports": [ACTION_CONSULTER],
        "cartographie": [ACTION_CONSULTER],
        "meteo": [ACTION_CONSULTER],
    },
}


def role_permission_pairs(role_key: str) -> list[tuple[str, str]]:
    """Couples (module, action) accordés à un rôle par la matrice RBAC."""
    matrix = ROLE_MATRIX.get(role_key, {})
    pairs: list[tuple[str, str]] = []
    if "*" in matrix:
        wildcard = matrix["*"]
        for spec in ACCESS_MODULES:
            actions = (
                spec["actions"] if wildcard == "*" else list(wildcard)  # type: ignore[arg-type]
            )
            for action in actions:
                if action in spec["actions"]:
                    pairs.append((spec["key"], action))
        return pairs
    for module_key, actions in matrix.items():
        spec = MODULE_BY_KEY.get(module_key)
        if spec is None:
            continue
        selected = spec["actions"] if actions == "*" else list(actions)  # type: ignore[arg-type]
        for action in selected:
            if action in spec["actions"]:
                pairs.append((spec["key"], action))
    return pairs


# ---------------------------------------------------------------------------
# Périmètres, statuts, MFA et journal
# ---------------------------------------------------------------------------

SCOPE_EXPLOITATION: str = "EXPLOITATION"
SCOPE_SITE: str = "SITE"
SCOPE_SECTEUR: str = "SECTEUR"
SCOPE_PARCELLE: str = "PARCELLE"
SCOPE_CULTURE: str = "CULTURE"
SCOPE_EQUIPE: str = "EQUIPE"
SCOPE_ACTIVITE: str = "ACTIVITE"
SCOPE_CAMPAGNE: str = "CAMPAGNE"
SCOPE_PERSONNEL: str = "PERSONNEL"

SCOPE_LABELS: dict[str, str] = {
    SCOPE_EXPLOITATION: "Toute l'exploitation",
    SCOPE_SITE: "Un site",
    SCOPE_SECTEUR: "Un secteur",
    SCOPE_PARCELLE: "Une parcelle",
    SCOPE_CULTURE: "Une culture",
    SCOPE_EQUIPE: "Une équipe",
    SCOPE_ACTIVITE: "Une activité",
    SCOPE_CAMPAGNE: "Une campagne",
    SCOPE_PERSONNEL: "Données personnelles",
}

SCOPE_ICONS: dict[str, str] = {
    SCOPE_EXPLOITATION: "building-2",
    SCOPE_SITE: "warehouse",
    SCOPE_SECTEUR: "compass",
    SCOPE_PARCELLE: "map",
    SCOPE_CULTURE: "sprout",
    SCOPE_EQUIPE: "users",
    SCOPE_ACTIVITE: "activity",
    SCOPE_CAMPAGNE: "calendar-days",
    SCOPE_PERSONNEL: "user",
}

USER_STATUS_LABELS: dict[str, str] = {
    "ACTIF": "Actif",
    "INACTIF": "Inactif",
    "SUSPENDU": "Suspendu",
    "ARCHIVE": "Archivé",
    "EN_ATTENTE": "En attente",
}

USER_STATUS_TONES: dict[str, str] = {
    "ACTIF": "good",
    "INACTIF": "muted",
    "SUSPENDU": "bad",
    "ARCHIVE": "muted",
    "EN_ATTENTE": "warn",
}

MFA_LABELS: dict[str, str] = {
    "AUCUNE": "Sans MFA",
    "SMS": "Code SMS",
    "APPLICATION": "Application d'authentification",
    "EMAIL": "Code e-mail",
    "CLE_MATERIELLE": "Clé matérielle",
}

DELEGATION_STATUS_LABELS: dict[str, str] = {
    "PLANIFIEE": "Planifiée",
    "ACTIVE": "Active",
    "EXPIREE": "Expirée",
    "REVOQUEE": "Révoquée",
}

SESSION_STATUS_LABELS: dict[str, str] = {
    "ACTIVE": "Session active",
    "EXPIREE": "Session expirée",
    "REVOQUEE": "Session révoquée",
}

ACTIVITY_KINDS: dict[str, str] = {
    "CONNEXION": "Connexion",
    "DECONNEXION": "Déconnexion",
    "CREATION": "Création",
    "MODIFICATION": "Modification",
    "SUPPRESSION": "Suppression",
    "AFFECTATION": "Affectation",
    "VALIDATION": "Validation",
    "ROLE": "Changement de rôle",
    "PERMISSION": "Modification de permission",
    "DELEGATION": "Délégation",
    "REFUS": "Accès refusé",
    "CONSULTATION": "Consultation",
}

ACTIVITY_TONES: dict[str, str] = {
    "CONNEXION": "info",
    "DECONNEXION": "muted",
    "CREATION": "good",
    "MODIFICATION": "warn",
    "SUPPRESSION": "bad",
    "AFFECTATION": "info",
    "VALIDATION": "good",
    "ROLE": "warn",
    "PERMISSION": "warn",
    "DELEGATION": "info",
    "REFUS": "bad",
    "CONSULTATION": "muted",
}

# Motifs de refus renvoyés par les contrôles serveur.
DENY_UNKNOWN_USER: str = "UTILISATEUR_INCONNU"
DENY_INACTIVE_USER: str = "UTILISATEUR_INACTIF"
DENY_NO_PERMISSION: str = "PERMISSION_ABSENTE"
DENY_OUT_OF_SCOPE: str = "HORS_PERIMETRE"
DENY_REASONS: dict[str, str] = {
    DENY_UNKNOWN_USER: "Utilisateur inconnu.",
    DENY_INACTIVE_USER: "Compte inactif, suspendu ou archivé.",
    DENY_NO_PERMISSION: "Aucun rôle ni délégation n'accorde cette action.",
    DENY_OUT_OF_SCOPE: "L'objet visé est hors du périmètre autorisé.",
}


def module_label(key: str) -> str:
    spec = MODULE_BY_KEY.get(key)
    return spec["label"] if spec is not None else key


def action_label(key: str) -> str:
    return ACTION_LABELS.get(key, key)


def role_label(key: str) -> str:
    spec = ROLE_BY_KEY.get(key)
    return spec["name"] if spec is not None else key


def scope_label(key: str) -> str:
    return SCOPE_LABELS.get(key, key)

"""Référentiel de contexte du guide embarqué (aide contextuelle intelligente).

Ce module ne contient QUE des constantes Python : la correspondance entre un
écran de l'application (cockpit, parcelles, cartographie, traitements, employés,
maintenance, charges, recherche, guide) et les catégories éditoriales du Guide
Agricole, ainsi que les « sujets de règle » utilisés pour enrichir pédagogiquement
les messages d'erreur des formulaires (surface, dates, stock, montant, géométrie,
habilitation, récolte, phyto, maintenance, code d'îlot).

Aucune lecture de contenu ici : les articles, procédures, FAQ, termes et règles
sont toujours lus en SQL brut depuis la base (voir `app/states/help_state.py`).
"""

from __future__ import annotations

from typing import TypedDict


class ContextSpec(TypedDict):
    """Contexte d'aide rattaché à un écran de l'application."""

    label: str
    tagline: str
    icon: str
    route: str
    categories: list[str]


class TopicSpec(TypedDict):
    """Sujet de règle de cohérence mobilisé par un message d'erreur."""

    label: str
    icon: str
    hint: str
    codes: list[str]


CONTEXTS: dict[str, ContextSpec] = {
    "cockpit": {
        "label": "Cockpit agronomique",
        "tagline": "Lire les alertes, la météo puis le calendrier.",
        "icon": "layout-dashboard",
        "route": "/",
        "categories": ["fondamentaux", "cultures", "travaux"],
    },
    "parcelles": {
        "label": "Parcelles & cultures",
        "tagline": "Décrire le foncier une fois, bien, pour tout le reste.",
        "icon": "map",
        "route": "/parcelles",
        "categories": ["parcelles", "cultures"],
    },
    "referentiel": {
        "label": "Référentiel cultures",
        "tagline": "Catégorie, culture, espèce, variété : l'herbier de l'exploitation.",
        "icon": "sprout",
        "route": "/referentiel",
        "categories": ["cultures", "parcelles", "fondamentaux"],
    },
    "cartographie": {
        "label": "Cartographie interactive",
        "tagline": "Contours réels, surfaces calculées et historique parcellaire.",
        "icon": "map-pinned",
        "route": "/cartographie",
        "categories": ["parcelles", "fondamentaux"],
    },
    "traitements": {
        "label": "Traitements, stocks & récoltes",
        "tagline": "Planifier, tracer, sortir le stock, mesurer le rendement.",
        "icon": "spray-can",
        "route": "/traitements",
        "categories": [
            "travaux",
            "phytosanitaire",
            "stocks",
            "irrigation",
            "fertilisation",
            "recolte",
        ],
    },
    "employes": {
        "label": "Employés & compétences",
        "tagline": "La bonne personne, habilitée, disponible.",
        "icon": "users-round",
        "route": "/employes",
        "categories": ["personnel", "travaux"],
    },
    "maintenance": {
        "label": "Engins & maintenance",
        "tagline": "Échéances, compteurs et coûts d'atelier.",
        "icon": "wrench",
        "route": "/maintenance",
        "categories": ["materiel", "economie"],
    },
    "charges": {
        "label": "Charges & dépenses",
        "tagline": "Chaque euro rattaché devient une décision.",
        "icon": "coins",
        "route": "/charges",
        "categories": ["economie", "stocks"],
    },
    "recherche": {
        "label": "Recherche globale",
        "tagline": "Retrouver une instance dans toutes les tables métier.",
        "icon": "radar",
        "route": "/recherche",
        "categories": ["fondamentaux", "cultures"],
    },
    "audit": {
        "label": "Audit & diagnostic",
        "tagline": "Modules sains, états à traiter, décisions documentées.",
        "icon": "clipboard-check",
        "route": "/audit",
        "categories": ["fondamentaux", "stocks", "parcelles", "cultures"],
    },
    "guide": {
        "label": "Guide Agricole",
        "tagline": "Double lecture agricole et AgriPro de bout en bout.",
        "icon": "book-open",
        "route": "/guide",
        "categories": ["fondamentaux"],
    },
}

TOPIC_HINTS: dict[str, TopicSpec] = {
    "surface": {
        "label": "Règle de surface",
        "icon": "ruler",
        "hint": (
            "Toutes les doses, tous les coûts et tous les rendements sont "
            "ramenés à l'hectare : une surface nulle, aberrante ou supérieure "
            "à celle de l'îlot rend ces ratios invérifiables."
        ),
        "codes": ["COH-PARC-002", "COH-CULT-001", "ATT-PARC-003"],
    },
    "code": {
        "label": "Règle d'identification",
        "icon": "hash",
        "hint": (
            "Le code d'îlot est la clé de lecture humaine des filtres, de la "
            "carte et des exports : un doublon rattache interventions et "
            "charges à la mauvaise parcelle."
        ),
        "codes": ["COH-PARC-001"],
    },
    "dates": {
        "label": "Règle de chronologie",
        "icon": "calendar-clock",
        "hint": (
            "L'ordre des dates (semis → récolte, planifié → réalisé) alimente "
            "le calendrier et le calcul des cycles : une date inversée produit "
            "des durées négatives et fausse l'analyse des délais."
        ),
        "codes": ["COH-CULT-002", "COH-TRAV-002", "POU-TRAV-001"],
    },
    "geometrie": {
        "label": "Règle de géométrie",
        "icon": "shapes",
        "hint": (
            "Un contour est un polygone WGS84 fermé d'au moins trois sommets : "
            "la surface qu'il calcule sert de contrôle face à la surface "
            "déclarée, avec arbitrage au-delà de 5 % d'écart."
        ),
        "codes": ["ATT-PARC-003", "COH-PARC-002"],
    },
    "stock": {
        "label": "Règle de stock",
        "icon": "package",
        "hint": (
            "Le stock informatique doit refléter le local : une sortie ne "
            "descend jamais sous zéro, un écart se documente par un inventaire "
            "et une casse se déclare en perte pour rester chiffrable."
        ),
        "codes": ["POU-STOCK-001", "ATT-STOCK-002"],
    },
    "phyto": {
        "label": "Règle phytosanitaire",
        "icon": "shield-check",
        "hint": (
            "Cible, produit, dose, surface traitée, vent et délais font la "
            "valeur du registre : au-delà d'environ 19 km/h de vent le chantier "
            "se reporte, et le délai avant récolte doit rester compatible avec "
            "la date de moisson prévue."
        ),
        "codes": ["ATT-PHY-001", "ATT-PHY-002", "COH-PHY-003"],
    },
    "recolte": {
        "label": "Règle de récolte",
        "icon": "wheat",
        "hint": (
            "Le rendement est calculé, jamais saisi : quantité et surface "
            "récoltée doivent être strictement positives, et l'humidité "
            "renseignée pour comparer deux campagnes."
        ),
        "codes": ["COH-RECO-001", "ATT-RECO-002"],
    },
    "montant": {
        "label": "Règle financière",
        "icon": "coins",
        "hint": (
            "Le TTC doit correspondre au HT majoré de la TVA et la date "
            "d'engagement précéder l'échéance : sinon les synthèses de charges "
            "et le suivi de trésorerie divergent."
        ),
        "codes": ["COH-ECO-001", "POU-ECO-002"],
    },
    "habilitation": {
        "label": "Règle d'habilitation",
        "icon": "badge-check",
        "hint": (
            "Compétence, certificat valide et disponibilité conditionnent une "
            "affectation : une habilitation expirée interdit le chantier "
            "réglementé, l'obligation étant individuelle et opposable."
        ),
        "codes": ["COH-PERS-001", "ATT-PERS-002"],
    },
    "maintenance": {
        "label": "Règle d'atelier",
        "icon": "wrench",
        "hint": (
            "Le compteur relevé au passage recale l'échéance suivante : sans "
            "lui le préventif se dérègle, et un contrôle réglementaire échu "
            "interdit l'usage de l'engin."
        ),
        "codes": ["ATT-MAT-001", "POU-MAT-002"],
    },
}

FALLBACK_TOPIC: TopicSpec = {
    "label": "Règle de cohérence",
    "icon": "scale",
    "hint": (
        "Chaque contrôle de saisie protège un indicateur : corriger la donnée "
        "à la source évite de propager l'erreur sur toute la campagne."
    ),
    "codes": ["POU-FOND-001"],
}


class ShortcutSpec(TypedDict):
    """Accès contextuel au référentiel agronomique depuis un écran."""

    label: str
    title: str
    detail: str
    icon: str
    route: str
    cta: str


# Aide contextuelle : depuis quels écrans le référentiel Catégorie → Culture →
# Espèce → Variété doit être accessible, et pour y faire quoi.
CONTEXT_SHORTCUTS: dict[str, ShortcutSpec] = {
    "parcelles": {
        "label": "Aide contextuelle",
        "title": "Choisir l'espèce et la variété dans le référentiel",
        "detail": (
            "Fenêtres de semis et de récolte, cycle, besoin en eau et "
            "rendement visé viennent du référentiel : sélectionnez la variété "
            "plutôt que de ressaisir ces repères."
        ),
        "icon": "sprout",
        "route": "/referentiel",
        "cta": "Référentiel cultures",
    },
    "traitements": {
        "label": "Aide contextuelle",
        "title": "Doses, ravageurs et rendements de référence",
        "detail": (
            "Le référentiel porte les besoins N/P/K, le seuil d'irrigation, "
            "les ravageurs et maladies dominants ainsi que le rendement visé "
            "de chaque espèce cultivée."
        ),
        "icon": "leaf",
        "route": "/referentiel",
        "cta": "Repères agronomiques",
    },
    "audit": {
        "label": "Aide contextuelle",
        "title": "Contrôler la couverture du référentiel cultures",
        "detail": (
            "Catégories, cultures, espèces, variétés et liens vers le "
            "référentiel variétal historique : l'herbier se vérifie écran en "
            "main."
        ),
        "icon": "layers",
        "route": "/referentiel",
        "cta": "Ouvrir le référentiel",
    },
}

FALLBACK_SHORTCUT: ShortcutSpec = {
    "label": "Aide contextuelle",
    "title": "Référentiel Catégorie → Culture → Espèce → Variété",
    "detail": (
        "L'herbier de l'exploitation : familles cultivées, repères "
        "agronomiques par espèce et fiches variétales."
    ),
    "icon": "sprout",
    "route": "/referentiel",
    "cta": "Ouvrir le référentiel",
}


def shortcut_spec(key: str) -> ShortcutSpec:
    """Retourne l'accès contextuel au référentiel pour un écran donné."""
    return CONTEXT_SHORTCUTS.get(key, FALLBACK_SHORTCUT)


def context_spec(key: str) -> ContextSpec:
    """Retourne le contexte demandé, avec repli sur le cockpit."""
    return CONTEXTS.get(key, CONTEXTS["cockpit"])


def topic_spec(key: str) -> TopicSpec:
    """Retourne le sujet de règle demandé, avec repli générique."""
    return TOPIC_HINTS.get(key, FALLBACK_TOPIC)


def topic_label(key: str) -> str:
    return topic_spec(key)["label"]


def topic_hint(key: str) -> str:
    return topic_spec(key)["hint"]


def topic_icon(key: str) -> str:
    return topic_spec(key)["icon"]

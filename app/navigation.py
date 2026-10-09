import reflex as rx
from typing import TypedDict
from urllib.parse import urlencode


class Cockpit(TypedDict):
    key: str
    label: str
    icon: str
    available: bool
    note: str


class NavigationEntry(TypedDict):
    key: str
    page: str
    route: str
    cockpit: str
    domain: str
    label: str
    icon: str
    tab: str
    anchor: str
    href: str


COCKPITS: list[Cockpit] = [
    {
        "key": "global",
        "label": "Global",
        "icon": "house",
        "available": True,
        "note": "Vision de l'exploitation et accès transversaux.",
    },
    {
        "key": "agricole",
        "label": "Agricole",
        "icon": "wheat",
        "available": True,
        "note": "Production, interventions et suivi agronomique.",
    },
    {
        "key": "commercial",
        "label": "Commercial",
        "icon": "briefcase-business",
        "available": True,
        "note": "Relations clients et registres commerciaux existants.",
    },
    {
        "key": "stocks",
        "label": "Stocks & Logistique",
        "icon": "package",
        "available": True,
        "note": "Magasin d'intrants et mouvements existants.",
    },
    {
        "key": "materiel",
        "label": "Matériel & Maintenance",
        "icon": "tractor",
        "available": True,
        "note": "Flotte agricole, atelier et échéances.",
    },
    {
        "key": "rh",
        "label": "Ressources humaines",
        "icon": "users-round",
        "available": True,
        "note": "Employés, compétences et affectations.",
    },
    {
        "key": "financier",
        "label": "Financier",
        "icon": "coins",
        "available": True,
        "note": "Charges et registres financiers CRM existants.",
    },
    {
        "key": "achats",
        "label": "Achats",
        "icon": "shopping-cart",
        "available": True,
        "note": "Achats et relations fournisseurs du CRM.",
    },
    {
        "key": "infrastructures",
        "label": "Infrastructures",
        "icon": "warehouse",
        "available": False,
        "note": "À venir — aucune page dédiée.",
    },
    {
        "key": "elevage",
        "label": "Élevage",
        "icon": "fence",
        "available": False,
        "note": "À venir — aucune page dédiée.",
    },
    {
        "key": "documentaire",
        "label": "Documentaire",
        "icon": "book-open",
        "available": True,
        "note": "Guide documentaire agricole existant, pas une GED.",
    },
    {
        "key": "analytics",
        "label": "Analytics & IA",
        "icon": "chart-no-axes-combined",
        "available": True,
        "note": "Rapports et diagnostics existants uniquement ; aucune IA disponible.",
    },
    {
        "key": "cartographique",
        "label": "Cartographique",
        "icon": "map-pinned",
        "available": True,
        "note": "Carte interactive et contours parcellaires.",
    },
    {
        "key": "planification",
        "label": "Planification",
        "icon": "calendar-days",
        "available": True,
        "note": "Calendrier, chantiers et échéances machine existants.",
    },
    {
        "key": "partenaires",
        "label": "Partenaires",
        "icon": "handshake",
        "available": True,
        "note": "Accès transversal aux mêmes partenaires CRM.",
    },
    {
        "key": "administration",
        "label": "Administration",
        "icon": "shield-check",
        "available": True,
        "note": "Accès, référentiel phénologique et audit ; contrôles métier inchangés.",
    },
    {
        "key": "configuration",
        "label": "Configuration",
        "icon": "settings",
        "available": False,
        "note": "À venir — aucune page dédiée.",
    },
]


def _entry(
    key: str,
    page: str,
    route: str,
    cockpit: str,
    domain: str,
    label: str,
    icon: str,
    tab: str = "",
    anchor: str = "",
) -> NavigationEntry:
    query = (
        urlencode({"cockpit": cockpit, "vue": tab})
        if tab
        else urlencode({"cockpit": cockpit})
    )
    href = f"{route}?{query}"
    if anchor:
        href = f"{href}#{anchor}"
    return {
        "key": key,
        "page": page,
        "route": route,
        "cockpit": cockpit,
        "domain": domain,
        "label": label,
        "icon": icon,
        "tab": tab,
        "anchor": anchor,
        "href": href,
    }


NAVIGATION: list[NavigationEntry] = [
    _entry(
        "global.overview",
        "cockpit",
        "/",
        "global",
        "Pilotage",
        "Vue d'ensemble",
        "house",
    ),
    _entry(
        "global.search",
        "recherche",
        "/recherche",
        "global",
        "Transversal",
        "Recherche globale",
        "search",
    ),
    _entry(
        "agricole.parcelles",
        "parcelles",
        "/parcelles",
        "agricole",
        "Production",
        "Parcelles & cultures",
        "map",
    ),
    _entry(
        "agricole.referentiel",
        "referentiel",
        "/referentiel",
        "agricole",
        "Ressources agricoles",
        "Référentiel cultures",
        "sprout",
    ),
    _entry(
        "agricole.traitements",
        "traitements",
        "/traitements",
        "agricole",
        "Opérations",
        "Traitements & récoltes",
        "spray-can",
    ),
    _entry(
        "agricole.phenologie",
        "phenologie",
        "/phenologie",
        "agricole",
        "Référentiels",
        "Administration phénologie",
        "git-branch",
    ),
    _entry(
        "agricole.rapports",
        "rapports",
        "/rapports",
        "agricole",
        "Suivi agronomique",
        "Rapports phénologiques",
        "chart-column",
    ),
    _entry(
        "commercial.overview",
        "crm",
        "/crm",
        "commercial",
        "Pilotage commercial",
        "CRM & Partenaires",
        "briefcase-business",
        "synthese",
    ),
    _entry(
        "commercial.clients",
        "crm",
        "/crm",
        "commercial",
        "Relations commerciales",
        "Clients",
        "users-round",
        "clients",
    ),
    _entry(
        "commercial.ventes",
        "crm",
        "/crm",
        "commercial",
        "Registres",
        "Ventes",
        "receipt",
        "ventes",
    ),
    _entry(
        "commercial.rapports",
        "crm",
        "/crm",
        "commercial",
        "Performance",
        "Rapports commerciaux",
        "chart-column",
        "rapports",
    ),
    _entry(
        "stocks.magasin",
        "traitements",
        "/traitements",
        "stocks",
        "Intrants & magasin",
        "Stocks, produits & mouvements",
        "package",
        anchor="nav-magasin",
    ),
    _entry(
        "materiel.flotte",
        "maintenance",
        "/maintenance",
        "materiel",
        "Parc matériel & atelier",
        "Engins & maintenance",
        "wrench",
    ),
    _entry(
        "rh.employes",
        "employes",
        "/employes",
        "rh",
        "Personnel agricole",
        "Employés & compétences",
        "users-round",
    ),
    _entry(
        "financier.charges",
        "charges",
        "/charges",
        "financier",
        "Dépenses",
        "Charges & dépenses",
        "coins",
    ),
    _entry(
        "financier.creances",
        "crm",
        "/crm",
        "financier",
        "Registres financiers CRM",
        "Créances",
        "wallet",
        "creances",
    ),
    _entry(
        "financier.dettes",
        "crm",
        "/crm",
        "financier",
        "Registres financiers CRM",
        "Dettes",
        "receipt",
        "dettes",
    ),
    _entry(
        "financier.paiements",
        "crm",
        "/crm",
        "financier",
        "Registres financiers CRM",
        "Paiements",
        "credit-card",
        "paiements",
    ),
    _entry(
        "achats.achats",
        "crm",
        "/crm",
        "achats",
        "Registres fournisseurs",
        "Achats",
        "shopping-cart",
        "achats",
    ),
    _entry(
        "achats.fournisseurs",
        "crm",
        "/crm",
        "achats",
        "Relations fournisseurs",
        "Fournisseurs",
        "truck",
        "fournisseurs",
    ),
    _entry(
        "documentaire.guide",
        "guide",
        "/guide",
        "documentaire",
        "Guide agricole",
        "Guide Agricole",
        "book-open",
    ),
    _entry(
        "analytics.rapports",
        "rapports",
        "/rapports",
        "analytics",
        "Rapports existants",
        "Rapports phénologiques",
        "chart-column",
    ),
    _entry(
        "analytics.audit",
        "audit",
        "/audit",
        "analytics",
        "Diagnostics existants",
        "Audit fonctionnel",
        "clipboard-check",
    ),
    _entry(
        "cartographique.carte",
        "cartographie",
        "/cartographie",
        "cartographique",
        "Géomatique agricole",
        "Cartographie",
        "map-pinned",
    ),
    _entry(
        "planification.chantiers",
        "traitements",
        "/traitements",
        "planification",
        "Planning agricole",
        "Journal & planification des chantiers",
        "calendar-days",
        anchor="nav-planning",
    ),
    _entry(
        "planification.maintenance",
        "maintenance",
        "/maintenance",
        "planification",
        "Planning matériel",
        "Échéances machine",
        "calendar-clock",
        anchor="nav-echeances",
    ),
    _entry(
        "planification.calendrier",
        "cockpit",
        "/",
        "planification",
        "Calendrier global",
        "Calendrier des interventions",
        "calendar-days",
        anchor="nav-calendrier",
    ),
    _entry(
        "partenaires.tiers",
        "crm",
        "/crm",
        "partenaires",
        "Relations transversales",
        "Partenaires",
        "handshake",
        "partenaires",
    ),
    _entry(
        "partenaires.clients",
        "crm",
        "/crm",
        "partenaires",
        "Relations transversales",
        "Clients",
        "users-round",
        "clients",
    ),
    _entry(
        "partenaires.fournisseurs",
        "crm",
        "/crm",
        "partenaires",
        "Relations transversales",
        "Fournisseurs",
        "truck",
        "fournisseurs",
    ),
    _entry(
        "administration.acces",
        "administration",
        "/administration",
        "administration",
        "Sécurité & organisation",
        "Administration & accès",
        "shield-check",
    ),
    _entry(
        "administration.phenologie",
        "phenologie",
        "/phenologie",
        "administration",
        "Référentiels",
        "Administration phénologie",
        "git-branch",
    ),
    _entry(
        "administration.audit",
        "audit",
        "/audit",
        "administration",
        "Contrôle",
        "Audit fonctionnel",
        "clipboard-check",
    ),
]

PRIMARY_KEYS: dict[str, str] = {
    "cockpit": "global.overview",
    "parcelles": "agricole.parcelles",
    "referentiel": "agricole.referentiel",
    "phenologie": "administration.phenologie",
    "traitements": "agricole.traitements",
    "employes": "rh.employes",
    "maintenance": "materiel.flotte",
    "cartographie": "cartographique.carte",
    "rapports": "agricole.rapports",
    "charges": "financier.charges",
    "crm": "commercial.overview",
    "recherche": "global.search",
    "guide": "documentaire.guide",
    "administration": "administration.acces",
    "audit": "administration.audit",
}
ENTRY_BY_KEY: dict[str, NavigationEntry] = {
    entry["key"]: entry for entry in NAVIGATION
}
COCKPIT_BY_KEY: dict[str, Cockpit] = {item["key"]: item for item in COCKPITS}
ROUTE_MATRIX: dict[str, NavigationEntry] = {
    page: ENTRY_BY_KEY[key] for page, key in PRIMARY_KEYS.items()
}


def navigation_coverage(routes: set[str]) -> dict[str, list[str]]:
    covered = {entry["route"] for entry in NAVIGATION}
    return {
        "orphan_routes": sorted(routes - covered),
        "unregistered_routes": sorted(covered - routes),
    }

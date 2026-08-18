"""Constantes métier du référentiel Catégorie → Culture → Espèce → Variété.

Ce module ne contient QUE des constantes Python et des fonctions pures : aucune
lecture de base, aucun composant visuel. Il fournit :

* le vocabulaire normalisé du référentiel (cycles, besoins en eau, tolérances,
  usages, niveaux de qualité) et ses libellés français ;
* la direction visuelle AgriPro (vert nuit, chlorophylle, ambre) à porter par
  les écrans à venir : palette, tonalités de statut, icônes ;
* les profils d'irrigation et de fertilisation par défaut, exploitables par les
  itinéraires techniques, l'irrigation, la fertilisation et les traitements ;
* la correspondance entre le référentiel et les modules consommateurs
  (parcelles, campagnes, itinéraires, irrigation, fertilisation, traitements,
  récoltes, statistiques) ;
* les métriques statistiques attendues sur ce référentiel.
"""

from __future__ import annotations

from typing import TypedDict

# ---------------------------------------------------------------------------
# Direction visuelle AgriPro (à porter par les écrans du référentiel)
# ---------------------------------------------------------------------------

PALETTE: dict[str, str] = {
    "night": "#04120c",
    "surface": "#04140d",
    "chlorophyll": "#a3e635",
    "leaf": "#4ade80",
    "amber": "#fbbf24",
    "ember": "#f97316",
    "sky": "#38bdf8",
    "ink": "#ecfdf5",
}

# Surfaces vitrées et typographie éditoriale réutilisées telles quelles.
GLASS_SURFACE: str = (
    "rounded-3xl border border-white/10 bg-white/[0.03] backdrop-blur-xl"
)
GLASS_CARD: str = "rounded-2xl border border-white/10 bg-white/[0.03]"
EDITORIAL_TITLE: str = "font-['Instrument_Serif'] text-3xl text-emerald-50"
EYEBROW: str = (
    "text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80"
)

# Tonalités de statut agricole « lumineuses », alignées sur le reste de l'app.
TONE_CLASSES: dict[str, str] = {
    "good": (
        "rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 "
        "text-[10px] font-bold text-lime-200 w-fit"
    ),
    "warn": (
        "rounded-full border border-amber-300/30 bg-amber-300/10 px-2 py-0.5 "
        "text-[10px] font-bold text-amber-200 w-fit"
    ),
    "bad": (
        "rounded-full border border-red-400/30 bg-red-500/10 px-2 py-0.5 "
        "text-[10px] font-bold text-red-300 w-fit"
    ),
    "info": (
        "rounded-full border border-sky-300/30 bg-sky-300/10 px-2 py-0.5 "
        "text-[10px] font-bold text-sky-200 w-fit"
    ),
    "muted": (
        "rounded-full border border-white/10 bg-white/5 px-2 py-0.5 "
        "text-[10px] font-semibold text-emerald-100/50 w-fit"
    ),
}


# ---------------------------------------------------------------------------
# Vocabulaire normalisé
# ---------------------------------------------------------------------------

CYCLE_ANNUELLE: str = "ANNUELLE"
CYCLE_BISANNUELLE: str = "BISANNUELLE"
CYCLE_PERENNE: str = "PERENNE"

CYCLE_KEYS: list[str] = [CYCLE_ANNUELLE, CYCLE_BISANNUELLE, CYCLE_PERENNE]

CYCLE_LABELS: dict[str, str] = {
    CYCLE_ANNUELLE: "Cycle annuel",
    CYCLE_BISANNUELLE: "Cycle bisannuel",
    CYCLE_PERENNE: "Culture pérenne",
}

CYCLE_TONES: dict[str, str] = {
    CYCLE_ANNUELLE: "good",
    CYCLE_BISANNUELLE: "info",
    CYCLE_PERENNE: "warn",
}

CYCLE_ICONS: dict[str, str] = {
    CYCLE_ANNUELLE: "rotate-ccw",
    CYCLE_BISANNUELLE: "calendar-range",
    CYCLE_PERENNE: "trees",
}

WATER_FAIBLE: str = "FAIBLE"
WATER_MODEREE: str = "MODEREE"
WATER_ELEVEE: str = "ELEVEE"
WATER_TRES_ELEVEE: str = "TRES_ELEVEE"

WATER_KEYS: list[str] = [
    WATER_FAIBLE,
    WATER_MODEREE,
    WATER_ELEVEE,
    WATER_TRES_ELEVEE,
]

WATER_LABELS: dict[str, str] = {
    WATER_FAIBLE: "Besoin en eau faible",
    WATER_MODEREE: "Besoin en eau modéré",
    WATER_ELEVEE: "Besoin en eau élevé",
    WATER_TRES_ELEVEE: "Besoin en eau très élevé",
}

WATER_SHORT_LABELS: dict[str, str] = {
    WATER_FAIBLE: "Eau faible",
    WATER_MODEREE: "Eau modérée",
    WATER_ELEVEE: "Eau élevée",
    WATER_TRES_ELEVEE: "Eau très élevée",
}

WATER_TONES: dict[str, str] = {
    WATER_FAIBLE: "good",
    WATER_MODEREE: "info",
    WATER_ELEVEE: "warn",
    WATER_TRES_ELEVEE: "bad",
}

TOLERANCE_FAIBLE: str = "FAIBLE"
TOLERANCE_MOYENNE: str = "MOYENNE"
TOLERANCE_BONNE: str = "BONNE"
TOLERANCE_EXCELLENTE: str = "EXCELLENTE"

TOLERANCE_KEYS: list[str] = [
    TOLERANCE_FAIBLE,
    TOLERANCE_MOYENNE,
    TOLERANCE_BONNE,
    TOLERANCE_EXCELLENTE,
]

TOLERANCE_LABELS: dict[str, str] = {
    TOLERANCE_FAIBLE: "Faible",
    TOLERANCE_MOYENNE: "Moyenne",
    TOLERANCE_BONNE: "Bonne",
    TOLERANCE_EXCELLENTE: "Excellente",
}

TOLERANCE_TONES: dict[str, str] = {
    TOLERANCE_FAIBLE: "bad",
    TOLERANCE_MOYENNE: "warn",
    TOLERANCE_BONNE: "good",
    TOLERANCE_EXCELLENTE: "good",
}


# ---------------------------------------------------------------------------
# Profils d'irrigation et de fertilisation par défaut
# ---------------------------------------------------------------------------


class IrrigationProfile(TypedDict):
    """Repères de pilotage hydrique dérivés du besoin en eau de l'espèce."""

    trigger_kpa: float
    dose_mm: float
    interval_days: int
    kc_mid: float
    comment: str


IRRIGATION_PROFILES: dict[str, IrrigationProfile] = {
    WATER_FAIBLE: {
        "trigger_kpa": -80.0,
        "dose_mm": 20.0,
        "interval_days": 14,
        "kc_mid": 0.75,
        "comment": (
            "Conduite le plus souvent en pluvial : n'irriguer qu'en secours "
            "sur les stades sensibles."
        ),
    },
    WATER_MODEREE: {
        "trigger_kpa": -65.0,
        "dose_mm": 25.0,
        "interval_days": 10,
        "kc_mid": 1.0,
        "comment": (
            "Deux à quatre tours d'eau suffisent, positionnés sur floraison "
            "et remplissage."
        ),
    },
    WATER_ELEVEE: {
        "trigger_kpa": -50.0,
        "dose_mm": 30.0,
        "interval_days": 7,
        "kc_mid": 1.15,
        "comment": (
            "Bilan hydrique à tenir à la semaine : tout stress marqué se "
            "traduit directement en rendement."
        ),
    },
    WATER_TRES_ELEVEE: {
        "trigger_kpa": -35.0,
        "dose_mm": 35.0,
        "interval_days": 4,
        "kc_mid": 1.25,
        "comment": (
            "Irrigation quasi continue en saison : privilégier le "
            "goutte-à-goutte et le pilotage par sondes."
        ),
    },
}


class FertilisationProfile(TypedDict):
    """Cadre de raisonnement de la fumure par grande famille de cultures."""

    splits: int
    strategy: str
    organic_first: bool


FERTILISATION_PROFILES: dict[str, FertilisationProfile] = {
    "cereales": {
        "splits": 3,
        "strategy": "Bilan azoté fractionné tallage / épi 1 cm / dernière feuille.",
        "organic_first": False,
    },
    "legumineuses": {
        "splits": 1,
        "strategy": "Pas d'azote de fond : fixation symbiotique, viser P et K.",
        "organic_first": True,
    },
    "oleagineux": {
        "splits": 2,
        "strategy": "Azote de sortie d'hiver puis relais avant floraison, soufre indispensable.",
        "organic_first": False,
    },
    "fourrages": {
        "splits": 3,
        "strategy": "Un apport par cycle de repousse, potasse dominante.",
        "organic_first": True,
    },
    "maraichage": {
        "splits": 4,
        "strategy": "Fertigation régulière, pilotage par conductivité de la solution.",
        "organic_first": True,
    },
    "tubercules": {
        "splits": 2,
        "strategy": "Fond de fumure riche en potasse puis relais à la tubérisation.",
        "organic_first": True,
    },
    "dattes": {
        "splits": 3,
        "strategy": "Fumier de fond en hiver, puis azote et potasse au nouaison et à la véraison.",
        "organic_first": True,
    },
    "arboriculture": {
        "splits": 3,
        "strategy": "Apports post-récolte, débourrement et grossissement du fruit.",
        "organic_first": True,
    },
    "agrumes": {
        "splits": 4,
        "strategy": "Fertigation étalée de la floraison au grossissement, oligo-éléments suivis.",
        "organic_first": True,
    },
    "vigne": {
        "splits": 2,
        "strategy": "Entretien modéré : azote maîtrisé, potasse et magnésie surveillées.",
        "organic_first": True,
    },
    "industrielles": {
        "splits": 2,
        "strategy": "Fond de fumure complet puis relais azoté selon reliquat.",
        "organic_first": False,
    },
    "aromatiques": {
        "splits": 2,
        "strategy": "Fumure légère : un excès d'azote dilue les huiles essentielles.",
        "organic_first": True,
    },
    "epices": {
        "splits": 2,
        "strategy": (
            "Fumure de fond organique puis un seul relais azoté : la richesse "
            "en principes aromatiques primerait sur la biomasse."
        ),
        "organic_first": True,
    },
    "tropicales": {
        "splits": 4,
        "strategy": (
            "Fertigation étalée sur toute la saison de croissance, potasse "
            "dominante et oligo-éléments suivis (bore, zinc, fer)."
        ),
        "organic_first": True,
    },
}

DEFAULT_FERTILISATION: FertilisationProfile = {
    "splits": 2,
    "strategy": "Bilan simple : besoins de la culture moins fournitures du sol.",
    "organic_first": True,
}


# ---------------------------------------------------------------------------
# Modules consommateurs du référentiel
# ---------------------------------------------------------------------------


class ConsumerSpec(TypedDict):
    """Module de l'application qui exploitera le référentiel."""

    key: str
    label: str
    route: str
    icon: str
    usage: str


CATALOG_CONSUMERS: list[ConsumerSpec] = [
    {
        "key": "parcelles",
        "label": "Parcelles & cultures",
        "route": "/parcelles",
        "icon": "map",
        "usage": "Choisir l'espèce et la variété implantées sur l'îlot.",
    },
    {
        "key": "campagnes",
        "label": "Campagnes & assolement",
        "route": "/parcelles",
        "icon": "calendar-range",
        "usage": "Positionner semis et récolte à partir des fenêtres du référentiel.",
    },
    {
        "key": "itineraires",
        "label": "Itinéraires techniques",
        "route": "/traitements",
        "icon": "clipboard-list",
        "usage": "Dérouler les chantiers types selon le cycle de l'espèce.",
    },
    {
        "key": "irrigation",
        "label": "Irrigation",
        "route": "/traitements",
        "icon": "droplets",
        "usage": "Seuil de déclenchement, dose et Kc issus du besoin en eau.",
    },
    {
        "key": "fertilisation",
        "label": "Fertilisation",
        "route": "/traitements",
        "icon": "flask-conical",
        "usage": "Besoins N/P/K et fractionnement de référence par espèce.",
    },
    {
        "key": "traitements",
        "label": "Protection des cultures",
        "route": "/traitements",
        "icon": "shield-check",
        "usage": "Ravageurs et maladies dominants attendus sur l'espèce.",
    },
    {
        "key": "recoltes",
        "label": "Récoltes & rendements",
        "route": "/traitements",
        "icon": "wheat",
        "usage": "Rendement visé et qualité attendue de la variété.",
    },
    {
        "key": "statistiques",
        "label": "Statistiques & audit",
        "route": "/audit",
        "icon": "chart-no-axes-column",
        "usage": "Agréger surfaces et performances par catégorie et par espèce.",
    },
]


class MetricSpec(TypedDict):
    """Métrique statistique attendue sur le référentiel."""

    key: str
    label: str
    unit: str
    icon: str


CATALOG_METRICS: list[MetricSpec] = [
    {
        "key": "categories",
        "label": "Catégories",
        "unit": "familles",
        "icon": "layers",
    },
    {
        "key": "cultures",
        "label": "Cultures",
        "unit": "cultures",
        "icon": "sprout",
    },
    {
        "key": "species",
        "label": "Espèces",
        "unit": "espèces",
        "icon": "leaf",
    },
    {
        "key": "varieties",
        "label": "Variétés",
        "unit": "variétés",
        "icon": "flower-2",
    },
    {
        "key": "linked",
        "label": "Variétés reliées au référentiel historique",
        "unit": "liens",
        "icon": "link",
    },
    {
        "key": "perennial",
        "label": "Cultures pérennes",
        "unit": "cultures",
        "icon": "trees",
    },
]


# ---------------------------------------------------------------------------
# Périmètre du référentiel : catégories attendues
# ---------------------------------------------------------------------------

# Clés stables des catégories du référentiel, dans l'ordre d'affichage.
# Toute nouvelle catégorie doit être ajoutée ici ET dans `app/seed_catalog.py`.
CATALOG_CATEGORY_KEYS: list[str] = [
    "cereales",
    "legumineuses",
    "oleagineux",
    "fourrages",
    "maraichage",
    "tubercules",
    "dattes",
    "arboriculture",
    "agrumes",
    "vigne",
    "industrielles",
    "aromatiques",
    "epices",
    "tropicales",
]

# Doublons volontaires du référentiel : certaines cultures sont attendues dans
# plusieurs catégories parce que l'exploitation les raisonne différemment selon
# le débouché (la pomme de terre est un tubercule ET un légume de maraîchage,
# le soja est une légumineuse ET un oléagineux, etc.).
# Chaque entrée associe un fragment de nom de culture (en minuscules, sans
# ambiguïté) aux catégories dans lesquelles ce fragment DOIT apparaître.
CROSS_CATEGORY_CULTURES: list[tuple[str, list[str]]] = [
    ("pomme de terre", ["maraichage", "tubercules"]),
    ("carotte", ["maraichage", "tubercules"]),
    ("soja", ["legumineuses", "oleagineux"]),
    ("olivier", ["arboriculture", "oleagineux"]),
    ("fenouil", ["maraichage", "aromatiques"]),
    ("coriandre", ["aromatiques", "epices"]),
    ("piment", ["maraichage", "epices"]),
    ("maïs", ["cereales", "fourrages"]),
    ("lin", ["oleagineux", "industrielles"]),
]

CATALOG_CATEGORY_LABELS: dict[str, str] = {
    "cereales": "Céréales & graminées",
    "legumineuses": "Légumineuses & protéagineux",
    "oleagineux": "Oléagineux",
    "fourrages": "Fourrages & prairies",
    "maraichage": "Cultures maraîchères & légumes",
    "tubercules": "Tubercules & racines",
    "dattes": "Dattes & palmier dattier",
    "arboriculture": "Arboriculture fruitière",
    "agrumes": "Agrumes",
    "vigne": "Viticulture & raisin",
    "industrielles": "Cultures industrielles",
    "aromatiques": "Plantes aromatiques & médicinales",
    "epices": "Plantes à épices",
    "tropicales": "Cultures tropicales & subtropicales",
}


# ---------------------------------------------------------------------------
# Repères propres à la catégorie Dattes / palmier dattier
# ---------------------------------------------------------------------------

DATE_CATEGORY_KEY: str = "dattes"

# Variétés de palmier dattier exigées par le référentiel.
DATE_VARIETY_NAMES: list[str] = [
    "Deglet Nour",
    "Mech Degla",
    "Ghars",
    "Degla Beida",
    "Tafezouine",
]

# Familles de consistance de la datte, utilisées pour la qualité et le stockage.
DATE_CONSISTENCIES: dict[str, str] = {
    "MOLLE": "Datte molle",
    "DEMI_MOLLE": "Datte demi-molle",
    "SECHE": "Datte sèche",
}


# ---------------------------------------------------------------------------
# Fonctions utilitaires (pures)
# ---------------------------------------------------------------------------


def cycle_label(key: str) -> str:
    return CYCLE_LABELS.get(key, key)


def cycle_tone(key: str) -> str:
    return CYCLE_TONES.get(key, "muted")


def cycle_icon(key: str) -> str:
    return CYCLE_ICONS.get(key, "sprout")


def water_label(key: str) -> str:
    return WATER_LABELS.get(key, key)


def water_short_label(key: str) -> str:
    return WATER_SHORT_LABELS.get(key, key)


def water_tone(key: str) -> str:
    return WATER_TONES.get(key, "muted")


def tolerance_label(key: str) -> str:
    return TOLERANCE_LABELS.get(key, key)


def tolerance_tone(key: str) -> str:
    return TOLERANCE_TONES.get(key, "muted")


def irrigation_profile(water_need: str) -> IrrigationProfile:
    """Profil hydrique de référence pour un besoin en eau donné."""
    return IRRIGATION_PROFILES.get(
        water_need, IRRIGATION_PROFILES[WATER_MODEREE]
    )


def fertilisation_profile(category_key: str) -> FertilisationProfile:
    """Cadre de fumure de référence pour une catégorie du référentiel."""
    return FERTILISATION_PROFILES.get(category_key, DEFAULT_FERTILISATION)


def cycle_weeks(days_min: int, days_max: int) -> str:
    """Durée de cycle exprimée en semaines pour l'affichage."""
    if days_min <= 0 and days_max <= 0:
        return "—"
    low = max(0, days_min) // 7
    high = max(days_min, days_max) // 7
    if low == high:
        return f"{high} semaines"
    return f"{low} à {high} semaines"

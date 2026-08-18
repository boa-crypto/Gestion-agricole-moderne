"""Référentiel phénologique multicultures : constantes et fonctions pures.

Ce module ne contient QUE des constantes Python et des fonctions pures : aucune
lecture de base, aucun composant visuel. Il porte :

* le vocabulaire normalisé du suivi phénologique (systèmes de notation, statuts
  d'observation, source de l'information, domaines de recommandation, niveaux
  de confiance, types de média) et ses libellés français ;
* les **cycles distincts par culture** : chaque culture possède son propre
  référentiel de stades ordonnés. Il n'existe volontairement AUCUNE liste
  globale unique de stades ;
* les fonctions pures réutilisables par les étapes suivantes : normalisation
  d'un libellé de stade, progression, qualification d'un écart de durée,
  confiance d'un stade probable.

Direction visuelle inchangée (AgriPro vert nuit, chlorophylle / ambre, surfaces
vitrées) : les tonalités exposées ici réutilisent le vocabulaire de
`app/catalog_reference.py` et ne sont consommées qu'ultérieurement par l'UI.
"""

from __future__ import annotations

from typing import TypedDict

# ---------------------------------------------------------------------------
# Vocabulaire normalisé
# ---------------------------------------------------------------------------

SYSTEM_BBCH: str = "BBCH"
SYSTEM_LOCAL: str = "LOCAL"
SYSTEM_MIXTE: str = "MIXTE"

SYSTEM_KEYS: list[str] = [SYSTEM_BBCH, SYSTEM_LOCAL, SYSTEM_MIXTE]

SYSTEM_LABELS: dict[str, str] = {
    SYSTEM_BBCH: "Échelle BBCH",
    SYSTEM_LOCAL: "Vocabulaire local",
    SYSTEM_MIXTE: "BBCH et vocabulaire local",
}

STATUS_PROPOSE: str = "PROPOSE"
STATUS_CONFIRME: str = "CONFIRME"
STATUS_CORRIGE: str = "CORRIGE"
STATUS_REJETE: str = "REJETE"

OBSERVATION_STATUS_KEYS: list[str] = [
    STATUS_PROPOSE,
    STATUS_CONFIRME,
    STATUS_CORRIGE,
    STATUS_REJETE,
]

OBSERVATION_STATUS_LABELS: dict[str, str] = {
    STATUS_PROPOSE: "Proposé",
    STATUS_CONFIRME: "Confirmé",
    STATUS_CORRIGE: "Corrigé",
    STATUS_REJETE: "Écarté",
}

OBSERVATION_STATUS_TONES: dict[str, str] = {
    STATUS_PROPOSE: "info",
    STATUS_CONFIRME: "good",
    STATUS_CORRIGE: "warn",
    STATUS_REJETE: "muted",
}

SOURCE_HUMAINE: str = "HUMAINE"
SOURCE_SYSTEME: str = "SYSTEME"
SOURCE_IMPORT: str = "IMPORT"

OBSERVATION_SOURCE_KEYS: list[str] = [
    SOURCE_HUMAINE,
    SOURCE_SYSTEME,
    SOURCE_IMPORT,
]

OBSERVATION_SOURCE_LABELS: dict[str, str] = {
    SOURCE_HUMAINE: "Observation de terrain",
    SOURCE_SYSTEME: "Stade probable calculé",
    SOURCE_IMPORT: "Import de référentiel",
}

DOMAIN_IRRIGATION: str = "IRRIGATION"
DOMAIN_FERTILISATION: str = "FERTILISATION"
DOMAIN_TRAITEMENT: str = "TRAITEMENT"
DOMAIN_SURVEILLANCE: str = "SURVEILLANCE"
DOMAIN_TRAVAIL_DU_SOL: str = "TRAVAIL_DU_SOL"
DOMAIN_RECOLTE: str = "RECOLTE"
DOMAIN_AUTRE: str = "AUTRE"

RECOMMENDATION_DOMAIN_KEYS: list[str] = [
    DOMAIN_IRRIGATION,
    DOMAIN_FERTILISATION,
    DOMAIN_TRAITEMENT,
    DOMAIN_SURVEILLANCE,
    DOMAIN_TRAVAIL_DU_SOL,
    DOMAIN_RECOLTE,
    DOMAIN_AUTRE,
]

RECOMMENDATION_DOMAIN_LABELS: dict[str, str] = {
    DOMAIN_IRRIGATION: "Irrigation",
    DOMAIN_FERTILISATION: "Fertilisation",
    DOMAIN_TRAITEMENT: "Protection des cultures",
    DOMAIN_SURVEILLANCE: "Surveillance",
    DOMAIN_TRAVAIL_DU_SOL: "Travail du sol",
    DOMAIN_RECOLTE: "Récolte",
    DOMAIN_AUTRE: "Autre",
}

RECOMMENDATION_DOMAIN_ICONS: dict[str, str] = {
    DOMAIN_IRRIGATION: "droplets",
    DOMAIN_FERTILISATION: "flask-conical",
    DOMAIN_TRAITEMENT: "shield-check",
    DOMAIN_SURVEILLANCE: "eye",
    DOMAIN_TRAVAIL_DU_SOL: "shovel",
    DOMAIN_RECOLTE: "wheat",
    DOMAIN_AUTRE: "circle-dot",
}

# Niveau de confiance d'une recommandation : rien n'est prescriptif par défaut.
CONFIDENCE_INDICATIVE: str = "INDICATIVE"
CONFIDENCE_VALIDEE: str = "VALIDEE"
CONFIDENCE_REGLEMENTAIRE: str = "REGLEMENTAIRE"

CONFIDENCE_KEYS: list[str] = [
    CONFIDENCE_INDICATIVE,
    CONFIDENCE_VALIDEE,
    CONFIDENCE_REGLEMENTAIRE,
]

CONFIDENCE_LABELS: dict[str, str] = {
    CONFIDENCE_INDICATIVE: "Information générale, à vérifier",
    CONFIDENCE_VALIDEE: "Validée par la cellule agronomique",
    CONFIDENCE_REGLEMENTAIRE: "Encadrée par une source réglementaire",
}

MEDIA_PHOTO: str = "PHOTO"
MEDIA_DOCUMENT: str = "DOCUMENT"
MEDIA_AUTRE: str = "AUTRE"

MEDIA_KIND_KEYS: list[str] = [MEDIA_PHOTO, MEDIA_DOCUMENT, MEDIA_AUTRE]

MEDIA_KIND_LABELS: dict[str, str] = {
    MEDIA_PHOTO: "Photographie",
    MEDIA_DOCUMENT: "Document",
    MEDIA_AUTRE: "Pièce jointe",
}

# Qualification d'un écart de durée dans un stade (non prescriptive).
DEVIATION_NORMAL: str = "NORMAL"
DEVIATION_COURT: str = "COURT"
DEVIATION_LONG: str = "LONG"
DEVIATION_INCONNU: str = "INCONNU"

DEVIATION_LABELS: dict[str, str] = {
    DEVIATION_NORMAL: "Durée conforme aux repères",
    DEVIATION_COURT: "Stade plus court que prévu, à vérifier",
    DEVIATION_LONG: "Stade plus long que prévu, à vérifier",
    DEVIATION_INCONNU: "Durée indicative non renseignée",
}

DEVIATION_TONES: dict[str, str] = {
    DEVIATION_NORMAL: "good",
    DEVIATION_COURT: "info",
    DEVIATION_LONG: "warn",
    DEVIATION_INCONNU: "muted",
}


# ---------------------------------------------------------------------------
# Cycles phénologiques : un référentiel PAR CULTURE
# ---------------------------------------------------------------------------


class StageSpec(TypedDict, total=False):
    """Stade ordonné d'un profil phénologique."""

    key: str
    name: str
    bbch: str
    description: str
    recognition: str
    watchpoints: str
    common_errors: str
    days_min: int
    days_max: int
    is_critical: bool
    icon: str
    color_hex: str
    recommendations: list[dict[str, str]]


class ProfileSpec(TypedDict, total=False):
    """Profil phénologique rattaché à une culture, une espèce ou une variété."""

    key: str
    name: str
    culture_key: str
    species_key: str
    variety_key: str
    system: str
    summary: str
    source: str
    is_default: bool
    stages: list[StageSpec]


def _reco(
    domain: str,
    title: str,
    statement: str,
    confidence: str = CONFIDENCE_INDICATIVE,
    source: str = "Référentiel agronomique AgriPro",
) -> dict[str, str]:
    """Recommandation NON prescriptive attachée à un stade."""
    return {
        "domain": domain,
        "title": title,
        "statement": statement,
        "confidence": confidence,
        "source": source,
    }


# Clés de culture : elles reprennent la convention du référentiel structuré
# (`app/seed_catalog.py`) : « <catégorie>--<culture> ».
PHENOLOGY_PROFILES: list[ProfileSpec] = [
    # ------------------------------------------------------------------
    # Blé : cycle céréalier noté en BBCH
    # ------------------------------------------------------------------
    {
        "key": "phen-ble",
        "name": "Cycle phénologique du blé",
        "culture_key": "cereales--ble",
        "system": SYSTEM_MIXTE,
        "summary": (
            "Germination → Levée → Tallage → Montaison → Épiaison → "
            "Floraison → Remplissage → Maturation."
        ),
        "source": "Échelle BBCH céréales à paille",
        "is_default": True,
        "stages": [
            {
                "key": "germination",
                "name": "Germination",
                "bbch": "BBCH 00-09",
                "description": "Imbibition du grain puis sortie du coléoptile.",
                "recognition": "Grain gonflé, radicelle et coléoptile visibles.",
                "watchpoints": "Humidité du lit de semence, attaques de limaces.",
                "days_min": 7,
                "days_max": 15,
                "icon": "sprout",
                "color_hex": "#a3e635",
                "recommendations": [
                    _reco(
                        DOMAIN_SURVEILLANCE,
                        "Contrôler la régularité de la levée",
                        "Compter les pieds sur plusieurs placettes pour "
                        "estimer le peuplement réellement implanté.",
                    ),
                ],
            },
            {
                "key": "levee",
                "name": "Levée",
                "bbch": "BBCH 10-13",
                "description": "Première à troisième feuille étalée.",
                "recognition": "Lignes de semis nettement visibles.",
                "watchpoints": "Pucerons vecteurs de viroses, ravageurs du sol.",
                "days_min": 10,
                "days_max": 20,
                "icon": "seedling",
                "color_hex": "#84cc16",
            },
            {
                "key": "tallage",
                "name": "Tallage",
                "bbch": "BBCH 21-29",
                "description": (
                    "Émission des talles : le peuplement épis se construit."
                ),
                "recognition": "Plusieurs brins par pied à la base de la plante.",
                "watchpoints": "Concurrence des adventices, reliquat azoté.",
                "common_errors": (
                    "Apporter tout l'azote au tallage : la fraction est "
                    "mieux valorisée plus tard dans le cycle."
                ),
                "days_min": 30,
                "days_max": 70,
                "is_critical": True,
                "icon": "wheat",
                "color_hex": "#bef264",
                "recommendations": [
                    _reco(
                        DOMAIN_FERTILISATION,
                        "Positionner la première fraction azotée",
                        "Le bilan prévisionnel de l'exploitation détermine la "
                        "dose : cette information ne remplace pas le plan de "
                        "fumure validé.",
                    ),
                    _reco(
                        DOMAIN_SURVEILLANCE,
                        "Estimer le nombre de talles",
                        "Le peuplement de talles conditionne le nombre d'épis "
                        "au mètre carré.",
                    ),
                ],
            },
            {
                "key": "montaison",
                "name": "Montaison",
                "bbch": "BBCH 30-39",
                "description": "Épi 1 cm puis élongation des entre-nœuds.",
                "recognition": "Épi palpable dans la gaine, tige qui s'allonge.",
                "watchpoints": "Septoriose, rouilles, risque de verse.",
                "days_min": 25,
                "days_max": 45,
                "is_critical": True,
                "icon": "arrow-up",
                "color_hex": "#4ade80",
                "recommendations": [
                    _reco(
                        DOMAIN_TRAITEMENT,
                        "Surveiller la pression foliaire",
                        "Noter la maladie dominante sur les trois dernières "
                        "feuilles avant toute décision de protection.",
                    ),
                ],
            },
            {
                "key": "epiaison",
                "name": "Épiaison",
                "bbch": "BBCH 51-59",
                "description": "Sortie de l'épi hors de la gaine.",
                "recognition": "Épis visibles au-dessus du feuillage.",
                "watchpoints": "Fusariose si pluies, cécidomyies.",
                "days_min": 7,
                "days_max": 14,
                "is_critical": True,
                "icon": "wheat",
                "color_hex": "#facc15",
            },
            {
                "key": "floraison",
                "name": "Floraison",
                "bbch": "BBCH 61-69",
                "description": "Émission des anthères, fécondation des fleurs.",
                "recognition": "Anthères jaunes au tiers médian de l'épi.",
                "watchpoints": "Fusariose des épis par temps humide.",
                "days_min": 5,
                "days_max": 12,
                "is_critical": True,
                "icon": "flower-2",
                "color_hex": "#fbbf24",
            },
            {
                "key": "remplissage",
                "name": "Remplissage du grain",
                "bbch": "BBCH 71-77",
                "description": "Grain laiteux puis pâteux.",
                "recognition": "Grain qui s'écrase en laissant un lait épais.",
                "watchpoints": "Stress hydrique et thermique, pucerons des épis.",
                "days_min": 20,
                "days_max": 35,
                "icon": "droplets",
                "color_hex": "#f59e0b",
                "recommendations": [
                    _reco(
                        DOMAIN_IRRIGATION,
                        "Sécuriser la fin de cycle si irrigable",
                        "Le bilan hydrique de la parcelle guide la décision : "
                        "aucune dose n'est proposée automatiquement.",
                    ),
                ],
            },
            {
                "key": "maturation",
                "name": "Maturation",
                "bbch": "BBCH 83-92",
                "description": "Grain dur, plante desséchée.",
                "recognition": "Grain incisable à l'ongle sans laisser de trace.",
                "watchpoints": "Humidité du grain, risque de verse et d'égrenage.",
                "days_min": 10,
                "days_max": 20,
                "icon": "sun",
                "color_hex": "#d97706",
                "recommendations": [
                    _reco(
                        DOMAIN_RECOLTE,
                        "Programmer le chantier de récolte",
                        "Contrôler l'humidité du grain avant de mobiliser la "
                        "moissonneuse.",
                    ),
                ],
            },
        ],
    },
    # Variante d'espèce : le blé dur est légèrement plus précoce.
    {
        "key": "phen-ble-dur",
        "name": "Cycle phénologique du blé dur",
        "culture_key": "cereales--ble",
        "species_key": "cereales--ble--ble-dur",
        "system": SYSTEM_MIXTE,
        "summary": (
            "Même enchaînement que le blé tendre, avec un cycle plus court "
            "et une vigilance accrue au remplissage (mitadinage)."
        ),
        "source": "Échelle BBCH céréales à paille",
        "stages": [
            {
                "key": "germination",
                "name": "Germination",
                "bbch": "BBCH 00-09",
                "days_min": 6,
                "days_max": 13,
                "description": "Imbibition puis sortie du coléoptile.",
            },
            {
                "key": "levee",
                "name": "Levée",
                "bbch": "BBCH 10-13",
                "days_min": 8,
                "days_max": 18,
                "description": "Première à troisième feuille étalée.",
            },
            {
                "key": "tallage",
                "name": "Tallage",
                "bbch": "BBCH 21-29",
                "days_min": 25,
                "days_max": 60,
                "is_critical": True,
                "description": "Construction du peuplement épis.",
            },
            {
                "key": "montaison",
                "name": "Montaison",
                "bbch": "BBCH 30-39",
                "days_min": 20,
                "days_max": 40,
                "is_critical": True,
                "description": "Élongation des entre-nœuds.",
            },
            {
                "key": "epiaison",
                "name": "Épiaison",
                "bbch": "BBCH 51-59",
                "days_min": 6,
                "days_max": 12,
                "description": "Sortie de l'épi hors de la gaine.",
            },
            {
                "key": "floraison",
                "name": "Floraison",
                "bbch": "BBCH 61-69",
                "days_min": 5,
                "days_max": 10,
                "is_critical": True,
                "description": "Fécondation des fleurs.",
            },
            {
                "key": "remplissage",
                "name": "Remplissage du grain",
                "bbch": "BBCH 71-77",
                "days_min": 18,
                "days_max": 30,
                "description": "Grain laiteux puis pâteux.",
                "watchpoints": (
                    "Un déficit azoté de fin de cycle se traduit par du "
                    "mitadinage sanctionné en semoulerie."
                ),
            },
            {
                "key": "maturation",
                "name": "Maturation",
                "bbch": "BBCH 83-92",
                "days_min": 8,
                "days_max": 18,
                "description": "Grain vitreux et dur.",
            },
        ],
    },
    # ------------------------------------------------------------------
    # Tomate : cycle maraîcher à nouaison
    # ------------------------------------------------------------------
    {
        "key": "phen-tomate",
        "name": "Cycle phénologique de la tomate",
        "culture_key": "maraichage--tomate",
        "system": SYSTEM_LOCAL,
        "summary": (
            "Germination → Levée → Croissance végétative → Floraison → "
            "Nouaison → Développement du fruit → Véraison → Maturation."
        ),
        "source": "Vocabulaire maraîcher AgriPro",
        "is_default": True,
        "stages": [
            {
                "key": "germination",
                "name": "Germination",
                "days_min": 5,
                "days_max": 12,
                "description": "Sortie de la radicelle puis des cotylédons.",
                "recognition": "Cotylédons ouverts en pépinière.",
                "watchpoints": "Fonte des semis, température du substrat.",
            },
            {
                "key": "levee",
                "name": "Levée",
                "days_min": 7,
                "days_max": 15,
                "description": "Première vraie feuille étalée.",
            },
            {
                "key": "croissance-vegetative",
                "name": "Croissance végétative",
                "days_min": 20,
                "days_max": 40,
                "description": "Mise en place de la charpente et du feuillage.",
                "watchpoints": "Aleurodes, acariens, équilibre azote / eau.",
                "recommendations": [
                    _reco(
                        DOMAIN_TRAVAIL_DU_SOL,
                        "Tutorage et palissage",
                        "Installer le palissage avant que les tiges ne "
                        "s'affaissent.",
                    ),
                ],
            },
            {
                "key": "floraison",
                "name": "Floraison",
                "days_min": 10,
                "days_max": 25,
                "is_critical": True,
                "description": "Ouverture des premiers bouquets floraux.",
                "recognition": "Fleurs jaunes ouvertes sur le premier bouquet.",
                "watchpoints": "Coulure par excès de chaleur, pollinisation.",
            },
            {
                "key": "nouaison",
                "name": "Nouaison",
                "days_min": 7,
                "days_max": 20,
                "is_critical": True,
                "description": (
                    "Transformation de la fleur fécondée en jeune fruit."
                ),
                "recognition": (
                    "Petits fruits verts de la taille d'un pois derrière la "
                    "fleur fanée."
                ),
                "watchpoints": (
                    "Régularité de l'irrigation, nécrose apicale, coulure."
                ),
                "common_errors": (
                    "Confondre nouaison et floraison : la nouaison se "
                    "constate sur le fruit, pas sur la fleur."
                ),
                "icon": "cherry",
                "color_hex": "#4ade80",
                "recommendations": [
                    _reco(
                        DOMAIN_IRRIGATION,
                        "Éviter les à-coups hydriques",
                        "L'irrégularité de l'apport favorise nécrose apicale "
                        "et éclatement : la dose reste définie par le pilotage "
                        "de la parcelle.",
                    ),
                    _reco(
                        DOMAIN_SURVEILLANCE,
                        "Contrôler la charge en fruits",
                        "Compter les fruits noués par bouquet pour suivre la "
                        "régularité de la production.",
                    ),
                ],
            },
            {
                "key": "developpement-fruit",
                "name": "Développement du fruit",
                "days_min": 15,
                "days_max": 35,
                "description": "Grossissement des fruits noués.",
                "watchpoints": "Mildiou, oïdium, fertigation.",
            },
            {
                "key": "veraison",
                "name": "Véraison",
                "days_min": 7,
                "days_max": 15,
                "description": "Changement de couleur des fruits.",
                "recognition": "Passage du vert au jaune puis au rouge.",
            },
            {
                "key": "maturation",
                "name": "Maturation",
                "days_min": 10,
                "days_max": 60,
                "description": "Récoltes échelonnées des fruits mûrs.",
                "recommendations": [
                    _reco(
                        DOMAIN_RECOLTE,
                        "Échelonner les passages de récolte",
                        "La maturité s'étale : plusieurs passages sont "
                        "nécessaires sur le même bouquet.",
                    ),
                ],
            },
        ],
    },
    # ------------------------------------------------------------------
    # Olivier : cycle pérenne, SANS tallage (contrôle de cohérence)
    # ------------------------------------------------------------------
    {
        "key": "phen-olivier",
        "name": "Cycle phénologique de l'olivier",
        "culture_key": "arboriculture--olivier",
        "system": SYSTEM_LOCAL,
        "summary": (
            "Repos végétatif → Reprise → Floraison → Nouaison → "
            "Développement du fruit → Durcissement du noyau → Véraison → "
            "Maturation."
        ),
        "source": "Vocabulaire oléicole AgriPro",
        "is_default": True,
        "stages": [
            {
                "key": "repos-vegetatif",
                "name": "Repos végétatif",
                "days_min": 60,
                "days_max": 120,
                "description": "Arrêt de croissance hivernal.",
                "watchpoints": "Taille de formation, œil de paon.",
                "recommendations": [
                    _reco(
                        DOMAIN_TRAVAIL_DU_SOL,
                        "Période favorable à la taille",
                        "La taille d'hiver se raisonne selon la charge de "
                        "l'année précédente.",
                    ),
                ],
            },
            {
                "key": "reprise",
                "name": "Reprise végétative",
                "days_min": 20,
                "days_max": 45,
                "description": "Débourrement des bourgeons et croissance.",
            },
            {
                "key": "floraison",
                "name": "Floraison",
                "days_min": 7,
                "days_max": 20,
                "is_critical": True,
                "description": "Ouverture des inflorescences.",
                "recognition": "Grappes de fleurs blanches sur bois d'un an.",
                "watchpoints": "Vent chaud et sec, teigne de l'olivier.",
            },
            {
                "key": "nouaison",
                "name": "Nouaison",
                "days_min": 10,
                "days_max": 25,
                "is_critical": True,
                "description": "Formation des jeunes olives.",
                "watchpoints": "Chute physiologique, alimentation en eau.",
            },
            {
                "key": "developpement-fruit",
                "name": "Développement du fruit",
                "days_min": 30,
                "days_max": 60,
                "description": "Grossissement de la drupe.",
            },
            {
                "key": "durcissement-noyau",
                "name": "Durcissement du noyau",
                "days_min": 20,
                "days_max": 40,
                "description": "Lignification du noyau.",
                "recognition": "Noyau résistant à la coupe au couteau.",
                "watchpoints": "Mouche de l'olive à partir de ce stade.",
            },
            {
                "key": "veraison",
                "name": "Véraison",
                "days_min": 15,
                "days_max": 35,
                "description": "Changement de couleur des olives.",
                "recommendations": [
                    _reco(
                        DOMAIN_RECOLTE,
                        "Arbitrer la date de récolte",
                        "La véraison marque le compromis entre rendement en "
                        "huile et profil aromatique.",
                    ),
                ],
            },
            {
                "key": "maturation",
                "name": "Maturation",
                "days_min": 20,
                "days_max": 60,
                "description": "Olives mûres, récolte et trituration.",
            },
        ],
    },
    # ------------------------------------------------------------------
    # Vigne
    # ------------------------------------------------------------------
    {
        "key": "phen-vigne",
        "name": "Cycle phénologique de la vigne (raisin de table)",
        "culture_key": "vigne--raisin-de-table",
        "system": SYSTEM_MIXTE,
        "summary": (
            "Dormance → Débourrement → Croissance végétative → Floraison → "
            "Nouaison → Fermeture de la grappe → Véraison → Maturation → "
            "Récolte."
        ),
        "source": "Échelle BBCH vigne",
        "is_default": True,
        "stages": [
            {
                "key": "dormance",
                "name": "Dormance",
                "bbch": "BBCH 00",
                "days_min": 60,
                "days_max": 120,
                "description": "Bourgeons au repos, taille d'hiver.",
            },
            {
                "key": "debourrement",
                "name": "Débourrement",
                "bbch": "BBCH 07-09",
                "days_min": 10,
                "days_max": 25,
                "is_critical": True,
                "description": "Sortie des feuilles hors du bourgeon.",
                "watchpoints": "Gelées de printemps.",
            },
            {
                "key": "croissance-vegetative",
                "name": "Croissance végétative",
                "bbch": "BBCH 12-19",
                "days_min": 25,
                "days_max": 45,
                "description": "Allongement des rameaux.",
            },
            {
                "key": "floraison",
                "name": "Floraison",
                "bbch": "BBCH 61-69",
                "days_min": 7,
                "days_max": 15,
                "is_critical": True,
                "description": "Chute des capuchons floraux.",
                "watchpoints": "Mildiou, oïdium sur inflorescences.",
            },
            {
                "key": "nouaison",
                "name": "Nouaison",
                "bbch": "BBCH 71",
                "days_min": 7,
                "days_max": 15,
                "description": "Jeunes baies formées.",
            },
            {
                "key": "fermeture-grappe",
                "name": "Fermeture de la grappe",
                "bbch": "BBCH 77",
                "days_min": 10,
                "days_max": 25,
                "description": "Les baies se touchent.",
                "watchpoints": "Dernier accès à l'intérieur de la grappe.",
            },
            {
                "key": "veraison",
                "name": "Véraison",
                "bbch": "BBCH 81-85",
                "days_min": 12,
                "days_max": 25,
                "is_critical": True,
                "description": "Changement de couleur et ramollissement.",
            },
            {
                "key": "maturation",
                "name": "Maturation",
                "bbch": "BBCH 89",
                "days_min": 20,
                "days_max": 45,
                "description": "Accumulation des sucres.",
            },
            {
                "key": "recolte",
                "name": "Récolte",
                "bbch": "BBCH 89",
                "days_min": 5,
                "days_max": 25,
                "description": "Contrôles de maturité puis vendange.",
            },
        ],
    },
    # ------------------------------------------------------------------
    # Maïs
    # ------------------------------------------------------------------
    {
        "key": "phen-mais",
        "name": "Cycle phénologique du maïs",
        "culture_key": "cereales--mais",
        "system": SYSTEM_MIXTE,
        "summary": (
            "Germination → Levée → 6 feuilles → 10 feuilles → Floraison mâle "
            "→ Floraison femelle → Grain laiteux → Grain pâteux → Maturité "
            "physiologique."
        ),
        "source": "Échelle BBCH maïs",
        "is_default": True,
        "stages": [
            {
                "key": "germination",
                "name": "Germination",
                "bbch": "BBCH 00-09",
                "days_min": 6,
                "days_max": 14,
                "description": "Sortie du coléoptile.",
            },
            {
                "key": "levee",
                "name": "Levée",
                "bbch": "BBCH 10-11",
                "days_min": 5,
                "days_max": 12,
                "description": "Première feuille étalée.",
            },
            {
                "key": "6-feuilles",
                "name": "Stade 6 feuilles",
                "bbch": "BBCH 16",
                "days_min": 12,
                "days_max": 22,
                "description": "Début de croissance rapide.",
                "recommendations": [
                    _reco(
                        DOMAIN_SURVEILLANCE,
                        "Vérifier la propreté de la parcelle",
                        "La concurrence des adventices est déterminante "
                        "jusqu'au recouvrement du sol.",
                    ),
                ],
            },
            {
                "key": "10-feuilles",
                "name": "Stade 10 feuilles",
                "bbch": "BBCH 19",
                "days_min": 12,
                "days_max": 20,
                "description": "Croissance maximale, forte demande en eau.",
            },
            {
                "key": "floraison-male",
                "name": "Floraison mâle",
                "bbch": "BBCH 63",
                "days_min": 5,
                "days_max": 10,
                "is_critical": True,
                "description": "Sortie et libération du pollen par la panicule.",
            },
            {
                "key": "floraison-femelle",
                "name": "Floraison femelle",
                "bbch": "BBCH 65",
                "days_min": 5,
                "days_max": 12,
                "is_critical": True,
                "description": "Sortie des soies et fécondation.",
                "watchpoints": (
                    "Période la plus sensible au stress hydrique du cycle."
                ),
                "recommendations": [
                    _reco(
                        DOMAIN_IRRIGATION,
                        "Stade sensible à l'alimentation en eau",
                        "Le pilotage de l'irrigation à ce stade détermine le "
                        "nombre de grains par épi ; aucune dose n'est imposée.",
                    ),
                ],
            },
            {
                "key": "grain-laiteux",
                "name": "Grain laiteux",
                "bbch": "BBCH 73-75",
                "days_min": 15,
                "days_max": 25,
                "description": "Remplissage du grain.",
            },
            {
                "key": "grain-pateux",
                "name": "Grain pâteux",
                "bbch": "BBCH 83-85",
                "days_min": 15,
                "days_max": 25,
                "description": "Le grain durcit progressivement.",
            },
            {
                "key": "maturite-physiologique",
                "name": "Maturité physiologique",
                "bbch": "BBCH 87-89",
                "days_min": 10,
                "days_max": 25,
                "description": "Point noir à la base du grain.",
            },
        ],
    },
    # ------------------------------------------------------------------
    # Pomme de terre
    # ------------------------------------------------------------------
    {
        "key": "phen-pomme-de-terre",
        "name": "Cycle phénologique de la pomme de terre",
        "culture_key": "tubercules--pomme-de-terre",
        "system": SYSTEM_LOCAL,
        "summary": (
            "Plantation → Levée → Croissance végétative → Tubérisation → "
            "Grossissement des tubercules → Floraison → Sénescence → "
            "Défanage."
        ),
        "source": "Vocabulaire maraîcher AgriPro",
        "is_default": True,
        "stages": [
            {
                "key": "plantation",
                "name": "Plantation",
                "days_min": 1,
                "days_max": 5,
                "description": "Mise en terre des plants germés.",
            },
            {
                "key": "levee",
                "name": "Levée",
                "days_min": 12,
                "days_max": 28,
                "description": "Sortie des tiges hors de la butte.",
            },
            {
                "key": "croissance-vegetative",
                "name": "Croissance végétative",
                "days_min": 15,
                "days_max": 30,
                "description": "Développement du feuillage.",
                "watchpoints": "Doryphore, mildiou dès le recouvrement.",
            },
            {
                "key": "tuberisation",
                "name": "Tubérisation",
                "days_min": 10,
                "days_max": 20,
                "is_critical": True,
                "description": "Initiation des tubercules sur les stolons.",
            },
            {
                "key": "grossissement",
                "name": "Grossissement des tubercules",
                "days_min": 25,
                "days_max": 50,
                "is_critical": True,
                "description": "Accumulation de matière sèche.",
                "recommendations": [
                    _reco(
                        DOMAIN_TRAITEMENT,
                        "Cadence de protection anti-mildiou",
                        "Le modèle épidémiologique de la parcelle définit le "
                        "rythme : aucune application n'est déclenchée "
                        "automatiquement.",
                    ),
                ],
            },
            {
                "key": "floraison",
                "name": "Floraison",
                "days_min": 7,
                "days_max": 20,
                "description": "Floraison, variable selon la variété.",
            },
            {
                "key": "senescence",
                "name": "Sénescence",
                "days_min": 10,
                "days_max": 25,
                "description": "Jaunissement du feuillage.",
            },
            {
                "key": "defanage",
                "name": "Défanage",
                "days_min": 10,
                "days_max": 21,
                "description": "Destruction du feuillage avant récolte.",
                "recommendations": [
                    _reco(
                        DOMAIN_RECOLTE,
                        "Attendre la tenue de la peau",
                        "Le délai entre défanage et arrachage conditionne la "
                        "conservation.",
                    ),
                ],
            },
        ],
    },
    # ------------------------------------------------------------------
    # Palmier dattier
    # ------------------------------------------------------------------
    {
        "key": "phen-palmier-dattier",
        "name": "Cycle phénologique du palmier dattier",
        "culture_key": "dattes--palmier-dattier",
        "system": SYSTEM_LOCAL,
        "summary": (
            "Repos → Sortie des spathes → Pollinisation → Nouaison → "
            "Kimri → Khalal → Rutab → Tamar."
        ),
        "source": "Vocabulaire phénicicole (stades Kimri à Tamar)",
        "is_default": True,
        "stages": [
            {
                "key": "repos",
                "name": "Repos hivernal",
                "days_min": 45,
                "days_max": 100,
                "description": "Ralentissement de la croissance.",
            },
            {
                "key": "sortie-spathes",
                "name": "Sortie des spathes",
                "days_min": 15,
                "days_max": 35,
                "description": "Apparition des inflorescences.",
            },
            {
                "key": "pollinisation",
                "name": "Pollinisation",
                "days_min": 5,
                "days_max": 20,
                "is_critical": True,
                "description": "Pollinisation manuelle des inflorescences.",
                "watchpoints": "Fenêtre courte, sensible aux pluies.",
            },
            {
                "key": "nouaison",
                "name": "Nouaison",
                "days_min": 10,
                "days_max": 25,
                "description": "Formation des jeunes dattes.",
            },
            {
                "key": "kimri",
                "name": "Kimri (datte verte)",
                "days_min": 60,
                "days_max": 110,
                "description": "Croissance rapide du fruit vert.",
                "watchpoints": "Boufaroua (acarien), ciselage des régimes.",
            },
            {
                "key": "khalal",
                "name": "Khalal (coloration)",
                "days_min": 25,
                "days_max": 45,
                "description": "Coloration du fruit, sucres en hausse.",
            },
            {
                "key": "rutab",
                "name": "Rutab (ramollissement)",
                "days_min": 15,
                "days_max": 35,
                "is_critical": True,
                "description": "Ramollissement du fruit.",
                "recommendations": [
                    _reco(
                        DOMAIN_SURVEILLANCE,
                        "Protéger les régimes",
                        "L'ensachage limite les dégâts de pluie et de pyrale "
                        "sur les régimes en cours de maturation.",
                    ),
                ],
            },
            {
                "key": "tamar",
                "name": "Tamar (datte mûre)",
                "days_min": 15,
                "days_max": 45,
                "description": "Datte mûre, récolte étalée.",
            },
        ],
    },
    # ------------------------------------------------------------------
    # Oranger
    # ------------------------------------------------------------------
    {
        "key": "phen-oranger",
        "name": "Cycle phénologique de l'oranger",
        "culture_key": "agrumes--oranger",
        "system": SYSTEM_LOCAL,
        "summary": (
            "Repos → Débourrement → Floraison → Nouaison → Chute "
            "physiologique → Grossissement du fruit → Changement de couleur → "
            "Maturation."
        ),
        "source": "Vocabulaire agrumicole AgriPro",
        "is_default": True,
        "stages": [
            {
                "key": "repos",
                "name": "Repos relatif",
                "days_min": 30,
                "days_max": 80,
                "description": "Croissance ralentie en période fraîche.",
            },
            {
                "key": "debourrement",
                "name": "Débourrement",
                "days_min": 15,
                "days_max": 30,
                "description": "Nouvelle poussée végétative.",
            },
            {
                "key": "floraison",
                "name": "Floraison",
                "days_min": 10,
                "days_max": 25,
                "is_critical": True,
                "description": "Fleurs blanches très parfumées.",
            },
            {
                "key": "nouaison",
                "name": "Nouaison",
                "days_min": 10,
                "days_max": 25,
                "is_critical": True,
                "description": "Formation des jeunes fruits.",
            },
            {
                "key": "chute-physiologique",
                "name": "Chute physiologique",
                "days_min": 15,
                "days_max": 35,
                "description": "Régulation naturelle de la charge.",
            },
            {
                "key": "grossissement",
                "name": "Grossissement du fruit",
                "days_min": 90,
                "days_max": 150,
                "description": "Développement du fruit.",
                "recommendations": [
                    _reco(
                        DOMAIN_FERTILISATION,
                        "Fertigation étalée",
                        "Les besoins se répartissent sur toute la phase de "
                        "grossissement ; le plan de fumure reste maître.",
                    ),
                ],
            },
            {
                "key": "changement-couleur",
                "name": "Changement de couleur",
                "days_min": 20,
                "days_max": 45,
                "description": "Coloration de l'épiderme.",
            },
            {
                "key": "maturation",
                "name": "Maturation",
                "days_min": 30,
                "days_max": 90,
                "description": "Rapport sucre / acide commercialisable.",
            },
        ],
    },
    # ------------------------------------------------------------------
    # Pois chiche (légumineuse)
    # ------------------------------------------------------------------
    {
        "key": "phen-pois-chiche",
        "name": "Cycle phénologique du pois chiche",
        "culture_key": "legumineuses--pois-chiche",
        "system": SYSTEM_LOCAL,
        "summary": (
            "Germination → Levée → Ramification → Floraison → Formation des "
            "gousses → Remplissage des graines → Maturation."
        ),
        "source": "Vocabulaire protéagineux AgriPro",
        "is_default": True,
        "stages": [
            {
                "key": "germination",
                "name": "Germination",
                "days_min": 6,
                "days_max": 14,
                "description": "Imbibition et sortie de la radicelle.",
            },
            {
                "key": "levee",
                "name": "Levée",
                "days_min": 8,
                "days_max": 18,
                "description": "Sortie des premières feuilles.",
            },
            {
                "key": "ramification",
                "name": "Ramification",
                "days_min": 20,
                "days_max": 40,
                "description": "Développement des tiges secondaires.",
                "watchpoints": "Nodosités, concurrence des adventices.",
            },
            {
                "key": "floraison",
                "name": "Floraison",
                "days_min": 15,
                "days_max": 35,
                "is_critical": True,
                "description": "Floraison étalée.",
                "watchpoints": "Anthracnose (Ascochyta) par temps humide.",
            },
            {
                "key": "formation-gousses",
                "name": "Formation des gousses",
                "days_min": 15,
                "days_max": 30,
                "is_critical": True,
                "description": "Apparition des gousses.",
            },
            {
                "key": "remplissage",
                "name": "Remplissage des graines",
                "days_min": 20,
                "days_max": 35,
                "description": "Grossissement des graines.",
            },
            {
                "key": "maturation",
                "name": "Maturation",
                "days_min": 10,
                "days_max": 25,
                "description": "Dessèchement des gousses.",
            },
        ],
    },
    # ------------------------------------------------------------------
    # Oignon (bulbe)
    # ------------------------------------------------------------------
    {
        "key": "phen-oignon",
        "name": "Cycle phénologique de l'oignon",
        "culture_key": "maraichage--oignon",
        "system": SYSTEM_LOCAL,
        "summary": (
            "Germination → Levée → Croissance foliaire → Bulbaison → "
            "Grossissement du bulbe → Tombaison → Maturation."
        ),
        "source": "Vocabulaire maraîcher AgriPro",
        "is_default": True,
        "stages": [
            {
                "key": "germination",
                "name": "Germination",
                "days_min": 8,
                "days_max": 18,
                "description": "Sortie de la crosse.",
            },
            {
                "key": "levee",
                "name": "Levée",
                "days_min": 10,
                "days_max": 20,
                "description": "Redressement des premières feuilles.",
            },
            {
                "key": "croissance-foliaire",
                "name": "Croissance foliaire",
                "days_min": 30,
                "days_max": 60,
                "description": "Construction du feuillage.",
            },
            {
                "key": "bulbaison",
                "name": "Bulbaison",
                "days_min": 15,
                "days_max": 30,
                "is_critical": True,
                "description": "Début de grossissement du bulbe.",
            },
            {
                "key": "grossissement-bulbe",
                "name": "Grossissement du bulbe",
                "days_min": 25,
                "days_max": 45,
                "description": "Accumulation des réserves.",
            },
            {
                "key": "tombaison",
                "name": "Tombaison",
                "days_min": 7,
                "days_max": 20,
                "description": "Le feuillage se couche.",
                "recommendations": [
                    _reco(
                        DOMAIN_IRRIGATION,
                        "Arrêter l'irrigation",
                        "La tombaison marque la fin des apports pour "
                        "sécuriser la conservation.",
                    ),
                ],
            },
            {
                "key": "maturation",
                "name": "Maturation",
                "days_min": 10,
                "days_max": 25,
                "description": "Séchage des tuniques avant stockage.",
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Fonctions pures réutilisables
# ---------------------------------------------------------------------------

_ACCENTS: dict[int, str] = str.maketrans(
    {
        "à": "a",
        "â": "a",
        "ä": "a",
        "á": "a",
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "î": "i",
        "ï": "i",
        "í": "i",
        "ô": "o",
        "ö": "o",
        "ó": "o",
        "ù": "u",
        "û": "u",
        "ü": "u",
        "ç": "c",
        "ñ": "n",
        "œ": "oe",
        "æ": "ae",
    }
)


def normalize_stage_label(value: str) -> str:
    """Clé de comparaison d'un libellé de stade (sans accent ni ponctuation).

    « Tallage », « tallage » et « TALLAGE » donnent la même clé ; « Grain
    laiteux » donne « grain-laiteux ».
    """
    chars: list[str] = []
    for char in str(value).lower().strip().translate(_ACCENTS):
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-")


def stage_progress_percent(position: int, total: int) -> int:
    """Progression du cycle, en pourcentage, pour un stade donné.

    Le premier stade n'est pas à 0 % (il est atteint) et le dernier vaut
    100 %. Retourne 0 si le profil est vide ou la position invalide.
    """
    if total <= 0 or position <= 0:
        return 0
    capped = min(position, total)
    return int(round(capped * 100 / total))


def stage_duration_status(
    days_in_stage: int, days_min: int, days_max: int
) -> str:
    """Qualifie la durée passée dans un stade, sans conclure agronomiquement."""
    if days_min <= 0 and days_max <= 0:
        return DEVIATION_INCONNU
    if days_in_stage < 0:
        return DEVIATION_INCONNU
    if days_max > 0 and days_in_stage > days_max:
        return DEVIATION_LONG
    if days_min > 0 and days_in_stage < days_min:
        return DEVIATION_COURT
    return DEVIATION_NORMAL


def deviation_label(key: str) -> str:
    return DEVIATION_LABELS.get(key, DEVIATION_LABELS[DEVIATION_INCONNU])


def deviation_tone(key: str) -> str:
    return DEVIATION_TONES.get(key, "muted")


def observation_status_label(key: str) -> str:
    return OBSERVATION_STATUS_LABELS.get(key, key)


def observation_status_tone(key: str) -> str:
    return OBSERVATION_STATUS_TONES.get(key, "muted")


def observation_source_label(key: str) -> str:
    return OBSERVATION_SOURCE_LABELS.get(key, key)


def recommendation_domain_label(key: str) -> str:
    return RECOMMENDATION_DOMAIN_LABELS.get(key, key)


def recommendation_domain_icon(key: str) -> str:
    return RECOMMENDATION_DOMAIN_ICONS.get(key, "circle-dot")


def confidence_label(key: str) -> str:
    return CONFIDENCE_LABELS.get(key, CONFIDENCE_LABELS[CONFIDENCE_INDICATIVE])


def system_label(key: str) -> str:
    return SYSTEM_LABELS.get(key, key)


def profile_stage_keys(profile_key: str) -> list[str]:
    """Clés de stades attendues pour un profil du référentiel embarqué."""
    for profile in PHENOLOGY_PROFILES:
        if profile["key"] == profile_key:
            return [str(stage["key"]) for stage in profile.get("stages", [])]
    return []


def expected_stage_labels(culture_key: str) -> list[str]:
    """Libellés de stades du profil par défaut d'une culture (référentiel dur).

    Utile pour un contrôle hors base : la vérité d'exécution reste la table
    `crop_phenology_stage` (voir `app/phenology_validation.py`).
    """
    for profile in PHENOLOGY_PROFILES:
        if profile.get("culture_key") != culture_key:
            continue
        if profile.get("species_key") or profile.get("variety_key"):
            continue
        return [str(stage["name"]) for stage in profile.get("stages", [])]
    return []


def is_stage_declared(culture_key: str, stage_label: str) -> bool:
    """Contrôle pur : le stade appartient-il au cycle déclaré de la culture ?

    Exemples : (« cereales--ble », « Tallage ») est vrai,
    (« arboriculture--olivier », « Tallage ») est faux.
    """
    target = normalize_stage_label(stage_label)
    if not target:
        return False
    for profile in PHENOLOGY_PROFILES:
        if profile.get("culture_key") != culture_key:
            continue
        for stage in profile.get("stages", []):
            if normalize_stage_label(stage["name"]) == target:
                return True
            if normalize_stage_label(stage["key"]) == target:
                return True
    return False

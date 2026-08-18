"""État de chargement de la base de connaissances « Guide Agricole ».

Cet item ne construit pas encore l'interface de consultation : l'état ci-dessous
est le strict minimum permettant de charger les contenus éditoriaux publiés
(catégories, articles en double lecture, procédures, dictionnaire, questions
fréquentes, règles « Pourquoi ? »/« Attention », parcours et version courante).

Toutes les lectures sont écrites en SQL brut via `rx.asession()`.
"""

from __future__ import annotations

import datetime
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.date_utils import as_date
from app.seed_corrections import seed_guide_corrections
from app.seed_guide import seed_guide_data
from app.states.dashboard_state import MONTHS, WEEKDAYS_SHORT

AUDIENCE_LABELS: dict[str, str] = {
    "AGRICOLE": "Lecture agricole",
    "AGRIPRO": "Lecture AgriPro",
    "MIXTE": "Double lecture",
}

DIFFICULTY_LABELS: dict[str, str] = {
    "DECOUVERTE": "Découverte",
    "INTERMEDIAIRE": "Intermédiaire",
    "AVANCE": "Avancé",
}

STATUS_LABELS: dict[str, str] = {
    "BROUILLON": "Brouillon",
    "RELECTURE": "En relecture",
    "PUBLIE": "Publié",
    "ARCHIVE": "Archivé",
}

RULE_KIND_LABELS: dict[str, str] = {
    "POURQUOI": "Pourquoi ?",
    "ATTENTION": "Attention",
    "COHERENCE": "Règle de cohérence",
    "BONNE_PRATIQUE": "Bonne pratique",
}

SEVERITY_LABELS: dict[str, str] = {
    "INFO": "Information",
    "ATTENTION": "Attention",
    "CRITIQUE": "Critique",
}

SEVERITY_TONES: dict[str, str] = {
    "INFO": "good",
    "ATTENTION": "warn",
    "CRITIQUE": "bad",
}


class CategoryCard(TypedDict):
    id: int
    key: str
    name: str
    tagline: str
    description: str
    icon: str
    color: str
    accent: str
    module_route: str
    article_count: int
    procedure_count: int
    faq_count: int
    rule_count: int
    term_count: int


class ArticleCard(TypedDict):
    id: int
    slug: str
    category_key: str
    category_name: str
    title: str
    subtitle: str
    summary: str
    body_farmer: str
    body_pro: str
    audience_label: str
    difficulty_label: str
    status_label: str
    reading_minutes: int
    keywords: str
    module_route: str
    version_label: str
    published_label: str
    is_featured: bool


class ProcedureCard(TypedDict):
    id: int
    slug: str
    category_key: str
    title: str
    objective: str
    context: str
    expected_result: str
    module_route: str
    estimated_minutes: int
    difficulty_label: str
    step_count: int


class TermCard(TypedDict):
    id: int
    slug: str
    term: str
    acronym: str
    category_key: str
    definition_farmer: str
    definition_pro: str
    unit: str
    formula: str
    example: str
    module_route: str


class FaqCard(TypedDict):
    id: int
    category_key: str
    category_name: str
    question: str
    answer_farmer: str
    answer_pro: str
    audience_label: str
    module_route: str
    is_frequent: bool


class RuleCard(TypedDict):
    id: int
    code: str
    category_key: str
    kind: str
    kind_label: str
    severity_label: str
    tone: str
    title: str
    statement: str
    rationale: str
    consequence: str
    remediation: str
    module_route: str
    field_reference: str
    is_blocking: bool


class PathCard(TypedDict):
    id: int
    slug: str
    title: str
    subtitle: str
    objective: str
    audience_label: str
    difficulty_label: str
    estimated_minutes: int
    icon: str
    color: str
    step_count: int


class VersionCard(TypedDict):
    version_label: str
    title: str
    summary: str
    changelog: str
    author: str
    status_label: str
    published_label: str
    entry_count: int


EMPTY_VERSION: VersionCard = {
    "version_label": "—",
    "title": "Aucune version publiée",
    "summary": "",
    "changelog": "",
    "author": "",
    "status_label": "—",
    "published_label": "—",
    "entry_count": 0,
}


def _fmt_date(value: object) -> str:
    day = as_date(value)
    if day is None:
        return "—"
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _short(value: object, size: int = 160) -> str:
    text_value = str(value or "").strip().replace("\n", " ")
    if not text_value:
        return "Aucun détail consigné."
    if len(text_value) <= size:
        return text_value
    return f"{text_value[:size].rstrip()}…"


EMPTY_ARTICLE: ArticleCard = {
    "id": 0,
    "slug": "",
    "category_key": "",
    "category_name": "",
    "title": "",
    "subtitle": "",
    "summary": "",
    "body_farmer": "",
    "body_pro": "",
    "audience_label": "",
    "difficulty_label": "",
    "status_label": "",
    "reading_minutes": 0,
    "keywords": "",
    "module_route": "",
    "version_label": "",
    "published_label": "",
    "is_featured": False,
}


class ArticleLink(TypedDict):
    id: int
    label: str
    route: str
    icon: str
    description: str


class ProcedureStep(TypedDict):
    id: int
    position: int
    title: str
    instruction_farmer: str
    instruction_pro: str
    ui_hint: str
    module_route: str
    field_reference: str
    why: str
    warning: str
    duration_minutes: int
    is_optional: bool


class PathStep(TypedDict):
    id: int
    position: int
    title: str
    description: str
    milestone: str
    module_route: str
    duration_minutes: int
    is_optional: bool
    article_slug: str
    procedure_slug: str


class SearchHit(TypedDict):
    key: str
    kind: str
    kind_label: str
    icon: str
    title: str
    subtitle: str
    excerpt: str
    ref: str


class SearchGroup(TypedDict):
    kind: str
    label: str
    icon: str
    tone: str
    count: int
    hits: list[SearchHit]


class RelationNode(TypedDict):
    key: str
    label: str
    step: str
    icon: str
    tone: str
    route: str
    route_label: str
    category_key: str
    summary_farmer: str
    summary_pro: str
    inputs: list[str]
    outputs: list[str]
    metrics: list[str]
    is_parallel: bool


SECTIONS: list[tuple[str, str, str]] = [
    ("bibliotheque", "Bibliothèque", "library-big"),
    ("dictionnaire", "Dictionnaire", "book-a"),
    ("faq", "FAQ intelligente", "message-circle-question"),
    ("parcours", "Parcours", "graduation-cap"),
    ("regles", "Pourquoi & Attention", "shield-alert"),
    ("relations", "Carte des données", "workflow"),
    ("administration", "Pupitre éditorial", "square-pen"),
]

RELATION_CHAIN: list[RelationNode] = [
    {
        "key": "exploitation",
        "label": "Exploitation",
        "step": "01",
        "icon": "leaf",
        "tone": "vegetal",
        "route": "/",
        "route_label": "Ouvrir le cockpit",
        "category_key": "fondamentaux",
        "summary_farmer": "Votre ferme dans son ensemble : les terres, l'équipe, le matériel et les comptes.",
        "summary_pro": "Entité de pilotage racine : agrège surfaces, main d'œuvre, flotte, stocks et charges de structure.",
        "inputs": ["Foncier déclaré", "Équipe", "Flotte"],
        "outputs": ["Parcelles", "Indicateurs consolidés"],
        "metrics": ["Surface totale", "Alertes actives", "Charges cumulées"],
        "is_parallel": False,
    },
    {
        "key": "parcelle",
        "label": "Parcelle",
        "step": "02",
        "icon": "map",
        "tone": "vegetal",
        "route": "/parcelles",
        "route_label": "Ouvrir l'assolement",
        "category_key": "parcelles",
        "summary_farmer": "L'îlot que vous reconnaissez sur le terrain, avec son nom, son code et sa surface.",
        "summary_pro": "Unité foncière porteuse du sol, de l'irrigation, de la géométrie GeoJSON et de la surface de référence.",
        "inputs": [
            "Code d'îlot",
            "Surface exploitée",
            "Contour cartographique",
        ],
        "outputs": ["Cultures", "Analyses de sol", "Coût à l'hectare"],
        "metrics": ["area_ha", "geometry_area_ha", "pH"],
        "is_parallel": False,
    },
    {
        "key": "culture",
        "label": "Culture",
        "step": "03",
        "icon": "sprout",
        "tone": "vegetal",
        "route": "/parcelles",
        "route_label": "Ouvrir les fiches culturales",
        "category_key": "cultures",
        "summary_farmer": "Ce que vous avez semé sur la parcelle, avec sa variété et ses dates clés.",
        "summary_pro": "Fiche culturale liée à une variété du référentiel : stade, statut, état sanitaire, avancement.",
        "inputs": ["Parcelle", "Variété", "Date de semis"],
        "outputs": ["Interventions", "Récoltes", "Journal de stades"],
        "metrics": ["Surface implantée", "Stade", "Rendement visé"],
        "is_parallel": False,
    },
    {
        "key": "campagne",
        "label": "Campagne",
        "step": "04",
        "icon": "calendar-range",
        "tone": "vegetal",
        "route": "/parcelles",
        "route_label": "Comparer les campagnes",
        "category_key": "cultures",
        "summary_farmer": "L'année de culture, du semis à la récolte : elle sert à comparer d'une année sur l'autre.",
        "summary_pro": "Millésime de référence porté par la culture : axe d'analyse pluriannuelle des rendements et des marges.",
        "inputs": ["Culture", "Millésime"],
        "outputs": ["Séries pluriannuelles", "Rotation"],
        "metrics": ["Saison", "Cycle en jours"],
        "is_parallel": False,
    },
    {
        "key": "intervention",
        "label": "Intervention",
        "step": "05",
        "icon": "spray-can",
        "tone": "operations",
        "route": "/traitements",
        "route_label": "Ouvrir le journal",
        "category_key": "travaux",
        "summary_farmer": "Chaque passage sur la parcelle : travail du sol, semis, traitement, irrigation, observation.",
        "summary_pro": "Chantier planifié puis clôturé, porteur des conditions météo, de la surface traitée et du coût de passage.",
        "inputs": ["Parcelle", "Culture", "Date planifiée"],
        "outputs": [
            "Sorties de stock",
            "Heures de main d'œuvre",
            "Heures d'engin",
        ],
        "metrics": ["Surface traitée", "Durée", "Coût"],
        "is_parallel": False,
    },
    {
        "key": "intrants",
        "label": "Intrants",
        "step": "06",
        "icon": "flask-conical",
        "tone": "operations",
        "route": "/traitements",
        "route_label": "Ouvrir le magasin",
        "category_key": "stocks",
        "summary_farmer": "Les produits utilisés lors du passage : semences, engrais, produits de protection.",
        "summary_pro": "Lignes produit dosées à l'hectare : génèrent un mouvement de stock SORTIE et un coût matière.",
        "inputs": ["Produit", "Dose/ha", "Surface traitée"],
        "outputs": ["Mouvement de stock", "Coût matière"],
        "metrics": ["Quantité totale", "Stock restant"],
        "is_parallel": True,
    },
    {
        "key": "main_oeuvre",
        "label": "Main d'œuvre",
        "step": "06",
        "icon": "users-round",
        "tone": "humain",
        "route": "/employes",
        "route_label": "Ouvrir les affectations",
        "category_key": "personnel",
        "summary_farmer": "Qui a fait le travail, avec quelle habilitation et pendant combien de temps.",
        "summary_pro": "Affectation croisant compétence, habilitation valide et disponibilité : heures prévues et réalisées valorisées.",
        "inputs": ["Salarié", "Compétence", "Disponibilité"],
        "outputs": ["Heures réalisées", "Coût de main d'œuvre"],
        "metrics": ["Heures", "Coût horaire"],
        "is_parallel": True,
    },
    {
        "key": "materiel",
        "label": "Matériel",
        "step": "06",
        "icon": "tractor",
        "tone": "flotte",
        "route": "/maintenance",
        "route_label": "Ouvrir la flotte",
        "category_key": "materiel",
        "summary_farmer": "L'engin utilisé, ses heures et son carburant, plus l'entretien qu'il réclame.",
        "summary_pro": "Engin porteur d'un compteur d'usage : relevés, plans d'entretien et coûts d'atelier alimentent le coût horaire.",
        "inputs": ["Engin", "Relevé de compteur", "Carburant"],
        "outputs": ["Coût horaire", "Échéances d'entretien"],
        "metrics": ["Heures d'usage", "Coût d'atelier"],
        "is_parallel": True,
    },
    {
        "key": "cout",
        "label": "Coût",
        "step": "07",
        "icon": "coins",
        "tone": "operations",
        "route": "/charges",
        "route_label": "Ouvrir le registre des charges",
        "category_key": "economie",
        "summary_farmer": "Tout ce que le chantier a coûté : produits, heures, engin, factures rattachées.",
        "summary_pro": "Charges opérationnelles affectées : dépense typée, rattachée à la parcelle, la culture, le salarié ou l'engin.",
        "inputs": ["Intrants", "Main d'œuvre", "Matériel", "Factures"],
        "outputs": ["Coût à l'hectare", "Encours fournisseurs"],
        "metrics": ["Montant HT", "Montant TTC", "€/ha"],
        "is_parallel": False,
    },
    {
        "key": "recolte",
        "label": "Récolte",
        "step": "08",
        "icon": "wheat",
        "tone": "operations",
        "route": "/traitements",
        "route_label": "Ouvrir les récoltes",
        "category_key": "recolte",
        "summary_farmer": "Ce que la parcelle a donné : quantité, surface moissonnée, humidité, qualité.",
        "summary_pro": "Événement de récolte rattaché à la culture : quantité, surface récoltée, humidité, pertes et qualité.",
        "inputs": ["Culture", "Pesées", "Surface moissonnée"],
        "outputs": ["Rendement", "Produit brut"],
        "metrics": ["Quantité", "Humidité", "Pertes"],
        "is_parallel": False,
    },
    {
        "key": "rendement",
        "label": "Rendement",
        "step": "09",
        "icon": "chart-line",
        "tone": "vegetal",
        "route": "/traitements",
        "route_label": "Comparer les rendements",
        "category_key": "recolte",
        "summary_farmer": "Ce que la parcelle a produit par hectare, comparé à ce que vous visiez.",
        "summary_pro": "Quantité rapportée à la surface récoltée, normalisée à l'humidité de référence avant comparaison.",
        "inputs": ["Récolte", "Surface récoltée"],
        "outputs": ["Performance vs objectif", "Classement des îlots"],
        "metrics": ["t/ha", "Écart à l'objectif"],
        "is_parallel": False,
    },
    {
        "key": "vente",
        "label": "Vente",
        "step": "10",
        "icon": "banknote",
        "tone": "operations",
        "route": "/traitements",
        "route_label": "Ouvrir la valorisation",
        "category_key": "economie",
        "summary_farmer": "Le prix auquel la récolte est valorisée, et le produit qui en découle.",
        "summary_pro": "Valorisation de la récolte : quantité × prix unitaire = produit brut de la campagne.",
        "inputs": ["Quantité récoltée", "Prix unitaire"],
        "outputs": ["Produit brut"],
        "metrics": ["€/t", "Produit brut"],
        "is_parallel": False,
    },
    {
        "key": "resultat",
        "label": "Résultat",
        "step": "11",
        "icon": "trending-up",
        "tone": "vegetal",
        "route": "/charges",
        "route_label": "Ouvrir la synthèse",
        "category_key": "economie",
        "summary_farmer": "Ce qui reste une fois les charges payées : la vraie mesure de la campagne.",
        "summary_pro": "Marge brute par îlot = produit brut − charges opérationnelles affectées, ramenée à l'hectare.",
        "inputs": ["Produit brut", "Coûts rattachés"],
        "outputs": ["Décisions d'assolement", "Arbitrages d'investissement"],
        "metrics": ["Marge brute €/ha", "Coût de production"],
        "is_parallel": False,
    },
]

RELATION_BY_KEY: dict[str, RelationNode] = {
    node["key"]: node for node in RELATION_CHAIN
}


class GuideState(rx.State):
    """Contenus éditoriaux publiés du Guide Agricole."""

    is_loading: bool = True
    today_label: str = ""

    totals: dict[str, int] = {
        "categories": 0,
        "articles": 0,
        "procedures": 0,
        "steps": 0,
        "terms": 0,
        "faq": 0,
        "rules": 0,
        "paths": 0,
        "versions": 0,
    }

    categories: list[CategoryCard] = []
    articles: list[ArticleCard] = []
    procedures: list[ProcedureCard] = []
    terms: list[TermCard] = []
    faq: list[FaqCard] = []
    rules: list[RuleCard] = []
    paths: list[PathCard] = []
    current_version: VersionCard = EMPTY_VERSION

    # --- Navigation & recherche de l'interface -------------------------
    active_section: str = "bibliotheque"
    selected_category: str = "TOUS"
    query: str = ""
    search_groups: list[SearchGroup] = []

    # --- Lecture d'article ---------------------------------------------
    active_article_slug: str = ""
    article_links: list[ArticleLink] = []
    related_procedures: list[ProcedureCard] = []
    # "article" : procédures rattachées directement à l'article ;
    # "categorie" : procédures de la même catégorie ;
    # "transverse" : procédures clés de l'exploitation (repli).
    related_scope: str = "article"
    show_procedures: bool = False

    # --- Procédure interactive ------------------------------------------
    open_procedure_slug: str = ""
    procedure_steps: list[ProcedureStep] = []
    done_steps: list[int] = []

    # --- Dictionnaire, FAQ, parcours, règles, relations ------------------
    term_query: str = ""
    active_term_slug: str = ""
    open_faq_id: int = 0
    rule_filter: str = "TOUS"
    active_path_slug: str = ""
    path_steps: list[PathStep] = []
    active_relation: str = "exploitation"

    sections: list[tuple[str, str, str]] = SECTIONS
    relation_chain: list[RelationNode] = RELATION_CHAIN

    @rx.var
    def featured_articles(self) -> list[ArticleCard]:
        return [item for item in self.articles if item["is_featured"]]

    @rx.var
    def why_rules(self) -> list[RuleCard]:
        return [item for item in self.rules if item["kind"] == "POURQUOI"]

    @rx.var
    def warning_rules(self) -> list[RuleCard]:
        return [item for item in self.rules if item["kind"] == "ATTENTION"]

    @rx.var
    def frequent_questions(self) -> list[FaqCard]:
        return [item for item in self.faq if item["is_frequent"]]

    # ------------------------------------------------------------------
    # Vars dérivées de l'interface
    # ------------------------------------------------------------------

    @rx.var
    def category_label(self) -> str:
        if self.selected_category == "TOUS":
            return "Toutes les catégories"
        for item in self.categories:
            if item["key"] == self.selected_category:
                return item["name"]
        return "Toutes les catégories"

    @rx.var
    def category_articles(self) -> list[ArticleCard]:
        if self.selected_category == "TOUS":
            return self.articles
        return [
            item
            for item in self.articles
            if item["category_key"] == self.selected_category
        ]

    @rx.var
    def active_article(self) -> ArticleCard:
        for item in self.articles:
            if item["slug"] == self.active_article_slug:
                return item
        return EMPTY_ARTICLE

    @rx.var
    def has_article(self) -> bool:
        return self.active_article_slug != ""

    @rx.var
    def farmer_paragraphs(self) -> list[str]:
        body = self.active_article["body_farmer"]
        return [chunk.strip() for chunk in body.split("\n\n") if chunk.strip()]

    @rx.var
    def pro_paragraphs(self) -> list[str]:
        body = self.active_article["body_pro"]
        return [chunk.strip() for chunk in body.split("\n\n") if chunk.strip()]

    @rx.var
    def article_keywords(self) -> list[str]:
        raw = self.active_article["keywords"]
        return [chunk.strip() for chunk in raw.split(",") if chunk.strip()]

    @rx.var
    def has_search(self) -> bool:
        return len(self.query.strip()) >= 2

    @rx.var
    def search_total(self) -> int:
        return sum(group["count"] for group in self.search_groups)

    @rx.var
    def visible_terms(self) -> list[TermCard]:
        needle = self.term_query.strip().lower()
        if not needle:
            return self.terms
        return [
            item
            for item in self.terms
            if needle in item["term"].lower()
            or needle in item["acronym"].lower()
            or needle in item["definition_farmer"].lower()
            or needle in item["definition_pro"].lower()
        ]

    @rx.var
    def active_term(self) -> TermCard:
        for item in self.terms:
            if item["slug"] == self.active_term_slug:
                return item
        if self.visible_terms:
            return self.visible_terms[0]
        return {
            "id": 0,
            "slug": "",
            "term": "Dictionnaire",
            "acronym": "",
            "category_key": "",
            "definition_farmer": "Sélectionnez une entrée pour afficher sa double lecture.",
            "definition_pro": "",
            "unit": "",
            "formula": "",
            "example": "",
            "module_route": "",
        }

    @rx.var
    def visible_faq(self) -> list[FaqCard]:
        if self.selected_category == "TOUS":
            return self.faq
        return [
            item
            for item in self.faq
            if item["category_key"] == self.selected_category
        ]

    @rx.var
    def visible_rules(self) -> list[RuleCard]:
        items = self.rules
        if self.selected_category != "TOUS":
            items = [
                item
                for item in items
                if item["category_key"] == self.selected_category
            ]
        if self.rule_filter != "TOUS":
            items = [item for item in items if item["kind"] == self.rule_filter]
        return items

    @rx.var
    def farmer_paths(self) -> list[PathCard]:
        return [
            item
            for item in self.paths
            if item["audience_label"] != AUDIENCE_LABELS["AGRIPRO"]
        ]

    @rx.var
    def pro_paths(self) -> list[PathCard]:
        return [
            item
            for item in self.paths
            if item["audience_label"] == AUDIENCE_LABELS["AGRIPRO"]
        ]

    @rx.var
    def active_path(self) -> PathCard:
        for item in self.paths:
            if item["slug"] == self.active_path_slug:
                return item
        return {
            "id": 0,
            "slug": "",
            "title": "",
            "subtitle": "",
            "objective": "",
            "audience_label": "",
            "difficulty_label": "",
            "estimated_minutes": 0,
            "icon": "graduation-cap",
            "color": "#a3e635",
            "step_count": 0,
        }

    @rx.var
    def active_relation_node(self) -> RelationNode:
        return RELATION_BY_KEY.get(self.active_relation, RELATION_CHAIN[0])

    @rx.var
    def open_procedure(self) -> ProcedureCard:
        for item in self.procedures:
            if item["slug"] == self.open_procedure_slug:
                return item
        return {
            "id": 0,
            "slug": "",
            "category_key": "",
            "title": "",
            "objective": "",
            "context": "",
            "expected_result": "",
            "module_route": "/",
            "estimated_minutes": 0,
            "difficulty_label": "",
            "step_count": 0,
        }

    @rx.var
    def has_open_procedure(self) -> bool:
        return self.open_procedure_slug != ""

    @rx.var
    def related_scope_label(self) -> str:
        if self.related_scope == "article":
            return "Procédures rattachées à cet article"
        if self.related_scope == "categorie":
            return "Procédures de la même catégorie"
        return "Procédures clés de l'exploitation"

    @rx.var
    def step_progress(self) -> int:
        if not self.procedure_steps:
            return 0
        return int(
            round(100 * len(self.done_steps) / len(self.procedure_steps))
        )

    @rx.var
    def step_progress_width(self) -> str:
        return f"{self.step_progress}%"

    @rx.event
    async def load_guide(self):
        self.is_loading = True
        yield

        await seed_guide_data()
        # Procédures manquantes et règles orphelines corrigées (idempotent).
        await seed_guide_corrections()

        async with rx.asession() as asession:
            totals_row = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            (SELECT COUNT(*) FROM guide_category),
                            (SELECT COUNT(*) FROM guide_article WHERE status = 'PUBLIE'),
                            (SELECT COUNT(*) FROM guide_procedure WHERE status = 'PUBLIE'),
                            (SELECT COUNT(*) FROM guide_procedure_step),
                            (SELECT COUNT(*) FROM guide_term WHERE status = 'PUBLIE'),
                            (SELECT COUNT(*) FROM guide_faq WHERE status = 'PUBLIE'),
                            (SELECT COUNT(*) FROM guide_rule WHERE status = 'PUBLIE'),
                            (SELECT COUNT(*) FROM guide_learning_path WHERE status = 'PUBLIE'),
                            (SELECT COUNT(*) FROM guide_version)
                        """
                    )
                )
            ).first()

            category_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT c.id, c.key, c.name, COALESCE(c.tagline, ''),
                               COALESCE(c.description, ''), c.icon, c.color_hex,
                               c.accent_hex, COALESCE(c.module_route, '/'),
                               (SELECT COUNT(*) FROM guide_article a
                                  WHERE a.category_id = c.id AND a.status = 'PUBLIE'),
                               (SELECT COUNT(*) FROM guide_procedure p
                                  WHERE p.category_id = c.id AND p.status = 'PUBLIE'),
                               (SELECT COUNT(*) FROM guide_faq f
                                  WHERE f.category_id = c.id AND f.status = 'PUBLIE'),
                               (SELECT COUNT(*) FROM guide_rule r
                                  WHERE r.category_id = c.id AND r.status = 'PUBLIE'),
                               (SELECT COUNT(*) FROM guide_term t
                                  WHERE t.category_id = c.id AND t.status = 'PUBLIE')
                        FROM guide_category c
                        WHERE c.is_active = 1
                        ORDER BY c.position, c.name
                        LIMIT 40
                        """
                    )
                )
            ).all()

            article_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT a.id, a.slug, c.key, c.name, a.title,
                               COALESCE(a.subtitle, ''), COALESCE(a.summary, ''),
                               COALESCE(a.body_farmer, ''), COALESCE(a.body_pro, ''),
                               a.audience, a.difficulty, a.status,
                               COALESCE(a.reading_minutes, 0),
                               COALESCE(a.keywords, ''),
                               COALESCE(a.module_route, ''),
                               COALESCE(a.version_label, ''), a.published_on,
                               a.is_featured
                        FROM guide_article a
                        JOIN guide_category c ON c.id = a.category_id
                        WHERE a.status = 'PUBLIE'
                        ORDER BY c.position, a.position, a.title
                        LIMIT 120
                        """
                    )
                )
            ).all()

            procedure_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT p.id, p.slug, c.key, p.title,
                               COALESCE(p.objective, ''), COALESCE(p.context, ''),
                               COALESCE(p.expected_result, ''),
                               COALESCE(p.module_route, '/'),
                               COALESCE(p.estimated_minutes, 0), p.difficulty,
                               (SELECT COUNT(*) FROM guide_procedure_step s
                                  WHERE s.procedure_id = p.id)
                        FROM guide_procedure p
                        JOIN guide_category c ON c.id = p.category_id
                        WHERE p.status = 'PUBLIE'
                        ORDER BY c.position, p.position, p.title
                        LIMIT 60
                        """
                    )
                )
            ).all()

            term_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT t.id, t.slug, t.term, COALESCE(t.acronym, ''),
                               COALESCE(c.key, ''),
                               COALESCE(t.definition_farmer, ''),
                               COALESCE(t.definition_pro, ''),
                               COALESCE(t.unit, ''), COALESCE(t.formula, ''),
                               COALESCE(t.example, ''),
                               COALESCE(t.module_route, '')
                        FROM guide_term t
                        LEFT JOIN guide_category c ON c.id = t.category_id
                        WHERE t.status = 'PUBLIE'
                        ORDER BY t.term
                        LIMIT 200
                        """
                    )
                )
            ).all()

            faq_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT f.id, c.key, c.name, f.question,
                               COALESCE(f.answer_farmer, ''),
                               COALESCE(f.answer_pro, ''), f.audience,
                               COALESCE(f.module_route, ''), f.is_frequent
                        FROM guide_faq f
                        JOIN guide_category c ON c.id = f.category_id
                        WHERE f.status = 'PUBLIE'
                        ORDER BY c.position, f.position, f.id
                        LIMIT 120
                        """
                    )
                )
            ).all()

            rule_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT r.id, r.code, COALESCE(c.key, ''), r.kind,
                               r.severity, r.title, COALESCE(r.statement, ''),
                               COALESCE(r.rationale, ''),
                               COALESCE(r.consequence, ''),
                               COALESCE(r.remediation, ''),
                               COALESCE(r.module_route, ''),
                               COALESCE(r.field_reference, ''), r.is_blocking
                        FROM guide_rule r
                        LEFT JOIN guide_category c ON c.id = r.category_id
                        WHERE r.status = 'PUBLIE'
                        ORDER BY r.code
                        LIMIT 120
                        """
                    )
                )
            ).all()

            path_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT p.id, p.slug, p.title, COALESCE(p.subtitle, ''),
                               COALESCE(p.objective, ''), p.audience,
                               p.difficulty, COALESCE(p.estimated_minutes, 0),
                               p.icon, p.color_hex,
                               (SELECT COUNT(*) FROM guide_learning_step s
                                  WHERE s.path_id = p.id)
                        FROM guide_learning_path p
                        WHERE p.status = 'PUBLIE'
                        ORDER BY p.position, p.title
                        LIMIT 30
                        """
                    )
                )
            ).all()

            linked_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT DISTINCT a.slug
                        FROM guide_procedure p
                        JOIN guide_article a ON a.id = p.article_id
                        WHERE p.status = 'PUBLIE'
                        """
                    )
                )
            ).all()

            version_row = (
                await asession.execute(
                    text(
                        """
                        SELECT v.version_label, v.title, COALESCE(v.summary, ''),
                               COALESCE(v.changelog, ''), COALESCE(v.author, ''),
                               v.status, v.published_on,
                               (SELECT COUNT(*) FROM guide_version_entry e
                                  WHERE e.version_id = v.id)
                        FROM guide_version v
                        ORDER BY v.is_current DESC, v.published_on DESC
                        LIMIT 1
                        """
                    )
                )
            ).first()

        categories: list[CategoryCard] = [
            {
                "id": int(row[0]),
                "key": str(row[1]),
                "name": str(row[2]),
                "tagline": str(row[3]),
                "description": str(row[4]),
                "icon": str(row[5]),
                "color": str(row[6]),
                "accent": str(row[7]),
                "module_route": str(row[8]),
                "article_count": int(row[9] or 0),
                "procedure_count": int(row[10] or 0),
                "faq_count": int(row[11] or 0),
                "rule_count": int(row[12] or 0),
                "term_count": int(row[13] or 0),
            }
            for row in category_rows
        ]

        articles: list[ArticleCard] = [
            {
                "id": int(row[0]),
                "slug": str(row[1]),
                "category_key": str(row[2]),
                "category_name": str(row[3]),
                "title": str(row[4]),
                "subtitle": str(row[5]),
                "summary": str(row[6]),
                "body_farmer": str(row[7]),
                "body_pro": str(row[8]),
                "audience_label": AUDIENCE_LABELS.get(row[9], row[9]),
                "difficulty_label": DIFFICULTY_LABELS.get(row[10], row[10]),
                "status_label": STATUS_LABELS.get(row[11], row[11]),
                "reading_minutes": int(row[12] or 0),
                "keywords": str(row[13]),
                "module_route": str(row[14]),
                "version_label": str(row[15]),
                "published_label": _fmt_date(row[16]),
                "is_featured": bool(row[17]),
            }
            for row in article_rows
        ]

        procedures: list[ProcedureCard] = [
            {
                "id": int(row[0]),
                "slug": str(row[1]),
                "category_key": str(row[2]),
                "title": str(row[3]),
                "objective": str(row[4]),
                "context": str(row[5]),
                "expected_result": str(row[6]),
                "module_route": str(row[7]),
                "estimated_minutes": int(row[8] or 0),
                "difficulty_label": DIFFICULTY_LABELS.get(row[9], row[9]),
                "step_count": int(row[10] or 0),
            }
            for row in procedure_rows
        ]

        terms: list[TermCard] = [
            {
                "id": int(row[0]),
                "slug": str(row[1]),
                "term": str(row[2]),
                "acronym": str(row[3]),
                "category_key": str(row[4]),
                "definition_farmer": str(row[5]),
                "definition_pro": str(row[6]),
                "unit": str(row[7]),
                "formula": str(row[8]),
                "example": str(row[9]),
                "module_route": str(row[10]),
            }
            for row in term_rows
        ]

        faq: list[FaqCard] = [
            {
                "id": int(row[0]),
                "category_key": str(row[1]),
                "category_name": str(row[2]),
                "question": str(row[3]),
                "answer_farmer": str(row[4]),
                "answer_pro": str(row[5]),
                "audience_label": AUDIENCE_LABELS.get(row[6], row[6]),
                "module_route": str(row[7]),
                "is_frequent": bool(row[8]),
            }
            for row in faq_rows
        ]

        rules: list[RuleCard] = []
        for row in rule_rows:
            kind = str(row[3])
            severity = str(row[4])
            rules.append(
                {
                    "id": int(row[0]),
                    "code": str(row[1]),
                    "category_key": str(row[2]),
                    "kind": kind,
                    "kind_label": RULE_KIND_LABELS.get(kind, kind),
                    "severity_label": SEVERITY_LABELS.get(severity, severity),
                    "tone": SEVERITY_TONES.get(severity, "good"),
                    "title": str(row[5]),
                    "statement": str(row[6]),
                    "rationale": str(row[7]),
                    "consequence": str(row[8]),
                    "remediation": str(row[9]),
                    "module_route": str(row[10]),
                    "field_reference": str(row[11]),
                    "is_blocking": bool(row[12]),
                }
            )

        paths: list[PathCard] = [
            {
                "id": int(row[0]),
                "slug": str(row[1]),
                "title": str(row[2]),
                "subtitle": str(row[3]),
                "objective": str(row[4]),
                "audience_label": AUDIENCE_LABELS.get(row[5], row[5]),
                "difficulty_label": DIFFICULTY_LABELS.get(row[6], row[6]),
                "estimated_minutes": int(row[7] or 0),
                "icon": str(row[8]),
                "color": str(row[9]),
                "step_count": int(row[10] or 0),
            }
            for row in path_rows
        ]

        version: VersionCard = EMPTY_VERSION
        if version_row is not None:
            version = {
                "version_label": str(version_row[0]),
                "title": str(version_row[1]),
                "summary": str(version_row[2]),
                "changelog": str(version_row[3]),
                "author": str(version_row[4]),
                "status_label": STATUS_LABELS.get(
                    version_row[5], version_row[5]
                ),
                "published_label": _fmt_date(version_row[6]),
                "entry_count": int(version_row[7] or 0),
            }

        today = datetime.date.today()
        self.totals = {
            "categories": int(totals_row[0] or 0) if totals_row else 0,
            "articles": int(totals_row[1] or 0) if totals_row else 0,
            "procedures": int(totals_row[2] or 0) if totals_row else 0,
            "steps": int(totals_row[3] or 0) if totals_row else 0,
            "terms": int(totals_row[4] or 0) if totals_row else 0,
            "faq": int(totals_row[5] or 0) if totals_row else 0,
            "rules": int(totals_row[6] or 0) if totals_row else 0,
            "paths": int(totals_row[7] or 0) if totals_row else 0,
            "versions": int(totals_row[8] or 0) if totals_row else 0,
        }
        self.categories = categories
        self.articles = articles
        self.procedures = procedures
        self.terms = terms
        self.faq = faq
        self.rules = rules
        self.paths = paths
        self.current_version = version
        self.today_label = (
            f"{WEEKDAYS_SHORT[today.weekday()]}. {today.day} "
            f"{MONTHS[today.month - 1]} {today.year}"
        )

        if not self.active_article_slug and articles:
            linked_slugs = [str(row[0]) for row in linked_rows]
            procedure_categories = [item["category_key"] for item in procedures]
            default_slug = self._pick_default_article(
                articles, linked_slugs, procedure_categories
            )
            await self._load_article(default_slug)
        if not self.active_term_slug and terms:
            self.active_term_slug = terms[0]["slug"]
        if not self.active_path_slug and paths:
            await self._load_path(paths[0]["slug"])

        self.is_loading = False

    # ------------------------------------------------------------------
    # Chargements ciblés (SQL brut)
    # ------------------------------------------------------------------

    def _pick_default_article(
        self,
        articles: list[ArticleCard],
        linked_slugs: list[str],
        procedure_categories: list[str],
    ) -> str:
        """Choisit un article d'accueil disposant de procédures exploitables."""
        featured = [item for item in articles if item["is_featured"]]
        pools = (featured, articles)
        # 1) Article (mis en avant si possible) avec une procédure directe.
        for pool in pools:
            for item in pool:
                if item["slug"] in linked_slugs:
                    return item["slug"]
        # 2) Article dont la catégorie propose au moins une procédure.
        for pool in pools:
            for item in pool:
                if item["category_key"] in procedure_categories:
                    return item["slug"]
        # 3) Repli : premier article mis en avant, sinon premier article.
        if featured:
            return featured[0]["slug"]
        return articles[0]["slug"]

    def _category_of(self, slug: str) -> str:
        for item in self.articles:
            if item["slug"] == slug:
                return item["category_key"]
        return ""

    async def _load_article(self, slug: str) -> None:
        self.active_article_slug = slug
        self.show_procedures = False
        self.open_procedure_slug = ""
        self.procedure_steps = []
        self.done_steps = []
        async with rx.asession() as asession:
            link_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT l.id, COALESCE(l.label, ''),
                               COALESCE(l.route, '/'), COALESCE(l.icon, 'arrow-right'),
                               COALESCE(l.description, '')
                        FROM guide_article_link l
                        JOIN guide_article a ON a.id = l.article_id
                        WHERE a.slug = :slug
                        ORDER BY l.position, l.id
                        LIMIT 12
                        """
                    ),
                    {"slug": slug},
                )
            ).all()
            base_query = """
                        SELECT p.id, p.slug, c.key, p.title,
                               COALESCE(p.objective, ''), COALESCE(p.context, ''),
                               COALESCE(p.expected_result, ''),
                               COALESCE(p.module_route, '/'),
                               COALESCE(p.estimated_minutes, 0), p.difficulty,
                               (SELECT COUNT(*) FROM guide_procedure_step s
                                  WHERE s.procedure_id = p.id)
                        FROM guide_procedure p
                        JOIN guide_category c ON c.id = p.category_id
                        LEFT JOIN guide_article a ON a.id = p.article_id
                        WHERE p.status = 'PUBLIE'
                    """
            category_key = self._category_of(slug)
            # 1) Procédures rattachées directement à l'article.
            proc_rows = (
                await asession.execute(
                    text(
                        f"""{base_query}
                          AND a.slug = :slug
                        ORDER BY p.position, p.title
                        LIMIT 6
                        """
                    ),
                    {"slug": slug},
                )
            ).all()
            scope = "article"
            # 2) Sinon, procédures de la même catégorie éditoriale.
            if not proc_rows and category_key:
                proc_rows = (
                    await asession.execute(
                        text(
                            f"""{base_query}
                          AND c.key = :category
                        ORDER BY p.position, p.title
                        LIMIT 6
                        """
                        ),
                        {"category": category_key},
                    )
                ).all()
                scope = "categorie"
            # 3) Sinon, procédures clés transverses de l'exploitation.
            if not proc_rows:
                proc_rows = (
                    await asession.execute(
                        text(
                            f"""{base_query}
                        ORDER BY c.position, p.position, p.title
                        LIMIT 6
                        """
                        )
                    )
                ).all()
                scope = "transverse"

        self.related_scope = scope
        self.article_links = [
            {
                "id": int(row[0]),
                "label": str(row[1]),
                "route": str(row[2]),
                "icon": str(row[3]),
                "description": str(row[4]),
            }
            for row in link_rows
        ]
        self.related_procedures = [
            {
                "id": int(row[0]),
                "slug": str(row[1]),
                "category_key": str(row[2]),
                "title": str(row[3]),
                "objective": str(row[4]),
                "context": str(row[5]),
                "expected_result": str(row[6]),
                "module_route": str(row[7]),
                "estimated_minutes": int(row[8] or 0),
                "difficulty_label": DIFFICULTY_LABELS.get(row[9], row[9]),
                "step_count": int(row[10] or 0),
            }
            for row in proc_rows
        ]

    async def _load_procedure(self, slug: str) -> None:
        self.open_procedure_slug = slug
        self.done_steps = []
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT s.id, s.position, COALESCE(s.title, ''),
                               COALESCE(s.instruction_farmer, ''),
                               COALESCE(s.instruction_pro, ''),
                               COALESCE(s.ui_hint, ''),
                               COALESCE(s.module_route, ''),
                               COALESCE(s.field_reference, ''),
                               COALESCE(s.why, ''), COALESCE(s.warning, ''),
                               COALESCE(s.duration_minutes, 0), s.is_optional
                        FROM guide_procedure_step s
                        JOIN guide_procedure p ON p.id = s.procedure_id
                        WHERE p.slug = :slug
                        ORDER BY s.position, s.id
                        LIMIT 40
                        """
                    ),
                    {"slug": slug},
                )
            ).all()
        self.procedure_steps = [
            {
                "id": int(row[0]),
                "position": int(row[1] or 0),
                "title": str(row[2]),
                "instruction_farmer": str(row[3]),
                "instruction_pro": str(row[4]),
                "ui_hint": str(row[5]),
                "module_route": str(row[6]),
                "field_reference": str(row[7]),
                "why": str(row[8]),
                "warning": str(row[9]),
                "duration_minutes": int(row[10] or 0),
                "is_optional": bool(row[11]),
            }
            for row in rows
        ]

    async def _load_path(self, slug: str) -> None:
        self.active_path_slug = slug
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT s.id, s.position, COALESCE(s.title, ''),
                               COALESCE(s.description, ''),
                               COALESCE(s.milestone, ''),
                               COALESCE(s.module_route, ''),
                               COALESCE(s.duration_minutes, 0), s.is_optional,
                               COALESCE(a.slug, ''), COALESCE(pr.slug, '')
                        FROM guide_learning_step s
                        JOIN guide_learning_path p ON p.id = s.path_id
                        LEFT JOIN guide_article a ON a.id = s.article_id
                        LEFT JOIN guide_procedure pr ON pr.id = s.procedure_id
                        WHERE p.slug = :slug
                        ORDER BY s.position, s.id
                        LIMIT 40
                        """
                    ),
                    {"slug": slug},
                )
            ).all()
        self.path_steps = [
            {
                "id": int(row[0]),
                "position": int(row[1] or 0),
                "title": str(row[2]),
                "description": str(row[3]),
                "milestone": str(row[4]),
                "module_route": str(row[5]),
                "duration_minutes": int(row[6] or 0),
                "is_optional": bool(row[7]),
                "article_slug": str(row[8]),
                "procedure_slug": str(row[9]),
            }
            for row in rows
        ]

    async def _run_search(self) -> None:
        needle = self.query.strip().lower()
        if len(needle) < 2:
            self.search_groups = []
            return
        params = {"q": f"%{needle}%"}
        async with rx.asession() as asession:
            article_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT a.slug, a.title, c.name,
                               COALESCE(NULLIF(a.summary, ''), a.body_farmer)
                        FROM guide_article a
                        JOIN guide_category c ON c.id = a.category_id
                        WHERE a.status = 'PUBLIE' AND (
                            LOWER(a.title) LIKE :q
                            OR LOWER(COALESCE(a.subtitle, '')) LIKE :q
                            OR LOWER(COALESCE(a.summary, '')) LIKE :q
                            OR LOWER(COALESCE(a.body_farmer, '')) LIKE :q
                            OR LOWER(COALESCE(a.body_pro, '')) LIKE :q
                            OR LOWER(COALESCE(a.keywords, '')) LIKE :q)
                        ORDER BY a.is_featured DESC, a.position, a.title
                        LIMIT 8
                        """
                    ),
                    params,
                )
            ).all()
            procedure_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT p.slug, p.title, c.name, COALESCE(p.objective, '')
                        FROM guide_procedure p
                        JOIN guide_category c ON c.id = p.category_id
                        WHERE p.status = 'PUBLIE' AND (
                            LOWER(p.title) LIKE :q
                            OR LOWER(COALESCE(p.objective, '')) LIKE :q
                            OR LOWER(COALESCE(p.context, '')) LIKE :q
                            OR LOWER(COALESCE(p.expected_result, '')) LIKE :q)
                        ORDER BY p.position, p.title
                        LIMIT 8
                        """
                    ),
                    params,
                )
            ).all()
            term_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT t.slug, t.term,
                               COALESCE(NULLIF(t.acronym, ''), COALESCE(c.name, '')),
                               COALESCE(t.definition_farmer, '')
                        FROM guide_term t
                        LEFT JOIN guide_category c ON c.id = t.category_id
                        WHERE t.status = 'PUBLIE' AND (
                            LOWER(t.term) LIKE :q
                            OR LOWER(COALESCE(t.acronym, '')) LIKE :q
                            OR LOWER(COALESCE(t.definition_farmer, '')) LIKE :q
                            OR LOWER(COALESCE(t.definition_pro, '')) LIKE :q
                            OR LOWER(COALESCE(t.synonyms, '')) LIKE :q)
                        ORDER BY t.term
                        LIMIT 8
                        """
                    ),
                    params,
                )
            ).all()
            faq_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT f.id, f.question, c.name,
                               COALESCE(f.answer_farmer, '')
                        FROM guide_faq f
                        JOIN guide_category c ON c.id = f.category_id
                        WHERE f.status = 'PUBLIE' AND (
                            LOWER(f.question) LIKE :q
                            OR LOWER(COALESCE(f.answer_farmer, '')) LIKE :q
                            OR LOWER(COALESCE(f.answer_pro, '')) LIKE :q
                            OR LOWER(COALESCE(f.keywords, '')) LIKE :q)
                        ORDER BY f.is_frequent DESC, f.position
                        LIMIT 8
                        """
                    ),
                    params,
                )
            ).all()
            rule_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT r.code, r.title, r.kind,
                               COALESCE(r.statement, '')
                        FROM guide_rule r
                        WHERE r.status = 'PUBLIE' AND (
                            LOWER(r.title) LIKE :q
                            OR LOWER(COALESCE(r.statement, '')) LIKE :q
                            OR LOWER(COALESCE(r.rationale, '')) LIKE :q
                            OR LOWER(COALESCE(r.remediation, '')) LIKE :q
                            OR LOWER(r.code) LIKE :q)
                        ORDER BY r.code
                        LIMIT 8
                        """
                    ),
                    params,
                )
            ).all()
            path_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT p.slug, p.title, COALESCE(p.subtitle, ''),
                               COALESCE(p.objective, '')
                        FROM guide_learning_path p
                        WHERE p.status = 'PUBLIE' AND (
                            LOWER(p.title) LIKE :q
                            OR LOWER(COALESCE(p.subtitle, '')) LIKE :q
                            OR LOWER(COALESCE(p.objective, '')) LIKE :q)
                        ORDER BY p.position, p.title
                        LIMIT 8
                        """
                    ),
                    params,
                )
            ).all()

        raw: list[tuple[str, str, str, str, list]] = [
            ("article", "Articles", "file-text", "vegetal", list(article_rows)),
            (
                "procedure",
                "Procédures",
                "list-checks",
                "operations",
                list(procedure_rows),
            ),
            ("term", "Dictionnaire", "book-a", "humain", list(term_rows)),
            (
                "faq",
                "Questions fréquentes",
                "message-circle-question",
                "flotte",
                list(faq_rows),
            ),
            ("rule", "Règles", "shield-alert", "alerte", list(rule_rows)),
            (
                "path",
                "Parcours",
                "graduation-cap",
                "vegetal",
                list(path_rows),
            ),
        ]

        singulars: dict[str, str] = {
            "article": "Article",
            "procedure": "Procédure",
            "term": "Terme",
            "faq": "Question",
            "rule": "Règle",
            "path": "Parcours",
        }

        groups: list[SearchGroup] = []
        for kind, label, icon, tone, rows in raw:
            if not rows:
                continue
            hits: list[SearchHit] = []
            for row in rows:
                ref = str(row[0])
                subtitle = str(row[2])
                if kind == "rule":
                    subtitle = RULE_KIND_LABELS.get(subtitle, subtitle)
                hits.append(
                    {
                        "key": f"{kind}-{ref}",
                        "kind": kind,
                        "kind_label": singulars[kind],
                        "icon": icon,
                        "title": str(row[1]),
                        "subtitle": subtitle,
                        "excerpt": _short(row[3], 130),
                        "ref": ref,
                    }
                )
            groups.append(
                {
                    "kind": kind,
                    "label": label,
                    "icon": icon,
                    "tone": tone,
                    "count": len(hits),
                    "hits": hits,
                }
            )
        self.search_groups = groups

    # ------------------------------------------------------------------
    # Événements de l'interface
    # ------------------------------------------------------------------

    @rx.event
    def set_section(self, value: str):
        self.active_section = value

    @rx.event
    async def set_query(self, value: str):
        self.query = value
        await self._run_search()

    @rx.event
    async def clear_query(self):
        self.query = ""
        self.search_groups = []

    @rx.event
    def select_category(self, key: str):
        self.selected_category = key
        self.active_section = "bibliotheque"

    @rx.event
    async def select_article(self, slug: str):
        self.active_section = "bibliotheque"
        await self._load_article(slug)

    @rx.event
    async def open_related_procedures(self):
        self.show_procedures = True
        if len(self.related_procedures) == 1:
            await self._load_procedure(self.related_procedures[0]["slug"])

    @rx.event
    async def start_procedure(self, slug: str):
        self.show_procedures = True
        await self._load_procedure(slug)

    @rx.event
    def close_procedure(self):
        self.open_procedure_slug = ""
        self.procedure_steps = []
        self.done_steps = []

    @rx.event
    def toggle_step(self, step_id: int):
        if step_id in self.done_steps:
            self.done_steps = [
                item for item in self.done_steps if item != step_id
            ]
        else:
            self.done_steps = self.done_steps + [step_id]

    @rx.event
    def set_term_query(self, value: str):
        self.term_query = value

    @rx.event
    def select_term(self, slug: str):
        self.active_term_slug = slug
        self.active_section = "dictionnaire"

    @rx.event
    def toggle_faq(self, faq_id: int):
        self.open_faq_id = 0 if self.open_faq_id == faq_id else faq_id

    @rx.event
    def set_rule_filter(self, value: str):
        self.rule_filter = value

    @rx.event
    async def select_path(self, slug: str):
        self.active_section = "parcours"
        await self._load_path(slug)

    @rx.event
    def select_relation(self, key: str):
        self.active_relation = key
        self.active_section = "relations"

    @rx.event
    async def open_hit(self, kind: str, ref: str):
        if kind == "article":
            self.active_section = "bibliotheque"
            await self._load_article(ref)
        elif kind == "procedure":
            self.active_section = "bibliotheque"
            self.show_procedures = True
            await self._load_procedure(ref)
        elif kind == "term":
            self.active_section = "dictionnaire"
            self.active_term_slug = ref
        elif kind == "faq":
            self.active_section = "faq"
            self.open_faq_id = int(ref)
        elif kind == "rule":
            self.active_section = "regles"
            self.rule_filter = "TOUS"
            self.selected_category = "TOUS"
        elif kind == "path":
            self.active_section = "parcours"
            await self._load_path(ref)

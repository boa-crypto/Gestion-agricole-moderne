"""État du pupitre éditorial du Guide Agricole (administration des contenus).

Toutes les lectures ET les écritures sont faites en SQL brut via `rx.asession()`
sur la base SQLite locale de l'application. Aucune migration n'est touchée : les
tables `guide_*` existantes (articles, procédures, dictionnaire, FAQ, règles,
versions et changelog) suffisent, l'archivage se faisant par le statut éditorial
`ARCHIVE` plutôt que par une suppression destructive.
"""

from __future__ import annotations

import datetime
import re
from typing import Any, TypedDict

import reflex as rx
from sqlalchemy import text

from app.date_utils import as_date
from app.seed_guide import GUIDE_AUTHOR, GUIDE_VERSION, seed_guide_data
from app.states.dashboard_state import MONTHS
from app.states.guide_state import GuideState

# ---------------------------------------------------------------------------
# Référentiels éditoriaux (noms d'énumérations stockés en base)
# ---------------------------------------------------------------------------

STATUS_LABELS: dict[str, str] = {
    "BROUILLON": "Brouillon",
    "RELECTURE": "En relecture",
    "PUBLIE": "Publié",
    "ARCHIVE": "Archivé",
}

STATUS_TONES: dict[str, str] = {
    "BROUILLON": "muted",
    "RELECTURE": "warn",
    "PUBLIE": "good",
    "ARCHIVE": "bad",
}

CHANGE_LABELS: dict[str, str] = {
    "AJOUT": "Ajout",
    "MISE_A_JOUR": "Mise à jour",
    "CORRECTION": "Correction",
    "SUPPRESSION": "Archivage",
}

RULE_KIND_LABELS: dict[str, str] = {
    "POURQUOI": "Pourquoi ?",
    "ATTENTION": "Attention",
    "COHERENCE": "Cohérence",
    "BONNE_PRATIQUE": "Bonne pratique",
}

SEVERITY_LABELS: dict[str, str] = {
    "INFO": "Information",
    "ATTENTION": "Attention",
    "CRITIQUE": "Critique",
}

DIFFICULTY_LABELS: dict[str, str] = {
    "DECOUVERTE": "Découverte",
    "INTERMEDIAIRE": "Intermédiaire",
    "AVANCE": "Avancé",
}

AUDIENCE_LABELS: dict[str, str] = {
    "AGRICOLE": "Lecture agricole",
    "AGRIPRO": "Lecture AgriPro",
    "MIXTE": "Double lecture",
}

KIND_LABELS: dict[str, str] = {
    "article": "Article",
    "procedure": "Procédure",
    "term": "Terme",
    "faq": "Question",
    "rule": "Règle",
}

KIND_TABLES: dict[str, str] = {
    "article": "guide_article",
    "procedure": "guide_procedure",
    "term": "guide_term",
    "faq": "guide_faq",
    "rule": "guide_rule",
}

ENTITY_TYPES: dict[str, str] = {
    "article": "ARTICLE",
    "procedure": "PROCEDURE",
    "term": "TERME",
    "faq": "QUESTION",
    "rule": "REGLE",
}

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9\-]{2,59}$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


class CategoryOption(TypedDict):
    key: str
    name: str


class VersionRow(TypedDict):
    id: int
    version_label: str
    title: str
    summary: str
    changelog: str
    author: str
    status: str
    status_label: str
    tone: str
    published_label: str
    is_current: bool
    entry_count: int


class ChangelogRow(TypedDict):
    id: int
    entity_type: str
    entity_ref: str
    change_kind: str
    change_label: str
    summary: str
    author: str
    position: int


class ContentRow(TypedDict):
    id: int
    kind: str
    kind_label: str
    ref: str
    title: str
    subtitle: str
    category_key: str
    category_name: str
    status: str
    status_label: str
    tone: str
    version_label: str
    author: str
    date_label: str
    excerpt: str


EMPTY_DRAFT: dict[str, str] = {
    "id": "0",
    "kind": "article",
    "ref": "",
    "slug": "",
    "title": "",
    "subtitle": "",
    "summary": "",
    "body_farmer": "",
    "body_pro": "",
    "question": "",
    "answer_farmer": "",
    "answer_pro": "",
    "term": "",
    "acronym": "",
    "definition_farmer": "",
    "definition_pro": "",
    "unit": "",
    "formula": "",
    "example": "",
    "synonyms": "",
    "related_terms": "",
    "code": "",
    "rule_kind": "COHERENCE",
    "severity": "INFO",
    "statement": "",
    "rationale": "",
    "consequence": "",
    "remediation": "",
    "field_reference": "",
    "objective": "",
    "context": "",
    "expected_result": "",
    "prerequisites": "",
    "module_route": "",
    "keywords": "",
    "author": GUIDE_AUTHOR,
    "version_label": GUIDE_VERSION,
    "status": "BROUILLON",
    "category_key": "",
    "difficulty": "DECOUVERTE",
    "audience": "MIXTE",
    "reading_minutes": "3",
    "estimated_minutes": "5",
    "is_blocking": "0",
    "is_featured": "0",
    "is_frequent": "0",
    "published_label": "—",
    "reviewed_label": "—",
    "category_name": "",
    "kind_label": "Article",
}

EMPTY_VERSION_ROW: VersionRow = {
    "id": 0,
    "version_label": "—",
    "title": "Aucune version",
    "summary": "",
    "changelog": "",
    "author": "",
    "status": "BROUILLON",
    "status_label": "Brouillon",
    "tone": "muted",
    "published_label": "—",
    "is_current": False,
    "entry_count": 0,
}

# Requêtes de registre : une par type de contenu, colonnes normalisées.
_LIST_SQL: dict[str, str] = {
    "article": """
        SELECT a.id, a.slug, a.title, COALESCE(a.subtitle, ''),
               COALESCE(c.key, ''), COALESCE(c.name, ''), a.status,
               COALESCE(a.version_label, ''), COALESCE(a.author, ''),
               a.published_on, COALESCE(a.summary, '')
        FROM guide_article a
        LEFT JOIN guide_category c ON c.id = a.category_id
        WHERE 1 = 1 {filters}
        ORDER BY a.status, a.position, a.title
        LIMIT 150
    """,
    "procedure": """
        SELECT p.id, p.slug, p.title, COALESCE(p.expected_result, ''),
               COALESCE(c.key, ''), COALESCE(c.name, ''), p.status,
               COALESCE(p.version_label, ''), '',
               p.created_at, COALESCE(p.objective, '')
        FROM guide_procedure p
        LEFT JOIN guide_category c ON c.id = p.category_id
        WHERE 1 = 1 {filters}
        ORDER BY p.status, p.position, p.title
        LIMIT 150
    """,
    "term": """
        SELECT t.id, t.slug, t.term, COALESCE(t.acronym, ''),
               COALESCE(c.key, ''), COALESCE(c.name, ''), t.status,
               COALESCE(t.version_label, ''), '',
               t.created_at, COALESCE(t.definition_farmer, '')
        FROM guide_term t
        LEFT JOIN guide_category c ON c.id = t.category_id
        WHERE 1 = 1 {filters}
        ORDER BY t.status, t.term
        LIMIT 200
    """,
    "faq": """
        SELECT f.id, CAST(f.id AS TEXT), f.question, '',
               COALESCE(c.key, ''), COALESCE(c.name, ''), f.status,
               COALESCE(f.version_label, ''), '',
               f.created_at, COALESCE(f.answer_farmer, '')
        FROM guide_faq f
        LEFT JOIN guide_category c ON c.id = f.category_id
        WHERE 1 = 1 {filters}
        ORDER BY f.status, f.position, f.id
        LIMIT 200
    """,
    "rule": """
        SELECT r.id, r.code, r.title, r.kind,
               COALESCE(c.key, ''), COALESCE(c.name, ''), r.status,
               COALESCE(r.version_label, ''), '',
               r.created_at, COALESCE(r.statement, '')
        FROM guide_rule r
        LEFT JOIN guide_category c ON c.id = r.category_id
        WHERE 1 = 1 {filters}
        ORDER BY r.status, r.code
        LIMIT 200
    """,
}

_FILTERS: dict[str, dict[str, str]] = {
    "article": {
        "status": " AND a.status = :status",
        "category": " AND c.key = :category",
        "search": (
            " AND (LOWER(a.title) LIKE :q OR LOWER(a.slug) LIKE :q"
            " OR LOWER(COALESCE(a.summary, '')) LIKE :q)"
        ),
    },
    "procedure": {
        "status": " AND p.status = :status",
        "category": " AND c.key = :category",
        "search": (
            " AND (LOWER(p.title) LIKE :q OR LOWER(p.slug) LIKE :q"
            " OR LOWER(COALESCE(p.objective, '')) LIKE :q)"
        ),
    },
    "term": {
        "status": " AND t.status = :status",
        "category": " AND c.key = :category",
        "search": (
            " AND (LOWER(t.term) LIKE :q OR LOWER(t.slug) LIKE :q"
            " OR LOWER(COALESCE(t.definition_farmer, '')) LIKE :q)"
        ),
    },
    "faq": {
        "status": " AND f.status = :status",
        "category": " AND c.key = :category",
        "search": (
            " AND (LOWER(f.question) LIKE :q"
            " OR LOWER(COALESCE(f.answer_farmer, '')) LIKE :q)"
        ),
    },
    "rule": {
        "status": " AND r.status = :status",
        "category": " AND c.key = :category",
        "search": (
            " AND (LOWER(r.title) LIKE :q OR LOWER(r.code) LIKE :q"
            " OR LOWER(COALESCE(r.statement, '')) LIKE :q)"
        ),
    },
}

_DETAIL_SQL: dict[str, str] = {
    "article": """
        SELECT a.id, a.slug, a.title, COALESCE(a.subtitle, ''),
               COALESCE(a.summary, ''), COALESCE(a.body_farmer, ''),
               COALESCE(a.body_pro, ''), a.audience, a.status, a.difficulty,
               COALESCE(a.reading_minutes, 0), COALESCE(a.keywords, ''),
               COALESCE(a.author, ''), COALESCE(a.version_label, ''),
               COALESCE(a.module_route, ''), a.published_on, a.reviewed_on,
               a.is_featured, COALESCE(c.key, ''), COALESCE(c.name, '')
        FROM guide_article a
        LEFT JOIN guide_category c ON c.id = a.category_id
        WHERE a.id = :id
    """,
    "procedure": """
        SELECT p.id, p.slug, p.title, COALESCE(p.objective, ''),
               COALESCE(p.context, ''), COALESCE(p.expected_result, ''),
               COALESCE(p.prerequisites, ''), COALESCE(p.module_route, ''),
               COALESCE(p.estimated_minutes, 0), p.difficulty, p.audience,
               p.status, COALESCE(p.version_label, ''),
               COALESCE(c.key, ''), COALESCE(c.name, '')
        FROM guide_procedure p
        LEFT JOIN guide_category c ON c.id = p.category_id
        WHERE p.id = :id
    """,
    "term": """
        SELECT t.id, t.slug, t.term, COALESCE(t.acronym, ''),
               COALESCE(t.definition_farmer, ''), COALESCE(t.definition_pro, ''),
               COALESCE(t.unit, ''), COALESCE(t.formula, ''),
               COALESCE(t.example, ''), COALESCE(t.synonyms, ''),
               COALESCE(t.related_terms, ''), COALESCE(t.module_route, ''),
               t.status, COALESCE(t.version_label, ''),
               COALESCE(c.key, ''), COALESCE(c.name, '')
        FROM guide_term t
        LEFT JOIN guide_category c ON c.id = t.category_id
        WHERE t.id = :id
    """,
    "faq": """
        SELECT f.id, f.question, COALESCE(f.answer_farmer, ''),
               COALESCE(f.answer_pro, ''), f.audience, f.status,
               COALESCE(f.keywords, ''), COALESCE(f.module_route, ''),
               f.is_frequent, COALESCE(f.version_label, ''),
               COALESCE(c.key, ''), COALESCE(c.name, '')
        FROM guide_faq f
        LEFT JOIN guide_category c ON c.id = f.category_id
        WHERE f.id = :id
    """,
    "rule": """
        SELECT r.id, r.code, r.kind, r.severity, r.title,
               COALESCE(r.statement, ''), COALESCE(r.rationale, ''),
               COALESCE(r.consequence, ''), COALESCE(r.remediation, ''),
               COALESCE(r.module_route, ''), COALESCE(r.field_reference, ''),
               r.is_blocking, r.status, COALESCE(r.version_label, ''),
               COALESCE(c.key, ''), COALESCE(c.name, '')
        FROM guide_rule r
        LEFT JOIN guide_category c ON c.id = r.category_id
        WHERE r.id = :id
    """,
}


def _fmt_date(value: object) -> str:
    day = as_date(value)
    if day is None:
        return "—"
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _short(value: object, size: int = 150) -> str:
    raw = str(value or "").strip().replace("\n", " ")
    if not raw:
        return "Aucun résumé consigné."
    if len(raw) <= size:
        return raw
    return f"{raw[:size].rstrip()}…"


def _as_int(value: object, fallback: int = 0) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return fallback


def _flag(value: object) -> bool:
    return str(value).strip().lower() in ("1", "on", "true", "oui")


def _validate(kind: str, data: dict[str, str]) -> list[str]:
    """Contrôles de cohérence éditoriale avant écriture."""
    errors: list[str] = []
    if data.get("status", "") not in STATUS_LABELS:
        errors.append("Le statut éditorial est invalide.")
    version = data.get("version_label", "").strip()
    if not version:
        errors.append("La version éditoriale est obligatoire (ex. 1.1.0).")
    elif not VERSION_PATTERN.fullmatch(version):
        errors.append("La version doit suivre le format numérique X.Y.Z.")
    if data.get("category_key", "") in ("", "TOUS"):
        errors.append("La catégorie du guide est obligatoire.")

    if kind == "article":
        slug = data.get("slug", "").strip()
        if not SLUG_PATTERN.fullmatch(slug):
            errors.append(
                "L'identifiant (slug) doit être en minuscules, chiffres et tirets."
            )
        if len(data.get("title", "").strip()) < 4:
            errors.append("Le titre doit comporter au moins 4 caractères.")
        if len(data.get("body_farmer", "").strip()) < 40:
            errors.append(
                "La lecture agricole doit faire au moins 40 caractères."
            )
        if len(data.get("body_pro", "").strip()) < 40:
            errors.append(
                "La lecture AgriPro doit faire au moins 40 caractères."
            )
        minutes = _as_int(data.get("reading_minutes"), 0)
        if minutes < 1 or minutes > 90:
            errors.append(
                "La durée de lecture doit être comprise entre 1 et 90 minutes."
            )
        if data.get("audience", "") not in AUDIENCE_LABELS:
            errors.append("Le niveau de lecture est invalide.")
        if data.get("difficulty", "") not in DIFFICULTY_LABELS:
            errors.append("Le niveau de difficulté est invalide.")
    elif kind == "procedure":
        slug = data.get("slug", "").strip()
        if not SLUG_PATTERN.fullmatch(slug):
            errors.append(
                "L'identifiant (slug) doit être en minuscules, chiffres et tirets."
            )
        if len(data.get("title", "").strip()) < 4:
            errors.append("Le titre de la procédure est trop court.")
        if len(data.get("objective", "").strip()) < 20:
            errors.append(
                "L'objectif doit être explicite (20 caractères minimum)."
            )
        minutes = _as_int(data.get("estimated_minutes"), 0)
        if minutes < 1 or minutes > 240:
            errors.append(
                "La durée estimée doit être comprise entre 1 et 240 minutes."
            )
        if data.get("difficulty", "") not in DIFFICULTY_LABELS:
            errors.append("Le niveau de difficulté est invalide.")
    elif kind == "term":
        slug = data.get("slug", "").strip()
        if not SLUG_PATTERN.fullmatch(slug):
            errors.append(
                "L'identifiant (slug) doit être en minuscules, chiffres et tirets."
            )
        if len(data.get("term", "").strip()) < 2:
            errors.append("L'entrée du dictionnaire est obligatoire.")
        if len(data.get("definition_farmer", "").strip()) < 15:
            errors.append("La définition agricole est trop courte.")
        if len(data.get("definition_pro", "").strip()) < 15:
            errors.append("La définition AgriPro est trop courte.")
    elif kind == "faq":
        question = data.get("question", "").strip()
        if len(question) < 8:
            errors.append("La question doit être formulée complètement.")
        elif not question.endswith("?"):
            errors.append(
                "La question doit se terminer par un point d'interrogation."
            )
        if len(data.get("answer_farmer", "").strip()) < 20:
            errors.append("La réponse agricole est trop courte.")
        if len(data.get("answer_pro", "").strip()) < 20:
            errors.append("La réponse AgriPro est trop courte.")
    elif kind == "rule":
        code = data.get("code", "").strip().upper()
        if not CODE_PATTERN.fullmatch(code):
            errors.append(
                "Le code de règle doit être en majuscules (ex. COH-PARC-004)."
            )
        if len(data.get("title", "").strip()) < 6:
            errors.append("Le titre de la règle est trop court.")
        if len(data.get("statement", "").strip()) < 20:
            errors.append("L'énoncé de la règle est trop court.")
        if len(data.get("rationale", "").strip()) < 20:
            errors.append(
                "La justification « Pourquoi ? » doit être renseignée."
            )
        if data.get("rule_kind", "") not in RULE_KIND_LABELS:
            errors.append("La nature de la règle est invalide.")
        if data.get("severity", "") not in SEVERITY_LABELS:
            errors.append("La sévérité de la règle est invalide.")
    else:
        errors.append("Type de contenu inconnu.")
    return errors


class GuideAdminState(rx.State):
    """Pupitre éditorial : versions publiées et contenus du guide."""

    is_loading: bool = True
    is_saving: bool = False
    error: str = ""
    notice: str = ""
    form_errors: list[str] = []

    categories: list[CategoryOption] = []
    versions: list[VersionRow] = []
    selected_version_id: int = 0
    changelog: list[ChangelogRow] = []

    content_kind: str = "article"
    filter_category: str = "TOUS"
    filter_status: str = "TOUS"
    search: str = ""
    items: list[ContentRow] = []

    kind_totals: dict[str, int] = {
        "article": 0,
        "procedure": 0,
        "term": 0,
        "faq": 0,
        "rule": 0,
    }
    status_totals: dict[str, int] = {
        "BROUILLON": 0,
        "RELECTURE": 0,
        "PUBLIE": 0,
        "ARCHIVE": 0,
        "TOTAL": 0,
    }

    editor_open: bool = False
    editor_mode: str = "create"
    draft: dict[str, str] = EMPTY_DRAFT

    preview_open: bool = False
    preview: dict[str, str] = EMPTY_DRAFT

    version_form_open: bool = False

    # Référentiels exposés au frontend -----------------------------------
    kind_tabs: list[tuple[str, str, str]] = [
        ("article", "Articles", "file-text"),
        ("procedure", "Procédures", "list-checks"),
        ("term", "Dictionnaire", "book-a"),
        ("faq", "Questions", "message-circle-question"),
        ("rule", "Règles", "shield-alert"),
    ]
    status_options: list[tuple[str, str]] = [
        ("BROUILLON", "Brouillon"),
        ("RELECTURE", "En relecture"),
        ("PUBLIE", "Publié"),
        ("ARCHIVE", "Archivé"),
    ]
    audience_options: list[tuple[str, str]] = [
        ("AGRICOLE", "Lecture agricole"),
        ("AGRIPRO", "Lecture AgriPro"),
        ("MIXTE", "Double lecture"),
    ]
    difficulty_options: list[tuple[str, str]] = [
        ("DECOUVERTE", "Découverte"),
        ("INTERMEDIAIRE", "Intermédiaire"),
        ("AVANCE", "Avancé"),
    ]
    rule_kind_options: list[tuple[str, str]] = [
        ("POURQUOI", "Pourquoi ?"),
        ("ATTENTION", "Attention"),
        ("COHERENCE", "Cohérence"),
        ("BONNE_PRATIQUE", "Bonne pratique"),
    ]
    severity_options: list[tuple[str, str]] = [
        ("INFO", "Information"),
        ("ATTENTION", "Attention"),
        ("CRITIQUE", "Critique"),
    ]

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def kind_label(self) -> str:
        return KIND_LABELS.get(self.content_kind, "Contenu")

    @rx.var
    def current_version(self) -> VersionRow:
        for item in self.versions:
            if item["is_current"]:
                return item
        if self.versions:
            return self.versions[0]
        return EMPTY_VERSION_ROW

    @rx.var
    def selected_version(self) -> VersionRow:
        for item in self.versions:
            if item["id"] == self.selected_version_id:
                return item
        return self.current_version

    @rx.var
    def has_current_version(self) -> bool:
        return self.current_version["id"] > 0

    @rx.var
    def has_errors(self) -> bool:
        return len(self.form_errors) > 0

    @rx.var
    def editor_key(self) -> str:
        return f"{self.editor_mode}-{self.draft['kind']}-{self.draft['id']}"

    @rx.var
    def editor_title(self) -> str:
        label = KIND_LABELS.get(self.draft["kind"], "Contenu")
        if self.editor_mode == "create":
            return f"Nouveau contenu · {label}"
        return f"Édition · {label}"

    @rx.var
    def visible_count(self) -> int:
        return len(self.items)

    @rx.var
    def next_version_suggestion(self) -> str:
        label = self.current_version["version_label"]
        if not VERSION_PATTERN.fullmatch(label):
            return "1.1.0"
        major, minor, patch = (int(part) for part in label.split("."))
        return f"{major}.{minor + 1}.0"

    # ------------------------------------------------------------------
    # Lectures
    # ------------------------------------------------------------------

    async def _load_reference(self) -> None:
        async with rx.asession() as asession:
            category_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT c.key, c.name
                        FROM guide_category c
                        WHERE c.is_active = 1
                        ORDER BY c.position, c.name
                        LIMIT 40
                        """
                    )
                )
            ).all()
            count_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT 'article', COUNT(*) FROM guide_article
                        UNION ALL SELECT 'procedure', COUNT(*) FROM guide_procedure
                        UNION ALL SELECT 'term', COUNT(*) FROM guide_term
                        UNION ALL SELECT 'faq', COUNT(*) FROM guide_faq
                        UNION ALL SELECT 'rule', COUNT(*) FROM guide_rule
                        """
                    )
                )
            ).all()
        self.categories = [
            {"key": str(row[0]), "name": str(row[1])} for row in category_rows
        ]
        totals = {
            "article": 0,
            "procedure": 0,
            "term": 0,
            "faq": 0,
            "rule": 0,
        }
        for row in count_rows:
            totals[str(row[0])] = int(row[1] or 0)
        self.kind_totals = totals

    async def _load_versions(self) -> None:
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT v.id, v.version_label, v.title,
                               COALESCE(v.summary, ''), COALESCE(v.changelog, ''),
                               COALESCE(v.author, ''), v.status, v.published_on,
                               v.is_current,
                               (SELECT COUNT(*) FROM guide_version_entry e
                                  WHERE e.version_id = v.id)
                        FROM guide_version v
                        ORDER BY v.is_current DESC, v.published_on DESC, v.id DESC
                        LIMIT 40
                        """
                    )
                )
            ).all()
        self.versions = [
            {
                "id": int(row[0]),
                "version_label": str(row[1]),
                "title": str(row[2]),
                "summary": str(row[3]),
                "changelog": str(row[4]),
                "author": str(row[5]),
                "status": str(row[6]),
                "status_label": STATUS_LABELS.get(row[6], row[6]),
                "tone": STATUS_TONES.get(row[6], "muted"),
                "published_label": _fmt_date(row[7]),
                "is_current": bool(row[8]),
                "entry_count": int(row[9] or 0),
            }
            for row in rows
        ]
        if self.selected_version_id == 0 or all(
            item["id"] != self.selected_version_id for item in self.versions
        ):
            self.selected_version_id = (
                self.versions[0]["id"] if self.versions else 0
            )

    async def _load_changelog(self) -> None:
        if self.selected_version_id == 0:
            self.changelog = []
            return
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT e.id, e.entity_type, e.entity_ref, e.change_kind,
                               COALESCE(e.summary, ''), COALESCE(e.author, ''),
                               COALESCE(e.position, 0)
                        FROM guide_version_entry e
                        WHERE e.version_id = :vid
                        ORDER BY e.position DESC, e.id DESC
                        LIMIT 60
                        """
                    ),
                    {"vid": self.selected_version_id},
                )
            ).all()
        self.changelog = [
            {
                "id": int(row[0]),
                "entity_type": str(row[1]),
                "entity_ref": str(row[2]),
                "change_kind": str(row[3]),
                "change_label": CHANGE_LABELS.get(row[3], row[3]),
                "summary": str(row[4]),
                "author": str(row[5]),
                "position": int(row[6] or 0),
            }
            for row in rows
        ]

    async def _load_items(self) -> None:
        kind = self.content_kind
        filters = ""
        params: dict[str, str] = {}
        if self.filter_status != "TOUS":
            filters += _FILTERS[kind]["status"]
            params["status"] = self.filter_status
        if self.filter_category != "TOUS":
            filters += _FILTERS[kind]["category"]
            params["category"] = self.filter_category
        needle = self.search.strip().lower()
        if needle:
            filters += _FILTERS[kind]["search"]
            params["q"] = f"%{needle}%"
        query = _LIST_SQL[kind].format(filters=filters)
        status_sql = f"""
            SELECT {KIND_TABLES[kind]}.status, COUNT(*)
            FROM {KIND_TABLES[kind]}
            GROUP BY {KIND_TABLES[kind]}.status
        """
        async with rx.asession() as asession:
            rows = (await asession.execute(text(query), params)).all()
            status_rows = (await asession.execute(text(status_sql))).all()

        items: list[ContentRow] = []
        for row in rows:
            status = str(row[6])
            items.append(
                {
                    "id": int(row[0]),
                    "kind": kind,
                    "kind_label": KIND_LABELS.get(kind, "Contenu"),
                    "ref": str(row[1]),
                    "title": str(row[2]),
                    "subtitle": str(row[3]),
                    "category_key": str(row[4]),
                    "category_name": str(row[5]),
                    "status": status,
                    "status_label": STATUS_LABELS.get(status, status),
                    "tone": STATUS_TONES.get(status, "muted"),
                    "version_label": str(row[7]),
                    "author": str(row[8]),
                    "date_label": _fmt_date(row[9]),
                    "excerpt": _short(row[10]),
                }
            )
        self.items = items

        totals = {
            "BROUILLON": 0,
            "RELECTURE": 0,
            "PUBLIE": 0,
            "ARCHIVE": 0,
            "TOTAL": 0,
        }
        for row in status_rows:
            key = str(row[0])
            count = int(row[1] or 0)
            if key in totals:
                totals[key] = count
            totals["TOTAL"] += count
        self.status_totals = totals

    @rx.event
    async def load_admin(self):
        """Charge le pupitre éditorial (référentiels, versions, registre)."""
        self.is_loading = True
        self.error = ""
        yield
        await seed_guide_data()
        await self._load_reference()
        await self._load_versions()
        await self._load_changelog()
        await self._load_items()
        self.is_loading = False

    # ------------------------------------------------------------------
    # Navigation du registre
    # ------------------------------------------------------------------

    @rx.event
    async def set_content_kind(self, kind: str):
        self.content_kind = kind
        self.notice = ""
        await self._load_items()

    @rx.event
    async def set_filter_category(self, value: str):
        self.filter_category = value
        await self._load_items()

    @rx.event
    async def set_filter_status(self, value: str):
        self.filter_status = value
        await self._load_items()

    @rx.event
    async def set_search(self, value: str):
        self.search = value
        await self._load_items()

    @rx.event
    async def reset_filters(self):
        self.filter_category = "TOUS"
        self.filter_status = "TOUS"
        self.search = ""
        await self._load_items()

    @rx.event
    async def select_version(self, version_id: int):
        self.selected_version_id = version_id
        await self._load_changelog()

    @rx.event
    def toggle_version_form(self):
        self.version_form_open = not self.version_form_open
        self.form_errors = []

    @rx.event
    def close_preview(self):
        self.preview_open = False

    # ------------------------------------------------------------------
    # Chargement d'une fiche
    # ------------------------------------------------------------------

    async def _read_record(self, kind: str, item_id: int) -> dict[str, str]:
        async with rx.asession() as asession:
            row = (
                await asession.execute(text(_DETAIL_SQL[kind]), {"id": item_id})
            ).first()
        draft = dict(EMPTY_DRAFT)
        draft["kind"] = kind
        draft["kind_label"] = KIND_LABELS.get(kind, "Contenu")
        if row is None:
            return draft
        draft["id"] = str(int(row[0]))
        if kind == "article":
            draft.update(
                {
                    "ref": str(row[1]),
                    "slug": str(row[1]),
                    "title": str(row[2]),
                    "subtitle": str(row[3]),
                    "summary": str(row[4]),
                    "body_farmer": str(row[5]),
                    "body_pro": str(row[6]),
                    "audience": str(row[7]),
                    "status": str(row[8]),
                    "difficulty": str(row[9]),
                    "reading_minutes": str(int(row[10] or 0)),
                    "keywords": str(row[11]),
                    "author": str(row[12]),
                    "version_label": str(row[13]),
                    "module_route": str(row[14]),
                    "published_label": _fmt_date(row[15]),
                    "reviewed_label": _fmt_date(row[16]),
                    "is_featured": "1" if bool(row[17]) else "0",
                    "category_key": str(row[18]),
                    "category_name": str(row[19]),
                }
            )
        elif kind == "procedure":
            draft.update(
                {
                    "ref": str(row[1]),
                    "slug": str(row[1]),
                    "title": str(row[2]),
                    "objective": str(row[3]),
                    "context": str(row[4]),
                    "expected_result": str(row[5]),
                    "prerequisites": str(row[6]),
                    "module_route": str(row[7]),
                    "estimated_minutes": str(int(row[8] or 0)),
                    "difficulty": str(row[9]),
                    "audience": str(row[10]),
                    "status": str(row[11]),
                    "version_label": str(row[12]),
                    "category_key": str(row[13]),
                    "category_name": str(row[14]),
                }
            )
        elif kind == "term":
            draft.update(
                {
                    "ref": str(row[1]),
                    "slug": str(row[1]),
                    "term": str(row[2]),
                    "title": str(row[2]),
                    "acronym": str(row[3]),
                    "definition_farmer": str(row[4]),
                    "definition_pro": str(row[5]),
                    "unit": str(row[6]),
                    "formula": str(row[7]),
                    "example": str(row[8]),
                    "synonyms": str(row[9]),
                    "related_terms": str(row[10]),
                    "module_route": str(row[11]),
                    "status": str(row[12]),
                    "version_label": str(row[13]),
                    "category_key": str(row[14]),
                    "category_name": str(row[15]),
                }
            )
        elif kind == "faq":
            draft.update(
                {
                    "ref": str(int(row[0])),
                    "question": str(row[1]),
                    "title": str(row[1]),
                    "answer_farmer": str(row[2]),
                    "answer_pro": str(row[3]),
                    "audience": str(row[4]),
                    "status": str(row[5]),
                    "keywords": str(row[6]),
                    "module_route": str(row[7]),
                    "is_frequent": "1" if bool(row[8]) else "0",
                    "version_label": str(row[9]),
                    "category_key": str(row[10]),
                    "category_name": str(row[11]),
                }
            )
        elif kind == "rule":
            draft.update(
                {
                    "ref": str(row[1]),
                    "code": str(row[1]),
                    "rule_kind": str(row[2]),
                    "severity": str(row[3]),
                    "title": str(row[4]),
                    "statement": str(row[5]),
                    "rationale": str(row[6]),
                    "consequence": str(row[7]),
                    "remediation": str(row[8]),
                    "module_route": str(row[9]),
                    "field_reference": str(row[10]),
                    "is_blocking": "1" if bool(row[11]) else "0",
                    "status": str(row[12]),
                    "version_label": str(row[13]),
                    "category_key": str(row[14]),
                    "category_name": str(row[15]),
                }
            )
        return draft

    @rx.event
    async def start_edit(self, kind: str, item_id: int):
        self.form_errors = []
        self.notice = ""
        self.editor_mode = "edit"
        self.draft = await self._read_record(kind, item_id)
        self.editor_open = True

    @rx.event
    def start_create(self, kind: str):
        draft = dict(EMPTY_DRAFT)
        draft["kind"] = kind
        draft["kind_label"] = KIND_LABELS.get(kind, "Contenu")
        draft["version_label"] = self.current_version["version_label"]
        if not VERSION_PATTERN.fullmatch(draft["version_label"]):
            draft["version_label"] = GUIDE_VERSION
        if self.filter_category != "TOUS":
            draft["category_key"] = self.filter_category
        elif self.categories:
            draft["category_key"] = self.categories[0]["key"]
        self.draft = draft
        self.editor_mode = "create"
        self.form_errors = []
        self.notice = ""
        self.editor_open = True

    @rx.event
    def close_editor(self):
        self.editor_open = False
        self.form_errors = []

    @rx.event
    async def open_preview(self, kind: str, item_id: int):
        self.preview = await self._read_record(kind, item_id)
        self.preview_open = True

    # ------------------------------------------------------------------
    # Écritures : contenus
    # ------------------------------------------------------------------

    async def _log_change(
        self,
        asession,
        kind: str,
        ref: str,
        change_kind: str,
        summary: str,
    ) -> None:
        version_id = self.current_version["id"]
        if version_id <= 0:
            return
        position = int(
            (
                await asession.execute(
                    text(
                        """
                        SELECT COALESCE(MAX(position), 0) + 1
                        FROM guide_version_entry WHERE version_id = :vid
                        """
                    ),
                    {"vid": version_id},
                )
            ).scalar()
            or 1
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
            {
                "version_id": version_id,
                "entity_type": ENTITY_TYPES.get(kind, "ARTICLE"),
                "entity_ref": ref,
                "change_kind": change_kind,
                "summary": summary,
                "author": self.draft.get("author") or GUIDE_AUTHOR,
                "position": position,
            },
        )

    @rx.event
    async def save_content(self, form_data: dict[str, Any]):
        """Valide puis enregistre le contenu (création ou mise à jour)."""
        kind = self.draft["kind"]
        data = dict(self.draft)
        for key, value in form_data.items():
            data[key] = str(value)
        for flag in ("is_featured", "is_frequent", "is_blocking"):
            data[flag] = "1" if _flag(form_data.get(flag, "")) else "0"
        if kind == "rule":
            data["code"] = data.get("code", "").strip().upper()
        if kind == "term":
            data["term"] = data.get("term", "").strip()

        errors = _validate(kind, data)
        self.draft = data
        if errors:
            self.form_errors = errors
            self.error = "Corrigez les points signalés avant d'enregistrer."
            return

        item_id = _as_int(data.get("id"), 0)
        is_create = self.editor_mode == "create" or item_id <= 0
        today = datetime.date.today().isoformat()

        async with rx.asession() as asession:
            category_id = (
                await asession.execute(
                    text("SELECT id FROM guide_category WHERE key = :key"),
                    {"key": data["category_key"]},
                )
            ).scalar()
            if category_id is None:
                self.form_errors = [
                    "La catégorie sélectionnée est introuvable."
                ]
                self.error = "Catégorie invalide."
                return
            category_id = int(category_id)

            # Unicité des identifiants métier
            if kind in ("article", "procedure", "term", "rule"):
                column = "code" if kind == "rule" else "slug"
                ref_value = data["code"] if kind == "rule" else data["slug"]
                clash = (
                    await asession.execute(
                        text(
                            f"""
                            SELECT COUNT(*) FROM {KIND_TABLES[kind]}
                            WHERE {column} = :ref AND id <> :id
                            """
                        ),
                        {"ref": ref_value, "id": item_id},
                    )
                ).scalar()
                if int(clash or 0) > 0:
                    self.form_errors = [
                        f"L'identifiant « {ref_value} » est déjà utilisé."
                    ]
                    self.error = "Identifiant en doublon."
                    return
            else:
                ref_value = data.get("ref", "") or str(item_id)

            params: dict[str, object] = {
                "category_id": category_id,
                "status": data["status"],
                "version_label": data["version_label"].strip(),
                "module_route": data.get("module_route", "").strip(),
                "id": item_id,
            }

            if kind == "article":
                params.update(
                    {
                        "slug": data["slug"].strip(),
                        "title": data["title"].strip(),
                        "subtitle": data.get("subtitle", "").strip(),
                        "summary": data.get("summary", "").strip(),
                        "body_farmer": data["body_farmer"].strip(),
                        "body_pro": data["body_pro"].strip(),
                        "audience": data["audience"],
                        "difficulty": data["difficulty"],
                        "reading_minutes": _as_int(data["reading_minutes"], 3),
                        "keywords": data.get("keywords", "").strip(),
                        "author": data.get("author", "").strip()
                        or GUIDE_AUTHOR,
                        "is_featured": 1 if data["is_featured"] == "1" else 0,
                        "published_on": today
                        if data["status"] == "PUBLIE"
                        else None,
                        "reviewed_on": today,
                    }
                )
                if is_create:
                    params["position"] = 1 + int(
                        (
                            await asession.execute(
                                text(
                                    "SELECT COALESCE(MAX(position), 0) FROM guide_article"
                                )
                            )
                        ).scalar()
                        or 0
                    )
                    await asession.execute(
                        text(
                            """
                            INSERT INTO guide_article (
                                category_id, slug, title, subtitle, summary,
                                body_farmer, body_pro, audience, status,
                                difficulty, reading_minutes, keywords, tags,
                                author, version_label, module_route,
                                published_on, reviewed_on, is_featured, position
                            ) VALUES (
                                :category_id, :slug, :title, :subtitle, :summary,
                                :body_farmer, :body_pro, :audience, :status,
                                :difficulty, :reading_minutes, :keywords, '',
                                :author, :version_label, :module_route,
                                :published_on, :reviewed_on, :is_featured, :position
                            )
                            """
                        ),
                        params,
                    )
                else:
                    await asession.execute(
                        text(
                            """
                            UPDATE guide_article SET
                                category_id = :category_id, slug = :slug,
                                title = :title, subtitle = :subtitle,
                                summary = :summary, body_farmer = :body_farmer,
                                body_pro = :body_pro, audience = :audience,
                                status = :status, difficulty = :difficulty,
                                reading_minutes = :reading_minutes,
                                keywords = :keywords, author = :author,
                                version_label = :version_label,
                                module_route = :module_route,
                                published_on = COALESCE(:published_on, published_on),
                                reviewed_on = :reviewed_on,
                                is_featured = :is_featured
                            WHERE id = :id
                            """
                        ),
                        params,
                    )
            elif kind == "procedure":
                params.update(
                    {
                        "slug": data["slug"].strip(),
                        "title": data["title"].strip(),
                        "objective": data["objective"].strip(),
                        "context": data.get("context", "").strip(),
                        "expected_result": data.get(
                            "expected_result", ""
                        ).strip(),
                        "prerequisites": data.get("prerequisites", "").strip(),
                        "estimated_minutes": _as_int(
                            data["estimated_minutes"], 5
                        ),
                        "difficulty": data["difficulty"],
                        "audience": data["audience"],
                    }
                )
                if is_create:
                    params["position"] = 1 + int(
                        (
                            await asession.execute(
                                text(
                                    "SELECT COALESCE(MAX(position), 0) FROM guide_procedure"
                                )
                            )
                        ).scalar()
                        or 0
                    )
                    await asession.execute(
                        text(
                            """
                            INSERT INTO guide_procedure (
                                category_id, slug, title, objective, context,
                                expected_result, prerequisites, module_route,
                                estimated_minutes, difficulty, audience, status,
                                version_label, position
                            ) VALUES (
                                :category_id, :slug, :title, :objective, :context,
                                :expected_result, :prerequisites, :module_route,
                                :estimated_minutes, :difficulty, :audience, :status,
                                :version_label, :position
                            )
                            """
                        ),
                        params,
                    )
                else:
                    await asession.execute(
                        text(
                            """
                            UPDATE guide_procedure SET
                                category_id = :category_id, slug = :slug,
                                title = :title, objective = :objective,
                                context = :context,
                                expected_result = :expected_result,
                                prerequisites = :prerequisites,
                                module_route = :module_route,
                                estimated_minutes = :estimated_minutes,
                                difficulty = :difficulty, audience = :audience,
                                status = :status, version_label = :version_label
                            WHERE id = :id
                            """
                        ),
                        params,
                    )
            elif kind == "term":
                params.update(
                    {
                        "slug": data["slug"].strip(),
                        "term": data["term"].strip(),
                        "acronym": data.get("acronym", "").strip(),
                        "definition_farmer": data["definition_farmer"].strip(),
                        "definition_pro": data["definition_pro"].strip(),
                        "unit": data.get("unit", "").strip(),
                        "formula": data.get("formula", "").strip(),
                        "example": data.get("example", "").strip(),
                        "synonyms": data.get("synonyms", "").strip(),
                        "related_terms": data.get("related_terms", "").strip(),
                    }
                )
                if is_create:
                    await asession.execute(
                        text(
                            """
                            INSERT INTO guide_term (
                                category_id, slug, term, acronym,
                                definition_farmer, definition_pro, unit,
                                formula, example, synonyms, related_terms,
                                module_route, status, version_label
                            ) VALUES (
                                :category_id, :slug, :term, :acronym,
                                :definition_farmer, :definition_pro, :unit,
                                :formula, :example, :synonyms, :related_terms,
                                :module_route, :status, :version_label
                            )
                            """
                        ),
                        params,
                    )
                else:
                    await asession.execute(
                        text(
                            """
                            UPDATE guide_term SET
                                category_id = :category_id, slug = :slug,
                                term = :term, acronym = :acronym,
                                definition_farmer = :definition_farmer,
                                definition_pro = :definition_pro, unit = :unit,
                                formula = :formula, example = :example,
                                synonyms = :synonyms,
                                related_terms = :related_terms,
                                module_route = :module_route, status = :status,
                                version_label = :version_label
                            WHERE id = :id
                            """
                        ),
                        params,
                    )
            elif kind == "faq":
                params.update(
                    {
                        "question": data["question"].strip(),
                        "answer_farmer": data["answer_farmer"].strip(),
                        "answer_pro": data["answer_pro"].strip(),
                        "audience": data["audience"],
                        "keywords": data.get("keywords", "").strip(),
                        "is_frequent": 1 if data["is_frequent"] == "1" else 0,
                    }
                )
                if is_create:
                    params["position"] = 1 + int(
                        (
                            await asession.execute(
                                text(
                                    "SELECT COALESCE(MAX(position), 0) FROM guide_faq"
                                )
                            )
                        ).scalar()
                        or 0
                    )
                    await asession.execute(
                        text(
                            """
                            INSERT INTO guide_faq (
                                category_id, question, answer_farmer, answer_pro,
                                audience, status, keywords, module_route,
                                is_frequent, position, version_label
                            ) VALUES (
                                :category_id, :question, :answer_farmer, :answer_pro,
                                :audience, :status, :keywords, :module_route,
                                :is_frequent, :position, :version_label
                            )
                            """
                        ),
                        params,
                    )
                else:
                    await asession.execute(
                        text(
                            """
                            UPDATE guide_faq SET
                                category_id = :category_id, question = :question,
                                answer_farmer = :answer_farmer,
                                answer_pro = :answer_pro, audience = :audience,
                                status = :status, keywords = :keywords,
                                module_route = :module_route,
                                is_frequent = :is_frequent,
                                version_label = :version_label
                            WHERE id = :id
                            """
                        ),
                        params,
                    )
            else:  # rule
                params.update(
                    {
                        "code": data["code"].strip().upper(),
                        "kind": data["rule_kind"],
                        "severity": data["severity"],
                        "title": data["title"].strip(),
                        "statement": data["statement"].strip(),
                        "rationale": data["rationale"].strip(),
                        "consequence": data.get("consequence", "").strip(),
                        "remediation": data.get("remediation", "").strip(),
                        "field_reference": data.get(
                            "field_reference", ""
                        ).strip(),
                        "is_blocking": 1 if data["is_blocking"] == "1" else 0,
                    }
                )
                if is_create:
                    params["position"] = 1 + int(
                        (
                            await asession.execute(
                                text(
                                    "SELECT COALESCE(MAX(position), 0) FROM guide_rule"
                                )
                            )
                        ).scalar()
                        or 0
                    )
                    await asession.execute(
                        text(
                            """
                            INSERT INTO guide_rule (
                                category_id, code, kind, severity, title,
                                statement, rationale, consequence, remediation,
                                module_route, field_reference, is_blocking,
                                status, version_label, position
                            ) VALUES (
                                :category_id, :code, :kind, :severity, :title,
                                :statement, :rationale, :consequence, :remediation,
                                :module_route, :field_reference, :is_blocking,
                                :status, :version_label, :position
                            )
                            """
                        ),
                        params,
                    )
                else:
                    await asession.execute(
                        text(
                            """
                            UPDATE guide_rule SET
                                category_id = :category_id, code = :code,
                                kind = :kind, severity = :severity,
                                title = :title, statement = :statement,
                                rationale = :rationale,
                                consequence = :consequence,
                                remediation = :remediation,
                                module_route = :module_route,
                                field_reference = :field_reference,
                                is_blocking = :is_blocking, status = :status,
                                version_label = :version_label
                            WHERE id = :id
                            """
                        ),
                        params,
                    )

            label = data.get("title") or data.get("question") or ref_value
            await self._log_change(
                asession,
                kind,
                ref_value,
                "AJOUT" if is_create else "MISE_A_JOUR",
                f"{KIND_LABELS.get(kind, 'Contenu')} « {label} » "
                f"({STATUS_LABELS.get(data['status'], data['status'])}).",
            )
            await asession.commit()

        self.form_errors = []
        self.error = ""
        self.editor_open = False
        self.notice = (
            f"{KIND_LABELS.get(kind, 'Contenu')} enregistré en "
            f"{STATUS_LABELS.get(data['status'], data['status']).lower()}."
        )
        self.content_kind = kind
        await self._load_reference()
        await self._load_versions()
        await self._load_changelog()
        await self._load_items()
        yield rx.toast(self.notice, duration=4000, close_button=True)
        yield GuideState.load_guide

    async def _apply_status(self, kind: str, item_id: int, status: str) -> str:
        """Applique un statut éditorial et journalise le changement."""
        record = await self._read_record(kind, item_id)
        self.draft = record
        async with rx.asession() as asession:
            if kind == "article" and status == "PUBLIE":
                await asession.execute(
                    text(
                        """
                        UPDATE guide_article
                        SET status = :status,
                            published_on = COALESCE(published_on, :today),
                            reviewed_on = :today
                        WHERE id = :id
                        """
                    ),
                    {
                        "status": status,
                        "today": datetime.date.today().isoformat(),
                        "id": item_id,
                    },
                )
            else:
                await asession.execute(
                    text(
                        f"UPDATE {KIND_TABLES[kind]} SET status = :status WHERE id = :id"
                    ),
                    {"status": status, "id": item_id},
                )
            await self._log_change(
                asession,
                kind,
                record["ref"],
                "SUPPRESSION" if status == "ARCHIVE" else "CORRECTION",
                f"Passage en {STATUS_LABELS[status].lower()} de "
                f"« {record['title'] or record['question'] or record['ref']} ».",
            )
            await asession.commit()
        self.notice = f"Contenu passé en {STATUS_LABELS[status].lower()}."
        await self._load_versions()
        await self._load_changelog()
        await self._load_items()
        return self.notice

    @rx.event
    async def set_content_status(self, kind: str, item_id: int, status: str):
        """Change le statut éditorial d'un contenu (dont l'archivage)."""
        if status not in STATUS_LABELS:
            self.error = "Statut inconnu."
            return
        notice = await self._apply_status(kind, item_id, status)
        yield rx.toast(notice, duration=3500, close_button=True)
        yield GuideState.load_guide

    @rx.event
    async def archive_content(self, kind: str, item_id: int):
        """Archivage non destructif d'un contenu (jamais de suppression)."""
        notice = await self._apply_status(kind, item_id, "ARCHIVE")
        yield rx.toast(notice, duration=3500, close_button=True)
        yield GuideState.load_guide

    # ------------------------------------------------------------------
    # Écritures : versions éditoriales
    # ------------------------------------------------------------------

    @rx.event
    async def create_version(self, form_data: dict[str, Any]):
        label = str(form_data.get("version_label", "")).strip()
        title = str(form_data.get("title", "")).strip()
        summary = str(form_data.get("summary", "")).strip()
        author = str(form_data.get("author", "")).strip() or GUIDE_AUTHOR
        errors: list[str] = []
        if not VERSION_PATTERN.fullmatch(label):
            errors.append("La version doit suivre le format numérique X.Y.Z.")
        if len(title) < 6:
            errors.append("Le titre de la version est trop court.")
        if len(summary) < 20:
            errors.append("Le résumé de publication doit être renseigné.")
        if errors:
            self.form_errors = errors
            return

        async with rx.asession() as asession:
            clash = (
                await asession.execute(
                    text(
                        "SELECT COUNT(*) FROM guide_version WHERE version_label = :v"
                    ),
                    {"v": label},
                )
            ).scalar()
            if int(clash or 0) > 0:
                self.form_errors = [f"La version {label} existe déjà."]
                return
            await asession.execute(
                text(
                    """
                    INSERT INTO guide_version (
                        version_label, title, summary, changelog, author,
                        status, published_on, is_current
                    ) VALUES (
                        :version_label, :title, :summary, '', :author,
                        'BROUILLON', NULL, 0
                    )
                    """
                ),
                {
                    "version_label": label,
                    "title": title,
                    "summary": summary,
                    "author": author,
                },
            )
            new_id = int(
                (
                    await asession.execute(
                        text(
                            "SELECT id FROM guide_version WHERE version_label = :v"
                        ),
                        {"v": label},
                    )
                ).scalar()
                or 0
            )
            await asession.execute(
                text(
                    """
                    INSERT INTO guide_version_entry (
                        version_id, entity_type, entity_ref, change_kind,
                        summary, author, position
                    ) VALUES (
                        :version_id, 'VERSION', :ref, 'AJOUT', :summary,
                        :author, 1
                    )
                    """
                ),
                {
                    "version_id": new_id,
                    "ref": label,
                    "summary": f"Ouverture de la version {label} en brouillon.",
                    "author": author,
                },
            )
            await asession.commit()

        self.form_errors = []
        self.version_form_open = False
        self.selected_version_id = new_id
        self.notice = f"Version {label} ouverte en brouillon."
        await self._load_versions()
        await self._load_changelog()
        yield rx.toast(self.notice, duration=4000, close_button=True)

    @rx.event
    async def publish_version(self, version_id: int):
        """Publie une version : elle devient la version courante consultable."""
        async with rx.asession() as asession:
            await asession.execute(
                text("UPDATE guide_version SET is_current = 0")
            )
            await asession.execute(
                text(
                    """
                    UPDATE guide_version SET
                        status = 'PUBLIE', is_current = 1,
                        published_on = COALESCE(published_on, :today)
                    WHERE id = :id
                    """
                ),
                {"today": datetime.date.today().isoformat(), "id": version_id},
            )
            await asession.commit()
        self.selected_version_id = version_id
        self.notice = "Version publiée et rendue consultable."
        await self._load_versions()
        await self._load_changelog()
        yield rx.toast(self.notice, duration=3500, close_button=True)

    @rx.event
    async def unpublish_version(self, version_id: int):
        """Dépublie la version courante (retour en relecture)."""
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE guide_version
                    SET status = 'RELECTURE', is_current = 0
                    WHERE id = :id
                    """
                ),
                {"id": version_id},
            )
            await asession.commit()
        self.notice = "Version dépubliée : elle repasse en relecture."
        await self._load_versions()
        await self._load_changelog()
        yield rx.toast(self.notice, duration=3500, close_button=True)

    @rx.event
    async def archive_version(self, version_id: int):
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE guide_version
                    SET status = 'ARCHIVE', is_current = 0
                    WHERE id = :id
                    """
                ),
                {"id": version_id},
            )
            await asession.commit()
        self.notice = "Version archivée."
        await self._load_versions()
        await self._load_changelog()
        yield rx.toast(self.notice, duration=3500, close_button=True)

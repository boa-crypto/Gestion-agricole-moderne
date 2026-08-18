"""État léger du guide contextuel embarqué.

Charge, en SQL brut via `rx.asession()`, les concepts clés, les règles
« Pourquoi ? » / « Attention », les erreurs fréquentes (FAQ), les procédures et
les articles pertinents pour l'écran courant, sans changer aucune route.
"""

from __future__ import annotations

from typing import TypedDict

import reflex as rx
from sqlalchemy import bindparam, text

from app.guide_hints import context_spec, topic_spec
from app.seed_guide import seed_guide_data

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

SEVERITY_TONES: dict[str, str] = {
    "INFO": "good",
    "ATTENTION": "warn",
    "CRITIQUE": "bad",
}


class HelpConcept(TypedDict):
    slug: str
    term: str
    acronym: str
    definition_farmer: str
    definition_pro: str
    unit: str


class HelpRule(TypedDict):
    code: str
    kind: str
    kind_label: str
    severity_label: str
    tone: str
    title: str
    statement: str
    rationale: str
    consequence: str
    remediation: str
    field_reference: str
    module_route: str
    is_blocking: bool


class HelpFaq(TypedDict):
    id: int
    question: str
    answer_farmer: str
    answer_pro: str
    is_frequent: bool


class HelpProcedure(TypedDict):
    slug: str
    title: str
    objective: str
    estimated_minutes: int
    step_count: int
    module_route: str


class HelpArticle(TypedDict):
    slug: str
    title: str
    subtitle: str
    category_name: str
    reading_minutes: int


def _keys_stmt(query: str):
    """Prépare une requête avec une liste de clés en paramètre expansible."""
    return text(query).bindparams(bindparam("keys", expanding=True))


def _codes_stmt(query: str):
    return text(query).bindparams(bindparam("codes", expanding=True))


class HelpState(rx.State):
    """Panneau d'aide embarquée, contextuel à l'écran et au formulaire actif."""

    is_open: bool = False
    is_loading: bool = False

    context_key: str = "cockpit"
    context_label: str = "Cockpit agronomique"
    context_tagline: str = ""
    context_icon: str = "life-buoy"
    context_route: str = "/"

    focus_topic: str = ""
    focus_label: str = ""
    focus_hint: str = ""
    focus_icon: str = "scale"

    concepts: list[HelpConcept] = []
    rules: list[HelpRule] = []
    focus_rules: list[HelpRule] = []
    faqs: list[HelpFaq] = []
    procedures: list[HelpProcedure] = []
    articles: list[HelpArticle] = []

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def has_focus(self) -> bool:
        return self.focus_topic != ""

    @rx.var
    def why_rules(self) -> list[HelpRule]:
        return [item for item in self.rules if item["kind"] == "POURQUOI"]

    @rx.var
    def attention_rules(self) -> list[HelpRule]:
        return [
            item
            for item in self.rules
            if item["kind"] in ("ATTENTION", "COHERENCE", "BONNE_PRATIQUE")
        ]

    @rx.var
    def frequent_faqs(self) -> list[HelpFaq]:
        return [item for item in self.faqs if item["is_frequent"]]

    @rx.var
    def content_count(self) -> int:
        return (
            len(self.concepts)
            + len(self.rules)
            + len(self.faqs)
            + len(self.procedures)
            + len(self.articles)
        )

    # ------------------------------------------------------------------
    # Lecture SQL brute
    # ------------------------------------------------------------------

    def _rule_row(self, row) -> HelpRule:
        kind = str(row[1])
        severity = str(row[2])
        return {
            "code": str(row[0]),
            "kind": kind,
            "kind_label": RULE_KIND_LABELS.get(kind, kind),
            "severity_label": SEVERITY_LABELS.get(severity, severity),
            "tone": SEVERITY_TONES.get(severity, "good"),
            "title": str(row[3]),
            "statement": str(row[4]),
            "rationale": str(row[5]),
            "consequence": str(row[6]),
            "remediation": str(row[7]),
            "field_reference": str(row[8]),
            "module_route": str(row[9]),
            "is_blocking": bool(row[10]),
        }

    async def _load_context(self, categories: list[str]) -> None:
        await seed_guide_data()
        params = {"keys": categories}
        async with rx.asession() as asession:
            term_rows = (
                await asession.execute(
                    _keys_stmt(
                        """
                        SELECT t.slug, t.term, COALESCE(t.acronym, ''),
                               COALESCE(t.definition_farmer, ''),
                               COALESCE(t.definition_pro, ''),
                               COALESCE(t.unit, '')
                        FROM guide_term t
                        JOIN guide_category c ON c.id = t.category_id
                        WHERE t.status = 'PUBLIE' AND c.key IN :keys
                        ORDER BY t.term
                        LIMIT 8
                        """
                    ),
                    params,
                )
            ).all()

            rule_rows = (
                await asession.execute(
                    _keys_stmt(
                        """
                        SELECT r.code, r.kind, r.severity, r.title,
                               COALESCE(r.statement, ''),
                               COALESCE(r.rationale, ''),
                               COALESCE(r.consequence, ''),
                               COALESCE(r.remediation, ''),
                               COALESCE(r.field_reference, ''),
                               COALESCE(r.module_route, ''), r.is_blocking
                        FROM guide_rule r
                        JOIN guide_category c ON c.id = r.category_id
                        WHERE r.status = 'PUBLIE' AND c.key IN :keys
                        ORDER BY r.kind, r.position, r.code
                        LIMIT 12
                        """
                    ),
                    params,
                )
            ).all()

            faq_rows = (
                await asession.execute(
                    _keys_stmt(
                        """
                        SELECT f.id, f.question, COALESCE(f.answer_farmer, ''),
                               COALESCE(f.answer_pro, ''), f.is_frequent
                        FROM guide_faq f
                        JOIN guide_category c ON c.id = f.category_id
                        WHERE f.status = 'PUBLIE' AND c.key IN :keys
                        ORDER BY f.is_frequent DESC, f.position, f.id
                        LIMIT 6
                        """
                    ),
                    params,
                )
            ).all()

            procedure_rows = (
                await asession.execute(
                    _keys_stmt(
                        """
                        SELECT p.slug, p.title, COALESCE(p.objective, ''),
                               COALESCE(p.estimated_minutes, 0),
                               COALESCE(p.module_route, '/'),
                               (SELECT COUNT(*) FROM guide_procedure_step s
                                  WHERE s.procedure_id = p.id)
                        FROM guide_procedure p
                        JOIN guide_category c ON c.id = p.category_id
                        WHERE p.status = 'PUBLIE' AND c.key IN :keys
                        ORDER BY p.position, p.title
                        LIMIT 6
                        """
                    ),
                    params,
                )
            ).all()

            article_rows = (
                await asession.execute(
                    _keys_stmt(
                        """
                        SELECT a.slug, a.title, COALESCE(a.subtitle, ''),
                               c.name, COALESCE(a.reading_minutes, 0)
                        FROM guide_article a
                        JOIN guide_category c ON c.id = a.category_id
                        WHERE a.status = 'PUBLIE' AND c.key IN :keys
                        ORDER BY a.is_featured DESC, a.position, a.title
                        LIMIT 6
                        """
                    ),
                    params,
                )
            ).all()

        self.concepts = [
            {
                "slug": str(row[0]),
                "term": str(row[1]),
                "acronym": str(row[2]),
                "definition_farmer": str(row[3]),
                "definition_pro": str(row[4]),
                "unit": str(row[5]),
            }
            for row in term_rows
        ]
        self.rules = [self._rule_row(row) for row in rule_rows]
        self.faqs = [
            {
                "id": int(row[0]),
                "question": str(row[1]),
                "answer_farmer": str(row[2]),
                "answer_pro": str(row[3]),
                "is_frequent": bool(row[4]),
            }
            for row in faq_rows
        ]
        self.procedures = [
            {
                "slug": str(row[0]),
                "title": str(row[1]),
                "objective": str(row[2]),
                "estimated_minutes": int(row[3] or 0),
                "module_route": str(row[4]),
                "step_count": int(row[5] or 0),
            }
            for row in procedure_rows
        ]
        self.articles = [
            {
                "slug": str(row[0]),
                "title": str(row[1]),
                "subtitle": str(row[2]),
                "category_name": str(row[3]),
                "reading_minutes": int(row[4] or 0),
            }
            for row in article_rows
        ]

    async def _load_focus_rules(self, codes: list[str]) -> None:
        if not codes:
            self.focus_rules = []
            return
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    _codes_stmt(
                        """
                        SELECT r.code, r.kind, r.severity, r.title,
                               COALESCE(r.statement, ''),
                               COALESCE(r.rationale, ''),
                               COALESCE(r.consequence, ''),
                               COALESCE(r.remediation, ''),
                               COALESCE(r.field_reference, ''),
                               COALESCE(r.module_route, ''), r.is_blocking
                        FROM guide_rule r
                        WHERE r.status = 'PUBLIE' AND r.code IN :codes
                        ORDER BY r.code
                        LIMIT 8
                        """
                    ),
                    {"codes": codes},
                )
            ).all()
        self.focus_rules = [self._rule_row(row) for row in rows]

    def _apply_context(self, key: str) -> list[str]:
        spec = context_spec(key)
        self.context_key = key
        self.context_label = spec["label"]
        self.context_tagline = spec["tagline"]
        self.context_icon = spec["icon"]
        self.context_route = spec["route"]
        return spec["categories"]

    # ------------------------------------------------------------------
    # Événements
    # ------------------------------------------------------------------

    @rx.event
    async def open_context(self, key: str):
        """Ouvre l'aide sur le contexte d'un écran (sans sujet de règle)."""
        categories = self._apply_context(key)
        self.focus_topic = ""
        self.focus_label = ""
        self.focus_hint = ""
        self.focus_icon = "scale"
        self.focus_rules = []
        self.is_open = True
        self.is_loading = True
        yield
        await self._load_context(categories)
        self.is_loading = False

    @rx.event
    async def open_topic(self, key: str, topic: str):
        """Ouvre l'aide focalisée sur une règle de cohérence précise."""
        categories = self._apply_context(key)
        spec = topic_spec(topic)
        self.focus_topic = topic
        self.focus_label = spec["label"]
        self.focus_hint = spec["hint"]
        self.focus_icon = spec["icon"]
        self.is_open = True
        self.is_loading = True
        yield
        await self._load_focus_rules(spec["codes"])
        await self._load_context(categories)
        self.is_loading = False

    @rx.event
    def toggle_context(self, key: str):
        """Bascule le panneau pour un écran donné."""
        if self.is_open and self.context_key == key and self.focus_topic == "":
            self.is_open = False
            return None
        return HelpState.open_context(key)

    @rx.event
    def clear_focus(self):
        self.focus_topic = ""
        self.focus_label = ""
        self.focus_hint = ""
        self.focus_rules = []

    @rx.event
    def close_panel(self):
        self.is_open = False

    @rx.event
    def explain(self, key: str, topic: str):
        """Notifie l'explication pédagogique puis ouvre l'aide sur la règle."""
        spec = topic_spec(topic)
        yield rx.toast(
            f"{spec['label']} — {spec['hint']}",
            duration=8000,
            close_button=True,
        )
        yield HelpState.open_topic(key, topic)

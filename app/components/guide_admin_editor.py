"""Fiche d'édition du pupitre éditorial (formulaires complets + validation)."""

import reflex as rx

from app.components.guide_admin_fields import (
    area_field,
    category_field,
    check_field,
    number_field,
    select_field,
    text_field,
)
from app.states.guide_admin_state import GuideAdminState

_DRAFT = GuideAdminState.draft


def _errors_block() -> rx.Component:
    return rx.cond(
        GuideAdminState.has_errors,
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "octagon-alert",
                    class_name="h-4 w-4 stroke-red-300 shrink-0",
                ),
                rx.el.span(
                    "Contrôles de cohérence éditoriale",
                    class_name="text-[11px] font-semibold uppercase tracking-[0.18em] text-red-200",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.ul(
                rx.foreach(
                    GuideAdminState.form_errors,
                    lambda message: rx.el.li(
                        message,
                        class_name="text-[12px] font-medium text-red-100/90 leading-relaxed list-disc ml-4",
                    ),
                ),
                class_name="flex flex-col gap-1 w-full mt-2",
            ),
            class_name="w-full rounded-2xl border border-red-400/30 bg-red-500/[0.08] p-3.5",
        ),
        rx.fragment(),
    )


def _meta_block() -> rx.Component:
    return rx.el.div(
        category_field(_DRAFT["category_key"]),
        select_field(
            "Statut éditorial",
            "status",
            _DRAFT["status"],
            GuideAdminState.status_options,
        ),
        text_field(
            "Version éditoriale",
            "version_label",
            _DRAFT["version_label"],
            placeholder="1.1.0",
            hint="Format numérique X.Y.Z",
            required=True,
        ),
        text_field(
            "Écran de l'application",
            "module_route",
            _DRAFT["module_route"],
            placeholder="/parcelles",
            hint="Lien direct proposé au lecteur",
        ),
        class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 w-full",
    )


def _article_form() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            text_field(
                "Identifiant (slug)",
                "slug",
                _DRAFT["slug"],
                placeholder="creer-une-parcelle",
                hint="Minuscules, chiffres et tirets",
                required=True,
            ),
            text_field(
                "Titre",
                "title",
                _DRAFT["title"],
                placeholder="Créer et décrire une parcelle",
                required=True,
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-3 w-full",
        ),
        text_field(
            "Sous-titre",
            "subtitle",
            _DRAFT["subtitle"],
            placeholder="Code, surface, sol, irrigation",
        ),
        area_field(
            "Résumé de tête",
            "summary",
            _DRAFT["summary"],
            placeholder="Une phrase qui donne l'intention de la fiche.",
            rows="2",
        ),
        rx.el.div(
            area_field(
                "Lecture agricole",
                "body_farmer",
                _DRAFT["body_farmer"],
                placeholder="Vocabulaire de terrain, phrases courtes…",
                rows="9",
                hint="Séparez les paragraphes par une ligne vide",
            ),
            area_field(
                "Lecture AgriPro",
                "body_pro",
                _DRAFT["body_pro"],
                placeholder="Vocabulaire technique, champs et indicateurs…",
                rows="9",
                hint="Séparez les paragraphes par une ligne vide",
            ),
            class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 w-full",
        ),
        rx.el.div(
            select_field(
                "Niveau de lecture",
                "audience",
                _DRAFT["audience"],
                GuideAdminState.audience_options,
            ),
            select_field(
                "Difficulté",
                "difficulty",
                _DRAFT["difficulty"],
                GuideAdminState.difficulty_options,
            ),
            number_field(
                "Durée de lecture (min)",
                "reading_minutes",
                _DRAFT["reading_minutes"],
            ),
            text_field("Auteur", "author", _DRAFT["author"]),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 w-full",
        ),
        text_field(
            "Mots-clés",
            "keywords",
            _DRAFT["keywords"],
            placeholder="parcelle, surface, sol",
            hint="Séparés par des virgules, utilisés par la recherche globale",
        ),
        check_field(
            "Fiche clé du guide",
            "is_featured",
            _DRAFT["is_featured"],
            "Mise en avant dans le sommaire vivant et la recherche.",
        ),
        class_name="flex flex-col gap-3 w-full",
    )


def _procedure_form() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            text_field(
                "Identifiant (slug)",
                "slug",
                _DRAFT["slug"],
                placeholder="proc-creer-parcelle",
                required=True,
            ),
            text_field(
                "Titre",
                "title",
                _DRAFT["title"],
                placeholder="Créer une parcelle de A à Z",
                required=True,
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-3 w-full",
        ),
        area_field(
            "Objectif",
            "objective",
            _DRAFT["objective"],
            placeholder="Ce que l'utilisateur obtient à la fin.",
            rows="3",
        ),
        rx.el.div(
            area_field(
                "Contexte d'usage",
                "context",
                _DRAFT["context"],
                rows="3",
            ),
            area_field(
                "Résultat attendu",
                "expected_result",
                _DRAFT["expected_result"],
                rows="3",
            ),
            class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 w-full",
        ),
        area_field(
            "Prérequis",
            "prerequisites",
            _DRAFT["prerequisites"],
            rows="2",
        ),
        rx.el.div(
            select_field(
                "Niveau de lecture",
                "audience",
                _DRAFT["audience"],
                GuideAdminState.audience_options,
            ),
            select_field(
                "Difficulté",
                "difficulty",
                _DRAFT["difficulty"],
                GuideAdminState.difficulty_options,
            ),
            number_field(
                "Durée estimée (min)",
                "estimated_minutes",
                _DRAFT["estimated_minutes"],
            ),
            class_name="grid grid-cols-1 md:grid-cols-3 gap-3 w-full",
        ),
        class_name="flex flex-col gap-3 w-full",
    )


def _term_form() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            text_field(
                "Identifiant (slug)",
                "slug",
                _DRAFT["slug"],
                placeholder="reserve-utile",
                required=True,
            ),
            text_field(
                "Entrée",
                "term",
                _DRAFT["term"],
                placeholder="Réserve utile",
                required=True,
            ),
            text_field(
                "Sigle",
                "acronym",
                _DRAFT["acronym"],
                placeholder="RU",
            ),
            class_name="grid grid-cols-1 md:grid-cols-3 gap-3 w-full",
        ),
        rx.el.div(
            area_field(
                "Définition agricole",
                "definition_farmer",
                _DRAFT["definition_farmer"],
                rows="4",
            ),
            area_field(
                "Définition AgriPro",
                "definition_pro",
                _DRAFT["definition_pro"],
                rows="4",
            ),
            class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 w-full",
        ),
        rx.el.div(
            text_field("Unité", "unit", _DRAFT["unit"], placeholder="mm"),
            text_field(
                "Formule",
                "formula",
                _DRAFT["formula"],
                placeholder="RU = (θcc − θpf) × profondeur",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-3 w-full",
        ),
        area_field(
            "Exemple de terrain",
            "example",
            _DRAFT["example"],
            rows="2",
        ),
        rx.el.div(
            text_field("Synonymes", "synonyms", _DRAFT["synonyms"]),
            text_field("Termes liés", "related_terms", _DRAFT["related_terms"]),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-3 w-full",
        ),
        class_name="flex flex-col gap-3 w-full",
    )


def _faq_form() -> rx.Component:
    return rx.el.div(
        text_field(
            "Question posée",
            "question",
            _DRAFT["question"],
            placeholder="Puis-je traiter avec du vent ?",
            hint="Doit se terminer par un point d'interrogation",
            required=True,
        ),
        rx.el.div(
            area_field(
                "Réponse agricole",
                "answer_farmer",
                _DRAFT["answer_farmer"],
                rows="5",
            ),
            area_field(
                "Réponse AgriPro",
                "answer_pro",
                _DRAFT["answer_pro"],
                rows="5",
            ),
            class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 w-full",
        ),
        rx.el.div(
            select_field(
                "Niveau de lecture",
                "audience",
                _DRAFT["audience"],
                GuideAdminState.audience_options,
            ),
            text_field("Mots-clés", "keywords", _DRAFT["keywords"]),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-3 w-full",
        ),
        check_field(
            "Question fréquente",
            "is_frequent",
            _DRAFT["is_frequent"],
            "Remontée en tête de la FAQ intelligente et de l'aide embarquée.",
        ),
        class_name="flex flex-col gap-3 w-full",
    )


def _rule_form() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            text_field(
                "Code de règle",
                "code",
                _DRAFT["code"],
                placeholder="COH-PARC-004",
                hint="Majuscules et tirets",
                required=True,
            ),
            select_field(
                "Nature",
                "rule_kind",
                _DRAFT["rule_kind"],
                GuideAdminState.rule_kind_options,
            ),
            select_field(
                "Sévérité",
                "severity",
                _DRAFT["severity"],
                GuideAdminState.severity_options,
            ),
            class_name="grid grid-cols-1 md:grid-cols-3 gap-3 w-full",
        ),
        text_field(
            "Titre de la règle",
            "title",
            _DRAFT["title"],
            placeholder="La surface implantée ne dépasse pas la parcelle",
            required=True,
        ),
        area_field(
            "Énoncé",
            "statement",
            _DRAFT["statement"],
            rows="3",
        ),
        rx.el.div(
            area_field(
                "Pourquoi ? (justification)",
                "rationale",
                _DRAFT["rationale"],
                rows="4",
            ),
            area_field(
                "Conséquence si non respectée",
                "consequence",
                _DRAFT["consequence"],
                rows="4",
            ),
            class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 w-full",
        ),
        area_field(
            "Correction proposée",
            "remediation",
            _DRAFT["remediation"],
            rows="3",
        ),
        text_field(
            "Champ concerné",
            "field_reference",
            _DRAFT["field_reference"],
            placeholder="crop.area_ha",
        ),
        check_field(
            "Règle bloquante",
            "is_blocking",
            _DRAFT["is_blocking"],
            "La saisie est refusée tant que la règle n'est pas respectée.",
        ),
        class_name="flex flex-col gap-3 w-full",
    )


def guide_admin_editor() -> rx.Component:
    """Fiche de publication : formulaire complet du contenu en cours d'édition."""
    return rx.cond(
        GuideAdminState.editor_open,
        rx.fragment(
            rx.el.div(
                on_click=GuideAdminState.close_editor,
                class_name="fixed inset-0 z-[65] bg-[#020a07]/70 backdrop-blur-[2px]",
            ),
            rx.el.aside(
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.icon(
                                "square-pen",
                                class_name="h-4 w-4 stroke-[#04140d]",
                            ),
                            class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-lime-300",
                        ),
                        rx.el.div(
                            rx.el.span(
                                "Fiche de publication",
                                class_name="text-[9px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                            ),
                            rx.el.h3(
                                GuideAdminState.editor_title,
                                class_name="font-['Instrument_Serif'] text-2xl text-emerald-50 mt-0.5",
                            ),
                            class_name="min-w-0 flex-1",
                        ),
                        rx.el.button(
                            rx.icon("x", class_name="h-4 w-4"),
                            type="button",
                            on_click=GuideAdminState.close_editor,
                            aria_label="Fermer la fiche d'édition",
                            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-emerald-100/60 hover:text-emerald-50 hover:border-lime-300/30 transition-colors",
                        ),
                        class_name="flex items-start gap-3 w-full",
                    ),
                    rx.el.div(
                        rx.el.span(
                            f"Référence : {GuideAdminState.draft['ref']}",
                            class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-mono text-emerald-100/55 w-fit",
                        ),
                        rx.el.span(
                            f"Version courante : {GuideAdminState.current_version['version_label']}",
                            class_name="rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1 text-[10px] font-bold text-lime-200 w-fit",
                        ),
                        rx.el.span(
                            f"Publié le {GuideAdminState.draft['published_label']}",
                            class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-semibold text-emerald-100/55 w-fit",
                        ),
                        class_name="flex flex-wrap items-center gap-2 w-full mt-3",
                    ),
                    class_name="w-full border-b border-white/10 pb-4",
                ),
                rx.el.form(
                    _errors_block(),
                    _meta_block(),
                    rx.match(
                        GuideAdminState.draft["kind"],
                        ("article", _article_form()),
                        ("procedure", _procedure_form()),
                        ("term", _term_form()),
                        ("faq", _faq_form()),
                        ("rule", _rule_form()),
                        _article_form(),
                    ),
                    rx.el.div(
                        rx.el.button(
                            rx.icon("x", class_name="h-3.5 w-3.5"),
                            rx.el.span("Annuler"),
                            type="button",
                            on_click=GuideAdminState.close_editor,
                            class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-emerald-100/65 hover:text-emerald-50 hover:border-lime-300/30 transition-colors w-fit",
                        ),
                        rx.el.button(
                            rx.icon(
                                "save", class_name="h-4 w-4 stroke-[#04140d]"
                            ),
                            rx.el.span(
                                "Enregistrer la fiche",
                                class_name="text-[#04140d]",
                            ),
                            type="submit",
                            class_name="flex items-center gap-2 rounded-full bg-lime-300 px-5 py-2 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                        ),
                        class_name="flex flex-wrap items-center justify-end gap-2 w-full border-t border-white/10 pt-4",
                    ),
                    on_submit=GuideAdminState.save_content,
                    class_name="flex flex-col gap-4 w-full mt-5",
                ),
                aria_label="Fiche d'édition du guide",
                class_name="fixed right-0 top-0 z-[70] h-screen w-full lg:w-[52rem] overflow-y-auto border-l border-lime-300/20 bg-[#03110b]/97 px-5 sm:px-7 py-6 pb-28 backdrop-blur-2xl",
            ),
        ),
        rx.fragment(),
    )

"""Composants réutilisables du guide contextuel embarqué.

- `help_button` / `help_icon_button` : déclencheurs discrets pour les headers de
  pages, les modales et les formulaires.
- `guide_error` : message d'erreur enrichi d'une explication pédagogique et d'un
  accès direct à la règle de cohérence concernée.
- `guide_help_panel` : panneau latéral d'aide embarquée (concepts, « Pourquoi ? »,
  « Attention », erreurs fréquentes, procédures, articles, lien vers /guide).
"""

import reflex as rx

from app.components.design import skeleton_page

from app.guide_hints import topic_hint, topic_icon, topic_label
from app.states.help_state import (
    HelpArticle,
    HelpConcept,
    HelpFaq,
    HelpProcedure,
    HelpRule,
    HelpState,
)


# ---------------------------------------------------------------------------
# Déclencheurs
# ---------------------------------------------------------------------------


def help_button(context_key: str, label: str = "Guide") -> rx.Component:
    """Bouton discret « Guide » pour les headers de pages et de modales."""
    return rx.el.button(
        rx.icon("life-buoy", class_name="h-3.5 w-3.5 stroke-[rgb(var(--ap-accent-rgb))]"),
        rx.el.span(label, class_name="text-xs font-semibold"),
        type="button",
        title="Aide contextuelle du Guide Agricole",
        aria_label="Ouvrir l'aide contextuelle",
        on_click=HelpState.toggle_context(context_key),
        class_name="flex items-center gap-2 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb))]/[0.07] px-3 py-1.5 text-[rgb(var(--ap-accent-pale-rgb)/0.85)] hover:border-[rgb(var(--ap-accent-rgb)/0.50)] hover:bg-[rgb(var(--ap-accent-rgb))]/[0.14] transition-colors w-fit",
    )


def help_icon_button(context_key: str) -> rx.Component:
    """Icône « ? » compacte, pour les en-têtes de blocs et de formulaires."""
    return rx.el.button(
        rx.icon("circle-help", class_name="h-3.5 w-3.5 stroke-[rgb(var(--ap-accent-rgb))]"),
        type="button",
        title="Aide contextuelle",
        aria_label="Ouvrir l'aide contextuelle",
        on_click=HelpState.toggle_context(context_key),
        class_name="flex h-7 w-7 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.20)] bg-[rgb(var(--ap-accent-rgb))]/[0.06] hover:border-[rgb(var(--ap-accent-rgb)/0.50)] hover:bg-[rgb(var(--ap-accent-rgb))]/[0.14] transition-colors",
    )


def help_topic_button(
    context_key: str, topic: str, label: str = "Pourquoi cette règle ?"
) -> rx.Component:
    """Accès direct à la règle de cohérence concernée par une erreur."""
    return rx.el.button(
        rx.icon(topic_icon(topic), class_name="h-3.5 w-3.5 stroke-[rgb(var(--ap-flame-soft-rgb))]"),
        rx.el.span(label, class_name="text-[11px] font-semibold"),
        type="button",
        on_click=HelpState.open_topic(context_key, topic),
        class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb))]/[0.08] px-3 py-1 text-[rgb(var(--ap-warm-100-rgb)/0.90)] hover:border-[rgb(var(--ap-flame-soft-rgb)/0.60)] hover:bg-[rgb(var(--ap-flame-soft-rgb))]/[0.16] transition-colors w-fit",
    )


def guide_error(message: rx.Var, context_key: str, topic: str) -> rx.Component:
    """Message d'erreur de formulaire enrichi d'une lecture pédagogique."""
    return rx.cond(
        message != "",
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "octagon-alert",
                    class_name="h-4 w-4 stroke-[rgb(var(--ap-danger-soft-rgb))] shrink-0 mt-0.5",
                ),
                rx.el.p(
                    message,
                    class_name="text-xs font-semibold text-[rgb(var(--ap-warm-150-rgb))] leading-relaxed",
                ),
                class_name="flex items-start gap-2 w-full",
            ),
            rx.el.div(
                rx.icon(
                    topic_icon(topic),
                    class_name="h-3.5 w-3.5 stroke-[rgb(var(--ap-accent-rgb))] shrink-0 mt-0.5",
                ),
                rx.el.div(
                    rx.el.span(
                        topic_label(topic),
                        class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                    ),
                    rx.el.p(
                        topic_hint(topic),
                        class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.90)] leading-relaxed mt-1",
                    ),
                    class_name="min-w-0 flex-1",
                ),
                class_name="flex items-start gap-2 w-full rounded-none border border-[rgb(var(--ap-accent-rgb)/0.20)] bg-[rgb(var(--ap-accent-rgb))]/[0.05] px-3 py-2.5 mt-3",
            ),
            rx.el.div(
                help_topic_button(context_key, topic),
                rx.el.a(
                    rx.el.span("Voir le guide", class_name="text-[11px]"),
                    rx.icon("arrow-up-right", class_name="h-3 w-3"),
                    href="/guide",
                    class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] hover:text-[rgb(var(--ap-paper-rgb))] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 mt-3",
            ),
            class_name="w-full rounded-none border border-[rgb(var(--ap-danger-rgb)/0.30)] bg-[rgb(var(--ap-flame-strong-rgb))]/[0.08] p-3.5 mt-5",
        ),
        rx.fragment(),
    )


# ---------------------------------------------------------------------------
# Panneau d'aide embarquée
# ---------------------------------------------------------------------------


def _section(
    title: str, icon: str, count: rx.Var | int, body: rx.Component
) -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 stroke-[rgb(var(--ap-accent-rgb)/0.80)]"),
            rx.el.span(
                title,
                class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            rx.el.span(
                count,
                class_name="rounded-none bg-[rgb(var(--ap-accent-rgb)/0.15)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit ml-auto",
            ),
            class_name="flex items-center gap-2 w-full",
        ),
        body,
        class_name="w-full",
    )


def _concept_card(item: HelpConcept, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                item["term"],
                class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
            ),
            rx.cond(
                item["acronym"] != "",
                rx.el.span(
                    item["acronym"],
                    class_name="rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-1.5 py-0.5 text-[9px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
                ),
                rx.fragment(),
            ),
            rx.cond(
                item["unit"] != "",
                rx.el.span(
                    item["unit"],
                    class_name="text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] ml-auto shrink-0",
                ),
                rx.fragment(),
            ),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.p(
            item["definition_farmer"],
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] leading-relaxed mt-1.5",
        ),
        rx.cond(
            item["definition_pro"] != "",
            rx.el.p(
                item["definition_pro"],
                class_name="text-[11px] font-medium text-[rgb(var(--ap-warm-100-rgb)/0.55)] leading-relaxed mt-1.5",
            ),
            rx.fragment(),
        ),
        key=key,
        class_name="w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] p-3",
    )


def _rule_card(item: HelpRule, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name=rx.match(
                item["tone"],
                ("bad", "h-1 w-full rounded-none bg-[rgb(var(--ap-danger-rgb)/0.80)]"),
                ("warn", "h-1 w-full rounded-none bg-[rgb(var(--ap-flame-soft-rgb)/0.80)]"),
                "h-1 w-full rounded-none bg-[rgb(var(--ap-accent-rgb)/0.80)]",
            )
        ),
        rx.el.div(
            rx.el.span(
                item["kind_label"],
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[9px] font-bold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit",
            ),
            rx.cond(
                item["is_blocking"],
                rx.el.span(
                    "Bloquante",
                    class_name="rounded-none border border-[rgb(var(--ap-danger-rgb)/0.35)] bg-[rgb(var(--ap-flame-strong-rgb)/0.10)] px-2 py-0.5 text-[9px] font-bold text-[rgb(var(--ap-warm-150-rgb))] w-fit",
                ),
                rx.fragment(),
            ),
            rx.el.span(
                item["code"],
                class_name="text-[9px] font-mono text-[rgb(var(--ap-paper-muted-rgb)/0.86)] ml-auto shrink-0",
            ),
            class_name="flex items-center gap-1.5 w-full mt-3",
        ),
        rx.el.p(
            item["title"],
            class_name="text-[13px] font-semibold text-[rgb(var(--ap-paper-rgb))] mt-2",
        ),
        rx.el.p(
            item["statement"],
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] leading-relaxed mt-1.5",
        ),
        rx.cond(
            item["rationale"] != "",
            rx.el.div(
                rx.icon(
                    "circle-help",
                    class_name="h-3 w-3 stroke-[rgb(var(--ap-accent-rgb))] shrink-0 mt-0.5",
                ),
                rx.el.p(
                    item["rationale"],
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-accent-pale-rgb)/0.75)] leading-relaxed",
                ),
                class_name="flex items-start gap-2 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.20)] bg-[rgb(var(--ap-accent-rgb))]/[0.05] px-2.5 py-2 mt-2",
            ),
            rx.fragment(),
        ),
        rx.cond(
            item["remediation"] != "",
            rx.el.div(
                rx.icon(
                    "wrench",
                    class_name="h-3 w-3 stroke-[rgb(var(--ap-flame-soft-rgb))] shrink-0 mt-0.5",
                ),
                rx.el.p(
                    item["remediation"],
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-warm-100-rgb)/0.75)] leading-relaxed",
                ),
                class_name="flex items-start gap-2 rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.20)] bg-[rgb(var(--ap-flame-soft-rgb))]/[0.05] px-2.5 py-2 mt-2",
            ),
            rx.fragment(),
        ),
        rx.cond(
            item["field_reference"] != "",
            rx.el.span(
                item["field_reference"],
                class_name="inline-block rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[9px] font-mono text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit mt-2",
            ),
            rx.fragment(),
        ),
        key=key,
        class_name="w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] p-3",
    )


def _faq_card(item: HelpFaq, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "message-circle-question",
                class_name="h-3.5 w-3.5 stroke-[rgb(var(--ap-flame-soft-rgb))] shrink-0 mt-0.5",
            ),
            rx.el.p(
                item["question"],
                class_name="text-[12px] font-semibold text-[rgb(var(--ap-paper-rgb))] leading-snug",
            ),
            class_name="flex items-start gap-2 w-full",
        ),
        rx.el.p(
            item["answer_farmer"],
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] leading-relaxed mt-2",
        ),
        rx.cond(
            item["answer_pro"] != "",
            rx.el.p(
                item["answer_pro"],
                class_name="text-[11px] font-medium text-[rgb(var(--ap-warm-100-rgb)/0.55)] leading-relaxed mt-1.5",
            ),
            rx.fragment(),
        ),
        key=key,
        class_name="w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] p-3",
    )


def _procedure_card(item: HelpProcedure, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("list-checks", class_name="h-3.5 w-3.5 stroke-[rgb(var(--ap-accent-rgb))]"),
            rx.el.p(
                item["title"],
                class_name="text-[12px] font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
            ),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.p(
            item["objective"],
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] leading-relaxed mt-1.5",
        ),
        rx.el.div(
            rx.el.span(
                f"{item['step_count']} étape(s)",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[9px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
            ),
            rx.el.span(
                f"{item['estimated_minutes']} min",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[9px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
            ),
            rx.el.a(
                rx.el.span("Dérouler", class_name="text-[10px]"),
                rx.icon("arrow-up-right", class_name="h-3 w-3"),
                href="/guide",
                class_name="flex items-center gap-1 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] hover:bg-[rgb(var(--ap-accent-rgb)/0.20)] transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-1.5 w-full mt-2.5",
        ),
        key=key,
        class_name="w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] p-3",
    )


def _article_card(item: HelpArticle, key: str = "") -> rx.Component:
    return rx.el.a(
        rx.el.div(
            rx.icon("file-text", class_name="h-3.5 w-3.5 stroke-[rgb(var(--ap-accent-rgb))]"),
            class_name="flex h-7 w-7 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.20)] bg-[rgb(var(--ap-accent-rgb))]/[0.07]",
        ),
        rx.el.div(
            rx.el.p(
                item["title"],
                class_name="text-[12px] font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
            ),
            rx.el.p(
                f"{item['category_name']} · {item['reading_minutes']} min",
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-0.5",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.icon(
            "arrow-up-right",
            class_name="h-3 w-3 stroke-[rgb(var(--ap-paper-muted-rgb)/0.40)] shrink-0",
        ),
        href="/guide",
        key=key,
        class_name="flex items-center gap-2.5 w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] p-2.5 hover:border-[rgb(var(--ap-accent-rgb)/0.30)] hover:bg-[rgb(var(--ap-surface-high-rgb))] transition-colors",
    )


def _focus_block() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("target", class_name="h-3.5 w-3.5 stroke-[rgb(var(--ap-ink-rgb))]"),
                class_name="flex h-7 w-7 shrink-0 items-center justify-center rounded-none bg-[rgb(var(--ap-flame-soft-rgb))]",
            ),
            rx.el.div(
                rx.el.span(
                    "Règle appliquée à votre saisie",
                    class_name="ap-eyebrow text-[rgb(var(--ap-flame-soft-rgb)/0.80)]",
                ),
                rx.el.p(
                    HelpState.focus_label,
                    class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.button(
                rx.icon("x", class_name="h-3 w-3"),
                type="button",
                on_click=HelpState.clear_focus,
                class_name="flex h-6 w-6 items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] text-[rgb(var(--ap-paper-muted-rgb)/0.82)] hover:text-[rgb(var(--ap-paper-rgb))] transition-colors shrink-0",
            ),
            class_name="flex items-start gap-2.5 w-full",
        ),
        rx.el.p(
            HelpState.focus_hint,
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.90)] leading-relaxed mt-2.5",
        ),
        rx.el.div(
            rx.foreach(
                HelpState.focus_rules,
                lambda item: _rule_card(item, key=item["code"]),
            ),
            class_name="flex flex-col gap-2 w-full mt-3",
        ),
        class_name="w-full rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb))]/[0.06] p-3.5",
    )


def _skeleton() -> rx.Component:
    return rx.el.div(
        skeleton_page(3),
        class_name="flex flex-col gap-3 w-full",
    )


def _panel_body() -> rx.Component:
    return rx.el.div(
        rx.cond(HelpState.has_focus, _focus_block(), rx.fragment()),
        _section(
            "Concepts clés",
            "book-a",
            HelpState.concepts.length(),
            rx.el.div(
                rx.foreach(
                    HelpState.concepts,
                    lambda item: _concept_card(item, key=item["slug"]),
                ),
                class_name="flex flex-col gap-2 w-full mt-2.5",
            ),
        ),
        _section(
            "Pourquoi ?",
            "circle-help",
            HelpState.why_rules.length(),
            rx.el.div(
                rx.foreach(
                    HelpState.why_rules,
                    lambda item: _rule_card(item, key=item["code"]),
                ),
                class_name="flex flex-col gap-2 w-full mt-2.5",
            ),
        ),
        _section(
            "Attention",
            "triangle-alert",
            HelpState.attention_rules.length(),
            rx.el.div(
                rx.foreach(
                    HelpState.attention_rules,
                    lambda item: _rule_card(item, key=item["code"]),
                ),
                class_name="flex flex-col gap-2 w-full mt-2.5",
            ),
        ),
        _section(
            "Erreurs fréquentes",
            "message-circle-question",
            HelpState.faqs.length(),
            rx.el.div(
                rx.foreach(
                    HelpState.faqs,
                    lambda item: _faq_card(item, key=item["id"].to_string()),
                ),
                class_name="flex flex-col gap-2 w-full mt-2.5",
            ),
        ),
        _section(
            "Procédures",
            "list-checks",
            HelpState.procedures.length(),
            rx.el.div(
                rx.foreach(
                    HelpState.procedures,
                    lambda item: _procedure_card(item, key=item["slug"]),
                ),
                class_name="flex flex-col gap-2 w-full mt-2.5",
            ),
        ),
        _section(
            "À lire",
            "library-big",
            HelpState.articles.length(),
            rx.el.div(
                rx.foreach(
                    HelpState.articles,
                    lambda item: _article_card(item, key=item["slug"]),
                ),
                class_name="flex flex-col gap-2 w-full mt-2.5",
            ),
        ),
        class_name="flex flex-col gap-5 w-full",
    )


def guide_help_panel() -> rx.Component:
    """Panneau latéral d'aide embarquée, monté une fois par écran."""
    return rx.cond(
        HelpState.is_open,
        rx.fragment(
            rx.el.div(
                on_click=HelpState.close_panel,
                class_name="fixed inset-0 z-[55] bg-[rgb(var(--ap-ink-deep-rgb)/0.60)] -[2px]",
            ),
            rx.el.aside(
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.icon(
                                HelpState.context_icon,
                                class_name="h-4 w-4 stroke-[rgb(var(--ap-ink-rgb))]",
                            ),
                            class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none bg-[rgb(var(--ap-accent-rgb))]",
                        ),
                        rx.el.div(
                            rx.el.span(
                                "Aide embarquée",
                                class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                            ),
                            rx.el.h2(
                                HelpState.context_label,
                                class_name="ap-serif text-xl leading-tight text-[rgb(var(--ap-paper-rgb))] mt-0.5",
                            ),
                            class_name="min-w-0 flex-1",
                        ),
                        rx.el.button(
                            rx.icon("x", class_name="h-4 w-4"),
                            type="button",
                            on_click=HelpState.close_panel,
                            aria_label="Fermer l'aide contextuelle",
                            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] text-[rgb(var(--ap-paper-muted-rgb)/0.82)] hover:text-[rgb(var(--ap-paper-rgb))] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] transition-colors",
                        ),
                        class_name="flex items-start gap-2.5 w-full",
                    ),
                    rx.el.p(
                        HelpState.context_tagline,
                        class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] leading-relaxed mt-2.5",
                    ),
                    rx.el.div(
                        rx.el.a(
                            rx.icon(
                                "corner-down-right",
                                class_name="h-3 w-3 stroke-[rgb(var(--ap-accent-rgb))]",
                            ),
                            rx.el.span(
                                HelpState.context_route,
                                class_name="text-[10px] font-semibold",
                            ),
                            href=HelpState.context_route,
                            class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2.5 py-1 text-[rgb(var(--ap-paper-muted-rgb)/0.82)] hover:text-[rgb(var(--ap-paper-rgb))] transition-colors w-fit",
                        ),
                        rx.el.span(
                            f"{HelpState.content_count} contenu(s)",
                            class_name="rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2.5 py-1 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
                        ),
                        class_name="flex flex-wrap items-center gap-2 mt-3",
                    ),
                    class_name="w-full border-b border-[rgb(var(--ap-paper-rgb)/0.18)] pb-4",
                ),
                rx.el.div(
                    rx.cond(HelpState.is_loading, _skeleton(), _panel_body()),
                    class_name="w-full mt-5",
                ),
                rx.el.a(
                    rx.icon("book-open", class_name="h-4 w-4 stroke-[rgb(var(--ap-ink-rgb))]"),
                    rx.el.span(
                        "Ouvrir le Guide Agricole",
                        class_name="text-sm font-semibold text-[rgb(var(--ap-ink-rgb))]",
                    ),
                    href="/guide",
                    class_name="flex items-center justify-center gap-2 w-full rounded-none bg-[rgb(var(--ap-accent-rgb))] px-4 py-2.5 hover:bg-[rgb(var(--ap-accent-soft-rgb))] transition-colors mt-6",
                ),
                aria_label="Guide contextuel",
                class_name="fixed right-0 top-0 z-[60] h-screen w-full sm:w-[26rem] overflow-y-auto border-l border-[rgb(var(--ap-accent-rgb)/0.20)] bg-[rgb(var(--ap-surface-soft-rgb)/0.95)] px-5 py-6 pb-28 sm:pb-8 ",
            ),
        ),
        rx.fragment(),
    )

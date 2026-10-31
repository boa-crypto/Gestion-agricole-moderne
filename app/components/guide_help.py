"""Composants réutilisables du guide contextuel embarqué.

- `help_button` / `help_icon_button` : déclencheurs discrets pour les headers de
  pages, les modales et les formulaires.
- `guide_error` : message d'erreur enrichi d'une explication pédagogique et d'un
  accès direct à la règle de cohérence concernée.
- `guide_help_panel` : panneau latéral d'aide embarquée (concepts, « Pourquoi ? »,
  « Attention », erreurs fréquentes, procédures, articles, lien vers /guide).
"""

import reflex as rx

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
        rx.icon("life-buoy", class_name="h-3.5 w-3.5 stroke-[#d8fa5e]"),
        rx.el.span(label, class_name="text-xs font-semibold"),
        type="button",
        title="Aide contextuelle du Guide Agricole",
        aria_label="Ouvrir l'aide contextuelle",
        on_click=HelpState.toggle_context(context_key),
        class_name="flex items-center gap-2 rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/[0.07] px-3 py-1.5 text-[#efffc4]/85 hover:border-[#d8fa5e]/50 hover:bg-[#d8fa5e]/[0.14] transition-colors w-fit",
    )


def help_icon_button(context_key: str) -> rx.Component:
    """Icône « ? » compacte, pour les en-têtes de blocs et de formulaires."""
    return rx.el.button(
        rx.icon("circle-help", class_name="h-3.5 w-3.5 stroke-[#d8fa5e]"),
        type="button",
        title="Aide contextuelle",
        aria_label="Ouvrir l'aide contextuelle",
        on_click=HelpState.toggle_context(context_key),
        class_name="flex h-7 w-7 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/20 bg-[#d8fa5e]/[0.06] hover:border-[#d8fa5e]/50 hover:bg-[#d8fa5e]/[0.14] transition-colors",
    )


def help_topic_button(
    context_key: str, topic: str, label: str = "Pourquoi cette règle ?"
) -> rx.Component:
    """Accès direct à la règle de cohérence concernée par une erreur."""
    return rx.el.button(
        rx.icon(topic_icon(topic), class_name="h-3.5 w-3.5 stroke-[#ff8a5b]"),
        rx.el.span(label, class_name="text-[11px] font-semibold"),
        type="button",
        on_click=HelpState.open_topic(context_key, topic),
        class_name="flex items-center gap-1.5 rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/[0.08] px-3 py-1 text-[#ffdccb]/90 hover:border-[#ff8a5b]/60 hover:bg-[#ff8a5b]/[0.16] transition-colors w-fit",
    )


def guide_error(message: rx.Var, context_key: str, topic: str) -> rx.Component:
    """Message d'erreur de formulaire enrichi d'une lecture pédagogique."""
    return rx.cond(
        message != "",
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "octagon-alert",
                    class_name="h-4 w-4 stroke-[#ff9b8c] shrink-0 mt-0.5",
                ),
                rx.el.p(
                    message,
                    class_name="text-xs font-semibold text-[#ffbcb0] leading-relaxed",
                ),
                class_name="flex items-start gap-2 w-full",
            ),
            rx.el.div(
                rx.icon(
                    topic_icon(topic),
                    class_name="h-3.5 w-3.5 stroke-[#d8fa5e] shrink-0 mt-0.5",
                ),
                rx.el.div(
                    rx.el.span(
                        topic_label(topic),
                        class_name="ap-eyebrow text-[#d8fa5e]/80",
                    ),
                    rx.el.p(
                        topic_hint(topic),
                        class_name="text-[11px] font-medium text-[#c9c5b4]/70 leading-relaxed mt-1",
                    ),
                    class_name="min-w-0 flex-1",
                ),
                class_name="flex items-start gap-2 w-full rounded-none border border-[#d8fa5e]/20 bg-[#d8fa5e]/[0.05] px-3 py-2.5 mt-3",
            ),
            rx.el.div(
                help_topic_button(context_key, topic),
                rx.el.a(
                    rx.el.span("Voir le guide", class_name="text-[11px]"),
                    rx.icon("arrow-up-right", class_name="h-3 w-3"),
                    href="/guide",
                    class_name="flex items-center gap-1.5 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/65 hover:text-[#f2efe4] hover:border-[#d8fa5e]/30 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 mt-3",
            ),
            class_name="w-full rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/[0.08] p-3.5 mt-5",
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
            rx.icon(icon, class_name="h-3.5 w-3.5 stroke-[#d8fa5e]/80"),
            rx.el.span(
                title,
                class_name="ap-eyebrow text-[#c9c5b4]/50",
            ),
            rx.el.span(
                count,
                class_name="rounded-none bg-[#d8fa5e]/15 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit ml-auto",
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
                class_name="text-sm font-semibold text-[#f2efe4] truncate",
            ),
            rx.cond(
                item["acronym"] != "",
                rx.el.span(
                    item["acronym"],
                    class_name="rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-1.5 py-0.5 text-[9px] font-bold text-[#e4ff9b] w-fit",
                ),
                rx.fragment(),
            ),
            rx.cond(
                item["unit"] != "",
                rx.el.span(
                    item["unit"],
                    class_name="text-[10px] font-semibold text-[#c9c5b4]/45 ml-auto shrink-0",
                ),
                rx.fragment(),
            ),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.p(
            item["definition_farmer"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/65 leading-relaxed mt-1.5",
        ),
        rx.cond(
            item["definition_pro"] != "",
            rx.el.p(
                item["definition_pro"],
                class_name="text-[11px] font-medium text-[#ffdccb]/55 leading-relaxed mt-1.5",
            ),
            rx.fragment(),
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
    )


def _rule_card(item: HelpRule, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name=rx.match(
                item["tone"],
                ("bad", "h-1 w-full rounded-none bg-[#ff6b5a]/80"),
                ("warn", "h-1 w-full rounded-none bg-[#ff8a5b]/80"),
                "h-1 w-full rounded-none bg-[#d8fa5e]/80",
            )
        ),
        rx.el.div(
            rx.el.span(
                item["kind_label"],
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[9px] font-bold text-[#c9c5b4]/65 w-fit",
            ),
            rx.cond(
                item["is_blocking"],
                rx.el.span(
                    "Bloquante",
                    class_name="rounded-none border border-[#ff6b5a]/35 bg-[#f2452c]/10 px-2 py-0.5 text-[9px] font-bold text-[#ffbcb0] w-fit",
                ),
                rx.fragment(),
            ),
            rx.el.span(
                item["code"],
                class_name="text-[9px] font-mono text-[#c9c5b4]/40 ml-auto shrink-0",
            ),
            class_name="flex items-center gap-1.5 w-full mt-3",
        ),
        rx.el.p(
            item["title"],
            class_name="text-[13px] font-semibold text-[#f2efe4] mt-2",
        ),
        rx.el.p(
            item["statement"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/65 leading-relaxed mt-1.5",
        ),
        rx.cond(
            item["rationale"] != "",
            rx.el.div(
                rx.icon(
                    "circle-help",
                    class_name="h-3 w-3 stroke-[#d8fa5e] shrink-0 mt-0.5",
                ),
                rx.el.p(
                    item["rationale"],
                    class_name="text-[11px] font-medium text-[#efffc4]/75 leading-relaxed",
                ),
                class_name="flex items-start gap-2 rounded-none border border-[#d8fa5e]/20 bg-[#d8fa5e]/[0.05] px-2.5 py-2 mt-2",
            ),
            rx.fragment(),
        ),
        rx.cond(
            item["remediation"] != "",
            rx.el.div(
                rx.icon(
                    "wrench",
                    class_name="h-3 w-3 stroke-[#ff8a5b] shrink-0 mt-0.5",
                ),
                rx.el.p(
                    item["remediation"],
                    class_name="text-[11px] font-medium text-[#ffdccb]/75 leading-relaxed",
                ),
                class_name="flex items-start gap-2 rounded-none border border-[#ff8a5b]/20 bg-[#ff8a5b]/[0.05] px-2.5 py-2 mt-2",
            ),
            rx.fragment(),
        ),
        rx.cond(
            item["field_reference"] != "",
            rx.el.span(
                item["field_reference"],
                class_name="inline-block rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[9px] font-mono text-[#c9c5b4]/45 w-fit mt-2",
            ),
            rx.fragment(),
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
    )


def _faq_card(item: HelpFaq, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "message-circle-question",
                class_name="h-3.5 w-3.5 stroke-[#ff8a5b] shrink-0 mt-0.5",
            ),
            rx.el.p(
                item["question"],
                class_name="text-[12px] font-semibold text-[#f2efe4] leading-snug",
            ),
            class_name="flex items-start gap-2 w-full",
        ),
        rx.el.p(
            item["answer_farmer"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/65 leading-relaxed mt-2",
        ),
        rx.cond(
            item["answer_pro"] != "",
            rx.el.p(
                item["answer_pro"],
                class_name="text-[11px] font-medium text-[#ffdccb]/55 leading-relaxed mt-1.5",
            ),
            rx.fragment(),
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
    )


def _procedure_card(item: HelpProcedure, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("list-checks", class_name="h-3.5 w-3.5 stroke-[#d8fa5e]"),
            rx.el.p(
                item["title"],
                class_name="text-[12px] font-semibold text-[#f2efe4] truncate",
            ),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.p(
            item["objective"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/60 leading-relaxed mt-1.5",
        ),
        rx.el.div(
            rx.el.span(
                f"{item['step_count']} étape(s)",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[9px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            rx.el.span(
                f"{item['estimated_minutes']} min",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[9px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            rx.el.a(
                rx.el.span("Dérouler", class_name="text-[10px]"),
                rx.icon("arrow-up-right", class_name="h-3 w-3"),
                href="/guide",
                class_name="flex items-center gap-1 rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] hover:bg-[#d8fa5e]/20 transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-1.5 w-full mt-2.5",
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
    )


def _article_card(item: HelpArticle, key: str = "") -> rx.Component:
    return rx.el.a(
        rx.el.div(
            rx.icon("file-text", class_name="h-3.5 w-3.5 stroke-[#d8fa5e]"),
            class_name="flex h-7 w-7 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/20 bg-[#d8fa5e]/[0.07]",
        ),
        rx.el.div(
            rx.el.p(
                item["title"],
                class_name="text-[12px] font-semibold text-[#f2efe4] truncate",
            ),
            rx.el.p(
                f"{item['category_name']} · {item['reading_minutes']} min",
                class_name="text-[10px] font-medium text-[#c9c5b4]/45 mt-0.5",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.icon(
            "arrow-up-right",
            class_name="h-3 w-3 stroke-[#c9c5b4]/40 shrink-0",
        ),
        href="/guide",
        key=key,
        class_name="flex items-center gap-2.5 w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-2.5 hover:border-[#d8fa5e]/30 hover:bg-[#191c13] transition-colors",
    )


def _focus_block() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("target", class_name="h-3.5 w-3.5 stroke-[#0A0A08]"),
                class_name="flex h-7 w-7 shrink-0 items-center justify-center rounded-none bg-[#ff8a5b]",
            ),
            rx.el.div(
                rx.el.span(
                    "Règle appliquée à votre saisie",
                    class_name="ap-eyebrow text-[#ff8a5b]/80",
                ),
                rx.el.p(
                    HelpState.focus_label,
                    class_name="text-sm font-semibold text-[#f2efe4] mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.button(
                rx.icon("x", class_name="h-3 w-3"),
                type="button",
                on_click=HelpState.clear_focus,
                class_name="flex h-6 w-6 items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#14160f] text-[#c9c5b4]/60 hover:text-[#f2efe4] transition-colors shrink-0",
            ),
            class_name="flex items-start gap-2.5 w-full",
        ),
        rx.el.p(
            HelpState.focus_hint,
            class_name="text-[11px] font-medium text-[#c9c5b4]/70 leading-relaxed mt-2.5",
        ),
        rx.el.div(
            rx.foreach(
                HelpState.focus_rules,
                lambda item: _rule_card(item, key=item["code"]),
            ),
            class_name="flex flex-col gap-2 w-full mt-3",
        ),
        class_name="w-full rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/[0.06] p-3.5",
    )


def _skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(class_name="animate-pulse h-20 rounded-none bg-[#16190f]"),
        rx.el.div(class_name="animate-pulse h-28 rounded-none bg-[#16190f]"),
        rx.el.div(class_name="animate-pulse h-24 rounded-none bg-[#16190f]"),
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
                class_name="fixed inset-0 z-[55] bg-[#060604]/60 -[2px]",
            ),
            rx.el.aside(
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.icon(
                                HelpState.context_icon,
                                class_name="h-4 w-4 stroke-[#0A0A08]",
                            ),
                            class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none bg-[#d8fa5e]",
                        ),
                        rx.el.div(
                            rx.el.span(
                                "Aide embarquée",
                                class_name="ap-eyebrow text-[#d8fa5e]/80",
                            ),
                            rx.el.h2(
                                HelpState.context_label,
                                class_name="ap-serif text-xl leading-tight text-[#f2efe4] mt-0.5",
                            ),
                            class_name="min-w-0 flex-1",
                        ),
                        rx.el.button(
                            rx.icon("x", class_name="h-4 w-4"),
                            type="button",
                            on_click=HelpState.close_panel,
                            aria_label="Fermer l'aide contextuelle",
                            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#14160f] text-[#c9c5b4]/60 hover:text-[#f2efe4] hover:border-[#d8fa5e]/30 transition-colors",
                        ),
                        class_name="flex items-start gap-2.5 w-full",
                    ),
                    rx.el.p(
                        HelpState.context_tagline,
                        class_name="text-[11px] font-medium text-[#c9c5b4]/55 leading-relaxed mt-2.5",
                    ),
                    rx.el.div(
                        rx.el.a(
                            rx.icon(
                                "corner-down-right",
                                class_name="h-3 w-3 stroke-[#d8fa5e]",
                            ),
                            rx.el.span(
                                HelpState.context_route,
                                class_name="text-[10px] font-semibold",
                            ),
                            href=HelpState.context_route,
                            class_name="flex items-center gap-1.5 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2.5 py-1 text-[#c9c5b4]/60 hover:text-[#f2efe4] transition-colors w-fit",
                        ),
                        rx.el.span(
                            f"{HelpState.content_count} contenu(s)",
                            class_name="rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10 px-2.5 py-1 text-[10px] font-bold text-[#e4ff9b] w-fit",
                        ),
                        class_name="flex flex-wrap items-center gap-2 mt-3",
                    ),
                    class_name="w-full border-b border-[#f2efe4]/12 pb-4",
                ),
                rx.el.div(
                    rx.cond(HelpState.is_loading, _skeleton(), _panel_body()),
                    class_name="w-full mt-5",
                ),
                rx.el.a(
                    rx.icon("book-open", class_name="h-4 w-4 stroke-[#0A0A08]"),
                    rx.el.span(
                        "Ouvrir le Guide Agricole",
                        class_name="text-sm font-semibold text-[#0A0A08]",
                    ),
                    href="/guide",
                    class_name="flex items-center justify-center gap-2 w-full rounded-none bg-[#d8fa5e] px-4 py-2.5 hover:bg-[#e4ff9b] transition-colors mt-6",
                ),
                aria_label="Guide contextuel",
                class_name="fixed right-0 top-0 z-[60] h-screen w-full sm:w-[26rem] overflow-y-auto border-l border-[#d8fa5e]/20 bg-[#0D0F09]/95 px-5 py-6 pb-28 sm:pb-8 ",
            ),
        ),
        rx.fragment(),
    )

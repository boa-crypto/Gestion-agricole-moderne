import reflex as rx

from app.states.guide_state import (
    ArticleCard,
    ArticleLink,
    GuideState,
    ProcedureCard,
    ProcedureStep,
)


def _article_item(article: ArticleCard, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.el.span(
                article["category_name"],
                class_name="ap-eyebrow text-[#c9c5b4]/45 truncate",
            ),
            rx.cond(
                article["is_featured"],
                rx.el.span(
                    "Clé",
                    class_name="rounded-none border border-[#ff8a5b]/40 bg-[#ff8a5b]/10 px-1.5 py-0.5 text-[9px] font-bold text-[#ffb894] w-fit ml-auto",
                ),
                rx.fragment(),
            ),
            class_name="flex items-center gap-2 w-full",
        ),
        rx.el.p(
            article["title"],
            class_name="text-sm font-semibold text-[#f2efe4] text-left mt-2",
        ),
        rx.el.p(
            article["subtitle"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/50 text-left mt-1 line-clamp-2",
        ),
        rx.el.div(
            rx.el.span(
                article["difficulty_label"],
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            rx.el.span(
                f"{article['reading_minutes']} min",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            class_name="flex flex-wrap items-center gap-1.5 w-full mt-3",
        ),
        on_click=GuideState.select_article(article["slug"]),
        key=key,
        class_name=rx.cond(
            GuideState.active_article_slug == article["slug"],
            "w-full rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/[0.07] p-4 text-left ring-2 ring-[#d8fa5e]/30 transition-all",
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 text-left hover:border-[#d8fa5e]/25 transition-all",
        ),
    )


def _article_list() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Sommaire vivant",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    GuideState.category_label,
                    class_name="ap-serif text-2xl text-[#f2efe4] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                GuideState.category_articles.length(),
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-xs font-bold text-[#c9c5b4]/70 w-fit",
            ),
            class_name="flex items-end justify-between gap-3 w-full",
        ),
        rx.cond(
            GuideState.category_articles.length() > 0,
            rx.el.div(
                rx.foreach(
                    GuideState.category_articles,
                    lambda a: _article_item(a, key=a["slug"]),
                ),
                class_name="flex flex-col gap-3 mt-5 max-h-[48rem] overflow-y-auto pr-1",
            ),
            rx.el.div(
                rx.icon("book-dashed", class_name="h-6 w-6 text-[#ff8a5b]"),
                rx.el.p(
                    "Aucun article dans cette catégorie.",
                    class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2 text-center",
                ),
                class_name="flex flex-col items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#101208] py-12 mt-5",
            ),
        ),
        class_name="w-full xl:w-[22rem] shrink-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5 ",
    )


def _meta(icon: str, label: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="h-3.5 w-3.5 text-[#d8fa5e]/80"),
        rx.el.span(
            label, class_name="text-[11px] font-semibold text-[#c9c5b4]/65"
        ),
        class_name="flex items-center gap-1.5 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 w-fit",
    )


def _paragraph(chunk: str) -> rx.Component:
    return rx.el.p(
        chunk,
        class_name="text-sm font-medium text-[#c9c5b4]/70 leading-relaxed",
    )


def _reading_block(
    title: str,
    caption: str,
    icon: str,
    paragraphs: rx.Var,
    accent: str,
) -> rx.Component:
    return rx.el.article(
        rx.el.div(class_name=accent),
        rx.el.div(
            rx.el.div(
                rx.icon(icon, class_name="h-4 w-4 text-[#d8fa5e]"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10",
            ),
            rx.el.div(
                rx.el.h4(
                    title,
                    class_name="ap-serif text-xl text-[#f2efe4]",
                ),
                rx.el.p(
                    caption,
                    class_name="ap-eyebrow text-[#c9c5b4]/40 mt-1",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-center gap-3 w-full mt-4",
        ),
        rx.el.div(
            rx.foreach(paragraphs, _paragraph),
            class_name="flex flex-col gap-3 w-full mt-4",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5",
    )


def _module_link(link: ArticleLink, key: str = "") -> rx.Component:
    return rx.el.a(
        rx.el.div(
            rx.icon(link["icon"], class_name="h-4 w-4 text-[#d8fa5e]"),
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10",
        ),
        rx.el.div(
            rx.el.p(
                link["label"],
                class_name="text-sm font-semibold text-[#f2efe4] truncate",
            ),
            rx.el.p(
                link["description"],
                class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-0.5 line-clamp-2",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.icon(
            "arrow-up-right",
            class_name="h-3.5 w-3.5 text-[#c9c5b4]/45 shrink-0",
        ),
        href=link["route"],
        key=key,
        class_name="flex items-start gap-3 w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3 hover:border-[#d8fa5e]/30 hover:bg-[#191c13] transition-colors",
    )


def _procedure_card(procedure: ProcedureCard, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.icon("list-checks", class_name="h-4 w-4 text-[#ff8a5b]"),
            rx.el.p(
                procedure["title"],
                class_name="text-sm font-semibold text-[#f2efe4] text-left truncate",
            ),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.p(
            procedure["objective"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/55 text-left leading-relaxed mt-2",
        ),
        rx.el.div(
            rx.el.span(
                f"{procedure['step_count']} étape(s)",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            rx.el.span(
                f"{procedure['estimated_minutes']} min",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            rx.el.span(
                procedure["difficulty_label"],
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            rx.el.span(
                "Dérouler",
                class_name="rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-1.5 w-full mt-3",
        ),
        on_click=GuideState.start_procedure(procedure["slug"]),
        key=key,
        class_name=rx.cond(
            GuideState.open_procedure_slug == procedure["slug"],
            "w-full rounded-none border border-[#ff8a5b]/40 bg-[#ff8a5b]/[0.07] p-4 text-left transition-all",
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 text-left hover:border-[#ff8a5b]/30 transition-all",
        ),
    )


def _step(step: ProcedureStep, key: str = "") -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.el.button(
                rx.cond(
                    GuideState.done_steps.contains(step["id"]),
                    rx.icon("check", class_name="h-4 w-4 text-[#0A0A08]"),
                    rx.el.span(
                        step["position"],
                        class_name="text-[11px] font-bold text-[#c9c5b4]/60",
                    ),
                ),
                on_click=GuideState.toggle_step(step["id"]),
                class_name=rx.cond(
                    GuideState.done_steps.contains(step["id"]),
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-none bg-[#d8fa5e] transition-colors",
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[#f2efe4]/16 bg-[#14160f] hover:border-[#d8fa5e]/40 transition-colors",
                ),
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.p(
                        step["title"],
                        class_name="text-sm font-semibold text-[#f2efe4]",
                    ),
                    rx.cond(
                        step["is_optional"],
                        rx.el.span(
                            "Optionnelle",
                            class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[9px] font-semibold text-[#c9c5b4]/50 w-fit",
                        ),
                        rx.fragment(),
                    ),
                    rx.el.span(
                        f"{step['duration_minutes']} min",
                        class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[9px] font-semibold text-[#c9c5b4]/50 w-fit ml-auto",
                    ),
                    class_name="flex flex-wrap items-center gap-2 w-full",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.span(
                            "Lecture agricole",
                            class_name="ap-eyebrow text-[#d8fa5e]/70",
                        ),
                        rx.el.p(
                            step["instruction_farmer"],
                            class_name="text-[12px] font-medium text-[#c9c5b4]/70 leading-relaxed mt-1",
                        ),
                        class_name="flex-1 min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
                    ),
                    rx.el.div(
                        rx.el.span(
                            "Lecture AgriPro",
                            class_name="ap-eyebrow text-[#ff8a5b]/70",
                        ),
                        rx.el.p(
                            step["instruction_pro"],
                            class_name="text-[12px] font-medium text-[#c9c5b4]/70 leading-relaxed mt-1",
                        ),
                        class_name="flex-1 min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
                    ),
                    class_name="flex flex-col lg:flex-row gap-2 w-full mt-3",
                ),
                rx.cond(
                    step["ui_hint"] != "",
                    rx.el.div(
                        rx.icon(
                            "mouse-pointer-click",
                            class_name="h-3.5 w-3.5 text-[#a9c98b] shrink-0",
                        ),
                        rx.el.p(
                            step["ui_hint"],
                            class_name="text-[11px] font-medium text-[#c9c5b4]/60",
                        ),
                        class_name="flex items-start gap-2 w-full mt-2",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    step["why"] != "",
                    rx.el.div(
                        rx.icon(
                            "circle-help",
                            class_name="h-3.5 w-3.5 text-[#d8fa5e] shrink-0",
                        ),
                        rx.el.p(
                            step["why"],
                            class_name="text-[11px] font-medium text-[#efffc4]/80",
                        ),
                        class_name="flex items-start gap-2 rounded-none border border-[#d8fa5e]/20 bg-[#d8fa5e]/[0.06] px-3 py-2 w-full mt-2",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    step["warning"] != "",
                    rx.el.div(
                        rx.icon(
                            "triangle-alert",
                            class_name="h-3.5 w-3.5 text-[#ff8a5b] shrink-0",
                        ),
                        rx.el.p(
                            step["warning"],
                            class_name="text-[11px] font-medium text-[#ffdccb]/85",
                        ),
                        class_name="flex items-start gap-2 rounded-none border border-[#ff8a5b]/25 bg-[#ff8a5b]/[0.07] px-3 py-2 w-full mt-2",
                    ),
                    rx.fragment(),
                ),
                rx.el.div(
                    rx.cond(
                        step["field_reference"] != "",
                        rx.el.span(
                            step["field_reference"],
                            class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-mono text-[#c9c5b4]/50 w-fit",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        step["module_route"] != "",
                        rx.el.a(
                            rx.el.span("Ouvrir l'écran"),
                            rx.icon("arrow-up-right", class_name="h-3 w-3"),
                            href=step["module_route"],
                            class_name="flex items-center gap-1.5 rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10 px-3 py-1 text-[10px] font-semibold text-[#e4ff9b] hover:bg-[#d8fa5e]/20 transition-colors w-fit ml-auto",
                        ),
                        rx.fragment(),
                    ),
                    class_name="flex flex-wrap items-center gap-2 w-full mt-3",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        key=key,
        class_name=rx.cond(
            GuideState.done_steps.contains(step["id"]),
            "w-full rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/[0.05] p-4",
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#0d0f09] p-4",
        ),
    )


def _procedure_runner() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Procédure interactive",
                    class_name="ap-eyebrow text-[#ff8a5b]/80",
                ),
                rx.el.h4(
                    GuideState.open_procedure["title"],
                    class_name="ap-serif text-2xl text-[#f2efe4] mt-1",
                ),
                rx.el.p(
                    GuideState.open_procedure["objective"],
                    class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2 max-w-2xl",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.button(
                rx.icon("x", class_name="h-3.5 w-3.5"),
                rx.el.span("Fermer"),
                on_click=GuideState.close_procedure,
                class_name="flex items-center gap-1.5 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1.5 text-[11px] font-semibold text-[#c9c5b4]/65 hover:text-[#f2efe4] hover:border-[#d8fa5e]/30 transition-colors w-fit",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3 w-full",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("target", class_name="h-3.5 w-3.5 text-[#d8fa5e]/80"),
                rx.el.p(
                    GuideState.open_procedure["expected_result"],
                    class_name="text-[11px] font-medium text-[#c9c5b4]/60",
                ),
                class_name="flex items-start gap-2 flex-1 min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] px-3 py-2",
            ),
            rx.el.div(
                rx.icon(
                    "map-pin", class_name="h-3.5 w-3.5 text-[#a9c98b]/80"
                ),
                rx.el.p(
                    GuideState.open_procedure["context"],
                    class_name="text-[11px] font-medium text-[#c9c5b4]/60",
                ),
                class_name="flex items-start gap-2 flex-1 min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] px-3 py-2",
            ),
            class_name="flex flex-col lg:flex-row gap-2 w-full mt-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    f"{GuideState.done_steps.length()} / {GuideState.procedure_steps.length()} étape(s) validée(s)",
                    class_name="text-[11px] font-semibold text-[#c9c5b4]/60",
                ),
                rx.el.span(
                    GuideState.step_progress_width,
                    class_name="text-[11px] font-bold text-[#e4ff9b] ml-auto",
                ),
                class_name="flex items-center gap-2 w-full",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="h-full rounded-none bg-gradient-to-r from-[#8fb37a] to-[#d8fa5e]",
                    style={"width": GuideState.step_progress_width},
                ),
                class_name="h-1.5 w-full rounded-none bg-[#20241a] mt-2",
            ),
            class_name="w-full mt-4",
        ),
        rx.el.ol(
            rx.foreach(
                GuideState.procedure_steps,
                lambda s: _step(s, key=s["id"].to_string()),
            ),
            class_name="flex flex-col gap-3 w-full mt-5",
        ),
        class_name="w-full rounded-none border border-[#ff8a5b]/25 bg-[#0A0A08]/70 p-5 mt-4",
    )


def _article_reader() -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.span(
                GuideState.active_article["category_name"],
                class_name="rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#e4ff9b] w-fit",
            ),
            rx.el.span(
                GuideState.active_article["status_label"],
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[10px] font-semibold text-[#c9c5b4]/55 w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.el.h3(
            GuideState.active_article["title"],
            class_name="ap-serif text-3xl md:text-4xl leading-tight text-[#f2efe4] mt-3",
        ),
        rx.el.p(
            GuideState.active_article["subtitle"],
            class_name="text-sm font-medium text-[#c9c5b4]/55 mt-2",
        ),
        rx.el.div(
            _meta("users-round", GuideState.active_article["audience_label"]),
            _meta("gauge", GuideState.active_article["difficulty_label"]),
            _meta(
                "clock",
                f"{GuideState.active_article['reading_minutes']} min de lecture",
            ),
            _meta("git-branch", GuideState.active_article["version_label"]),
            _meta(
                "calendar-check",
                GuideState.active_article["published_label"],
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-4",
        ),
        rx.el.div(
            rx.icon("quote", class_name="h-4 w-4 text-[#d8fa5e]/70 shrink-0"),
            rx.el.p(
                GuideState.active_article["summary"],
                class_name="text-sm font-medium text-[#f2efe4]/85 leading-relaxed",
            ),
            class_name="flex items-start gap-3 rounded-none border border-[#d8fa5e]/20 bg-[#d8fa5e]/[0.05] p-4 w-full mt-5",
        ),
        rx.el.div(
            _reading_block(
                "Lecture agricole",
                "Vocabulaire de terrain",
                "tractor",
                GuideState.farmer_paragraphs,
                "h-1 w-full rounded-none bg-[#d8fa5e]/70",
            ),
            _reading_block(
                "Lecture AgriPro",
                "Vocabulaire technique & données",
                "database",
                GuideState.pro_paragraphs,
                "h-1 w-full rounded-none bg-[#ff8a5b]/70",
            ),
            class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 w-full mt-5",
        ),
        rx.cond(
            GuideState.article_keywords.length() > 0,
            rx.el.div(
                rx.foreach(
                    GuideState.article_keywords,
                    lambda word: rx.el.span(
                        word,
                        class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2.5 py-1 text-[10px] font-semibold text-[#c9c5b4]/55 w-fit",
                    ),
                ),
                class_name="flex flex-wrap items-center gap-2 w-full mt-5",
            ),
            rx.fragment(),
        ),
        rx.cond(
            GuideState.article_links.length() > 0,
            rx.el.div(
                rx.el.div(
                    rx.icon("link", class_name="h-3.5 w-3.5 text-[#d8fa5e]/80"),
                    rx.el.span(
                        "Liens directs vers les modules",
                        class_name="ap-eyebrow text-[#c9c5b4]/45",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.div(
                    rx.foreach(
                        GuideState.article_links,
                        lambda link: _module_link(
                            link, key=link["id"].to_string()
                        ),
                    ),
                    class_name="grid grid-cols-1 lg:grid-cols-2 gap-2 w-full mt-3",
                ),
                class_name="w-full mt-6 border-t border-[#f2efe4]/12 pt-5",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("play", class_name="h-4 w-4 text-[#0A0A08]"),
                rx.el.span(
                    "Comment faire dans AgriPro ?",
                    class_name="text-[#0A0A08]",
                ),
                on_click=GuideState.open_related_procedures,
                class_name="ap-mono inline-flex w-fit items-center gap-2 bg-[#D8FA5E] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[#0A0A08] transition-colors hover:bg-[#E4FF9B]",
            ),
            rx.el.span(
                f"{GuideState.related_procedures.length()} procédure(s) · {GuideState.related_scope_label}",
                class_name="text-[11px] font-medium text-[#c9c5b4]/50",
            ),
            class_name="flex flex-wrap items-center gap-3 w-full mt-6",
        ),
        rx.cond(
            GuideState.show_procedures,
            rx.el.div(
                rx.el.div(
                    rx.foreach(
                        GuideState.related_procedures,
                        lambda p: _procedure_card(p, key=p["slug"]),
                    ),
                    class_name="grid grid-cols-1 lg:grid-cols-2 gap-2 w-full mt-4",
                ),
                rx.cond(
                    GuideState.has_open_procedure,
                    _procedure_runner(),
                    rx.fragment(),
                ),
                class_name="w-full",
            ),
            rx.fragment(),
        ),
        class_name="w-full flex-1 min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 md:p-8 ",
    )


def guide_library() -> rx.Component:
    return rx.el.div(
        _article_list(),
        rx.cond(
            GuideState.has_article,
            _article_reader(),
            rx.el.div(
                rx.icon("book-open", class_name="h-7 w-7 text-[#d8fa5e]"),
                rx.el.h3(
                    "Choisissez un article",
                    class_name="ap-serif text-2xl text-[#f2efe4] mt-3",
                ),
                rx.el.p(
                    "Chaque fiche propose une double lecture : agricole pour le terrain, AgriPro pour la donnée.",
                    class_name="text-sm font-medium text-[#c9c5b4]/55 mt-2 text-center max-w-md",
                ),
                class_name="flex flex-col items-center justify-center flex-1 min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] py-20 px-6 ",
            ),
        ),
        class_name="flex flex-col xl:flex-row gap-4 w-full",
    )

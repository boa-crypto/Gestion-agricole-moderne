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
                class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45 truncate",
            ),
            rx.cond(
                article["is_featured"],
                rx.el.span(
                    "Clé",
                    class_name="rounded-full border border-amber-300/40 bg-amber-300/10 px-1.5 py-0.5 text-[9px] font-bold text-amber-200 w-fit ml-auto",
                ),
                rx.fragment(),
            ),
            class_name="flex items-center gap-2 w-full",
        ),
        rx.el.p(
            article["title"],
            class_name="text-sm font-semibold text-emerald-50 text-left mt-2",
        ),
        rx.el.p(
            article["subtitle"],
            class_name="text-[11px] font-medium text-emerald-100/50 text-left mt-1 line-clamp-2",
        ),
        rx.el.div(
            rx.el.span(
                article["difficulty_label"],
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                f"{article['reading_minutes']} min",
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            class_name="flex flex-wrap items-center gap-1.5 w-full mt-3",
        ),
        on_click=GuideState.select_article(article["slug"]),
        key=key,
        class_name=rx.cond(
            GuideState.active_article_slug == article["slug"],
            "w-full rounded-2xl border border-lime-300/40 bg-lime-300/[0.07] p-4 text-left ring-2 ring-lime-300/30 transition-all",
            "w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left hover:border-lime-300/25 transition-all",
        ),
    )


def _article_list() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Sommaire vivant",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    GuideState.category_label,
                    class_name="font-['Instrument_Serif'] text-2xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                GuideState.category_articles.length(),
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-bold text-emerald-100/70 w-fit",
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
                rx.icon("book-dashed", class_name="h-6 w-6 text-amber-300"),
                rx.el.p(
                    "Aucun article dans cette catégorie.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-2 text-center",
                ),
                class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-12 mt-5",
            ),
        ),
        class_name="w-full xl:w-[22rem] shrink-0 rounded-3xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl",
    )


def _meta(icon: str, label: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="h-3.5 w-3.5 text-lime-300/80"),
        rx.el.span(
            label, class_name="text-[11px] font-semibold text-emerald-100/65"
        ),
        class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1 w-fit",
    )


def _paragraph(chunk: str) -> rx.Component:
    return rx.el.p(
        chunk,
        class_name="text-sm font-medium text-emerald-100/70 leading-relaxed",
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
                rx.icon(icon, class_name="h-4 w-4 text-lime-300"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-lime-300/25 bg-lime-300/10",
            ),
            rx.el.div(
                rx.el.h4(
                    title,
                    class_name="font-['Instrument_Serif'] text-xl text-emerald-50",
                ),
                rx.el.p(
                    caption,
                    class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/40 mt-1",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-center gap-3 w-full mt-4",
        ),
        rx.el.div(
            rx.foreach(paragraphs, _paragraph),
            class_name="flex flex-col gap-3 w-full mt-4",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-5",
    )


def _module_link(link: ArticleLink, key: str = "") -> rx.Component:
    return rx.el.a(
        rx.el.div(
            rx.icon(link["icon"], class_name="h-4 w-4 text-lime-300"),
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-lime-300/25 bg-lime-300/10",
        ),
        rx.el.div(
            rx.el.p(
                link["label"],
                class_name="text-sm font-semibold text-emerald-50 truncate",
            ),
            rx.el.p(
                link["description"],
                class_name="text-[11px] font-medium text-emerald-100/50 mt-0.5 line-clamp-2",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.icon(
            "arrow-up-right",
            class_name="h-3.5 w-3.5 text-emerald-100/45 shrink-0",
        ),
        href=link["route"],
        key=key,
        class_name="flex items-start gap-3 w-full rounded-2xl border border-white/10 bg-white/[0.03] p-3 hover:border-lime-300/30 hover:bg-white/[0.06] transition-colors",
    )


def _procedure_card(procedure: ProcedureCard, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.icon("list-checks", class_name="h-4 w-4 text-amber-300"),
            rx.el.p(
                procedure["title"],
                class_name="text-sm font-semibold text-emerald-50 text-left truncate",
            ),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.p(
            procedure["objective"],
            class_name="text-[11px] font-medium text-emerald-100/55 text-left leading-relaxed mt-2",
        ),
        rx.el.div(
            rx.el.span(
                f"{procedure['step_count']} étape(s)",
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                f"{procedure['estimated_minutes']} min",
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                procedure["difficulty_label"],
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                "Dérouler",
                class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-1.5 w-full mt-3",
        ),
        on_click=GuideState.start_procedure(procedure["slug"]),
        key=key,
        class_name=rx.cond(
            GuideState.open_procedure_slug == procedure["slug"],
            "w-full rounded-2xl border border-amber-300/40 bg-amber-300/[0.07] p-4 text-left transition-all",
            "w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left hover:border-amber-300/30 transition-all",
        ),
    )


def _step(step: ProcedureStep, key: str = "") -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.el.button(
                rx.cond(
                    GuideState.done_steps.contains(step["id"]),
                    rx.icon("check", class_name="h-4 w-4 text-[#04140d]"),
                    rx.el.span(
                        step["position"],
                        class_name="text-[11px] font-bold text-emerald-100/60",
                    ),
                ),
                on_click=GuideState.toggle_step(step["id"]),
                class_name=rx.cond(
                    GuideState.done_steps.contains(step["id"]),
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-lime-300 transition-colors",
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-white/15 bg-white/5 hover:border-lime-300/40 transition-colors",
                ),
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.p(
                        step["title"],
                        class_name="text-sm font-semibold text-emerald-50",
                    ),
                    rx.cond(
                        step["is_optional"],
                        rx.el.span(
                            "Optionnelle",
                            class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[9px] font-semibold text-emerald-100/50 w-fit",
                        ),
                        rx.fragment(),
                    ),
                    rx.el.span(
                        f"{step['duration_minutes']} min",
                        class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[9px] font-semibold text-emerald-100/50 w-fit ml-auto",
                    ),
                    class_name="flex flex-wrap items-center gap-2 w-full",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.span(
                            "Lecture agricole",
                            class_name="text-[9px] font-semibold uppercase tracking-[0.18em] text-lime-300/70",
                        ),
                        rx.el.p(
                            step["instruction_farmer"],
                            class_name="text-[12px] font-medium text-emerald-100/70 leading-relaxed mt-1",
                        ),
                        class_name="flex-1 min-w-0 rounded-xl border border-white/10 bg-white/[0.03] p-3",
                    ),
                    rx.el.div(
                        rx.el.span(
                            "Lecture AgriPro",
                            class_name="text-[9px] font-semibold uppercase tracking-[0.18em] text-amber-300/70",
                        ),
                        rx.el.p(
                            step["instruction_pro"],
                            class_name="text-[12px] font-medium text-emerald-100/70 leading-relaxed mt-1",
                        ),
                        class_name="flex-1 min-w-0 rounded-xl border border-white/10 bg-white/[0.03] p-3",
                    ),
                    class_name="flex flex-col lg:flex-row gap-2 w-full mt-3",
                ),
                rx.cond(
                    step["ui_hint"] != "",
                    rx.el.div(
                        rx.icon(
                            "mouse-pointer-click",
                            class_name="h-3.5 w-3.5 text-emerald-300 shrink-0",
                        ),
                        rx.el.p(
                            step["ui_hint"],
                            class_name="text-[11px] font-medium text-emerald-100/60",
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
                            class_name="h-3.5 w-3.5 text-lime-300 shrink-0",
                        ),
                        rx.el.p(
                            step["why"],
                            class_name="text-[11px] font-medium text-lime-100/80",
                        ),
                        class_name="flex items-start gap-2 rounded-xl border border-lime-300/20 bg-lime-300/[0.06] px-3 py-2 w-full mt-2",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    step["warning"] != "",
                    rx.el.div(
                        rx.icon(
                            "triangle-alert",
                            class_name="h-3.5 w-3.5 text-amber-300 shrink-0",
                        ),
                        rx.el.p(
                            step["warning"],
                            class_name="text-[11px] font-medium text-amber-100/85",
                        ),
                        class_name="flex items-start gap-2 rounded-xl border border-amber-300/25 bg-amber-300/[0.07] px-3 py-2 w-full mt-2",
                    ),
                    rx.fragment(),
                ),
                rx.el.div(
                    rx.cond(
                        step["field_reference"] != "",
                        rx.el.span(
                            step["field_reference"],
                            class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-mono text-emerald-100/50 w-fit",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        step["module_route"] != "",
                        rx.el.a(
                            rx.el.span("Ouvrir l'écran"),
                            rx.icon("arrow-up-right", class_name="h-3 w-3"),
                            href=step["module_route"],
                            class_name="flex items-center gap-1.5 rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1 text-[10px] font-semibold text-lime-200 hover:bg-lime-300/20 transition-colors w-fit ml-auto",
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
            "w-full rounded-2xl border border-lime-300/30 bg-lime-300/[0.05] p-4",
            "w-full rounded-2xl border border-white/10 bg-white/[0.02] p-4",
        ),
    )


def _procedure_runner() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Procédure interactive",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-amber-300/80",
                ),
                rx.el.h4(
                    GuideState.open_procedure["title"],
                    class_name="font-['Instrument_Serif'] text-2xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    GuideState.open_procedure["objective"],
                    class_name="text-sm font-medium text-emerald-100/60 mt-2 max-w-2xl",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.button(
                rx.icon("x", class_name="h-3.5 w-3.5"),
                rx.el.span("Fermer"),
                on_click=GuideState.close_procedure,
                class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] font-semibold text-emerald-100/65 hover:text-emerald-50 hover:border-lime-300/30 transition-colors w-fit",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3 w-full",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("target", class_name="h-3.5 w-3.5 text-lime-300/80"),
                rx.el.p(
                    GuideState.open_procedure["expected_result"],
                    class_name="text-[11px] font-medium text-emerald-100/60",
                ),
                class_name="flex items-start gap-2 flex-1 min-w-0 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2",
            ),
            rx.el.div(
                rx.icon(
                    "map-pin", class_name="h-3.5 w-3.5 text-emerald-300/80"
                ),
                rx.el.p(
                    GuideState.open_procedure["context"],
                    class_name="text-[11px] font-medium text-emerald-100/60",
                ),
                class_name="flex items-start gap-2 flex-1 min-w-0 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2",
            ),
            class_name="flex flex-col lg:flex-row gap-2 w-full mt-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    f"{GuideState.done_steps.length()} / {GuideState.procedure_steps.length()} étape(s) validée(s)",
                    class_name="text-[11px] font-semibold text-emerald-100/60",
                ),
                rx.el.span(
                    GuideState.step_progress_width,
                    class_name="text-[11px] font-bold text-lime-200 ml-auto",
                ),
                class_name="flex items-center gap-2 w-full",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="h-full rounded-full bg-gradient-to-r from-emerald-400 to-lime-300",
                    style={"width": GuideState.step_progress_width},
                ),
                class_name="h-1.5 w-full rounded-full bg-white/10 mt-2",
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
        class_name="w-full rounded-3xl border border-amber-300/25 bg-[#04140d]/70 p-5 mt-4",
    )


def _article_reader() -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.span(
                GuideState.active_article["category_name"],
                class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-lime-200 w-fit",
            ),
            rx.el.span(
                GuideState.active_article["status_label"],
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-semibold text-emerald-100/55 w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.el.h3(
            GuideState.active_article["title"],
            class_name="font-['Instrument_Serif'] text-3xl md:text-4xl leading-tight text-emerald-50 mt-3",
        ),
        rx.el.p(
            GuideState.active_article["subtitle"],
            class_name="text-sm font-medium text-emerald-100/55 mt-2",
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
            rx.icon("quote", class_name="h-4 w-4 text-lime-300/70 shrink-0"),
            rx.el.p(
                GuideState.active_article["summary"],
                class_name="text-sm font-medium text-emerald-50/85 leading-relaxed",
            ),
            class_name="flex items-start gap-3 rounded-2xl border border-lime-300/20 bg-lime-300/[0.05] p-4 w-full mt-5",
        ),
        rx.el.div(
            _reading_block(
                "Lecture agricole",
                "Vocabulaire de terrain",
                "tractor",
                GuideState.farmer_paragraphs,
                "h-1 w-full rounded-full bg-lime-300/70",
            ),
            _reading_block(
                "Lecture AgriPro",
                "Vocabulaire technique & données",
                "database",
                GuideState.pro_paragraphs,
                "h-1 w-full rounded-full bg-amber-300/70",
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
                        class_name="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-semibold text-emerald-100/55 w-fit",
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
                    rx.icon("link", class_name="h-3.5 w-3.5 text-lime-300/80"),
                    rx.el.span(
                        "Liens directs vers les modules",
                        class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-emerald-100/45",
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
                class_name="w-full mt-6 border-t border-white/10 pt-5",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("play", class_name="h-4 w-4 text-[#04140d]"),
                rx.el.span(
                    "Comment faire dans AgriPro ?",
                    class_name="text-[#04140d]",
                ),
                on_click=GuideState.open_related_procedures,
                class_name="flex items-center gap-2 rounded-full bg-lime-300 px-4 py-2 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
            ),
            rx.el.span(
                f"{GuideState.related_procedures.length()} procédure(s) · {GuideState.related_scope_label}",
                class_name="text-[11px] font-medium text-emerald-100/50",
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
        class_name="w-full flex-1 min-w-0 rounded-3xl border border-white/10 bg-white/[0.03] p-6 md:p-8 backdrop-blur-xl",
    )


def guide_library() -> rx.Component:
    return rx.el.div(
        _article_list(),
        rx.cond(
            GuideState.has_article,
            _article_reader(),
            rx.el.div(
                rx.icon("book-open", class_name="h-7 w-7 text-lime-300"),
                rx.el.h3(
                    "Choisissez un article",
                    class_name="font-['Instrument_Serif'] text-2xl text-emerald-50 mt-3",
                ),
                rx.el.p(
                    "Chaque fiche propose une double lecture : agricole pour le terrain, AgriPro pour la donnée.",
                    class_name="text-sm font-medium text-emerald-100/55 mt-2 text-center max-w-md",
                ),
                class_name="flex flex-col items-center justify-center flex-1 min-w-0 rounded-3xl border border-white/10 bg-white/[0.03] py-20 px-6 backdrop-blur-xl",
            ),
        ),
        class_name="flex flex-col xl:flex-row gap-4 w-full",
    )

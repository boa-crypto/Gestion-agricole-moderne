import reflex as rx

from app.components.guide_help import help_button
from app.states.guide_state import GuideState, SearchGroup, SearchHit


def _stat(label: str, value: rx.Var | int, unit: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="font-['Instrument_Serif'] text-2xl leading-none text-emerald-50",
            ),
            rx.el.span(
                unit,
                class_name="text-[11px] font-medium text-emerald-100/50 mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-2",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3",
    )


def _hit(hit: SearchHit, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.icon(hit["icon"], class_name="h-4 w-4 text-lime-300"),
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-lime-300/25 bg-lime-300/10",
        ),
        rx.el.div(
            rx.el.p(
                hit["title"],
                class_name="text-sm font-semibold text-emerald-50 text-left truncate",
            ),
            rx.el.p(
                hit["subtitle"],
                class_name="text-[11px] font-medium text-emerald-100/50 text-left truncate mt-0.5",
            ),
            rx.el.p(
                hit["excerpt"],
                class_name="text-[11px] font-medium text-emerald-100/45 text-left leading-relaxed mt-1.5",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.icon(
            "arrow-up-right",
            class_name="h-3.5 w-3.5 text-emerald-100/40 shrink-0",
        ),
        on_click=GuideState.open_hit(hit["kind"], hit["ref"]),
        key=key,
        class_name="flex items-start gap-3 w-full rounded-2xl border border-white/10 bg-white/[0.03] p-3 hover:border-lime-300/30 hover:bg-white/[0.06] transition-colors text-left",
    )


def _group(group: SearchGroup, key: str = "") -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.icon(group["icon"], class_name="h-3.5 w-3.5 text-lime-300/80"),
            rx.el.span(
                group["label"],
                class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-emerald-100/50",
            ),
            rx.el.span(
                group["count"],
                class_name="rounded-full bg-lime-300/15 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.div(
            rx.foreach(group["hits"], lambda h: _hit(h, key=h["key"])),
            class_name="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-2 w-full mt-3",
        ),
        key=key,
        class_name="w-full",
    )


def _search_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("radar", class_name="h-3.5 w-3.5 text-lime-300"),
                rx.el.span(
                    f"{GuideState.search_total} résultat(s) groupé(s) par type",
                    class_name="text-[11px] font-semibold text-emerald-100/65",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.button(
                rx.icon("x", class_name="h-3.5 w-3.5"),
                rx.el.span("Effacer"),
                on_click=GuideState.clear_query,
                class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/65 hover:text-emerald-50 hover:border-lime-300/30 transition-colors w-fit ml-auto",
            ),
            class_name="flex items-center gap-2 w-full",
        ),
        rx.cond(
            GuideState.search_total > 0,
            rx.el.div(
                rx.foreach(
                    GuideState.search_groups,
                    lambda g: _group(g, key=g["kind"]),
                ),
                class_name="flex flex-col gap-5 w-full mt-4",
            ),
            rx.el.div(
                rx.icon("search-x", class_name="h-6 w-6 text-amber-300"),
                rx.el.p(
                    "Aucun contenu du guide ne correspond à cette recherche.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-2 text-center",
                ),
                class_name="flex flex-col items-center justify-center py-10 w-full",
            ),
        ),
        class_name="w-full rounded-3xl border border-lime-300/20 bg-[#03110b]/70 p-5 mt-4 backdrop-blur-xl",
    )


def guide_hero() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("book-open", class_name="h-4 w-4 text-lime-300"),
                    rx.el.span(
                        "Bibliothèque embarquée",
                        class_name="text-[11px] font-semibold uppercase tracking-[0.32em] text-lime-300/90",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "Guide Agricole AgriPro",
                    class_name="font-['Instrument_Serif'] text-4xl md:text-5xl leading-[1.05] text-emerald-50 mt-3",
                ),
                rx.el.p(
                    "Comprendre l'agriculture et maîtriser AgriPro, du geste au terrain jusqu'à la donnée dans l'application.",
                    class_name="text-base font-medium text-emerald-100/70 mt-3 max-w-2xl",
                ),
                rx.el.div(
                    rx.el.span(
                        GuideState.current_version["version_label"],
                        class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-3 py-1 text-[11px] font-bold text-lime-200 w-fit",
                    ),
                    rx.el.span(
                        GuideState.current_version["status_label"],
                        class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-medium text-emerald-100/60 w-fit",
                    ),
                    rx.el.span(
                        f"Publié le {GuideState.current_version['published_label']}",
                        class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-medium text-emerald-100/60 w-fit",
                    ),
                    rx.el.span(
                        GuideState.today_label,
                        class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-medium text-emerald-100/60 w-fit",
                    ),
                    class_name="flex flex-wrap items-center gap-2 mt-5",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                help_button("guide", "Aide embarquée"),
                rx.el.button(
                    rx.cond(
                        GuideState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#04140d]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#04140d]"
                        ),
                    ),
                    rx.el.span("Actualiser", class_name="text-[#04140d]"),
                    on_click=GuideState.load_guide,
                    class_name="flex items-center gap-2 rounded-full bg-lime-300 px-4 py-2 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-start gap-2 lg:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-start justify-between gap-6 w-full",
        ),
        rx.el.div(
            _stat("Articles", GuideState.totals["articles"], "publiés"),
            _stat("Procédures", GuideState.totals["procedures"], "pas à pas"),
            _stat("Dictionnaire", GuideState.totals["terms"], "entrées"),
            _stat("Questions", GuideState.totals["faq"], "réponses"),
            _stat("Règles", GuideState.totals["rules"], "garde-fous"),
            _stat("Parcours", GuideState.totals["paths"], "guidés"),
            class_name="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3 w-full mt-7",
        ),
        rx.el.div(
            rx.el.div(
                class_name="pointer-events-none absolute -inset-0.5 rounded-2xl bg-gradient-to-r from-lime-300/25 via-emerald-400/10 to-amber-300/20 blur-md",
            ),
            rx.el.div(
                rx.icon(
                    "search",
                    class_name="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-lime-300 pointer-events-none",
                ),
                rx.el.input(
                    placeholder="Rechercher un article, une procédure, un terme, une question, une règle, un parcours…",
                    default_value=GuideState.query,
                    on_change=GuideState.set_query.debounce(400),
                    class_name="w-full rounded-2xl border border-lime-300/25 bg-[#03110b]/90 py-4 pl-12 pr-28 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/60 focus:ring-2 focus:ring-lime-300/25 outline-hidden transition-colors",
                ),
                rx.el.span(
                    "Recherche globale",
                    class_name="absolute right-4 top-1/2 -translate-y-1/2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-100/50",
                ),
                class_name="relative w-full",
            ),
            class_name="relative w-full mt-7",
        ),
        rx.cond(GuideState.has_search, _search_panel(), rx.fragment()),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 md:p-8 backdrop-blur-xl",
    )

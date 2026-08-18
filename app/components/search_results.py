import reflex as rx

from app.states.search_state import SearchHit, SearchSection, SearchState


def _tone_ring(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        (
            "vegetal",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-lime-300/30 bg-lime-300/10",
        ),
        (
            "operations",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-amber-300/30 bg-amber-300/10",
        ),
        (
            "humain",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-sky-300/30 bg-sky-300/10",
        ),
        (
            "flotte",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-emerald-300/30 bg-emerald-300/10",
        ),
        (
            "alerte",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-red-400/30 bg-red-500/10",
        ),
        "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/[0.05]",
    )


def _tone_icon(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        ("vegetal", "h-4 w-4 text-lime-300"),
        ("operations", "h-4 w-4 text-amber-300"),
        ("humain", "h-4 w-4 text-sky-300"),
        ("flotte", "h-4 w-4 text-emerald-300"),
        ("alerte", "h-4 w-4 text-red-300"),
        "h-4 w-4 text-emerald-100/60",
    )


def _tone_accent(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        ("vegetal", "h-1 w-full rounded-full bg-lime-300/70"),
        ("operations", "h-1 w-full rounded-full bg-amber-300/70"),
        ("humain", "h-1 w-full rounded-full bg-sky-300/70"),
        ("flotte", "h-1 w-full rounded-full bg-emerald-300/70"),
        ("alerte", "h-1 w-full rounded-full bg-red-400/70"),
        "h-1 w-full rounded-full bg-white/20",
    )


def _badge(label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name="rounded-full border border-white/10 bg-white/[0.05] px-2 py-0.5 text-[10px] font-semibold text-emerald-100/65 w-fit whitespace-nowrap",
    )


def _hit_card(hit: SearchHit, key: str = "") -> rx.Component:
    return rx.el.article(
        rx.el.div(class_name=_tone_accent(hit["tone"])),
        rx.el.div(
            rx.el.div(
                rx.icon(hit["icon"], class_name=_tone_icon(hit["tone"])),
                class_name=_tone_ring(hit["tone"]),
            ),
            rx.el.div(
                rx.el.p(
                    hit["title"],
                    class_name="text-sm font-semibold text-emerald-50 truncate",
                ),
                rx.el.div(
                    rx.icon(
                        "corner-down-right",
                        class_name="h-3 w-3 text-emerald-100/35",
                    ),
                    rx.el.span(
                        hit["subtitle"],
                        class_name="text-[11px] font-medium text-emerald-100/55 truncate",
                    ),
                    class_name="flex items-center gap-1.5 min-w-0 mt-1",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                hit["kind_label"],
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-100/45 w-fit whitespace-nowrap",
            ),
            class_name="flex items-start gap-3 w-full mt-4",
        ),
        rx.cond(
            hit["badges"].length() > 0,
            rx.el.div(
                rx.foreach(hit["badges"], _badge),
                class_name="flex flex-wrap items-center gap-2 mt-3",
            ),
            rx.fragment(),
        ),
        rx.el.p(
            hit["excerpt"],
            class_name="text-[11px] font-medium text-emerald-100/55 leading-relaxed mt-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "calendar-days", class_name="h-3.5 w-3.5 text-lime-300/70"
                ),
                rx.el.span(
                    f"{hit['date_kind']} · {hit['date_label']}",
                    class_name="text-[11px] font-medium text-emerald-100/60 whitespace-nowrap",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.a(
                rx.el.span(hit["href_label"]),
                rx.icon("arrow-up-right", class_name="h-3.5 w-3.5"),
                href=hit["href"],
                class_name="flex items-center gap-1.5 rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1 text-[11px] font-semibold text-lime-200 hover:bg-lime-300/20 transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-4 pt-3 border-t border-white/5",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:border-lime-300/25 transition-colors",
    )


def _section(section: SearchSection, key: str = "") -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    section["icon"], class_name=_tone_icon(section["tone"])
                ),
                class_name=_tone_ring(section["tone"]),
            ),
            rx.el.div(
                rx.el.h3(
                    section["label"],
                    class_name="font-['Instrument_Serif'] text-2xl text-emerald-50",
                ),
                rx.el.p(
                    f"Date pertinente : {section['date_kind'].lower()}",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/40 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{section['count']} instance(s)",
                    class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/65 w-fit",
                ),
                rx.cond(
                    section["truncated"],
                    rx.el.span(
                        f"{section['shown']} affichées",
                        class_name="rounded-full border border-amber-300/30 bg-amber-300/10 px-3 py-1 text-[11px] font-semibold text-amber-200 w-fit",
                    ),
                    rx.fragment(),
                ),
                rx.el.a(
                    rx.el.span(section["href_label"]),
                    rx.icon("arrow-right", class_name="h-3.5 w-3.5"),
                    href=section["href"],
                    class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.foreach(
                section["hits"], lambda hit: _hit_card(hit, key=hit["key"])
            ),
            class_name="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-3 w-full mt-5",
        ),
        key=key,
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )


def _skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="animate-pulse h-8 w-56 rounded-xl bg-white/[0.06]"
        ),
        rx.el.div(
            rx.el.div(
                class_name="animate-pulse h-40 rounded-2xl bg-white/[0.05]"
            ),
            rx.el.div(
                class_name="animate-pulse h-40 rounded-2xl bg-white/[0.05]"
            ),
            rx.el.div(
                class_name="animate-pulse h-40 rounded-2xl bg-white/[0.05]"
            ),
            class_name="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-3 w-full mt-5",
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )


def _empty() -> rx.Component:
    return rx.el.div(
        rx.icon("search-x", class_name="h-7 w-7 text-amber-300"),
        rx.el.h3(
            "Aucune instance retrouvée",
            class_name="font-['Instrument_Serif'] text-2xl text-emerald-50 mt-3",
        ),
        rx.el.p(
            "Élargissez la fenêtre de dates, changez de mot-clé ou réinitialisez le périmètre pour balayer à nouveau l'ensemble des tables métier.",
            class_name="text-sm font-medium text-emerald-100/55 mt-2 max-w-xl text-center",
        ),
        rx.el.div(
            rx.el.span(
                SearchState.term_label,
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-medium text-emerald-100/55 w-fit",
            ),
            rx.el.span(
                SearchState.range_label,
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-medium text-emerald-100/55 w-fit",
            ),
            rx.el.span(
                SearchState.scope_label,
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-medium text-emerald-100/55 w-fit",
            ),
            class_name="flex flex-wrap items-center justify-center gap-2 mt-5",
        ),
        rx.el.button(
            rx.icon("rotate-ccw", class_name="h-4 w-4 text-[#04140d]"),
            rx.el.span(
                "Réinitialiser la recherche", class_name="text-[#04140d]"
            ),
            on_click=SearchState.reset_search,
            class_name="flex items-center gap-2 rounded-full bg-lime-300 px-4 py-2 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit mt-6",
        ),
        class_name="flex flex-col items-center justify-center w-full rounded-3xl border border-white/10 bg-white/[0.03] py-16 px-6 backdrop-blur-xl",
    )


def search_results() -> rx.Component:
    return rx.el.div(
        rx.cond(
            SearchState.is_loading,
            rx.el.div(
                _skeleton(),
                _skeleton(),
                class_name="flex flex-col gap-4 w-full",
            ),
            rx.cond(
                SearchState.error != "",
                rx.el.div(
                    rx.icon("octagon-alert", class_name="h-7 w-7 text-red-300"),
                    rx.el.h3(
                        "Recherche interrompue",
                        class_name="font-['Instrument_Serif'] text-2xl text-emerald-50 mt-3",
                    ),
                    rx.el.p(
                        SearchState.error,
                        class_name="text-sm font-medium text-red-200/80 mt-2 text-center max-w-lg",
                    ),
                    class_name="flex flex-col items-center justify-center w-full rounded-3xl border border-red-400/25 bg-red-500/[0.06] py-16 px-6 backdrop-blur-xl",
                ),
                rx.cond(
                    SearchState.has_results,
                    rx.el.div(
                        rx.foreach(
                            SearchState.sections,
                            lambda section: _section(
                                section, key=section["kind"]
                            ),
                        ),
                        class_name="flex flex-col gap-4 w-full",
                    ),
                    _empty(),
                ),
            ),
        ),
        class_name="w-full",
    )

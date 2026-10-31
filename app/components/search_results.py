import reflex as rx

from app.states.search_state import SearchHit, SearchSection, SearchState


def _tone_ring(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        (
            "vegetal",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10",
        ),
        (
            "operations",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10",
        ),
        (
            "humain",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#9cc3ff]/30 bg-[#9cc3ff]/10",
        ),
        (
            "flotte",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#a9c98b]/30 bg-[#a9c98b]/10",
        ),
        (
            "alerte",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10",
        ),
        "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#16190f]",
    )


def _tone_icon(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        ("vegetal", "h-4 w-4 text-[#d8fa5e]"),
        ("operations", "h-4 w-4 text-[#ff8a5b]"),
        ("humain", "h-4 w-4 text-[#9cc3ff]"),
        ("flotte", "h-4 w-4 text-[#a9c98b]"),
        ("alerte", "h-4 w-4 text-[#ff9b8c]"),
        "h-4 w-4 text-[#c9c5b4]/60",
    )


def _tone_accent(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        ("vegetal", "h-1 w-full rounded-none bg-[#d8fa5e]/70"),
        ("operations", "h-1 w-full rounded-none bg-[#ff8a5b]/70"),
        ("humain", "h-1 w-full rounded-none bg-[#9cc3ff]/70"),
        ("flotte", "h-1 w-full rounded-none bg-[#a9c98b]/70"),
        ("alerte", "h-1 w-full rounded-none bg-[#ff6b5a]/70"),
        "h-1 w-full rounded-none bg-[#2c3123]",
    )


def _badge(label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name="rounded-none border border-[#f2efe4]/12 bg-[#16190f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/65 w-fit whitespace-nowrap",
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
                    class_name="text-sm font-semibold text-[#f2efe4] truncate",
                ),
                rx.el.div(
                    rx.icon(
                        "corner-down-right",
                        class_name="h-3 w-3 text-[#c9c5b4]/35",
                    ),
                    rx.el.span(
                        hit["subtitle"],
                        class_name="text-[11px] font-medium text-[#c9c5b4]/55 truncate",
                    ),
                    class_name="flex items-center gap-1.5 min-w-0 mt-1",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                hit["kind_label"],
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 ap-eyebrow text-[#c9c5b4]/45 w-fit whitespace-nowrap",
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
            class_name="text-[11px] font-medium text-[#c9c5b4]/55 leading-relaxed mt-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "calendar-days", class_name="h-3.5 w-3.5 text-[#d8fa5e]/70"
                ),
                rx.el.span(
                    f"{hit['date_kind']} · {hit['date_label']}",
                    class_name="text-[11px] font-medium text-[#c9c5b4]/60 whitespace-nowrap",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.a(
                rx.el.span(hit["href_label"]),
                rx.icon("arrow-up-right", class_name="h-3.5 w-3.5"),
                href=hit["href"],
                class_name="flex items-center gap-1.5 rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10 px-3 py-1 text-[11px] font-semibold text-[#e4ff9b] hover:bg-[#d8fa5e]/20 transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-4 pt-3 border-t border-[#f2efe4]/8",
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 hover:border-[#d8fa5e]/25 transition-colors",
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
                    class_name="ap-serif text-2xl text-[#f2efe4]",
                ),
                rx.el.p(
                    f"Date pertinente : {section['date_kind'].lower()}",
                    class_name="ap-eyebrow text-[#c9c5b4]/40 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{section['count']} instance(s)",
                    class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/65 w-fit",
                ),
                rx.cond(
                    section["truncated"],
                    rx.el.span(
                        f"{section['shown']} affichées",
                        class_name="rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-3 py-1 text-[11px] font-semibold text-[#ffb894] w-fit",
                    ),
                    rx.fragment(),
                ),
                rx.el.a(
                    rx.el.span(section["href_label"]),
                    rx.icon("arrow-right", class_name="h-3.5 w-3.5"),
                    href=section["href"],
                    class_name="flex items-center gap-1.5 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/70 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit",
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
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )


def _skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="animate-pulse h-8 w-56 rounded-none bg-[#191c13]"
        ),
        rx.el.div(
            rx.el.div(
                class_name="animate-pulse h-40 rounded-none bg-[#16190f]"
            ),
            rx.el.div(
                class_name="animate-pulse h-40 rounded-none bg-[#16190f]"
            ),
            rx.el.div(
                class_name="animate-pulse h-40 rounded-none bg-[#16190f]"
            ),
            class_name="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-3 w-full mt-5",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )


def _empty() -> rx.Component:
    return rx.el.div(
        rx.icon("search-x", class_name="h-7 w-7 text-[#ff8a5b]"),
        rx.el.h3(
            "Aucune instance retrouvée",
            class_name="ap-serif text-2xl text-[#f2efe4] mt-3",
        ),
        rx.el.p(
            "Élargissez la fenêtre de dates, changez de mot-clé ou réinitialisez le périmètre pour balayer à nouveau l'ensemble des tables métier.",
            class_name="text-sm font-medium text-[#c9c5b4]/55 mt-2 max-w-xl text-center",
        ),
        rx.el.div(
            rx.el.span(
                SearchState.term_label,
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-medium text-[#c9c5b4]/55 w-fit",
            ),
            rx.el.span(
                SearchState.range_label,
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-medium text-[#c9c5b4]/55 w-fit",
            ),
            rx.el.span(
                SearchState.scope_label,
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-medium text-[#c9c5b4]/55 w-fit",
            ),
            class_name="flex flex-wrap items-center justify-center gap-2 mt-5",
        ),
        rx.el.button(
            rx.icon("rotate-ccw", class_name="h-4 w-4 text-[#0A0A08]"),
            rx.el.span(
                "Réinitialiser la recherche", class_name="text-[#0A0A08]"
            ),
            on_click=SearchState.reset_search,
            class_name="ap-mono inline-flex w-fit items-center gap-2 bg-[#D8FA5E] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[#0A0A08] transition-colors hover:bg-[#E4FF9B] mt-6",
        ),
        class_name="flex flex-col items-center justify-center w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] py-16 px-6 ",
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
                    rx.icon("octagon-alert", class_name="h-7 w-7 text-[#ff9b8c]"),
                    rx.el.h3(
                        "Recherche interrompue",
                        class_name="ap-serif text-2xl text-[#f2efe4] mt-3",
                    ),
                    rx.el.p(
                        SearchState.error,
                        class_name="text-sm font-medium text-[#ffbcb0]/80 mt-2 text-center max-w-lg",
                    ),
                    class_name="flex flex-col items-center justify-center w-full rounded-none border border-[#ff6b5a]/25 bg-[#f2452c]/[0.06] py-16 px-6 ",
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

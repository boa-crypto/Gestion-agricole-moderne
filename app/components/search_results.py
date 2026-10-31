import reflex as rx

from app.components.design import skeleton_rows

from app.states.search_state import SearchHit, SearchSection, SearchState


def _tone_ring(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        (
            "vegetal",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)]",
        ),
        (
            "operations",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)]",
        ),
        (
            "humain",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-info-rgb)/0.30)] bg-[rgb(var(--ap-info-rgb)/0.10)]",
        ),
        (
            "flotte",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-sage-rgb)/0.30)] bg-[rgb(var(--ap-sage-rgb)/0.10)]",
        ),
        (
            "alerte",
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-danger-rgb)/0.30)] bg-[rgb(var(--ap-flame-strong-rgb)/0.10)]",
        ),
        "flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-muted-rgb))]",
    )


def _tone_icon(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        ("vegetal", "h-4 w-4 text-[rgb(var(--ap-accent-rgb))]"),
        ("operations", "h-4 w-4 text-[rgb(var(--ap-flame-soft-rgb))]"),
        ("humain", "h-4 w-4 text-[rgb(var(--ap-info-rgb))]"),
        ("flotte", "h-4 w-4 text-[rgb(var(--ap-sage-rgb))]"),
        ("alerte", "h-4 w-4 text-[rgb(var(--ap-danger-soft-rgb))]"),
        "h-4 w-4 text-[rgb(var(--ap-paper-muted-rgb)/0.82)]",
    )


def _tone_accent(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        ("vegetal", "h-1 w-full rounded-none bg-[rgb(var(--ap-accent-rgb)/0.70)]"),
        ("operations", "h-1 w-full rounded-none bg-[rgb(var(--ap-flame-soft-rgb)/0.70)]"),
        ("humain", "h-1 w-full rounded-none bg-[rgb(var(--ap-info-rgb)/0.70)]"),
        ("flotte", "h-1 w-full rounded-none bg-[rgb(var(--ap-sage-rgb)/0.70)]"),
        ("alerte", "h-1 w-full rounded-none bg-[rgb(var(--ap-danger-rgb)/0.70)]"),
        "h-1 w-full rounded-none bg-[rgb(var(--ap-track-soft-rgb))]",
    )


def _badge(label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-muted-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit whitespace-nowrap",
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
                    class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
                ),
                rx.el.div(
                    rx.icon(
                        "corner-down-right",
                        class_name="h-3 w-3 text-[rgb(var(--ap-paper-muted-rgb)/0.82)]",
                    ),
                    rx.el.span(
                        hit["subtitle"],
                        class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] truncate",
                    ),
                    class_name="flex items-center gap-1.5 min-w-0 mt-1",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                hit["kind_label"],
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit whitespace-nowrap",
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
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] leading-relaxed mt-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "calendar-days", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb)/0.70)]"
                ),
                rx.el.span(
                    f"{hit['date_kind']} · {hit['date_label']}",
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] whitespace-nowrap",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.a(
                rx.el.span(hit["href_label"]),
                rx.icon("arrow-up-right", class_name="h-3.5 w-3.5"),
                href=hit["href"],
                class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-accent-soft-rgb))] hover:bg-[rgb(var(--ap-accent-rgb)/0.20)] transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-4 pt-3 border-t border-[rgb(var(--ap-paper-rgb)/0.12)]",
        ),
        key=key,
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-4 hover:border-t-[rgb(var(--ap-accent-rgb)/0.40)] transition-colors",
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
                    class_name="ap-serif text-2xl text-[rgb(var(--ap-paper-rgb))]",
                ),
                rx.el.p(
                    f"Date pertinente : {section['date_kind'].lower()}",
                    class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{section['count']} instance(s)",
                    class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit",
                ),
                rx.cond(
                    section["truncated"],
                    rx.el.span(
                        f"{section['shown']} affichées",
                        class_name="rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
                    ),
                    rx.fragment(),
                ),
                rx.el.a(
                    rx.el.span(section["href_label"]),
                    rx.icon("arrow-right", class_name="h-3.5 w-3.5"),
                    href=section["href"],
                    class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.90)] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] hover:text-[rgb(var(--ap-paper-rgb))] transition-colors w-fit",
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
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )


def _skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="ap-skeleton bg-[rgb(var(--ap-surface-high-rgb)/0.70)] h-8 w-56"
        ),
        rx.el.div(skeleton_rows(3), class_name="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-3 w-full mt-5"),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )


def _empty() -> rx.Component:
    return rx.el.div(
        rx.icon("search-x", class_name="h-7 w-7 text-[rgb(var(--ap-flame-soft-rgb))]"),
        rx.el.h3(
            "Aucune instance retrouvée",
            class_name="ap-serif text-2xl text-[rgb(var(--ap-paper-rgb))] mt-3",
        ),
        rx.el.p(
            "Élargissez la fenêtre de dates, changez de mot-clé ou réinitialisez le périmètre pour balayer à nouveau l'ensemble des tables métier.",
            class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] mt-2 max-w-xl text-center",
        ),
        rx.el.div(
            rx.el.span(
                SearchState.term_label,
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] w-fit",
            ),
            rx.el.span(
                SearchState.range_label,
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] w-fit",
            ),
            rx.el.span(
                SearchState.scope_label,
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] w-fit",
            ),
            class_name="flex flex-wrap items-center justify-center gap-2 mt-5",
        ),
        rx.el.button(
            rx.icon("rotate-ccw", class_name="h-4 w-4 text-[rgb(var(--ap-ink-rgb))]"),
            rx.el.span(
                "Réinitialiser la recherche", class_name="text-[rgb(var(--ap-ink-rgb))]"
            ),
            on_click=SearchState.reset_search,
            class_name="ap-mono inline-flex w-fit items-center gap-2 bg-[rgb(var(--ap-accent-rgb))] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[rgb(var(--ap-ink-rgb))] transition-colors hover:bg-[rgb(var(--ap-accent-soft-rgb))] mt-6",
        ),
        class_name="flex flex-col items-center justify-center w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] py-16 px-6 ",
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
                    rx.icon("octagon-alert", class_name="h-7 w-7 text-[rgb(var(--ap-danger-soft-rgb))]"),
                    rx.el.h3(
                        "Recherche interrompue",
                        class_name="ap-serif text-2xl text-[rgb(var(--ap-paper-rgb))] mt-3",
                    ),
                    rx.el.p(
                        SearchState.error,
                        class_name="text-sm font-medium text-[rgb(var(--ap-warm-150-rgb)/0.80)] mt-2 text-center max-w-lg",
                    ),
                    class_name="flex flex-col items-center justify-center w-full rounded-none border border-[rgb(var(--ap-danger-rgb)/0.25)] bg-[rgb(var(--ap-flame-strong-rgb))]/[0.06] py-16 px-6 ",
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

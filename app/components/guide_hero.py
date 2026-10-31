import reflex as rx

from app.components.design import (
    empty_state,
    meta_ledger,
    meta_row,
    page_hero,
    stat,
)
from app.components.guide_help import help_button
from app.states.guide_state import GuideState, SearchGroup, SearchHit


def _hit(hit: SearchHit, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.icon(hit["icon"], class_name="h-4 w-4 text-[rgb(var(--ap-accent-rgb))]"),
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)]",
        ),
        rx.el.div(
            rx.el.p(
                hit["title"],
                class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] text-left truncate",
            ),
            rx.el.p(
                hit["subtitle"],
                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] text-left truncate mt-0.5",
            ),
            rx.el.p(
                hit["excerpt"],
                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] text-left leading-relaxed mt-1.5",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.icon(
            "arrow-up-right",
            class_name="h-3.5 w-3.5 text-[rgb(var(--ap-paper-muted-rgb)/0.86)] shrink-0",
        ),
        on_click=GuideState.open_hit(hit["kind"], hit["ref"]),
        key=key,
        class_name="flex items-start gap-3 w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] p-3 hover:border-[rgb(var(--ap-accent-rgb)/0.30)] hover:bg-[rgb(var(--ap-surface-high-rgb))] transition-colors text-left",
    )


def _group(group: SearchGroup, key: str = "") -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.icon(group["icon"], class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb)/0.80)]"),
            rx.el.span(
                group["label"],
                class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            rx.el.span(
                group["count"],
                class_name="rounded-none bg-[rgb(var(--ap-accent-rgb)/0.15)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
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
                rx.icon("radar", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb))]"),
                rx.el.span(
                    f"{GuideState.search_total} résultat(s) groupé(s) par type",
                    class_name="text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.button(
                rx.icon("x", class_name="h-3.5 w-3.5"),
                rx.el.span("Effacer"),
                on_click=GuideState.clear_query,
                class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] hover:text-[rgb(var(--ap-paper-rgb))] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] transition-colors w-fit ml-auto",
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
            empty_state(
                "search-x",
                "Aucun contenu du guide ne correspond à cette recherche.",
            ),
        ),
        class_name="w-full border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-5 mt-6",
    )


def guide_metrics() -> rx.Component:
    return rx.el.div(
        stat(
            "Articles",
            GuideState.totals["articles"].to_string(),
            "publiés",
            index="01",
        ),
        stat(
            "Procédures",
            GuideState.totals["procedures"].to_string(),
            "pas à pas",
            index="02",
        ),
        stat(
            "Dictionnaire",
            GuideState.totals["terms"].to_string(),
            "entrées",
            index="03",
        ),
        stat(
            "Questions",
            GuideState.totals["faq"].to_string(),
            "réponses",
            index="04",
        ),
        stat(
            "Règles",
            GuideState.totals["rules"].to_string(),
            "garde-fous",
            index="05",
        ),
        stat(
            "Parcours",
            GuideState.totals["paths"].to_string(),
            "guidés",
            index="06",
        ),
        class_name=(
            "grid grid-cols-2 gap-x-6 gap-y-8 sm:grid-cols-3 xl:grid-cols-6 "
            "xl:gap-x-8 mt-10"
        ),
    )


def _refresh() -> rx.Component:
    return rx.el.button(
        rx.cond(
            GuideState.is_loading,
            rx.icon("loader-circle", class_name="h-3.5 w-3.5 animate-spin"),
            rx.icon("refresh-cw", class_name="h-3.5 w-3.5"),
        ),
        rx.el.span("Actualiser"),
        type="button",
        on_click=GuideState.load_guide,
        disabled=GuideState.is_loading,
        class_name=(
            "ap-mono inline-flex w-fit items-center justify-center gap-2 border "
            "border-[rgb(var(--ap-accent-rgb))] bg-[rgb(var(--ap-accent-rgb))] px-3.5 py-2.5 text-[10px] uppercase "
            "tracking-[0.18em] text-[rgb(var(--ap-ink-rgb))] transition-colors "
            "hover:border-[rgb(var(--ap-accent-soft-rgb))] hover:bg-[rgb(var(--ap-accent-soft-rgb))] "
            "disabled:cursor-not-allowed disabled:opacity-45"
        ),
    )


def _search_field() -> rx.Component:
    return rx.el.div(
        rx.icon(
            "search",
            class_name=(
                "pointer-events-none absolute left-0 top-1/2 h-4 w-4 "
                "-translate-y-1/2 text-[rgb(var(--ap-paper-muted-rgb)/0.86)]"
            ),
        ),
        rx.el.input(
            placeholder=(
                "Rechercher un article, une procédure, un terme, une question, "
                "une règle, un parcours…"
            ),
            default_value=GuideState.query,
            on_change=GuideState.set_query.debounce(400),
            class_name=(
                "w-full border-b border-[rgb(var(--ap-paper-rgb)/0.24)] bg-transparent py-3.5 pl-7 "
                "pr-32 text-sm text-[rgb(var(--ap-paper-rgb))] outline-hidden transition-colors "
                "placeholder:text-[rgb(var(--ap-paper-muted-rgb)/0.82)] focus:border-[rgb(var(--ap-accent-rgb))]"
            ),
        ),
        rx.el.span(
            "Recherche globale",
            class_name=(
                "ap-eyebrow pointer-events-none absolute right-0 top-1/2 "
                "-translate-y-1/2 text-[rgb(var(--ap-paper-muted-rgb)/0.82)]"
            ),
        ),
        class_name="relative w-full",
    )


def guide_hero() -> rx.Component:
    return rx.el.header(
        page_hero(
            "Bibliothèque embarquée",
            "Guide Agricole AgriPro",
            "Comprendre l'agriculture et maîtriser AgriPro, du geste au terrain "
            "jusqu'à la donnée dans l'application.",
            meta=meta_ledger(
                meta_row("Version", GuideState.current_version["version_label"]),
                meta_row("Statut", GuideState.current_version["status_label"]),
                meta_row(
                    "Publication",
                    GuideState.current_version["published_label"],
                ),
                meta_row("Jour", GuideState.today_label),
            ),
            actions=rx.el.div(
                help_button("guide", "Aide embarquée"),
                _refresh(),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="pb-8",
        ),
        guide_metrics(),
        rx.el.div(_search_field(), class_name="mt-10"),
        rx.cond(GuideState.has_search, _search_panel(), rx.fragment()),
        class_name="w-full",
    )

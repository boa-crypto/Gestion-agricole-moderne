import reflex as rx

from app.components.design import (
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
            rx.icon(hit["icon"], class_name="h-4 w-4 text-[#d8fa5e]"),
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10",
        ),
        rx.el.div(
            rx.el.p(
                hit["title"],
                class_name="text-sm font-semibold text-[#f2efe4] text-left truncate",
            ),
            rx.el.p(
                hit["subtitle"],
                class_name="text-[11px] font-medium text-[#c9c5b4]/50 text-left truncate mt-0.5",
            ),
            rx.el.p(
                hit["excerpt"],
                class_name="text-[11px] font-medium text-[#c9c5b4]/45 text-left leading-relaxed mt-1.5",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.icon(
            "arrow-up-right",
            class_name="h-3.5 w-3.5 text-[#c9c5b4]/40 shrink-0",
        ),
        on_click=GuideState.open_hit(hit["kind"], hit["ref"]),
        key=key,
        class_name="flex items-start gap-3 w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3 hover:border-[#d8fa5e]/30 hover:bg-[#191c13] transition-colors text-left",
    )


def _group(group: SearchGroup, key: str = "") -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.icon(group["icon"], class_name="h-3.5 w-3.5 text-[#d8fa5e]/80"),
            rx.el.span(
                group["label"],
                class_name="ap-eyebrow text-[#c9c5b4]/50",
            ),
            rx.el.span(
                group["count"],
                class_name="rounded-none bg-[#d8fa5e]/15 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit",
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
                rx.icon("radar", class_name="h-3.5 w-3.5 text-[#d8fa5e]"),
                rx.el.span(
                    f"{GuideState.search_total} résultat(s) groupé(s) par type",
                    class_name="text-[11px] font-semibold text-[#c9c5b4]/65",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.button(
                rx.icon("x", class_name="h-3.5 w-3.5"),
                rx.el.span("Effacer"),
                on_click=GuideState.clear_query,
                class_name="flex items-center gap-1.5 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/65 hover:text-[#f2efe4] hover:border-[#d8fa5e]/30 transition-colors w-fit ml-auto",
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
                rx.icon("search-x", class_name="h-6 w-6 text-[#ff8a5b]"),
                rx.el.p(
                    "Aucun contenu du guide ne correspond à cette recherche.",
                    class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2 text-center",
                ),
                class_name="flex flex-col items-center justify-center py-10 w-full",
            ),
        ),
        class_name="w-full border-t border-[#F2EFE4]/12 pt-5 mt-6",
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
            "border-[#D8FA5E] bg-[#D8FA5E] px-3.5 py-2.5 text-[10px] uppercase "
            "tracking-[0.18em] text-[#0A0A08] transition-colors "
            "hover:border-[#E4FF9B] hover:bg-[#E4FF9B] "
            "disabled:cursor-not-allowed disabled:opacity-45"
        ),
    )


def _search_field() -> rx.Component:
    return rx.el.div(
        rx.icon(
            "search",
            class_name=(
                "pointer-events-none absolute left-0 top-1/2 h-4 w-4 "
                "-translate-y-1/2 text-[#C9C5B4]/45"
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
                "w-full border-b border-[#F2EFE4]/16 bg-transparent py-3.5 pl-7 "
                "pr-32 text-sm text-[#F2EFE4] outline-hidden transition-colors "
                "placeholder:text-[#C9C5B4]/35 focus:border-[#D8FA5E]"
            ),
        ),
        rx.el.span(
            "Recherche globale",
            class_name=(
                "ap-eyebrow pointer-events-none absolute right-0 top-1/2 "
                "-translate-y-1/2 text-[#C9C5B4]/35"
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

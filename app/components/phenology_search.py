"""Section phénologique de la recherche globale."""

import reflex as rx

from app.phenology_ops import SearchHit
from app.states.phenology_search_state import (
    KINDS,
    PhenologySearchState,
    SearchSection,
)

_KIND_OPTIONS: list[dict[str, str]] = [
    {"value": kind, "label": label} for kind, label, _icon in KINDS
]


def _hit(hit: SearchHit) -> rx.Component:
    return rx.el.a(
        rx.el.div(
            rx.icon(hit["icon"], class_name="h-3.5 w-3.5 text-lime-300"),
            rx.el.span(
                hit["title"],
                class_name="text-xs font-semibold text-emerald-50 truncate",
            ),
            rx.icon(
                "arrow-up-right",
                class_name="h-3 w-3 text-emerald-100/35 ml-auto shrink-0",
            ),
            class_name="flex items-center gap-2 min-w-0",
        ),
        rx.el.p(
            hit["subtitle"],
            class_name="text-[10px] font-medium text-emerald-100/50 mt-1 truncate",
        ),
        rx.el.p(
            hit["detail"],
            class_name="text-[10px] font-medium text-emerald-100/40 mt-1.5 leading-relaxed",
        ),
        href=hit["route"],
        class_name="block w-full rounded-2xl border border-white/10 bg-white/[0.02] p-3 hover:border-lime-300/25 hover:bg-white/[0.05] transition-colors",
    )


def _section(section: SearchSection) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(section["icon"], class_name="h-4 w-4 text-lime-300"),
            rx.el.span(
                section["kind_label"],
                class_name="text-[11px] font-semibold uppercase tracking-[0.22em] text-lime-300/80",
            ),
            rx.el.span(
                section["count"],
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-bold text-emerald-100/70 w-fit ml-auto",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.div(
            rx.foreach(section["hits"], lambda hit: _hit(hit)),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 mt-3",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4",
    )


def phenology_search_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Index phénologique",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Profils, stades, observations, opérations et changements",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{PhenologySearchState.total_hits} résultat(s)",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "search",
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                ),
                rx.el.input(
                    placeholder="Nouaison, tallage, observateur, commentaire…",
                    default_value=PhenologySearchState.term,
                    on_change=PhenologySearchState.set_term.debounce(400),
                    class_name="w-full rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-3 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 outline-hidden transition-colors",
                ),
                class_name="relative w-full",
            ),
            rx.el.div(
                rx.icon(
                    "layers",
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300/80 pointer-events-none",
                ),
                rx.el.select(
                    rx.el.option("Tout le périmètre", value="TOUS"),
                    rx.foreach(
                        _KIND_OPTIONS,
                        lambda opt: rx.el.option(
                            opt["label"], value=opt["value"]
                        ),
                    ),
                    value=PhenologySearchState.kind_filter,
                    on_change=PhenologySearchState.set_kind_filter,
                    class_name="w-full appearance-none cursor-pointer rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-9 text-sm font-medium text-emerald-50 focus:border-lime-300/50 outline-hidden transition-colors",
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                ),
                class_name="relative w-full",
            ),
            rx.el.button(
                rx.icon("rotate-ccw", class_name="h-4 w-4"),
                rx.el.span("Réinitialiser"),
                on_click=PhenologySearchState.reset_index,
                class_name="flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-full lg:w-fit",
            ),
            class_name="grid grid-cols-1 lg:grid-cols-3 gap-3 mt-5",
        ),
        rx.cond(
            PhenologySearchState.is_loading,
            rx.el.div(
                class_name="animate-pulse h-40 rounded-2xl bg-white/[0.05] mt-5"
            ),
            rx.cond(
                PhenologySearchState.sections.length() > 0,
                rx.el.div(
                    rx.foreach(
                        PhenologySearchState.sections,
                        lambda section: _section(section),
                    ),
                    class_name="flex flex-col gap-3 mt-5",
                ),
                rx.el.p(
                    "Aucune entrée phénologique ne correspond à cette recherche.",
                    class_name="text-sm font-medium text-emerald-100/50 mt-5",
                ),
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )

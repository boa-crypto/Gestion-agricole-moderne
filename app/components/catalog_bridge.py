"""Passerelles visuelles vers le référentiel agronomique.

Deux composants, réutilisables depuis n'importe quel écran :

* `catalog_shortcut(context)` : accès contextuel au référentiel depuis les
  parcelles, les traitements ou l'audit (aide contextuelle embarquée) ;
* `catalog_context_panel()` : lecture Catégorie → Culture → Espèce → Variété
  des cultures de la parcelle sélectionnée.

Direction visuelle inchangée : vert nuit, chlorophylle et ambre, surfaces
vitrées, statuts agricoles lumineux, titres en Instrument Serif.
"""

import reflex as rx

from app.guide_hints import shortcut_spec
from app.states.parcels_state import CropRow, ParcelsState

_TONE = {
    "good": "rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
    "warn": "rounded-full border border-amber-300/30 bg-amber-300/10 px-2 py-0.5 text-[10px] font-bold text-amber-200 w-fit",
    "bad": "rounded-full border border-red-400/30 bg-red-500/10 px-2 py-0.5 text-[10px] font-bold text-red-300 w-fit",
    "info": "rounded-full border border-sky-300/30 bg-sky-300/10 px-2 py-0.5 text-[10px] font-bold text-sky-200 w-fit",
    "muted": "rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/50 w-fit",
}


def _tone_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            ("good", _TONE["good"]),
            ("warn", _TONE["warn"]),
            ("bad", _TONE["bad"]),
            ("info", _TONE["info"]),
            _TONE["muted"],
        ),
    )


def catalog_shortcut(context: str) -> rx.Component:
    """Accès contextuel au référentiel, adapté à l'écran courant."""
    spec = shortcut_spec(context)
    return rx.el.section(
        rx.el.div(
            rx.icon(spec["icon"], class_name="h-4 w-4 text-lime-300"),
            class_name="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-lime-300/25 bg-lime-300/10",
        ),
        rx.el.div(
            rx.el.p(
                spec["label"],
                class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
            ),
            rx.el.p(
                spec["title"],
                class_name="text-sm font-semibold text-emerald-50 mt-0.5",
            ),
            rx.el.p(
                spec["detail"],
                class_name="text-[11px] font-medium text-emerald-100/50 mt-0.5",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.a(
            rx.icon("sprout", class_name="h-3.5 w-3.5 text-[#04140d]"),
            rx.el.span(spec["cta"], class_name="text-[#04140d]"),
            href=spec["route"],
            class_name="flex items-center gap-2 rounded-full bg-lime-300 px-4 py-2 text-xs font-semibold hover:bg-lime-200 transition-colors w-fit shrink-0",
        ),
        class_name="flex flex-col sm:flex-row sm:items-center gap-3 w-full rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 backdrop-blur-xl mt-6",
    )


def _breadcrumb(crop: CropRow) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            crop["catalog_category"],
            class_name="text-[10px] font-semibold uppercase tracking-[0.16em] text-lime-300/80 truncate",
        ),
        rx.icon("chevron-right", class_name="h-3 w-3 text-emerald-100/30"),
        rx.el.span(
            crop["catalog_culture"],
            class_name="text-[11px] font-semibold text-emerald-50/85 truncate",
        ),
        rx.icon("chevron-right", class_name="h-3 w-3 text-emerald-100/30"),
        rx.el.span(
            crop["catalog_species"],
            class_name="text-[11px] font-medium text-emerald-100/60 truncate",
        ),
        rx.icon("chevron-right", class_name="h-3 w-3 text-emerald-100/30"),
        rx.el.span(
            crop["catalog_variety"],
            class_name="text-[11px] font-bold text-amber-200 truncate",
        ),
        class_name="flex flex-wrap items-center gap-1.5 w-full",
    )


def _linked_card(crop: CropRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="h-1 w-full rounded-full",
            style={"backgroundColor": crop["catalog_category_color"]},
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    crop["catalog_culture_icon"],
                    class_name="h-4 w-4 text-lime-300",
                ),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-lime-300/25 bg-lime-300/10",
            ),
            rx.el.div(
                rx.el.p(
                    crop["name"],
                    class_name="text-sm font-semibold text-emerald-50 truncate",
                ),
                rx.el.p(
                    crop["catalog_scientific"],
                    class_name="text-[11px] font-medium italic text-emerald-100/45 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.cond(
                crop["catalog_is_reference"],
                rx.el.span(
                    "Référence",
                    class_name=_TONE["info"],
                ),
                rx.fragment(),
            ),
            class_name="flex items-start gap-3 w-full mt-3",
        ),
        rx.el.div(_breadcrumb(crop), class_name="w-full mt-3"),
        rx.el.div(
            _tone_badge(
                crop["catalog_cycle_tone"], crop["catalog_cycle_label"]
            ),
            _tone_badge(
                crop["catalog_water_tone"], crop["catalog_water_label"]
            ),
            rx.cond(
                crop["catalog_maturity"] != "",
                rx.el.span(crop["catalog_maturity"], class_name=_TONE["muted"]),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-1.5 w-full mt-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "Qualité attendue",
                    class_name="text-[9px] font-semibold uppercase tracking-[0.18em] text-emerald-100/40",
                ),
                rx.el.p(
                    crop["catalog_quality"],
                    class_name="text-[11px] font-medium text-emerald-100/70 mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                rx.el.p(
                    "Rendement de référence",
                    class_name="text-[9px] font-semibold uppercase tracking-[0.18em] text-emerald-100/40",
                ),
                rx.el.p(
                    f"{crop['catalog_yield']} t/ha",
                    class_name="text-[11px] font-bold text-amber-200 mt-0.5",
                ),
                class_name="shrink-0 text-right",
            ),
            class_name="flex items-start gap-3 w-full mt-3 pt-3 border-t border-white/5",
        ),
        key=crop["id"].to_string(),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4",
    )


def _unlinked_row(crop: CropRow) -> rx.Component:
    return rx.el.div(
        rx.icon("unlink", class_name="h-3.5 w-3.5 text-amber-200 shrink-0"),
        rx.el.span(
            crop["name"],
            class_name="text-[11px] font-semibold text-emerald-50 truncate",
        ),
        rx.el.span(
            crop["season"],
            class_name="text-[10px] font-medium text-emerald-100/45 shrink-0",
        ),
        key=crop["id"].to_string(),
        class_name="flex items-center gap-2 rounded-xl border border-amber-300/20 bg-amber-300/[0.06] px-3 py-2 w-full",
    )


def _totals_pill() -> rx.Component:
    return rx.el.div(
        rx.icon("layers", class_name="h-3.5 w-3.5 text-lime-300"),
        rx.el.span(
            ParcelsState.catalog_coverage_label,
            class_name="text-[11px] font-medium text-emerald-50/80",
        ),
        class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 w-fit",
    )


def catalog_context_panel() -> rx.Component:
    """Lecture référentielle des cultures de la parcelle sélectionnée."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Référentiel agronomique",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Catégorie → Culture → Espèce → Variété",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    "Chaque fiche culturale reliée au référentiel hérite de sa "
                    "famille, de son espèce botanique et de sa variété : cycle, "
                    "besoin en eau, qualité attendue et rendement de référence.",
                    class_name="text-[11px] font-medium text-emerald-100/50 mt-1.5 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                _totals_pill(),
                rx.el.a(
                    rx.icon(
                        "arrow-up-right",
                        class_name="h-3.5 w-3.5 text-[#04140d]",
                    ),
                    rx.el.span(
                        "Ouvrir le référentiel", class_name="text-[#04140d]"
                    ),
                    href="/referentiel",
                    class_name="flex items-center gap-2 rounded-full bg-lime-300 px-4 py-2 text-xs font-semibold hover:bg-lime-200 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 lg:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4 w-full",
        ),
        rx.el.div(
            rx.el.span(
                ParcelsState.catalog_link_label,
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                f"{ParcelsState.catalog_variety_count} variétés sélectionnables",
                class_name="rounded-full border border-lime-300/25 bg-lime-300/[0.08] px-3 py-1 text-[11px] font-semibold text-lime-200 w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-4",
        ),
        rx.cond(
            ParcelsState.has_catalog_links,
            rx.el.div(
                rx.foreach(ParcelsState.catalog_linked_crops, _linked_card),
                class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 w-full mt-4",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon("sprout", class_name="h-5 w-5 text-amber-200"),
                    class_name="flex h-11 w-11 items-center justify-center rounded-2xl border border-amber-300/25 bg-amber-300/10",
                ),
                rx.el.p(
                    "Aucune culture reliée au référentiel sur cette parcelle",
                    class_name="text-sm font-semibold text-emerald-50 mt-3",
                ),
                rx.el.p(
                    "Ouvrez la fiche culturale et choisissez une variété du "
                    "référentiel structuré : l'espèce et sa famille suivront "
                    "automatiquement.",
                    class_name="text-[11px] font-medium text-emerald-100/50 mt-1.5 max-w-xl",
                ),
                class_name="flex flex-col items-start rounded-2xl border border-white/10 bg-white/[0.02] p-5 mt-4",
            ),
        ),
        rx.cond(
            ParcelsState.has_catalog_gaps,
            rx.el.div(
                rx.el.p(
                    "Cultures à relier au référentiel",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-amber-200/80",
                ),
                rx.el.div(
                    rx.foreach(
                        ParcelsState.catalog_unlinked_crops, _unlinked_row
                    ),
                    class_name="grid grid-cols-1 md:grid-cols-3 gap-2 w-full mt-2",
                ),
                class_name="w-full mt-4 rounded-2xl border border-amber-300/15 bg-amber-300/[0.03] p-4",
            ),
            rx.fragment(),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl mt-4",
    )

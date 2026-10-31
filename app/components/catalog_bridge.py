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
    "good": "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit",
    "warn": "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffb894] w-fit",
    "bad": "rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-2 py-0.5 text-[10px] font-bold text-[#ff9b8c] w-fit",
    "info": "rounded-none border border-[#9cc3ff]/30 bg-[#9cc3ff]/10 px-2 py-0.5 text-[10px] font-bold text-[#c3daff] w-fit",
    "muted": "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/50 w-fit",
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
            rx.icon(spec["icon"], class_name="h-4 w-4 text-[#d8fa5e]"),
            class_name="flex h-10 w-10 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10",
        ),
        rx.el.div(
            rx.el.p(
                spec["label"],
                class_name="ap-eyebrow text-[#d8fa5e]/80",
            ),
            rx.el.p(
                spec["title"],
                class_name="text-sm font-semibold text-[#f2efe4] mt-0.5",
            ),
            rx.el.p(
                spec["detail"],
                class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-0.5",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.a(
            rx.el.span(spec["cta"]),
            rx.icon("arrow-up-right", class_name="h-3.5 w-3.5"),
            href=spec["route"],
            class_name=(
                "ap-mono inline-flex shrink-0 items-center gap-2 border-b "
                "border-[#D8FA5E] pb-1 text-[10px] uppercase tracking-[0.18em] "
                "text-[#D8FA5E] transition-colors hover:border-[#F2EFE4] "
                "hover:text-[#F2EFE4]"
            ),
        ),
        class_name=(
            "flex w-full flex-col items-start gap-3 border-y "
            "border-[#F2EFE4]/12 py-3 sm:flex-row sm:items-center mt-6"
        ),
    )


def _breadcrumb(crop: CropRow) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            crop["catalog_category"],
            class_name="ap-eyebrow text-[#d8fa5e]/80 truncate",
        ),
        rx.icon("chevron-right", class_name="h-3 w-3 text-[#c9c5b4]/30"),
        rx.el.span(
            crop["catalog_culture"],
            class_name="text-[11px] font-semibold text-[#f2efe4]/85 truncate",
        ),
        rx.icon("chevron-right", class_name="h-3 w-3 text-[#c9c5b4]/30"),
        rx.el.span(
            crop["catalog_species"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/60 truncate",
        ),
        rx.icon("chevron-right", class_name="h-3 w-3 text-[#c9c5b4]/30"),
        rx.el.span(
            crop["catalog_variety"],
            class_name="text-[11px] font-bold text-[#ffb894] truncate",
        ),
        class_name="flex flex-wrap items-center gap-1.5 w-full",
    )


def _linked_card(crop: CropRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="h-1 w-full rounded-none",
            style={"backgroundColor": crop["catalog_category_color"]},
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    crop["catalog_culture_icon"],
                    class_name="h-4 w-4 text-[#d8fa5e]",
                ),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10",
            ),
            rx.el.div(
                rx.el.p(
                    crop["name"],
                    class_name="text-sm font-semibold text-[#f2efe4] truncate",
                ),
                rx.el.p(
                    crop["catalog_scientific"],
                    class_name="text-[11px] font-medium italic text-[#c9c5b4]/45 truncate",
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
                    class_name="ap-eyebrow text-[#c9c5b4]/40",
                ),
                rx.el.p(
                    crop["catalog_quality"],
                    class_name="text-[11px] font-medium text-[#c9c5b4]/70 mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                rx.el.p(
                    "Rendement de référence",
                    class_name="ap-eyebrow text-[#c9c5b4]/40",
                ),
                rx.el.p(
                    f"{crop['catalog_yield']} t/ha",
                    class_name="text-[11px] font-bold text-[#ffb894] mt-0.5",
                ),
                class_name="shrink-0 text-right",
            ),
            class_name="flex items-start gap-3 w-full mt-3 pt-3 border-t border-[#f2efe4]/8",
        ),
        key=crop["id"].to_string(),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4",
    )


def _unlinked_row(crop: CropRow) -> rx.Component:
    return rx.el.div(
        rx.icon("unlink", class_name="h-3.5 w-3.5 text-[#ffb894] shrink-0"),
        rx.el.span(
            crop["name"],
            class_name="text-[11px] font-semibold text-[#f2efe4] truncate",
        ),
        rx.el.span(
            crop["season"],
            class_name="text-[10px] font-medium text-[#c9c5b4]/45 shrink-0",
        ),
        key=crop["id"].to_string(),
        class_name="flex items-center gap-2 rounded-none border border-[#ff8a5b]/20 bg-[#ff8a5b]/[0.06] px-3 py-2 w-full",
    )


def _totals_pill() -> rx.Component:
    return rx.el.div(
        rx.icon("layers", class_name="h-3.5 w-3.5 text-[#d8fa5e]"),
        rx.el.span(
            ParcelsState.catalog_coverage_label,
            class_name="text-[11px] font-medium text-[#f2efe4]/80",
        ),
        class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1.5 w-fit",
    )


def catalog_context_panel() -> rx.Component:
    """Lecture référentielle des cultures de la parcelle sélectionnée."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Référentiel agronomique",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Catégorie → Culture → Espèce → Variété",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                rx.el.p(
                    "Chaque fiche culturale reliée au référentiel hérite de sa "
                    "famille, de son espèce botanique et de sa variété : cycle, "
                    "besoin en eau, qualité attendue et rendement de référence.",
                    class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-1.5 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                _totals_pill(),
                rx.el.a(
                    rx.icon(
                        "arrow-up-right",
                        class_name="h-3.5 w-3.5 text-[#0A0A08]",
                    ),
                    rx.el.span(
                        "Ouvrir le référentiel", class_name="text-[#0A0A08]"
                    ),
                    href="/referentiel",
                    class_name="flex items-center gap-2 rounded-none bg-[#d8fa5e] px-4 py-2 text-xs font-semibold hover:bg-[#e4ff9b] transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 lg:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4 w-full",
        ),
        rx.el.div(
            rx.el.span(
                ParcelsState.catalog_link_label,
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            rx.el.span(
                f"{ParcelsState.catalog_variety_count} variétés sélectionnables",
                class_name="rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/[0.08] px-3 py-1 text-[11px] font-semibold text-[#e4ff9b] w-fit",
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
                    rx.icon("sprout", class_name="h-5 w-5 text-[#ffb894]"),
                    class_name="flex h-11 w-11 items-center justify-center rounded-none border border-[#ff8a5b]/25 bg-[#ff8a5b]/10",
                ),
                rx.el.p(
                    "Aucune culture reliée au référentiel sur cette parcelle",
                    class_name="text-sm font-semibold text-[#f2efe4] mt-3",
                ),
                rx.el.p(
                    "Ouvrez la fiche culturale et choisissez une variété du "
                    "référentiel structuré : l'espèce et sa famille suivront "
                    "automatiquement.",
                    class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-1.5 max-w-xl",
                ),
                class_name="flex flex-col items-start rounded-none border border-[#f2efe4]/12 bg-[#0d0f09] p-5 mt-4",
            ),
        ),
        rx.cond(
            ParcelsState.has_catalog_gaps,
            rx.el.div(
                rx.el.p(
                    "Cultures à relier au référentiel",
                    class_name="ap-eyebrow text-[#ffb894]/80",
                ),
                rx.el.div(
                    rx.foreach(
                        ParcelsState.catalog_unlinked_crops, _unlinked_row
                    ),
                    class_name="grid grid-cols-1 md:grid-cols-3 gap-2 w-full mt-2",
                ),
                class_name="w-full mt-4 rounded-none border border-[#ff8a5b]/15 bg-[#ff8a5b]/[0.03] p-4",
            ),
            rx.fragment(),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6  mt-4",
    )

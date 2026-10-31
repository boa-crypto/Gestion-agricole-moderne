"""Fiche détaillée culture → espèces → variétés et usages par module."""

import reflex as rx

from app.states.catalog_browser_state import (
    CatalogBrowserState,
    ConsumerHint,
    SpeciesCard,
    VarietyRow,
)


def _tone_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit",
            ),
            (
                "warn",
                "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffb894] w-fit",
            ),
            (
                "bad",
                "rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-2 py-0.5 text-[10px] font-bold text-[#ff9b8c] w-fit",
            ),
            (
                "info",
                "rounded-none border border-[#9cc3ff]/30 bg-[#9cc3ff]/10 px-2 py-0.5 text-[10px] font-bold text-[#c3daff] w-fit",
            ),
            "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/50 w-fit",
        ),
    )


def _fact(icon: str, label: str, value: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-[#d8fa5e]/80"),
            rx.el.span(
                label,
                class_name="ap-eyebrow text-[#c9c5b4]/40",
            ),
            class_name="flex items-center gap-1.5",
        ),
        rx.el.p(
            value,
            class_name="text-[12px] font-semibold text-[#f2efe4] mt-1 leading-snug",
        ),
        class_name="rounded-none border border-white/[0.07] bg-[#0d0f09] p-3",
    )


def _variety_card(variety: VarietyRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="h-1 w-full rounded-none",
            style={"backgroundColor": variety["color"]},
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    variety["name"],
                    class_name="text-sm font-semibold text-[#f2efe4] truncate",
                ),
                rx.cond(
                    variety["local_name"] != "",
                    rx.el.p(
                        variety["local_name"],
                        class_name="text-[11px] font-medium text-[#c9c5b4]/45 mt-0.5 truncate",
                    ),
                    rx.fragment(),
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.cond(
                variety["is_reference"],
                rx.el.span(
                    "Référence",
                    class_name="rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit",
                ),
                rx.fragment(),
            ),
            class_name="flex items-start justify-between gap-2 mt-3",
        ),
        rx.el.div(
            rx.el.span(
                variety["maturity"],
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            _tone_badge(variety["drought_tone"], variety["drought_label"]),
            rx.cond(
                variety["consistency"] != "",
                rx.el.span(
                    variety["consistency"],
                    class_name="rounded-none border border-[#ff8a5b]/25 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-semibold text-[#ffb894] w-fit",
                ),
                rx.fragment(),
            ),
            rx.cond(
                variety["is_linked"],
                rx.el.span(
                    rx.icon("link", class_name="h-3 w-3"),
                    title="Reliée au référentiel variétal de l'exploitation",
                    class_name="flex items-center justify-center rounded-none border border-[#9cc3ff]/25 bg-[#9cc3ff]/10 h-5 w-5 text-[#c3daff]",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-1.5 mt-2.5",
        ),
        rx.el.p(
            variety["quality"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/60 mt-2.5 leading-relaxed",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("wheat", class_name="h-3.5 w-3.5 text-[#ff8a5b]/80"),
                rx.el.span(
                    f"{variety['yield_t_ha']:.1f} t/ha",
                    class_name="text-[11px] font-bold text-[#ffb894]",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.div(
                rx.icon("timer", class_name="h-3.5 w-3.5 text-[#a9c98b]/80"),
                rx.el.span(
                    f"{variety['cycle_days']} j",
                    class_name="text-[11px] font-semibold text-[#c9c5b4]/60",
                ),
                class_name="flex items-center gap-1.5",
            ),
            class_name="flex items-center gap-4 mt-3 pt-3 border-t border-[#f2efe4]/8",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "calendar-plus",
                    class_name="h-3.5 w-3.5 text-[#a9c98b]/70",
                ),
                rx.el.span(
                    variety["sowing"],
                    class_name="text-[10px] font-medium text-[#c9c5b4]/50 truncate",
                ),
                class_name="flex items-center gap-1.5 min-w-0",
            ),
            rx.el.div(
                rx.icon(
                    "calendar-check",
                    class_name="h-3.5 w-3.5 text-[#ff8a5b]/70",
                ),
                rx.el.span(
                    variety["harvest"],
                    class_name="text-[10px] font-medium text-[#c9c5b4]/50 truncate",
                ),
                class_name="flex items-center gap-1.5 min-w-0",
            ),
            class_name="flex flex-col gap-1.5 mt-2.5",
        ),
        rx.cond(
            variety["notes"] != "",
            rx.el.p(
                variety["notes"],
                class_name="text-[10px] font-medium text-[#c9c5b4]/40 mt-2.5 leading-relaxed",
            ),
            rx.fragment(),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#0d0f09] p-4 hover:border-[#d8fa5e]/25 transition-colors",
    )


def _species_card(species: SpeciesCard) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    species["name"],
                    class_name="text-base font-semibold text-[#f2efe4]",
                ),
                rx.el.p(
                    species["scientific_name"],
                    class_name="ap-serif italic text-lg text-[#e4ff9b]/80 mt-0.5",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    species["family"],
                    class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
                ),
                _tone_badge(
                    species["salinity_tone"],
                    f"Salinité : {species['salinity_label']}",
                ),
                class_name="flex flex-wrap items-center gap-1.5",
            ),
            class_name="flex flex-col sm:flex-row sm:items-start justify-between gap-3",
        ),
        rx.el.div(
            _fact("timer", "Cycle", species["cycle_weeks"]),
            _fact("calendar-plus", "Semis / plantation", species["sowing"]),
            _fact("calendar-check", "Récolte", species["harvest"]),
            _fact("droplets", "Besoin en eau", f"{species['water_mm']:.0f} mm"),
            _fact(
                "arrow-down-to-line",
                "Enracinement",
                f"{species['root_cm']:.0f} cm",
            ),
            _fact(
                "thermometer",
                "Température de base",
                f"{species['base_temp']:.1f} °C",
            ),
            _fact("flask-conical", "pH optimal", species["ph_label"]),
            _fact(
                "leaf",
                "Fumure N / P / K",
                f"{species['nitrogen']:.0f} / {species['phosphorus']:.0f} / {species['potassium']:.0f} kg/ha",
            ),
            _fact("grid-2x2", "Densité de référence", species["density"]),
            class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-2.5 w-full mt-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("bug", class_name="h-3.5 w-3.5 text-[#ff8a5b]/80"),
                    rx.el.span(
                        "Ravageurs dominants",
                        class_name="ap-eyebrow text-[#c9c5b4]/40",
                    ),
                    class_name="flex items-center gap-1.5",
                ),
                rx.el.p(
                    species["pests"],
                    class_name="text-[11px] font-medium text-[#c9c5b4]/60 mt-1.5 leading-relaxed",
                ),
                class_name="flex-1 min-w-0 rounded-none border border-white/[0.07] bg-[#0d0f09] p-3",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "shield-alert",
                        class_name="h-3.5 w-3.5 text-[#ff9b8c]/80",
                    ),
                    rx.el.span(
                        "Maladies dominantes",
                        class_name="ap-eyebrow text-[#c9c5b4]/40",
                    ),
                    class_name="flex items-center gap-1.5",
                ),
                rx.el.p(
                    species["diseases"],
                    class_name="text-[11px] font-medium text-[#c9c5b4]/60 mt-1.5 leading-relaxed",
                ),
                class_name="flex-1 min-w-0 rounded-none border border-white/[0.07] bg-[#0d0f09] p-3",
            ),
            class_name="flex flex-col lg:flex-row gap-2.5 w-full mt-2.5",
        ),
        rx.cond(
            species["notes"] != "",
            rx.el.div(
                rx.icon(
                    "info", class_name="h-3.5 w-3.5 shrink-0 text-[#d8fa5e]/80"
                ),
                rx.el.p(
                    species["notes"],
                    class_name="text-[11px] font-medium text-[#c9c5b4]/60 leading-relaxed",
                ),
                class_name="flex items-start gap-2 rounded-none border border-[#d8fa5e]/15 bg-[#d8fa5e]/[0.05] p-3 w-full mt-2.5",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("flower-2", class_name="h-4 w-4 text-[#d8fa5e]"),
                rx.el.h4(
                    "Variétés décrites",
                    class_name="text-sm font-semibold text-[#f2efe4]",
                ),
                rx.el.span(
                    species["variety_count"],
                    class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-bold text-[#c9c5b4]/60 w-fit ml-auto",
                ),
                class_name="flex items-center gap-2 w-full",
            ),
            rx.cond(
                species["variety_count"] > 0,
                rx.el.div(
                    rx.foreach(species["varieties"], _variety_card),
                    class_name="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-3 w-full mt-3",
                ),
                rx.el.p(
                    "Aucune variété décrite pour cette espèce.",
                    class_name="text-[11px] font-medium text-[#c9c5b4]/45 mt-3",
                ),
            ),
            class_name="w-full mt-5 pt-5 border-t border-white/[0.07]",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5",
    )


def _consumer_card(consumer: ConsumerHint) -> rx.Component:
    return rx.el.a(
        rx.el.div(
            rx.el.div(
                rx.icon(consumer["icon"], class_name="h-4 w-4 text-[#d8fa5e]"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10",
            ),
            rx.el.div(
                rx.el.p(
                    consumer["label"],
                    class_name="text-sm font-semibold text-[#f2efe4] truncate",
                ),
                rx.el.p(
                    consumer["usage"],
                    class_name="text-[10px] font-medium text-[#c9c5b4]/45 mt-0.5 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.icon(
                "arrow-up-right",
                class_name="h-3.5 w-3.5 shrink-0 text-[#c9c5b4]/35",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        rx.el.p(
            consumer["detail"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/60 mt-3 leading-relaxed",
        ),
        rx.el.div(
            rx.icon("corner-down-right", class_name="h-3 w-3 text-[#d8fa5e]/70"),
            rx.el.span(
                consumer["route"],
                class_name="text-[10px] font-semibold text-[#c9c5b4]/40",
            ),
            class_name="flex items-center gap-1.5 w-full mt-3 pt-3 border-t border-[#f2efe4]/8",
        ),
        href=consumer["route"],
        class_name="block w-full rounded-none border border-[#f2efe4]/12 bg-[#0d0f09] p-4 hover:border-[#d8fa5e]/25 hover:bg-[#16190f] transition-colors",
    )


def _culture_head() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="h-1.5 w-full rounded-none",
            style={"backgroundColor": CatalogBrowserState.culture["color"]},
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        CatalogBrowserState.culture["icon"],
                        class_name="h-5 w-5 text-[#d8fa5e]",
                    ),
                    class_name="flex h-11 w-11 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10",
                ),
                rx.el.div(
                    rx.el.span(
                        CatalogBrowserState.culture["category_name"],
                        class_name="ap-eyebrow text-[#d8fa5e]/80",
                    ),
                    rx.el.h2(
                        CatalogBrowserState.culture["name"],
                        class_name="ap-serif text-4xl text-[#f2efe4] leading-tight mt-1",
                    ),
                    rx.el.p(
                        f"{CatalogBrowserState.culture['common_name']} · {CatalogBrowserState.culture['family']}",
                        class_name="text-[12px] font-medium text-[#c9c5b4]/50 mt-1",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-start gap-3 min-w-0",
            ),
            rx.el.div(
                _tone_badge(
                    CatalogBrowserState.culture["cycle_tone"],
                    CatalogBrowserState.culture["cycle_label"],
                ),
                _tone_badge(
                    CatalogBrowserState.culture["water_tone"],
                    CatalogBrowserState.culture["water_label"],
                ),
                class_name="flex flex-wrap items-center gap-1.5 lg:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-start justify-between gap-4 w-full mt-4",
        ),
        rx.el.p(
            CatalogBrowserState.culture["description"],
            class_name="text-sm font-medium text-[#c9c5b4]/65 mt-4 leading-relaxed max-w-4xl",
        ),
        rx.el.div(
            _fact("target", "Débouché", CatalogBrowserState.culture["usage"]),
            _fact(
                "timer",
                "Cycle observé",
                CatalogBrowserState.culture["cycle_range"],
            ),
            _fact(
                "leaf",
                "Espèces décrites",
                CatalogBrowserState.culture["species_count"],
            ),
            _fact(
                "flower-2",
                "Variétés décrites",
                CatalogBrowserState.culture["variety_count"],
            ),
            _fact(
                "wheat",
                "Rendement de référence",
                f"{CatalogBrowserState.culture['yield_max']:.1f} t/ha",
            ),
            class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-2.5 w-full mt-4",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5",
    )


def _consumers_block() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Usages",
                class_name="ap-eyebrow text-[#d8fa5e]/80",
            ),
            rx.el.h3(
                "Ce que les modules en font",
                class_name="ap-serif text-2xl text-[#f2efe4] mt-1",
            ),
            rx.el.p(
                "Chaque module consommateur reçoit du référentiel des consignes "
                "prêtes à l'emploi pour la culture sélectionnée.",
                class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-1.5",
            ),
            class_name="min-w-0",
        ),
        rx.el.div(
            rx.foreach(CatalogBrowserState.consumers, _consumer_card),
            class_name="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-4 gap-3 w-full mt-4",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5",
    )


def _detail_skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(class_name="animate-pulse h-44 rounded-none bg-[#16190f]"),
        rx.el.div(class_name="animate-pulse h-64 rounded-none bg-[#16190f]"),
        rx.el.div(class_name="animate-pulse h-72 rounded-none bg-[#16190f]"),
        class_name="flex flex-col gap-4 w-full",
    )


def _detail_empty() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("sprout", class_name="h-6 w-6 text-[#d8fa5e]"),
            class_name="flex h-14 w-14 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10",
        ),
        rx.el.h3(
            "Choisissez une culture dans l'herbier",
            class_name="ap-serif text-3xl text-[#f2efe4] mt-4",
        ),
        rx.el.p(
            "Sélectionnez une famille sur le radar agronomique ou une culture "
            "dans la liste pour afficher ses espèces, ses variétés et les "
            "consignes transmises aux modules de l'exploitation.",
            class_name="text-sm font-medium text-[#c9c5b4]/50 mt-2 max-w-xl",
        ),
        class_name="flex flex-col items-start w-full rounded-none border border-[#f2efe4]/12 bg-[#0d0f09] p-8",
    )


def catalog_detail() -> rx.Component:
    return rx.el.section(
        rx.cond(
            CatalogBrowserState.is_loading,
            _detail_skeleton(),
            rx.cond(
                CatalogBrowserState.has_selection,
                rx.el.div(
                    _culture_head(),
                    _consumers_block(),
                    rx.el.div(
                        rx.el.div(
                            rx.el.span(
                                "Botanique & agronomie",
                                class_name="ap-eyebrow text-[#d8fa5e]/80",
                            ),
                            rx.el.h3(
                                "Espèces et variétés",
                                class_name="ap-serif text-2xl text-[#f2efe4] mt-1",
                            ),
                            class_name="min-w-0",
                        ),
                        rx.cond(
                            CatalogBrowserState.species.length() > 0,
                            rx.el.div(
                                rx.foreach(
                                    CatalogBrowserState.species,
                                    lambda s: _species_card(s),
                                ),
                                class_name="flex flex-col gap-4 w-full mt-4",
                            ),
                            rx.el.p(
                                "Aucune espèce décrite pour cette culture.",
                                class_name="text-sm font-medium text-[#c9c5b4]/50 mt-4",
                            ),
                        ),
                        class_name="w-full",
                    ),
                    class_name="flex flex-col gap-4 w-full",
                ),
                _detail_empty(),
            ),
        ),
        class_name="flex-1 w-full min-w-0",
    )

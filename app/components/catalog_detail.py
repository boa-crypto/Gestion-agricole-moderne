"""Fiche détaillée culture → espèces → variétés et usages par module."""

import reflex as rx

from app.components.design import skeleton_page

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
                "rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
            ),
            (
                "warn",
                "rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
            ),
            (
                "bad",
                "rounded-none border border-[rgb(var(--ap-danger-rgb)/0.30)] bg-[rgb(var(--ap-flame-strong-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-danger-soft-rgb))] w-fit",
            ),
            (
                "info",
                "rounded-none border border-[rgb(var(--ap-info-rgb)/0.30)] bg-[rgb(var(--ap-info-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-info-soft-rgb))] w-fit",
            ),
            "rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit",
        ),
    )


def _fact(icon: str, label: str, value: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb)/0.80)]"),
            rx.el.span(
                label,
                class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            class_name="flex items-center gap-1.5",
        ),
        rx.el.p(
            value,
            class_name="text-[12px] font-semibold text-[rgb(var(--ap-paper-rgb))] mt-1 leading-snug",
        ),
        class_name="rounded-none border border-white/[0.07] bg-[rgb(var(--ap-surface-soft-rgb))] p-3",
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
                    class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
                ),
                rx.cond(
                    variety["local_name"] != "",
                    rx.el.p(
                        variety["local_name"],
                        class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-0.5 truncate",
                    ),
                    rx.fragment(),
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.cond(
                variety["is_reference"],
                rx.el.span(
                    "Référence",
                    class_name="rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
                ),
                rx.fragment(),
            ),
            class_name="flex items-start justify-between gap-2 mt-3",
        ),
        rx.el.div(
            rx.el.span(
                variety["maturity"],
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
            ),
            _tone_badge(variety["drought_tone"], variety["drought_label"]),
            rx.cond(
                variety["consistency"] != "",
                rx.el.span(
                    variety["consistency"],
                    class_name="rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.25)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
                ),
                rx.fragment(),
            ),
            rx.cond(
                variety["is_linked"],
                rx.el.span(
                    rx.icon("link", class_name="h-3 w-3"),
                    title="Reliée au référentiel variétal de l'exploitation",
                    class_name="flex items-center justify-center rounded-none border border-[rgb(var(--ap-info-rgb)/0.25)] bg-[rgb(var(--ap-info-rgb)/0.10)] h-5 w-5 text-[rgb(var(--ap-info-soft-rgb))]",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-1.5 mt-2.5",
        ),
        rx.el.p(
            variety["quality"],
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] mt-2.5 leading-relaxed",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("wheat", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-flame-soft-rgb)/0.80)]"),
                rx.el.span(
                    f"{variety['yield_t_ha']:.1f} t/ha",
                    class_name="text-[11px] font-bold text-[rgb(var(--ap-flame-tint-rgb))]",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.div(
                rx.icon("timer", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-sage-rgb)/0.80)]"),
                rx.el.span(
                    f"{variety['cycle_days']} j",
                    class_name="text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)]",
                ),
                class_name="flex items-center gap-1.5",
            ),
            class_name="flex items-center gap-4 mt-3 pt-3 border-t border-[rgb(var(--ap-paper-rgb)/0.12)]",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "calendar-plus",
                    class_name="h-3.5 w-3.5 text-[rgb(var(--ap-sage-rgb)/0.70)]",
                ),
                rx.el.span(
                    variety["sowing"],
                    class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate",
                ),
                class_name="flex items-center gap-1.5 min-w-0",
            ),
            rx.el.div(
                rx.icon(
                    "calendar-check",
                    class_name="h-3.5 w-3.5 text-[rgb(var(--ap-flame-soft-rgb)/0.70)]",
                ),
                rx.el.span(
                    variety["harvest"],
                    class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate",
                ),
                class_name="flex items-center gap-1.5 min-w-0",
            ),
            class_name="flex flex-col gap-1.5 mt-2.5",
        ),
        rx.cond(
            variety["notes"] != "",
            rx.el.p(
                variety["notes"],
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-2.5 leading-relaxed",
            ),
            rx.fragment(),
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.12)] w-full pt-4 hover:border-t-[rgb(var(--ap-accent-rgb)/0.40)] transition-colors",
    )


def _species_card(species: SpeciesCard) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    species["name"],
                    class_name="text-base font-semibold text-[rgb(var(--ap-paper-rgb))]",
                ),
                rx.el.p(
                    species["scientific_name"],
                    class_name="ap-serif italic text-lg text-[rgb(var(--ap-accent-soft-rgb)/0.80)] mt-0.5",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    species["family"],
                    class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
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
                    rx.icon("bug", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-flame-soft-rgb)/0.80)]"),
                    rx.el.span(
                        "Ravageurs dominants",
                        class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                    ),
                    class_name="flex items-center gap-1.5",
                ),
                rx.el.p(
                    species["pests"],
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] mt-1.5 leading-relaxed",
                ),
                class_name="flex-1 min-w-0 rounded-none border border-white/[0.07] bg-[rgb(var(--ap-surface-soft-rgb))] p-3",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "shield-alert",
                        class_name="h-3.5 w-3.5 text-[rgb(var(--ap-danger-soft-rgb)/0.80)]",
                    ),
                    rx.el.span(
                        "Maladies dominantes",
                        class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                    ),
                    class_name="flex items-center gap-1.5",
                ),
                rx.el.p(
                    species["diseases"],
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] mt-1.5 leading-relaxed",
                ),
                class_name="flex-1 min-w-0 rounded-none border border-white/[0.07] bg-[rgb(var(--ap-surface-soft-rgb))] p-3",
            ),
            class_name="flex flex-col lg:flex-row gap-2.5 w-full mt-2.5",
        ),
        rx.cond(
            species["notes"] != "",
            rx.el.div(
                rx.icon(
                    "info", class_name="h-3.5 w-3.5 shrink-0 text-[rgb(var(--ap-accent-rgb)/0.80)]"
                ),
                rx.el.p(
                    species["notes"],
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] leading-relaxed",
                ),
                class_name="flex items-start gap-2 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.15)] bg-[rgb(var(--ap-accent-rgb))]/[0.05] p-3 w-full mt-2.5",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("flower-2", class_name="h-4 w-4 text-[rgb(var(--ap-accent-rgb))]"),
                rx.el.h4(
                    "Variétés décrites",
                    class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))]",
                ),
                rx.el.span(
                    species["variety_count"],
                    class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit ml-auto",
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
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-3",
                ),
            ),
            class_name="w-full mt-5 pt-5 border-t border-white/[0.07]",
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-5",
    )


def _consumer_card(consumer: ConsumerHint) -> rx.Component:
    return rx.el.a(
        rx.el.div(
            rx.el.div(
                rx.icon(consumer["icon"], class_name="h-4 w-4 text-[rgb(var(--ap-accent-rgb))]"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)]",
            ),
            rx.el.div(
                rx.el.p(
                    consumer["label"],
                    class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
                ),
                rx.el.p(
                    consumer["usage"],
                    class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-0.5 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.icon(
                "arrow-up-right",
                class_name="h-3.5 w-3.5 shrink-0 text-[rgb(var(--ap-paper-muted-rgb)/0.82)]",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        rx.el.p(
            consumer["detail"],
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] mt-3 leading-relaxed",
        ),
        rx.el.div(
            rx.icon("corner-down-right", class_name="h-3 w-3 text-[rgb(var(--ap-accent-rgb)/0.70)]"),
            rx.el.span(
                consumer["route"],
                class_name="text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            class_name="flex items-center gap-1.5 w-full mt-3 pt-3 border-t border-[rgb(var(--ap-paper-rgb)/0.12)]",
        ),
        href=consumer["route"],
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.12)] block w-full pt-4 hover:border-t-[rgb(var(--ap-accent-rgb)/0.40)] hover:bg-[rgb(var(--ap-surface-muted-rgb))] transition-colors",
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
                        class_name="h-5 w-5 text-[rgb(var(--ap-accent-rgb))]",
                    ),
                    class_name="flex h-11 w-11 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)]",
                ),
                rx.el.div(
                    rx.el.span(
                        CatalogBrowserState.culture["category_name"],
                        class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                    ),
                    rx.el.h2(
                        CatalogBrowserState.culture["name"],
                        class_name="ap-serif text-4xl text-[rgb(var(--ap-paper-rgb))] leading-tight mt-1",
                    ),
                    rx.el.p(
                        f"{CatalogBrowserState.culture['common_name']} · {CatalogBrowserState.culture['family']}",
                        class_name="text-[12px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-1",
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
            class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-4 leading-relaxed max-w-4xl",
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
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-5",
    )


def _consumers_block() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Usages",
                class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
            ),
            rx.el.h3(
                "Ce que les modules en font",
                class_name="ap-serif text-2xl text-[rgb(var(--ap-paper-rgb))] mt-1",
            ),
            rx.el.p(
                "Chaque module consommateur reçoit du référentiel des consignes "
                "prêtes à l'emploi pour la culture sélectionnée.",
                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-1.5",
            ),
            class_name="min-w-0",
        ),
        rx.el.div(
            rx.foreach(CatalogBrowserState.consumers, _consumer_card),
            class_name="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-4 gap-3 w-full mt-4",
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-5",
    )


def _detail_skeleton() -> rx.Component:
    return rx.el.div(
        skeleton_page(3),
        class_name="flex flex-col gap-4 w-full",
    )


def _detail_empty() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("sprout", class_name="h-6 w-6 text-[rgb(var(--ap-accent-rgb))]"),
            class_name="flex h-14 w-14 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)]",
        ),
        rx.el.h3(
            "Choisissez une culture dans l'herbier",
            class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-4",
        ),
        rx.el.p(
            "Sélectionnez une famille sur le radar agronomique ou une culture "
            "dans la liste pour afficher ses espèces, ses variétés et les "
            "consignes transmises aux modules de l'exploitation.",
            class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-2 max-w-xl",
        ),
        class_name="flex flex-col items-start w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-soft-rgb))] p-8",
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
                                class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                            ),
                            rx.el.h3(
                                "Espèces et variétés",
                                class_name="ap-serif text-2xl text-[rgb(var(--ap-paper-rgb))] mt-1",
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
                                class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-4",
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

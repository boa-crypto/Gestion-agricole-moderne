"""En-tête du référentiel cultures et centerpiece « herbier / radar agronomique »."""

import reflex as rx

from app.components.guide_help import help_button
from app.states.catalog_browser_state import (
    CatalogBrowserState,
    CategoryNode,
    CoverageMetric,
)


def catalog_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("sprout", class_name="h-4 w-4 text-lime-300"),
                    rx.el.span(
                        "Référentiel agronomique",
                        class_name="text-[11px] font-semibold uppercase tracking-[0.32em] text-lime-300/90",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "Catégorie → Culture → Espèce → Variété",
                    class_name="font-['Instrument_Serif'] text-4xl md:text-5xl leading-[1.05] text-emerald-50 mt-3",
                ),
                rx.el.p(
                    "L'herbier de l'exploitation : familles cultivées, repères "
                    "agronomiques par espèce et fiches variétales, prêts à être "
                    "consommés par les parcelles, les campagnes, l'irrigation, "
                    "la fertilisation, les traitements et les récoltes.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-3 max-w-3xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon("layers", class_name="h-3.5 w-3.5 text-lime-300"),
                    rx.el.span(
                        CatalogBrowserState.coverage_label,
                        class_name="text-xs font-medium text-emerald-50/80",
                    ),
                    class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 backdrop-blur-xl w-fit",
                ),
                help_button("referentiel", "Guide du référentiel"),
                rx.el.button(
                    rx.cond(
                        CatalogBrowserState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#04140d]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#04140d]"
                        ),
                    ),
                    rx.el.span("Actualiser", class_name="text-[#04140d]"),
                    on_click=CatalogBrowserState.load_referentiel,
                    class_name="flex items-center gap-2 rounded-full bg-lime-300 px-4 py-2 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 lg:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full",
        ),
        class_name="w-full border-b border-white/10 pb-8 mt-6",
    )


def _metric_tile(metric: CoverageMetric) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(metric["icon"], class_name="h-4 w-4 text-lime-300"),
            rx.el.span(
                metric["label"],
                class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/50",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            metric["value"],
            class_name="font-['Instrument_Serif'] text-4xl text-emerald-50 mt-2 leading-none",
        ),
        rx.el.p(
            metric["unit"],
            class_name="text-[11px] font-medium text-emerald-100/45 mt-1.5",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4",
    )


def catalog_coverage() -> rx.Component:
    return rx.el.section(
        rx.cond(
            CatalogBrowserState.is_loading,
            rx.el.div(
                rx.foreach(
                    [0, 1, 2, 3, 4, 5],
                    lambda _i: rx.el.div(
                        class_name="animate-pulse h-28 rounded-2xl bg-white/[0.05]"
                    ),
                ),
                class_name="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3 w-full",
            ),
            rx.el.div(
                rx.foreach(CatalogBrowserState.coverage, _metric_tile),
                class_name="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3 w-full",
            ),
        ),
        class_name="w-full",
    )


def _radar_spoke(node: CategoryNode) -> rx.Component:
    return rx.el.div(
        class_name="absolute left-1/2 top-1/2 h-px",
        style={
            "width": f"{node['spoke_pct']}%",
            "transform": f"rotate({node['angle']}deg)",
            "transformOrigin": "left center",
            "backgroundImage": (
                f"linear-gradient(90deg, {node['color']}00, {node['color']}99)"
            ),
        },
    )


def _radar_dot(node: CategoryNode) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            class_name="block h-full w-full rounded-full",
            style={
                "backgroundColor": node["color"],
                "boxShadow": f"0 0 12px {node['color']}",
            },
        ),
        on_click=CatalogBrowserState.select_category(node["key"]),
        title=f"{node['name']} · {node['varieties']} variétés",
        aria_label=node["name"],
        class_name=rx.cond(
            CatalogBrowserState.category_filter == node["key"],
            "absolute -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ring-lime-200/80 ring-offset-2 ring-offset-[#04120c] transition-transform hover:scale-125",
            "absolute -translate-x-1/2 -translate-y-1/2 rounded-full opacity-80 transition-transform hover:scale-125 hover:opacity-100",
        ),
        style={
            "left": f"{node['x_pct']}%",
            "top": f"{node['y_pct']}%",
            "width": f"{node['dot_size']}px",
            "height": f"{node['dot_size']}px",
        },
    )


def _legend_row(node: CategoryNode) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            class_name="h-2.5 w-2.5 shrink-0 rounded-full",
            style={"backgroundColor": node["color"]},
        ),
        rx.el.div(
            rx.el.p(
                node["name"],
                class_name="text-[12px] font-semibold text-emerald-50 text-left truncate",
            ),
            rx.el.p(
                f"{node['cultures']} cultures · {node['species']} espèces · {node['varieties']} variétés",
                class_name="text-[10px] font-medium text-emerald-100/45 text-left truncate",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-full rounded-full",
                style={
                    "width": f"{node['share_pct']}%",
                    "backgroundColor": node["color"],
                },
            ),
            class_name="hidden sm:block h-1.5 w-16 shrink-0 rounded-full bg-white/10 overflow-hidden",
        ),
        on_click=CatalogBrowserState.select_category(node["key"]),
        class_name=rx.cond(
            CatalogBrowserState.category_filter == node["key"],
            "flex items-center gap-2.5 w-full rounded-xl border border-lime-300/40 bg-lime-300/[0.08] px-3 py-2 transition-colors",
            "flex items-center gap-2.5 w-full rounded-xl border border-white/[0.06] bg-white/[0.02] px-3 py-2 hover:border-lime-300/25 hover:bg-white/[0.05] transition-colors",
        ),
    )


def catalog_radar() -> rx.Component:
    """Centerpiece : planche d'herbier radiale du référentiel."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Planche d'herbier",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Radar agronomique du référentiel",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    "Chaque branche est une famille cultivée : sa longueur et "
                    "son bourgeon traduisent la richesse variétale décrite.",
                    class_name="text-[11px] font-medium text-emerald-100/50 mt-1.5 max-w-md",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{CatalogBrowserState.totals['reference']} variétés de référence · {CatalogBrowserState.totals['linked']} reliées",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit",
            ),
            class_name="flex flex-col sm:flex-row sm:items-end justify-between gap-3 w-full",
        ),
        rx.cond(
            CatalogBrowserState.is_loading,
            rx.el.div(
                class_name="animate-pulse h-80 w-full rounded-2xl bg-white/[0.05] mt-5"
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            class_name="absolute inset-0 rounded-full border border-white/[0.06]"
                        ),
                        rx.el.div(
                            class_name="absolute inset-[14%] rounded-full border border-white/[0.06]"
                        ),
                        rx.el.div(
                            class_name="absolute inset-[28%] rounded-full border border-dashed border-lime-300/15"
                        ),
                        rx.el.div(
                            class_name="absolute inset-[42%] rounded-full border border-white/[0.06]"
                        ),
                        rx.foreach(CatalogBrowserState.nodes, _radar_spoke),
                        rx.foreach(CatalogBrowserState.nodes, _radar_dot),
                        rx.el.div(
                            rx.icon(
                                "leaf",
                                class_name="h-5 w-5 text-lime-300",
                            ),
                            rx.el.span(
                                CatalogBrowserState.totals["varieties"],
                                class_name="font-['Instrument_Serif'] text-2xl text-emerald-50 leading-none",
                            ),
                            rx.el.span(
                                "variétés",
                                class_name="text-[9px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
                            ),
                            class_name="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-0.5 rounded-full border border-lime-300/20 bg-[#04140d]/85 h-24 w-24 justify-center backdrop-blur-xl",
                        ),
                        class_name="relative aspect-square w-full max-w-[24rem]",
                    ),
                    class_name="flex items-center justify-center w-full lg:w-[26rem] shrink-0",
                ),
                rx.el.div(
                    rx.foreach(CatalogBrowserState.nodes, _legend_row),
                    class_name="grid grid-cols-1 md:grid-cols-2 gap-2 flex-1 min-w-0 content-start",
                ),
                class_name="flex flex-col lg:flex-row items-start gap-6 w-full mt-5",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )

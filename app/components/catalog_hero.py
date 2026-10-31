"""En-tête du référentiel cultures et centerpiece « herbier / radar agronomique »."""

import reflex as rx

from app.components.design import (
    meta_ledger,
    meta_row,
    page_hero,
    stat,
)
from app.components.guide_help import help_button
from app.states.catalog_browser_state import (
    CatalogBrowserState,
    CategoryNode,
    CoverageMetric,
)


def _refresh() -> rx.Component:
    return rx.el.button(
        rx.cond(
            CatalogBrowserState.is_loading,
            rx.icon("loader-circle", class_name="h-3.5 w-3.5 animate-spin"),
            rx.icon("refresh-cw", class_name="h-3.5 w-3.5"),
        ),
        rx.el.span("Actualiser"),
        type="button",
        on_click=CatalogBrowserState.load_referentiel,
        disabled=CatalogBrowserState.is_loading,
        class_name=(
            "ap-mono inline-flex w-fit items-center justify-center gap-2 border "
            "border-[rgb(var(--ap-accent-rgb))] bg-[rgb(var(--ap-accent-rgb))] px-3.5 py-2.5 text-[10px] uppercase "
            "tracking-[0.18em] text-[rgb(var(--ap-ink-rgb))] transition-colors "
            "hover:border-[rgb(var(--ap-accent-soft-rgb))] hover:bg-[rgb(var(--ap-accent-soft-rgb))] "
            "disabled:cursor-not-allowed disabled:opacity-45"
        ),
    )


def catalog_header() -> rx.Component:
    return page_hero(
        "Référentiel agronomique",
        "Catégorie → Culture → Espèce → Variété",
        "L'herbier de l'exploitation : familles cultivées, repères agronomiques "
        "par espèce et fiches variétales, prêts à être consommés par les parcelles, "
        "les campagnes, l'irrigation, la fertilisation, les traitements et les "
        "récoltes.",
        meta=meta_ledger(
            rx.cond(
                CatalogBrowserState.coverage.length() > 0,
                rx.foreach(
                    CatalogBrowserState.coverage,
                    lambda metric: meta_row(metric["label"], metric["value"]),
                ),
                meta_row("Inventaire", CatalogBrowserState.coverage_label),
            ),
        ),
        actions=rx.el.div(
            help_button("referentiel", "Guide du référentiel"),
            _refresh(),
            class_name="flex flex-wrap items-center gap-2",
        ),
        class_name="pb-8",
    )


def _metric_tile(metric: CoverageMetric) -> rx.Component:
    return stat(
        metric["label"],
        metric["value"],
        metric["unit"],
        icon=metric["icon"],
        tone="paper",
    )


def catalog_coverage() -> rx.Component:
    return rx.el.section(
        rx.cond(
            CatalogBrowserState.is_loading,
            rx.el.div(
                rx.foreach(
                    [0, 1, 2, 3, 4, 5],
                    lambda _i: rx.el.div(
                        rx.el.div(class_name="h-px w-full bg-[rgb(var(--ap-paper-rgb)/0.12)]"),
                        rx.el.div(
                            class_name=(
                                "mt-4 h-2 w-24 ap-skeleton bg-[rgb(var(--ap-paper-rgb)/0.10)]"
                            )
                        ),
                        rx.el.div(
                            class_name=(
                                "mt-3 h-8 w-16 ap-skeleton bg-[rgb(var(--ap-paper-rgb)/0.10)]"
                            )
                        ),
                        class_name="pb-1",
                    ),
                ),
                class_name=(
                    "grid grid-cols-2 gap-x-6 gap-y-8 sm:grid-cols-3 "
                    "xl:grid-cols-6 xl:gap-x-8 w-full"
                ),
            ),
            rx.el.div(
                rx.foreach(CatalogBrowserState.coverage, _metric_tile),
                class_name=(
                    "grid grid-cols-2 gap-x-6 gap-y-8 sm:grid-cols-3 "
                    "xl:grid-cols-6 xl:gap-x-8 w-full"
                ),
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
            class_name="block h-full w-full rounded-none",
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
            "absolute -translate-x-1/2 -translate-y-1/2 rounded-none ring-2 ring-[rgb(var(--ap-accent-soft-rgb)/0.80)] ring-offset-2 ring-offset-[rgb(var(--ap-ink-rgb))] transition-transform hover:scale-125",
            "absolute -translate-x-1/2 -translate-y-1/2 rounded-none opacity-80 transition-transform hover:scale-125 hover:opacity-100",
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
            class_name="h-2.5 w-2.5 shrink-0 rounded-none",
            style={"backgroundColor": node["color"]},
        ),
        rx.el.div(
            rx.el.p(
                node["name"],
                class_name="text-[12px] font-semibold text-[rgb(var(--ap-paper-rgb))] text-left truncate",
            ),
            rx.el.p(
                f"{node['cultures']} cultures · {node['species']} espèces · {node['varieties']} variétés",
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] text-left truncate",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-full rounded-none",
                style={
                    "width": f"{node['share_pct']}%",
                    "backgroundColor": node["color"],
                },
            ),
            class_name="hidden sm:block h-1.5 w-16 shrink-0 rounded-none bg-[rgb(var(--ap-surface-control-rgb))] overflow-hidden",
        ),
        on_click=CatalogBrowserState.select_category(node["key"]),
        class_name=rx.cond(
            CatalogBrowserState.category_filter == node["key"],
            "flex items-center gap-2.5 w-full rounded-none border border-[rgb(var(--ap-accent-rgb)/0.40)] bg-[rgb(var(--ap-accent-rgb))]/[0.08] px-3 py-2 transition-colors",
            "flex items-center gap-2.5 w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.15)] bg-[rgb(var(--ap-surface-soft-rgb))] px-3 py-2 hover:border-[rgb(var(--ap-accent-rgb)/0.25)] hover:bg-[rgb(var(--ap-surface-muted-rgb))] transition-colors",
        ),
    )


def catalog_radar() -> rx.Component:
    """Centerpiece : planche d'herbier radiale du référentiel."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Planche d'herbier",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Radar agronomique du référentiel",
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                rx.el.p(
                    "Chaque branche est une famille cultivée : sa longueur et "
                    "son bourgeon traduisent la richesse variétale décrite.",
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-1.5 max-w-md",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{CatalogBrowserState.totals['reference']} variétés de référence · {CatalogBrowserState.totals['linked']} reliées",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
            ),
            class_name="flex flex-col sm:flex-row sm:items-end justify-between gap-3 w-full",
        ),
        rx.cond(
            CatalogBrowserState.is_loading,
            rx.el.div(
                class_name="ap-skeleton bg-[rgb(var(--ap-surface-high-rgb)/0.70)] h-80 w-full mt-5"
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            class_name="absolute inset-0 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.15)]"
                        ),
                        rx.el.div(
                            class_name="absolute inset-[14%] rounded-none border border-[rgb(var(--ap-paper-rgb)/0.15)]"
                        ),
                        rx.el.div(
                            class_name="absolute inset-[28%] rounded-none border border-dashed border-[rgb(var(--ap-accent-rgb)/0.15)]"
                        ),
                        rx.el.div(
                            class_name="absolute inset-[42%] rounded-none border border-[rgb(var(--ap-paper-rgb)/0.15)]"
                        ),
                        rx.foreach(CatalogBrowserState.nodes, _radar_spoke),
                        rx.foreach(CatalogBrowserState.nodes, _radar_dot),
                        rx.el.div(
                            rx.icon(
                                "leaf",
                                class_name="h-5 w-5 text-[rgb(var(--ap-accent-rgb))]",
                            ),
                            rx.el.span(
                                CatalogBrowserState.totals["varieties"],
                                class_name="ap-serif text-2xl text-[rgb(var(--ap-paper-rgb))] leading-none",
                            ),
                            rx.el.span(
                                "variétés",
                                class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                            ),
                            class_name="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-0.5 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.20)] bg-[rgb(var(--ap-ink-rgb)/0.85)] h-24 w-24 justify-center ",
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
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )

"""Focus dédié à la catégorie Dattes / palmier dattier."""

import reflex as rx

from app.states.catalog_browser_state import CatalogBrowserState, VarietyRow


def _palm_fact(icon: str, label: str, value: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-[rgb(var(--ap-flame-soft-rgb)/0.90)]"),
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


def _date_variety(variety: VarietyRow) -> rx.Component:
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
                rx.el.p(
                    rx.cond(
                        variety["local_name"] != "",
                        variety["local_name"],
                        variety["maturity"],
                    ),
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-flame-tint-rgb)/0.70)] mt-0.5 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.cond(
                variety["consistency"] != "",
                rx.el.span(
                    variety["consistency"],
                    class_name="rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
                ),
                rx.fragment(),
            ),
            class_name="flex items-start justify-between gap-2 mt-3",
        ),
        rx.el.p(
            variety["quality"],
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] mt-2.5 leading-relaxed",
        ),
        rx.el.div(
            rx.el.span(
                variety["maturity"],
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.78)] w-fit",
            ),
            rx.el.span(
                f"{variety['yield_t_ha']:.1f} t/ha",
                class_name="text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-1.5 mt-3",
        ),
        rx.el.div(
            rx.icon(
                "calendar-check", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-flame-soft-rgb)/0.70)]"
            ),
            rx.el.span(
                variety["harvest"],
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate",
            ),
            class_name="flex items-center gap-1.5 mt-3 pt-3 border-t border-[rgb(var(--ap-paper-rgb)/0.12)]",
        ),
        rx.cond(
            variety["notes"] != "",
            rx.el.p(
                variety["notes"],
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-2.5 leading-relaxed",
            ),
            rx.fragment(),
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.12)] w-full pt-4 hover:border-[rgb(var(--ap-flame-soft-rgb)/0.25)] transition-colors",
    )


def catalog_dates() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("tree_palm", class_name="h-4 w-4 text-[rgb(var(--ap-flame-soft-rgb))]"),
                    rx.el.span(
                        "Phéniciculture",
                        class_name="ap-eyebrow text-[rgb(var(--ap-flame-soft-rgb)/0.90)]",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h2(
                    "Dattes & palmier dattier",
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                rx.el.p(
                    "Conduite oasienne pérenne : pollinisation manuelle, "
                    "ciselage, ensachage des régimes puis récolte étalée. Le "
                    "classement variétal par consistance commande le séchage "
                    "et la conservation.",
                    class_name="text-[12px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{CatalogBrowserState.totals['date_varieties']} variétés décrites",
                    class_name="rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.25)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
                ),
                rx.el.button(
                    rx.icon("scan-search", class_name="h-3.5 w-3.5"),
                    rx.el.span("Ouvrir la fiche"),
                    on_click=CatalogBrowserState.focus_dates,
                    class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1.5 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.90)] hover:border-[rgb(var(--ap-flame-soft-rgb)/0.35)] hover:text-[rgb(var(--ap-paper-rgb))] transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 lg:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4 w-full",
        ),
        rx.cond(
            CatalogBrowserState.is_loading,
            rx.el.div(
                class_name="ap-skeleton bg-[rgb(var(--ap-surface-high-rgb)/0.70)] h-64 w-full mt-5"
            ),
            rx.cond(
                CatalogBrowserState.has_date_focus,
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.el.p(
                                CatalogBrowserState.palm["name"],
                                class_name="text-base font-semibold text-[rgb(var(--ap-paper-rgb))]",
                            ),
                            rx.el.p(
                                CatalogBrowserState.palm["scientific_name"],
                                class_name="ap-serif italic text-lg text-[rgb(var(--ap-flame-tint-rgb)/0.80)] mt-0.5",
                            ),
                            class_name="min-w-0",
                        ),
                        rx.el.div(
                            _palm_fact(
                                "calendar-plus",
                                "Plantation",
                                CatalogBrowserState.palm["sowing"],
                            ),
                            _palm_fact(
                                "calendar-check",
                                "Récolte",
                                CatalogBrowserState.palm["harvest"],
                            ),
                            _palm_fact(
                                "droplets",
                                "Besoin en eau annuel",
                                f"{CatalogBrowserState.palm['water_mm']} mm",
                            ),
                            _palm_fact(
                                "leaf",
                                "Fumure N / P / K",
                                f"{CatalogBrowserState.palm['npk']} kg/ha/an",
                            ),
                            _palm_fact(
                                "grid-2x2",
                                "Densité de plantation",
                                CatalogBrowserState.palm["density"],
                            ),
                            _palm_fact(
                                "waves",
                                "Tolérance à la salinité",
                                CatalogBrowserState.palm["salinity_label"],
                            ),
                            class_name="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full mt-4",
                        ),
                        rx.el.div(
                            rx.el.div(
                                rx.icon(
                                    "bug",
                                    class_name="h-3.5 w-3.5 text-[rgb(var(--ap-flame-soft-rgb)/0.80)]",
                                ),
                                rx.el.span(
                                    "Ravageurs",
                                    class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                                ),
                                class_name="flex items-center gap-1.5",
                            ),
                            rx.el.p(
                                CatalogBrowserState.palm["pests"],
                                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] mt-1.5 leading-relaxed",
                            ),
                            rx.el.div(
                                rx.icon(
                                    "shield-alert",
                                    class_name="h-3.5 w-3.5 text-[rgb(var(--ap-danger-soft-rgb)/0.80)]",
                                ),
                                rx.el.span(
                                    "Maladies",
                                    class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                                ),
                                class_name="flex items-center gap-1.5 mt-3",
                            ),
                            rx.el.p(
                                CatalogBrowserState.palm["diseases"],
                                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] mt-1.5 leading-relaxed",
                            ),
                            class_name="rounded-none border border-white/[0.07] bg-[rgb(var(--ap-surface-soft-rgb))] p-3 w-full mt-2.5",
                        ),
                        rx.cond(
                            CatalogBrowserState.palm["notes"] != "",
                            rx.el.div(
                                rx.icon(
                                    "info",
                                    class_name="h-3.5 w-3.5 shrink-0 text-[rgb(var(--ap-flame-soft-rgb)/0.90)]",
                                ),
                                rx.el.p(
                                    CatalogBrowserState.palm["notes"],
                                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] leading-relaxed",
                                ),
                                class_name="flex items-start gap-2 rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.15)] bg-[rgb(var(--ap-flame-soft-rgb))]/[0.05] p-3 w-full mt-2.5",
                            ),
                            rx.fragment(),
                        ),
                        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full xl:w-[28rem] shrink-0 pt-5",
                    ),
                    rx.el.div(
                        rx.foreach(
                            CatalogBrowserState.date_varieties, _date_variety
                        ),
                        class_name="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-3 flex-1 min-w-0 content-start",
                    ),
                    class_name="flex flex-col xl:flex-row gap-4 w-full mt-5",
                ),
                rx.el.p(
                    "La catégorie Dattes n'est pas encore amorcée dans le "
                    "référentiel : actualisez l'écran pour la charger.",
                    class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-5",
                ),
            ),
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )

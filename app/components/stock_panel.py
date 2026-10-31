import reflex as rx

from app.states.operations_state import (
    MovementRow,
    OperationsState,
    ProductRow,
)


def _tone_bar(tone: rx.Var, width: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name=rx.match(
                tone,
                ("bad", "h-full rounded-none bg-[rgb(var(--ap-danger-rgb))]"),
                ("warn", "h-full rounded-none bg-[rgb(var(--ap-flame-soft-rgb))]"),
                "h-full rounded-none bg-gradient-to-r from-[rgb(var(--ap-sage-soft-rgb))] to-[rgb(var(--ap-accent-rgb))]",
            ),
            style={"width": width},
        ),
        class_name="h-1.5 w-full rounded-none bg-[rgb(var(--ap-surface-control-rgb))]",
    )


def _critical_card(product: ProductRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("triangle-alert", class_name="h-4 w-4 text-[rgb(var(--ap-flame-soft-rgb))]"),
            rx.el.span(
                product["category_label"],
                class_name="ap-eyebrow text-[rgb(var(--ap-flame-tint-rgb)/0.70)]",
            ),
            rx.cond(
                product["organic"],
                rx.el.span(
                    "AB",
                    class_name="rounded-none border border-[rgb(var(--ap-accent-rgb)/0.40)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-1.5 py-0.5 text-[9px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit ml-auto",
                ),
                rx.fragment(),
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            product["name"],
            class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] mt-2 truncate",
        ),
        rx.el.p(
            f"{product['stock']:.1f} {product['unit']} en stock · seuil {product['threshold']:.1f}",
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] mt-1",
        ),
        _tone_bar(product["tone"], product["ratio_pct"]),
        rx.el.div(
            rx.el.span(
                product["location"],
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate",
            ),
            rx.el.button(
                rx.icon("plus", class_name="h-3 w-3"),
                rx.el.span("Réappro", class_name="text-[10px]"),
                on_click=OperationsState.open_movement_form(product["id"]),
                class_name="flex items-center gap-1 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2 py-0.5 text-[rgb(var(--ap-accent-soft-rgb))] hover:bg-[rgb(var(--ap-accent-rgb)/0.20)] transition-colors w-fit shrink-0 ml-auto",
            ),
            class_name="flex items-center gap-2 mt-3",
        ),
        key=key,
        class_name="w-full rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.25)] bg-[rgb(var(--ap-flame-soft-rgb))]/[0.06] p-4",
    )


def _product_row(product: ProductRow, key: str = "") -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.p(
                product["name"],
                class_name="text-xs font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
            ),
            rx.el.p(
                f"{product['substance']} · réf. {product['reference']}",
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate",
            ),
            class_name="px-3 py-2.5 align-middle min-w-[14rem]",
        ),
        rx.el.td(
            rx.el.span(
                product["category_label"],
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        rx.el.td(
            rx.el.div(
                rx.el.span(
                    f"{product['stock']:.1f} {product['unit']}",
                    class_name=rx.match(
                        product["tone"],
                        (
                            "bad",
                            "text-xs font-bold text-[rgb(var(--ap-danger-soft-rgb))] whitespace-nowrap",
                        ),
                        (
                            "warn",
                            "text-xs font-bold text-[rgb(var(--ap-flame-tint-rgb))] whitespace-nowrap",
                        ),
                        "text-xs font-semibold text-[rgb(var(--ap-paper-rgb))] whitespace-nowrap",
                    ),
                ),
                rx.el.span(
                    f"seuil {product['threshold']:.0f}",
                    class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] ml-auto whitespace-nowrap",
                ),
                class_name="flex items-center gap-2",
            ),
            _tone_bar(product["tone"], product["ratio_pct"]),
            class_name="px-3 py-2.5 align-middle min-w-[11rem]",
        ),
        rx.el.td(
            rx.el.p(
                f"{product['value']:.0f} €",
                class_name="text-xs font-semibold text-[rgb(var(--ap-accent-soft-rgb))] whitespace-nowrap text-right",
            ),
            rx.el.p(
                f"{product['unit_price']:.2f} €/{product['unit']}",
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] whitespace-nowrap text-right",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        rx.el.td(
            rx.el.p(
                product["expiry_label"],
                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] whitespace-nowrap",
            ),
            rx.el.p(
                f"DRE {product['reentry']} h · DAR {product['preharvest']} j",
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        rx.el.td(
            rx.el.button(
                rx.icon("arrow-left-right", class_name="h-3.5 w-3.5"),
                on_click=OperationsState.open_movement_form(product["id"]),
                title="Mouvement de stock",
                class_name="flex items-center justify-center h-7 w-7 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] text-[rgb(var(--ap-paper-muted-rgb)/0.90)] hover:text-[rgb(var(--ap-paper-rgb))] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] transition-colors ml-auto",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        key=key,
        class_name="border-b border-[rgb(var(--ap-paper-rgb)/0.12)] even:bg-[rgb(var(--ap-surface-soft-rgb))] hover:bg-[rgb(var(--ap-accent-rgb))]/[0.05] transition-colors",
    )


def _movement_row(movement: MovementRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.match(
                movement["type"],
                (
                    "ENTREE",
                    rx.icon(
                        "arrow-down-to-line", class_name="h-4 w-4 text-[rgb(var(--ap-accent-rgb))]"
                    ),
                ),
                (
                    "SORTIE",
                    rx.icon(
                        "arrow-up-from-line",
                        class_name="h-4 w-4 text-[rgb(var(--ap-flame-soft-rgb))]",
                    ),
                ),
                (
                    "PERTE",
                    rx.icon("trash-2", class_name="h-4 w-4 text-[rgb(var(--ap-danger-soft-rgb))]"),
                ),
                rx.icon("clipboard-check", class_name="h-4 w-4 text-[rgb(var(--ap-info-rgb))]"),
            ),
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))]",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    movement["product_name"],
                    class_name="text-xs font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
                ),
                rx.el.span(
                    movement["type_label"],
                    class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-1.5 py-0.5 text-[9px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.78)] w-fit shrink-0",
                ),
                class_name="flex items-center gap-2 min-w-0",
            ),
            rx.el.p(
                f"{movement['reference']} · {movement['notes']}",
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate mt-0.5",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.div(
            rx.el.span(
                f"{movement['quantity']:.1f} {movement['unit']}",
                class_name="text-xs font-semibold text-[rgb(var(--ap-paper-rgb))] whitespace-nowrap",
            ),
            rx.el.span(
                movement["date_label"],
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] whitespace-nowrap",
            ),
            class_name="flex flex-col items-end shrink-0",
        ),
        key=key,
        class_name="flex items-center gap-3 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] p-3",
    )


def _view_button(label: str, value: str, icon: str) -> rx.Component:
    return rx.el.button(
        rx.icon(icon, class_name="h-3.5 w-3.5"),
        rx.el.span(label, class_name="text-[11px]"),
        on_click=OperationsState.set_stock_view(value),
        class_name=rx.cond(
            OperationsState.stock_view == value,
            "flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.40)] bg-[rgb(var(--ap-accent-rgb)/0.15)] px-3 py-1.5 font-semibold text-[rgb(var(--ap-accent-pale-rgb))] w-fit",
            "flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1.5 font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] hover:text-[rgb(var(--ap-paper-rgb))] hover:border-[rgb(var(--ap-accent-rgb)/0.30)] transition-colors w-fit",
        ),
    )


def stock_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Intrants & magasin",
                    class_name="ap-eyebrow text-[rgb(var(--ap-flame-soft-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Stocks de produits",
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                _view_button("Tous", "TOUS", "layers"),
                _view_button("Critiques", "CRITIQUE", "triangle-alert"),
                _view_button("Homologués AB", "BIO", "leaf"),
                rx.el.button(
                    rx.icon(
                        "arrow-left-right", class_name="h-4 w-4 text-[rgb(var(--ap-ink-rgb))]"
                    ),
                    rx.el.span("Mouvement", class_name="text-[rgb(var(--ap-ink-rgb))]"),
                    on_click=OperationsState.open_movement_form(0),
                    class_name="ap-mono inline-flex w-fit items-center gap-2 bg-[rgb(var(--ap-accent-rgb))] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[rgb(var(--ap-ink-rgb))] transition-colors hover:bg-[rgb(var(--ap-accent-soft-rgb))]",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4",
        ),
        rx.cond(
            OperationsState.critical_products.length() > 0,
            rx.el.div(
                rx.foreach(
                    OperationsState.critical_products,
                    lambda p: _critical_card(p, key=p["id"].to_string()),
                ),
                class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 mt-5",
            ),
            rx.el.div(
                rx.icon("shield-check", class_name="h-5 w-5 text-[rgb(var(--ap-accent-rgb))]"),
                rx.el.p(
                    "Aucun intrant sous le seuil de réapprovisionnement.",
                    class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] mt-2",
                ),
                class_name="flex flex-col items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] py-8 mt-5",
            ),
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.table(
                        rx.el.thead(
                            rx.el.tr(
                                rx.el.th(
                                    rx.el.div(
                                        rx.icon(
                                            "package",
                                            class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb)/0.70)]",
                                        ),
                                        rx.el.span("Produit"),
                                        class_name="flex items-center gap-1.5",
                                    ),
                                    class_name="px-3 py-3 text-left ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                                ),
                                rx.el.th(
                                    "Catégorie",
                                    class_name="px-3 py-3 text-left ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                                ),
                                rx.el.th(
                                    "Stock / seuil",
                                    class_name="px-3 py-3 text-left ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                                ),
                                rx.el.th(
                                    "Valeur",
                                    class_name="px-3 py-3 text-right ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                                ),
                                rx.el.th(
                                    "Délais",
                                    class_name="px-3 py-3 text-left ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                                ),
                                rx.el.th(
                                    "",
                                    class_name="px-3 py-3",
                                ),
                                class_name="border-b border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))]",
                            ),
                        ),
                        rx.el.tbody(
                            rx.foreach(
                                OperationsState.visible_products,
                                lambda p: _product_row(
                                    p, key=p["id"].to_string()
                                ),
                            ),
                        ),
                        class_name="table-auto w-full min-w-[48rem]",
                    ),
                    class_name="overflow-x-auto",
                ),
                class_name="flex-1 min-w-0 rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-soft-rgb)/0.60)] overflow-hidden max-h-[32rem] overflow-y-auto",
            ),
            rx.el.div(
                rx.el.span(
                    "Derniers mouvements",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.cond(
                    OperationsState.movements.length() > 0,
                    rx.el.div(
                        rx.foreach(
                            OperationsState.movements,
                            lambda m: _movement_row(m, key=m["id"].to_string()),
                        ),
                        class_name="flex flex-col gap-2 mt-3 max-h-[28rem] overflow-y-auto pr-1",
                    ),
                    rx.el.p(
                        "Aucun mouvement enregistré.",
                        class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-3",
                    ),
                ),
                class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full xl:w-[24rem] shrink-0 pt-4",
            ),
            class_name="flex flex-col xl:flex-row gap-4 w-full mt-5",
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )

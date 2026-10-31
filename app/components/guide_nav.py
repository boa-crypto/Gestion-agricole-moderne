import reflex as rx

from app.components.design import index_rail, index_tab
from app.states.guide_state import CategoryCard, GuideState


def _section_tab(item: tuple[str, str, str]) -> rx.Component:
    return index_tab(
        item[1],
        active=GuideState.active_section == item[0],
        on_click=GuideState.set_section(item[0]),
        icon=item[2],
    )


def guide_sections() -> rx.Component:
    return index_rail(
        rx.foreach(GuideState.sections, _section_tab),
        label="Sections du guide",
    )


def _category_card(category: CategoryCard, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            class_name="h-1 w-full rounded-none",
            style={"backgroundColor": category["color"]},
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(category["icon"], class_name="h-4 w-4 text-[rgb(var(--ap-accent-rgb))]"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)]",
            ),
            rx.el.div(
                rx.el.p(
                    category["name"],
                    class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] text-left truncate",
                ),
                rx.el.p(
                    category["tagline"],
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] text-left mt-1 line-clamp-2",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-3 w-full mt-3",
        ),
        rx.el.div(
            rx.el.span(
                f"{category['article_count']} article(s)",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
            ),
            rx.el.span(
                f"{category['procedure_count']} procédure(s)",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
            ),
            rx.el.span(
                f"{category['rule_count']} règle(s)",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
            ),
            class_name="flex flex-wrap items-center gap-1.5 w-full mt-3",
        ),
        rx.el.div(
            rx.icon("corner-down-right", class_name="h-3 w-3 text-[rgb(var(--ap-accent-rgb)/0.70)]"),
            rx.el.span(
                category["module_route"],
                class_name="text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            class_name="flex items-center gap-1.5 w-full mt-3 pt-3 border-t border-[rgb(var(--ap-paper-rgb)/0.12)]",
        ),
        on_click=GuideState.select_category(category["key"]),
        key=key,
        class_name=rx.cond(
            GuideState.selected_category == category["key"],
            "w-full border border-[rgb(var(--ap-accent-rgb)/0.40)] bg-[rgb(var(--ap-surface-raised-rgb))] p-4 text-left transition-colors",
            "w-full border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-transparent p-4 text-left transition-colors hover:border-[rgb(var(--ap-paper-rgb)/0.30)]",
        ),
    )


def guide_categories() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Carte de connaissances",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Navigation par catégories",
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.button(
                rx.icon("layers", class_name="h-3.5 w-3.5"),
                rx.el.span("Toutes les catégories"),
                on_click=GuideState.select_category("TOUS"),
                class_name=rx.cond(
                    GuideState.selected_category == "TOUS",
                    "ap-mono flex items-center gap-2 border-b border-[rgb(var(--ap-accent-rgb))] pb-1.5 text-[10px] uppercase tracking-[0.18em] text-[rgb(var(--ap-accent-rgb))] transition-colors w-fit",
                    "ap-mono flex items-center gap-2 border-b border-transparent pb-1.5 text-[10px] uppercase tracking-[0.18em] text-[rgb(var(--ap-paper-muted-rgb)/0.78)] hover:border-[rgb(var(--ap-paper-rgb)/0.30)] hover:text-[rgb(var(--ap-paper-rgb))] transition-colors w-fit",
                ),
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.cond(
            GuideState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="ap-skeleton bg-[rgb(var(--ap-surface-high-rgb)/0.70)] h-32 w-full"
                ),
                rx.el.div(
                    class_name="ap-skeleton bg-[rgb(var(--ap-surface-high-rgb)/0.70)] h-32 w-full"
                ),
                rx.el.div(
                    class_name="ap-skeleton bg-[rgb(var(--ap-surface-high-rgb)/0.70)] h-32 w-full"
                ),
                rx.el.div(
                    class_name="ap-skeleton bg-[rgb(var(--ap-surface-high-rgb)/0.70)] h-32 w-full"
                ),
                class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 w-full mt-5",
            ),
            rx.el.div(
                rx.foreach(
                    GuideState.categories,
                    lambda c: _category_card(c, key=c["key"]),
                ),
                class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 w-full mt-5",
            ),
        ),
        class_name="w-full border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-6",
    )

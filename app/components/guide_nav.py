import reflex as rx

from app.states.guide_state import CategoryCard, GuideState


def _section_tab(item: tuple[str, str, str]) -> rx.Component:
    return rx.el.button(
        rx.icon(
            item[2],
            class_name=rx.cond(
                GuideState.active_section == item[0],
                "h-4 w-4 text-[#d8fa5e]",
                "h-4 w-4 text-[#c9c5b4]/45",
            ),
        ),
        rx.el.span(item[1]),
        on_click=GuideState.set_section(item[0]),
        class_name=rx.cond(
            GuideState.active_section == item[0],
            "flex items-center gap-2 rounded-none border border-[#d8fa5e]/45 bg-[#d8fa5e]/15 px-4 py-2 text-xs font-semibold text-[#efffc4] transition-colors w-fit",
            "flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2 text-xs font-medium text-[#c9c5b4]/60 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit",
        ),
    )


def guide_sections() -> rx.Component:
    return rx.el.nav(
        rx.foreach(GuideState.sections, _section_tab),
        aria_label="Sections du guide",
        class_name="flex flex-wrap items-center gap-2 w-full",
    )


def _category_card(category: CategoryCard, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            class_name="h-1 w-full rounded-none",
            style={"backgroundColor": category["color"]},
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(category["icon"], class_name="h-4 w-4 text-[#d8fa5e]"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10",
            ),
            rx.el.div(
                rx.el.p(
                    category["name"],
                    class_name="text-sm font-semibold text-[#f2efe4] text-left truncate",
                ),
                rx.el.p(
                    category["tagline"],
                    class_name="text-[11px] font-medium text-[#c9c5b4]/50 text-left mt-1 line-clamp-2",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-3 w-full mt-3",
        ),
        rx.el.div(
            rx.el.span(
                f"{category['article_count']} article(s)",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            rx.el.span(
                f"{category['procedure_count']} procédure(s)",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            rx.el.span(
                f"{category['rule_count']} règle(s)",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            class_name="flex flex-wrap items-center gap-1.5 w-full mt-3",
        ),
        rx.el.div(
            rx.icon("corner-down-right", class_name="h-3 w-3 text-[#d8fa5e]/70"),
            rx.el.span(
                category["module_route"],
                class_name="text-[10px] font-semibold text-[#c9c5b4]/45",
            ),
            class_name="flex items-center gap-1.5 w-full mt-3 pt-3 border-t border-[#f2efe4]/8",
        ),
        on_click=GuideState.select_category(category["key"]),
        key=key,
        class_name=rx.cond(
            GuideState.selected_category == category["key"],
            "w-full rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/[0.07] p-4 text-left ring-2 ring-[#d8fa5e]/30 transition-all",
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 text-left hover:border-[#d8fa5e]/25 hover:bg-[#16190f] transition-all",
        ),
    )


def guide_categories() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Carte de connaissances",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Navigation par catégories",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.button(
                rx.icon("layers", class_name="h-3.5 w-3.5"),
                rx.el.span("Toutes les catégories"),
                on_click=GuideState.select_category("TOUS"),
                class_name=rx.cond(
                    GuideState.selected_category == "TOUS",
                    "flex items-center gap-2 rounded-none border border-[#d8fa5e]/45 bg-[#d8fa5e]/15 px-4 py-2 text-xs font-semibold text-[#efffc4] transition-colors w-fit",
                    "flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2 text-xs font-medium text-[#c9c5b4]/60 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit",
                ),
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.cond(
            GuideState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-32 rounded-none bg-[#16190f]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-32 rounded-none bg-[#16190f]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-32 rounded-none bg-[#16190f]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-32 rounded-none bg-[#16190f]"
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
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )

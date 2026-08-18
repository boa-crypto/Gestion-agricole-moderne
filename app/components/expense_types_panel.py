import reflex as rx

from app.states.expenses_state import ExpensesState, TypeRow


def _type_card(item: TypeRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(item["icon"], class_name="h-4 w-4 text-[#04140d]"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl",
                style={"backgroundColor": item["color"]},
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        item["code"],
                        class_name="text-[10px] font-semibold uppercase tracking-[0.22em] text-lime-300/80",
                    ),
                    rx.cond(
                        item["is_archived"],
                        rx.el.span(
                            "Archivé",
                            class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/45 w-fit",
                        ),
                        rx.cond(
                            item["is_active"],
                            rx.el.span(
                                "Actif",
                                class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
                            ),
                            rx.el.span(
                                "Désactivé",
                                class_name="rounded-full border border-amber-300/30 bg-amber-300/10 px-2 py-0.5 text-[10px] font-bold text-amber-200 w-fit",
                            ),
                        ),
                    ),
                    class_name="flex flex-wrap items-center gap-2",
                ),
                rx.el.p(
                    item["name"],
                    class_name="text-sm font-semibold text-emerald-50 mt-0.5 truncate",
                ),
                rx.el.p(
                    item["category"],
                    class_name="text-[10px] font-medium text-emerald-100/45 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                f"{item['total_ttc']:.0f} €",
                class_name="text-xs font-bold text-lime-200 shrink-0",
            ),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        rx.el.p(
            item["description"],
            class_name="text-[11px] font-medium text-emerald-100/50 mt-3 leading-relaxed",
        ),
        rx.el.div(
            rx.el.span(
                f"{item['expense_count']} ligne(s)",
                class_name="text-[10px] font-medium text-emerald-100/45",
            ),
            rx.el.span(
                f"TVA {item['vat_rate']:.0f} %",
                class_name="text-[10px] font-medium text-emerald-100/45",
            ),
            rx.el.span(
                item["payment_label"],
                class_name="text-[10px] font-medium text-emerald-100/45",
            ),
            class_name="flex flex-wrap items-center gap-3 mt-3",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("pencil", class_name="h-3.5 w-3.5"),
                rx.el.span("Modifier", class_name="text-[11px]"),
                on_click=ExpensesState.open_type_edit(item["id"]),
                class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
            ),
            rx.el.button(
                rx.icon("power", class_name="h-3.5 w-3.5"),
                rx.el.span(
                    rx.cond(item["is_active"], "Désactiver", "Réactiver"),
                    class_name="text-[11px]",
                ),
                on_click=ExpensesState.toggle_type_active(item["id"]),
                class_name="flex items-center gap-1.5 rounded-full border border-amber-300/30 bg-amber-300/10 px-2.5 py-1 text-amber-200 hover:bg-amber-300/20 transition-colors w-fit",
            ),
            rx.el.button(
                rx.icon("archive", class_name="h-3.5 w-3.5"),
                rx.el.span(
                    rx.cond(item["is_archived"], "Restaurer", "Archiver"),
                    class_name="text-[11px]",
                ),
                on_click=ExpensesState.archive_type(item["id"]),
                class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-emerald-100/60 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 border-t border-white/5 pt-3 mt-3",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:border-lime-300/25 transition-colors",
    )


def expense_types_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Plan de charges personnalisable",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-amber-300/80",
                ),
                rx.el.h2(
                    "Types de dépenses",
                    class_name="font-['Instrument_Serif'] text-2xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.button(
                rx.icon("tags", class_name="h-4 w-4"),
                rx.el.span("Nouveau type"),
                on_click=ExpensesState.open_type_create,
                class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/75 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3 w-full pb-5 border-b border-white/10",
        ),
        rx.el.div(
            rx.foreach(
                ExpensesState.types,
                lambda item: _type_card(item, key=item["id"].to_string()),
            ),
            class_name="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-3 w-full mt-5",
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )

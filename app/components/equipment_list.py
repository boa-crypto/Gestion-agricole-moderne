import reflex as rx

from app.states.maintenance_state import EquipmentRow, MaintenanceState


def _status_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit whitespace-nowrap",
            ),
            (
                "warn",
                "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffb894] w-fit whitespace-nowrap",
            ),
            (
                "bad",
                "rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-2 py-0.5 text-[10px] font-bold text-[#ff9b8c] w-fit whitespace-nowrap",
            ),
            (
                "info",
                "rounded-none border border-[#9cc3ff]/30 bg-[#9cc3ff]/10 px-2 py-0.5 text-[10px] font-bold text-[#c3daff] w-fit whitespace-nowrap",
            ),
            "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/45 w-fit whitespace-nowrap",
        ),
    )


def _equipment_card(machine: EquipmentRow, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.el.div(
                rx.icon(machine["icon"], class_name="h-4 w-4 text-[#d8fa5e]"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#16190f]",
            ),
            rx.el.div(
                rx.el.p(
                    machine["name"],
                    class_name="text-sm font-semibold text-[#f2efe4] truncate text-left",
                ),
                rx.el.p(
                    f"{machine['code']} · {machine['brand_model']}",
                    class_name="text-[11px] font-medium text-[#c9c5b4]/50 truncate text-left",
                ),
                class_name="min-w-0 flex-1",
            ),
            _status_badge(machine["status_tone"], machine["status_label"]),
            class_name="flex items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.el.span(
                machine["category_label"],
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            rx.el.span(
                machine["ownership_label"],
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/50 w-fit",
            ),
            rx.cond(
                machine["overdue_ops"] > 0,
                rx.el.span(
                    f"{machine['overdue_ops']} retard",
                    class_name="rounded-none border border-[#ff6b5a]/40 bg-[#f2452c]/10 px-1.5 py-0.5 text-[9px] font-bold text-[#ff9b8c] w-fit",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        rx.el.div(
            rx.icon("user-round", class_name="h-3.5 w-3.5 text-[#d8fa5e]/80"),
            rx.el.span(
                machine["responsible"],
                class_name="text-[11px] font-medium text-[#c9c5b4]/60 truncate",
            ),
            class_name="flex items-center gap-1.5 w-full mt-2 min-w-0",
        ),
        rx.el.div(
            rx.el.div(
                class_name=rx.match(
                    machine["health_tone"],
                    (
                        "good",
                        "h-full rounded-none bg-gradient-to-r from-[#8fb37a] to-[#d8fa5e]",
                    ),
                    ("warn", "h-full rounded-none bg-[#ff8a5b]"),
                    "h-full rounded-none bg-[#ff6b5a]",
                ),
                style={"width": machine["health_pct"]},
            ),
            class_name="h-1.5 w-full rounded-none bg-[#20241a] mt-3",
        ),
        rx.el.div(
            rx.el.span(
                f"{machine['usage_counter']:.0f} {machine['usage_unit_label']}",
                class_name="text-[10px] font-semibold text-[#c9c5b4]/65",
            ),
            rx.el.span(
                f"{machine['cost_year']:.0f} € / 12 m",
                class_name="text-[10px] font-medium text-[#c9c5b4]/45",
            ),
            rx.el.span(
                machine["health_label"],
                class_name=rx.match(
                    machine["health_tone"],
                    ("good", "text-[10px] font-bold text-[#e4ff9b] ml-auto"),
                    ("warn", "text-[10px] font-bold text-[#ffb894] ml-auto"),
                    "text-[10px] font-bold text-[#ff9b8c] ml-auto",
                ),
            ),
            class_name="flex items-center gap-2 w-full mt-2",
        ),
        on_click=MaintenanceState.select_equipment(machine["id"]),
        key=key,
        class_name=rx.cond(
            MaintenanceState.selected_equipment_id == machine["id"],
            "w-full rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/[0.07] p-4 text-left ring-2 ring-[#d8fa5e]/40 transition-all",
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 text-left hover:border-[#d8fa5e]/25 transition-all",
        ),
    )


def equipment_list() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Registre",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Flotte",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                MaintenanceState.equipment_count,
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-xs font-bold text-[#c9c5b4]/70 w-fit",
            ),
            class_name="flex items-end justify-between gap-3",
        ),
        rx.cond(
            MaintenanceState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-none bg-[#16190f]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-none bg-[#16190f]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-none bg-[#16190f]"
                ),
                class_name="flex flex-col gap-3 mt-5",
            ),
            rx.cond(
                MaintenanceState.equipments.length() > 0,
                rx.el.div(
                    rx.foreach(
                        MaintenanceState.equipments,
                        lambda m: _equipment_card(m, key=m["id"].to_string()),
                    ),
                    class_name="flex flex-col gap-3 mt-5 max-h-[46rem] overflow-y-auto pr-1",
                ),
                rx.el.div(
                    rx.icon("search-x", class_name="h-6 w-6 text-[#ff8a5b]"),
                    rx.el.p(
                        "Aucun engin ne correspond aux filtres.",
                        class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2 text-center",
                    ),
                    class_name="flex flex-col items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#101208] py-12 mt-5",
                ),
            ),
        ),
        class_name="w-full xl:w-[24rem] shrink-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5 ",
    )

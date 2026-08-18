import reflex as rx

from app.states.maintenance_state import EquipmentRow, MaintenanceState


def _status_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit whitespace-nowrap",
            ),
            (
                "warn",
                "rounded-full border border-amber-300/30 bg-amber-300/10 px-2 py-0.5 text-[10px] font-bold text-amber-200 w-fit whitespace-nowrap",
            ),
            (
                "bad",
                "rounded-full border border-red-400/30 bg-red-500/10 px-2 py-0.5 text-[10px] font-bold text-red-300 w-fit whitespace-nowrap",
            ),
            (
                "info",
                "rounded-full border border-sky-300/30 bg-sky-300/10 px-2 py-0.5 text-[10px] font-bold text-sky-200 w-fit whitespace-nowrap",
            ),
            "rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/45 w-fit whitespace-nowrap",
        ),
    )


def _equipment_card(machine: EquipmentRow, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.el.div(
                rx.icon(machine["icon"], class_name="h-4 w-4 text-lime-300"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/[0.05]",
            ),
            rx.el.div(
                rx.el.p(
                    machine["name"],
                    class_name="text-sm font-semibold text-emerald-50 truncate text-left",
                ),
                rx.el.p(
                    f"{machine['code']} · {machine['brand_model']}",
                    class_name="text-[11px] font-medium text-emerald-100/50 truncate text-left",
                ),
                class_name="min-w-0 flex-1",
            ),
            _status_badge(machine["status_tone"], machine["status_label"]),
            class_name="flex items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.el.span(
                machine["category_label"],
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                machine["ownership_label"],
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/50 w-fit",
            ),
            rx.cond(
                machine["overdue_ops"] > 0,
                rx.el.span(
                    f"{machine['overdue_ops']} retard",
                    class_name="rounded-full border border-red-400/40 bg-red-500/10 px-1.5 py-0.5 text-[9px] font-bold text-red-300 w-fit",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        rx.el.div(
            rx.icon("user-round", class_name="h-3.5 w-3.5 text-lime-300/80"),
            rx.el.span(
                machine["responsible"],
                class_name="text-[11px] font-medium text-emerald-100/60 truncate",
            ),
            class_name="flex items-center gap-1.5 w-full mt-2 min-w-0",
        ),
        rx.el.div(
            rx.el.div(
                class_name=rx.match(
                    machine["health_tone"],
                    (
                        "good",
                        "h-full rounded-full bg-gradient-to-r from-emerald-400 to-lime-300",
                    ),
                    ("warn", "h-full rounded-full bg-amber-300"),
                    "h-full rounded-full bg-red-400",
                ),
                style={"width": machine["health_pct"]},
            ),
            class_name="h-1.5 w-full rounded-full bg-white/10 mt-3",
        ),
        rx.el.div(
            rx.el.span(
                f"{machine['usage_counter']:.0f} {machine['usage_unit_label']}",
                class_name="text-[10px] font-semibold text-emerald-100/65",
            ),
            rx.el.span(
                f"{machine['cost_year']:.0f} € / 12 m",
                class_name="text-[10px] font-medium text-emerald-100/45",
            ),
            rx.el.span(
                machine["health_label"],
                class_name=rx.match(
                    machine["health_tone"],
                    ("good", "text-[10px] font-bold text-lime-200 ml-auto"),
                    ("warn", "text-[10px] font-bold text-amber-200 ml-auto"),
                    "text-[10px] font-bold text-red-300 ml-auto",
                ),
            ),
            class_name="flex items-center gap-2 w-full mt-2",
        ),
        on_click=MaintenanceState.select_equipment(machine["id"]),
        key=key,
        class_name=rx.cond(
            MaintenanceState.selected_equipment_id == machine["id"],
            "w-full rounded-2xl border border-lime-300/40 bg-lime-300/[0.07] p-4 text-left ring-2 ring-lime-300/40 transition-all",
            "w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left hover:border-lime-300/25 transition-all",
        ),
    )


def equipment_list() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Registre",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Flotte",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                MaintenanceState.equipment_count,
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-bold text-emerald-100/70 w-fit",
            ),
            class_name="flex items-end justify-between gap-3",
        ),
        rx.cond(
            MaintenanceState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-2xl bg-white/[0.05]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-2xl bg-white/[0.05]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-2xl bg-white/[0.05]"
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
                    rx.icon("search-x", class_name="h-6 w-6 text-amber-300"),
                    rx.el.p(
                        "Aucun engin ne correspond aux filtres.",
                        class_name="text-sm font-medium text-emerald-100/60 mt-2 text-center",
                    ),
                    class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-12 mt-5",
                ),
            ),
        ),
        class_name="w-full xl:w-[24rem] shrink-0 rounded-3xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl",
    )

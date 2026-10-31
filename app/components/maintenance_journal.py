import reflex as rx

from app.states.maintenance_state import (
    MaintenanceState,
    OperationRow,
    Option,
)

_SELECT = "w-full appearance-none cursor-pointer rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] py-2.5 pl-9 pr-9 text-sm font-medium text-[#f2efe4] focus:border-[#d8fa5e]/50 focus:ring-2 focus:ring-[#d8fa5e]/20 outline-hidden transition-colors"


def _status_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "done",
                "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit whitespace-nowrap",
            ),
            (
                "running",
                "rounded-none border border-[#a9c98b]/30 bg-[#a9c98b]/10 px-2 py-0.5 text-[10px] font-bold text-[#b3af9f] w-fit whitespace-nowrap",
            ),
            (
                "late",
                "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffb894] w-fit whitespace-nowrap",
            ),
            (
                "cancelled",
                "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-bold text-[#c9c5b4]/40 line-through w-fit whitespace-nowrap",
            ),
            "rounded-none border border-[#9cc3ff]/30 bg-[#9cc3ff]/10 px-2 py-0.5 text-[10px] font-bold text-[#c3daff] w-fit whitespace-nowrap",
        ),
    )


def _priority_badge(priority: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            priority,
            (
                "URGENTE",
                "rounded-none border border-[#ff6b5a]/40 bg-[#f2452c]/10 px-1.5 py-0.5 text-[9px] font-bold text-[#ff9b8c] w-fit whitespace-nowrap",
            ),
            (
                "HAUTE",
                "rounded-none border border-[#ff8a5b]/40 bg-[#ff8a5b]/10 px-1.5 py-0.5 text-[9px] font-bold text-[#ffb894] w-fit whitespace-nowrap",
            ),
            (
                "NORMALE",
                "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-1.5 py-0.5 text-[9px] font-semibold text-[#c9c5b4]/55 w-fit whitespace-nowrap",
            ),
            "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-1.5 py-0.5 text-[9px] font-semibold text-[#c9c5b4]/35 w-fit whitespace-nowrap",
        ),
    )


def _kind_icon(kind: rx.Var, class_name: str) -> rx.Component:
    return rx.match(
        kind,
        ("PREVENTIVE", rx.icon("calendar-clock", class_name=class_name)),
        ("CORRECTIVE", rx.icon("wrench", class_name=class_name)),
        ("REGLEMENTAIRE", rx.icon("badge-check", class_name=class_name)),
        ("AMELIORATION", rx.icon("sparkles", class_name=class_name)),
        rx.icon("cog", class_name=class_name),
    )


def _filter_select(
    name: str,
    icon: str,
    value: rx.Var | str,
    on_change: rx.event.EventType,
    first_option: rx.Component,
    options: rx.Var[list[Option]],
) -> rx.Component:
    return rx.el.div(
        rx.icon(
            icon,
            class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#d8fa5e]/80 pointer-events-none",
        ),
        rx.el.select(
            first_option,
            rx.foreach(
                options,
                lambda opt: rx.el.option(opt["label"], value=opt["value"]),
            ),
            name=name,
            default_value=value,
            key=f"{name}-{MaintenanceState.form_key}",
            on_change=on_change,
            class_name=_SELECT,
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
        ),
        class_name="relative w-full sm:w-52",
    )


def _filters() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "search",
                class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
            ),
            rx.el.input(
                placeholder="Rechercher une opération, un engin, un prestataire, une panne…",
                default_value=MaintenanceState.journal_search,
                on_change=MaintenanceState.set_journal_search.debounce(400),
                class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] py-2.5 pl-9 pr-3 text-sm font-medium text-[#f2efe4] placeholder:text-[#c9c5b4]/30 focus:border-[#d8fa5e]/50 focus:ring-2 focus:ring-[#d8fa5e]/20 outline-hidden transition-colors",
            ),
            class_name="relative flex-1 min-w-0",
        ),
        _filter_select(
            "kind_filter",
            "wrench",
            MaintenanceState.kind_filter,
            MaintenanceState.set_kind_filter,
            rx.el.option("Toutes les natures", value="TOUS"),
            MaintenanceState.kind_options,
        ),
        _filter_select(
            "op_status_filter",
            "flag",
            MaintenanceState.op_status_filter,
            MaintenanceState.set_op_status_filter,
            rx.el.option("Tous les statuts", value="TOUS"),
            MaintenanceState.op_status_options,
        ),
        _filter_select(
            "equipment_filter",
            "tractor",
            MaintenanceState.equipment_filter,
            MaintenanceState.set_equipment_filter,
            rx.el.option("Tous les engins", value="TOUS"),
            MaintenanceState.equipment_options,
        ),
        rx.el.button(
            rx.icon("rotate-ccw", class_name="h-4 w-4"),
            rx.el.span("Réinitialiser"),
            on_click=MaintenanceState.reset_journal_filters,
            class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2.5 text-sm font-semibold text-[#c9c5b4]/70 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit",
        ),
        rx.el.button(
            rx.icon("plus", class_name="h-4 w-4 text-[#0A0A08]"),
            rx.el.span("Planifier", class_name="text-[#0A0A08]"),
            on_click=MaintenanceState.open_operation_create,
            class_name="flex items-center gap-2 rounded-none bg-[#d8fa5e] px-4 py-2.5 text-sm font-semibold hover:bg-[#e4ff9b] transition-colors w-fit",
        ),
        class_name="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-3 w-full mt-5",
    )


def _header_cell(label: str, icon: str, extra: str = "") -> rx.Component:
    return rx.el.th(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-[#d8fa5e]/70"),
            rx.el.span(label),
            class_name="flex items-center gap-1.5",
        ),
        class_name=f"px-3 py-3 text-left ap-eyebrow text-[#c9c5b4]/45 whitespace-nowrap {extra}",
    )


def _actions(row: OperationRow) -> rx.Component:
    return rx.el.div(
        rx.cond(
            row["is_closed"],
            rx.fragment(),
            rx.el.button(
                rx.icon("play", class_name="h-3.5 w-3.5"),
                on_click=MaintenanceState.start_operation(row["id"]),
                title="Démarrer à l'atelier",
                class_name="flex h-7 w-7 items-center justify-center rounded-none border border-[#a9c98b]/30 bg-[#a9c98b]/10 text-[#b3af9f] hover:bg-[#a9c98b]/20 transition-colors",
            ),
        ),
        rx.cond(
            row["is_closed"],
            rx.fragment(),
            rx.el.button(
                rx.icon("check", class_name="h-3.5 w-3.5"),
                on_click=MaintenanceState.mark_operation_done(row["id"]),
                title="Marquer réalisée",
                class_name="flex h-7 w-7 items-center justify-center rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 text-[#e4ff9b] hover:bg-[#d8fa5e]/20 transition-colors",
            ),
        ),
        rx.cond(
            row["is_closed"],
            rx.fragment(),
            rx.el.button(
                rx.icon("calendar-plus", class_name="h-3.5 w-3.5"),
                on_click=MaintenanceState.postpone_operation(row["id"]),
                title="Reporter de 7 jours",
                class_name="flex h-7 w-7 items-center justify-center rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 text-[#ffb894] hover:bg-[#ff8a5b]/20 transition-colors",
            ),
        ),
        rx.el.button(
            rx.icon("pencil", class_name="h-3.5 w-3.5"),
            on_click=MaintenanceState.open_operation_edit(row["id"]),
            title="Modifier",
            class_name="flex h-7 w-7 items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#14160f] text-[#c9c5b4]/70 hover:text-[#f2efe4] hover:border-[#d8fa5e]/30 transition-colors",
        ),
        rx.cond(
            row["is_closed"],
            rx.fragment(),
            rx.el.button(
                rx.icon("x", class_name="h-3.5 w-3.5"),
                on_click=MaintenanceState.cancel_operation(row["id"]),
                title="Annuler",
                class_name="flex h-7 w-7 items-center justify-center rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 text-[#ff9b8c] hover:bg-[#f2452c]/20 transition-colors",
            ),
        ),
        class_name="flex items-center gap-1.5 justify-end",
    )


def _journal_row(row: OperationRow, key: str = "") -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                rx.el.div(
                    _kind_icon(row["kind"], "h-4 w-4 text-[#d8fa5e]"),
                    class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#14160f]",
                ),
                rx.el.div(
                    rx.el.p(
                        row["title"],
                        class_name="text-sm font-semibold text-[#f2efe4] truncate",
                    ),
                    rx.el.p(
                        f"{row['kind_label']} · {row['provider']}",
                        class_name="text-[10px] font-medium text-[#c9c5b4]/45 truncate",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-center gap-2.5 min-w-0",
            ),
            class_name="px-3 py-3 align-middle min-w-[16rem]",
        ),
        rx.el.td(
            rx.el.button(
                rx.el.p(
                    row["code"],
                    class_name="text-xs font-semibold text-[#f2efe4] text-left",
                ),
                rx.el.p(
                    row["equipment"],
                    class_name="text-[10px] font-medium text-[#c9c5b4]/45 truncate text-left",
                ),
                on_click=MaintenanceState.select_equipment(row["equipment_id"]),
                class_name="min-w-0 text-left hover:text-[#e4ff9b] transition-colors",
            ),
            class_name="px-3 py-3 align-middle min-w-[11rem]",
        ),
        rx.el.td(
            rx.el.p(
                row["due_label"],
                class_name="text-xs font-semibold text-[#f2efe4] whitespace-nowrap",
            ),
            rx.el.p(
                rx.cond(
                    row["is_overdue"],
                    f"retard de {row['days_delta'] * -1} j",
                    rx.cond(
                        row["is_closed"],
                        f"fait le {row['done_label']}",
                        rx.cond(
                            row["days_delta"] == 0,
                            "aujourd'hui",
                            f"dans {row['days_delta']} j",
                        ),
                    ),
                ),
                class_name=rx.cond(
                    row["is_overdue"],
                    "text-[10px] font-semibold text-[#ff9b8c] whitespace-nowrap",
                    "text-[10px] font-medium text-[#c9c5b4]/45 whitespace-nowrap",
                ),
            ),
            class_name="px-3 py-3 align-middle",
        ),
        rx.el.td(
            rx.el.div(
                _status_badge(row["tone"], row["status_label"]),
                _priority_badge(row["priority"], row["priority_label"]),
                class_name="flex flex-col items-start gap-1",
            ),
            class_name="px-3 py-3 align-middle",
        ),
        rx.el.td(
            rx.el.p(
                row["responsible"],
                class_name="text-xs font-medium text-[#c9c5b4]/70 truncate",
            ),
            rx.el.p(
                rx.cond(row["is_internal"], "Atelier interne", "Externalisée"),
                class_name="text-[10px] font-medium text-[#c9c5b4]/40",
            ),
            class_name="px-3 py-3 align-middle min-w-[10rem]",
        ),
        rx.el.td(
            rx.el.span(
                f"{row['labor_hours']:.1f} h MO",
                class_name="text-[11px] font-medium text-[#c9c5b4]/65 whitespace-nowrap",
            ),
            rx.el.p(
                f"{row['downtime']:.1f} h immo.",
                class_name="text-[10px] font-medium text-[#c9c5b4]/40 whitespace-nowrap",
            ),
            class_name="px-3 py-3 align-middle",
        ),
        rx.el.td(
            rx.el.span(
                f"{row['total_cost']:.0f} €",
                class_name="text-xs font-semibold text-[#e4ff9b] whitespace-nowrap",
            ),
            class_name="px-3 py-3 align-middle text-right",
        ),
        rx.el.td(
            _actions(row),
            class_name="px-3 py-3 align-middle",
        ),
        key=key,
        class_name=rx.cond(
            row["is_overdue"],
            "border-b border-[#f2efe4]/8 bg-[#f2452c]/[0.05] hover:bg-[#f2452c]/[0.09] transition-colors",
            "border-b border-[#f2efe4]/8 even:bg-[#0d0f09] hover:bg-[#d8fa5e]/[0.05] transition-colors",
        ),
    )


def maintenance_journal() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Journal atelier",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Opérations préventives & correctives",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{MaintenanceState.operation_count} lignes",
                    class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/60 w-fit",
                ),
                rx.el.span(
                    f"{MaintenanceState.kpis['overdue_ops']:.0f} en retard",
                    class_name="rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-3 py-1 text-[11px] font-semibold text-[#ffb894] w-fit",
                ),
                rx.el.span(
                    f"{MaintenanceState.operation_cost_shown:.0f} € engagés",
                    class_name="rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-3 py-1 text-[11px] font-semibold text-[#e4ff9b] w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4",
        ),
        _filters(),
        rx.cond(
            MaintenanceState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-12 rounded-none bg-[#16190f]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-12 rounded-none bg-[#16190f]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-12 rounded-none bg-[#16190f]"
                ),
                class_name="flex flex-col gap-2 mt-6",
            ),
            rx.cond(
                MaintenanceState.operations.length() > 0,
                rx.el.div(
                    rx.el.div(
                        rx.el.table(
                            rx.el.thead(
                                rx.el.tr(
                                    _header_cell("Opération", "clipboard-list"),
                                    _header_cell("Engin", "tractor"),
                                    _header_cell("Échéance", "calendar-days"),
                                    _header_cell("Statut", "flag"),
                                    _header_cell("Responsable", "user-round"),
                                    _header_cell("Durées", "clock"),
                                    _header_cell("Coût", "coins", "text-right"),
                                    _header_cell("Actions", "settings_2"),
                                    class_name="border-b border-[#f2efe4]/12 bg-[#101208]",
                                ),
                            ),
                            rx.el.tbody(
                                rx.foreach(
                                    MaintenanceState.operations,
                                    lambda row: _journal_row(
                                        row, key=row["id"].to_string()
                                    ),
                                ),
                            ),
                            class_name="table-auto w-full min-w-[66rem]",
                        ),
                        class_name="overflow-x-auto",
                    ),
                    class_name="mt-6 w-full rounded-none border border-[#f2efe4]/12 bg-[#0D0F09]/60 overflow-hidden max-h-[42rem] overflow-y-auto",
                ),
                rx.el.div(
                    rx.icon("search-x", class_name="h-6 w-6 text-[#ff8a5b]"),
                    rx.el.p(
                        "Aucune opération de maintenance ne correspond aux filtres.",
                        class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2 text-center",
                    ),
                    class_name="flex flex-col items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#101208] py-14 mt-6",
                ),
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )

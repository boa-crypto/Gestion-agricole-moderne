import reflex as rx

from app.states.maintenance_state import (
    CostRow,
    MaintenanceState,
    ScheduleRow,
    UsageRow,
)

_INPUT = "w-full rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] px-3 py-2.5 text-sm font-medium text-[#f2efe4] placeholder:text-[#c9c5b4]/30 focus:border-[#d8fa5e]/50 outline-hidden transition-colors"
_SELECT = f"{_INPUT} appearance-none cursor-pointer pr-9"


def _fact(label: str, value: rx.Var | str, icon: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-[#d8fa5e]/80"),
            rx.el.span(
                label,
                class_name="ap-eyebrow text-[#c9c5b4]/45",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            value,
            class_name="text-sm font-semibold text-[#f2efe4] mt-1.5 truncate",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3 min-w-0",
    )


def _tone_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
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


def _detail_header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    MaintenanceState.equipment_detail["icon"],
                    class_name="h-6 w-6 text-[#0A0A08]",
                ),
                class_name="flex h-14 w-14 shrink-0 items-center justify-center rounded-none bg-[#d8fa5e]",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        MaintenanceState.equipment_detail["code"],
                        class_name="ap-eyebrow text-[#d8fa5e]/80",
                    ),
                    _tone_badge(
                        MaintenanceState.equipment_detail["status_tone"],
                        MaintenanceState.equipment_detail["status_label"],
                    ),
                    _tone_badge(
                        MaintenanceState.equipment_detail["health_tone"],
                        MaintenanceState.equipment_detail["health_label"],
                    ),
                    class_name="flex flex-wrap items-center gap-2",
                ),
                rx.el.h2(
                    MaintenanceState.equipment_detail["name"],
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                rx.el.p(
                    f"{MaintenanceState.equipment_detail['category_label']} · {MaintenanceState.equipment_detail['brand']} {MaintenanceState.equipment_detail['model']} · {MaintenanceState.equipment_detail['ownership_label']}",
                    class_name="text-xs font-medium text-[#c9c5b4]/55 mt-1",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-center gap-4 min-w-0",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("pencil", class_name="h-4 w-4"),
                rx.el.span("Modifier l'engin"),
                on_click=MaintenanceState.open_equipment_edit,
                class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2.5 text-sm font-semibold text-[#c9c5b4]/75 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit",
            ),
            rx.el.button(
                rx.icon("wrench", class_name="h-4 w-4 text-[#0A0A08]"),
                rx.el.span("Nouvelle opération", class_name="text-[#0A0A08]"),
                on_click=MaintenanceState.open_operation_create,
                class_name="flex items-center gap-2 rounded-none bg-[#d8fa5e] px-4 py-2.5 text-sm font-semibold hover:bg-[#e4ff9b] transition-colors w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
        class_name="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-5 border-b border-[#f2efe4]/12",
    )


def _health_bar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Indice de santé machine",
                class_name="ap-eyebrow text-[#c9c5b4]/45",
            ),
            rx.el.span(
                f"{MaintenanceState.equipment_detail['health']} / 100",
                class_name="text-[11px] font-bold text-[#e4ff9b] ml-auto",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.div(
            rx.el.div(
                class_name=rx.match(
                    MaintenanceState.equipment_detail["health_tone"],
                    (
                        "good",
                        "h-full rounded-none bg-gradient-to-r from-[#8fb37a] to-[#d8fa5e]",
                    ),
                    ("warn", "h-full rounded-none bg-[#ff8a5b]"),
                    "h-full rounded-none bg-[#ff6b5a]",
                ),
                style={
                    "width": MaintenanceState.equipment_detail["health_pct"]
                },
            ),
            class_name="h-2 w-full rounded-none bg-[#20241a] mt-2",
        ),
        class_name="mt-5",
    )


def _schedule_card(schedule: ScheduleRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("calendar-clock", class_name="h-4 w-4 text-[#d8fa5e]"),
                class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#16190f]",
            ),
            rx.el.div(
                rx.el.p(
                    schedule["title"],
                    class_name="text-sm font-semibold text-[#f2efe4] truncate",
                ),
                rx.el.p(
                    f"{schedule['kind_label']} · déclenchement {schedule['basis_label']}",
                    class_name="text-[10px] font-medium text-[#c9c5b4]/45 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            _tone_badge(
                schedule["tone"],
                rx.cond(
                    schedule["days_left"] < 0,
                    f"retard {schedule['days_left'] * -1} j",
                    f"J-{schedule['days_left']}",
                ),
            ),
            class_name="flex items-center gap-2.5 w-full",
        ),
        rx.el.div(
            rx.el.span(
                f"Prochaine échéance {schedule['next_due_label']}",
                class_name="text-[11px] font-medium text-[#c9c5b4]/60",
            ),
            rx.el.span(
                f"seuil compteur {schedule['next_due_counter']:.0f}",
                class_name="text-[10px] font-medium text-[#c9c5b4]/40",
            ),
            class_name="flex flex-wrap items-center gap-3 mt-3",
        ),
        rx.el.div(
            rx.el.span(
                f"Intervalle {schedule['interval_days']} j / {schedule['interval_counter']:.0f} u",
                class_name="text-[10px] font-medium text-[#c9c5b4]/45",
            ),
            rx.el.span(
                f"Dernier fait {schedule['last_done_label']}",
                class_name="text-[10px] font-medium text-[#c9c5b4]/45",
            ),
            rx.el.span(
                f"{schedule['estimated_cost']:.0f} € · {schedule['estimated_hours']:.1f} h",
                class_name="text-[10px] font-bold text-[#e4ff9b] ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3 mt-2",
        ),
        rx.el.div(
            rx.icon("user-round", class_name="h-3 w-3 text-[#a9c98b]/70"),
            rx.el.span(
                schedule["responsible"],
                class_name="text-[10px] font-medium text-[#c9c5b4]/50 truncate",
            ),
            rx.el.button(
                rx.icon("plus", class_name="h-3.5 w-3.5"),
                rx.el.span("Planifier", class_name="text-[11px]"),
                on_click=MaintenanceState.open_schedule_operation(
                    schedule["id"]
                ),
                class_name="flex items-center gap-1.5 rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2.5 py-1 text-[#e4ff9b] hover:bg-[#d8fa5e]/20 transition-colors w-fit ml-auto shrink-0",
            ),
            class_name="flex items-center gap-1.5 border-t border-[#f2efe4]/8 pt-3 mt-3 min-w-0",
        ),
        rx.el.p(
            schedule["checklist"],
            class_name="text-[10px] font-medium text-[#c9c5b4]/35 mt-2 leading-relaxed",
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 hover:border-[#d8fa5e]/25 transition-colors",
    )


def _cost_row(cost: CostRow, key: str = "") -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.p(
                cost["label"],
                class_name="text-xs font-semibold text-[#f2efe4] truncate",
            ),
            rx.el.p(
                f"{cost['operation']} · réf. {cost['reference']}",
                class_name="text-[10px] font-medium text-[#c9c5b4]/40 truncate",
            ),
            class_name="px-3 py-2.5 align-middle min-w-[15rem]",
        ),
        rx.el.td(
            rx.el.span(
                cost["type_label"],
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        rx.el.td(
            rx.el.span(
                f"{cost['quantity']:.2f} {cost['unit']}",
                class_name="text-[11px] font-medium text-[#c9c5b4]/65 whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        rx.el.td(
            rx.el.span(
                f"{cost['unit_price']:.2f} €",
                class_name="text-[11px] font-medium text-[#c9c5b4]/65 whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        rx.el.td(
            rx.el.span(
                f"{cost['amount']:.2f} €",
                class_name="text-xs font-bold text-[#e4ff9b] whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-middle text-right",
        ),
        rx.el.td(
            rx.el.p(
                cost["supplier"],
                class_name="text-[11px] font-medium text-[#c9c5b4]/55 truncate",
            ),
            rx.el.p(
                cost["date_label"],
                class_name="text-[10px] font-medium text-[#c9c5b4]/35 whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-middle min-w-[9rem]",
        ),
        rx.el.td(
            rx.el.button(
                rx.icon("trash-2", class_name="h-3.5 w-3.5"),
                on_click=MaintenanceState.remove_cost(cost["id"]),
                title="Supprimer la ligne",
                class_name="flex h-7 w-7 items-center justify-center rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 text-[#ff9b8c] hover:bg-[#f2452c]/20 transition-colors ml-auto",
            ),
            class_name="px-3 py-2.5 align-middle",
        ),
        key=key,
        class_name="border-b border-[#f2efe4]/8 even:bg-[#0d0f09] hover:bg-[#d8fa5e]/[0.05] transition-colors",
    )


def _head(label: str, extra: str = "") -> rx.Component:
    return rx.el.th(
        label,
        class_name=f"px-3 py-3 text-left ap-eyebrow text-[#c9c5b4]/45 whitespace-nowrap {extra}",
    )


def _cost_form() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            rx.el.div(
                rx.el.select(
                    rx.el.option(
                        "Opération concernée", value="", disabled=True
                    ),
                    rx.foreach(
                        MaintenanceState.operation_options,
                        lambda opt: rx.el.option(
                            opt["label"], value=opt["value"]
                        ),
                    ),
                    name="maintenance_id",
                    default_value="",
                    key=f"cost-op-{MaintenanceState.form_key}",
                    class_name=_SELECT,
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
                ),
                class_name="relative w-full",
            ),
            rx.el.div(
                rx.el.select(
                    rx.foreach(
                        MaintenanceState.cost_type_options,
                        lambda opt: rx.el.option(
                            opt["label"], value=opt["value"]
                        ),
                    ),
                    name="type",
                    default_value="PIECE",
                    key=f"cost-type-{MaintenanceState.form_key}",
                    class_name=_SELECT,
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
                ),
                class_name="relative w-full",
            ),
            rx.el.input(
                name="label",
                placeholder="Libellé (pièce, prestation…)",
                key=f"cost-label-{MaintenanceState.form_key}",
                class_name=_INPUT,
            ),
            rx.el.input(
                name="reference",
                placeholder="Référence",
                key=f"cost-ref-{MaintenanceState.form_key}",
                class_name=_INPUT,
            ),
            rx.el.input(
                name="supplier",
                placeholder="Fournisseur",
                key=f"cost-supplier-{MaintenanceState.form_key}",
                class_name=_INPUT,
            ),
            rx.el.input(
                type="number",
                step="0.01",
                name="quantity",
                placeholder="Quantité",
                default_value="1",
                key=f"cost-qty-{MaintenanceState.form_key}",
                class_name=_INPUT,
            ),
            rx.el.input(
                name="unit",
                placeholder="Unité",
                default_value="u",
                key=f"cost-unit-{MaintenanceState.form_key}",
                class_name=_INPUT,
            ),
            rx.el.input(
                type="number",
                step="0.01",
                name="unit_price",
                placeholder="Prix unitaire (€)",
                default_value="0",
                key=f"cost-price-{MaintenanceState.form_key}",
                class_name=_INPUT,
            ),
            rx.el.input(
                type="date",
                name="incurred_on",
                key=f"cost-date-{MaintenanceState.form_key}",
                class_name=_INPUT,
            ),
            class_name="grid grid-cols-1 md:grid-cols-3 gap-3",
        ),
        rx.cond(
            MaintenanceState.cost_error != "",
            rx.el.p(
                MaintenanceState.cost_error,
                class_name="text-xs font-semibold text-[#ff9b8c] mt-2",
            ),
            rx.fragment(),
        ),
        rx.el.button(
            rx.icon("receipt-text", class_name="h-4 w-4 text-[#0A0A08]"),
            rx.el.span("Ajouter la ligne de coût", class_name="text-[#0A0A08]"),
            type="submit",
            class_name="flex items-center gap-2 rounded-none bg-[#d8fa5e] px-4 py-2.5 text-sm font-semibold hover:bg-[#e4ff9b] transition-colors w-fit mt-3",
        ),
        on_submit=MaintenanceState.submit_cost,
        reset_on_submit=True,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 mt-4",
    )


def _usage_row(usage: UsageRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("gauge", class_name="h-4 w-4 text-[#d8fa5e]"),
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#16190f]",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    usage["date_label"],
                    class_name="text-xs font-semibold text-[#f2efe4]",
                ),
                rx.el.span(
                    usage["operator"],
                    class_name="text-[10px] font-medium text-[#c9c5b4]/45 truncate",
                ),
                class_name="flex items-center gap-2 min-w-0",
            ),
            rx.el.p(
                f"{usage['counter_start']:.0f} → {usage['counter_end']:.0f} · {usage['hours_used']:.1f} u · {usage['fuel_liters']:.0f} L",
                class_name="text-[11px] font-medium text-[#c9c5b4]/55 mt-1",
            ),
            rx.el.p(
                usage["notes"],
                class_name="text-[10px] font-medium text-[#c9c5b4]/35 truncate",
            ),
            class_name="min-w-0 flex-1",
        ),
        key=key,
        class_name="flex items-center gap-3 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
    )


def _usage_form() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            rx.el.input(
                type="date",
                name="used_on",
                key=f"usage-date-{MaintenanceState.form_key}",
                class_name=_INPUT,
            ),
            rx.el.div(
                rx.el.select(
                    rx.el.option("Opérateur (facultatif)", value=""),
                    rx.foreach(
                        MaintenanceState.employee_options,
                        lambda opt: rx.el.option(
                            opt["label"], value=opt["value"]
                        ),
                    ),
                    name="employee_id",
                    default_value="",
                    key=f"usage-emp-{MaintenanceState.form_key}",
                    class_name=_SELECT,
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
                ),
                class_name="relative w-full",
            ),
            rx.el.input(
                type="number",
                step="0.1",
                name="counter_start",
                placeholder="Compteur début",
                default_value=MaintenanceState.equipment_detail[
                    "usage_counter"
                ],
                key=f"usage-start-{MaintenanceState.form_key}",
                class_name=_INPUT,
            ),
            rx.el.input(
                type="number",
                step="0.1",
                name="counter_end",
                placeholder="Compteur fin",
                key=f"usage-end-{MaintenanceState.form_key}",
                class_name=_INPUT,
            ),
            rx.el.input(
                type="number",
                step="0.1",
                name="fuel_liters",
                placeholder="Carburant (L)",
                default_value="0",
                key=f"usage-fuel-{MaintenanceState.form_key}",
                class_name=_INPUT,
            ),
            rx.el.input(
                name="notes",
                placeholder="Chantier, observation…",
                key=f"usage-notes-{MaintenanceState.form_key}",
                class_name=_INPUT,
            ),
            class_name="grid grid-cols-1 md:grid-cols-3 gap-3",
        ),
        rx.cond(
            MaintenanceState.usage_error != "",
            rx.el.p(
                MaintenanceState.usage_error,
                class_name="text-xs font-semibold text-[#ff9b8c] mt-2",
            ),
            rx.fragment(),
        ),
        rx.el.button(
            rx.icon("gauge", class_name="h-4 w-4 text-[#0A0A08]"),
            rx.el.span("Enregistrer le relevé", class_name="text-[#0A0A08]"),
            type="submit",
            class_name="flex items-center gap-2 rounded-none bg-[#d8fa5e] px-4 py-2.5 text-sm font-semibold hover:bg-[#e4ff9b] transition-colors w-fit mt-3",
        ),
        on_submit=MaintenanceState.submit_usage,
        reset_on_submit=True,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 mt-4",
    )


def _schedules_block() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Échéances préventives",
                class_name="ap-eyebrow text-[#d8fa5e]/80",
            ),
            rx.el.span(
                f"Prochain entretien {MaintenanceState.equipment_detail['next_service_label']}",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/60 w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3",
        ),
        rx.cond(
            MaintenanceState.schedules.length() > 0,
            rx.el.div(
                rx.foreach(
                    MaintenanceState.schedules,
                    lambda s: _schedule_card(s, key=s["id"].to_string()),
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 mt-4",
            ),
            rx.el.p(
                "Aucun plan d'entretien préventif défini pour cet engin.",
                class_name="text-sm font-medium text-[#c9c5b4]/50 mt-4",
            ),
        ),
        class_name="mt-8",
    )


def _costs_block() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Coûts de maintenance",
                class_name="ap-eyebrow text-[#ff8a5b]/80",
            ),
            rx.el.span(
                f"{MaintenanceState.equipment_detail['cost_year']} € sur 12 mois",
                class_name="rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-3 py-1 text-[11px] font-semibold text-[#e4ff9b] w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3",
        ),
        rx.cond(
            MaintenanceState.costs.length() > 0,
            rx.el.div(
                rx.el.div(
                    rx.el.table(
                        rx.el.thead(
                            rx.el.tr(
                                _head("Ligne"),
                                _head("Nature"),
                                _head("Quantité"),
                                _head("PU"),
                                _head("Montant", "text-right"),
                                _head("Fournisseur"),
                                _head(""),
                                class_name="border-b border-[#f2efe4]/12 bg-[#101208]",
                            ),
                        ),
                        rx.el.tbody(
                            rx.foreach(
                                MaintenanceState.costs,
                                lambda c: _cost_row(c, key=c["id"].to_string()),
                            ),
                        ),
                        class_name="table-auto w-full min-w-[52rem]",
                    ),
                    class_name="overflow-x-auto",
                ),
                class_name="mt-4 w-full rounded-none border border-[#f2efe4]/12 bg-[#0D0F09]/60 overflow-hidden max-h-[26rem] overflow-y-auto",
            ),
            rx.el.p(
                "Aucune ligne de coût enregistrée pour cet engin.",
                class_name="text-sm font-medium text-[#c9c5b4]/50 mt-4",
            ),
        ),
        _cost_form(),
        class_name="mt-8 border-t border-[#f2efe4]/12 pt-6",
    )


def _usage_block() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Relevés d'usage",
                class_name="ap-eyebrow text-[#d8fa5e]/80",
            ),
            rx.el.span(
                f"{MaintenanceState.equipment_detail['hours_30']} u · {MaintenanceState.equipment_detail['fuel_30']} L sur 30 j",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/60 w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3",
        ),
        rx.cond(
            MaintenanceState.usage_logs.length() > 0,
            rx.el.div(
                rx.foreach(
                    MaintenanceState.usage_logs,
                    lambda u: _usage_row(u, key=u["id"].to_string()),
                ),
                class_name="flex flex-col gap-2 mt-4",
            ),
            rx.el.p(
                "Aucun relevé de compteur pour cet engin.",
                class_name="text-sm font-medium text-[#c9c5b4]/50 mt-4",
            ),
        ),
        _usage_form(),
        class_name="mt-8 border-t border-[#f2efe4]/12 pt-6",
    )


def equipment_detail() -> rx.Component:
    return rx.el.section(
        rx.cond(
            MaintenanceState.has_selection,
            rx.el.div(
                _detail_header(),
                _health_bar(),
                rx.el.div(
                    _fact(
                        "Compteur",
                        f"{MaintenanceState.equipment_detail['usage_counter']} {MaintenanceState.equipment_detail['usage_unit_label']}",
                        "gauge",
                    ),
                    _fact(
                        "Responsable",
                        MaintenanceState.equipment_detail["responsible"],
                        "user-round",
                    ),
                    _fact(
                        "Emplacement",
                        MaintenanceState.equipment_detail["location"],
                        "map-pin",
                    ),
                    _fact(
                        "Immatriculation",
                        MaintenanceState.equipment_detail["registration"],
                        "credit-card",
                    ),
                    _fact(
                        "Année / puissance",
                        f"{MaintenanceState.equipment_detail['year']} · {MaintenanceState.equipment_detail['power']} ch",
                        "zap",
                    ),
                    _fact(
                        "Largeur de travail",
                        f"{MaintenanceState.equipment_detail['width']} m",
                        "ruler",
                    ),
                    _fact(
                        "Coût horaire",
                        f"{MaintenanceState.equipment_detail['hourly_cost']} €",
                        "coins",
                    ),
                    _fact(
                        "Consommation",
                        f"{MaintenanceState.equipment_detail['fuel']} L/h",
                        "fuel",
                    ),
                    _fact(
                        "Assurance",
                        MaintenanceState.equipment_detail["insurance_label"],
                        "shield-check",
                    ),
                    _fact(
                        "Contrôle réglementaire",
                        MaintenanceState.equipment_detail["inspection_label"],
                        "badge-check",
                    ),
                    _fact(
                        "Prochain entretien",
                        MaintenanceState.equipment_detail["next_service_label"],
                        "calendar-clock",
                    ),
                    _fact(
                        "Immobilisation 12 m",
                        f"{MaintenanceState.equipment_detail['downtime_year']} h",
                        "clock",
                    ),
                    class_name="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-5",
                ),
                rx.el.div(
                    rx.el.span(
                        f"Acquis le {MaintenanceState.equipment_detail['purchase_label']}",
                        class_name="text-[11px] font-medium text-[#c9c5b4]/55",
                    ),
                    rx.el.span(
                        f"Achat {MaintenanceState.equipment_detail['purchase_price']} € · valeur résiduelle {MaintenanceState.equipment_detail['residual_value']} €",
                        class_name="text-[11px] font-medium text-[#c9c5b4]/55",
                    ),
                    rx.el.span(
                        f"N° série {MaintenanceState.equipment_detail['serial_number']}",
                        class_name="text-[11px] font-medium text-[#c9c5b4]/40",
                    ),
                    rx.el.span(
                        f"Intervalle {MaintenanceState.equipment_detail['interval_days']} j / {MaintenanceState.equipment_detail['interval_counter']} u",
                        class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
                    ),
                    class_name="flex flex-wrap items-center gap-4 mt-4",
                ),
                rx.el.p(
                    MaintenanceState.equipment_detail["notes"],
                    class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-3 leading-relaxed",
                ),
                _schedules_block(),
                _costs_block(),
                _usage_block(),
                class_name="w-full",
            ),
            rx.el.div(
                rx.icon("tractor", class_name="h-7 w-7 text-[#d8fa5e]"),
                rx.el.p(
                    "Sélectionnez un engin dans la flotte ou ajoutez une première machine.",
                    class_name="mt-4 text-[13px] leading-relaxed text-[#C9C5B4]/70 text-center max-w-sm",
                ),
                class_name="flex flex-col items-center justify-center py-24",
            ),
        ),
        class_name="flex-1 min-w-0 w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )

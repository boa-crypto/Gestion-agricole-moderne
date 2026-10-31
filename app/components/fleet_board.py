import reflex as rx

from app.states.maintenance_state import (
    DeadlineRow,
    EquipmentRow,
    FleetAlert,
    MaintenanceState,
)


def _health_tile(machine: EquipmentRow, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.el.div(
                rx.icon(machine["icon"], class_name="h-4 w-4 text-[#d8fa5e]"),
                class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#16190f]",
            ),
            rx.el.div(
                rx.el.span(
                    machine["code"],
                    class_name="ap-eyebrow text-[#c9c5b4]/50 block text-left",
                ),
                rx.el.span(
                    machine["category_label"],
                    class_name="text-[10px] font-medium text-[#c9c5b4]/40 block text-left",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                machine["health"],
                class_name=rx.match(
                    machine["health_tone"],
                    ("good", "text-sm font-bold text-[#e4ff9b]"),
                    ("warn", "text-sm font-bold text-[#ffb894]"),
                    "text-sm font-bold text-[#ff9b8c]",
                ),
            ),
            class_name="flex items-center gap-2 w-full",
        ),
        rx.el.p(
            machine["name"],
            class_name="text-xs font-semibold text-[#f2efe4] text-left mt-2 truncate w-full",
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
            class_name="h-1.5 w-full rounded-none bg-[#20241a] mt-2",
        ),
        rx.el.div(
            rx.el.span(
                machine["status_label"],
                class_name="text-[10px] font-medium text-[#c9c5b4]/55",
            ),
            rx.el.span(
                rx.cond(
                    machine["days_to_service"] < 0,
                    f"retard {machine['days_to_service'] * -1} j",
                    f"J-{machine['days_to_service']}",
                ),
                class_name=rx.cond(
                    machine["days_to_service"] < 0,
                    "text-[10px] font-bold text-[#ff9b8c] ml-auto",
                    "text-[10px] font-semibold text-[#c9c5b4]/65 ml-auto",
                ),
            ),
            class_name="flex items-center gap-2 w-full mt-2",
        ),
        on_click=MaintenanceState.select_equipment(machine["id"]),
        key=key,
        class_name=rx.cond(
            MaintenanceState.selected_equipment_id == machine["id"],
            "w-full rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/[0.08] p-3 text-left ring-2 ring-[#d8fa5e]/40 transition-all",
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3 text-left hover:border-[#d8fa5e]/25 transition-all",
        ),
    )


def _deadline_row(item: DeadlineRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                item["code"],
                class_name="ap-eyebrow text-[#d8fa5e]/80 shrink-0 w-10",
            ),
            rx.el.div(
                rx.el.p(
                    item["title"],
                    class_name="text-xs font-semibold text-[#f2efe4] truncate",
                ),
                rx.el.p(
                    f"{item['equipment']} · {item['kind_label']}",
                    class_name="text-[10px] font-medium text-[#c9c5b4]/40 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                rx.el.span(
                    item["date_label"],
                    class_name="text-[11px] font-semibold text-[#f2efe4] block text-right whitespace-nowrap",
                ),
                rx.el.span(
                    rx.cond(
                        item["overdue"],
                        f"retard {item['days_left'] * -1} j",
                        f"dans {item['days_left']} j",
                    ),
                    class_name=rx.match(
                        item["tone"],
                        (
                            "bad",
                            "text-[10px] font-bold text-[#ff9b8c] block text-right",
                        ),
                        (
                            "warn",
                            "text-[10px] font-bold text-[#ffb894] block text-right",
                        ),
                        "text-[10px] font-medium text-[#c9c5b4]/45 block text-right",
                    ),
                ),
                class_name="shrink-0 w-28",
            ),
            class_name="flex items-center gap-3 min-w-0",
        ),
        rx.el.div(
            rx.el.div(
                class_name="absolute inset-y-0 left-0 w-px bg-[#ff6b5a]/40",
            ),
            rx.el.div(
                class_name=rx.match(
                    item["tone"],
                    (
                        "bad",
                        "absolute top-1/2 -translate-y-1/2 h-3 w-3 rounded-none bg-[#ff6b5a] ring-4 ring-[#ff6b5a]/20",
                    ),
                    (
                        "warn",
                        "absolute top-1/2 -translate-y-1/2 h-3 w-3 rounded-none bg-[#ff8a5b] ring-4 ring-[#ff8a5b]/20",
                    ),
                    "absolute top-1/2 -translate-y-1/2 h-3 w-3 rounded-none bg-[#d8fa5e] ring-4 ring-[#d8fa5e]/20",
                ),
                style={"left": item["left"]},
            ),
            class_name="relative h-4 w-full rounded-none bg-[linear-gradient(to_right,rgba(248,113,113,0.18),rgba(252,211,77,0.14)_25%,rgba(163,230,53,0.10))] mt-2",
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3 hover:border-[#d8fa5e]/25 transition-colors",
    )


def _alert_card(alert: FleetAlert, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.match(
                alert["level"],
                (
                    "CRITIQUE",
                    rx.icon("octagon-alert", class_name="h-4 w-4 text-[#ff6b5a]"),
                ),
                (
                    "ATTENTION",
                    rx.icon(
                        "triangle-alert", class_name="h-4 w-4 text-[#ff8a5b]"
                    ),
                ),
                rx.icon("info", class_name="h-4 w-4 text-[#9cc3ff]"),
            ),
            rx.el.span(
                alert["category"],
                class_name="ap-eyebrow text-[#c9c5b4]/45",
            ),
            rx.el.span(
                alert["date_label"],
                class_name="text-[10px] font-medium text-[#c9c5b4]/40 ml-auto",
            ),
            class_name="flex items-center gap-2 w-full",
        ),
        rx.el.p(
            alert["title"],
            class_name="text-sm font-semibold text-[#f2efe4] mt-2 text-left",
        ),
        rx.el.p(
            alert["message"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/55 mt-1 text-left leading-relaxed",
        ),
        rx.el.div(
            rx.icon("tractor", class_name="h-3 w-3 text-[#d8fa5e]/80"),
            rx.el.span(
                alert["equipment"],
                class_name="text-[11px] font-medium text-[#c9c5b4]/60 truncate",
            ),
            class_name="flex items-center gap-1.5 mt-3 w-full min-w-0",
        ),
        on_click=MaintenanceState.select_equipment(alert["equipment_id"]),
        key=key,
        class_name=rx.match(
            alert["level"],
            (
                "CRITIQUE",
                "w-full rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/[0.07] p-4 text-left hover:border-[#ff6b5a]/50 transition-colors",
            ),
            (
                "ATTENTION",
                "w-full rounded-none border border-[#ff8a5b]/25 bg-[#ff8a5b]/[0.06] p-4 text-left hover:border-[#ff8a5b]/45 transition-colors",
            ),
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 text-left hover:border-[#d8fa5e]/25 transition-colors",
        ),
    )


def _legend(label: str, dot: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(class_name=dot),
        rx.el.span(
            label, class_name="text-[11px] font-medium text-[#c9c5b4]/60"
        ),
        class_name="flex items-center gap-2 w-fit",
    )


def deadline_planner() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Atelier & planning machine",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Planning des échéances machine",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                rx.el.p(
                    "Horizon 90 jours : entretiens préventifs et contrôles réglementaires de la flotte.",
                    class_name="text-xs font-medium text-[#c9c5b4]/50 mt-2 max-w-xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{MaintenanceState.overdue_deadlines} en retard",
                    class_name="rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-3 py-1 text-[11px] font-semibold text-[#ffbcb0] w-fit",
                ),
                rx.el.span(
                    f"{MaintenanceState.deadlines.length()} échéances suivies",
                    class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/60 w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4",
        ),
        rx.el.div(
            _legend("Échéance dépassée", "h-2 w-2 rounded-none bg-[#ff6b5a]"),
            _legend("Sous 14 jours", "h-2 w-2 rounded-none bg-[#ff8a5b]"),
            _legend("À planifier", "h-2 w-2 rounded-none bg-[#d8fa5e]"),
            rx.el.span(
                "Aujourd'hui → J+90",
                class_name="ap-eyebrow text-[#c9c5b4]/35 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-5 mt-4",
        ),
        rx.cond(
            MaintenanceState.deadlines.length() > 0,
            rx.el.div(
                rx.foreach(
                    MaintenanceState.deadlines,
                    lambda item: _deadline_row(item, key=item["key"]),
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 mt-5",
            ),
            rx.el.div(
                rx.icon("calendar-check", class_name="h-6 w-6 text-[#d8fa5e]"),
                rx.el.p(
                    "Aucune échéance préventive dans les 90 prochains jours.",
                    class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2",
                ),
                class_name="flex flex-col items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#101208] py-12 mt-5",
            ),
        ),
        class_name="flex-1 min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )


def fleet_health_map() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.span(
                "Cartographie de santé",
                class_name="ap-eyebrow text-[#d8fa5e]/80",
            ),
            rx.el.span(
                f"{MaintenanceState.fleet_health_average:.0f} / 100",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-bold text-[#c9c5b4]/70 w-fit ml-auto",
            ),
            class_name="flex items-center gap-3",
        ),
        rx.cond(
            MaintenanceState.equipments.length() > 0,
            rx.el.div(
                rx.foreach(
                    MaintenanceState.equipments,
                    lambda m: _health_tile(m, key=m["id"].to_string()),
                ),
                class_name="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4",
            ),
            rx.el.p(
                "Aucun engin pour ces filtres.",
                class_name="text-sm font-medium text-[#c9c5b4]/50 mt-4",
            ),
        ),
        rx.el.div(
            rx.el.span(
                "Alertes atelier",
                class_name="ap-eyebrow text-[#ff8a5b]/80",
            ),
            rx.cond(
                MaintenanceState.fleet_alerts.length() > 0,
                rx.el.div(
                    rx.foreach(
                        MaintenanceState.fleet_alerts,
                        lambda a: _alert_card(a, key=a["key"]),
                    ),
                    class_name="flex flex-col gap-3 mt-3 max-h-[26rem] overflow-y-auto pr-1",
                ),
                rx.el.div(
                    rx.icon("shield-check", class_name="h-5 w-5 text-[#d8fa5e]"),
                    rx.el.p(
                        "Aucune échéance d'assurance, de contrôle ou d'entretien à traiter.",
                        class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2 text-center",
                    ),
                    class_name="flex flex-col items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#101208] py-10 mt-3",
                ),
            ),
            class_name="mt-6 border-t border-[#f2efe4]/12 pt-5",
        ),
        class_name="w-full xl:w-[28rem] shrink-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )

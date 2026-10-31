import reflex as rx

from app.states.dashboard_state import (
    CalendarDay,
    DashboardState,
    InterventionItem,
)


def _type_icon(type_key: rx.Var, class_name: str) -> rx.Component:
    return rx.match(
        type_key,
        ("SEMIS", rx.icon("sprout", class_name=class_name)),
        ("PLANTATION", rx.icon("shovel", class_name=class_name)),
        ("FERTILISATION", rx.icon("package", class_name=class_name)),
        ("TRAITEMENT_PHYTO", rx.icon("spray-can", class_name=class_name)),
        ("DESHERBAGE", rx.icon("scissors", class_name=class_name)),
        ("IRRIGATION", rx.icon("droplets", class_name=class_name)),
        ("TRAVAIL_DU_SOL", rx.icon("tractor", class_name=class_name)),
        ("OBSERVATION", rx.icon("eye", class_name=class_name)),
        ("RECOLTE", rx.icon("wheat", class_name=class_name)),
        rx.icon("circle-dot", class_name=class_name),
    )


def _day_cell(day: CalendarDay) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            day["num"],
            class_name=rx.match(
                day["tone"],
                ("today", "text-sm font-bold text-[#0A0A08]"),
                ("past", "text-sm font-semibold text-[#c9c5b4]/35"),
                "text-sm font-semibold text-[#f2efe4]",
            ),
        ),
        rx.cond(
            day["count"] > 0,
            rx.el.div(
                rx.el.span(
                    day["count"],
                    class_name=rx.cond(
                        day["tone"] == "today",
                        "text-[10px] font-bold text-[#0A0A08]",
                        "text-[10px] font-bold text-[#e4ff9b]",
                    ),
                ),
                rx.el.span(
                    class_name=rx.cond(
                        day["tone"] == "today",
                        "h-1.5 w-1.5 rounded-none bg-[#0A0A08]",
                        "h-1.5 w-1.5 rounded-none bg-[#d8fa5e]",
                    ),
                ),
                class_name="flex items-center gap-1 mt-1.5",
            ),
            rx.el.span(
                class_name="h-1.5 w-1.5 rounded-none bg-[#20241a] mt-1.5"
            ),
        ),
        class_name=rx.match(
            day["tone"],
            (
                "today",
                "flex flex-col items-center justify-center aspect-square rounded-none bg-[#d8fa5e] border border-[#e4ff9b]",
            ),
            (
                "past",
                "flex flex-col items-center justify-center aspect-square rounded-none border border-[#f2efe4]/8 bg-[#0d0f09]",
            ),
            "flex flex-col items-center justify-center aspect-square rounded-none border border-[#f2efe4]/12 bg-[#14160f] hover:border-[#d8fa5e]/30 transition-colors",
        ),
    )


def _intervention_row(item: InterventionItem) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _type_icon(item["type"], "h-4 w-4 text-[#d8fa5e]"),
            class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#14160f]",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    item["title"],
                    class_name="text-sm font-semibold text-[#f2efe4] truncate",
                ),
                rx.el.span(
                    item["type_label"],
                    class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit shrink-0",
                ),
                class_name="flex items-center gap-2 min-w-0",
            ),
            rx.el.p(
                f"{item['parcel']} · {item['operator']} · {item['area_ha']:.1f} ha",
                class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-1 truncate",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.div(
            rx.el.span(
                item["date_label"],
                class_name="text-xs font-semibold text-[#f2efe4]",
            ),
            rx.el.span(
                rx.cond(
                    item["days_from_now"] == 0,
                    "aujourd'hui",
                    f"dans {item['days_from_now']} j",
                ),
                class_name=rx.cond(
                    item["days_from_now"] <= 2,
                    "text-[10px] font-semibold text-[#ff8a5b]",
                    "text-[10px] font-medium text-[#c9c5b4]/45",
                ),
            ),
            class_name="flex flex-col items-end shrink-0",
        ),
        class_name="flex items-center gap-3 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3 hover:border-[#d8fa5e]/25 transition-colors w-full",
    )


def calendar_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Planification",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Calendrier des interventions",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                "3 semaines",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            class_name="flex items-end justify-between gap-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.foreach(
                    DashboardState.weekday_headers,
                    lambda label: rx.el.span(
                        label,
                        class_name="text-center ap-eyebrow text-[#c9c5b4]/40",
                    ),
                ),
                class_name="grid grid-cols-7 gap-2",
            ),
            rx.el.div(
                rx.foreach(
                    DashboardState.calendar_days, lambda d: _day_cell(d)
                ),
                class_name="grid grid-cols-7 gap-2 mt-2",
            ),
            class_name="mt-5",
        ),
        rx.el.div(
            rx.el.span(
                "Prochains chantiers",
                class_name="ap-eyebrow text-[#c9c5b4]/45",
            ),
            rx.cond(
                DashboardState.interventions.length() > 0,
                rx.el.div(
                    rx.foreach(
                        DashboardState.interventions,
                        lambda i: _intervention_row(i),
                    ),
                    class_name="flex flex-col gap-2 mt-3",
                ),
                rx.el.p(
                    "Aucune intervention planifiée à venir.",
                    class_name="text-sm font-medium text-[#c9c5b4]/50 mt-3",
                ),
            ),
            class_name="mt-6",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )

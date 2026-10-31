import reflex as rx

from app.states.dashboard_state import AlertItem, DashboardState


def _alert_card(alert: AlertItem) -> rx.Component:
    return rx.el.div(
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
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            alert["title"],
            class_name="text-sm font-semibold text-[#f2efe4] mt-2 leading-snug",
        ),
        rx.el.p(
            alert["message"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/55 mt-1 leading-relaxed",
        ),
        rx.el.div(
            rx.icon("map-pin", class_name="h-3 w-3 text-[#d8fa5e]/80"),
            rx.el.span(
                alert["parcel"],
                class_name="text-[11px] font-medium text-[#c9c5b4]/60",
            ),
            class_name="flex items-center gap-1.5 mt-3",
        ),
        class_name=rx.match(
            alert["level"],
            (
                "CRITIQUE",
                "rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/[0.07] p-4 w-full",
            ),
            (
                "ATTENTION",
                "rounded-none border border-[#ff8a5b]/25 bg-[#ff8a5b]/[0.06] p-4 w-full",
            ),
            "rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 w-full",
        ),
    )


def alerts_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Veille agronomique",
                    class_name="ap-eyebrow text-[#ff8a5b]/80",
                ),
                rx.el.h2(
                    "Alertes actives",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{DashboardState.kpis['alerts']:.0f}",
                class_name="rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-3 py-1 text-xs font-bold text-[#ffb894] w-fit",
            ),
            class_name="flex items-end justify-between gap-4",
        ),
        rx.cond(
            DashboardState.alerts.length() > 0,
            rx.el.div(
                rx.foreach(DashboardState.alerts, lambda a: _alert_card(a)),
                class_name="flex flex-col gap-3 mt-5",
            ),
            rx.el.div(
                rx.icon("shield-check", class_name="h-6 w-6 text-[#d8fa5e]"),
                rx.el.p(
                    "Aucune alerte en cours sur l'exploitation.",
                    class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2",
                ),
                class_name="flex flex-col items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#101208] py-10 mt-5",
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )

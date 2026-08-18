import reflex as rx

from app.states.dashboard_state import AlertItem, DashboardState


def _alert_card(alert: AlertItem) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.match(
                alert["level"],
                (
                    "CRITIQUE",
                    rx.icon("octagon-alert", class_name="h-4 w-4 text-red-400"),
                ),
                (
                    "ATTENTION",
                    rx.icon(
                        "triangle-alert", class_name="h-4 w-4 text-amber-300"
                    ),
                ),
                rx.icon("info", class_name="h-4 w-4 text-sky-300"),
            ),
            rx.el.span(
                alert["category"],
                class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
            ),
            rx.el.span(
                alert["date_label"],
                class_name="text-[10px] font-medium text-emerald-100/40 ml-auto",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            alert["title"],
            class_name="text-sm font-semibold text-emerald-50 mt-2 leading-snug",
        ),
        rx.el.p(
            alert["message"],
            class_name="text-[11px] font-medium text-emerald-100/55 mt-1 leading-relaxed",
        ),
        rx.el.div(
            rx.icon("map-pin", class_name="h-3 w-3 text-lime-300/80"),
            rx.el.span(
                alert["parcel"],
                class_name="text-[11px] font-medium text-emerald-100/60",
            ),
            class_name="flex items-center gap-1.5 mt-3",
        ),
        class_name=rx.match(
            alert["level"],
            (
                "CRITIQUE",
                "rounded-2xl border border-red-400/30 bg-red-500/[0.07] p-4 w-full",
            ),
            (
                "ATTENTION",
                "rounded-2xl border border-amber-300/25 bg-amber-300/[0.06] p-4 w-full",
            ),
            "rounded-2xl border border-white/10 bg-white/[0.03] p-4 w-full",
        ),
    )


def alerts_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Veille agronomique",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-amber-300/80",
                ),
                rx.el.h2(
                    "Alertes actives",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{DashboardState.kpis['alerts']:.0f}",
                class_name="rounded-full border border-amber-300/30 bg-amber-300/10 px-3 py-1 text-xs font-bold text-amber-200 w-fit",
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
                rx.icon("shield-check", class_name="h-6 w-6 text-lime-300"),
                rx.el.p(
                    "Aucune alerte en cours sur l'exploitation.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-2",
                ),
                class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-10 mt-5",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )

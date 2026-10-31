import reflex as rx

from app.states.dashboard_state import AlertItem, DashboardState


def _alert_card(alert: AlertItem) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.match(
                alert["level"],
                (
                    "CRITIQUE",
                    rx.icon("octagon-alert", class_name="h-4 w-4 text-[rgb(var(--ap-danger-rgb))]"),
                ),
                (
                    "ATTENTION",
                    rx.icon(
                        "triangle-alert", class_name="h-4 w-4 text-[rgb(var(--ap-flame-soft-rgb))]"
                    ),
                ),
                rx.icon("info", class_name="h-4 w-4 text-[rgb(var(--ap-info-rgb))]"),
            ),
            rx.el.span(
                alert["category"],
                class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            rx.el.span(
                alert["date_label"],
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] ml-auto",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            alert["title"],
            class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] mt-2 leading-snug",
        ),
        rx.el.p(
            alert["message"],
            class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] mt-1 leading-relaxed",
        ),
        rx.el.div(
            rx.icon("map-pin", class_name="h-3 w-3 text-[rgb(var(--ap-accent-rgb)/0.80)]"),
            rx.el.span(
                alert["parcel"],
                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)]",
            ),
            class_name="flex items-center gap-1.5 mt-3",
        ),
        class_name=rx.match(
            alert["level"],
            (
                "CRITIQUE",
                "rounded-none border border-[rgb(var(--ap-danger-rgb)/0.30)] bg-[rgb(var(--ap-flame-strong-rgb))]/[0.07] p-4 w-full",
            ),
            (
                "ATTENTION",
                "rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.25)] bg-[rgb(var(--ap-flame-soft-rgb))]/[0.06] p-4 w-full",
            ),
            "border-t border-[rgb(var(--ap-paper-rgb)/0.18)] pt-4 w-full",
        ),
    )


def alerts_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Veille agronomique",
                    class_name="ap-eyebrow text-[rgb(var(--ap-flame-soft-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Alertes actives",
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{DashboardState.kpis['alerts']:.0f}",
                class_name="rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-3 py-1 text-xs font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
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
                rx.icon("shield-check", class_name="h-6 w-6 text-[rgb(var(--ap-accent-rgb))]"),
                rx.el.p(
                    "Aucune alerte en cours sur l'exploitation.",
                    class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] mt-2",
                ),
                class_name="flex flex-col items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] py-10 mt-5",
            ),
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )

import reflex as rx

from app.states.dashboard_state import CropCard, DashboardState


def _health_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
            ),
            (
                "warn",
                "rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
            ),
            "rounded-none border border-[rgb(var(--ap-danger-rgb)/0.30)] bg-[rgb(var(--ap-flame-strong-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-danger-soft-rgb))] w-fit",
        ),
    )


def _crop_card(crop: CropCard) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="h-1 w-full rounded-none",
            style={"backgroundColor": crop["color"]},
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    crop["name"],
                    class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
                ),
                rx.el.p(
                    f"{crop['species']} · {crop['parcel']}",
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            _health_badge(crop["health_tone"], crop["health_label"]),
            class_name="flex items-start justify-between gap-3 mt-4",
        ),
        rx.el.div(
            rx.el.span(
                crop["stage_label"],
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.90)] w-fit",
            ),
            rx.el.span(
                crop["status_label"],
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit",
            ),
            rx.el.span(
                f"{crop['area_ha']:.1f} ha",
                class_name="text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Avancement du cycle",
                    class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                ),
                rx.el.span(
                    crop["progress_pct"],
                    class_name="text-[11px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] ml-auto",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="h-full rounded-none bg-gradient-to-r from-[rgb(var(--ap-sage-soft-rgb))] to-[rgb(var(--ap-accent-rgb))]",
                    style={"width": crop["progress_pct"]},
                ),
                class_name="h-1.5 w-full rounded-none bg-[rgb(var(--ap-surface-control-rgb))] mt-1.5",
            ),
            class_name="mt-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "calendar-plus",
                    class_name="h-3.5 w-3.5 text-[rgb(var(--ap-sage-rgb)/0.80)]",
                ),
                rx.el.span(
                    crop["sowing_label"],
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)]",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.div(
                rx.icon("wheat", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-flame-soft-rgb)/0.80)]"),
                rx.el.span(
                    crop["harvest_label"],
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)]",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.span(
                rx.cond(
                    crop["days_left"] > 0,
                    f"J-{crop['days_left']}",
                    "échéance atteinte",
                ),
                class_name="text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] ml-auto",
            ),
            class_name="flex items-center gap-3 border-t border-[rgb(var(--ap-paper-rgb)/0.12)] pt-3 mt-4",
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-4 hover:border-t-[rgb(var(--ap-accent-rgb)/0.40)] transition-colors",
    )


def crops_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Suivi cultural",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Cultures en cours",
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{DashboardState.kpis['active_crops']:.0f} cultures · {DashboardState.kpis['area_active']:.1f} ha",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
            ),
            class_name="flex flex-col sm:flex-row sm:items-end justify-between gap-3",
        ),
        rx.cond(
            DashboardState.crops.length() > 0,
            rx.el.div(
                rx.foreach(DashboardState.crops, lambda c: _crop_card(c)),
                class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mt-5",
            ),
            rx.el.p(
                "Aucune culture active pour la campagne en cours.",
                class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-5",
            ),
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )

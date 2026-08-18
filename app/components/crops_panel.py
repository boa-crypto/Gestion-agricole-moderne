import reflex as rx

from app.states.dashboard_state import CropCard, DashboardState


def _health_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
            ),
            (
                "warn",
                "rounded-full border border-amber-300/30 bg-amber-300/10 px-2 py-0.5 text-[10px] font-bold text-amber-200 w-fit",
            ),
            "rounded-full border border-red-400/30 bg-red-500/10 px-2 py-0.5 text-[10px] font-bold text-red-300 w-fit",
        ),
    )


def _crop_card(crop: CropCard) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name="h-1 w-full rounded-full",
            style={"backgroundColor": crop["color"]},
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    crop["name"],
                    class_name="text-sm font-semibold text-emerald-50 truncate",
                ),
                rx.el.p(
                    f"{crop['species']} · {crop['parcel']}",
                    class_name="text-[11px] font-medium text-emerald-100/50 truncate mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            _health_badge(crop["health_tone"], crop["health_label"]),
            class_name="flex items-start justify-between gap-3 mt-4",
        ),
        rx.el.div(
            rx.el.span(
                crop["stage_label"],
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/70 w-fit",
            ),
            rx.el.span(
                crop["status_label"],
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/50 w-fit",
            ),
            rx.el.span(
                f"{crop['area_ha']:.1f} ha",
                class_name="text-[10px] font-semibold text-emerald-100/60 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Avancement du cycle",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-100/40",
                ),
                rx.el.span(
                    crop["progress_pct"],
                    class_name="text-[11px] font-bold text-lime-200 ml-auto",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="h-full rounded-full bg-gradient-to-r from-emerald-400 to-lime-300",
                    style={"width": crop["progress_pct"]},
                ),
                class_name="h-1.5 w-full rounded-full bg-white/10 mt-1.5",
            ),
            class_name="mt-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "calendar-plus",
                    class_name="h-3.5 w-3.5 text-emerald-300/80",
                ),
                rx.el.span(
                    crop["sowing_label"],
                    class_name="text-[11px] font-medium text-emerald-100/60",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.div(
                rx.icon("wheat", class_name="h-3.5 w-3.5 text-amber-300/80"),
                rx.el.span(
                    crop["harvest_label"],
                    class_name="text-[11px] font-medium text-emerald-100/60",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.span(
                rx.cond(
                    crop["days_left"] > 0,
                    f"J-{crop['days_left']}",
                    "échéance atteinte",
                ),
                class_name="text-[10px] font-bold text-amber-200 ml-auto",
            ),
            class_name="flex items-center gap-3 border-t border-white/5 pt-3 mt-4",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:border-lime-300/25 transition-colors",
    )


def crops_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Suivi cultural",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Cultures en cours",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{DashboardState.kpis['active_crops']:.0f} cultures · {DashboardState.kpis['area_active']:.1f} ha",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit",
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
                class_name="text-sm font-medium text-emerald-100/50 mt-5",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )

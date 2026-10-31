import reflex as rx

from app.states.dashboard_state import CropCard, DashboardState


def _health_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit",
            ),
            (
                "warn",
                "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffb894] w-fit",
            ),
            "rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-2 py-0.5 text-[10px] font-bold text-[#ff9b8c] w-fit",
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
                    class_name="text-sm font-semibold text-[#f2efe4] truncate",
                ),
                rx.el.p(
                    f"{crop['species']} · {crop['parcel']}",
                    class_name="text-[11px] font-medium text-[#c9c5b4]/50 truncate mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            _health_badge(crop["health_tone"], crop["health_label"]),
            class_name="flex items-start justify-between gap-3 mt-4",
        ),
        rx.el.div(
            rx.el.span(
                crop["stage_label"],
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/70 w-fit",
            ),
            rx.el.span(
                crop["status_label"],
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/50 w-fit",
            ),
            rx.el.span(
                f"{crop['area_ha']:.1f} ha",
                class_name="text-[10px] font-semibold text-[#c9c5b4]/60 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Avancement du cycle",
                    class_name="ap-eyebrow text-[#c9c5b4]/40",
                ),
                rx.el.span(
                    crop["progress_pct"],
                    class_name="text-[11px] font-bold text-[#e4ff9b] ml-auto",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="h-full rounded-none bg-gradient-to-r from-[#8fb37a] to-[#d8fa5e]",
                    style={"width": crop["progress_pct"]},
                ),
                class_name="h-1.5 w-full rounded-none bg-[#20241a] mt-1.5",
            ),
            class_name="mt-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "calendar-plus",
                    class_name="h-3.5 w-3.5 text-[#a9c98b]/80",
                ),
                rx.el.span(
                    crop["sowing_label"],
                    class_name="text-[11px] font-medium text-[#c9c5b4]/60",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.div(
                rx.icon("wheat", class_name="h-3.5 w-3.5 text-[#ff8a5b]/80"),
                rx.el.span(
                    crop["harvest_label"],
                    class_name="text-[11px] font-medium text-[#c9c5b4]/60",
                ),
                class_name="flex items-center gap-1.5",
            ),
            rx.el.span(
                rx.cond(
                    crop["days_left"] > 0,
                    f"J-{crop['days_left']}",
                    "échéance atteinte",
                ),
                class_name="text-[10px] font-bold text-[#ffb894] ml-auto",
            ),
            class_name="flex items-center gap-3 border-t border-[#f2efe4]/8 pt-3 mt-4",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 hover:border-[#d8fa5e]/25 transition-colors",
    )


def crops_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Suivi cultural",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Cultures en cours",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{DashboardState.kpis['active_crops']:.0f} cultures · {DashboardState.kpis['area_active']:.1f} ha",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/60 w-fit",
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
                class_name="text-sm font-medium text-[#c9c5b4]/50 mt-5",
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )

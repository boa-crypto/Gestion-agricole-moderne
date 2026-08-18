import reflex as rx

from app.components.guide_help import help_button
from app.states.dashboard_state import DashboardState


def _pill(icon: str, label: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="h-3.5 w-3.5 text-lime-300"),
        rx.el.span(label, class_name="text-xs font-medium text-emerald-50/80"),
        class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 backdrop-blur-xl w-fit",
    )


def cockpit_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("leaf", class_name="h-4 w-4 text-lime-300"),
                    rx.el.span(
                        "Pilotage végétal",
                        class_name="text-[11px] font-semibold uppercase tracking-[0.32em] text-lime-300/90",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "Cockpit agronomique",
                    class_name="font-['Instrument_Serif'] text-4xl md:text-5xl leading-[1.05] text-emerald-50 mt-3",
                ),
                rx.el.p(
                    "Vision instantanée des parcelles, des cultures et des chantiers de l'exploitation.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-3 max-w-xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                _pill("calendar-days", DashboardState.today_label),
                _pill("sprout", DashboardState.season_label),
                _pill(
                    "triangle-alert",
                    f"{DashboardState.critical_alerts} alerte(s) critique(s)",
                ),
                help_button("cockpit", "Guide du cockpit"),
                rx.el.button(
                    rx.cond(
                        DashboardState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#04140d]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#04140d]"
                        ),
                    ),
                    rx.el.span("Actualiser", class_name="text-[#04140d]"),
                    on_click=DashboardState.load_dashboard,
                    class_name="flex items-center gap-2 rounded-full bg-lime-300 px-4 py-2 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full",
        ),
        class_name="w-full border-b border-white/10 pb-8",
    )

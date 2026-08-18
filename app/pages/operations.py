import reflex as rx

from app.components.guide_help import help_button
from app.components.harvest_panel import harvest_panel, yield_comparison
from app.components.intervention_journal import intervention_journal
from app.components.operations_forms import operations_modals
from app.components.operations_kpis import operations_kpis
from app.components.remediation_panels import stock_decision_panel
from app.components.stock_control import stock_control_panel
from app.components.stock_panel import stock_panel
from app.components.catalog_bridge import catalog_shortcut
from app.components.side_rail import side_rail
from app.states.operations_state import OperationsState


def _space_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("spray-can", class_name="h-4 w-4 text-lime-300"),
                    rx.el.span(
                        "Chantiers & valorisation",
                        class_name="text-[11px] font-semibold uppercase tracking-[0.32em] text-lime-300/90",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "Traitements & récoltes",
                    class_name="font-['Instrument_Serif'] text-4xl md:text-5xl leading-[1.05] text-emerald-50 mt-3",
                ),
                rx.el.p(
                    "Journal opérationnel, planification des chantiers, magasin d'intrants et comparaison des rendements réalisés.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-3 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "calendar-days", class_name="h-3.5 w-3.5 text-lime-300"
                    ),
                    rx.el.span(
                        OperationsState.today_label,
                        class_name="text-xs font-medium text-emerald-50/80",
                    ),
                    class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 backdrop-blur-xl w-fit",
                ),
                rx.el.div(
                    rx.icon(
                        "triangle-alert",
                        class_name="h-3.5 w-3.5 text-amber-300",
                    ),
                    rx.el.span(
                        f"{OperationsState.kpis['overdue']:.0f} chantier(s) en retard",
                        class_name="text-xs font-medium text-emerald-50/80",
                    ),
                    class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 backdrop-blur-xl w-fit",
                ),
                help_button("traitements", "Guide des chantiers"),
                rx.el.button(
                    rx.cond(
                        OperationsState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#04140d]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#04140d]"
                        ),
                    ),
                    rx.el.span("Actualiser", class_name="text-[#04140d]"),
                    on_click=OperationsState.load_operations,
                    class_name="flex items-center gap-2 rounded-full bg-lime-300 px-4 py-2 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full",
        ),
        class_name="w-full border-b border-white/10 pb-8 mt-6",
    )


def operations_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            class_name="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-[#04120c]/35 via-[#04120c]/45 to-[#020a07]/60",
        ),
        rx.el.div(
            side_rail("traitements"),
            catalog_shortcut("traitements"),
            _space_header(),
            rx.el.div(
                operations_kpis(),
                intervention_journal(),
                stock_panel(),
                stock_control_panel(),
                stock_decision_panel(),
                harvest_panel(),
                yield_comparison(),
                class_name="flex flex-col gap-4 w-full mt-8",
            ),
            operations_modals(),
            class_name="relative z-10 w-full max-w-[110rem] mx-auto px-4 sm:px-8 md:pl-24 lg:pl-28 py-10 pb-28 md:pb-10",
        ),
        class_name="relative min-h-screen w-full font-['Inter'] bg-[#04120c] bg-[url('/wide_cinematic_background.png')] bg-cover bg-center bg-fixed text-emerald-50 antialiased",
    )

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
from app.components.shell import app_shell
from app.states.operations_state import OperationsState


def _space_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("spray-can", class_name="h-4 w-4 text-[#d8fa5e]"),
                    rx.el.span(
                        "Chantiers & valorisation",
                        class_name="ap-eyebrow text-[#D8FA5E]",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "Traitements & récoltes",
                    class_name="ap-display text-[clamp(2.4rem,4.6vw,4.1rem)] text-[#f2efe4] mt-3",
                ),
                rx.el.p(
                    "Journal opérationnel, planification des chantiers, magasin d'intrants et comparaison des rendements réalisés.",
                    class_name="mt-4 text-[13px] leading-relaxed text-[#C9C5B4]/70 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "calendar-days", class_name="h-3.5 w-3.5 text-[#d8fa5e]"
                    ),
                    rx.el.span(
                        OperationsState.today_label,
                        class_name="text-xs font-medium text-[#f2efe4]/80",
                    ),
                    class_name="ap-mono inline-flex w-fit items-center gap-2 border border-[#F2EFE4]/12 px-3 py-2 text-[9px] uppercase tracking-[0.18em] text-[#C9C5B4]",
                ),
                rx.el.div(
                    rx.icon(
                        "triangle-alert",
                        class_name="h-3.5 w-3.5 text-[#ff8a5b]",
                    ),
                    rx.el.span(
                        f"{OperationsState.kpis['overdue']:.0f} chantier(s) en retard",
                        class_name="text-xs font-medium text-[#f2efe4]/80",
                    ),
                    class_name="ap-mono inline-flex w-fit items-center gap-2 border border-[#F2EFE4]/12 px-3 py-2 text-[9px] uppercase tracking-[0.18em] text-[#C9C5B4]",
                ),
                help_button("traitements", "Guide des chantiers"),
                rx.el.button(
                    rx.cond(
                        OperationsState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#0A0A08]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#0A0A08]"
                        ),
                    ),
                    rx.el.span("Actualiser", class_name="text-[#0A0A08]"),
                    on_click=OperationsState.load_operations,
                    class_name="ap-mono inline-flex w-fit items-center gap-2 bg-[#D8FA5E] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[#0A0A08] transition-colors hover:bg-[#E4FF9B]",
                ),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full",
        ),
        class_name="w-full border-b border-[#F2EFE4]/12 pb-8",
    )


def operations_page() -> rx.Component:
    return app_shell(
        rx.el.div(
            catalog_shortcut("traitements"),
            _space_header(),
            rx.el.div(
                operations_kpis(),
                rx.el.div(
                    intervention_journal(),
                    id="nav-planning",
                    class_name="w-full scroll-mt-6",
                ),
                rx.el.div(
                    stock_panel(),
                    id="nav-magasin",
                    class_name="w-full scroll-mt-6",
                ),
                stock_control_panel(),
                stock_decision_panel(),
                harvest_panel(),
                yield_comparison(),
                class_name="flex flex-col gap-4 w-full mt-8",
            ),
            operations_modals(),
            class_name="flex w-full flex-col gap-6",
        ),
        "traitements",
    )

import reflex as rx

from app.components.design import meta_ledger, meta_row, page_hero, refresh_button
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
    return page_hero(
        "Chantiers & valorisation",
        "Traitements & récoltes",
        "Journal opérationnel, planification des chantiers, magasin d'intrants et comparaison des rendements réalisés.",
        meta=meta_ledger(
            meta_row("Jour", OperationsState.today_label),
            meta_row("Chantiers en retard", f"{OperationsState.kpis['overdue']:.0f}", tone="flame"),
        ),
        actions=rx.el.div(
            help_button("traitements", "Guide des chantiers"),
            refresh_button(
                on_click=OperationsState.load_operations,
                loading=OperationsState.is_loading,
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
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

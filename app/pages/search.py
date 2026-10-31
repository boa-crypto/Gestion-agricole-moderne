import reflex as rx

from app.components.design import meta_ledger, meta_row, page_hero, refresh_button
from app.components.phenology_search import phenology_search_panel
from app.components.search_console import search_console
from app.components.search_results import search_results
from app.components.shell import app_shell
from app.states.search_state import SearchState


def _space_header() -> rx.Component:
    return page_hero(
        "Console transversale",
        "Recherche globale",
        "Un seul champ pour balayer parcelles, cultures, variétés, interventions, intrants, stocks, récoltes, alertes, salariés, compétences, disponibilités, affectations, engins, plans d'entretien, opérations, coûts et relevés d'usage.",
        meta=meta_ledger(
            meta_row("Jour", SearchState.today_label),
            meta_row("Périmètre", SearchState.scope_label),
        ),
        actions=rx.el.div(
            refresh_button(
                on_click=SearchState.load_search,
                loading=SearchState.is_loading,
                label="Rebalayer",
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
    )


def search_page() -> rx.Component:
    return app_shell(
        rx.el.div(
            _space_header(),
            rx.el.div(
                search_console(),
                search_results(),
                phenology_search_panel(),
                class_name="flex flex-col gap-4 w-full mt-8",
            ),
            class_name="flex w-full flex-col gap-6",
        ),
        "recherche",
    )

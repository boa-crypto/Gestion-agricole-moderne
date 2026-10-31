import reflex as rx

from app.components.design import (
    action_button,
    field,
    input_class,
    select_field,
    stat,
)
from app.states.maintenance_state import MaintenanceState, Option


def _stat(
    label: str,
    value: rx.Var | str,
    unit: str,
    tone: str = "paper",
) -> rx.Component:
    return stat(label, value, unit, tone=tone)


def _select(
    name: str,
    icon: str,
    value: rx.Var | str,
    on_change: rx.event.EventType,
    first_option: rx.Component,
    options: rx.Var[list[Option]],
) -> rx.Component:
    return select_field(
        first_option,
        rx.foreach(
            options,
            lambda opt: rx.el.option(opt["label"], value=opt["value"]),
        ),
        name=name,
        icon=icon,
        default_value=value,
        on_change=on_change,
        form_key=MaintenanceState.form_key,
    )


def fleet_filters() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            _stat(
                "Engins listés", MaintenanceState.equipment_count, "machines"
            ),
            _stat(
                "Santé moyenne",
                f"{MaintenanceState.fleet_health_average:.0f}",
                "/ 100",
                tone="accent",
            ),
            _stat(
                "Santé critique",
                MaintenanceState.critical_count,
                "engins",
                tone="flame",
            ),
            _stat(
                "Compteurs cumulés",
                f"{MaintenanceState.counter_shown:.0f}",
                "unités",
            ),
            class_name=(
                "grid grid-cols-1 gap-x-8 gap-y-7 sm:grid-cols-2 "
                "xl:grid-cols-4 w-full"
            ),
        ),
        rx.el.div(
            field(
                rx.el.input(
                    placeholder=(
                        "Rechercher un engin, un code, une marque "
                        "ou une immatriculation…"
                    ),
                    default_value=MaintenanceState.search,
                    on_change=MaintenanceState.set_search.debounce(400),
                    class_name=input_class(icon=True),
                ),
                icon="search",
            ),
            class_name="w-full mt-6",
        ),
        rx.el.div(
            _select(
                "category_filter",
                "tractor",
                MaintenanceState.category_filter,
                MaintenanceState.set_category_filter,
                rx.el.option("Toutes les catégories", value="TOUTES"),
                MaintenanceState.category_options,
            ),
            _select(
                "fleet_status_filter",
                "flag",
                MaintenanceState.status_filter,
                MaintenanceState.set_status_filter,
                rx.el.option("Tous les statuts", value="TOUS"),
                MaintenanceState.status_options,
            ),
            _select(
                "health_filter",
                "activity",
                MaintenanceState.health_filter,
                MaintenanceState.set_health_filter,
                rx.el.option("Toutes les santés", value="TOUS"),
                MaintenanceState.health_options,
            ),
            action_button(
                "Réinitialiser",
                icon="rotate-ccw",
                tone="outline",
                on_click=MaintenanceState.reset_filters,
            ),
            action_button(
                "Nouvel engin",
                icon="plus",
                on_click=MaintenanceState.open_equipment_create,
            ),
            class_name=(
                "flex flex-col sm:flex-row sm:flex-wrap items-stretch "
                "sm:items-center gap-3 w-full mt-4"
            ),
        ),
        class_name="w-full border-b border-[#F2EFE4]/12 pb-7",
    )

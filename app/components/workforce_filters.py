import reflex as rx

from app.components.design import (
    action_button,
    field,
    input_class,
    select_field,
    stat,
)
from app.states.employees_state import EmployeesState, Option


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
        form_key=EmployeesState.form_key,
    )


def workforce_filters() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            _stat("Salariés listés", EmployeesState.employee_count, "fiches"),
            _stat("Équipes couvertes", EmployeesState.teams_shown, "pôles"),
            _stat(
                "Heures affichées", f"{EmployeesState.hours_shown:.1f}", "h/sem"
            ),
            _stat(
                "Compétences suivies",
                f"{EmployeesState.kpis['skills']:.0f}",
                "références",
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
                        "Rechercher un salarié, un matricule, un poste "
                        "ou une équipe…"
                    ),
                    default_value=EmployeesState.search,
                    on_change=EmployeesState.set_search.debounce(400),
                    class_name=input_class(icon=True),
                ),
                icon="search",
            ),
            class_name="w-full mt-6",
        ),
        rx.el.div(
            _select(
                "status_filter",
                "flag",
                EmployeesState.status_filter,
                EmployeesState.set_status_filter,
                rx.el.option("Tous les statuts", value="TOUS"),
                EmployeesState.status_options,
            ),
            select_field(
                rx.el.option("Toutes les équipes", value="TOUTES"),
                rx.foreach(
                    EmployeesState.team_options,
                    lambda team: rx.el.option(team, value=team),
                ),
                name="team_filter",
                icon="users-round",
                default_value=EmployeesState.team_filter,
                on_change=EmployeesState.set_team_filter,
                form_key=EmployeesState.form_key,
            ),
            _select(
                "skill_filter",
                "badge-check",
                EmployeesState.skill_filter,
                EmployeesState.set_skill_filter,
                rx.el.option("Toutes les compétences", value="TOUTES"),
                EmployeesState.skill_options,
            ),
            action_button(
                "Réinitialiser",
                icon="rotate-ccw",
                tone="outline",
                on_click=EmployeesState.reset_filters,
            ),
            action_button(
                "Nouvel employé",
                icon="user-plus",
                on_click=EmployeesState.open_employee_create,
            ),
            class_name=(
                "flex flex-col sm:flex-row sm:flex-wrap items-stretch "
                "sm:items-center gap-3 w-full mt-4"
            ),
        ),
        class_name="w-full border-b border-[#F2EFE4]/12 pb-7",
    )

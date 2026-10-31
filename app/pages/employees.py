import reflex as rx

from app.components.design import meta_ledger, meta_row, page_hero, refresh_button
from app.components.employee_detail import employee_detail
from app.components.employee_forms import employee_modals
from app.components.employee_list import employee_list
from app.components.guide_help import help_button
from app.components.skill_matrix import skill_matrix
from app.components.workforce_filters import workforce_filters
from app.components.workforce_kpis import workforce_kpis
from app.components.shell import app_shell
from app.states.employees_state import EmployeesState


def _space_header() -> rx.Component:
    return page_hero(
        "Capital humain agricole",
        "Employés & compétences",
        "Registre des salariés, matrice des habilitations, disponibilités réelles et affectations aux chantiers.",
        meta=meta_ledger(
            meta_row("Jour", EmployeesState.today_label),
            meta_row("Absences", f"{EmployeesState.kpis['absent']:.0f}", tone="flame"),
        ),
        actions=rx.el.div(
            help_button("employes", "Guide RH agricole"),
            refresh_button(
                on_click=EmployeesState.load_workforce,
                loading=EmployeesState.is_loading,
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
    )


def employees_page() -> rx.Component:
    return app_shell(
        rx.el.div(
            _space_header(),
            rx.el.div(
                workforce_kpis(),
                workforce_filters(),
                skill_matrix(),
                rx.el.div(
                    employee_list(),
                    employee_detail(),
                    class_name="flex flex-col xl:flex-row gap-4 w-full",
                ),
                class_name="flex flex-col gap-4 w-full mt-8",
            ),
            employee_modals(),
            class_name="flex w-full flex-col gap-6",
        ),
        "employes",
    )

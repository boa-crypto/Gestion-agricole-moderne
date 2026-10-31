import reflex as rx

from app.components.admin_kpis import admin_kpis, admin_section_nav
from app.components.admin_library import admin_functions, admin_teams
from app.components.admin_operations import (
    admin_assignments,
    admin_delegations,
    admin_workflows,
)
from app.components.admin_org import admin_org_chart, admin_personal_space
from app.components.admin_permissions import admin_journal, admin_rbac
from app.components.admin_user_detail import admin_user_detail
from app.components.admin_users import admin_filters, admin_user_list
from app.components.design import meta_ledger, meta_row, page_hero, refresh_button
from app.components.guide_help import help_button
from app.components.shell import app_shell
from app.states.administration_state import AdministrationState


def _header() -> rx.Component:
    return page_hero(
        "Administration AgriPro",
        "Utilisateurs, rôles & permissions",
        "Qui travaille dans l'exploitation, quelle est sa fonction, quelles actions peut-il effectuer et sur quel périmètre agricole.",
        meta=meta_ledger(
            meta_row("Jour", AdministrationState.today),
            meta_row("Session", AdministrationState.actor_label),
        ),
        actions=rx.el.div(
            help_button("utilisateurs", "Guide sécurité"),
            refresh_button(
                on_click=AdministrationState.load_administration,
                loading=AdministrationState.is_loading,
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
    )


def _users_section() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            admin_filters(),
            class_name="w-full border-t border-[#F2EFE4]/10 pt-6",
        ),
        rx.el.div(
            admin_user_list(),
            admin_user_detail(),
            class_name="flex flex-col xl:flex-row gap-4 w-full",
        ),
        class_name="flex flex-col gap-4 w-full",
    )


def administration_page() -> rx.Component:
    return app_shell(
        rx.el.div(
            _header(),
            rx.el.div(
                admin_kpis(),
                admin_section_nav(),
                rx.match(
                    AdministrationState.section,
                    ("utilisateurs", _users_section()),
                    ("fonctions", admin_functions()),
                    ("equipes", admin_teams()),
                    ("permissions", admin_rbac()),
                    ("organigramme", admin_org_chart()),
                    ("espace", admin_personal_space()),
                    ("workflows", admin_workflows()),
                    ("delegations", admin_delegations()),
                    ("affectations", admin_assignments()),
                    ("journal", admin_journal()),
                    _users_section(),
                ),
                class_name="flex flex-col gap-4 w-full mt-8",
            ),
            class_name="flex w-full flex-col gap-6",
        ),
        "administration",
    )

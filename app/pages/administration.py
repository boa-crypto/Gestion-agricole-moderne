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
from app.components.guide_help import help_button
from app.components.shell import app_shell
from app.states.administration_state import AdministrationState


def _header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("shield-check", class_name="h-4 w-4 text-[#d8fa5e]"),
                    rx.el.span(
                        "Administration AgriPro",
                        class_name="ap-eyebrow text-[#D8FA5E]",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "Utilisateurs, rôles & permissions",
                    class_name="ap-display text-[clamp(2.4rem,4.6vw,4.1rem)] text-[#f2efe4] mt-3",
                ),
                rx.el.p(
                    "Qui travaille dans l'exploitation, quelle est sa fonction, "
                    "quelles actions peut-il effectuer et sur quel périmètre agricole.",
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
                        AdministrationState.today,
                        class_name="text-xs font-medium text-[#f2efe4]/80",
                    ),
                    class_name="ap-mono inline-flex w-fit items-center gap-2 border border-[#F2EFE4]/12 px-3 py-2 text-[9px] uppercase tracking-[0.18em] text-[#C9C5B4]",
                ),
                rx.el.div(
                    rx.icon(
                        "user-cog", class_name="h-3.5 w-3.5 text-[#ff8a5b]"
                    ),
                    rx.el.span(
                        AdministrationState.actor_label,
                        class_name="text-xs font-medium text-[#f2efe4]/80",
                    ),
                    class_name="ap-mono inline-flex w-fit items-center gap-2 border border-[#F2EFE4]/12 px-3 py-2 text-[9px] uppercase tracking-[0.18em] text-[#C9C5B4]",
                ),
                help_button("utilisateurs", "Guide sécurité"),
                rx.el.button(
                    rx.cond(
                        AdministrationState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#0A0A08]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#0A0A08]"
                        ),
                    ),
                    rx.el.span("Actualiser", class_name="text-[#0A0A08]"),
                    on_click=AdministrationState.load_administration,
                    class_name="ap-mono inline-flex w-fit items-center gap-2 bg-[#D8FA5E] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[#0A0A08] transition-colors hover:bg-[#E4FF9B]",
                ),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full",
        ),
        class_name="w-full border-b border-[#F2EFE4]/12 pb-8",
    )


def _users_section() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            admin_filters(),
            class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5 ",
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

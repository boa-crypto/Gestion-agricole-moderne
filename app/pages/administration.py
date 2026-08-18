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
from app.components.side_rail import side_rail
from app.states.administration_state import AdministrationState


def _header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("shield-check", class_name="h-4 w-4 text-lime-300"),
                    rx.el.span(
                        "Administration AgriPro",
                        class_name="text-[11px] font-semibold uppercase tracking-[0.32em] text-lime-300/90",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "Utilisateurs, rôles & permissions",
                    class_name="font-['Instrument_Serif'] text-4xl md:text-5xl leading-[1.05] text-emerald-50 mt-3",
                ),
                rx.el.p(
                    "Qui travaille dans l'exploitation, quelle est sa fonction, "
                    "quelles actions peut-il effectuer et sur quel périmètre agricole.",
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
                        AdministrationState.today,
                        class_name="text-xs font-medium text-emerald-50/80",
                    ),
                    class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 backdrop-blur-xl w-fit",
                ),
                rx.el.div(
                    rx.icon(
                        "user-cog", class_name="h-3.5 w-3.5 text-amber-300"
                    ),
                    rx.el.span(
                        AdministrationState.actor_label,
                        class_name="text-xs font-medium text-emerald-50/80",
                    ),
                    class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 backdrop-blur-xl w-fit",
                ),
                help_button("utilisateurs", "Guide sécurité"),
                rx.el.button(
                    rx.cond(
                        AdministrationState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#04140d]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#04140d]"
                        ),
                    ),
                    rx.el.span("Actualiser", class_name="text-[#04140d]"),
                    on_click=AdministrationState.load_administration,
                    class_name="flex items-center gap-2 rounded-full bg-lime-300 px-4 py-2 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full",
        ),
        class_name="w-full border-b border-white/10 pb-8 mt-6",
    )


def _users_section() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            admin_filters(),
            class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl",
        ),
        rx.el.div(
            admin_user_list(),
            admin_user_detail(),
            class_name="flex flex-col xl:flex-row gap-4 w-full",
        ),
        class_name="flex flex-col gap-4 w-full",
    )


def administration_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            class_name="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-[#04120c]/35 via-[#04120c]/45 to-[#020a07]/60",
        ),
        rx.el.div(
            side_rail("administration"),
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
            class_name="relative z-10 w-full max-w-[110rem] mx-auto px-4 sm:px-8 md:pl-24 lg:pl-28 py-10 pb-28 md:pb-10",
        ),
        class_name="relative min-h-screen w-full font-['Inter'] bg-[#04120c] bg-[url('/wide_cinematic_background.png')] bg-cover bg-center bg-fixed text-emerald-50 antialiased",
    )

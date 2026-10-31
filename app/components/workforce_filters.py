import reflex as rx

from app.states.employees_state import EmployeesState, Option

_SELECT = "w-full appearance-none cursor-pointer rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] py-2.5 pl-9 pr-9 text-sm font-medium text-[#f2efe4] focus:border-[#d8fa5e]/50 focus:ring-2 focus:ring-[#d8fa5e]/20 outline-hidden transition-colors"


def _stat(label: str, value: rx.Var | str, unit: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="ap-eyebrow text-[#c9c5b4]/45",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="ap-serif text-2xl leading-none text-[#f2efe4]",
            ),
            rx.el.span(
                unit,
                class_name="text-[11px] font-medium text-[#c9c5b4]/50 mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-2",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-3",
    )


def _select(
    name: str,
    icon: str,
    value: rx.Var | str,
    on_change: rx.event.EventType,
    first_option: rx.Component,
    options: rx.Var[list[Option]],
) -> rx.Component:
    return rx.el.div(
        rx.icon(
            icon,
            class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#d8fa5e]/80 pointer-events-none",
        ),
        rx.el.select(
            first_option,
            rx.foreach(
                options,
                lambda opt: rx.el.option(opt["label"], value=opt["value"]),
            ),
            name=name,
            default_value=value,
            key=f"{name}-{EmployeesState.form_key}",
            on_change=on_change,
            class_name=_SELECT,
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
        ),
        class_name="relative w-full sm:w-56",
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
            class_name="grid grid-cols-2 lg:grid-cols-4 gap-3 w-full",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "search",
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
                ),
                rx.el.input(
                    placeholder="Rechercher un salarié, un matricule, un poste ou une équipe…",
                    default_value=EmployeesState.search,
                    on_change=EmployeesState.set_search.debounce(400),
                    class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] py-2.5 pl-9 pr-3 text-sm font-medium text-[#f2efe4] placeholder:text-[#c9c5b4]/30 focus:border-[#d8fa5e]/50 focus:ring-2 focus:ring-[#d8fa5e]/20 outline-hidden transition-colors",
                ),
                class_name="relative flex-1 min-w-0",
            ),
            _select(
                "status_filter",
                "flag",
                EmployeesState.status_filter,
                EmployeesState.set_status_filter,
                rx.el.option("Tous les statuts", value="TOUS"),
                EmployeesState.status_options,
            ),
            rx.el.div(
                rx.icon(
                    "users-round",
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#d8fa5e]/80 pointer-events-none",
                ),
                rx.el.select(
                    rx.el.option("Toutes les équipes", value="TOUTES"),
                    rx.foreach(
                        EmployeesState.team_options,
                        lambda team: rx.el.option(team, value=team),
                    ),
                    name="team_filter",
                    default_value=EmployeesState.team_filter,
                    key=f"team-{EmployeesState.form_key}",
                    on_change=EmployeesState.set_team_filter,
                    class_name=_SELECT,
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
                ),
                class_name="relative w-full sm:w-56",
            ),
            _select(
                "skill_filter",
                "badge-check",
                EmployeesState.skill_filter,
                EmployeesState.set_skill_filter,
                rx.el.option("Toutes les compétences", value="TOUTES"),
                EmployeesState.skill_options,
            ),
            rx.el.button(
                rx.icon("rotate-ccw", class_name="h-4 w-4"),
                rx.el.span("Réinitialiser"),
                on_click=EmployeesState.reset_filters,
                class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2.5 text-sm font-semibold text-[#c9c5b4]/70 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit",
            ),
            rx.el.button(
                rx.icon("user-plus", class_name="h-4 w-4 text-[#0A0A08]"),
                rx.el.span("Nouvel employé", class_name="text-[#0A0A08]"),
                on_click=EmployeesState.open_employee_create,
                class_name="flex items-center gap-2 rounded-none bg-[#d8fa5e] px-4 py-2.5 text-sm font-semibold hover:bg-[#e4ff9b] transition-colors w-fit",
            ),
            class_name="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-3 w-full mt-4",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5 ",
    )

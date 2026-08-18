import reflex as rx

from app.states.employees_state import EmployeesState, Option

_SELECT = "w-full appearance-none cursor-pointer rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-9 text-sm font-medium text-emerald-50 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors"


def _stat(label: str, value: rx.Var | str, unit: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="font-['Instrument_Serif'] text-2xl leading-none text-emerald-50",
            ),
            rx.el.span(
                unit,
                class_name="text-[11px] font-medium text-emerald-100/50 mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-2",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3",
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
            class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300/80 pointer-events-none",
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
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
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
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                ),
                rx.el.input(
                    placeholder="Rechercher un salarié, un matricule, un poste ou une équipe…",
                    default_value=EmployeesState.search,
                    on_change=EmployeesState.set_search.debounce(400),
                    class_name="w-full rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-3 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors",
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
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300/80 pointer-events-none",
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
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
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
                class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
            ),
            rx.el.button(
                rx.icon("user-plus", class_name="h-4 w-4 text-[#04140d]"),
                rx.el.span("Nouvel employé", class_name="text-[#04140d]"),
                on_click=EmployeesState.open_employee_create,
                class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
            ),
            class_name="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-3 w-full mt-4",
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl",
    )

import reflex as rx

from app.states.employees_state import EmployeeRow, EmployeesState


def _status_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
            ),
            (
                "warn",
                "rounded-full border border-amber-300/30 bg-amber-300/10 px-2 py-0.5 text-[10px] font-bold text-amber-200 w-fit",
            ),
            (
                "bad",
                "rounded-full border border-red-400/30 bg-red-500/10 px-2 py-0.5 text-[10px] font-bold text-red-300 w-fit",
            ),
            (
                "info",
                "rounded-full border border-sky-300/30 bg-sky-300/10 px-2 py-0.5 text-[10px] font-bold text-sky-200 w-fit",
            ),
            "rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/45 w-fit",
        ),
    )


def _employee_card(employee: EmployeeRow, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    employee["initials"],
                    class_name="text-xs font-bold text-[#04140d]",
                ),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-lime-300",
            ),
            rx.el.div(
                rx.el.p(
                    employee["name"],
                    class_name="text-sm font-semibold text-emerald-50 truncate text-left",
                ),
                rx.el.p(
                    f"{employee['code']} · {employee['job_title']}",
                    class_name="text-[11px] font-medium text-emerald-100/50 truncate text-left",
                ),
                class_name="min-w-0 flex-1",
            ),
            _status_badge(employee["status_tone"], employee["status_label"]),
            class_name="flex items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.el.span(
                employee["team"],
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                employee["contract_label"],
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/50 w-fit",
            ),
            rx.cond(
                employee["phyto"],
                rx.el.span(
                    "CERTIPHYTO",
                    class_name="rounded-full border border-lime-300/40 bg-lime-300/10 px-1.5 py-0.5 text-[9px] font-bold text-lime-200 w-fit",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        rx.el.div(
            rx.icon("badge-check", class_name="h-3.5 w-3.5 text-lime-300/80"),
            rx.el.span(
                employee["top_skill"],
                class_name="text-[11px] font-medium text-emerald-100/60 truncate",
            ),
            class_name="flex items-center gap-1.5 w-full mt-2 min-w-0",
        ),
        rx.el.div(
            rx.el.span(
                f"{employee['skill_count']} compétence(s)",
                class_name="text-[10px] font-medium text-emerald-100/45",
            ),
            rx.el.span(
                f"{employee['weekly_hours']:.0f} h/sem",
                class_name="text-[10px] font-semibold text-emerald-100/65",
            ),
            rx.el.span(
                f"{employee['assignments']} mission(s)",
                class_name="text-[10px] font-bold text-lime-200 ml-auto",
            ),
            class_name="flex items-center gap-2 w-full mt-2",
        ),
        on_click=EmployeesState.select_employee(employee["id"]),
        key=key,
        class_name=rx.cond(
            EmployeesState.selected_employee_id == employee["id"],
            "w-full rounded-2xl border border-lime-300/40 bg-lime-300/[0.07] p-4 text-left ring-2 ring-lime-300/40 transition-all",
            "w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left hover:border-lime-300/25 transition-all",
        ),
    )


def employee_list() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Registre",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Équipe",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                EmployeesState.employee_count,
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-bold text-emerald-100/70 w-fit",
            ),
            class_name="flex items-end justify-between gap-3",
        ),
        rx.cond(
            EmployeesState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-2xl bg-white/[0.05]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-2xl bg-white/[0.05]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-2xl bg-white/[0.05]"
                ),
                class_name="flex flex-col gap-3 mt-5",
            ),
            rx.cond(
                EmployeesState.employees.length() > 0,
                rx.el.div(
                    rx.foreach(
                        EmployeesState.employees,
                        lambda e: _employee_card(e, key=e["id"].to_string()),
                    ),
                    class_name="flex flex-col gap-3 mt-5 max-h-[46rem] overflow-y-auto pr-1",
                ),
                rx.el.div(
                    rx.icon("user-x", class_name="h-6 w-6 text-amber-300"),
                    rx.el.p(
                        "Aucun salarié pour ces critères.",
                        class_name="text-sm font-medium text-emerald-100/60 mt-2 text-center",
                    ),
                    class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-12 mt-5",
                ),
            ),
        ),
        class_name="w-full xl:w-[24rem] shrink-0 rounded-3xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl",
    )

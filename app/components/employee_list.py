import reflex as rx

from app.states.employees_state import EmployeeRow, EmployeesState


def _status_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit",
            ),
            (
                "warn",
                "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffb894] w-fit",
            ),
            (
                "bad",
                "rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-2 py-0.5 text-[10px] font-bold text-[#ff9b8c] w-fit",
            ),
            (
                "info",
                "rounded-none border border-[#9cc3ff]/30 bg-[#9cc3ff]/10 px-2 py-0.5 text-[10px] font-bold text-[#c3daff] w-fit",
            ),
            "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/45 w-fit",
        ),
    )


def _employee_card(employee: EmployeeRow, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    employee["initials"],
                    class_name="text-xs font-bold text-[#0A0A08]",
                ),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none bg-[#d8fa5e]",
            ),
            rx.el.div(
                rx.el.p(
                    employee["name"],
                    class_name="text-sm font-semibold text-[#f2efe4] truncate text-left",
                ),
                rx.el.p(
                    f"{employee['code']} · {employee['job_title']}",
                    class_name="text-[11px] font-medium text-[#c9c5b4]/50 truncate text-left",
                ),
                class_name="min-w-0 flex-1",
            ),
            _status_badge(employee["status_tone"], employee["status_label"]),
            class_name="flex items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.el.span(
                employee["team"],
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
            ),
            rx.el.span(
                employee["contract_label"],
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/50 w-fit",
            ),
            rx.cond(
                employee["phyto"],
                rx.el.span(
                    "CERTIPHYTO",
                    class_name="rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/10 px-1.5 py-0.5 text-[9px] font-bold text-[#e4ff9b] w-fit",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        rx.el.div(
            rx.icon("badge-check", class_name="h-3.5 w-3.5 text-[#d8fa5e]/80"),
            rx.el.span(
                employee["top_skill"],
                class_name="text-[11px] font-medium text-[#c9c5b4]/60 truncate",
            ),
            class_name="flex items-center gap-1.5 w-full mt-2 min-w-0",
        ),
        rx.el.div(
            rx.el.span(
                f"{employee['skill_count']} compétence(s)",
                class_name="text-[10px] font-medium text-[#c9c5b4]/45",
            ),
            rx.el.span(
                f"{employee['weekly_hours']:.0f} h/sem",
                class_name="text-[10px] font-semibold text-[#c9c5b4]/65",
            ),
            rx.el.span(
                f"{employee['assignments']} mission(s)",
                class_name="text-[10px] font-bold text-[#e4ff9b] ml-auto",
            ),
            class_name="flex items-center gap-2 w-full mt-2",
        ),
        on_click=EmployeesState.select_employee(employee["id"]),
        key=key,
        class_name=rx.cond(
            EmployeesState.selected_employee_id == employee["id"],
            "w-full rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/[0.07] p-4 text-left ring-2 ring-[#d8fa5e]/40 transition-all",
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 text-left hover:border-[#d8fa5e]/25 transition-all",
        ),
    )


def employee_list() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Registre",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Équipe",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                EmployeesState.employee_count,
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-xs font-bold text-[#c9c5b4]/70 w-fit",
            ),
            class_name="flex items-end justify-between gap-3",
        ),
        rx.cond(
            EmployeesState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-none bg-[#16190f]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-none bg-[#16190f]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-none bg-[#16190f]"
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
                    rx.icon("user-x", class_name="h-6 w-6 text-[#ff8a5b]"),
                    rx.el.p(
                        "Aucun salarié pour ces critères.",
                        class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2 text-center",
                    ),
                    class_name="flex flex-col items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#101208] py-12 mt-5",
                ),
            ),
        ),
        class_name="w-full xl:w-[24rem] shrink-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5 ",
    )

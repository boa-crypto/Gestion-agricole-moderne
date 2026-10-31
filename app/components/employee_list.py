import reflex as rx

from app.components.design import empty_state, skeleton_rows
from app.states.employees_state import EmployeeRow, EmployeesState


def _status_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
            ),
            (
                "warn",
                "rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
            ),
            (
                "bad",
                "rounded-none border border-[rgb(var(--ap-danger-rgb)/0.30)] bg-[rgb(var(--ap-flame-strong-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-danger-soft-rgb))] w-fit",
            ),
            (
                "info",
                "rounded-none border border-[rgb(var(--ap-info-rgb)/0.30)] bg-[rgb(var(--ap-info-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-info-soft-rgb))] w-fit",
            ),
            "rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit",
        ),
    )


def _employee_card(employee: EmployeeRow, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    employee["initials"],
                    class_name="text-xs font-bold text-[rgb(var(--ap-ink-rgb))]",
                ),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none bg-[rgb(var(--ap-accent-rgb))]",
            ),
            rx.el.div(
                rx.el.p(
                    employee["name"],
                    class_name="text-sm font-semibold text-[rgb(var(--ap-paper-rgb))] truncate text-left",
                ),
                rx.el.p(
                    f"{employee['code']} · {employee['job_title']}",
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate text-left",
                ),
                class_name="min-w-0 flex-1",
            ),
            _status_badge(employee["status_tone"], employee["status_label"]),
            class_name="flex items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.el.span(
                employee["team"],
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
            ),
            rx.el.span(
                employee["contract_label"],
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit",
            ),
            rx.cond(
                employee["phyto"],
                rx.el.span(
                    "CERTIPHYTO",
                    class_name="rounded-none border border-[rgb(var(--ap-accent-rgb)/0.40)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-1.5 py-0.5 text-[9px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        rx.el.div(
            rx.icon("badge-check", class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb)/0.80)]"),
            rx.el.span(
                employee["top_skill"],
                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] truncate",
            ),
            class_name="flex items-center gap-1.5 w-full mt-2 min-w-0",
        ),
        rx.el.div(
            rx.el.span(
                f"{employee['skill_count']} compétence(s)",
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            rx.el.span(
                f"{employee['weekly_hours']:.0f} h/sem",
                class_name="text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            rx.el.span(
                f"{employee['assignments']} mission(s)",
                class_name="text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] ml-auto",
            ),
            class_name="flex items-center gap-2 w-full mt-2",
        ),
        on_click=EmployeesState.select_employee(employee["id"]),
        key=key,
        class_name=rx.cond(
            EmployeesState.selected_employee_id == employee["id"],
            "w-full border-t border-[rgb(var(--ap-paper-rgb)/0.18)] border-l-2 border-l-[rgb(var(--ap-accent-rgb))] bg-[rgb(var(--ap-accent-rgb))]/[0.07] pl-3 pr-2 pt-4 text-left transition-colors",
            "border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-4 text-left hover:border-t-[rgb(var(--ap-accent-rgb)/0.40)] transition-all",
        ),
    )


def employee_list() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Registre",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Équipe",
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                EmployeesState.employee_count,
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-xs font-bold text-[rgb(var(--ap-paper-muted-rgb)/0.90)] w-fit",
            ),
            class_name="flex items-end justify-between gap-3",
        ),
        rx.cond(
            EmployeesState.is_loading,
            rx.el.div(skeleton_rows(3), class_name="mt-5"),
            rx.cond(
                EmployeesState.employees.length() > 0,
                rx.el.div(
                    rx.foreach(
                        EmployeesState.employees,
                        lambda e: _employee_card(e, key=e["id"].to_string()),
                    ),
                    class_name="flex flex-col gap-3 mt-5 max-h-[46rem] overflow-y-auto pr-1",
                ),
                empty_state(
                    "user-x",
                    "Aucun salarié pour ces critères.",
                    "Élargissez le statut, l'équipe ou la compétence pour "
                    "retrouver une fiche du registre.",
                    class_name="mt-5",
                ),
            ),
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full xl:w-[24rem] shrink-0 pt-5",
    )

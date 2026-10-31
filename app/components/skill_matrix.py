import reflex as rx

from app.components.design import empty_state
from app.states.employees_state import EmployeesState, MatrixCell, MatrixRow

_CELL_CLASSES = {
    "EXPERT": "flex h-8 w-full items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.50)] bg-[rgb(var(--ap-accent-rgb)/0.25)] text-[10px] font-bold text-[rgb(var(--ap-accent-pale-rgb))]",
    "AVANCE": "flex h-8 w-full items-center justify-center rounded-none border border-[rgb(var(--ap-sage-rgb)/0.40)] bg-[rgb(var(--ap-sage-rgb)/0.15)] text-[10px] font-bold text-[rgb(var(--ap-paper-muted-rgb))]",
    "INTERMEDIAIRE": "flex h-8 w-full items-center justify-center rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.35)] bg-[rgb(var(--ap-flame-soft-rgb)/0.12)] text-[10px] font-bold text-[rgb(var(--ap-warm-100-rgb))]",
    "DEBUTANT": "flex h-8 w-full items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.24)] bg-[rgb(var(--ap-surface-high-rgb))] text-[10px] font-bold text-[rgb(var(--ap-paper-muted-rgb)/0.82)]",
}


def _cell(cell: MatrixCell) -> rx.Component:
    return rx.el.div(
        rx.el.span(cell["short"]),
        title=f"{cell['skill']} · {cell['level_label']}",
        class_name=rx.match(
            cell["tone"],
            ("EXPERT", _CELL_CLASSES["EXPERT"]),
            ("AVANCE", _CELL_CLASSES["AVANCE"]),
            ("INTERMEDIAIRE", _CELL_CLASSES["INTERMEDIAIRE"]),
            ("DEBUTANT", _CELL_CLASSES["DEBUTANT"]),
            "flex h-8 w-full items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.12)] bg-[rgb(var(--ap-surface-soft-rgb))] text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)]",
        ),
    )


def _availability_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit whitespace-nowrap",
            ),
            (
                "warn",
                "rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit whitespace-nowrap",
            ),
            (
                "bad",
                "rounded-none border border-[rgb(var(--ap-danger-rgb)/0.30)] bg-[rgb(var(--ap-flame-strong-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-danger-soft-rgb))] w-fit whitespace-nowrap",
            ),
            (
                "info",
                "rounded-none border border-[rgb(var(--ap-info-rgb)/0.30)] bg-[rgb(var(--ap-info-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-info-soft-rgb))] w-fit whitespace-nowrap",
            ),
            "rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit whitespace-nowrap",
        ),
    )


def _matrix_row(row: MatrixRow, key: str = "") -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.button(
                rx.el.div(
                    rx.el.span(
                        row["initials"],
                        class_name="text-[11px] font-bold text-[rgb(var(--ap-ink-rgb))]",
                    ),
                    class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none bg-[rgb(var(--ap-accent-rgb))]",
                ),
                rx.el.div(
                    rx.el.p(
                        row["name"],
                        class_name="text-xs font-semibold text-[rgb(var(--ap-paper-rgb))] truncate text-left",
                    ),
                    rx.el.p(
                        row["team"],
                        class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] truncate text-left",
                    ),
                    class_name="min-w-0",
                ),
                on_click=EmployeesState.select_employee(row["id"]),
                class_name="flex items-center gap-2.5 min-w-0 w-full text-left",
            ),
            class_name="px-3 py-2 align-middle min-w-[13rem] sticky left-0 bg-[rgb(var(--ap-surface-soft-rgb)/0.95)]",
        ),
        rx.foreach(
            row["cells"],
            lambda cell: rx.el.td(
                _cell(cell), class_name="px-1.5 py-2 align-middle w-16"
            ),
        ),
        rx.el.td(
            rx.el.div(
                rx.el.div(
                    class_name="h-full rounded-none bg-gradient-to-r from-[rgb(var(--ap-sage-soft-rgb))] to-[rgb(var(--ap-accent-rgb))]",
                    style={"width": row["coverage_pct"]},
                ),
                class_name="h-1.5 w-24 rounded-none bg-[rgb(var(--ap-surface-control-rgb))]",
            ),
            rx.el.span(
                row["coverage_pct"],
                class_name="text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] mt-1 block",
            ),
            class_name="px-3 py-2 align-middle",
        ),
        rx.el.td(
            _availability_badge(
                row["availability_tone"], row["availability_label"]
            ),
            class_name="px-3 py-2 align-middle",
        ),
        key=key,
        class_name=rx.cond(
            EmployeesState.selected_employee_id == row["id"],
            "border-b border-[rgb(var(--ap-paper-rgb)/0.12)] bg-[rgb(var(--ap-accent-rgb))]/[0.07]",
            "border-b border-[rgb(var(--ap-paper-rgb)/0.12)] even:bg-[rgb(var(--ap-surface-soft-rgb))] hover:bg-[rgb(var(--ap-accent-rgb))]/[0.04] transition-colors",
        ),
    )


def _legend(label: str, dot: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(class_name=dot),
        rx.el.span(
            label, class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)]"
        ),
        class_name="flex items-center gap-2 w-fit",
    )


def skill_matrix() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Capital humain",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Matrice compétences & disponibilités",
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                rx.el.p(
                    "Croisement des habilitations de l'équipe et de leur présence réelle sur l'exploitation.",
                    class_name="text-xs font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-2 max-w-xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                _legend("Expert", "h-2.5 w-2.5 rounded-none bg-[rgb(var(--ap-accent-rgb))]"),
                _legend("Avancé", "h-2.5 w-2.5 rounded-none bg-[rgb(var(--ap-sage-soft-rgb))]"),
                _legend(
                    "Intermédiaire", "h-2.5 w-2.5 rounded-none bg-[rgb(var(--ap-flame-soft-rgb))]"
                ),
                _legend("Débutant", "h-2.5 w-2.5 rounded-none bg-[rgb(var(--ap-neutral-deep-rgb))]"),
                class_name="flex flex-wrap items-center gap-4",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4",
        ),
        rx.cond(
            EmployeesState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="ap-skeleton bg-[rgb(var(--ap-surface-high-rgb)/0.70)] h-12 w-full"
                ),
                rx.el.div(
                    class_name="ap-skeleton bg-[rgb(var(--ap-surface-high-rgb)/0.70)] h-12 w-full"
                ),
                rx.el.div(
                    class_name="ap-skeleton bg-[rgb(var(--ap-surface-high-rgb)/0.70)] h-12 w-full"
                ),
                class_name="flex flex-col gap-2 mt-6",
            ),
            rx.cond(
                EmployeesState.matrix_rows.length() > 0,
                rx.el.div(
                    rx.el.div(
                        rx.el.table(
                            rx.el.thead(
                                rx.el.tr(
                                    rx.el.th(
                                        rx.el.div(
                                            rx.icon(
                                                "users-round",
                                                class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb)/0.70)]",
                                            ),
                                            rx.el.span("Salarié"),
                                            class_name="flex items-center gap-1.5",
                                        ),
                                        class_name="px-3 py-3 text-left ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)] sticky left-0 bg-[rgb(var(--ap-surface-soft-rgb)/0.95)]",
                                    ),
                                    rx.foreach(
                                        EmployeesState.matrix_skills,
                                        lambda name: rx.el.th(
                                            rx.el.span(
                                                name,
                                                class_name="block w-16 text-[9px] font-semibold uppercase leading-tight tracking-[0.08em] text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
                                            ),
                                            class_name="px-1.5 py-3 align-bottom",
                                        ),
                                    ),
                                    rx.el.th(
                                        "Couverture",
                                        class_name="px-3 py-3 text-left ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)] whitespace-nowrap",
                                    ),
                                    rx.el.th(
                                        "Présence",
                                        class_name="px-3 py-3 text-left ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)] whitespace-nowrap",
                                    ),
                                    class_name="border-b border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))]",
                                ),
                            ),
                            rx.el.tbody(
                                rx.foreach(
                                    EmployeesState.matrix_rows,
                                    lambda row: _matrix_row(
                                        row, key=row["id"].to_string()
                                    ),
                                ),
                            ),
                            class_name="table-auto w-full min-w-[58rem]",
                        ),
                        class_name="overflow-x-auto",
                    ),
                    class_name="mt-6 w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-soft-rgb)/0.60)] overflow-hidden max-h-[34rem] overflow-y-auto",
                ),
                empty_state(
                    "search-x",
                    "Aucun salarié ne correspond aux filtres sélectionnés.",
                ),
            ),
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )

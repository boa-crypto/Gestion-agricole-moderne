import reflex as rx

from app.states.employees_state import EmployeesState, MatrixCell, MatrixRow

_CELL_CLASSES = {
    "EXPERT": "flex h-8 w-full items-center justify-center rounded-lg border border-lime-300/50 bg-lime-300/25 text-[10px] font-bold text-lime-100",
    "AVANCE": "flex h-8 w-full items-center justify-center rounded-lg border border-emerald-300/40 bg-emerald-300/15 text-[10px] font-bold text-emerald-100",
    "INTERMEDIAIRE": "flex h-8 w-full items-center justify-center rounded-lg border border-amber-300/35 bg-amber-300/12 text-[10px] font-bold text-amber-100",
    "DEBUTANT": "flex h-8 w-full items-center justify-center rounded-lg border border-white/15 bg-white/[0.06] text-[10px] font-bold text-emerald-100/60",
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
            "flex h-8 w-full items-center justify-center rounded-lg border border-white/5 bg-white/[0.02] text-[10px] font-medium text-emerald-100/20",
        ),
    )


def _availability_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit whitespace-nowrap",
            ),
            (
                "warn",
                "rounded-full border border-amber-300/30 bg-amber-300/10 px-2 py-0.5 text-[10px] font-bold text-amber-200 w-fit whitespace-nowrap",
            ),
            (
                "bad",
                "rounded-full border border-red-400/30 bg-red-500/10 px-2 py-0.5 text-[10px] font-bold text-red-300 w-fit whitespace-nowrap",
            ),
            (
                "info",
                "rounded-full border border-sky-300/30 bg-sky-300/10 px-2 py-0.5 text-[10px] font-bold text-sky-200 w-fit whitespace-nowrap",
            ),
            "rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/45 w-fit whitespace-nowrap",
        ),
    )


def _matrix_row(row: MatrixRow, key: str = "") -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.button(
                rx.el.div(
                    rx.el.span(
                        row["initials"],
                        class_name="text-[11px] font-bold text-[#04140d]",
                    ),
                    class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-lime-300",
                ),
                rx.el.div(
                    rx.el.p(
                        row["name"],
                        class_name="text-xs font-semibold text-emerald-50 truncate text-left",
                    ),
                    rx.el.p(
                        row["team"],
                        class_name="text-[10px] font-medium text-emerald-100/45 truncate text-left",
                    ),
                    class_name="min-w-0",
                ),
                on_click=EmployeesState.select_employee(row["id"]),
                class_name="flex items-center gap-2.5 min-w-0 w-full text-left",
            ),
            class_name="px-3 py-2 align-middle min-w-[13rem] sticky left-0 bg-[#03110b]/95",
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
                    class_name="h-full rounded-full bg-gradient-to-r from-emerald-400 to-lime-300",
                    style={"width": row["coverage_pct"]},
                ),
                class_name="h-1.5 w-24 rounded-full bg-white/10",
            ),
            rx.el.span(
                row["coverage_pct"],
                class_name="text-[10px] font-bold text-lime-200 mt-1 block",
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
            "border-b border-white/5 bg-lime-300/[0.07]",
            "border-b border-white/5 even:bg-white/[0.02] hover:bg-lime-300/[0.04] transition-colors",
        ),
    )


def _legend(label: str, dot: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(class_name=dot),
        rx.el.span(
            label, class_name="text-[11px] font-medium text-emerald-100/60"
        ),
        class_name="flex items-center gap-2 w-fit",
    )


def skill_matrix() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Capital humain",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Matrice compétences & disponibilités",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    "Croisement des habilitations de l'équipe et de leur présence réelle sur l'exploitation.",
                    class_name="text-xs font-medium text-emerald-100/50 mt-2 max-w-xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                _legend("Expert", "h-2.5 w-2.5 rounded-full bg-lime-300"),
                _legend("Avancé", "h-2.5 w-2.5 rounded-full bg-emerald-400"),
                _legend(
                    "Intermédiaire", "h-2.5 w-2.5 rounded-full bg-amber-300"
                ),
                _legend("Débutant", "h-2.5 w-2.5 rounded-full bg-white/40"),
                class_name="flex flex-wrap items-center gap-4",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4",
        ),
        rx.cond(
            EmployeesState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-12 rounded-xl bg-white/[0.05]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-12 rounded-xl bg-white/[0.05]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-12 rounded-xl bg-white/[0.05]"
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
                                                class_name="h-3.5 w-3.5 text-lime-300/70",
                                            ),
                                            rx.el.span("Salarié"),
                                            class_name="flex items-center gap-1.5",
                                        ),
                                        class_name="px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-100/45 sticky left-0 bg-[#03110b]/95",
                                    ),
                                    rx.foreach(
                                        EmployeesState.matrix_skills,
                                        lambda name: rx.el.th(
                                            rx.el.span(
                                                name,
                                                class_name="block w-16 text-[9px] font-semibold uppercase leading-tight tracking-[0.08em] text-emerald-100/45",
                                            ),
                                            class_name="px-1.5 py-3 align-bottom",
                                        ),
                                    ),
                                    rx.el.th(
                                        "Couverture",
                                        class_name="px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-100/45 whitespace-nowrap",
                                    ),
                                    rx.el.th(
                                        "Présence",
                                        class_name="px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-100/45 whitespace-nowrap",
                                    ),
                                    class_name="border-b border-white/10 bg-white/[0.03]",
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
                    class_name="mt-6 w-full rounded-2xl border border-white/10 bg-[#03110b]/60 overflow-hidden max-h-[34rem] overflow-y-auto",
                ),
                rx.el.div(
                    rx.icon("search-x", class_name="h-6 w-6 text-amber-300"),
                    rx.el.p(
                        "Aucun salarié ne correspond aux filtres sélectionnés.",
                        class_name="text-sm font-medium text-emerald-100/60 mt-2 text-center",
                    ),
                    class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-14 mt-6",
                ),
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )

import reflex as rx

from app.states.employees_state import EmployeesState, MatrixCell, MatrixRow

_CELL_CLASSES = {
    "EXPERT": "flex h-8 w-full items-center justify-center rounded-none border border-[#d8fa5e]/50 bg-[#d8fa5e]/25 text-[10px] font-bold text-[#efffc4]",
    "AVANCE": "flex h-8 w-full items-center justify-center rounded-none border border-[#a9c98b]/40 bg-[#a9c98b]/15 text-[10px] font-bold text-[#c9c5b4]",
    "INTERMEDIAIRE": "flex h-8 w-full items-center justify-center rounded-none border border-[#ff8a5b]/35 bg-[#ff8a5b]/12 text-[10px] font-bold text-[#ffdccb]",
    "DEBUTANT": "flex h-8 w-full items-center justify-center rounded-none border border-[#f2efe4]/16 bg-[#191c13] text-[10px] font-bold text-[#c9c5b4]/60",
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
            "flex h-8 w-full items-center justify-center rounded-none border border-[#f2efe4]/8 bg-[#0d0f09] text-[10px] font-medium text-[#c9c5b4]/20",
        ),
    )


def _availability_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit whitespace-nowrap",
            ),
            (
                "warn",
                "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffb894] w-fit whitespace-nowrap",
            ),
            (
                "bad",
                "rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-2 py-0.5 text-[10px] font-bold text-[#ff9b8c] w-fit whitespace-nowrap",
            ),
            (
                "info",
                "rounded-none border border-[#9cc3ff]/30 bg-[#9cc3ff]/10 px-2 py-0.5 text-[10px] font-bold text-[#c3daff] w-fit whitespace-nowrap",
            ),
            "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/45 w-fit whitespace-nowrap",
        ),
    )


def _matrix_row(row: MatrixRow, key: str = "") -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.button(
                rx.el.div(
                    rx.el.span(
                        row["initials"],
                        class_name="text-[11px] font-bold text-[#0A0A08]",
                    ),
                    class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none bg-[#d8fa5e]",
                ),
                rx.el.div(
                    rx.el.p(
                        row["name"],
                        class_name="text-xs font-semibold text-[#f2efe4] truncate text-left",
                    ),
                    rx.el.p(
                        row["team"],
                        class_name="text-[10px] font-medium text-[#c9c5b4]/45 truncate text-left",
                    ),
                    class_name="min-w-0",
                ),
                on_click=EmployeesState.select_employee(row["id"]),
                class_name="flex items-center gap-2.5 min-w-0 w-full text-left",
            ),
            class_name="px-3 py-2 align-middle min-w-[13rem] sticky left-0 bg-[#0D0F09]/95",
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
                    class_name="h-full rounded-none bg-gradient-to-r from-[#8fb37a] to-[#d8fa5e]",
                    style={"width": row["coverage_pct"]},
                ),
                class_name="h-1.5 w-24 rounded-none bg-[#20241a]",
            ),
            rx.el.span(
                row["coverage_pct"],
                class_name="text-[10px] font-bold text-[#e4ff9b] mt-1 block",
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
            "border-b border-[#f2efe4]/8 bg-[#d8fa5e]/[0.07]",
            "border-b border-[#f2efe4]/8 even:bg-[#0d0f09] hover:bg-[#d8fa5e]/[0.04] transition-colors",
        ),
    )


def _legend(label: str, dot: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(class_name=dot),
        rx.el.span(
            label, class_name="text-[11px] font-medium text-[#c9c5b4]/60"
        ),
        class_name="flex items-center gap-2 w-fit",
    )


def skill_matrix() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Capital humain",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Matrice compétences & disponibilités",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                rx.el.p(
                    "Croisement des habilitations de l'équipe et de leur présence réelle sur l'exploitation.",
                    class_name="text-xs font-medium text-[#c9c5b4]/50 mt-2 max-w-xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                _legend("Expert", "h-2.5 w-2.5 rounded-none bg-[#d8fa5e]"),
                _legend("Avancé", "h-2.5 w-2.5 rounded-none bg-[#8fb37a]"),
                _legend(
                    "Intermédiaire", "h-2.5 w-2.5 rounded-none bg-[#ff8a5b]"
                ),
                _legend("Débutant", "h-2.5 w-2.5 rounded-none bg-[#4a5140]"),
                class_name="flex flex-wrap items-center gap-4",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4",
        ),
        rx.cond(
            EmployeesState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-12 rounded-none bg-[#16190f]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-12 rounded-none bg-[#16190f]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-12 rounded-none bg-[#16190f]"
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
                                                class_name="h-3.5 w-3.5 text-[#d8fa5e]/70",
                                            ),
                                            rx.el.span("Salarié"),
                                            class_name="flex items-center gap-1.5",
                                        ),
                                        class_name="px-3 py-3 text-left ap-eyebrow text-[#c9c5b4]/45 sticky left-0 bg-[#0D0F09]/95",
                                    ),
                                    rx.foreach(
                                        EmployeesState.matrix_skills,
                                        lambda name: rx.el.th(
                                            rx.el.span(
                                                name,
                                                class_name="block w-16 text-[9px] font-semibold uppercase leading-tight tracking-[0.08em] text-[#c9c5b4]/45",
                                            ),
                                            class_name="px-1.5 py-3 align-bottom",
                                        ),
                                    ),
                                    rx.el.th(
                                        "Couverture",
                                        class_name="px-3 py-3 text-left ap-eyebrow text-[#c9c5b4]/45 whitespace-nowrap",
                                    ),
                                    rx.el.th(
                                        "Présence",
                                        class_name="px-3 py-3 text-left ap-eyebrow text-[#c9c5b4]/45 whitespace-nowrap",
                                    ),
                                    class_name="border-b border-[#f2efe4]/12 bg-[#101208]",
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
                    class_name="mt-6 w-full rounded-none border border-[#f2efe4]/12 bg-[#0D0F09]/60 overflow-hidden max-h-[34rem] overflow-y-auto",
                ),
                rx.el.div(
                    rx.icon("search-x", class_name="h-6 w-6 text-[#ff8a5b]"),
                    rx.el.p(
                        "Aucun salarié ne correspond aux filtres sélectionnés.",
                        class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2 text-center",
                    ),
                    class_name="flex flex-col items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#101208] py-14 mt-6",
                ),
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )

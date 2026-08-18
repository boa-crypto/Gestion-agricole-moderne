import reflex as rx

from app.states.employees_state import (
    AssignmentRow,
    AvailabilityRow,
    EmployeesState,
    SkillRow,
)

_INPUT = "w-full rounded-xl border border-white/10 bg-[#04140d] px-3 py-2.5 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 outline-hidden transition-colors"
_SELECT = f"{_INPUT} appearance-none cursor-pointer pr-9"


def _fact(label: str, value: rx.Var | str, icon: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-lime-300/80"),
            rx.el.span(
                label,
                class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            value,
            class_name="text-sm font-semibold text-emerald-50 mt-1.5 truncate",
        ),
        class_name="w-full rounded-xl border border-white/10 bg-white/[0.03] p-3 min-w-0",
    )


def _tone_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
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


def _detail_header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    EmployeesState.employee_detail["initials"],
                    class_name="text-lg font-bold text-[#04140d]",
                ),
                class_name="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-lime-300",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        EmployeesState.employee_detail["code"],
                        class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                    ),
                    _tone_badge(
                        EmployeesState.employee_detail["status_tone"],
                        EmployeesState.employee_detail["status_label"],
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h2(
                    EmployeesState.employee_detail["name"],
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    f"{EmployeesState.employee_detail['job_title']} · {EmployeesState.employee_detail['team']} · {EmployeesState.employee_detail['contract_label']}",
                    class_name="text-xs font-medium text-emerald-100/55 mt-1",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-center gap-4 min-w-0",
        ),
        rx.el.button(
            rx.icon("pencil", class_name="h-4 w-4"),
            rx.el.span("Modifier la fiche"),
            on_click=EmployeesState.open_employee_edit,
            class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/75 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
        ),
        class_name="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-5 border-b border-white/10",
    )


def _skill_card(skill: SkillRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("badge-check", class_name="h-4 w-4 text-lime-300"),
                class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/[0.04]",
            ),
            rx.el.div(
                rx.el.p(
                    skill["name"],
                    class_name="text-sm font-semibold text-emerald-50 truncate",
                ),
                rx.el.p(
                    f"{skill['category']} · {skill['years']:.1f} an(s) d'expérience",
                    class_name="text-[10px] font-medium text-emerald-100/45 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                skill["level_label"],
                class_name=rx.match(
                    skill["level"],
                    (
                        "EXPERT",
                        "rounded-full border border-lime-300/40 bg-lime-300/15 px-2 py-0.5 text-[10px] font-bold text-lime-100 w-fit",
                    ),
                    (
                        "AVANCE",
                        "rounded-full border border-emerald-300/40 bg-emerald-300/15 px-2 py-0.5 text-[10px] font-bold text-emerald-100 w-fit",
                    ),
                    (
                        "INTERMEDIAIRE",
                        "rounded-full border border-amber-300/40 bg-amber-300/12 px-2 py-0.5 text-[10px] font-bold text-amber-100 w-fit",
                    ),
                    "rounded-full border border-white/15 bg-white/[0.06] px-2 py-0.5 text-[10px] font-bold text-emerald-100/60 w-fit",
                ),
            ),
            rx.el.button(
                rx.icon("trash-2", class_name="h-3.5 w-3.5"),
                on_click=EmployeesState.remove_skill(skill["id"]),
                title="Retirer la compétence",
                class_name="flex h-7 w-7 items-center justify-center rounded-lg border border-red-400/30 bg-red-500/10 text-red-300 hover:bg-red-500/20 transition-colors shrink-0",
            ),
            class_name="flex items-center gap-2.5 w-full",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-full rounded-full bg-gradient-to-r from-emerald-400 to-lime-300",
                style={"width": f"{skill['score'] * 25}%"},
            ),
            class_name="h-1.5 w-full rounded-full bg-white/10 mt-3",
        ),
        rx.el.div(
            rx.cond(
                skill["requires_certification"],
                _tone_badge(skill["expiry_tone"], skill["expiry_label"]),
                rx.el.span(
                    "Sans certification requise",
                    class_name="text-[10px] font-medium text-emerald-100/40",
                ),
            ),
            rx.el.span(
                f"Obtenue {skill['certified_label']}",
                class_name="text-[10px] font-medium text-emerald-100/35 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:border-lime-300/25 transition-colors",
    )


def _skill_form() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            rx.el.div(
                rx.el.select(
                    rx.el.option(
                        "Compétence du référentiel", value="", disabled=True
                    ),
                    rx.foreach(
                        EmployeesState.skill_options,
                        lambda opt: rx.el.option(
                            opt["label"], value=opt["value"]
                        ),
                    ),
                    name="skill_id",
                    default_value="",
                    key=f"skill-add-{EmployeesState.form_key}",
                    class_name=_SELECT,
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                ),
                class_name="relative w-full",
            ),
            rx.el.div(
                rx.el.select(
                    rx.foreach(
                        EmployeesState.level_options,
                        lambda opt: rx.el.option(
                            opt["label"], value=opt["value"]
                        ),
                    ),
                    name="level",
                    default_value="INTERMEDIAIRE",
                    key=f"skill-level-{EmployeesState.form_key}",
                    class_name=_SELECT,
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                ),
                class_name="relative w-full",
            ),
            rx.el.input(
                type="number",
                step="0.5",
                name="years_experience",
                placeholder="Années d'expérience",
                default_value="1",
                key=f"skill-years-{EmployeesState.form_key}",
                class_name=_INPUT,
            ),
            rx.el.input(
                type="date",
                name="certified_on",
                key=f"skill-cert-{EmployeesState.form_key}",
                class_name=_INPUT,
            ),
            rx.el.input(
                type="date",
                name="certificate_expiry",
                key=f"skill-exp-{EmployeesState.form_key}",
                class_name=_INPUT,
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3",
        ),
        rx.cond(
            EmployeesState.skill_error != "",
            rx.el.p(
                EmployeesState.skill_error,
                class_name="text-xs font-semibold text-red-300 mt-2",
            ),
            rx.fragment(),
        ),
        rx.el.button(
            rx.icon("plus", class_name="h-4 w-4 text-[#04140d]"),
            rx.el.span(
                "Ajouter / mettre à jour la compétence",
                class_name="text-[#04140d]",
            ),
            type="submit",
            class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit mt-3",
        ),
        on_submit=EmployeesState.submit_skill,
        reset_on_submit=True,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 mt-4",
    )


def _availability_row(item: AvailabilityRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.match(
                item["type"],
                (
                    "DISPONIBLE",
                    rx.icon("circle-check", class_name="h-4 w-4 text-lime-300"),
                ),
                (
                    "ASTREINTE",
                    rx.icon("bell-ring", class_name="h-4 w-4 text-sky-300"),
                ),
                (
                    "FORMATION",
                    rx.icon(
                        "graduation-cap", class_name="h-4 w-4 text-sky-300"
                    ),
                ),
                (
                    "CONGE",
                    rx.icon("tree_palm", class_name="h-4 w-4 text-amber-300"),
                ),
                (
                    "ARRET",
                    rx.icon("bandage", class_name="h-4 w-4 text-red-300"),
                ),
                rx.icon(
                    "circle-slash", class_name="h-4 w-4 text-emerald-100/40"
                ),
            ),
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/[0.04]",
        ),
        rx.el.div(
            rx.el.div(
                _tone_badge(item["tone"], item["type_label"]),
                rx.cond(
                    item["is_current"],
                    rx.el.span(
                        "en cours",
                        class_name="text-[10px] font-bold text-lime-200",
                    ),
                    rx.fragment(),
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.p(
                f"{item['start_label']} → {item['end_label']} · {item['days']} j · {item['hours_per_day']:.1f} h/j",
                class_name="text-[11px] font-medium text-emerald-100/55 mt-1",
            ),
            rx.el.p(
                item["reason"],
                class_name="text-[10px] font-medium text-emerald-100/35 truncate",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.button(
            rx.icon("trash-2", class_name="h-3.5 w-3.5"),
            on_click=EmployeesState.remove_availability(item["id"]),
            title="Supprimer le créneau",
            class_name="flex h-7 w-7 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-emerald-100/60 hover:text-red-300 hover:border-red-400/30 transition-colors shrink-0",
        ),
        key=key,
        class_name="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-3",
    )


def _availability_form() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            rx.el.div(
                rx.el.select(
                    rx.foreach(
                        EmployeesState.availability_options,
                        lambda opt: rx.el.option(
                            opt["label"], value=opt["value"]
                        ),
                    ),
                    name="type",
                    default_value="DISPONIBLE",
                    key=f"av-type-{EmployeesState.form_key}",
                    class_name=_SELECT,
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                ),
                class_name="relative w-full",
            ),
            rx.el.input(
                type="date",
                name="start_date",
                key=f"av-start-{EmployeesState.form_key}",
                class_name=_INPUT,
            ),
            rx.el.input(
                type="date",
                name="end_date",
                key=f"av-end-{EmployeesState.form_key}",
                class_name=_INPUT,
            ),
            rx.el.input(
                type="number",
                step="0.5",
                name="hours_per_day",
                placeholder="Heures / jour",
                default_value="7",
                key=f"av-hours-{EmployeesState.form_key}",
                class_name=_INPUT,
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3",
        ),
        rx.el.input(
            name="reason",
            placeholder="Motif ou commentaire (facultatif)",
            key=f"av-reason-{EmployeesState.form_key}",
            class_name=f"{_INPUT} mt-3",
        ),
        rx.cond(
            EmployeesState.availability_error != "",
            rx.el.p(
                EmployeesState.availability_error,
                class_name="text-xs font-semibold text-red-300 mt-2",
            ),
            rx.fragment(),
        ),
        rx.el.button(
            rx.icon("calendar-plus", class_name="h-4 w-4 text-[#04140d]"),
            rx.el.span("Enregistrer le créneau", class_name="text-[#04140d]"),
            type="submit",
            class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit mt-3",
        ),
        on_submit=EmployeesState.submit_availability,
        reset_on_submit=True,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 mt-4",
    )


def _assignment_row(item: AssignmentRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    item["title"],
                    class_name="text-sm font-semibold text-emerald-50 truncate",
                ),
                rx.el.p(
                    f"{item['role_label']} · {item['context']}",
                    class_name="text-[10px] font-medium text-emerald-100/45 truncate mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            _tone_badge(item["tone"], item["status_label"]),
            class_name="flex items-start gap-3 w-full",
        ),
        rx.el.div(
            rx.icon("calendar-days", class_name="h-3.5 w-3.5 text-lime-300/70"),
            rx.el.span(
                f"{item['start_label']} → {item['end_label']}",
                class_name="text-[11px] font-medium text-emerald-100/55",
            ),
            rx.icon("clock", class_name="h-3.5 w-3.5 text-emerald-300/70 ml-2"),
            rx.el.span(
                f"{item['planned_hours']:.1f} h prévues · {item['actual_hours']:.1f} h réalisées",
                class_name="text-[11px] font-medium text-emerald-100/55",
            ),
            rx.el.span(
                f"{item['labor_cost']:.0f} €",
                class_name="text-[11px] font-bold text-lime-200 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-1.5 mt-3",
        ),
        rx.el.div(
            rx.cond(
                item["status"] == "PROPOSEE",
                rx.el.button(
                    rx.icon("check", class_name="h-3.5 w-3.5"),
                    rx.el.span("Confirmer", class_name="text-[11px]"),
                    on_click=EmployeesState.confirm_assignment(item["id"]),
                    class_name="flex items-center gap-1.5 rounded-full border border-lime-300/30 bg-lime-300/10 px-2.5 py-1 text-lime-200 hover:bg-lime-300/20 transition-colors w-fit",
                ),
                rx.fragment(),
            ),
            rx.cond(
                (item["status"] == "TERMINEE") | (item["status"] == "ANNULEE"),
                rx.fragment(),
                rx.el.button(
                    rx.icon("flag", class_name="h-3.5 w-3.5"),
                    rx.el.span("Clôturer", class_name="text-[11px]"),
                    on_click=EmployeesState.complete_assignment(item["id"]),
                    class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-emerald-100/70 hover:text-emerald-50 hover:border-lime-300/30 transition-colors w-fit",
                ),
            ),
            rx.cond(
                (item["status"] == "TERMINEE") | (item["status"] == "ANNULEE"),
                rx.fragment(),
                rx.el.button(
                    rx.icon("x", class_name="h-3.5 w-3.5"),
                    rx.el.span("Annuler", class_name="text-[11px]"),
                    on_click=EmployeesState.cancel_assignment(item["id"]),
                    class_name="flex items-center gap-1.5 rounded-full border border-red-400/30 bg-red-500/10 px-2.5 py-1 text-red-300 hover:bg-red-500/20 transition-colors w-fit",
                ),
            ),
            class_name="flex flex-wrap items-center gap-2 border-t border-white/5 pt-3 mt-3",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4",
    )


def _skills_block() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Compétences & certifications",
                class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
            ),
            rx.el.span(
                f"Niveau moyen {EmployeesState.employee_detail['avg_level']} / 4",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3",
        ),
        rx.cond(
            EmployeesState.employee_skills.length() > 0,
            rx.el.div(
                rx.foreach(
                    EmployeesState.employee_skills,
                    lambda s: _skill_card(s, key=s["id"].to_string()),
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 mt-4",
            ),
            rx.el.p(
                "Aucune compétence consignée pour ce salarié.",
                class_name="text-sm font-medium text-emerald-100/50 mt-4",
            ),
        ),
        _skill_form(),
        class_name="mt-8",
    )


def _availability_block() -> rx.Component:
    return rx.el.div(
        rx.el.span(
            "Disponibilités & absences",
            class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
        ),
        rx.cond(
            EmployeesState.availabilities.length() > 0,
            rx.el.div(
                rx.foreach(
                    EmployeesState.availabilities,
                    lambda a: _availability_row(a, key=a["id"].to_string()),
                ),
                class_name="flex flex-col gap-2 mt-4",
            ),
            rx.el.p(
                "Aucun créneau planifié.",
                class_name="text-sm font-medium text-emerald-100/50 mt-4",
            ),
        ),
        _availability_form(),
        class_name="mt-8 border-t border-white/10 pt-6",
    )


def _assignment_block() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Affectations",
                class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
            ),
            rx.el.span(
                f"{EmployeesState.employee_detail['assignment_count']} missions · {EmployeesState.employee_detail['planned_hours']} h à venir",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3",
        ),
        rx.cond(
            EmployeesState.assignments.length() > 0,
            rx.el.div(
                rx.foreach(
                    EmployeesState.assignments,
                    lambda a: _assignment_row(a, key=a["id"].to_string()),
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 mt-4",
            ),
            rx.el.p(
                "Aucune affectation enregistrée pour ce salarié.",
                class_name="text-sm font-medium text-emerald-100/50 mt-4",
            ),
        ),
        class_name="mt-8 border-t border-white/10 pt-6",
    )


def employee_detail() -> rx.Component:
    return rx.el.section(
        rx.cond(
            EmployeesState.has_selection,
            rx.el.div(
                _detail_header(),
                rx.el.div(
                    _fact(
                        "Contrat",
                        EmployeesState.employee_detail["contract_label"],
                        "file-text",
                    ),
                    _fact(
                        "Embauche",
                        EmployeesState.employee_detail["hired_label"],
                        "calendar-plus",
                    ),
                    _fact(
                        "Ancienneté",
                        f"{EmployeesState.employee_detail['seniority']} an(s)",
                        "history",
                    ),
                    _fact(
                        "Fin de contrat",
                        EmployeesState.employee_detail["contract_end_label"],
                        "calendar-x",
                    ),
                    _fact(
                        "Temps de travail",
                        f"{EmployeesState.employee_detail['weekly_hours']} h/sem",
                        "clock",
                    ),
                    _fact(
                        "Coût horaire",
                        f"{EmployeesState.employee_detail['hourly_cost']} €",
                        "coins",
                    ),
                    _fact(
                        "Coût hebdo",
                        f"{EmployeesState.employee_detail['weekly_cost']} €",
                        "wallet",
                    ),
                    _fact(
                        "Compétences",
                        EmployeesState.employee_detail["skill_count"],
                        "badge-check",
                    ),
                    class_name="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-5",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.icon(
                            "mail", class_name="h-3.5 w-3.5 text-lime-300/80"
                        ),
                        rx.el.span(
                            EmployeesState.employee_detail["email"],
                            class_name="text-[11px] font-medium text-emerald-100/60 truncate",
                        ),
                        class_name="flex items-center gap-1.5 min-w-0",
                    ),
                    rx.el.div(
                        rx.icon(
                            "phone", class_name="h-3.5 w-3.5 text-lime-300/80"
                        ),
                        rx.el.span(
                            EmployeesState.employee_detail["phone"],
                            class_name="text-[11px] font-medium text-emerald-100/60",
                        ),
                        class_name="flex items-center gap-1.5",
                    ),
                    rx.el.div(
                        rx.icon(
                            "life-buoy",
                            class_name="h-3.5 w-3.5 text-amber-300/80",
                        ),
                        rx.el.span(
                            EmployeesState.employee_detail["emergency_contact"],
                            class_name="text-[11px] font-medium text-emerald-100/60 truncate",
                        ),
                        class_name="flex items-center gap-1.5 min-w-0",
                    ),
                    rx.el.span(
                        EmployeesState.employee_detail["licence_label"],
                        class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
                    ),
                    rx.el.span(
                        f"{EmployeesState.employee_detail['phyto_label']} · {EmployeesState.employee_detail['phyto_expiry_label']}",
                        class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-semibold text-lime-200 w-fit",
                    ),
                    class_name="flex flex-wrap items-center gap-4 mt-4",
                ),
                rx.el.p(
                    EmployeesState.employee_detail["notes"],
                    class_name="text-[11px] font-medium text-emerald-100/50 mt-3 leading-relaxed",
                ),
                _skills_block(),
                _availability_block(),
                _assignment_block(),
                class_name="w-full",
            ),
            rx.el.div(
                rx.icon("users-round", class_name="h-7 w-7 text-lime-300"),
                rx.el.p(
                    "Sélectionnez un salarié dans le registre ou créez une première fiche.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-3 text-center max-w-sm",
                ),
                class_name="flex flex-col items-center justify-center py-24",
            ),
        ),
        class_name="flex-1 min-w-0 w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )

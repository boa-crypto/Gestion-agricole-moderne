import reflex as rx

from app.states.employees_state import (
    AssignmentRow,
    AvailabilityRow,
    EmployeesState,
    SkillRow,
)

_INPUT = "w-full rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] px-3 py-2.5 text-sm font-medium text-[#f2efe4] placeholder:text-[#c9c5b4]/30 focus:border-[#d8fa5e]/50 outline-hidden transition-colors"
_SELECT = f"{_INPUT} appearance-none cursor-pointer pr-9"


def _fact(label: str, value: rx.Var | str, icon: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-[#d8fa5e]/80"),
            rx.el.span(
                label,
                class_name="ap-eyebrow text-[#c9c5b4]/45",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            value,
            class_name="text-sm font-semibold text-[#f2efe4] mt-1.5 truncate",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3 min-w-0",
    )


def _tone_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
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


def _detail_header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    EmployeesState.employee_detail["initials"],
                    class_name="text-lg font-bold text-[#0A0A08]",
                ),
                class_name="flex h-14 w-14 shrink-0 items-center justify-center rounded-none bg-[#d8fa5e]",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        EmployeesState.employee_detail["code"],
                        class_name="ap-eyebrow text-[#d8fa5e]/80",
                    ),
                    _tone_badge(
                        EmployeesState.employee_detail["status_tone"],
                        EmployeesState.employee_detail["status_label"],
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h2(
                    EmployeesState.employee_detail["name"],
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                rx.el.p(
                    f"{EmployeesState.employee_detail['job_title']} · {EmployeesState.employee_detail['team']} · {EmployeesState.employee_detail['contract_label']}",
                    class_name="text-xs font-medium text-[#c9c5b4]/55 mt-1",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-center gap-4 min-w-0",
        ),
        rx.el.button(
            rx.icon("pencil", class_name="h-4 w-4"),
            rx.el.span("Modifier la fiche"),
            on_click=EmployeesState.open_employee_edit,
            class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2.5 text-sm font-semibold text-[#c9c5b4]/75 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit",
        ),
        class_name="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-5 border-b border-[#f2efe4]/12",
    )


def _skill_card(skill: SkillRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("badge-check", class_name="h-4 w-4 text-[#d8fa5e]"),
                class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#14160f]",
            ),
            rx.el.div(
                rx.el.p(
                    skill["name"],
                    class_name="text-sm font-semibold text-[#f2efe4] truncate",
                ),
                rx.el.p(
                    f"{skill['category']} · {skill['years']:.1f} an(s) d'expérience",
                    class_name="text-[10px] font-medium text-[#c9c5b4]/45 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                skill["level_label"],
                class_name=rx.match(
                    skill["level"],
                    (
                        "EXPERT",
                        "rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/15 px-2 py-0.5 text-[10px] font-bold text-[#efffc4] w-fit",
                    ),
                    (
                        "AVANCE",
                        "rounded-none border border-[#a9c98b]/40 bg-[#a9c98b]/15 px-2 py-0.5 text-[10px] font-bold text-[#c9c5b4] w-fit",
                    ),
                    (
                        "INTERMEDIAIRE",
                        "rounded-none border border-[#ff8a5b]/40 bg-[#ff8a5b]/12 px-2 py-0.5 text-[10px] font-bold text-[#ffdccb] w-fit",
                    ),
                    "rounded-none border border-[#f2efe4]/16 bg-[#191c13] px-2 py-0.5 text-[10px] font-bold text-[#c9c5b4]/60 w-fit",
                ),
            ),
            rx.el.button(
                rx.icon("trash-2", class_name="h-3.5 w-3.5"),
                on_click=EmployeesState.remove_skill(skill["id"]),
                title="Retirer la compétence",
                class_name="flex h-7 w-7 items-center justify-center rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 text-[#ff9b8c] hover:bg-[#f2452c]/20 transition-colors shrink-0",
            ),
            class_name="flex items-center gap-2.5 w-full",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-full rounded-none bg-gradient-to-r from-[#8fb37a] to-[#d8fa5e]",
                style={"width": f"{skill['score'] * 25}%"},
            ),
            class_name="h-1.5 w-full rounded-none bg-[#20241a] mt-3",
        ),
        rx.el.div(
            rx.cond(
                skill["requires_certification"],
                _tone_badge(skill["expiry_tone"], skill["expiry_label"]),
                rx.el.span(
                    "Sans certification requise",
                    class_name="text-[10px] font-medium text-[#c9c5b4]/40",
                ),
            ),
            rx.el.span(
                f"Obtenue {skill['certified_label']}",
                class_name="text-[10px] font-medium text-[#c9c5b4]/35 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 hover:border-[#d8fa5e]/25 transition-colors",
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
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
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
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
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
                class_name="text-xs font-semibold text-[#ff9b8c] mt-2",
            ),
            rx.fragment(),
        ),
        rx.el.button(
            rx.icon("plus", class_name="h-4 w-4 text-[#0A0A08]"),
            rx.el.span(
                "Ajouter / mettre à jour la compétence",
                class_name="text-[#0A0A08]",
            ),
            type="submit",
            class_name="flex items-center gap-2 rounded-none bg-[#d8fa5e] px-4 py-2.5 text-sm font-semibold hover:bg-[#e4ff9b] transition-colors w-fit mt-3",
        ),
        on_submit=EmployeesState.submit_skill,
        reset_on_submit=True,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 mt-4",
    )


def _availability_row(item: AvailabilityRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.match(
                item["type"],
                (
                    "DISPONIBLE",
                    rx.icon("circle-check", class_name="h-4 w-4 text-[#d8fa5e]"),
                ),
                (
                    "ASTREINTE",
                    rx.icon("bell-ring", class_name="h-4 w-4 text-[#9cc3ff]"),
                ),
                (
                    "FORMATION",
                    rx.icon(
                        "graduation-cap", class_name="h-4 w-4 text-[#9cc3ff]"
                    ),
                ),
                (
                    "CONGE",
                    rx.icon("tree_palm", class_name="h-4 w-4 text-[#ff8a5b]"),
                ),
                (
                    "ARRET",
                    rx.icon("bandage", class_name="h-4 w-4 text-[#ff9b8c]"),
                ),
                rx.icon(
                    "circle-slash", class_name="h-4 w-4 text-[#c9c5b4]/40"
                ),
            ),
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#14160f]",
        ),
        rx.el.div(
            rx.el.div(
                _tone_badge(item["tone"], item["type_label"]),
                rx.cond(
                    item["is_current"],
                    rx.el.span(
                        "en cours",
                        class_name="text-[10px] font-bold text-[#e4ff9b]",
                    ),
                    rx.fragment(),
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.p(
                f"{item['start_label']} → {item['end_label']} · {item['days']} j · {item['hours_per_day']:.1f} h/j",
                class_name="text-[11px] font-medium text-[#c9c5b4]/55 mt-1",
            ),
            rx.el.p(
                item["reason"],
                class_name="text-[10px] font-medium text-[#c9c5b4]/35 truncate",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.button(
            rx.icon("trash-2", class_name="h-3.5 w-3.5"),
            on_click=EmployeesState.remove_availability(item["id"]),
            title="Supprimer le créneau",
            class_name="flex h-7 w-7 items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#14160f] text-[#c9c5b4]/60 hover:text-[#ff9b8c] hover:border-[#ff6b5a]/30 transition-colors shrink-0",
        ),
        key=key,
        class_name="flex items-center gap-3 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
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
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
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
                class_name="text-xs font-semibold text-[#ff9b8c] mt-2",
            ),
            rx.fragment(),
        ),
        rx.el.button(
            rx.icon("calendar-plus", class_name="h-4 w-4 text-[#0A0A08]"),
            rx.el.span("Enregistrer le créneau", class_name="text-[#0A0A08]"),
            type="submit",
            class_name="flex items-center gap-2 rounded-none bg-[#d8fa5e] px-4 py-2.5 text-sm font-semibold hover:bg-[#e4ff9b] transition-colors w-fit mt-3",
        ),
        on_submit=EmployeesState.submit_availability,
        reset_on_submit=True,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 mt-4",
    )


def _assignment_row(item: AssignmentRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    item["title"],
                    class_name="text-sm font-semibold text-[#f2efe4] truncate",
                ),
                rx.el.p(
                    f"{item['role_label']} · {item['context']}",
                    class_name="text-[10px] font-medium text-[#c9c5b4]/45 truncate mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            _tone_badge(item["tone"], item["status_label"]),
            class_name="flex items-start gap-3 w-full",
        ),
        rx.el.div(
            rx.icon("calendar-days", class_name="h-3.5 w-3.5 text-[#d8fa5e]/70"),
            rx.el.span(
                f"{item['start_label']} → {item['end_label']}",
                class_name="text-[11px] font-medium text-[#c9c5b4]/55",
            ),
            rx.icon("clock", class_name="h-3.5 w-3.5 text-[#a9c98b]/70 ml-2"),
            rx.el.span(
                f"{item['planned_hours']:.1f} h prévues · {item['actual_hours']:.1f} h réalisées",
                class_name="text-[11px] font-medium text-[#c9c5b4]/55",
            ),
            rx.el.span(
                f"{item['labor_cost']:.0f} €",
                class_name="text-[11px] font-bold text-[#e4ff9b] ml-auto",
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
                    class_name="flex items-center gap-1.5 rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2.5 py-1 text-[#e4ff9b] hover:bg-[#d8fa5e]/20 transition-colors w-fit",
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
                    class_name="flex items-center gap-1.5 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2.5 py-1 text-[#c9c5b4]/70 hover:text-[#f2efe4] hover:border-[#d8fa5e]/30 transition-colors w-fit",
                ),
            ),
            rx.cond(
                (item["status"] == "TERMINEE") | (item["status"] == "ANNULEE"),
                rx.fragment(),
                rx.el.button(
                    rx.icon("x", class_name="h-3.5 w-3.5"),
                    rx.el.span("Annuler", class_name="text-[11px]"),
                    on_click=EmployeesState.cancel_assignment(item["id"]),
                    class_name="flex items-center gap-1.5 rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-2.5 py-1 text-[#ff9b8c] hover:bg-[#f2452c]/20 transition-colors w-fit",
                ),
            ),
            class_name="flex flex-wrap items-center gap-2 border-t border-[#f2efe4]/8 pt-3 mt-3",
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4",
    )


def _skills_block() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Compétences & certifications",
                class_name="ap-eyebrow text-[#d8fa5e]/80",
            ),
            rx.el.span(
                f"Niveau moyen {EmployeesState.employee_detail['avg_level']} / 4",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/60 w-fit ml-auto",
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
                class_name="text-sm font-medium text-[#c9c5b4]/50 mt-4",
            ),
        ),
        _skill_form(),
        class_name="mt-8",
    )


def _availability_block() -> rx.Component:
    return rx.el.div(
        rx.el.span(
            "Disponibilités & absences",
            class_name="ap-eyebrow text-[#d8fa5e]/80",
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
                class_name="text-sm font-medium text-[#c9c5b4]/50 mt-4",
            ),
        ),
        _availability_form(),
        class_name="mt-8 border-t border-[#f2efe4]/12 pt-6",
    )


def _assignment_block() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Affectations",
                class_name="ap-eyebrow text-[#d8fa5e]/80",
            ),
            rx.el.span(
                f"{EmployeesState.employee_detail['assignment_count']} missions · {EmployeesState.employee_detail['planned_hours']} h à venir",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/60 w-fit ml-auto",
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
                class_name="text-sm font-medium text-[#c9c5b4]/50 mt-4",
            ),
        ),
        class_name="mt-8 border-t border-[#f2efe4]/12 pt-6",
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
                            "mail", class_name="h-3.5 w-3.5 text-[#d8fa5e]/80"
                        ),
                        rx.el.span(
                            EmployeesState.employee_detail["email"],
                            class_name="text-[11px] font-medium text-[#c9c5b4]/60 truncate",
                        ),
                        class_name="flex items-center gap-1.5 min-w-0",
                    ),
                    rx.el.div(
                        rx.icon(
                            "phone", class_name="h-3.5 w-3.5 text-[#d8fa5e]/80"
                        ),
                        rx.el.span(
                            EmployeesState.employee_detail["phone"],
                            class_name="text-[11px] font-medium text-[#c9c5b4]/60",
                        ),
                        class_name="flex items-center gap-1.5",
                    ),
                    rx.el.div(
                        rx.icon(
                            "life-buoy",
                            class_name="h-3.5 w-3.5 text-[#ff8a5b]/80",
                        ),
                        rx.el.span(
                            EmployeesState.employee_detail["emergency_contact"],
                            class_name="text-[11px] font-medium text-[#c9c5b4]/60 truncate",
                        ),
                        class_name="flex items-center gap-1.5 min-w-0",
                    ),
                    rx.el.span(
                        EmployeesState.employee_detail["licence_label"],
                        class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
                    ),
                    rx.el.span(
                        f"{EmployeesState.employee_detail['phyto_label']} · {EmployeesState.employee_detail['phyto_expiry_label']}",
                        class_name="rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-semibold text-[#e4ff9b] w-fit",
                    ),
                    class_name="flex flex-wrap items-center gap-4 mt-4",
                ),
                rx.el.p(
                    EmployeesState.employee_detail["notes"],
                    class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-3 leading-relaxed",
                ),
                _skills_block(),
                _availability_block(),
                _assignment_block(),
                class_name="w-full",
            ),
            rx.el.div(
                rx.icon("users-round", class_name="h-7 w-7 text-[#d8fa5e]"),
                rx.el.p(
                    "Sélectionnez un salarié dans le registre ou créez une première fiche.",
                    class_name="mt-4 text-[13px] leading-relaxed text-[#C9C5B4]/70 text-center max-w-sm",
                ),
                class_name="flex flex-col items-center justify-center py-24",
            ),
        ),
        class_name="flex-1 min-w-0 w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )

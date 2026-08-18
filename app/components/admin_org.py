import reflex as rx

from app.admin_operations import (
    OrgLevel,
    OrgNode,
    ResponsibilityRow,
    TaskRow,
    TeamMemberRow,
)
from app.components.admin_shared import (
    CARD,
    avatar,
    chip,
    section_title,
    stat_line,
    tone_badge,
)
from app.states.administration_state import AdministrationState


def _node_card(node: OrgNode, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            avatar(node["seed"], node["initials"]),
            rx.el.div(
                rx.el.p(
                    node["name"],
                    class_name="text-sm font-semibold text-emerald-50 truncate text-left",
                ),
                rx.el.p(
                    node["function_label"],
                    class_name="text-[11px] font-medium text-emerald-100/50 truncate text-left",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.icon(node["role_icon"], class_name="h-4 w-4 text-lime-300"),
            class_name="flex items-center gap-3 w-full min-w-0",
        ),
        rx.el.div(
            rx.el.span(
                node["role_label"],
                class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
            ),
            chip(node["team_label"]),
            tone_badge(node["status"], node["status_tone"]),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        rx.el.div(
            rx.icon("users", class_name="h-3 w-3 text-emerald-100/50"),
            rx.el.span(
                node["reports"].to_string() + " rattaché(s)",
                class_name="text-[10px] font-medium text-emerald-100/45",
            ),
            rx.icon("map", class_name="h-3 w-3 text-emerald-100/50 ml-2"),
            rx.el.span(
                node["parcels"].to_string() + " parcelle(s)",
                class_name="text-[10px] font-medium text-emerald-100/45",
            ),
            rx.el.span(
                node["sector"],
                class_name="text-[10px] font-semibold text-lime-200 ml-auto truncate",
            ),
            class_name="flex items-center gap-1.5 w-full mt-2 min-w-0",
        ),
        on_click=AdministrationState.select_org_node(node["id"]),
        key=key,
        class_name=rx.cond(
            AdministrationState.org_selected_id == node["id"],
            "w-[17rem] shrink-0 rounded-2xl border border-lime-300/45 bg-lime-300/[0.08] p-4 text-left ring-2 ring-lime-300/40 transition-all",
            "w-[17rem] shrink-0 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left hover:border-lime-300/30 transition-all",
        ),
    )


def _level_row(level: OrgLevel) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Niveau " + (level["depth"] + 1).to_string(),
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.2em] text-emerald-100/50 w-fit",
            ),
            rx.el.span(
                level["label"],
                class_name="text-[11px] font-semibold uppercase tracking-[0.22em] text-lime-300/80",
            ),
            rx.el.span(
                level["count"].to_string() + " personne(s)",
                class_name="text-[10px] font-medium text-emerald-100/40 ml-auto",
            ),
            class_name="flex items-center gap-2 w-full",
        ),
        rx.el.div(
            rx.foreach(
                level["nodes"],
                lambda node: _node_card(node, key=node["id"].to_string()),
            ),
            class_name="flex flex-nowrap items-stretch gap-3 mt-3 overflow-x-auto pb-2",
        ),
        rx.el.div(
            class_name="mt-3 h-px w-full bg-gradient-to-r from-lime-300/30 via-white/10 to-transparent",
        ),
        class_name="w-full",
    )


def _node_detail() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            avatar(
                AdministrationState.org_node["seed"],
                AdministrationState.org_node["initials"],
            ),
            rx.el.div(
                rx.el.span(
                    AdministrationState.org_node["matricule"],
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h3(
                    AdministrationState.org_node["name"],
                    class_name="font-['Instrument_Serif'] text-2xl text-emerald-50",
                ),
                class_name="min-w-0 flex-1",
            ),
            tone_badge(
                AdministrationState.org_node["status"],
                AdministrationState.org_node["status_tone"],
            ),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        stat_line(
            "briefcase",
            "Fonction",
            AdministrationState.org_node["function_label"],
        ),
        stat_line(
            "shield-check", "Rôle", AdministrationState.org_node["role_label"]
        ),
        stat_line(
            "user-check",
            "Responsable",
            AdministrationState.org_node["manager_label"],
        ),
        stat_line(
            "users", "Équipe", AdministrationState.org_node["team_label"]
        ),
        stat_line(
            "map",
            "Parcelles affectées",
            AdministrationState.org_node["parcels"].to_string(),
        ),
        rx.el.button(
            rx.icon("user-round", class_name="h-4 w-4 text-[#04140d]"),
            rx.el.span("Ouvrir son espace", class_name="text-[#04140d]"),
            on_click=AdministrationState.open_personal_space(
                AdministrationState.org_node["id"]
            ),
            class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit mt-4",
        ),
        class_name="w-full xl:w-[22rem] shrink-0 rounded-2xl border border-white/10 bg-white/[0.03] p-5",
    )


def admin_org_chart() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            section_title(
                "Organisation",
                "Organigramme agricole",
                "Propriétaire → direction → responsables → chefs d'équipe → terrain. Cliquez sur une personne pour ouvrir sa fiche.",
            ),
            rx.el.span(
                AdministrationState.org_levels.length().to_string()
                + " niveau(x)",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-bold text-emerald-100/70 w-fit",
            ),
            class_name="flex flex-col sm:flex-row sm:items-end justify-between gap-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.foreach(AdministrationState.org_levels, _level_row),
                class_name="flex flex-col gap-5 flex-1 min-w-0 w-full",
            ),
            _node_detail(),
            class_name="flex flex-col xl:flex-row gap-5 w-full mt-5",
        ),
        class_name=f"w-full {CARD}",
    )


def task_card(task: TaskRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(task["icon"], class_name="h-4 w-4 text-lime-300"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-lime-300/25 bg-lime-300/[0.08]",
            ),
            rx.el.div(
                rx.el.p(
                    task["title"],
                    class_name="text-sm font-semibold text-emerald-50 truncate",
                ),
                rx.el.p(
                    task["type_label"] + " · " + task["parcel"],
                    class_name="text-[11px] font-medium text-emerald-100/50 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            tone_badge(task["status_label"], task["tone"]),
            class_name="flex items-center gap-3 w-full min-w-0",
        ),
        rx.el.div(
            chip(task["crop"]),
            chip(task["when"]),
            chip(task["operator"]),
            rx.cond(
                task["validated"],
                rx.el.span(
                    "VALIDÉE",
                    class_name="rounded-full border border-lime-300/40 bg-lime-300/10 px-1.5 py-0.5 text-[9px] font-bold text-lime-200 w-fit",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        rx.el.div(
            rx.cond(
                task["can_close"],
                rx.el.button(
                    rx.icon("flag", class_name="h-3.5 w-3.5"),
                    rx.el.span("Clôturer", class_name="text-[11px]"),
                    on_click=AdministrationState.complete_intervention(
                        task["id"]
                    ),
                    class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 font-semibold text-emerald-100/70 hover:border-lime-300/40 hover:text-emerald-50 transition-colors w-fit",
                ),
                rx.fragment(),
            ),
            rx.cond(
                task["can_validate"],
                rx.el.button(
                    rx.icon("check-check", class_name="h-3.5 w-3.5"),
                    rx.el.span("Valider", class_name="text-[11px]"),
                    on_click=AdministrationState.validate_intervention(
                        task["id"]
                    ),
                    class_name="flex items-center gap-1.5 rounded-full border border-lime-300/40 bg-lime-300/10 px-2.5 py-1 font-semibold text-lime-200 hover:bg-lime-300/20 transition-colors w-fit",
                ),
                rx.fragment(),
            ),
            rx.el.span(
                f"{task['area']:.1f} ha",
                class_name="text-[10px] font-semibold text-emerald-100/45 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 border-t border-white/[0.06] pt-3 mt-3",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:border-lime-300/25 transition-colors",
    )


def _member_card(member: TeamMemberRow) -> rx.Component:
    return rx.el.div(
        avatar(member["seed"], member["initials"]),
        rx.el.div(
            rx.el.p(
                member["name"],
                class_name="text-sm font-semibold text-emerald-50 truncate",
            ),
            rx.el.p(
                member["role_in_team"] + " · " + member["role_label"],
                class_name="text-[10px] font-medium text-emerald-100/45 truncate",
            ),
            class_name="min-w-0 flex-1",
        ),
        class_name="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-3 w-full min-w-0",
    )


def _responsibility_card(item: ResponsibilityRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(item["icon"], class_name="h-4 w-4 text-amber-300"),
            rx.el.p(
                item["label"],
                class_name="text-sm font-semibold text-emerald-50 truncate",
            ),
            chip(item["kind"]),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.p(
            item["detail"],
            class_name="text-[11px] font-medium text-emerald-100/55 mt-1",
        ),
        class_name="rounded-2xl border border-white/10 bg-white/[0.03] p-4 w-full",
    )


def _personal_tile(
    label: str, value: rx.Var | str, caption: str, icon: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                label,
                class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/50",
            ),
            rx.icon(icon, class_name="h-4 w-4 text-lime-300"),
            class_name="flex items-start justify-between gap-2",
        ),
        rx.el.span(
            value,
            class_name="font-['Instrument_Serif'] text-3xl leading-none text-emerald-50 mt-3 block",
        ),
        rx.el.p(
            caption,
            class_name="text-[10px] font-medium text-emerald-100/40 mt-2",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.04] p-4",
    )


def _personal_header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            avatar(
                AdministrationState.personal["seed"],
                AdministrationState.personal["initials"],
            ),
            rx.el.div(
                rx.el.span(
                    AdministrationState.personal["matricule"]
                    + " · "
                    + AdministrationState.personal["farm_key"],
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                ),
                rx.el.h2(
                    AdministrationState.personal["name"],
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    AdministrationState.personal["function_label"]
                    + " · "
                    + AdministrationState.personal["role_label"]
                    + " · "
                    + AdministrationState.personal["team_label"],
                    class_name="text-sm font-medium text-emerald-100/60 mt-1",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                rx.icon("shield-check", class_name="h-3.5 w-3.5 text-lime-300"),
                rx.el.span(
                    AdministrationState.personal["scope_label"],
                    class_name="text-[11px] font-semibold text-emerald-50/85",
                ),
                class_name="flex items-center gap-2 rounded-full border border-lime-300/30 bg-lime-300/[0.07] px-3 py-1.5 w-fit",
            ),
            class_name="flex flex-col lg:flex-row lg:items-center gap-4 w-full min-w-0",
        ),
        rx.el.div(
            _personal_tile(
                "Mes tâches",
                AdministrationState.personal["tasks_open"],
                "chantiers ouverts sur mon périmètre",
                "clipboard-list",
            ),
            _personal_tile(
                "À valider",
                AdministrationState.personal["validations_pending"],
                "interventions terminées en attente",
                "check-check",
            ),
            _personal_tile(
                "Mes parcelles",
                AdministrationState.personal["parcels"],
                AdministrationState.personal["crops"].to_string()
                + " culture(s) suivie(s)",
                "map",
            ),
            _personal_tile(
                "Mon organisation",
                AdministrationState.personal["teams"],
                AdministrationState.personal["activities"].to_string()
                + " activité(s) autorisée(s)",
                "users",
            ),
            class_name="grid grid-cols-2 lg:grid-cols-4 gap-3 w-full mt-5",
        ),
        class_name="w-full",
    )


def admin_personal_space() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            section_title(
                "Mon espace",
                "Tableau de bord personnel",
                "Tâches, validations, parcelles, équipe et responsabilités du profil sélectionné.",
            ),
            rx.el.button(
                rx.icon("refresh-cw", class_name="h-4 w-4"),
                rx.el.span("Recharger l'espace"),
                on_click=AdministrationState.reload_personal_space,
                class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
            ),
            class_name="flex flex-col sm:flex-row sm:items-end justify-between gap-3",
        ),
        rx.el.div(_personal_header(), class_name="mt-5"),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "Mes tâches & interventions",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/40",
                ),
                rx.cond(
                    AdministrationState.personal_tasks.length() > 0,
                    rx.el.div(
                        rx.foreach(
                            AdministrationState.personal_tasks,
                            lambda t: task_card(t, key=t["id"].to_string()),
                        ),
                        class_name="flex flex-col gap-3 mt-3 max-h-[38rem] overflow-y-auto pr-1",
                    ),
                    rx.el.p(
                        "Aucune tâche sur ce périmètre.",
                        class_name="text-sm font-medium text-emerald-100/50 mt-3",
                    ),
                ),
                class_name="flex-1 min-w-0",
            ),
            rx.el.div(
                rx.el.p(
                    "Mes responsabilités",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/40",
                ),
                rx.cond(
                    AdministrationState.personal_responsibilities.length() > 0,
                    rx.el.div(
                        rx.foreach(
                            AdministrationState.personal_responsibilities,
                            _responsibility_card,
                        ),
                        class_name="flex flex-col gap-3 mt-3",
                    ),
                    rx.el.p(
                        "Aucune responsabilité déclarée.",
                        class_name="text-sm font-medium text-emerald-100/50 mt-3",
                    ),
                ),
                rx.el.p(
                    "Mon équipe",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/40 mt-6",
                ),
                rx.cond(
                    AdministrationState.personal_team.length() > 0,
                    rx.el.div(
                        rx.foreach(
                            AdministrationState.personal_team, _member_card
                        ),
                        class_name="flex flex-col gap-2 mt-3",
                    ),
                    rx.el.p(
                        "Ce profil n'est rattaché à aucune équipe.",
                        class_name="text-sm font-medium text-emerald-100/50 mt-3",
                    ),
                ),
                class_name="w-full xl:w-[26rem] shrink-0",
            ),
            class_name="flex flex-col xl:flex-row gap-6 w-full mt-6 border-t border-white/10 pt-6",
        ),
        class_name=f"w-full {CARD}",
    )

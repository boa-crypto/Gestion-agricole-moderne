import reflex as rx

from app.admin_operations import AssignmentDetailRow, DelegationRow
from app.components.admin_org import task_card
from app.components.admin_shared import (
    CARD,
    SELECT,
    avatar,
    chip,
    section_title,
    tone_badge,
)
from app.states.administration_state import (
    SCOPE_CHOICES,
    AdministrationState,
)

_INPUT = "w-full rounded-xl border border-white/10 bg-[#04140d] px-3 py-2.5 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors"
_LABEL = "block text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45 mb-1.5"


# ---------------------------------------------------------------------------
# Workflows de validation
# ---------------------------------------------------------------------------


def _step_pill(label: str) -> rx.Component:
    return rx.el.div(
        rx.icon("circle-dot", class_name="h-3.5 w-3.5 text-lime-300/80"),
        rx.el.span(
            label,
            class_name="text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-100/55",
        ),
        class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 w-fit",
    )


def admin_workflows() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            section_title(
                "Workflow agricole",
                "Validations en attente",
                "Planifiée → en cours → terminée → à valider → validée. Chaque décision est journalisée.",
            ),
            rx.el.div(
                rx.el.span(
                    AdministrationState.pending_validations.length().to_string()
                    + " à valider",
                    class_name="rounded-full border border-amber-300/30 bg-amber-300/10 px-3 py-1.5 text-[11px] font-bold text-amber-200 w-fit",
                ),
                rx.el.button(
                    rx.icon("refresh-cw", class_name="h-4 w-4"),
                    rx.el.span("Actualiser"),
                    on_click=AdministrationState.reload_workflows,
                    class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4",
        ),
        rx.el.div(
            *[
                _step_pill(label)
                for label in (
                    "Planifiée",
                    "En cours",
                    "Terminée",
                    "À valider",
                    "Validée",
                )
            ],
            class_name="flex flex-wrap items-center gap-2 mt-5",
        ),
        rx.cond(
            AdministrationState.pending_validations.length() > 0,
            rx.el.div(
                rx.foreach(
                    AdministrationState.pending_validations,
                    lambda t: task_card(t, key=t["id"].to_string()),
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 mt-5",
            ),
            rx.el.div(
                rx.icon("circle-check", class_name="h-6 w-6 text-lime-300"),
                rx.el.p(
                    "Aucune intervention n'attend de validation.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-2 text-center",
                ),
                class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-12 mt-5",
            ),
        ),
        rx.el.div(
            rx.el.p(
                "Chantiers en cours sur l'exploitation",
                class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/40",
            ),
            rx.cond(
                AdministrationState.open_tasks.length() > 0,
                rx.el.div(
                    rx.foreach(
                        AdministrationState.open_tasks,
                        lambda t: task_card(t, key=t["id"].to_string()),
                    ),
                    class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 mt-3",
                ),
                rx.el.p(
                    "Aucun chantier ouvert.",
                    class_name="text-sm font-medium text-emerald-100/50 mt-3",
                ),
            ),
            class_name="mt-6 border-t border-white/10 pt-6",
        ),
        class_name=f"w-full {CARD}",
    )


# ---------------------------------------------------------------------------
# Délégations / permissions temporaires
# ---------------------------------------------------------------------------


def _select(
    name: str,
    icon: str,
    options: rx.Var,
    first: rx.Component,
) -> rx.Component:
    return rx.el.div(
        rx.icon(
            icon,
            class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300/80 pointer-events-none",
        ),
        rx.el.select(
            first,
            rx.foreach(
                options,
                lambda opt: rx.el.option(opt["label"], value=opt["value"]),
            ),
            name=name,
            key=f"deleg-{name}-{AdministrationState.form_key}",
            class_name=SELECT,
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
        ),
        class_name="relative w-full",
    )


def _delegation_form() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            rx.el.div(
                rx.el.label("Délégant", class_name=_LABEL),
                _select(
                    "delegator_id",
                    "user-check",
                    AdministrationState.people_options,
                    rx.el.option(
                        "Choisir le délégant", value="", disabled=True
                    ),
                ),
                class_name="w-full min-w-0",
            ),
            rx.el.div(
                rx.el.label("Délégataire", class_name=_LABEL),
                _select(
                    "delegate_id",
                    "user-plus",
                    AdministrationState.people_options,
                    rx.el.option(
                        "Choisir le délégataire", value="", disabled=True
                    ),
                ),
                class_name="w-full min-w-0",
            ),
            rx.el.div(
                rx.el.label("Rôle délégué", class_name=_LABEL),
                _select(
                    "role_id",
                    "shield-check",
                    AdministrationState.delegable_roles,
                    rx.el.option("Choisir le rôle", value="", disabled=True),
                ),
                class_name="w-full min-w-0",
            ),
            rx.el.div(
                rx.el.label("Périmètre", class_name=_LABEL),
                rx.el.div(
                    rx.icon(
                        "map",
                        class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300/80 pointer-events-none",
                    ),
                    rx.el.select(
                        *[
                            rx.el.option(label, value=value)
                            for value, label in SCOPE_CHOICES
                        ],
                        name="scope_kind",
                        default_value="EXPLOITATION",
                        key=f"deleg-scope-{AdministrationState.form_key}",
                        class_name=SELECT,
                    ),
                    rx.icon(
                        "chevron-down",
                        class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                    ),
                    class_name="relative w-full",
                ),
                class_name="w-full min-w-0",
            ),
            rx.el.div(
                rx.el.label("Équipe concernée", class_name=_LABEL),
                _select(
                    "team_id",
                    "users",
                    AdministrationState.delegation_teams,
                    rx.el.option("Sans équipe précise", value=""),
                ),
                class_name="w-full min-w-0",
            ),
            rx.el.div(
                rx.el.label("Début", class_name=_LABEL),
                rx.el.input(
                    type="date",
                    name="start_date",
                    key=f"deleg-start-{AdministrationState.form_key}",
                    class_name=_INPUT,
                ),
                class_name="w-full min-w-0",
            ),
            rx.el.div(
                rx.el.label("Fin", class_name=_LABEL),
                rx.el.input(
                    type="date",
                    name="end_date",
                    key=f"deleg-end-{AdministrationState.form_key}",
                    class_name=_INPUT,
                ),
                class_name="w-full min-w-0",
            ),
            rx.el.div(
                rx.el.label("Motif", class_name=_LABEL),
                rx.el.input(
                    name="reason",
                    placeholder="Absence du responsable irrigation…",
                    key=f"deleg-reason-{AdministrationState.form_key}",
                    class_name=_INPUT,
                ),
                class_name="w-full min-w-0 md:col-span-2",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4",
        ),
        rx.cond(
            AdministrationState.delegation_error != "",
            rx.el.p(
                AdministrationState.delegation_error,
                class_name="text-xs font-semibold text-red-300 mt-3",
            ),
            rx.fragment(),
        ),
        rx.el.button(
            rx.icon("hourglass", class_name="h-4 w-4 text-[#04140d]"),
            rx.el.span(
                "Accorder la permission temporaire",
                class_name="text-[#04140d]",
            ),
            type="submit",
            class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-5 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit mt-4",
        ),
        on_submit=AdministrationState.submit_delegation,
        reset_on_submit=True,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-5 mt-5",
    )


def _delegation_card(item: DelegationRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            avatar(item["delegate_seed"], item["delegate_label"]),
            rx.el.div(
                rx.el.p(
                    item["delegate_label"],
                    class_name="text-sm font-semibold text-emerald-50 truncate",
                ),
                rx.el.p(
                    "Délégué par " + item["delegator_label"],
                    class_name="text-[11px] font-medium text-emerald-100/50 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            tone_badge(item["status_label"], item["tone"]),
            class_name="flex items-center gap-3 w-full min-w-0",
        ),
        rx.el.div(
            rx.el.span(
                item["role_label"],
                class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
            ),
            rx.el.span(
                rx.icon(item["scope_icon"], class_name="h-3 w-3"),
                rx.el.span(item["scope_label"]),
                class_name="flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            chip(item["target"]),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        rx.el.p(
            item["reason"],
            class_name="text-[11px] font-medium text-emerald-100/60 mt-3",
        ),
        rx.el.div(
            rx.icon("calendar-days", class_name="h-3.5 w-3.5 text-lime-300/80"),
            rx.el.span(
                item["start_label"] + " → " + item["end_label"],
                class_name="text-[10px] font-semibold text-emerald-100/55",
            ),
            rx.cond(
                item["is_open"],
                rx.el.span(
                    item["days_left"].to_string() + " j restant(s)",
                    class_name="text-[10px] font-bold text-amber-200",
                ),
                rx.fragment(),
            ),
            rx.cond(
                item["is_open"],
                rx.el.button(
                    rx.icon("circle-slash", class_name="h-3.5 w-3.5"),
                    rx.el.span("Révoquer", class_name="text-[11px]"),
                    on_click=AdministrationState.revoke_temporary_permission(
                        item["id"]
                    ),
                    class_name="flex items-center gap-1.5 rounded-full border border-red-400/30 bg-red-500/10 px-2.5 py-1 font-semibold text-red-300 hover:bg-red-500/20 transition-colors w-fit ml-auto",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-2 border-t border-white/[0.06] pt-3 mt-3",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:border-lime-300/25 transition-colors",
    )


def admin_delegations() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            section_title(
                "Permissions temporaires",
                "Délégations",
                "Confier un rôle pendant une absence, avec date de fin, motif et autorisation tracée.",
            ),
            rx.el.button(
                rx.icon("timer-off", class_name="h-4 w-4"),
                rx.el.span("Expirer les délégations échues"),
                on_click=AdministrationState.expire_temporary_permissions,
                class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
            ),
            class_name="flex flex-col sm:flex-row sm:items-end justify-between gap-3",
        ),
        _delegation_form(),
        rx.cond(
            AdministrationState.delegations.length() > 0,
            rx.el.div(
                rx.foreach(
                    AdministrationState.delegations,
                    lambda d: _delegation_card(d, key=d["id"].to_string()),
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 mt-5",
            ),
            rx.el.p(
                "Aucune permission temporaire enregistrée.",
                class_name="text-sm font-medium text-emerald-100/50 mt-5",
            ),
        ),
        class_name=f"w-full {CARD}",
    )


# ---------------------------------------------------------------------------
# Affectations
# ---------------------------------------------------------------------------


def _assignment_row(item: AssignmentDetailRow) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                avatar(item["seed"], item["initials"]),
                rx.el.div(
                    rx.el.p(
                        item["user_label"],
                        class_name="text-sm font-semibold text-emerald-50 truncate",
                    ),
                    rx.el.p(
                        item["role_label"],
                        class_name="text-[10px] font-medium text-emerald-100/45 truncate",
                    ),
                    class_name="min-w-0",
                ),
                class_name="flex items-center gap-3 min-w-0",
            ),
            class_name="px-4 py-3 align-middle",
        ),
        rx.el.td(
            rx.el.p(
                item["parcel"],
                class_name="text-sm font-medium text-emerald-50/85",
            ),
            rx.el.p(
                item["crop"],
                class_name="text-[10px] font-medium text-emerald-100/45",
            ),
            class_name="px-4 py-3 align-middle",
        ),
        rx.el.td(
            rx.el.div(
                chip(item["team"]),
                chip(item["activity"]),
                class_name="flex flex-wrap items-center gap-1.5",
            ),
            class_name="px-4 py-3 align-middle",
        ),
        rx.el.td(
            rx.el.p(
                item["sector"] + " · " + item["season"],
                class_name="text-[11px] font-medium text-emerald-100/55 whitespace-nowrap",
            ),
            rx.el.p(
                item["period"],
                class_name="text-[10px] font-medium text-emerald-100/35 whitespace-nowrap",
            ),
            class_name="px-4 py-3 align-middle",
        ),
        rx.el.td(
            rx.cond(
                item["responsible"],
                rx.el.span(
                    "RESPONSABLE",
                    class_name="rounded-full border border-lime-300/40 bg-lime-300/10 px-2 py-0.5 text-[9px] font-bold text-lime-200 w-fit",
                ),
                rx.el.span(
                    "Intervenant",
                    class_name="text-[10px] font-semibold text-emerald-100/40",
                ),
            ),
            class_name="px-4 py-3 align-middle text-right",
        ),
        class_name="border-t border-white/[0.06] hover:bg-white/[0.03] transition-colors",
    )


def _head(label: str, icon: str, align: str = "left") -> rx.Component:
    return rx.el.th(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 mr-2"),
            rx.el.span(label),
            class_name="flex items-center",
        ),
        class_name=f"px-4 py-3 text-{align} text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
    )


def admin_assignments() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            section_title(
                "Affectations",
                "Parcelles, cultures, équipes & activités",
                "Exploitation → secteur → parcelle → culture → équipe : qui est responsable de quoi.",
            ),
            rx.el.div(
                rx.el.span(
                    AdministrationState.assignments.length().to_string()
                    + " affectation(s)",
                    class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-bold text-emerald-100/70 w-fit",
                ),
                rx.el.button(
                    rx.icon("download", class_name="h-4 w-4 text-[#04140d]"),
                    rx.el.span("Exporter (CSV)", class_name="text-[#04140d]"),
                    on_click=AdministrationState.export_assignments,
                    class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col sm:flex-row sm:items-end justify-between gap-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "users",
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300/80 pointer-events-none",
                ),
                rx.el.select(
                    rx.el.option("Toutes les équipes", value="TOUTES"),
                    rx.foreach(
                        AdministrationState.assignment_team_options,
                        lambda opt: rx.el.option(
                            opt["label"], value=opt["value"]
                        ),
                    ),
                    name="assignment_team",
                    default_value=AdministrationState.assignment_team,
                    key=f"assign-team-{AdministrationState.form_key}",
                    on_change=AdministrationState.set_assignment_team,
                    class_name=SELECT,
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                ),
                class_name="relative w-full sm:w-60",
            ),
            rx.el.div(
                rx.icon(
                    "activity",
                    class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300/80 pointer-events-none",
                ),
                rx.el.select(
                    rx.el.option("Toutes les activités", value="TOUTES"),
                    rx.foreach(
                        AdministrationState.assignment_activity_options,
                        lambda opt: rx.el.option(
                            opt["label"], value=opt["value"]
                        ),
                    ),
                    name="assignment_activity",
                    default_value=AdministrationState.assignment_activity,
                    key=f"assign-activity-{AdministrationState.form_key}",
                    on_change=AdministrationState.set_assignment_activity,
                    class_name=SELECT,
                ),
                rx.icon(
                    "chevron-down",
                    class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
                ),
                class_name="relative w-full sm:w-60",
            ),
            rx.el.button(
                rx.icon("rotate-ccw", class_name="h-4 w-4"),
                rx.el.span("Réinitialiser"),
                on_click=AdministrationState.reset_assignment_filters,
                class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
            ),
            class_name="flex flex-col sm:flex-row sm:items-center gap-3 w-full mt-5",
        ),
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        _head("Collaborateur", "user"),
                        _head("Parcelle & culture", "map"),
                        _head("Équipe & activité", "users"),
                        _head("Secteur & période", "calendar-days"),
                        rx.el.th(
                            "Rôle",
                            class_name="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
                        ),
                        class_name="bg-white/[0.04]",
                    ),
                ),
                rx.el.tbody(
                    rx.foreach(AdministrationState.assignments, _assignment_row)
                ),
                class_name="table-auto w-full min-w-[52rem]",
            ),
            class_name="mt-5 w-full overflow-x-auto overflow-hidden rounded-2xl border border-white/10 bg-white/[0.02]",
        ),
        class_name=f"w-full {CARD}",
    )

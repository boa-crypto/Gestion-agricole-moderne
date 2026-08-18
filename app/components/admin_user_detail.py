import reflex as rx

from app.admin_users import (
    ActivityRow,
    AssignmentRow,
    PermGroup,
    RoleRow,
    ScopeRow,
)
from app.components.admin_shared import (
    CARD,
    avatar,
    chip,
    stat_line,
    tone_badge,
)
from app.states.administration_state import (
    STATUS_BUTTONS,
    TABS,
    AdministrationState,
)


def _tab(key: str, label: str, icon: str) -> rx.Component:
    return rx.el.button(
        rx.icon(
            icon,
            class_name=rx.cond(
                AdministrationState.tab == key,
                "h-3.5 w-3.5 text-lime-300",
                "h-3.5 w-3.5 text-emerald-100/45",
            ),
        ),
        rx.el.span(label),
        on_click=AdministrationState.set_tab(key),
        class_name=rx.cond(
            AdministrationState.tab == key,
            "flex items-center gap-1.5 rounded-xl border border-lime-300/40 bg-lime-300/10 px-3 py-2 text-xs font-semibold text-emerald-50 transition-colors w-fit",
            "flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-emerald-100/60 hover:border-lime-300/25 transition-colors w-fit",
        ),
    )


def _status_button(action: str, label: str, icon: str) -> rx.Component:
    return rx.el.button(
        rx.icon(icon, class_name="h-3.5 w-3.5"),
        rx.el.span(label),
        on_click=AdministrationState.apply_status(action),
        disabled=~AdministrationState.has_selection,
        class_name="flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-emerald-100/70 hover:border-lime-300/40 hover:text-emerald-50 disabled:opacity-40 transition-colors w-fit",
    )


def _header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            avatar(
                AdministrationState.detail["seed"],
                AdministrationState.detail["initials"],
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        AdministrationState.detail["matricule"],
                        class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                    ),
                    tone_badge(
                        AdministrationState.detail["status_label"],
                        AdministrationState.detail["status_tone"],
                    ),
                    class_name="flex items-center gap-2 flex-wrap",
                ),
                rx.el.h2(
                    AdministrationState.detail["name"],
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    AdministrationState.detail["function_label"]
                    + " · "
                    + AdministrationState.detail["role_label"],
                    class_name="text-sm font-medium text-emerald-100/60 mt-1",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-4 w-full min-w-0",
        ),
        rx.el.div(
            *[
                _status_button(action, label, icon)
                for action, label, icon in STATUS_BUTTONS
            ],
            class_name="flex flex-wrap items-center gap-2 mt-4",
        ),
        rx.el.div(
            *[_tab(key, label, icon) for key, label, icon in TABS],
            class_name="flex flex-wrap items-center gap-2 mt-4 border-t border-white/10 pt-4",
        ),
        class_name="w-full",
    )


def _profil() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            stat_line("mail", "E-mail", AdministrationState.detail["email"]),
            stat_line(
                "phone", "Téléphone", AdministrationState.detail["phone"]
            ),
            stat_line(
                "map-pin", "Adresse", AdministrationState.detail["address"]
            ),
            stat_line(
                "calendar-days",
                "Embauche",
                AdministrationState.detail["hired_on"],
            ),
            class_name="w-full",
        ),
        rx.el.div(
            stat_line(
                "shield-check",
                "MFA",
                AdministrationState.detail["mfa_label"],
            ),
            stat_line(
                "clock",
                "Dernière connexion",
                AdministrationState.detail["last_login"],
            ),
            stat_line(
                "key-round",
                "Permissions effectives",
                AdministrationState.detail["permission_count"].to_string(),
            ),
            stat_line(
                "hourglass",
                "Délégations reçues",
                AdministrationState.detail["delegation_count"].to_string(),
            ),
            class_name="w-full",
        ),
        rx.el.div(
            rx.el.p(
                "Notes RH",
                class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/40",
            ),
            rx.el.p(
                AdministrationState.detail["notes"],
                class_name="text-sm font-medium text-emerald-100/70 mt-2",
            ),
            class_name="rounded-2xl border border-white/10 bg-white/[0.03] p-4 md:col-span-2",
        ),
        class_name="grid grid-cols-1 md:grid-cols-2 gap-5 mt-5",
    )


def _organisation() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            stat_line(
                "building-2",
                "Exploitation",
                AdministrationState.detail["farm_key"],
            ),
            stat_line(
                "compass", "Secteur", AdministrationState.detail["sector"]
            ),
            stat_line(
                "users", "Équipe", AdministrationState.detail["team_label"]
            ),
            stat_line(
                "user-check",
                "Responsable",
                AdministrationState.detail["manager_label"],
            ),
            class_name="w-full",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("briefcase", class_name="h-4 w-4 text-lime-300"),
                rx.el.span(
                    AdministrationState.detail["family_label"],
                    class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-lime-300/80",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.p(
                AdministrationState.detail["function_mission"],
                class_name="text-sm font-medium text-emerald-100/75 mt-2",
            ),
            rx.el.p(
                AdministrationState.detail["function_responsibilities"],
                class_name="text-[11px] font-medium text-emerald-100/45 mt-2",
            ),
            class_name="rounded-2xl border border-white/10 bg-white/[0.03] p-4",
        ),
        class_name="grid grid-cols-1 md:grid-cols-2 gap-5 mt-5",
    )


def _role_card(role: RoleRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(role["icon"], class_name="h-4 w-4 text-lime-300"),
            rx.el.p(
                role["label"],
                class_name="text-sm font-semibold text-emerald-50 truncate",
            ),
            rx.cond(
                role["is_primary"],
                rx.el.span(
                    "PRINCIPAL",
                    class_name="rounded-full border border-lime-300/40 bg-lime-300/10 px-1.5 py-0.5 text-[9px] font-bold text-lime-200 w-fit ml-auto",
                ),
                rx.fragment(),
            ),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.p(
            "Attribué par " + role["granted_by"] + " · " + role["granted_on"],
            class_name="text-[11px] font-medium text-emerald-100/45 mt-1",
        ),
        class_name="rounded-2xl border border-white/10 bg-white/[0.03] p-4 w-full",
    )


def _perm_group(group: PermGroup) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(group["icon"], class_name="h-4 w-4 text-lime-300"),
            rx.el.p(
                group["label"],
                class_name="text-sm font-semibold text-emerald-50 truncate",
            ),
            rx.cond(
                group["sensitive"],
                rx.el.span(
                    "SENSIBLE",
                    class_name="rounded-full border border-amber-300/40 bg-amber-300/10 px-1.5 py-0.5 text-[9px] font-bold text-amber-200 w-fit",
                ),
                rx.fragment(),
            ),
            rx.el.span(
                group["count"].to_string() + " action(s)",
                class_name="text-[10px] font-semibold text-emerald-100/50 ml-auto",
            ),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.div(
            rx.foreach(group["actions"], chip),
            class_name="flex flex-wrap items-center gap-1.5 mt-2",
        ),
        class_name="rounded-2xl border border-white/10 bg-white/[0.03] p-4 w-full",
    )


def _roles_tab() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(
                "Rôles attribués",
                class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/40",
            ),
            rx.foreach(AdministrationState.detail_roles, _role_card),
            class_name="flex flex-col gap-3",
        ),
        rx.el.div(
            rx.el.p(
                "Permissions effectives par module",
                class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/40",
            ),
            rx.foreach(AdministrationState.detail_permissions, _perm_group),
            class_name="flex flex-col gap-3 max-h-[32rem] overflow-y-auto pr-1",
        ),
        class_name="grid grid-cols-1 lg:grid-cols-2 gap-5 mt-5",
    )


def _scope_card(scope: ScopeRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(scope["icon"], class_name="h-4 w-4 text-lime-300"),
            rx.el.p(
                scope["label"],
                class_name="text-sm font-semibold text-emerald-50 truncate",
            ),
            rx.cond(
                scope["readonly"],
                rx.el.span(
                    "LECTURE SEULE",
                    class_name="rounded-full border border-sky-300/40 bg-sky-300/10 px-1.5 py-0.5 text-[9px] font-bold text-sky-200 w-fit ml-auto",
                ),
                rx.fragment(),
            ),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.p(
            scope["detail"],
            class_name="text-[11px] font-medium text-emerald-100/50 mt-1",
        ),
        class_name="rounded-2xl border border-white/10 bg-white/[0.03] p-4 w-full",
    )


def _assignment_card(item: AssignmentRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("map", class_name="h-4 w-4 text-lime-300"),
            rx.el.p(
                item["parcel"],
                class_name="text-sm font-semibold text-emerald-50 truncate",
            ),
            rx.cond(
                item["responsible"],
                rx.el.span(
                    "RESPONSABLE",
                    class_name="rounded-full border border-lime-300/40 bg-lime-300/10 px-1.5 py-0.5 text-[9px] font-bold text-lime-200 w-fit ml-auto",
                ),
                rx.fragment(),
            ),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.div(
            chip(item["team"]),
            chip(item["activity"]),
            chip(item["season"]),
            class_name="flex flex-wrap items-center gap-1.5 mt-2",
        ),
        class_name="rounded-2xl border border-white/10 bg-white/[0.03] p-4 w-full",
    )


def _scope_tab() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("shield-check", class_name="h-4 w-4 text-lime-300"),
                rx.el.p(
                    AdministrationState.detail["scope_label"],
                    class_name="text-sm font-semibold text-emerald-50",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.div(
                chip(
                    AdministrationState.detail["parcel_count"].to_string()
                    + " parcelle(s)"
                ),
                chip(
                    AdministrationState.detail["team_count"].to_string()
                    + " équipe(s)"
                ),
                rx.cond(
                    AdministrationState.detail["has_full_scope"],
                    rx.el.span(
                        "PÉRIMÈTRE GLOBAL",
                        class_name="rounded-full border border-amber-300/40 bg-amber-300/10 px-2 py-0.5 text-[9px] font-bold text-amber-200 w-fit",
                    ),
                    rx.fragment(),
                ),
                class_name="flex flex-wrap items-center gap-2 mt-2",
            ),
            class_name="rounded-2xl border border-lime-300/25 bg-lime-300/[0.05] p-4 w-full",
        ),
        rx.el.div(
            rx.el.p(
                "Périmètres déclarés",
                class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/40",
            ),
            rx.foreach(AdministrationState.detail_scopes, _scope_card),
            class_name="flex flex-col gap-3 mt-4",
        ),
        rx.el.div(
            rx.el.p(
                "Affectations opérationnelles",
                class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/40",
            ),
            rx.foreach(
                AdministrationState.detail_assignments, _assignment_card
            ),
            class_name="flex flex-col gap-3 mt-4",
        ),
        class_name="flex flex-col gap-2 mt-5",
    )


def activity_row(item: ActivityRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            tone_badge(item["kind_label"], item["tone"]),
            rx.el.span(
                item["module_label"] + " · " + item["action_label"],
                class_name="text-[11px] font-semibold text-emerald-100/55 truncate",
            ),
            rx.el.span(
                item["when"],
                class_name="text-[10px] font-medium text-emerald-100/40 ml-auto shrink-0",
            ),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.p(
            item["summary"],
            class_name="text-sm font-medium text-emerald-50/85 mt-1",
        ),
        rx.el.div(
            rx.icon("user", class_name="h-3 w-3 text-lime-300/70"),
            rx.el.span(
                item["actor"],
                class_name="text-[10px] font-semibold text-emerald-100/50",
            ),
            chip(item["object_ref"]),
            rx.cond(
                item["sensitive"],
                rx.el.span(
                    "AUDIT",
                    class_name="rounded-full border border-red-400/30 bg-red-500/10 px-1.5 py-0.5 text-[9px] font-bold text-red-300 w-fit",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-2 mt-2",
        ),
        class_name="rounded-2xl border border-white/10 bg-white/[0.03] p-4 w-full",
    )


def _history_tab() -> rx.Component:
    return rx.el.div(
        rx.cond(
            AdministrationState.detail_activity.length() > 0,
            rx.el.div(
                rx.foreach(AdministrationState.detail_activity, activity_row),
                class_name="flex flex-col gap-3",
            ),
            rx.el.p(
                "Aucune activité consignée pour ce compte.",
                class_name="text-sm font-medium text-emerald-100/50",
            ),
        ),
        class_name="mt-5",
    )


def admin_user_detail() -> rx.Component:
    return rx.el.section(
        rx.cond(
            AdministrationState.has_selection,
            rx.el.div(
                _header(),
                rx.match(
                    AdministrationState.tab,
                    ("profil", _profil()),
                    ("organisation", _organisation()),
                    ("roles", _roles_tab()),
                    ("perimetre", _scope_tab()),
                    ("historique", _history_tab()),
                    _profil(),
                ),
                class_name="w-full",
            ),
            rx.el.div(
                rx.icon("id-card", class_name="h-7 w-7 text-lime-300/70"),
                rx.el.p(
                    "Sélectionnez un utilisateur pour ouvrir sa fiche.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-3",
                ),
                class_name="flex flex-col items-center justify-center py-24",
            ),
        ),
        class_name=f"flex-1 min-w-0 {CARD}",
    )

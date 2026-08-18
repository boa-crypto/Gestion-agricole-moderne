import reflex as rx

from app.admin_users import Option, UserRow
from app.components.admin_shared import (
    CARD,
    SELECT,
    avatar,
    chip,
    section_title,
    tone_badge,
)
from app.states.administration_state import AdministrationState


def _select(
    name: str,
    icon: str,
    value: rx.Var,
    on_change: rx.event.EventType,
    first: rx.Component,
    options: rx.Var[list[Option]],
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
            default_value=value,
            key=f"admin-{name}-{AdministrationState.form_key}",
            on_change=on_change,
            class_name=SELECT,
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
        ),
        class_name="relative w-full sm:w-52",
    )


def admin_filters() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "search",
                class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
            ),
            rx.el.input(
                placeholder="Rechercher un nom, un matricule, une fonction, un rôle ou une équipe…",
                default_value=AdministrationState.search,
                on_change=AdministrationState.set_search.debounce(400),
                class_name="w-full rounded-xl border border-white/10 bg-[#04140d] py-2.5 pl-9 pr-3 text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 outline-hidden transition-colors",
            ),
            class_name="relative flex-1 min-w-0",
        ),
        _select(
            "status",
            "flag",
            AdministrationState.status_filter,
            AdministrationState.set_status_filter,
            rx.el.option("Tous les statuts", value="TOUS"),
            AdministrationState.status_options,
        ),
        _select(
            "role",
            "shield-check",
            AdministrationState.role_filter,
            AdministrationState.set_role_filter,
            rx.el.option("Tous les rôles", value="TOUS"),
            AdministrationState.role_options,
        ),
        _select(
            "team",
            "users",
            AdministrationState.team_filter,
            AdministrationState.set_team_filter,
            rx.el.option("Toutes les équipes", value="TOUTES"),
            AdministrationState.team_options,
        ),
        rx.el.button(
            rx.icon("download", class_name="h-4 w-4 text-[#04140d]"),
            rx.el.span("Exporter (CSV)", class_name="text-[#04140d]"),
            on_click=AdministrationState.export_users,
            class_name="flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
        ),
        rx.el.button(
            rx.icon("rotate-ccw", class_name="h-4 w-4"),
            rx.el.span("Réinitialiser"),
            on_click=AdministrationState.reset_filters,
            class_name="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
        ),
        class_name="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-3 w-full",
    )


def _user_card(user: UserRow, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            avatar(user["seed"], user["initials"]),
            rx.el.div(
                rx.el.p(
                    user["name"],
                    class_name="text-sm font-semibold text-emerald-50 truncate text-left",
                ),
                rx.el.p(
                    user["matricule"] + " · " + user["function_label"],
                    class_name="text-[11px] font-medium text-emerald-100/50 truncate text-left",
                ),
                class_name="min-w-0 flex-1",
            ),
            tone_badge(user["status_label"], user["status_tone"]),
            class_name="flex items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.el.span(
                user["role_label"],
                class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
            ),
            chip(user["team_label"]),
            chip(user["family_label"]),
            rx.cond(
                user["mfa_enabled"],
                rx.el.span(
                    "MFA",
                    class_name="rounded-full border border-sky-300/40 bg-sky-300/10 px-1.5 py-0.5 text-[9px] font-bold text-sky-200 w-fit",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        rx.el.div(
            rx.el.span(
                user["scopes"].to_string() + " périmètre(s)",
                class_name="text-[10px] font-medium text-emerald-100/45",
            ),
            rx.el.span(
                user["assignments"].to_string() + " affectation(s)",
                class_name="text-[10px] font-medium text-emerald-100/45",
            ),
            rx.el.span(
                user["last_login"],
                class_name="text-[10px] font-semibold text-lime-200 ml-auto truncate",
            ),
            class_name="flex items-center gap-2 w-full mt-2 min-w-0",
        ),
        on_click=AdministrationState.select_user(user["id"]),
        key=key,
        class_name=rx.cond(
            AdministrationState.selected_user_id == user["id"],
            "w-full rounded-2xl border border-lime-300/40 bg-lime-300/[0.07] p-4 text-left ring-2 ring-lime-300/40 transition-all",
            "w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left hover:border-lime-300/25 transition-all",
        ),
    )


def admin_user_list() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            section_title(
                "Registre",
                "Utilisateurs",
                "Qui travaille dans l'exploitation et avec quels droits.",
            ),
            rx.el.span(
                AdministrationState.user_count,
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-bold text-emerald-100/70 w-fit",
            ),
            class_name="flex items-end justify-between gap-3",
        ),
        rx.cond(
            AdministrationState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-2xl bg-white/[0.05]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-2xl bg-white/[0.05]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-2xl bg-white/[0.05]"
                ),
                class_name="flex flex-col gap-3 mt-5",
            ),
            rx.cond(
                AdministrationState.users.length() > 0,
                rx.el.div(
                    rx.foreach(
                        AdministrationState.users,
                        lambda u: _user_card(u, key=u["id"].to_string()),
                    ),
                    class_name="flex flex-col gap-3 mt-5 max-h-[48rem] overflow-y-auto pr-1",
                ),
                rx.el.div(
                    rx.icon("user-x", class_name="h-6 w-6 text-amber-300"),
                    rx.el.p(
                        "Aucun compte pour ces critères.",
                        class_name="text-sm font-medium text-emerald-100/60 mt-2 text-center",
                    ),
                    class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-12 mt-5",
                ),
            ),
        ),
        class_name=f"w-full xl:w-[25rem] shrink-0 {CARD}",
    )

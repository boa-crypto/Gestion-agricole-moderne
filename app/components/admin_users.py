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
from app.components.design import action_button, field, input_class, select_field
from app.states.administration_state import AdministrationState


def _select(
    name: str,
    icon: str,
    value: rx.Var,
    on_change: rx.event.EventType,
    first: rx.Component,
    options: rx.Var[list[Option]],
) -> rx.Component:
    return select_field(
        first,
        rx.foreach(
            options,
            lambda opt: rx.el.option(opt["label"], value=opt["value"]),
        ),
        name=name,
        icon=icon,
        default_value=value,
        on_change=on_change,
        form_key=AdministrationState.form_key,
    )


def admin_filters() -> rx.Component:
    return rx.el.div(
        field(
            rx.el.input(
                placeholder=(
                    "Rechercher un nom, un matricule, une fonction, "
                    "un rôle ou une équipe…"
                ),
                default_value=AdministrationState.search,
                on_change=AdministrationState.set_search.debounce(400),
                class_name=input_class(icon=True),
            ),
            icon="search",
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
        action_button(
            "Exporter (CSV)",
            icon="download",
            on_click=AdministrationState.export_users,
        ),
        action_button(
            "Réinitialiser",
            icon="rotate-ccw",
            tone="outline",
            on_click=AdministrationState.reset_filters,
        ),
        class_name=(
            "flex flex-col sm:flex-row sm:flex-wrap items-stretch "
            "sm:items-center gap-3 w-full mt-5"
        ),
    )


def _user_card(user: UserRow, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            avatar(user["seed"], user["initials"]),
            rx.el.div(
                rx.el.p(
                    user["name"],
                    class_name="text-sm font-semibold text-[#f2efe4] truncate text-left",
                ),
                rx.el.p(
                    user["matricule"] + " · " + user["function_label"],
                    class_name="text-[11px] font-medium text-[#c9c5b4]/50 truncate text-left",
                ),
                class_name="min-w-0 flex-1",
            ),
            tone_badge(user["status_label"], user["status_tone"]),
            class_name="flex items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.el.span(
                user["role_label"],
                class_name="rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit",
            ),
            chip(user["team_label"]),
            chip(user["family_label"]),
            rx.cond(
                user["mfa_enabled"],
                rx.el.span(
                    "MFA",
                    class_name="rounded-none border border-[#9cc3ff]/40 bg-[#9cc3ff]/10 px-1.5 py-0.5 text-[9px] font-bold text-[#c3daff] w-fit",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        rx.el.div(
            rx.el.span(
                user["scopes"].to_string() + " périmètre(s)",
                class_name="text-[10px] font-medium text-[#c9c5b4]/45",
            ),
            rx.el.span(
                user["assignments"].to_string() + " affectation(s)",
                class_name="text-[10px] font-medium text-[#c9c5b4]/45",
            ),
            rx.el.span(
                user["last_login"],
                class_name="text-[10px] font-semibold text-[#e4ff9b] ml-auto truncate",
            ),
            class_name="flex items-center gap-2 w-full mt-2 min-w-0",
        ),
        on_click=AdministrationState.select_user(user["id"]),
        key=key,
        class_name=rx.cond(
            AdministrationState.selected_user_id == user["id"],
            "w-full rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/[0.07] p-4 text-left ring-2 ring-[#d8fa5e]/40 transition-all",
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 text-left hover:border-[#d8fa5e]/25 transition-all",
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
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-xs font-bold text-[#c9c5b4]/70 w-fit",
            ),
            class_name="flex items-end justify-between gap-3",
        ),
        rx.cond(
            AdministrationState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-none bg-[#16190f]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-none bg-[#16190f]"
                ),
                rx.el.div(
                    class_name="animate-pulse h-28 rounded-none bg-[#16190f]"
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
                    rx.icon("user-x", class_name="h-6 w-6 text-[#ff8a5b]"),
                    rx.el.p(
                        "Aucun compte pour ces critères.",
                        class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2 text-center",
                    ),
                    class_name="flex flex-col items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#101208] py-12 mt-5",
                ),
            ),
        ),
        class_name=f"w-full xl:w-[25rem] shrink-0 {CARD}",
    )

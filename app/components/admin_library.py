import reflex as rx

from app.admin_users import FunctionRow, TeamRow
from app.components.admin_shared import CARD, chip, section_title, tone_badge
from app.states.administration_state import AdministrationState


def _family_chip(option: dict) -> rx.Component:
    return rx.el.button(
        rx.el.span(option["label"]),
        on_click=AdministrationState.set_family_filter(option["value"]),
        class_name=rx.cond(
            AdministrationState.family_filter == option["value"],
            "rounded-none bg-[#d8fa5e] px-3 py-1.5 text-[11px] font-bold text-[#0A0A08] transition-colors w-fit",
            "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1.5 text-[11px] font-semibold text-[#c9c5b4]/65 hover:border-[#d8fa5e]/30 transition-colors w-fit",
        ),
    )


def _function_card(item: FunctionRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(item["icon"], class_name="h-4 w-4 text-[#d8fa5e]"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/[0.08]",
            ),
            rx.el.div(
                rx.el.p(
                    item["label"],
                    class_name="text-sm font-semibold text-[#f2efe4] truncate",
                ),
                rx.el.p(
                    item["family_label"],
                    class_name="ap-eyebrow text-[#d8fa5e]/70",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.span(
                item["users"].to_string(),
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-bold text-[#c9c5b4]/70 w-fit",
            ),
            class_name="flex items-center gap-3 w-full min-w-0",
        ),
        rx.el.p(
            item["mission"],
            class_name="text-[12px] font-medium text-[#c9c5b4]/65 mt-3",
        ),
        rx.el.p(
            item["responsibilities"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/40 mt-2",
        ),
        rx.el.div(
            rx.icon("shield-check", class_name="h-3.5 w-3.5 text-[#ff8a5b]/80"),
            rx.el.span(
                "Rôle par défaut : " + item["default_role"],
                class_name="text-[10px] font-semibold text-[#c9c5b4]/55",
            ),
            class_name="flex items-center gap-1.5 mt-3 border-t border-[#f2efe4]/10 pt-3",
        ),
        class_name="rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 hover:border-[#d8fa5e]/25 transition-colors w-full",
    )


def admin_functions() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            section_title(
                "Bibliothèque",
                "Fonctions agricoles",
                "Le métier réel de la personne, distinct de son rôle applicatif.",
            ),
            rx.el.span(
                AdministrationState.functions.length(),
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-xs font-bold text-[#c9c5b4]/70 w-fit",
            ),
            class_name="flex items-end justify-between gap-3",
        ),
        rx.el.div(
            rx.el.button(
                "Toutes les familles",
                on_click=AdministrationState.set_family_filter("TOUTES"),
                class_name=rx.cond(
                    AdministrationState.family_filter == "TOUTES",
                    "rounded-none bg-[#d8fa5e] px-3 py-1.5 text-[11px] font-bold text-[#0A0A08] transition-colors w-fit",
                    "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1.5 text-[11px] font-semibold text-[#c9c5b4]/65 hover:border-[#d8fa5e]/30 transition-colors w-fit",
                ),
            ),
            rx.foreach(AdministrationState.family_options, _family_chip),
            class_name="flex flex-wrap items-center gap-2 mt-4",
        ),
        rx.el.div(
            rx.foreach(AdministrationState.functions, _function_card),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mt-5",
        ),
        class_name=f"w-full {CARD}",
    )


def _team_card(team: TeamRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(team["icon"], class_name="h-4 w-4 text-[#d8fa5e]"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/[0.08]",
            ),
            rx.el.div(
                rx.el.p(
                    team["name"],
                    class_name="text-sm font-semibold text-[#f2efe4] truncate",
                ),
                rx.el.p(
                    team["code"] + " · " + team["sector"],
                    class_name="text-[11px] font-medium text-[#c9c5b4]/50 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            tone_badge(
                team["status"],
                rx.cond(team["status"] == "ACTIVE", "good", "muted"),
            ),
            class_name="flex items-center gap-3 w-full min-w-0",
        ),
        rx.el.p(
            team["activity"],
            class_name="text-[12px] font-medium text-[#c9c5b4]/65 mt-3",
        ),
        rx.el.div(
            rx.icon("user-check", class_name="h-3.5 w-3.5 text-[#d8fa5e]/80"),
            rx.el.span(
                team["leader"],
                class_name="text-[11px] font-semibold text-[#f2efe4]/85 truncate",
            ),
            class_name="flex items-center gap-1.5 mt-3 min-w-0",
        ),
        rx.el.div(
            chip(team["members"].to_string() + " membre(s)"),
            chip(team["parcels"].to_string() + " parcelle(s)"),
            chip(team["schedule"]),
            class_name="flex flex-wrap items-center gap-2 mt-3 border-t border-[#f2efe4]/10 pt-3",
        ),
        class_name="rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 hover:border-[#d8fa5e]/25 transition-colors w-full",
    )


def admin_teams() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            section_title(
                "Organisation",
                "Équipes agricoles",
                "Responsable, membres, activité et parcelles couvertes.",
            ),
            rx.el.span(
                AdministrationState.teams.length(),
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-xs font-bold text-[#c9c5b4]/70 w-fit",
            ),
            class_name="flex items-end justify-between gap-3",
        ),
        rx.el.div(
            rx.foreach(AdministrationState.teams, _team_card),
            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mt-5",
        ),
        class_name=f"w-full {CARD}",
    )

"""Index latéral éditorial et navigation mobile d'AgriPro."""

from __future__ import annotations

import reflex as rx

from app.components.design import hairline
from app.components.guide_help import guide_help_panel
from app.components.menu_auth import account_controls
from app.states.help_state import HelpState
from app.states.navigation_state import NavigationState


def _number(index) -> rx.Var | str:
    return rx.cond(index < 9, "0", "") + (index + 1).to_string()


def _rail_item(item, index) -> rx.Component:
    active = NavigationState.selected_cockpit == item["key"]
    return rx.el.button(
        rx.el.span(
            _number(index),
            class_name=rx.cond(
                active,
                "ap-mono hidden w-5 shrink-0 text-[9px] tracking-[0.1em] text-[#D8FA5E] xl:block",
                "ap-mono hidden w-5 shrink-0 text-[9px] tracking-[0.1em] text-[#C9C5B4]/30 xl:block",
            ),
        ),
        rx.icon(item["icon"], class_name="h-4 w-4 shrink-0"),
        rx.el.span(
            item["label"],
            class_name="hidden flex-1 truncate text-left text-[11px] leading-tight xl:block",
        ),
        rx.cond(
            item["available"],
            rx.fragment(),
            rx.el.span(
                "—",
                class_name="ap-mono hidden text-[10px] text-[#FF8A5B] xl:block",
                title=item["note"],
            ),
        ),
        type="button",
        disabled=~item["available"],
        title=rx.cond(item["available"], item["label"], f"{item['label']} — à venir"),
        aria_label=rx.cond(
            item["available"], item["label"], f"{item['label']} — à venir"
        ),
        aria_pressed=active,
        on_click=NavigationState.select_cockpit(item["key"]),
        class_name=rx.cond(
            active,
            "flex w-full items-center gap-2.5 border-l-2 border-[#D8FA5E] bg-[#D8FA5E]/8 px-2.5 py-2.5 text-[#D8FA5E] transition-colors xl:gap-3 xl:px-3",
            "flex w-full items-center gap-2.5 border-l-2 border-transparent px-2.5 py-2.5 text-[#C9C5B4]/70 transition-colors hover:border-[#F2EFE4]/25 hover:bg-[#14160F] hover:text-[#F2EFE4] xl:gap-3 xl:px-3 disabled:cursor-not-allowed disabled:opacity-35 disabled:hover:bg-transparent",
        ),
    )


def _rail_link(label: str, href: str, icon: str) -> rx.Component:
    return rx.el.a(
        rx.icon(icon, class_name="h-4 w-4 shrink-0"),
        rx.el.span(
            label,
            class_name="ap-mono hidden text-[9px] uppercase tracking-[0.16em] xl:block",
        ),
        href=href,
        title=label,
        aria_label=label,
        class_name=(
            "ap-mono flex w-full items-center gap-2.5 border-l-2 border-transparent "
            "px-2.5 py-2.5 text-[#C9C5B4]/60 transition-colors hover:border-[#F2EFE4]/25 "
            "hover:bg-[#14160F] hover:text-[#F2EFE4] xl:gap-3 xl:px-3"
        ),
    )


def side_rail(active: str) -> rx.Component:
    """Index vertical numéroté des cockpits (desktop)."""
    return rx.fragment(
        guide_help_panel(),
        rx.el.aside(
            rx.el.div(
                rx.el.span(
                    "Sommaire",
                    class_name=(
                        "ap-eyebrow block px-3 pb-3 pt-6 text-[#C9C5B4]/35 "
                        "xl:px-3"
                    ),
                ),
                rx.el.nav(
                    rx.foreach(
                        NavigationState.cockpits,
                        lambda item, index: _rail_item(item, index),
                    ),
                    aria_label="Cockpits métier",
                    class_name="flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto pb-4",
                ),
                hairline(),
                rx.el.div(
                    rx.cond(
                        NavigationState.global_visible,
                        _rail_link("Cockpit global", "/", "house"),
                        rx.fragment(),
                    ),
                    rx.cond(
                        NavigationState.search_visible,
                        _rail_link("Recherche", "/recherche", "search"),
                        rx.fragment(),
                    ),
                    rx.el.button(
                        rx.icon("life-buoy", class_name="h-4 w-4 shrink-0"),
                        rx.el.span(
                            "Aide",
                            class_name="ap-mono hidden text-[9px] uppercase tracking-[0.16em] xl:block",
                        ),
                        type="button",
                        on_click=HelpState.toggle_context(active),
                        aria_label="Ouvrir l'aide contextuelle",
                        class_name=(
                            "ap-mono flex w-full items-center gap-2.5 border-l-2 "
                            "border-transparent px-2.5 py-2.5 text-[#C9C5B4]/60 transition-colors "
                            "hover:border-[#F2EFE4]/25 hover:bg-[#14160F] hover:text-[#F2EFE4] "
                            "xl:gap-3 xl:px-3"
                        ),
                    ),
                    rx.el.p(
                        "MMXXVI",
                        class_name=(
                            "ap-mono hidden px-3 pb-4 pt-3 text-[9px] tracking-[0.3em] "
                            "text-[#C9C5B4]/25 xl:block"
                        ),
                    ),
                    class_name="mt-2 flex flex-col",
                ),
                class_name="flex min-h-0 flex-1 flex-col px-2 pt-0",
            ),
            class_name=(
                "fixed bottom-0 left-0 top-14 z-30 hidden w-16 flex-col border-r "
                "border-[#F2EFE4]/12 bg-[#0A0A08] md:flex xl:w-60"
            ),
        ),
    )


def _mobile_item(item, index) -> rx.Component:
    active = NavigationState.selected_cockpit == item["key"]
    return rx.el.button(
        rx.el.span(
            _number(index),
            class_name=rx.cond(
                active,
                "ap-mono w-6 shrink-0 text-[9px] text-[#D8FA5E]",
                "ap-mono w-6 shrink-0 text-[9px] text-[#C9C5B4]/30",
            ),
        ),
        rx.icon(item["icon"], class_name="h-4 w-4 shrink-0"),
        rx.el.span(item["label"], class_name="flex-1 truncate text-left"),
        rx.cond(
            item["available"],
            rx.icon("arrow-up-right", class_name="h-3.5 w-3.5 opacity-40"),
            rx.el.span("À venir", class_name="ap-mono text-[8px] text-[#FF8A5B]"),
        ),
        type="button",
        disabled=~item["available"],
        aria_pressed=active,
        on_click=NavigationState.select_cockpit(item["key"]),
        class_name=rx.cond(
            active,
            "flex w-full items-center gap-3 border border-[#D8FA5E]/40 bg-[#D8FA5E]/8 px-3 py-3 text-[12px] font-medium text-[#D8FA5E]",
            "flex w-full items-center gap-3 border border-[#F2EFE4]/10 px-3 py-3 text-[12px] text-[#C9C5B4] disabled:opacity-35",
        ),
    )


def mobile_navigation(active: str) -> rx.Component:
    """Tiroir de navigation mobile (masthead)."""
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.trigger(
            rx.el.button(
                rx.icon("menu", class_name="h-4 w-4"),
                type="button",
                aria_label="Ouvrir l'index des cockpits",
                class_name=(
                    "ap-mono inline-flex h-9 w-9 items-center justify-center border "
                    "border-[#F2EFE4]/16 text-[#C9C5B4] transition-colors "
                    "hover:border-[#D8FA5E] hover:text-[#D8FA5E] md:hidden"
                ),
            ),
            as_child=True,
        ),
        rx.radix.primitives.dialog.portal(
            rx.radix.primitives.dialog.overlay(
                class_name="fixed inset-0 z-[70] bg-[#060604]/85"
            ),
            rx.radix.primitives.dialog.content(
                rx.el.div(
                    rx.el.div(
                        rx.el.span(class_name="h-2 w-2 bg-[#D8FA5E]"),
                        rx.el.span(
                            "AgriPro",
                            class_name="ap-serif text-2xl text-[#F2EFE4]",
                        ),
                        class_name="flex items-center gap-3",
                    ),
                    rx.radix.primitives.dialog.title(
                        "Index des cockpits",
                        class_name="ap-eyebrow mt-6 text-[#C9C5B4]/45",
                    ),
                    rx.radix.primitives.dialog.description(
                        "Choisissez un cockpit, puis un domaine. Échap ferme ce panneau.",
                        class_name="mt-2 text-[12px] leading-relaxed text-[#C9C5B4]/60",
                    ),
                    rx.radix.primitives.dialog.close(
                        rx.el.button(
                            rx.icon("x", class_name="h-4 w-4"),
                            type="button",
                            aria_label="Fermer la navigation",
                            class_name=(
                                "inline-flex h-9 w-9 items-center justify-center border "
                                "border-[#F2EFE4]/16 text-[#C9C5B4]"
                            ),
                        ),
                        as_child=True,
                    ),
                    class_name="flex items-start justify-between gap-3",
                ),
                rx.el.div(
                    rx.foreach(
                        NavigationState.cockpits,
                        lambda item, index: _mobile_item(item, index),
                    ),
                    class_name="mt-6 flex max-h-[52vh] flex-col gap-1.5 overflow-y-auto pr-1",
                ),
                rx.el.div(
                    account_controls(),
                    rx.el.button(
                        "Aide contextuelle",
                        type="button",
                        on_click=HelpState.toggle_context(active),
                        class_name=(
                            "ap-mono inline-flex items-center gap-2 border "
                            "border-[#F2EFE4]/16 px-3 py-2.5 text-[9px] uppercase "
                            "tracking-[0.18em] text-[#C9C5B4]"
                        ),
                    ),
                    class_name="mt-6 flex items-center justify-between gap-3 border-t border-[#F2EFE4]/12 pt-5",
                ),
                class_name=(
                    "fixed inset-x-3 bottom-3 top-3 z-[80] overflow-y-auto border "
                    "border-[#F2EFE4]/16 bg-[#0A0A08] p-5 sm:inset-x-auto sm:left-3 "
                    "sm:w-[24rem]"
                ),
            ),
        ),
        open=NavigationState.mobile_open,
        on_open_change=NavigationState.set_mobile_open,
    )

"""Coque éditoriale de l'application AgriPro.

Masthead fixe, index latéral numéroté, bandeau de domaines dépliable et
colophon : la coque remplace les duplications d'en-têtes page par page et
installe la grille typographique de la maison.
"""

from __future__ import annotations

import reflex as rx

from app.components.design import eyebrow, hairline, icon_action
from app.components.menu_auth import account_controls
from app.components.side_rail import mobile_navigation, side_rail
from app.states.help_state import HelpState
from app.states.navigation_state import NavigationState


def _brand() -> rx.Component:
    return rx.el.a(
        rx.el.span(
            class_name="h-2 w-2 shrink-0 bg-[#D8FA5E]",
            aria_hidden="true",
        ),
        rx.el.span(
            "AgriPro",
            class_name="ap-serif text-[27px] leading-none text-[#F2EFE4]",
        ),
        rx.el.span(
            "Édition agronomique",
            class_name=(
                "ap-mono hidden 2xl:block border-l border-[#F2EFE4]/16 pl-4 "
                "text-[9px] uppercase leading-tight tracking-[0.26em] "
                "text-[#C9C5B4]/50"
            ),
        ),
        href="/",
        aria_label="AgriPro — retour au cockpit global",
        class_name=(
            "flex h-full shrink-0 items-center gap-3 border-r border-[#F2EFE4]/12 "
            "px-4 sm:px-6 transition-colors hover:bg-[#14160F]"
        ),
    )


def _breadcrumb() -> rx.Component:
    return rx.el.nav(
        rx.el.a(
            "AgriPro",
            href="/",
            class_name="ap-mono hidden text-[9px] uppercase tracking-[0.22em] text-[#C9C5B4]/45 hover:text-[#D8FA5E] sm:inline",
        ),
        rx.el.span(
            "/",
            class_name="ap-mono hidden text-[9px] text-[#C9C5B4]/25 sm:inline",
            aria_hidden="true",
        ),
        rx.el.span(
            NavigationState.current_cockpit_label,
            class_name="ap-mono text-[9px] uppercase tracking-[0.22em] text-[#C9C5B4]/70",
        ),
        rx.el.span(
            "/",
            class_name="ap-mono hidden text-[9px] text-[#C9C5B4]/25 md:inline",
            aria_hidden="true",
        ),
        rx.el.span(
            NavigationState.current_entry["domain"],
            class_name="ap-mono hidden text-[9px] uppercase tracking-[0.22em] text-[#C9C5B4]/40 md:inline",
        ),
        rx.el.span(
            "/",
            class_name="ap-mono hidden text-[9px] text-[#C9C5B4]/25 lg:inline",
            aria_hidden="true",
        ),
        rx.el.span(
            NavigationState.current_entry["label"],
            aria_current="page",
            class_name="ap-mono hidden text-[9px] uppercase tracking-[0.22em] text-[#F2EFE4] lg:inline",
        ),
        aria_label="Fil d'Ariane",
        class_name="flex min-w-0 items-center gap-2 overflow-hidden",
    )


def _cockpit_selector() -> rx.Component:
    return rx.el.div(
        rx.el.select(
            rx.foreach(
                NavigationState.cockpits,
                lambda item: rx.el.option(
                    rx.cond(
                        item["available"],
                        item["label"],
                        f"{item['label']} — à venir",
                    ),
                    value=item["key"],
                    disabled=~item["available"],
                ),
            ),
            value=NavigationState.selected_cockpit,
            on_change=NavigationState.select_cockpit,
            id="nav-selector",
            aria_label="Sélectionner un cockpit",
            class_name=(
                "ap-mono h-9 w-full appearance-none border border-[#F2EFE4]/16 "
                "bg-[#0A0A08] px-3 pr-8 text-[9px] uppercase tracking-[0.18em] "
                "text-[#F2EFE4] hover:border-[#D8FA5E]/50 focus-visible:border-[#D8FA5E]"
            ),
        ),
        rx.icon(
            "chevron-down",
            class_name="pointer-events-none absolute right-2.5 top-2.5 h-4 w-4 text-[#C9C5B4]/60",
        ),
        class_name="relative hidden w-44 shrink-0 lg:block xl:w-52",
    )


def _masthead(active: str) -> rx.Component:
    return rx.el.header(
        rx.el.div(
            _brand(),
            rx.el.div(
                _breadcrumb(),
                class_name="flex min-w-0 flex-1 items-center px-4 sm:px-6",
            ),
            rx.el.div(
                _cockpit_selector(),
                rx.el.button(
                    rx.icon("layout-grid", class_name="h-4 w-4"),
                    rx.el.span(
                        "Domaines",
                        class_name="ap-mono hidden text-[9px] uppercase tracking-[0.18em] xl:inline",
                    ),
                    type="button",
                    on_click=NavigationState.toggle_panel,
                    aria_expanded=NavigationState.panel_open,
                    aria_controls="nav-context",
                    title="Index des domaines du cockpit",
                    class_name=(
                        "inline-flex h-9 items-center gap-2 border border-[#F2EFE4]/16 "
                        "px-3 text-[#C9C5B4] transition-colors hover:border-[#D8FA5E] "
                        "hover:text-[#D8FA5E]"
                    ),
                ),
                rx.cond(
                    NavigationState.search_visible,
                    icon_action("search", "Recherche globale", href="/recherche"),
                    rx.fragment(),
                ),
                rx.el.button(
                    rx.icon("life-buoy", class_name="h-4 w-4"),
                    type="button",
                    on_click=HelpState.toggle_context(active),
                    aria_label="Ouvrir l'aide contextuelle",
                    title="Aide contextuelle",
                    class_name=(
                        "ap-mono inline-flex h-9 w-9 items-center justify-center "
                        "border border-[#F2EFE4]/16 text-[#C9C5B4] transition-colors "
                        "hover:border-[#D8FA5E] hover:text-[#D8FA5E]"
                    ),
                ),
                account_controls(),
                mobile_navigation(active),
                class_name="flex shrink-0 items-center gap-2 px-3 sm:px-5",
            ),
            class_name="flex h-14 w-full items-stretch",
        ),
        class_name=(
            "fixed inset-x-0 top-0 z-40 border-b border-[#F2EFE4]/16 "
            "bg-[#0A0A08]"
        ),
    )


def _context_domain(domain) -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            domain,
            class_name="ap-eyebrow text-[#C9C5B4]/45",
        ),
        rx.el.div(
            rx.foreach(
                NavigationState.entries,
                lambda entry: rx.cond(
                    entry["domain"] == domain,
                    rx.el.a(
                        rx.icon(
                            entry["icon"],
                            class_name="h-3.5 w-3.5 shrink-0 text-[#C9C5B4]/50",
                        ),
                        rx.el.span(entry["label"], class_name="truncate"),
                        href=entry["href"],
                        on_click=NavigationState.close_mobile,
                        aria_current=rx.cond(
                            NavigationState.current_entry["key"] == entry["key"],
                            "page",
                            "false",
                        ),
                        class_name=rx.cond(
                            NavigationState.current_entry["key"] == entry["key"],
                            "ap-mono flex items-center gap-2.5 border-l-2 border-[#D8FA5E] bg-[#D8FA5E]/8 px-3 py-2 text-[10px] uppercase tracking-[0.12em] text-[#D8FA5E]",
                            "ap-mono flex items-center gap-2.5 border-l-2 border-transparent px-3 py-2 text-[10px] uppercase tracking-[0.12em] text-[#C9C5B4]/70 transition-colors hover:border-[#F2EFE4]/25 hover:text-[#F2EFE4]",
                        ),
                    ),
                    rx.fragment(),
                ),
            ),
            class_name="mt-3 flex flex-col",
        ),
        class_name="min-w-0",
    )


def context_panel() -> rx.Component:
    """Index des domaines du cockpit courant (déplié depuis le masthead)."""
    return rx.cond(
        NavigationState.panel_open,
        rx.el.section(
            rx.el.div(
                eyebrow("Index du cockpit", tone="accent"),
                rx.el.h2(
                    NavigationState.selected_label,
                    class_name="ap-serif mt-3 text-3xl text-[#F2EFE4]",
                ),
                rx.el.p(
                    NavigationState.selected_note,
                    class_name="mt-2 max-w-xl text-[12px] leading-relaxed text-[#C9C5B4]/60",
                ),
                rx.el.button(
                    rx.icon("x", class_name="h-4 w-4"),
                    "Fermer",
                    type="button",
                    on_click=NavigationState.close_panel,
                    class_name=(
                        "ap-mono inline-flex h-8 shrink-0 items-center gap-2 border "
                        "border-[#F2EFE4]/16 px-3 text-[9px] uppercase tracking-[0.18em] "
                        "text-[#C9C5B4] hover:border-[#D8FA5E] hover:text-[#D8FA5E]"
                    ),
                ),
                class_name="flex items-start justify-between gap-6",
            ),
            hairline("mt-6"),
            rx.el.div(
                rx.foreach(NavigationState.domains, _context_domain),
                class_name="mt-6 grid grid-cols-1 gap-x-8 gap-y-6 sm:grid-cols-2 xl:grid-cols-4",
            ),
            id="nav-context",
            class_name=(
                "ap-reveal mb-10 border border-[#F2EFE4]/12 bg-[#101208] p-5 sm:p-7"
            ),
        ),
        rx.fragment(),
    )


def _colophon(active: str) -> rx.Component:
    return rx.el.footer(
        rx.el.div(
            rx.el.span(
                "AgriPro — Pilotage végétal",
                class_name="ap-mono text-[9px] uppercase tracking-[0.24em] text-[#C9C5B4]/45",
            ),
            rx.el.span(
                NavigationState.current_entry["label"],
                class_name="ap-mono text-[9px] uppercase tracking-[0.24em] text-[#C9C5B4]/30",
            ),
            rx.el.span(
                "Édition MMXXVI",
                class_name="ap-mono text-[9px] uppercase tracking-[0.24em] text-[#C9C5B4]/45",
            ),
            class_name=(
                "flex flex-col gap-2 border-t border-[#F2EFE4]/12 pt-5 "
                "sm:flex-row sm:items-center sm:justify-between"
            ),
        ),
        class_name="mt-16 w-full",
    )


def app_shell(
    content: rx.Component,
    active: str,
    *,
    max_width: str = "max-w-[104rem]",
) -> rx.Component:
    """Coque commune : masthead, index, contenu, colophon."""
    return rx.el.div(
        _masthead(active),
        side_rail(active),
        rx.el.main(
            rx.el.div(
                context_panel(),
                content,
                _colophon(active),
                class_name=(
                    f"relative z-10 mx-auto w-full {max_width} px-4 pb-20 pt-8 "
                    "sm:px-8 lg:px-10"
                ),
            ),
            class_name="min-h-screen w-full pt-14 md:pl-16 xl:pl-60",
        ),
        class_name="relative min-h-screen w-full bg-[#0A0A08] antialiased",
    )

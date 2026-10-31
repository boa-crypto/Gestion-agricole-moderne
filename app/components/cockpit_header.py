"""En-tête éditorial du cockpit agronomique."""

from __future__ import annotations

import reflex as rx

from app.components.design import action_button, eyebrow, hairline
from app.components.guide_help import help_button
from app.states.dashboard_state import DashboardState


def _meta_row(label: str, value: rx.Var | str, *, tone: str = "paper") -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="ap-mono text-[9px] uppercase tracking-[0.22em] text-[#C9C5B4]/40",
        ),
        rx.el.span(
            value,
            class_name=(
                "ap-mono text-[10px] uppercase tracking-[0.14em] "
                + (
                    "text-[#FF8A5B]"
                    if tone == "flame"
                    else "text-[#F2EFE4]"
                )
            ),
        ),
        class_name="flex items-center justify-between gap-6 py-2",
    )


def cockpit_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            eyebrow("Pilotage végétal — relevé du jour", tone="accent"),
            rx.el.h1(
                rx.el.span("Cockpit "),
                rx.el.span(
                    "agronomique",
                    class_name="ap-italic text-[#D8FA5E]",
                ),
                class_name=(
                    "ap-display mt-6 text-[clamp(2.9rem,6.4vw,5.6rem)] "
                    "text-[#F2EFE4]"
                ),
            ),
            rx.el.p(
                "Vision instantanée des parcelles, des cultures et des chantiers "
                "de l'exploitation — une lecture d'ensemble, sans détour.",
                class_name="mt-6 max-w-xl text-[13px] leading-relaxed text-[#C9C5B4]/70",
            ),
            class_name="min-w-0 max-w-3xl",
        ),
        rx.el.div(
            rx.el.div(
                _meta_row("Jour", DashboardState.today_label),
                _meta_row("Saison", DashboardState.season_label),
                _meta_row(
                    "Alertes critiques",
                    DashboardState.critical_alerts.to_string(),
                    tone="flame",
                ),
                class_name="divide-y divide-[#F2EFE4]/10 border-y border-[#F2EFE4]/12",
            ),
            rx.el.div(
                action_button(
                    "Actualiser",
                    icon="refresh-cw",
                    on_click=DashboardState.load_dashboard,
                    disabled=DashboardState.is_loading,
                ),
                help_button("cockpit", "Guide du cockpit"),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex w-full max-w-xs shrink-0 flex-col gap-5 self-end lg:items-stretch",
        ),
        class_name=(
            "flex flex-col gap-10 pb-8 lg:flex-row lg:items-end "
            "lg:justify-between lg:gap-16"
        ),
    )

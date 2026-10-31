"""Bandeau de chiffres clés du cockpit, en registre éditorial."""

from __future__ import annotations

import reflex as rx

from app.components.design import stat
from app.states.dashboard_state import DashboardState


def kpi_strip() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.span(
                "Chiffres clés",
                class_name="ap-eyebrow text-[#C9C5B4]/40",
            ),
            rx.el.span(
                "Relevé consolidé de l'exploitation",
                class_name="ap-mono text-[9px] uppercase tracking-[0.2em] text-[#C9C5B4]/25",
            ),
            class_name="mb-5 flex flex-wrap items-baseline justify-between gap-3 border-b border-[#F2EFE4]/12 pb-3",
        ),
        rx.el.div(
            stat(
                "Surface totale",
                f"{DashboardState.kpis['area_total']:.1f}",
                "ha",
                f"{DashboardState.kpis['parcels']:.0f} parcelles cartographiées",
                index="01",
                tone="paper",
            ),
            stat(
                "En culture",
                f"{DashboardState.kpis['area_active']:.1f}",
                "ha",
                f"{DashboardState.kpis['active_crops']:.0f} cultures en cours",
                index="02",
                tone="sage",
            ),
            stat(
                "Avancement moyen",
                f"{DashboardState.kpis['progress']:.0f}",
                "%",
                "Progression des cycles culturaux",
                index="03",
                tone="paper",
            ),
            stat(
                "Chantiers 7 jours",
                f"{DashboardState.kpis['planned']:.0f}",
                "interventions",
                "Planifiées sur la semaine",
                index="04",
                tone="flame",
            ),
            stat(
                "Alertes actives",
                f"{DashboardState.kpis['alerts']:.0f}",
                "à traiter",
                f"{DashboardState.critical_alerts} en niveau critique",
                index="05",
                tone="flame",
            ),
            stat(
                "Récolté / valorisé",
                f"{DashboardState.kpis['harvest_qty']:.1f}",
                "t",
                DashboardState.revenue_display + " € de produit brut",
                index="06",
                tone="accent",
            ),
            class_name=(
                "grid grid-cols-2 gap-x-6 gap-y-8 sm:grid-cols-3 xl:grid-cols-6 "
                "xl:gap-x-8"
            ),
        ),
        class_name="w-full",
    )

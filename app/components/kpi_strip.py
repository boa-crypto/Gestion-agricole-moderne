import reflex as rx

from app.states.dashboard_state import DashboardState


def kpi_tile(
    label: str,
    value: rx.Var | str,
    unit: str,
    caption: rx.Var | str,
    icon: str,
    icon_class: str,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                label,
                class_name="text-[10px] font-semibold uppercase tracking-[0.22em] text-emerald-100/50",
            ),
            rx.icon(icon, class_name=icon_class),
            class_name="flex items-start justify-between gap-3",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="font-['Instrument_Serif'] text-3xl leading-none text-emerald-50",
            ),
            rx.el.span(
                unit,
                class_name="text-xs font-medium text-emerald-100/50 mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-4",
        ),
        rx.el.p(
            caption,
            class_name="text-[11px] font-medium text-emerald-100/45 mt-2",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.04] p-5 backdrop-blur-xl hover:border-lime-300/30 transition-colors",
    )


def kpi_strip() -> rx.Component:
    return rx.el.section(
        kpi_tile(
            "Surface totale",
            f"{DashboardState.kpis['area_total']:.1f}",
            "ha",
            f"{DashboardState.kpis['parcels']:.0f} parcelles cartographiées",
            "map",
            "h-4 w-4 text-lime-300",
        ),
        kpi_tile(
            "En culture",
            f"{DashboardState.kpis['area_active']:.1f}",
            "ha",
            f"{DashboardState.kpis['active_crops']:.0f} cultures en cours",
            "sprout",
            "h-4 w-4 text-emerald-300",
        ),
        kpi_tile(
            "Avancement moyen",
            f"{DashboardState.kpis['progress']:.0f}",
            "%",
            "Progression des cycles culturaux",
            "gauge",
            "h-4 w-4 text-lime-300",
        ),
        kpi_tile(
            "Chantiers 7 jours",
            f"{DashboardState.kpis['planned']:.0f}",
            "interventions",
            "Planifiées sur la semaine",
            "calendar-clock",
            "h-4 w-4 text-amber-300",
        ),
        kpi_tile(
            "Alertes actives",
            f"{DashboardState.kpis['alerts']:.0f}",
            "à traiter",
            f"{DashboardState.critical_alerts} en niveau critique",
            "triangle-alert",
            "h-4 w-4 text-amber-300",
        ),
        kpi_tile(
            "Récolté / valorisé",
            f"{DashboardState.kpis['harvest_qty']:.1f}",
            "t",
            f"{DashboardState.kpis['revenue']:.0f} € de produit brut",
            "wheat",
            "h-4 w-4 text-amber-300",
        ),
        class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 w-full",
    )

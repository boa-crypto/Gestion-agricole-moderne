import reflex as rx

from app.states.maintenance_state import MaintenanceState


def _tile(
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


def fleet_kpis() -> rx.Component:
    return rx.el.section(
        _tile(
            "Flotte suivie",
            f"{MaintenanceState.kpis['fleet']:.0f}",
            "engins",
            f"{MaintenanceState.kpis['available']:.0f} disponibles immédiatement",
            "tractor",
            "h-4 w-4 text-lime-300",
        ),
        _tile(
            "Immobilisations",
            f"{MaintenanceState.kpis['in_maintenance']:.0f}",
            "à l'atelier",
            f"{MaintenanceState.kpis['out_of_service']:.0f} hors service",
            "wrench",
            "h-4 w-4 text-amber-300",
        ),
        _tile(
            "Opérations ouvertes",
            f"{MaintenanceState.kpis['open_ops']:.0f}",
            "chantiers",
            f"{MaintenanceState.kpis['overdue_ops']:.0f} en retard d'exécution",
            "clipboard-list",
            "h-4 w-4 text-lime-300",
        ),
        _tile(
            "Échéances 30 j",
            f"{MaintenanceState.kpis['due_soon']:.0f}",
            "engins concernés",
            "Assurance, contrôle ou entretien",
            "calendar-clock",
            "h-4 w-4 text-amber-300",
        ),
        _tile(
            "Coût maintenance",
            f"{MaintenanceState.kpis['cost_year']:.0f}",
            "€ / 12 mois",
            f"{MaintenanceState.kpis['downtime_year']:.0f} h d'immobilisation",
            "coins",
            "h-4 w-4 text-lime-300",
        ),
        _tile(
            "Valeur du parc",
            f"{MaintenanceState.kpis['fleet_value']:.0f}",
            "€ à l'achat",
            "Capital matériel de l'exploitation",
            "warehouse",
            "h-4 w-4 text-emerald-300",
        ),
        class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 w-full",
    )

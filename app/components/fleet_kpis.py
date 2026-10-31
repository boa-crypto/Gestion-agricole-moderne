import reflex as rx

from app.components.design import stat
from app.states.maintenance_state import MaintenanceState


def _tile(
    label: str,
    value: rx.Var | str,
    unit: str,
    caption: rx.Var | str,
    icon: str,
    icon_class: str = "",
) -> rx.Component:
    """Chiffre indicateur, registre éditorial : filet, valeur serif, légende."""
    tone = "flame" if "ff8a5b" in icon_class else "paper"
    return stat(label, value, unit, caption, icon=icon, tone=tone)


def _section_title() -> rx.Component:
    return rx.el.div(
        rx.icon("wrench", class_name="h-4 w-4 text-[rgb(var(--ap-flame-soft-rgb))]"),
        rx.el.span("Indicateurs atelier", class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.78)]"),
        class_name="flex w-full items-center gap-2",
    )


def fleet_kpis() -> rx.Component:
    return rx.el.section(
        _section_title(),
        rx.el.div(
            _tile(
                "Flotte suivie",
                f"{MaintenanceState.kpis['fleet']:.0f}",
                "engins",
                f"{MaintenanceState.kpis['available']:.0f} disponibles immédiatement",
                "tractor",
                "h-4 w-4 text-[rgb(var(--ap-accent-rgb))]",
            ),
            _tile(
                "Immobilisations",
                f"{MaintenanceState.kpis['in_maintenance']:.0f}",
                "à l'atelier",
                f"{MaintenanceState.kpis['out_of_service']:.0f} hors service",
                "wrench",
                "h-4 w-4 text-[rgb(var(--ap-flame-soft-rgb))]",
            ),
            _tile(
                "Opérations ouvertes",
                f"{MaintenanceState.kpis['open_ops']:.0f}",
                "chantiers",
                f"{MaintenanceState.kpis['overdue_ops']:.0f} en retard d'exécution",
                "clipboard-list",
                "h-4 w-4 text-[rgb(var(--ap-accent-rgb))]",
            ),
            _tile(
                "Échéances 30 j",
                f"{MaintenanceState.kpis['due_soon']:.0f}",
                "engins concernés",
                "Assurance, contrôle ou entretien",
                "calendar-clock",
                "h-4 w-4 text-[rgb(var(--ap-flame-soft-rgb))]",
            ),
            _tile(
                "Coût maintenance",
                f"{MaintenanceState.kpis['cost_year']:.0f}",
                "€ / 12 mois",
                f"{MaintenanceState.kpis['downtime_year']:.0f} h d'immobilisation",
                "coins",
                "h-4 w-4 text-[rgb(var(--ap-accent-rgb))]",
            ),
            _tile(
                "Valeur du parc",
                f"{MaintenanceState.kpis['fleet_value']:.0f}",
                "€ à l'achat",
                "Capital matériel de l'exploitation",
                "warehouse",
                "h-4 w-4 text-[rgb(var(--ap-sage-rgb))]",
            ),
            class_name=(
                "ap-stagger grid grid-cols-1 gap-x-8 gap-y-7 sm:grid-cols-2 "
                "xl:grid-cols-3 w-full mt-5"
            ),
        ),
        class_name="w-full",
    )

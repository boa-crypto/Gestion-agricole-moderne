import reflex as rx

from app.components.design import stat
from app.states.operations_state import OperationsState


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
        rx.icon("tractor", class_name="h-4 w-4 text-[rgb(var(--ap-sage-rgb))]"),
        rx.el.span("Indicateurs de chantiers", class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.78)]"),
        class_name="flex w-full items-center gap-2",
    )


def operations_kpis() -> rx.Component:
    return rx.el.section(
        _section_title(),
        rx.el.div(
            _tile(
                "Chantiers à venir",
                f"{OperationsState.kpis['planned']:.0f}",
                "interventions",
                f"{OperationsState.kpis['overdue']:.0f} en retard à replanifier",
                "calendar-clock",
                "h-4 w-4 text-[rgb(var(--ap-accent-rgb))]",
            ),
            _tile(
                "Réalisées 30 j",
                f"{OperationsState.kpis['done_30']:.0f}",
                "chantiers",
                f"{OperationsState.kpis['cost_30']:.0f} € de charges opérationnelles",
                "circle-check",
                "h-4 w-4 text-[rgb(var(--ap-sage-rgb))]",
            ),
            _tile(
                "Intrants suivis",
                f"{OperationsState.kpis['products']:.0f}",
                "références",
                f"{OperationsState.kpis['critical']:.0f} sous le seuil de réappro",
                "package",
                "h-4 w-4 text-[rgb(var(--ap-flame-soft-rgb))]",
            ),
            _tile(
                "Valeur du stock",
                f"{OperationsState.kpis['stock_value']:.0f}",
                "€",
                "Valorisation au prix d'achat",
                "warehouse",
                "h-4 w-4 text-[rgb(var(--ap-accent-rgb))]",
            ),
            _tile(
                "Récolté",
                f"{OperationsState.kpis['harvest_qty']:.1f}",
                "t",
                f"Rendement moyen {OperationsState.kpis['avg_yield']:.1f} t/ha",
                "wheat",
                "h-4 w-4 text-[rgb(var(--ap-flame-soft-rgb))]",
            ),
            _tile(
                "Produit brut",
                f"{OperationsState.kpis['revenue']:.0f}",
                "€",
                "Cumul des ventes de récolte",
                "coins",
                "h-4 w-4 text-[rgb(var(--ap-accent-rgb))]",
            ),
            class_name=(
                "ap-stagger grid grid-cols-1 gap-x-8 gap-y-7 sm:grid-cols-2 "
                "xl:grid-cols-3 w-full mt-5"
            ),
        ),
        class_name="w-full",
    )

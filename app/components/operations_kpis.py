import reflex as rx

from app.states.operations_state import OperationsState


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
                class_name="ap-eyebrow text-[#c9c5b4]/50",
            ),
            rx.icon(icon, class_name=icon_class),
            class_name="flex items-start justify-between gap-3",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="ap-serif text-3xl leading-none text-[#f2efe4]",
            ),
            rx.el.span(
                unit,
                class_name="text-xs font-medium text-[#c9c5b4]/50 mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-4",
        ),
        rx.el.p(
            caption,
            class_name="text-[11px] font-medium text-[#c9c5b4]/45 mt-2",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#14160f] p-5  hover:border-[#d8fa5e]/30 transition-colors",
    )


def operations_kpis() -> rx.Component:
    return rx.el.section(
        _tile(
            "Chantiers à venir",
            f"{OperationsState.kpis['planned']:.0f}",
            "interventions",
            f"{OperationsState.kpis['overdue']:.0f} en retard à replanifier",
            "calendar-clock",
            "h-4 w-4 text-[#d8fa5e]",
        ),
        _tile(
            "Réalisées 30 j",
            f"{OperationsState.kpis['done_30']:.0f}",
            "chantiers",
            f"{OperationsState.kpis['cost_30']:.0f} € de charges opérationnelles",
            "circle-check",
            "h-4 w-4 text-[#a9c98b]",
        ),
        _tile(
            "Intrants suivis",
            f"{OperationsState.kpis['products']:.0f}",
            "références",
            f"{OperationsState.kpis['critical']:.0f} sous le seuil de réappro",
            "package",
            "h-4 w-4 text-[#ff8a5b]",
        ),
        _tile(
            "Valeur du stock",
            f"{OperationsState.kpis['stock_value']:.0f}",
            "€",
            "Valorisation au prix d'achat",
            "warehouse",
            "h-4 w-4 text-[#d8fa5e]",
        ),
        _tile(
            "Récolté",
            f"{OperationsState.kpis['harvest_qty']:.1f}",
            "t",
            f"Rendement moyen {OperationsState.kpis['avg_yield']:.1f} t/ha",
            "wheat",
            "h-4 w-4 text-[#ff8a5b]",
        ),
        _tile(
            "Produit brut",
            f"{OperationsState.kpis['revenue']:.0f}",
            "€",
            "Cumul des ventes de récolte",
            "coins",
            "h-4 w-4 text-[#d8fa5e]",
        ),
        class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 w-full",
    )

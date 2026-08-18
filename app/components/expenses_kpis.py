import reflex as rx

from app.states.expenses_state import ExpensesState


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


def expenses_kpis() -> rx.Component:
    return rx.el.section(
        _tile(
            "Charges filtrées",
            f"{ExpensesState.kpis['total_ttc']:.0f}",
            "€ TTC",
            f"{ExpensesState.kpis['total_ht']:.0f} € HT sur {ExpensesState.kpis['count']:.0f} ligne(s)",
            "receipt-text",
            "h-4 w-4 text-lime-300",
        ),
        _tile(
            "Réglé",
            f"{ExpensesState.kpis['paid']:.0f}",
            "€ TTC",
            "Dépenses déjà payées au fournisseur",
            "circle-check",
            "h-4 w-4 text-emerald-300",
        ),
        _tile(
            "Reste à payer",
            f"{ExpensesState.kpis['pending']:.0f}",
            "€ TTC",
            f"{ExpensesState.kpis['overdue']:.0f} échéance(s) dépassée(s)",
            "hourglass",
            "h-4 w-4 text-amber-300",
        ),
        _tile(
            "Mois en cours",
            f"{ExpensesState.kpis['month_total']:.0f}",
            "€ TTC",
            f"{ExpensesState.kpis['year_total']:.0f} € depuis le 1er janvier",
            "calendar-days",
            "h-4 w-4 text-lime-300",
        ),
        _tile(
            "Ticket moyen",
            f"{ExpensesState.kpis['average']:.0f}",
            "€ / ligne",
            f"{ExpensesState.kpis['cancelled']:.0f} annulée(s) · {ExpensesState.kpis['archived']:.0f} archivée(s)",
            "scale",
            "h-4 w-4 text-amber-300",
        ),
        _tile(
            "Types de charges",
            f"{ExpensesState.kpis['active_types']:.0f}",
            "actifs",
            f"{ExpensesState.kpis['types']:.0f} référencés au plan de charges",
            "tags",
            "h-4 w-4 text-emerald-300",
        ),
        class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 w-full",
    )

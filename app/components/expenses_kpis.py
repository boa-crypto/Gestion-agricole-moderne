import reflex as rx

from app.components.design import stat
from app.states.expenses_state import ExpensesState


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
        rx.icon("wallet", class_name="h-4 w-4 text-[#d8fa5e]"),
        rx.el.span("Indicateurs de charges", class_name="ap-eyebrow text-[#c9c5b4]/55"),
        class_name="flex w-full items-center gap-2",
    )


def expenses_kpis() -> rx.Component:
    return rx.el.section(
        _section_title(),
        rx.el.div(
            _tile(
                "Charges filtrées",
                f"{ExpensesState.kpis['total_ttc']:.0f}",
                "€ TTC",
                f"{ExpensesState.kpis['total_ht']:.0f} € HT sur {ExpensesState.kpis['count']:.0f} ligne(s)",
                "receipt-text",
                "h-4 w-4 text-[#d8fa5e]",
            ),
            _tile(
                "Réglé",
                f"{ExpensesState.kpis['paid']:.0f}",
                "€ TTC",
                "Dépenses déjà payées au fournisseur",
                "circle-check",
                "h-4 w-4 text-[#a9c98b]",
            ),
            _tile(
                "Reste à payer",
                f"{ExpensesState.kpis['pending']:.0f}",
                "€ TTC",
                f"{ExpensesState.kpis['overdue']:.0f} échéance(s) dépassée(s)",
                "hourglass",
                "h-4 w-4 text-[#ff8a5b]",
            ),
            _tile(
                "Mois en cours",
                f"{ExpensesState.kpis['month_total']:.0f}",
                "€ TTC",
                f"{ExpensesState.kpis['year_total']:.0f} € depuis le 1er janvier",
                "calendar-days",
                "h-4 w-4 text-[#d8fa5e]",
            ),
            _tile(
                "Ticket moyen",
                f"{ExpensesState.kpis['average']:.0f}",
                "€ / ligne",
                f"{ExpensesState.kpis['cancelled']:.0f} annulée(s) · {ExpensesState.kpis['archived']:.0f} archivée(s)",
                "scale",
                "h-4 w-4 text-[#ff8a5b]",
            ),
            _tile(
                "Types de charges",
                f"{ExpensesState.kpis['active_types']:.0f}",
                "actifs",
                f"{ExpensesState.kpis['types']:.0f} référencés au plan de charges",
                "tags",
                "h-4 w-4 text-[#a9c98b]",
            ),
            class_name=(
                "grid grid-cols-1 gap-x-8 gap-y-7 sm:grid-cols-2 "
                "xl:grid-cols-3 w-full mt-5"
            ),
        ),
        class_name="w-full",
    )

import reflex as rx

from app.components.design import stat
from app.states.crm_state import CrmState


def _tile(
    label: str,
    value: rx.Var | str,
    unit: str,
    caption: rx.Var | str,
    icon: str,
    icon_class: str = "",
) -> rx.Component:
    """Chiffre indicateur, registre éditorial : filet, valeur serif, légende."""
    return stat(
        label,
        value,
        unit,
        caption,
        icon=icon,
        tone="paper",
    )


def _section_title(label: str, icon: str, icon_class: str) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name=icon_class),
        rx.el.span(
            label,
            class_name="ap-eyebrow text-[#c9c5b4]/55",
        ),
        class_name="flex items-center gap-2 w-full",
    )


def crm_client_kpis() -> rx.Component:
    return rx.el.section(
        _section_title(
            "Indicateurs clients", "users-round", "h-4 w-4 text-[#d8fa5e]"
        ),
        rx.el.div(
            _tile(
                "Clients suivis",
                f"{CrmState.kpis['clients']:.0f}",
                "tiers",
                f"{CrmState.kpis['clients_active']:.0f} actifs · {CrmState.kpis['clients_inactive']:.0f} inactifs",
                "users-round",
                "h-4 w-4 text-[#d8fa5e]",
            ),
            _tile(
                "Nouveaux clients",
                f"{CrmState.kpis['clients_new']:.0f}",
                "90 jours",
                f"{CrmState.kpis['clients_blocked']:.0f} compte(s) bloqué(s)",
                "user-round-plus",
                "h-4 w-4 text-[#a9c98b]",
            ),
            _tile(
                "CA clients",
                CrmState.turnover_display,
                "DA TTC",
                f"{CrmState.kpis['sales_count']:.0f} vente(s) enregistrée(s)",
                "trending-up",
                "h-4 w-4 text-[#d8fa5e]",
            ),
            _tile(
                "Créances clients",
                CrmState.receivable_display,
                "DA",
                CrmState.receivable_overdue_display + " DA échus",
                "hand-coins",
                "h-4 w-4 text-[#ff8a5b]",
            ),
            _tile(
                "Paiements reçus",
                CrmState.received_display,
                "DA",
                f"{CrmState.kpis['unpaid_sales_invoices']:.0f} facture(s) impayée(s)",
                "banknote",
                "h-4 w-4 text-[#a9c98b]",
            ),
            _tile(
                "Factures en retard",
                f"{CrmState.kpis['late_sales_invoices']:.0f}",
                "clients",
                f"{CrmState.kpis['due_soon']:.0f} échéance(s) sous 15 jours",
                "alarm-clock",
                "h-4 w-4 text-[#ff8a5b]",
            ),
            class_name=(
                "grid grid-cols-1 gap-x-8 gap-y-7 sm:grid-cols-2 "
                "xl:grid-cols-3 w-full mt-5"
            ),
        ),
        class_name="w-full",
    )


def crm_supplier_kpis() -> rx.Component:
    return rx.el.section(
        _section_title(
            "Indicateurs fournisseurs", "truck", "h-4 w-4 text-[#ff8a5b]"
        ),
        rx.el.div(
            _tile(
                "Fournisseurs suivis",
                f"{CrmState.kpis['suppliers']:.0f}",
                "tiers",
                f"{CrmState.kpis['suppliers_active']:.0f} actifs sur {CrmState.kpis['partners']:.0f} partenaires",
                "truck",
                "h-4 w-4 text-[#ff8a5b]",
            ),
            _tile(
                "Achats totaux",
                CrmState.purchases_display,
                "DA TTC",
                f"{CrmState.kpis['purchases_count']:.0f} achat(s) référencé(s)",
                "package",
                "h-4 w-4 text-[#d8fa5e]",
            ),
            _tile(
                "Dettes fournisseurs",
                CrmState.payable_display,
                "DA",
                CrmState.payable_overdue_display + " DA en retard",
                "wallet",
                "h-4 w-4 text-[#ff8a5b]",
            ),
            _tile(
                "Paiements effectués",
                CrmState.paid_out_display,
                "DA",
                f"{CrmState.kpis['unpaid_purchase_invoices']:.0f} facture(s) impayée(s)",
                "credit-card",
                "h-4 w-4 text-[#a9c98b]",
            ),
            _tile(
                "Retards fournisseurs",
                f"{CrmState.kpis['late_purchase_invoices']:.0f}",
                "factures",
                "Factures d'achat au-delà de l'échéance",
                "triangle-alert",
                "h-4 w-4 text-[#ff8a5b]",
            ),
            _tile(
                "Nouveaux fournisseurs",
                f"{CrmState.kpis['suppliers_new']:.0f}",
                "90 jours",
                "Premières transactions récentes",
                "handshake",
                "h-4 w-4 text-[#d8fa5e]",
            ),
            class_name=(
                "grid grid-cols-1 gap-x-8 gap-y-7 sm:grid-cols-2 "
                "xl:grid-cols-3 w-full mt-5"
            ),
        ),
        class_name="w-full",
    )


def crm_commercial_kpis() -> rx.Component:
    return rx.el.section(
        _section_title(
            "Indicateurs commerciaux", "activity", "h-4 w-4 text-[#a9c98b]"
        ),
        rx.el.div(
            _tile(
                "CA du mois",
                CrmState.turnover_month_display,
                "DA TTC",
                CrmState.turnover_season_display + " DA sur la campagne",
                "calendar-days",
                "h-4 w-4 text-[#d8fa5e]",
            ),
            _tile(
                "Achats du mois",
                CrmState.purchases_month_display,
                "DA TTC",
                CrmState.purchases_season_display + " DA sur la campagne",
                "shopping-cart",
                "h-4 w-4 text-[#ff8a5b]",
            ),
            _tile(
                "Marge commerciale",
                CrmState.margin_display,
                "DA",
                CrmState.margin_label,
                "scale",
                "h-4 w-4 text-[#a9c98b]",
            ),
            _tile(
                "Taux de marge",
                f"{CrmState.kpis['margin_rate']:.1f}",
                "%",
                "Ventes moins achats de la campagne",
                "percent",
                "h-4 w-4 text-[#d8fa5e]",
            ),
            _tile(
                "Position nette",
                CrmState.net_cash_display,
                "DA",
                CrmState.cash_label,
                "landmark",
                "h-4 w-4 text-[#a9c98b]",
            ),
            _tile(
                "Limites de crédit",
                f"{CrmState.kpis['credit_alerts']:.0f}",
                "dépassées",
                "Encours client supérieur à la limite autorisée",
                "shield-alert",
                "h-4 w-4 text-[#ff8a5b]",
            ),
            class_name=(
                "grid grid-cols-1 gap-x-8 gap-y-7 sm:grid-cols-2 "
                "xl:grid-cols-3 w-full mt-5"
            ),
        ),
        class_name="w-full",
    )

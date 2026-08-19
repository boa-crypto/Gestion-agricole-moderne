import reflex as rx

from app.states.crm_state import CrmState


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


def _section_title(label: str, icon: str, icon_class: str) -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name=icon_class),
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-emerald-100/55",
        ),
        class_name="flex items-center gap-2 w-full",
    )


def crm_client_kpis() -> rx.Component:
    return rx.el.section(
        _section_title(
            "Indicateurs clients", "users-round", "h-4 w-4 text-lime-300"
        ),
        rx.el.div(
            _tile(
                "Clients suivis",
                f"{CrmState.kpis['clients']:.0f}",
                "tiers",
                f"{CrmState.kpis['clients_active']:.0f} actifs · {CrmState.kpis['clients_inactive']:.0f} inactifs",
                "users-round",
                "h-4 w-4 text-lime-300",
            ),
            _tile(
                "Nouveaux clients",
                f"{CrmState.kpis['clients_new']:.0f}",
                "90 jours",
                f"{CrmState.kpis['clients_blocked']:.0f} compte(s) bloqué(s)",
                "user-round-plus",
                "h-4 w-4 text-emerald-300",
            ),
            _tile(
                "CA clients",
                f"{CrmState.kpis['turnover']:.0f}",
                "DA TTC",
                f"{CrmState.kpis['sales_count']:.0f} vente(s) enregistrée(s)",
                "trending-up",
                "h-4 w-4 text-lime-300",
            ),
            _tile(
                "Créances clients",
                f"{CrmState.kpis['receivable']:.0f}",
                "DA",
                f"{CrmState.kpis['receivable_overdue']:.0f} DA échus",
                "hand-coins",
                "h-4 w-4 text-amber-300",
            ),
            _tile(
                "Paiements reçus",
                f"{CrmState.kpis['received']:.0f}",
                "DA",
                f"{CrmState.kpis['unpaid_sales_invoices']:.0f} facture(s) impayée(s)",
                "banknote",
                "h-4 w-4 text-emerald-300",
            ),
            _tile(
                "Factures en retard",
                f"{CrmState.kpis['late_sales_invoices']:.0f}",
                "clients",
                f"{CrmState.kpis['due_soon']:.0f} échéance(s) sous 15 jours",
                "alarm-clock",
                "h-4 w-4 text-amber-300",
            ),
            class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 w-full mt-4",
        ),
        class_name="w-full",
    )


def crm_supplier_kpis() -> rx.Component:
    return rx.el.section(
        _section_title(
            "Indicateurs fournisseurs", "truck", "h-4 w-4 text-amber-300"
        ),
        rx.el.div(
            _tile(
                "Fournisseurs suivis",
                f"{CrmState.kpis['suppliers']:.0f}",
                "tiers",
                f"{CrmState.kpis['suppliers_active']:.0f} actifs sur {CrmState.kpis['partners']:.0f} partenaires",
                "truck",
                "h-4 w-4 text-amber-300",
            ),
            _tile(
                "Achats totaux",
                f"{CrmState.kpis['purchases']:.0f}",
                "DA TTC",
                f"{CrmState.kpis['purchases_count']:.0f} achat(s) référencé(s)",
                "package",
                "h-4 w-4 text-lime-300",
            ),
            _tile(
                "Dettes fournisseurs",
                f"{CrmState.kpis['payable']:.0f}",
                "DA",
                f"{CrmState.kpis['payable_overdue']:.0f} DA en retard",
                "wallet",
                "h-4 w-4 text-amber-300",
            ),
            _tile(
                "Paiements effectués",
                f"{CrmState.kpis['paid_out']:.0f}",
                "DA",
                f"{CrmState.kpis['unpaid_purchase_invoices']:.0f} facture(s) impayée(s)",
                "credit-card",
                "h-4 w-4 text-emerald-300",
            ),
            _tile(
                "Retards fournisseurs",
                f"{CrmState.kpis['late_purchase_invoices']:.0f}",
                "factures",
                "Factures d'achat au-delà de l'échéance",
                "triangle-alert",
                "h-4 w-4 text-amber-300",
            ),
            _tile(
                "Nouveaux fournisseurs",
                f"{CrmState.kpis['suppliers_new']:.0f}",
                "90 jours",
                "Premières transactions récentes",
                "handshake",
                "h-4 w-4 text-lime-300",
            ),
            class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 w-full mt-4",
        ),
        class_name="w-full",
    )


def crm_commercial_kpis() -> rx.Component:
    return rx.el.section(
        _section_title(
            "Indicateurs commerciaux", "activity", "h-4 w-4 text-emerald-300"
        ),
        rx.el.div(
            _tile(
                "CA du mois",
                f"{CrmState.kpis['turnover_month']:.0f}",
                "DA TTC",
                f"{CrmState.kpis['turnover_season']:.0f} DA sur la campagne",
                "calendar-days",
                "h-4 w-4 text-lime-300",
            ),
            _tile(
                "Achats du mois",
                f"{CrmState.kpis['purchases_month']:.0f}",
                "DA TTC",
                f"{CrmState.kpis['purchases_season']:.0f} DA sur la campagne",
                "shopping-cart",
                "h-4 w-4 text-amber-300",
            ),
            _tile(
                "Marge commerciale",
                f"{CrmState.kpis['margin']:.0f}",
                "DA",
                CrmState.margin_label,
                "scale",
                "h-4 w-4 text-emerald-300",
            ),
            _tile(
                "Taux de marge",
                f"{CrmState.kpis['margin_rate']:.1f}",
                "%",
                "Ventes moins achats de la campagne",
                "percent",
                "h-4 w-4 text-lime-300",
            ),
            _tile(
                "Position nette",
                f"{CrmState.kpis['net_cash']:.0f}",
                "DA",
                CrmState.cash_label,
                "landmark",
                "h-4 w-4 text-emerald-300",
            ),
            _tile(
                "Limites de crédit",
                f"{CrmState.kpis['credit_alerts']:.0f}",
                "dépassées",
                "Encours client supérieur à la limite autorisée",
                "shield-alert",
                "h-4 w-4 text-amber-300",
            ),
            class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 w-full mt-4",
        ),
        class_name="w-full",
    )

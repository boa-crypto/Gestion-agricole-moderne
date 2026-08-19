import reflex as rx

from app.states.crm_partners_state import (
    ContactRow,
    CrmPartnersState,
    DocumentRow,
    EventRow,
    InvoiceRow,
    PaymentRow,
    SettlementRow,
    TxRow,
)


def _chip(label: rx.Var | str, icon: str = "link") -> rx.Component:
    return rx.el.div(
        rx.icon(icon, class_name="h-3 w-3 text-lime-300 shrink-0"),
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold text-emerald-100/65 truncate",
        ),
        class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 w-fit max-w-full min-w-0",
    )


def _link_chips(links: rx.Var) -> rx.Component:
    return rx.cond(
        links.length() > 0,
        rx.el.div(
            rx.foreach(links, lambda item: _chip(item, "sprout")),
            class_name="flex flex-wrap items-center gap-1.5 mt-2.5",
        ),
        rx.el.p(
            "Aucun lien agricole rattaché à cette opération.",
            class_name="text-[10px] font-medium text-emerald-100/35 mt-2.5",
        ),
    )


def _field(label: str, value: rx.Var | str, icon: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-lime-300 shrink-0"),
            rx.el.span(
                label,
                class_name="text-[9px] font-semibold uppercase tracking-[0.2em] text-emerald-100/40",
            ),
            class_name="flex items-center gap-1.5",
        ),
        rx.el.p(
            value,
            class_name="text-xs font-semibold text-emerald-50 mt-1.5 break-words",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-3",
    )


def _kpi(label: str, value: rx.Var | str, unit: str, tone: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="text-[9px] font-semibold uppercase tracking-[0.2em] text-emerald-100/40",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="font-['Instrument_Serif'] text-2xl leading-none",
            ),
            rx.el.span(
                unit,
                class_name="text-[10px] font-medium text-emerald-100/45 mb-0.5",
            ),
            class_name=f"flex items-end gap-1.5 mt-2 {tone}",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.04] p-4",
    )


def _detail_tab(item: dict) -> rx.Component:
    return rx.el.button(
        rx.icon(
            item["icon"],
            class_name=rx.cond(
                CrmPartnersState.detail_tab == item["key"],
                "h-3.5 w-3.5 stroke-[#04140d]",
                "h-3.5 w-3.5 stroke-emerald-100/60",
            ),
        ),
        rx.el.span(
            item["label"],
            class_name=rx.cond(
                CrmPartnersState.detail_tab == item["key"],
                "text-[11px] font-semibold text-[#04140d]",
                "text-[11px] font-semibold text-emerald-100/65",
            ),
        ),
        type="button",
        on_click=CrmPartnersState.set_detail_tab(item["key"]),
        class_name=rx.cond(
            CrmPartnersState.detail_tab == item["key"],
            "flex items-center gap-2 rounded-full bg-lime-300 px-3.5 py-1.5 transition-colors w-fit",
            "flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3.5 py-1.5 hover:border-lime-300/35 transition-colors w-fit",
        ),
    )


def _header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        CrmPartnersState.detail["kind_label"],
                        class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/85",
                    ),
                    rx.el.span(
                        CrmPartnersState.detail["status_label"],
                        class_name="rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-100/65 w-fit",
                    ),
                    class_name="flex flex-wrap items-center gap-2",
                ),
                rx.el.h2(
                    CrmPartnersState.detail["name"],
                    class_name="font-['Instrument_Serif'] text-3xl md:text-4xl leading-tight text-emerald-50 mt-2",
                ),
                rx.el.p(
                    f"{CrmPartnersState.detail['code']} · {CrmPartnersState.detail['legal_form_label']} · {CrmPartnersState.detail['city']}",
                    class_name="text-xs font-medium text-emerald-100/50 mt-1.5",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("pencil", class_name="h-3.5 w-3.5"),
                    rx.el.span("Modifier", class_name="text-xs font-semibold"),
                    type="button",
                    on_click=CrmPartnersState.open_edit,
                    class_name="flex items-center gap-2 rounded-full bg-lime-300 px-3.5 py-1.5 text-[#04140d] hover:bg-lime-200 transition-colors w-fit",
                ),
                rx.cond(
                    CrmPartnersState.detail["is_archived"],
                    rx.el.button(
                        rx.icon(
                            "rotate-ccw",
                            class_name="h-3.5 w-3.5 text-emerald-100/70",
                        ),
                        rx.el.span(
                            "Réactiver",
                            class_name="text-xs font-semibold text-emerald-100/70",
                        ),
                        type="button",
                        on_click=CrmPartnersState.restore_partner,
                        class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3.5 py-1.5 hover:border-lime-300/35 transition-colors w-fit",
                    ),
                    rx.el.button(
                        rx.icon(
                            "archive",
                            class_name="h-3.5 w-3.5 text-amber-200",
                        ),
                        rx.el.span(
                            "Archiver",
                            class_name="text-xs font-semibold text-amber-200",
                        ),
                        type="button",
                        on_click=CrmPartnersState.archive_partner,
                        class_name="flex items-center gap-2 rounded-full border border-amber-300/30 bg-amber-300/[0.08] px-3.5 py-1.5 hover:border-amber-300/50 transition-colors w-fit",
                    ),
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col lg:flex-row lg:items-start justify-between gap-4 w-full",
        ),
        rx.el.p(
            CrmPartnersState.archive_hint,
            class_name="text-[11px] font-medium text-amber-200/70 mt-3",
        ),
        rx.el.div(
            _kpi(
                "Chiffre d'affaires",
                f"{CrmPartnersState.stats['turnover']:.0f}",
                "DA",
                "text-lime-200",
            ),
            _kpi(
                "Achats",
                f"{CrmPartnersState.stats['purchases']:.0f}",
                "DA",
                "text-amber-200",
            ),
            _kpi(
                "Créances",
                f"{CrmPartnersState.stats['receivable']:.0f}",
                "DA",
                "text-emerald-100",
            ),
            _kpi(
                "Dettes",
                f"{CrmPartnersState.stats['payable']:.0f}",
                "DA",
                "text-emerald-100",
            ),
            _kpi(
                "Marge",
                f"{CrmPartnersState.stats['margin']:.0f}",
                "DA",
                "text-lime-200",
            ),
            _kpi(
                "Encours / limite",
                f"{CrmPartnersState.stats['credit_usage']:.1f}",
                "%",
                "text-amber-200",
            ),
            class_name="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3 w-full mt-5",
        ),
        rx.el.nav(
            rx.foreach(CrmPartnersState.detail_tabs, _detail_tab),
            class_name="flex flex-wrap items-center gap-2 w-full mt-5 border-t border-white/10 pt-5",
        ),
        class_name="w-full",
    )


def _identity() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _field(
                "Nom commercial",
                CrmPartnersState.detail["trade_name"],
                "signature",
            ),
            _field("Catégorie", CrmPartnersState.detail["category"], "tags"),
            _field("Segment", CrmPartnersState.detail["segment"], "layers"),
            _field(
                "Filière fournisseur",
                CrmPartnersState.detail["supplier_domain"],
                "package",
            ),
            _field("Adresse", CrmPartnersState.detail["address"], "map-pin"),
            _field("Pays", CrmPartnersState.detail["country"], "globe"),
            _field("Téléphone", CrmPartnersState.detail["phone"], "phone"),
            _field(
                "Téléphone secondaire",
                CrmPartnersState.detail["phone_secondary"],
                "phone-call",
            ),
            _field(
                "WhatsApp",
                CrmPartnersState.detail["whatsapp"],
                "message-circle",
            ),
            _field("E-mail", CrmPartnersState.detail["email"], "mail"),
            _field("Site web", CrmPartnersState.detail["website"], "link"),
            _field("NIF", CrmPartnersState.detail["nif"], "file-badge"),
            _field("NIS", CrmPartnersState.detail["nis"], "file-badge"),
            _field(
                "Registre de commerce",
                CrmPartnersState.detail["trade_register"],
                "scroll-text",
            ),
            _field(
                "Identifiant fiscal",
                CrmPartnersState.detail["tax_id"],
                "receipt",
            ),
            _field(
                "Conditions de paiement",
                CrmPartnersState.detail["payment_terms"],
                "handshake",
            ),
            _field(
                "Délai de paiement",
                f"{CrmPartnersState.detail['payment_delay_days']} jours",
                "clock",
            ),
            _field(
                "Limite de crédit",
                f"{CrmPartnersState.detail['credit_limit']:.0f} {CrmPartnersState.detail['currency']}",
                "shield-alert",
            ),
            _field(
                "Remise habituelle",
                f"{CrmPartnersState.detail['discount_percent']:.1f} %",
                "percent",
            ),
            _field(
                "TVA par défaut",
                f"{CrmPartnersState.detail['vat_rate']:.1f} %",
                "calculator",
            ),
            _field(
                "Mode de paiement",
                CrmPartnersState.detail["payment_method"],
                "credit-card",
            ),
            _field(
                "Contact principal",
                f"{CrmPartnersState.detail['primary_contact']} · {CrmPartnersState.detail['primary_contact_role']}",
                "user-round",
            ),
            _field(
                "Première transaction",
                CrmPartnersState.detail["first_deal"],
                "calendar-plus",
            ),
            _field(
                "Dernière activité",
                CrmPartnersState.detail["last_activity"],
                "activity",
            ),
            class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 w-full",
        ),
        rx.el.div(
            rx.el.p(
                "Ancrage agricole",
                class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
            ),
            rx.el.div(
                rx.cond(
                    CrmPartnersState.detail["main_parcel"] != "",
                    _chip(
                        f"Parcelle · {CrmPartnersState.detail['main_parcel']}",
                        "map",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    CrmPartnersState.detail["main_culture"] != "",
                    _chip(
                        f"Culture · {CrmPartnersState.detail['main_culture']}",
                        "sprout",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    CrmPartnersState.detail["main_product"] != "",
                    _chip(
                        f"Produit · {CrmPartnersState.detail['main_product']}",
                        "package",
                    ),
                    rx.fragment(),
                ),
                _chip(
                    f"Score {CrmPartnersState.score['total']}/100 · {CrmPartnersState.score['grade_label']}",
                    "gauge",
                ),
                class_name="flex flex-wrap items-center gap-2 mt-3",
            ),
            rx.cond(
                CrmPartnersState.detail["notes"] != "",
                rx.el.p(
                    CrmPartnersState.detail["notes"],
                    class_name="text-[11px] font-medium text-emerald-100/55 mt-4 leading-relaxed",
                ),
                rx.fragment(),
            ),
            class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 mt-4",
        ),
        _score_panel(),
        class_name="flex flex-col gap-4 w-full",
    )


def _score_bar(label: str, value: rx.Var, maximum: int) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                label,
                class_name="text-[10px] font-semibold text-emerald-100/60",
            ),
            rx.el.span(
                f"{value}/{maximum}",
                class_name="text-[10px] font-bold text-emerald-50 ml-auto",
            ),
            class_name="flex items-center gap-2 w-full",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-1.5 rounded-full bg-gradient-to-r from-emerald-400 to-lime-300",
                style={"width": f"{value / maximum * 100}%"},
            ),
            class_name="h-1.5 w-full rounded-full bg-white/[0.06] mt-1.5",
        ),
        class_name="w-full",
    )


def _score_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("gauge", class_name="h-4 w-4 text-lime-300"),
            rx.el.span(
                "Scoring du tiers",
                class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
            ),
            rx.el.span(
                CrmPartnersState.score_label,
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/65 w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.el.div(
            _score_bar("Volume", CrmPartnersState.score["volume"], 25),
            _score_bar("Fréquence", CrmPartnersState.score["frequency"], 15),
            _score_bar("Ancienneté", CrmPartnersState.score["seniority"], 10),
            _score_bar(
                "Ponctualité", CrmPartnersState.score["punctuality"], 20
            ),
            _score_bar(
                "Rentabilité", CrmPartnersState.score["profitability"], 15
            ),
            _score_bar("Croissance", CrmPartnersState.score["growth"], 15),
            _score_bar("Qualité", CrmPartnersState.score["quality"], 20),
            _score_bar(
                "Délai livraison", CrmPartnersState.score["lead_time"], 15
            ),
            _score_bar("Fiabilité", CrmPartnersState.score["reliability"], 15),
            class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 w-full mt-4",
        ),
        rx.el.div(
            _chip(
                f"Délai moyen de paiement · {CrmPartnersState.score['average_delay']:.0f} j",
                "clock",
            ),
            _chip(
                f"Transactions · {CrmPartnersState.score['transactions']}",
                "receipt",
            ),
            _chip(
                f"Incidents · {CrmPartnersState.score['incidents']}",
                "triangle-alert",
            ),
            _chip(
                f"Calculé le {CrmPartnersState.score['computed_on']}",
                "calendar-days",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-4",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4",
    )


def _contact_card(item: ContactRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    item["name"],
                    class_name="text-sm font-semibold text-emerald-50 truncate",
                ),
                rx.el.p(
                    item["role"],
                    class_name="text-[10px] font-medium text-emerald-100/45 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.cond(
                item["is_primary"],
                rx.el.span(
                    "Contact principal",
                    class_name="rounded-full border border-lime-300/30 bg-lime-300/10 px-2.5 py-0.5 text-[10px] font-semibold text-lime-200 w-fit shrink-0",
                ),
                rx.el.button(
                    "Définir principal",
                    type="button",
                    on_click=CrmPartnersState.set_primary_contact(item["id"]),
                    class_name="rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-100/60 hover:border-lime-300/35 transition-colors w-fit shrink-0",
                ),
            ),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        rx.el.div(
            _chip(item["phone"], "phone"),
            _chip(item["mobile"], "smartphone"),
            _chip(item["email"], "mail"),
            _chip(item["whatsapp"], "message-circle"),
            class_name="flex flex-wrap items-center gap-1.5 mt-3",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("pencil", class_name="h-3 w-3 text-emerald-100/60"),
                rx.el.span(
                    "Modifier",
                    class_name="text-[10px] font-semibold text-emerald-100/60",
                ),
                type="button",
                on_click=CrmPartnersState.open_contact_edit(item["id"]),
                class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 hover:border-lime-300/35 transition-colors w-fit",
            ),
            rx.el.button(
                rx.icon("archive", class_name="h-3 w-3 text-amber-200"),
                rx.el.span(
                    "Archiver",
                    class_name="text-[10px] font-semibold text-amber-200",
                ),
                type="button",
                on_click=CrmPartnersState.archive_contact(item["id"]),
                class_name="flex items-center gap-1.5 rounded-full border border-amber-300/25 bg-amber-300/[0.06] px-2.5 py-1 hover:border-amber-300/45 transition-colors w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-3",
        ),
        key=item["id"].to_string(),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4",
    )


def _contacts() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("users-round", class_name="h-4 w-4 text-lime-300"),
            rx.el.span(
                "Contacts du tiers",
                class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
            ),
            rx.el.button(
                rx.icon("plus", class_name="h-3.5 w-3.5"),
                rx.el.span(
                    "Nouveau contact", class_name="text-xs font-semibold"
                ),
                type="button",
                on_click=CrmPartnersState.open_contact_create,
                class_name="flex items-center gap-2 rounded-full bg-lime-300 px-3.5 py-1.5 text-[#04140d] hover:bg-lime-200 transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.cond(
            CrmPartnersState.contacts.length() > 0,
            rx.el.div(
                rx.foreach(CrmPartnersState.contacts, _contact_card),
                class_name="grid grid-cols-1 lg:grid-cols-2 gap-3 w-full mt-4",
            ),
            rx.el.p(
                "Aucun contact enregistré : ajoutez le contact principal du tiers.",
                class_name="text-sm font-medium text-emerald-100/50 mt-4",
            ),
        ),
        class_name="w-full",
    )


def _tx_card(item: TxRow, tone: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    item["label"],
                    class_name="text-sm font-semibold text-emerald-50 truncate",
                ),
                rx.el.p(
                    f"{item['code']} · {item['date']} · {item['status_label']}",
                    class_name="text-[10px] font-medium text-emerald-100/45 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                rx.el.span(f"{item['amount']:.0f} DA", class_name=tone),
                rx.el.span(
                    f"Reste {item['remaining']:.0f} DA",
                    class_name="text-[10px] font-medium text-emerald-100/45 text-right",
                ),
                class_name="flex flex-col shrink-0",
            ),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        _link_chips(item["links"]),
        key=item["id"].to_string(),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4",
    )


def _transactions() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("trending-up", class_name="h-4 w-4 text-lime-300"),
                rx.el.span(
                    "Ventes du tiers",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                ),
                rx.el.span(
                    f"{CrmPartnersState.stats['sales_count']:.0f} opération(s)",
                    class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit ml-auto",
                ),
                class_name="flex flex-wrap items-center gap-2 w-full",
            ),
            rx.cond(
                CrmPartnersState.sales.length() > 0,
                rx.el.div(
                    rx.foreach(
                        CrmPartnersState.sales,
                        lambda item: _tx_card(
                            item, "text-xs font-bold text-lime-200 text-right"
                        ),
                    ),
                    class_name="flex flex-col gap-3 w-full mt-4",
                ),
                rx.el.p(
                    "Aucune vente rattachée à ce tiers.",
                    class_name="text-sm font-medium text-emerald-100/50 mt-4",
                ),
            ),
            class_name="w-full",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("truck", class_name="h-4 w-4 text-amber-300"),
                rx.el.span(
                    "Achats auprès du tiers",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-amber-300/80",
                ),
                rx.el.span(
                    f"{CrmPartnersState.stats['purchases_count']:.0f} opération(s)",
                    class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit ml-auto",
                ),
                class_name="flex flex-wrap items-center gap-2 w-full",
            ),
            rx.cond(
                CrmPartnersState.purchases.length() > 0,
                rx.el.div(
                    rx.foreach(
                        CrmPartnersState.purchases,
                        lambda item: _tx_card(
                            item, "text-xs font-bold text-amber-200 text-right"
                        ),
                    ),
                    class_name="flex flex-col gap-3 w-full mt-4",
                ),
                rx.el.p(
                    "Aucun achat rattaché à ce tiers.",
                    class_name="text-sm font-medium text-emerald-100/50 mt-4",
                ),
            ),
            class_name="w-full mt-6 border-t border-white/10 pt-6",
        ),
        class_name="w-full",
    )


def _invoice_row(item: InvoiceRow) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            item["code"],
            class_name="px-3 py-2.5 text-xs font-semibold text-emerald-50 whitespace-nowrap",
        ),
        rx.el.td(
            item["kind_label"],
            class_name="px-3 py-2.5 text-xs font-medium text-emerald-100/60 whitespace-nowrap",
        ),
        rx.el.td(
            item["issue_date"],
            class_name="px-3 py-2.5 text-xs font-medium text-emerald-100/60 whitespace-nowrap",
        ),
        rx.el.td(
            item["due_date"],
            class_name="px-3 py-2.5 text-xs font-medium text-emerald-100/60 whitespace-nowrap",
        ),
        rx.el.td(
            f"{item['amount']:.0f} DA",
            class_name="px-3 py-2.5 text-xs font-bold text-lime-200 text-right whitespace-nowrap",
        ),
        rx.el.td(
            f"{item['remaining']:.0f} DA",
            class_name="px-3 py-2.5 text-xs font-bold text-amber-200 text-right whitespace-nowrap",
        ),
        rx.el.td(
            item["status_label"],
            class_name="px-3 py-2.5 text-xs font-medium text-emerald-100/60 whitespace-nowrap",
        ),
        key=item["id"].to_string(),
        class_name="border-t border-white/[0.06] even:bg-white/[0.02]",
    )


def _payment_row(item: PaymentRow) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            item["code"],
            class_name="px-3 py-2.5 text-xs font-semibold text-emerald-50 whitespace-nowrap",
        ),
        rx.el.td(
            item["direction_label"],
            class_name="px-3 py-2.5 text-xs font-medium text-emerald-100/60 whitespace-nowrap",
        ),
        rx.el.td(
            item["date"],
            class_name="px-3 py-2.5 text-xs font-medium text-emerald-100/60 whitespace-nowrap",
        ),
        rx.el.td(
            item["invoice_code"],
            class_name="px-3 py-2.5 text-xs font-medium text-emerald-100/60 whitespace-nowrap",
        ),
        rx.el.td(
            item["method"],
            class_name="px-3 py-2.5 text-xs font-medium text-emerald-100/60 whitespace-nowrap",
        ),
        rx.el.td(
            f"{item['amount']:.0f} DA",
            class_name="px-3 py-2.5 text-xs font-bold text-lime-200 text-right whitespace-nowrap",
        ),
        key=item["id"].to_string(),
        class_name="border-t border-white/[0.06] even:bg-white/[0.02]",
    )


def _settlement_row(item: SettlementRow) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            item["invoice_code"],
            class_name="px-3 py-2.5 text-xs font-semibold text-emerald-50 whitespace-nowrap",
        ),
        rx.el.td(
            item["due_date"],
            class_name="px-3 py-2.5 text-xs font-medium text-emerald-100/60 whitespace-nowrap",
        ),
        rx.el.td(
            f"{item['amount_due']:.0f} DA",
            class_name="px-3 py-2.5 text-xs font-medium text-emerald-100/70 text-right whitespace-nowrap",
        ),
        rx.el.td(
            f"{item['remaining']:.0f} DA",
            class_name="px-3 py-2.5 text-xs font-bold text-amber-200 text-right whitespace-nowrap",
        ),
        rx.el.td(
            f"{item['overdue_days']} j",
            class_name="px-3 py-2.5 text-xs font-medium text-emerald-100/60 text-right whitespace-nowrap",
        ),
        rx.el.td(
            f"{item['status_label']} · {item['bucket']}",
            class_name="px-3 py-2.5 text-xs font-medium text-emerald-100/60 whitespace-nowrap",
        ),
        key=item["id"].to_string(),
        class_name="border-t border-white/[0.06] even:bg-white/[0.02]",
    )


def _header_cells(headers: list[str]) -> list[rx.Component]:
    """Cellules d'en-tête (retourne une liste, pas un composant)."""
    return [
        rx.el.th(
            header,
            class_name="px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-100/45 text-left whitespace-nowrap",
        )
        for header in headers
    ]


def _table(
    title: str, icon: str, headers: list[str], body: rx.Component
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-lime-300"),
            rx.el.span(
                title,
                class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
            ),
            class_name="flex items-center gap-2 w-full",
        ),
        rx.el.div(
            rx.el.table(
                rx.el.thead(rx.el.tr(*_header_cells(headers))),
                body,
                class_name="table-auto w-full min-w-[38rem]",
            ),
            class_name="w-full overflow-x-auto overflow-hidden rounded-2xl border border-white/10 bg-white/[0.02] mt-3",
        ),
        class_name="w-full",
    )


def _finance() -> rx.Component:
    return rx.el.div(
        _table(
            "Factures",
            "receipt",
            [
                "Facture",
                "Nature",
                "Émission",
                "Échéance",
                "Montant",
                "Restant",
                "Statut",
            ],
            rx.el.tbody(rx.foreach(CrmPartnersState.invoices, _invoice_row)),
        ),
        _table(
            "Créances clients",
            "hand-coins",
            ["Facture", "Échéance", "Dû", "Restant", "Retard", "Statut"],
            rx.el.tbody(
                rx.foreach(CrmPartnersState.receivables, _settlement_row)
            ),
        ),
        _table(
            "Dettes fournisseurs",
            "wallet",
            ["Facture", "Échéance", "Dû", "Restant", "Retard", "Statut"],
            rx.el.tbody(rx.foreach(CrmPartnersState.payables, _settlement_row)),
        ),
        _table(
            "Paiements",
            "banknote",
            ["Pièce", "Sens", "Date", "Facture", "Mode", "Montant"],
            rx.el.tbody(rx.foreach(CrmPartnersState.payments, _payment_row)),
        ),
        class_name="flex flex-col gap-6 w-full",
    )


def _document_card(item: DocumentRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    item["title"],
                    class_name="text-sm font-semibold text-emerald-50 truncate",
                ),
                rx.el.p(
                    f"{item['kind_label']} · {item['issued_on']} · {item['reference']}",
                    class_name="text-[10px] font-medium text-emerald-100/45 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.button(
                rx.icon("archive", class_name="h-3 w-3 text-amber-200"),
                rx.el.span(
                    "Archiver",
                    class_name="text-[10px] font-semibold text-amber-200",
                ),
                type="button",
                on_click=CrmPartnersState.archive_document(item["id"]),
                class_name="flex items-center gap-1.5 rounded-full border border-amber-300/25 bg-amber-300/[0.06] px-2.5 py-1 hover:border-amber-300/45 transition-colors w-fit shrink-0",
            ),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        rx.cond(
            item["links"].length() > 0,
            rx.el.div(
                rx.foreach(
                    item["links"], lambda label: _chip(label, "paperclip")
                ),
                class_name="flex flex-wrap items-center gap-1.5 mt-2.5",
            ),
            rx.fragment(),
        ),
        rx.cond(
            item["notes"] != "",
            rx.el.p(
                item["notes"],
                class_name="text-[10px] font-medium text-emerald-100/50 mt-2.5",
            ),
            rx.fragment(),
        ),
        key=item["id"].to_string(),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4",
    )


def _documents() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("folder-open", class_name="h-4 w-4 text-lime-300"),
            rx.el.span(
                "Espace documentaire",
                class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
            ),
            rx.el.button(
                rx.icon("plus", class_name="h-3.5 w-3.5"),
                rx.el.span(
                    "Nouveau document", class_name="text-xs font-semibold"
                ),
                type="button",
                on_click=CrmPartnersState.open_document_form,
                class_name="flex items-center gap-2 rounded-full bg-lime-300 px-3.5 py-1.5 text-[#04140d] hover:bg-lime-200 transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.cond(
            CrmPartnersState.documents.length() > 0,
            rx.el.div(
                rx.foreach(CrmPartnersState.documents, _document_card),
                class_name="grid grid-cols-1 lg:grid-cols-2 gap-3 w-full mt-4",
            ),
            rx.el.p(
                "Aucun document classé pour ce tiers.",
                class_name="text-sm font-medium text-emerald-100/50 mt-4",
            ),
        ),
        class_name="w-full",
    )


def _event_card(item: EventRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(item["icon"], class_name="h-3.5 w-3.5 text-lime-300"),
                class_name="flex h-8 w-8 items-center justify-center rounded-full border border-lime-300/25 bg-lime-300/10 shrink-0",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.p(
                        item["title"],
                        class_name="text-sm font-semibold text-emerald-50",
                    ),
                    rx.el.span(
                        item["date"],
                        class_name="text-[10px] font-semibold text-emerald-100/45 ml-auto shrink-0",
                    ),
                    class_name="flex items-start gap-3 w-full min-w-0",
                ),
                rx.el.p(
                    item["summary"],
                    class_name="text-[11px] font-medium text-emerald-100/55 mt-1 leading-relaxed",
                ),
                rx.el.div(
                    _chip(item["kind_label"], "tag"),
                    rx.cond(
                        item["amount"] > 0,
                        _chip(f"{item['amount']:.0f} DA", "coins"),
                        rx.fragment(),
                    ),
                    rx.foreach(
                        item["links"], lambda label: _chip(label, "sprout")
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 mt-2.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        key=item["id"].to_string(),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4",
    )


def _history() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("history", class_name="h-4 w-4 text-lime-300"),
            rx.el.span(
                "Historique 360°",
                class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
            ),
            rx.el.span(
                f"{CrmPartnersState.events.length()} événement(s)",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/60 w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.cond(
            CrmPartnersState.events.length() > 0,
            rx.el.div(
                rx.foreach(CrmPartnersState.events, _event_card),
                class_name="flex flex-col gap-3 w-full mt-4 border-l border-white/10 pl-4",
            ),
            rx.el.p(
                "L'historique se remplira dès la première opération enregistrée.",
                class_name="text-sm font-medium text-emerald-100/50 mt-4",
            ),
        ),
        class_name="w-full",
    )


def crm_partner_detail() -> rx.Component:
    return rx.el.section(
        rx.cond(
            CrmPartnersState.has_selection,
            rx.el.div(
                _header(),
                rx.el.div(
                    rx.match(
                        CrmPartnersState.detail_tab,
                        ("identite", _identity()),
                        ("contacts", _contacts()),
                        ("transactions", _transactions()),
                        ("finance", _finance()),
                        ("documents", _documents()),
                        ("historique", _history()),
                        _identity(),
                    ),
                    class_name="w-full mt-6",
                ),
                class_name="w-full",
            ),
            rx.el.div(
                rx.icon(
                    "contact-round",
                    class_name="h-8 w-8 text-emerald-100/30",
                ),
                rx.el.p(
                    "Sélectionnez un tiers pour ouvrir sa fiche 360°",
                    class_name="text-sm font-semibold text-emerald-100/60 mt-3",
                ),
                rx.el.p(
                    "Identité, contacts, ventes, achats, factures, règlements, documents et historique complet.",
                    class_name="text-[11px] font-medium text-emerald-100/40 mt-1 text-center max-w-md",
                ),
                class_name="flex flex-col items-center justify-center py-24 w-full",
            ),
        ),
        class_name="flex-1 min-w-0 rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )

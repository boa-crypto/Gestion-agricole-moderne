import reflex as rx

from app.components.crm_register_forms import crm_register_form
from app.states.crm_registers_state import (
    CrmRegistersState,
    RegisterRow,
    ReportMonth,
    ReportPartner,
)


def _badge(row: RegisterRow) -> rx.Component:
    return rx.el.span(
        row["status_label"],
        class_name=rx.match(
            row["tone"],
            (
                "good",
                "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2.5 py-0.5 text-[10px] font-semibold text-[#e4ff9b] w-fit whitespace-nowrap",
            ),
            (
                "warn",
                "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2.5 py-0.5 text-[10px] font-semibold text-[#ffb894] w-fit whitespace-nowrap",
            ),
            (
                "bad",
                "rounded-none border border-[#ff6b5a]/30 bg-[#ff6b5a]/10 px-2.5 py-0.5 text-[10px] font-semibold text-[#ffbcb0] w-fit whitespace-nowrap",
            ),
            "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2.5 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/65 w-fit whitespace-nowrap",
        ),
    )


def _kpi(label: str, value: rx.Var | str, unit: str, tone: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="ap-eyebrow text-[#c9c5b4]/40",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="ap-serif text-2xl leading-none",
            ),
            rx.el.span(
                unit,
                class_name="text-[10px] font-medium text-[#c9c5b4]/45 mb-0.5",
            ),
            class_name=f"flex items-end gap-1.5 mt-2 {tone}",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#14160f] p-4",
    )


def crm_register_kpis() -> rx.Component:
    return rx.el.div(
        _kpi(
            "Lignes",
            f"{CrmRegistersState.totals['count']:.0f}",
            "pièce(s)",
            "text-[#f2efe4]",
        ),
        _kpi(
            CrmRegistersState.amount_header,
            f"{CrmRegistersState.totals['amount_ht']:.0f}",
            "DA",
            "text-[#c9c5b4]",
        ),
        _kpi(
            "TVA",
            f"{CrmRegistersState.totals['vat_amount']:.0f}",
            "DA",
            "text-[#c9c5b4]",
        ),
        _kpi(
            "TTC",
            f"{CrmRegistersState.totals['amount_ttc']:.0f}",
            "DA",
            "text-[#e4ff9b]",
        ),
        _kpi(
            "Réglé",
            f"{CrmRegistersState.totals['paid']:.0f}",
            "DA",
            "text-[#e4ff9b]",
        ),
        _kpi(
            "Restant dû",
            f"{CrmRegistersState.totals['remaining']:.0f}",
            "DA",
            "text-[#ffb894]",
        ),
        _kpi(
            "En retard",
            f"{CrmRegistersState.totals['overdue_amount']:.0f}",
            "DA",
            "text-[#ffbcb0]",
        ),
        _kpi(
            "Archivées",
            f"{CrmRegistersState.totals['archived']:.0f}",
            "pièce(s)",
            "text-[#c9c5b4]/70",
        ),
        class_name="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-3 w-full",
    )


def _select(
    label: rx.Var | str,
    value: rx.Var,
    options: rx.Var,
    placeholder: str,
    on_change: rx.event.EventType,
) -> rx.Component:
    return rx.el.label(
        rx.el.span(
            label,
            class_name="ap-eyebrow text-[#c9c5b4]/45",
        ),
        rx.el.div(
            rx.el.select(
                rx.el.option(placeholder, value=""),
                rx.foreach(
                    options,
                    lambda item: rx.el.option(
                        item.replace("_", " ").lower(), value=item
                    ),
                ),
                value=value,
                on_change=on_change,
                class_name="w-full appearance-none rounded-none border border-[#f2efe4]/12 bg-[#16190f] px-3 py-2 pr-9 text-xs font-semibold capitalize text-[#f2efe4] focus:border-[#d8fa5e]/40 focus:outline-hidden",
            ),
            rx.icon(
                "chevron-down",
                class_name="pointer-events-none absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#c9c5b4]/50",
            ),
            class_name="relative w-full mt-1.5",
        ),
        class_name="flex flex-col w-full min-w-0",
    )


def _period_select() -> rx.Component:
    return rx.el.label(
        rx.el.span(
            "Période",
            class_name="ap-eyebrow text-[#c9c5b4]/45",
        ),
        rx.el.div(
            rx.el.select(
                rx.foreach(
                    CrmRegistersState.periods,
                    lambda item: rx.el.option(item[1], value=item[0]),
                ),
                value=CrmRegistersState.period,
                on_change=CrmRegistersState.set_period,
                class_name="w-full appearance-none rounded-none border border-[#f2efe4]/12 bg-[#16190f] px-3 py-2 pr-9 text-xs font-semibold text-[#f2efe4] focus:border-[#d8fa5e]/40 focus:outline-hidden",
            ),
            rx.icon(
                "chevron-down",
                class_name="pointer-events-none absolute right-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#c9c5b4]/50",
            ),
            class_name="relative w-full mt-1.5",
        ),
        class_name="flex flex-col w-full min-w-0",
    )


def crm_register_toolbar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("scroll-text", class_name="h-4 w-4 text-[#d8fa5e]"),
                    rx.el.h2(
                        CrmRegistersState.register_title,
                        class_name="ap-serif text-2xl text-[#f2efe4]",
                    ),
                    rx.el.span(
                        f"{CrmRegistersState.row_count} ligne(s)",
                        class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2.5 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
                    ),
                    class_name="flex flex-wrap items-center gap-2 min-w-0",
                ),
                rx.el.p(
                    CrmRegistersState.register_subtitle,
                    class_name="text-xs font-medium text-[#c9c5b4]/50 mt-1.5 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.cond(
                    CrmRegistersState.can_create,
                    rx.el.button(
                        rx.icon("plus", class_name="h-3.5 w-3.5"),
                        rx.el.span(
                            CrmRegistersState.create_label,
                            class_name="text-xs font-semibold",
                        ),
                        type="button",
                        on_click=CrmRegistersState.open_form,
                        class_name="flex items-center gap-2 rounded-none bg-[#d8fa5e] px-3.5 py-1.5 text-[#0A0A08] hover:bg-[#e4ff9b] transition-colors w-fit",
                    ),
                    rx.fragment(),
                ),
                rx.el.button(
                    rx.icon(
                        "file-spreadsheet",
                        class_name="h-3.5 w-3.5 text-[#c9c5b4]/70",
                    ),
                    rx.el.span(
                        "Export CSV",
                        class_name="text-xs font-semibold text-[#c9c5b4]/70",
                    ),
                    type="button",
                    on_click=CrmRegistersState.export_csv,
                    class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3.5 py-1.5 hover:border-[#d8fa5e]/35 transition-colors w-fit",
                ),
                rx.el.button(
                    rx.icon(
                        "file-text",
                        class_name="h-3.5 w-3.5 text-[#c9c5b4]/70",
                    ),
                    rx.el.span(
                        "Export texte",
                        class_name="text-xs font-semibold text-[#c9c5b4]/70",
                    ),
                    type="button",
                    on_click=CrmRegistersState.export_text,
                    class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3.5 py-1.5 hover:border-[#d8fa5e]/35 transition-colors w-fit",
                ),
                rx.el.button(
                    rx.cond(
                        CrmRegistersState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-3.5 w-3.5 animate-spin text-[#c9c5b4]/70",
                        ),
                        rx.icon(
                            "refresh-cw",
                            class_name="h-3.5 w-3.5 text-[#c9c5b4]/70",
                        ),
                    ),
                    rx.el.span(
                        "Actualiser",
                        class_name="text-xs font-semibold text-[#c9c5b4]/70",
                    ),
                    type="button",
                    on_click=CrmRegistersState.refresh,
                    class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3.5 py-1.5 hover:border-[#d8fa5e]/35 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col lg:flex-row lg:items-start justify-between gap-4 w-full",
        ),
        rx.cond(
            CrmRegistersState.is_report,
            rx.fragment(),
            rx.el.div(
                rx.el.input(
                    placeholder="Rechercher une pièce, un tiers, une facture, une référence...",
                    default_value=CrmRegistersState.search,
                    on_change=CrmRegistersState.set_search.debounce(400),
                    class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2.5 text-sm font-medium text-[#f2efe4] placeholder:text-[#c9c5b4]/35 focus:border-[#d8fa5e]/40 focus:outline-hidden",
                ),
                rx.el.div(
                    _select(
                        CrmRegistersState.status_filter_label,
                        CrmRegistersState.status_filter,
                        CrmRegistersState.status_options,
                        "Tous",
                        CrmRegistersState.set_status_filter,
                    ),
                    _select(
                        CrmRegistersState.type_filter_label,
                        CrmRegistersState.type_filter,
                        CrmRegistersState.type_options,
                        "Tous",
                        CrmRegistersState.set_type_filter,
                    ),
                    _period_select(),
                    class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 w-full mt-3",
                ),
                rx.el.div(
                    rx.el.button(
                        rx.icon(
                            "archive",
                            class_name=rx.cond(
                                CrmRegistersState.include_archived,
                                "h-3.5 w-3.5 text-[#0A0A08]",
                                "h-3.5 w-3.5 text-[#c9c5b4]/60",
                            ),
                        ),
                        rx.el.span(
                            "Inclure les archivées",
                            class_name=rx.cond(
                                CrmRegistersState.include_archived,
                                "text-[11px] font-semibold text-[#0A0A08]",
                                "text-[11px] font-semibold text-[#c9c5b4]/60",
                            ),
                        ),
                        type="button",
                        on_click=CrmRegistersState.toggle_archived,
                        class_name=rx.cond(
                            CrmRegistersState.include_archived,
                            "flex items-center gap-2 rounded-none bg-[#d8fa5e] px-3 py-1.5 transition-colors w-fit",
                            "flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1.5 hover:border-[#d8fa5e]/35 transition-colors w-fit",
                        ),
                    ),
                    rx.cond(
                        CrmRegistersState.has_filters,
                        rx.el.button(
                            rx.icon(
                                "eraser",
                                class_name="h-3.5 w-3.5 text-[#c9c5b4]/60",
                            ),
                            rx.el.span(
                                "Réinitialiser les filtres",
                                class_name="text-[11px] font-semibold text-[#c9c5b4]/60",
                            ),
                            type="button",
                            on_click=CrmRegistersState.clear_filters,
                            class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1.5 hover:border-[#d8fa5e]/35 transition-colors w-fit",
                        ),
                        rx.fragment(),
                    ),
                    class_name="flex flex-wrap items-center gap-2 w-full mt-3",
                ),
                class_name="w-full mt-5 border-t border-[#f2efe4]/12 pt-5",
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5 ",
    )


def _actions(row: RegisterRow) -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon("contact-round", class_name="h-3 w-3 text-[#c9c5b4]/70"),
            rx.el.span(
                "Fiche",
                class_name="text-[10px] font-semibold text-[#c9c5b4]/70",
            ),
            type="button",
            on_click=CrmRegistersState.open_partner(row["partner_id"]),
            class_name="flex items-center gap-1.5 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2.5 py-1 hover:border-[#d8fa5e]/35 transition-colors w-fit",
        ),
        rx.cond(
            row["is_archived"],
            rx.el.button(
                rx.icon("rotate-ccw", class_name="h-3 w-3 text-[#e4ff9b]"),
                rx.el.span(
                    "Réactiver",
                    class_name="text-[10px] font-semibold text-[#e4ff9b]",
                ),
                type="button",
                on_click=CrmRegistersState.restore_row(row["id"]),
                class_name="flex items-center gap-1.5 rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/[0.06] px-2.5 py-1 hover:border-[#d8fa5e]/45 transition-colors w-fit",
            ),
            rx.el.button(
                rx.icon("archive", class_name="h-3 w-3 text-[#ffb894]"),
                rx.el.span(
                    "Archiver",
                    class_name="text-[10px] font-semibold text-[#ffb894]",
                ),
                type="button",
                on_click=CrmRegistersState.archive_row(row["id"]),
                class_name="flex items-center gap-1.5 rounded-none border border-[#ff8a5b]/25 bg-[#ff8a5b]/[0.06] px-2.5 py-1 hover:border-[#ff8a5b]/45 transition-colors w-fit",
            ),
        ),
        class_name="flex flex-wrap items-center gap-1.5",
    )


def _cell(value: rx.Var | str, tone: str) -> rx.Component:
    return rx.el.td(value, class_name=tone)


_TEXT = "px-3 py-2.5 text-xs font-medium text-[#c9c5b4]/65 whitespace-nowrap"
_STRONG = "px-3 py-2.5 text-xs font-semibold text-[#f2efe4] whitespace-nowrap"
_NUM = "px-3 py-2.5 text-xs font-medium text-[#c9c5b4]/70 text-right whitespace-nowrap"


def _row(row: RegisterRow) -> rx.Component:
    return rx.el.tr(
        _cell(row["code"], _STRONG),
        _cell(row["date"], _TEXT),
        rx.el.td(
            rx.el.button(
                row["partner"],
                type="button",
                on_click=CrmRegistersState.open_partner(row["partner_id"]),
                class_name="text-xs font-semibold text-[#e4ff9b] hover:text-[#efffc4] transition-colors text-left",
            ),
            class_name="px-3 py-2.5 whitespace-nowrap",
        ),
        _cell(row["title"], _TEXT),
        _cell(row["reference"], _TEXT),
        _cell(row["type_label"], _TEXT),
        _cell(f"{row['amount_ht']:.2f}", _NUM),
        _cell(f"{row['vat_amount']:.2f}", _NUM),
        _cell(
            f"{row['amount_ttc']:.2f}",
            "px-3 py-2.5 text-xs font-bold text-[#e4ff9b] text-right whitespace-nowrap",
        ),
        _cell(f"{row['paid']:.2f}", _NUM),
        _cell(
            f"{row['remaining']:.2f}",
            "px-3 py-2.5 text-xs font-bold text-[#ffb894] text-right whitespace-nowrap",
        ),
        _cell(row["due_date"], _TEXT),
        rx.el.td(
            rx.cond(
                row["overdue_days"] > 0,
                rx.el.span(
                    f"{row['overdue_days']} j",
                    class_name="text-xs font-bold text-[#ffbcb0]",
                ),
                rx.el.span(
                    "—", class_name="text-xs font-medium text-[#c9c5b4]/40"
                ),
            ),
            class_name="px-3 py-2.5 text-right whitespace-nowrap",
        ),
        rx.el.td(_badge(row), class_name="px-3 py-2.5 whitespace-nowrap"),
        rx.el.td(_actions(row), class_name="px-3 py-2.5"),
        key=row["id"].to_string(),
        class_name=rx.cond(
            row["is_archived"],
            "border-t border-[#f2efe4]/10 bg-white/[0.01] opacity-60",
            "border-t border-[#f2efe4]/10 even:bg-[#0d0f09] hover:bg-[#d8fa5e]/[0.04] transition-colors",
        ),
    )


def _headers() -> list[rx.Component]:
    labels = [
        ("Pièce", "receipt"),
        ("Date", "calendar-days"),
        ("Tiers", "contact-round"),
        ("Objet", "tag"),
        ("Facture", "file-text"),
        ("Type", "layers"),
    ]
    cells = [
        rx.el.th(
            rx.el.div(
                rx.icon(icon, class_name="h-3 w-3 text-[#d8fa5e]/70"),
                rx.el.span(label),
                class_name="flex items-center gap-1.5",
            ),
            class_name="px-3 py-2.5 ap-eyebrow text-[#c9c5b4]/45 text-left whitespace-nowrap",
        )
        for label, icon in labels
    ]
    numeric = [
        CrmRegistersState.amount_header,
        "TVA",
        "TTC",
        "Réglé",
        "Restant dû",
    ]
    cells += [
        rx.el.th(
            label,
            class_name="px-3 py-2.5 ap-eyebrow text-[#c9c5b4]/45 text-right whitespace-nowrap",
        )
        for label in numeric
    ]
    cells += [
        rx.el.th(
            label,
            class_name="px-3 py-2.5 ap-eyebrow text-[#c9c5b4]/45 text-left whitespace-nowrap",
        )
        for label in ["Échéance", "Retard", "Statut", "Actions"]
    ]
    return cells


def crm_register_table() -> rx.Component:
    return rx.el.div(
        rx.el.table(
            rx.el.thead(
                rx.el.tr(*_headers()),
                class_name="bg-[#101208]",
            ),
            rx.el.tbody(rx.foreach(CrmRegistersState.rows, _row)),
            class_name="table-auto w-full min-w-[78rem]",
        ),
        class_name="hidden lg:block w-full overflow-x-auto overflow-hidden rounded-none border border-[#f2efe4]/12 bg-[#0d0f09] ",
    )


def _stat(label: str, value: rx.Var | str, tone: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="ap-eyebrow text-[#c9c5b4]/40",
        ),
        rx.el.span(value, class_name=tone),
        class_name="flex flex-col min-w-0",
    )


def _card(row: RegisterRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    row["code"],
                    class_name="text-sm font-semibold text-[#f2efe4] truncate",
                ),
                rx.el.p(
                    f"{row['date']} · {row['type_label']}",
                    class_name="text-[10px] font-medium text-[#c9c5b4]/45 truncate",
                ),
                class_name="min-w-0 flex-1",
            ),
            _badge(row),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        rx.el.button(
            rx.icon("contact-round", class_name="h-3 w-3 text-[#d8fa5e]"),
            rx.el.span(
                row["partner"],
                class_name="text-xs font-semibold text-[#e4ff9b] truncate",
            ),
            type="button",
            on_click=CrmRegistersState.open_partner(row["partner_id"]),
            class_name="flex items-center gap-1.5 w-full min-w-0 mt-2.5 text-left",
        ),
        rx.el.p(
            f"{row['title']} · {row['reference']}",
            class_name="text-[10px] font-medium text-[#c9c5b4]/45 mt-1 truncate",
        ),
        rx.el.div(
            _stat(
                CrmRegistersState.amount_header,
                f"{row['amount_ht']:.2f} DA",
                "text-[11px] font-bold text-[#c9c5b4] truncate",
            ),
            _stat(
                "TVA",
                f"{row['vat_amount']:.2f} DA",
                "text-[11px] font-bold text-[#c9c5b4] truncate",
            ),
            _stat(
                "TTC",
                f"{row['amount_ttc']:.2f} DA",
                "text-[11px] font-bold text-[#e4ff9b] truncate",
            ),
            _stat(
                "Réglé",
                f"{row['paid']:.2f} DA",
                "text-[11px] font-bold text-[#c9c5b4] truncate",
            ),
            _stat(
                "Restant dû",
                f"{row['remaining']:.2f} DA",
                "text-[11px] font-bold text-[#ffb894] truncate",
            ),
            _stat(
                "Échéance",
                row["due_date"],
                "text-[11px] font-bold text-[#c9c5b4] truncate",
            ),
            class_name="grid grid-cols-2 sm:grid-cols-3 gap-2 w-full mt-3 border-t border-[#f2efe4]/12 pt-3",
        ),
        rx.cond(
            row["overdue_days"] > 0,
            rx.el.p(
                f"{row['overdue_days']} jour(s) de retard",
                class_name="text-[10px] font-semibold text-[#ffbcb0] mt-2.5",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            _actions(row),
            class_name="w-full mt-3 border-t border-[#f2efe4]/12 pt-3",
        ),
        key=row["id"].to_string(),
        class_name=rx.cond(
            row["is_archived"],
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#0d0f09] p-4 opacity-60",
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4",
        ),
    )


def crm_register_cards() -> rx.Component:
    return rx.el.div(
        rx.foreach(CrmRegistersState.rows, _card),
        class_name="grid grid-cols-1 md:grid-cols-2 gap-3 w-full lg:hidden",
    )


def _month_bar(month: ReportMonth) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                month["label"],
                class_name="text-[11px] font-semibold text-[#c9c5b4]/70 w-20 shrink-0",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        class_name="h-1.5 rounded-none bg-gradient-to-r from-[#8fb37a] to-[#d8fa5e]",
                        style={"width": month["sales_width"]},
                    ),
                    class_name="h-1.5 w-full rounded-none bg-[#191c13]",
                ),
                rx.el.div(
                    rx.el.div(
                        class_name="h-1.5 rounded-none bg-gradient-to-r from-[#ff6a38] to-[#ffb894]",
                        style={"width": month["purchases_width"]},
                    ),
                    class_name="h-1.5 w-full rounded-none bg-[#191c13] mt-1.5",
                ),
                class_name="flex-1 min-w-0",
            ),
            class_name="flex items-center gap-3 w-full min-w-0",
        ),
        rx.el.div(
            rx.el.span(
                f"Ventes {month['sales']:.0f} DA",
                class_name="text-[10px] font-semibold text-[#e4ff9b]",
            ),
            rx.el.span(
                f"Achats {month['purchases']:.0f} DA",
                class_name="text-[10px] font-semibold text-[#ffb894]",
            ),
            rx.el.span(
                f"Marge {month['margin']:.0f} DA",
                class_name="text-[10px] font-semibold text-[#c9c5b4]/60 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-3 w-full mt-1.5 pl-[5.75rem]",
        ),
        key=month["key"],
        class_name="w-full",
    )


def _partner_row(item: ReportPartner) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.button(
                item["name"],
                type="button",
                on_click=CrmRegistersState.open_partner(item["id"]),
                class_name="text-xs font-semibold text-[#e4ff9b] hover:text-[#efffc4] transition-colors text-left",
            ),
            class_name="px-3 py-2.5 whitespace-nowrap",
        ),
        _cell(item["kind_label"], _TEXT),
        _cell(f"{item['sales']:.2f}", _NUM),
        _cell(f"{item['purchases']:.2f}", _NUM),
        _cell(
            f"{item['margin']:.2f}",
            "px-3 py-2.5 text-xs font-bold text-[#e4ff9b] text-right whitespace-nowrap",
        ),
        _cell(f"{item['receivable']:.2f}", _NUM),
        _cell(
            f"{item['payable']:.2f}",
            "px-3 py-2.5 text-xs font-bold text-[#ffb894] text-right whitespace-nowrap",
        ),
        key=item["id"].to_string(),
        class_name="border-t border-[#f2efe4]/10 even:bg-[#0d0f09]",
    )


def _partner_card(item: ReportPartner) -> rx.Component:
    return rx.el.div(
        rx.el.button(
            item["name"],
            type="button",
            on_click=CrmRegistersState.open_partner(item["id"]),
            class_name="text-sm font-semibold text-[#e4ff9b] text-left truncate w-full",
        ),
        rx.el.p(
            item["kind_label"],
            class_name="text-[10px] font-medium text-[#c9c5b4]/45 mt-0.5",
        ),
        rx.el.div(
            _stat(
                "Ventes",
                f"{item['sales']:.0f} DA",
                "text-[11px] font-bold text-[#e4ff9b] truncate",
            ),
            _stat(
                "Achats",
                f"{item['purchases']:.0f} DA",
                "text-[11px] font-bold text-[#ffb894] truncate",
            ),
            _stat(
                "Marge",
                f"{item['margin']:.0f} DA",
                "text-[11px] font-bold text-[#c9c5b4] truncate",
            ),
            _stat(
                "Créances",
                f"{item['receivable']:.0f} DA",
                "text-[11px] font-bold text-[#c9c5b4] truncate",
            ),
            _stat(
                "Dettes",
                f"{item['payable']:.0f} DA",
                "text-[11px] font-bold text-[#ffb894] truncate",
            ),
            class_name="grid grid-cols-2 gap-2 w-full mt-3 border-t border-[#f2efe4]/12 pt-3",
        ),
        key=item["id"].to_string(),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4",
    )


def crm_register_reports() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _kpi(
                "Ventes campagne",
                f"{CrmRegistersState.report['sales']:.0f}",
                "DA",
                "text-[#e4ff9b]",
            ),
            _kpi(
                "Achats campagne",
                f"{CrmRegistersState.report['purchases']:.0f}",
                "DA",
                "text-[#ffb894]",
            ),
            _kpi(
                "Marge",
                f"{CrmRegistersState.report['margin']:.0f}",
                "DA",
                "text-[#e4ff9b]",
            ),
            _kpi(
                "Taux de marge",
                f"{CrmRegistersState.report['margin_rate']:.1f}",
                "%",
                "text-[#c9c5b4]",
            ),
            _kpi(
                "Créances",
                f"{CrmRegistersState.report['receivable']:.0f}",
                "DA",
                "text-[#c9c5b4]",
            ),
            _kpi(
                "Dettes",
                f"{CrmRegistersState.report['payable']:.0f}",
                "DA",
                "text-[#c9c5b4]",
            ),
            _kpi(
                "Encaissé",
                f"{CrmRegistersState.report['received']:.0f}",
                "DA",
                "text-[#e4ff9b]",
            ),
            _kpi(
                "Décaissé",
                f"{CrmRegistersState.report['paid_out']:.0f}",
                "DA",
                "text-[#ffb894]",
            ),
            class_name="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-3 w-full",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("bar-chart-3", class_name="h-4 w-4 text-[#d8fa5e]"),
                rx.el.span(
                    "Cadence mensuelle ventes / achats",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                class_name="flex items-center gap-2 w-full",
            ),
            rx.el.div(
                rx.foreach(CrmRegistersState.report_months, _month_bar),
                class_name="flex flex-col gap-3 w-full mt-4",
            ),
            class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5 ",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("scale", class_name="h-4 w-4 text-[#d8fa5e]"),
                rx.el.span(
                    "Balance des tiers",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                class_name="flex items-center gap-2 w-full",
            ),
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            rx.el.th(
                                "Tiers",
                                class_name="px-3 py-2.5 ap-eyebrow text-[#c9c5b4]/45 text-left whitespace-nowrap",
                            ),
                            rx.el.th(
                                "Type",
                                class_name="px-3 py-2.5 ap-eyebrow text-[#c9c5b4]/45 text-left whitespace-nowrap",
                            ),
                            rx.el.th(
                                "Ventes",
                                class_name="px-3 py-2.5 ap-eyebrow text-[#c9c5b4]/45 text-right whitespace-nowrap",
                            ),
                            rx.el.th(
                                "Achats",
                                class_name="px-3 py-2.5 ap-eyebrow text-[#c9c5b4]/45 text-right whitespace-nowrap",
                            ),
                            rx.el.th(
                                "Marge",
                                class_name="px-3 py-2.5 ap-eyebrow text-[#c9c5b4]/45 text-right whitespace-nowrap",
                            ),
                            rx.el.th(
                                "Créances",
                                class_name="px-3 py-2.5 ap-eyebrow text-[#c9c5b4]/45 text-right whitespace-nowrap",
                            ),
                            rx.el.th(
                                "Dettes",
                                class_name="px-3 py-2.5 ap-eyebrow text-[#c9c5b4]/45 text-right whitespace-nowrap",
                            ),
                        ),
                        class_name="bg-[#101208]",
                    ),
                    rx.el.tbody(
                        rx.foreach(
                            CrmRegistersState.report_partners, _partner_row
                        )
                    ),
                    class_name="table-auto w-full min-w-[52rem]",
                ),
                class_name="hidden lg:block w-full overflow-x-auto overflow-hidden rounded-none border border-[#f2efe4]/12 bg-[#0d0f09] mt-4",
            ),
            rx.el.div(
                rx.foreach(CrmRegistersState.report_partners, _partner_card),
                class_name="grid grid-cols-1 md:grid-cols-2 gap-3 w-full mt-4 lg:hidden",
            ),
            class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5 ",
        ),
        class_name="flex flex-col gap-4 w-full",
    )


def _ledger() -> rx.Component:
    return rx.el.div(
        crm_register_kpis(),
        rx.cond(
            CrmRegistersState.row_count > 0,
            rx.el.div(
                crm_register_table(),
                crm_register_cards(),
                class_name="w-full",
            ),
            rx.el.div(
                rx.icon("inbox", class_name="h-8 w-8 text-[#c9c5b4]/30"),
                rx.el.p(
                    "Aucune écriture pour ces filtres",
                    class_name="text-sm font-semibold text-[#c9c5b4]/60 mt-3",
                ),
                rx.el.p(
                    "Élargissez la période, changez de statut ou enregistrez une nouvelle opération.",
                    class_name="text-[11px] font-medium text-[#c9c5b4]/40 mt-1 text-center max-w-md",
                ),
                class_name="flex flex-col items-center justify-center py-20 w-full rounded-none border border-[#f2efe4]/12 bg-[#0d0f09]",
            ),
        ),
        class_name="flex flex-col gap-4 w-full",
    )


def crm_registers(register: str) -> rx.Component:
    """Registre financier CRM (ventes, achats, créances, dettes, paiements)."""
    return rx.el.div(
        crm_register_toolbar(),
        rx.cond(
            CrmRegistersState.is_loading,
            rx.el.div(
                class_name="h-[28rem] w-full animate-pulse rounded-none border border-[#f2efe4]/12 bg-[#14160f]"
            ),
            rx.cond(
                CrmRegistersState.is_report,
                crm_register_reports(),
                _ledger(),
            ),
        ),
        crm_register_form(),
        on_mount=CrmRegistersState.enter_register(register),
        class_name="flex flex-col gap-4 w-full",
    )

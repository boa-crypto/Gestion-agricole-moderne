"""Poste de contrôle des intrants sous seuil (sous-module Stocks).

Panneaux du module Traitements et tuile de diagnostic de l'audit : impact sur
les chantiers planifiés, recommandation chiffrée, décisions d'achat / report /
stock suffisant, historique et accès Guide et recherche globale. Identité
visuelle inchangée : vert nuit, chlorophylle et ambre, surfaces vitrées.
"""

import reflex as rx

from app.components.guide_help import help_icon_button, help_topic_button
from app.states.stock_state import (
    PlannedJob,
    StockItem,
    StockLog,
    StockState,
)

_INPUT = (
    "w-full rounded-none border border-[#f2efe4]/12 bg-[#0A0A08] px-3 py-2.5 "
    "text-sm font-medium text-[#f2efe4] placeholder:text-[#c9c5b4]/30 "
    "focus:border-[#d8fa5e]/50 outline-hidden transition-colors"
)

_PRIMARY = (
    "flex items-center gap-1.5 rounded-none bg-[#d8fa5e] px-3 py-1.5 "
    "text-[11px] font-semibold text-[#0A0A08] hover:bg-[#e4ff9b] "
    "transition-colors w-fit"
)

_GHOST = (
    "flex items-center gap-1.5 rounded-none border border-[#f2efe4]/12 bg-[#14160f] "
    "px-3 py-1.5 text-[11px] font-semibold text-[#c9c5b4]/70 "
    "hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit"
)

_LINK = (
    "flex items-center gap-1.5 rounded-none border border-[#d8fa5e]/25 "
    "bg-[#d8fa5e]/10 px-3 py-1.5 text-[10px] font-semibold text-[#e4ff9b] "
    "hover:bg-[#d8fa5e]/20 transition-colors w-fit"
)

_CHIP = (
    "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 "
    "text-[10px] font-semibold text-[#c9c5b4]/60 w-fit whitespace-nowrap"
)


def _badge(tone: rx.Var | str, label: rx.Var | str) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit whitespace-nowrap",
            ),
            (
                "warn",
                "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffb894] w-fit whitespace-nowrap",
            ),
            (
                "bad",
                "rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-2 py-0.5 text-[10px] font-bold text-[#ff9b8c] w-fit whitespace-nowrap",
            ),
            (
                "info",
                "rounded-none border border-[#9cc3ff]/30 bg-[#9cc3ff]/10 px-2 py-0.5 text-[10px] font-bold text-[#c3daff] w-fit whitespace-nowrap",
            ),
            "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/50 w-fit whitespace-nowrap",
        ),
    )


def _tile(label: str, value: rx.Var | str, unit: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="ap-eyebrow text-[#c9c5b4]/45",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="ap-serif text-2xl leading-none text-[#f2efe4]",
            ),
            rx.el.span(
                unit,
                class_name="text-[11px] font-medium text-[#c9c5b4]/50 mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-2",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-3",
    )


def stock_note_bar() -> rx.Component:
    """Traçabilité de la décision : auteur et motif de l'arbitrage."""
    return rx.el.div(
        rx.el.div(
            rx.icon("pen-line", class_name="h-3.5 w-3.5 text-[#d8fa5e]"),
            rx.el.span(
                "Traçabilité de l'arbitrage magasin",
                class_name="ap-eyebrow text-[#c9c5b4]/50",
            ),
            help_icon_button("traitements"),
            class_name="flex items-center gap-2",
        ),
        rx.el.div(
            rx.el.input(
                placeholder="Qui décide ?",
                default_value=StockState.author_draft,
                on_change=StockState.set_author_draft.debounce(400),
                class_name=_INPUT,
            ),
            rx.el.input(
                placeholder="Pourquoi ? (délai fournisseur, chantier décalé, comptage local…)",
                default_value=StockState.note_draft,
                on_change=StockState.set_note_draft.debounce(400),
                class_name=_INPUT,
            ),
            class_name="grid grid-cols-1 md:grid-cols-[14rem_1fr] gap-3 w-full mt-3",
        ),
        rx.el.p(
            "La note accompagne chaque décision : elle explique six mois plus tard pourquoi le chantier a été tenu ou reporté.",
            class_name="text-[10px] font-medium text-[#c9c5b4]/40 mt-2",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4",
    )


def _view_button(value: str, label: str, icon: str) -> rx.Component:
    return rx.el.button(
        rx.icon(icon, class_name="h-3.5 w-3.5"),
        rx.el.span(label, class_name="text-[11px]"),
        type="button",
        on_click=StockState.set_view(value),
        class_name=rx.cond(
            StockState.view == value,
            "flex items-center gap-1.5 rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/15 px-3 py-1.5 font-semibold text-[#efffc4] w-fit",
            "flex items-center gap-1.5 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1.5 font-medium text-[#c9c5b4]/55 hover:text-[#f2efe4] hover:border-[#d8fa5e]/30 transition-colors w-fit",
        ),
    )


def _recommendation(text_value: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.icon("wrench", class_name="h-3 w-3 text-[#ff8a5b] shrink-0 mt-0.5"),
        rx.el.p(
            text_value,
            class_name="text-[11px] font-medium text-[#ffdccb]/80 leading-relaxed",
        ),
        class_name="flex items-start gap-2 rounded-none border border-[#ff8a5b]/20 bg-[#ff8a5b]/[0.06] px-3 py-2 w-full mt-2",
    )


def _impact(item: StockItem) -> rx.Component:
    return rx.el.div(
        rx.icon(
            "calendar-clock", class_name="h-3 w-3 text-[#d8fa5e] shrink-0 mt-0.5"
        ),
        rx.el.p(
            item["impact"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/70 leading-relaxed",
        ),
        class_name="flex items-start gap-2 rounded-none border border-[#d8fa5e]/20 bg-[#d8fa5e]/[0.05] px-3 py-2 w-full mt-2",
    )


def _trace(item: StockItem) -> rx.Component:
    return rx.cond(
        item["is_documented"],
        rx.el.div(
            rx.icon(item["icon"], class_name="h-3 w-3 text-[#d8fa5e] shrink-0"),
            rx.el.p(
                f"{item['decision_label']} · {item['decided_label']} · {item['author']} — {item['note']}",
                class_name="text-[10px] font-medium text-[#c9c5b4]/55 leading-relaxed",
            ),
            class_name="flex items-start gap-2 rounded-none border border-[#f2efe4]/12 bg-[#101208] px-3 py-2 w-full mt-2",
        ),
        rx.fragment(),
    )


def _item_card(item: StockItem, key: str = "") -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.icon("package", class_name="h-4 w-4 text-[#ff8a5b]"),
            rx.el.span(
                item["category_label"],
                class_name="ap-eyebrow text-[#c9c5b4]/45",
            ),
            _badge(item["severity"], item["status_label"]),
            _badge(item["tone"], item["decision_label"]),
            rx.cond(
                item["organic"],
                rx.el.span(
                    "AB",
                    class_name="rounded-none border border-[#d8fa5e]/40 bg-[#d8fa5e]/10 px-1.5 py-0.5 text-[9px] font-bold text-[#e4ff9b] w-fit ml-auto",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.el.p(
            item["name"],
            class_name="text-sm font-semibold text-[#f2efe4] mt-2 truncate",
        ),
        rx.el.p(
            f"{item['stock']:.1f} {item['unit']} en stock · seuil {item['threshold']:.1f} {item['unit']} · {item['supplier']}",
            class_name="text-[11px] font-medium text-[#c9c5b4]/55 mt-1",
        ),
        rx.el.div(
            rx.el.div(
                class_name=rx.match(
                    item["severity"],
                    ("bad", "h-full rounded-none bg-[#ff6b5a]"),
                    ("warn", "h-full rounded-none bg-[#ff8a5b]"),
                    "h-full rounded-none bg-[#d8fa5e]",
                ),
                style={"width": item["coverage_pct"]},
            ),
            class_name="h-1.5 w-full rounded-none bg-[#20241a] mt-3",
        ),
        rx.el.div(
            rx.el.span(
                f"Manque {item['gap']:.1f} {item['unit']}", class_name=_CHIP
            ),
            rx.el.span(
                f"{item['planned_jobs']} chantier(s) · {item['planned_quantity']:.1f} {item['unit']}",
                class_name=_CHIP,
            ),
            rx.el.span(
                f"Prochain passage {item['next_job_label']}",
                class_name=_CHIP,
            ),
            rx.el.span(
                f"Valeur stock {item['stock_value']:.0f} €",
                class_name=_CHIP,
            ),
            rx.el.span(
                f"Commande conseillée {item['order_quantity']:.1f} {item['unit']} · {item['order_cost']:.0f} €",
                class_name="rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit whitespace-nowrap",
            ),
            class_name="flex flex-wrap items-center gap-1.5 w-full mt-3",
        ),
        _impact(item),
        _recommendation(item["recommendation"]),
        _trace(item),
        rx.el.div(
            rx.el.button(
                rx.icon("truck", class_name="h-3.5 w-3.5"),
                rx.el.span("Commande engagée"),
                type="button",
                on_click=StockState.order_stock(item["id"]),
                class_name=_PRIMARY,
            ),
            rx.el.button(
                rx.icon("calendar-clock", class_name="h-3.5 w-3.5"),
                rx.el.span("Reporter le chantier"),
                type="button",
                on_click=StockState.defer_stock(item["id"]),
                class_name=_GHOST,
            ),
            rx.el.button(
                rx.icon("shield-check", class_name="h-3.5 w-3.5"),
                rx.el.span("Stock suffisant"),
                type="button",
                on_click=StockState.accept_stock(item["id"]),
                class_name=_GHOST,
            ),
            rx.el.button(
                rx.icon("list-tree", class_name="h-3.5 w-3.5"),
                rx.el.span(
                    rx.cond(
                        StockState.selected_id == item["id"],
                        "Masquer le détail",
                        "Chantiers & historique",
                    )
                ),
                type="button",
                on_click=StockState.select_product(item["id"]),
                class_name=_GHOST,
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-3",
        ),
        rx.el.div(
            help_topic_button("traitements", "stock", "Règle de stock"),
            rx.el.a(
                rx.el.span("Guide des stocks"),
                rx.icon("arrow-up-right", class_name="h-3 w-3"),
                href="/guide",
                class_name=_LINK,
            ),
            rx.el.a(
                rx.el.span("Chercher cet intrant"),
                rx.icon("radar", class_name="h-3 w-3"),
                href="/recherche",
                class_name=_LINK,
            ),
            rx.el.span(
                f"{item['decision_count']} décision(s)",
                class_name=f"{_CHIP} ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-2",
        ),
        key=key,
        class_name=rx.match(
            item["severity"],
            (
                "bad",
                "w-full rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/[0.07] p-4",
            ),
            (
                "warn",
                "w-full rounded-none border border-[#ff8a5b]/25 bg-[#ff8a5b]/[0.06] p-4",
            ),
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4",
        ),
    )


def _job_row(job: PlannedJob, key: str = "") -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.icon("spray-can", class_name="h-3.5 w-3.5 text-[#d8fa5e]"),
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    job["title"],
                    class_name="text-[12px] font-semibold text-[#f2efe4] truncate",
                ),
                rx.cond(
                    job["is_late"],
                    _badge("bad", "En retard"),
                    _badge("info", job["status_label"]),
                ),
                rx.el.span(
                    job["date_label"],
                    class_name="text-[10px] font-medium text-[#c9c5b4]/40 ml-auto shrink-0",
                ),
                class_name="flex flex-wrap items-center gap-2 w-full min-w-0",
            ),
            rx.el.p(
                f"{job['parcel']} · {job['crop']} — {job['dose']:.2f} {job['unit']}/ha sur {job['area']:.1f} ha, soit {job['quantity']:.1f} {job['unit']}",
                class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-1 leading-relaxed",
            ),
            class_name="min-w-0 flex-1",
        ),
        key=key,
        class_name="flex items-start gap-3 w-full rounded-none border border-[#f2efe4]/12 bg-[#0d0f09] p-3",
    )


def _log_row(entry: StockLog, key: str = "") -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.icon(entry["icon"], class_name="h-3.5 w-3.5 text-[#d8fa5e]"),
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    entry["target_label"],
                    class_name="text-[12px] font-semibold text-[#f2efe4] truncate",
                ),
                _badge(entry["tone"], entry["action_label"]),
                rx.el.span(
                    entry["date_label"],
                    class_name="text-[10px] font-medium text-[#c9c5b4]/40 ml-auto shrink-0",
                ),
                class_name="flex flex-wrap items-center gap-2 w-full min-w-0",
            ),
            rx.el.p(
                f"{entry['author']} — {entry['note']}",
                class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-1 leading-relaxed",
            ),
            class_name="min-w-0 flex-1",
        ),
        key=key,
        class_name="flex items-start gap-3 w-full rounded-none border border-[#f2efe4]/12 bg-[#0d0f09] p-3",
    )


def _selection_block() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Détail de l'intrant",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h3(
                    StockState.selected_label,
                    class_name="ap-serif text-2xl text-[#f2efe4] mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.button(
                rx.icon("x", class_name="h-3.5 w-3.5"),
                type="button",
                on_click=StockState.clear_selection,
                class_name="flex h-7 w-7 shrink-0 items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#14160f] text-[#c9c5b4]/60 hover:text-[#f2efe4] hover:border-[#d8fa5e]/30 transition-colors",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Chantiers exposés",
                    class_name="ap-eyebrow text-[#c9c5b4]/50",
                ),
                rx.cond(
                    StockState.has_selected_jobs,
                    rx.el.ul(
                        rx.foreach(
                            StockState.selected_jobs,
                            lambda job: _job_row(
                                job, key=job["id"].to_string()
                            ),
                        ),
                        class_name="flex flex-col gap-2 w-full mt-3",
                    ),
                    rx.el.p(
                        "Aucun chantier programmé ne consomme cet intrant : la commande peut attendre la prochaine tournée.",
                        class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-3 leading-relaxed",
                    ),
                ),
                class_name="flex-1 min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4",
            ),
            rx.el.div(
                rx.el.span(
                    "Historique des décisions",
                    class_name="ap-eyebrow text-[#c9c5b4]/50",
                ),
                rx.cond(
                    StockState.has_selected_history,
                    rx.el.ul(
                        rx.foreach(
                            StockState.selected_history,
                            lambda entry: _log_row(
                                entry, key=entry["id"].to_string()
                            ),
                        ),
                        class_name="flex flex-col gap-2 w-full mt-3",
                    ),
                    rx.el.p(
                        "Aucune décision consignée pour cet intrant.",
                        class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-3",
                    ),
                ),
                class_name="w-full xl:w-[26rem] shrink-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4",
            ),
            class_name="flex flex-col xl:flex-row gap-3 w-full mt-4",
        ),
        class_name="w-full rounded-none border border-[#d8fa5e]/20 bg-[#d8fa5e]/[0.04] p-5 mt-4",
    )


def _summary_tiles() -> rx.Component:
    return rx.el.div(
        _tile(
            "Intrants sous tension",
            f"{StockState.summary['total']:.0f}",
            "références",
        ),
        _tile("Ruptures", f"{StockState.summary['rupture']:.0f}", "à engager"),
        _tile(
            "Chantiers exposés",
            f"{StockState.summary['jobs_at_risk']:.0f}",
            "passages",
        ),
        _tile(
            "Commande conseillée",
            f"{StockState.summary['order_cost']:.0f}",
            "€",
        ),
        _tile(
            "Décisions consignées",
            f"{StockState.summary['decisions']:.0f}",
            "lignes",
        ),
        _tile(
            "Valeur en tension",
            f"{StockState.summary['stock_value']:.0f}",
            "€",
        ),
        class_name="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3 w-full mt-5",
    )


def stock_control_panel() -> rx.Component:
    """Poste de contrôle complet des intrants, pour le module Traitements."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Sous-module Stocks · arbitrage magasin",
                    class_name="ap-eyebrow text-[#ff8a5b]/80",
                ),
                rx.el.h2(
                    "Piloter les intrants sous seuil",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                rx.el.p(
                    "Pour chaque intrant : couverture réelle, chantiers programmés exposés, quantité et coût de commande conseillés, puis décision consignée — commande engagée, chantier reporté ou stock suffisant.",
                    class_name="text-sm font-medium text-[#c9c5b4]/55 mt-2 max-w-3xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                _badge(StockState.verdict_tone, StockState.verdict_label),
                rx.el.span(
                    StockState.today_label,
                    class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/65 w-fit",
                ),
                rx.el.button(
                    rx.cond(
                        StockState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#0A0A08]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#0A0A08]"
                        ),
                    ),
                    rx.el.span("Recalculer", class_name="text-[#0A0A08]"),
                    type="button",
                    on_click=StockState.load_stocks,
                    class_name="ap-mono inline-flex w-fit items-center gap-2 bg-[#D8FA5E] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[#0A0A08] transition-colors hover:bg-[#E4FF9B]",
                ),
                help_icon_button("traitements"),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4 w-full",
        ),
        rx.el.p(
            StockState.verdict_detail,
            class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-3",
        ),
        _summary_tiles(),
        rx.el.div(
            _view_button("TOUS", "Tous", "layers"),
            _view_button("RUPTURE", "Ruptures", "octagon-alert"),
            _view_button("A_ARBITRER", "À arbitrer", "circle-dashed"),
            _view_button("DOCUMENTE", "Documentés", "history"),
            rx.el.span(
                f"{StockState.visible_items.length()} intrant(s) affiché(s)",
                class_name=f"{_CHIP} ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-5",
        ),
        rx.el.div(stock_note_bar(), class_name="w-full mt-4"),
        rx.cond(
            StockState.has_visible_items,
            rx.el.div(
                rx.foreach(
                    StockState.visible_items,
                    lambda item: _item_card(item, key=item["id"].to_string()),
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 w-full mt-4",
            ),
            rx.el.div(
                rx.icon("shield-check", class_name="h-6 w-6 text-[#d8fa5e]"),
                rx.el.p(
                    "Aucun intrant dans cette vue : le magasin couvre les chantiers programmés.",
                    class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2",
                ),
                class_name="flex flex-col items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#101208] py-12 w-full mt-4",
            ),
        ),
        rx.cond(StockState.has_selection, _selection_block(), rx.fragment()),
        rx.cond(
            StockState.has_history,
            rx.el.div(
                rx.el.span(
                    "Journal des décisions d'intrants",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.ul(
                    rx.foreach(
                        StockState.history,
                        lambda entry: _log_row(
                            entry, key=entry["id"].to_string()
                        ),
                    ),
                    class_name="flex flex-col gap-2 w-full mt-3",
                ),
                class_name="w-full mt-6 border-t border-[#f2efe4]/12 pt-5",
            ),
            rx.el.p(
                "Aucune décision d'intrant consignée pour le moment.",
                class_name="text-sm font-medium text-[#c9c5b4]/50 mt-6",
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )


def stock_diagnostic_tile() -> rx.Component:
    """Tuile compacte du sous-module Stocks pour le diagnostic /audit."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Sous-module Stocks · état d'exploitation",
                    class_name="ap-eyebrow text-[#ff8a5b]/80",
                ),
                rx.el.h2(
                    "Intrants sous seuil et arbitrages",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                rx.el.p(
                    StockState.verdict_detail,
                    class_name="text-sm font-medium text-[#c9c5b4]/55 mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                _badge(StockState.verdict_tone, StockState.verdict_label),
                rx.el.a(
                    rx.el.span("Poste de contrôle des intrants"),
                    rx.icon("arrow-up-right", class_name="h-3 w-3"),
                    href="/traitements",
                    class_name=_LINK,
                ),
                rx.el.a(
                    rx.el.span("Guide des stocks"),
                    rx.icon("book-open", class_name="h-3 w-3"),
                    href="/guide",
                    class_name=_LINK,
                ),
                rx.el.a(
                    rx.el.span("Chercher une décision"),
                    rx.icon("radar", class_name="h-3 w-3"),
                    href="/recherche",
                    class_name=_LINK,
                ),
                help_topic_button("traitements", "stock", "Règle de stock"),
                help_icon_button("traitements"),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4 w-full",
        ),
        _summary_tiles(),
        rx.cond(
            StockState.has_history,
            rx.el.ul(
                rx.foreach(
                    StockState.history,
                    lambda entry: _log_row(entry, key=entry["id"].to_string()),
                ),
                class_name="flex flex-col gap-2 w-full mt-5",
            ),
            rx.el.p(
                "Aucune décision d'intrant consignée : les tensions restent à arbitrer.",
                class_name="text-sm font-medium text-[#c9c5b4]/50 mt-5",
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )

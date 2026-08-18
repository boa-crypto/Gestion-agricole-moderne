"""Panneaux de remédiation des états d'exploitation (cockpit AgriPro).

Trois sous-modules connectés au diagnostic : triage des alertes, aide à la
décision sur les intrants sous seuil, validation des contours générés. Identité
visuelle inchangée : vert nuit, chlorophylle et ambre, surfaces vitrées.
"""

import reflex as rx

from app.components.guide_help import help_icon_button
from app.states.remediation_state import (
    AlertTriage,
    ContourCheck,
    RemediationEntry,
    RemediationState,
    StockDecision,
)

_INPUT = (
    "w-full rounded-xl border border-white/10 bg-[#04140d] px-3 py-2.5 "
    "text-sm font-medium text-emerald-50 placeholder:text-emerald-100/30 "
    "focus:border-lime-300/50 outline-hidden transition-colors"
)

_PRIMARY = (
    "flex items-center gap-1.5 rounded-full bg-lime-300 px-3 py-1.5 "
    "text-[11px] font-semibold text-[#04140d] hover:bg-lime-200 "
    "transition-colors w-fit"
)

_GHOST = (
    "flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 "
    "px-3 py-1.5 text-[11px] font-semibold text-emerald-100/70 "
    "hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit"
)


def _badge(tone: rx.Var, label: rx.Var | str) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-full border border-lime-300/30 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit whitespace-nowrap",
            ),
            (
                "warn",
                "rounded-full border border-amber-300/30 bg-amber-300/10 px-2 py-0.5 text-[10px] font-bold text-amber-200 w-fit whitespace-nowrap",
            ),
            (
                "bad",
                "rounded-full border border-red-400/30 bg-red-500/10 px-2 py-0.5 text-[10px] font-bold text-red-300 w-fit whitespace-nowrap",
            ),
            (
                "info",
                "rounded-full border border-sky-300/30 bg-sky-300/10 px-2 py-0.5 text-[10px] font-bold text-sky-200 w-fit whitespace-nowrap",
            ),
            "rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/50 w-fit whitespace-nowrap",
        ),
    )


def _recommendation(text_value: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.icon("wrench", class_name="h-3 w-3 text-amber-300 shrink-0 mt-0.5"),
        rx.el.p(
            text_value,
            class_name="text-[11px] font-medium text-amber-100/80 leading-relaxed",
        ),
        class_name="flex items-start gap-2 rounded-xl border border-amber-300/20 bg-amber-300/[0.06] px-3 py-2 w-full mt-2",
    )


def _trace(
    is_documented: rx.Var, action_label: rx.Var, note: rx.Var, date: rx.Var
) -> rx.Component:
    return rx.cond(
        is_documented,
        rx.el.div(
            rx.icon("history", class_name="h-3 w-3 text-lime-300 shrink-0"),
            rx.el.p(
                f"{action_label} · {date} — {note}",
                class_name="text-[10px] font-medium text-emerald-100/55 leading-relaxed",
            ),
            class_name="flex items-start gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 w-full mt-2",
        ),
        rx.fragment(),
    )


def _section_head(
    caption: str,
    title: str,
    intro: str,
    context: str,
    right: rx.Component,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                caption,
                class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
            ),
            rx.el.h2(
                title,
                class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
            ),
            rx.el.p(
                intro,
                class_name="text-sm font-medium text-emerald-100/55 mt-2 max-w-2xl",
            ),
            class_name="min-w-0",
        ),
        rx.el.div(
            right,
            help_icon_button(context),
            class_name="flex flex-wrap items-center gap-2",
        ),
        class_name="flex flex-wrap items-end justify-between gap-3 w-full",
    )


def remediation_note_bar() -> rx.Component:
    """Saisie commune de traçabilité : auteur et note de décision."""
    return rx.el.div(
        rx.el.div(
            rx.icon("pen-line", class_name="h-3.5 w-3.5 text-lime-300"),
            rx.el.span(
                "Traçabilité de la décision",
                class_name="text-[10px] font-semibold uppercase tracking-[0.22em] text-emerald-100/50",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.div(
            rx.el.input(
                placeholder="Qui décide ?",
                default_value=RemediationState.author_draft,
                on_change=RemediationState.set_author_draft.debounce(400),
                class_name=_INPUT,
            ),
            rx.el.input(
                placeholder="Pourquoi cette décision ? (constat de terrain, arbitrage…)",
                default_value=RemediationState.note_draft,
                on_change=RemediationState.set_note_draft.debounce(400),
                class_name=_INPUT,
            ),
            class_name="grid grid-cols-1 md:grid-cols-[14rem_1fr] gap-3 w-full mt-3",
        ),
        rx.el.p(
            "La note est attachée à chaque décision consignée : elle rend l'arbitrage relisible six mois plus tard.",
            class_name="text-[10px] font-medium text-emerald-100/40 mt-2",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4",
    )


# ---------------------------------------------------------------------------
# 1) Triage des alertes agronomiques
# ---------------------------------------------------------------------------


def _alert_card(item: AlertTriage, key: str = "") -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.match(
                item["level"],
                (
                    "CRITIQUE",
                    rx.icon("octagon-alert", class_name="h-4 w-4 text-red-400"),
                ),
                (
                    "ATTENTION",
                    rx.icon(
                        "triangle-alert", class_name="h-4 w-4 text-amber-300"
                    ),
                ),
                rx.icon("info", class_name="h-4 w-4 text-sky-300"),
            ),
            rx.el.span(
                item["category"],
                class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
            ),
            _badge(item["tone"], item["action_label"]),
            rx.el.span(
                item["date_label"],
                class_name="text-[10px] font-medium text-emerald-100/40 ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.el.p(
            item["title"],
            class_name="text-sm font-semibold text-emerald-50 mt-2 leading-snug",
        ),
        rx.el.p(
            item["message"],
            class_name="text-[11px] font-medium text-emerald-100/55 mt-1 leading-relaxed",
        ),
        rx.el.div(
            rx.icon("map-pin", class_name="h-3 w-3 text-lime-300/80"),
            rx.el.span(
                item["parcel"],
                class_name="text-[11px] font-medium text-emerald-100/60",
            ),
            class_name="flex items-center gap-1.5 mt-3",
        ),
        _recommendation(item["recommendation"]),
        _trace(
            item["is_documented"],
            item["action_label"],
            item["note"],
            item["decided_label"],
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("circle-check", class_name="h-3.5 w-3.5"),
                rx.el.span("Traiter et clôturer"),
                on_click=RemediationState.resolve_alert(item["id"]),
                class_name=_PRIMARY,
            ),
            rx.el.button(
                rx.icon("eye", class_name="h-3.5 w-3.5"),
                rx.el.span("Mettre sous surveillance"),
                on_click=RemediationState.watch_alert(item["id"]),
                class_name=_GHOST,
            ),
            rx.el.a(
                rx.el.span("Guide phytosanitaire"),
                rx.icon("arrow-up-right", class_name="h-3 w-3"),
                href="/guide",
                class_name="flex items-center gap-1.5 rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1.5 text-[10px] font-semibold text-lime-200 hover:bg-lime-300/20 transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-3",
        ),
        key=key,
        class_name=rx.match(
            item["level"],
            (
                "CRITIQUE",
                "w-full rounded-2xl border border-red-400/30 bg-red-500/[0.07] p-4",
            ),
            (
                "ATTENTION",
                "w-full rounded-2xl border border-amber-300/25 bg-amber-300/[0.06] p-4",
            ),
            "w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4",
        ),
    )


def alert_triage_panel() -> rx.Component:
    return rx.el.section(
        _section_head(
            "Remédiation · veille agronomique",
            "Traiter les alertes actives",
            "Chaque alerte se termine par une décision : intervention réalisée puis clôture, ou mise sous surveillance documentée.",
            "cockpit",
            rx.el.span(
                f"{RemediationState.counters['alerts_critical']:.0f} critique(s) · {RemediationState.counters['alerts_closed']:.0f} clôturée(s)",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/65 w-fit",
            ),
        ),
        remediation_note_bar(),
        rx.cond(
            RemediationState.has_alerts,
            rx.el.div(
                rx.foreach(
                    RemediationState.alerts,
                    lambda item: _alert_card(item, key=item["id"].to_string()),
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 w-full mt-4",
            ),
            rx.el.div(
                rx.icon("shield-check", class_name="h-6 w-6 text-lime-300"),
                rx.el.p(
                    "Aucune alerte active : la veille agronomique est à jour.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-2",
                ),
                class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-12 w-full mt-4",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )


# ---------------------------------------------------------------------------
# 2) Aide à la décision sur les intrants sous seuil
# ---------------------------------------------------------------------------


def _stock_card(item: StockDecision, key: str = "") -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.icon("package", class_name="h-4 w-4 text-amber-300"),
            rx.el.span(
                item["category_label"],
                class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
            ),
            _badge(item["severity"], item["status_label"]),
            _badge(item["tone"], item["action_label"]),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.el.p(
            item["name"],
            class_name="text-sm font-semibold text-emerald-50 mt-2 truncate",
        ),
        rx.el.p(
            f"{item['stock']:.1f} {item['unit']} en stock · seuil {item['threshold']:.1f} {item['unit']} · {item['supplier']}",
            class_name="text-[11px] font-medium text-emerald-100/55 mt-1",
        ),
        rx.el.div(
            rx.el.div(
                class_name=rx.match(
                    item["severity"],
                    ("bad", "h-full rounded-full bg-red-400"),
                    ("warn", "h-full rounded-full bg-amber-300"),
                    "h-full rounded-full bg-lime-300",
                ),
                style={"width": item["coverage_pct"]},
            ),
            class_name="h-1.5 w-full rounded-full bg-white/10 mt-3",
        ),
        rx.el.div(
            rx.el.span(
                f"Manque {item['gap']:.1f} {item['unit']}",
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                f"{item['planned_jobs']} chantier(s) programmé(s)",
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                f"Commande conseillée {item['order_quantity']:.1f} {item['unit']} · {item['order_cost']:.0f} €",
                class_name="rounded-full border border-lime-300/25 bg-lime-300/10 px-2 py-0.5 text-[10px] font-bold text-lime-200 w-fit",
            ),
            class_name="flex flex-wrap items-center gap-1.5 w-full mt-3",
        ),
        _recommendation(item["recommendation"]),
        _trace(
            item["is_documented"],
            item["action_label"],
            item["note"],
            item["decided_label"],
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("truck", class_name="h-3.5 w-3.5"),
                rx.el.span("Commande engagée"),
                on_click=RemediationState.decide_stock(item["id"], "COMMANDE"),
                class_name=_PRIMARY,
            ),
            rx.el.button(
                rx.icon("calendar-clock", class_name="h-3.5 w-3.5"),
                rx.el.span("Reporter le chantier"),
                on_click=RemediationState.decide_stock(item["id"], "REPORT"),
                class_name=_GHOST,
            ),
            rx.el.button(
                rx.icon("shield-check", class_name="h-3.5 w-3.5"),
                rx.el.span("Stock suffisant"),
                on_click=RemediationState.decide_stock(item["id"], "SUFFISANT"),
                class_name=_GHOST,
            ),
            rx.el.a(
                rx.el.span("Guide des stocks"),
                rx.icon("arrow-up-right", class_name="h-3 w-3"),
                href="/guide",
                class_name="flex items-center gap-1.5 rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1.5 text-[10px] font-semibold text-lime-200 hover:bg-lime-300/20 transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-3",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:border-lime-300/25 transition-colors",
    )


def stock_decision_panel() -> rx.Component:
    return rx.el.section(
        _section_head(
            "Remédiation · intrants sous seuil",
            "Aide à la décision de réapprovisionnement",
            "Pour chaque intrant sous le seuil : couverture réelle, chantiers programmés, quantité et coût de commande conseillés.",
            "traitements",
            rx.el.span(
                f"{RemediationState.counters['stocks_open']:.0f} à arbitrer · {RemediationState.counters['stock_order_cost']:.0f} € de commande estimée",
                class_name="rounded-full border border-amber-300/25 bg-amber-300/10 px-3 py-1 text-[11px] font-semibold text-amber-200 w-fit",
            ),
        ),
        remediation_note_bar(),
        rx.cond(
            RemediationState.has_stocks,
            rx.el.div(
                rx.foreach(
                    RemediationState.stocks,
                    lambda item: _stock_card(item, key=item["id"].to_string()),
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 w-full mt-4",
            ),
            rx.el.div(
                rx.icon("shield-check", class_name="h-6 w-6 text-lime-300"),
                rx.el.p(
                    "Aucun intrant sous le seuil de réapprovisionnement.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-2",
                ),
                class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-12 w-full mt-4",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )


# ---------------------------------------------------------------------------
# 3) Validation des contours générés
# ---------------------------------------------------------------------------


def _contour_card(item: ContourCheck, key: str = "") -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.icon("shapes", class_name="h-4 w-4 text-lime-300"),
            rx.el.span(
                item["code"],
                class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/50",
            ),
            _badge(item["severity"], item["source_label"]),
            _badge(item["tone"], item["action_label"]),
            class_name="flex flex-wrap items-center gap-2 w-full",
        ),
        rx.el.p(
            item["name"],
            class_name="text-sm font-semibold text-emerald-50 mt-2 truncate",
        ),
        rx.el.p(
            item["locality"],
            class_name="text-[11px] font-medium text-emerald-100/45 mt-0.5",
        ),
        rx.el.div(
            rx.el.span(
                f"Déclarée {item['declared_area']:.1f} ha",
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            rx.el.span(
                f"Contour {item['computed_area']:.1f} ha",
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
            ),
            _badge(
                rx.cond(item["gap_pct"] > 5.0, "bad", "good"),
                f"Écart {item['gap_label']}",
            ),
            rx.el.span(
                f"{item['vertex_count']} sommets",
                class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/55 w-fit",
            ),
            class_name="flex flex-wrap items-center gap-1.5 w-full mt-3",
        ),
        _recommendation(item["recommendation"]),
        rx.el.p(
            "Un contour vérifié à l'écran reste une validation visuelle : il ne vaut pas relevé cadastral ni mesure GPS.",
            class_name="text-[10px] font-medium text-emerald-100/40 leading-relaxed mt-2",
        ),
        _trace(
            item["is_documented"],
            item["action_label"],
            item["note"],
            item["decided_label"],
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("scan-eye", class_name="h-3.5 w-3.5"),
                rx.el.span("Marquer vérifié à l'écran"),
                on_click=RemediationState.decide_contour(item["id"], "VERIFIE"),
                class_name=_PRIMARY,
            ),
            rx.el.button(
                rx.icon("map-pin", class_name="h-3.5 w-3.5"),
                rx.el.span("À relever sur le terrain"),
                on_click=RemediationState.decide_contour(
                    item["id"], "A_RELEVER"
                ),
                class_name=_GHOST,
            ),
            rx.el.a(
                rx.el.span("Ouvrir la cartographie"),
                rx.icon("arrow-up-right", class_name="h-3 w-3"),
                href="/cartographie",
                class_name="flex items-center gap-1.5 rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1.5 text-[10px] font-semibold text-lime-200 hover:bg-lime-300/20 transition-colors w-fit ml-auto",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-3",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:border-lime-300/25 transition-colors",
    )


def contour_validation_panel() -> rx.Component:
    return rx.el.section(
        _section_head(
            "Remédiation · géométrie parcellaire",
            "Valider les contours générés",
            "Les contours générés sont approximatifs : contrôler l'écart de surface, puis les marquer vérifiés à l'écran ou à relever sur le terrain.",
            "cartographie",
            rx.el.span(
                f"{RemediationState.counters['contours_open']:.0f} à valider · {RemediationState.counters['contours_gap']:.0f} écart(s) > 5 %",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/65 w-fit",
            ),
        ),
        remediation_note_bar(),
        rx.cond(
            RemediationState.geometry_ready,
            rx.fragment(),
            rx.el.div(
                rx.icon(
                    "triangle-alert",
                    class_name="h-4 w-4 text-amber-300 shrink-0",
                ),
                rx.el.p(
                    "Les colonnes de géométrie sont indisponibles : la validation des contours est suspendue.",
                    class_name="text-xs font-medium text-amber-100/80",
                ),
                class_name="flex items-center gap-2 rounded-2xl border border-amber-300/25 bg-amber-300/[0.07] px-4 py-3 w-full mt-4",
            ),
        ),
        rx.cond(
            RemediationState.has_contours,
            rx.el.div(
                rx.foreach(
                    RemediationState.contours,
                    lambda item: _contour_card(
                        item, key=item["id"].to_string()
                    ),
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 w-full mt-4",
            ),
            rx.el.div(
                rx.icon("circle-check", class_name="h-6 w-6 text-lime-300"),
                rx.el.p(
                    "Tous les îlots affichent un contour cohérent avec leur surface déclarée.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-2",
                ),
                class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-12 w-full mt-4",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )


# ---------------------------------------------------------------------------
# Journal et synthèse pour le diagnostic
# ---------------------------------------------------------------------------


def _history_row(item: RemediationEntry, key: str = "") -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.icon(item["icon"], class_name="h-3.5 w-3.5 text-lime-300"),
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-lime-300/25 bg-lime-300/10",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    item["target_label"],
                    class_name="text-[12px] font-semibold text-emerald-50 truncate",
                ),
                _badge(item["tone"], item["action_label"]),
                rx.el.span(
                    item["date_label"],
                    class_name="text-[10px] font-medium text-emerald-100/40 ml-auto shrink-0",
                ),
                class_name="flex flex-wrap items-center gap-2 w-full min-w-0",
            ),
            rx.el.p(
                f"{item['domain_label']} · {item['author']} — {item['note']}",
                class_name="text-[11px] font-medium text-emerald-100/50 mt-1 leading-relaxed",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.a(
            rx.icon("arrow-up-right", class_name="h-3.5 w-3.5"),
            href=item["module_route"],
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-emerald-100/60 hover:text-emerald-50 hover:border-lime-300/30 transition-colors",
        ),
        key=key,
        class_name="flex items-start gap-3 w-full rounded-2xl border border-white/10 bg-white/[0.02] p-3",
    )


def _tile(label: str, value: rx.Var | str, unit: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-100/45",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="font-['Instrument_Serif'] text-2xl leading-none text-emerald-50",
            ),
            rx.el.span(
                unit,
                class_name="text-[11px] font-medium text-emerald-100/50 mb-0.5",
            ),
            class_name="flex items-end gap-1.5 mt-2",
        ),
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3",
    )


def remediation_summary() -> rx.Component:
    """Console de remédiation intégrée au diagnostic /audit."""
    return rx.el.section(
        _section_head(
            "Remédiation des états d'exploitation",
            "Résoudre ou documenter",
            "Le diagnostic conserve les états d'exploitation ; ces sous-modules permettent de les traiter et d'en garder la trace.",
            "guide",
            rx.el.span(
                f"{RemediationState.open_total} état(s) ouvert(s) · {RemediationState.counters['decisions']:.0f} décision(s)",
                class_name="rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1 text-[11px] font-bold text-lime-200 w-fit",
            ),
        ),
        rx.el.div(
            _tile(
                "Alertes actives",
                f"{RemediationState.counters['alerts_open']:.0f}",
                "à traiter",
            ),
            _tile(
                "Alertes clôturées",
                f"{RemediationState.counters['alerts_closed']:.0f}",
                "documentées",
            ),
            _tile(
                "Intrants sous seuil",
                f"{RemediationState.counters['stocks_open']:.0f}",
                "à arbitrer",
            ),
            _tile(
                "Commande estimée",
                f"{RemediationState.counters['stock_order_cost']:.0f}",
                "€",
            ),
            _tile(
                "Contours à valider",
                f"{RemediationState.counters['contours_open']:.0f}",
                "îlots",
            ),
            _tile(
                "Décisions consignées",
                f"{RemediationState.counters['decisions']:.0f}",
                "lignes",
            ),
            class_name="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3 w-full mt-5",
        ),
        rx.el.div(
            _badge(
                RemediationState.verdict_tone, RemediationState.verdict_label
            ),
            rx.el.a(
                rx.el.span("Cockpit · alertes"),
                rx.icon("arrow-up-right", class_name="h-3 w-3"),
                href="/",
                class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[10px] font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
            ),
            rx.el.a(
                rx.el.span("Traitements · stocks"),
                rx.icon("arrow-up-right", class_name="h-3 w-3"),
                href="/traitements",
                class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[10px] font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
            ),
            rx.el.a(
                rx.el.span("Cartographie · contours"),
                rx.icon("arrow-up-right", class_name="h-3 w-3"),
                href="/cartographie",
                class_name="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[10px] font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-4",
        ),
        rx.cond(
            RemediationState.has_history,
            rx.el.div(
                rx.el.span(
                    "Journal des décisions",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.24em] text-lime-300/80",
                ),
                rx.el.ul(
                    rx.foreach(
                        RemediationState.history,
                        lambda item: _history_row(
                            item, key=item["id"].to_string()
                        ),
                    ),
                    class_name="flex flex-col gap-2 w-full mt-3",
                ),
                class_name="w-full mt-6 border-t border-white/10 pt-5",
            ),
            rx.el.p(
                "Aucune décision de remédiation consignée pour le moment.",
                class_name="text-sm font-medium text-emerald-100/50 mt-6",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )

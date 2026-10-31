"""Pouls opérationnel du cockpit agronomique.

Ce bloc ne crée aucune donnée : il relit les états déjà consolidés par les
sous-modules de remédiation (alertes), Stocks (intrants sous seuil) et Contours
(géométrie parcellaire) pour répondre à deux questions de terrain :

* que reste-t-il à décider aujourd'hui (priorités restantes) ;
* qu'a-t-on déjà décidé et documenté (décisions récentes).

Identité visuelle inchangée : vert nuit, chlorophylle et ambre, surfaces
vitrées, typographie éditoriale Instrument Serif.
"""

import reflex as rx

from app.components.guide_help import help_icon_button, help_topic_button
from app.states.contour_state import ContourState
from app.states.remediation_state import RemediationEntry, RemediationState
from app.states.stock_state import StockState

_CHIP = (
    "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2.5 py-1 "
    "text-[10px] font-semibold text-[#c9c5b4]/60 w-fit whitespace-nowrap"
)

_LINK = (
    "flex items-center gap-1.5 rounded-none border border-[#d8fa5e]/25 "
    "bg-[#d8fa5e]/10 px-3 py-1.5 text-[10px] font-semibold text-[#e4ff9b] "
    "hover:bg-[#d8fa5e]/20 transition-colors w-fit"
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


def _tile(
    label: str, value: rx.Var | str, unit: str, caption: rx.Var | str
) -> rx.Component:
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
        rx.el.p(
            caption,
            class_name="text-[10px] font-medium text-[#c9c5b4]/40 mt-2 leading-relaxed",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-3",
    )


def _priority_card(
    caption: str,
    title: str,
    icon: str,
    tone: rx.Var | str,
    status_label: rx.Var | str,
    value: rx.Var | str,
    unit: str,
    detail: rx.Var | str,
    recommendation: rx.Var | str,
    href: str,
    href_label: str,
    context_key: str,
    topic: str,
    topic_label: str,
) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.div(
                rx.icon(icon, class_name="h-4 w-4 text-[#d8fa5e]"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10",
            ),
            rx.el.div(
                rx.el.span(
                    caption,
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.p(
                    title,
                    class_name="ap-serif text-xl text-[#f2efe4] mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            _badge(tone, status_label),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        rx.el.div(
            rx.el.span(
                value,
                class_name="ap-serif text-3xl leading-none text-[#f2efe4]",
            ),
            rx.el.span(
                unit,
                class_name="text-[11px] font-medium text-[#c9c5b4]/50 mb-1",
            ),
            class_name="flex items-end gap-1.5 w-full mt-4",
        ),
        rx.el.p(
            detail,
            class_name="text-[11px] font-medium text-[#c9c5b4]/55 leading-relaxed mt-2",
        ),
        rx.el.div(
            rx.icon(
                "wrench", class_name="h-3 w-3 text-[#ff8a5b] shrink-0 mt-0.5"
            ),
            rx.el.p(
                recommendation,
                class_name="text-[11px] font-medium text-[#ffdccb]/80 leading-relaxed",
            ),
            class_name="flex items-start gap-2 rounded-none border border-[#ff8a5b]/20 bg-[#ff8a5b]/[0.06] px-3 py-2 w-full mt-3",
        ),
        rx.el.div(
            rx.el.a(
                rx.el.span(href_label),
                rx.icon("arrow-up-right", class_name="h-3 w-3"),
                href=href,
                class_name=_LINK,
            ),
            help_topic_button(context_key, topic, topic_label),
            help_icon_button(context_key),
            class_name="flex flex-wrap items-center gap-2 w-full mt-3",
        ),
        class_name=rx.match(
            tone,
            (
                "bad",
                "w-full rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/[0.06] p-4",
            ),
            (
                "warn",
                "w-full rounded-none border border-[#ff8a5b]/25 bg-[#ff8a5b]/[0.05] p-4",
            ),
            "w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4",
        ),
    )


def _decision_row(item: RemediationEntry, key: str = "") -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.icon(item["icon"], class_name="h-3.5 w-3.5 text-[#d8fa5e]"),
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    item["target_label"],
                    class_name="text-[12px] font-semibold text-[#f2efe4] truncate",
                ),
                _badge(item["tone"], item["action_label"]),
                rx.el.span(
                    item["date_label"],
                    class_name="text-[10px] font-medium text-[#c9c5b4]/40 ml-auto shrink-0",
                ),
                class_name="flex flex-wrap items-center gap-2 w-full min-w-0",
            ),
            rx.el.p(
                f"{item['domain_label']} · {item['author']} — {item['note']}",
                class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-1 leading-relaxed",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.a(
            rx.icon("arrow-up-right", class_name="h-3.5 w-3.5"),
            href=item["module_route"],
            class_name="flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#14160f] text-[#c9c5b4]/60 hover:text-[#f2efe4] hover:border-[#d8fa5e]/30 transition-colors",
        ),
        key=key,
        class_name="flex items-start gap-3 w-full rounded-none border border-[#f2efe4]/12 bg-[#0d0f09] p-3",
    )


def _priorities() -> rx.Component:
    return rx.el.div(
        _priority_card(
            "Veille agronomique",
            "Alertes à décider",
            "triangle-alert",
            rx.cond(
                RemediationState.counters["alerts_critical"] > 0,
                "bad",
                rx.cond(
                    RemediationState.counters["alerts_open"] > 0,
                    "warn",
                    "good",
                ),
            ),
            rx.cond(
                RemediationState.counters["alerts_open"] > 0,
                "À traiter",
                "Veille à jour",
            ),
            f"{RemediationState.counters['alerts_open']:.0f}",
            "alerte(s) active(s)",
            f"{RemediationState.counters['alerts_critical']:.0f} critique(s) · {RemediationState.counters['alerts_closed']:.0f} clôturée(s) et documentée(s)",
            rx.cond(
                RemediationState.counters["alerts_critical"] > 0,
                "Décision attendue sous 24 h : intervenir puis clôturer l'alerte depuis le triage du cockpit.",
                rx.cond(
                    RemediationState.counters["alerts_open"] > 0,
                    "Documenter la surveillance ou clôturer les alertes dont le risque est levé.",
                    "Aucune alerte ouverte : conserver la trace des clôtures pour la prochaine campagne.",
                ),
            ),
            "/",
            "Triage des alertes",
            "cockpit",
            "phyto",
            "Règle phytosanitaire",
        ),
        _priority_card(
            "Sous-module Stocks",
            "Intrants sous seuil",
            "package",
            rx.cond(
                StockState.summary["rupture"] > 0,
                "bad",
                rx.cond(StockState.summary["open"] > 0, "warn", "good"),
            ),
            rx.cond(
                StockState.summary["open"] > 0,
                "À arbitrer",
                "Arbitrages documentés",
            ),
            f"{StockState.summary['open']:.0f}",
            "intrant(s) à arbitrer",
            f"{StockState.summary['rupture']:.0f} rupture(s) · {StockState.summary['jobs_at_risk']:.0f} chantier(s) exposé(s) · {StockState.summary['order_cost']:.0f} € de commande conseillée",
            rx.cond(
                StockState.summary["rupture"] > 0,
                "Engager la commande ou reporter le chantier concerné depuis le poste de contrôle des intrants.",
                rx.cond(
                    StockState.summary["open"] > 0,
                    "Arbitrer chaque intrant sous seuil : commande engagée, chantier reporté ou stock jugé suffisant.",
                    "Toutes les tensions de stock portent une décision consignée.",
                ),
            ),
            "/traitements",
            "Poste de contrôle des intrants",
            "traitements",
            "stock",
            "Règle de stock",
        ),
        _priority_card(
            "Sous-module Contours",
            "Contours d'îlots",
            "shapes",
            rx.cond(
                ContourState.kpis["ecart"] > 0,
                "bad",
                rx.cond(ContourState.open_total > 0, "warn", "good"),
            ),
            rx.cond(
                ContourState.open_total > 0,
                "À contrôler",
                "Contrôle à jour",
            ),
            f"{ContourState.open_total}",
            "îlot(s) à contrôler",
            f"taux de contrôle {ContourState.control_rate_pct} · {ContourState.kpis['ecart']:.0f} écart(s) > 5 % · {ContourState.kpis['verifie']:.0f} vérifié(s) à l'écran",
            rx.cond(
                ContourState.kpis["ecart"] > 0,
                "Arbitrer les écarts de surface puis marquer les îlots à relever sur le terrain.",
                rx.cond(
                    ContourState.open_total > 0,
                    "Vérifier les contours générés à l'écran ou programmer un relevé GPS.",
                    "Chaque îlot audité porte une décision de contour consignée.",
                ),
            ),
            "/cartographie",
            "Contrôle des contours",
            "cartographie",
            "geometrie",
            "Règle de géométrie",
        ),
        class_name="grid grid-cols-1 lg:grid-cols-3 gap-3 w-full mt-5",
    )


def cockpit_pulse() -> rx.Component:
    """Décisions opérationnelles récentes et priorités restantes du cockpit."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Pouls opérationnel",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Décidé, documenté, restant",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                rx.el.p(
                    "Les sous-modules Contours et Stocks remontent ici leurs statuts : ce qui a été décidé et tracé, ce qui reste à arbitrer aujourd'hui.",
                    class_name="text-sm font-medium text-[#c9c5b4]/55 mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                _badge(
                    RemediationState.verdict_tone,
                    RemediationState.verdict_label,
                ),
                rx.el.span(
                    f"{RemediationState.counters['decisions']:.0f} décision(s) consignée(s)",
                    class_name=_CHIP,
                ),
                help_icon_button("cockpit"),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.el.div(
            _tile(
                "États ouverts",
                f"{RemediationState.open_total}",
                "à décider",
                "Alertes, intrants et contours cumulés",
            ),
            _tile(
                "Décisions tracées",
                f"{RemediationState.counters['decisions']:.0f}",
                "lignes",
                "Journal de remédiation, tous domaines",
            ),
            _tile(
                "Commande conseillée",
                f"{StockState.summary['order_cost']:.0f}",
                "€",
                "Réapprovisionnement des intrants sous seuil",
            ),
            _tile(
                "Contrôle des contours",
                ContourState.control_rate_pct,
                "des îlots",
                f"{ContourState.kpis['decisions']:.0f} décision(s) de géométrie",
            ),
            class_name="grid grid-cols-2 xl:grid-cols-4 gap-3 w-full mt-5",
        ),
        _priorities(),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Décisions récentes",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.a(
                    rx.el.span("Journal complet · diagnostic"),
                    rx.icon("arrow-up-right", class_name="h-3 w-3"),
                    href="/audit",
                    class_name=f"{_LINK} ml-auto",
                ),
                class_name="flex flex-wrap items-center gap-2 w-full",
            ),
            rx.cond(
                RemediationState.has_history,
                rx.el.ul(
                    rx.foreach(
                        RemediationState.history,
                        lambda item: _decision_row(
                            item, key=item["id"].to_string()
                        ),
                    ),
                    class_name="flex flex-col gap-2 w-full mt-3",
                ),
                rx.el.p(
                    "Aucune décision opérationnelle consignée : traiter une alerte, arbitrer un intrant ou valider un contour alimentera ce journal.",
                    class_name="text-sm font-medium text-[#c9c5b4]/50 mt-3 leading-relaxed",
                ),
            ),
            class_name="w-full mt-6 border-t border-[#f2efe4]/12 pt-5",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )

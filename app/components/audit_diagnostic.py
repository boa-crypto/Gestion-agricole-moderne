"""Salle de contrôle du diagnostic fonctionnel CMS² AgriPro.

Synthèse décisionnelle, distributions normalisées (statut, priorité, domaine),
file de correction priorisée et modules sous surveillance. Aucune écriture :
tous les constats proviennent de l'audit existant (`AuditState`).

Identité visuelle : vert nuit, chlorophylle et ambre, surfaces vitrées,
typographie éditoriale Instrument Serif.
"""

import reflex as rx

from app.components.guide_help import help_icon_button, help_topic_button
from app.states.audit_state import (
    ActionRow,
    AuditState,
    DiagnosticRow,
    IssueRow,
    ModuleRow,
)
from app.states.contour_state import ContourState
from app.states.remediation_state import RemediationEntry, RemediationState
from app.states.stock_state import StockState


def _tone_value(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        ("good", "text-[11px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] ml-auto"),
        ("warn", "text-[11px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] ml-auto"),
        ("bad", "text-[11px] font-bold text-[rgb(var(--ap-danger-soft-rgb))] ml-auto"),
        ("info", "text-[11px] font-bold text-[rgb(var(--ap-info-soft-rgb))] ml-auto"),
        "text-[11px] font-bold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] ml-auto",
    )


def _tone_bar(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        ("good", "h-full rounded-none bg-[rgb(var(--ap-accent-rgb)/0.80)]"),
        ("warn", "h-full rounded-none bg-[rgb(var(--ap-flame-soft-rgb)/0.80)]"),
        ("bad", "h-full rounded-none bg-[rgb(var(--ap-danger-rgb)/0.80)]"),
        ("info", "h-full rounded-none bg-[rgb(var(--ap-info-rgb)/0.80)]"),
        "h-full rounded-none bg-[rgb(var(--ap-track-deep-rgb))]",
    )


def _tone_ring(tone: rx.Var) -> rx.Var | str:
    return rx.match(
        tone,
        (
            "good",
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)]",
        ),
        (
            "warn",
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)]",
        ),
        (
            "bad",
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-danger-rgb)/0.30)] bg-[rgb(var(--ap-flame-strong-rgb)/0.10)]",
        ),
        (
            "info",
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-info-rgb)/0.30)] bg-[rgb(var(--ap-info-rgb)/0.10)]",
        ),
        "flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))]",
    )


def _badge(tone: rx.Var, label: rx.Var) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-none border border-[rgb(var(--ap-accent-rgb)/0.30)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit whitespace-nowrap",
            ),
            (
                "warn",
                "rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.30)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] w-fit whitespace-nowrap",
            ),
            (
                "bad",
                "rounded-none border border-[rgb(var(--ap-danger-rgb)/0.30)] bg-[rgb(var(--ap-flame-strong-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-danger-soft-rgb))] w-fit whitespace-nowrap",
            ),
            (
                "info",
                "rounded-none border border-[rgb(var(--ap-info-rgb)/0.30)] bg-[rgb(var(--ap-info-rgb)/0.10)] px-2 py-0.5 text-[10px] font-bold text-[rgb(var(--ap-info-soft-rgb))] w-fit whitespace-nowrap",
            ),
            "rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit whitespace-nowrap",
        ),
    )


def _distribution_row(row: DiagnosticRow, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(row["icon"], class_name="h-3.5 w-3.5"),
                class_name=_tone_ring(row["tone"]),
            ),
            rx.el.span(
                row["label"],
                class_name="text-[12px] font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
            ),
            rx.el.span(
                row["value"],
                class_name=rx.cond(
                    row["value"] > 0,
                    "text-[12px] font-bold text-[rgb(var(--ap-paper-rgb))] ml-auto",
                    "text-[12px] font-bold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] ml-auto",
                ),
            ),
            rx.el.span(
                row["share_pct"],
                class_name="text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-9 text-right",
            ),
            class_name="flex items-center gap-2.5 w-full min-w-0",
        ),
        rx.el.div(
            rx.el.div(
                class_name=_tone_bar(row["tone"]),
                style={"width": row["share_pct"]},
            ),
            class_name="h-1.5 w-full rounded-none bg-[rgb(var(--ap-surface-control-rgb))] mt-2",
        ),
        key=key,
        class_name="w-full",
    )


def _distribution_card(
    caption: str, title: str, icon: str, rows: rx.Var
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(icon, class_name="h-4 w-4 text-[rgb(var(--ap-accent-rgb))]"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)]",
            ),
            rx.el.div(
                rx.el.span(
                    caption,
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h3(
                    title,
                    class_name="ap-serif text-xl text-[rgb(var(--ap-paper-rgb))] mt-0.5",
                ),
                class_name="min-w-0",
            ),
            class_name="flex items-center gap-3 w-full",
        ),
        rx.el.div(
            rx.foreach(
                rows, lambda row: _distribution_row(row, key=row["key"])
            ),
            class_name="flex flex-col gap-3 w-full mt-4",
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] flex-1 min-w-[16rem] w-full pt-4",
    )


def _gauge() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                "Indice de conformité fonctionnelle",
                class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            _badge(AuditState.verdict_tone, AuditState.verdict_label),
            class_name="flex flex-wrap items-center justify-between gap-2 w-full",
        ),
        rx.el.div(
            rx.el.span(
                AuditState.readiness_pct,
                class_name="ap-serif text-5xl leading-none text-[rgb(var(--ap-paper-rgb))]",
            ),
            rx.el.span(
                "de la chaîne Guide ↔ application validée",
                class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mb-1.5",
            ),
            class_name="flex items-end gap-2 w-full mt-3",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-full rounded-none bg-gradient-to-r from-[rgb(var(--ap-sage-soft-rgb))] via-[rgb(var(--ap-accent-rgb))] to-[rgb(var(--ap-flame-soft-rgb))]",
                style={"width": AuditState.readiness_pct},
            ),
            class_name="h-2 w-full rounded-none bg-[rgb(var(--ap-surface-control-rgb))] mt-4",
        ),
        rx.el.p(
            AuditState.verdict_detail,
            class_name="text-[12px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] leading-relaxed mt-4",
        ),
        rx.el.div(
            rx.el.span(
                f"{AuditState.kpis['records']:.0f} enregistrement(s) lus",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2.5 py-1 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.78)] w-fit",
            ),
            rx.el.span(
                f"{AuditState.kpis['guide_contents']:.0f} contenu(s) de Guide",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2.5 py-1 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.78)] w-fit",
            ),
            rx.el.span(
                f"{AuditState.kpis['empty_entities']:.0f} table(s) vide(s)",
                class_name="rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.25)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2.5 py-1 text-[10px] font-semibold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full mt-4",
        ),
        class_name="w-full xl:w-[24rem] shrink-0 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.20)] bg-[rgb(var(--ap-ink-rgb)/0.70)] p-5",
    )


def diagnostic_synthesis() -> rx.Component:
    """Synthèse décisionnelle : verdict, indice et distributions normalisées."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Synthèse décisionnelle",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Diagnostic fonctionnel",
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                rx.el.p(
                    "Où en est réellement l'application face au Guide Agricole : conformité, blocages et charge de correction.",
                    class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                AuditState.generated_label,
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit",
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.el.div(
            _gauge(),
            rx.el.div(
                _distribution_card(
                    "Modules",
                    "Statuts normalisés",
                    "flag",
                    AuditState.status_distribution,
                ),
                _distribution_card(
                    "Constats",
                    "Priorité de correction",
                    "siren",
                    AuditState.priority_distribution,
                ),
                _distribution_card(
                    "Origine",
                    "Domaines concernés",
                    "layers",
                    AuditState.domain_distribution,
                ),
                class_name="flex flex-col lg:flex-row gap-3 flex-1 w-full min-w-0",
            ),
            class_name="flex flex-col xl:flex-row gap-3 w-full mt-5",
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )


def _column(
    caption: str,
    title: str,
    icon: str,
    count: rx.Var | str,
    unit: str,
    body: rx.Component,
    footer: rx.Component,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(icon, class_name="h-4 w-4 text-[rgb(var(--ap-accent-rgb))]"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)]",
            ),
            rx.el.div(
                rx.el.span(
                    caption,
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h3(
                    title,
                    class_name="ap-serif text-xl text-[rgb(var(--ap-paper-rgb))] mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                rx.el.span(
                    count,
                    class_name="ap-serif text-2xl leading-none text-[rgb(var(--ap-paper-rgb))]",
                ),
                rx.el.span(
                    unit,
                    class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mb-0.5",
                ),
                class_name="flex items-end gap-1 shrink-0",
            ),
            class_name="flex items-start gap-3 w-full min-w-0",
        ),
        body,
        footer,
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] flex-1 min-w-[16rem] w-full pt-4 flex flex-col",
    )


def _healthy_row(row: ModuleRow, key: str = "") -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.icon(row["icon"], class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb))]"),
            class_name="flex h-7 w-7 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)]",
        ),
        rx.el.div(
            rx.el.p(
                row["label"],
                class_name="text-[12px] font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
            ),
            rx.el.p(
                row["route"],
                class_name="text-[10px] font-mono text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-0.5",
            ),
            class_name="min-w-0 flex-1",
        ),
        _badge("good", row["coverage_pct"]),
        key=key,
        class_name="flex items-center gap-2.5 w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-soft-rgb))] p-2.5",
    )


def _operational_row(row: IssueRow, key: str = "") -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.el.p(
                row["label"],
                class_name="text-[12px] font-semibold text-[rgb(var(--ap-paper-rgb))]",
            ),
            _badge(row["priority_tone"], row["priority_label"]),
            rx.el.span(
                f"{row['count']}",
                class_name="text-[11px] font-bold text-[rgb(var(--ap-flame-tint-rgb))] ml-auto shrink-0",
            ),
            class_name="flex flex-wrap items-center gap-2 w-full min-w-0",
        ),
        rx.el.p(
            row["recommendation"],
            class_name="text-[11px] font-medium text-[rgb(var(--ap-warm-100-rgb)/0.75)] leading-relaxed mt-1.5",
        ),
        rx.el.a(
            rx.el.span(row["module_label"]),
            rx.icon("arrow-up-right", class_name="h-3 w-3"),
            href=row["module_route"],
            class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-3 py-1 text-[10px] font-semibold text-[rgb(var(--ap-accent-soft-rgb))] hover:bg-[rgb(var(--ap-accent-rgb)/0.20)] transition-colors w-fit mt-2",
        ),
        key=key,
        class_name="w-full rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.20)] bg-[rgb(var(--ap-flame-soft-rgb))]/[0.05] p-3",
    )


def _documented_row(item: RemediationEntry, key: str = "") -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.icon(item["icon"], class_name="h-3.5 w-3.5 text-[rgb(var(--ap-accent-rgb))]"),
            class_name="flex h-7 w-7 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)]",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    item["target_label"],
                    class_name="text-[12px] font-semibold text-[rgb(var(--ap-paper-rgb))] truncate",
                ),
                _badge(item["tone"], item["action_label"]),
                class_name="flex flex-wrap items-center gap-2 w-full min-w-0",
            ),
            rx.el.p(
                f"{item['domain_label']} · {item['date_label']} · {item['author']}",
                class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-0.5",
            ),
            class_name="min-w-0 flex-1",
        ),
        key=key,
        class_name="flex items-start gap-2.5 w-full rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-soft-rgb))] p-2.5",
    )


def diagnostic_triage() -> rx.Component:
    """Tri de lecture : modules sains, états à traiter, décisions documentées."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Tri de lecture",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Sains, à traiter, documentés",
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                rx.el.p(
                    "Un module sain n'est pas un module sans travail : les états d'exploitation (alertes, intrants sous seuil, contours à contrôler) se traitent, ils ne cassent pas la chaîne fonctionnelle.",
                    class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    AuditState.triage_label,
                    class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit",
                ),
                help_icon_button("audit"),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.el.div(
            _column(
                "Chaîne conforme",
                "Modules sains",
                "circle-check",
                AuditState.healthy_module_count,
                "écrans",
                rx.cond(
                    AuditState.has_healthy_modules,
                    rx.el.ul(
                        rx.foreach(
                            AuditState.healthy_modules,
                            lambda row: _healthy_row(row, key=row["key"]),
                        ),
                        class_name="flex flex-col gap-2 w-full mt-4",
                    ),
                    rx.el.p(
                        "Aucun module pleinement conforme pour le moment.",
                        class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-4",
                    ),
                ),
                rx.el.p(
                    f"{AuditState.coherence_issue_count} écart(s) de cohérence métier restant à corriger hors exploitation.",
                    class_name="text-[10px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-4 pt-3 border-t border-[rgb(var(--ap-paper-rgb)/0.12)]",
                ),
            ),
            _column(
                "Exploitation",
                "États à traiter",
                "siren",
                AuditState.operational_issue_count,
                "constats",
                rx.cond(
                    AuditState.has_operational_issues,
                    rx.el.ul(
                        rx.foreach(
                            AuditState.operational_issues,
                            lambda row: _operational_row(row, key=row["id"]),
                        ),
                        class_name="flex flex-col gap-2 w-full mt-4",
                    ),
                    rx.el.p(
                        "Aucun état d'exploitation ouvert : alertes, intrants et contours sont traités.",
                        class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-4 leading-relaxed",
                    ),
                ),
                rx.el.div(
                    rx.el.span(
                        f"{StockState.summary['open']:.0f} intrant(s) à arbitrer",
                        class_name="rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.25)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
                    ),
                    rx.el.span(
                        f"{ContourState.open_total} contour(s) à contrôler",
                        class_name="rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.25)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
                    ),
                    rx.el.span(
                        f"{RemediationState.counters['alerts_open']:.0f} alerte(s) active(s)",
                        class_name="rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.25)] bg-[rgb(var(--ap-flame-soft-rgb)/0.10)] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-flame-tint-rgb))] w-fit",
                    ),
                    class_name="flex flex-wrap items-center gap-1.5 w-full mt-4 pt-3 border-t border-[rgb(var(--ap-paper-rgb)/0.12)]",
                ),
            ),
            _column(
                "Traçabilité",
                "Décisions documentées",
                "history",
                f"{RemediationState.counters['decisions']:.0f}",
                "lignes",
                rx.cond(
                    RemediationState.has_history,
                    rx.el.ul(
                        rx.foreach(
                            RemediationState.history,
                            lambda item: _documented_row(
                                item, key=item["id"].to_string()
                            ),
                        ),
                        class_name="flex flex-col gap-2 w-full mt-4",
                    ),
                    rx.el.p(
                        "Aucune décision consignée : les états d'exploitation restent à arbitrer.",
                        class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.86)] mt-4 leading-relaxed",
                    ),
                ),
                rx.el.div(
                    help_topic_button("traitements", "stock", "Règle de stock"),
                    help_topic_button(
                        "cartographie", "geometrie", "Règle de géométrie"
                    ),
                    class_name="flex flex-wrap items-center gap-2 w-full mt-4 pt-3 border-t border-[rgb(var(--ap-paper-rgb)/0.12)]",
                ),
            ),
            class_name="flex flex-col xl:flex-row gap-3 w-full mt-5",
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )


def _action_row(row: ActionRow, key: str = "") -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.el.span(
                row["rank"],
                class_name=rx.match(
                    row["priority_tone"],
                    (
                        "bad",
                        "flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-danger-rgb)/0.40)] bg-[rgb(var(--ap-flame-strong-rgb)/0.15)] text-[11px] font-bold text-[rgb(var(--ap-warm-150-rgb))]",
                    ),
                    (
                        "warn",
                        "flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.40)] bg-[rgb(var(--ap-flame-soft-rgb)/0.15)] text-[11px] font-bold text-[rgb(var(--ap-flame-tint-rgb))]",
                    ),
                    (
                        "info",
                        "flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-info-rgb)/0.40)] bg-[rgb(var(--ap-info-rgb)/0.15)] text-[11px] font-bold text-[rgb(var(--ap-info-soft-rgb))]",
                    ),
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.24)] bg-[rgb(var(--ap-surface-raised-rgb))] text-[11px] font-bold text-[rgb(var(--ap-paper-muted-rgb)/0.82)]",
                ),
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.p(
                        row["label"],
                        class_name="text-[13px] font-semibold text-[rgb(var(--ap-paper-rgb))]",
                    ),
                    _badge(row["priority_tone"], row["priority_label"]),
                    _badge(row["tone"], row["status_label"]),
                    class_name="flex flex-wrap items-center gap-2 w-full",
                ),
                rx.el.p(
                    row["detail"],
                    class_name="text-[11px] font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] leading-relaxed mt-1.5",
                ),
                rx.el.div(
                    rx.icon(
                        "wrench", class_name="h-3 w-3 text-[rgb(var(--ap-flame-soft-rgb))] shrink-0"
                    ),
                    rx.el.p(
                        row["recommendation"],
                        class_name="text-[11px] font-medium text-[rgb(var(--ap-warm-100-rgb)/0.80)] leading-relaxed",
                    ),
                    class_name="flex items-start gap-2 rounded-none border border-[rgb(var(--ap-flame-soft-rgb)/0.20)] bg-[rgb(var(--ap-flame-soft-rgb))]/[0.06] px-3 py-2 w-full mt-2",
                ),
                rx.el.div(
                    rx.el.span(
                        row["domain_label"],
                        class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.78)] w-fit",
                    ),
                    rx.el.span(
                        row["reference"],
                        class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[9px] font-mono text-[rgb(var(--ap-paper-muted-rgb)/0.86)] w-fit",
                    ),
                    rx.el.a(
                        rx.el.span(row["module_label"]),
                        rx.icon("arrow-up-right", class_name="h-3 w-3"),
                        href=row["module_route"],
                        class_name="flex items-center gap-1.5 rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-3 py-1 text-[10px] font-semibold text-[rgb(var(--ap-accent-soft-rgb))] hover:bg-[rgb(var(--ap-accent-rgb)/0.20)] transition-colors w-fit ml-auto",
                    ),
                    class_name="flex flex-wrap items-center gap-2 w-full mt-2",
                ),
                class_name="min-w-0 flex-1",
            ),
            class_name="flex items-start gap-3 w-full",
        ),
        key=key,
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.12)] w-full pt-4 hover:border-t-[rgb(var(--ap-accent-rgb)/0.40)] transition-colors",
    )


def diagnostic_actions() -> rx.Component:
    """File de correction priorisée, alignée sur les filtres du diagnostic."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Priorisation des corrections",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Plan d'action séquencé",
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                rx.el.p(
                    "Les écarts sont ordonnés par priorité puis par module : traiter du haut vers le bas.",
                    class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.78)] mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{AuditState.action_plan.length()} action(s) en tête de file",
                class_name="rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)] px-3 py-1 text-[11px] font-bold text-[rgb(var(--ap-accent-soft-rgb))] w-fit",
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.cond(
            AuditState.has_action_plan,
            rx.el.ol(
                rx.foreach(
                    AuditState.action_plan,
                    lambda row: _action_row(row, key=row["id"]),
                ),
                class_name="flex flex-col gap-2.5 w-full mt-5",
            ),
            rx.el.div(
                rx.icon("shield-check", class_name="h-6 w-6 text-[rgb(var(--ap-accent-rgb))]"),
                rx.el.p(
                    "Aucune correction à séquencer sur ce périmètre.",
                    class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] mt-2",
                ),
                class_name="flex flex-col items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] py-12 w-full mt-5",
            ),
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )


def _watch_card(row: ModuleRow, key: str = "") -> rx.Component:
    return rx.el.button(
        rx.el.div(
            rx.el.div(
                rx.icon(row["icon"], class_name="h-4 w-4 text-[rgb(var(--ap-accent-rgb))]"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[rgb(var(--ap-accent-rgb)/0.25)] bg-[rgb(var(--ap-accent-rgb)/0.10)]",
            ),
            rx.el.div(
                rx.el.p(
                    row["label"],
                    class_name="text-[13px] font-semibold text-[rgb(var(--ap-paper-rgb))] text-left truncate",
                ),
                rx.el.p(
                    row["route"],
                    class_name="text-[10px] font-mono text-[rgb(var(--ap-paper-muted-rgb)/0.86)] text-left mt-0.5",
                ),
                class_name="min-w-0 flex-1",
            ),
            _badge(row["tone"], row["status_label"]),
            class_name="flex items-center gap-3 w-full min-w-0",
        ),
        rx.el.div(
            rx.el.span(
                "Couverture",
                class_name="ap-eyebrow text-[rgb(var(--ap-paper-muted-rgb)/0.86)]",
            ),
            rx.el.span(
                row["coverage_pct"],
                class_name=_tone_value(row["tone"]),
            ),
            class_name="flex items-center gap-2 w-full mt-3",
        ),
        rx.el.div(
            rx.el.div(
                class_name=_tone_bar(row["tone"]),
                style={"width": row["coverage_pct"]},
            ),
            class_name="h-1.5 w-full rounded-none bg-[rgb(var(--ap-surface-control-rgb))] mt-2",
        ),
        rx.el.div(
            _badge(row["priority_tone"], row["priority_label"]),
            rx.el.span(
                f"{row['issue_count']} écart(s)",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.78)] w-fit",
            ),
            rx.el.span(
                f"{row['blocking_count']} bloquant(s)",
                class_name="rounded-none border border-[rgb(var(--ap-danger-rgb)/0.25)] bg-[rgb(var(--ap-flame-strong-rgb)/0.10)] px-2 py-0.5 text-[10px] font-semibold text-[rgb(var(--ap-warm-150-rgb))] w-fit",
            ),
            class_name="flex flex-wrap items-center gap-1.5 w-full mt-3",
        ),
        rx.el.p(
            row["recommendations"][0],
            class_name="text-[11px] font-medium text-[rgb(var(--ap-warm-100-rgb)/0.75)] text-left leading-relaxed mt-3",
        ),
        on_click=AuditState.focus_module(row["key"]),
        key=key,
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-4 text-left hover:border-[rgb(var(--ap-accent-rgb)/0.30)] hover:bg-[rgb(var(--ap-surface-high-rgb))] transition-colors",
    )


def diagnostic_watchlist() -> rx.Component:
    """Modules manquants, incohérents ou incomplets à traiter en premier."""
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Modules sous surveillance",
                    class_name="ap-eyebrow text-[rgb(var(--ap-accent-rgb)/0.80)]",
                ),
                rx.el.h2(
                    "Manquants, incohérents, incomplets",
                    class_name="ap-serif text-3xl text-[rgb(var(--ap-paper-rgb))] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                "Cliquer un module pour filtrer tout le diagnostic",
                class_name="rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-raised-rgb))] px-3 py-1 text-[11px] font-semibold text-[rgb(var(--ap-paper-muted-rgb)/0.82)] w-fit",
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.cond(
            AuditState.has_watchlist,
            rx.el.div(
                rx.foreach(
                    AuditState.watchlist,
                    lambda row: _watch_card(row, key=row["key"]),
                ),
                class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 w-full mt-5",
            ),
            rx.el.div(
                rx.icon("circle-check", class_name="h-6 w-6 text-[rgb(var(--ap-accent-rgb))]"),
                rx.el.p(
                    "Tous les modules audités sont conformes au Guide Agricole.",
                    class_name="text-sm font-medium text-[rgb(var(--ap-paper-muted-rgb)/0.82)] mt-2",
                ),
                class_name="flex flex-col items-center justify-center rounded-none border border-[rgb(var(--ap-paper-rgb)/0.18)] bg-[rgb(var(--ap-surface-rgb))] py-12 w-full mt-5",
            ),
        ),
        class_name="border-t border-[rgb(var(--ap-paper-rgb)/0.18)] w-full pt-6",
    )

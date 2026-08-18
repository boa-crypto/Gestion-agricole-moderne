"""Consultation minimale de l'audit fonctionnel CMS² AgriPro.

Identité visuelle inchangée : cockpit vert nuit, accents chlorophylle et ambre,
surfaces vitrées et typographie éditoriale Instrument Serif.
"""

import reflex as rx

from app.states.audit_state import (
    AuditState,
    CategoryRow,
    EntityRow,
    IssueRow,
    ModuleRow,
)

_SELECT = (
    "w-full appearance-none cursor-pointer rounded-xl border border-white/10 "
    "bg-[#04140d] py-2.5 pl-9 pr-9 text-sm font-medium text-emerald-50 "
    "focus:border-lime-300/50 focus:ring-2 focus:ring-lime-300/20 "
    "outline-hidden transition-colors"
)


def _status_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
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


def _accent(tone: rx.Var) -> rx.Component:
    return rx.el.div(
        class_name=rx.match(
            tone,
            ("good", "h-1 w-full rounded-full bg-lime-300/80"),
            ("warn", "h-1 w-full rounded-full bg-amber-300/80"),
            ("bad", "h-1 w-full rounded-full bg-red-400/80"),
            "h-1 w-full rounded-full bg-white/15",
        )
    )


def _stat(label: str, value: rx.Var | str, unit: str) -> rx.Component:
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


def audit_kpis() -> rx.Component:
    return rx.el.section(
        _stat("Modules audités", AuditState.kpis["modules"], "écrans"),
        _stat("Couverture moyenne", f"{AuditState.kpis['coverage']:.0f}", "%"),
        _stat("Conformes", AuditState.kpis["present"], "présents"),
        _stat("À compléter", AuditState.kpis["incomplete"], "incomplets"),
        _stat("Incohérents", AuditState.kpis["incoherent"], "à corriger"),
        _stat("Constats", AuditState.kpis["issues"], "dont bloquants"),
        class_name="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3 w-full",
    )


def _chip(label: rx.Var | str) -> rx.Component:
    return rx.el.span(
        label,
        class_name="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold text-emerald-100/60 w-fit",
    )


def _bullet(label: rx.Var) -> rx.Component:
    return rx.el.li(
        label,
        class_name="text-[11px] font-medium text-emerald-100/65 leading-relaxed list-disc ml-4",
    )


def _module_card(row: ModuleRow, key: str = "") -> rx.Component:
    return rx.el.article(
        _accent(row["tone"]),
        rx.el.div(
            rx.el.div(
                rx.icon(row["icon"], class_name="h-4 w-4 text-lime-300"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-lime-300/25 bg-lime-300/10",
            ),
            rx.el.div(
                rx.el.p(
                    row["label"],
                    class_name="text-sm font-semibold text-emerald-50",
                ),
                rx.el.p(
                    row["mission"],
                    class_name="text-[11px] font-medium text-emerald-100/50 mt-1",
                ),
                class_name="min-w-0 flex-1",
            ),
            rx.el.div(
                _status_badge(row["tone"], row["status_label"]),
                _status_badge(row["priority_tone"], row["priority_label"]),
                class_name="flex flex-col items-end gap-1.5 shrink-0",
            ),
            class_name="flex items-start gap-3 w-full mt-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Couverture",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
                ),
                rx.el.span(
                    row["coverage_pct"],
                    class_name="text-[11px] font-bold text-lime-200 ml-auto",
                ),
                class_name="flex items-center gap-2 w-full",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="h-full rounded-full bg-gradient-to-r from-emerald-400 to-lime-300",
                    style={"width": row["coverage_pct"]},
                ),
                class_name="h-1.5 w-full rounded-full bg-white/10 mt-2",
            ),
            class_name="w-full mt-4",
        ),
        rx.el.div(
            _chip(f"{row['records']} enregistrement(s)"),
            _chip(f"{row['articles']} article(s)"),
            _chip(f"{row['procedures']} procédure(s)"),
            _chip(f"{row['rules']} règle(s)"),
            _chip(f"{row['faq']} question(s)"),
            _chip(f"{row['issue_count']} constat(s)"),
            class_name="flex flex-wrap items-center gap-1.5 w-full mt-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "search-check", class_name="h-3 w-3 text-lime-300/80"
                    ),
                    rx.el.span(
                        "Constats",
                        class_name="text-[9px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
                    ),
                    class_name="flex items-center gap-1.5",
                ),
                rx.el.ul(
                    rx.foreach(row["findings"], _bullet),
                    class_name="flex flex-col gap-1 w-full mt-2",
                ),
                class_name="flex-1 min-w-0 rounded-xl border border-white/10 bg-white/[0.03] p-3",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon("wrench", class_name="h-3 w-3 text-amber-300/80"),
                    rx.el.span(
                        "Recommandations",
                        class_name="text-[9px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
                    ),
                    class_name="flex items-center gap-1.5",
                ),
                rx.el.ul(
                    rx.foreach(row["recommendations"], _bullet),
                    class_name="flex flex-col gap-1 w-full mt-2",
                ),
                class_name="flex-1 min-w-0 rounded-xl border border-white/10 bg-white/[0.03] p-3",
            ),
            class_name="flex flex-col lg:flex-row gap-2 w-full mt-3",
        ),
        rx.el.a(
            rx.el.span(f"Ouvrir {row['route']}"),
            rx.icon("arrow-up-right", class_name="h-3 w-3"),
            href=row["route"],
            class_name="flex items-center gap-1.5 rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1 text-[10px] font-semibold text-lime-200 hover:bg-lime-300/20 transition-colors w-fit mt-3",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-4 hover:border-lime-300/25 transition-colors",
    )


def audit_modules() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Matrice de couverture",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Guide Agricole ↔ application",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                rx.el.p(
                    "Chaque module est confronté à ses catégories du Guide, ses entités de données et ses règles métier.",
                    class_name="text-sm font-medium text-emerald-100/55 mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{AuditState.visible_modules.length()} module(s) affiché(s)",
                class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/65 w-fit",
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.el.div(
            rx.foreach(
                AuditState.visible_modules,
                lambda row: _module_card(row, key=row["key"]),
            ),
            class_name="grid grid-cols-1 xl:grid-cols-2 gap-3 w-full mt-5",
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )


def _select(
    name: str,
    icon: str,
    value: rx.Var,
    on_change: rx.event.EventType,
    first_label: str,
    options: rx.Var,
) -> rx.Component:
    return rx.el.div(
        rx.icon(
            icon,
            class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lime-300/80 pointer-events-none",
        ),
        rx.el.select(
            rx.el.option(first_label, value="TOUS"),
            rx.foreach(
                options,
                lambda opt: rx.el.option(opt[1], value=opt[0]),
            ),
            name=name,
            value=value,
            on_change=on_change,
            class_name=_SELECT,
        ),
        rx.icon(
            "chevron-down",
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-emerald-100/40 pointer-events-none",
        ),
        class_name="relative w-full",
    )


def audit_filters() -> rx.Component:
    return rx.el.section(
        _select(
            "audit_status",
            "flag",
            AuditState.status_filter,
            AuditState.set_status_filter,
            "Tous les statuts",
            AuditState.status_options,
        ),
        _select(
            "audit_module",
            "layout-dashboard",
            AuditState.module_filter,
            AuditState.set_module_filter,
            "Tous les modules",
            AuditState.module_options,
        ),
        _select(
            "audit_domain",
            "layers",
            AuditState.domain_filter,
            AuditState.set_domain_filter,
            "Tous les domaines",
            AuditState.domain_options,
        ),
        _select(
            "audit_priority",
            "siren",
            AuditState.priority_filter,
            AuditState.set_priority_filter,
            "Toutes les priorités",
            AuditState.priority_options,
        ),
        rx.el.button(
            rx.icon("rotate-ccw", class_name="h-4 w-4"),
            rx.el.span("Réinitialiser"),
            on_click=AuditState.reset_filters,
            class_name="flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-emerald-100/70 hover:border-lime-300/30 hover:text-emerald-50 transition-colors w-full",
        ),
        class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3 w-full rounded-3xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl",
    )


def _issue_row(row: IssueRow, key: str = "") -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                _status_badge(row["tone"], row["status_label"]),
                _status_badge(row["priority_tone"], row["priority_label"]),
                class_name="flex flex-wrap items-center gap-1.5",
            ),
            class_name="px-3 py-3 align-top",
        ),
        rx.el.td(
            rx.el.p(
                row["label"],
                class_name="text-[12px] font-semibold text-emerald-50",
            ),
            rx.el.p(
                row["detail"],
                class_name="text-[11px] font-medium text-emerald-100/55 mt-1 leading-relaxed",
            ),
            rx.el.span(
                row["reference"],
                class_name="inline-block rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[9px] font-mono text-emerald-100/45 w-fit mt-2",
            ),
            class_name="px-3 py-3 align-top min-w-[18rem]",
        ),
        rx.el.td(
            rx.el.a(
                rx.el.span(row["module_label"]),
                rx.icon("arrow-up-right", class_name="h-3 w-3"),
                href=row["module_route"],
                class_name="flex items-center gap-1.5 text-[11px] font-semibold text-lime-200 hover:text-lime-100 transition-colors w-fit whitespace-nowrap",
            ),
            rx.el.span(
                row["domain_label"],
                class_name="text-[10px] font-medium text-emerald-100/45 mt-1 block",
            ),
            class_name="px-3 py-3 align-top",
        ),
        rx.el.td(
            rx.el.p(
                row["recommendation"],
                class_name="text-[11px] font-medium text-amber-100/75 leading-relaxed",
            ),
            class_name="px-3 py-3 align-top min-w-[14rem]",
        ),
        key=key,
        class_name="border-t border-white/5 hover:bg-white/[0.03] transition-colors",
    )


def _head(label: str, icon: str) -> rx.Component:
    return rx.el.th(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-lime-300/70"),
            rx.el.span(label),
            class_name="flex items-center gap-2",
        ),
        class_name="px-3 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-100/45",
    )


def audit_issues() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Incohérences détectables",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Constats et recommandations",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{AuditState.kpis['blocking']:.0f} bloquant(s)",
                    class_name="rounded-full border border-red-400/30 bg-red-500/10 px-3 py-1 text-[11px] font-bold text-red-200 w-fit",
                ),
                rx.el.span(
                    f"{AuditState.visible_issue_count} affiché(s)",
                    class_name="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold text-emerald-100/65 w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.cond(
            AuditState.has_issues,
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            _head("Statut", "flag"),
                            _head("Constat", "search-check"),
                            _head("Module", "layout-dashboard"),
                            _head("Recommandation", "wrench"),
                        ),
                        class_name="bg-white/[0.04]",
                    ),
                    rx.el.tbody(
                        rx.foreach(
                            AuditState.visible_issues,
                            lambda row: _issue_row(row, key=row["id"]),
                        )
                    ),
                    class_name="table-auto w-full",
                ),
                class_name="w-full overflow-x-auto overflow-hidden rounded-2xl border border-white/10 bg-[#04140d]/60 mt-5",
            ),
            rx.el.div(
                rx.icon("shield-check", class_name="h-6 w-6 text-lime-300"),
                rx.el.p(
                    "Aucun constat pour ce périmètre d'audit.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-2",
                ),
                class_name="flex flex-col items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] py-12 w-full mt-5",
            ),
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )


def _category_row(row: CategoryRow, key: str = "") -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.p(
                row["name"],
                class_name="text-[12px] font-semibold text-emerald-50",
            ),
            rx.el.span(
                row["key"],
                class_name="text-[9px] font-mono text-emerald-100/40",
            ),
            class_name="px-3 py-2.5 align-top",
        ),
        rx.el.td(
            rx.el.span(
                row["module_route"],
                class_name="text-[11px] font-medium text-emerald-100/55 whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-top",
        ),
        rx.el.td(
            row["articles"],
            class_name="px-3 py-2.5 text-[11px] font-semibold text-emerald-100/70",
        ),
        rx.el.td(
            row["procedures"],
            class_name="px-3 py-2.5 text-[11px] font-semibold text-emerald-100/70",
        ),
        rx.el.td(
            row["rules"],
            class_name="px-3 py-2.5 text-[11px] font-semibold text-emerald-100/70",
        ),
        rx.el.td(
            row["faq"],
            class_name="px-3 py-2.5 text-[11px] font-semibold text-emerald-100/70",
        ),
        rx.el.td(
            row["terms"],
            class_name="px-3 py-2.5 text-[11px] font-semibold text-emerald-100/70",
        ),
        rx.el.td(
            _status_badge(row["tone"], row["status_label"]),
            class_name="px-3 py-2.5 align-top",
        ),
        key=key,
        class_name="border-t border-white/5 hover:bg-white/[0.03] transition-colors",
    )


def audit_categories() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.span(
                "Couverture éditoriale",
                class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
            ),
            rx.el.h2(
                "Catégories du Guide",
                class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
            ),
            class_name="w-full",
        ),
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        _head("Catégorie", "book-open"),
                        _head("Écran", "corner-down-right"),
                        _head("Articles", "file-text"),
                        _head("Procédures", "list-checks"),
                        _head("Règles", "shield-alert"),
                        _head("Questions", "message-circle-question"),
                        _head("Termes", "book-a"),
                        _head("Statut", "flag"),
                    ),
                    class_name="bg-white/[0.04]",
                ),
                rx.el.tbody(
                    rx.foreach(
                        AuditState.categories,
                        lambda row: _category_row(row, key=row["key"]),
                    )
                ),
                class_name="table-auto w-full",
            ),
            class_name="w-full overflow-x-auto overflow-hidden rounded-2xl border border-white/10 bg-[#04140d]/60 mt-5",
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )


def _entity_card(row: EntityRow, key: str = "") -> rx.Component:
    return rx.el.div(
        _accent(row["tone"]),
        rx.el.div(
            rx.el.p(
                row["label"],
                class_name="text-[12px] font-semibold text-emerald-50 truncate",
            ),
            _status_badge(row["tone"], row["status_label"]),
            class_name="flex items-center gap-2 w-full mt-3 min-w-0",
        ),
        rx.el.span(
            row["table"],
            class_name="inline-block rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[9px] font-mono text-emerald-100/45 w-fit mt-2",
        ),
        rx.el.p(
            row["role"],
            class_name="text-[11px] font-medium text-emerald-100/50 leading-relaxed mt-2",
        ),
        rx.el.div(
            rx.el.span(
                f"{row['rows']} ligne(s)",
                class_name="text-[11px] font-bold text-lime-200",
            ),
            rx.el.span(
                row["module_label"],
                class_name="text-[10px] font-medium text-emerald-100/45 ml-auto",
            ),
            class_name="flex items-center gap-2 w-full mt-3",
        ),
        key=key,
        class_name="w-full rounded-2xl border border-white/10 bg-white/[0.03] p-3",
    )


def audit_entities() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Entités de données",
                    class_name="text-[10px] font-semibold uppercase tracking-[0.28em] text-lime-300/80",
                ),
                rx.el.h2(
                    "Volumes observés en base",
                    class_name="font-['Instrument_Serif'] text-3xl text-emerald-50 mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{AuditState.kpis['records']:.0f} enregistrement(s)",
                    class_name="rounded-full border border-lime-300/25 bg-lime-300/10 px-3 py-1 text-[11px] font-bold text-lime-200 w-fit",
                ),
                rx.el.span(
                    f"{AuditState.kpis['empty_entities']:.0f} table(s) vide(s)",
                    class_name="rounded-full border border-amber-300/25 bg-amber-300/10 px-3 py-1 text-[11px] font-semibold text-amber-200 w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-wrap items-end justify-between gap-3 w-full",
        ),
        rx.el.div(
            rx.foreach(
                AuditState.entities,
                lambda row: _entity_card(row, key=row["table"]),
            ),
            class_name="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 w-full mt-5",
        ),
        class_name="w-full rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl",
    )


def audit_skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(class_name="animate-pulse h-24 rounded-3xl bg-white/[0.05]"),
        rx.el.div(class_name="animate-pulse h-64 rounded-3xl bg-white/[0.05]"),
        rx.el.div(class_name="animate-pulse h-48 rounded-3xl bg-white/[0.05]"),
        class_name="flex flex-col gap-4 w-full",
    )

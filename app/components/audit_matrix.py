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
    "w-full appearance-none cursor-pointer rounded-none border border-[#f2efe4]/12 "
    "bg-[#0A0A08] py-2.5 pl-9 pr-9 text-sm font-medium text-[#f2efe4] "
    "focus:border-[#d8fa5e]/50 focus:ring-2 focus:ring-[#d8fa5e]/20 "
    "outline-hidden transition-colors"
)


def _status_badge(tone: rx.Var, label: rx.Var) -> rx.Component:
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


def _accent(tone: rx.Var) -> rx.Component:
    return rx.el.div(
        class_name=rx.match(
            tone,
            ("good", "h-1 w-full rounded-none bg-[#d8fa5e]/80"),
            ("warn", "h-1 w-full rounded-none bg-[#ff8a5b]/80"),
            ("bad", "h-1 w-full rounded-none bg-[#ff6b5a]/80"),
            "h-1 w-full rounded-none bg-[#262b1e]",
        )
    )


def _stat(label: str, value: rx.Var | str, unit: str) -> rx.Component:
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
        class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/60 w-fit",
    )


def _bullet(label: rx.Var) -> rx.Component:
    return rx.el.li(
        label,
        class_name="text-[11px] font-medium text-[#c9c5b4]/65 leading-relaxed list-disc ml-4",
    )


def _module_card(row: ModuleRow, key: str = "") -> rx.Component:
    return rx.el.article(
        _accent(row["tone"]),
        rx.el.div(
            rx.el.div(
                rx.icon(row["icon"], class_name="h-4 w-4 text-[#d8fa5e]"),
                class_name="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10",
            ),
            rx.el.div(
                rx.el.p(
                    row["label"],
                    class_name="text-sm font-semibold text-[#f2efe4]",
                ),
                rx.el.p(
                    row["mission"],
                    class_name="text-[11px] font-medium text-[#c9c5b4]/50 mt-1",
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
                    class_name="ap-eyebrow text-[#c9c5b4]/45",
                ),
                rx.el.span(
                    row["coverage_pct"],
                    class_name="text-[11px] font-bold text-[#e4ff9b] ml-auto",
                ),
                class_name="flex items-center gap-2 w-full",
            ),
            rx.el.div(
                rx.el.div(
                    class_name="h-full rounded-none bg-gradient-to-r from-[#8fb37a] to-[#d8fa5e]",
                    style={"width": row["coverage_pct"]},
                ),
                class_name="h-1.5 w-full rounded-none bg-[#20241a] mt-2",
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
                        "search-check", class_name="h-3 w-3 text-[#d8fa5e]/80"
                    ),
                    rx.el.span(
                        "Constats",
                        class_name="ap-eyebrow text-[#c9c5b4]/45",
                    ),
                    class_name="flex items-center gap-1.5",
                ),
                rx.el.ul(
                    rx.foreach(row["findings"], _bullet),
                    class_name="flex flex-col gap-1 w-full mt-2",
                ),
                class_name="flex-1 min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon("wrench", class_name="h-3 w-3 text-[#ff8a5b]/80"),
                    rx.el.span(
                        "Recommandations",
                        class_name="ap-eyebrow text-[#c9c5b4]/45",
                    ),
                    class_name="flex items-center gap-1.5",
                ),
                rx.el.ul(
                    rx.foreach(row["recommendations"], _bullet),
                    class_name="flex flex-col gap-1 w-full mt-2",
                ),
                class_name="flex-1 min-w-0 rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
            ),
            class_name="flex flex-col lg:flex-row gap-2 w-full mt-3",
        ),
        rx.el.a(
            rx.el.span(f"Ouvrir {row['route']}"),
            rx.icon("arrow-up-right", class_name="h-3 w-3"),
            href=row["route"],
            class_name="flex items-center gap-1.5 rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10 px-3 py-1 text-[10px] font-semibold text-[#e4ff9b] hover:bg-[#d8fa5e]/20 transition-colors w-fit mt-3",
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 hover:border-[#d8fa5e]/25 transition-colors",
    )


def audit_modules() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Matrice de couverture",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Guide Agricole ↔ application",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                rx.el.p(
                    "Chaque module est confronté à ses catégories du Guide, ses entités de données et ses règles métier.",
                    class_name="text-sm font-medium text-[#c9c5b4]/55 mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.span(
                f"{AuditState.visible_modules.length()} module(s) affiché(s)",
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/65 w-fit",
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
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
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
            class_name="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#d8fa5e]/80 pointer-events-none",
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
            class_name="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#c9c5b4]/40 pointer-events-none",
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
            class_name="flex items-center justify-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2.5 text-sm font-semibold text-[#c9c5b4]/70 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-full",
        ),
        class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3 w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-5 ",
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
                class_name="text-[12px] font-semibold text-[#f2efe4]",
            ),
            rx.el.p(
                row["detail"],
                class_name="text-[11px] font-medium text-[#c9c5b4]/55 mt-1 leading-relaxed",
            ),
            rx.el.span(
                row["reference"],
                class_name="inline-block rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[9px] font-mono text-[#c9c5b4]/45 w-fit mt-2",
            ),
            class_name="px-3 py-3 align-top min-w-[18rem]",
        ),
        rx.el.td(
            rx.el.a(
                rx.el.span(row["module_label"]),
                rx.icon("arrow-up-right", class_name="h-3 w-3"),
                href=row["module_route"],
                class_name="flex items-center gap-1.5 text-[11px] font-semibold text-[#e4ff9b] hover:text-[#efffc4] transition-colors w-fit whitespace-nowrap",
            ),
            rx.el.span(
                row["domain_label"],
                class_name="text-[10px] font-medium text-[#c9c5b4]/45 mt-1 block",
            ),
            class_name="px-3 py-3 align-top",
        ),
        rx.el.td(
            rx.el.p(
                row["recommendation"],
                class_name="text-[11px] font-medium text-[#ffdccb]/75 leading-relaxed",
            ),
            class_name="px-3 py-3 align-top min-w-[14rem]",
        ),
        key=key,
        class_name="border-t border-[#f2efe4]/8 hover:bg-[#101208] transition-colors",
    )


def _head(label: str, icon: str) -> rx.Component:
    return rx.el.th(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-[#d8fa5e]/70"),
            rx.el.span(label),
            class_name="flex items-center gap-2",
        ),
        class_name="px-3 py-3 text-left ap-eyebrow text-[#c9c5b4]/45",
    )


def audit_issues() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Incohérences détectables",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Constats et recommandations",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{AuditState.kpis['blocking']:.0f} bloquant(s)",
                    class_name="rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-3 py-1 text-[11px] font-bold text-[#ffbcb0] w-fit",
                ),
                rx.el.span(
                    f"{AuditState.visible_issue_count} affiché(s)",
                    class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-3 py-1 text-[11px] font-semibold text-[#c9c5b4]/65 w-fit",
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
                        class_name="bg-[#14160f]",
                    ),
                    rx.el.tbody(
                        rx.foreach(
                            AuditState.visible_issues,
                            lambda row: _issue_row(row, key=row["id"]),
                        )
                    ),
                    class_name="table-auto w-full",
                ),
                class_name="w-full overflow-x-auto overflow-hidden rounded-none border border-[#f2efe4]/12 bg-[#0A0A08]/60 mt-5",
            ),
            rx.el.div(
                rx.icon("shield-check", class_name="h-6 w-6 text-[#d8fa5e]"),
                rx.el.p(
                    "Aucun constat pour ce périmètre d'audit.",
                    class_name="text-sm font-medium text-[#c9c5b4]/60 mt-2",
                ),
                class_name="flex flex-col items-center justify-center rounded-none border border-[#f2efe4]/12 bg-[#101208] py-12 w-full mt-5",
            ),
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )


def _category_row(row: CategoryRow, key: str = "") -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.p(
                row["name"],
                class_name="text-[12px] font-semibold text-[#f2efe4]",
            ),
            rx.el.span(
                row["key"],
                class_name="text-[9px] font-mono text-[#c9c5b4]/40",
            ),
            class_name="px-3 py-2.5 align-top",
        ),
        rx.el.td(
            rx.el.span(
                row["module_route"],
                class_name="text-[11px] font-medium text-[#c9c5b4]/55 whitespace-nowrap",
            ),
            class_name="px-3 py-2.5 align-top",
        ),
        rx.el.td(
            row["articles"],
            class_name="px-3 py-2.5 text-[11px] font-semibold text-[#c9c5b4]/70",
        ),
        rx.el.td(
            row["procedures"],
            class_name="px-3 py-2.5 text-[11px] font-semibold text-[#c9c5b4]/70",
        ),
        rx.el.td(
            row["rules"],
            class_name="px-3 py-2.5 text-[11px] font-semibold text-[#c9c5b4]/70",
        ),
        rx.el.td(
            row["faq"],
            class_name="px-3 py-2.5 text-[11px] font-semibold text-[#c9c5b4]/70",
        ),
        rx.el.td(
            row["terms"],
            class_name="px-3 py-2.5 text-[11px] font-semibold text-[#c9c5b4]/70",
        ),
        rx.el.td(
            _status_badge(row["tone"], row["status_label"]),
            class_name="px-3 py-2.5 align-top",
        ),
        key=key,
        class_name="border-t border-[#f2efe4]/8 hover:bg-[#101208] transition-colors",
    )


def audit_categories() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.span(
                "Couverture éditoriale",
                class_name="ap-eyebrow text-[#d8fa5e]/80",
            ),
            rx.el.h2(
                "Catégories du Guide",
                class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
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
                    class_name="bg-[#14160f]",
                ),
                rx.el.tbody(
                    rx.foreach(
                        AuditState.categories,
                        lambda row: _category_row(row, key=row["key"]),
                    )
                ),
                class_name="table-auto w-full",
            ),
            class_name="w-full overflow-x-auto overflow-hidden rounded-none border border-[#f2efe4]/12 bg-[#0A0A08]/60 mt-5",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )


def _entity_card(row: EntityRow, key: str = "") -> rx.Component:
    return rx.el.div(
        _accent(row["tone"]),
        rx.el.div(
            rx.el.p(
                row["label"],
                class_name="text-[12px] font-semibold text-[#f2efe4] truncate",
            ),
            _status_badge(row["tone"], row["status_label"]),
            class_name="flex items-center gap-2 w-full mt-3 min-w-0",
        ),
        rx.el.span(
            row["table"],
            class_name="inline-block rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[9px] font-mono text-[#c9c5b4]/45 w-fit mt-2",
        ),
        rx.el.p(
            row["role"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/50 leading-relaxed mt-2",
        ),
        rx.el.div(
            rx.el.span(
                f"{row['rows']} ligne(s)",
                class_name="text-[11px] font-bold text-[#e4ff9b]",
            ),
            rx.el.span(
                row["module_label"],
                class_name="text-[10px] font-medium text-[#c9c5b4]/45 ml-auto",
            ),
            class_name="flex items-center gap-2 w-full mt-3",
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-3",
    )


def audit_entities() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Entités de données",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Volumes observés en base",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.span(
                    f"{AuditState.kpis['records']:.0f} enregistrement(s)",
                    class_name="rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10 px-3 py-1 text-[11px] font-bold text-[#e4ff9b] w-fit",
                ),
                rx.el.span(
                    f"{AuditState.kpis['empty_entities']:.0f} table(s) vide(s)",
                    class_name="rounded-none border border-[#ff8a5b]/25 bg-[#ff8a5b]/10 px-3 py-1 text-[11px] font-semibold text-[#ffb894] w-fit",
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
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )


def audit_skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(class_name="animate-pulse h-24 rounded-none bg-[#16190f]"),
        rx.el.div(class_name="animate-pulse h-64 rounded-none bg-[#16190f]"),
        rx.el.div(class_name="animate-pulse h-48 rounded-none bg-[#16190f]"),
        class_name="flex flex-col gap-4 w-full",
    )

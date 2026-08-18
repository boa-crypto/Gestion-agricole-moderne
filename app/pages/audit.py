import reflex as rx

from app.components.audit_matrix import (
    audit_categories,
    audit_entities,
    audit_filters,
    audit_issues,
    audit_kpis,
    audit_modules,
    audit_skeleton,
)
from app.components.audit_diagnostic import (
    diagnostic_actions,
    diagnostic_synthesis,
    diagnostic_triage,
    diagnostic_watchlist,
)
from app.components.audit_security import audit_security_panel
from app.components.contour_control import contour_diagnostic_tile
from app.components.phenology_audit import phenology_audit_panel
from app.components.guide_help import help_button
from app.components.remediation_panels import (
    alert_triage_panel,
    contour_validation_panel,
    remediation_summary,
    stock_decision_panel,
)
from app.components.catalog_bridge import catalog_shortcut
from app.components.side_rail import side_rail
from app.components.stock_control import stock_diagnostic_tile
from app.states.audit_state import AuditState


def _space_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "clipboard-check", class_name="h-4 w-4 text-lime-300"
                    ),
                    rx.el.span(
                        "Audit fonctionnel CMS²",
                        class_name="text-[11px] font-semibold uppercase tracking-[0.32em] text-lime-300/90",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "Cartographie AgriPro ↔ Guide",
                    class_name="font-['Instrument_Serif'] text-4xl md:text-5xl leading-[1.05] text-emerald-50 mt-3",
                ),
                rx.el.p(
                    "Modules existants, entités de données, routes, liens guide → application, catégories, règles métier, procédures et incohérences détectables, avec statuts normalisés et priorités.",
                    class_name="text-sm font-medium text-emerald-100/60 mt-3 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "calendar-days", class_name="h-3.5 w-3.5 text-lime-300"
                    ),
                    rx.el.span(
                        AuditState.generated_label,
                        class_name="text-xs font-medium text-emerald-50/80",
                    ),
                    class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 backdrop-blur-xl w-fit",
                ),
                rx.el.div(
                    rx.icon(
                        "octagon-alert",
                        class_name="h-3.5 w-3.5 text-amber-300",
                    ),
                    rx.el.span(
                        f"{AuditState.kpis['issues']:.0f} constat(s)",
                        class_name="text-xs font-medium text-emerald-50/80",
                    ),
                    class_name="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 backdrop-blur-xl w-fit",
                ),
                help_button("guide", "Guide de lecture"),
                rx.el.button(
                    rx.cond(
                        AuditState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#04140d]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#04140d]"
                        ),
                    ),
                    rx.el.span("Relancer l'audit", class_name="text-[#04140d]"),
                    on_click=AuditState.load_audit,
                    class_name="flex items-center gap-2 rounded-full bg-lime-300 px-4 py-2 text-sm font-semibold hover:bg-lime-200 transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full",
        ),
        class_name="w-full border-b border-white/10 pb-8 mt-6",
    )


def _body() -> rx.Component:
    return rx.el.div(
        audit_kpis(),
        diagnostic_synthesis(),
        diagnostic_triage(),
        audit_filters(),
        diagnostic_watchlist(),
        diagnostic_actions(),
        remediation_summary(),
        contour_diagnostic_tile(),
        stock_diagnostic_tile(),
        alert_triage_panel(),
        stock_decision_panel(),
        contour_validation_panel(),
        phenology_audit_panel(),
        audit_security_panel(),
        audit_modules(),
        audit_issues(),
        audit_categories(),
        audit_entities(),
        class_name="flex flex-col gap-4 w-full",
    )


def audit_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            class_name="pointer-events-none fixed inset-0 z-0 bg-gradient-to-b from-[#04120c]/35 via-[#04120c]/45 to-[#020a07]/60",
        ),
        rx.el.div(
            side_rail("audit"),
            catalog_shortcut("audit"),
            _space_header(),
            rx.el.div(
                rx.cond(AuditState.is_loading, audit_skeleton(), _body()),
                class_name="w-full mt-8",
            ),
            class_name="relative z-10 w-full max-w-[110rem] mx-auto px-4 sm:px-8 md:pl-24 lg:pl-28 py-10 pb-28 md:pb-10",
        ),
        class_name="relative min-h-screen w-full font-['Inter'] bg-[#04120c] bg-[url('/wide_cinematic_background.png')] bg-cover bg-center bg-fixed text-emerald-50 antialiased",
    )

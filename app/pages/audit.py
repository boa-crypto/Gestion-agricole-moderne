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
from app.components.stock_control import stock_diagnostic_tile
from app.components.shell import app_shell
from app.states.audit_state import AuditState


def _space_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "clipboard-check", class_name="h-4 w-4 text-[#d8fa5e]"
                    ),
                    rx.el.span(
                        "Audit fonctionnel CMS²",
                        class_name="ap-eyebrow text-[#D8FA5E]",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.h1(
                    "Cartographie AgriPro ↔ Guide",
                    class_name="ap-display text-[clamp(2.4rem,4.6vw,4.1rem)] text-[#f2efe4] mt-3",
                ),
                rx.el.p(
                    "Modules existants, entités de données, routes, liens guide → application, catégories, règles métier, procédures et incohérences détectables, avec statuts normalisés et priorités.",
                    class_name="mt-4 text-[13px] leading-relaxed text-[#C9C5B4]/70 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "calendar-days", class_name="h-3.5 w-3.5 text-[#d8fa5e]"
                    ),
                    rx.el.span(
                        AuditState.generated_label,
                        class_name="text-xs font-medium text-[#f2efe4]/80",
                    ),
                    class_name="ap-mono inline-flex w-fit items-center gap-2 border border-[#F2EFE4]/12 px-3 py-2 text-[9px] uppercase tracking-[0.18em] text-[#C9C5B4]",
                ),
                rx.el.div(
                    rx.icon(
                        "octagon-alert",
                        class_name="h-3.5 w-3.5 text-[#ff8a5b]",
                    ),
                    rx.el.span(
                        f"{AuditState.kpis['issues']:.0f} constat(s)",
                        class_name="text-xs font-medium text-[#f2efe4]/80",
                    ),
                    class_name="ap-mono inline-flex w-fit items-center gap-2 border border-[#F2EFE4]/12 px-3 py-2 text-[9px] uppercase tracking-[0.18em] text-[#C9C5B4]",
                ),
                help_button("guide", "Guide de lecture"),
                rx.el.button(
                    rx.cond(
                        AuditState.is_loading,
                        rx.icon(
                            "loader-circle",
                            class_name="h-4 w-4 animate-spin text-[#0A0A08]",
                        ),
                        rx.icon(
                            "refresh-cw", class_name="h-4 w-4 text-[#0A0A08]"
                        ),
                    ),
                    rx.el.span("Relancer l'audit", class_name="text-[#0A0A08]"),
                    on_click=AuditState.load_audit,
                    class_name="ap-mono inline-flex w-fit items-center gap-2 bg-[#D8FA5E] px-4 py-2.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[#0A0A08] transition-colors hover:bg-[#E4FF9B]",
                ),
                class_name="flex flex-wrap items-center gap-2 md:justify-end",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full",
        ),
        class_name="w-full border-b border-[#F2EFE4]/12 pb-8",
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
    return app_shell(
        rx.el.div(
            catalog_shortcut("audit"),
            _space_header(),
            rx.el.div(
                rx.cond(AuditState.is_loading, audit_skeleton(), _body()),
                class_name="w-full mt-8",
            ),
            class_name="flex w-full flex-col gap-6",
        ),
        "audit",
    )

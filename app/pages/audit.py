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
from app.components.design import meta_ledger, meta_row, page_hero, refresh_button
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
    return page_hero(
        "Audit fonctionnel CMS²",
        "Cartographie AgriPro ↔ Guide",
        "Modules existants, entités de données, routes, liens guide → application, catégories, règles métier, procédures et incohérences détectables, avec statuts normalisés et priorités.",
        meta=meta_ledger(
            meta_row("Relevé", AuditState.generated_label),
            meta_row("Constats", f"{AuditState.kpis['issues']:.0f}", tone="flame"),
        ),
        actions=rx.el.div(
            help_button("guide", "Guide de lecture"),
            refresh_button(
                on_click=AuditState.load_audit,
                loading=AuditState.is_loading,
                label="Relancer l'audit",
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
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

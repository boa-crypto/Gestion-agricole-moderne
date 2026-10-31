"""Bloc « Audit sécurité » : RBAC, MFA, délégations, évènements sensibles."""

import reflex as rx

from app.security_audit import SecurityEvent, SecurityFinding
from app.states.security_audit_state import SecurityAuditState


def _tone_badge(label: rx.Var | str, tone: rx.Var | str) -> rx.Component:
    return rx.el.span(
        label,
        class_name=rx.match(
            tone,
            (
                "good",
                "rounded-none border border-[#d8fa5e]/30 bg-[#d8fa5e]/10 px-2 py-0.5 text-[10px] font-bold text-[#e4ff9b] w-fit",
            ),
            (
                "warn",
                "rounded-none border border-[#ff8a5b]/30 bg-[#ff8a5b]/10 px-2 py-0.5 text-[10px] font-bold text-[#ffb894] w-fit",
            ),
            (
                "bad",
                "rounded-none border border-[#ff6b5a]/30 bg-[#f2452c]/10 px-2 py-0.5 text-[10px] font-bold text-[#ff9b8c] w-fit",
            ),
            (
                "info",
                "rounded-none border border-[#9cc3ff]/30 bg-[#9cc3ff]/10 px-2 py-0.5 text-[10px] font-bold text-[#c3daff] w-fit",
            ),
            "rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/50 w-fit",
        ),
    )


def _tile(
    label: str, value: rx.Var | str, unit: str, caption: rx.Var | str, icon: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                label,
                class_name="ap-eyebrow text-[#c9c5b4]/45",
            ),
            rx.icon(icon, class_name="h-4 w-4 text-[#d8fa5e]"),
            class_name="flex items-start justify-between gap-2",
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
            class_name="flex items-end gap-1.5 mt-3",
        ),
        rx.el.p(
            caption,
            class_name="text-[10px] font-medium text-[#c9c5b4]/40 mt-2",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#14160f] p-4",
    )


def _finding(item: SecurityFinding, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(item["icon"], class_name="h-4 w-4 text-[#ff8a5b] shrink-0"),
            rx.el.p(
                item["label"],
                class_name="text-sm font-semibold text-[#f2efe4] truncate",
            ),
            _tone_badge(item["value"].to_string(), item["tone"]),
            class_name="flex items-center gap-2 min-w-0",
        ),
        rx.el.p(
            item["detail"],
            class_name="text-[11px] font-medium text-[#c9c5b4]/60 mt-2 leading-relaxed",
        ),
        rx.el.p(
            item["recommendation"],
            class_name="text-[11px] font-medium text-[#ffdccb]/75 mt-2",
        ),
        rx.el.span(
            item["reference"],
            class_name="inline-block rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[9px] font-mono text-[#c9c5b4]/45 w-fit mt-2",
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4 hover:border-[#d8fa5e]/25 transition-colors",
    )


def _event(item: SecurityEvent, key: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _tone_badge(item["kind"], item["tone"]),
            rx.el.span(
                item["module"] + " · " + item["action"],
                class_name="text-[11px] font-semibold text-[#c9c5b4]/55 truncate",
            ),
            rx.el.span(
                item["when"],
                class_name="text-[10px] font-medium text-[#c9c5b4]/40 ml-auto shrink-0",
            ),
            class_name="flex items-center gap-2 w-full min-w-0",
        ),
        rx.el.p(
            item["summary"],
            class_name="text-sm font-medium text-[#f2efe4]/85 mt-1",
        ),
        rx.el.div(
            rx.icon("user", class_name="h-3 w-3 text-[#d8fa5e]/70"),
            rx.el.span(
                item["actor"],
                class_name="text-[10px] font-semibold text-[#c9c5b4]/50",
            ),
            rx.el.span(
                item["object_ref"],
                class_name="rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-2 py-0.5 text-[10px] font-semibold text-[#c9c5b4]/55 w-fit",
            ),
            class_name="flex flex-wrap items-center gap-2 mt-2",
        ),
        key=key,
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-4",
    )


def audit_security_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "Audit sécurité",
                    class_name="ap-eyebrow text-[#d8fa5e]/80",
                ),
                rx.el.h2(
                    "Utilisateurs, rôles & permissions",
                    class_name="ap-serif text-3xl text-[#f2efe4] mt-1",
                ),
                rx.el.p(
                    "Couverture RBAC, second facteur, périmètres agricoles, permissions temporaires et évènements sensibles du journal.",
                    class_name="text-sm font-medium text-[#c9c5b4]/55 mt-2 max-w-2xl",
                ),
                class_name="min-w-0",
            ),
            rx.el.div(
                _tone_badge(
                    SecurityAuditState.verdict_label,
                    SecurityAuditState.verdict_tone,
                ),
                rx.el.a(
                    rx.el.span("Ouvrir l'administration"),
                    rx.icon("arrow-up-right", class_name="h-3 w-3"),
                    href="/administration",
                    class_name="flex items-center gap-1.5 rounded-none border border-[#d8fa5e]/25 bg-[#d8fa5e]/10 px-3 py-1 text-[11px] font-semibold text-[#e4ff9b] hover:bg-[#d8fa5e]/20 transition-colors w-fit",
                ),
                rx.el.button(
                    rx.icon("refresh-cw", class_name="h-4 w-4"),
                    rx.el.span("Relancer"),
                    on_click=SecurityAuditState.load_security,
                    class_name="flex items-center gap-2 rounded-none border border-[#f2efe4]/12 bg-[#14160f] px-4 py-2 text-sm font-semibold text-[#c9c5b4]/70 hover:border-[#d8fa5e]/30 hover:text-[#f2efe4] transition-colors w-fit",
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col lg:flex-row lg:items-end justify-between gap-4 w-full",
        ),
        rx.el.div(
            _tile(
                "Comptes actifs",
                SecurityAuditState.kpis["active_users"],
                "sur "
                + SecurityAuditState.kpis["users"].to_string()
                + " comptes",
                SecurityAuditState.kpis["inactive_users"].to_string()
                + " compte(s) inactif(s) ou suspendu(s)",
                "users-round",
            ),
            _tile(
                "Couverture RBAC",
                f"{SecurityAuditState.kpis['rbac_coverage']:.1f}",
                "%",
                SecurityAuditState.rbac_label,
                "key-round",
            ),
            _tile(
                "Second facteur",
                f"{SecurityAuditState.kpis['mfa_coverage']:.0f}",
                "% MFA",
                SecurityAuditState.mfa_label,
                "shield-check",
            ),
            _tile(
                "Délégations actives",
                SecurityAuditState.kpis["active_delegations"],
                "permissions temporaires",
                SecurityAuditState.kpis["expiring_delegations"].to_string()
                + " échéance(s) sous 7 jours",
                "hourglass",
            ),
            _tile(
                "Actions sensibles",
                SecurityAuditState.kpis["sensitive_permissions"],
                "module × action",
                SecurityAuditState.kpis["sensitive_events"].to_string()
                + " évènement(s) sensible(s) journalisé(s)",
                "siren",
            ),
            _tile(
                "Accès refusés",
                SecurityAuditState.kpis["denials_30d"],
                "sur 30 jours",
                SecurityAuditState.kpis["events_30d"].to_string()
                + " évènement(s) tracé(s) sur la période",
                "octagon-alert",
            ),
            class_name="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3 w-full mt-5",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "Constats de sécurité",
                    class_name="ap-eyebrow text-[#c9c5b4]/40",
                ),
                rx.el.div(
                    rx.foreach(
                        SecurityAuditState.findings,
                        lambda item: _finding(item, key=item["id"]),
                    ),
                    class_name="flex flex-col gap-3 mt-3",
                ),
                class_name="flex-1 min-w-0",
            ),
            rx.el.div(
                rx.el.p(
                    "Évènements sensibles & refus",
                    class_name="ap-eyebrow text-[#c9c5b4]/40",
                ),
                rx.cond(
                    SecurityAuditState.events.length() > 0,
                    rx.el.div(
                        rx.foreach(
                            SecurityAuditState.events,
                            lambda item: _event(
                                item, key=item["id"].to_string()
                            ),
                        ),
                        class_name="flex flex-col gap-3 mt-3 max-h-[34rem] overflow-y-auto pr-1",
                    ),
                    rx.el.p(
                        "Aucun évènement sensible consigné.",
                        class_name="text-sm font-medium text-[#c9c5b4]/50 mt-3",
                    ),
                ),
                class_name="w-full xl:w-[28rem] shrink-0",
            ),
            class_name="flex flex-col xl:flex-row gap-6 w-full mt-6 border-t border-[#f2efe4]/12 pt-6",
        ),
        class_name="w-full rounded-none border border-[#f2efe4]/12 bg-[#101208] p-6 ",
    )

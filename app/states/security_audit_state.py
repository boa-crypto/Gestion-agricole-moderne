"""État du bloc « Audit sécurité » de l'audit fonctionnel AgriPro."""

from __future__ import annotations

import reflex as rx

from app.security_audit import (
    SecurityEvent,
    SecurityFinding,
    SecurityKpis,
    empty_security_kpis,
    load_security_audit,
    load_security_events,
)


# Poids de tri : les constats bloquants d'abord, puis les avertissements.
_TONE_WEIGHT: dict[str, int] = {"bad": 0, "warn": 1, "info": 2, "good": 3}


class SecurityAuditState(rx.State):
    """Indicateurs RBAC, MFA, délégations et évènements sensibles."""

    is_loading: bool = True
    kpis: SecurityKpis = empty_security_kpis()
    findings: list[SecurityFinding] = []
    # Alias stable attendu par l'audit sécurité final : mêmes constats que
    # `findings`, triés par gravité décroissante. Toujours une liste.
    risks: list[SecurityFinding] = []
    events: list[SecurityEvent] = []
    show_sensitive_only: bool = True

    @rx.var
    def finding_count(self) -> int:
        return len(self.findings)

    @rx.var
    def risk_count(self) -> int:
        return len(self.risks)

    @rx.var
    def has_risks(self) -> bool:
        return len(self.risks) > 0

    @rx.var
    def event_count(self) -> int:
        return len(self.events)

    @rx.var
    def sensitive_events(self) -> list[SecurityEvent]:
        return [item for item in self.events if item["sensitive"]]

    @rx.var
    def denial_events(self) -> list[SecurityEvent]:
        return [item for item in self.events if item["tone"] == "bad"]

    @rx.var
    def blocking_findings(self) -> int:
        return len([f for f in self.findings if f["tone"] == "bad"])

    @rx.var
    def mfa_label(self) -> str:
        return f"{self.kpis['mfa_enabled']:.0f} compte(s) protégé(s) par MFA"

    @rx.var
    def rbac_label(self) -> str:
        return (
            f"{self.kpis['grants']:.0f} liaisons rôle × permission accordées "
            f"sur {self.kpis['roles']:.0f} rôles"
        )

    @rx.var
    def verdict_tone(self) -> str:
        if self.blocking_findings > 0:
            return "bad"
        if len([f for f in self.findings if f["tone"] == "warn"]) > 0:
            return "warn"
        return "good"

    @rx.var
    def verdict_label(self) -> str:
        tone = self.verdict_tone
        if tone == "bad":
            return "Accès à sécuriser"
        if tone == "warn":
            return "Revue des accès à planifier"
        return "Socle de sécurité conforme"

    @rx.event
    async def load_security(self):
        self.is_loading = True
        yield
        self.kpis, self.findings = await load_security_audit()
        # `risks` reste systématiquement synchronisé avec l'analyse RBAC.
        self.risks = sorted(
            self.findings,
            key=lambda item: (
                _TONE_WEIGHT.get(item["tone"], 9),
                -int(item["value"]),
                str(item["label"]),
            ),
        )
        # Évènements sensibles et refus lus depuis `agripro_activity_log`.
        self.events = await load_security_events(14)
        self.is_loading = False

"""Audit sécurité du module utilisateurs AgriPro (lecture seule).

Toutes les lectures passent par le socle `agripro_*` en SQL brut via
`rx.asession()` : aucune écriture, aucune migration. Ce module alimente le bloc
« Audit sécurité » de l'audit fonctionnel avec des indicateurs RBAC, MFA,
délégations et évènements sensibles, ainsi que des constats lisibles.
"""

from __future__ import annotations

import datetime
import logging
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.access_control import expire_stale_delegations
from app.database import ensure_local_database

__all__ = [
    "SecurityFinding",
    "SecurityKpis",
    "empty_security_kpis",
    "load_security_audit",
    "load_security_events",
]


class SecurityKpis(TypedDict):
    users: float
    active_users: float
    inactive_users: float
    users_without_role: float
    users_without_scope: float
    full_scope_users: float
    roles: float
    permissions: float
    grants: float
    sensitive_permissions: float
    rbac_coverage: float
    mfa_enabled: float
    mfa_coverage: float
    mfa_missing_privileged: float
    active_delegations: float
    expiring_delegations: float
    stale_delegations: float
    sensitive_events: float
    denials_30d: float
    events_30d: float
    activities: float


class SecurityFinding(TypedDict):
    id: str
    label: str
    detail: str
    reference: str
    tone: str
    icon: str
    value: int
    recommendation: str


class SecurityEvent(TypedDict):
    id: int
    actor: str
    kind: str
    module: str
    action: str
    object_ref: str
    summary: str
    when: str
    sensitive: bool
    tone: str


def empty_security_kpis() -> SecurityKpis:
    return {
        "users": 0.0,
        "active_users": 0.0,
        "inactive_users": 0.0,
        "users_without_role": 0.0,
        "users_without_scope": 0.0,
        "full_scope_users": 0.0,
        "roles": 0.0,
        "permissions": 0.0,
        "grants": 0.0,
        "sensitive_permissions": 0.0,
        "rbac_coverage": 0.0,
        "mfa_enabled": 0.0,
        "mfa_coverage": 0.0,
        "mfa_missing_privileged": 0.0,
        "active_delegations": 0.0,
        "expiring_delegations": 0.0,
        "stale_delegations": 0.0,
        "sensitive_events": 0.0,
        "denials_30d": 0.0,
        "events_30d": 0.0,
        "activities": 0.0,
    }


_SNAPSHOT_SQL: str = """
    SELECT
        (SELECT COUNT(*) FROM agripro_user),
        (SELECT COUNT(*) FROM agripro_user WHERE status = 'ACTIF'),
        (SELECT COUNT(*) FROM agripro_user WHERE status <> 'ACTIF'),
        (SELECT COUNT(*) FROM agripro_user u
          WHERE NOT EXISTS (SELECT 1 FROM agripro_user_role ur
                             WHERE ur.user_id = u.id)),
        (SELECT COUNT(*) FROM agripro_user u
          WHERE NOT EXISTS (SELECT 1 FROM agripro_scope s
                             WHERE s.user_id = u.id)),
        (SELECT COUNT(*) FROM agripro_scope
          WHERE scope_kind = 'EXPLOITATION'),
        (SELECT COUNT(*) FROM agripro_role),
        (SELECT COUNT(*) FROM agripro_permission),
        (SELECT COUNT(*) FROM agripro_role_permission WHERE is_granted = 1),
        (SELECT COUNT(*) FROM agripro_permission WHERE is_sensitive = 1),
        (SELECT COUNT(*) FROM agripro_user WHERE mfa_enabled = 1),
        (SELECT COUNT(*) FROM agripro_user u
           JOIN agripro_role r ON r.id = u.role_id
          WHERE u.status = 'ACTIF' AND COALESCE(r.level, 0) >= 60
            AND u.mfa_enabled = 0),
        (SELECT COUNT(*) FROM agripro_delegation WHERE status = 'ACTIVE'),
        (SELECT COUNT(*) FROM agripro_delegation
          WHERE status = 'ACTIVE' AND end_date IS NOT NULL
            AND end_date <= :soon),
        (SELECT COUNT(*) FROM agripro_delegation
          WHERE status IN ('ACTIVE', 'PLANIFIEE') AND end_date IS NOT NULL
            AND end_date < :today),
        (SELECT COUNT(*) FROM agripro_activity_log WHERE is_sensitive = 1),
        (SELECT COUNT(*) FROM agripro_activity_log
          WHERE kind = 'REFUS'
            AND DATE(COALESCE(occurred_at, created_at)) >= :window),
        (SELECT COUNT(*) FROM agripro_activity_log
          WHERE DATE(COALESCE(occurred_at, created_at)) >= :window),
        (SELECT COUNT(*) FROM agripro_activity_log)
"""


async def load_security_audit() -> tuple[SecurityKpis, list[SecurityFinding]]:
    """Indicateurs de sécurité et constats associés (RBAC, MFA, délégations)."""
    await ensure_local_database()
    await expire_stale_delegations()
    kpis = empty_security_kpis()
    findings: list[SecurityFinding] = []
    today = datetime.date.today()
    try:
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(_SNAPSHOT_SQL),
                    {
                        "today": today,
                        "soon": today + datetime.timedelta(days=7),
                        "window": today - datetime.timedelta(days=30),
                    },
                )
            ).first()
    except Exception as e:  # noqa: BLE001
        logging.exception(f"Error: {e}")
        return kpis, findings

    if row is None:
        return kpis, findings

    order = [
        "users",
        "active_users",
        "inactive_users",
        "users_without_role",
        "users_without_scope",
        "full_scope_users",
        "roles",
        "permissions",
        "grants",
        "sensitive_permissions",
        "mfa_enabled",
        "mfa_missing_privileged",
        "active_delegations",
        "expiring_delegations",
        "stale_delegations",
        "sensitive_events",
        "denials_30d",
        "events_30d",
        "activities",
    ]
    for index, key in enumerate(order):
        kpis[key] = float(row[index] or 0)  # type: ignore[literal-required]

    if kpis["users"] > 0:
        kpis["mfa_coverage"] = round(
            100 * kpis["mfa_enabled"] / kpis["users"], 1
        )
    if kpis["permissions"] > 0 and kpis["roles"] > 0:
        kpis["rbac_coverage"] = round(
            100 * kpis["grants"] / (kpis["permissions"] * kpis["roles"]), 1
        )

    checks: list[tuple[float, str, str, str, str, str, str, str]] = [
        (
            kpis["users_without_role"],
            "users-sans-role",
            "Comptes sans rôle applicatif",
            "agripro_user_role",
            "bad",
            "user-x",
            "Attribuer un rôle explicite ou archiver le compte.",
            "compte(s) ne portent aucun rôle : leurs permissions sont nulles.",
        ),
        (
            kpis["users_without_scope"],
            "users-sans-perimetre",
            "Comptes sans périmètre agricole",
            "agripro_scope",
            "warn",
            "map",
            "Déclarer un périmètre (exploitation, secteur, parcelle ou équipe).",
            "compte(s) sans périmètre déclaré : aucune parcelle accessible.",
        ),
        (
            kpis["mfa_missing_privileged"],
            "mfa-privilegies",
            "Comptes privilégiés sans second facteur",
            "agripro_user.mfa_enabled",
            "bad",
            "shield-alert",
            "Activer le MFA sur tous les rôles de niveau responsable.",
            "compte(s) à privilèges élevés ne sont pas protégés par MFA.",
        ),
        (
            kpis["stale_delegations"],
            "delegations-echues",
            "Délégations échues encore ouvertes",
            "agripro_delegation.end_date",
            "bad",
            "timer-off",
            "Expirer les permissions temporaires dépassées.",
            "délégation(s) ont dépassé leur date de fin.",
        ),
        (
            kpis["expiring_delegations"],
            "delegations-bientot",
            "Délégations arrivant à échéance",
            "agripro_delegation.end_date",
            "warn",
            "hourglass",
            "Prolonger explicitement ou préparer la reprise de service.",
            "délégation(s) se terminent dans les 7 jours.",
        ),
        (
            kpis["denials_30d"],
            "refus-acces",
            "Accès refusés sur 30 jours",
            "agripro_activity_log.kind = REFUS",
            "warn",
            "octagon-alert",
            "Vérifier les périmètres ou corriger les rôles concernés.",
            "tentative(s) d'action hors droits ont été bloquées côté serveur.",
        ),
        (
            kpis["full_scope_users"],
            "perimetre-global",
            "Périmètres « toute l'exploitation »",
            "agripro_scope.scope_kind = EXPLOITATION",
            "info",
            "building-2",
            "Limiter le périmètre global à la direction de l'exploitation.",
            "périmètre(s) global/globaux accordés.",
        ),
    ]
    for (
        value,
        key,
        label,
        reference,
        tone,
        icon,
        recommendation,
        detail,
    ) in checks:
        if value <= 0:
            continue
        findings.append(
            {
                "id": key,
                "label": label,
                "detail": f"{int(value)} {detail}",
                "reference": reference,
                "tone": tone,
                "icon": icon,
                "value": int(value),
                "recommendation": recommendation,
            }
        )

    if not findings:
        findings.append(
            {
                "id": "securite-conforme",
                "label": "Socle de sécurité conforme",
                "detail": (
                    "Rôles attribués, périmètres déclarés, MFA en place et "
                    "aucune délégation échue."
                ),
                "reference": "agripro_*",
                "tone": "good",
                "icon": "shield-check",
                "value": 0,
                "recommendation": "Maintenir la revue périodique des accès.",
            }
        )
    return kpis, findings


async def load_security_events(limit: int = 12) -> list[SecurityEvent]:
    """Derniers évènements sensibles ou refus, prêts pour l'audit."""
    await ensure_local_database()
    from app.access_reference import ACTIVITY_KINDS, ACTIVITY_TONES
    from app.admin_users import _fmt_when

    async with rx.asession() as asession:
        rows = (
            await asession.execute(
                text(
                    f"""
                    SELECT l.id, COALESCE(l.actor_label, 'Système'), l.kind,
                           COALESCE(l.module, ''), COALESCE(l.action, ''),
                           COALESCE(l.object_ref, ''), COALESCE(l.summary, ''),
                           COALESCE(l.occurred_at, l.created_at),
                           l.is_sensitive
                    FROM agripro_activity_log l
                    WHERE l.is_sensitive = 1 OR l.kind = 'REFUS'
                    ORDER BY COALESCE(l.occurred_at, l.created_at) DESC,
                             l.id DESC
                    LIMIT {int(limit)}
                    """
                )
            )
        ).all()
    items: list[SecurityEvent] = []
    for row in rows:
        kind = str(row[2] or "CONSULTATION")
        items.append(
            {
                "id": int(row[0]),
                "actor": str(row[1]),
                "kind": ACTIVITY_KINDS.get(kind, kind),
                "module": str(row[3]) or "Transverse",
                "action": str(row[4]) or "—",
                "object_ref": str(row[5]) or "—",
                "summary": str(row[6]) or "Aucun détail consigné.",
                "when": _fmt_when(row[7]),
                "sensitive": bool(row[8]),
                "tone": ACTIVITY_TONES.get(kind, "muted"),
            }
        )
    return items

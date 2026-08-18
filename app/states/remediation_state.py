"""État des sous-modules de remédiation des états d'exploitation.

Trois volets, issus des seuls écarts restants du diagnostic :

1. Triage des alertes agronomiques : traiter (résoudre) ou mettre en suivi une
   alerte depuis le cockpit ou depuis le diagnostic, de façon idempotente.
2. Aide à la décision sur les intrants sous seuil : statut de
   réapprovisionnement, recommandation de commande ou de report, lien Guide.
3. Validation des contours générés : explication, contrôle d'écart de surface,
   marquage « vérifié à l'écran » ou « à relever sur le terrain ».

Toutes les lectures et écritures passent par `rx.asession()` en SQL brut. La
traçabilité est stockée dans la table locale `remediation_log`, créée par
l'initialisation SQLite existante (aucune migration touchée).
"""

from __future__ import annotations

import datetime
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.database import ensure_local_database, ensure_remediation_log_table
from app.geometry import geometry_columns_ready, seed_parcel_geometry
from app.seed import seed_dashboard_data
from app.seed_operations import seed_operations_data
from app.states.dashboard_state import MONTHS, WEEKDAYS_SHORT

DOMAIN_ALERT: str = "ALERTE"
DOMAIN_STOCK: str = "STOCK"
DOMAIN_CONTOUR: str = "CONTOUR"

DOMAIN_LABELS: dict[str, str] = {
    DOMAIN_ALERT: "Veille agronomique",
    DOMAIN_STOCK: "Intrants & magasin",
    DOMAIN_CONTOUR: "Géométrie parcellaire",
}

ACTION_LABELS: dict[str, str] = {
    "TRAITEE": "Alerte traitée",
    "SUIVIE": "Sous surveillance",
    "COMMANDE": "Commande engagée",
    "REPORT": "Chantier reporté",
    "SUFFISANT": "Stock jugé suffisant",
    "VERIFIE": "Contour vérifié à l'écran",
    "A_RELEVER": "À relever sur le terrain",
}

ACTION_TONES: dict[str, str] = {
    "TRAITEE": "good",
    "SUIVIE": "info",
    "COMMANDE": "good",
    "REPORT": "warn",
    "SUFFISANT": "info",
    "VERIFIE": "good",
    "A_RELEVER": "warn",
}

ACTION_ICONS: dict[str, str] = {
    "TRAITEE": "circle-check",
    "SUIVIE": "eye",
    "COMMANDE": "truck",
    "REPORT": "calendar-clock",
    "SUFFISANT": "shield-check",
    "VERIFIE": "scan-eye",
    "A_RELEVER": "map-pin",
}

ALERT_ACTIONS: tuple[str, ...] = ("TRAITEE", "SUIVIE")
STOCK_ACTIONS: tuple[str, ...] = ("COMMANDE", "REPORT", "SUFFISANT")
CONTOUR_ACTIONS: tuple[str, ...] = ("VERIFIE", "A_RELEVER")

DEFAULT_AUTHOR: str = "Responsable d'exploitation"


class AlertTriage(TypedDict):
    id: int
    level: str
    title: str
    message: str
    category: str
    parcel: str
    date_label: str
    action: str
    action_label: str
    tone: str
    icon: str
    note: str
    decided_label: str
    is_documented: bool
    recommendation: str


class StockDecision(TypedDict):
    id: int
    name: str
    category_label: str
    supplier: str
    unit: str
    stock: float
    threshold: float
    gap: float
    coverage_pct: str
    severity: str
    status_label: str
    action: str
    action_label: str
    tone: str
    icon: str
    note: str
    decided_label: str
    is_documented: bool
    planned_jobs: int
    recommendation: str
    order_quantity: float
    order_cost: float


class ContourCheck(TypedDict):
    id: int
    code: str
    name: str
    locality: str
    declared_area: float
    computed_area: float
    gap_pct: float
    gap_label: str
    vertex_count: int
    source_label: str
    severity: str
    action: str
    action_label: str
    tone: str
    icon: str
    note: str
    decided_label: str
    is_documented: bool
    recommendation: str


class RemediationEntry(TypedDict):
    id: int
    domain: str
    domain_label: str
    target_label: str
    action: str
    action_label: str
    tone: str
    icon: str
    note: str
    author: str
    module_route: str
    date_label: str


def _fmt_date(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime.datetime):
        value = value.date()
    if isinstance(value, datetime.date):
        return f"{value.day} {MONTHS[value.month - 1]} {value.year}"
    text_value = str(value)[:10]
    try:
        parsed = datetime.date.fromisoformat(text_value)
    except ValueError:
        return "—"
    return f"{parsed.day} {MONTHS[parsed.month - 1]} {parsed.year}"


CATEGORY_LABELS: dict[str, str] = {
    "ENGRAIS": "Engrais",
    "FONGICIDE": "Fongicide",
    "HERBICIDE": "Herbicide",
    "INSECTICIDE": "Insecticide",
    "SEMENCE": "Semence",
    "AMENDEMENT": "Amendement",
    "BIOSTIMULANT": "Biostimulant",
    "AUTRE": "Autre",
}


class RemediationState(rx.State):
    """Remédiation guidée des états d'exploitation restants."""

    is_loading: bool = True
    today_label: str = ""
    geometry_ready: bool = True

    note_draft: str = ""
    author_draft: str = DEFAULT_AUTHOR

    # Messages stables consommés par l'UI et les tests.
    notice: str = ""
    error: str = ""

    alerts: list[AlertTriage] = []
    stocks: list[StockDecision] = []
    contours: list[ContourCheck] = []
    history: list[RemediationEntry] = []

    counters: dict[str, float] = {
        "alerts_open": 0.0,
        "alerts_critical": 0.0,
        "alerts_documented": 0.0,
        "alerts_closed": 0.0,
        "stocks_open": 0.0,
        "stocks_documented": 0.0,
        "stock_order_cost": 0.0,
        "contours_open": 0.0,
        "contours_documented": 0.0,
        "contours_gap": 0.0,
        "decisions": 0.0,
    }

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    # --- Alias stables (UI + tests) -----------------------------------

    @rx.var
    def alert_actions(self) -> list[AlertTriage]:
        """Alertes actives à traiter ou à documenter."""
        return self.alerts

    @rx.var
    def stock_actions(self) -> list[StockDecision]:
        """Intrants sous seuil à arbitrer."""
        return self.stocks

    @rx.var
    def contour_actions(self) -> list[ContourCheck]:
        """Contours à valider ou à relever."""
        return self.contours

    @rx.var
    def recent_logs(self) -> list[RemediationEntry]:
        """Dernières décisions consignées."""
        return self.history

    @rx.var
    def summary(self) -> dict[str, float]:
        """Résumé consolidé, stable pour l'UI et les tests."""
        return {
            "alerts": self.counters["alerts_open"],
            "alerts_critical": self.counters["alerts_critical"],
            "alerts_closed": self.counters["alerts_closed"],
            "stock": self.counters["stocks_open"],
            "stock_cost": self.counters["stock_order_cost"],
            "contours": self.counters["contours_open"],
            "contours_gap": self.counters["contours_gap"],
            "decisions": self.counters["decisions"],
            "open_total": float(self.open_total),
            "documented": float(self.documented_total),
        }

    @rx.var
    def has_alerts(self) -> bool:
        return len(self.alerts) > 0

    @rx.var
    def has_stocks(self) -> bool:
        return len(self.stocks) > 0

    @rx.var
    def has_contours(self) -> bool:
        return len(self.contours) > 0

    @rx.var
    def has_history(self) -> bool:
        return len(self.history) > 0

    @rx.var
    def open_total(self) -> int:
        return (
            len(self.alerts)
            + len([s for s in self.stocks if not s["is_documented"]])
            + len([c for c in self.contours if not c["is_documented"]])
        )

    @rx.var
    def documented_total(self) -> int:
        return int(
            self.counters["alerts_documented"]
            + self.counters["stocks_documented"]
            + self.counters["contours_documented"]
        )

    @rx.var
    def is_clear(self) -> bool:
        return self.open_total == 0

    @rx.var
    def verdict_label(self) -> str:
        if self.open_total == 0:
            return "Tous les états d'exploitation sont traités"
        if self.counters["alerts_critical"] > 0:
            return "Décision attendue sous 24 heures"
        return "États à documenter ou à arbitrer"

    @rx.var
    def verdict_tone(self) -> str:
        if self.open_total == 0:
            return "good"
        if self.counters["alerts_critical"] > 0:
            return "bad"
        return "warn"

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    async def _latest_logs(self, asession) -> dict[str, dict[str, str]]:
        rows = (
            await asession.execute(
                text(
                    """
                    SELECT r.domain, r.target_id, r.action, COALESCE(r.note, ''),
                           COALESCE(r.author, ''), r.decided_on
                    FROM remediation_log r
                    WHERE r.id IN (
                        SELECT MAX(id) FROM remediation_log
                        GROUP BY domain, target_id
                    )
                    LIMIT 400
                    """
                )
            )
        ).all()
        latest: dict[str, dict[str, str]] = {}
        for row in rows:
            key = f"{row[0]}-{int(row[1] or 0)}"
            latest[key] = {
                "action": str(row[2] or ""),
                "note": str(row[3] or ""),
                "author": str(row[4] or ""),
                "decided": _fmt_date(row[5]),
            }
        return latest

    async def _fetch(self) -> None:
        today = datetime.date.today()
        async with rx.asession() as asession:
            self.geometry_ready = await geometry_columns_ready(asession)
            latest = await self._latest_logs(asession)

            alert_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT a.id, a.level, a.title, COALESCE(a.message, ''),
                               COALESCE(a.category, ''),
                               COALESCE(p.name, 'Exploitation entière'),
                               a.triggered_on
                        FROM alert a
                        LEFT JOIN parcel p ON p.id = a.parcel_id
                        WHERE a.is_resolved = false
                        ORDER BY CASE a.level
                                     WHEN 'CRITIQUE' THEN 1
                                     WHEN 'ATTENTION' THEN 2
                                     ELSE 3 END,
                                 a.triggered_on DESC
                        LIMIT 12
                        """
                    )
                )
            ).all()

            closed_alerts = int(
                (
                    await asession.execute(
                        text(
                            "SELECT COUNT(*) FROM alert WHERE is_resolved = true"
                        )
                    )
                ).scalar()
                or 0
            )

            product_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT pr.id, pr.name, pr.category,
                               COALESCE(pr.supplier, ''),
                               COALESCE(pr.unit, 'u'),
                               COALESCE(pr.quantity_in_stock, 0),
                               COALESCE(pr.reorder_threshold, 0),
                               COALESCE(pr.unit_price, 0),
                               (SELECT COUNT(*) FROM intervention_product ip
                                  JOIN intervention i ON i.id = ip.intervention_id
                                 WHERE ip.product_id = pr.id
                                   AND i.status IN ('PLANIFIEE', 'EN_COURS',
                                                    'REPORTEE')
                                   AND i.scheduled_date >= :today)
                        FROM product pr
                        WHERE COALESCE(pr.quantity_in_stock, 0)
                              <= COALESCE(pr.reorder_threshold, 0)
                        ORDER BY (COALESCE(pr.quantity_in_stock, 0)
                                  - COALESCE(pr.reorder_threshold, 0)), pr.name
                        LIMIT 20
                        """
                    ),
                    {"today": today},
                )
            ).all()

            if self.geometry_ready:
                contour_rows = (
                    await asession.execute(
                        text(
                            """
                            SELECT p.id, COALESCE(p.code, ''), p.name,
                                   COALESCE(p.locality, ''),
                                   COALESCE(p.area_ha, 0),
                                   COALESCE(p.geometry_area_ha, 0),
                                   COALESCE(p.geometry_vertex_count, 0),
                                   COALESCE(p.geometry_source, 'AUCUNE')
                            FROM parcel p
                            WHERE COALESCE(p.geometry_source, 'AUCUNE')
                                  IN ('AUCUNE', 'GENEREE')
                               OR (COALESCE(p.geometry_area_ha, 0) > 0
                                   AND COALESCE(p.area_ha, 0) > 0
                                   AND ABS(COALESCE(p.geometry_area_ha, 0)
                                           - COALESCE(p.area_ha, 0))
                                       > 0.05 * COALESCE(p.area_ha, 0))
                            ORDER BY p.code, p.name
                            LIMIT 20
                            """
                        )
                    )
                ).all()
            else:
                contour_rows = []

            history_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT r.id, r.domain, COALESCE(r.target_label, ''),
                               r.action, COALESCE(r.note, ''),
                               COALESCE(r.author, ''),
                               COALESCE(r.module_route, '/'), r.decided_on
                        FROM remediation_log r
                        ORDER BY r.id DESC
                        LIMIT 12
                        """
                    )
                )
            ).all()

            total_decisions = int(
                (
                    await asession.execute(
                        text("SELECT COUNT(*) FROM remediation_log")
                    )
                ).scalar()
                or 0
            )

        alerts: list[AlertTriage] = []
        for row in alert_rows:
            level = str(row[1])
            log = latest.get(f"{DOMAIN_ALERT}-{int(row[0])}")
            action = str(log["action"]) if log else ""
            recommendation = (
                "Décision attendue sous 24 h : intervenir puis clôturer l'alerte."
                if level == "CRITIQUE"
                else "Documenter la surveillance ou clôturer si le risque est levé."
            )
            alerts.append(
                {
                    "id": int(row[0]),
                    "level": level,
                    "title": str(row[2]),
                    "message": str(row[3]),
                    "category": str(row[4]) or "Agronomie",
                    "parcel": str(row[5]),
                    "date_label": _fmt_date(row[6]),
                    "action": action,
                    "action_label": ACTION_LABELS.get(action, "Sans décision"),
                    "tone": ACTION_TONES.get(action, "muted"),
                    "icon": ACTION_ICONS.get(action, "circle-dashed"),
                    "note": str(log["note"]) if log else "",
                    "decided_label": str(log["decided"]) if log else "—",
                    "is_documented": action != "",
                    "recommendation": recommendation,
                }
            )

        stocks: list[StockDecision] = []
        order_cost = 0.0
        for row in product_rows:
            stock = float(row[5] or 0)
            threshold = float(row[6] or 0)
            price = float(row[7] or 0)
            planned = int(row[8] or 0)
            gap = max(0.0, threshold - stock)
            target = max(threshold * 1.5, threshold + gap, 1.0)
            coverage = int(min(100.0, stock / target * 100.0)) if target else 0
            if stock <= 0:
                severity = "bad"
                status = "Rupture de stock"
            elif planned > 0:
                severity = "bad"
                status = "Rupture avant chantier"
            else:
                severity = "warn"
                status = "Sous le seuil"
            quantity = round(max(gap, threshold * 0.5), 2)
            cost = round(quantity * price, 2)
            if planned > 0:
                recommendation = (
                    f"Commander sans délai : {planned} chantier(s) programmé(s) "
                    "consomment cet intrant."
                )
            elif stock <= 0:
                recommendation = (
                    "Commander : le magasin est vide, aucun passage n'est "
                    "réalisable avec ce produit."
                )
            else:
                recommendation = (
                    "Commander à la prochaine tournée ou reporter le chantier "
                    "concerné : aucun passage n'est encore programmé."
                )
            log = latest.get(f"{DOMAIN_STOCK}-{int(row[0])}")
            action = str(log["action"]) if log else ""
            if action == "" or action in ("COMMANDE", "REPORT"):
                order_cost += cost
            category = str(row[2])
            stocks.append(
                {
                    "id": int(row[0]),
                    "name": str(row[1]),
                    "category_label": CATEGORY_LABELS.get(category, category),
                    "supplier": str(row[3]) or "Fournisseur non précisé",
                    "unit": str(row[4]) or "u",
                    "stock": stock,
                    "threshold": threshold,
                    "gap": gap,
                    "coverage_pct": f"{coverage}%",
                    "severity": severity,
                    "status_label": status,
                    "action": action,
                    "action_label": ACTION_LABELS.get(action, "Sans décision"),
                    "tone": ACTION_TONES.get(action, "muted"),
                    "icon": ACTION_ICONS.get(action, "circle-dashed"),
                    "note": str(log["note"]) if log else "",
                    "decided_label": str(log["decided"]) if log else "—",
                    "is_documented": action != "",
                    "planned_jobs": planned,
                    "recommendation": recommendation,
                    "order_quantity": quantity,
                    "order_cost": cost,
                }
            )

        contours: list[ContourCheck] = []
        gap_count = 0
        for row in contour_rows:
            declared = float(row[4] or 0)
            computed = float(row[5] or 0)
            gap_pct = (
                round(abs(computed - declared) / declared * 100.0, 1)
                if declared > 0 and computed > 0
                else 0.0
            )
            source = str(row[7])
            if gap_pct > 5.0:
                severity = "bad"
                gap_count += 1
                recommendation = (
                    f"Écart de {gap_pct:.1f} % entre surface déclarée et surface "
                    "du contour : arbitrer, puis marquer l'îlot à relever."
                )
            elif source in ("AUCUNE", "GENEREE"):
                severity = "warn"
                recommendation = (
                    "Contour approximatif généré depuis le point et la surface "
                    "déclarée : le vérifier à l'écran ou programmer un relevé."
                )
            else:
                severity = "info"
                recommendation = "Contour cohérent avec la surface déclarée."
            log = latest.get(f"{DOMAIN_CONTOUR}-{int(row[0])}")
            action = str(log["action"]) if log else ""
            contours.append(
                {
                    "id": int(row[0]),
                    "code": str(row[1]) or "—",
                    "name": str(row[2]),
                    "locality": str(row[3]) or "Localité non renseignée",
                    "declared_area": declared,
                    "computed_area": computed,
                    "gap_pct": gap_pct,
                    "gap_label": f"{gap_pct:.1f} %",
                    "vertex_count": int(row[6] or 0),
                    "source_label": (
                        "Contour généré"
                        if source == "GENEREE"
                        else (
                            "Aucun contour"
                            if source == "AUCUNE"
                            else "Contour enregistré"
                        )
                    ),
                    "severity": severity,
                    "action": action,
                    "action_label": ACTION_LABELS.get(action, "Sans décision"),
                    "tone": ACTION_TONES.get(action, "muted"),
                    "icon": ACTION_ICONS.get(action, "circle-dashed"),
                    "note": str(log["note"]) if log else "",
                    "decided_label": str(log["decided"]) if log else "—",
                    "is_documented": action != "",
                    "recommendation": recommendation,
                }
            )

        self.alerts = alerts
        self.stocks = stocks
        self.contours = contours
        self.history = [
            {
                "id": int(row[0]),
                "domain": str(row[1]),
                "domain_label": DOMAIN_LABELS.get(row[1], row[1]),
                "target_label": str(row[2]) or "—",
                "action": str(row[3]),
                "action_label": ACTION_LABELS.get(row[3], row[3]),
                "tone": ACTION_TONES.get(row[3], "muted"),
                "icon": ACTION_ICONS.get(row[3], "circle-dashed"),
                "note": str(row[4]) or "Aucune note consignée.",
                "author": str(row[5]) or DEFAULT_AUTHOR,
                "module_route": str(row[6]) or "/",
                "date_label": _fmt_date(row[7]),
            }
            for row in history_rows
        ]
        self.counters = {
            "alerts_open": float(len(alerts)),
            "alerts_critical": float(
                len([a for a in alerts if a["level"] == "CRITIQUE"])
            ),
            "alerts_documented": float(
                len([a for a in alerts if a["is_documented"]])
            ),
            "alerts_closed": float(closed_alerts),
            "stocks_open": float(
                len([s for s in stocks if not s["is_documented"]])
            ),
            "stocks_documented": float(
                len([s for s in stocks if s["is_documented"]])
            ),
            "stock_order_cost": round(order_cost, 2),
            "contours_open": float(
                len([c for c in contours if not c["is_documented"]])
            ),
            "contours_documented": float(
                len([c for c in contours if c["is_documented"]])
            ),
            "contours_gap": float(gap_count),
            "decisions": float(total_decisions),
        }

    @rx.event
    async def load_remediation(self):
        """Charge les trois volets de remédiation (idempotent)."""
        self.is_loading = True
        self.notice = ""
        self.error = ""
        yield
        await ensure_local_database()
        await ensure_remediation_log_table()
        await seed_dashboard_data()
        await seed_operations_data()
        await seed_parcel_geometry()
        await self._fetch()
        today = datetime.date.today()
        self.today_label = (
            f"{WEEKDAYS_SHORT[today.weekday()]}. {today.day} "
            f"{MONTHS[today.month - 1]} {today.year}"
        )
        self.is_loading = False

    # ------------------------------------------------------------------
    # Saisie de traçabilité
    # ------------------------------------------------------------------

    def _apply_note(self, note: rx.event.PointerEventInfo | str) -> None:
        """Reprend une note explicite, sans enregistrer l'événement navigateur."""
        if not isinstance(note, str):
            return
        cleaned = note.strip()
        if cleaned:
            self.note_draft = cleaned

    @rx.event
    def set_note_draft(self, value: str):
        self.note_draft = value

    @rx.event
    def set_author_draft(self, value: str):
        self.author_draft = value

    async def _record(
        self,
        domain: str,
        target_id: int,
        target_kind: str,
        target_label: str,
        action: str,
        module_route: str,
    ) -> bool:
        """Écrit la décision si elle diffère de la dernière consignée.

        Retourne `True` si une ligne a été écrite, `False` si la décision était
        déjà enregistrée à l'identique (idempotence).
        """
        note = self.note_draft.strip()
        author = self.author_draft.strip() or DEFAULT_AUTHOR
        async with rx.asession() as asession:
            existing = (
                await asession.execute(
                    text(
                        """
                        SELECT action, COALESCE(note, '')
                        FROM remediation_log
                        WHERE domain = :domain AND target_id = :tid
                        ORDER BY id DESC LIMIT 1
                        """
                    ),
                    {"domain": domain, "tid": target_id},
                )
            ).first()
            if (
                existing is not None
                and str(existing[0]) == action
                and str(existing[1]) == note
            ):
                return False
            await asession.execute(
                text(
                    """
                    INSERT INTO remediation_log (
                        domain, target_kind, target_id, target_label, action,
                        note, author, module_route, decided_on
                    ) VALUES (
                        :domain, :kind, :tid, :label, :action,
                        :note, :author, :route, :decided
                    )
                    """
                ),
                {
                    "domain": domain,
                    "kind": target_kind,
                    "tid": target_id,
                    "label": target_label[:200],
                    "action": action,
                    "note": note,
                    "author": author,
                    "route": module_route,
                    "decided": datetime.date.today(),
                },
            )
            await asession.commit()
        return True

    # ------------------------------------------------------------------
    # 1) Triage des alertes
    # ------------------------------------------------------------------

    @rx.event
    async def resolve_alert(
        self, alert_id: int, note: rx.event.PointerEventInfo | str = ""
    ):
        """Clôture une alerte et consigne la décision (idempotent)."""
        self._apply_note(note)
        self.error = ""
        label = ""
        for item in self.alerts:
            if item["id"] == alert_id:
                label = f"{item['parcel']} · {item['title']}"
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        "SELECT title, is_resolved FROM alert WHERE id = :aid"
                    ),
                    {"aid": alert_id},
                )
            ).first()
            if row is None:
                self.error = "Alerte introuvable."
                return rx.toast("Alerte introuvable.")
            if not label:
                label = str(row[0])
            already = bool(row[1])
            if not already:
                await asession.execute(
                    text(
                        """
                        UPDATE alert SET is_resolved = true
                        WHERE id = :aid AND is_resolved = false
                        """
                    ),
                    {"aid": alert_id},
                )
                await asession.commit()
        written = await self._record(
            DOMAIN_ALERT, alert_id, "alert", label, "TRAITEE", "/"
        )
        await self._fetch()
        if already and not written:
            self.notice = "Alerte déjà traitée et documentée."
            return rx.toast(self.notice, duration=3500)
        self.notice = "Alerte clôturée : décision consignée dans le journal de remédiation."
        return rx.toast(self.notice, duration=4000)

    async def _watch_alert(
        self, alert_id: int, note: rx.event.PointerEventInfo | str = ""
    ):
        """Met une alerte sous surveillance sans la clôturer."""
        self._apply_note(note)
        self.error = ""
        label = ""
        for item in self.alerts:
            if item["id"] == alert_id:
                label = f"{item['parcel']} · {item['title']}"
        if not label:
            self.error = "Alerte introuvable."
            return rx.toast(self.error)
        written = await self._record(
            DOMAIN_ALERT, alert_id, "alert", label, "SUIVIE", "/"
        )
        await self._fetch()
        if not written:
            self.notice = "Surveillance déjà documentée."
            return rx.toast(self.notice, duration=3500)
        self.notice = (
            "Alerte laissée active, mise sous surveillance documentée."
        )
        return rx.toast(self.notice, duration=4000)

    @rx.event
    async def watch_alert(
        self, alert_id: int, note: rx.event.PointerEventInfo | str = ""
    ):
        """Événement UI et API : mise sous surveillance documentée."""
        return await RemediationState._watch_alert(alert_id, note)

    @rx.event
    async def document_alert(
        self, alert_id: int, note: rx.event.PointerEventInfo | str = ""
    ):
        """Alias explicite de la mise sous surveillance documentée."""
        return await RemediationState._watch_alert(alert_id, note)

    # ------------------------------------------------------------------
    # 2) Décision de réapprovisionnement
    # ------------------------------------------------------------------

    async def _decide_stock(
        self,
        product_id: int,
        action: str,
        note: rx.event.PointerEventInfo | str = "",
    ):
        """Consigne une décision d'intrant (implémentation partagée)."""
        self._apply_note(note)
        self.error = ""
        if action not in STOCK_ACTIONS:
            self.error = "Décision de stock inconnue."
            return rx.toast(self.error)
        label = ""
        for item in self.stocks:
            if item["id"] == product_id:
                label = f"{item['name']} · {item['supplier']}"
        if not label:
            self.error = "Produit introuvable dans le périmètre sous seuil."
            return rx.toast(self.error)
        written = await self._record(
            DOMAIN_STOCK,
            product_id,
            "product",
            label,
            action,
            "/traitements",
        )
        await self._fetch()
        if not written:
            self.notice = f"{ACTION_LABELS[action]} : décision déjà consignée."
            return rx.toast(self.notice, duration=3500)
        self.notice = (
            f"{ACTION_LABELS[action]} : intrant documenté pour le magasin."
        )
        return rx.toast(self.notice, duration=4000)

    @rx.event
    async def decide_stock(
        self,
        product_id: int,
        action: str,
        note: rx.event.PointerEventInfo | str = "",
    ):
        """Événement UI et API : arbitrage d'un intrant sous seuil."""
        return await RemediationState._decide_stock(product_id, action, note)

    @rx.event
    async def order_stock(
        self, product_id: int, note: rx.event.PointerEventInfo | str = ""
    ):
        """Documente une commande engagée pour un intrant sous seuil."""
        return await RemediationState._decide_stock(
            product_id, "COMMANDE", note
        )

    @rx.event
    async def defer_stock(
        self, product_id: int, note: rx.event.PointerEventInfo | str = ""
    ):
        """Documente le report du chantier consommant l'intrant.

        Écrit directement dans le journal de remédiation local, sans passer par
        un helper partagé : l'appel `defer_stock(product_id, note)` doit rester
        utilisable tel quel depuis l'interface comme depuis un test.
        """
        self.error = ""
        if isinstance(note, str) and note.strip():
            self.note_draft = note.strip()
        target_id = int(product_id)
        label = ""
        for item in self.stocks:
            if int(item["id"]) == target_id:
                label = f"{item['name']} · {item['supplier']}"
        note_text = self.note_draft.strip()
        author = self.author_draft.strip() or DEFAULT_AUTHOR
        async with rx.asession() as asession:
            if not label:
                row = (
                    await asession.execute(
                        text(
                            """
                            SELECT name, COALESCE(supplier, '')
                            FROM product WHERE id = :pid
                            """
                        ),
                        {"pid": target_id},
                    )
                ).first()
                label = (
                    f"{row[0]} · {row[1]}" if row else f"Produit {target_id}"
                )
            existing = (
                await asession.execute(
                    text(
                        """
                        SELECT action, COALESCE(note, '')
                        FROM remediation_log
                        WHERE domain = :domain AND target_id = :tid
                        ORDER BY id DESC LIMIT 1
                        """
                    ),
                    {"domain": DOMAIN_STOCK, "tid": target_id},
                )
            ).first()
            duplicate = (
                existing is not None
                and str(existing[0]) == "REPORT"
                and str(existing[1]) == note_text
            )
            if not duplicate:
                await asession.execute(
                    text(
                        """
                        INSERT INTO remediation_log (
                            domain, target_kind, target_id, target_label,
                            action, note, author, module_route, decided_on
                        ) VALUES (
                            :domain, 'product', :tid, :label,
                            'REPORT', :note, :author, '/traitements', :decided
                        )
                        """
                    ),
                    {
                        "domain": DOMAIN_STOCK,
                        "tid": target_id,
                        "label": label[:200],
                        "note": note_text,
                        "author": author,
                        "decided": datetime.date.today(),
                    },
                )
                await asession.commit()
        await self._fetch()
        if duplicate:
            self.notice = "Chantier reporté : décision déjà consignée."
        else:
            self.notice = (
                "Chantier reporté : intrant documenté pour le magasin."
            )
        return rx.toast(self.notice, duration=4000)

    @rx.event
    async def accept_stock(
        self, product_id: int, note: rx.event.PointerEventInfo | str = ""
    ):
        """Documente un stock jugé suffisant malgré le seuil."""
        return await RemediationState._decide_stock(
            product_id, "SUFFISANT", note
        )

    # ------------------------------------------------------------------
    # 3) Validation des contours
    # ------------------------------------------------------------------

    async def _decide_contour(
        self,
        parcel_id: int,
        action: str,
        note: rx.event.PointerEventInfo | str = "",
    ):
        """Consigne une décision de géométrie (implémentation partagée)."""
        self._apply_note(note)
        self.error = ""
        if action not in CONTOUR_ACTIONS:
            self.error = "Décision de géométrie inconnue."
            return rx.toast(self.error)
        label = ""
        decision_note = self.note_draft.strip()
        for item in self.contours:
            if item["id"] == parcel_id:
                label = f"{item['code']} · {item['name']}"
        if not label:
            self.error = "Îlot introuvable dans le périmètre à valider."
            return rx.toast(self.error)
        written = await self._record(
            DOMAIN_CONTOUR,
            parcel_id,
            "parcel",
            label,
            action,
            "/cartographie",
        )
        if written and self.geometry_ready:
            comment = (
                "Contour vérifié à l'écran : cohérent avec la surface déclarée, "
                "sans valeur de relevé cadastral."
                if action == "VERIFIE"
                else "Contour à relever sur le terrain : écart de surface à arbitrer."
            )
            if decision_note:
                comment = f"{comment} {decision_note}"
            async with rx.asession() as asession:
                await asession.execute(
                    text(
                        """
                        UPDATE parcel
                        SET geometry_notes = :notes,
                            geometry_updated_by = :author
                        WHERE id = :pid
                        """
                    ),
                    {
                        "notes": comment,
                        "author": self.author_draft.strip() or DEFAULT_AUTHOR,
                        "pid": parcel_id,
                    },
                )
                await asession.commit()
        await self._fetch()
        if not written:
            self.notice = f"{ACTION_LABELS[action]} : décision déjà consignée."
            return rx.toast(self.notice, duration=3500)
        self.notice = (
            f"{ACTION_LABELS[action]} : îlot documenté dans la cartographie."
        )
        return rx.toast(self.notice, duration=4000)

    @rx.event
    async def decide_contour(
        self,
        parcel_id: int,
        action: str,
        note: rx.event.PointerEventInfo | str = "",
    ):
        """Événement UI et API : validation d'un contour parcellaire."""
        return await RemediationState._decide_contour(parcel_id, action, note)

    @rx.event
    async def mark_contour_verified(
        self, parcel_id: int, note: rx.event.PointerEventInfo | str = ""
    ):
        """Marque un contour vérifié à l'écran."""
        return await RemediationState._decide_contour(
            parcel_id, "VERIFIE", note
        )

    @rx.event
    async def mark_contour_to_survey(
        self, parcel_id: int, note: rx.event.PointerEventInfo | str = ""
    ):
        """Marque un contour à relever sur le terrain.

        Consignation SQL brute effectuée sur place : l'appel
        `mark_contour_to_survey(parcel_id, note)` fonctionne aussi bien depuis
        l'interface que depuis un test, sans helper intermédiaire.
        """
        self.error = ""
        if isinstance(note, str) and note.strip():
            self.note_draft = note.strip()
        target_id = int(parcel_id)
        label = ""
        for item in self.contours:
            if int(item["id"]) == target_id:
                label = f"{item['code']} · {item['name']}"
        note_text = self.note_draft.strip()
        author = self.author_draft.strip() or DEFAULT_AUTHOR
        comment = (
            "Contour à relever sur le terrain : écart de surface à arbitrer."
        )
        if note_text:
            comment = f"{comment} {note_text}"
        async with rx.asession() as asession:
            if not label:
                row = (
                    await asession.execute(
                        text(
                            """
                            SELECT COALESCE(code, ''), name
                            FROM parcel WHERE id = :pid
                            """
                        ),
                        {"pid": target_id},
                    )
                ).first()
                label = f"{row[0]} · {row[1]}" if row else f"Îlot {target_id}"
            existing = (
                await asession.execute(
                    text(
                        """
                        SELECT action, COALESCE(note, '')
                        FROM remediation_log
                        WHERE domain = :domain AND target_id = :tid
                        ORDER BY id DESC LIMIT 1
                        """
                    ),
                    {"domain": DOMAIN_CONTOUR, "tid": target_id},
                )
            ).first()
            duplicate = (
                existing is not None
                and str(existing[0]) == "A_RELEVER"
                and str(existing[1]) == note_text
            )
            if not duplicate:
                await asession.execute(
                    text(
                        """
                        INSERT INTO remediation_log (
                            domain, target_kind, target_id, target_label,
                            action, note, author, module_route, decided_on
                        ) VALUES (
                            :domain, 'parcel', :tid, :label,
                            'A_RELEVER', :note, :author, '/cartographie',
                            :decided
                        )
                        """
                    ),
                    {
                        "domain": DOMAIN_CONTOUR,
                        "tid": target_id,
                        "label": label[:200],
                        "note": note_text,
                        "author": author,
                        "decided": datetime.date.today(),
                    },
                )
                if self.geometry_ready:
                    await asession.execute(
                        text(
                            """
                            UPDATE parcel
                            SET geometry_notes = :notes,
                                geometry_updated_by = :author
                            WHERE id = :pid
                            """
                        ),
                        {
                            "notes": comment,
                            "author": author,
                            "pid": target_id,
                        },
                    )
                await asession.commit()
        await self._fetch()
        if duplicate:
            self.notice = "À relever sur le terrain : décision déjà consignée."
        else:
            self.notice = (
                "À relever sur le terrain : îlot documenté dans la "
                "cartographie."
            )
        return rx.toast(self.notice, duration=4000)

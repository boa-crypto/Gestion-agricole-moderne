"""État du poste de contrôle des intrants sous seuil (sous-module Stocks).

Ce module ne crée aucun domaine nouveau : il approfondit la remédiation
« STOCK » déjà en place (table locale `remediation_log`) en y ajoutant :

* la mesure de l'impact réel sur les chantiers planifiés (nombre de passages,
  quantité engagée, surface, prochaine échéance, retards) ;
* une recommandation chiffrée de réapprovisionnement (quantité et coût) ;
* les trois décisions d'arbitrage : commande engagée, chantier reporté, stock
  jugé suffisant, consignées de façon idempotente ;
* l'historique des décisions, global et par intrant, exploitable par le
  diagnostic et la recherche globale.

Toutes les lectures et écritures passent par `rx.asession()` en SQL brut.
Aucune migration n'est touchée.
"""

from __future__ import annotations

import datetime
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.database import ensure_local_database, ensure_remediation_log_table
from app.date_utils import as_date
from app.seed import seed_dashboard_data
from app.seed_operations import seed_operations_data
from app.states.dashboard_state import (
    INTERVENTION_STATUS_LABELS,
    MONTHS,
    WEEKDAYS_SHORT,
)
from app.states.remediation_state import (
    ACTION_ICONS,
    ACTION_LABELS,
    ACTION_TONES,
    CATEGORY_LABELS,
    DEFAULT_AUTHOR,
    DOMAIN_STOCK,
    STOCK_ACTIONS,
)

# Vues du poste de contrôle.
VIEW_ALL: str = "TOUS"
VIEW_BREAK: str = "RUPTURE"
VIEW_OPEN: str = "A_ARBITRER"
VIEW_DONE: str = "DOCUMENTE"

VIEW_LABELS: dict[str, str] = {
    VIEW_ALL: "Tous les intrants",
    VIEW_BREAK: "Ruptures",
    VIEW_OPEN: "À arbitrer",
    VIEW_DONE: "Documentés",
}

# Sévérités normalisées de tension de stock.
SEVERITY_LABELS: dict[str, str] = {
    "bad": "Rupture",
    "warn": "Sous le seuil",
    "info": "Tension surveillée",
}


class PlannedJob(TypedDict):
    """Chantier planifié consommant l'intrant sélectionné."""

    id: int
    title: str
    parcel: str
    crop: str
    date_label: str
    status_label: str
    dose: float
    quantity: float
    unit: str
    area: float
    days_delta: int
    is_late: bool


class StockLog(TypedDict):
    """Décision d'intrant consignée dans le journal de remédiation."""

    id: int
    target_id: int
    target_label: str
    action: str
    action_label: str
    tone: str
    icon: str
    note: str
    author: str
    date_label: str


class StockItem(TypedDict):
    """Intrant sous tension et son arbitrage."""

    id: int
    name: str
    category_label: str
    supplier: str
    reference: str
    unit: str
    unit_price: float
    stock: float
    threshold: float
    gap: float
    coverage_pct: str
    coverage_ratio: int
    severity: str
    severity_label: str
    status_label: str
    location: str
    expiry_label: str
    organic: bool
    stock_value: float
    planned_jobs: int
    planned_quantity: float
    planned_area: float
    next_job_label: str
    next_job_days: int
    late_jobs: int
    shortfall: float
    order_quantity: float
    order_cost: float
    recommendation: str
    impact: str
    decision: str
    decision_label: str
    tone: str
    icon: str
    note: str
    author: str
    decided_label: str
    is_documented: bool
    decision_count: int


def _fmt_date(value: object) -> str:
    day = as_date(value)
    if day is None:
        return "—"
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _clean_note(note: rx.event.PointerEventInfo | str) -> str:
    """Retourne une note explicite, en ignorant l'événement navigateur."""
    if isinstance(note, str):
        return note.strip()
    return ""


def _label_from_items(items: list[StockItem], product_id: int) -> str:
    """Libellé d'un intrant depuis la liste déjà chargée (sans requête)."""
    for item in items:
        if int(item["id"]) == product_id:
            return f"{item['name']} · {item['supplier']}"
    return ""


async def _write_stock_decision(
    product_id: int,
    action: str,
    note: str,
    author: str,
    label: str,
) -> bool:
    """Consigne une décision d'intrant dans `remediation_log`.

    Fonction de module (jamais une méthode d'état) : elle reçoit toutes ses
    données explicitement, ce qui évite toute confusion de liaison `self`.
    Retourne `True` si une ligne a été écrite, `False` si la même décision et
    la même note étaient déjà consignées (idempotence).
    """
    target = int(product_id)
    async with rx.asession() as asession:
        resolved = label
        if not resolved:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT name, COALESCE(supplier, '')
                        FROM product WHERE id = :pid
                        """
                    ),
                    {"pid": target},
                )
            ).first()
            resolved = f"{row[0]} · {row[1]}" if row else f"Produit {target}"
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
                {"domain": DOMAIN_STOCK, "tid": target},
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
                    domain, target_kind, target_id, target_label,
                    action, note, author, module_route, decided_on
                ) VALUES (
                    :domain, 'product', :tid, :label,
                    :action, :note, :author, '/traitements', :decided
                )
                """
            ),
            {
                "domain": DOMAIN_STOCK,
                "tid": target,
                "label": resolved[:200],
                "action": action,
                "note": note,
                "author": author,
                "decided": datetime.date.today(),
            },
        )
        await asession.commit()
    return True


class StockState(rx.State):
    """Poste de contrôle des intrants : impact, recommandation, décision."""

    is_loading: bool = True
    today_label: str = ""

    notice: str = ""
    error: str = ""

    note_draft: str = ""
    author_draft: str = DEFAULT_AUTHOR

    view: str = VIEW_ALL
    selected_id: int = 0

    items: list[StockItem] = []
    history: list[StockLog] = []
    selected_jobs: list[PlannedJob] = []
    selected_history: list[StockLog] = []

    summary: dict[str, float] = {
        "total": 0.0,
        "rupture": 0.0,
        "below": 0.0,
        "open": 0.0,
        "documented": 0.0,
        "order_quantity": 0.0,
        "order_cost": 0.0,
        "jobs_at_risk": 0.0,
        "late_jobs": 0.0,
        "decisions": 0.0,
        "stock_value": 0.0,
    }

    view_options: list[tuple[str, str]] = [
        (VIEW_ALL, VIEW_LABELS[VIEW_ALL]),
        (VIEW_BREAK, VIEW_LABELS[VIEW_BREAK]),
        (VIEW_OPEN, VIEW_LABELS[VIEW_OPEN]),
        (VIEW_DONE, VIEW_LABELS[VIEW_DONE]),
    ]

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def visible_items(self) -> list[StockItem]:
        if self.view == VIEW_BREAK:
            return [item for item in self.items if item["severity"] == "bad"]
        if self.view == VIEW_OPEN:
            return [item for item in self.items if not item["is_documented"]]
        if self.view == VIEW_DONE:
            return [item for item in self.items if item["is_documented"]]
        return self.items

    @rx.var
    def has_items(self) -> bool:
        return len(self.items) > 0

    @rx.var
    def has_visible_items(self) -> bool:
        return len(self.visible_items) > 0

    @rx.var
    def has_history(self) -> bool:
        return len(self.history) > 0

    @rx.var
    def has_selection(self) -> bool:
        return self.selected_id > 0

    @rx.var
    def selected_item(self) -> list[StockItem]:
        """Intrant sélectionné, sous forme de liste pour un `rx.foreach`."""
        return [item for item in self.items if item["id"] == self.selected_id]

    @rx.var
    def selected_label(self) -> str:
        for item in self.items:
            if item["id"] == self.selected_id:
                return f"{item['name']} · {item['supplier']}"
        return ""

    @rx.var
    def has_selected_jobs(self) -> bool:
        return len(self.selected_jobs) > 0

    @rx.var
    def has_selected_history(self) -> bool:
        return len(self.selected_history) > 0

    @rx.var
    def open_total(self) -> int:
        return len([item for item in self.items if not item["is_documented"]])

    @rx.var
    def verdict_tone(self) -> str:
        if self.summary["rupture"] > 0:
            return "bad"
        if self.open_total > 0:
            return "warn"
        if len(self.items) > 0:
            return "info"
        return "good"

    @rx.var
    def verdict_label(self) -> str:
        if self.summary["rupture"] > 0:
            return "Rupture d'intrant : commande à engager"
        if self.open_total > 0:
            return "Intrants sous seuil à arbitrer"
        if len(self.items) > 0:
            return "Tensions de stock documentées"
        return "Magasin d'intrants au-dessus des seuils"

    @rx.var
    def verdict_detail(self) -> str:
        return (
            f"{self.summary['rupture']:.0f} rupture(s), "
            f"{self.summary['below']:.0f} intrant(s) sous le seuil, "
            f"{self.summary['jobs_at_risk']:.0f} chantier(s) exposé(s) et "
            f"{self.summary['order_cost']:.0f} € de commande conseillée."
        )

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    async def _latest_decisions(
        self, asession
    ) -> tuple[dict[int, dict[str, str]], dict[int, int]]:
        latest_rows = (
            await asession.execute(
                text(
                    """
                    SELECT r.target_id, r.action, COALESCE(r.note, ''),
                           COALESCE(r.author, ''), r.decided_on
                    FROM remediation_log r
                    WHERE r.domain = :domain
                      AND r.id IN (
                          SELECT MAX(id) FROM remediation_log
                          WHERE domain = :domain
                          GROUP BY target_id
                      )
                    LIMIT 200
                    """
                ),
                {"domain": DOMAIN_STOCK},
            )
        ).all()
        latest: dict[int, dict[str, str]] = {
            int(row[0] or 0): {
                "action": str(row[1] or ""),
                "note": str(row[2] or ""),
                "author": str(row[3] or ""),
                "decided": _fmt_date(row[4]),
            }
            for row in latest_rows
        }
        count_rows = (
            await asession.execute(
                text(
                    """
                    SELECT target_id, COUNT(*) FROM remediation_log
                    WHERE domain = :domain
                    GROUP BY target_id
                    LIMIT 200
                    """
                ),
                {"domain": DOMAIN_STOCK},
            )
        ).all()
        counts: dict[int, int] = {
            int(row[0] or 0): int(row[1] or 0) for row in count_rows
        }
        return latest, counts

    def _log_row(self, row) -> StockLog:
        action = str(row[3])
        return {
            "id": int(row[0]),
            "target_id": int(row[1] or 0),
            "target_label": str(row[2]) or "—",
            "action": action,
            "action_label": ACTION_LABELS.get(action, action),
            "tone": ACTION_TONES.get(action, "muted"),
            "icon": ACTION_ICONS.get(action, "circle-dashed"),
            "note": str(row[4]) or "Aucune note consignée.",
            "author": str(row[5]) or DEFAULT_AUTHOR,
            "date_label": _fmt_date(row[6]),
        }

    async def _fetch(self) -> None:
        today = datetime.date.today()
        async with rx.asession() as asession:
            latest, counts = await self._latest_decisions(asession)

            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT pr.id, pr.name, pr.category,
                               COALESCE(pr.supplier, ''),
                               COALESCE(pr.reference, ''),
                               COALESCE(pr.unit, 'u'),
                               COALESCE(pr.unit_price, 0),
                               COALESCE(pr.quantity_in_stock, 0),
                               COALESCE(pr.reorder_threshold, 0),
                               COALESCE(pr.storage_location, ''),
                               pr.expiry_date, pr.is_organic_approved,
                               (SELECT COUNT(*) FROM intervention_product ip
                                  JOIN intervention i ON i.id = ip.intervention_id
                                 WHERE ip.product_id = pr.id
                                   AND i.status IN ('PLANIFIEE', 'EN_COURS',
                                                    'REPORTEE')),
                               (SELECT COALESCE(SUM(ip.total_quantity), 0)
                                  FROM intervention_product ip
                                  JOIN intervention i ON i.id = ip.intervention_id
                                 WHERE ip.product_id = pr.id
                                   AND i.status IN ('PLANIFIEE', 'EN_COURS',
                                                    'REPORTEE')),
                               (SELECT COALESCE(SUM(i.area_treated_ha), 0)
                                  FROM intervention_product ip
                                  JOIN intervention i ON i.id = ip.intervention_id
                                 WHERE ip.product_id = pr.id
                                   AND i.status IN ('PLANIFIEE', 'EN_COURS',
                                                    'REPORTEE')),
                               (SELECT MIN(i.scheduled_date)
                                  FROM intervention_product ip
                                  JOIN intervention i ON i.id = ip.intervention_id
                                 WHERE ip.product_id = pr.id
                                   AND i.status IN ('PLANIFIEE', 'EN_COURS',
                                                    'REPORTEE')),
                               (SELECT COUNT(*) FROM intervention_product ip
                                  JOIN intervention i ON i.id = ip.intervention_id
                                 WHERE ip.product_id = pr.id
                                   AND i.status IN ('PLANIFIEE', 'EN_COURS',
                                                    'REPORTEE')
                                   AND i.scheduled_date < :today)
                        FROM product pr
                        WHERE COALESCE(pr.quantity_in_stock, 0)
                              <= COALESCE(pr.reorder_threshold, 0)
                           OR COALESCE(pr.quantity_in_stock, 0) <
                              (SELECT COALESCE(SUM(ip.total_quantity), 0)
                                 FROM intervention_product ip
                                 JOIN intervention i ON i.id = ip.intervention_id
                                WHERE ip.product_id = pr.id
                                  AND i.status IN ('PLANIFIEE', 'EN_COURS',
                                                   'REPORTEE'))
                        ORDER BY (COALESCE(pr.quantity_in_stock, 0)
                                  - COALESCE(pr.reorder_threshold, 0)), pr.name
                        LIMIT 24
                        """
                    ),
                    {"today": today},
                )
            ).all()

            history_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT r.id, r.target_id, COALESCE(r.target_label, ''),
                               r.action, COALESCE(r.note, ''),
                               COALESCE(r.author, ''), r.decided_on
                        FROM remediation_log r
                        WHERE r.domain = :domain
                        ORDER BY r.id DESC
                        LIMIT 12
                        """
                    ),
                    {"domain": DOMAIN_STOCK},
                )
            ).all()

            total_decisions = int(
                (
                    await asession.execute(
                        text(
                            """
                            SELECT COUNT(*) FROM remediation_log
                            WHERE domain = :domain
                            """
                        ),
                        {"domain": DOMAIN_STOCK},
                    )
                ).scalar()
                or 0
            )

        items: list[StockItem] = []
        order_qty_total = 0.0
        order_cost_total = 0.0
        rupture = 0
        below = 0
        jobs_at_risk = 0
        late_jobs = 0
        stock_value = 0.0

        for row in rows:
            product_id = int(row[0])
            unit = str(row[5]) or "u"
            price = float(row[6] or 0)
            stock = float(row[7] or 0)
            threshold = float(row[8] or 0)
            planned_jobs = int(row[12] or 0)
            planned_qty = float(row[13] or 0)
            planned_area = float(row[14] or 0)
            next_job = as_date(row[15])
            late = int(row[16] or 0)

            gap = max(0.0, threshold - stock)
            shortfall = max(0.0, planned_qty - stock)
            target = max(threshold * 1.5, planned_qty, stock, 1.0)
            coverage = int(min(100.0, stock / target * 100.0))

            if stock <= 0:
                severity = "bad"
                status_label = "Rupture de stock"
            elif shortfall > 0:
                severity = "bad"
                status_label = "Rupture avant chantier"
            elif stock <= threshold:
                severity = "warn"
                status_label = "Sous le seuil"
            else:
                severity = "info"
                status_label = "Tension surveillée"

            if severity == "bad":
                rupture += 1
            if stock <= threshold:
                below += 1
            if planned_jobs > 0 and shortfall > 0:
                jobs_at_risk += planned_jobs
            late_jobs += late
            stock_value += stock * price

            order_quantity = round(
                max(
                    gap, shortfall, threshold * 0.5, 1.0 if stock <= 0 else 0.0
                ),
                2,
            )
            order_cost = round(order_quantity * price, 2)

            days = (next_job - today).days if next_job is not None else 0
            if planned_jobs == 0:
                impact = (
                    "Aucun chantier programmé ne consomme cet intrant pour le "
                    "moment."
                )
            else:
                impact = (
                    f"{planned_jobs} chantier(s) programmé(s) engagent "
                    f"{planned_qty:.1f} {unit} sur {planned_area:.1f} ha"
                )
                if next_job is not None:
                    impact = f"{impact}, dès le {_fmt_date(next_job)}"
                impact = f"{impact}."
                if late > 0:
                    impact = (
                        f"{impact} {late} passage(s) déjà en retard : le stock "
                        "bloque la replanification."
                    )

            if shortfall > 0 and planned_jobs > 0:
                recommendation = (
                    f"Commander {order_quantity:.1f} {unit} "
                    f"({order_cost:.0f} €) : il manque {shortfall:.1f} {unit} "
                    "pour couvrir les chantiers programmés, sinon reporter le "
                    "passage concerné."
                )
            elif stock <= 0:
                recommendation = (
                    f"Commander {order_quantity:.1f} {unit} "
                    f"({order_cost:.0f} €) : le magasin est vide, aucun "
                    "passage n'est réalisable avec ce produit."
                )
            elif stock <= threshold:
                recommendation = (
                    f"Réapprovisionner {order_quantity:.1f} {unit} "
                    f"({order_cost:.0f} €) pour repasser au-dessus du seuil de "
                    f"{threshold:.1f} {unit}, ou documenter un stock suffisant."
                )
            else:
                recommendation = (
                    "Stock au-dessus du seuil mais insuffisant face aux "
                    "chantiers : arbitrer entre commande et report."
                )

            log = latest.get(product_id)
            action = str(log["action"]) if log else ""
            if action == "" or action in ("COMMANDE", "REPORT"):
                order_qty_total += order_quantity
                order_cost_total += order_cost

            expiry = as_date(row[10])
            if expiry is None:
                expiry_label = "Sans péremption"
            elif expiry < today:
                expiry_label = f"Périmé le {_fmt_date(expiry)}"
            else:
                expiry_label = f"Péremption {_fmt_date(expiry)}"

            category = str(row[2])
            items.append(
                {
                    "id": product_id,
                    "name": str(row[1]),
                    "category_label": CATEGORY_LABELS.get(category, category),
                    "supplier": str(row[3]) or "Fournisseur non précisé",
                    "reference": str(row[4]) or "—",
                    "unit": unit,
                    "unit_price": price,
                    "stock": stock,
                    "threshold": threshold,
                    "gap": gap,
                    "coverage_pct": f"{coverage}%",
                    "coverage_ratio": coverage,
                    "severity": severity,
                    "severity_label": SEVERITY_LABELS.get(severity, "Tension"),
                    "status_label": status_label,
                    "location": str(row[9]) or "Emplacement non précisé",
                    "expiry_label": expiry_label,
                    "organic": bool(row[11]),
                    "stock_value": round(stock * price, 2),
                    "planned_jobs": planned_jobs,
                    "planned_quantity": planned_qty,
                    "planned_area": planned_area,
                    "next_job_label": (
                        _fmt_date(next_job)
                        if next_job is not None
                        else "Aucun chantier"
                    ),
                    "next_job_days": days,
                    "late_jobs": late,
                    "shortfall": shortfall,
                    "order_quantity": order_quantity,
                    "order_cost": order_cost,
                    "recommendation": recommendation,
                    "impact": impact,
                    "decision": action,
                    "decision_label": ACTION_LABELS.get(
                        action, "Sans décision"
                    ),
                    "tone": ACTION_TONES.get(action, "muted"),
                    "icon": ACTION_ICONS.get(action, "circle-dashed"),
                    "note": str(log["note"]) if log else "",
                    "author": str(log["author"]) if log else "",
                    "decided_label": str(log["decided"]) if log else "—",
                    "is_documented": action != "",
                    "decision_count": counts.get(product_id, 0),
                }
            )

        self.items = items
        self.history = [self._log_row(row) for row in history_rows]
        self.summary = {
            "total": float(len(items)),
            "rupture": float(rupture),
            "below": float(below),
            "open": float(
                len([item for item in items if not item["is_documented"]])
            ),
            "documented": float(
                len([item for item in items if item["is_documented"]])
            ),
            "order_quantity": round(order_qty_total, 2),
            "order_cost": round(order_cost_total, 2),
            "jobs_at_risk": float(jobs_at_risk),
            "late_jobs": float(late_jobs),
            "decisions": float(total_decisions),
            "stock_value": round(stock_value, 2),
        }

    async def _fetch_selection(self) -> None:
        if self.selected_id <= 0:
            self.selected_jobs = []
            self.selected_history = []
            return
        today = datetime.date.today()
        async with rx.asession() as asession:
            job_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT i.id, i.title, p.name, COALESCE(c.name, ''),
                               i.scheduled_date, i.status,
                               COALESCE(ip.dose_per_ha, 0),
                               COALESCE(ip.total_quantity, 0),
                               COALESCE(ip.unit, ''),
                               COALESCE(i.area_treated_ha, 0)
                        FROM intervention_product ip
                        JOIN intervention i ON i.id = ip.intervention_id
                        JOIN parcel p ON p.id = i.parcel_id
                        LEFT JOIN crop c ON c.id = i.crop_id
                        WHERE ip.product_id = :pid
                          AND i.status IN ('PLANIFIEE', 'EN_COURS', 'REPORTEE')
                        ORDER BY i.scheduled_date, i.id
                        LIMIT 12
                        """
                    ),
                    {"pid": self.selected_id},
                )
            ).all()
            log_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT r.id, r.target_id, COALESCE(r.target_label, ''),
                               r.action, COALESCE(r.note, ''),
                               COALESCE(r.author, ''), r.decided_on
                        FROM remediation_log r
                        WHERE r.domain = :domain AND r.target_id = :pid
                        ORDER BY r.id DESC
                        LIMIT 8
                        """
                    ),
                    {"domain": DOMAIN_STOCK, "pid": self.selected_id},
                )
            ).all()

        jobs: list[PlannedJob] = []
        for row in job_rows:
            scheduled = as_date(row[4])
            status = str(row[5])
            jobs.append(
                {
                    "id": int(row[0]),
                    "title": str(row[1]) or "Chantier sans intitulé",
                    "parcel": str(row[2]),
                    "crop": str(row[3]) or "Sans culture liée",
                    "date_label": _fmt_date(scheduled),
                    "status_label": INTERVENTION_STATUS_LABELS.get(
                        status, status
                    ),
                    "dose": float(row[6] or 0),
                    "quantity": float(row[7] or 0),
                    "unit": str(row[8]) or "u",
                    "area": float(row[9] or 0),
                    "days_delta": (
                        (scheduled - today).days if scheduled is not None else 0
                    ),
                    "is_late": bool(
                        scheduled is not None and scheduled < today
                    ),
                }
            )
        self.selected_jobs = jobs
        self.selected_history = [self._log_row(row) for row in log_rows]

    @rx.event
    async def load_stocks(self):
        """Charge le poste de contrôle des intrants (idempotent)."""
        self.is_loading = True
        self.notice = ""
        self.error = ""
        yield
        await ensure_local_database()
        await ensure_remediation_log_table()
        await seed_dashboard_data()
        await seed_operations_data()
        await self._fetch()
        await self._fetch_selection()
        today = datetime.date.today()
        self.today_label = (
            f"{WEEKDAYS_SHORT[today.weekday()]}. {today.day} "
            f"{MONTHS[today.month - 1]} {today.year}"
        )
        self.is_loading = False

    # ------------------------------------------------------------------
    # Interactions
    # ------------------------------------------------------------------

    @rx.event
    def set_view(self, value: str):
        self.view = value

    @rx.event
    def set_note_draft(self, value: str):
        self.note_draft = value

    @rx.event
    def set_author_draft(self, value: str):
        self.author_draft = value

    @rx.event
    async def select_product(self, product_id: int):
        """Ouvre le détail d'un intrant : chantiers exposés et historique."""
        target = int(product_id)
        self.selected_id = 0 if self.selected_id == target else target
        await self._fetch_selection()

    @rx.event
    async def clear_selection(self):
        self.selected_id = 0
        await self._fetch_selection()

    # Chaque décision publique est écrite en entier sur l'instance : elle
    # n'appelle aucun helper d'état partagé, seulement la fonction de module
    # `_write_stock_decision`. Un appel direct `order_stock(product_id, note)`
    # depuis un test est donc identique à un clic dans l'interface.

    @rx.event
    async def decide_stock(
        self,
        product_id: int,
        action: str = "",
        note: rx.event.PointerEventInfo | str = "",
    ):
        """Arbitrage générique d'un intrant sous tension."""
        self.error = ""
        self.notice = ""
        target = int(product_id)
        decision = str(action).strip().upper()
        explicit = _clean_note(note)
        if explicit:
            self.note_draft = explicit
        if decision not in STOCK_ACTIONS:
            self.error = (
                f"Décision de stock inconnue : « {action} ». "
                "Utiliser COMMANDE, REPORT ou SUFFISANT."
            )
            return rx.toast(self.error, duration=4000)
        written = await _write_stock_decision(
            target,
            decision,
            self.note_draft.strip(),
            self.author_draft.strip() or DEFAULT_AUTHOR,
            _label_from_items(self.items, target),
        )
        await self._fetch()
        await self._fetch_selection()
        if not written:
            self.notice = (
                f"{ACTION_LABELS[decision]} : décision déjà consignée."
            )
            return rx.toast(self.notice, duration=3500)
        self.notice = (
            f"{ACTION_LABELS[decision]} : intrant documenté pour le magasin."
        )
        return rx.toast(self.notice, duration=4000)

    @rx.event
    async def order_stock(
        self, product_id: int, note: rx.event.PointerEventInfo | str = ""
    ):
        """Documente une commande engagée pour l'intrant."""
        self.error = ""
        self.notice = ""
        target = int(product_id)
        explicit = _clean_note(note)
        if explicit:
            self.note_draft = explicit
        written = await _write_stock_decision(
            target,
            "COMMANDE",
            self.note_draft.strip(),
            self.author_draft.strip() or DEFAULT_AUTHOR,
            _label_from_items(self.items, target),
        )
        await self._fetch()
        await self._fetch_selection()
        if not written:
            self.notice = "Commande engagée : décision déjà consignée."
            return rx.toast(self.notice, duration=3500)
        self.notice = "Commande engagée : intrant documenté pour le magasin."
        return rx.toast(self.notice, duration=4000)

    @rx.event
    async def defer_stock(
        self, product_id: int, note: rx.event.PointerEventInfo | str = ""
    ):
        """Documente le report du chantier consommant l'intrant."""
        self.error = ""
        self.notice = ""
        target = int(product_id)
        explicit = _clean_note(note)
        if explicit:
            self.note_draft = explicit
        written = await _write_stock_decision(
            target,
            "REPORT",
            self.note_draft.strip(),
            self.author_draft.strip() or DEFAULT_AUTHOR,
            _label_from_items(self.items, target),
        )
        await self._fetch()
        await self._fetch_selection()
        if not written:
            self.notice = "Chantier reporté : décision déjà consignée."
            return rx.toast(self.notice, duration=3500)
        self.notice = "Chantier reporté : intrant documenté pour le magasin."
        return rx.toast(self.notice, duration=4000)

    @rx.event
    async def accept_stock(
        self, product_id: int, note: rx.event.PointerEventInfo | str = ""
    ):
        """Documente un stock jugé suffisant malgré le seuil."""
        self.error = ""
        self.notice = ""
        target = int(product_id)
        explicit = _clean_note(note)
        if explicit:
            self.note_draft = explicit
        written = await _write_stock_decision(
            target,
            "SUFFISANT",
            self.note_draft.strip(),
            self.author_draft.strip() or DEFAULT_AUTHOR,
            _label_from_items(self.items, target),
        )
        await self._fetch()
        await self._fetch_selection()
        if not written:
            self.notice = "Stock jugé suffisant : décision déjà consignée."
            return rx.toast(self.notice, duration=3500)
        self.notice = (
            "Stock jugé suffisant : intrant documenté pour le magasin."
        )
        return rx.toast(self.notice, duration=4000)

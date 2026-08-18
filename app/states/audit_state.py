"""État de l'audit fonctionnel CMS² AgriPro face au Guide Agricole.

L'audit lit UNIQUEMENT la base (SQL brut via `rx.asession()`) et le référentiel
statique `app/audit_reference.py`. Aucune migration n'est touchée, aucune donnée
métier n'est modifiée : ce module produit une cartographie et des constats.

Il expose, pour chaque module applicatif : un statut normalisé (présent,
incomplet, incohérent, manquant), une priorité, la couverture éditoriale du
Guide, le volume de données porté, les constats et les recommandations. Les
incohérences détectables sont listées séparément et rattachées à leur module,
afin que le futur module de diagnostic puisse les réutiliser telles quelles.
"""

from __future__ import annotations

import datetime
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.audit_reference import (
    APP_ROUTES,
    DOMAIN_LABELS,
    ENTITY_SPECS,
    ENTITY_TABLES,
    MODULE_SPECS,
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_NORMAL,
    PRIORITY_WEIGHT,
    STATUS_INCOHERENT,
    STATUS_INCOMPLETE,
    STATUS_MISSING,
    STATUS_ORDER,
    STATUS_PRESENT,
    STRUCTURAL_DOMAINS,
    module_label,
    priority_label,
    priority_tone,
    status_label,
    status_tone,
)
from app.catalog_link import materialize_catalog_varieties
from app.geometry import geometry_columns_ready
from app.phenology_validation import phenology_audit_report
from app.seed import seed_dashboard_data
from app.seed_catalog import link_legacy_varieties, seed_catalog_data
from app.seed_corrections import apply_audit_corrections
from app.seed_guide import seed_guide_data
from app.states.dashboard_state import MONTHS, WEEKDAYS_SHORT


class IssueRow(TypedDict):
    """Constat d'audit rattaché à un module et à un domaine."""

    id: str
    module: str
    module_label: str
    module_route: str
    domain: str
    domain_label: str
    label: str
    detail: str
    reference: str
    status: str
    status_label: str
    tone: str
    priority: str
    priority_label: str
    priority_tone: str
    recommendation: str
    count: int


class CategoryRow(TypedDict):
    """Couverture éditoriale d'une catégorie du Guide."""

    key: str
    name: str
    module_route: str
    module_label: str
    articles: int
    procedures: int
    rules: int
    faq: int
    terms: int
    total: int
    status: str
    status_label: str
    tone: str


class EntityRow(TypedDict):
    """Entité persistante et son volume observé."""

    table: str
    label: str
    module: str
    module_label: str
    role: str
    is_core: bool
    rows: int
    status: str
    status_label: str
    tone: str


class DiagnosticRow(TypedDict):
    """Ligne de distribution (statut, priorité ou domaine) du diagnostic."""

    key: str
    label: str
    value: int
    share: float
    share_pct: str
    tone: str
    icon: str


class ActionRow(TypedDict):
    """Action corrective priorisée, dérivée d'un constat d'audit."""

    id: str
    rank: int
    label: str
    detail: str
    module: str
    module_label: str
    module_route: str
    domain_label: str
    reference: str
    priority: str
    priority_label: str
    priority_tone: str
    status_label: str
    tone: str
    recommendation: str
    count: int


class ModuleRow(TypedDict):
    """Ligne de la matrice de couverture Guide ↔ application."""

    key: str
    label: str
    route: str
    icon: str
    mission: str
    features: list[str]
    categories: list[str]
    missing_categories: list[str]
    tables: int
    empty_tables: list[str]
    records: int
    articles: int
    procedures: int
    rules: int
    faq: int
    terms: int
    guide_total: int
    coverage: int
    coverage_pct: str
    issue_count: int
    blocking_count: int
    status: str
    status_label: str
    tone: str
    priority: str
    priority_label: str
    priority_tone: str
    findings: list[str]
    recommendations: list[str]


def _entity_counts_sql() -> str:
    """Construit un UNION ALL de comptages sur les tables du référentiel.

    Les noms de tables proviennent exclusivement du référentiel statique du
    code (aucune saisie utilisateur), la construction de la requête est donc
    sûre.
    """
    parts = [
        f"SELECT '{table}' AS entity, COUNT(*) AS total FROM {table}"
        for table in ENTITY_TABLES
    ]
    return " UNION ALL ".join(parts)


class AuditState(rx.State):
    """Audit fonctionnel : cartographie, statuts, constats, recommandations."""

    is_loading: bool = True
    generated_label: str = ""
    geometry_ready: bool = True

    kpis: dict[str, float] = {
        "modules": 0.0,
        "present": 0.0,
        "incomplete": 0.0,
        "incoherent": 0.0,
        "missing": 0.0,
        "coverage": 0.0,
        "issues": 0.0,
        "blocking": 0.0,
        "entities": 0.0,
        "records": 0.0,
        "guide_contents": 0.0,
        "empty_entities": 0.0,
        "phenology_profiles": 0.0,
        "phenology_stages": 0.0,
        "phenology_critical_stages": 0.0,
        "phenology_recommendations": 0.0,
        "phenology_observations": 0.0,
        "phenology_changes": 0.0,
        "phenology_cultures": 0.0,
        "phenology_invalid_observations": 0.0,
    }

    modules: list[ModuleRow] = []
    categories: list[CategoryRow] = []
    entities: list[EntityRow] = []
    issues: list[IssueRow] = []

    status_filter: str = "TOUS"
    module_filter: str = "TOUS"
    domain_filter: str = "TOUS"
    priority_filter: str = "TOUS"

    status_options: list[tuple[str, str]] = [
        (key, status_label(key)) for key in STATUS_ORDER
    ]
    domain_options: list[tuple[str, str]] = [
        (key, label) for key, label in DOMAIN_LABELS.items()
    ]
    priority_options: list[tuple[str, str]] = [
        (PRIORITY_CRITICAL, priority_label(PRIORITY_CRITICAL)),
        (PRIORITY_HIGH, priority_label(PRIORITY_HIGH)),
        (PRIORITY_NORMAL, priority_label(PRIORITY_NORMAL)),
        (PRIORITY_LOW, priority_label(PRIORITY_LOW)),
    ]

    status_icons: dict[str, str] = {
        STATUS_PRESENT: "circle-check",
        STATUS_INCOMPLETE: "circle-dashed",
        STATUS_INCOHERENT: "octagon-alert",
        STATUS_MISSING: "circle-slash",
    }

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def module_options(self) -> list[tuple[str, str]]:
        return [(item["key"], item["label"]) for item in self.modules]

    @rx.var
    def visible_issues(self) -> list[IssueRow]:
        rows = self.issues
        if self.status_filter != "TOUS":
            rows = [
                item for item in rows if item["status"] == self.status_filter
            ]
        if self.module_filter != "TOUS":
            rows = [
                item for item in rows if item["module"] == self.module_filter
            ]
        if self.domain_filter != "TOUS":
            rows = [
                item for item in rows if item["domain"] == self.domain_filter
            ]
        if self.priority_filter != "TOUS":
            rows = [
                item
                for item in rows
                if item["priority"] == self.priority_filter
            ]
        return rows

    @rx.var
    def visible_modules(self) -> list[ModuleRow]:
        rows = self.modules
        if self.status_filter != "TOUS":
            rows = [
                item for item in rows if item["status"] == self.status_filter
            ]
        if self.module_filter != "TOUS":
            rows = [item for item in rows if item["key"] == self.module_filter]
        if self.priority_filter != "TOUS":
            rows = [
                item
                for item in rows
                if item["priority"] == self.priority_filter
            ]
        return rows

    # --- Synthèse décisionnelle -----------------------------------------

    @rx.var
    def readiness(self) -> float:
        """Indice de conformité fonctionnelle (0-100) pondéré par les blocages."""
        if not self.modules:
            return 0.0
        base = sum(item["coverage"] for item in self.modules) / len(
            self.modules
        )
        penalty = min(30.0, 3.0 * float(self.kpis["blocking"]))
        return round(max(0.0, base - penalty), 1)

    @rx.var
    def readiness_pct(self) -> str:
        return f"{self.readiness:.0f}%"

    @rx.var
    def verdict_tone(self) -> str:
        if self.kpis["missing"] > 0 or self.kpis["blocking"] > 2:
            return "bad"
        if self.kpis["incoherent"] > 0 or self.kpis["blocking"] > 0:
            return "warn"
        if self.kpis["incomplete"] > 0:
            return "info"
        return "good"

    @rx.var
    def verdict_label(self) -> str:
        tone = self.verdict_tone
        if tone == "bad":
            return "Exploitation à sécuriser"
        if tone == "warn":
            return "Incohérences à arbitrer"
        if tone == "info":
            return "Couverture à compléter"
        return "Chaîne fonctionnelle conforme"

    @rx.var
    def verdict_detail(self) -> str:
        return (
            f"{self.kpis['blocking']:.0f} constat(s) bloquant(s) sur "
            f"{self.kpis['issues']:.0f}, {self.kpis['incoherent']:.0f} module(s) "
            f"incohérent(s) et {self.kpis['incomplete']:.0f} module(s) à "
            f"compléter pour {self.kpis['modules']:.0f} écrans audités."
        )

    @rx.var
    def status_distribution(self) -> list[DiagnosticRow]:
        total = max(1, len(self.modules))
        rows: list[DiagnosticRow] = []
        for key in STATUS_ORDER:
            value = len(
                [item for item in self.modules if item["status"] == key]
            )
            share = round(100 * value / total, 1)
            rows.append(
                {
                    "key": key,
                    "label": status_label(key),
                    "value": value,
                    "share": share,
                    "share_pct": f"{share:.0f}%",
                    "tone": status_tone(key),
                    "icon": self.status_icons.get(key, "circle"),
                }
            )
        return rows

    @rx.var
    def priority_distribution(self) -> list[DiagnosticRow]:
        total = max(1, len(self.issues))
        icons = {
            PRIORITY_CRITICAL: "siren",
            PRIORITY_HIGH: "flame",
            PRIORITY_NORMAL: "activity",
            PRIORITY_LOW: "minus",
        }
        rows: list[DiagnosticRow] = []
        for key in (
            PRIORITY_CRITICAL,
            PRIORITY_HIGH,
            PRIORITY_NORMAL,
            PRIORITY_LOW,
        ):
            value = len(
                [item for item in self.issues if item["priority"] == key]
            )
            share = round(100 * value / total, 1)
            rows.append(
                {
                    "key": key,
                    "label": priority_label(key),
                    "value": value,
                    "share": share,
                    "share_pct": f"{share:.0f}%",
                    "tone": priority_tone(key),
                    "icon": icons.get(key, "circle"),
                }
            )
        return rows

    @rx.var
    def domain_distribution(self) -> list[DiagnosticRow]:
        total = max(1, len(self.issues))
        icons = {
            "guide": "book-open",
            "liaison": "link",
            "donnees": "database",
            "coherence": "scale",
            "exploitation": "siren",
            "module": "layout-dashboard",
        }
        rows: list[DiagnosticRow] = []
        for key, label in DOMAIN_LABELS.items():
            value = len([item for item in self.issues if item["domain"] == key])
            if value == 0:
                continue
            share = round(100 * value / total, 1)
            rows.append(
                {
                    "key": key,
                    "label": label,
                    "value": value,
                    "share": share,
                    "share_pct": f"{share:.0f}%",
                    "tone": "bad" if share >= 40 else "warn",
                    "icon": icons.get(key, "layers"),
                }
            )
        rows.sort(key=lambda item: item["value"], reverse=True)
        return rows

    @rx.var
    def action_plan(self) -> list[ActionRow]:
        """File de correction : constats déjà triés, rangés et numérotés."""
        rows: list[ActionRow] = []
        for index, item in enumerate(self.visible_issues[:10]):
            rows.append(
                {
                    "id": item["id"],
                    "rank": index + 1,
                    "label": item["label"],
                    "detail": item["detail"],
                    "module": item["module"],
                    "module_label": item["module_label"],
                    "module_route": item["module_route"],
                    "domain_label": item["domain_label"],
                    "reference": item["reference"],
                    "priority": item["priority"],
                    "priority_label": item["priority_label"],
                    "priority_tone": item["priority_tone"],
                    "status_label": item["status_label"],
                    "tone": item["tone"],
                    "recommendation": item["recommendation"],
                    "count": item["count"],
                }
            )
        return rows

    @rx.var
    def has_action_plan(self) -> bool:
        return len(self.action_plan) > 0

    @rx.var
    def watchlist(self) -> list[ModuleRow]:
        """Modules à surveiller : hors conformité, les moins couverts d'abord."""
        rows = [
            item for item in self.modules if item["status"] != STATUS_PRESENT
        ]
        return rows[:6]

    @rx.var
    def has_watchlist(self) -> bool:
        return len(self.watchlist) > 0

    @rx.var
    def healthy_modules(self) -> list[ModuleRow]:
        """Modules sains : couverture complète et aucun constat structurel."""
        return [
            item for item in self.modules if item["status"] == STATUS_PRESENT
        ]

    @rx.var
    def healthy_module_count(self) -> int:
        return len(self.healthy_modules)

    @rx.var
    def has_healthy_modules(self) -> bool:
        return len(self.healthy_modules) > 0

    @rx.var
    def coherence_issues(self) -> list[IssueRow]:
        """Écarts de cohérence métier, hors états d'exploitation."""
        return [item for item in self.issues if item["domain"] == "coherence"]

    @rx.var
    def coherence_issue_count(self) -> int:
        return len(self.coherence_issues)

    @rx.var
    def has_operational_issues(self) -> bool:
        return len(self.operational_issues) > 0

    @rx.var
    def triage_label(self) -> str:
        """Lecture courte du tri : sains / à traiter / écarts structurels."""
        return (
            f"{self.healthy_module_count} module(s) sain(s), "
            f"{self.operational_issue_count} état(s) d'exploitation à traiter, "
            f"{self.structural_issue_count} écart(s) structurel(s)"
        )

    @rx.var
    def structural_issues(self) -> list[IssueRow]:
        """Écarts structurels : contenu, liaison, entités ou couverture."""
        return [
            item for item in self.issues if item["domain"] in STRUCTURAL_DOMAINS
        ]

    @rx.var
    def structural_issue_count(self) -> int:
        return len(self.structural_issues)

    @rx.var
    def operational_issues(self) -> list[IssueRow]:
        """États d'exploitation à traiter (alertes, stocks) : pas des ruptures."""
        return [
            item for item in self.issues if item["domain"] == "exploitation"
        ]

    @rx.var
    def operational_issue_count(self) -> int:
        return len(self.operational_issues)

    @rx.var
    def blocking_issues(self) -> list[IssueRow]:
        return [
            item
            for item in self.issues
            if item["priority"] == PRIORITY_CRITICAL
        ]

    @rx.var
    def issue_count(self) -> int:
        return len(self.issues)

    @rx.var
    def visible_issue_count(self) -> int:
        return len(self.visible_issues)

    @rx.var
    def has_issues(self) -> bool:
        return len(self.visible_issues) > 0

    @rx.var
    def priority_modules(self) -> list[ModuleRow]:
        return [
            item for item in self.modules if item["status"] != STATUS_PRESENT
        ]

    @rx.var
    def empty_entities(self) -> list[EntityRow]:
        return [item for item in self.entities if item["rows"] == 0]

    # ------------------------------------------------------------------
    # Filtres
    # ------------------------------------------------------------------

    @rx.event
    def set_status_filter(self, value: str):
        self.status_filter = value

    @rx.event
    def set_module_filter(self, value: str):
        self.module_filter = value

    @rx.event
    def set_domain_filter(self, value: str):
        self.domain_filter = value

    @rx.event
    def set_priority_filter(self, value: str):
        self.priority_filter = value

    @rx.event
    def focus_module(self, key: str):
        """Cible un module dans le diagnostic sans modifier les données."""
        self.module_filter = key
        self.status_filter = "TOUS"
        self.domain_filter = "TOUS"
        self.priority_filter = "TOUS"

    @rx.event
    def reset_filters(self):
        self.status_filter = "TOUS"
        self.module_filter = "TOUS"
        self.domain_filter = "TOUS"
        self.priority_filter = "TOUS"

    # ------------------------------------------------------------------
    # Construction des constats
    # ------------------------------------------------------------------

    def _issue(
        self,
        issue_id: str,
        module: str,
        domain: str,
        label: str,
        detail: str,
        reference: str,
        status: str,
        priority: str,
        recommendation: str,
        count: int = 1,
    ) -> IssueRow:
        return {
            "id": issue_id,
            "module": module,
            "module_label": module_label(module),
            "module_route": ("/" if module == "" else self._route_of(module)),
            "domain": domain,
            "domain_label": DOMAIN_LABELS.get(domain, domain),
            "label": label,
            "detail": detail,
            "reference": reference,
            "status": status,
            "status_label": status_label(status),
            "tone": status_tone(status),
            "priority": priority,
            "priority_label": priority_label(priority),
            "priority_tone": priority_tone(priority),
            "recommendation": recommendation,
            "count": count,
        }

    def _route_of(self, module: str) -> str:
        for spec in MODULE_SPECS:
            if spec["key"] == module:
                return spec["route"]
        return "/"

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    @rx.event
    async def load_audit(self):
        """Recalcule intégralement l'audit à partir de la base."""
        self.is_loading = True
        yield

        # L'audit s'appuie sur les données réelles : on garantit leur présence
        # de façon idempotente, sans jamais modifier de schéma.
        await seed_dashboard_data()
        await seed_guide_data()
        # Référentiel cultures : amorçage puis matérialisation des liens vers
        # le référentiel variétal historique (idempotent).
        await seed_catalog_data()
        await link_legacy_varieties()
        await materialize_catalog_varieties()
        # Corrections idempotentes des écarts structurels repérés par l'audit.
        await apply_audit_corrections()

        today = datetime.date.today()
        issues: list[IssueRow] = []

        async with rx.asession() as asession:
            self.geometry_ready = await geometry_columns_ready(asession)

            entity_rows = (
                await asession.execute(text(_entity_counts_sql()))
            ).all()

            category_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT c.key, c.name, COALESCE(c.module_route, ''),
                               (SELECT COUNT(*) FROM guide_article a
                                  WHERE a.category_id = c.id AND a.status = 'PUBLIE'),
                               (SELECT COUNT(*) FROM guide_procedure p
                                  WHERE p.category_id = c.id AND p.status = 'PUBLIE'),
                               (SELECT COUNT(*) FROM guide_rule r
                                  WHERE r.category_id = c.id AND r.status = 'PUBLIE'),
                               (SELECT COUNT(*) FROM guide_faq f
                                  WHERE f.category_id = c.id AND f.status = 'PUBLIE'),
                               (SELECT COUNT(*) FROM guide_term t
                                  WHERE t.category_id = c.id AND t.status = 'PUBLIE')
                        FROM guide_category c
                        WHERE c.is_active = 1
                        ORDER BY c.position, c.name
                        LIMIT 60
                        """
                    )
                )
            ).all()

            link_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT COALESCE(l.label, ''), COALESCE(l.route, ''),
                               a.slug, COALESCE(c.key, '')
                        FROM guide_article_link l
                        JOIN guide_article a ON a.id = l.article_id
                        LEFT JOIN guide_category c ON c.id = a.category_id
                        ORDER BY a.slug, l.position
                        LIMIT 300
                        """
                    )
                )
            ).all()

            rule_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT r.code, r.title, COALESCE(r.module_route, ''),
                               COALESCE(r.field_reference, ''),
                               COALESCE(c.key, ''), r.kind, r.is_blocking,
                               LENGTH(COALESCE(r.rationale, '')),
                               LENGTH(COALESCE(r.remediation, ''))
                        FROM guide_rule r
                        LEFT JOIN guide_category c ON c.id = r.category_id
                        WHERE r.status = 'PUBLIE'
                        ORDER BY r.code
                        LIMIT 300
                        """
                    )
                )
            ).all()

            procedure_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT p.slug, p.title, COALESCE(c.key, ''),
                               COALESCE(p.module_route, ''),
                               (SELECT COUNT(*) FROM guide_procedure_step s
                                  WHERE s.procedure_id = p.id)
                        FROM guide_procedure p
                        LEFT JOIN guide_category c ON c.id = p.category_id
                        WHERE p.status = 'PUBLIE'
                        ORDER BY p.slug
                        LIMIT 200
                        """
                    )
                )
            ).all()

            weak_article_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT a.slug, a.title, COALESCE(c.key, ''),
                               LENGTH(COALESCE(a.body_farmer, '')),
                               LENGTH(COALESCE(a.body_pro, ''))
                        FROM guide_article a
                        LEFT JOIN guide_category c ON c.id = a.category_id
                        WHERE a.status = 'PUBLIE'
                          AND (LENGTH(COALESCE(a.body_farmer, '')) < 40
                               OR LENGTH(COALESCE(a.body_pro, '')) < 40)
                        ORDER BY a.slug
                        LIMIT 60
                        """
                    )
                )
            ).all()

            weak_term_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT t.slug, t.term
                        FROM guide_term t
                        WHERE t.status = 'PUBLIE'
                          AND (LENGTH(COALESCE(t.definition_farmer, '')) < 15
                               OR LENGTH(COALESCE(t.definition_pro, '')) < 15)
                        ORDER BY t.term
                        LIMIT 60
                        """
                    )
                )
            ).all()

            weak_faq_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT f.id, f.question, COALESCE(c.key, '')
                        FROM guide_faq f
                        LEFT JOIN guide_category c ON c.id = f.category_id
                        WHERE f.status = 'PUBLIE'
                          AND (LENGTH(COALESCE(f.answer_farmer, '')) < 20
                               OR LENGTH(COALESCE(f.answer_pro, '')) < 20)
                        ORDER BY f.id
                        LIMIT 60
                        """
                    )
                )
            ).all()

            orphan_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            (SELECT COUNT(*) FROM guide_procedure p
                               WHERE p.status = 'PUBLIE' AND p.article_id IS NULL),
                            (SELECT COUNT(*) FROM guide_article a
                               WHERE a.status = 'PUBLIE'
                                 AND NOT EXISTS (SELECT 1 FROM guide_article_link l
                                                   WHERE l.article_id = a.id)),
                            (SELECT COUNT(*) FROM guide_version
                               WHERE is_current = 1),
                            (SELECT COUNT(*) FROM guide_article
                               WHERE status <> 'PUBLIE')
                        """
                    )
                )
            ).first()

            data_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            (SELECT COUNT(*) FROM crop c JOIN parcel p
                                ON p.id = c.parcel_id
                              WHERE COALESCE(c.area_ha, 0) > COALESCE(p.area_ha, 0)),
                            (SELECT COUNT(*) FROM crop
                              WHERE sowing_date IS NOT NULL
                                AND expected_harvest_date IS NOT NULL
                                AND expected_harvest_date < sowing_date),
                            (SELECT COUNT(*) FROM parcel
                              WHERE COALESCE(area_ha, 0) <= 0),
                            (SELECT COUNT(*) FROM parcel p
                              WHERE EXISTS (SELECT 1 FROM parcel q
                                              WHERE q.id <> p.id
                                                AND COALESCE(q.code, '') <> ''
                                                AND q.code = p.code)),
                            (SELECT COUNT(*) FROM intervention
                              WHERE status IN ('PLANIFIEE', 'EN_COURS', 'REPORTEE')
                                AND scheduled_date < :today),
                            (SELECT COUNT(*) FROM intervention
                              WHERE status = 'REALISEE' AND done_date IS NULL),
                            (SELECT COUNT(*) FROM product
                              WHERE COALESCE(quantity_in_stock, 0)
                                    <= COALESCE(reorder_threshold, 0)),
                            (SELECT COUNT(*) FROM harvest
                              WHERE COALESCE(area_harvested_ha, 0) <= 0
                                 OR COALESCE(quantity, 0) <= 0),
                            (SELECT COUNT(*) FROM alert WHERE is_resolved = false
                                AND level = 'CRITIQUE'),
                            (SELECT COUNT(*) FROM intervention i
                              WHERE i.type = 'TRAITEMENT_PHYTO'
                                AND NOT EXISTS (
                                    SELECT 1 FROM intervention_product ip
                                     WHERE ip.intervention_id = i.id))
                        """
                    ),
                    {"today": today},
                )
            ).first()

            catalog_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            (SELECT COUNT(*) FROM crop_catalog_variety
                               WHERE crop_variety_id IS NULL),
                            (SELECT COUNT(*) FROM crop_culture cu
                               WHERE NOT EXISTS (
                                 SELECT 1 FROM crop_species s
                                  WHERE s.culture_id = cu.id)),
                            (SELECT COUNT(*) FROM crop_species s
                               WHERE NOT EXISTS (
                                 SELECT 1 FROM crop_catalog_variety v
                                  WHERE v.species_id = s.id)),
                            (SELECT COUNT(*) FROM crop_species
                               WHERE COALESCE(scientific_name, '') = ''
                                  OR COALESCE(sowing_window, '') = ''
                                  OR COALESCE(harvest_window, '') = ''
                                  OR COALESCE(water_requirement_mm, 0) <= 0),
                            (SELECT COUNT(*) FROM crop_catalog_variety
                               WHERE COALESCE(expected_yield_t_ha, 0) <= 0),
                            (SELECT COUNT(*) FROM crop c
                               WHERE c.variety_id IS NOT NULL
                                 AND NOT EXISTS (
                                   SELECT 1 FROM crop_variety v
                                    WHERE v.id = c.variety_id)),
                            (SELECT COUNT(*) FROM crop WHERE variety_id IS NULL)
                        """
                    )
                )
            ).first()

            if self.geometry_ready:
                geometry_rows = (
                    await asession.execute(
                        text(
                            """
                            SELECT
                                (SELECT COUNT(*) FROM parcel
                                  WHERE COALESCE(boundary_geojson, '') = ''
                                     OR COALESCE(geometry_vertex_count, 0) = 0),
                                (SELECT COUNT(*) FROM parcel
                                  WHERE COALESCE(geometry_area_ha, 0) > 0
                                    AND COALESCE(area_ha, 0) > 0
                                    AND ABS(COALESCE(geometry_area_ha, 0)
                                            - COALESCE(area_ha, 0))
                                        > 0.05 * COALESCE(area_ha, 0)),
                                (SELECT COUNT(*) FROM parcel
                                  WHERE COALESCE(geometry_source, 'AUCUNE')
                                        IN ('AUCUNE', 'GENEREE'))
                            """
                        )
                    )
                ).first()
            else:
                geometry_rows = None

        # --- Volumes des entités -------------------------------------
        counts: dict[str, int] = {
            str(row[0]): int(row[1] or 0) for row in entity_rows
        }
        entities: list[EntityRow] = []
        for spec in ENTITY_SPECS:
            total = counts.get(spec["table"], 0)
            if total > 0:
                status = STATUS_PRESENT
            elif spec["is_core"]:
                status = STATUS_MISSING
            else:
                status = STATUS_INCOMPLETE
            entities.append(
                {
                    "table": spec["table"],
                    "label": spec["label"],
                    "module": spec["module"],
                    "module_label": module_label(spec["module"]),
                    "role": spec["role"],
                    "is_core": spec["is_core"],
                    "rows": total,
                    "status": status,
                    "status_label": status_label(status),
                    "tone": status_tone(status),
                }
            )
            if total == 0:
                issues.append(
                    self._issue(
                        f"entite-vide-{spec['table']}",
                        spec["module"],
                        "donnees",
                        f"Aucune donnée dans « {spec['label']} »",
                        (
                            f"La table `{spec['table']}` est vide : "
                            f"{spec['role']}"
                        ),
                        spec["table"],
                        STATUS_MISSING
                        if spec["is_core"]
                        else STATUS_INCOMPLETE,
                        PRIORITY_HIGH if spec["is_core"] else PRIORITY_LOW,
                        (
                            "Amorcer ou saisir les données de référence pour "
                            "que le module devienne exploitable."
                        ),
                        0,
                    )
                )

        # --- Couverture éditoriale par catégorie ----------------------
        categories: list[CategoryRow] = []
        by_category: dict[str, CategoryRow] = {}
        for row in category_rows:
            key = str(row[0])
            articles = int(row[3] or 0)
            procedures = int(row[4] or 0)
            rules = int(row[5] or 0)
            faq = int(row[6] or 0)
            terms = int(row[7] or 0)
            total = articles + procedures + rules + faq + terms
            route = str(row[2])
            if articles == 0:
                status = STATUS_MISSING
            elif procedures == 0 or rules == 0:
                status = STATUS_INCOMPLETE
            elif route not in APP_ROUTES:
                status = STATUS_INCOHERENT
            else:
                status = STATUS_PRESENT
            entry: CategoryRow = {
                "key": key,
                "name": str(row[1]),
                "module_route": route or "—",
                "module_label": module_label(
                    next(
                        (
                            spec["key"]
                            for spec in MODULE_SPECS
                            if spec["route"] == route
                        ),
                        "",
                    )
                ),
                "articles": articles,
                "procedures": procedures,
                "rules": rules,
                "faq": faq,
                "terms": terms,
                "total": total,
                "status": status,
                "status_label": status_label(status),
                "tone": status_tone(status),
            }
            categories.append(entry)
            by_category[key] = entry

            owner = next(
                (
                    spec["key"]
                    for spec in MODULE_SPECS
                    if key in spec["categories"]
                ),
                "",
            )
            if articles == 0:
                issues.append(
                    self._issue(
                        f"cat-sans-article-{key}",
                        owner,
                        "guide",
                        f"Catégorie « {row[1]} » sans article publié",
                        "La catégorie existe mais n'expose aucune fiche de lecture.",
                        key,
                        STATUS_MISSING,
                        PRIORITY_HIGH,
                        "Publier au moins une fiche de référence dans cette catégorie.",
                    )
                )
            elif procedures == 0:
                issues.append(
                    self._issue(
                        f"cat-sans-procedure-{key}",
                        owner,
                        "guide",
                        f"Catégorie « {row[1]} » sans procédure",
                        "Aucun mode opératoire pas à pas n'accompagne les articles.",
                        key,
                        STATUS_INCOMPLETE,
                        PRIORITY_NORMAL,
                        "Ajouter une procédure « Comment faire dans AgriPro ? ».",
                    )
                )
            elif rules == 0:
                issues.append(
                    self._issue(
                        f"cat-sans-regle-{key}",
                        owner,
                        "guide",
                        f"Catégorie « {row[1]} » sans garde-fou",
                        "Aucune règle « Pourquoi ? » ou « Attention » rattachée.",
                        key,
                        STATUS_INCOMPLETE,
                        PRIORITY_NORMAL,
                        "Documenter au moins une règle de cohérence de la catégorie.",
                    )
                )
            if route and route not in APP_ROUTES:
                issues.append(
                    self._issue(
                        f"cat-route-{key}",
                        owner,
                        "liaison",
                        f"Route inconnue pour la catégorie « {row[1]} »",
                        f"La route « {route} » n'est pas enregistrée dans l'application.",
                        route,
                        STATUS_INCOHERENT,
                        PRIORITY_CRITICAL,
                        "Corriger la route de la catégorie ou enregistrer l'écran manquant.",
                    )
                )

        # --- Liens guide → application --------------------------------
        broken_links: dict[str, list[str]] = {}
        for row in link_rows:
            route = str(row[1])
            if route and route not in APP_ROUTES:
                broken_links.setdefault(route, []).append(str(row[2]))
        for route, slugs in broken_links.items():
            issues.append(
                self._issue(
                    f"lien-mort-{route}",
                    "guide",
                    "liaison",
                    f"Lien guide → application cassé ({route})",
                    (
                        f"{len(slugs)} article(s) pointent vers une route "
                        f"non enregistrée : {', '.join(slugs[:4])}."
                    ),
                    route,
                    STATUS_INCOHERENT,
                    PRIORITY_CRITICAL,
                    "Corriger la route du lien ou créer l'écran cible.",
                    len(slugs),
                )
            )

        # --- Règles métier --------------------------------------------
        rule_route_gaps: list[str] = []
        rule_field_gaps: list[str] = []
        rule_reason_gaps: list[str] = []
        for row in rule_rows:
            code = str(row[0])
            route = str(row[2])
            field = str(row[3])
            if route and route not in APP_ROUTES:
                rule_route_gaps.append(f"{code} → {route}")
            if not field:
                rule_field_gaps.append(code)
            if int(row[7] or 0) < 20 or int(row[8] or 0) < 10:
                rule_reason_gaps.append(code)
        if rule_route_gaps:
            issues.append(
                self._issue(
                    "regle-route",
                    "guide",
                    "liaison",
                    "Règles pointant vers un écran inconnu",
                    ", ".join(rule_route_gaps[:6]),
                    "guide_rule.module_route",
                    STATUS_INCOHERENT,
                    PRIORITY_CRITICAL,
                    "Réaligner `module_route` sur les routes réellement enregistrées.",
                    len(rule_route_gaps),
                )
            )
        if rule_field_gaps:
            issues.append(
                self._issue(
                    "regle-champ",
                    "guide",
                    "guide",
                    "Règles sans champ de rattachement",
                    (
                        f"{len(rule_field_gaps)} règle(s) sans `field_reference` : "
                        f"{', '.join(rule_field_gaps[:6])}."
                    ),
                    "guide_rule.field_reference",
                    STATUS_INCOMPLETE,
                    PRIORITY_NORMAL,
                    "Rattacher chaque règle au champ contrôlé pour l'aide contextuelle.",
                    len(rule_field_gaps),
                )
            )
        if rule_reason_gaps:
            issues.append(
                self._issue(
                    "regle-justification",
                    "guide",
                    "guide",
                    "Règles sans justification ni correction exploitable",
                    ", ".join(rule_reason_gaps[:6]),
                    "guide_rule.rationale",
                    STATUS_INCOMPLETE,
                    PRIORITY_NORMAL,
                    "Compléter le « Pourquoi ? » et la correction proposée.",
                    len(rule_reason_gaps),
                )
            )

        # --- Procédures -----------------------------------------------
        empty_procedures = [
            f"{row[0]}" for row in procedure_rows if int(row[4] or 0) == 0
        ]
        if empty_procedures:
            issues.append(
                self._issue(
                    "procedure-vide",
                    "guide",
                    "guide",
                    "Procédures publiées sans étape",
                    ", ".join(empty_procedures[:6]),
                    "guide_procedure_step",
                    STATUS_INCOMPLETE,
                    PRIORITY_HIGH,
                    "Rédiger les étapes ou repasser la procédure en brouillon.",
                    len(empty_procedures),
                )
            )
        procedure_bad_routes = [
            f"{row[0]} → {row[3]}"
            for row in procedure_rows
            if str(row[3]) and str(row[3]) not in APP_ROUTES
        ]
        if procedure_bad_routes:
            issues.append(
                self._issue(
                    "procedure-route",
                    "guide",
                    "liaison",
                    "Procédures pointant vers un écran inconnu",
                    ", ".join(procedure_bad_routes[:6]),
                    "guide_procedure.module_route",
                    STATUS_INCOHERENT,
                    PRIORITY_HIGH,
                    "Corriger la route de la procédure.",
                    len(procedure_bad_routes),
                )
            )

        # --- Contenus éditoriaux incomplets ---------------------------
        if weak_article_rows:
            issues.append(
                self._issue(
                    "article-double-lecture",
                    "guide",
                    "guide",
                    "Articles sans double lecture complète",
                    ", ".join(str(row[0]) for row in weak_article_rows[:6]),
                    "guide_article.body_pro",
                    STATUS_INCOMPLETE,
                    PRIORITY_HIGH,
                    "Compléter la lecture agricole et la lecture AgriPro.",
                    len(weak_article_rows),
                )
            )
        if weak_term_rows:
            issues.append(
                self._issue(
                    "terme-incomplet",
                    "guide",
                    "guide",
                    "Entrées de dictionnaire incomplètes",
                    ", ".join(str(row[1]) for row in weak_term_rows[:6]),
                    "guide_term.definition_pro",
                    STATUS_INCOMPLETE,
                    PRIORITY_NORMAL,
                    "Compléter les deux définitions de chaque entrée.",
                    len(weak_term_rows),
                )
            )
        if weak_faq_rows:
            issues.append(
                self._issue(
                    "faq-incomplete",
                    "guide",
                    "guide",
                    "Questions fréquentes sans réponse complète",
                    f"{len(weak_faq_rows)} question(s) à compléter.",
                    "guide_faq.answer_pro",
                    STATUS_INCOMPLETE,
                    PRIORITY_NORMAL,
                    "Rédiger les deux niveaux de réponse.",
                    len(weak_faq_rows),
                )
            )

        if orphan_rows is not None:
            unlinked_articles = int(orphan_rows[1] or 0)
            current_versions = int(orphan_rows[2] or 0)
            if unlinked_articles > 0:
                issues.append(
                    self._issue(
                        "article-sans-lien",
                        "guide",
                        "liaison",
                        "Articles sans lien direct vers un écran",
                        (
                            f"{unlinked_articles} article(s) publiés n'offrent "
                            "aucun accès direct au module concerné."
                        ),
                        "guide_article_link",
                        STATUS_INCOMPLETE,
                        PRIORITY_NORMAL,
                        "Ajouter au moins un lien module par article.",
                        unlinked_articles,
                    )
                )
            if current_versions != 1:
                issues.append(
                    self._issue(
                        "version-courante",
                        "guide",
                        "guide",
                        "Version courante du Guide indéterminée",
                        (
                            f"{current_versions} version(s) marquée(s) courante(s) : "
                            "la consultation doit en désigner exactement une."
                        ),
                        "guide_version.is_current",
                        STATUS_INCOHERENT,
                        PRIORITY_HIGH,
                        "Publier une seule version courante depuis le pupitre éditorial.",
                        current_versions,
                    )
                )

        # --- Cohérence des données métier -----------------------------
        if data_rows is not None:
            metrics: list[tuple[int, str, str, str, str, str, str, str]] = [
                (
                    int(data_rows[0] or 0),
                    "surface-culture",
                    "parcelles",
                    "Cultures dépassant la surface de leur parcelle",
                    "COH-CULT-001 · crop.area_ha",
                    STATUS_INCOHERENT,
                    PRIORITY_CRITICAL,
                    "Réduire la surface implantée ou corriger la surface de l'îlot.",
                ),
                (
                    int(data_rows[1] or 0),
                    "dates-culture",
                    "parcelles",
                    "Récoltes prévues avant le semis",
                    "COH-CULT-002 · crop.expected_harvest_date",
                    STATUS_INCOHERENT,
                    PRIORITY_HIGH,
                    "Corriger la chronologie semis → récolte de la fiche culturale.",
                ),
                (
                    int(data_rows[2] or 0),
                    "surface-parcelle",
                    "parcelles",
                    "Parcelles sans surface exploitable",
                    "COH-PARC-002 · parcel.area_ha",
                    STATUS_INCOHERENT,
                    PRIORITY_CRITICAL,
                    "Renseigner une surface strictement positive.",
                ),
                (
                    int(data_rows[3] or 0),
                    "code-parcelle",
                    "parcelles",
                    "Codes d'îlot en doublon",
                    "COH-PARC-001 · parcel.code",
                    STATUS_INCOHERENT,
                    PRIORITY_CRITICAL,
                    "Rendre chaque code d'îlot unique avant toute autre saisie.",
                ),
                (
                    int(data_rows[4] or 0),
                    "chantier-retard",
                    "traitements",
                    "Chantiers planifiés en retard",
                    "POU-TRAV-001 · intervention.scheduled_date",
                    STATUS_INCOMPLETE,
                    PRIORITY_HIGH,
                    "Clôturer, reporter ou annuler les interventions dépassées.",
                ),
                (
                    int(data_rows[5] or 0),
                    "chantier-sans-date",
                    "traitements",
                    "Interventions réalisées sans date de réalisation",
                    "COH-TRAV-002 · intervention.done_date",
                    STATUS_INCOHERENT,
                    PRIORITY_HIGH,
                    "Renseigner la date de réalisation à la clôture.",
                ),
                (
                    int(data_rows[6] or 0),
                    "stock-critique",
                    "traitements",
                    "Produits au seuil de réapprovisionnement",
                    "ATT-STOCK-002 · product.reorder_threshold",
                    STATUS_INCOMPLETE,
                    PRIORITY_NORMAL,
                    "Commander ou reporter les chantiers concernés.",
                ),
                (
                    int(data_rows[7] or 0),
                    "recolte-invalide",
                    "traitements",
                    "Récoltes sans quantité ni surface exploitable",
                    "COH-RECO-001 · harvest.area_harvested_ha",
                    STATUS_INCOHERENT,
                    PRIORITY_HIGH,
                    "Compléter pesées et surface réellement moissonnée.",
                ),
                (
                    int(data_rows[8] or 0),
                    "alerte-critique",
                    "cockpit",
                    "Alertes critiques non résolues",
                    "alert.level = CRITIQUE",
                    STATUS_INCOMPLETE,
                    PRIORITY_HIGH,
                    "Traiter ou clôturer les alertes critiques du cockpit.",
                ),
                (
                    int(data_rows[9] or 0),
                    "phyto-sans-intrant",
                    "traitements",
                    "Traitements phytosanitaires sans intrant tracé",
                    "COH-PHY-003 · intervention_product",
                    STATUS_INCOHERENT,
                    PRIORITY_CRITICAL,
                    "Renseigner produit, dose et surface traitée pour le registre.",
                ),
            ]
            # Les alertes et les stocks sous seuil reflètent un état réel
            # d'exploitation : ils restent visibles mais sont classés comme
            # états à traiter, et non comme connexions cassées.
            operational_keys = {"alerte-critique", "stock-critique"}
            for (
                count,
                key,
                module,
                label,
                reference,
                status,
                priority,
                recommendation,
            ) in metrics:
                if count > 0:
                    issues.append(
                        self._issue(
                            f"data-{key}",
                            module,
                            "exploitation"
                            if key in operational_keys
                            else "coherence",
                            label,
                            f"{count} enregistrement(s) concerné(s).",
                            reference,
                            status,
                            priority,
                            recommendation,
                            count,
                        )
                    )

        if catalog_rows is not None:
            catalog_metrics: list[
                tuple[int, str, str, str, str, str, str, str, str]
            ] = [
                (
                    int(catalog_rows[0] or 0),
                    "variete-non-liee",
                    "referentiel",
                    "liaison",
                    "Variétés du référentiel sans correspondance historique",
                    "crop_catalog_variety.crop_variety_id",
                    STATUS_INCOHERENT,
                    PRIORITY_HIGH,
                    (
                        "Matérialiser la variété dans le référentiel variétal "
                        "historique pour la rendre sélectionnable sur un îlot."
                    ),
                ),
                (
                    int(catalog_rows[1] or 0),
                    "culture-sans-espece",
                    "referentiel",
                    "donnees",
                    "Cultures du référentiel sans espèce décrite",
                    "crop_species.culture_id",
                    STATUS_INCOMPLETE,
                    PRIORITY_NORMAL,
                    "Décrire au moins une espèce botanique par culture.",
                ),
                (
                    int(catalog_rows[2] or 0),
                    "espece-sans-variete",
                    "referentiel",
                    "donnees",
                    "Espèces du référentiel sans variété exploitable",
                    "crop_catalog_variety.species_id",
                    STATUS_INCOMPLETE,
                    PRIORITY_NORMAL,
                    "Ajouter une fiche variétale de référence par espèce.",
                ),
                (
                    int(catalog_rows[3] or 0),
                    "espece-incomplete",
                    "referentiel",
                    "coherence",
                    "Espèces sans repères agronomiques exploitables",
                    "crop_species.water_requirement_mm",
                    STATUS_INCOHERENT,
                    PRIORITY_NORMAL,
                    (
                        "Compléter nom latin, fenêtres de semis et de récolte "
                        "et besoin en eau : l'irrigation en dépend."
                    ),
                ),
                (
                    int(catalog_rows[4] or 0),
                    "variete-sans-rendement",
                    "referentiel",
                    "coherence",
                    "Variétés sans rendement de référence",
                    "crop_catalog_variety.expected_yield_t_ha",
                    STATUS_INCOMPLETE,
                    PRIORITY_LOW,
                    "Renseigner le rendement visé pour comparer les récoltes.",
                ),
                (
                    int(catalog_rows[5] or 0),
                    "culture-variete-orpheline",
                    "parcelles",
                    "coherence",
                    "Fiches culturales pointant vers une variété inexistante",
                    "crop.variety_id",
                    STATUS_INCOHERENT,
                    PRIORITY_CRITICAL,
                    "Réaffecter la culture à une variété du référentiel.",
                ),
                (
                    int(catalog_rows[6] or 0),
                    "culture-sans-variete",
                    "parcelles",
                    "coherence",
                    "Fiches culturales non reliées au référentiel",
                    "crop.variety_id",
                    STATUS_INCOMPLETE,
                    PRIORITY_NORMAL,
                    (
                        "Choisir la variété du référentiel sur la fiche "
                        "culturale : espèce, cycle et rendement en découlent."
                    ),
                ),
            ]
            for (
                count,
                key,
                module,
                domain,
                label,
                reference,
                status,
                priority,
                recommendation,
            ) in catalog_metrics:
                if count > 0:
                    issues.append(
                        self._issue(
                            f"catalog-{key}",
                            module,
                            domain,
                            label,
                            f"{count} enregistrement(s) concerné(s).",
                            reference,
                            status,
                            priority,
                            recommendation,
                            count,
                        )
                    )

        if geometry_rows is not None:
            no_contour = int(geometry_rows[0] or 0)
            mismatch = int(geometry_rows[1] or 0)
            generated = int(geometry_rows[2] or 0)
            if no_contour > 0:
                issues.append(
                    self._issue(
                        "geo-sans-contour",
                        "cartographie",
                        "coherence",
                        "Îlots sans contour cartographique",
                        f"{no_contour} parcelle(s) sans polygone enregistré.",
                        "parcel.boundary_geojson",
                        STATUS_INCOMPLETE,
                        PRIORITY_NORMAL,
                        (
                            "Tracer ou importer le contour depuis l'éditeur "
                            "GeoJSON, puis clore le contrôle dans le poste de "
                            "contrôle des contours de la cartographie."
                        ),
                        no_contour,
                    )
                )
            if mismatch > 0:
                issues.append(
                    self._issue(
                        "geo-ecart-surface",
                        "cartographie",
                        "coherence",
                        "Écart de surface supérieur à 5 %",
                        (
                            f"{mismatch} parcelle(s) présentent un écart entre "
                            "surface déclarée et surface calculée."
                        ),
                        "ATT-PARC-003 · parcel.geometry_area_ha",
                        STATUS_INCOHERENT,
                        PRIORITY_HIGH,
                        (
                            "Arbitrer entre contour incomplet et surface "
                            "obsolète, puis marquer l'îlot à relever depuis le "
                            "poste de contrôle des contours."
                        ),
                        mismatch,
                    )
                )
            if generated > 0:
                issues.append(
                    self._issue(
                        "geo-genere",
                        "cartographie",
                        "coherence",
                        "Contours générés automatiquement",
                        (
                            f"{generated} parcelle(s) affichent un contour "
                            "approximatif, non exploitable pour un calcul."
                        ),
                        "parcel.geometry_source",
                        STATUS_INCOMPLETE,
                        PRIORITY_LOW,
                        (
                            "Vérifier chaque contour généré à l'écran, ou "
                            "programmer un relevé GPS / import cadastral, "
                            "depuis le poste de contrôle des contours."
                        ),
                        generated,
                    )
                )
        else:
            issues.append(
                self._issue(
                    "geo-colonnes",
                    "cartographie",
                    "donnees",
                    "Colonnes de géométrie absentes en base",
                    (
                        "La cartographie fonctionne en mode dégradé : les "
                        "contours ne peuvent pas être enregistrés."
                    ),
                    "parcel.boundary_geojson",
                    STATUS_MISSING,
                    PRIORITY_CRITICAL,
                    "Appliquer la migration de géométrie avant tout tracé.",
                    0,
                )
            )

        # --- Matrice de couverture par module -------------------------
        modules: list[ModuleRow] = []
        for spec in MODULE_SPECS:
            key = spec["key"]
            module_issues = [item for item in issues if item["module"] == key]
            blocking = [
                item
                for item in module_issues
                if item["priority"] == PRIORITY_CRITICAL
            ]
            articles = 0
            procedures = 0
            rules = 0
            faq = 0
            terms = 0
            missing_categories: list[str] = []
            for cat_key in spec["categories"]:
                entry = by_category.get(cat_key)
                if entry is None:
                    missing_categories.append(cat_key)
                    continue
                articles += entry["articles"]
                procedures += entry["procedures"]
                rules += entry["rules"]
                faq += entry["faq"]
                terms += entry["terms"]
                if entry["articles"] == 0:
                    missing_categories.append(cat_key)
            guide_total = articles + procedures + rules + faq + terms
            records = sum(counts.get(table, 0) for table in spec["tables"])
            empty_tables = [
                table for table in spec["tables"] if counts.get(table, 0) == 0
            ]

            checks = [
                spec["route"] in APP_ROUTES,
                articles > 0,
                procedures > 0,
                rules > 0,
                records > 0,
                len(empty_tables) == 0,
                len(blocking) == 0,
            ]
            coverage = int(
                round(100 * sum(1 for ok in checks if ok) / len(checks))
            )

            if spec["route"] not in APP_ROUTES or records == 0:
                status = STATUS_MISSING
            elif blocking:
                status = STATUS_INCOHERENT
            elif module_issues or missing_categories or empty_tables:
                status = (
                    STATUS_INCOHERENT
                    if any(
                        item["status"] == STATUS_INCOHERENT
                        for item in module_issues
                    )
                    else STATUS_INCOMPLETE
                )
            else:
                status = STATUS_PRESENT

            if status == STATUS_MISSING or blocking:
                priority = PRIORITY_CRITICAL
            elif status == STATUS_INCOHERENT:
                priority = PRIORITY_HIGH
            elif status == STATUS_INCOMPLETE:
                priority = PRIORITY_NORMAL
            else:
                priority = PRIORITY_LOW

            findings: list[str] = []
            if spec["route"] not in APP_ROUTES:
                findings.append(
                    f"La route {spec['route']} n'est pas enregistrée dans l'application."
                )
            if records == 0:
                findings.append(
                    "Aucune donnée métier : le module ne peut rien afficher."
                )
            if missing_categories:
                findings.append(
                    "Catégories du Guide non couvertes : "
                    + ", ".join(missing_categories)
                )
            if empty_tables:
                findings.append(
                    "Entités sans enregistrement : " + ", ".join(empty_tables)
                )
            if procedures == 0:
                findings.append(
                    "Aucune procédure pas à pas ne documente l'écran."
                )
            if rules == 0:
                findings.append(
                    "Aucune règle de cohérence n'encadre les saisies."
                )
            for item in module_issues[:4]:
                findings.append(f"{item['label']} ({item['detail']})")
            if not findings:
                findings.append(
                    "Module couvert : données présentes, guide et garde-fous rattachés."
                )

            recommendations = [
                item["recommendation"] for item in module_issues[:4]
            ]
            if missing_categories:
                recommendations.append(
                    "Publier une fiche de référence pour chaque catégorie non couverte."
                )
            if procedures == 0:
                recommendations.append(
                    "Ajouter une procédure « Comment faire dans AgriPro ? » à cet écran."
                )
            if not recommendations:
                recommendations.append(
                    "Maintenir la couverture : relire le contenu à chaque évolution."
                )

            modules.append(
                {
                    "key": key,
                    "label": spec["label"],
                    "route": spec["route"],
                    "icon": spec["icon"],
                    "mission": spec["mission"],
                    "features": spec["features"],
                    "categories": spec["categories"],
                    "missing_categories": missing_categories,
                    "tables": len(spec["tables"]),
                    "empty_tables": empty_tables,
                    "records": records,
                    "articles": articles,
                    "procedures": procedures,
                    "rules": rules,
                    "faq": faq,
                    "terms": terms,
                    "guide_total": guide_total,
                    "coverage": coverage,
                    "coverage_pct": f"{coverage}%",
                    "issue_count": len(module_issues),
                    "blocking_count": len(blocking),
                    "status": status,
                    "status_label": status_label(status),
                    "tone": status_tone(status),
                    "priority": priority,
                    "priority_label": priority_label(priority),
                    "priority_tone": priority_tone(priority),
                    "findings": findings,
                    "recommendations": recommendations,
                }
            )

        modules.sort(
            key=lambda item: (
                PRIORITY_WEIGHT.get(item["priority"], 9),
                item["coverage"],
            )
        )
        issues.sort(
            key=lambda item: (
                PRIORITY_WEIGHT.get(item["priority"], 9),
                item["module_label"],
                item["label"],
            )
        )

        total_records = sum(counts.values())
        guide_contents = sum(
            counts.get(table, 0)
            for table in (
                "guide_article",
                "guide_procedure",
                "guide_term",
                "guide_faq",
                "guide_rule",
                "guide_learning_path",
            )
        )
        # Compteurs phénologiques : exposés dans les KPI sans altérer l'existant.
        phenology = await phenology_audit_report()
        coverage_avg = (
            round(sum(item["coverage"] for item in modules) / len(modules), 1)
            if modules
            else 0.0
        )

        self.modules = modules
        self.categories = categories
        self.entities = entities
        self.issues = issues
        self.kpis = {
            "modules": float(len(modules)),
            "present": float(
                len([m for m in modules if m["status"] == STATUS_PRESENT])
            ),
            "incomplete": float(
                len([m for m in modules if m["status"] == STATUS_INCOMPLETE])
            ),
            "incoherent": float(
                len([m for m in modules if m["status"] == STATUS_INCOHERENT])
            ),
            "missing": float(
                len([m for m in modules if m["status"] == STATUS_MISSING])
            ),
            "coverage": coverage_avg,
            "issues": float(len(issues)),
            "blocking": float(
                len(
                    [
                        item
                        for item in issues
                        if item["priority"] == PRIORITY_CRITICAL
                    ]
                )
            ),
            "entities": float(len(entities)),
            "records": float(total_records),
            "guide_contents": float(guide_contents),
            "empty_entities": float(
                len([item for item in entities if item["rows"] == 0])
            ),
            "phenology_profiles": float(
                phenology.get("active_profiles", 0)
                or phenology.get("profiles", 0)
            ),
            "phenology_stages": float(
                phenology.get("active_stages", 0) or phenology.get("stages", 0)
            ),
            "phenology_critical_stages": float(
                phenology.get("critical_stages", 0)
            ),
            "phenology_recommendations": float(
                phenology.get("recommendations", 0)
            ),
            "phenology_observations": float(phenology.get("observations", 0)),
            "phenology_changes": float(phenology.get("changes", 0)),
            "phenology_cultures": float(phenology.get("cultures", 0)),
            "phenology_invalid_observations": float(
                phenology.get("invalid_observations", 0)
            ),
        }
        self.generated_label = (
            f"{WEEKDAYS_SHORT[today.weekday()]}. {today.day} "
            f"{MONTHS[today.month - 1]} {today.year}"
        )
        self.is_loading = False

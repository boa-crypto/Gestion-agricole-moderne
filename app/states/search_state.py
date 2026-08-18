"""État de la recherche globale transversale.

Interroge toutes les tables métier principales via `rx.asession()` en SQL brut
paramétré, avec un filtre de dates optionnel appliqué à la date métier la plus
pertinente de chaque table, des filtres par type d'actif agricole et des
compteurs de résultats.
"""

from __future__ import annotations

import datetime
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.date_utils import as_date
from app.catalog_link import materialize_catalog_varieties
from app.seed import seed_dashboard_data
from app.seed_catalog import link_legacy_varieties, seed_catalog_data
from app.seed_employees import seed_employee_data
from app.seed_equipment import seed_equipment_data
from app.seed_expenses import seed_expense_data
from app.seed_operations import seed_operations_data
from app.access_reference import ACTION_LABELS as PERMISSION_ACTION_LABELS
from app.access_reference import (
    ACTIVITY_KINDS,
    USER_STATUS_LABELS,
)
from app.states.remediation_state import (
    ACTION_LABELS,
    DOMAIN_LABELS as REMEDIATION_DOMAIN_LABELS,
)
from app.states.expenses_state import (
    EXPENSE_STATUS_LABELS,
    PAYMENT_LABELS,
)
from app.states.dashboard_state import (
    CROP_STATUS_LABELS,
    HEALTH_LABELS,
    INTERVENTION_LABELS,
    INTERVENTION_STATUS_LABELS,
    IRRIGATION_LABELS,
    MONTHS,
    PARCEL_STATUS_LABELS,
    SOIL_LABELS,
    STAGE_LABELS,
    WEEKDAYS_SHORT,
)
from app.states.employees_state import (
    ASSIGNMENT_STATUS_LABELS,
    AVAILABILITY_LABELS,
    CONTRACT_LABELS,
    EMPLOYEE_STATUS_LABELS,
    LEVEL_LABELS,
    ROLE_LABELS,
)
from app.states.maintenance_state import (
    BASIS_LABELS,
    COST_TYPE_LABELS,
    EQUIPMENT_STATUS_LABELS,
    KIND_LABELS,
    MAINTENANCE_STATUS_LABELS,
    OWNERSHIP_LABELS,
    PRIORITY_LABELS,
)
from app.states.maintenance_state import CATEGORY_LABELS as EQUIPMENT_CATEGORIES
from app.states.operations_state import CATEGORY_LABELS as PRODUCT_CATEGORIES
from app.states.operations_state import MOVEMENT_LABELS, QUALITY_LABELS

PER_TYPE_LIMIT: int = 12
EXCERPT_LENGTH: int = 190

# Dictionnaire agrégé des libellés d'énumérations métier, utilisé pour
# transformer les clés brutes remontées par SQL en badges lisibles.
LABELS: dict[str, str] = {
    **SOIL_LABELS,
    **IRRIGATION_LABELS,
    **PARCEL_STATUS_LABELS,
    **STAGE_LABELS,
    **CROP_STATUS_LABELS,
    **HEALTH_LABELS,
    **INTERVENTION_LABELS,
    **INTERVENTION_STATUS_LABELS,
    **PRODUCT_CATEGORIES,
    **MOVEMENT_LABELS,
    **QUALITY_LABELS,
    **EMPLOYEE_STATUS_LABELS,
    **CONTRACT_LABELS,
    **LEVEL_LABELS,
    **AVAILABILITY_LABELS,
    **ROLE_LABELS,
    **ASSIGNMENT_STATUS_LABELS,
    **EQUIPMENT_CATEGORIES,
    **EQUIPMENT_STATUS_LABELS,
    **OWNERSHIP_LABELS,
    **KIND_LABELS,
    **MAINTENANCE_STATUS_LABELS,
    **PRIORITY_LABELS,
    **COST_TYPE_LABELS,
    **BASIS_LABELS,
    **EXPENSE_STATUS_LABELS,
    **PAYMENT_LABELS,
    **ACTION_LABELS,
    **REMEDIATION_DOMAIN_LABELS,
    **PERMISSION_ACTION_LABELS,
    **ACTIVITY_KINDS,
    **USER_STATUS_LABELS,
    "INFO": "Information",
    "ATTENTION": "Attention",
    "CRITIQUE": "Critique",
}

PERIODS: list[tuple[str, str, int]] = [
    ("7", "7 j", 7),
    ("30", "30 j", 30),
    ("90", "90 j", 90),
    ("365", "12 mois", 365),
    ("TOUT", "Tout", 0),
]

# Chaque entrée décrit une table métier : source SQL, colonnes projetées dans
# un format unique (id, titre, sous-titre, 3 badges, date, extrait), clause de
# recherche plein texte et expression de date métier filtrable.
SPECS: list[dict[str, str]] = [
    {
        "key": "parcelle",
        "label": "Parcelles",
        "singular": "Parcelle",
        "icon": "map",
        "tone": "vegetal",
        "href": "/parcelles",
        "href_label": "Ouvrir l'assolement",
        "date_kind": "Créée le",
        "source": "FROM parcel p",
        "id_expr": "p.id",
        "title": "COALESCE(NULLIF(p.code, '') || ' · ', '') || p.name",
        "subtitle": "COALESCE(NULLIF(p.locality, ''), 'Localité non renseignée')",
        "badge_a": "p.status",
        "badge_b": "CAST(ROUND(COALESCE(p.area_ha, 0), 1) AS VARCHAR) || ' ha'",
        "badge_c": "CASE WHEN p.is_organic THEN 'Conduite bio' ELSE p.soil_type END",
        "excerpt": "COALESCE(p.notes, '')",
        "search": (
            "LOWER(p.name) LIKE :q OR LOWER(COALESCE(p.code, '')) LIKE :q"
            " OR LOWER(COALESCE(p.locality, '')) LIKE :q"
            " OR LOWER(COALESCE(p.notes, '')) LIKE :q"
        ),
        "date_expr": "DATE(p.created_at)",
    },
    {
        "key": "culture",
        "label": "Cultures",
        "singular": "Culture",
        "icon": "sprout",
        "tone": "vegetal",
        "href": "/parcelles",
        "href_label": "Ouvrir la fiche culturale",
        "date_kind": "Semis",
        "source": (
            "FROM crop c JOIN parcel p ON p.id = c.parcel_id"
            " LEFT JOIN crop_variety v ON v.id = c.variety_id"
        ),
        "id_expr": "c.id",
        "title": "c.name",
        "subtitle": "COALESCE(NULLIF(p.code, '') || ' · ', '') || p.name",
        "badge_a": "c.status",
        "badge_b": "c.stage",
        "badge_c": "c.health",
        "excerpt": "COALESCE(NULLIF(c.notes, ''), COALESCE(v.species, ''))",
        "search": (
            "LOWER(c.name) LIKE :q OR LOWER(COALESCE(c.season, '')) LIKE :q"
            " OR LOWER(p.name) LIKE :q"
            " OR LOWER(COALESCE(v.species, '')) LIKE :q"
            " OR LOWER(COALESCE(v.name, '')) LIKE :q"
            " OR LOWER(COALESCE(c.notes, '')) LIKE :q"
        ),
        "date_expr": "COALESCE(c.sowing_date, DATE(c.created_at))",
    },
    {
        "key": "variete",
        "label": "Variétés",
        "singular": "Variété",
        "icon": "flower-2",
        "tone": "vegetal",
        "href": "/parcelles",
        "href_label": "Ouvrir le référentiel",
        "date_kind": "Référencée le",
        "source": "FROM crop_variety v",
        "id_expr": "v.id",
        "title": "v.name",
        "subtitle": "v.species",
        "badge_a": "COALESCE(NULLIF(v.family, ''), '')",
        "badge_b": "CAST(COALESCE(v.cycle_days, 0) AS VARCHAR) || ' j de cycle'",
        "badge_c": (
            "CAST(ROUND(COALESCE(v.expected_yield_t_ha, 0), 1) AS VARCHAR)"
            " || ' t/ha visés'"
        ),
        "excerpt": "COALESCE(v.notes, '')",
        "search": (
            "LOWER(v.name) LIKE :q OR LOWER(v.species) LIKE :q"
            " OR LOWER(COALESCE(v.family, '')) LIKE :q"
            " OR LOWER(COALESCE(v.notes, '')) LIKE :q"
        ),
        "date_expr": "DATE(v.created_at)",
    },
    {
        "key": "intervention",
        "label": "Interventions",
        "singular": "Intervention",
        "icon": "spray-can",
        "tone": "operations",
        "href": "/traitements",
        "href_label": "Ouvrir le journal",
        "date_kind": "Échéance",
        "source": (
            "FROM intervention i JOIN parcel p ON p.id = i.parcel_id"
            " LEFT JOIN crop c ON c.id = i.crop_id"
        ),
        "id_expr": "i.id",
        "title": "i.title",
        "subtitle": "COALESCE(NULLIF(p.code, '') || ' · ', '') || p.name",
        "badge_a": "i.status",
        "badge_b": "i.type",
        "badge_c": "COALESCE(NULLIF(i.operator, ''), '')",
        "excerpt": (
            "COALESCE(NULLIF(i.notes, ''), COALESCE(NULLIF(i.target, ''),"
            " COALESCE(i.equipment, '')))"
        ),
        "search": (
            "LOWER(i.title) LIKE :q OR LOWER(COALESCE(i.operator, '')) LIKE :q"
            " OR LOWER(COALESCE(i.equipment, '')) LIKE :q"
            " OR LOWER(COALESCE(i.target, '')) LIKE :q"
            " OR LOWER(COALESCE(i.notes, '')) LIKE :q"
            " OR LOWER(p.name) LIKE :q OR LOWER(COALESCE(c.name, '')) LIKE :q"
        ),
        "date_expr": "COALESCE(i.done_date, i.scheduled_date)",
    },
    {
        "key": "produit",
        "label": "Produits & intrants",
        "singular": "Produit",
        "icon": "flask-conical",
        "tone": "operations",
        "href": "/traitements",
        "href_label": "Ouvrir le magasin",
        "date_kind": "Référencé le",
        "source": "FROM product pr",
        "id_expr": "pr.id",
        "title": "pr.name",
        "subtitle": "COALESCE(NULLIF(pr.supplier, ''), 'Fournisseur non précisé')",
        "badge_a": "pr.category",
        "badge_b": (
            "CAST(ROUND(COALESCE(pr.quantity_in_stock, 0), 1) AS VARCHAR)"
            " || ' ' || COALESCE(NULLIF(pr.unit, ''), 'u') || ' en stock'"
        ),
        "badge_c": "CASE WHEN pr.is_organic_approved THEN 'Homologué AB' ELSE '' END",
        "excerpt": (
            "COALESCE(NULLIF(pr.notes, ''), COALESCE(pr.active_substance, ''))"
        ),
        "search": (
            "LOWER(pr.name) LIKE :q OR LOWER(COALESCE(pr.supplier, '')) LIKE :q"
            " OR LOWER(COALESCE(pr.reference, '')) LIKE :q"
            " OR LOWER(COALESCE(pr.active_substance, '')) LIKE :q"
            " OR LOWER(COALESCE(pr.storage_location, '')) LIKE :q"
            " OR LOWER(COALESCE(pr.notes, '')) LIKE :q"
        ),
        "date_expr": "DATE(pr.created_at)",
    },
    {
        "key": "mouvement",
        "label": "Mouvements de stock",
        "singular": "Mouvement",
        "icon": "arrow-left-right",
        "tone": "operations",
        "href": "/traitements",
        "href_label": "Ouvrir les mouvements",
        "date_kind": "Mouvement le",
        "source": "FROM stock_movement m JOIN product pr ON pr.id = m.product_id",
        "id_expr": "m.id",
        "title": "pr.name",
        "subtitle": "COALESCE(NULLIF(m.reference, ''), 'Sans référence')",
        "badge_a": "m.type",
        "badge_b": (
            "CAST(ROUND(COALESCE(m.quantity, 0), 2) AS VARCHAR) || ' '"
            " || COALESCE(NULLIF(pr.unit, ''), 'u')"
        ),
        "badge_c": (
            "CAST(ROUND(COALESCE(m.quantity, 0) * COALESCE(m.unit_price, 0), 0)"
            " AS VARCHAR) || ' €'"
        ),
        "excerpt": "COALESCE(m.notes, '')",
        "search": (
            "LOWER(pr.name) LIKE :q OR LOWER(COALESCE(m.reference, '')) LIKE :q"
            " OR LOWER(COALESCE(m.notes, '')) LIKE :q"
        ),
        "date_expr": "m.movement_date",
    },
    {
        "key": "recolte",
        "label": "Récoltes",
        "singular": "Récolte",
        "icon": "wheat",
        "tone": "operations",
        "href": "/traitements",
        "href_label": "Ouvrir les récoltes",
        "date_kind": "Récoltée le",
        "source": (
            "FROM harvest h JOIN crop c ON c.id = h.crop_id"
            " JOIN parcel p ON p.id = c.parcel_id"
        ),
        "id_expr": "h.id",
        "title": "c.name",
        "subtitle": "COALESCE(NULLIF(p.code, '') || ' · ', '') || p.name",
        "badge_a": "h.quality",
        "badge_b": (
            "CAST(ROUND(COALESCE(h.quantity, 0), 1) AS VARCHAR) || ' '"
            " || COALESCE(NULLIF(h.unit, ''), 't')"
        ),
        "badge_c": (
            "CAST(ROUND(COALESCE(h.yield_t_ha, 0), 1) AS VARCHAR) || ' t/ha'"
        ),
        "excerpt": (
            "COALESCE(NULLIF(h.notes, ''), COALESCE(h.storage_location, ''))"
        ),
        "search": (
            "LOWER(c.name) LIKE :q OR LOWER(p.name) LIKE :q"
            " OR LOWER(COALESCE(h.operator, '')) LIKE :q"
            " OR LOWER(COALESCE(h.storage_location, '')) LIKE :q"
            " OR LOWER(COALESCE(h.notes, '')) LIKE :q"
        ),
        "date_expr": "h.harvest_date",
    },
    {
        "key": "alerte",
        "label": "Alertes agronomiques",
        "singular": "Alerte",
        "icon": "triangle-alert",
        "tone": "alerte",
        "href": "/",
        "href_label": "Ouvrir le cockpit",
        "date_kind": "Déclenchée le",
        "source": "FROM alert a LEFT JOIN parcel p ON p.id = a.parcel_id",
        "id_expr": "a.id",
        "title": "a.title",
        "subtitle": "COALESCE(p.name, 'Exploitation entière')",
        "badge_a": "a.level",
        "badge_b": "COALESCE(NULLIF(a.category, ''), '')",
        "badge_c": "CASE WHEN a.is_resolved THEN 'Résolue' ELSE 'Active' END",
        "excerpt": "COALESCE(a.message, '')",
        "search": (
            "LOWER(a.title) LIKE :q OR LOWER(COALESCE(a.message, '')) LIKE :q"
            " OR LOWER(COALESCE(a.category, '')) LIKE :q"
            " OR LOWER(COALESCE(p.name, '')) LIKE :q"
        ),
        "date_expr": "COALESCE(a.triggered_on, DATE(a.created_at))",
    },
    {
        "key": "employe",
        "label": "Employés",
        "singular": "Employé",
        "icon": "users-round",
        "tone": "humain",
        "href": "/employes",
        "href_label": "Ouvrir le registre",
        "date_kind": "Embauché le",
        "source": "FROM employee e",
        "id_expr": "e.id",
        "title": "e.first_name || ' ' || e.last_name",
        "subtitle": "COALESCE(NULLIF(e.job_title, ''), 'Poste non précisé')",
        "badge_a": "e.status",
        "badge_b": "e.contract_type",
        "badge_c": "COALESCE(NULLIF(e.team, ''), '')",
        "excerpt": "COALESCE(NULLIF(e.notes, ''), COALESCE(e.email, ''))",
        "search": (
            "LOWER(e.first_name) LIKE :q OR LOWER(e.last_name) LIKE :q"
            " OR LOWER(COALESCE(e.employee_code, '')) LIKE :q"
            " OR LOWER(COALESCE(e.job_title, '')) LIKE :q"
            " OR LOWER(COALESCE(e.team, '')) LIKE :q"
            " OR LOWER(COALESCE(e.email, '')) LIKE :q"
            " OR LOWER(COALESCE(e.phone, '')) LIKE :q"
            " OR LOWER(COALESCE(e.notes, '')) LIKE :q"
        ),
        "date_expr": "COALESCE(e.hired_on, DATE(e.created_at))",
    },
    {
        "key": "competence",
        "label": "Compétences",
        "singular": "Compétence",
        "icon": "badge-check",
        "tone": "humain",
        "href": "/employes",
        "href_label": "Ouvrir la matrice",
        "date_kind": "Créée le",
        "source": "FROM skill s",
        "id_expr": "s.id",
        "title": "s.name",
        "subtitle": "COALESCE(NULLIF(s.category, ''), 'Général')",
        "badge_a": (
            "CASE WHEN s.requires_certification THEN 'Certification requise'"
            " ELSE 'Sans certification' END"
        ),
        "badge_b": "''",
        "badge_c": "''",
        "excerpt": "COALESCE(s.description, '')",
        "search": (
            "LOWER(s.name) LIKE :q OR LOWER(COALESCE(s.category, '')) LIKE :q"
            " OR LOWER(COALESCE(s.description, '')) LIKE :q"
        ),
        "date_expr": "DATE(s.created_at)",
    },
    {
        "key": "habilitation",
        "label": "Habilitations",
        "singular": "Habilitation",
        "icon": "shield-check",
        "tone": "humain",
        "href": "/employes",
        "href_label": "Ouvrir la fiche salarié",
        "date_kind": "Certifiée le",
        "source": (
            "FROM employee_skill es JOIN employee e ON e.id = es.employee_id"
            " JOIN skill s ON s.id = es.skill_id"
        ),
        "id_expr": "es.id",
        "title": "s.name",
        "subtitle": "e.first_name || ' ' || e.last_name",
        "badge_a": "es.level",
        "badge_b": (
            "CAST(ROUND(COALESCE(es.years_experience, 0), 1) AS VARCHAR)"
            " || ' an(s)'"
        ),
        "badge_c": "COALESCE(NULLIF(s.category, ''), '')",
        "excerpt": "COALESCE(NULLIF(es.notes, ''), COALESCE(s.description, ''))",
        "search": (
            "LOWER(s.name) LIKE :q OR LOWER(e.first_name) LIKE :q"
            " OR LOWER(e.last_name) LIKE :q"
            " OR LOWER(COALESCE(s.category, '')) LIKE :q"
            " OR LOWER(COALESCE(es.notes, '')) LIKE :q"
        ),
        "date_expr": "COALESCE(es.certified_on, es.certificate_expiry)",
    },
    {
        "key": "disponibilite",
        "label": "Disponibilités",
        "singular": "Disponibilité",
        "icon": "calendar-range",
        "tone": "humain",
        "href": "/employes",
        "href_label": "Ouvrir le planning",
        "date_kind": "Début",
        "source": (
            "FROM employee_availability av"
            " JOIN employee e ON e.id = av.employee_id"
        ),
        "id_expr": "av.id",
        "title": "e.first_name || ' ' || e.last_name",
        "subtitle": "COALESCE(NULLIF(av.reason, ''), 'Créneau planifié')",
        "badge_a": "av.type",
        "badge_b": (
            "CAST(ROUND(COALESCE(av.hours_per_day, 0), 1) AS VARCHAR) || ' h/j'"
        ),
        "badge_c": "CASE WHEN av.is_all_day THEN 'Journée entière' ELSE '' END",
        "excerpt": "COALESCE(av.notes, '')",
        "search": (
            "LOWER(e.first_name) LIKE :q OR LOWER(e.last_name) LIKE :q"
            " OR LOWER(COALESCE(av.reason, '')) LIKE :q"
            " OR LOWER(COALESCE(av.notes, '')) LIKE :q"
        ),
        "date_expr": "av.start_date",
    },
    {
        "key": "affectation",
        "label": "Affectations",
        "singular": "Affectation",
        "icon": "clipboard-list",
        "tone": "humain",
        "href": "/employes",
        "href_label": "Ouvrir les affectations",
        "date_kind": "Début",
        "source": (
            "FROM assignment a JOIN employee e ON e.id = a.employee_id"
            " LEFT JOIN intervention i ON i.id = a.intervention_id"
            " LEFT JOIN parcel p ON p.id = a.parcel_id"
            " LEFT JOIN equipment eq ON eq.id = a.equipment_id"
        ),
        "id_expr": "a.id",
        "title": "COALESCE(NULLIF(a.title, ''), 'Affectation')",
        "subtitle": "e.first_name || ' ' || e.last_name",
        "badge_a": "a.status",
        "badge_b": "a.role",
        "badge_c": (
            "CAST(ROUND(COALESCE(a.planned_hours, 0), 1) AS VARCHAR)"
            " || ' h prévues'"
        ),
        "excerpt": (
            "COALESCE(NULLIF(a.notes, ''), COALESCE(i.title,"
            " COALESCE(p.name, COALESCE(eq.name, ''))))"
        ),
        "search": (
            "LOWER(COALESCE(a.title, '')) LIKE :q OR LOWER(e.first_name) LIKE :q"
            " OR LOWER(e.last_name) LIKE :q"
            " OR LOWER(COALESCE(i.title, '')) LIKE :q"
            " OR LOWER(COALESCE(p.name, '')) LIKE :q"
            " OR LOWER(COALESCE(eq.name, '')) LIKE :q"
            " OR LOWER(COALESCE(a.notes, '')) LIKE :q"
        ),
        "date_expr": "COALESCE(a.start_date, DATE(a.created_at))",
    },
    {
        "key": "engin",
        "label": "Engins",
        "singular": "Engin",
        "icon": "tractor",
        "tone": "flotte",
        "href": "/maintenance",
        "href_label": "Ouvrir la flotte",
        "date_kind": "Acquis le",
        "source": (
            "FROM equipment e LEFT JOIN employee emp ON emp.id = e.responsible_id"
        ),
        "id_expr": "e.id",
        "title": "COALESCE(NULLIF(e.code, '') || ' · ', '') || e.name",
        "subtitle": (
            "COALESCE(NULLIF(COALESCE(e.brand, '') || ' ' || COALESCE(e.model, ''),"
            " ' '), 'Modèle non précisé')"
        ),
        "badge_a": "e.category",
        "badge_b": "e.status",
        "badge_c": "e.ownership",
        "excerpt": (
            "COALESCE(NULLIF(e.notes, ''), COALESCE(e.storage_location, ''))"
        ),
        "search": (
            "LOWER(e.name) LIKE :q OR LOWER(COALESCE(e.code, '')) LIKE :q"
            " OR LOWER(COALESCE(e.brand, '')) LIKE :q"
            " OR LOWER(COALESCE(e.model, '')) LIKE :q"
            " OR LOWER(COALESCE(e.registration, '')) LIKE :q"
            " OR LOWER(COALESCE(e.serial_number, '')) LIKE :q"
            " OR LOWER(COALESCE(e.storage_location, '')) LIKE :q"
            " OR LOWER(COALESCE(e.notes, '')) LIKE :q"
            " OR LOWER(COALESCE(emp.first_name, '')) LIKE :q"
            " OR LOWER(COALESCE(emp.last_name, '')) LIKE :q"
        ),
        "date_expr": "COALESCE(e.purchase_date, DATE(e.created_at))",
    },
    {
        "key": "plan",
        "label": "Plans d'entretien",
        "singular": "Plan d'entretien",
        "icon": "calendar-clock",
        "tone": "flotte",
        "href": "/maintenance",
        "href_label": "Ouvrir les échéances",
        "date_kind": "Prochaine échéance",
        "source": (
            "FROM maintenance_schedule s"
            " JOIN equipment e ON e.id = s.equipment_id"
        ),
        "id_expr": "s.id",
        "title": "s.title",
        "subtitle": "COALESCE(NULLIF(e.code, '') || ' · ', '') || e.name",
        "badge_a": "s.kind",
        "badge_b": "s.trigger_basis",
        "badge_c": (
            "CAST(ROUND(COALESCE(s.estimated_cost, 0), 0) AS VARCHAR)"
            " || ' € estimés'"
        ),
        "excerpt": "COALESCE(NULLIF(s.notes, ''), COALESCE(s.checklist, ''))",
        "search": (
            "LOWER(s.title) LIKE :q OR LOWER(e.name) LIKE :q"
            " OR LOWER(COALESCE(e.code, '')) LIKE :q"
            " OR LOWER(COALESCE(s.checklist, '')) LIKE :q"
            " OR LOWER(COALESCE(s.notes, '')) LIKE :q"
        ),
        "date_expr": "s.next_due_on",
    },
    {
        "key": "operation",
        "label": "Opérations de maintenance",
        "singular": "Opération",
        "icon": "wrench",
        "tone": "flotte",
        "href": "/maintenance",
        "href_label": "Ouvrir le journal atelier",
        "date_kind": "Échéance",
        "source": (
            "FROM maintenance_operation o"
            " JOIN equipment e ON e.id = o.equipment_id"
        ),
        "id_expr": "o.id",
        "title": "o.title",
        "subtitle": "COALESCE(NULLIF(e.code, '') || ' · ', '') || e.name",
        "badge_a": "o.status",
        "badge_b": "o.kind",
        "badge_c": "o.priority",
        "excerpt": (
            "COALESCE(NULLIF(o.work_performed, ''),"
            " COALESCE(NULLIF(o.failure_description, ''), COALESCE(o.notes, '')))"
        ),
        "search": (
            "LOWER(o.title) LIKE :q OR LOWER(e.name) LIKE :q"
            " OR LOWER(COALESCE(e.code, '')) LIKE :q"
            " OR LOWER(COALESCE(o.provider, '')) LIKE :q"
            " OR LOWER(COALESCE(o.failure_description, '')) LIKE :q"
            " OR LOWER(COALESCE(o.work_performed, '')) LIKE :q"
            " OR LOWER(COALESCE(o.notes, '')) LIKE :q"
        ),
        "date_expr": "COALESCE(o.done_date, COALESCE(o.due_date, o.scheduled_date))",
    },
    {
        "key": "cout",
        "label": "Coûts de maintenance",
        "singular": "Ligne de coût",
        "icon": "coins",
        "tone": "flotte",
        "href": "/maintenance",
        "href_label": "Ouvrir les coûts",
        "date_kind": "Engagée le",
        "source": (
            "FROM maintenance_cost c"
            " JOIN maintenance_operation o ON o.id = c.maintenance_id"
            " JOIN equipment e ON e.id = o.equipment_id"
        ),
        "id_expr": "c.id",
        "title": "COALESCE(NULLIF(c.label, ''), 'Ligne de coût')",
        "subtitle": "o.title",
        "badge_a": "c.type",
        "badge_b": "CAST(ROUND(COALESCE(c.amount, 0), 2) AS VARCHAR) || ' €'",
        "badge_c": "COALESCE(NULLIF(c.supplier, ''), '')",
        "excerpt": (
            "COALESCE(NULLIF(c.notes, ''),"
            " COALESCE(NULLIF(e.code, '') || ' · ', '') || e.name)"
        ),
        "search": (
            "LOWER(COALESCE(c.label, '')) LIKE :q"
            " OR LOWER(COALESCE(c.reference, '')) LIKE :q"
            " OR LOWER(COALESCE(c.supplier, '')) LIKE :q"
            " OR LOWER(o.title) LIKE :q OR LOWER(e.name) LIKE :q"
        ),
        "date_expr": "c.incurred_on",
    },
    {
        "key": "usage",
        "label": "Relevés d'usage",
        "singular": "Relevé d'usage",
        "icon": "gauge",
        "tone": "flotte",
        "href": "/maintenance",
        "href_label": "Ouvrir les relevés",
        "date_kind": "Relevé le",
        "source": (
            "FROM equipment_usage_log u"
            " JOIN equipment e ON e.id = u.equipment_id"
            " LEFT JOIN employee emp ON emp.id = u.employee_id"
        ),
        "id_expr": "u.id",
        "title": "COALESCE(NULLIF(e.code, '') || ' · ', '') || e.name",
        "subtitle": (
            "COALESCE(emp.first_name || ' ' || emp.last_name,"
            " 'Opérateur non précisé')"
        ),
        "badge_a": (
            "CAST(ROUND(COALESCE(u.hours_used, 0), 1) AS VARCHAR) || ' h'"
        ),
        "badge_b": (
            "CAST(ROUND(COALESCE(u.fuel_liters, 0), 0) AS VARCHAR) || ' L'"
        ),
        "badge_c": (
            "CAST(ROUND(COALESCE(u.counter_end, 0), 0) AS VARCHAR)"
            " || ' au compteur'"
        ),
        "excerpt": "COALESCE(u.notes, '')",
        "search": (
            "LOWER(e.name) LIKE :q OR LOWER(COALESCE(e.code, '')) LIKE :q"
            " OR LOWER(COALESCE(emp.first_name, '')) LIKE :q"
            " OR LOWER(COALESCE(emp.last_name, '')) LIKE :q"
            " OR LOWER(COALESCE(u.notes, '')) LIKE :q"
        ),
        "date_expr": "u.used_on",
    },
    {
        "key": "type_depense",
        "label": "Types de dépenses",
        "singular": "Type de dépense",
        "icon": "tags",
        "tone": "operations",
        "href": "/charges",
        "href_label": "Ouvrir le plan de charges",
        "date_kind": "Créé le",
        "source": "FROM expense_type et",
        "id_expr": "et.id",
        "title": "COALESCE(NULLIF(et.code, '') || ' · ', '') || et.name",
        "subtitle": "COALESCE(NULLIF(et.category, ''), 'Sans catégorie')",
        "badge_a": (
            "CASE WHEN et.is_archived THEN 'Archivé'"
            " WHEN et.is_active THEN 'Actif' ELSE 'Désactivé' END"
        ),
        "badge_b": "et.default_payment_method",
        "badge_c": (
            "'TVA ' || CAST(ROUND(COALESCE(et.default_vat_rate, 0), 0) AS VARCHAR)"
            " || ' %'"
        ),
        "excerpt": "COALESCE(NULLIF(et.description, ''), COALESCE(et.notes, ''))",
        "search": (
            "LOWER(et.name) LIKE :q OR LOWER(COALESCE(et.code, '')) LIKE :q"
            " OR LOWER(COALESCE(et.category, '')) LIKE :q"
            " OR LOWER(COALESCE(et.description, '')) LIKE :q"
            " OR LOWER(COALESCE(et.notes, '')) LIKE :q"
        ),
        "date_expr": "DATE(et.created_at)",
    },
    {
        "key": "depense",
        "label": "Dépenses",
        "singular": "Dépense",
        "icon": "receipt-text",
        "tone": "operations",
        "href": "/charges",
        "href_label": "Ouvrir le registre",
        "date_kind": "Engagée le",
        "source": (
            "FROM expense x JOIN expense_type et ON et.id = x.expense_type_id"
            " LEFT JOIN parcel p ON p.id = x.parcel_id"
            " LEFT JOIN crop c ON c.id = x.crop_id"
            " LEFT JOIN employee e ON e.id = x.employee_id"
            " LEFT JOIN equipment eq ON eq.id = x.equipment_id"
        ),
        "id_expr": "x.id",
        "title": "x.label",
        "subtitle": (
            "et.name || COALESCE(' · ' || NULLIF(x.supplier, ''), '')"
        ),
        "badge_a": "x.status",
        "badge_b": (
            "CAST(ROUND(COALESCE(x.amount_ttc, 0), 2) AS VARCHAR) || ' € TTC'"
        ),
        "badge_c": "x.payment_method",
        "excerpt": (
            "COALESCE(NULLIF(x.notes, ''), COALESCE(p.name,"
            " COALESCE(c.name, COALESCE(eq.name,"
            " COALESCE(e.first_name || ' ' || e.last_name, '')))))"
        ),
        "search": (
            "LOWER(x.label) LIKE :q OR LOWER(COALESCE(x.supplier, '')) LIKE :q"
            " OR LOWER(COALESCE(x.reference, '')) LIKE :q"
            " OR LOWER(COALESCE(x.invoice_reference, '')) LIKE :q"
            " OR LOWER(COALESCE(x.notes, '')) LIKE :q"
            " OR LOWER(et.name) LIKE :q OR LOWER(COALESCE(p.name, '')) LIKE :q"
            " OR LOWER(COALESCE(c.name, '')) LIKE :q"
            " OR LOWER(COALESCE(eq.name, '')) LIKE :q"
        ),
        "date_expr": "COALESCE(x.paid_on, COALESCE(x.incurred_on, DATE(x.created_at)))",
    },
    {
        "key": "categorie_referentiel",
        "label": "Catégories du référentiel",
        "singular": "Catégorie de culture",
        "icon": "layers",
        "tone": "vegetal",
        "href": "/referentiel",
        "href_label": "Ouvrir le référentiel",
        "date_kind": "Référencée le",
        "source": "FROM crop_category cat",
        "id_expr": "cat.id",
        "title": "cat.name",
        "subtitle": (
            "COALESCE(NULLIF(cat.tagline, ''), 'Famille cultivée du référentiel')"
        ),
        "badge_a": (
            "CAST((SELECT COUNT(*) FROM crop_culture cu"
            "       WHERE cu.category_id = cat.id) AS VARCHAR) || ' cultures'"
        ),
        "badge_b": (
            "CAST((SELECT COUNT(*) FROM crop_species s"
            "       JOIN crop_culture cu2 ON cu2.id = s.culture_id"
            "       WHERE cu2.category_id = cat.id) AS VARCHAR) || ' espèces'"
        ),
        "badge_c": (
            "CAST((SELECT COUNT(*) FROM crop_catalog_variety v"
            "       JOIN crop_species s2 ON s2.id = v.species_id"
            "       JOIN crop_culture cu3 ON cu3.id = s2.culture_id"
            "       WHERE cu3.category_id = cat.id) AS VARCHAR) || ' variétés'"
        ),
        "excerpt": "COALESCE(cat.description, '')",
        "search": (
            "LOWER(cat.name) LIKE :q OR LOWER(COALESCE(cat.key, '')) LIKE :q"
            " OR LOWER(COALESCE(cat.tagline, '')) LIKE :q"
            " OR LOWER(COALESCE(cat.description, '')) LIKE :q"
        ),
        "date_expr": "DATE(cat.created_at)",
    },
    {
        "key": "culture_referentiel",
        "label": "Cultures du référentiel",
        "singular": "Culture du référentiel",
        "icon": "sprout",
        "tone": "vegetal",
        "href": "/referentiel",
        "href_label": "Ouvrir le référentiel",
        "date_kind": "Référencée le",
        "source": (
            "FROM crop_culture cu"
            " JOIN crop_category cat ON cat.id = cu.category_id"
        ),
        "id_expr": "cu.id",
        "title": "cu.name",
        "subtitle": (
            "cat.name || COALESCE(' · ' || NULLIF(cu.botanical_family, ''), '')"
        ),
        "badge_a": (
            "CASE cu.cycle WHEN 'ANNUELLE' THEN 'Cycle annuel'"
            " WHEN 'BISANNUELLE' THEN 'Cycle bisannuel'"
            " ELSE 'Culture pérenne' END"
        ),
        "badge_b": (
            "CASE cu.water_need WHEN 'FAIBLE' THEN 'Eau faible'"
            " WHEN 'MODEREE' THEN 'Eau modérée'"
            " WHEN 'ELEVEE' THEN 'Eau élevée'"
            " ELSE 'Eau très élevée' END"
        ),
        "badge_c": (
            "CAST((SELECT COUNT(*) FROM crop_catalog_variety v"
            "       JOIN crop_species s ON s.id = v.species_id"
            "       WHERE s.culture_id = cu.id) AS VARCHAR) || ' variétés'"
        ),
        "excerpt": (
            "COALESCE(NULLIF(cu.description, ''), COALESCE(cu.usage, ''))"
        ),
        "search": (
            "LOWER(cu.name) LIKE :q OR LOWER(COALESCE(cu.common_name, '')) LIKE :q"
            " OR LOWER(COALESCE(cu.botanical_family, '')) LIKE :q"
            " OR LOWER(COALESCE(cu.usage, '')) LIKE :q"
            " OR LOWER(COALESCE(cu.description, '')) LIKE :q"
            " OR LOWER(cat.name) LIKE :q"
        ),
        "date_expr": "DATE(cu.created_at)",
    },
    {
        "key": "espece_referentiel",
        "label": "Espèces du référentiel",
        "singular": "Espèce",
        "icon": "leaf",
        "tone": "vegetal",
        "href": "/referentiel",
        "href_label": "Ouvrir le référentiel",
        "date_kind": "Référencée le",
        "source": (
            "FROM crop_species s"
            " JOIN crop_culture cu ON cu.id = s.culture_id"
            " JOIN crop_category cat ON cat.id = cu.category_id"
        ),
        "id_expr": "s.id",
        "title": "s.name",
        "subtitle": (
            "cat.name || ' · ' || cu.name"
            " || COALESCE(' · ' || NULLIF(s.scientific_name, ''), '')"
        ),
        "badge_a": (
            "CAST(COALESCE(s.cycle_days_max, 0) AS VARCHAR) || ' j de cycle'"
        ),
        "badge_b": (
            "CAST(ROUND(COALESCE(s.water_requirement_mm, 0), 0) AS VARCHAR)"
            " || ' mm d''eau'"
        ),
        "badge_c": (
            "'Sel : ' || CASE s.salinity_tolerance"
            " WHEN 'FAIBLE' THEN 'faible' WHEN 'MOYENNE' THEN 'moyenne'"
            " WHEN 'BONNE' THEN 'bonne' ELSE 'excellente' END"
        ),
        "excerpt": (
            "COALESCE(NULLIF(s.notes, ''),"
            " COALESCE(NULLIF(s.main_diseases, ''), COALESCE(s.main_pests, '')))"
        ),
        "search": (
            "LOWER(s.name) LIKE :q"
            " OR LOWER(COALESCE(s.scientific_name, '')) LIKE :q"
            " OR LOWER(COALESCE(s.botanical_family, '')) LIKE :q"
            " OR LOWER(COALESCE(s.main_pests, '')) LIKE :q"
            " OR LOWER(COALESCE(s.main_diseases, '')) LIKE :q"
            " OR LOWER(COALESCE(s.default_density, '')) LIKE :q"
            " OR LOWER(cu.name) LIKE :q OR LOWER(cat.name) LIKE :q"
        ),
        "date_expr": "DATE(s.created_at)",
    },
    {
        "key": "variete_referentiel",
        "label": "Variétés du référentiel",
        "singular": "Variété du référentiel",
        "icon": "flower-2",
        "tone": "vegetal",
        "href": "/referentiel",
        "href_label": "Ouvrir le référentiel",
        "date_kind": "Référencée le",
        "source": (
            "FROM crop_catalog_variety v"
            " JOIN crop_species s ON s.id = v.species_id"
            " JOIN crop_culture cu ON cu.id = s.culture_id"
            " JOIN crop_category cat ON cat.id = cu.category_id"
            " LEFT JOIN crop_variety l ON l.id = v.crop_variety_id"
        ),
        "id_expr": "v.id",
        "title": "v.name || COALESCE(' · ' || NULLIF(v.local_name, ''), '')",
        "subtitle": "cat.name || ' · ' || cu.name || ' · ' || s.name",
        "badge_a": (
            "COALESCE(NULLIF(v.maturity_group, ''), 'Précocité non précisée')"
        ),
        "badge_b": (
            "CAST(ROUND(COALESCE(v.expected_yield_t_ha, 0), 1) AS VARCHAR)"
            " || ' t/ha visés'"
        ),
        "badge_c": (
            "CASE WHEN v.crop_variety_id IS NOT NULL THEN 'Sélectionnable sur un îlot'"
            " ELSE 'Non reliée' END"
        ),
        "excerpt": (
            "COALESCE(NULLIF(v.notes, ''), COALESCE(v.quality_grade, ''))"
        ),
        "search": (
            "LOWER(v.name) LIKE :q OR LOWER(COALESCE(v.local_name, '')) LIKE :q"
            " OR LOWER(COALESCE(v.maturity_group, '')) LIKE :q"
            " OR LOWER(COALESCE(v.quality_grade, '')) LIKE :q"
            " OR LOWER(COALESCE(v.notes, '')) LIKE :q"
            " OR LOWER(s.name) LIKE :q OR LOWER(cu.name) LIKE :q"
            " OR LOWER(cat.name) LIKE :q"
            " OR LOWER(COALESCE(l.name, '')) LIKE :q"
        ),
        "date_expr": "DATE(v.created_at)",
    },
    {
        "key": "utilisateur",
        "label": "Utilisateurs",
        "singular": "Utilisateur",
        "icon": "user-round",
        "tone": "humain",
        "href": "/administration",
        "href_label": "Ouvrir l'administration",
        "date_kind": "Arrivé le",
        "source": (
            "FROM agripro_user u"
            " LEFT JOIN agripro_role r ON r.id = u.role_id"
            " LEFT JOIN agripro_function f ON f.id = u.function_id"
            " LEFT JOIN agripro_team t ON t.id = u.team_id"
        ),
        "id_expr": "u.id",
        "title": "COALESCE(NULLIF(u.matricule, '') || ' · ', '') || u.full_name",
        "subtitle": (
            "COALESCE(NULLIF(f.label, ''), 'Fonction non précisée')"
            " || COALESCE(' · ' || NULLIF(u.sector, ''), '')"
        ),
        "badge_a": "u.status",
        "badge_b": "COALESCE(NULLIF(r.label, ''), '')",
        "badge_c": (
            "CASE WHEN u.mfa_enabled = 1 THEN 'MFA activé' ELSE 'Sans MFA' END"
        ),
        "excerpt": (
            "COALESCE(NULLIF(u.notes, ''), COALESCE(NULLIF(t.name, ''),"
            " COALESCE(u.email, '')))"
        ),
        "search": (
            "LOWER(u.full_name) LIKE :q"
            " OR LOWER(COALESCE(u.matricule, '')) LIKE :q"
            " OR LOWER(COALESCE(u.email, '')) LIKE :q"
            " OR LOWER(COALESCE(u.phone, '')) LIKE :q"
            " OR LOWER(COALESCE(u.sector, '')) LIKE :q"
            " OR LOWER(COALESCE(u.notes, '')) LIKE :q"
            " OR LOWER(COALESCE(f.label, '')) LIKE :q"
            " OR LOWER(COALESCE(r.label, '')) LIKE :q"
            " OR LOWER(COALESCE(t.name, '')) LIKE :q"
        ),
        "date_expr": "COALESCE(u.hired_on, DATE(u.created_at))",
    },
    {
        "key": "role",
        "label": "Rôles applicatifs",
        "singular": "Rôle",
        "icon": "shield-check",
        "tone": "humain",
        "href": "/administration",
        "href_label": "Ouvrir la matrice RBAC",
        "date_kind": "Déclaré le",
        "source": "FROM agripro_role r",
        "id_expr": "r.id",
        "title": "r.label",
        "subtitle": (
            "COALESCE(NULLIF(r.tagline, ''), 'Rôle applicatif AgriPro')"
        ),
        "badge_a": "'Niveau ' || CAST(COALESCE(r.level, 0) AS VARCHAR)",
        "badge_b": (
            "CAST((SELECT COUNT(*) FROM agripro_user_role ur"
            "       WHERE ur.role_id = r.id) AS VARCHAR) || ' titulaire(s)'"
        ),
        "badge_c": (
            "CAST((SELECT COUNT(*) FROM agripro_role_permission rp"
            "       WHERE rp.role_id = r.id AND rp.is_granted = 1) AS VARCHAR)"
            " || ' permission(s)'"
        ),
        "excerpt": "COALESCE(NULLIF(r.description, ''), r.tagline)",
        "search": (
            "LOWER(r.label) LIKE :q OR LOWER(COALESCE(r.key, '')) LIKE :q"
            " OR LOWER(COALESCE(r.tagline, '')) LIKE :q"
            " OR LOWER(COALESCE(r.description, '')) LIKE :q"
        ),
        "date_expr": "DATE(r.created_at)",
    },
    {
        "key": "equipe",
        "label": "Équipes agricoles",
        "singular": "Équipe",
        "icon": "users",
        "tone": "humain",
        "href": "/administration",
        "href_label": "Ouvrir les équipes",
        "date_kind": "Constituée le",
        "source": (
            "FROM agripro_team t LEFT JOIN agripro_user l ON l.id = t.leader_id"
        ),
        "id_expr": "t.id",
        "title": "COALESCE(NULLIF(t.code, '') || ' · ', '') || t.name",
        "subtitle": (
            "COALESCE(l.full_name, 'Responsable à désigner')"
            " || COALESCE(' · ' || NULLIF(t.sector, ''), '')"
        ),
        "badge_a": "t.status",
        "badge_b": (
            "CAST((SELECT COUNT(*) FROM agripro_team_member m"
            "       WHERE m.team_id = t.id) AS VARCHAR) || ' membre(s)'"
        ),
        "badge_c": (
            "CAST((SELECT COUNT(DISTINCT a.parcel_id) FROM agripro_assignment a"
            "       WHERE a.team_id = t.id AND a.parcel_id IS NOT NULL)"
            " AS VARCHAR) || ' parcelle(s)'"
        ),
        "excerpt": (
            "COALESCE(NULLIF(t.notes, ''), COALESCE(NULLIF(t.activity, ''),"
            " COALESCE(t.schedule, '')))"
        ),
        "search": (
            "LOWER(t.name) LIKE :q OR LOWER(COALESCE(t.code, '')) LIKE :q"
            " OR LOWER(COALESCE(t.activity, '')) LIKE :q"
            " OR LOWER(COALESCE(t.sector, '')) LIKE :q"
            " OR LOWER(COALESCE(t.notes, '')) LIKE :q"
            " OR LOWER(COALESCE(l.full_name, '')) LIKE :q"
        ),
        "date_expr": "DATE(t.created_at)",
    },
    {
        "key": "permission",
        "label": "Permissions",
        "singular": "Permission",
        "icon": "key-round",
        "tone": "humain",
        "href": "/administration",
        "href_label": "Ouvrir les permissions",
        "date_kind": "Déclarée le",
        "source": "FROM agripro_permission p",
        "id_expr": "p.id",
        "title": "p.label",
        "subtitle": "p.key || ' · ' || COALESCE(p.module_route, '/')",
        "badge_a": "p.action",
        "badge_b": (
            "CAST((SELECT COUNT(*) FROM agripro_role_permission rp"
            "       WHERE rp.permission_id = p.id AND rp.is_granted = 1)"
            " AS VARCHAR) || ' rôle(s)'"
        ),
        "badge_c": (
            "CASE WHEN p.is_sensitive = 1 THEN 'Action sensible' ELSE '' END"
        ),
        "excerpt": "COALESCE(p.description, '')",
        "search": (
            "LOWER(p.label) LIKE :q OR LOWER(p.key) LIKE :q"
            " OR LOWER(p.module) LIKE :q OR LOWER(p.action) LIKE :q"
            " OR LOWER(COALESCE(p.description, '')) LIKE :q"
        ),
        "date_expr": "DATE(p.created_at)",
    },
    {
        "key": "journal",
        "label": "Journal d'activité",
        "singular": "Évènement",
        "icon": "scroll-text",
        "tone": "alerte",
        "href": "/administration",
        "href_label": "Ouvrir le journal",
        "date_kind": "Consigné le",
        "source": "FROM agripro_activity_log l",
        "id_expr": "l.id",
        "title": ("COALESCE(NULLIF(l.summary, ''), 'Action consignée')"),
        "subtitle": (
            "COALESCE(NULLIF(l.actor_label, ''), 'Système')"
            " || COALESCE(' · ' || NULLIF(l.object_ref, ''), '')"
        ),
        "badge_a": "l.kind",
        "badge_b": "COALESCE(NULLIF(l.action, ''), '')",
        "badge_c": (
            "CASE WHEN l.is_sensitive = 1 THEN 'Audit sécurité' ELSE '' END"
        ),
        "excerpt": (
            "COALESCE(NULLIF(l.scope_label, ''), COALESCE(l.module, ''))"
        ),
        "search": (
            "LOWER(COALESCE(l.summary, '')) LIKE :q"
            " OR LOWER(COALESCE(l.actor_label, '')) LIKE :q"
            " OR LOWER(COALESCE(l.object_ref, '')) LIKE :q"
            " OR LOWER(COALESCE(l.module, '')) LIKE :q"
            " OR LOWER(COALESCE(l.action, '')) LIKE :q"
            " OR LOWER(COALESCE(l.scope_label, '')) LIKE :q"
        ),
        "date_expr": "DATE(COALESCE(l.occurred_at, l.created_at))",
    },
    {
        "key": "remediation",
        "label": "Décisions de remédiation",
        "singular": "Décision",
        "icon": "clipboard-check",
        "tone": "alerte",
        "href": "/audit",
        "href_label": "Ouvrir la remédiation",
        "date_kind": "Décidée le",
        "source": "FROM remediation_log r",
        "id_expr": "r.id",
        "title": "COALESCE(NULLIF(r.target_label, ''), 'Décision')",
        "subtitle": (
            "CASE r.domain"
            " WHEN 'STOCK' THEN 'Intrants & magasin'"
            " WHEN 'CONTOUR' THEN 'Géométrie parcellaire'"
            " ELSE 'Veille agronomique' END"
            " || ' · ' || COALESCE(NULLIF(r.author, ''), 'Exploitation')"
        ),
        "badge_a": "r.domain",
        "badge_b": "r.action",
        "badge_c": "COALESCE(NULLIF(r.module_route, ''), '')",
        "excerpt": "COALESCE(NULLIF(r.note, ''), 'Aucune note consignée.')",
        "search": (
            "LOWER(COALESCE(r.target_label, '')) LIKE :q"
            " OR LOWER(COALESCE(r.note, '')) LIKE :q"
            " OR LOWER(COALESCE(r.author, '')) LIKE :q"
            " OR LOWER(COALESCE(r.action, '')) LIKE :q"
            " OR LOWER(COALESCE(r.domain, '')) LIKE :q"
            " OR LOWER(COALESCE(r.module_route, '')) LIKE :q"
            " OR LOWER(CASE r.domain"
            "      WHEN 'STOCK' THEN 'intrants magasin stock réapprovisionnement'"
            "      WHEN 'CONTOUR' THEN 'contour géométrie parcellaire îlot'"
            "      ELSE 'alerte veille agronomique' END) LIKE :q"
            " OR LOWER(CASE r.action"
            "      WHEN 'COMMANDE' THEN 'commande engagée réapprovisionnement'"
            "      WHEN 'REPORT' THEN 'chantier reporté report'"
            "      WHEN 'SUFFISANT' THEN 'stock jugé suffisant'"
            "      WHEN 'VERIFIE' THEN 'contour vérifié à l''écran'"
            "      WHEN 'A_RELEVER' THEN 'à relever sur le terrain relevé gps'"
            "      WHEN 'TRAITEE' THEN 'alerte traitée clôturée'"
            "      WHEN 'SUIVIE' THEN 'sous surveillance suivie'"
            "      ELSE '' END) LIKE :q"
        ),
        "date_expr": "COALESCE(r.decided_on, DATE(r.created_at))",
    },
]

SPEC_BY_KEY: dict[str, dict[str, str]] = {spec["key"]: spec for spec in SPECS}


class SearchHit(TypedDict):
    key: str
    kind: str
    kind_label: str
    icon: str
    tone: str
    title: str
    subtitle: str
    badges: list[str]
    date_kind: str
    date_label: str
    excerpt: str
    href: str
    href_label: str


class SearchSection(TypedDict):
    kind: str
    label: str
    icon: str
    tone: str
    count: int
    shown: int
    truncated: bool
    href: str
    href_label: str
    date_kind: str
    hits: list[SearchHit]


class TypeChip(TypedDict):
    value: str
    label: str
    icon: str
    tone: str
    count: int


class PeriodChip(TypedDict):
    value: str
    label: str


def _fmt_date(value: object) -> str:
    day = as_date(value)
    if day is None:
        return "—"
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _to_date(raw: str) -> datetime.date | None:
    value = str(raw).strip()
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


def _clean(raw: object) -> str:
    value = str(raw or "").strip()
    while value.startswith("·"):
        value = value[1:].strip()
    while value.endswith("·"):
        value = value[:-1].strip()
    return value


def _badge(raw: object) -> str:
    value = _clean(raw)
    if not value:
        return ""
    return LABELS.get(value, value)


def _excerpt(raw: object) -> str:
    value = _clean(raw)
    if not value:
        return "Aucun détail consigné."
    if len(value) <= EXCERPT_LENGTH:
        return value
    return f"{value[:EXCERPT_LENGTH].rstrip()}…"


def _where(
    spec: dict[str, str], has_query: bool, has_start: bool, has_end: bool
) -> str:
    clauses = ["1=1"]
    if has_query:
        clauses.append(f"({spec['search']})")
    if has_start:
        clauses.append(f"{spec['date_expr']} >= :start")
    if has_end:
        clauses.append(f"{spec['date_expr']} <= :end")
    return " AND ".join(clauses)


class SearchState(rx.State):
    """Console de recherche transversale sur toutes les tables métier."""

    is_loading: bool = True
    has_run: bool = False
    error: str = ""
    today_label: str = ""

    term: str = ""
    start_date: str = ""
    end_date: str = ""
    period: str = "TOUT"
    entity_filter: str = "TOUS"

    sections: list[SearchSection] = []
    chips: list[TypeChip] = []
    total_results: int = 0
    tables_touched: int = 0
    form_key: int = 0

    period_chips: list[PeriodChip] = [
        {"value": key, "label": label} for key, label, _ in PERIODS
    ]

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def section_count(self) -> int:
        return len(self.sections)

    @rx.var
    def query(self) -> str:
        """Alias stable du mot-clé courant (`term`)."""
        return self.term

    @rx.var
    def results(self) -> list[SearchHit]:
        """Liste plate de tous les résultats, toutes sections confondues.

        Inclut les instances du socle utilisateurs / rôles / équipes /
        permissions et les évènements du journal d'activité (sécurité).
        """
        flat: list[SearchHit] = []
        for section in self.sections:
            flat.extend(section["hits"])
        return flat

    @rx.var
    def has_results(self) -> bool:
        return len(self.sections) > 0

    @rx.var
    def has_filters(self) -> bool:
        return bool(
            self.term.strip()
            or self.start_date
            or self.end_date
            or self.entity_filter != "TOUS"
        )

    @rx.var
    def scope_label(self) -> str:
        if self.entity_filter == "TOUS":
            return f"{len(SPECS)} tables métier interrogées"
        spec = SPEC_BY_KEY.get(self.entity_filter)
        return f"Filtré sur : {spec['label']}" if spec else "Périmètre filtré"

    @rx.var
    def range_label(self) -> str:
        start = _to_date(self.start_date)
        end = _to_date(self.end_date)
        if start and end:
            return f"{_fmt_date(start)} → {_fmt_date(end)}"
        if start:
            return f"Depuis le {_fmt_date(start)}"
        if end:
            return f"Jusqu'au {_fmt_date(end)}"
        return "Tout l'historique"

    @rx.var
    def term_label(self) -> str:
        value = self.term.strip()
        if not value:
            return "Aucun mot-clé (balayage complet)"
        return f"« {value} »"

    # ------------------------------------------------------------------
    # Exécution de la recherche
    # ------------------------------------------------------------------

    def _validate(self) -> str:
        if self.start_date and _to_date(self.start_date) is None:
            return "Date de début invalide : utilisez le sélecteur de date."
        if self.end_date and _to_date(self.end_date) is None:
            return "Date de fin invalide : utilisez le sélecteur de date."
        start = _to_date(self.start_date)
        end = _to_date(self.end_date)
        if start and end and end < start:
            return "La date de fin doit suivre la date de début."
        term = self.term.strip()
        if term and len(term) < 2:
            return "Saisissez au moins 2 caractères pour rechercher."
        return ""

    async def _run(self) -> None:
        self.error = self._validate()
        if self.error:
            self.sections = []
            self.total_results = 0
            self.tables_touched = 0
            self.has_run = True
            return

        term = self.term.strip().lower()
        start = _to_date(self.start_date)
        end = _to_date(self.end_date)
        has_query = bool(term)
        params: dict[str, str | datetime.date] = {}
        if has_query:
            params["q"] = f"%{term}%"
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end

        count_sql = " UNION ALL ".join(
            f"SELECT '{spec['key']}' AS kind, COUNT(*) AS total {spec['source']}"
            f" WHERE {_where(spec, has_query, start is not None, end is not None)}"
            for spec in SPECS
        )

        selected = (
            SPECS
            if self.entity_filter == "TOUS"
            else [spec for spec in SPECS if spec["key"] == self.entity_filter]
        )

        async with rx.asession() as asession:
            count_rows = (await asession.execute(text(count_sql), params)).all()
            totals = {str(row[0]): int(row[1] or 0) for row in count_rows}

            sections: list[SearchSection] = []
            for spec in selected:
                total = totals.get(spec["key"], 0)
                if total == 0:
                    continue
                where = _where(
                    spec, has_query, start is not None, end is not None
                )
                rows = (
                    await asession.execute(
                        text(
                            f"""
                            SELECT {spec["id_expr"]}, {spec["title"]},
                                   {spec["subtitle"]}, {spec["badge_a"]},
                                   {spec["badge_b"]}, {spec["badge_c"]},
                                   {spec["date_expr"]}, {spec["excerpt"]}
                            {spec["source"]}
                            WHERE {where}
                            ORDER BY {spec["date_expr"]} DESC NULLS LAST,
                                     {spec["id_expr"]} DESC
                            LIMIT {PER_TYPE_LIMIT}
                            """
                        ),
                        params,
                    )
                ).all()

                hits: list[SearchHit] = []
                for row in rows:
                    badges = [
                        badge
                        for badge in (
                            _badge(row[3]),
                            _badge(row[4]),
                            _badge(row[5]),
                        )
                        if badge
                    ]
                    hits.append(
                        {
                            "key": f"{spec['key']}-{int(row[0])}",
                            "kind": spec["key"],
                            "kind_label": spec["singular"],
                            "icon": spec["icon"],
                            "tone": spec["tone"],
                            "title": _clean(row[1]) or spec["singular"],
                            "subtitle": _clean(row[2]) or "—",
                            "badges": badges,
                            "date_kind": spec["date_kind"],
                            "date_label": _fmt_date(row[6]),
                            "excerpt": _excerpt(row[7]),
                            "href": spec["href"],
                            "href_label": spec["href_label"],
                        }
                    )

                sections.append(
                    {
                        "kind": spec["key"],
                        "label": spec["label"],
                        "icon": spec["icon"],
                        "tone": spec["tone"],
                        "count": total,
                        "shown": len(hits),
                        "truncated": total > len(hits),
                        "href": spec["href"],
                        "href_label": spec["href_label"],
                        "date_kind": spec["date_kind"],
                        "hits": hits,
                    }
                )

        self.sections = sections
        self.chips = [
            {
                "value": "TOUS",
                "label": "Tous les actifs",
                "icon": "layers",
                "tone": "all",
                "count": sum(totals.values()),
            }
        ] + [
            {
                "value": spec["key"],
                "label": spec["label"],
                "icon": spec["icon"],
                "tone": spec["tone"],
                "count": totals.get(spec["key"], 0),
            }
            for spec in SPECS
        ]
        self.total_results = sum(totals.values())
        self.tables_touched = len([t for t in totals.values() if t > 0])
        self.has_run = True

    # ------------------------------------------------------------------
    # Événements
    # ------------------------------------------------------------------

    @rx.event
    async def load_search(self):
        self.is_loading = True
        yield
        await seed_dashboard_data()
        # Référentiel cultures : indispensable pour le retrouver en recherche.
        await seed_catalog_data()
        await link_legacy_varieties()
        await materialize_catalog_varieties()
        await seed_operations_data()
        await seed_employee_data()
        await seed_equipment_data()
        await seed_expense_data()
        # Socle utilisateurs / RBAC : indispensable pour retrouver un compte,
        # un rôle, une équipe, une permission ou un évènement du journal.
        from app.seed_access import seed_access_data

        await seed_access_data()
        await self._run()
        today = datetime.date.today()
        self.today_label = (
            f"{WEEKDAYS_SHORT[today.weekday()]}. {today.day} "
            f"{MONTHS[today.month - 1]} {today.year}"
        )
        self.is_loading = False

    @rx.event
    async def set_term(self, value: str):
        self.term = value
        self.is_loading = True
        yield
        await self._run()
        self.is_loading = False

    @rx.event
    async def set_query(self, value: str):
        """Alias événementiel stable de `set_term`.

        Synchronise le champ de recherche existant (`term`) puis relance le
        balayage global de toutes les tables métier, y compris le socle
        utilisateurs, rôles, équipes, permissions et le journal d'activité.
        """
        self.term = value
        self.is_loading = True
        yield
        await self._run()
        self.is_loading = False

    @rx.event
    async def set_start_date(self, value: str):
        self.start_date = value
        self.period = "PERSO"
        self.is_loading = True
        yield
        await self._run()
        self.is_loading = False

    @rx.event
    async def set_end_date(self, value: str):
        self.end_date = value
        self.period = "PERSO"
        self.is_loading = True
        yield
        await self._run()
        self.is_loading = False

    @rx.event
    async def set_period(self, value: str):
        self.period = value
        today = datetime.date.today()
        days = 0
        for key, _label, span in PERIODS:
            if key == value:
                days = span
        if days > 0:
            self.start_date = (
                today - datetime.timedelta(days=days)
            ).isoformat()
            self.end_date = today.isoformat()
        else:
            self.start_date = ""
            self.end_date = ""
        self.form_key += 1
        self.is_loading = True
        yield
        await self._run()
        self.is_loading = False

    @rx.event
    async def set_entity_filter(self, value: str):
        self.entity_filter = value
        self.is_loading = True
        yield
        await self._run()
        self.is_loading = False

    @rx.event
    async def reset_search(self):
        self.term = ""
        self.start_date = ""
        self.end_date = ""
        self.period = "TOUT"
        self.entity_filter = "TOUS"
        self.error = ""
        self.form_key += 1
        self.is_loading = True
        yield
        await self._run()
        self.is_loading = False

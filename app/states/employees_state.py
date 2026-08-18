"""État de l'espace employés.

Registre humain filtrable, matrice compétences / disponibilités, fiches
détaillées, certifications, disponibilités et affectations.
Toutes les lectures et écritures passent par `rx.asession()` en SQL brut.
"""

from __future__ import annotations

import datetime
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.date_utils import as_date, iso_or_empty
from app.seed import seed_dashboard_data
from app.seed_employees import seed_employee_data
from app.states.dashboard_state import MONTHS, WEEKDAYS_SHORT

EMPLOYEE_STATUS_KEYS: list[str] = [
    "ACTIF",
    "CONGE",
    "ARRET_MALADIE",
    "FORMATION",
    "SORTI",
]

EMPLOYEE_STATUS_LABELS: dict[str, str] = {
    "ACTIF": "Actif",
    "CONGE": "En congé",
    "ARRET_MALADIE": "Arrêt maladie",
    "FORMATION": "En formation",
    "SORTI": "Sorti",
}

EMPLOYEE_STATUS_TONES: dict[str, str] = {
    "ACTIF": "good",
    "CONGE": "warn",
    "ARRET_MALADIE": "bad",
    "FORMATION": "info",
    "SORTI": "muted",
}

CONTRACT_KEYS: list[str] = [
    "CDI",
    "CDD",
    "SAISONNIER",
    "APPRENTI",
    "STAGE",
    "PRESTATAIRE",
]

CONTRACT_LABELS: dict[str, str] = {
    "CDI": "CDI",
    "CDD": "CDD",
    "SAISONNIER": "Saisonnier",
    "APPRENTI": "Apprentissage",
    "STAGE": "Stage",
    "PRESTATAIRE": "Prestataire",
}

LEVEL_KEYS: list[str] = ["DEBUTANT", "INTERMEDIAIRE", "AVANCE", "EXPERT"]

LEVEL_LABELS: dict[str, str] = {
    "DEBUTANT": "Débutant",
    "INTERMEDIAIRE": "Intermédiaire",
    "AVANCE": "Avancé",
    "EXPERT": "Expert",
}

LEVEL_SCORES: dict[str, int] = {
    "DEBUTANT": 1,
    "INTERMEDIAIRE": 2,
    "AVANCE": 3,
    "EXPERT": 4,
}

AVAILABILITY_KEYS: list[str] = [
    "DISPONIBLE",
    "CONGE",
    "ARRET",
    "FORMATION",
    "ASTREINTE",
    "INDISPONIBLE",
]

AVAILABILITY_LABELS: dict[str, str] = {
    "DISPONIBLE": "Disponible",
    "CONGE": "Congé",
    "ARRET": "Arrêt",
    "FORMATION": "Formation",
    "ASTREINTE": "Astreinte",
    "INDISPONIBLE": "Indisponible",
}

AVAILABILITY_TONES: dict[str, str] = {
    "DISPONIBLE": "good",
    "ASTREINTE": "info",
    "FORMATION": "info",
    "CONGE": "warn",
    "ARRET": "bad",
    "INDISPONIBLE": "muted",
}

ROLE_LABELS: dict[str, str] = {
    "RESPONSABLE": "Responsable",
    "CONDUCTEUR": "Conducteur",
    "OPERATEUR": "Opérateur",
    "AIDE": "Aide",
    "OBSERVATEUR": "Observateur",
}

ASSIGNMENT_STATUS_LABELS: dict[str, str] = {
    "PROPOSEE": "Proposée",
    "CONFIRMEE": "Confirmée",
    "EN_COURS": "En cours",
    "TERMINEE": "Terminée",
    "ANNULEE": "Annulée",
}

ASSIGNMENT_STATUS_TONES: dict[str, str] = {
    "PROPOSEE": "info",
    "CONFIRMEE": "good",
    "EN_COURS": "good",
    "TERMINEE": "muted",
    "ANNULEE": "bad",
}


class Option(TypedDict):
    value: str
    label: str


class MatrixCell(TypedDict):
    skill: str
    level: str
    level_label: str
    score: int
    tone: str
    short: str


class MatrixRow(TypedDict):
    id: int
    name: str
    initials: str
    team: str
    availability_label: str
    availability_tone: str
    coverage: int
    coverage_pct: str
    cells: list[MatrixCell]


class EmployeeRow(TypedDict):
    id: int
    name: str
    initials: str
    code: str
    job_title: str
    team: str
    status: str
    status_label: str
    status_tone: str
    contract_label: str
    weekly_hours: float
    hourly_cost: float
    skill_count: int
    top_skill: str
    availability_label: str
    availability_tone: str
    assignments: int
    phyto: bool


class SkillRow(TypedDict):
    id: int
    skill_id: int
    name: str
    category: str
    icon: str
    level: str
    level_label: str
    score: int
    years: float
    certified_label: str
    expiry_label: str
    expiry_tone: str
    requires_certification: bool


class AvailabilityRow(TypedDict):
    id: int
    type: str
    type_label: str
    tone: str
    start_label: str
    end_label: str
    days: int
    hours_per_day: float
    reason: str
    is_current: bool


class AssignmentRow(TypedDict):
    id: int
    title: str
    role_label: str
    status: str
    status_label: str
    tone: str
    start_label: str
    end_label: str
    planned_hours: float
    actual_hours: float
    labor_cost: float
    context: str


EMPTY_EMPLOYEE_DETAIL: dict[str, str] = {
    "id": "0",
    "name": "Aucun employé sélectionné",
    "initials": "—",
    "code": "—",
    "job_title": "—",
    "team": "—",
    "status_label": "—",
    "status_tone": "muted",
    "contract_label": "—",
    "email": "—",
    "phone": "—",
    "hired_label": "—",
    "seniority": "0",
    "contract_end_label": "—",
    "weekly_hours": "0.0",
    "hourly_cost": "0.0",
    "weekly_cost": "0",
    "licence_label": "Sans permis",
    "phyto_label": "Sans Certiphyto",
    "phyto_expiry_label": "—",
    "emergency_contact": "—",
    "notes": "—",
    "skill_count": "0",
    "avg_level": "0.0",
    "assignment_count": "0",
    "planned_hours": "0.0",
}

EMPTY_EMPLOYEE_FORM: dict[str, str] = {
    "first_name": "",
    "last_name": "",
    "employee_code": "",
    "job_title": "",
    "contract_type": "CDI",
    "status": "ACTIF",
    "email": "",
    "phone": "",
    "hired_on": "",
    "contract_end_on": "",
    "weekly_hours": "35",
    "hourly_cost": "0",
    "team": "",
    "has_driving_licence": "0",
    "has_phyto_certificate": "0",
    "phyto_certificate_expiry": "",
    "emergency_contact": "",
    "notes": "",
}


def _fmt_date(value: object) -> str:
    day = as_date(value)
    if day is None:
        return "—"
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _iso(value: object) -> str:
    return iso_or_empty(value)


def _to_float(raw: str | None, default: float = 0.0) -> float:
    if raw is None:
        return default
    value = str(raw).strip().replace(",", ".")
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _to_date(raw: str | None) -> datetime.date | None:
    if raw is None:
        return None
    value = str(raw).strip()
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


def _options(keys: list[str], labels: dict[str, str]) -> list[Option]:
    return [{"value": key, "label": labels.get(key, key)} for key in keys]


def _initials(first: str, last: str) -> str:
    head = first[:1].upper() if first else ""
    tail = last[:1].upper() if last else ""
    return f"{head}{tail}" or "—"


class EmployeesState(rx.State):
    """Registre humain, compétences, disponibilités et affectations."""

    is_loading: bool = True
    today_label: str = ""

    search: str = ""
    status_filter: str = "TOUS"
    team_filter: str = "TOUTES"
    skill_filter: str = "TOUTES"

    kpis: dict[str, float] = {
        "total": 0.0,
        "active": 0.0,
        "absent": 0.0,
        "weekly_hours": 0.0,
        "weekly_cost": 0.0,
        "certified": 0.0,
        "assignments": 0.0,
        "skills": 0.0,
    }

    employees: list[EmployeeRow] = []
    matrix_skills: list[str] = []
    matrix_rows: list[MatrixRow] = []

    selected_employee_id: int = 0
    employee_detail: dict[str, str] = EMPTY_EMPLOYEE_DETAIL
    employee_skills: list[SkillRow] = []
    availabilities: list[AvailabilityRow] = []
    assignments: list[AssignmentRow] = []

    team_options: list[str] = []
    skill_options: list[Option] = []

    status_options: list[Option] = _options(
        EMPLOYEE_STATUS_KEYS, EMPLOYEE_STATUS_LABELS
    )
    contract_options: list[Option] = _options(CONTRACT_KEYS, CONTRACT_LABELS)
    level_options: list[Option] = _options(LEVEL_KEYS, LEVEL_LABELS)
    availability_options: list[Option] = _options(
        AVAILABILITY_KEYS, AVAILABILITY_LABELS
    )

    show_employee_form: bool = False
    employee_form_mode: str = "create"
    editing_employee_id: int = 0
    employee_form: dict[str, str] = EMPTY_EMPLOYEE_FORM

    form_error: str = ""
    skill_error: str = ""
    availability_error: str = ""
    form_key: int = 0

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def employee_count(self) -> int:
        return len(self.employees)

    @rx.var
    def has_selection(self) -> bool:
        return self.selected_employee_id > 0

    @rx.var
    def employee_form_title(self) -> str:
        if self.employee_form_mode == "edit":
            return "Modifier la fiche salarié"
        return "Nouvel employé"

    @rx.var
    def teams_shown(self) -> int:
        return len({e["team"] for e in self.employees})

    @rx.var
    def hours_shown(self) -> float:
        return round(sum(e["weekly_hours"] for e in self.employees), 1)

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    def _filters(self) -> tuple[str, dict[str, str | int]]:
        clauses = ["1=1"]
        params: dict[str, str | int] = {}
        query = self.search.strip().lower()
        if query:
            clauses.append(
                "(LOWER(e.first_name) LIKE :q OR LOWER(e.last_name) LIKE :q"
                " OR LOWER(e.employee_code) LIKE :q OR LOWER(e.job_title) LIKE :q"
                " OR LOWER(e.team) LIKE :q OR LOWER(e.email) LIKE :q)"
            )
            params["q"] = f"%{query}%"
        if self.status_filter != "TOUS":
            clauses.append("e.status = :status")
            params["status"] = self.status_filter
        if self.team_filter != "TOUTES":
            clauses.append("e.team = :team")
            params["team"] = self.team_filter
        if self.skill_filter != "TOUTES":
            clauses.append(
                "EXISTS (SELECT 1 FROM employee_skill es2"
                " WHERE es2.employee_id = e.id AND es2.skill_id = :skill)"
            )
            params["skill"] = int(self.skill_filter)
        return " AND ".join(clauses), params

    async def _fetch_registry(self) -> None:
        today = datetime.date.today()
        where, params = self._filters()
        params_with_date: dict[str, str | int | datetime.date] = dict(params)
        params_with_date["today"] = today

        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT e.id, e.first_name, e.last_name,
                               COALESCE(e.employee_code, ''),
                               COALESCE(e.job_title, ''), COALESCE(e.team, ''),
                               e.status, e.contract_type,
                               COALESCE(e.weekly_hours, 0),
                               COALESCE(e.hourly_cost, 0),
                               e.has_phyto_certificate,
                               (SELECT COUNT(*) FROM employee_skill es
                                  WHERE es.employee_id = e.id),
                               (SELECT s.name FROM employee_skill es
                                  JOIN skill s ON s.id = es.skill_id
                                  WHERE es.employee_id = e.id
                                  ORDER BY CASE es.level
                                      WHEN 'EXPERT' THEN 1
                                      WHEN 'AVANCE' THEN 2
                                      WHEN 'INTERMEDIAIRE' THEN 3
                                      ELSE 4 END, s.name
                                  LIMIT 1),
                               (SELECT COUNT(*) FROM assignment a
                                  WHERE a.employee_id = e.id
                                    AND a.status IN ('PROPOSEE', 'CONFIRMEE', 'EN_COURS')),
                               (SELECT av.type FROM employee_availability av
                                  WHERE av.employee_id = e.id
                                    AND av.start_date <= :today
                                    AND av.end_date >= :today
                                  ORDER BY av.id DESC LIMIT 1)
                        FROM employee e
                        WHERE {where}
                        ORDER BY e.team, e.last_name, e.first_name
                        LIMIT 200
                        """
                    ),
                    params_with_date,
                )
            ).all()

            skill_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT s.id, s.name
                        FROM skill s
                        ORDER BY s.category, s.name
                        LIMIT 10
                        """
                    )
                )
            ).all()

            matrix_rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT e.id, s.name, es.level
                        FROM employee e
                        JOIN employee_skill es ON es.employee_id = e.id
                        JOIN skill s ON s.id = es.skill_id
                        WHERE {where}
                        ORDER BY e.id
                        LIMIT 600
                        """
                    ),
                    params,
                )
            ).all()

        employees: list[EmployeeRow] = []
        for row in rows:
            status = str(row[6])
            contract = str(row[7])
            availability = str(row[14]) if row[14] else ""
            employees.append(
                {
                    "id": int(row[0]),
                    "name": f"{row[1]} {row[2]}",
                    "initials": _initials(row[1], row[2]),
                    "code": str(row[3]) or "—",
                    "job_title": str(row[4]) or "Poste non précisé",
                    "team": str(row[5]) or "Sans équipe",
                    "status": status,
                    "status_label": EMPLOYEE_STATUS_LABELS.get(status, status),
                    "status_tone": EMPLOYEE_STATUS_TONES.get(status, "muted"),
                    "contract_label": CONTRACT_LABELS.get(contract, contract),
                    "weekly_hours": float(row[8] or 0),
                    "hourly_cost": float(row[9] or 0),
                    "skill_count": int(row[11] or 0),
                    "top_skill": str(row[12])
                    if row[12]
                    else "Aucune compétence",
                    "availability_label": AVAILABILITY_LABELS.get(
                        availability, "Non planifié"
                    ),
                    "availability_tone": AVAILABILITY_TONES.get(
                        availability, "muted"
                    ),
                    "assignments": int(row[13] or 0),
                    "phyto": bool(row[10]),
                }
            )
        self.employees = employees

        skill_names = [str(row[1]) for row in skill_rows]
        self.matrix_skills = skill_names

        levels: dict[int, dict[str, str]] = {}
        for row in matrix_rows:
            levels.setdefault(int(row[0]), {})[str(row[1])] = str(row[2])

        matrix: list[MatrixRow] = []
        for employee in employees:
            owned = levels.get(employee["id"], {})
            cells: list[MatrixCell] = []
            for name in skill_names:
                level = owned.get(name, "")
                score = LEVEL_SCORES.get(level, 0)
                cells.append(
                    {
                        "skill": name,
                        "level": level,
                        "level_label": LEVEL_LABELS.get(level, "Non maîtrisé"),
                        "score": score,
                        "tone": level if level else "NONE",
                        "short": {
                            "DEBUTANT": "D",
                            "INTERMEDIAIRE": "I",
                            "AVANCE": "A",
                            "EXPERT": "E",
                        }.get(level, "·"),
                    }
                )
            covered = len([c for c in cells if c["score"] > 0])
            coverage = (
                int(covered / len(skill_names) * 100) if skill_names else 0
            )
            matrix.append(
                {
                    "id": employee["id"],
                    "name": employee["name"],
                    "initials": employee["initials"],
                    "team": employee["team"],
                    "availability_label": employee["availability_label"],
                    "availability_tone": employee["availability_tone"],
                    "coverage": coverage,
                    "coverage_pct": f"{coverage}%",
                    "cells": cells,
                }
            )
        self.matrix_rows = matrix

        ids = [e["id"] for e in employees]
        if self.selected_employee_id not in ids:
            self.selected_employee_id = ids[0] if ids else 0

    async def _fetch_kpis(self) -> None:
        today = datetime.date.today()
        horizon = today + datetime.timedelta(days=7)
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            (SELECT COUNT(*) FROM employee WHERE status <> 'SORTI'),
                            (SELECT COUNT(*) FROM employee WHERE status = 'ACTIF'),
                            (SELECT COUNT(*) FROM employee
                               WHERE status IN ('CONGE', 'ARRET_MALADIE')),
                            (SELECT COALESCE(SUM(weekly_hours), 0) FROM employee
                               WHERE status <> 'SORTI'),
                            (SELECT COALESCE(SUM(weekly_hours * hourly_cost), 0)
                               FROM employee WHERE status <> 'SORTI'),
                            (SELECT COUNT(*) FROM employee
                               WHERE has_phyto_certificate = true),
                            (SELECT COUNT(*) FROM assignment
                               WHERE status IN ('PROPOSEE', 'CONFIRMEE', 'EN_COURS')
                                 AND start_date BETWEEN :today AND :horizon),
                            (SELECT COUNT(*) FROM skill)
                        """
                    ),
                    {"today": today, "horizon": horizon},
                )
            ).first()
        self.kpis = {
            "total": float(row[0] or 0) if row else 0.0,
            "active": float(row[1] or 0) if row else 0.0,
            "absent": float(row[2] or 0) if row else 0.0,
            "weekly_hours": float(row[3] or 0) if row else 0.0,
            "weekly_cost": float(row[4] or 0) if row else 0.0,
            "certified": float(row[5] or 0) if row else 0.0,
            "assignments": float(row[6] or 0) if row else 0.0,
            "skills": float(row[7] or 0) if row else 0.0,
        }

    async def _fetch_detail(self) -> None:
        employee_id = self.selected_employee_id
        if employee_id == 0:
            self.employee_detail = EMPTY_EMPLOYEE_DETAIL
            self.employee_skills = []
            self.availabilities = []
            self.assignments = []
            return

        today = datetime.date.today()
        async with rx.asession() as asession:
            detail = (
                await asession.execute(
                    text(
                        """
                        SELECT e.id, e.first_name, e.last_name,
                               COALESCE(e.employee_code, ''),
                               COALESCE(e.job_title, ''), COALESCE(e.team, ''),
                               e.status, e.contract_type, COALESCE(e.email, ''),
                               COALESCE(e.phone, ''), e.hired_on, e.contract_end_on,
                               COALESCE(e.weekly_hours, 0), COALESCE(e.hourly_cost, 0),
                               e.has_driving_licence, e.has_phyto_certificate,
                               e.phyto_certificate_expiry,
                               COALESCE(e.emergency_contact, ''),
                               COALESCE(e.notes, ''),
                               (SELECT COUNT(*) FROM employee_skill es
                                  WHERE es.employee_id = e.id),
                               (SELECT COUNT(*) FROM assignment a
                                  WHERE a.employee_id = e.id),
                               (SELECT COALESCE(SUM(a.planned_hours), 0) FROM assignment a
                                  WHERE a.employee_id = e.id
                                    AND a.status IN ('PROPOSEE', 'CONFIRMEE', 'EN_COURS'))
                        FROM employee e WHERE e.id = :eid
                        """
                    ),
                    {"eid": employee_id},
                )
            ).first()

            skill_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT es.id, s.id, s.name, COALESCE(s.category, ''),
                               COALESCE(s.icon, 'badge-check'), es.level,
                               COALESCE(es.years_experience, 0), es.certified_on,
                               es.certificate_expiry, s.requires_certification
                        FROM employee_skill es
                        JOIN skill s ON s.id = es.skill_id
                        WHERE es.employee_id = :eid
                        ORDER BY CASE es.level
                            WHEN 'EXPERT' THEN 1 WHEN 'AVANCE' THEN 2
                            WHEN 'INTERMEDIAIRE' THEN 3 ELSE 4 END, s.name
                        LIMIT 40
                        """
                    ),
                    {"eid": employee_id},
                )
            ).all()

            availability_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT id, type, start_date, end_date,
                               COALESCE(hours_per_day, 0), COALESCE(reason, '')
                        FROM employee_availability
                        WHERE employee_id = :eid
                        ORDER BY start_date DESC NULLS LAST, id DESC
                        LIMIT 20
                        """
                    ),
                    {"eid": employee_id},
                )
            ).all()

            assignment_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT a.id, COALESCE(a.title, ''), a.role, a.status,
                               a.start_date, a.end_date,
                               COALESCE(a.planned_hours, 0),
                               COALESCE(a.actual_hours, 0),
                               COALESCE(a.labor_cost, 0),
                               COALESCE(i.title, ''), COALESCE(p.name, ''),
                               COALESCE(eq.name, '')
                        FROM assignment a
                        LEFT JOIN intervention i ON i.id = a.intervention_id
                        LEFT JOIN parcel p ON p.id = a.parcel_id
                        LEFT JOIN equipment eq ON eq.id = a.equipment_id
                        WHERE a.employee_id = :eid
                        ORDER BY a.start_date DESC NULLS LAST, a.id DESC
                        LIMIT 24
                        """
                    ),
                    {"eid": employee_id},
                )
            ).all()

        if detail is None:
            self.employee_detail = EMPTY_EMPLOYEE_DETAIL
            self.employee_skills = []
            self.availabilities = []
            self.assignments = []
            return

        status = str(detail[6])
        contract = str(detail[7])
        hired = as_date(detail[10])
        weekly = float(detail[12] or 0)
        cost = float(detail[13] or 0)
        scores = [LEVEL_SCORES.get(row[5], 0) for row in skill_rows]
        self.employee_detail = {
            "id": str(int(detail[0])),
            "name": f"{detail[1]} {detail[2]}",
            "initials": _initials(detail[1], detail[2]),
            "code": str(detail[3]) or "—",
            "job_title": str(detail[4]) or "Poste non précisé",
            "team": str(detail[5]) or "Sans équipe",
            "status_label": EMPLOYEE_STATUS_LABELS.get(status, status),
            "status_tone": EMPLOYEE_STATUS_TONES.get(status, "muted"),
            "contract_label": CONTRACT_LABELS.get(contract, contract),
            "email": str(detail[8]) or "—",
            "phone": str(detail[9]) or "—",
            "hired_label": _fmt_date(hired),
            "seniority": f"{((today - hired).days / 365):.1f}"
            if hired
            else "0.0",
            "contract_end_label": _fmt_date(detail[11]),
            "weekly_hours": f"{weekly:.1f}",
            "hourly_cost": f"{cost:.2f}",
            "weekly_cost": f"{weekly * cost:.0f}",
            "licence_label": "Permis B" if bool(detail[14]) else "Sans permis",
            "phyto_label": "Certiphyto valide"
            if bool(detail[15])
            else "Sans Certiphyto",
            "phyto_expiry_label": _fmt_date(detail[16]),
            "emergency_contact": str(detail[17]) or "—",
            "notes": str(detail[18]) or "Aucune note.",
            "skill_count": str(int(detail[19] or 0)),
            "avg_level": f"{(sum(scores) / len(scores)):.1f}"
            if scores
            else "0.0",
            "assignment_count": str(int(detail[20] or 0)),
            "planned_hours": f"{float(detail[21] or 0):.1f}",
        }

        skills: list[SkillRow] = []
        for row in skill_rows:
            level = str(row[5])
            expiry = as_date(row[8])
            if expiry is None:
                expiry_label = "Sans échéance"
                expiry_tone = "muted"
            elif expiry < today:
                expiry_label = f"Expiré le {_fmt_date(expiry)}"
                expiry_tone = "bad"
            elif (expiry - today).days <= 90:
                expiry_label = f"Expire le {_fmt_date(expiry)}"
                expiry_tone = "warn"
            else:
                expiry_label = f"Valide jusqu'au {_fmt_date(expiry)}"
                expiry_tone = "good"
            skills.append(
                {
                    "id": int(row[0]),
                    "skill_id": int(row[1]),
                    "name": str(row[2]),
                    "category": str(row[3]) or "Général",
                    "icon": str(row[4]) or "badge-check",
                    "level": level,
                    "level_label": LEVEL_LABELS.get(level, level),
                    "score": LEVEL_SCORES.get(level, 0),
                    "years": float(row[6] or 0),
                    "certified_label": _fmt_date(row[7]),
                    "expiry_label": expiry_label,
                    "expiry_tone": expiry_tone,
                    "requires_certification": bool(row[9]),
                }
            )
        self.employee_skills = skills

        availabilities: list[AvailabilityRow] = []
        for row in availability_rows:
            kind = str(row[1])
            start = as_date(row[2])
            end = as_date(row[3])
            span = (end - start).days + 1 if start and end else 0
            availabilities.append(
                {
                    "id": int(row[0]),
                    "type": kind,
                    "type_label": AVAILABILITY_LABELS.get(kind, kind),
                    "tone": AVAILABILITY_TONES.get(kind, "muted"),
                    "start_label": _fmt_date(start),
                    "end_label": _fmt_date(end),
                    "days": max(span, 0),
                    "hours_per_day": float(row[4] or 0),
                    "reason": str(row[5]) or "—",
                    "is_current": bool(start and end and start <= today <= end),
                }
            )
        self.availabilities = availabilities

        assignments: list[AssignmentRow] = []
        for row in assignment_rows:
            status_key = str(row[3])
            context_parts = [
                str(part) for part in (row[9], row[10], row[11]) if part
            ]
            assignments.append(
                {
                    "id": int(row[0]),
                    "title": str(row[1]) or "Affectation",
                    "role_label": ROLE_LABELS.get(row[2], row[2]),
                    "status": status_key,
                    "status_label": ASSIGNMENT_STATUS_LABELS.get(
                        status_key, status_key
                    ),
                    "tone": ASSIGNMENT_STATUS_TONES.get(status_key, "muted"),
                    "start_label": _fmt_date(row[4]),
                    "end_label": _fmt_date(row[5]),
                    "planned_hours": float(row[6] or 0),
                    "actual_hours": float(row[7] or 0),
                    "labor_cost": float(row[8] or 0),
                    "context": " · ".join(context_parts) or "Chantier interne",
                }
            )
        self.assignments = assignments

    async def _fetch_reference(self) -> None:
        async with rx.asession() as asession:
            team_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT COALESCE(team, '') FROM employee
                        GROUP BY COALESCE(team, '') ORDER BY 1
                        """
                    )
                )
            ).all()
            skill_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT id, name, COALESCE(category, '')
                        FROM skill ORDER BY category, name LIMIT 60
                        """
                    )
                )
            ).all()
        self.team_options = [str(row[0]) for row in team_rows if row[0]]
        self.skill_options = [
            {"value": str(int(row[0])), "label": f"{row[2]} · {row[1]}"}
            for row in skill_rows
        ]

    @rx.event
    async def load_workforce(self):
        self.is_loading = True
        yield
        await seed_dashboard_data()
        await seed_employee_data()
        await self._fetch_reference()
        await self._fetch_kpis()
        await self._fetch_registry()
        await self._fetch_detail()
        today = datetime.date.today()
        self.today_label = (
            f"{WEEKDAYS_SHORT[today.weekday()]}. {today.day} "
            f"{MONTHS[today.month - 1]} {today.year}"
        )
        self.is_loading = False

    # ------------------------------------------------------------------
    # Filtres & sélection
    # ------------------------------------------------------------------

    @rx.event
    async def set_search(self, value: str):
        self.search = value
        await self._fetch_registry()
        await self._fetch_detail()

    @rx.event
    async def set_status_filter(self, value: str):
        self.status_filter = value
        await self._fetch_registry()
        await self._fetch_detail()

    @rx.event
    async def set_team_filter(self, value: str):
        self.team_filter = value
        await self._fetch_registry()
        await self._fetch_detail()

    @rx.event
    async def set_skill_filter(self, value: str):
        self.skill_filter = value
        await self._fetch_registry()
        await self._fetch_detail()

    @rx.event
    async def reset_filters(self):
        self.search = ""
        self.status_filter = "TOUS"
        self.team_filter = "TOUTES"
        self.skill_filter = "TOUTES"
        self.form_key += 1
        await self._fetch_registry()
        await self._fetch_detail()

    @rx.event
    async def select_employee(self, employee_id: int):
        self.selected_employee_id = employee_id
        self.skill_error = ""
        self.availability_error = ""
        await self._fetch_detail()

    # ------------------------------------------------------------------
    # Formulaire employé
    # ------------------------------------------------------------------

    @rx.event
    def open_employee_create(self):
        self.employee_form = dict(EMPTY_EMPLOYEE_FORM)
        self.employee_form_mode = "create"
        self.editing_employee_id = 0
        self.form_error = ""
        self.form_key += 1
        self.show_employee_form = True

    @rx.event
    async def open_employee_edit(self):
        if self.selected_employee_id == 0:
            return rx.toast("Sélectionnez d'abord un employé.")
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT first_name, last_name, COALESCE(employee_code, ''),
                               COALESCE(job_title, ''), contract_type, status,
                               COALESCE(email, ''), COALESCE(phone, ''),
                               hired_on, contract_end_on,
                               COALESCE(weekly_hours, 0), COALESCE(hourly_cost, 0),
                               COALESCE(team, ''), has_driving_licence,
                               has_phyto_certificate, phyto_certificate_expiry,
                               COALESCE(emergency_contact, ''), COALESCE(notes, '')
                        FROM employee WHERE id = :eid
                        """
                    ),
                    {"eid": self.selected_employee_id},
                )
            ).first()
        if row is None:
            return rx.toast("Employé introuvable.")
        self.employee_form = {
            "first_name": str(row[0]),
            "last_name": str(row[1]),
            "employee_code": str(row[2]),
            "job_title": str(row[3]),
            "contract_type": str(row[4]),
            "status": str(row[5]),
            "email": str(row[6]),
            "phone": str(row[7]),
            "hired_on": _iso(row[8]),
            "contract_end_on": _iso(row[9]),
            "weekly_hours": f"{float(row[10]):.1f}",
            "hourly_cost": f"{float(row[11]):.2f}",
            "team": str(row[12]),
            "has_driving_licence": "1" if bool(row[13]) else "0",
            "has_phyto_certificate": "1" if bool(row[14]) else "0",
            "phyto_certificate_expiry": _iso(row[15]),
            "emergency_contact": str(row[16]),
            "notes": str(row[17]),
        }
        self.employee_form_mode = "edit"
        self.editing_employee_id = self.selected_employee_id
        self.form_error = ""
        self.form_key += 1
        self.show_employee_form = True

    @rx.event
    def close_employee_form(self):
        self.show_employee_form = False
        self.form_error = ""

    def _validate_employee(self, data: dict) -> str:
        first = str(data.get("first_name", "")).strip()
        last = str(data.get("last_name", "")).strip()
        code = str(data.get("employee_code", "")).strip()
        email = str(data.get("email", "")).strip()
        hours = _to_float(data.get("weekly_hours"), -1.0)
        cost = _to_float(data.get("hourly_cost"), -1.0)
        hired = _to_date(data.get("hired_on"))
        end = _to_date(data.get("contract_end_on"))
        if len(first) < 2:
            return "Le prénom doit contenir au moins 2 caractères."
        if len(last) < 2:
            return "Le nom doit contenir au moins 2 caractères."
        if not code:
            return "Le matricule est obligatoire (ex. E08)."
        if email and "@" not in email:
            return "L'adresse e-mail saisie est invalide."
        if hours <= 0 or hours > 60:
            return (
                "Les heures hebdomadaires doivent être comprises entre 1 et 60."
            )
        if cost < 0:
            return "Le coût horaire ne peut pas être négatif."
        if hired and end and end < hired:
            return "La fin de contrat doit suivre la date d'embauche."
        return ""

    @rx.event
    async def submit_employee(self, form_data: dict):
        error = self._validate_employee(form_data)
        if error:
            self.form_error = error
            return
        params: dict[str, str | float | bool | datetime.date | None | int] = {
            "first_name": str(form_data.get("first_name", "")).strip(),
            "last_name": str(form_data.get("last_name", "")).strip(),
            "employee_code": str(form_data.get("employee_code", ""))
            .strip()
            .upper(),
            "job_title": str(form_data.get("job_title", "")).strip(),
            "contract_type": str(form_data.get("contract_type", "CDI")),
            "status": str(form_data.get("status", "ACTIF")),
            "email": str(form_data.get("email", "")).strip(),
            "phone": str(form_data.get("phone", "")).strip(),
            "hired_on": _to_date(form_data.get("hired_on")),
            "contract_end_on": _to_date(form_data.get("contract_end_on")),
            "weekly_hours": _to_float(form_data.get("weekly_hours"), 35.0),
            "hourly_cost": _to_float(form_data.get("hourly_cost")),
            "team": str(form_data.get("team", "")).strip(),
            "has_driving_licence": bool(form_data.get("has_driving_licence")),
            "has_phyto_certificate": bool(
                form_data.get("has_phyto_certificate")
            ),
            "phyto_certificate_expiry": _to_date(
                form_data.get("phyto_certificate_expiry")
            ),
            "emergency_contact": str(
                form_data.get("emergency_contact", "")
            ).strip(),
            "notes": str(form_data.get("notes", "")).strip(),
        }

        async with rx.asession() as asession:
            if (
                self.employee_form_mode == "edit"
                and self.editing_employee_id > 0
            ):
                params["eid"] = self.editing_employee_id
                await asession.execute(
                    text(
                        """
                        UPDATE employee SET
                            first_name = :first_name, last_name = :last_name,
                            employee_code = :employee_code, job_title = :job_title,
                            contract_type = :contract_type, status = :status,
                            email = :email, phone = :phone, hired_on = :hired_on,
                            contract_end_on = :contract_end_on,
                            weekly_hours = :weekly_hours, hourly_cost = :hourly_cost,
                            team = :team,
                            has_driving_licence = :has_driving_licence,
                            has_phyto_certificate = :has_phyto_certificate,
                            phyto_certificate_expiry = :phyto_certificate_expiry,
                            emergency_contact = :emergency_contact, notes = :notes
                        WHERE id = :eid
                        """
                    ),
                    params,
                )
                new_id = self.editing_employee_id
                message = "Fiche salarié mise à jour."
            else:
                new_id = int(
                    (
                        await asession.execute(
                            text(
                                """
                                INSERT INTO employee (
                                    first_name, last_name, employee_code, job_title,
                                    contract_type, status, email, phone, hired_on,
                                    contract_end_on, weekly_hours, hourly_cost, team,
                                    has_driving_licence, has_phyto_certificate,
                                    phyto_certificate_expiry, emergency_contact, notes
                                ) VALUES (
                                    :first_name, :last_name, :employee_code, :job_title,
                                    :contract_type, :status, :email, :phone, :hired_on,
                                    :contract_end_on, :weekly_hours, :hourly_cost, :team,
                                    :has_driving_licence, :has_phyto_certificate,
                                    :phyto_certificate_expiry, :emergency_contact, :notes
                                ) RETURNING id
                                """
                            ),
                            params,
                        )
                    ).scalar()
                    or 0
                )
                message = "Employé créé."
            await asession.commit()

        self.show_employee_form = False
        self.form_error = ""
        self.form_key += 1
        self.selected_employee_id = new_id
        await self._fetch_reference()
        await self._fetch_kpis()
        await self._fetch_registry()
        await self._fetch_detail()
        return rx.toast(message, duration=4000)

    # ------------------------------------------------------------------
    # Compétences
    # ------------------------------------------------------------------

    @rx.event
    async def submit_skill(self, form_data: dict):
        self.skill_error = ""
        if self.selected_employee_id == 0:
            self.skill_error = "Sélectionnez un employé."
            return
        skill_raw = str(form_data.get("skill_id", "")).strip()
        if not skill_raw:
            self.skill_error = "Choisissez une compétence du référentiel."
            return
        years = _to_float(form_data.get("years_experience"), -1.0)
        if years < 0 or years > 60:
            self.skill_error = (
                "L'expérience doit être comprise entre 0 et 60 ans."
            )
            return
        certified = _to_date(form_data.get("certified_on"))
        expiry = _to_date(form_data.get("certificate_expiry"))
        if certified and expiry and expiry < certified:
            self.skill_error = (
                "L'échéance de certification doit suivre la date d'obtention."
            )
            return
        params: dict[str, str | float | int | datetime.date | None] = {
            "employee_id": self.selected_employee_id,
            "skill_id": int(skill_raw),
            "level": str(form_data.get("level", "INTERMEDIAIRE")),
            "years_experience": years,
            "certified_on": certified,
            "certificate_expiry": expiry,
            "notes": str(form_data.get("notes", "")).strip(),
        }

        async with rx.asession() as asession:
            existing = (
                await asession.execute(
                    text(
                        """
                        SELECT id FROM employee_skill
                        WHERE employee_id = :employee_id AND skill_id = :skill_id
                        """
                    ),
                    {
                        "employee_id": params["employee_id"],
                        "skill_id": params["skill_id"],
                    },
                )
            ).first()
            if existing is None:
                await asession.execute(
                    text(
                        """
                        INSERT INTO employee_skill (
                            employee_id, skill_id, level, years_experience,
                            certified_on, certificate_expiry, notes
                        ) VALUES (
                            :employee_id, :skill_id, :level, :years_experience,
                            :certified_on, :certificate_expiry, :notes
                        )
                        """
                    ),
                    params,
                )
                message = "Compétence ajoutée."
            else:
                params["esid"] = int(existing[0])
                await asession.execute(
                    text(
                        """
                        UPDATE employee_skill SET
                            level = :level, years_experience = :years_experience,
                            certified_on = :certified_on,
                            certificate_expiry = :certificate_expiry,
                            notes = :notes
                        WHERE id = :esid
                        """
                    ),
                    params,
                )
                message = "Niveau de compétence mis à jour."
            await asession.commit()

        self.form_key += 1
        await self._fetch_registry()
        await self._fetch_detail()
        return rx.toast(message, duration=4000)

    @rx.event
    async def remove_skill(self, employee_skill_id: int):
        async with rx.asession() as asession:
            await asession.execute(
                text("DELETE FROM employee_skill WHERE id = :esid"),
                {"esid": employee_skill_id},
            )
            await asession.commit()
        await self._fetch_registry()
        await self._fetch_detail()
        return rx.toast("Compétence retirée.", duration=3000)

    # ------------------------------------------------------------------
    # Disponibilités
    # ------------------------------------------------------------------

    @rx.event
    async def submit_availability(self, form_data: dict):
        self.availability_error = ""
        if self.selected_employee_id == 0:
            self.availability_error = "Sélectionnez un employé."
            return
        start = _to_date(form_data.get("start_date"))
        end = _to_date(form_data.get("end_date"))
        hours = _to_float(form_data.get("hours_per_day"), -1.0)
        if start is None:
            self.availability_error = "La date de début est obligatoire."
            return
        if end is None:
            self.availability_error = "La date de fin est obligatoire."
            return
        if end < start:
            self.availability_error = (
                "La date de fin doit suivre la date de début."
            )
            return
        if hours < 0 or hours > 14:
            self.availability_error = (
                "Les heures par jour doivent être comprises entre 0 et 14."
            )
            return

        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    INSERT INTO employee_availability (
                        employee_id, type, start_date, end_date, hours_per_day,
                        is_all_day, reason, notes
                    ) VALUES (
                        :employee_id, :type, :start_date, :end_date, :hours_per_day,
                        true, :reason, ''
                    )
                    """
                ),
                {
                    "employee_id": self.selected_employee_id,
                    "type": str(form_data.get("type", "DISPONIBLE")),
                    "start_date": start,
                    "end_date": end,
                    "hours_per_day": hours,
                    "reason": str(form_data.get("reason", "")).strip(),
                },
            )
            await asession.commit()

        self.form_key += 1
        await self._fetch_registry()
        await self._fetch_detail()
        return rx.toast("Créneau de disponibilité enregistré.", duration=4000)

    @rx.event
    async def remove_availability(self, availability_id: int):
        async with rx.asession() as asession:
            await asession.execute(
                text("DELETE FROM employee_availability WHERE id = :aid"),
                {"aid": availability_id},
            )
            await asession.commit()
        await self._fetch_registry()
        await self._fetch_detail()
        return rx.toast("Créneau supprimé.", duration=3000)

    # ------------------------------------------------------------------
    # Affectations
    # ------------------------------------------------------------------

    @rx.event
    async def confirm_assignment(self, assignment_id: int):
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    "UPDATE assignment SET status = 'CONFIRMEE' WHERE id = :aid"
                ),
                {"aid": assignment_id},
            )
            await asession.commit()
        await self._fetch_kpis()
        await self._fetch_detail()
        return rx.toast("Affectation confirmée.", duration=3000)

    @rx.event
    async def complete_assignment(self, assignment_id: int):
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    """
                    UPDATE assignment
                    SET status = 'TERMINEE',
                        actual_hours = CASE WHEN COALESCE(actual_hours, 0) > 0
                            THEN actual_hours ELSE COALESCE(planned_hours, 0) END
                    WHERE id = :aid
                    """
                ),
                {"aid": assignment_id},
            )
            await asession.commit()
        await self._fetch_kpis()
        await self._fetch_registry()
        await self._fetch_detail()
        return rx.toast("Affectation clôturée.", duration=3000)

    @rx.event
    async def cancel_assignment(self, assignment_id: int):
        async with rx.asession() as asession:
            await asession.execute(
                text(
                    "UPDATE assignment SET status = 'ANNULEE' WHERE id = :aid"
                ),
                {"aid": assignment_id},
            )
            await asession.commit()
        await self._fetch_kpis()
        await self._fetch_registry()
        await self._fetch_detail()
        return rx.toast("Affectation annulée.", duration=3000)

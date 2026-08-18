"""État du sous-module « contrôle des contours parcellaires ».

Ce module ne crée aucune table : il lit la géométrie déjà persistée sur
`parcel` (contour GeoJSON, surface calculée, sommets, origine) et le journal
local `remediation_log` (domaine `CONTOUR`) créé par l'initialisation SQLite
existante. Tout passe par `rx.asession()` en SQL brut.

Il transforme les contours générés en workflow exploitable :

* un statut de contrôle lisible par îlot (conforme, à vérifier, écart de
  surface, sans contour) ;
* un état de validation (non contrôlé, vérifié à l'écran, à relever) ;
* une recommandation graduée selon l'écart entre surface déclarée et surface
  du contour ;
* deux décisions traçables et idempotentes (vérifier / relever) ;
* l'historique complet des décisions de contour, réutilisable par le
  diagnostic.
"""

from __future__ import annotations

import datetime
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.database import ensure_local_database, ensure_remediation_log_table
from app.geometry import geometry_columns_ready, seed_parcel_geometry
from app.seed import seed_dashboard_data
from app.states.dashboard_state import MONTHS, WEEKDAYS_SHORT

DOMAIN_CONTOUR: str = "CONTOUR"
DEFAULT_AUTHOR: str = "Responsable d'exploitation"

# Tolérance métier : au-delà, l'écart de surface doit être arbitré.
GAP_TOLERANCE: float = 5.0
GAP_MAJOR: float = 15.0

CONTROL_CONFORME: str = "CONFORME"
CONTROL_A_VERIFIER: str = "A_VERIFIER"
CONTROL_ECART: str = "ECART"
CONTROL_SANS: str = "SANS_CONTOUR"

CONTROL_ORDER: list[str] = [
    CONTROL_ECART,
    CONTROL_SANS,
    CONTROL_A_VERIFIER,
    CONTROL_CONFORME,
]

CONTROL_LABELS: dict[str, str] = {
    CONTROL_CONFORME: "Contour conforme",
    CONTROL_A_VERIFIER: "Contour à vérifier",
    CONTROL_ECART: "Écart de surface",
    CONTROL_SANS: "Sans contour tracé",
}

CONTROL_TONES: dict[str, str] = {
    CONTROL_CONFORME: "good",
    CONTROL_A_VERIFIER: "warn",
    CONTROL_ECART: "bad",
    CONTROL_SANS: "muted",
}

CONTROL_ICONS: dict[str, str] = {
    CONTROL_CONFORME: "circle-check",
    CONTROL_A_VERIFIER: "scan-eye",
    CONTROL_ECART: "octagon-alert",
    CONTROL_SANS: "circle-slash",
}

CONTROL_WEIGHT: dict[str, int] = {
    key: index for index, key in enumerate(CONTROL_ORDER)
}

VALIDATION_VERIFIE: str = "VERIFIE"
VALIDATION_A_RELEVER: str = "A_RELEVER"
VALIDATION_NONE: str = "NON_CONTROLE"

VALIDATION_LABELS: dict[str, str] = {
    VALIDATION_VERIFIE: "Vérifié à l'écran",
    VALIDATION_A_RELEVER: "À relever sur le terrain",
    VALIDATION_NONE: "Non contrôlé",
}

VALIDATION_TONES: dict[str, str] = {
    VALIDATION_VERIFIE: "good",
    VALIDATION_A_RELEVER: "warn",
    VALIDATION_NONE: "muted",
}

VALIDATION_ICONS: dict[str, str] = {
    VALIDATION_VERIFIE: "scan-eye",
    VALIDATION_A_RELEVER: "map-pin",
    VALIDATION_NONE: "circle-dashed",
}

SOURCE_LABELS: dict[str, str] = {
    "AUCUNE": "Aucun contour",
    "GENEREE": "Contour généré",
    "DESSINEE": "Contour dessiné",
    "IMPORTEE": "Contour importé",
    "CADASTRE": "Contour cadastral",
}


class Option(TypedDict):
    value: str
    label: str


class ContourRow(TypedDict):
    """Ligne de contrôle de contour pour un îlot."""

    id: int
    code: str
    name: str
    locality: str
    declared_area: float
    computed_area: float
    gap_ha: float
    gap_pct: float
    gap_label: str
    gap_bar_pct: str
    vertex_count: int
    has_geometry: bool
    source: str
    source_label: str
    control: str
    control_label: str
    control_tone: str
    control_icon: str
    validation: str
    validation_label: str
    validation_tone: str
    validation_icon: str
    decision: str
    recommendation: str
    decision_count: int
    last_note: str
    last_author: str
    last_decided_label: str
    updated_label: str
    updated_by: str
    geometry_notes: str


class ContourLog(TypedDict):
    """Décision de contour consignée au journal de remédiation."""

    id: int
    parcel_id: int
    label: str
    action: str
    action_label: str
    tone: str
    icon: str
    note: str
    author: str
    date_label: str


class ControlDistribution(TypedDict):
    key: str
    label: str
    value: int
    share_pct: str
    tone: str
    icon: str


def _fmt_date(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime.datetime):
        value = value.date()
    if isinstance(value, datetime.date):
        return f"{value.day} {MONTHS[value.month - 1]} {value.year}"
    raw = str(value)[:10]
    try:
        parsed = datetime.date.fromisoformat(raw)
    except ValueError:
        return "—"
    return f"{parsed.day} {MONTHS[parsed.month - 1]} {parsed.year}"


def _recommendation(
    control: str, gap_pct: float, gap_ha: float, validation: str
) -> str:
    if control == CONTROL_SANS:
        return (
            "Tracer ou importer le contour depuis l'éditeur GeoJSON de la "
            "cartographie : sans polygone, aucune surface ne peut être "
            "contrôlée face à la déclaration."
        )
    if control == CONTROL_ECART:
        if gap_pct >= GAP_MAJOR:
            return (
                f"Écart majeur de {gap_pct:.1f} % ({gap_ha:.2f} ha) : un relevé "
                "GPS ou un import cadastral est indispensable avant de "
                "réutiliser cette surface dans une dose ou une marge."
            )
        return (
            f"Écart de {gap_pct:.1f} % ({gap_ha:.2f} ha) : arbitrer entre "
            "surface déclarée obsolète et contour incomplet, puis programmer "
            "un relevé de terrain."
        )
    if control == CONTROL_A_VERIFIER:
        return (
            "Contour généré à partir du point et de la surface déclarée : le "
            "confronter au parcellaire réel à l'écran, puis le marquer vérifié "
            "ou à relever."
        )
    if validation == VALIDATION_NONE:
        return (
            "Contour cohérent avec la surface déclarée : une vérification à "
            "l'écran suffit à clore le contrôle."
        )
    return (
        "Contour contrôlé et cohérent : revalider uniquement après une "
        "modification de tracé ou de surface déclarée."
    )


class ContourState(rx.State):
    """Contrôle et validation des contours parcellaires."""

    is_loading: bool = True
    today_label: str = ""
    geometry_ready: bool = True

    notice: str = ""
    error: str = ""

    note_draft: str = ""
    author_draft: str = DEFAULT_AUTHOR

    search: str = ""
    control_filter: str = "TOUS"
    validation_filter: str = "TOUS"

    # Îlot ciblé par le poste de contrôle (0 = aucun).
    selected_id: int = 0

    rows: list[ContourRow] = []
    logs: list[ContourLog] = []

    kpis: dict[str, float] = {
        "parcels": 0.0,
        "conforme": 0.0,
        "a_verifier": 0.0,
        "ecart": 0.0,
        "sans_contour": 0.0,
        "verifie": 0.0,
        "a_relever": 0.0,
        "non_controle": 0.0,
        "gap_area": 0.0,
        "gap_max": 0.0,
        "mapped_area": 0.0,
        "decisions": 0.0,
    }

    control_options: list[Option] = [
        {"value": key, "label": CONTROL_LABELS[key]} for key in CONTROL_ORDER
    ]
    validation_options: list[Option] = [
        {"value": VALIDATION_NONE, "label": VALIDATION_LABELS[VALIDATION_NONE]},
        {
            "value": VALIDATION_VERIFIE,
            "label": VALIDATION_LABELS[VALIDATION_VERIFIE],
        },
        {
            "value": VALIDATION_A_RELEVER,
            "label": VALIDATION_LABELS[VALIDATION_A_RELEVER],
        },
    ]

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def visible_rows(self) -> list[ContourRow]:
        rows = self.rows
        if self.control_filter != "TOUS":
            rows = [
                item for item in rows if item["control"] == self.control_filter
            ]
        if self.validation_filter != "TOUS":
            rows = [
                item
                for item in rows
                if item["validation"] == self.validation_filter
            ]
        return rows

    @rx.var
    def visible_count(self) -> int:
        return len(self.visible_rows)

    @rx.var
    def has_rows(self) -> bool:
        return len(self.visible_rows) > 0

    @rx.var
    def items(self) -> list[ContourRow]:
        """Alias stable des lignes affichées (UI et tests)."""
        return self.visible_rows

    @rx.var
    def has_items(self) -> bool:
        """Vrai si au moins un îlot est affiché dans le périmètre courant."""
        return len(self.visible_rows) > 0

    @rx.var
    def item_count(self) -> int:
        return len(self.visible_rows)

    @rx.var
    def has_selection(self) -> bool:
        return self.selected_id > 0

    @rx.var
    def selected_label(self) -> str:
        for item in self.rows:
            if item["id"] == self.selected_id:
                return f"{item['code']} · {item['name']}"
        return "Aucun îlot ciblé"

    @rx.var
    def has_logs(self) -> bool:
        return len(self.logs) > 0

    @rx.var
    def open_total(self) -> int:
        """Îlots dont le contrôle de contour reste à traiter."""
        return len(
            [
                item
                for item in self.rows
                if item["control"] != CONTROL_CONFORME
                and item["validation"] == VALIDATION_NONE
            ]
        )

    @rx.var
    def control_rate(self) -> float:
        total = len(self.rows)
        if total == 0:
            return 0.0
        controlled = len(
            [
                item
                for item in self.rows
                if item["validation"] != VALIDATION_NONE
            ]
        )
        return round(100.0 * controlled / total, 1)

    @rx.var
    def control_rate_pct(self) -> str:
        return f"{self.control_rate:.0f}%"

    @rx.var
    def verdict_label(self) -> str:
        if len(self.rows) == 0:
            return "Aucun îlot à contrôler"
        if self.kpis["ecart"] > 0:
            return "Écarts de surface à arbitrer"
        if self.kpis["sans_contour"] > 0:
            return "Contours manquants à tracer"
        if self.open_total > 0:
            return "Contours générés à vérifier"
        return "Contrôle des contours à jour"

    @rx.var
    def verdict_tone(self) -> str:
        if self.kpis["ecart"] > 0:
            return "bad"
        if self.kpis["sans_contour"] > 0 or self.open_total > 0:
            return "warn"
        return "good"

    @rx.var
    def verdict_detail(self) -> str:
        return (
            f"{self.open_total} îlot(s) en attente de décision sur "
            f"{len(self.rows)} audité(s) · {self.kpis['ecart']:.0f} écart(s) "
            f"au-delà de {GAP_TOLERANCE:.0f} % · "
            f"{self.kpis['decisions']:.0f} décision(s) consignée(s)."
        )

    @rx.var
    def summary(self) -> dict[str, float]:
        """Résumé stable du contrôle des contours (UI, audit et tests)."""
        return {
            "total": self.kpis["parcels"],
            "generated": self.kpis["a_verifier"],
            "verified": self.kpis["verifie"],
            "to_survey": self.kpis["a_relever"],
            "decisions": self.kpis["decisions"],
            "conforme": self.kpis["conforme"],
            "ecart": self.kpis["ecart"],
            "sans_contour": self.kpis["sans_contour"],
            "non_controle": self.kpis["non_controle"],
            "gap_area": self.kpis["gap_area"],
            "gap_max": self.kpis["gap_max"],
            "mapped_area": self.kpis["mapped_area"],
            "open_total": float(self.open_total),
            "control_rate": self.control_rate,
            "visible": float(len(self.visible_rows)),
        }

    @rx.var
    def control_distribution(self) -> list[ControlDistribution]:
        total = max(1, len(self.rows))
        keys = {
            CONTROL_ECART: "ecart",
            CONTROL_SANS: "sans_contour",
            CONTROL_A_VERIFIER: "a_verifier",
            CONTROL_CONFORME: "conforme",
        }
        rows: list[ControlDistribution] = []
        for key in CONTROL_ORDER:
            value = int(self.kpis[keys[key]])
            rows.append(
                {
                    "key": key,
                    "label": CONTROL_LABELS[key],
                    "value": value,
                    "share_pct": f"{round(100.0 * value / total)}%",
                    "tone": CONTROL_TONES[key],
                    "icon": CONTROL_ICONS[key],
                }
            )
        return rows

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    async def _fetch(self) -> None:
        query = self.search.strip().lower()
        clauses = ["1=1"]
        params: dict[str, str] = {}
        if query:
            clauses.append(
                "(LOWER(p.name) LIKE :q OR LOWER(COALESCE(p.code, '')) LIKE :q"
                " OR LOWER(COALESCE(p.locality, '')) LIKE :q)"
            )
            params["q"] = f"%{query}%"
        where = " AND ".join(clauses)

        geometry_select = (
            """
            COALESCE(p.geometry_area_ha, 0),
            COALESCE(p.geometry_vertex_count, 0),
            COALESCE(p.geometry_source, 'AUCUNE'),
            COALESCE(p.boundary_geojson, ''),
            p.geometry_updated_at,
            COALESCE(p.geometry_updated_by, ''),
            COALESCE(p.geometry_notes, '')
            """
            if self.geometry_ready
            else """
            0, 0, 'AUCUNE', '', NULL, '', ''
            """
        )

        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        f"""
                        SELECT p.id, COALESCE(p.code, ''), p.name,
                               COALESCE(p.locality, ''),
                               COALESCE(p.area_ha, 0),
                               {geometry_select},
                               (SELECT COUNT(*) FROM remediation_log r
                                  WHERE r.domain = 'CONTOUR'
                                    AND r.target_id = p.id),
                               (SELECT r.action FROM remediation_log r
                                  WHERE r.domain = 'CONTOUR'
                                    AND r.target_id = p.id
                                  ORDER BY r.id DESC LIMIT 1),
                               (SELECT COALESCE(r.note, '')
                                  FROM remediation_log r
                                  WHERE r.domain = 'CONTOUR'
                                    AND r.target_id = p.id
                                  ORDER BY r.id DESC LIMIT 1),
                               (SELECT COALESCE(r.author, '')
                                  FROM remediation_log r
                                  WHERE r.domain = 'CONTOUR'
                                    AND r.target_id = p.id
                                  ORDER BY r.id DESC LIMIT 1),
                               (SELECT r.decided_on FROM remediation_log r
                                  WHERE r.domain = 'CONTOUR'
                                    AND r.target_id = p.id
                                  ORDER BY r.id DESC LIMIT 1)
                        FROM parcel p
                        WHERE {where}
                        ORDER BY p.code, p.name
                        LIMIT 200
                        """
                    ),
                    params,
                )
            ).all()

            log_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT r.id, r.target_id,
                               COALESCE(r.target_label, ''), r.action,
                               COALESCE(r.note, ''), COALESCE(r.author, ''),
                               r.decided_on, COALESCE(p.code, ''),
                               COALESCE(p.name, '')
                        FROM remediation_log r
                        LEFT JOIN parcel p ON p.id = r.target_id
                        WHERE r.domain = 'CONTOUR'
                        ORDER BY r.id DESC
                        LIMIT 20
                        """
                    )
                )
            ).all()

            total_decisions = int(
                (
                    await asession.execute(
                        text(
                            """
                            SELECT COUNT(*) FROM remediation_log
                            WHERE domain = 'CONTOUR'
                            """
                        )
                    )
                ).scalar()
                or 0
            )

        entries: list[ContourRow] = []
        gap_area = 0.0
        gap_max = 0.0
        mapped_area = 0.0
        for row in rows:
            declared = float(row[4] or 0)
            computed = float(row[5] or 0)
            vertex = int(row[6] or 0)
            source = str(row[7] or "AUCUNE")
            has_geometry = bool(row[8] or "") and vertex > 0
            gap_ha = (
                round(abs(computed - declared), 2)
                if has_geometry and computed > 0
                else 0.0
            )
            gap_pct = (
                round(gap_ha / declared * 100.0, 1)
                if declared > 0 and gap_ha > 0
                else 0.0
            )
            if not has_geometry:
                control = CONTROL_SANS
            elif gap_pct > GAP_TOLERANCE:
                control = CONTROL_ECART
            elif source in ("AUCUNE", "GENEREE"):
                control = CONTROL_A_VERIFIER
            else:
                control = CONTROL_CONFORME

            action = str(row[13] or "")
            validation = (
                action
                if action in (VALIDATION_VERIFIE, VALIDATION_A_RELEVER)
                else VALIDATION_NONE
            )
            gap_area += gap_ha
            gap_max = max(gap_max, gap_pct)
            if has_geometry:
                mapped_area += computed

            entries.append(
                {
                    "id": int(row[0]),
                    "code": str(row[1]) or "—",
                    "name": str(row[2]),
                    "locality": str(row[3]) or "Localité non renseignée",
                    "declared_area": declared,
                    "computed_area": computed,
                    "gap_ha": gap_ha,
                    "gap_pct": gap_pct,
                    "gap_label": f"{gap_pct:.1f} %",
                    "gap_bar_pct": f"{min(100.0, gap_pct * 4.0):.0f}%",
                    "vertex_count": vertex,
                    "has_geometry": has_geometry,
                    "source": source,
                    "source_label": SOURCE_LABELS.get(source, source),
                    "control": control,
                    "control_label": CONTROL_LABELS[control],
                    "control_tone": CONTROL_TONES[control],
                    "control_icon": CONTROL_ICONS[control],
                    "validation": validation,
                    "validation_label": VALIDATION_LABELS[validation],
                    "validation_tone": VALIDATION_TONES[validation],
                    "validation_icon": VALIDATION_ICONS[validation],
                    "decision": (
                        "" if validation == VALIDATION_NONE else validation
                    ),
                    "recommendation": _recommendation(
                        control, gap_pct, gap_ha, validation
                    ),
                    "decision_count": int(row[12] or 0),
                    "last_note": str(row[14] or "")
                    or "Aucune note de décision.",
                    "last_author": str(row[15] or "") or "—",
                    "last_decided_label": _fmt_date(row[16]),
                    "updated_label": _fmt_date(row[9]),
                    "updated_by": str(row[10] or "") or "—",
                    "geometry_notes": str(row[11] or "")
                    or "Aucune note de géométrie.",
                }
            )

        entries.sort(
            key=lambda item: (
                CONTROL_WEIGHT.get(item["control"], 9),
                0 if item["validation"] == VALIDATION_NONE else 1,
                -item["gap_pct"],
                item["code"],
            )
        )

        self.rows = entries
        ids = [item["id"] for item in entries]
        if self.selected_id not in ids:
            self.selected_id = ids[0] if ids else 0
        self.logs = [
            {
                "id": int(log[0]),
                "parcel_id": int(log[1] or 0),
                "label": (
                    f"{log[7]} · {log[8]}"
                    if str(log[8] or "")
                    else str(log[2] or "Îlot")
                ),
                "action": str(log[3]),
                "action_label": VALIDATION_LABELS.get(log[3], log[3]),
                "tone": VALIDATION_TONES.get(log[3], "muted"),
                "icon": VALIDATION_ICONS.get(log[3], "circle-dashed"),
                "note": str(log[4] or "") or "Aucune note consignée.",
                "author": str(log[5] or "") or DEFAULT_AUTHOR,
                "date_label": _fmt_date(log[6]),
            }
            for log in log_rows
        ]
        self.kpis = {
            "parcels": float(len(entries)),
            "conforme": float(
                len([i for i in entries if i["control"] == CONTROL_CONFORME])
            ),
            "a_verifier": float(
                len([i for i in entries if i["control"] == CONTROL_A_VERIFIER])
            ),
            "ecart": float(
                len([i for i in entries if i["control"] == CONTROL_ECART])
            ),
            "sans_contour": float(
                len([i for i in entries if i["control"] == CONTROL_SANS])
            ),
            "verifie": float(
                len(
                    [
                        i
                        for i in entries
                        if i["validation"] == VALIDATION_VERIFIE
                    ]
                )
            ),
            "a_relever": float(
                len(
                    [
                        i
                        for i in entries
                        if i["validation"] == VALIDATION_A_RELEVER
                    ]
                )
            ),
            "non_controle": float(
                len([i for i in entries if i["validation"] == VALIDATION_NONE])
            ),
            "gap_area": round(gap_area, 2),
            "gap_max": round(gap_max, 1),
            "mapped_area": round(mapped_area, 1),
            "decisions": float(total_decisions),
        }

    @rx.event
    async def load_contours(self):
        """Charge le contrôle des contours (idempotent, sans migration)."""
        self.is_loading = True
        self.notice = ""
        self.error = ""
        yield
        await ensure_local_database()
        await ensure_remediation_log_table()
        await seed_dashboard_data()
        await seed_parcel_geometry()
        async with rx.asession() as asession:
            self.geometry_ready = await geometry_columns_ready(asession)
        await self._fetch()
        today = datetime.date.today()
        self.today_label = (
            f"{WEEKDAYS_SHORT[today.weekday()]}. {today.day} "
            f"{MONTHS[today.month - 1]} {today.year}"
        )
        self.is_loading = False

    # ------------------------------------------------------------------
    # Filtres et saisie
    # ------------------------------------------------------------------

    @rx.event
    async def set_search(self, value: str):
        self.search = value
        await self._fetch()

    @rx.event
    def set_control_filter(self, value: str):
        self.control_filter = value

    @rx.event
    def set_validation_filter(self, value: str):
        self.validation_filter = value

    @rx.event
    async def reset_filters(self):
        self.search = ""
        self.control_filter = "TOUS"
        self.validation_filter = "TOUS"
        await self._fetch()

    @rx.event
    def set_note_draft(self, value: str):
        self.note_draft = value

    @rx.event
    def set_author_draft(self, value: str):
        self.author_draft = value

    @rx.event
    def focus_control(self, control: str):
        """Cible un statut de contrôle depuis les distributions."""
        self.control_filter = control
        self.validation_filter = "TOUS"

    @rx.event
    def select_contour(self, parcel_id: int):
        """Cible un îlot du poste de contrôle (appel direct compatible)."""
        self.error = ""
        self.selected_id = int(parcel_id)
        known = [item for item in self.rows if item["id"] == self.selected_id]
        if not known and self.rows:
            self.error = "Îlot hors du périmètre de contrôle courant."

    @rx.event
    def clear_selection(self):
        self.selected_id = 0

    # ------------------------------------------------------------------
    # Décisions traçables
    # ------------------------------------------------------------------

    async def _decide(self, parcel_id: int, action: str, note: str) -> str:
        """Consigne une décision de contour ; retourne un message d'état."""
        target_id = int(parcel_id)
        label = ""
        for item in self.rows:
            if item["id"] == target_id:
                label = f"{item['code']} · {item['name']}"
        author = self.author_draft.strip() or DEFAULT_AUTHOR
        comment = (
            "Contour vérifié à l'écran : cohérent avec la surface déclarée, "
            "sans valeur de relevé cadastral."
            if action == VALIDATION_VERIFIE
            else "Contour à relever sur le terrain : écart de surface à arbitrer."
        )
        if note:
            comment = f"{comment} {note}"

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
                if row is None:
                    return ""
                label = f"{row[0]} · {row[1]}"
            existing = (
                await asession.execute(
                    text(
                        """
                        SELECT action, COALESCE(note, '')
                        FROM remediation_log
                        WHERE domain = 'CONTOUR' AND target_id = :tid
                        ORDER BY id DESC LIMIT 1
                        """
                    ),
                    {"tid": target_id},
                )
            ).first()
            if (
                existing is not None
                and str(existing[0]) == action
                and str(existing[1]) == note
            ):
                return "duplicate"
            await asession.execute(
                text(
                    """
                    INSERT INTO remediation_log (
                        domain, target_kind, target_id, target_label,
                        action, note, author, module_route, decided_on
                    ) VALUES (
                        'CONTOUR', 'parcel', :tid, :label,
                        :action, :note, :author, '/cartographie', :decided
                    )
                    """
                ),
                {
                    "tid": target_id,
                    "label": label[:200],
                    "action": action,
                    "note": note,
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
        return "written"

    async def _decide_and_report(
        self,
        parcel_id: int,
        action: str,
        note: rx.event.PointerEventInfo | str = "",
    ):
        """Consigne une décision de contour et prépare le message d'état.

        Implémentation partagée par `verify_contour` / `mark_verified` et
        `survey_contour` / `mark_to_survey`, afin que les quatre noms restent
        utilisables depuis l'interface comme depuis un appel direct.
        """
        self.error = ""
        if isinstance(note, str) and note.strip():
            self.note_draft = note.strip()
        target_id = int(parcel_id)
        outcome = await self._decide(target_id, action, self.note_draft.strip())
        if outcome == "":
            self.error = "Îlot introuvable."
            return rx.toast(self.error)
        self.selected_id = target_id
        await self._fetch()
        self.selected_id = target_id
        if action == VALIDATION_VERIFIE:
            duplicate = "Vérification déjà consignée pour cet îlot."
            written = (
                "Contour vérifié à l'écran : décision consignée au journal."
            )
        else:
            duplicate = "Relevé terrain déjà programmé pour cet îlot."
            written = (
                "Relevé de terrain demandé : îlot documenté dans la "
                "cartographie."
            )
        if outcome == "duplicate":
            self.notice = duplicate
            return rx.toast(self.notice, duration=3500)
        self.notice = written
        return rx.toast(self.notice, duration=4000)

    @rx.event
    async def verify_contour(
        self, parcel_id: int, note: rx.event.PointerEventInfo | str = ""
    ):
        """Marque un contour vérifié à l'écran."""
        return await ContourState._decide_and_report(
            parcel_id, VALIDATION_VERIFIE, note
        )

    @rx.event
    async def survey_contour(
        self, parcel_id: int, note: rx.event.PointerEventInfo | str = ""
    ):
        """Marque un contour à relever sur le terrain."""
        return await ContourState._decide_and_report(
            parcel_id, VALIDATION_A_RELEVER, note
        )

    @rx.event
    async def mark_verified(self, parcel_id: int, note: str = ""):
        """Contour vérifié à l'écran : décision consignée sans helper.

        Implémentation autonome (SQL brut via `rx.asession()`) pour rester
        appelable indifféremment depuis l'interface ou depuis un test, sur
        l'instance courante de l'état.
        """
        self.error = ""
        if isinstance(note, str) and note.strip():
            self.note_draft = note.strip()
        target_id = int(parcel_id)
        note_text = self.note_draft.strip()
        author = self.author_draft.strip() or DEFAULT_AUTHOR
        label = ""
        for item in self.rows:
            if int(item["id"]) == target_id:
                label = f"{item['code']} · {item['name']}"
        comment = (
            "Contour vérifié à l'écran : cohérent avec la surface déclarée, "
            "sans valeur de relevé cadastral."
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
                if row is None:
                    self.error = "Îlot introuvable."
                    return rx.toast(self.error)
                label = f"{row[0]} · {row[1]}"
            existing = (
                await asession.execute(
                    text(
                        """
                        SELECT action, COALESCE(note, '')
                        FROM remediation_log
                        WHERE domain = 'CONTOUR' AND target_id = :tid
                        ORDER BY id DESC LIMIT 1
                        """
                    ),
                    {"tid": target_id},
                )
            ).first()
            duplicate = (
                existing is not None
                and str(existing[0]) == VALIDATION_VERIFIE
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
                            'CONTOUR', 'parcel', :tid, :label,
                            :action, :note, :author, '/cartographie', :decided
                        )
                        """
                    ),
                    {
                        "tid": target_id,
                        "label": label[:200],
                        "action": VALIDATION_VERIFIE,
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

        self.selected_id = target_id
        await self._fetch()
        self.selected_id = target_id
        if duplicate:
            self.notice = "Vérification déjà consignée pour cet îlot."
            return rx.toast(self.notice, duration=3500)
        self.notice = (
            "Contour vérifié à l'écran : décision consignée au journal."
        )
        return rx.toast(self.notice, duration=4000)

    @rx.event
    async def mark_to_survey(self, parcel_id: int, note: str = ""):
        """Contour à relever sur le terrain : décision consignée sans helper."""
        self.error = ""
        if isinstance(note, str) and note.strip():
            self.note_draft = note.strip()
        target_id = int(parcel_id)
        note_text = self.note_draft.strip()
        author = self.author_draft.strip() or DEFAULT_AUTHOR
        label = ""
        for item in self.rows:
            if int(item["id"]) == target_id:
                label = f"{item['code']} · {item['name']}"
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
                if row is None:
                    self.error = "Îlot introuvable."
                    return rx.toast(self.error)
                label = f"{row[0]} · {row[1]}"
            existing = (
                await asession.execute(
                    text(
                        """
                        SELECT action, COALESCE(note, '')
                        FROM remediation_log
                        WHERE domain = 'CONTOUR' AND target_id = :tid
                        ORDER BY id DESC LIMIT 1
                        """
                    ),
                    {"tid": target_id},
                )
            ).first()
            duplicate = (
                existing is not None
                and str(existing[0]) == VALIDATION_A_RELEVER
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
                            'CONTOUR', 'parcel', :tid, :label,
                            :action, :note, :author, '/cartographie', :decided
                        )
                        """
                    ),
                    {
                        "tid": target_id,
                        "label": label[:200],
                        "action": VALIDATION_A_RELEVER,
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

        self.selected_id = target_id
        await self._fetch()
        self.selected_id = target_id
        if duplicate:
            self.notice = "Relevé terrain déjà programmé pour cet îlot."
            return rx.toast(self.notice, duration=3500)
        self.notice = (
            "Relevé de terrain demandé : îlot documenté dans la cartographie."
        )
        return rx.toast(self.notice, duration=4000)

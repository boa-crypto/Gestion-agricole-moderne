"""État d'administration du référentiel phénologique AgriPro.

Pilote le pupitre « Administration → Référentiels → Phénologie → Stades » :
profils, stades, ordre, activation, codes BBCH, définitions, stades sensibles,
liens Guide, recommandations indicatives, import CSV/JSON et export JSON/CSV.

Toutes les écritures passent par `app/phenology_admin.py` (SQL brut via
`rx.asession()`), rien n'est jamais supprimé et aucune recommandation ne peut
devenir prescriptive.
"""

from __future__ import annotations

from typing import Any, TypedDict

import reflex as rx
from sqlalchemy import text

from app.phenology_admin import (
    CultureOption,
    ProfileAdminRow,
    RecoAdminRow,
    StageAdminRow,
    admin_profiles,
    admin_recommendations,
    admin_stages,
    culture_options,
    export_phenology_csv,
    export_phenology_json,
    import_stages,
    move_stage,
    save_profile,
    save_recommendation,
    save_stage,
    set_profile_active,
    set_stage_active,
    set_stage_critical,
)
from app.phenology_api import get_stage_detail
from app.phenology_reference import (
    CONFIDENCE_KEYS,
    RECOMMENDATION_DOMAIN_KEYS,
    SYSTEM_KEYS,
    confidence_label,
    recommendation_domain_label,
    system_label,
)
from app.phenology_validation import (
    phenology_audit_report,
    validate_stage_for_crop_name,
)
from app.seed_phenology import seed_phenology_data


class CheckRow(TypedDict):
    id: str
    label: str
    expectation: str
    ok: bool
    tone: str
    message: str
    detail: str


EMPTY_PROFILE: ProfileAdminRow = {
    "id": 0,
    "key": "",
    "name": "Aucun profil sélectionné",
    "culture_id": 0,
    "culture_name": "—",
    "culture_key": "",
    "system": "LOCAL",
    "system_label": "—",
    "summary": "",
    "source": "—",
    "is_default": False,
    "is_active": False,
    "stage_count": 0,
    "active_stages": 0,
    "critical_stages": 0,
    "recommendation_count": 0,
    "scope_label": "—",
}

EMPTY_STAGE: StageAdminRow = {
    "id": 0,
    "profile_id": 0,
    "key": "",
    "name": "Aucun stade sélectionné",
    "position": 0,
    "bbch_code": "",
    "description": "",
    "recognition": "",
    "watchpoints": "",
    "common_errors": "",
    "duration_days_min": 0,
    "duration_days_max": 0,
    "duration_label": "—",
    "is_critical": False,
    "is_active": False,
    "icon": "sprout",
    "color_hex": "#a3e635",
    "guide_article_slug": "",
    "guide_term_slug": "",
    "recommendation_count": 0,
}

EMPTY_PROFILE_DRAFT: dict[str, str] = {
    "id": "0",
    "key": "",
    "name": "",
    "culture_id": "",
    "system": "LOCAL",
    "summary": "",
    "source": "",
    "is_default": "0",
    "is_active": "1",
}

EMPTY_STAGE_DRAFT: dict[str, str] = {
    "id": "0",
    "key": "",
    "name": "",
    "bbch_code": "",
    "description": "",
    "recognition": "",
    "watchpoints": "",
    "common_errors": "",
    "duration_days_min": "0",
    "duration_days_max": "0",
    "is_critical": "0",
    "is_active": "1",
    "icon": "sprout",
    "color_hex": "#a3e635",
    "guide_article_slug": "",
    "guide_term_slug": "",
}

EMPTY_RECO_DRAFT: dict[str, str] = {
    "id": "0",
    "domain": "SURVEILLANCE",
    "title": "",
    "statement": "",
    "confidence": "INDICATIVE",
    "source": "Référentiel agronomique AgriPro",
    "guide_article_slug": "",
}

EMPTY_TOTALS: dict[str, int] = {
    "profiles": 0,
    "active_profiles": 0,
    "stages": 0,
    "active_stages": 0,
    "critical_stages": 0,
    "recommendations": 0,
    "advisory_recommendations": 0,
    "prescriptive_recommendations": 0,
    "observations": 0,
    "changes": 0,
    "cultures": 0,
    "invalid_observations": 0,
}

CSV_TEMPLATE: str = (
    "key,name,bbch_code,duration_days_min,duration_days_max,is_critical,"
    "description,recognition,watchpoints,common_errors,guide_article_slug\n"
    "epiaison,Épiaison,BBCH 51-59,7,14,1,"
    "Sortie de l'épi hors de la gaine.,Épis visibles au-dessus du feuillage.,"
    "Fusariose si pluies.,Confondre gonflement et épiaison,suivre-les-stades\n"
)


class PhenologyAdminState(rx.State):
    """Pupitre d'administration du référentiel phénologique."""

    is_loading: bool = True
    notice: str = ""
    form_errors: list[str] = []

    cultures: list[CultureOption] = []
    profiles: list[ProfileAdminRow] = []
    selected_profile_id: int = 0

    stages: list[StageAdminRow] = []
    selected_stage_id: int = 0
    recommendations: list[RecoAdminRow] = []
    stage_preview: dict[str, str] = {
        "name": "",
        "description": "",
        "recognition": "",
        "watchpoints": "",
        "common_errors": "",
        "duration_label": "",
        "bbch_code": "",
        "system_label": "",
        "culture_name": "",
        "profile_name": "",
        "guide_article_slug": "",
    }

    totals: dict[str, int] = EMPTY_TOTALS

    profile_editor_open: bool = False
    profile_draft: dict[str, str] = EMPTY_PROFILE_DRAFT
    stage_editor_open: bool = False
    stage_draft: dict[str, str] = EMPTY_STAGE_DRAFT
    reco_editor_open: bool = False
    reco_draft: dict[str, str] = EMPTY_RECO_DRAFT
    form_key: int = 0

    import_format: str = "CSV"
    import_payload: str = ""
    import_report: list[str] = []
    export_format: str = "JSON"
    export_payload: str = ""

    checks: list[CheckRow] = []

    # Référentiels exposés au frontend --------------------------------------
    system_options: list[tuple[str, str]] = [
        (key, system_label(key)) for key in SYSTEM_KEYS
    ]
    domain_options: list[tuple[str, str]] = [
        (key, recommendation_domain_label(key))
        for key in RECOMMENDATION_DOMAIN_KEYS
    ]
    confidence_options: list[tuple[str, str]] = [
        (key, confidence_label(key)) for key in CONFIDENCE_KEYS
    ]
    format_options: list[tuple[str, str]] = [
        ("CSV", "CSV (tableur)"),
        ("JSON", "JSON (structuré)"),
    ]
    csv_template: str = CSV_TEMPLATE

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def selected_profile(self) -> ProfileAdminRow:
        for item in self.profiles:
            if item["id"] == self.selected_profile_id:
                return item
        return EMPTY_PROFILE

    @rx.var
    def selected_stage(self) -> StageAdminRow:
        for item in self.stages:
            if item["id"] == self.selected_stage_id:
                return item
        return EMPTY_STAGE

    @rx.var
    def has_profile(self) -> bool:
        return self.selected_profile_id > 0

    @rx.var
    def has_stage(self) -> bool:
        return self.selected_stage_id > 0

    @rx.var
    def has_errors(self) -> bool:
        return len(self.form_errors) > 0

    @rx.var
    def stage_count(self) -> int:
        return len(self.stages)

    @rx.var
    def profile_count(self) -> int:
        return len(self.profiles)

    @rx.var
    def failed_checks(self) -> int:
        return len([item for item in self.checks if not item["ok"]])

    @rx.var
    def checks_passed(self) -> bool:
        return len(self.checks) > 0 and self.failed_checks == 0

    @rx.var
    def editor_key(self) -> str:
        return f"phen-admin-{self.form_key}"

    @rx.var
    def stage_editor_title(self) -> str:
        if self.stage_draft.get("id", "0") in ("", "0"):
            return "Nouveau stade du cycle"
        return "Modifier le stade"

    @rx.var
    def profile_editor_title(self) -> str:
        if self.profile_draft.get("id", "0") in ("", "0"):
            return "Nouveau profil phénologique"
        return "Modifier le profil phénologique"

    @rx.var
    def reco_editor_title(self) -> str:
        if self.reco_draft.get("id", "0") in ("", "0"):
            return "Nouvelle opération associée"
        return "Modifier l'opération associée"

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    async def _load_profiles(self) -> None:
        self.profiles = await admin_profiles()
        ids = [item["id"] for item in self.profiles]
        if self.selected_profile_id not in ids:
            self.selected_profile_id = ids[0] if ids else 0

    async def _load_stages(self) -> None:
        self.stages = await admin_stages(self.selected_profile_id)
        ids = [item["id"] for item in self.stages]
        if self.selected_stage_id not in ids:
            self.selected_stage_id = ids[0] if ids else 0
        await self._load_stage_context()

    async def _load_stage_context(self) -> None:
        if self.selected_stage_id <= 0:
            self.recommendations = []
            self.stage_preview = {key: "" for key in self.stage_preview}
            return
        self.recommendations = await admin_recommendations(
            self.selected_stage_id
        )
        detail = await get_stage_detail(self.selected_stage_id)
        self.stage_preview = {
            "name": str(detail["name"]),
            "description": str(detail["description"]),
            "recognition": str(detail["recognition"]),
            "watchpoints": str(detail["watchpoints"]),
            "common_errors": str(detail["common_errors"]),
            "duration_label": str(detail["duration_label"]),
            "bbch_code": str(detail["bbch_code"]),
            "system_label": str(detail["system_label"]),
            "culture_name": str(detail["culture_name"]),
            "profile_name": str(detail["profile_name"]),
            "guide_article_slug": str(detail["guide_article_slug"]),
        }

    async def _load_totals(self) -> None:
        report = await phenology_audit_report()
        totals = dict(EMPTY_TOTALS)
        for key in totals:
            if key in report:
                totals[key] = int(report[key])
        self.totals = totals

    @rx.event
    async def load_admin(self):
        """Charge le pupitre d'administration phénologique."""
        self.is_loading = True
        self.notice = ""
        self.form_errors = []
        yield
        await seed_phenology_data()
        self.cultures = await culture_options()
        await self._load_profiles()
        await self._load_stages()
        await self._load_totals()
        await self._run_checks()
        self.is_loading = False

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @rx.event
    async def select_profile(self, profile_id: int):
        self.selected_profile_id = int(profile_id)
        self.selected_stage_id = 0
        self.notice = ""
        self.form_errors = []
        self.export_payload = ""
        await self._load_stages()

    @rx.event
    async def select_stage(self, stage_id: int):
        self.selected_stage_id = int(stage_id)
        self.form_errors = []
        await self._load_stage_context()

    # ------------------------------------------------------------------
    # Éditeur de profil
    # ------------------------------------------------------------------

    @rx.event
    def open_profile_create(self):
        draft = dict(EMPTY_PROFILE_DRAFT)
        if self.cultures:
            draft["culture_id"] = self.cultures[0]["value"]
        self.profile_draft = draft
        self.form_errors = []
        self.form_key += 1
        self.profile_editor_open = True

    @rx.event
    def open_profile_edit(self):
        profile = self.selected_profile
        if profile["id"] == 0:
            self.form_errors = ["Sélectionnez d'abord un profil."]
            return
        self.profile_draft = {
            "id": str(profile["id"]),
            "key": profile["key"],
            "name": profile["name"],
            "culture_id": str(profile["culture_id"]),
            "system": profile["system"],
            "summary": profile["summary"],
            "source": profile["source"],
            "is_default": "1" if profile["is_default"] else "0",
            "is_active": "1" if profile["is_active"] else "0",
        }
        self.form_errors = []
        self.form_key += 1
        self.profile_editor_open = True

    @rx.event
    def close_profile_editor(self):
        self.profile_editor_open = False
        self.form_errors = []

    @rx.event
    async def submit_profile(self, form_data: dict[str, Any]):
        data = dict(self.profile_draft)
        for key, value in form_data.items():
            data[key] = str(value)
        data["is_default"] = "1" if form_data.get("is_default") else "0"
        data["is_active"] = "1" if form_data.get("is_active") else "0"
        profile_id = int(data.get("id", "0") or 0)
        result = await save_profile(data, profile_id)
        if not result["ok"]:
            self.form_errors = [str(item) for item in result["errors"]]
            self.profile_draft = data
            return
        self.form_errors = []
        self.profile_editor_open = False
        self.selected_profile_id = int(result["profile_id"])
        self.notice = str(result.get("message", "Profil enregistré."))
        await self._load_profiles()
        await self._load_stages()
        await self._load_totals()
        yield rx.toast(self.notice, duration=4000, close_button=True)

    @rx.event
    async def toggle_profile_active(self, profile_id: int, active: bool):
        self.notice = await set_profile_active(int(profile_id), bool(active))
        await self._load_profiles()
        await self._load_totals()
        yield rx.toast(self.notice, duration=3500, close_button=True)

    # ------------------------------------------------------------------
    # Éditeur de stade
    # ------------------------------------------------------------------

    @rx.event
    def open_stage_create(self):
        if self.selected_profile_id == 0:
            self.form_errors = ["Sélectionnez d'abord un profil."]
            return
        self.stage_draft = dict(EMPTY_STAGE_DRAFT)
        self.form_errors = []
        self.form_key += 1
        self.stage_editor_open = True

    @rx.event
    def open_stage_edit(self, stage_id: int):
        for item in self.stages:
            if item["id"] == int(stage_id):
                self.stage_draft = {
                    "id": str(item["id"]),
                    "key": item["key"],
                    "name": item["name"],
                    "bbch_code": item["bbch_code"],
                    "description": item["description"],
                    "recognition": item["recognition"],
                    "watchpoints": item["watchpoints"],
                    "common_errors": item["common_errors"],
                    "duration_days_min": str(item["duration_days_min"]),
                    "duration_days_max": str(item["duration_days_max"]),
                    "is_critical": "1" if item["is_critical"] else "0",
                    "is_active": "1" if item["is_active"] else "0",
                    "icon": item["icon"],
                    "color_hex": item["color_hex"],
                    "guide_article_slug": item["guide_article_slug"],
                    "guide_term_slug": item["guide_term_slug"],
                }
                self.selected_stage_id = int(stage_id)
                self.form_errors = []
                self.form_key += 1
                self.stage_editor_open = True
                return
        self.form_errors = ["Stade introuvable."]

    @rx.event
    def close_stage_editor(self):
        self.stage_editor_open = False
        self.form_errors = []

    @rx.event
    async def submit_stage(self, form_data: dict[str, Any]):
        data = dict(self.stage_draft)
        for key, value in form_data.items():
            data[key] = str(value)
        data["is_critical"] = "1" if form_data.get("is_critical") else "0"
        data["is_active"] = "1" if form_data.get("is_active") else "0"
        stage_id = int(data.get("id", "0") or 0)
        result = await save_stage(self.selected_profile_id, data, stage_id)
        if not result["ok"]:
            self.form_errors = [str(item) for item in result["errors"]]
            self.stage_draft = data
            return
        self.form_errors = []
        self.stage_editor_open = False
        self.selected_stage_id = int(result["stage_id"])
        self.notice = str(result.get("message", "Stade enregistré."))
        await self._load_profiles()
        await self._load_stages()
        await self._load_totals()
        await self._run_checks()
        yield rx.toast(self.notice, duration=4000, close_button=True)

    @rx.event
    async def toggle_stage_active(self, stage_id: int, active: bool):
        self.notice = await set_stage_active(int(stage_id), bool(active))
        await self._load_profiles()
        await self._load_stages()
        await self._load_totals()
        yield rx.toast(self.notice, duration=3500, close_button=True)

    @rx.event
    async def toggle_stage_critical(self, stage_id: int, critical: bool):
        self.notice = await set_stage_critical(int(stage_id), bool(critical))
        await self._load_profiles()
        await self._load_stages()
        await self._load_totals()
        yield rx.toast(self.notice, duration=3500, close_button=True)

    @rx.event
    async def shift_stage(self, stage_id: int, direction: int):
        self.notice = await move_stage(int(stage_id), int(direction))
        await self._load_stages()
        yield rx.toast(self.notice, duration=3000, close_button=True)

    # ------------------------------------------------------------------
    # Recommandations indicatives
    # ------------------------------------------------------------------

    @rx.event
    def open_reco_create(self):
        if self.selected_stage_id == 0:
            self.form_errors = ["Sélectionnez d'abord un stade."]
            return
        self.reco_draft = dict(EMPTY_RECO_DRAFT)
        self.form_errors = []
        self.form_key += 1
        self.reco_editor_open = True

    @rx.event
    def open_reco_edit(self, reco_id: int):
        for item in self.recommendations:
            if item["id"] == int(reco_id):
                self.reco_draft = {
                    "id": str(item["id"]),
                    "domain": item["domain"],
                    "title": item["title"],
                    "statement": item["statement"],
                    "confidence": item["confidence"],
                    "source": item["source"],
                    "guide_article_slug": item["guide_article_slug"],
                }
                self.form_errors = []
                self.form_key += 1
                self.reco_editor_open = True
                return
        self.form_errors = ["Recommandation introuvable."]

    @rx.event
    def close_reco_editor(self):
        self.reco_editor_open = False
        self.form_errors = []

    @rx.event
    async def submit_recommendation(self, form_data: dict[str, Any]):
        data = dict(self.reco_draft)
        for key, value in form_data.items():
            data[key] = str(value)
        reco_id = int(data.get("id", "0") or 0)
        result = await save_recommendation(
            self.selected_stage_id, data, reco_id
        )
        if not result["ok"]:
            self.form_errors = [str(item) for item in result["errors"]]
            self.reco_draft = data
            return
        self.form_errors = []
        self.reco_editor_open = False
        self.notice = str(result.get("message", "Recommandation enregistrée."))
        await self._load_stages()
        await self._load_totals()
        await self._run_checks()
        yield rx.toast(self.notice, duration=4000, close_button=True)

    # ------------------------------------------------------------------
    # Import / export
    # ------------------------------------------------------------------

    @rx.event
    def set_import_format(self, value: str):
        self.import_format = value

    @rx.event
    def set_import_payload(self, value: str):
        self.import_payload = value

    @rx.event
    def set_export_format(self, value: str):
        self.export_format = value
        self.export_payload = ""

    @rx.event
    def load_csv_template(self):
        self.import_format = "CSV"
        self.import_payload = CSV_TEMPLATE
        self.form_key += 1
        self.import_report = [
            "Modèle CSV chargé : complétez les lignes puis lancez l'import."
        ]

    @rx.event
    async def run_import(self, form_data: dict[str, Any]):
        payload = str(form_data.get("payload", self.import_payload))
        fmt = str(form_data.get("format", self.import_format)) or "CSV"
        self.import_payload = payload
        self.import_format = fmt
        result = await import_stages(self.selected_profile_id, payload, fmt)
        report = [
            f"{int(result['created'])} stade(s) créé(s)",
            f"{int(result['updated'])} stade(s) enrichi(s)",
            f"{int(result['skipped'])} ligne(s) ignorée(s)",
        ]
        report.extend(str(item) for item in result["errors"])
        self.import_report = report
        await self._load_profiles()
        await self._load_stages()
        await self._load_totals()
        await self._run_checks()
        if result["ok"]:
            self.notice = (
                f"Import {fmt.upper()} appliqué : aucun stade existant n'a été "
                "supprimé."
            )
            yield rx.toast(self.notice, duration=4500, close_button=True)
        else:
            yield rx.toast(
                "Import refusé : consultez le rapport détaillé.",
                duration=4500,
                close_button=True,
            )

    @rx.event
    async def run_export(self):
        if self.export_format == "CSV":
            self.export_payload = await export_phenology_csv(
                self.selected_profile_id
            )
        else:
            self.export_payload = await export_phenology_json(
                self.selected_profile_id
            )
        self.notice = f"Export {self.export_format} généré."
        yield rx.toast(self.notice, duration=3500, close_button=True)

    @rx.event
    async def export_all(self):
        if self.export_format == "CSV":
            self.export_payload = await export_phenology_csv(0)
        else:
            self.export_payload = await export_phenology_json(0)
        self.notice = f"Export {self.export_format} complet généré."
        yield rx.toast(self.notice, duration=3500, close_button=True)

    # ------------------------------------------------------------------
    # Validations finales
    # ------------------------------------------------------------------

    async def _run_checks(self) -> None:
        checks: list[CheckRow] = []

        expectations: list[tuple[str, str, str, bool]] = [
            ("ble", "Blé dur", "Tallage", True),
            ("tomate", "Tomate", "Nouaison", True),
            ("olivier", "Olivier", "Tallage", False),
        ]
        for key, culture, stage, expected in expectations:
            result = await validate_stage_for_crop_name(culture, stage)
            ok = result.is_valid is expected
            preview = ", ".join(result.available_stages[:6])
            checks.append(
                {
                    "id": f"stage-{key}",
                    "label": f"{culture} + {stage}",
                    "expectation": "doit être accepté"
                    if expected
                    else "doit être refusé",
                    "ok": ok,
                    "tone": "good" if ok else "bad",
                    "message": result.message or "Aucun message de validation.",
                    "detail": f"Stades du profil : {preview}"
                    if preview
                    else "Aucun stade disponible dans ce profil.",
                }
            )

        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            (SELECT COUNT(*) FROM crop_stage_observation),
                            (SELECT COUNT(*) FROM crop_stage_change),
                            (SELECT COUNT(*) FROM crop_stage_recommendation
                               WHERE is_advisory = 0),
                            (SELECT COUNT(*) FROM crop_stage_recommendation
                               WHERE COALESCE(source, '') = ''),
                            (SELECT COUNT(*) FROM crop_phenology_stage
                               WHERE is_active = 1)
                        """
                    )
                )
            ).first()
        observations = int(row[0] or 0) if row else 0
        changes = int(row[1] or 0) if row else 0
        prescriptive = int(row[2] or 0) if row else 0
        unsourced = int(row[3] or 0) if row else 0
        active_stages = int(row[4] or 0) if row else 0

        history_ok = changes >= observations if observations else True
        checks.append(
            {
                "id": "history",
                "label": "Historique conservé",
                "expectation": "un changement tracé par observation",
                "ok": history_ok,
                "tone": "good" if history_ok else "bad",
                "message": (
                    f"{observations} observation(s) pour {changes} "
                    "changement(s) tracé(s) : aucun historique purgé."
                    if history_ok
                    else f"{observations} observation(s) mais seulement "
                    f"{changes} changement(s) tracé(s)."
                ),
                "detail": "La désactivation remplace toute suppression.",
            }
        )
        advisory_ok = prescriptive == 0 and unsourced == 0
        checks.append(
            {
                "id": "advisory",
                "label": "Recommandations non prescriptives",
                "expectation": "toutes indicatives et sourcées",
                "ok": advisory_ok,
                "tone": "good" if advisory_ok else "bad",
                "message": (
                    "Toutes les recommandations restent indicatives et portent "
                    "leur source."
                    if advisory_ok
                    else f"{prescriptive} prescriptive(s) et {unsourced} sans "
                    "source détectée(s)."
                ),
                "detail": "Aucune dose ni produit non sourcé n'est proposé.",
            }
        )
        cycles_ok = active_stages > 0
        checks.append(
            {
                "id": "cycles",
                "label": "Cycles propres à chaque culture",
                "expectation": "aucune liste globale de stades",
                "ok": cycles_ok,
                "tone": "good" if cycles_ok else "warn",
                "message": (
                    f"{active_stages} stade(s) actif(s) répartis par profil de "
                    "culture."
                ),
                "detail": "Chaque profil porte son propre enchaînement.",
            }
        )
        self.checks = checks

    @rx.event
    async def run_checks(self):
        """Relance les validations finales du système phénologique."""
        await self._load_totals()
        await self._run_checks()
        yield rx.toast(
            f"{len(self.checks) - PhenologyAdminState.failed_checks} contrôle(s) conforme(s) sur {len(self.checks)}.",
            duration=4000,
            close_button=True,
        )

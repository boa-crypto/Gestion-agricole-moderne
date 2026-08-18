"""État du suivi phénologique de la culture sélectionnée (module Parcelles).

Toutes les lectures et écritures se font en SQL brut via `rx.asession()` et
réutilisent les briques de `app/phenology_validation.py` (résolution du profil
culture/variété, contrôle de cohérence stade ↔ culture, historique).

Règles respectées :

* le stade observé DOIT appartenir au profil phénologique de la culture
  (« Olivier + Tallage » est refusé) ;
* rien n'est jamais supprimé : chaque observation crée une ligne d'historique
  conservant l'ancien et le nouveau stade ;
* les recommandations restent indicatives, jamais prescriptives.
"""

from __future__ import annotations

import datetime
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.date_utils import as_date
from app.phenology_reference import (
    CONFIDENCE_LABELS,
    DEVIATION_INCONNU,
    OBSERVATION_STATUS_KEYS,
    STATUS_CONFIRME,
    confidence_label,
    deviation_label,
    deviation_tone,
    observation_source_label,
    observation_status_label,
    observation_status_tone,
    recommendation_domain_icon,
    recommendation_domain_label,
    system_label,
)
from app.phenology_validation import (
    observation_history,
    profile_for_crop,
    profile_stages,
    stage_duration_report,
    stage_recommendations,
    validate_observation,
)
from app.seed_phenology import seed_phenology_data
from app.states.dashboard_state import MONTHS

STATUS_FORM_KEYS: list[str] = OBSERVATION_STATUS_KEYS[:3]


class Option(TypedDict):
    value: str
    label: str


class StageRail(TypedDict):
    id: int
    name: str
    bbch: str
    position: int
    state: str
    is_critical: bool
    icon: str
    color: str
    duration: str
    description: str
    recognition: str
    watchpoints: str
    common_errors: str
    progress: int


class RecoRow(TypedDict):
    id: int
    domain_label: str
    icon: str
    title: str
    statement: str
    confidence_label: str
    source: str


class HistoryRow(TypedDict):
    id: int
    date_label: str
    author: str
    comment: str
    previous_stage: str
    new_stage: str


class ObsRow(TypedDict):
    id: int
    date_label: str
    time_label: str
    stage_name: str
    status_label: str
    status_tone: str
    source_label: str
    observer: str
    vigour: str
    homogeneity: str
    anomalies: str
    diseases: str
    pests: str
    water_stress: bool
    thermal_stress: bool
    comment: str
    progress: int


class GuideLink(TypedDict):
    title: str
    subtitle: str
    route: str


EMPTY_SUMMARY: dict[str, str] = {
    "crop_name": "—",
    "culture_name": "—",
    "profile_name": "—",
    "system_label": "—",
    "profile_summary": "",
    "scope_label": "—",
    "current_stage": "Aucun stade observé",
    "previous_stage": "—",
    "next_stage": "—",
    "progress": "0",
    "progress_pct": "0%",
    "stages_done": "0",
    "stage_count": "0",
    "last_observation": "—",
    "last_observer": "—",
    "last_status": "—",
    "last_status_tone": "muted",
    "days_in_stage": "0",
    "duration_label": deviation_label(DEVIATION_INCONNU),
    "duration_tone": "muted",
    "bbch": "",
    "is_critical": "0",
}


def _fmt_date(value: object) -> str:
    day = as_date(value)
    if day is None:
        return "—"
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


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


def _duration_label(days_min: int, days_max: int) -> str:
    if days_min <= 0 and days_max <= 0:
        return "Durée indicative non renseignée"
    if days_min <= 0:
        return f"jusqu'à {days_max} j"
    if days_max <= 0:
        return f"à partir de {days_min} j"
    return f"{days_min} à {days_max} j"


SCOPE_LABELS: dict[str, str] = {
    "VARIETE": "Profil propre à la variété",
    "ESPECE": "Profil propre à l'espèce",
    "CULTURE": "Profil générique de la culture",
}


class PhenologyState(rx.State):
    """Suivi phénologique d'une culture de parcelle."""

    is_loading: bool = True
    parcel_label: str = "—"
    selected_crop_id: int = 0
    crop_options: list[Option] = []
    has_profile: bool = False

    summary: dict[str, str] = EMPTY_SUMMARY
    stages: list[StageRail] = []
    recommendations: list[RecoRow] = []
    history: list[HistoryRow] = []
    observations: list[ObsRow] = []
    guide_links: list[GuideLink] = []

    stage_choices: list[Option] = []
    status_options: list[Option] = [
        {"value": key, "label": observation_status_label(key)}
        for key in STATUS_FORM_KEYS
    ]

    form_error: str = ""
    form_errors: list[str] = []
    form_key: int = 0

    # ------------------------------------------------------------------
    # Vars dérivées
    # ------------------------------------------------------------------

    @rx.var
    def has_selection(self) -> bool:
        return self.selected_crop_id > 0

    @rx.var
    def confidence_note(self) -> str:
        return CONFIDENCE_LABELS[list(CONFIDENCE_LABELS.keys())[0]]

    @rx.var
    def observation_count(self) -> int:
        return len(self.observations)

    @rx.var
    def history_count(self) -> int:
        return len(self.history)

    @rx.var
    def today_iso(self) -> str:
        return datetime.date.today().isoformat()

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    def _reset_view(self) -> None:
        self.summary = dict(EMPTY_SUMMARY)
        self.stages = []
        self.recommendations = []
        self.history = []
        self.observations = []
        self.guide_links = []
        self.stage_choices = []
        self.has_profile = False

    async def _load_crops(self, parcel_id: int) -> None:
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT c.id, c.name, COALESCE(c.season, '')
                        FROM crop c
                        WHERE c.parcel_id = :pid
                        ORDER BY
                            CASE c.status WHEN 'EN_COURS' THEN 1
                                          WHEN 'PLANIFIEE' THEN 2
                                          ELSE 3 END,
                            c.id
                        LIMIT 40
                        """
                    ),
                    {"pid": int(parcel_id)},
                )
            ).all()
        options: list[Option] = []
        for row in rows:
            season = str(row[2])
            suffix = f" · campagne {season}" if season else ""
            options.append(
                {"value": str(int(row[0])), "label": f"{row[1]}{suffix}"}
            )
        self.crop_options = options
        ids = [int(opt["value"]) for opt in options]
        if self.selected_crop_id not in ids:
            self.selected_crop_id = ids[0] if ids else 0

    async def _load_guide_links(self, slug: str) -> None:
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT a.title, COALESCE(a.summary, ''),
                               COALESCE(NULLIF(a.module_route, ''), '/guide')
                        FROM guide_article a
                        LEFT JOIN guide_category cat ON cat.id = a.category_id
                        WHERE a.slug = :slug
                           OR COALESCE(cat.key, '') IN ('cultures', 'travaux')
                        ORDER BY CASE WHEN a.slug = :slug THEN 0 ELSE 1 END,
                                 a.position, a.id
                        LIMIT 4
                        """
                    ),
                    {"slug": slug},
                )
            ).all()
        self.guide_links = [
            {
                "title": str(row[0]),
                "subtitle": str(row[1]),
                "route": "/guide",
            }
            for row in rows
        ]

    async def _load_observations(self, crop_id: int) -> int:
        """Charge les observations et retourne l'identifiant du stade courant."""
        async with rx.asession() as asession:
            rows = (
                await asession.execute(
                    text(
                        """
                        SELECT o.id, o.observed_on, COALESCE(o.observed_at_time, ''),
                               COALESCE(st.name, ''), o.status, o.source,
                               COALESCE(o.observer, ''), COALESCE(o.vigour, ''),
                               COALESCE(o.homogeneity, ''), COALESCE(o.anomalies, ''),
                               COALESCE(o.diseases_observed, ''),
                               COALESCE(o.pests_observed, ''),
                               o.water_stress, o.thermal_stress,
                               COALESCE(o.comment, ''),
                               COALESCE(o.progress_percent, 0),
                               COALESCE(o.stage_id, 0)
                        FROM crop_stage_observation o
                        LEFT JOIN crop_phenology_stage st ON st.id = o.stage_id
                        WHERE o.crop_id = :cid
                        ORDER BY o.observed_on DESC, o.id DESC
                        LIMIT 24
                        """
                    ),
                    {"cid": int(crop_id)},
                )
            ).all()

        observations: list[ObsRow] = []
        for row in rows:
            status = str(row[4])
            observations.append(
                {
                    "id": int(row[0]),
                    "date_label": _fmt_date(row[1]),
                    "time_label": str(row[2]),
                    "stage_name": str(row[3]) or "Stade inconnu",
                    "status_label": observation_status_label(status),
                    "status_tone": observation_status_tone(status),
                    "source_label": observation_source_label(row[5]),
                    "observer": str(row[6]) or "Observateur non précisé",
                    "vigour": str(row[7]),
                    "homogeneity": str(row[8]),
                    "anomalies": str(row[9]),
                    "diseases": str(row[10]),
                    "pests": str(row[11]),
                    "water_stress": bool(row[12]),
                    "thermal_stress": bool(row[13]),
                    "comment": str(row[14]) or "Aucun commentaire consigné.",
                    "progress": int(row[15] or 0),
                }
            )
        self.observations = observations
        return int(rows[0][16] or 0) if rows else 0

    async def _refresh(self) -> None:
        crop_id = self.selected_crop_id
        if crop_id == 0:
            self._reset_view()
            return

        resolution = await profile_for_crop(crop_id)
        if not resolution["found"]:
            self._reset_view()
            self.summary = dict(EMPTY_SUMMARY)
            return

        stages = await profile_stages(resolution["profile_id"])
        current_stage_id = await self._load_observations(crop_id)
        current_position = 0
        for stage in stages:
            if stage["id"] == current_stage_id:
                current_position = stage["position"]

        rail: list[StageRail] = []
        for stage in stages:
            if current_position == 0:
                state = "todo"
            elif stage["position"] < current_position:
                state = "done"
            elif stage["position"] == current_position:
                state = "current"
            else:
                state = "todo"
            rail.append(
                {
                    "id": stage["id"],
                    "name": stage["name"],
                    "bbch": stage["bbch_code"],
                    "position": stage["position"],
                    "state": state,
                    "is_critical": stage["is_critical"],
                    "icon": stage["icon"],
                    "color": stage["color_hex"],
                    "duration": _duration_label(
                        stage["days_min"], stage["days_max"]
                    ),
                    "description": stage["description"],
                    "recognition": stage["recognition"],
                    "watchpoints": stage["watchpoints"],
                    "common_errors": stage["common_errors"],
                    "progress": stage["progress"],
                }
            )
        self.stages = rail
        self.stage_choices = [
            {"value": stage["name"], "label": stage["name"]} for stage in stages
        ]

        current = next(
            (s for s in stages if s["position"] == current_position), None
        )
        previous = next(
            (s for s in stages if s["position"] == current_position - 1), None
        )
        following = next(
            (s for s in stages if s["position"] == current_position + 1), None
        )

        self.recommendations = []
        guide_slug = ""
        if current is not None:
            recos = await stage_recommendations(current["id"])
            self.recommendations = [
                {
                    "id": int(reco["id"]),
                    "domain_label": recommendation_domain_label(reco["domain"]),
                    "icon": recommendation_domain_icon(reco["domain"]),
                    "title": str(reco["title"]),
                    "statement": str(reco["statement"]),
                    "confidence_label": confidence_label(reco["confidence"]),
                    "source": str(reco["source"]),
                }
                for reco in recos
            ]
            async with rx.asession() as asession:
                slug = (
                    await asession.execute(
                        text(
                            """
                            SELECT COALESCE(guide_article_slug, '')
                            FROM crop_phenology_stage WHERE id = :sid
                            """
                        ),
                        {"sid": current["id"]},
                    )
                ).scalar()
            guide_slug = str(slug or "")
        await self._load_guide_links(guide_slug)

        self.history = [
            {
                "id": int(item["id"]),
                "date_label": _fmt_date(item["changed_on"]),
                "author": str(item["author"]) or "Auteur non précisé",
                "comment": str(item["comment"]) or "—",
                "previous_stage": str(item["previous_stage"])
                or "Premier stade consigné",
                "new_stage": str(item["new_stage"]) or "—",
            }
            for item in await observation_history(crop_id)
        ]

        duration = await stage_duration_report(crop_id)
        latest = self.observations[0] if self.observations else None
        crop_label = ""
        for option in self.crop_options:
            if int(option["value"]) == crop_id:
                crop_label = option["label"]

        self.summary = {
            "crop_name": crop_label or "Culture sélectionnée",
            "culture_name": resolution["culture_name"] or "—",
            "profile_name": resolution["profile_name"],
            "system_label": system_label(resolution["system"]),
            "profile_summary": resolution["summary"],
            "scope_label": SCOPE_LABELS.get(
                resolution["scope"], "Profil du référentiel"
            ),
            "current_stage": current["name"]
            if current is not None
            else "Aucun stade observé",
            "previous_stage": previous["name"]
            if previous is not None
            else "Début de cycle",
            "next_stage": following["name"]
            if following is not None
            else "Fin de cycle",
            "progress": str(current["progress"] if current is not None else 0),
            "progress_pct": f"{current['progress'] if current is not None else 0}%",
            "stages_done": str(current_position),
            "stage_count": str(len(stages)),
            "last_observation": latest["date_label"] if latest else "—",
            "last_observer": latest["observer"] if latest else "—",
            "last_status": latest["status_label"] if latest else "—",
            "last_status_tone": latest["status_tone"] if latest else "muted",
            "days_in_stage": str(int(duration["days_in_stage"])),
            "duration_label": deviation_label(duration["status"]),
            "duration_tone": deviation_tone(duration["status"]),
            "bbch": current["bbch_code"] if current is not None else "",
            "is_critical": "1"
            if current is not None and current["is_critical"]
            else "0",
        }
        self.has_profile = True

    # ------------------------------------------------------------------
    # Événements
    # ------------------------------------------------------------------

    @rx.event
    async def load_phenology(self):
        from app.states.parcels_state import ParcelsState

        self.is_loading = True
        self.form_error = ""
        self.form_errors = []
        yield
        await seed_phenology_data()
        parcels = await self.get_state(ParcelsState)
        parcel_id = parcels.selected_parcel_id
        self.parcel_label = parcels.parcel_detail.get("name", "—")
        if parcel_id == 0:
            self.crop_options = []
            self.selected_crop_id = 0
            self._reset_view()
            self.is_loading = False
            return
        await self._load_crops(parcel_id)
        await self._refresh()
        self.is_loading = False

    @rx.event
    async def select_crop(self, value: str):
        raw = str(value).strip()
        self.selected_crop_id = int(raw) if raw.isdigit() else 0
        self.form_error = ""
        self.form_errors = []
        self.is_loading = True
        yield
        await self._refresh()
        self.is_loading = False

    @rx.event
    async def submit_observation(self, form_data: dict):
        self.form_error = ""
        self.form_errors = []
        if self.selected_crop_id == 0:
            self.form_error = "Sélectionnez d'abord une culture."
            return

        stage_label = str(form_data.get("stage", "")).strip()
        observer = str(form_data.get("observer", "")).strip()
        observed_on = _to_date(form_data.get("observed_on"))
        observed_time = str(form_data.get("observed_at_time", "")).strip()
        status = str(form_data.get("status", STATUS_CONFIRME)).strip()
        if status not in STATUS_FORM_KEYS:
            status = STATUS_CONFIRME

        check = await validate_observation(
            crop_id=self.selected_crop_id,
            stage_label=stage_label,
            observed_on=observed_on,
            observer=observer,
        )
        if not check["valid"]:
            errors = [str(item) for item in check["errors"]]
            self.form_errors = errors
            self.form_error = errors[0] if errors else "Observation invalide."
            return

        stage_id = int(check["stage_id"])
        params = {
            "crop_id": self.selected_crop_id,
            "profile_id": int(check["profile_id"]),
            "stage_id": stage_id,
            "observed_on": observed_on or datetime.date.today(),
            "observed_at_time": observed_time,
            "observer": observer,
            "status": status,
            "vigour": str(form_data.get("vigour", "")).strip(),
            "homogeneity": str(form_data.get("homogeneity", "")).strip(),
            "anomalies": str(form_data.get("anomalies", "")).strip(),
            "diseases": str(form_data.get("diseases_observed", "")).strip(),
            "pests": str(form_data.get("pests_observed", "")).strip(),
            "water_stress": bool(form_data.get("water_stress")),
            "thermal_stress": bool(form_data.get("thermal_stress")),
            "comment": str(form_data.get("comment", "")).strip(),
            "progress": int(check["progress"]),
        }

        async with rx.asession() as asession:
            crop = (
                await asession.execute(
                    text(
                        """
                        SELECT c.parcel_id, COALESCE(c.season, '')
                        FROM crop c WHERE c.id = :cid
                        """
                    ),
                    {"cid": self.selected_crop_id},
                )
            ).first()
            previous_stage_id = (
                await asession.execute(
                    text(
                        """
                        SELECT stage_id FROM crop_stage_observation
                        WHERE crop_id = :cid
                        ORDER BY observed_on DESC, id DESC LIMIT 1
                        """
                    ),
                    {"cid": self.selected_crop_id},
                )
            ).scalar()

            params["parcel_id"] = int(crop[0]) if crop else 0
            params["season"] = str(crop[1]) if crop else ""

            observation_id = int(
                (
                    await asession.execute(
                        text(
                            """
                            INSERT INTO crop_stage_observation (
                                crop_id, parcel_id, profile_id, stage_id, season,
                                observed_on, observed_at_time, observer, status,
                                source, vigour, homogeneity, anomalies,
                                diseases_observed, pests_observed, water_stress,
                                thermal_stress, comment, progress_percent
                            ) VALUES (
                                :crop_id, :parcel_id, :profile_id, :stage_id, :season,
                                :observed_on, :observed_at_time, :observer, :status,
                                'HUMAINE', :vigour, :homogeneity, :anomalies,
                                :diseases, :pests, :water_stress,
                                :thermal_stress, :comment, :progress
                            ) RETURNING id
                            """
                        ),
                        params,
                    )
                ).scalar()
                or 0
            )
            # Historique : jamais purgé, l'ancien stade est conservé.
            await asession.execute(
                text(
                    """
                    INSERT INTO crop_stage_change (
                        crop_id, observation_id, previous_stage_id,
                        new_stage_id, changed_on, author, comment
                    ) VALUES (
                        :crop_id, :observation_id, :previous_stage_id,
                        :new_stage_id, :changed_on, :author, :comment
                    )
                    """
                ),
                {
                    "crop_id": self.selected_crop_id,
                    "observation_id": observation_id,
                    "previous_stage_id": int(previous_stage_id)
                    if previous_stage_id
                    else None,
                    "new_stage_id": stage_id,
                    "changed_on": params["observed_on"],
                    "author": observer,
                    "comment": params["comment"],
                },
            )
            await asession.commit()

        self.form_key += 1
        await self._refresh()
        return rx.toast(
            f"Observation « {check['stage_name']} » enregistrée.",
            duration=4000,
        )

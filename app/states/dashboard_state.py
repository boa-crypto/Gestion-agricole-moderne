"""État du tableau de bord de pilotage végétal.

Toutes les lectures se font en SQL brut via `rx.asession()`.
La météo agricole est simulée de façon déterministe côté serveur.
"""

from __future__ import annotations

import datetime
import random
from typing import TypedDict

import reflex as rx
from sqlalchemy import text

from app.date_utils import as_date
from app.seed import seed_dashboard_data

PARCEL_STATUS_LABELS: dict[str, str] = {
    "EN_CULTURE": "En culture",
    "JACHERE": "Jachère",
    "PREPARATION": "Préparation",
    "RECOLTEE": "Récoltée",
    "INACTIVE": "Inactive",
}

SOIL_LABELS: dict[str, str] = {
    "ARGILEUX": "Argileux",
    "LIMONEUX": "Limoneux",
    "SABLEUX": "Sableux",
    "ARGILO_CALCAIRE": "Argilo-calcaire",
    "LIMONO_SABLEUX": "Limono-sableux",
    "HUMIFERE": "Humifère",
    "AUTRE": "Autre",
}

IRRIGATION_LABELS: dict[str, str] = {
    "AUCUNE": "Sans irrigation",
    "ASPERSION": "Aspersion",
    "GOUTTE_A_GOUTTE": "Goutte-à-goutte",
    "PIVOT": "Pivot",
    "GRAVITAIRE": "Gravitaire",
}

STAGE_LABELS: dict[str, str] = {
    "SEMIS": "Semis",
    "LEVEE": "Levée",
    "TALLAGE": "Tallage",
    "CROISSANCE": "Croissance",
    "FLORAISON": "Floraison",
    "FRUCTIFICATION": "Fructification",
    "MATURATION": "Maturation",
    "RECOLTE": "Récolte",
    "TERMINEE": "Terminée",
}

CROP_STATUS_LABELS: dict[str, str] = {
    "PLANIFIEE": "Planifiée",
    "EN_COURS": "En cours",
    "RECOLTEE": "Récoltée",
    "ABANDONNEE": "Abandonnée",
}

HEALTH_LABELS: dict[str, str] = {
    "EXCELLENT": "Excellent",
    "BON": "Bon",
    "MOYEN": "Moyen",
    "FAIBLE": "Faible",
    "CRITIQUE": "Critique",
}

HEALTH_TONES: dict[str, str] = {
    "EXCELLENT": "good",
    "BON": "good",
    "MOYEN": "warn",
    "FAIBLE": "warn",
    "CRITIQUE": "bad",
}

INTERVENTION_LABELS: dict[str, str] = {
    "SEMIS": "Semis",
    "PLANTATION": "Plantation",
    "FERTILISATION": "Fertilisation",
    "TRAITEMENT_PHYTO": "Traitement",
    "DESHERBAGE": "Désherbage",
    "IRRIGATION": "Irrigation",
    "TRAVAIL_DU_SOL": "Travail du sol",
    "OBSERVATION": "Observation",
    "RECOLTE": "Récolte",
    "AUTRE": "Autre",
}

INTERVENTION_STATUS_LABELS: dict[str, str] = {
    "PLANIFIEE": "Planifiée",
    "EN_COURS": "En cours",
    "REALISEE": "Réalisée",
    "ANNULEE": "Annulée",
    "REPORTEE": "Reportée",
}

WEEKDAYS_SHORT: list[str] = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]
MONTHS: list[str] = [
    "janv.",
    "févr.",
    "mars",
    "avr.",
    "mai",
    "juin",
    "juil.",
    "août",
    "sept.",
    "oct.",
    "nov.",
    "déc.",
]

WEATHER_KINDS: list[tuple[str, str]] = [
    ("sun", "Ensoleillé"),
    ("cloud-sun", "Voilé"),
    ("cloud", "Nuageux"),
    ("cloud-rain", "Averses"),
    ("cloud-lightning", "Orageux"),
]


class ParcelTile(TypedDict):
    id: int
    name: str
    code: str
    area_ha: float
    status: str
    status_label: str
    soil_label: str
    irrigation_label: str
    is_organic: bool
    crop_name: str
    health_label: str
    health_tone: str
    progress: int
    progress_pct: str
    left: str
    top: str
    width: str
    height: str
    fill: str
    stroke: str
    color: str


class CropCard(TypedDict):
    id: int
    name: str
    species: str
    parcel: str
    stage_label: str
    status_label: str
    health_label: str
    health_tone: str
    area_ha: float
    progress: int
    progress_pct: str
    sowing_label: str
    harvest_label: str
    days_left: int
    color: str


class AlertItem(TypedDict):
    id: int
    level: str
    title: str
    message: str
    category: str
    parcel: str
    date_label: str


class InterventionItem(TypedDict):
    id: int
    title: str
    type: str
    type_label: str
    status_label: str
    date_label: str
    parcel: str
    operator: str
    equipment: str
    target: str
    area_ha: float
    days_from_now: int


class CalendarDay(TypedDict):
    iso: str
    num: str
    weekday: str
    count: int
    tone: str


class WeatherDay(TypedDict):
    day: str
    date_label: str
    kind: str
    label: str
    tmax: float
    tmin: float
    rain: float
    wind: float
    humidity: float
    spray: bool


class SpeciesArea(TypedDict):
    species: str
    area_ha: float
    share: str
    color: str


EMPTY_TILE: ParcelTile = {
    "id": 0,
    "name": "—",
    "code": "",
    "area_ha": 0.0,
    "status": "INACTIVE",
    "status_label": "—",
    "soil_label": "—",
    "irrigation_label": "—",
    "is_organic": False,
    "crop_name": "Aucune culture",
    "health_label": "—",
    "health_tone": "good",
    "progress": 0,
    "progress_pct": "0%",
    "left": "0%",
    "top": "0%",
    "width": "0%",
    "height": "0%",
    "fill": "#22c55e26",
    "stroke": "#22c55e",
    "color": "#22c55e",
}


def _fmt_date(value: object) -> str:
    day = as_date(value)
    if day is None:
        return "—"
    return f"{day.day} {MONTHS[day.month - 1]}"


def _generate_weather(
    today: datetime.date,
) -> tuple[list[WeatherDay], dict[str, str]]:
    """Météo agricole simulée, déterministe pour une journée donnée."""
    rnd = random.Random(today.toordinal())
    days: list[WeatherDay] = []
    base = rnd.uniform(20.0, 26.0)
    for offset in range(7):
        day_date = today + datetime.timedelta(days=offset)
        kind, label = WEATHER_KINDS[rnd.randrange(len(WEATHER_KINDS))]
        tmax = round(base + rnd.uniform(-4.0, 5.0), 1)
        tmin = round(tmax - rnd.uniform(7.0, 12.0), 1)
        rain = 0.0
        if kind == "cloud-rain":
            rain = round(rnd.uniform(2.0, 11.0), 1)
        elif kind == "cloud-lightning":
            rain = round(rnd.uniform(8.0, 24.0), 1)
        elif kind == "cloud":
            rain = round(rnd.uniform(0.0, 1.6), 1)
        wind = round(rnd.uniform(4.0, 26.0), 1)
        humidity = round(rnd.uniform(48.0, 88.0), 1)
        days.append(
            {
                "day": WEEKDAYS_SHORT[day_date.weekday()],
                "date_label": _fmt_date(day_date),
                "kind": kind,
                "label": label,
                "tmax": tmax,
                "tmin": tmin,
                "rain": rain,
                "wind": wind,
                "humidity": humidity,
                "spray": wind < 19.0 and rain < 2.0,
            }
        )

    first = days[0]
    et0 = round(
        0.0023
        * (first["tmax"] - first["tmin"]) ** 0.5
        * (first["tmax"] + 17.8)
        * 0.4,
        2,
    )
    soil = round(
        max(12.0, min(96.0, 100.0 - first["tmax"] * 1.6 + first["rain"] * 3.2)),
        0,
    )
    gdd = round(max(0.0, (first["tmax"] + first["tmin"]) / 2 - 6.0), 1)
    spray_ok = first["spray"]
    now: dict[str, str] = {
        "kind": first["kind"],
        "label": first["label"],
        "temp": f"{first['tmax']:.1f}",
        "tmin": f"{first['tmin']:.1f}",
        "humidity": f"{first['humidity']:.0f}",
        "wind": f"{first['wind']:.0f}",
        "rain": f"{first['rain']:.1f}",
        "et0": f"{et0:.2f}",
        "soil": f"{soil:.0f}",
        "gdd": f"{gdd:.1f}",
        "rain_week": f"{sum(d['rain'] for d in days):.1f}",
        "spray_label": "Fenêtre de traitement ouverte"
        if spray_ok
        else "Fenêtre de traitement fermée",
        "spray_tone": "good" if spray_ok else "bad",
        "date_label": f"{WEEKDAYS_SHORT[today.weekday()]}. {_fmt_date(today)}",
    }
    return days, now


class DashboardState(rx.State):
    """Données agrégées du cockpit agronomique."""

    is_loading: bool = True
    today_label: str = ""
    season_label: str = ""

    kpis: dict[str, float] = {
        "parcels": 0.0,
        "area_total": 0.0,
        "active_crops": 0.0,
        "area_active": 0.0,
        "alerts": 0.0,
        "planned": 0.0,
        "harvest_qty": 0.0,
        "revenue": 0.0,
        "progress": 0.0,
        "organic_area": 0.0,
    }

    parcels: list[ParcelTile] = []
    selected_parcel_id: int = 0
    crops: list[CropCard] = []
    alerts: list[AlertItem] = []
    interventions: list[InterventionItem] = []
    calendar_days: list[CalendarDay] = []
    weather_days: list[WeatherDay] = []
    weather_now: dict[str, str] = {
        "kind": "sun",
        "label": "—",
        "temp": "0.0",
        "tmin": "0.0",
        "humidity": "0",
        "wind": "0",
        "rain": "0.0",
        "et0": "0.00",
        "soil": "0",
        "gdd": "0.0",
        "rain_week": "0.0",
        "spray_label": "—",
        "spray_tone": "good",
        "date_label": "—",
    }
    species_mix: list[SpeciesArea] = []
    weekday_headers: list[str] = [
        "lun",
        "mar",
        "mer",
        "jeu",
        "ven",
        "sam",
        "dim",
    ]

    @rx.var
    def selected_parcel(self) -> ParcelTile:
        for tile in self.parcels:
            if tile["id"] == self.selected_parcel_id:
                return tile
        if self.parcels:
            return self.parcels[0]
        return EMPTY_TILE

    @rx.var
    def critical_alerts(self) -> int:
        return len([a for a in self.alerts if a["level"] == "CRITIQUE"])

    @rx.event
    def select_parcel(self, parcel_id: int):
        self.selected_parcel_id = parcel_id

    @rx.event(background=True)
    async def load_dashboard(self):
        async with self:
            self.is_loading = True

        await seed_dashboard_data()

        today = datetime.date.today()
        horizon = today + datetime.timedelta(days=7)
        cal_start = today - datetime.timedelta(days=today.weekday())
        cal_end = cal_start + datetime.timedelta(days=20)

        async with rx.asession() as asession:
            kpi_row = (
                await asession.execute(
                    text(
                        """
                        SELECT
                            (SELECT COUNT(*) FROM parcel),
                            (SELECT COALESCE(SUM(area_ha), 0) FROM parcel),
                            (SELECT COUNT(*) FROM crop WHERE status = 'EN_COURS'),
                            (SELECT COALESCE(SUM(area_ha), 0) FROM crop WHERE status = 'EN_COURS'),
                            (SELECT COUNT(*) FROM alert WHERE is_resolved = false),
                            (SELECT COUNT(*) FROM intervention
                                WHERE status IN ('PLANIFIEE', 'EN_COURS', 'REPORTEE')
                                AND scheduled_date BETWEEN :today AND :horizon),
                            (SELECT COALESCE(SUM(quantity), 0) FROM harvest),
                            (SELECT COALESCE(SUM(revenue), 0) FROM harvest),
                            (SELECT COALESCE(AVG(progress_percent), 0) FROM crop WHERE status = 'EN_COURS'),
                            (SELECT COALESCE(SUM(area_ha), 0) FROM parcel WHERE is_organic = true)
                        """
                    ),
                    {"today": today, "horizon": horizon},
                )
            ).first()

            parcel_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT p.id, p.name, p.code, COALESCE(p.area_ha, 0), p.status,
                               p.is_organic, p.soil_type, p.irrigation,
                               COALESCE(p.map_x, 0), COALESCE(p.map_y, 0),
                               COALESCE(p.map_w, 0), COALESCE(p.map_h, 0),
                               c.name, c.health, COALESCE(c.progress_percent, 0),
                               COALESCE(v.color_hex, '#4ade80')
                        FROM parcel p
                        LEFT JOIN crop c ON c.parcel_id = p.id AND c.status = 'EN_COURS'
                        LEFT JOIN crop_variety v ON v.id = c.variety_id
                        ORDER BY p.code
                        """
                    )
                )
            ).all()

            crop_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT c.id, c.name, COALESCE(v.species, ''), p.name, c.stage, c.status,
                               c.health, COALESCE(c.area_ha, 0), COALESCE(c.progress_percent, 0),
                               c.sowing_date, c.expected_harvest_date,
                               COALESCE(v.color_hex, '#4ade80')
                        FROM crop c
                        JOIN parcel p ON p.id = c.parcel_id
                        LEFT JOIN crop_variety v ON v.id = c.variety_id
                        WHERE c.status IN ('EN_COURS', 'PLANIFIEE')
                        ORDER BY c.expected_harvest_date NULLS LAST
                        LIMIT 8
                        """
                    )
                )
            ).all()

            alert_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT a.id, a.level, a.title, a.message, a.category,
                               COALESCE(p.name, 'Exploitation'), a.triggered_on
                        FROM alert a
                        LEFT JOIN parcel p ON p.id = a.parcel_id
                        WHERE a.is_resolved = false
                        ORDER BY
                            CASE a.level
                                WHEN 'CRITIQUE' THEN 1
                                WHEN 'ATTENTION' THEN 2
                                ELSE 3
                            END,
                            a.triggered_on DESC
                        LIMIT 6
                        """
                    )
                )
            ).all()

            intervention_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT i.id, i.title, i.type, i.status, i.scheduled_date, p.name,
                               COALESCE(i.operator, ''), COALESCE(i.equipment, ''),
                               COALESCE(i.target, ''), COALESCE(i.area_treated_ha, 0)
                        FROM intervention i
                        JOIN parcel p ON p.id = i.parcel_id
                        WHERE i.scheduled_date >= :today
                          AND i.status IN ('PLANIFIEE', 'EN_COURS', 'REPORTEE')
                        ORDER BY i.scheduled_date
                        LIMIT 7
                        """
                    ),
                    {"today": today},
                )
            ).all()

            calendar_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT scheduled_date, COUNT(*)
                        FROM intervention
                        WHERE scheduled_date BETWEEN :start AND :end
                        GROUP BY scheduled_date
                        """
                    ),
                    {"start": cal_start, "end": cal_end},
                )
            ).all()

            species_rows = (
                await asession.execute(
                    text(
                        """
                        SELECT COALESCE(v.species, c.name) AS species,
                               COALESCE(SUM(c.area_ha), 0) AS area_ha,
                               MIN(COALESCE(v.color_hex, '#4ade80')) AS color
                        FROM crop c
                        LEFT JOIN crop_variety v ON v.id = c.variety_id
                        WHERE c.status = 'EN_COURS'
                        GROUP BY COALESCE(v.species, c.name)
                        ORDER BY area_ha DESC
                        LIMIT 6
                        """
                    )
                )
            ).all()

        parcels: list[ParcelTile] = []
        for row in parcel_rows:
            status = str(row[4])
            health = str(row[13]) if row[13] is not None else "BON"
            color = str(row[15])
            progress = int(row[14] or 0)
            parcels.append(
                {
                    "id": int(row[0]),
                    "name": str(row[1]),
                    "code": str(row[2]),
                    "area_ha": float(row[3]),
                    "status": status,
                    "status_label": PARCEL_STATUS_LABELS.get(status, status),
                    "soil_label": SOIL_LABELS.get(row[6], row[6]),
                    "irrigation_label": IRRIGATION_LABELS.get(row[7], row[7]),
                    "is_organic": bool(row[5]),
                    "crop_name": str(row[12])
                    if row[12]
                    else "Sans culture active",
                    "health_label": HEALTH_LABELS.get(health, health),
                    "health_tone": HEALTH_TONES.get(health, "good"),
                    "progress": progress,
                    "progress_pct": f"{progress}%",
                    "left": f"{float(row[8]):.2f}%",
                    "top": f"{float(row[9]):.2f}%",
                    "width": f"{float(row[10]):.2f}%",
                    "height": f"{float(row[11]):.2f}%",
                    "fill": f"{color}26",
                    "stroke": color,
                    "color": color,
                }
            )

        crops: list[CropCard] = []
        for row in crop_rows:
            stage = str(row[4])
            status = str(row[5])
            health = str(row[6])
            progress = int(row[8] or 0)
            harvest_date = as_date(row[10])
            days_left = (harvest_date - today).days if harvest_date else 0
            crops.append(
                {
                    "id": int(row[0]),
                    "name": str(row[1]),
                    "species": str(row[2]) or "Espèce non renseignée",
                    "parcel": str(row[3]),
                    "stage_label": STAGE_LABELS.get(stage, stage),
                    "status_label": CROP_STATUS_LABELS.get(status, status),
                    "health_label": HEALTH_LABELS.get(health, health),
                    "health_tone": HEALTH_TONES.get(health, "good"),
                    "area_ha": float(row[7]),
                    "progress": progress,
                    "progress_pct": f"{progress}%",
                    "sowing_label": _fmt_date(row[9]),
                    "harvest_label": _fmt_date(harvest_date),
                    "days_left": days_left,
                    "color": str(row[11]),
                }
            )

        alerts: list[AlertItem] = [
            {
                "id": int(row[0]),
                "level": str(row[1]),
                "title": str(row[2]),
                "message": str(row[3]),
                "category": str(row[4]),
                "parcel": str(row[5]),
                "date_label": _fmt_date(row[6]),
            }
            for row in alert_rows
        ]

        interventions: list[InterventionItem] = []
        for row in intervention_rows:
            i_type = str(row[2])
            i_status = str(row[3])
            scheduled = as_date(row[4])
            interventions.append(
                {
                    "id": int(row[0]),
                    "title": str(row[1]),
                    "type": i_type,
                    "type_label": INTERVENTION_LABELS.get(i_type, i_type),
                    "status_label": INTERVENTION_STATUS_LABELS.get(
                        i_status, i_status
                    ),
                    "date_label": _fmt_date(scheduled),
                    "parcel": str(row[5]),
                    "operator": str(row[6]),
                    "equipment": str(row[7]),
                    "target": str(row[8]),
                    "area_ha": float(row[9]),
                    "days_from_now": (scheduled - today).days
                    if scheduled
                    else 0,
                }
            )

        counts: dict[datetime.date, int] = {}
        for row in calendar_rows:
            day_key = as_date(row[0])
            if day_key is not None:
                counts[day_key] = int(row[1] or 0)
        calendar_days: list[CalendarDay] = []
        for offset in range(21):
            day = cal_start + datetime.timedelta(days=offset)
            if day == today:
                tone = "today"
            elif day < today:
                tone = "past"
            else:
                tone = "future"
            calendar_days.append(
                {
                    "iso": day.isoformat(),
                    "num": f"{day.day:02d}",
                    "weekday": WEEKDAYS_SHORT[day.weekday()],
                    "count": counts.get(day, 0),
                    "tone": tone,
                }
            )

        total_species_area = sum(float(row[1]) for row in species_rows) or 1.0
        species_mix: list[SpeciesArea] = [
            {
                "species": str(row[0]),
                "area_ha": float(row[1]),
                "share": f"{float(row[1]) / total_species_area * 100:.0f}%",
                "color": str(row[2]),
            }
            for row in species_rows
        ]

        weather_days, weather_now = _generate_weather(today)

        async with self:
            self.kpis = {
                "parcels": float(kpi_row[0] or 0) if kpi_row else 0.0,
                "area_total": float(kpi_row[1] or 0) if kpi_row else 0.0,
                "active_crops": float(kpi_row[2] or 0) if kpi_row else 0.0,
                "area_active": float(kpi_row[3] or 0) if kpi_row else 0.0,
                "alerts": float(kpi_row[4] or 0) if kpi_row else 0.0,
                "planned": float(kpi_row[5] or 0) if kpi_row else 0.0,
                "harvest_qty": float(kpi_row[6] or 0) if kpi_row else 0.0,
                "revenue": float(kpi_row[7] or 0) if kpi_row else 0.0,
                "progress": float(kpi_row[8] or 0) if kpi_row else 0.0,
                "organic_area": float(kpi_row[9] or 0) if kpi_row else 0.0,
            }
            self.parcels = parcels
            if parcels and self.selected_parcel_id == 0:
                self.selected_parcel_id = parcels[0]["id"]
            self.crops = crops
            self.alerts = alerts
            self.interventions = interventions
            self.calendar_days = calendar_days
            self.species_mix = species_mix
            self.weather_days = weather_days
            self.weather_now = weather_now
            self.today_label = (
                f"{WEEKDAYS_SHORT[today.weekday()]}. {today.day} "
                f"{MONTHS[today.month - 1]} {today.year}"
            )
            self.season_label = f"Campagne {today.year}"
            self.is_loading = False

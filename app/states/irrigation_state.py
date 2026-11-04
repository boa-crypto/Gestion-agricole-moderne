import reflex as rx

import asyncio
import datetime as dt
import logging
from typing import TypedDict

from sqlalchemy import text

from app.catalog_reference import WATER_LABELS
from app.database import ensure_local_database
from app.irrigation import (
    EMPTY_RECOMMENDATION,
    IrrigationInput,
    WaterDay,
    calculate_recommendation,
    exclusion,
    forecast_days,
)
from app.server_guard import require_service
from app.states.weather_state import farm_coordinates, fetch_forecast


class IrrigationCard(TypedDict):
    key: str
    parcel_id: int
    parcel: str
    crop: str
    area: str
    system: str
    position: str
    source: str
    recommendation: dict[str, str]
    days: list[WaterDay]


IRRIGATION_SQL = """
SELECT p.id AS parcel_id, p.name AS parcel, COALESCE(p.area_ha,0) AS parcel_area,
       COALESCE(p.latitude,0) AS latitude, COALESCE(p.longitude,0) AS longitude,
       p.irrigation, COALESCE(c.id,0) AS crop_id, COALESCE(c.name,'') AS crop,
       COALESCE(c.status,'') AS status, COALESCE(c.stage,'') AS fallback_stage,
       COALESCE(c.area_ha,0) AS crop_area, COALESCE(cu.id,0) AS linked,
       COALESCE(cu.water_need,'') AS water_need, COALESCE(s.water_requirement_mm,0) AS requirement,
       COALESCE(ps.name,'') AS stage, COALESCE(o.observed_on,'') AS observed_on,
       COALESCE(ps.position,0) AS position, COALESCE(ps.is_critical,0) AS critical,
       COALESCE(o.water_stress,0) AS stress,
       COALESCE((SELECT MIN(position) FROM crop_phenology_stage WHERE profile_id=ps.profile_id),0) AS min_position,
       COALESCE((SELECT MAX(position) FROM crop_phenology_stage WHERE profile_id=ps.profile_id),0) AS max_position,
       COALESCE((SELECT SUM(i.water_volume_l_ha / 10000.0 *
          MIN(i.area_treated_ha, CASE WHEN c.area_ha>0 THEN c.area_ha ELSE p.area_ha END) /
          NULLIF(CASE WHEN c.area_ha>0 THEN c.area_ha ELSE p.area_ha END,0))
          FROM intervention i WHERE i.parcel_id=p.id AND i.crop_id=c.id
          AND i.type='IRRIGATION' AND i.status='REALISEE'
          AND i.done_date BETWEEN :recent_start AND :today
          AND i.water_volume_l_ha>0 AND i.area_treated_ha>0),0) AS recent_mm,
       COALESCE((SELECT MAX(i.done_date) FROM intervention i
          WHERE i.parcel_id=p.id AND i.crop_id=c.id AND i.type='IRRIGATION'
          AND i.status='REALISEE' AND i.done_date<=:today),'') AS last_water,
       (SELECT COUNT(*) FROM intervention i WHERE i.parcel_id=p.id
          AND (i.crop_id=c.id OR i.crop_id IS NULL)
          AND i.type='IRRIGATION' AND i.status='REALISEE'
          AND i.done_date BETWEEN :recent_start AND :today
          AND (i.crop_id IS NULL OR COALESCE(i.water_volume_l_ha,0)<=0 OR COALESCE(i.area_treated_ha,0)<=0)) AS unknown_water
FROM parcel p
LEFT JOIN crop c ON c.parcel_id=p.id AND c.status IN ('EN_COURS','PLANIFIEE')
LEFT JOIN crop_catalog_variety v ON v.id=(SELECT MIN(v2.id) FROM crop_catalog_variety v2 WHERE v2.crop_variety_id=c.variety_id)
LEFT JOIN crop_species s ON s.id=v.species_id
LEFT JOIN crop_culture cu ON cu.id=s.culture_id
LEFT JOIN crop_stage_observation o ON o.id=(SELECT o2.id FROM crop_stage_observation o2
    WHERE o2.crop_id=c.id AND o2.observed_on<=:today
    ORDER BY o2.observed_on DESC, o2.id DESC LIMIT 1)
LEFT JOIN crop_phenology_stage ps ON ps.id=o.stage_id
ORDER BY p.name, p.id, c.status, c.id
LIMIT 201
"""


async def location_forecasts(
    locations: set[tuple[float, float]],
) -> dict[tuple[float, float], tuple[list[WaterDay], str]]:
    semaphore = asyncio.Semaphore(3)

    async def fetch(
        location: tuple[float, float],
    ) -> tuple[tuple[float, float], list[WaterDay], str]:
        async with semaphore:
            try:
                raw = await asyncio.to_thread(fetch_forecast, *location)
                offset = int(raw.get("utc_offset_seconds", 0) or 0)
                now = dt.datetime.now(dt.UTC)
                today = (now + dt.timedelta(seconds=offset)).date()
                days = forecast_days(raw, today)
                source = f"Open-Meteo · prévisions réelles · récupérées le {now.strftime('%d/%m/%Y à %H:%M UTC')} · {raw.get('timezone', 'heure locale')}"
                return location, days, source
            except Exception as e:
                logging.exception(f"Error: {e}")
                return (
                    location,
                    [],
                    "Open-Meteo indisponible ou prévisions incomplètes — aucune météo de substitution.",
                )

    results = await asyncio.gather(
        *(fetch(location) for location in sorted(locations))
    )
    return {location: (days, source) for location, days, source in results}


class IrrigationState(rx.State):
    is_loading: bool = False
    error: str = ""
    notice: str = ""
    selected_parcel: str = "all"
    cards: list[IrrigationCard] = []
    _generation: int = 0

    @rx.var
    def parcel_options(self) -> list[dict[str, str]]:
        return [
            {"id": str(pid), "name": name}
            for pid, name in dict(
                (card["parcel_id"], card["parcel"]) for card in self.cards
            ).items()
        ]

    @rx.var
    def visible_cards(self) -> list[IrrigationCard]:
        return [
            card
            for card in self.cards
            if self.selected_parcel == "all"
            or str(card["parcel_id"]) == self.selected_parcel
        ]

    @rx.event
    def select_parcel(self, value: str):
        if value == "all" or value in {
            str(card["parcel_id"]) for card in self.cards
        }:
            self.selected_parcel = value

    @rx.event(background=True)
    async def load_irrigation(self):
        await require_service(("irrigation", "CONSULTER"))
        async with self:
            if self.is_loading:
                return
            self._generation += 1
            generation = self._generation
            self.is_loading = True
            self.error = ""
            self.cards = []
            self.notice = ""
        try:
            await ensure_local_database()
            today = dt.date.today()
            async with rx.asession() as session:
                rows = (
                    (
                        await session.execute(
                            text(IRRIGATION_SQL),
                            {
                                "today": today.isoformat(),
                                "recent_start": (
                                    today - dt.timedelta(days=6)
                                ).isoformat(),
                            },
                        )
                    )
                    .mappings()
                    .all()
                )
            truncated = len(rows) > 200
            rows = rows[:200]
            farm = (
                await farm_coordinates()
                if any(
                    not row["latitude"] or not row["longitude"] for row in rows
                )
                else (0.0, 0.0)
            )
            inputs: list[
                tuple[IrrigationCard, IrrigationInput, tuple[float, float]]
            ] = []
            locations: set[tuple[float, float]] = set()
            for row in rows:
                area = (
                    float(row["crop_area"])
                    if row["crop_area"] > 0
                    else float(row["parcel_area"])
                )
                position_range = int(row["max_position"]) - int(
                    row["min_position"]
                )
                data: IrrigationInput = {
                    "crop_id": int(row["crop_id"]),
                    "status": str(row["status"]),
                    "linked": bool(row["linked"]),
                    "irrigation": str(row["irrigation"]),
                    "area": area,
                    "water_need": str(row["water_need"]),
                    "requirement": float(row["requirement"]),
                    "stage": str(row["stage"] or row["fallback_stage"]),
                    "observed_on": str(row["observed_on"])
                    if row["stage"]
                    else "",
                    "progression": (
                        int(row["position"]) - int(row["min_position"])
                    )
                    / position_range
                    if position_range > 0
                    else 0.5,
                    "critical": bool(row["critical"]),
                    "stress": bool(row["stress"]),
                    "recent_mm": float(row["recent_mm"]),
                    "last_water": str(row["last_water"]),
                    "unknown_water": int(row["unknown_water"]),
                }
                missing = not row["latitude"] or not row["longitude"]
                lat, lon = (
                    farm
                    if missing
                    else (float(row["latitude"]), float(row["longitude"]))
                )
                position = f"{'Exploitation (coordonnées parcellaires manquantes)' if missing else 'Parcelle'} · {lat:.5f}°, {lon:.5f}°"
                reason = exclusion(data)
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    reason = (
                        reason
                        or "Coordonnées parcellaires invalides : aucune substitution météo."
                    )
                card: IrrigationCard = {
                    "key": f"{row['parcel_id']}-{row['crop_id']}",
                    "parcel_id": int(row["parcel_id"]),
                    "parcel": str(row["parcel"]),
                    "crop": str(row["crop"]) or "Sans culture active",
                    "area": f"{area:.2f} ha · {'surface culture' if row['crop_area'] > 0 else 'surface parcelle utilisée par défaut'}",
                    "system": str(row["irrigation"]).replace("_", " ").lower(),
                    "position": position,
                    "source": "",
                    "recommendation": dict(EMPTY_RECOMMENDATION),
                    "days": [],
                }
                card["recommendation"]["message"] = reason
                card["recommendation"]["water_need"] = WATER_LABELS.get(
                    data["water_need"],
                    "Besoin inconnu — hypothèse modérée pour culture reliée"
                    if data["linked"]
                    else "Référentiel hydrique non relié",
                )
                card["recommendation"]["phenology"] = (
                    f"{data['stage'] or 'Stade non renseigné'} · {data['observed_on'] or 'sans observation datée (stade déclaré)'}"
                )
                if not reason:
                    locations.add((lat, lon))
                inputs.append((card, data, (lat, lon)))
            forecasts = await location_forecasts(locations)
            cards: list[IrrigationCard] = []
            for card, data, location in inputs:
                if not card["recommendation"]["message"]:
                    days, source = forecasts[location]
                    card["source"] = source
                    if days:
                        card["recommendation"] = calculate_recommendation(
                            data, days, dt.date.fromisoformat(days[0]["date"])
                        )
                        card["days"] = days
                    else:
                        card["recommendation"]["status"] = "unavailable"
                        card["recommendation"]["message"] = (
                            "Météo indisponible : ni dose, ni volume, ni date recommandés. Actualisez pour réessayer."
                        )
                cards.append(card)
            await require_service(("irrigation", "CONSULTER"))
            async with self:
                if self._generation != generation:
                    return
                self.cards = cards
                if self.selected_parcel not in {
                    str(card["parcel_id"]) for card in cards
                }:
                    self.selected_parcel = "all"
                self.notice = (
                    "Affichage limité aux 200 premières cultures/parcelles, classées par nom."
                    if truncated
                    else ""
                )
                self.is_loading = False
        except PermissionError:
            async with self:
                self.cards = []
                self.is_loading = False
            raise
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                if self._generation == generation:
                    self.error = "Données agricoles indisponibles : aucun calcul effectué. Réessayez avec Actualiser."
                    self.cards = []
                    self.is_loading = False

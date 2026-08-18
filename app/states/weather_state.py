"""État météo réelle (Open-Meteo, sans clé API).

Prévisions journalières 15 jours + prévisions horaires du jour pour la
position du navigateur, avec repli automatique sur la position de
l'exploitation, et repli final sur la météo simulée si l'API est
indisponible.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
from typing import TypedDict

import reflex as rx
import requests
from sqlalchemy import text

from app.database import (
    ensure_local_database,
    local_table_exists,
    local_table_exists_async,
)
from app.states.dashboard_state import (
    MONTHS,
    WEEKDAYS_SHORT,
    _generate_weather,
)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

FARM_LATITUDE = 48.234512
FARM_LONGITUDE = 1.845233

GEO_SCRIPT = """
new Promise((resolve) => {
    if (!navigator.geolocation) {
        resolve({error: "Géolocalisation non supportée par ce navigateur"});
        return;
    }
    navigator.geolocation.getCurrentPosition(
        (position) => resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
        }),
        (error) => resolve({error: error.message || "Position refusée"}),
        {enableHighAccuracy: false, timeout: 9000, maximumAge: 300000}
    );
})
"""

WMO_LABELS: dict[int, str] = {
    0: "Ciel dégagé",
    1: "Peu nuageux",
    2: "Partiellement nuageux",
    3: "Couvert",
    45: "Brouillard",
    48: "Brouillard givrant",
    51: "Bruine faible",
    53: "Bruine modérée",
    55: "Bruine dense",
    56: "Bruine verglaçante",
    57: "Bruine verglaçante dense",
    61: "Pluie faible",
    63: "Pluie modérée",
    65: "Pluie forte",
    66: "Pluie verglaçante",
    67: "Pluie verglaçante forte",
    71: "Neige faible",
    73: "Neige modérée",
    75: "Neige forte",
    77: "Grains de neige",
    80: "Averses faibles",
    81: "Averses modérées",
    82: "Averses violentes",
    85: "Averses de neige",
    86: "Averses de neige fortes",
    95: "Orage",
    96: "Orage avec grêle",
    99: "Orage violent avec grêle",
}


class WeatherDaily(TypedDict):
    iso: str
    day: str
    date_label: str
    kind: str
    label: str
    tmax: float
    tmin: float
    rain: float
    rain_prob: float
    wind: float
    gust: float
    spray: bool
    is_today: bool


class WeatherHour(TypedDict):
    iso: str
    hour: str
    kind: str
    label: str
    temp: float
    rain: float
    humidity: float
    wind: float
    is_now: bool


EMPTY_CURRENT: dict[str, str] = {
    "kind": "sun",
    "label": "—",
    "temp": "0.0",
    "tmin": "0.0",
    "tmax": "0.0",
    "humidity": "0",
    "wind": "0",
    "gust": "0",
    "rain": "0.0",
    "et0": "0.00",
    "soil": "0",
    "gdd": "0.0",
    "rain_week": "0.0",
    "rain_prob": "0",
    "sunrise": "—",
    "sunset": "—",
    "spray_label": "—",
    "spray_tone": "good",
    "date_label": "—",
}


def wmo_label(code: int) -> str:
    return WMO_LABELS.get(int(code), "Conditions inconnues")


def wmo_icon(code: int) -> str:
    code = int(code)
    if code == 0:
        return "sun"
    if code in (1, 2):
        return "cloud-sun"
    if code == 3:
        return "cloud"
    if code in (45, 48):
        return "cloud-fog"
    if code in (71, 73, 75, 77, 85, 86):
        return "snowflake"
    if code in (95, 96, 99):
        return "cloud-lightning"
    if code in (51, 53, 55, 56, 57):
        return "cloud-drizzle"
    return "cloud-rain"


def fmt_day(value: datetime.date) -> str:
    return f"{value.day} {MONTHS[value.month - 1]}"


def parse_geolocation(
    result: dict[str, str | float] | None,
) -> tuple[float, float] | None:
    """Extrait des coordonnées valides du retour navigateur."""
    if not isinstance(result, dict):
        return None
    lat = result.get("latitude")
    lon = result.get("longitude")
    if lat is None or lon is None:
        return None
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError):
        return None
    if not (-90.0 <= lat_f <= 90.0 and -180.0 <= lon_f <= 180.0):
        return None
    return (lat_f, lon_f)


def fetch_forecast(latitude: float, longitude: float) -> dict:
    """Appel Open-Meteo (bloquant) : 15 jours + horaire."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": (
            "temperature_2m,relative_humidity_2m,precipitation,"
            "weather_code,wind_speed_10m,soil_moisture_0_to_7cm"
        ),
        "daily": (
            "weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_sum,precipitation_probability_max,"
            "wind_speed_10m_max,wind_gusts_10m_max,"
            "et0_fao_evapotranspiration,sunrise,sunset"
        ),
        "timezone": "auto",
        "forecast_days": 15,
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }
    response = requests.get(OPEN_METEO_URL, params=params, timeout=12)
    response.raise_for_status()
    return response.json()


def build_payload(
    data: dict,
) -> tuple[dict[str, str], list[WeatherDaily], list[WeatherHour], str]:
    """Transforme la réponse Open-Meteo en structures d'affichage."""
    offset = int(data.get("utc_offset_seconds", 0) or 0)
    now_local = datetime.datetime.now(datetime.timezone.utc) + (
        datetime.timedelta(seconds=offset)
    )
    today = now_local.date()

    daily_raw = data.get("daily", {})
    times: list[str] = list(daily_raw.get("time", []))
    days: list[WeatherDaily] = []
    for i, iso in enumerate(times):
        day_date = datetime.date.fromisoformat(iso)
        code = int(daily_raw["weather_code"][i] or 0)
        rain = float(daily_raw["precipitation_sum"][i] or 0.0)
        wind = float(daily_raw["wind_speed_10m_max"][i] or 0.0)
        gusts = daily_raw.get("wind_gusts_10m_max") or []
        probs = daily_raw.get("precipitation_probability_max") or []
        days.append(
            {
                "iso": iso,
                "day": WEEKDAYS_SHORT[day_date.weekday()],
                "date_label": fmt_day(day_date),
                "kind": wmo_icon(code),
                "label": wmo_label(code),
                "tmax": float(daily_raw["temperature_2m_max"][i] or 0.0),
                "tmin": float(daily_raw["temperature_2m_min"][i] or 0.0),
                "rain": rain,
                "rain_prob": float(probs[i] or 0.0) if i < len(probs) else 0.0,
                "wind": wind,
                "gust": float(gusts[i] or 0.0) if i < len(gusts) else 0.0,
                "spray": wind < 19.0 and rain < 2.0,
                "is_today": day_date == today,
            }
        )

    hourly_raw = data.get("hourly", {})
    hour_times: list[str] = list(hourly_raw.get("time", []))
    hours: list[WeatherHour] = []
    soil_values: list[float] = []
    for i, iso in enumerate(hour_times):
        stamp = datetime.datetime.fromisoformat(iso)
        if stamp.date() != today:
            continue
        code = int(hourly_raw["weather_code"][i] or 0)
        soils = hourly_raw.get("soil_moisture_0_to_7cm") or []
        if i < len(soils) and soils[i] is not None:
            soil_values.append(float(soils[i]))
        hours.append(
            {
                "iso": iso,
                "hour": f"{stamp.hour:02d}h",
                "kind": wmo_icon(code),
                "label": wmo_label(code),
                "temp": float(hourly_raw["temperature_2m"][i] or 0.0),
                "rain": float(hourly_raw["precipitation"][i] or 0.0),
                "humidity": float(hourly_raw["relative_humidity_2m"][i] or 0.0),
                "wind": float(hourly_raw["wind_speed_10m"][i] or 0.0),
                "is_now": stamp.hour == now_local.hour,
            }
        )

    current_hour = next(
        (h for h in hours if h["is_now"]), hours[0] if hours else None
    )
    first_day = days[0] if days else None
    et0_list = daily_raw.get("et0_fao_evapotranspiration") or []
    sunrise = daily_raw.get("sunrise") or []
    sunset = daily_raw.get("sunset") or []
    et0 = float(et0_list[0] or 0.0) if et0_list else 0.0
    soil_pct = (
        sum(soil_values) / len(soil_values) * 100.0 if soil_values else 0.0
    )
    tmax = first_day["tmax"] if first_day else 0.0
    tmin = first_day["tmin"] if first_day else 0.0
    gdd = max(0.0, (tmax + tmin) / 2 - 6.0)
    wind_now = current_hour["wind"] if current_hour else 0.0
    rain_now = first_day["rain"] if first_day else 0.0
    spray_ok = wind_now < 19.0 and rain_now < 2.0

    current: dict[str, str] = {
        "kind": current_hour["kind"] if current_hour else "sun",
        "label": current_hour["label"] if current_hour else "—",
        "temp": f"{current_hour['temp']:.1f}" if current_hour else "0.0",
        "tmin": f"{tmin:.1f}",
        "tmax": f"{tmax:.1f}",
        "humidity": f"{current_hour['humidity']:.0f}" if current_hour else "0",
        "wind": f"{wind_now:.0f}",
        "gust": f"{first_day['gust']:.0f}" if first_day else "0",
        "rain": f"{rain_now:.1f}",
        "et0": f"{et0:.2f}",
        "soil": f"{soil_pct:.0f}",
        "gdd": f"{gdd:.1f}",
        "rain_week": f"{sum(d['rain'] for d in days[:7]):.1f}",
        "rain_prob": f"{first_day['rain_prob']:.0f}" if first_day else "0",
        "sunrise": str(sunrise[0])[-5:] if sunrise else "—",
        "sunset": str(sunset[0])[-5:] if sunset else "—",
        "spray_label": "Fenêtre de traitement ouverte"
        if spray_ok
        else "Fenêtre de traitement fermée",
        "spray_tone": "good" if spray_ok else "bad",
        "date_label": f"{WEEKDAYS_SHORT[today.weekday()]}. {fmt_day(today)}",
    }
    return current, days, hours, str(data.get("timezone", "") or "")


def simulated_payload(
    today: datetime.date,
) -> tuple[dict[str, str], list[WeatherDaily], list[WeatherHour]]:
    """Secours simulé (ancien calcul) si Open-Meteo est indisponible."""
    sim_days, sim_now = _generate_weather(today)
    current = dict(EMPTY_CURRENT)
    current.update(sim_now)
    current["tmax"] = sim_now["temp"]
    current["gust"] = sim_now["wind"]
    days: list[WeatherDaily] = []
    for offset, day in enumerate(sim_days):
        day_date = today + datetime.timedelta(days=offset)
        days.append(
            {
                "iso": day_date.isoformat(),
                "day": day["day"],
                "date_label": day["date_label"],
                "kind": day["kind"],
                "label": day["label"],
                "tmax": day["tmax"],
                "tmin": day["tmin"],
                "rain": day["rain"],
                "rain_prob": 0.0,
                "wind": day["wind"],
                "gust": day["wind"],
                "spray": day["spray"],
                "is_today": offset == 0,
            }
        )
    first = sim_days[0]
    hours: list[WeatherHour] = []
    for hour in range(0, 24, 3):
        share = abs(12 - hour) / 12.0
        hours.append(
            {
                "iso": f"{today.isoformat()}T{hour:02d}:00",
                "hour": f"{hour:02d}h",
                "kind": first["kind"],
                "label": first["label"],
                "temp": round(
                    first["tmin"]
                    + (first["tmax"] - first["tmin"]) * (1 - share),
                    1,
                ),
                "rain": round(first["rain"] / 8.0, 1),
                "humidity": first["humidity"],
                "wind": first["wind"],
                "is_now": False,
            }
        )
    return current, days, hours


async def farm_coordinates() -> tuple[float, float]:
    """Coordonnées moyennes des parcelles, avec repli sur l'exploitation.

    Le schéma SQLite local est initialisé au préalable (idempotent) afin que la
    météo puisse être chargée même si la page d'accueil n'a pas encore amorcé
    la base. Si la table `parcel` est absente, vide ou illisible, les
    coordonnées de référence de l'exploitation sont renvoyées sans lever
    d'erreur.
    """
    try:
        await ensure_local_database()
    except Exception as e:  # noqa: BLE001
        logging.exception("Unexpected error")
        logging.warning(
            "Initialisation SQLite locale indisponible (%s) : repli sur les "
            "coordonnées de l'exploitation pour la météo.",
            e,
        )
        return (FARM_LATITUDE, FARM_LONGITUDE)

    # 1. Introspection synchrone (hors boucle d'événements). `None` =
    #    indéterminé (verrou, WAL, erreur d'E/S) : on n'en conclut rien.
    try:
        exists = await asyncio.to_thread(local_table_exists, "parcel")
    except Exception as e:  # noqa: BLE001
        logging.exception("Unexpected error")
        logging.warning("Vérification de la table 'parcel' impossible (%s).", e)
        exists = None
    # 2. Vérification asynchrone fiable via `rx.asession()` (raw SQL, sans
    #    PRAGMA) lorsque le résultat précédent est indéterminé.
    if exists is None:
        exists = await local_table_exists_async("parcel")
    if exists is False:
        logging.warning(
            "Table 'parcel' indisponible : repli sur les coordonnées "
            "de l'exploitation pour la météo."
        )
        return (FARM_LATITUDE, FARM_LONGITUDE)

    try:
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    text(
                        """
                        SELECT AVG(latitude), AVG(longitude)
                        FROM parcel
                        WHERE latitude <> 0 AND longitude <> 0
                        """
                    )
                )
            ).first()
    except Exception as e:  # noqa: BLE001
        # Erreur non bloquante (table absente, base verrouillée, E/S) :
        # la météo se charge sur la position de référence.
        logging.exception("Unexpected error")
        logging.warning(
            "Lecture des coordonnées parcellaires impossible (%s) : repli "
            "sur la position de l'exploitation.",
            e,
        )
        return (FARM_LATITUDE, FARM_LONGITUDE)

    if row is not None and row[0] is not None and row[1] is not None:
        return (float(row[0]), float(row[1]))
    return (FARM_LATITUDE, FARM_LONGITUDE)


class WeatherState(rx.State):
    """Météo réelle géolocalisée du cockpit agronomique."""

    is_loading: bool = False
    error: str = ""
    is_simulated: bool = False
    latitude: float = FARM_LATITUDE
    longitude: float = FARM_LONGITUDE
    position_source: str = "Position de l'exploitation"
    timezone: str = ""
    current: dict[str, str] = EMPTY_CURRENT
    daily: list[WeatherDaily] = []
    hourly: list[WeatherHour] = []

    @rx.var
    def coords_label(self) -> str:
        return f"{self.latitude:.4f}° / {self.longitude:.4f}°"

    @rx.event
    def request_geolocation(self):
        """Demande la position du navigateur à l'utilisateur."""
        self.error = ""
        return rx.call_script(
            GEO_SCRIPT, callback=WeatherState.handle_geolocation
        )

    @rx.event
    def handle_geolocation(self, result: dict[str, str | float] | None):
        """Réception de la géolocalisation, avec repli exploitation."""
        coords = parse_geolocation(result)
        if coords is None:
            message = ""
            if isinstance(result, dict):
                message = str(result.get("error", "") or "")
            self.error = (
                f"Géolocalisation indisponible ({message}) — repli sur la "
                "position de l'exploitation."
                if message
                else "Géolocalisation indisponible — repli sur la position "
                "de l'exploitation."
            )
            self.position_source = "Position de l'exploitation"
            return WeatherState.load_weather
        self.latitude = coords[0]
        self.longitude = coords[1]
        self.position_source = "Position du navigateur"
        self.error = ""
        return WeatherState.load_weather

    @rx.event(background=True)
    async def load_weather(self):
        """Charge la météo réelle pour la position courante."""
        async with self:
            self.is_loading = True
            source = self.position_source
            latitude = self.latitude
            longitude = self.longitude

        if source == "Position de l'exploitation":
            coords = await farm_coordinates()
            latitude, longitude = coords

        data: dict | None = None
        error = ""
        try:
            data = await asyncio.to_thread(fetch_forecast, latitude, longitude)
        except Exception as e:  # noqa: BLE001
            logging.exception(f"Error: {e}")
            error = "Open-Meteo indisponible — météo simulée de secours."

        today = datetime.date.today()
        if data is not None:
            current, days, hours, timezone = build_payload(data)
            simulated = False
        else:
            current, days, hours = simulated_payload(today)
            timezone = "local (simulation)"
            simulated = True

        async with self:
            self.latitude = latitude
            self.longitude = longitude
            self.current = current
            self.daily = days
            self.hourly = hours
            self.timezone = timezone
            self.is_simulated = simulated
            if error:
                self.error = error
            self.is_loading = False

import reflex as rx

import datetime as dt
import math
from typing import TypedDict

from app.catalog_reference import WATER_LABELS, irrigation_profile


class WaterDay(TypedDict):
    date: str
    et0: float
    rain: float


class IrrigationInput(TypedDict):
    crop_id: int
    status: str
    linked: bool
    irrigation: str
    area: float
    water_need: str
    requirement: float
    stage: str
    observed_on: str
    progression: float
    critical: bool
    stress: bool
    recent_mm: float
    last_water: str
    unknown_water: int


EMPTY_RECOMMENDATION: dict[str, str] = {
    "status": "empty",
    "message": "Aucune recommandation disponible.",
    "dose": "",
    "volume": "",
    "date": "",
    "period": "",
    "deficit": "",
    "et0": "",
    "etc": "",
    "rain": "",
    "effective_rain": "",
    "recent": "",
    "kc": "",
    "profile": "",
    "phenology": "",
    "rationale": "",
    "assumptions": "",
    "water_need": "",
    "requirement": "",
}


def forecast_days(data: dict, today: dt.date) -> list[WaterDay]:
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    rain = daily.get("precipitation_sum", [])
    et0 = daily.get("et0_fao_evapotranspiration", [])
    if not (len(dates) == len(rain) == len(et0)):
        raise ValueError("Prévisions journalières incomplètes.")
    by_date: dict[str, WaterDay] = {}
    for iso, r, e in zip(dates, rain, et0):
        date = dt.date.fromisoformat(iso)
        if today <= date < today + dt.timedelta(days=7):
            if r is None or e is None:
                raise ValueError("Pluie ou ET0 manquante.")
            r, e = float(r), float(e)
            if not math.isfinite(r) or not math.isfinite(e) or r < 0 or e < 0:
                raise ValueError("Pluie ou ET0 invalide.")
            by_date[iso] = {"date": iso, "rain": r, "et0": e}
    expected = [(today + dt.timedelta(days=i)).isoformat() for i in range(7)]
    if any(iso not in by_date for iso in expected):
        raise ValueError(
            "Sept jours consécutifs de prévisions sont nécessaires."
        )
    return [by_date[iso] for iso in expected]


def exclusion(data: IrrigationInput) -> str:
    if not data["crop_id"]:
        return (
            "Aucune culture active sur cette parcelle : aucun besoin inventé."
        )
    if data["status"] != "EN_COURS":
        return (
            "Culture planifiée, pas encore en cours : aucun apport recommandé."
        )
    if data["irrigation"] == "AUCUNE":
        return "Parcelle conduite sans irrigation (AUCUNE) : pas de tour d’eau proposé."
    if not data["linked"]:
        return "Culture non reliée au référentiel : besoin en eau et profil indisponibles."
    if not math.isfinite(data["area"]) or data["area"] <= 0:
        return "Surface culturale/parcellaire absente ou invalide : volume non calculable."
    return ""


def calculate_recommendation(
    data: IrrigationInput, days: list[WaterDay], today: dt.date
) -> dict[str, str]:
    result = dict(EMPTY_RECOMMENDATION)
    result["message"] = exclusion(data)
    if result["message"]:
        return result
    profile = irrigation_profile(data["water_need"])
    assumptions = [
        "Pluie efficace = 80 % de la pluie prévue ; apports nets supposés, sans pertes réseau ni réserve initiale du sol."
    ]
    if data["water_need"] not in WATER_LABELS:
        assumptions.append(
            "Besoin en eau inconnu pour cette culture reliée : profil MODEREE par défaut."
        )
    progression = max(0.0, min(1.0, data["progression"]))
    if data["observed_on"]:
        factor = (
            0.55 + progression * 0.45
            if progression < 0.5
            else 1.0
            if progression <= 0.8
            else 0.75
        )
        result["phenology"] = (
            f"{data['stage']} · observé le {data['observed_on']} · progression ordonnée {progression * 100:.0f} %"
        )
        if (today - dt.date.fromisoformat(data["observed_on"])).days > 30:
            assumptions.append(
                "Observation de plus de 30 jours : vérifier le stade au champ."
            )
    else:
        factor = {
            "SEMIS": 0.55,
            "LEVEE": 0.65,
            "TALLAGE": 0.8,
            "CROISSANCE": 0.9,
            "FLORAISON": 1.0,
            "FRUCTIFICATION": 1.0,
            "MATURATION": 0.75,
            "RECOLTE": 0.6,
        }.get(data["stage"], 0.85)
        result["phenology"] = (
            f"{data['stage'] or 'Stade inconnu'} · stade déclaré de la culture, sans observation datée"
        )
        assumptions.append(
            "Kc approximé depuis le stade déclaré ; progression non observée."
        )
    if data["critical"]:
        factor = max(factor, 1.0)
        assumptions.append("Stade critique : facteur Kc porté au minimum à 1.")
    if data["stress"]:
        factor *= 1.1
        assumptions.append(
            "Stress hydrique observé : majoration indicative du Kc de 10 %, à confirmer au champ."
        )
    if len(days) != 7 or any(
        day["date"] != (today + dt.timedelta(days=i)).isoformat()
        for i, day in enumerate(days)
    ):
        raise ValueError("Prévisions de sept jours requises.")
    if any(
        not math.isfinite(day[key]) or day[key] < 0
        for day in days
        for key in ("et0", "rain")
    ):
        raise ValueError("Données météorologiques invalides.")
    kc = profile["kc_mid"] * factor
    et0 = sum(day["et0"] for day in days)
    rain = sum(day["rain"] for day in days)
    recent = max(0.0, data["recent_mm"])
    deficit = max(0.0, et0 * kc - rain * 0.8 - recent)
    dose = min(deficit, profile["dose_mm"])
    earliest = today
    if data["last_water"]:
        earliest = max(
            today,
            dt.date.fromisoformat(data["last_water"])
            + dt.timedelta(days=profile["interval_days"]),
        )
    cumulative = -recent
    proposed = ""
    for day in days:
        cumulative += day["et0"] * kc - day["rain"] * 0.8
        date = dt.date.fromisoformat(day["date"])
        if (
            dose > 0
            and date >= earliest
            and cumulative >= min(dose, profile["dose_mm"] * 0.5)
        ):
            proposed = day["date"]
            break
    if dose > 0 and not proposed and earliest <= today + dt.timedelta(days=6):
        proposed = max(earliest, today + dt.timedelta(days=6)).isoformat()
    if data["unknown_water"]:
        assumptions.append(
            f"{data['unknown_water']} irrigation(s) récente(s) sans rattachement culturel, dose ou surface exploitable : non déduite(s)."
        )
    message = (
        "Apport indicatif à vérifier au champ"
        if proposed
        else "Aucun apport nécessaire selon ce bilan"
        if deficit == 0
        else "Intervalle de référence non écoulé sur ces 7 jours : réévaluer avant le prochain tour"
    )
    if not proposed:
        dose = 0.0
    result.update(
        {
            "status": "ready",
            "message": message,
            "date": proposed,
            "period": f"{days[0]['date']} → {days[-1]['date']}",
            "dose": f"{dose:.1f}",
            "volume": f"{dose * data['area'] * 10:.1f}",
            "deficit": f"{deficit:.1f}",
            "et0": f"{et0:.1f}",
            "etc": f"{et0 * kc:.1f}",
            "rain": f"{rain:.1f}",
            "effective_rain": f"{rain * 0.8:.1f}",
            "recent": f"{recent:.1f}",
            "kc": f"{kc:.2f}",
            "profile": f"Dose plafond {profile['dose_mm']:.0f} mm · intervalle {profile['interval_days']} jours. {profile['comment']}",
            "water_need": WATER_LABELS.get(
                data["water_need"], "Besoin inconnu — hypothèse modérée"
            ),
            "requirement": f"{data['requirement']:.0f} mm sur le cycle (repère espèces, pas une dose hebdomadaire)"
            if data["requirement"] > 0
            else "Besoin total du cycle non renseigné",
            "rationale": "Déficit = max(0, Σ ET0 × Kc − 0,8 × Σ pluie − apports réalisés des 7 derniers jours). Dose du prochain tour limitée au plafond du profil ; le solde reste à réévaluer, sans rattrapage automatique.",
            "assumptions": " ".join(assumptions),
        }
    )
    return result

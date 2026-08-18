"""Tests des fonctions clés de la météo réelle (Open-Meteo)."""

from __future__ import annotations

import datetime

from app.states.weather_state import (
    build_payload,
    fetch_forecast,
    parse_geolocation,
    simulated_payload,
    wmo_icon,
    wmo_label,
)


def test_parse_geolocation_ok():
    assert parse_geolocation({"latitude": 48.5, "longitude": 1.9}) == (
        48.5,
        1.9,
    )


def test_parse_geolocation_refus():
    assert parse_geolocation({"error": "User denied Geolocation"}) is None
    assert parse_geolocation(None) is None
    assert parse_geolocation({"latitude": 300, "longitude": 0}) is None


def test_wmo_mapping():
    assert wmo_icon(0) == "sun"
    assert wmo_icon(95) == "cloud-lightning"
    assert "Pluie" in wmo_label(63)


def test_build_payload_from_api():
    data = fetch_forecast(48.234512, 1.845233)
    current, days, hours, timezone = build_payload(data)
    assert len(days) == 15
    assert timezone
    assert 0 < len(hours) <= 24
    assert float(current["temp"]) > -60
    assert current["spray_tone"] in ("good", "bad")
    assert days[0]["is_today"] is True


def test_simulated_fallback():
    current, days, hours = simulated_payload(datetime.date(2026, 5, 12))
    assert len(days) == 7
    assert len(hours) == 8
    assert current["date_label"] != "—"

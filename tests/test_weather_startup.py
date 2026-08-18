"""Vérifie l'initialisation SQLite locale avant toute lecture météo."""

from __future__ import annotations

import asyncio

from app.database import init_local_database, local_table_exists
from app.states.weather_state import (
    FARM_LATITUDE,
    FARM_LONGITUDE,
    farm_coordinates,
)


def test_local_schema_is_initialized_idempotently() -> None:
    init_local_database()
    init_local_database()
    assert local_table_exists("parcel") is True


def test_farm_coordinates_are_valid_without_prior_page_load() -> None:
    latitude, longitude = asyncio.run(farm_coordinates())
    assert -90.0 <= latitude <= 90.0
    assert -180.0 <= longitude <= 180.0


def test_farm_coordinates_fallback_when_table_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.states.weather_state.local_table_exists", lambda name: False
    )
    assert asyncio.run(farm_coordinates()) == (FARM_LATITUDE, FARM_LONGITUDE)

import reflex as rx

import asyncio
import datetime as dt
import sqlite3
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.irrigation import (
    IrrigationInput,
    calculate_recommendation,
    forecast_days,
)
from app.menu_policy import evaluate_policy, visible_entries
from app.navigation import ENTRY_BY_KEY, ROUTE_MATRIX
from app.server_guard import authorize_event, build_rule
from app.states.irrigation_state import (
    IRRIGATION_SQL,
    IrrigationState,
    location_forecasts,
)
from app.states.menu_auth_state import MenuAuthState
from app.states.menu_configuration_state import MenuConfigurationState
from app.states.navigation_state import (
    NavigationState,
    resolve_navigation_entry,
)

TODAY = dt.date(2026, 6, 1)


def crop_input(**changes) -> IrrigationInput:
    data: IrrigationInput = {
        "crop_id": 1,
        "status": "EN_COURS",
        "linked": True,
        "irrigation": "PIVOT",
        "area": 2.0,
        "water_need": "ELEVEE",
        "requirement": 600.0,
        "stage": "Floraison",
        "observed_on": TODAY.isoformat(),
        "progression": 0.6,
        "critical": False,
        "stress": False,
        "recent_mm": 0.0,
        "last_water": "",
        "unknown_water": 0,
    }
    data.update(changes)
    return data


def weather(et0=5.0, rain=0.0):
    return [
        {
            "date": (TODAY + dt.timedelta(days=i)).isoformat(),
            "et0": et0,
            "rain": rain,
        }
        for i in range(7)
    ]


def api_weather():
    return {
        "daily": {
            "time": [day["date"] for day in weather()],
            "precipitation_sum": [0.0] * 7,
            "et0_fao_evapotranspiration": [5.0] * 7,
        }
    }


def test_deficit_dose_cap_and_volume_are_deterministic():
    result = calculate_recommendation(crop_input(), weather(), TODAY)
    assert result["etc"] == "40.2"
    assert result["deficit"] == "40.2"
    assert result["dose"] == "30.0"
    assert result["volume"] == "600.0"
    assert result["date"] == "2026-06-03"
    assert result == calculate_recommendation(crop_input(), weather(), TODAY)


def test_effective_rain_and_completed_water_reduce_deficit():
    result = calculate_recommendation(
        crop_input(recent_mm=10.0), weather(rain=2.0), TODAY
    )
    assert result["effective_rain"] == "11.2"
    assert result["deficit"] == "19.0"
    assert result["dose"] == "19.0"
    assert result["volume"] == "381.0"
    wet = calculate_recommendation(crop_input(), weather(rain=10), TODAY)
    assert wet["dose"] == "0.0" and wet["date"] == ""


def test_stage_critical_stress_default_and_interval():
    early = calculate_recommendation(
        crop_input(progression=0.0), weather(), TODAY
    )
    critical = calculate_recommendation(
        crop_input(progression=0.0, critical=True), weather(), TODAY
    )
    stressed = calculate_recommendation(
        crop_input(stress=True), weather(), TODAY
    )
    assert float(early["kc"]) < float(critical["kc"]) < float(stressed["kc"])
    fallback = calculate_recommendation(
        crop_input(observed_on="", stage="LEVEE", water_need=""),
        weather(),
        TODAY,
    )
    assert (
        "défaut" in fallback["assumptions"]
        and "sans observation" in fallback["phenology"]
    )
    waiting = calculate_recommendation(
        crop_input(last_water=TODAY.isoformat()), weather(), TODAY
    )
    assert (
        waiting["deficit"] != "0.0"
        and waiting["dose"] == "0.0"
        and waiting["date"] == ""
    )


def test_excluded_parcels_never_get_default_numeric_recommendations():
    for changes in (
        {"crop_id": 0},
        {"status": "PLANIFIEE"},
        {"linked": False},
        {"irrigation": "AUCUNE"},
        {"area": 0},
    ):
        result = calculate_recommendation(crop_input(**changes), [], TODAY)
        assert result["status"] == "empty" and result["message"]
        assert result["dose"] == result["volume"] == result["date"] == ""


def test_forecast_requires_seven_consecutive_real_values():
    assert len(forecast_days(api_weather(), TODAY)) == 7
    for invalid in (None, -1.0, float("nan")):
        data = api_weather()
        data["daily"]["precipitation_sum"][3] = invalid
        try:
            forecast_days(data, TODAY)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid forecast accepted")
    data = api_weather()
    data["daily"]["time"][3] = "2026-05-01"
    try:
        forecast_days(data, TODAY)
    except ValueError:
        pass
    else:
        raise AssertionError("Missing day accepted")


def test_navigation_uses_only_existing_irrigation_read_permission():
    entry = ENTRY_BY_KEY["agricole.irrigation"]
    assert (
        entry
        == ROUTE_MATRIX["irrigation"]
        == resolve_navigation_entry("irrigation", "agricole")
    )
    assert (
        entry["route"] == "/irrigation"
        and entry["href"] == "/irrigation?cockpit=agricole"
    )
    assert entry in visible_entries({"irrigation:CONSULTER"}, {})
    assert entry not in visible_entries({"parcelles:CONSULTER"}, {})
    assert entry not in visible_entries(
        {"irrigation:CONSULTER"}, {"agricole": False}
    )
    assert entry not in visible_entries(
        {"irrigation:CONSULTER"}, {"agricole.irrigation": False}
    )
    for name in ("load_irrigation", "select_parcel"):
        rule = build_rule(
            IrrigationState, name, IrrigationState.event_handlers[name]
        )
        assert rule.modules == ("irrigation",) and rule.actions == (
            "CONSULTER",
        )
        assert rule.routes == ("/irrigation",)


def test_existing_sql_links_latest_observation_and_completed_water_only():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript("""
        CREATE TABLE parcel(id INTEGER, name TEXT, area_ha REAL, latitude REAL, longitude REAL, irrigation TEXT);
        CREATE TABLE crop(id INTEGER, parcel_id INTEGER, variety_id INTEGER, name TEXT, status TEXT, stage TEXT, area_ha REAL);
        CREATE TABLE crop_catalog_variety(id INTEGER, crop_variety_id INTEGER, species_id INTEGER);
        CREATE TABLE crop_species(id INTEGER, culture_id INTEGER, water_requirement_mm REAL);
        CREATE TABLE crop_culture(id INTEGER, water_need TEXT);
        CREATE TABLE crop_stage_observation(id INTEGER, crop_id INTEGER, stage_id INTEGER, observed_on TEXT, water_stress INTEGER);
        CREATE TABLE crop_phenology_stage(id INTEGER, profile_id INTEGER, name TEXT, position INTEGER, is_critical INTEGER);
        CREATE TABLE intervention(id INTEGER, parcel_id INTEGER, crop_id INTEGER, type TEXT, status TEXT, done_date TEXT, water_volume_l_ha REAL, area_treated_ha REAL);
        INSERT INTO parcel VALUES(1,'Parcelle test',2,48,1,'PIVOT');
        INSERT INTO crop VALUES(1,1,10,'Culture test','EN_COURS','LEVEE',2);
        INSERT INTO crop_catalog_variety VALUES(1,10,2);
        INSERT INTO crop_species VALUES(2,3,600);
        INSERT INTO crop_culture VALUES(3,'ELEVEE');
        INSERT INTO crop_phenology_stage VALUES(1,1,'Levée',1,0),(2,1,'Floraison',4,1);
        INSERT INTO crop_stage_observation VALUES(1,1,1,'2026-05-27',0),(2,1,2,'2026-05-31',1),(3,1,1,'2026-06-02',0);
        INSERT INTO intervention VALUES(1,1,1,'IRRIGATION','REALISEE','2026-05-31',200000,1);
        INSERT INTO intervention VALUES(2,1,1,'IRRIGATION','PLANIFIEE','2026-06-01',500000,2);
        INSERT INTO intervention VALUES(3,1,1,'TRAITEMENT_PHYTO','REALISEE','2026-05-31',500000,2);
    """)
    try:
        row = connection.execute(
            IRRIGATION_SQL,
            {"today": TODAY.isoformat(), "recent_start": "2026-05-26"},
        ).fetchone()
        assert row["water_need"] == "ELEVEE" and row["requirement"] == 600
        assert row["stage"] == "Floraison" and row["critical"] and row["stress"]
        assert row["recent_mm"] == 10.0 and row["last_water"] == "2026-05-31"
    finally:
        connection.close()


class IrrigationAsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_outage_returns_no_weather_and_fetches_are_bounded(self):
        with (
            patch(
                "app.states.irrigation_state.fetch_forecast",
                side_effect=RuntimeError("offline"),
            ),
            patch("app.states.irrigation_state.logging.exception"),
        ):
            result = await location_forecasts({(48.0, 1.0)})
        assert result[(48.0, 1.0)][0] == []
        assert "indisponible" in result[(48.0, 1.0)][1]
        active = 0
        maximum = 0

        async def fake_thread(fn, *args):
            nonlocal active, maximum
            active += 1
            maximum = max(maximum, active)
            await asyncio.sleep(0.001)
            active -= 1
            return api_weather()

        with (
            patch(
                "app.states.irrigation_state.asyncio.to_thread",
                side_effect=fake_thread,
            ),
            patch(
                "app.states.irrigation_state.forecast_days",
                return_value=weather(),
            ),
        ):
            result = await location_forecasts(
                {(48.0, float(i)) for i in range(8)}
            )
        assert len(result) == 8 and maximum <= 3

    async def test_real_authorizer_rejects_denial_wrong_route_and_unverified_session(
        self,
    ):
        class Context(SimpleNamespace):
            async def get_state(self, cls):
                return self.states.setdefault(cls, cls())

        auth = MenuAuthState()
        auth.token = "test-only-token"
        auth.ready = auth.authenticated = True
        auth._verified_token = auth.token
        auth.verified_path = "/irrigation"
        auth.requested_entry = "agricole.irrigation"
        auth._generation = 1
        state = Context(
            states={
                MenuAuthState: auth,
                NavigationState: NavigationState(),
                MenuConfigurationState: MenuConfigurationState(),
            },
            router=SimpleNamespace(url=SimpleNamespace(path="/irrigation")),
        )
        rule = build_rule(
            IrrigationState,
            "load_irrigation",
            IrrigationState.event_handlers["load_irrigation"],
        )
        policy = evaluate_policy(
            {"id": 1, "email": "unit-test", "admin": False},
            {"policy:account:1:permission:irrigation:CONSULTER": True},
        )
        with patch(
            "app.server_guard.resolve_policy",
            new=AsyncMock(return_value=policy),
        ):
            assert await authorize_event(state, rule)
            auth.ready = False
            assert not await authorize_event(state, rule)
            auth.ready = True
            state.router.url.path = "/parcelles"
            assert not await authorize_event(state, rule)
            state.router.url.path = "/irrigation"
            policy["permissions"] = []
            assert not await authorize_event(state, rule)

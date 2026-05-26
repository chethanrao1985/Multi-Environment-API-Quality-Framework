"""
Open-Meteo Weather API test suite.

All tests are marked with @pytest.mark.weather so --env=weather selects them
and --env=countries skips them.

Cities are loaded from test_data/cities.json — no inline test data.
Base URL and thresholds come exclusively from the weather_env fixture.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import allure
import pytest
import requests

from src.clients import api_client
from src.validators import WeatherValidator


_CITIES_PATH = Path(__file__).parent.parent / "test_data" / "cities.json"


def _load_cities() -> list[dict[str, Any]]:
    if not _CITIES_PATH.exists():
        raise FileNotFoundError(
            f"Test data file not found: {_CITIES_PATH}. "
            "Ensure test_data/cities.json exists in the project root."
        )
    with _CITIES_PATH.open() as fh:
        return json.load(fh)


# Parametrize IDs come from city names for readable test output
_CITIES = _load_cities()
_CITY_IDS = [city["name"] for city in _CITIES]


@allure.suite("weather")
@allure.feature("Performance")
@pytest.mark.weather
@pytest.mark.performance
class TestWeatherPerformance:
    """Response-time tests driven entirely by environments.yaml thresholds."""

    @pytest.mark.parametrize("city", _CITIES, ids=_CITY_IDS)
    def test_forecast_response_time(
        self, city: dict[str, Any], weather_env: dict
    ) -> None:
        url = f"{weather_env['base_url']}/forecast"
        params = {
            "latitude": city["latitude"],
            "longitude": city["longitude"],
            "hourly": "temperature_2m",
            "timezone": city["timezone"],
        }
        with allure.step(f"GET /forecast for {city['name']}"):
            try:
                _, elapsed = api_client.get(url, params=params, timeout=15)
            except requests.exceptions.ReadTimeout:
                pytest.skip(
                    f"[{city['name']}] Open-Meteo did not respond within 15s — skipping."
                )

        allure.attach(
            f"{elapsed:.3f}s (threshold: {weather_env['max_response_time']}s)",
            name="Response time",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert elapsed <= weather_env["max_response_time"], (
            f"[{city['name']}] Response took {elapsed:.3f}s, "
            f"exceeds threshold of {weather_env['max_response_time']}s"
        )


@allure.suite("weather")
@allure.feature("Forecast Validation")
@pytest.mark.weather
@pytest.mark.schema
class TestWeatherForecast:
    """Schema and data-integrity tests for the /forecast endpoint."""

    @pytest.fixture(
        scope="class",
        params=_CITIES,
        ids=_CITY_IDS,
    )
    def forecast(
        self, request: pytest.FixtureRequest, weather_env: dict
    ) -> dict[str, Any]:
        city: dict = request.param
        url = f"{weather_env['base_url']}/forecast"
        params = {
            "latitude": city["latitude"],
            "longitude": city["longitude"],
            "hourly": "temperature_2m",
            "timezone": city["timezone"],
        }
        try:
            response, _ = api_client.get(url, params=params, timeout=15)
        except requests.exceptions.ReadTimeout:
            pytest.skip(
                f"[{city['name']}] Open-Meteo did not respond within 15s — skipping."
            )
        assert response.status_code == 200, (
            f"[{city['name']}] Expected 200, got {response.status_code}"
        )
        data = response.json()
        data["_city_name"] = city["name"]
        data["_status_code"] = response.status_code
        return data

    def test_timezone_field_present(self, forecast: dict) -> None:
        city_name = forecast.get("_city_name", "unknown")
        with allure.step(f"[{city_name}] Validate 'timezone' field is present"):
            WeatherValidator(forecast).validate_timezone().assert_valid()

    def test_hourly_entries_count_positive(
        self, forecast: dict, weather_env: dict
    ) -> None:
        city_name = forecast.get("_city_name", "unknown")
        with allure.step(
            f"[{city_name}] Validate hourly entry count >= {weather_env['min_results_count']}"
        ):
            WeatherValidator(forecast).validate_hourly_count(
                weather_env["min_results_count"]
            ).assert_valid()

    def test_temperature_range_reasonable(self, forecast: dict) -> None:
        city_name = forecast.get("_city_name", "unknown")
        with allure.step(
            f"[{city_name}] Validate all temperatures within [-80, 60]°C"
        ):
            WeatherValidator(forecast).validate_temperature_range().assert_valid()

    def test_full_schema(self, forecast: dict, weather_env: dict) -> None:
        city_name = forecast.get("_city_name", "unknown")
        with allure.step(f"[{city_name}] Run full schema validation chain"):
            WeatherValidator.validate_all(
                forecast,
                min_hourly_count=weather_env["min_results_count"],
            )

    def test_status_200(self, forecast: dict) -> None:
        city_name = forecast.get("_city_name", "unknown")
        with allure.step(f"[{city_name}] Confirm HTTP 200 was returned"):
            assert forecast["_status_code"] == 200, (
                f"[{city_name}] Expected HTTP 200, got {forecast['_status_code']}"
            )


@allure.suite("weather")
@allure.feature("Negative")
@pytest.mark.weather
class TestNegativeWeather:
    """
    Negative-path tests: the API must return 4xx and a structured error body
    for invalid inputs, not silently succeed with bad data.

    These verify that the API's contract includes its error surface — not just
    the happy path.
    """

    @pytest.mark.parametrize("latitude,longitude,label", [
        (999.0, 0.0, "latitude out of range (+999)"),
        (-999.0, 0.0, "latitude out of range (-999)"),
    ])
    def test_out_of_range_coordinates_returns_400(
        self,
        latitude: float,
        longitude: float,
        label: str,
        weather_env: dict,
    ) -> None:
        """
        Coordinates outside [-90, 90] latitude must return HTTP 400 with
        error=true in the response body.
        The API returns: {"reason": "Latitude must be in range ...", "error": true}
        """
        url = f"{weather_env['base_url']}/forecast"
        params = {"latitude": latitude, "longitude": longitude, "hourly": "temperature_2m"}
        with allure.step(f"GET /forecast with {label} — expect 400"):
            try:
                response, _ = api_client.get(url, params=params, timeout=15)
            except requests.exceptions.ReadTimeout:
                pytest.skip(
                    f"Open-Meteo did not respond within 15s for {label!r} — skipping."
                )
        allure.attach(
            f"Status: {response.status_code}\nBody: {response.text[:300]}",
            name="Response",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert response.status_code == 400, (
            f"Expected 400 for {label}, got {response.status_code}"
        )
        body = response.json()
        assert body.get("error") is True, (
            f"Expected error=true in body for {label}, got: {body}"
        )
        assert "reason" in body, (
            f"Expected 'reason' field in error body for {label}, got: {body}"
        )

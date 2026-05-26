"""
Weather response validator.

Validates forecast responses from the Open-Meteo API.
All validation logic lives here — test files never contain inline assertions
about field shapes or types.
"""
from __future__ import annotations

from typing import Any

TEMP_MIN_C: float = -80.0
TEMP_MAX_C: float = 60.0


class WeatherValidator:
    """Typed validator for an Open-Meteo /forecast response object."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
        self._errors: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_timezone(self) -> "WeatherValidator":
        """timezone field must be a non-empty string."""
        timezone = self._data.get("timezone")
        if not isinstance(timezone, str):
            self._errors.append("'timezone' must be a string")
        elif not timezone.strip():
            self._errors.append("'timezone' must not be blank")
        return self

    def validate_hourly_present(self) -> "WeatherValidator":
        """hourly block and temperature_2m array must exist."""
        hourly = self._data.get("hourly")
        if not isinstance(hourly, dict):
            self._errors.append("'hourly' must be an object")
            return self
        temps = hourly.get("temperature_2m")
        if not isinstance(temps, list):
            self._errors.append("'hourly.temperature_2m' must be a list")
        return self

    def validate_hourly_count(self, min_count: int = 1) -> "WeatherValidator":
        """hourly.temperature_2m must contain at least min_count entries."""
        hourly = self._data.get("hourly", {})
        temps = hourly.get("temperature_2m", [])
        if len(temps) < min_count:
            self._errors.append(
                f"'hourly.temperature_2m' must have >= {min_count} entries, "
                f"got {len(temps)}"
            )
        return self

    def validate_temperature_range(self) -> "WeatherValidator":
        """All temperature readings must fall within the physically plausible range."""
        hourly = self._data.get("hourly", {})
        temps = hourly.get("temperature_2m", [])
        # Open-Meteo returns null for hours with no sensor data; skip those entries.
        out_of_range = [
            t for t in temps
            if t is not None and not (TEMP_MIN_C <= t <= TEMP_MAX_C)
        ]
        if out_of_range:
            self._errors.append(
                f"Temperature readings out of range [{TEMP_MIN_C}, {TEMP_MAX_C}]°C: "
                f"{out_of_range[:5]}{'...' if len(out_of_range) > 5 else ''}"
            )
        return self

    def assert_valid(self) -> None:
        """Raise AssertionError with all collected errors if any exist."""
        if self._errors:
            joined = "\n  ".join(self._errors)
            raise AssertionError(
                f"Weather schema validation failed:\n  {joined}"
            )

    @classmethod
    def validate_all(cls, data: dict[str, Any], min_hourly_count: int = 1) -> None:
        """Convenience: run the full validation chain on a forecast response."""
        (
            cls(data)
            .validate_timezone()
            .validate_hourly_present()
            .validate_hourly_count(min_hourly_count)
            .validate_temperature_range()
            .assert_valid()
        )

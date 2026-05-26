"""
Country schema validator.

Validates fields returned by the REST Countries API.
All validation logic lives here — test files never contain inline assertions
about field shapes or types.
"""
from __future__ import annotations

from typing import Any


class CountryValidator:
    """Typed validator for a single REST Countries v3.1 country object."""

    REQUIRED_FIELDS: tuple[str, ...] = (
        "name",
        "capital",
        "population",
        "currencies",
        "languages",
    )

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
        self._errors: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_required_fields(self) -> "CountryValidator":
        """Assert every required top-level field is present and non-null."""
        for field in self.REQUIRED_FIELDS:
            if field not in self._data:
                self._errors.append(f"Missing required field: '{field}'")
            elif self._data[field] is None:
                self._errors.append(f"Field '{field}' must not be null")
        return self

    def validate_name(self) -> "CountryValidator":
        """name must contain at least a 'common' subfield."""
        if "name" not in self._data:
            return self  # already flagged by validate_required_fields
        name = self._data["name"]
        if not isinstance(name, dict):
            self._errors.append("'name' must be an object")
        elif "common" not in name or not isinstance(name["common"], str):
            self._errors.append("'name.common' must be a non-empty string")
        return self

    def validate_population(self) -> "CountryValidator":
        """population must be a non-negative integer (0 is valid for uninhabited territories)."""
        if "population" not in self._data:
            return self  # already flagged by validate_required_fields
        population = self._data["population"]
        if not isinstance(population, int):
            self._errors.append("'population' must be an integer")
        elif population < 0:
            self._errors.append(f"'population' must be >= 0, got {population}")
        return self

    def validate_capital(self) -> "CountryValidator":
        """capital must be a non-empty list of strings."""
        if "capital" not in self._data:
            return self  # already flagged by validate_required_fields
        capital = self._data["capital"]
        if not isinstance(capital, list):
            self._errors.append("'capital' must be a list")
        elif len(capital) == 0:
            self._errors.append("'capital' list must not be empty")
        elif not all(isinstance(c, str) for c in capital):
            self._errors.append("'capital' entries must all be strings")
        return self

    def validate_currencies(self) -> "CountryValidator":
        """currencies must be a non-empty dict."""
        if "currencies" not in self._data:
            return self  # already flagged by validate_required_fields
        currencies = self._data["currencies"]
        if not isinstance(currencies, dict):
            self._errors.append("'currencies' must be an object")
        elif len(currencies) == 0:
            self._errors.append("'currencies' must not be empty")
        return self

    def validate_languages(self) -> "CountryValidator":
        """languages must be a non-empty dict."""
        if "languages" not in self._data:
            return self  # already flagged by validate_required_fields
        languages = self._data["languages"]
        if not isinstance(languages, dict):
            self._errors.append("'languages' must be an object")
        elif len(languages) == 0:
            self._errors.append("'languages' must not be empty")
        return self

    def assert_valid(self) -> None:
        """Raise AssertionError with all collected errors if any exist."""
        if self._errors:
            joined = "\n  ".join(self._errors)
            raise AssertionError(
                f"Country schema validation failed:\n  {joined}"
            )

    @classmethod
    def validate_all(cls, data: dict[str, Any]) -> None:
        """Convenience: run the full validation chain on a single country dict."""
        (
            cls(data)
            .validate_required_fields()
            .validate_name()
            .validate_population()
            .validate_capital()
            .validate_currencies()
            .validate_languages()
            .assert_valid()
        )

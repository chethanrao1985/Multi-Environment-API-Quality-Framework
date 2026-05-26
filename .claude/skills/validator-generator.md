# Skill: Validator Generator

Given a sample JSON response (or a field list with types), generate a typed
validator class that fits this framework's `src/validators/` architecture.

## Input Format

Provide one of:

**Option A — field list:**
```
Resource: Country
Fields:
  name: object { common: str, official: str }
  capital: list[str]
  population: int
  currencies: dict[str, object]
  languages: dict[str, str]
```

**Option B — raw JSON sample:**
```json
{
  "name": { "common": "Germany", "official": "Federal Republic of Germany" },
  "capital": ["Berlin"],
  "population": 83200000,
  "currencies": { "EUR": { "name": "Euro", "symbol": "€" } },
  "languages": { "deu": "German" }
}
```

## Output Contract

The generated file must live at `src/validators/<resource>_validator.py` and
satisfy all of the following:

1. **Module docstring** — one sentence naming the API and the validator's role.
2. **`from __future__ import annotations`** at the top.
3. **`REQUIRED_FIELDS: tuple[str, ...]`** class constant listing every top-level
   required field.
4. **`__init__(self, data: dict[str, Any]) -> None`** — stores `self._data` and
   initialises `self._errors: list[str] = []`.
5. **One `validate_<field>(self) -> "<ClassName>":` method per logical field group.**
   - Appends to `self._errors` — never raises immediately.
   - Returns `self` for chaining.
   - Type checks must be explicit: `isinstance(value, int)`, never `type(value) == int`.
   - For nested objects, validate one level deep (e.g. `name.common` must be a
     non-empty string — do not recurse further unless the spec requires it).
   - For list fields: check `isinstance(x, list)`, `len(x) > 0`, and element type.
   - For dict fields: check `isinstance(x, dict)` and `len(x) > 0`.
6. **`validate_required_fields(self) -> "<ClassName>":`** — iterates
   `REQUIRED_FIELDS`, appends an error for any missing or null field.
7. **`assert_valid(self) -> None:`** — raises `AssertionError` with all errors
   joined by `"\n  "` if `self._errors` is non-empty.
8. **`validate_all(cls, data: dict[str, Any]) -> None:`** classmethod that chains
   `validate_required_fields()` + all field validators + `assert_valid()`.

## Error message format

```
"Missing required field: 'capital'"
"'population' must be an integer"
"'population' must be > 0, got -1"
"'capital' must be a non-empty list"
"'currencies' must be an object"
```

All messages follow: `"'<field>' <condition>, got <actual>"`. Always include
the actual value in range/type failure messages.

## Anti-patterns to avoid

- **Never raise inside a `validate_*` method** — only `assert_valid` raises.
- **Never use `assert` inside `validate_*` methods** — assertions belong in
  `assert_valid`.
- **Never import pytest or requests** in a validator file.
- **Never access `self._data` inside `assert_valid`** — errors are collected
  by the validate methods; `assert_valid` only checks `self._errors`.

## Example output (abbreviated)

```python
from __future__ import annotations
from typing import Any

class CountryValidator:
    """Validates a REST Countries v3.1 country response object."""

    REQUIRED_FIELDS: tuple[str, ...] = ("name", "capital", "population", ...)

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
        self._errors: list[str] = []

    def validate_population(self) -> "CountryValidator":
        pop = self._data.get("population")
        if not isinstance(pop, int):
            self._errors.append("'population' must be an integer")
        elif pop <= 0:
            self._errors.append(f"'population' must be > 0, got {pop}")
        return self

    def assert_valid(self) -> None:
        if self._errors:
            raise AssertionError("Validation failed:\n  " + "\n  ".join(self._errors))

    @classmethod
    def validate_all(cls, data: dict[str, Any]) -> None:
        (cls(data)
            .validate_required_fields()
            .validate_name()
            .validate_population()
            ...
            .assert_valid())
```

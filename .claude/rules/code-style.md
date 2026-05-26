# Code Style Rules

Python style rules specific to this test framework. These augment (and where
they conflict, override) PEP 8 and generic Python conventions.

## Type Hints

- All public functions and methods must carry full type annotations:
  parameters, return type, and instance variables.
- Use `from __future__ import annotations` at the top of every module to
  enable PEP 563 lazy annotation evaluation. This removes the need for
  forward-reference strings in most cases.
- `dict` and `list` are preferred over `Dict` / `List` from `typing` (Python
  3.9+ style). Use `dict[str, Any]` not `Dict[str, Any]`.
- `tuple[str, ...]` (lowercase) for fixed-length tuples. `tuple[str, float]`
  for a two-item tuple.
- The `Any` type is allowed only when the shape of external API data is
  genuinely unknown. Never use it to avoid typing a known structure.

## Validators (`src/validators/`)

- All field-level validators live in `src/validators/`. Never write validation
  logic in `tests/`, `conftest.py`, or anywhere outside `src/`.
- Each validator file maps 1-to-1 with an API domain: `country_validator.py`
  for REST Countries, `weather_validator.py` for Open-Meteo.
- Validators must follow the builder / chained-method pattern: each
  `.validate_*()` method appends to `self._errors: list[str]` and returns
  `self`. The final `.assert_valid()` method raises `AssertionError` with all
  collected errors joined — never one error at a time.
- Required field names must be stored in a class-level tuple constant named
  `REQUIRED_FIELDS`, not inlined in any method body.
- Validators must never make HTTP requests. They receive already-parsed dicts.

## Test Files

- Test file names follow `test_<domain>.py` (e.g. `test_countries.py`).
  Never use `test_api.py` or other generic names.
- Test classes group tests by feature or endpoint, not by method type.
  Correct: `class TestRegionEurope`. Wrong: `class TestGETEndpoints`.
- Test function names are descriptive verb phrases: `test_result_count_exceeds_40`,
  not `test_count` or `test1`.
- Test files must not import from other test files. All shared utilities live in
  `src/` or `conftest.py`.
- `import` order: stdlib → third-party → local `src/` imports. One blank line
  between each group.

## conftest.py

- The top-level `conftest.py` handles: (a) CLI option registration via
  `pytest_addoption`, (b) environment fixture injection, (c) collection-time
  skip logic via `pytest_collection_modifyitems`. Nothing else.
- Fixtures in `conftest.py` must be `scope="session"` unless there is an
  explicit reason to narrow the scope.
- No HTTP requests in `conftest.py`. All network calls happen in test files.

## HTTP Helper

- All HTTP calls go through the private `_get(url, params)` module-level helper
  that returns `(response, elapsed_seconds)`. Never call `requests.get` directly
  in a test method body.
- The `timeout` argument to `requests.get` must always be set explicitly. Never
  rely on the default (no timeout). Use `10` for fast endpoints, `15` for
  parametrized fixture requests.

## Docstrings

- Every module must have a module-level docstring explaining: (1) which API it
  targets, (2) what markers it uses, and (3) where config comes from.
- Every class must have a one-sentence docstring.
- Individual test methods do not require docstrings unless the test logic is
  non-obvious.

## String Formatting

- f-strings for all string interpolation. No `%`-style or `.format()`.
- Assertion messages must include the actual value: `f"Expected > 40, got {n}"`.

## Imports

- Never use star imports (`from module import *`).
- `requests`, `pytest`, `allure`, and `yaml` are always imported at the top of
  the file, not inside functions.
- Internal src imports always use absolute paths from the project root:
  `from src.validators import CountryValidator` — never relative imports
  (`from ..validators import ...`).

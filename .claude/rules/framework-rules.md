# Framework Architecture Rules

Structural constraints for this multi-environment API test framework. These rules
govern how the pieces fit together and must be respected when extending the framework.

## Configuration

- **All configuration lives in `config/environments.yaml`.** This is the single
  source of truth for base URLs and quality-gate thresholds.
- **Zero hardcoded values in test code.** No URL strings, no numeric thresholds,
  no timeout constants may appear in `tests/` files. Base URLs come from
  `*_env` fixtures. Thresholds come from `env["max_response_time"]` and
  `env["min_results_count"]`. The only exception is the physical temperature
  range constant, which lives in `WeatherValidator`.
- When a new API environment is added, the only file that must change is
  `config/environments.yaml`. No test file, no conftest, and no validator should
  require modification to support a new environment.

## Environment Fixture Contract

- The environment fixture system is defined entirely in the top-level
  `conftest.py` and uses three layers:
  1. `all_environments` — the raw parsed YAML dict
  2. `countries_env` / `weather_env` — named session-scoped shortcuts
  3. `active_env` — for generic utilities that need the current `--env` value
- Adding a new environment requires: (a) a new entry in `environments.yaml`,
  (b) a new named fixture in `conftest.py`, (c) a new test file. Nothing else.
- Environment fixtures are always `scope="session"`. Narrowing them to
  `"function"` scope re-parses the YAML on every test and is forbidden.

## Validators

- Validators must extend nothing (no `BaseValidator` inheritance required for
  two-validator frameworks), but if the framework grows beyond 3 API targets, a
  `src/validators/base.py` `BaseValidator` class must be introduced and all
  validators must subclass it.
- Each validator operates on a single already-parsed Python dict. Validators
  must never make network calls, read files, or access pytest fixtures.
- The error collection pattern (`self._errors: list[str]`, `.assert_valid()`)
  is mandatory. Raising immediately on the first failure breaks the
  "collect all errors" design principle and is forbidden.

## Test Data

- **All test input data lives in `test_data/`** and is committed to the repo.
- Data files are JSON. No CSV, no XLSX, no inline Python data structures.
- Test data files must have a flat, consistent schema (list of objects with
  identical keys). No nested or polymorphic structures.
- The `test_data/cities.json` file must always contain exactly 5 entries to
  match the assignment specification. If additional cities are needed, add a
  separate `test_data/cities_extended.json`.

## CLI Flag (`--env`)

- The `--env` flag is implemented via `pytest_addoption` in `conftest.py`.
  Never use environment variables, `pytest.ini` `addopts`, or fixture
  autouse to replicate this behavior.
- The flag must accept exactly these values: `countries`, `weather`, or
  no value (both environments run).
- Test filtering by environment uses `pytest_collection_modifyitems` and
  per-test `@pytest.mark.<env>` markers. Never use `pytest.skip()` inside
  a test body to implement environment filtering.

## CI / CD

- The CI pipeline (`.github/workflows/ci.yml`) must run both environments as
  parallel matrix jobs.
- A combined "all tests" job runs without `--env` and generates the merged
  Allure report.
- The pipeline fails if any test in any environment fails. Matrix jobs must
  use `fail-fast: false` so a failure in one environment does not cancel the
  other.
- Allure report artifacts must be uploaded on both success and failure
  (`if: always()`).
- The `PYTHONPATH` environment variable must be set to the workspace root in
  all test steps so that `from src.validators import ...` resolves correctly.

## Allure Sections

- Allure suite names map 1-to-1 to environment names: `@allure.suite("countries")`
  and `@allure.suite("weather")`. No custom suite names.
- Feature names describe the API feature under test, not the test type.
  Correct: `@allure.feature("Region Europe")`. Wrong: `@allure.feature("GET Tests")`.
- Every test class must carry both `@allure.suite` and `@allure.feature`
  decorators. Standalone test functions must carry both at function level.

## Module Boundaries

- `tests/` files must not import from other `tests/` files.
- `conftest.py` must not import from `tests/` files.
- `src/validators/` files must not import from `tests/` or `conftest.py`.
- The only permitted cross-boundary imports are: `tests/* → src/validators/*`
  and `conftest.py → yaml / pathlib` (stdlib) and `pytest`.

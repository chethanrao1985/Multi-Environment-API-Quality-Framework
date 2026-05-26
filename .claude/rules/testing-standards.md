# Testing Standards

These rules govern how tests are written in this pytest framework. They apply
to all files under `tests/` and override any generic Python testing advice.

## Parametrization

- **Always parametrize from `test_data/`** — never inline test data inside test
  files. Cities, country names, expected values, and any other data set with
  two or more members must live in a JSON file under `test_data/` and be loaded
  at module import time.
- The `ids=` argument to `@pytest.mark.parametrize` must always be set to
  human-readable strings (e.g. city names, country codes) — not numeric
  indices. This makes CI output scannable without cross-referencing source.
- Parametrize data must be loaded with a private module-level function (e.g.
  `_load_cities()`) and stored in a module-level constant (e.g. `_CITIES`).
  Never call `json.load` inside a test function body.

## Schema Validation

- **Every endpoint must have a schema validation test.** A test that only
  checks the HTTP status code is not considered complete.
- Schema assertions never live inline in test files. All type and field checks
  must be delegated to a validator class in `src/validators/`. Test files call
  `.validate_*()` methods and `.assert_valid()` — they never assert on
  individual field types or values directly.
- Validators use a builder / chained-method pattern so test code reads
  declaratively:
  ```python
  CountryValidator(data).validate_name().validate_population().assert_valid()
  ```
- Each validator must expose a `validate_all(data)` classmethod for the common
  full-validation path.

## Assertions

- No bare `assert` statements on raw API response fields in test bodies.
  All assertions go through validator classes or named helper functions.
- When asserting on counts or thresholds, the right-hand side must always
  come from the environment fixture (e.g. `env["min_results_count"]`) — never
  a literal number in the test.
- The only literal threshold allowed in test code is the temperature range
  `(-80, 60)` used by `WeatherValidator` — it is a physical constant, not a
  configurable business rule, and it lives inside the validator, not in a test.

## Markers

- Every test class and standalone test function must carry one of:
  `@pytest.mark.countries` or `@pytest.mark.weather`.
- Schema-validation tests additionally carry `@pytest.mark.schema`.
- Performance / response-time tests additionally carry
  `@pytest.mark.performance`.
- Never mix environment markers on a single test (a test belongs to one
  environment).

## Fixtures

- Environment config (base URL, thresholds) must be obtained through the
  session-scoped `countries_env` or `weather_env` fixtures from `conftest.py`.
  Never import or parse `environments.yaml` inside a test file.
- Fixtures that issue HTTP requests should be scoped to `"class"` (or
  `"session"` for read-only shared data) to avoid redundant network calls
  during a single run.
- Fixtures that return API response data must include the `_city_name` or
  equivalent metadata key so downstream tests can produce meaningful failure
  messages.

## Cross-Reference Tests

- Every API environment must have at least one cross-reference test that
  validates the same entity across two different endpoints of that API.
  For the Countries environment, the canonical case is: a country found via
  `/name/{name}` must also appear in the corresponding `/region/{region}` list.

## Allure Integration

- Every test class must be decorated with `@allure.suite("<env_name>")` and
  `@allure.feature("<feature_name>")` so reports are partitioned by environment
  and feature automatically.
- HTTP calls inside tests must be wrapped in `with allure.step(f"GET {url}"):`.
- Response-time results must be attached via `allure.attach(...)` so they are
  visible in the report without reading log output.

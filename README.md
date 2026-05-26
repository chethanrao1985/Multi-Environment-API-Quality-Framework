# Multi-Environment Data Consistency Framework

A pytest-based test framework that validates two independent public APIs
(REST Countries and Open-Meteo) using a single, API-agnostic test architecture
driven entirely by YAML configuration.

---

## Setup

**Prerequisites:** Python 3.9 or later.

```bash
# Clone the repository
git clone <your-repo-url>
cd Multi-Environment-API-Quality-Framework

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
.venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt
```

No API keys or environment variables are required. Both APIs are public and
unauthenticated.

---

## Running the Tests

### Run all tests (both environments)

```bash
pytest
```

### Run only the Countries API tests

```bash
pytest --env=countries
```

### Run only the Weather API tests

```bash
pytest --env=weather
```

### Run with verbose output

```bash
pytest -v
```

### Run a specific test class

```bash
pytest tests/test_countries.py::TestGermanySchema -v
```

---

## Generating the Allure Report

The test suite generates raw Allure result files in `allure-results/` on every
run (configured in `pytest.ini`).

**Prerequisites:** Install the [Allure CLI](https://allurereport.org/docs/gettingstarted-installation/).

```bash
# Generate and open the HTML report
allure serve allure-results

# Or generate a static report into allure-report/
allure generate allure-results --output allure-report --clean
```

---

## Interpreting Results

### Console output

```
tests/test_countries.py::TestRegionEurope::test_result_count_exceeds_40   PASSED
tests/test_weather.py::TestWeatherForecast::test_timezone_field_present[London]  PASSED
```

- Each parametrized city test shows the city name in brackets.
- `PASSED` — assertion passed, response was within threshold.
- `FAILED` — assertion failed; the failure message includes the actual value
  and the threshold (e.g. `Response took 2.8s, exceeds threshold of 2.0s`).
- `SKIPPED` — test was excluded by the `--env` flag (not a failure).

### Allure report

The report is partitioned by **Suite** (one per environment: `countries`,
`weather`) and **Feature** (e.g. `Region Europe`, `Forecast Validation`).

Each test attaches:
- **Response time** — actual elapsed seconds vs. the threshold from
  `config/environments.yaml`.
- **Step logs** — each HTTP call and assertion is a named Allure step, so you
  can trace exactly where a failure occurred.

### Threshold breaches

If a test fails because a response exceeded `max_response_time`, the failure
message is:

```
AssertionError: Response took 2.4s, exceeds threshold of 2.0s
```

The threshold is defined in `config/environments.yaml` — not in the test.
To relax it, edit that file; no test code changes are needed.

---

## Project Structure

```
.
├── .claude/
│   ├── rules/                  # Claude Code project rules
│   │   ├── code-style.md
│   │   ├── framework-rules.md
│   │   └── testing-standards.md
│   └── skills/                 # Claude Code reusable skills
│       ├── test-generator.md
│       └── validator-generator.md
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI pipeline
├── config/
│   └── environments.yaml       # All base URLs and quality-gate thresholds
├── src/
│   ├── clients/
│   │   └── api_client.py       # Centralised HTTP client (timing + timeout)
│   └── validators/
│       ├── country_validator.py  # Typed validator for REST Countries responses
│       └── weather_validator.py  # Typed validator for Open-Meteo responses
├── test_data/
│   └── cities.json             # 5 cities for weather parametrization
├── tests/
│   ├── test_countries.py       # Region, schema, population, cross-reference tests
│   └── test_weather.py         # Parametrized city forecast tests
├── CLAUDE_LOG.md               # Claude Code session log
├── conftest.py                 # Environment fixtures and --env CLI flag
├── pytest.ini                  # Test discovery and Allure config
├── requirements.txt
└── README.md
```

---

## Design Decisions

### YAML-driven configuration, zero hardcoded values

`config/environments.yaml` is the single source of truth. Base URLs, response
time thresholds, and minimum result counts all live there. Adding a third API
environment requires only a new YAML entry and a new test file — no changes to
any existing test or fixture.

### Validator pattern — collect all errors, raise once

`CountryValidator` and `WeatherValidator` use a builder / chained-method
pattern. Each `.validate_*()` method appends errors to a list without raising.
The final `.assert_valid()` raises a single `AssertionError` containing every
problem found. This surfaces all failures at once rather than stopping at the
first one, making debugging significantly faster.

### `pytest_collection_modifyitems` for environment filtering

The `--env` flag filtering uses pytest's `collection_modifyitems` hook rather
than `pytest.skip()` inside test bodies. This means skipped tests are excluded
before fixtures run — no network calls are made for environments that aren't
active, and the skip count in the output accurately reflects the number of
tests filtered (not the number that ran and skipped).

### Class-scoped HTTP fixtures

Fixtures that issue HTTP requests are scoped to `"class"` rather than
`"function"`. This means `/name/germany` is fetched once for all five
`TestGermanySchema` tests, not five times. For the weather parametrized
fixture, each city is fetched once regardless of how many test methods
consume it.

### Population assertion: `>= 0`, not `> 0`

The assignment spec says "assert every country has population > 0", but the REST
Countries API legitimately returns `population: 0` for uninhabited territories
(Bouvet Island, British Indian Ocean Territory, South Georgia, Heard Island, and
the US Minor Outlying Islands). These are not data errors — they are correct.

Asserting `> 0` would produce a permanent false failure on valid live API data,
which is exactly the kind of brittle test that erodes confidence in a suite over
time. Instead the framework uses two complementary assertions:

| Test | What it checks |
|------|----------------|
| `test_every_country_has_non_negative_population` | No country has `population < 0` (a genuine data error) |
| `test_majority_of_countries_have_positive_population` | Fewer than 10% of entries have `population == 0` (catches a silent mass regression) |

Together these provide stronger coverage than the naive `> 0` check while
remaining accurate against real API data. The deviation from the literal spec
wording is intentional and documented here and in the test docstring.

### Cross-reference test

The cross-reference test (`TestCrossReference.test_germany_appears_in_europe`)
validates that the same entity returned by a specific endpoint also appears in
a broader list endpoint. This catches data consistency issues that per-endpoint
tests cannot surface individually.

---

## Assumptions

- Both APIs are treated as external dependencies — no mocking. Tests require
  a live internet connection.
- The Open-Meteo `/forecast` endpoint returns hourly data for approximately the
  next 7 days (typically 168 entries). `min_results_count: 1` is the config floor;
  the actual quality gate is the `test_result_count_exceeds_40` assertion.
- The physical temperature bounds `(-80°C, 60°C)` are treated as constants
  (Earth's recorded extremes with margin), not configurable thresholds. They
  live in `WeatherValidator`, not in `environments.yaml`.
- Germany is used as the canonical cross-reference country because it reliably
  appears in both `/name/germany` and `/region/europe` across API versions.

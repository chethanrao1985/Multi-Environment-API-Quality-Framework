# Skill: Test Generator

Given an endpoint URL, HTTP method, and expected response fields, generate a
complete pytest test file that fits this framework's architecture.

## Input Format

Provide the following when invoking this skill:

```
Endpoint: GET https://api.example.com/v1/items/{id}
Environment: <env name — must match an entry in config/environments.yaml>
Response fields: id (int), name (str), price (float), tags (list[str]), active (bool)
Marker: items
```

## Output Contract

The generated file must:

1. **Live at** `tests/test_<resource>.py` (e.g. `tests/test_items.py`).
2. **Import block** (in order, one blank line between groups):
   ```python
   from __future__ import annotations
   from typing import Any

   import allure
   import pytest

   from src.clients import api_client
   from src.validators import <ResourceValidator>
   ```
3. **Include a module-level docstring** naming the API, the marker, and the
   config source.
4. **No local `_get()` helper.** Use `api_client.get(url, params=..., timeout=...)`
   directly in every test/fixture. Signature: `(response, elapsed_seconds)`.
   Default timeout is 10 s; pass `timeout=15` for slow parametrized fixture calls.
5. **Performance class** — `@allure.suite("<env>")`, `@allure.feature("Performance")`,
   `@pytest.mark.<env>`, one test per endpoint:
   ```python
   def test_<endpoint_slug>_response_time(self, <env>_env: dict) -> None:
       url = f"{env['base_url']}/<path>"
       _, elapsed = api_client.get(url)
       assert elapsed <= env["max_response_time"]
   ```
6. **Schema class** — `@allure.suite("<env>")`, `@allure.feature("<Resource> Schema")`,
   `@pytest.mark.<env>`, `@pytest.mark.schema`:
   - A `scope="class"` fixture that fetches the response once
   - One test per required field group (not per field — group logically)
   - A `test_full_schema()` that calls `<Validator>.validate_all(data)`
7. **Parametrized test** for list endpoints — if the endpoint returns a list,
   add a standalone `@pytest.mark.parametrize` test asserting the count meets
   `env["min_results_count"]`.
8. **Negative tests** — at minimum one test for an invalid path parameter
   (e.g. `/items/INVALID`) asserting a 404 or 400 status code.

## Validator generation

After generating the test file, immediately invoke the `validator-generator`
skill with the sample response fields to generate the matching
`src/validators/<resource>_validator.py`.

## Example invocation

```
Endpoint: GET https://restcountries.com/v3.1/name/{name}
Environment: countries
Response fields: name (obj with common/official), capital (list[str]),
                 population (int), currencies (dict), languages (dict)
Marker: countries
```

Expected output files:
- `tests/test_countries_name.py`
- `src/validators/country_name_validator.py`

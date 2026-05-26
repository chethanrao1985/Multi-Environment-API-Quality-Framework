"""
Top-level conftest.py — environment fixture and CLI flag wiring.

The --env flag controls which environment(s) are active for the session.
All base URLs and thresholds are injected from config/environments.yaml;
no values are hardcoded in test code.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_CONFIG_PATH = Path(__file__).parent / "config" / "environments.yaml"


def _load_environments() -> dict:
    with _CONFIG_PATH.open() as fh:
        data = yaml.safe_load(fh)
    return data["environments"]


def pytest_addoption(parser: pytest.Parser) -> None:
    _envs = list(_load_environments().keys())
    parser.addoption(
        "--env",
        action="store",
        default=None,
        choices=_envs,
        help=(
            "Restrict the test run to a single environment. "
            "Omit to run both environments."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "countries: REST Countries API tests")
    config.addinivalue_line("markers", "weather: Open-Meteo Weather API tests")


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip tests whose environment marker doesn't match the --env flag."""
    selected_env = config.getoption("--env")
    if selected_env is None:
        return

    skip_marker = pytest.mark.skip(
        reason=f"--env={selected_env}: this environment is not selected"
    )
    for item in items:
        all_markers = {m.name for m in item.iter_markers()}
        if selected_env not in all_markers:
            item.add_marker(skip_marker)


@pytest.fixture(scope="session")
def all_environments() -> dict:
    return _load_environments()


@pytest.fixture(scope="session")
def countries_env(all_environments: dict) -> dict:
    return all_environments["countries"]


@pytest.fixture(scope="session")
def weather_env(all_environments: dict) -> dict:
    return all_environments["weather"]



from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import custom_components

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from . import fake_pantry

DOMAIN = "pantry"

# pytest-homeassistant-custom-component imports its own test "custom_components" package first; add ours to it.
_OURS = str(Path(__file__).resolve().parents[1] / "custom_components")
if _OURS not in custom_components.__path__:
    custom_components.__path__.append(_OURS)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
async def tz(hass: HomeAssistant) -> None:
    await hass.config.async_set_time_zone("America/New_York")


@pytest.fixture
def pantry(aioclient_mock: AiohttpClientMocker) -> Callable[..., None]:
    """Make the fake Pantry answer: pantry(**state_kwargs), pantry(status=401), pantry(exc=...)."""
    def answer(status: int = 200, exc: Exception | None = None, **kwargs) -> None:
        aioclient_mock.clear_requests()
        url = f"{fake_pantry.URL}/api/ha/state"
        if exc:
            aioclient_mock.get(url, exc=exc)
        elif status != 200:
            aioclient_mock.get(url, status=status)
        else:
            from homeassistant.util import dt as dt_util
            aioclient_mock.get(url, json=fake_pantry.state(dt_util.now().date(), **kwargs))
    answer()
    return answer


@pytest.fixture
async def entry(hass: HomeAssistant, tz, pantry) -> MockConfigEntry:
    e = MockConfigEntry(domain=DOMAIN, unique_id=fake_pantry.INSTANCE_ID, title="Pantry",
                        data={"url": fake_pantry.URL, "token": fake_pantry.TOKEN})
    e.add_to_hass(hass)
    await hass.config_entries.async_setup(e.entry_id)
    await hass.async_block_till_done()
    return e

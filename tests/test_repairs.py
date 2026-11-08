from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir

from . import fake_pantry
from .conftest import DOMAIN


def _issues(hass):
    return {i.translation_key: i for (domain, _), i in ir.async_get(hass).issues.items() if domain == DOMAIN}


async def _poll(hass, entry, pantry, **kwargs):
    pantry(**kwargs)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()


async def test_versions_match_no_issue(hass: HomeAssistant, entry):
    assert _issues(hass) == {}


async def test_pantry_too_old(hass: HomeAssistant, entry, pantry):
    await _poll(hass, entry, pantry, version="2026.11.07.4", integration_min=None)
    issue = _issues(hass)["pantry_outdated"]
    assert issue.severity == ir.IssueSeverity.WARNING and not issue.is_fixable
    assert issue.translation_placeholders == {"pantry_version": "2026.11.07.4", "needed": "2026.11.8"}
    await _poll(hass, entry, pantry)                       # Pantry updated on the PC
    assert _issues(hass) == {}


async def test_integration_too_old(hass: HomeAssistant, entry, pantry):
    await _poll(hass, entry, pantry, version="2027.1.15", integration_min="2027.1.1")
    issue = _issues(hass)["integration_outdated"]
    assert issue.translation_placeholders["needed"] == "2027.1.1"
    assert issue.translation_placeholders["pantry_version"] == "2027.1.15"
    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, fake_pantry.INSTANCE_ID)})
    assert device.sw_version == "2027.1.15"                 # device page follows Pantry's version
    await _poll(hass, entry, pantry, version="2027.1.15", integration_min="2026.11.8")
    assert _issues(hass) == {}


async def test_newer_pantry_is_fine(hass: HomeAssistant, entry, pantry):
    await _poll(hass, entry, pantry, version="2026.12.01")
    assert _issues(hass) == {}


async def test_issues_removed_with_entry(hass: HomeAssistant, entry, pantry):
    await _poll(hass, entry, pantry, version="2026.11.01")
    assert "pantry_outdated" in _issues(hass)
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert _issues(hass) == {}

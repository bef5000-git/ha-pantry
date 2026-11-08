"""Pantry: meal plans and meal-prep tasks from Pantry on your PC, for automations and dashboards."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.loader import async_get_integration

from .const import DOMAIN
from .coordinator import PantryCoordinator, issue_ids

PLATFORMS = [Platform.BINARY_SENSOR, Platform.CALENDAR, Platform.SENSOR]

type PantryConfigEntry = ConfigEntry[PantryCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: PantryConfigEntry) -> bool:
    integration = await async_get_integration(hass, DOMAIN)
    coordinator = PantryCoordinator(hass, entry, str(integration.version))
    # Not async_config_entry_first_refresh: if the PC is off when Home Assistant starts, the entities are still
    # set up (unavailable, and binary_sensor.pantry_online "off") instead of the whole integration waiting.
    # A wrong token still starts re-authentication.
    await coordinator.async_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PantryConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    for issue in issue_ids(entry):
        ir.async_delete_issue(hass, DOMAIN, issue)

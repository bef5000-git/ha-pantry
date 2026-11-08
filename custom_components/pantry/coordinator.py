"""Fetches Pantry's plan every few minutes, for all the entities, and checks the two versions match up."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import versions
from .api import PantryAuthError, PantryConnectionError, fetch_state
from .const import CONF_TOKEN, CONF_URL, DOMAIN, MIN_PANTRY_VERSION, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


def issue_ids(entry: ConfigEntry) -> tuple[str, str]:
    return f"pantry_outdated_{entry.entry_id}", f"integration_outdated_{entry.entry_id}"


class PantryCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, integration_version: str) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL, config_entry=entry)
        self.url: str = entry.data[CONF_URL]
        self._token: str = entry.data[CONF_TOKEN]
        self.integration_version = integration_version
        self.instance_id: str = entry.unique_id or entry.entry_id
        self._pantry_version: str | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await fetch_state(async_get_clientsession(self.hass), self.url, self._token)
        except PantryAuthError as err:
            raise ConfigEntryAuthFailed("Pantry didn't accept the token") from err
        except PantryConnectionError as err:
            raise UpdateFailed(f"Can't reach Pantry at {self.url}: {err}") from err
        self._check_versions(data)
        return data

    def _check_versions(self, data: dict[str, Any]) -> None:
        """A Repairs issue when Pantry on the PC is too old for this integration, or the other way round."""
        pantry = str(data.get("version") or "unknown")
        needs = data.get("integration_min")
        pantry_issue, integration_issue = issue_ids(self.config_entry)
        if versions.older(pantry, MIN_PANTRY_VERSION):
            ir.async_create_issue(
                self.hass, DOMAIN, pantry_issue, is_fixable=False, severity=ir.IssueSeverity.WARNING,
                translation_key="pantry_outdated",
                translation_placeholders={"pantry_version": pantry, "needed": MIN_PANTRY_VERSION})
        else:
            ir.async_delete_issue(self.hass, DOMAIN, pantry_issue)
        if versions.older(self.integration_version, needs):
            ir.async_create_issue(
                self.hass, DOMAIN, integration_issue, is_fixable=False, severity=ir.IssueSeverity.WARNING,
                translation_key="integration_outdated",
                translation_placeholders={"version": self.integration_version, "needed": str(needs),
                                          "pantry_version": pantry})
        else:
            ir.async_delete_issue(self.hass, DOMAIN, integration_issue)
        if pantry != self._pantry_version:          # keep the device page's version current
            self._pantry_version = pantry
            registry = dr.async_get(self.hass)
            if device := registry.async_get_device(identifiers={(DOMAIN, self.instance_id)}):
                registry.async_update_device(device.id, sw_version=pantry)

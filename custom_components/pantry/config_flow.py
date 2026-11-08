"""Setting up Pantry in Home Assistant: Pantry's address on your network, and its token."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import versions
from .api import PantryAuthError, PantryConnectionError, fetch_state
from .const import CONF_TOKEN, CONF_URL, DOMAIN, MIN_PANTRY_VERSION


def _clean_url(url: str) -> str:
    url = url.strip().rstrip("/")
    return url if url.startswith(("http://", "https://")) else f"http://{url}"


class PantryConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _check(self, url: str, token: str) -> tuple[str | None, dict[str, Any]]:
        """(error key or None, Pantry's reply)."""
        try:
            data = await fetch_state(async_get_clientsession(self.hass), url, token)
        except PantryAuthError:
            return "invalid_auth", {}
        except PantryConnectionError:
            return "cannot_connect", {}
        if not data.get("instance_id") or versions.older(data.get("version"), MIN_PANTRY_VERSION):
            return "pantry_outdated", data
        return None, data

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders = {"needed": MIN_PANTRY_VERSION, "pantry_version": "?"}
        if user_input is not None:
            url, token = _clean_url(user_input[CONF_URL]), user_input[CONF_TOKEN].strip()
            error, data = await self._check(url, token)
            placeholders["pantry_version"] = str(data.get("version") or "?")
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(data["instance_id"])
                # the same Pantry at a new address: update it rather than add a second one
                self._abort_if_unique_id_configured(updates={CONF_URL: url, CONF_TOKEN: token})
                return self.async_create_entry(title="Pantry", data={CONF_URL: url, CONF_TOKEN: token})
        defaults = user_input or {}
        schema = vol.Schema({
            vol.Required(CONF_URL, default=defaults.get(CONF_URL, "")): str,
            vol.Required(CONF_TOKEN): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors,
                                    description_placeholders=placeholders)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders = {"needed": MIN_PANTRY_VERSION, "pantry_version": "?"}
        entry = self._get_reauth_entry()
        if user_input is not None:
            token = user_input[CONF_TOKEN].strip()
            error, data = await self._check(entry.data[CONF_URL], token)
            placeholders["pantry_version"] = str(data.get("version") or "?")
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(data["instance_id"])
                self._abort_if_unique_id_mismatch(reason="wrong_pantry")
                return self.async_update_reload_and_abort(entry, data_updates={CONF_TOKEN: token})
        return self.async_show_form(step_id="reauth_confirm", errors=errors, description_placeholders=placeholders,
                                    data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}))

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Change Pantry's address (e.g. the PC got a new IP) or token."""
        errors: dict[str, str] = {}
        placeholders = {"needed": MIN_PANTRY_VERSION, "pantry_version": "?"}
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            url, token = _clean_url(user_input[CONF_URL]), user_input[CONF_TOKEN].strip()
            error, data = await self._check(url, token)
            placeholders["pantry_version"] = str(data.get("version") or "?")
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(data["instance_id"])
                self._abort_if_unique_id_mismatch(reason="wrong_pantry")
                return self.async_update_reload_and_abort(entry, data_updates={CONF_URL: url, CONF_TOKEN: token})
        schema = vol.Schema({
            vol.Required(CONF_URL, default=entry.data[CONF_URL]): str,
            vol.Required(CONF_TOKEN, default=entry.data[CONF_TOKEN]): str,
        })
        return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors,
                                    description_placeholders=placeholders)

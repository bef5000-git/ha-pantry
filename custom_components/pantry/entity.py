"""Shared base for Pantry entities: one "Pantry" device.

Unique ids come from Pantry's own instance id (made once on the PC), so they stay the same when the PC's
address changes or the integration is removed and added again.
"""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PantryCoordinator


class PantryEntity(CoordinatorEntity[PantryCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: PantryCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.instance_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.instance_id)},
            name="Pantry",
            manufacturer="Pantry",
            model="Meal planner",
            sw_version=(coordinator.data or {}).get("version"),
            configuration_url=coordinator.url,
            entry_type=DeviceEntryType.SERVICE,
        )

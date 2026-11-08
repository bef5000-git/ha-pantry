"""binary_sensor.pantry_online: whether Home Assistant reached Pantry on its last check (every 5 minutes)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PantryConfigEntry
from .entity import PantryEntity


async def async_setup_entry(hass: HomeAssistant, entry: PantryConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([PantryOnline(entry.runtime_data)])


class PantryOnline(PantryEntity, BinarySensorEntity):
    _attr_translation_key = "online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "online")

    @property
    def available(self) -> bool:
        return True                     # it reports "off" when Pantry can't be reached, never "unavailable"

    @property
    def is_on(self) -> bool:
        return self.coordinator.last_update_success

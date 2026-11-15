"""Pantry sensors: today's prep, tonight's prep for tomorrow, the next prep time, and today's meals.

Use them in automations at times you choose, e.g. at 6:45 on weekdays, if "Prep today" is above 0,
send its "summary" attribute to your phones.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import PantryConfigEntry
from .data import meal_name, meals_on, next_prep, prep_today, prep_tonight, summary, task_list
from .entity import PantryEntity


async def async_setup_entry(hass: HomeAssistant, entry: PantryConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    async_add_entities([PrepTodaySensor(c), PrepTonightSensor(c), NextPrepSensor(c), MealsTodaySensor(c)])


class _PrepListSensor(PantryEntity, SensorEntity):
    """State = how many tasks; attributes = the tasks and a ready-to-send summary."""
    _attr_native_unit_of_measurement = "tasks"
    _attr_icon = "mdi:pot-steam-outline"

    def _items(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @property
    def native_value(self) -> int:
        return len(self._items())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        items = self._items()
        return {"summary": summary(items), "tasks": task_list(items),
                "meals": sorted({p["meal"] for p in items})}


class PrepTodaySensor(_PrepListSensor):
    _attr_translation_key = "prep_today"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "prep_today")

    def _items(self):
        return prep_today(self.coordinator.data, dt_util.now().date())


class PrepTonightSensor(_PrepListSensor):
    _attr_translation_key = "prep_tonight"
    _attr_icon = "mdi:fridge-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "prep_tonight")

    def _items(self):
        return prep_tonight(self.coordinator.data, dt_util.now().date())


class NextPrepSensor(PantryEntity, SensorEntity):
    """When the next prep task is due, at Pantry's time for it. Works in a Time trigger."""
    _attr_translation_key = "next_prep"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "next_prep")

    @property
    def native_value(self):
        p = next_prep(self.coordinator.data, dt_util.now())
        return p["due_dt"] if p else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        p = next_prep(self.coordinator.data, dt_util.now())
        if not p:
            return {}
        return {"task": p["task"], "meal": p["meal"], "slot": p["slot"], "meal_date": p["meal_date"],
                "summary": summary([p])}


class MealsTodaySensor(PantryEntity, SensorEntity):
    _attr_translation_key = "meals_today"
    _attr_icon = "mdi:silverware-fork-knife"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "meals_today")

    def _meals(self):
        return meals_on(self.coordinator.data, dt_util.now().date())

    @property
    def native_value(self) -> str:
        meals = self._meals()
        if not meals:
            return "Nothing planned"
        text = ", ".join(f"{m['meal']} ({m['slot']}{', ' + m['for'] if m.get('for') else ''})" for m in meals)
        return text if len(text) <= 255 else text[:252] + "..."

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        meals = self._meals()
        out: dict[str, Any] = {slot: [meal_name(m) for m in meals if m["slot"] == slot]
                               for slot in ("breakfast", "lunch", "dinner")}
        out["meals"] = [{"meal": m["meal"], "slot": m["slot"], "for": m.get("for") or "everyone",
                         "ingredients": m.get("ingredients"), "prep": m.get("prep", [])} for m in meals]
        return out

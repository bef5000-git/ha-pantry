"""Pantry calendars.

"Meal prep": each prep task at Pantry's time for it (7:00 am on the day, 8:00 pm the night before, or the
time you gave). Use a Calendar trigger with an offset to remind earlier or later.
"Meals": the planned meals, as all-day events.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import PantryConfigEntry
from .const import PREP_EVENT_MINUTES
from .data import prep_items
from .entity import PantryEntity


async def async_setup_entry(hass: HomeAssistant, entry: PantryConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    async_add_entities([PrepCalendar(c), MealsCalendar(c)])


def _overlaps(event: CalendarEvent, start: datetime, end: datetime) -> bool:
    return event.start_datetime_local < end and event.end_datetime_local > start


class _PantryCalendar(PantryEntity, CalendarEntity):
    def _events(self) -> list[CalendarEvent]:
        raise NotImplementedError

    @property
    def event(self) -> CalendarEvent | None:
        """The current or next event."""
        now = dt_util.now()
        upcoming = [e for e in self._events() if e.end_datetime_local > now]
        return min(upcoming, key=lambda e: e.start_datetime_local) if upcoming else None

    async def async_get_events(self, hass: HomeAssistant, start_date: datetime,
                               end_date: datetime) -> list[CalendarEvent]:
        return [e for e in self._events() if _overlaps(e, start_date, end_date)]


class PrepCalendar(_PantryCalendar):
    _attr_translation_key = "meal_prep"
    _attr_icon = "mdi:pot-steam-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "meal_prep")

    def _events(self) -> list[CalendarEvent]:
        events = []
        for p in prep_items(self.coordinator.data):
            when = "tomorrow's" if p.get("day") == "day_before" else "today's"
            events.append(CalendarEvent(
                start=p["due_dt"], end=p["due_dt"] + timedelta(minutes=PREP_EVENT_MINUTES),
                summary=p["task"], uid=f"pantry-prep-{p['id']}",
                description=f"For {when} {p['slot']}: {p['meal']}"))
        return events


class MealsCalendar(_PantryCalendar):
    _attr_translation_key = "meals"
    _attr_icon = "mdi:silverware-fork-knife"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "meals")

    def _events(self) -> list[CalendarEvent]:
        events = []
        for m in (self.coordinator.data or {}).get("meals", []):
            try:
                day = date.fromisoformat(m["date"])
            except (KeyError, TypeError, ValueError):
                continue
            lines = []
            if m.get("ingredients"):
                lines.append(f"Ingredients: {m['ingredients']}")
            lines += [f"Prep, {p['when']}: {p['task']}" for p in m.get("prep", [])]
            events.append(CalendarEvent(
                start=day, end=day + timedelta(days=1), summary=f"{m['slot'].capitalize()}{' for ' + m['for'] if m.get('for') else ''}: {m['meal']}",
                uid=f"pantry-meal-{m['plan_id']}", description="\n".join(lines) or None))
        return events

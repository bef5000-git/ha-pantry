from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from . import fake_pantry
from .conftest import DOMAIN

KEYS = ("online", "prep_today", "prep_tonight", "next_prep", "meals_today", "meal_prep", "meals")
ENTITY_IDS = {
    "online": "binary_sensor.pantry_online", "prep_today": "sensor.pantry_prep_today",
    "prep_tonight": "sensor.pantry_prep_tonight", "next_prep": "sensor.pantry_next_prep",
    "meals_today": "sensor.pantry_meals_today", "meal_prep": "calendar.pantry_meal_prep",
    "meals": "calendar.pantry_meals",
}


async def test_unique_ids_are_stable(hass: HomeAssistant, entry):
    """Unique ids are Pantry's instance id + a fixed key: the same after removing and re-adding."""
    reg = er.async_get(hass)
    got = {e.unique_id: e.entity_id for e in er.async_entries_for_config_entry(reg, entry.entry_id)}
    assert got == {f"{fake_pantry.INSTANCE_ID}_{k}": v for k, v in ENTITY_IDS.items()}
    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, fake_pantry.INSTANCE_ID)})
    assert device.name == "Pantry" and device.sw_version == "2026.11.08"

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    again = MockConfigEntry(domain=DOMAIN, unique_id=fake_pantry.INSTANCE_ID,
                            data={"url": "http://192.0.2.1:8765", "token": fake_pantry.TOKEN})
    again.add_to_hass(hass)
    hass.config_entries.async_update_entry(again, data={"url": fake_pantry.URL, "token": fake_pantry.TOKEN})
    await hass.config_entries.async_setup(again.entry_id)
    await hass.async_block_till_done()
    got2 = {e.unique_id: e.entity_id for e in er.async_entries_for_config_entry(reg, again.entry_id)}
    assert got2 == got                     # same unique ids, same entity ids (no "_2")


async def test_states(hass: HomeAssistant, entry):
    today = hass.states.get("sensor.pantry_prep_today")
    assert today.state == "1"
    assert today.attributes["summary"] == "Take the chicken out of the freezer (Chicken Tacos, dinner)"
    tonight = hass.states.get("sensor.pantry_prep_tonight")
    assert tonight.state == "1" and tonight.attributes["summary"] == "Move the roast to the fridge (Pot Roast, dinner)"
    meals = hass.states.get("sensor.pantry_meals_today")
    assert meals.state == "Oatmeal (breakfast), French toast sticks (breakfast, Kids), Chicken Tacos (dinner)"
    assert meals.attributes["breakfast"] == ["Oatmeal", "French toast sticks (Kids)"]
    assert [m["for"] for m in meals.attributes["meals"]] == ["everyone", "Kids", "everyone"]
    nxt = hass.states.get("sensor.pantry_next_prep")
    assert nxt.attributes["device_class"] == "timestamp" and dt_util.parse_datetime(nxt.state) > dt_util.now()
    online = hass.states.get("binary_sensor.pantry_online")
    assert online.state == "on" and online.attributes["device_class"] == "connectivity"


async def test_calendars(hass: HomeAssistant, entry):
    start = dt_util.start_of_local_day()
    resp = await hass.services.async_call(
        "calendar", "get_events",
        {"entity_id": ["calendar.pantry_meal_prep", "calendar.pantry_meals"],
         "start_date_time": start.isoformat(), "end_date_time": (start + timedelta(days=2)).isoformat()},
        blocking=True, return_response=True)
    prep = resp["calendar.pantry_meal_prep"]["events"]
    assert [e["summary"] for e in prep] == ["Take the chicken out of the freezer", "Move the roast to the fridge",
                                           "Start the crock pot on low"]
    assert prep[1]["description"] == "For tomorrow's dinner: Pot Roast"
    meals = resp["calendar.pantry_meals"]["events"]
    assert [e["summary"] for e in meals] == ["Breakfast: Oatmeal", "Breakfast for Kids: French toast sticks",
                                            "Dinner: Chicken Tacos", "Dinner: Pot Roast"]


async def test_pc_off(hass: HomeAssistant, tz, pantry):
    """PC off when Home Assistant starts: still set up; online off, the rest unavailable; back on next poll."""
    pantry(exc=aiohttp.ClientError())
    e = MockConfigEntry(domain=DOMAIN, unique_id=fake_pantry.INSTANCE_ID,
                        data={"url": fake_pantry.URL, "token": fake_pantry.TOKEN})
    e.add_to_hass(hass)
    await hass.config_entries.async_setup(e.entry_id)
    await hass.async_block_till_done()
    assert e.state is ConfigEntryState.LOADED
    assert hass.states.get("binary_sensor.pantry_online").state == "off"
    assert hass.states.get("sensor.pantry_prep_today").state == "unavailable"
    assert hass.states.get("calendar.pantry_meals").state == "unavailable"
    pantry()
    await e.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.pantry_online").state == "on"
    assert hass.states.get("sensor.pantry_prep_today").state == "1"


async def test_unload(hass: HomeAssistant, entry):
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED

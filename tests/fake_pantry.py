"""What Pantry's GET /api/ha/state returns, built around a given day (made-up meals)."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")
INSTANCE_ID = "0123456789abcdef0123456789abcdef"
TOKEN = "test-token"
URL = "http://pantry.test:8765"


def _due(day: date, hhmm: str) -> str:
    h, m = map(int, hhmm.split(":"))
    return datetime.combine(day, time(h, m), TZ).isoformat(timespec="minutes")


def state(today: date, version: str = "2026.11.08", integration_min: str | None = "2026.11.8",
          instance_id: str | None = INSTANCE_ID) -> dict:
    tomorrow = today + timedelta(days=1)
    meals = [
        {"plan_id": 1, "date": today.isoformat(), "slot": "breakfast", "meal": "Oatmeal", "added_by": "Sam",
         "ingredients": "oats (1/2 cup), milk (1 cup)", "prep": [], "for": None},
        {"plan_id": 4, "date": today.isoformat(), "slot": "breakfast", "meal": "French toast sticks",
         "added_by": "Sam", "ingredients": "French toast sticks", "prep": [], "for": "Kids"},
        {"plan_id": 2, "date": today.isoformat(), "slot": "dinner", "meal": "Chicken Tacos", "added_by": "Sam",
         "ingredients": "chicken thighs, tortillas",
         "prep": [{"task": "Take the chicken out of the freezer", "when": "7:00 am"}]},
        {"plan_id": 3, "date": tomorrow.isoformat(), "slot": "dinner", "meal": "Pot Roast", "added_by": "Sam",
         "ingredients": "chuck roast",
         "prep": [{"task": "Move the roast to the fridge", "when": "the night before, 8:00 pm"},
                  {"task": "Start the crock pot on low", "when": "8:00 am"}]},
    ]
    prep = [
        {"id": "2-1", "plan_id": 2, "task": "Take the chicken out of the freezer", "meal": "Chicken Tacos",
         "slot": "dinner", "meal_date": today.isoformat(), "day": "day_of", "time": "07:00", "when": "7:00 am",
         "due": _due(today, "07:00")},
        {"id": "3-2", "plan_id": 3, "task": "Move the roast to the fridge", "meal": "Pot Roast", "slot": "dinner",
         "meal_date": tomorrow.isoformat(), "day": "day_before", "time": "20:00",
         "when": "the night before, 8:00 pm", "due": _due(today, "20:00")},
        {"id": "3-3", "plan_id": 3, "task": "Start the crock pot on low", "meal": "Pot Roast", "slot": "dinner",
         "meal_date": tomorrow.isoformat(), "day": "day_of", "time": "08:00", "when": "8:00 am",
         "due": _due(tomorrow, "08:00")},
    ]
    out = {"version": version, "generated": datetime.now(TZ).isoformat(timespec="seconds"),
           "meals": meals, "prep": prep}
    if integration_min:
        out["integration_min"] = integration_min
    if instance_id:
        out["instance_id"] = instance_id
    return out

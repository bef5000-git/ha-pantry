"""Turns Pantry's data into what the sensors and calendars show. No Home Assistant objects here."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value)


def prep_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Prep tasks with their due time as an aware datetime."""
    out = []
    for p in (data or {}).get("prep", []):
        try:
            out.append({**p, "due_dt": _parse(p["due"])})
        except (KeyError, ValueError):
            continue
    return out


def prep_today(data: dict[str, Any], today: date) -> list[dict[str, Any]]:
    """Tasks for today's meals that are done that day ("that morning")."""
    return [p for p in prep_items(data) if p.get("day") == "day_of" and p.get("meal_date") == today.isoformat()]


def prep_tonight(data: dict[str, Any], today: date) -> list[dict[str, Any]]:
    """Tasks to do this evening for tomorrow's meals ("the night before")."""
    tomorrow = (today + timedelta(days=1)).isoformat()
    return [p for p in prep_items(data) if p.get("day") == "day_before" and p.get("meal_date") == tomorrow]


def next_prep(data: dict[str, Any], now: datetime) -> dict[str, Any] | None:
    upcoming = [p for p in prep_items(data) if p["due_dt"] > now]
    return min(upcoming, key=lambda p: p["due_dt"]) if upcoming else None


def summary(items: list[dict[str, Any]]) -> str:
    """One line per task, ready for a notification message."""
    return "\n".join(f"{p['task']} ({p['meal']}, {p['slot']})" for p in items)


def task_list(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"task": p["task"], "meal": p["meal"], "slot": p["slot"], "time": p.get("time"),
             "due": p.get("due")} for p in items]


def meals_on(data: dict[str, Any], day: date) -> list[dict[str, Any]]:
    return [m for m in (data or {}).get("meals", []) if m.get("date") == day.isoformat()]


def meal_name(m: dict[str, Any]) -> str:
    """"Uncrustables (Kids)" when Pantry says whose meal it is, else just the meal."""
    return f"{m['meal']} ({m['for']})" if m.get("for") else m["meal"]

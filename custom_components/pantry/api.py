"""Talks to Pantry on your PC: one read-only call, GET /api/ha/state."""
from __future__ import annotations

import asyncio
from typing import Any

import aiohttp


class PantryAuthError(Exception):
    """Pantry didn't accept the token."""


class PantryConnectionError(Exception):
    """Pantry couldn't be reached, or answered with an error."""


async def fetch_state(session: aiohttp.ClientSession, url: str, token: str) -> dict[str, Any]:
    try:
        async with session.get(
            f"{url.rstrip('/')}/api/ha/state",
            headers={"Authorization": f"Bearer {token}"},
            timeout=aiohttp.ClientTimeout(total=20),
        ) as resp:
            if resp.status in (401, 403):
                raise PantryAuthError
            if resp.status != 200:
                raise PantryConnectionError(f"Pantry answered HTTP {resp.status}")
            data = await resp.json()
    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        raise PantryConnectionError(str(err) or type(err).__name__) from err
    if not isinstance(data, dict) or "meals" not in data or "prep" not in data:
        raise PantryConnectionError("That address answered, but it isn't Pantry")
    return data

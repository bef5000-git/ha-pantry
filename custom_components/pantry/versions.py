"""Comparing Pantry's and the integration's versions (e.g. "2026.11.07.4" and "2026.11.8")."""
from __future__ import annotations

import re


def parse(version: str | None) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", version or ""))


def older(version: str | None, than: str | None) -> bool:
    """True when `version` is older than `than`. Unknown versions count as older; no `than` means no limit."""
    if not than:
        return False
    return parse(version) < parse(than)

"""The decoding settings the meter compares."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DecodingSetting:
    """A named sampling configuration. `top_p` is None when it is left at the provider default."""

    name: str
    temperature: float
    top_p: float | None = None


DEFAULT_SETTINGS = (
    DecodingSetting("t0", 0.0),
    DecodingSetting("t07", 0.7),
    DecodingSetting("t10", 1.0, 0.9),
)

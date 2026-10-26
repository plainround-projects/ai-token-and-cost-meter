"""Helpers that read and validate environment variables (twelve-factor configuration)."""

from __future__ import annotations

from collections.abc import Collection, Mapping


class ConfigurationError(ValueError):
    """An environment variable is missing or has an unusable value."""


def text(environ: Mapping[str, str], name: str, default: str) -> str:
    """A non-empty string, or `default` when the variable is unset."""
    value = environ.get(name, default).strip()
    if not value:
        raise ConfigurationError(f"{name} must not be empty")
    return value


def optional_text(environ: Mapping[str, str], name: str) -> str | None:
    """The variable's text, or None when it is unset or blank."""
    value = environ.get(name, "").strip()
    return value or None


def positive_int(environ: Mapping[str, str], name: str, default: int) -> int:
    """An integer of 1 or more."""
    raw = environ.get(name, str(default)).strip()
    if not raw.isdigit() or int(raw) < 1:
        raise ConfigurationError(f"{name} must be a positive integer, got {raw!r}")
    return int(raw)


def non_negative_int(environ: Mapping[str, str], name: str, default: int) -> int:
    """An integer of 0 or more."""
    raw = environ.get(name, str(default)).strip()
    if not raw.isdigit():
        raise ConfigurationError(f"{name} must be a non-negative integer, got {raw!r}")
    return int(raw)


def positive_float(environ: Mapping[str, str], name: str, default: float) -> float:
    """A number greater than zero."""
    raw = environ.get(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError as error:
        raise ConfigurationError(f"{name} must be a number, got {raw!r}") from error
    if value <= 0:
        raise ConfigurationError(f"{name} must be greater than zero, got {raw!r}")
    return value


def non_negative_float(environ: Mapping[str, str], name: str, default: float) -> float:
    """A number of 0 or more."""
    raw = environ.get(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError as error:
        raise ConfigurationError(f"{name} must be a number, got {raw!r}") from error
    if value < 0:
        raise ConfigurationError(f"{name} must not be negative, got {raw!r}")
    return value


def choice(environ: Mapping[str, str], name: str, default: str, allowed: Collection[str]) -> str:
    """One of the `allowed` strings."""
    value = text(environ, name, default)
    if value not in allowed:
        raise ConfigurationError(f"{name} must be one of {sorted(allowed)}, got {value!r}")
    return value

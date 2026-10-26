"""Configuration from the environment, validated once at startup (twelve-factor)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from token_meter.infrastructure.env import (
    ConfigurationError,
    choice,
    non_negative_float,
    optional_text,
    positive_int,
    text,
)

_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")


@dataclass(frozen=True, slots=True)
class MeterSettings:
    """Everything the programs read from the environment. See .env.example for each variable."""

    prompts_path: Path
    prices_path: Path
    journal_path: Path
    max_output_tokens: int
    repeats: int
    price_max_age_days: int
    throttle_seconds: float
    budget: Decimal | None
    log_level: str

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> MeterSettings:
        env = os.environ if environ is None else environ
        raw_budget = optional_text(env, "BUDGET_USD")
        try:
            budget = Decimal(raw_budget) if raw_budget else None
        except InvalidOperation as error:
            raise ConfigurationError(f"BUDGET_USD must be a decimal number, got {raw_budget!r}") from error
        return cls(
            prompts_path=Path(text(env, "PROMPTS_PATH", "data/prompts.jsonl")),
            prices_path=Path(text(env, "PRICES_PATH", "data/prices.json")),
            journal_path=Path(text(env, "JOURNAL_PATH", "out/journal.csv")),
            max_output_tokens=positive_int(env, "MAX_OUTPUT_TOKENS", 200),
            repeats=positive_int(env, "REPEATS", 3),
            price_max_age_days=positive_int(env, "PRICE_MAX_AGE_DAYS", 30),
            throttle_seconds=non_negative_float(env, "THROTTLE_SECONDS", 0.0),
            budget=budget,
            log_level=choice({**env, "LOG_LEVEL": env.get("LOG_LEVEL", "INFO").upper()}, "LOG_LEVEL", "INFO", _LEVELS),
        )

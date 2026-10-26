"""The dated price table. Prices change, so a table older than the allowed age is refused."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from token_meter.domain.errors import DomainError


class StalePrices(DomainError):
    """The price table was read too long ago to trust."""


@dataclass(frozen=True, slots=True)
class PriceTable:
    """Price per 1,000 input and output tokens, with the day the numbers were read."""

    model: str
    input_per_1k: Decimal
    output_per_1k: Decimal
    read_date: date

    def cost(self, input_tokens: int, output_tokens: int) -> Decimal:
        """Cost in dollars of a call with these token counts."""
        return input_tokens * self.input_per_1k / 1000 + output_tokens * self.output_per_1k / 1000

    def require_fresh(self, today: date, max_age_days: int) -> None:
        """Raise `StalePrices` when the table is older than `max_age_days` (or dated in the future)."""
        age = (today - self.read_date).days
        if age < 0:
            raise StalePrices(f"price table is dated {self.read_date}, which is after today ({today})")
        if age > max_age_days:
            raise StalePrices(
                f"price table was read on {self.read_date}, {age} days ago (limit {max_age_days}); "
                "read the current prices, update data/prices.json and its read_date"
            )

"""Estimate tokens and cost before any call is made."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal

from token_meter.domain.errors import DomainError
from token_meter.domain.pricing import PriceTable
from token_meter.domain.prompts import Kind, PromptRecord


class BudgetExceeded(DomainError):
    """The estimate is above the budget, so the run must not start."""


@dataclass(frozen=True, slots=True)
class TokenEstimator:
    """Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.

    The overhead is zero and the ratio is 4 until you measure them: `calibrate` derives both from billed usage,
    with one ratio per kind of prompt because prose, code and other languages tokenize at different densities.
    """

    chars_per_token: float = 4.0
    per_call_overhead: int = 0
    by_kind: Mapping[Kind, float] = field(default_factory=dict)

    def tokens(self, text: str, system: str = "", kind: Kind | None = None) -> int:
        """Estimated input tokens of one call that sends `text` (and `system`)."""
        ratio = self.by_kind.get(kind, self.chars_per_token) if kind else self.chars_per_token
        return max(1, math.ceil((len(text) + len(system)) / ratio)) + self.per_call_overhead

    def with_overhead(self, overhead: int) -> TokenEstimator:
        """The same ratios with a different fixed overhead."""
        return TokenEstimator(self.chars_per_token, overhead, self.by_kind)

    def with_ratios(self, by_kind: Mapping[Kind, float]) -> TokenEstimator:
        """The same overhead with measured characters-per-token ratios per kind."""
        return TokenEstimator(self.chars_per_token, self.per_call_overhead, by_kind)


@dataclass(frozen=True, slots=True)
class RunEstimate:
    """What a run is expected to cost, before the first call."""

    calls: int
    input_tokens: int
    output_tokens: int
    cost: Decimal


def estimate_run(
    prompts: Sequence[PromptRecord],
    calls_per_prompt: int,
    max_output_tokens: int,
    prices: PriceTable,
    estimator: TokenEstimator,
    system: str = "",
) -> RunEstimate:
    """Estimate a run of `calls_per_prompt` calls for each prompt, each assumed to use the full output cap."""
    input_tokens = sum(estimator.tokens(p.text, system, p.kind) for p in prompts) * calls_per_prompt
    calls = len(prompts) * calls_per_prompt
    output_tokens = calls * max_output_tokens
    return RunEstimate(calls, input_tokens, output_tokens, prices.cost(input_tokens, output_tokens))


def require_within_budget(estimate: RunEstimate, budget: Decimal | None) -> None:
    """Raise `BudgetExceeded` when a budget is set and the estimate is above it."""
    if budget is not None and estimate.cost > budget:
        raise BudgetExceeded(f"estimated cost {estimate.cost:.4f} exceeds budget {budget}")

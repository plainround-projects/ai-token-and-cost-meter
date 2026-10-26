"""Build the report from the journal: estimated against billed, calibration and spread."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from token_meter.application.ports import Journal
from token_meter.domain.analysis import (
    CostCheck,
    EstimateReport,
    SpreadReport,
    calibrate,
    calibrate_overhead,
    compare_estimates,
    leave_one_out,
    measure_spread,
)
from token_meter.domain.estimation import TokenEstimator
from token_meter.domain.pricing import PriceTable
from token_meter.domain.prompts import PromptRecord


@dataclass(frozen=True, slots=True)
class MeterReport:
    """Everything the `report` command prints."""

    calls: int
    billed_cost_total: str
    naive: EstimateReport
    overhead: int
    with_overhead: EstimateReport
    ratios: dict[str, float]
    forecast: EstimateReport
    cost_check: CostCheck
    spread: SpreadReport


def build_report(
    journal: Journal,
    prompts: Sequence[PromptRecord],
    prices: PriceTable,
    naive: TokenEstimator,
    max_output_tokens: int,
) -> MeterReport:
    """Compare the naive estimator with the bill, add the measured overhead, then forecast each prompt leave-one-out."""
    rows = journal.rows()
    overhead = calibrate_overhead(prompts, rows, naive)
    full = calibrate(prompts, rows, naive)
    forecast = leave_one_out(prompts, rows, naive, prices, max_output_tokens)
    total = sum((prices.cost(r.input_tokens, r.output_tokens) for r in rows), start=prices.cost(0, 0))
    return MeterReport(
        calls=len(rows),
        billed_cost_total=f"{total:.6f}",
        naive=compare_estimates(prompts, rows, naive, known_overhead=overhead),
        overhead=overhead,
        with_overhead=compare_estimates(prompts, rows, naive.with_overhead(overhead)),
        ratios={kind.value: round(ratio, 2) for kind, ratio in full.estimator.by_kind.items()},
        forecast=forecast.input_tokens,
        cost_check=forecast.cost,
        spread=measure_spread(prompts, rows, prices),
    )

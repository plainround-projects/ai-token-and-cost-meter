from datetime import date
from decimal import Decimal

import pytest

from tests.conftest import prompt
from token_meter.domain.estimation import BudgetExceeded, TokenEstimator, estimate_run, require_within_budget
from token_meter.domain.pricing import PriceTable, StalePrices
from token_meter.domain.prompts import Kind

PRICES = PriceTable("m", Decimal("0.00015"), Decimal("0.0006"), date(2026, 10, 26))


def test_cost_uses_separate_input_and_output_prices():
    assert PRICES.cost(1000, 1000) == Decimal("0.00075")
    assert PRICES.cost(0, 0) == 0


def test_a_fresh_table_is_accepted_and_an_old_one_is_refused():
    PRICES.require_fresh(date(2026, 11, 20), 30)
    with pytest.raises(StalePrices, match="read on 2026-10-26, 36 days ago"):
        PRICES.require_fresh(date(2026, 12, 1), 30)


def test_a_table_dated_in_the_future_is_refused():
    with pytest.raises(StalePrices, match="after today"):
        PRICES.require_fresh(date(2026, 10, 1), 30)


def test_the_estimator_divides_characters_and_adds_the_overhead():
    assert TokenEstimator().tokens("a" * 40) == 10
    assert TokenEstimator(per_call_overhead=28).tokens("a" * 40) == 38
    assert TokenEstimator().tokens("") == 1
    assert TokenEstimator().tokens("a" * 40, system="b" * 8) == 12


def test_with_overhead_returns_a_new_estimator():
    base = TokenEstimator()
    assert base.with_overhead(5).per_call_overhead == 5
    assert base.per_call_overhead == 0


def test_a_run_estimate_counts_calls_tokens_and_cost():
    prompts = [prompt("a", Kind.SHORT, "a" * 40), prompt("b", Kind.SHORT, "a" * 80)]
    estimate = estimate_run(
        prompts, calls_per_prompt=9, max_output_tokens=200, prices=PRICES, estimator=TokenEstimator()
    )
    assert estimate.calls == 18
    assert estimate.input_tokens == (10 + 20) * 9
    assert estimate.output_tokens == 18 * 200
    assert estimate.cost == PRICES.cost(270, 3600)


def test_a_budget_below_the_estimate_refuses_and_no_budget_never_does():
    estimate = estimate_run([prompt("a", Kind.SHORT, "hi")], 1, 100, PRICES, TokenEstimator())
    with pytest.raises(BudgetExceeded, match="exceeds budget"):
        require_within_budget(estimate, Decimal("0.00001"))
    require_within_budget(estimate, Decimal("1"))
    require_within_budget(estimate, None)

from datetime import date
from decimal import Decimal

import pytest

from tests.conftest import prompt, row
from token_meter.domain.analysis import (
    NotEnoughData,
    calibrate,
    calibrate_overhead,
    compare_estimates,
    explain_gap,
    extract_label,
    leave_one_out,
    measure_spread,
)
from token_meter.domain.estimation import TokenEstimator
from token_meter.domain.llm import StopReason
from token_meter.domain.pricing import PriceTable
from token_meter.domain.prompts import Kind

PRICES = PriceTable("m", Decimal("0.001"), Decimal("0.002"), date(2026, 10, 26))
PROMPTS = [
    prompt("s", Kind.SHORT, "a" * 40),  # 10 estimated
    prompt("l", Kind.LONG, "a" * 400),  # 100 estimated
    prompt("g", Kind.LANGUAGE, "a" * 40),  # 10 estimated
    prompt("b", Kind.LABEL, "a" * 40, "billing"),
]
# billed = estimate + 28, except the language prompt, which carries 34 extra
T0 = [row("s", "t0", 0, 38, 5), row("l", "t0", 0, 128, 5), row("g", "t0", 0, 44, 5), row("b", "t0", 0, 38, 5)]


def test_the_naive_estimator_is_off_most_on_short_prompts():
    report = compare_estimates(PROMPTS, T0, TokenEstimator())
    errors = {k.kind: k.error for k in report.by_kind}
    assert errors["short"] == pytest.approx(-28 / 38)
    assert errors["long"] == pytest.approx(-28 / 128)
    assert report.total.estimated == 130
    assert report.total.billed == 248


def test_the_largest_gap_names_a_cause():
    gap = compare_estimates(PROMPTS, T0, TokenEstimator(), known_overhead=28).largest_gap
    assert gap.prompt_id == "g"
    assert "template overhead" in gap.cause


def test_the_measured_overhead_is_the_median_residual():
    assert calibrate_overhead(PROMPTS, T0, TokenEstimator()) == 28


def test_with_the_overhead_added_the_total_error_nearly_vanishes():
    report = compare_estimates(PROMPTS, T0, TokenEstimator().with_overhead(28))
    assert abs(report.total.error) < 0.03
    assert report.largest_gap.kind is Kind.LANGUAGE
    assert "tokens per character" in report.largest_gap.cause


def test_a_missing_setting_is_reported():
    with pytest.raises(NotEnoughData, match="'t0'"):
        compare_estimates(PROMPTS, [row("s", "t07", 0, 1, 1)], TokenEstimator())
    with pytest.raises(NotEnoughData):
        calibrate_overhead(PROMPTS, [], TokenEstimator())


@pytest.mark.parametrize(
    ("kind", "estimated", "billed", "missing", "fragment"),
    [
        (Kind.SHORT, 10, 38, 28, "template overhead"),
        (Kind.LANGUAGE, 10, 80, 28, "non-English"),
        (Kind.CODE, 10, 80, 28, "code, JSON"),
        (Kind.LONG, 10, 80, 28, "less compactly"),
        (Kind.SHORT, 38, 44, 0, "rounding"),
        (Kind.LONG, 120, 100, 0, "above the bill"),
    ],
)
def test_explain_gap_picks_the_cause_from_the_kind_and_the_size(kind, estimated, billed, missing, fragment):
    assert fragment in explain_gap(kind, estimated, billed, missing)


def test_label_extraction_finds_the_first_category_word():
    assert extract_label("Billing.") == "billing"
    assert extract_label("The category is shipping, not billing") == "shipping"
    assert extract_label("no idea") == "none"


def test_spread_counts_distinct_answers_agreement_and_cost():
    rows = [
        row("s", "t0", 0, 10, 4, "same"),
        row("s", "t0", 1, 10, 4, "same"),
        row("s", "t0", 2, 10, 4, " same "),
        row("b", "t0", 0, 10, 2, "billing"),
        row("b", "t0", 1, 10, 2, "billing"),
        row("b", "t0", 2, 10, 2, "billing"),
        row("s", "t10", 0, 10, 6, "a"),
        row("s", "t10", 1, 10, 6, "b"),
        row("s", "t10", 2, 10, 6, "c", StopReason.LENGTH),
        row("b", "t10", 0, 10, 2, "billing"),
        row("b", "t10", 1, 10, 2, "shipping"),
        row("b", "t10", 2, 10, 2, "billing"),
    ]
    report = measure_spread(PROMPTS, rows, PRICES)
    t0, t10 = report.settings
    assert t0.setting == "t0"
    assert t0.mean_distinct_answers == 1.0
    assert t0.label_agreement == 1.0
    assert report.zero_temperature_identical
    assert t10.mean_distinct_answers == 2.5
    assert t10.label_agreement == pytest.approx(2 / 3)
    assert t10.mean_output_tokens == 4.0
    assert t10.length_stop_share == pytest.approx(1 / 6)
    assert t10.cost_per_1000 == (PRICES.cost(10, 6) * 3 + PRICES.cost(10, 2) * 3) / 6 * 1000


def test_a_setting_without_label_prompts_has_no_agreement_and_an_empty_journal_is_refused():
    report = measure_spread(PROMPTS, [row("s", "t07", 0, 1, 1)], PRICES)
    assert report.settings[0].label_agreement is None
    assert not report.zero_temperature_identical
    with pytest.raises(NotEnoughData):
        measure_spread(PROMPTS, [], PRICES)


def test_calibration_measures_overhead_a_density_per_kind_and_answer_length():
    fit = [prompt("s", Kind.SHORT, "a" * 40), prompt("s2", Kind.SHORT, "a" * 80), prompt("l", Kind.LONG, "a" * 300)]
    rows = [
        row("s", "t0", 0, 38, 10),
        row("s", "t07", 0, 38, 20),
        row("s2", "t0", 0, 48, 10),
        row("l", "t0", 0, 128, 40),
        row("l", "t07", 0, 128, 60),
    ]
    calibration = calibrate(fit, rows, TokenEstimator())
    assert calibration.estimator.per_call_overhead == 28
    assert calibration.estimator.by_kind[Kind.SHORT] == pytest.approx(4.0)
    assert calibration.estimator.by_kind[Kind.LONG] == pytest.approx(3.0)
    assert calibration.mean_output[(Kind.SHORT, "t07")] == 20
    assert calibration.estimator.tokens("a" * 30, kind=Kind.LONG) == 10 + 28


def test_each_prompt_is_forecast_by_an_estimator_that_never_saw_it():
    prompts = [prompt(f"s{i}", Kind.SHORT, "a" * (40 + 4 * i)) for i in range(4)]
    rows = [row(p.id, "t0", r, 10 + i + 28, 10) for i, p in enumerate(prompts) for r in range(2)]
    result = leave_one_out(prompts, rows, TokenEstimator(), PRICES, max_output_tokens=200)
    assert result.cost.calls == 8
    assert result.cost.within
    assert abs(result.input_tokens.total.error) < 0.02
    assert result.cost.ceiling > result.cost.billed


def test_an_outlier_prompt_leaves_a_visible_gap_even_when_the_totals_look_fine():
    prompts = [prompt(f"s{i}", Kind.SHORT, "a" * 40) for i in range(3)] + [prompt("odd", Kind.SHORT, "a" * 40)]
    rows = [row(p.id, "t0", 0, 38, 10) for p in prompts[:3]] + [row("odd", "t0", 0, 138, 10)]
    result = leave_one_out(prompts, rows, TokenEstimator(), PRICES, 200)
    gap = result.input_tokens.largest_gap
    assert abs(gap.billed - gap.estimated) / gap.billed > 0.4
    assert abs(result.input_tokens.total.error) < 0.05


def test_a_kind_with_one_prompt_borrows_the_answer_length_of_the_same_setting():
    prompts = [prompt("s", Kind.SHORT, "a" * 40), prompt("l", Kind.LONG, "a" * 400)]
    rows = [row("s", "t0", 0, 38, 10), row("l", "t0", 0, 128, 30)]
    result = leave_one_out(prompts, rows, TokenEstimator(), PRICES, 200)
    assert result.cost.calls == 2


def test_leave_one_out_needs_two_prompts():
    with pytest.raises(NotEnoughData, match="at least two"):
        leave_one_out([prompt("a", Kind.SHORT, "x")], [row("a", "t0", 0, 1, 1)], TokenEstimator(), PRICES, 200)

from datetime import date
from decimal import Decimal

import pytest

from tests.conftest import MemoryJournal, ScriptedModel, prompt, row
from token_meter.application.run_meter import RunMeter, RunPlan, estimate_pending, plan_keys
from token_meter.domain.decoding import DEFAULT_SETTINGS
from token_meter.domain.errors import UnsupportedParameter
from token_meter.domain.estimation import BudgetExceeded, TokenEstimator
from token_meter.domain.pricing import PriceTable
from token_meter.domain.prompts import Kind

PRICES = PriceTable("m", Decimal("0.001"), Decimal("0.002"), date(2026, 10, 26))
PROMPTS = [prompt("a", Kind.SHORT, "a" * 40), prompt("b", Kind.SHORT, "b" * 80)]


def plan(**changes):
    base = {
        "prompts": PROMPTS,
        "settings": DEFAULT_SETTINGS,
        "repeats": 3,
        "max_output_tokens": 50,
        "prices": PRICES,
        "estimator": TokenEstimator(),
    }
    return RunPlan(**{**base, **changes})


def test_a_plan_covers_every_prompt_setting_and_repeat():
    assert len(plan_keys(plan())) == 2 * 3 * 3


def test_a_run_makes_every_call_and_journals_one_row_each():
    model, journal = ScriptedModel(), MemoryJournal()
    summary = RunMeter(model, journal).run(plan())
    assert (summary.calls_made, summary.calls_skipped, summary.interrupted) == (18, 0, False)
    assert len(journal.rows()) == 18
    assert len({r.key for r in journal.rows()}) == 18


def test_the_output_cap_is_the_same_for_every_setting_and_only_sampling_changes():
    model = ScriptedModel()
    RunMeter(model, MemoryJournal()).run(plan())
    assert {r.max_output_tokens for r in model.requests} == {50}
    assert {(r.temperature, r.top_p) for r in model.requests} == {(0.0, None), (0.7, None), (1.0, 0.9)}


def test_every_request_carries_a_unique_tag():
    model = ScriptedModel()
    RunMeter(model, MemoryJournal()).run(plan())
    assert len({r.tag for r in model.requests}) == 18
    assert model.requests[0].tag == "a/t0/0"


def test_the_estimate_is_checked_against_the_budget_before_the_first_call():
    model, journal = ScriptedModel(), MemoryJournal()
    with pytest.raises(BudgetExceeded):
        RunMeter(model, journal).run(plan(budget=Decimal("0.000001")))
    assert model.requests == []
    assert journal.rows() == []


def test_a_restart_skips_calls_the_journal_already_holds():
    journal = MemoryJournal([row("a", "t0", 0, 1, 1), row("a", "t0", 1, 1, 1)])
    model = ScriptedModel()
    summary = RunMeter(model, journal).run(plan())
    assert (summary.calls_made, summary.calls_skipped) == (16, 2)
    assert "a/t0/0" not in {r.tag for r in model.requests}
    assert len({r.key for r in journal.rows()}) == len(journal.rows()) == 18


def test_the_estimate_only_counts_the_calls_still_to_make():
    journal = MemoryJournal([row("a", s.name, r, 1, 1) for s in DEFAULT_SETTINGS for r in range(3)])
    estimate = estimate_pending(plan(), journal.done_keys())
    assert estimate.calls == 9
    assert estimate.input_tokens == 20 * 9
    assert estimate.output_tokens == 9 * 50


def test_a_stop_request_ends_the_run_cleanly_between_calls():
    stops = iter([False, False, True])
    summary = RunMeter(ScriptedModel(), MemoryJournal(), stop_requested=lambda: next(stops)).run(plan())
    assert summary.interrupted
    assert summary.calls_made == 2


def test_a_model_that_rejects_sampling_cannot_run_the_three_settings():
    model = ScriptedModel(sampling=False)
    with pytest.raises(UnsupportedParameter, match="does not accept temperature"):
        RunMeter(model, MemoryJournal()).run(plan())
    assert model.requests == []


def test_throttling_pauses_after_each_call():
    pauses: list[float] = []
    RunMeter(ScriptedModel(), MemoryJournal(), sleep=pauses.append).run(plan(throttle_seconds=0.2, repeats=1))
    assert pauses == [0.2] * 6

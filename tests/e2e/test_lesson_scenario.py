"""The lesson's scenario from the prompt file to the report, on the recorded model."""

import json
from pathlib import Path

import pytest

from token_meter.application.report import build_report
from token_meter.domain.estimation import TokenEstimator
from token_meter.domain.prompts import PromptSetSpec, validate_prompt_set
from token_meter.infrastructure.csv_journal import CsvJournal
from token_meter.infrastructure.files import load_prices, load_prompts
from token_meter.interfaces.cli import EXIT_OK, EXIT_REFUSED, main

pytestmark = pytest.mark.e2e

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def scenario(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "recorded")
    monkeypatch.setenv("RECORDINGS_PATH", str(REPO / "tests" / "fixtures" / "recordings"))
    monkeypatch.setenv("JOURNAL_PATH", str(tmp_path / "journal.csv"))
    monkeypatch.setenv("PROMPTS_PATH", str(REPO / "data" / "prompts.jsonl"))
    monkeypatch.setenv("PRICES_PATH", str(REPO / "data" / "prices.json"))
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    return tmp_path / "journal.csv"


def test_step_1_the_prompt_file_has_fifty_rows_in_five_kinds_one_long_and_the_price_file_is_dated():
    prompts = load_prompts(REPO / "data" / "prompts.jsonl")
    validate_prompt_set(prompts, PromptSetSpec.lesson())
    assert json.loads((REPO / "data" / "prices.json").read_text())["read_date"]
    assert load_prices(REPO / "data" / "prices.json").read_date.isoformat()


def test_step_2_the_estimate_is_printed_and_a_low_budget_stops_the_run(scenario, capsys):
    assert main(["run", "--allow-stale-prices", "--budget", "0.001"]) == EXIT_REFUSED
    captured = capsys.readouterr()
    assert "Estimate before calling: calls=450" in captured.out
    assert "REFUSING TO START" in captured.err
    assert not scenario.exists() or len(CsvJournal(scenario).rows()) == 0


def test_steps_3_to_6_the_run_fills_450_rows_and_the_report_answers_each_question(scenario, capsys):
    assert main(["run", "--allow-stale-prices", "--budget", "0.05"]) == EXIT_OK
    journal = CsvJournal(scenario)
    rows = journal.rows()
    assert len(rows) == 450
    assert {r.key.setting for r in rows} == {"t0", "t07", "t10"}
    assert all(r.input_tokens > 0 and r.output_tokens > 0 and r.stop_reason for r in rows)
    capsys.readouterr()

    prompts = load_prompts(REPO / "data" / "prompts.jsonl")
    prices = load_prices(REPO / "data" / "prices.json")
    report = build_report(journal, prompts, prices, TokenEstimator(), max_output_tokens=200)

    assert report.naive.total.error < -0.3  # chars/4 alone undercounts badly
    assert report.with_overhead.total.error > report.naive.total.error  # the measured overhead closes part of the gap
    assert abs(report.forecast.total.error) < 0.05  # per-kind densities, forecast without each prompt's own data
    assert report.cost_check.within  # total estimated cost within 5% of the cost from billed tokens
    assert report.cost_check.ceiling > report.cost_check.billed  # the pre-run ceiling is an upper bound
    assert report.naive.largest_gap.cause
    assert len(report.spread.settings) == 3
    assert report.spread.settings[0].setting == "t0"
    assert (
        report.spread.settings[0].mean_distinct_answers < 1.1
    )  # temperature 0 is nearly, not exactly, repeatable here
    assert report.spread.settings[1].mean_distinct_answers > 2.5
    assert all(s.mean_distinct_answers >= 1.0 for s in report.spread.settings)


def test_step_4_a_second_run_pays_for_nothing(scenario, capsys):
    main(["run", "--allow-stale-prices"])
    capsys.readouterr()
    assert main(["run", "--allow-stale-prices"]) == EXIT_OK
    assert "calls made now: 0; skipped, already in the journal: 450" in capsys.readouterr().out

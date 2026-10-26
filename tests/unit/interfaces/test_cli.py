import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tests.conftest import ScriptedModel
from token_meter.infrastructure.settings import MeterSettings
from token_meter.infrastructure.shutdown import ShutdownSignal
from token_meter.interfaces import cli
from token_meter.interfaces.cli import EXIT_CONFIG, EXIT_INTERRUPTED, EXIT_OK, EXIT_REFUSED, main, run_command

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    today = datetime.now(UTC).date().isoformat()
    prices = tmp_path / "prices.json"
    prices.write_text(
        json.dumps({"model": "m", "input_per_1k": "0.0001", "output_per_1k": "0.0005", "read_date": today})
    )
    monkeypatch.setenv("PROMPTS_PATH", str(REPO / "data" / "prompts.jsonl"))
    monkeypatch.setenv("PRICES_PATH", str(prices))
    monkeypatch.setenv("JOURNAL_PATH", str(tmp_path / "out" / "journal.csv"))
    monkeypatch.setenv("MODEL_PROVIDER", "recorded")
    monkeypatch.setenv("RECORDINGS_PATH", str(tmp_path / "none.jsonl"))
    return tmp_path


def scripted(monkeypatch, **kwargs):
    model = ScriptedModel(lambda request: ("billing", 40, 6), **kwargs)
    monkeypatch.setattr(cli, "build_chat_model", lambda *args, **kw: model)
    return model


def test_estimate_prints_the_whole_run_and_calls_no_model(workspace, capsys):
    assert main(["estimate"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "calls=450" in out
    assert "cost_est=$" in out


def test_estimate_also_refuses_when_the_budget_is_below_it(workspace, capsys):
    assert main(["estimate", "--budget", "0.001"]) == EXIT_REFUSED
    assert "REFUSING TO START" in capsys.readouterr().err


def test_a_budget_below_the_estimate_refuses_to_start_with_a_clear_message(workspace, capsys, monkeypatch):
    model = scripted(monkeypatch)
    assert main(["run", "--budget", "0.001"]) == EXIT_REFUSED
    assert "REFUSING TO START: estimated cost" in capsys.readouterr().err
    assert model.requests == []


def test_a_run_fills_the_journal_and_a_second_run_pays_for_nothing(workspace, capsys, monkeypatch):
    model = scripted(monkeypatch)
    assert main(["run", "--budget", "0.05"]) == EXIT_OK
    assert "calls made now: 450; skipped, already in the journal: 0" in capsys.readouterr().out
    assert main(["run"]) == EXIT_OK
    assert "calls made now: 0; skipped, already in the journal: 450" in capsys.readouterr().out
    assert len(model.requests) == 450


def test_the_report_prints_every_section(workspace, capsys, monkeypatch):
    scripted(monkeypatch)
    main(["run"])
    capsys.readouterr()
    assert main(["report"]) == EXIT_OK
    out = capsys.readouterr().out
    for fragment in ("by kind", "measured template overhead", "largest gap", "spread per setting", "temperature 0"):
        assert fragment in out


def test_stale_prices_stop_the_run_unless_allowed(workspace, capsys, monkeypatch):
    (workspace / "prices.json").write_text(
        json.dumps({"model": "m", "input_per_1k": "0.0001", "output_per_1k": "0.0005", "read_date": "2026-01-01"})
    )
    model = scripted(monkeypatch)
    assert main(["run"]) == EXIT_REFUSED
    assert "days ago" in capsys.readouterr().err
    assert main(["run", "--allow-stale-prices"]) == EXIT_OK
    assert len(model.requests) == 450


def test_a_budget_that_is_not_a_number_is_a_configuration_error(workspace, capsys, monkeypatch):
    scripted(monkeypatch)
    assert main(["run", "--budget", "cheap"]) == EXIT_CONFIG
    assert "--budget" in capsys.readouterr().err


def test_a_model_without_sampling_support_is_a_configuration_error(workspace, capsys, monkeypatch):
    scripted(monkeypatch, sampling=False)
    assert main(["run"]) == EXIT_CONFIG
    assert "does not accept temperature" in capsys.readouterr().err


def test_a_prompt_file_that_breaks_the_lesson_rules_is_reported(workspace, capsys, monkeypatch):
    short = workspace / "short.jsonl"
    short.write_text('{"id":"a","kind":"short","text":"hi"}\n')
    monkeypatch.setenv("PROMPTS_PATH", str(short))
    assert main(["estimate"]) == EXIT_CONFIG
    assert "expected 50 prompts" in capsys.readouterr().err


def test_a_bad_environment_value_is_reported_before_anything_runs(workspace, capsys, monkeypatch):
    monkeypatch.setenv("REPEATS", "zero")
    assert main(["estimate"]) == EXIT_CONFIG
    assert "REPEATS" in capsys.readouterr().err


def test_a_shutdown_request_ends_the_run_with_the_interrupted_code(workspace, monkeypatch, capsys):
    model = scripted(monkeypatch)
    shutdown = ShutdownSignal()
    shutdown.request()
    args = cli.build_parser().parse_args(["run"])
    assert run_command(args, MeterSettings.from_env(), model, shutdown) == EXIT_INTERRUPTED
    assert model.requests == []
    assert "calls made now: 0" in capsys.readouterr().out

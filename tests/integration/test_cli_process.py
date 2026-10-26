"""The `meter` program as a real process: a hard kill in the middle of a run, then a restart."""

import csv
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

REPO = Path(__file__).resolve().parents[2]
RECORDINGS = REPO / "tests" / "fixtures" / "recordings"


def environment(journal: Path, **extra: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in {"ANTHROPIC_API_KEY", "OPENAI_API_KEY"}}
    env.update(
        MODEL_PROVIDER="recorded",
        RECORDINGS_PATH=str(RECORDINGS),
        JOURNAL_PATH=str(journal),
        PRICES_PATH=str(REPO / "data" / "prices.json"),
        PROMPTS_PATH=str(REPO / "data" / "prompts.jsonl"),
        LOG_LEVEL="WARNING",
        **extra,
    )
    return env


def meter(*args: str, env: dict[str, str]) -> subprocess.Popen[str]:
    command = [sys.executable, "-m", "token_meter.interfaces.cli", *args, "--allow-stale-prices"]
    return subprocess.Popen(command, cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def rows(journal: Path) -> list[dict[str, str]]:
    with journal.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_a_run_killed_with_sigkill_resumes_and_ends_with_exactly_450_rows_and_no_repeated_key(tmp_path):
    journal = tmp_path / "journal.csv"
    env = environment(journal, THROTTLE_SECONDS="0.01")
    first = meter("run", env=env)
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline and (not journal.exists() or len(journal.read_text().splitlines()) < 120):
        time.sleep(0.05)
    first.send_signal(signal.SIGKILL)
    first.wait(timeout=10)
    killed_at = len(rows(journal))
    assert 0 < killed_at < 450

    second = meter("run", env=environment(journal))
    stdout, stderr = second.communicate(timeout=120)
    assert second.returncode == 0, stderr
    assert f"skipped, already in the journal: {killed_at}" in stdout

    finished = rows(journal)
    keys = [(r["prompt_id"], r["setting"], r["repeat"]) for r in finished]
    assert len(finished) == 450
    assert len(set(keys)) == 450


def test_sigterm_finishes_the_call_in_flight_and_exits_with_the_interrupted_code(tmp_path):
    journal = tmp_path / "journal.csv"
    process = meter("run", env=environment(journal, THROTTLE_SECONDS="0.05"))
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline and (not journal.exists() or len(journal.read_text().splitlines()) < 30):
        time.sleep(0.05)
    process.send_signal(signal.SIGTERM)
    process.communicate(timeout=30)
    assert process.returncode == 4
    done = rows(journal)
    assert 0 < len(done) < 450
    assert len({(r["prompt_id"], r["setting"], r["repeat"]) for r in done}) == len(done)


def test_the_budget_refusal_happens_before_any_row_is_written(tmp_path):
    journal = tmp_path / "journal.csv"
    process = meter("run", "--budget", "0.001", env=environment(journal))
    _, stderr = process.communicate(timeout=60)
    assert process.returncode == 3
    assert "REFUSING TO START" in stderr
    assert rows(journal) == []

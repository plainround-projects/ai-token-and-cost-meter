# Python source, shared test helpers and the process, end-to-end and live tests

## What it is

These tests are the larger ones: `conftest.py` (shared builders and fakes used by many tests), the **integration** tests (the program or a service as a real process, with real signals), the **end-to-end** tests (the lesson's scenario from input to report on recorded answers) and the **live** tests (opt-in, call a real model).

This note walks through every file, line by line: 4 files with 9 test functions. Read `pytest.md` first for the test runner itself (fixtures, markers, parametrize); this note shows every test.

## Why this repository uses it

Every claim in a README ("a killed run resumes", "the estimate is within ...", "the same refund twice is refused") is backed by a test, and these files are those tests. Reading them is the most exact way to learn what the program promises.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/conftest.py` | 54 non-blank lines |
| `tests/e2e/test_lesson_scenario.py` | 61 non-blank lines |
| `tests/integration/test_cli_process.py` | 68 non-blank lines |
| `tests/live/test_live_models.py` | 34 non-blank lines |

## How it works underneath

A test is a function whose name starts with `test_`. pytest imports the file, finds those functions, calls each one, and reports it as passed unless an `assert` fails or an error escapes. Parameters of a test function are *fixtures*: pytest looks up a fixture with that name (in the file, in `conftest.py`, or built in) and passes in what it returns. A fixture that uses `yield` runs the code after the `yield` as cleanup.

Test names are written as sentences (`test_a_budget_below_the_estimate_refuses_to_start_with_a_clear_message`) so that the list of names reads like the specification.

How to read the explanations below is the same as in the source notes: a quoted block, then one bullet per statement, with indented bullets for the calls and operators inside it.

## Walkthrough of this repository's use

### `tests/conftest.py`

In its own words: "Shared builders for tests: small prompt sets, a fixed clock and a scripted model."

54 non-blank lines; it defines `FixedClock`, `ScriptedModel`, `MemoryJournal`, `prompt`, `row`, `clock`.

`tests/conftest.py`, lines 1 to 14:

```python
"""Shared builders for tests: small prompt sets, a fixed clock and a scripted model."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from token_meter.domain.journal import CallKey, JournalRow
from token_meter.domain.llm import ChatRequest, ChatResponse, StopReason, Usage
from token_meter.domain.prompts import Kind, PromptRecord


class FixedClock:
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `UTC`, `date`, `datetime` from the standard library module `datetime`.
- Makes the module `pytest` (installed package) available.
- Brings in `CallKey` (Identifies one call. A run never pays for the same key twice.), `JournalRow` (What one call cost and returned, as billed by the provider.) from the project module `token_meter.domain.journal`.
- Brings in `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.), `StopReason` (Why the model stopped writing.), `Usage` (Tokens the provider billed for one call, read from its usage block, never recomputed.) from the project module `token_meter.domain.llm`.
- Brings in `Kind` (What a prompt is for; the report breaks every number out by kind.), `PromptRecord` (One prompt. `expected_label` is set only for label prompts.) from the project module `token_meter.domain.prompts`.
- Defines the class `FixedClock`. The author's own description: "A clock that only moves when a test says so."

`tests/conftest.py`, lines 15 to 28:

```python
    """A clock that only moves when a test says so."""

    def __init__(self, today: date = date(2026, 10, 26)) -> None:
        self._today = today
        self._ticks = 0.0

    def monotonic(self) -> float:
        self._ticks += 0.25
        return self._ticks

    def today(self) -> date:
        return self._today

    def now(self) -> datetime:
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `today` holds a calendar date; if the caller leaves it out it is the result of calling `date`.
- Stores the value named `today` under the name `self._today` (as an attribute of this object, so other methods can use it).
- Stores the number `0.0` under the name `self._ticks` (as an attribute of this object, so other methods can use it).
- Defines the method `monotonic`. It returns a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Updates `self._ticks` in place: `+=` applies `+` with the number `0.25` and stores the result back.
- Ends the function and gives back the attribute `_ticks` of this object to the caller.
- Defines the method `today`. It returns a calendar date.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `_today` of this object to the caller.
- Defines the method `now`. It returns a date and time.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).

`tests/conftest.py`, lines 29 to 42:

```python
        return datetime(self._today.year, self._today.month, self._today.day, tzinfo=UTC)


class ScriptedModel:
    """Answers every request from a function, and remembers the requests it saw."""

    def __init__(self, answer=None, sampling: bool = True) -> None:
        self.requests: list[ChatRequest] = []
        self._answer = answer or (lambda request: ("ok", 10, 3))
        self._sampling = sampling

    @property
    def name(self) -> str:
        return "scripted"
```

- Ends the function and gives back the result of calling `datetime` to the caller.
  - `datetime` from the standard library module `datetime`.
- Defines the class `ScriptedModel`. The author's own description: "Answers every request from a function, and remembers the requests it saw."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `answer`; if the caller leaves it out it is nothing (`None`).
    - `sampling` holds true or false; if the caller leaves it out it is the value `True`.
- Declares `self.requests` as a list of the project type `ChatRequest` and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of combining conditions: `answer or (lambda request: ('ok', 10, 3))` under the name `self._answer` (as an attribute of this object, so other methods can use it).
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `lambda args: expression` is a small unnamed function written inline.
- Stores the value named `sampling` under the name `self._sampling` (as an attribute of this object, so other methods can use it).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the text `scripted` to the caller.

`tests/conftest.py`, lines 44 to 55:

```python
    @property
    def supports_sampling(self) -> bool:
        return self._sampling

    def complete(self, request: ChatRequest) -> ChatResponse:
        self.requests.append(request)
        text, tokens_in, tokens_out = self._answer(request)
        return ChatResponse(text, StopReason.END, Usage(tokens_in, tokens_out), 0.5, "scripted")


class MemoryJournal:
    """An in-memory journal with the same contract as the CSV one."""
```

- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `_sampling` of this object to the caller.
- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Calls `append` on the stored object `self.requests`: it adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `append` on the stored object `self.requests`: it adds one item at the end of a list.
- Stores the result of calling `self._answer` under the name `(text, tokens_in, tokens_out)`.
  - The method `_answer` of `self`.
- Ends the function and gives back the result of calling `ChatResponse` to the caller.
  - `ChatResponse` from the project's `token_meter.domain.llm` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.).
  - `Usage` from the project's `token_meter.domain.llm` (Tokens the provider billed for one call, read from its usage block, never recomputed.).
- Defines the class `MemoryJournal`. The author's own description: "An in-memory journal with the same contract as the CSV one."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`tests/conftest.py`, lines 57 to 67:

```python
    def __init__(self, rows: list[JournalRow] | None = None) -> None:
        self._rows = list(rows or [])

    def done_keys(self) -> set[CallKey]:
        return {r.key for r in self._rows}

    def append(self, row: JournalRow) -> None:
        self._rows.append(row)

    def rows(self) -> list[JournalRow]:
        return list(self._rows)
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `rows` holds a list of the project type `JournalRow`, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Stores the result of calling `list` under the name `self._rows` (as an attribute of this object, so other methods can use it).
  - `list` makes a list (a copy when given a collection).
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Defines the method `done_keys`. It returns a set of the project type `CallKey`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back a set built by looping to the caller.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Defines the method `append`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `row` holds the project type `JournalRow`.
- Calls `append` on the stored object `self._rows`: it adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `append` on the stored object `self._rows`: it adds one item at the end of a list.
- Defines the method `rows`. It returns a list of the project type `JournalRow`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `list` to the caller.
  - `list` makes a list (a copy when given a collection).

`tests/conftest.py`, lines 70 to 81:

```python
def prompt(id_: str, kind: Kind, text: str, label: str | None = None) -> PromptRecord:
    return PromptRecord(id_, kind, text, label)


def row(
    prompt_id: str, setting: str, repeat: int, tokens_in: int, tokens_out: int, text: str = "a", stop=StopReason.END
):
    return JournalRow(CallKey(prompt_id, setting, repeat), tokens_in, tokens_out, stop, 0.1, text)


@pytest.fixture
def clock() -> FixedClock:
```

- Defines the function `prompt`. It returns the project type `PromptRecord`.
- Its parameters:
    - `id_` holds text.
    - `kind` holds the project type `Kind`.
    - `text` holds text.
    - `label` holds text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Ends the function and gives back the result of calling `PromptRecord` to the caller.
  - `PromptRecord` from the project's `token_meter.domain.prompts` (One prompt. `expected_label` is set only for label prompts.).
- Defines the function `row`.
- Its parameters:
    - `prompt_id` holds text.
    - `setting` holds text.
    - `repeat` holds a whole number.
    - `tokens_in` holds a whole number.
    - `tokens_out` holds a whole number.
    - `text` holds text; if the caller leaves it out it is the text `a`.
    - `stop`; if the caller leaves it out it is the `END` of `StopReason`.
- Ends the function and gives back the result of calling `JournalRow` to the caller.
  - `JournalRow` from the project's `token_meter.domain.journal` (What one call cost and returned, as billed by the provider.).
  - `CallKey` from the project's `token_meter.domain.journal` (Identifies one call. A run never pays for the same key twice.).
- Defines the function `clock`. `@pytest.fixture` marks a function that builds something tests ask for by naming it as a parameter. It returns the project type `FixedClock`.
- It takes no parameters.

`tests/conftest.py`, lines 82 to 82:

```python
    return FixedClock()
```

- Ends the function and gives back the result of calling `FixedClock` to the caller.
  - `FixedClock`, a class of this project (A clock that only moves when a test says so.).

### `tests/e2e/test_lesson_scenario.py`

In its own words: "The lesson's scenario from the prompt file to the report, on the recorded model."

61 non-blank lines; it defines `scenario`, `test_step_1_the_prompt_file_has_fifty_rows_in_five_kinds_one_long_and_the_price_file_is_dated`, `test_step_2_the_estimate_is_printed_and_a_low_budget_stops_the_run`, `test_steps_3_to_6_the_run_fills_450_rows_and_the_report_answers_each_question`, `test_step_4_a_second_run_pays_for_nothing`.

`tests/e2e/test_lesson_scenario.py`, lines 1 to 13:

```python
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
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Makes the module `json` (standard library) available.
- Brings in `Path` from the standard library module `pathlib`.
- Makes the module `pytest` (installed package) available.
- Brings in `build_report` (Compare the naive estimator with the bill, add the measured overhead, then forecast each prompt leave-one-out.) from the project module `token_meter.application.report`.
- Brings in `TokenEstimator` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.) from the project module `token_meter.domain.estimation`.
- Brings in `PromptSetSpec` (The shape the lesson asks for: counts per kind and one prompt over a token threshold.), `validate_prompt_set` (Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken.) from the project module `token_meter.domain.prompts`.
- Brings in `CsvJournal` (Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open.) from the project module `token_meter.infrastructure.csv_journal`.
- Brings in `load_prices` (Read the price file. `read_date` is a real field so a script can refuse stale prices.), `load_prompts` (Read one prompt per line. A bad line is reported with its line number; the rest of the file is not lost.) from the project module `token_meter.infrastructure.files`.
- Brings in `EXIT_OK`, `EXIT_REFUSED`, `main` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).) from the project module `token_meter.interfaces.cli`.

`tests/e2e/test_lesson_scenario.py`, lines 15 to 27:

```python
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
```

- Stores the `e2e` of `pytest.mark` under the name `pytestmark`.
- Stores the part of `Path(__file__).resolve().pa...` picked by `2` under the name `REPO`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.resolve(...)` turns a path into a full absolute path.
  - `Path` from the standard library module `pathlib`, which a file or folder location.
- Defines the function `scenario`. `@pytest.fixture` marks a function that builds something tests ask for by naming it as a parameter.
- Its parameters:
    - `tmp_path`.
    - `monkeypatch`.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.

`tests/e2e/test_lesson_scenario.py`, lines 28 to 41:

```python
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
```

- Ends the function and gives back the result of `tmp_path / 'journal.csv'` to the caller.
  - `/` is divide.
- Defines the function `test_step_1_the_prompt_file_has_fifty_rows_in_five_kinds_one_long_and_the_price_file_is_dated`.
- It takes no parameters.
- Stores the result of calling `load_prompts` under the name `prompts`.
  - `load_prompts` from the project's `token_meter.infrastructure.files` (Read one prompt per line. A bad line is reported with its line number; the rest of the file is not lost.).
  - `/` is divide.
- Calls `validate_prompt_set` from the project's `token_meter.domain.prompts` (Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken.) with 2 argument(s); the result is not kept.
  - `validate_prompt_set` from the project's `token_meter.domain.prompts` (Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken.).
  - The method `lesson` of `PromptSetSpec`.
- Checks that `json.loads((REPO / 'data' / 'prices.json').read_text())['read_date']` is true; if it is not, the test fails with an `AssertionError`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `json.loads` turns JSON text into Python data.
  - `.read_text(...)` reads a whole file as text.
  - `/` is divide.
- Checks that `load_prices(REPO / 'data' / 'prices.json').read_date.isoformat()` is true; if it is not, the test fails with an `AssertionError`.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - `load_prices` from the project's `token_meter.infrastructure.files` (Read the price file. `read_date` is a real field so a script can refuse stale prices.).
  - `/` is divide.
- Defines the function `test_step_2_the_estimate_is_printed_and_a_low_budget_stops_the_run`.
- Its parameters:
    - `scenario`.
    - `capsys`.
- Checks that `main(['run', '--allow-stale-prices', '--budget', '0.001']) == EXIT_REFUSED` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).
- Stores the result of calling `capsys.readouterr` under the name `captured`.
  - `.readouterr(...)` reads what a test captured from the screen.
- Checks that `'Estimate before calling: calls=450' in captured.out` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.

`tests/e2e/test_lesson_scenario.py`, lines 42 to 55:

```python
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
```

- Checks that `'REFUSING TO START' in captured.err` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `not scenario.exists() or len(CsvJournal(scenario).rows()) == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `not` flips true and false.
  - `==` means equal.
  - `.exists(...)` asks whether the path exists.
  - `len` counts the items in a collection (or the characters in text).
  - The method `rows` of `CsvJournal(scenario)`.
  - `CsvJournal` from the project's `token_meter.infrastructure.csv_journal` (Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open.).
- Defines the function `test_steps_3_to_6_the_run_fills_450_rows_and_the_report_answers_each_question`.
- Its parameters:
    - `scenario`.
    - `capsys`.
- Checks that `main(['run', '--allow-stale-prices', '--budget', '0.05']) == EXIT_OK` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).
- Stores the result of calling `CsvJournal` under the name `journal`.
  - `CsvJournal` from the project's `token_meter.infrastructure.csv_journal` (Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open.).
- Stores the result of calling `journal.rows` under the name `rows`.
  - The method `rows` of `journal`.
- Checks that `len(rows) == 450` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Checks that `{r.key.setting for r in rows} == {'t0', 't07', 't10'}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Checks that `all((r.input_tokens > 0 and r.output_tokens > 0 and r.stop_reason for r in ro...` is true; if it is not, the test fails with an `AssertionError`.
  - `all` is true only if every item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `>` means greater than.
- Calls `.readouterr(...)` reads what a test captured from the screen; the result is not kept.
  - `.readouterr(...)` reads what a test captured from the screen.
- Stores the result of calling `load_prompts` under the name `prompts`.
  - `load_prompts` from the project's `token_meter.infrastructure.files` (Read one prompt per line. A bad line is reported with its line number; the rest of the file is not lost.).
  - `/` is divide.

`tests/e2e/test_lesson_scenario.py`, lines 56 to 69:

```python
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
```

- Stores the result of calling `load_prices` under the name `prices`.
  - `load_prices` from the project's `token_meter.infrastructure.files` (Read the price file. `read_date` is a real field so a script can refuse stale prices.).
  - `/` is divide.
- Stores the result of calling `build_report` under the name `report`.
  - `build_report` from the project's `token_meter.application.report` (Compare the naive estimator with the bill, add the measured overhead, then forecast each prompt leave-one-out.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Checks that `report.naive.total.error < -0.3` is true; if it is not, the test fails with an `AssertionError`.
  - `<` means less than.
- Checks that `report.with_overhead.total.error > report.naive.total.error` is true; if it is not, the test fails with an `AssertionError`.
  - `>` means greater than.
- Checks that `abs(report.forecast.total.error) < 0.05` is true; if it is not, the test fails with an `AssertionError`.
  - `<` means less than.
  - `abs` gives the absolute value (the number without its sign).
- Checks that `report.cost_check.within` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `report.cost_check.ceiling > report.cost_check.billed` is true; if it is not, the test fails with an `AssertionError`.
  - `>` means greater than.
- Checks that `report.naive.largest_gap.cause` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `len(report.spread.settings) == 3` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Checks that `report.spread.settings[0].setting == 't0'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `report.spread.settings[0].mean_distinct_answers < 1.1` is true; if it is not, the test fails with an `AssertionError`.
  - `<` means less than.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/e2e/test_lesson_scenario.py`, lines 70 to 78:

```python
    assert report.spread.settings[1].mean_distinct_answers > 2.5
    assert all(s.mean_distinct_answers >= 1.0 for s in report.spread.settings)


def test_step_4_a_second_run_pays_for_nothing(scenario, capsys):
    main(["run", "--allow-stale-prices"])
    capsys.readouterr()
    assert main(["run", "--allow-stale-prices"]) == EXIT_OK
    assert "calls made now: 0; skipped, already in the journal: 450" in capsys.readouterr().out
```

- Checks that `report.spread.settings[1].mean_distinct_answers > 2.5` is true; if it is not, the test fails with an `AssertionError`.
  - `>` means greater than.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `all((s.mean_distinct_answers >= 1.0 for s in report.spread.settings))` is true; if it is not, the test fails with an `AssertionError`.
  - `all` is true only if every item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `>=` means greater than or equal.
- Defines the function `test_step_4_a_second_run_pays_for_nothing`.
- Its parameters:
    - `scenario`.
    - `capsys`.
- Calls `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).) with 1 argument(s); the result is not kept.
  - `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).
- Calls `.readouterr(...)` reads what a test captured from the screen; the result is not kept.
  - `.readouterr(...)` reads what a test captured from the screen.
- Checks that `main(['run', '--allow-stale-prices']) == EXIT_OK` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).
- Checks that `'calls made now: 0; skipped, already in the journal: 450' in capsys.readouter...` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `.readouterr(...)` reads what a test captured from the screen.

### `tests/integration/test_cli_process.py`

In its own words: "The `meter` program as a real process: a hard kill in the middle of a run, then a restart."

68 non-blank lines; it defines `environment`, `meter`, `rows`, `test_a_run_killed_with_sigkill_resumes_and_ends_with_exactly_450_rows_and_no_repeated_key`, `test_sigterm_finishes_the_call_in_flight_and_exits_with_the_interrupted_code`, `test_the_budget_refusal_happens_before_any_row_is_written`.

`tests/integration/test_cli_process.py`, lines 1 to 13:

```python
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
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Makes the module `csv` (standard library) available.
- Makes the module `os` (standard library) available.
- Makes the module `signal` (standard library) available.
- Makes the module `subprocess` (standard library) available.
- Makes the module `sys` (standard library) available.
- Makes the module `time` (standard library) available.
- Brings in `Path` from the standard library module `pathlib`.
- Makes the module `pytest` (installed package) available.
- Stores the `integration` of `pytest.mark` under the name `pytestmark`.

`tests/integration/test_cli_process.py`, lines 15 to 20:

```python
REPO = Path(__file__).resolve().parents[2]
RECORDINGS = REPO / "tests" / "fixtures" / "recordings"


def environment(journal: Path, **extra: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in {"ANTHROPIC_API_KEY", "OPENAI_API_KEY"}}
```

- Stores the part of `Path(__file__).resolve().pa...` picked by `2` under the name `REPO`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.resolve(...)` turns a path into a full absolute path.
  - `Path` from the standard library module `pathlib`, which a file or folder location.
- Stores the result of `REPO / 'tests' / 'fixtures' / 'recordings'` under the name `RECORDINGS`.
  - `/` is divide.
- Defines the function `environment`. It returns a dictionary from text to text.
- Its parameters:
    - `journal` holds a file path.
    - `**extra` collects any extra named arguments into a dictionary.
- Stores a dictionary built by looping under the name `env`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `os.environ.items` from the standard library module `os`.
  - `not in` means is not contained in.

`tests/integration/test_cli_process.py`, lines 21 to 34:

```python
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
```

- Calls `.update(...)` merges another collection into this one with 7 argument(s); the result is not kept.
  - `.update(...)` merges another collection into this one.
  - `**name` inside a call passes every entry of a dictionary as a named argument.
  - `str` turns a value into text.
  - `/` is divide.
- Ends the function and gives back the value named `env` to the caller.
- Defines the function `meter`. It returns Popen of text.
- Its parameters:
    - `*args` collects any extra positional arguments into a tuple.
    - `env` holds a dictionary from text to text; it must be passed by name.
- Stores a list of 5 item(s) under the name `command`.

`tests/integration/test_cli_process.py`, lines 35 to 48:

```python
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
```

- Ends the function and gives back the result of calling `subprocess.Popen` to the caller.
  - `subprocess.Popen` starts another program and returns a handle.
- Defines the function `rows`. It returns a list of a dictionary from text to text.
- Its parameters:
    - `journal` holds a file path.
- A `with` block: it sets up `journal.open(newline='')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `journal`.
- Ends the function and gives back the result of calling `list` to the caller.
  - `list` makes a list (a copy when given a collection).
  - `csv.DictReader` reads CSV rows as dictionaries.
- Defines the function `test_a_run_killed_with_sigkill_resumes_and_ends_with_exactly_450_rows_and_no_repeated_key`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'journal.csv'` under the name `journal`.
  - `/` is divide.
- Stores the result of calling `environment` under the name `env`.
  - `environment`, a function of this file.
- Stores the result of calling `meter` under the name `first`.
  - `meter`, a function of this file.
- Stores the result of `time.monotonic() + 60` under the name `deadline`.
  - `+` is add.
  - `time.monotonic` a clock that never goes backwards, for measuring durations.
- Loop: the indented lines below repeat as long as `time.monotonic() < deadline and (not journal.exists() or ...` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `<` means less than.
  - `time.monotonic` a clock that never goes backwards, for measuring durations.
  - `not` flips true and false.
  - `.exists(...)` asks whether the path exists.
  - `len` counts the items in a collection (or the characters in text).
  - `.splitlines(...)` cuts text into a list of lines.
  - `.read_text(...)` reads a whole file as text.

`tests/integration/test_cli_process.py`, lines 49 to 62:

```python
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
```

- Calls `time.sleep` pauses the program with 1 argument(s); the result is not kept.
  - `time.sleep` pauses the program.
- Calls `.send_signal(...)` sends an operating-system signal to a process with 1 argument(s); the result is not kept.
  - `.send_signal(...)` sends an operating-system signal to a process.
- Calls `.wait(...)` waits until something happens with 1 argument(s); the result is not kept.
  - `.wait(...)` waits until something happens.
- Stores the result of calling `len` under the name `killed_at`.
  - `len` counts the items in a collection (or the characters in text).
  - `rows`, a function of this file.
- Checks that `0 < killed_at < 450` is true; if it is not, the test fails with an `AssertionError`.
  - `<` means less than.
- Stores the result of calling `meter` under the name `second`.
  - `meter`, a function of this file.
  - `environment`, a function of this file.
- Stores the result of calling `second.communicate` under the name `(stdout, stderr)`.
  - `.communicate(...)` waits for a process to finish and collects its output.
- Checks that `second.returncode == 0` is true; if it is not, the test fails with an `AssertionError` and the message `stderr`.
  - `==` means equal.
- Checks that `f'skipped, already in the journal: {killed_at}' in stdout` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of calling `rows` under the name `finished`.
  - `rows`, a function of this file.
- Stores a list built by looping under the name `keys`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `len(finished) == 450` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).

`tests/integration/test_cli_process.py`, lines 63 to 76:

```python
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
```

- Checks that `len(set(keys)) == 450` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `set` makes a set: a collection with no repeated items.
- Defines the function `test_sigterm_finishes_the_call_in_flight_and_exits_with_the_interrupted_code`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'journal.csv'` under the name `journal`.
  - `/` is divide.
- Stores the result of calling `meter` under the name `process`.
  - `meter`, a function of this file.
  - `environment`, a function of this file.
- Stores the result of `time.monotonic() + 60` under the name `deadline`.
  - `+` is add.
  - `time.monotonic` a clock that never goes backwards, for measuring durations.
- Loop: the indented lines below repeat as long as `time.monotonic() < deadline and (not journal.exists() or ...` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `<` means less than.
  - `time.monotonic` a clock that never goes backwards, for measuring durations.
  - `not` flips true and false.
  - `.exists(...)` asks whether the path exists.
  - `len` counts the items in a collection (or the characters in text).
  - `.splitlines(...)` cuts text into a list of lines.
  - `.read_text(...)` reads a whole file as text.
- Calls `time.sleep` pauses the program with 1 argument(s); the result is not kept.
  - `time.sleep` pauses the program.
- Calls `.send_signal(...)` sends an operating-system signal to a process with 1 argument(s); the result is not kept.
  - `.send_signal(...)` sends an operating-system signal to a process.
- Calls `.communicate(...)` waits for a process to finish and collects its output with 1 argument(s); the result is not kept.
  - `.communicate(...)` waits for a process to finish and collects its output.
- Checks that `process.returncode == 4` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Stores the result of calling `rows` under the name `done`.
  - `rows`, a function of this file.
- Checks that `0 < len(done) < 450` is true; if it is not, the test fails with an `AssertionError`.
  - `<` means less than.
  - `len` counts the items in a collection (or the characters in text).

`tests/integration/test_cli_process.py`, lines 77 to 86:

```python
    assert len({(r["prompt_id"], r["setting"], r["repeat"]) for r in done}) == len(done)


def test_the_budget_refusal_happens_before_any_row_is_written(tmp_path):
    journal = tmp_path / "journal.csv"
    process = meter("run", "--budget", "0.001", env=environment(journal))
    _, stderr = process.communicate(timeout=60)
    assert process.returncode == 3
    assert "REFUSING TO START" in stderr
    assert rows(journal) == []
```

- Checks that `len({(r['prompt_id'], r['setting'], r['repeat']) for r in done}) == len(done)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_the_budget_refusal_happens_before_any_row_is_written`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'journal.csv'` under the name `journal`.
  - `/` is divide.
- Stores the result of calling `meter` under the name `process`.
  - `meter`, a function of this file.
  - `environment`, a function of this file.
- Stores the result of calling `process.communicate` under the name `(_, stderr)`.
  - `.communicate(...)` waits for a process to finish and collects its output.
- Checks that `process.returncode == 3` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `'REFUSING TO START' in stderr` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `rows(journal) == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `rows`, a function of this file.

### `tests/live/test_live_models.py`

In its own words: "Opt-in tests that call a real model. Run with `make test-live`; skipped in every other run."

34 non-blank lines; it defines `local_server_up`, `test_claude_answers_and_reports_billed_usage`, `test_the_local_model_returns_a_usage_block_and_obeys_temperature_zero`.

`tests/live/test_live_models.py`, lines 1 to 12:

```python
"""Opt-in tests that call a real model. Run with `make test-live`; skipped in every other run."""

import os

import httpx
import pytest

from token_meter.domain.llm import ChatMessage, ChatRequest, StopReason
from token_meter.infrastructure.clock import SystemClock
from token_meter.infrastructure.model_factory import ModelSettings, build_chat_model

pytestmark = pytest.mark.live
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Makes the module `os` (standard library) available.
- Makes the module `httpx` (installed package) available.
- Makes the module `pytest` (installed package) available.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `StopReason` (Why the model stopped writing.) from the project module `token_meter.domain.llm`.
- Brings in `SystemClock` (Wall-clock and monotonic time from the operating system.) from the project module `token_meter.infrastructure.clock`.
- Brings in `ModelSettings` (Which model to call and how. See .env.example for every variable.), `build_chat_model` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.) from the project module `token_meter.infrastructure.model_factory`.
- Stores the `live` of `pytest.mark` under the name `pytestmark`.

`tests/live/test_live_models.py`, lines 15 to 26:

```python
def local_server_up() -> bool:
    try:
        return httpx.get("http://localhost:11434/api/tags", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY is not set")
def test_claude_answers_and_reports_billed_usage():
    settings = ModelSettings.from_env(
        {"MODEL_PROVIDER": "anthropic", **{k: v for k, v in os.environ.items() if k.startswith("MODEL_")}}
    )
```

- Defines the function `local_server_up`. It returns true or false.
- It takes no parameters.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Ends the function and gives back whether `httpx.get('http://localhost:11434/api/tags', timeout=2).s...` holds to the caller.
  - `==` means equal.
  - `httpx.get` sends an HTTP GET request.
- `except` handler: it runs when the `try` block raised `httpx.HTTPError`.
- Ends the function and gives back the value `False` to the caller.
- Defines the function `test_claude_answers_and_reports_billed_usage`. `@pytest.mark.skipif(...)` skips the test when the condition holds.
- It takes no parameters.
- Stores the result of calling `ModelSettings.from_env` under the name `settings`.
  - The method `from_env` of `ModelSettings`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `os.environ.items` from the standard library module `os`.
  - `.startswith(...)` asks whether text begins with the given text.

`tests/live/test_live_models.py`, lines 27 to 40:

```python
    model = build_chat_model(settings, SystemClock())
    response = model.complete(
        ChatRequest((ChatMessage.user("Reply with the single word: ready"),), max_output_tokens=64)
    )
    assert response.usage.input_tokens > 0
    assert response.usage.output_tokens > 0
    assert response.stop_reason in (StopReason.END, StopReason.LENGTH)


@pytest.mark.skipif(
    not local_server_up(), reason="no local OpenAI-compatible server on localhost:11434 (run make models)"
)
def test_the_local_model_returns_a_usage_block_and_obeys_temperature_zero():
    model = build_chat_model(ModelSettings.from_env({"MODEL_PROVIDER": "openai-compatible"}), SystemClock())
```

- Stores the result of calling `build_chat_model` under the name `model`.
  - `build_chat_model` from the project's `token_meter.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `SystemClock` from the project's `token_meter.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Stores the result of calling `model.complete` under the name `response`.
  - The method `complete` of `model`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
- Checks that `response.usage.input_tokens > 0` is true; if it is not, the test fails with an `AssertionError`.
  - `>` means greater than.
- Checks that `response.usage.output_tokens > 0` is true; if it is not, the test fails with an `AssertionError`.
  - `>` means greater than.
- Checks that `response.stop_reason in (StopReason.END, StopReason.LENGTH)` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Defines the function `test_the_local_model_returns_a_usage_block_and_obeys_temperature_zero`. `@pytest.mark.skipif(...)` skips the test when the condition holds.
- It takes no parameters.
- Stores the result of calling `build_chat_model` under the name `model`.
  - `build_chat_model` from the project's `token_meter.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - The method `from_env` of `ModelSettings`.
  - `SystemClock` from the project's `token_meter.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).

`tests/live/test_live_models.py`, lines 41 to 44:

```python
    request = ChatRequest((ChatMessage.user("How do I reset my password?"),), max_output_tokens=60, temperature=0.0)
    first, second = model.complete(request), model.complete(request)
    assert first.usage.input_tokens > 0
    assert first.text.strip() == second.text.strip()
```

- Stores the result of calling `ChatRequest` under the name `request`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
- Stores a tuple of 2 item(s) under the name `(first, second)`.
  - The method `complete` of `model`.
- Checks that `first.usage.input_tokens > 0` is true; if it is not, the test fails with an `AssertionError`.
  - `>` means greater than.
- Checks that `first.text.strip() == second.text.strip()` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.

## Try it yourself

1. List the tests of this group without running them: the last line is the count.

```bash
.venv/bin/python -m pytest tests/integration --collect-only -q -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
tests/integration/test_cli_process.py::test_the_budget_refusal_happens_before_any_row_is_written

3 tests collected in N.NNs
```

2. Run this group. A green run prints the number of passed tests.

```bash
.venv/bin/python -m pytest tests/integration -q -x -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
...                                                                      [100%]
3 passed in N.NNs
```

3. The first test names, written as sentences.

```bash
.venv/bin/python -m pytest tests/integration -q -p no:cacheprovider --co 2>&1 | sed -n 1,5p
```

What you should see (captured from this repository):

```text
tests/integration/test_cli_process.py::test_a_run_killed_with_sigkill_resumes_and_ends_with_exactly_450_rows_and_no_repeated_key
tests/integration/test_cli_process.py::test_sigterm_finishes_the_call_in_flight_and_exits_with_the_interrupted_code
tests/integration/test_cli_process.py::test_the_budget_refusal_happens_before_any_row_is_written

3 tests collected in N.NNs
```

## Mistakes people make

- **Tests that depend on each other.** Each test builds its own data, so they pass in any order.
- **Real files, real network, real time.** Tests use `tmp_path`, recorded answers, mock transports and a fake clock, so a result never depends on the machine.
- **Asserting on private details.** Tests call public functions and check results.
- **Sleeping to wait for a process.** The process tests poll with a deadline instead of sleeping a fixed time.

## Check yourself

1. What does `tests/conftest.py` test?

   *Answer:* Shared builders for tests: small prompt sets, a fixed clock and a scripted model.

2. What does `tests/e2e/test_lesson_scenario.py` test?

   *Answer:* The lesson's scenario from the prompt file to the report, on the recorded model.

3. What does `tests/integration/test_cli_process.py` test?

   *Answer:* The `meter` program as a real process: a hard kill in the middle of a run, then a restart.

4. What does `tests/live/test_live_models.py` test?

   *Answer:* Opt-in tests that call a real model. Run with `make test-live`; skipped in every other run.

5. What does a test function's name start with, and why?

   *Answer:* `test_`: pytest collects every function whose name starts with it.

## Further reading

- pytest documentation, https://docs.pytest.org/en/stable/ (pytest 9.1.1 is pinned; the per-statement explanations are generated from the code's structure).

# Python source, the unit tests (part 1 of 2)

## What it is

The **unit tests** check one small piece at a time (a function, a class) with in-memory fakes and mock transports. They run in a fraction of a second each and need no network, no service and no model.

This note walks through every file, line by line: 11 files with 90 test functions. Read `pytest.md` first for the test runner itself (fixtures, markers, parametrize); this note shows every test.

## Why this repository uses it

Every claim in a README ("a killed run resumes", "the estimate is within ...", "the same refund twice is refused") is backed by a test, and these files are those tests. Reading them is the most exact way to learn what the program promises.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/unit/application/test_report_and_metered_model.py` | 49 non-blank lines |
| `tests/unit/application/test_run_meter.py` | 73 non-blank lines |
| `tests/unit/domain/test_analysis.py` | 137 non-blank lines |
| `tests/unit/domain/test_llm.py` | 22 non-blank lines |
| `tests/unit/domain/test_pricing_and_estimation.py` | 42 non-blank lines |
| `tests/unit/domain/test_prompts.py` | 47 non-blank lines |
| `tests/unit/infrastructure/test_anthropic_chat.py` | 124 non-blank lines |
| `tests/unit/infrastructure/test_csv_journal.py` | 33 non-blank lines |
| `tests/unit/infrastructure/test_files_and_settings.py` | 69 non-blank lines |
| `tests/unit/infrastructure/test_openai_compatible.py` | 102 non-blank lines |
| `tests/unit/infrastructure/test_recording.py` | 45 non-blank lines |

## How it works underneath

A test is a function whose name starts with `test_`. pytest imports the file, finds those functions, calls each one, and reports it as passed unless an `assert` fails or an error escapes. Parameters of a test function are *fixtures*: pytest looks up a fixture with that name (in the file, in `conftest.py`, or built in) and passes in what it returns. A fixture that uses `yield` runs the code after the `yield` as cleanup.

Test names are written as sentences (`test_a_budget_below_the_estimate_refuses_to_start_with_a_clear_message`) so that the list of names reads like the specification.

How to read the explanations below is the same as in the source notes: a quoted block, then one bullet per statement, with indented bullets for the calls and operators inside it.

## Walkthrough of this repository's use

### `tests/unit/application/test_report_and_metered_model.py`

49 non-blank lines; it defines `test_the_report_finds_the_overhead_and_shows_the_error_shrink`, `test_the_metered_model_logs_estimate_and_bill_without_the_prompt_text`, `test_a_zero_billed_input_does_not_divide_by_zero`.

`tests/unit/application/test_report_and_metered_model.py`, lines 1 to 13:

```python
import logging
from datetime import date
from decimal import Decimal

from tests.conftest import MemoryJournal, ScriptedModel, prompt, row
from token_meter.application.metered_model import MeteredChatModel
from token_meter.application.report import build_report
from token_meter.domain.estimation import TokenEstimator
from token_meter.domain.llm import ChatMessage, ChatRequest
from token_meter.domain.pricing import PriceTable
from token_meter.domain.prompts import Kind

PRICES = PriceTable("m", Decimal("0.001"), Decimal("0.002"), date(2026, 10, 26))
```

- Makes the module `logging` (standard library) available.
- Brings in `date` from the standard library module `datetime`.
- Brings in `Decimal` from the standard library module `decimal`.
- Brings in `MemoryJournal` (An in-memory journal with the same contract as the CSV one.), `ScriptedModel` (Answers every request from a function, and remembers the requests it saw.), `prompt`, `row` from the project module `tests.conftest`.
- Brings in `MeteredChatModel` (Wraps any `ChatModel`. Logs sizes only, never the prompt text.) from the project module `token_meter.application.metered_model`.
- Brings in `build_report` (Compare the naive estimator with the bill, add the measured overhead, then forecast each prompt leave-one-out.) from the project module `token_meter.application.report`.
- Brings in `TokenEstimator` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.) from the project module `token_meter.domain.estimation`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.) from the project module `token_meter.domain.llm`.
- Brings in `PriceTable` (Price per 1,000 input and output tokens, with the day the numbers were read.) from the project module `token_meter.domain.pricing`.
- Brings in `Kind` (What a prompt is for; the report breaks every number out by kind.) from the project module `token_meter.domain.prompts`.
- Stores the result of calling `PriceTable` under the name `PRICES`.
  - `PriceTable` from the project's `token_meter.domain.pricing` (Price per 1,000 input and output tokens, with the day the numbers were read.).
  - `Decimal` from the standard library module `decimal`.
  - `date` from the standard library module `datetime`.

`tests/unit/application/test_report_and_metered_model.py`, lines 16 to 27:

```python
def test_the_report_finds_the_overhead_and_shows_the_error_shrink():
    prompts = [
        prompt("s", Kind.SHORT, "a" * 40),
        prompt("s2", Kind.SHORT, "a" * 80),
        prompt("l", Kind.LONG, "a" * 400),
    ]
    rows = [
        row(p, s, r, tokens + 28, 10)
        for p, tokens in (("s", 10), ("s2", 20), ("l", 100))
        for s in ("t0", "t07")
        for r in range(2)
    ]
```

- Defines the function `test_the_report_finds_the_overhead_and_shows_the_error_shrink`.
- It takes no parameters.
- Stores a list of 3 item(s) under the name `prompts`.
  - `prompt` from the project's `tests.conftest`.
  - `*` is multiply.
- Stores a list built by looping under the name `rows`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `row` from the project's `tests.conftest`.
  - `+` is add.
  - `range` makes the numbers from 0 up to (not including) the given one.

`tests/unit/application/test_report_and_metered_model.py`, lines 28 to 41:

```python
    report = build_report(MemoryJournal(rows), prompts, PRICES, TokenEstimator(), max_output_tokens=200)
    assert report.calls == 12
    assert report.overhead == 28
    assert report.naive.total.error < -0.2
    assert abs(report.with_overhead.total.error) < 0.01
    assert abs(report.forecast.total.error) < 0.05
    assert report.ratios == {"short": 4.0, "long": 4.0}
    assert report.cost_check.within


def test_the_metered_model_logs_estimate_and_bill_without_the_prompt_text(caplog):
    inner = ScriptedModel(lambda request: ("answer text", 40, 5))
    metered = MeteredChatModel(inner, TokenEstimator(per_call_overhead=28))
    request = ChatRequest((ChatMessage.user("secret customer words " * 2),), max_output_tokens=20, tag="t1")
```

- Stores the result of calling `build_report` under the name `report`.
  - `build_report` from the project's `token_meter.application.report` (Compare the naive estimator with the bill, add the measured overhead, then forecast each prompt leave-one-out.).
  - `MemoryJournal` from the project's `tests.conftest` (An in-memory journal with the same contract as the CSV one.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Checks that `report.calls == 12` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `report.overhead == 28` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `report.naive.total.error < -0.2` is true; if it is not, the test fails with an `AssertionError`.
  - `<` means less than.
- Checks that `abs(report.with_overhead.total.error) < 0.01` is true; if it is not, the test fails with an `AssertionError`.
  - `<` means less than.
  - `abs` gives the absolute value (the number without its sign).
- Checks that `abs(report.forecast.total.error) < 0.05` is true; if it is not, the test fails with an `AssertionError`.
  - `<` means less than.
  - `abs` gives the absolute value (the number without its sign).
- Checks that `report.ratios == {'short': 4.0, 'long': 4.0}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `report.cost_check.within` is true; if it is not, the test fails with an `AssertionError`.
- Defines the function `test_the_metered_model_logs_estimate_and_bill_without_the_prompt_text`.
- Its parameters:
    - `caplog`.
- Stores the result of calling `ScriptedModel` under the name `inner`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `lambda args: expression` is a small unnamed function written inline.
- Stores the result of calling `MeteredChatModel` under the name `metered`.
  - `MeteredChatModel` from the project's `token_meter.application.metered_model` (Wraps any `ChatModel`. Logs sizes only, never the prompt text.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Stores the result of calling `ChatRequest` under the name `request`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
  - `*` is multiply.

`tests/unit/application/test_report_and_metered_model.py`, lines 42 to 55:

```python
    with caplog.at_level(logging.INFO):
        response = metered.complete(request)
    assert response.text == "answer text"
    assert metered.name == "scripted"
    assert metered.supports_sampling
    record = next(r for r in caplog.records if r.getMessage() == "estimate against bill")
    assert record.fields["billed_input"] == 40
    assert record.fields["estimated_input"] == 11 + 28
    assert "secret" not in caplog.text


def test_a_zero_billed_input_does_not_divide_by_zero(caplog):
    metered = MeteredChatModel(ScriptedModel(lambda request: ("x", 0, 0)), TokenEstimator())
    with caplog.at_level(logging.INFO):
```

- A `with` block: it sets up `caplog.at_level(logging.INFO)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `at_level` of `caplog`.
- Stores the result of calling `metered.complete` under the name `response`.
  - The method `complete` of `metered`.
- Checks that `response.text == 'answer text'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `metered.name == 'scripted'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `metered.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.
- Stores the result of calling `next` under the name `record`.
  - `next` takes the next item from an iterator.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `==` means equal.
  - The method `getMessage` of `r`.
- Checks that `record.fields['billed_input'] == 40` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `record.fields['estimated_input'] == 11 + 28` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `+` is add.
- Checks that `'secret' not in caplog.text` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
- Defines the function `test_a_zero_billed_input_does_not_divide_by_zero`.
- Its parameters:
    - `caplog`.
- Stores the result of calling `MeteredChatModel` under the name `metered`.
  - `MeteredChatModel` from the project's `token_meter.application.metered_model` (Wraps any `ChatModel`. Logs sizes only, never the prompt text.).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
  - `lambda args: expression` is a small unnamed function written inline.
- A `with` block: it sets up `caplog.at_level(logging.INFO)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `at_level` of `caplog`.

`tests/unit/application/test_report_and_metered_model.py`, lines 56 to 57:

```python
        metered.complete(ChatRequest((ChatMessage.user("hi"),)))
    assert caplog.records[-1].fields["error"] == "+0.0%"
```

- Calls the method `complete` of `metered` with 1 argument(s); the result is not kept.
  - The method `complete` of `metered`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
- Checks that `caplog.records[-1].fields['error'] == '+0.0%'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

### `tests/unit/application/test_run_meter.py`

73 non-blank lines; it defines `plan`, `test_a_plan_covers_every_prompt_setting_and_repeat`, `test_a_run_makes_every_call_and_journals_one_row_each`, `test_the_output_cap_is_the_same_for_every_setting_and_only_sampling_changes`, `test_every_request_carries_a_unique_tag`, `test_the_estimate_is_checked_against_the_budget_before_the_first_call`, `test_a_restart_skips_calls_the_journal_already_holds`, `test_the_estimate_only_counts_the_calls_still_to_make`, `test_a_stop_request_ends_the_run_cleanly_between_calls`, `test_a_model_that_rejects_sampling_cannot_run_the_three_settings`, `test_throttling_pauses_after_each_call`.

`tests/unit/application/test_run_meter.py`, lines 1 to 14:

```python
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
```

- Brings in `date` from the standard library module `datetime`.
- Brings in `Decimal` from the standard library module `decimal`.
- Makes the module `pytest` (installed package) available.
- Brings in `MemoryJournal` (An in-memory journal with the same contract as the CSV one.), `ScriptedModel` (Answers every request from a function, and remembers the requests it saw.), `prompt`, `row` from the project module `tests.conftest`.
- Brings in `RunMeter` (Calls the model once per (prompt, setting, repeat) that the journal does not hold yet.), `RunPlan` (Everything that defines a run besides the model and the journal.), `estimate_pending` (The cost of the calls the journal does not hold yet, estimated before the first one.), `plan_keys` (Every call the plan covers, in the order they are made.) from the project module `token_meter.application.run_meter`.
- Brings in `DEFAULT_SETTINGS` from the project module `token_meter.domain.decoding`.
- Brings in `UnsupportedParameter` (The adapter cannot honor a parameter the request asked for (for example sampling on Claude).) from the project module `token_meter.domain.errors`.
- Brings in `BudgetExceeded` (The estimate is above the budget, so the run must not start.), `TokenEstimator` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.) from the project module `token_meter.domain.estimation`.
- Brings in `PriceTable` (Price per 1,000 input and output tokens, with the day the numbers were read.) from the project module `token_meter.domain.pricing`.
- Brings in `Kind` (What a prompt is for; the report breaks every number out by kind.) from the project module `token_meter.domain.prompts`.
- Stores the result of calling `PriceTable` under the name `PRICES`.
  - `PriceTable` from the project's `token_meter.domain.pricing` (Price per 1,000 input and output tokens, with the day the numbers were read.).
  - `Decimal` from the standard library module `decimal`.
  - `date` from the standard library module `datetime`.

`tests/unit/application/test_run_meter.py`, lines 15 to 27:

```python
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
```

- Stores a list of 2 item(s) under the name `PROMPTS`.
  - `prompt` from the project's `tests.conftest`.
  - `*` is multiply.
- Defines the function `plan`.
- Its parameters:
    - `**changes` collects any extra named arguments into a dictionary.
- Stores a dictionary with 6 entries under the name `base`.
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Ends the function and gives back the result of calling `RunPlan` to the caller.
  - `RunPlan` from the project's `token_meter.application.run_meter` (Everything that defines a run besides the model and the journal.).
  - `**name` inside a call passes every entry of a dictionary as a named argument.

`tests/unit/application/test_run_meter.py`, lines 30 to 39:

```python
def test_a_plan_covers_every_prompt_setting_and_repeat():
    assert len(plan_keys(plan())) == 2 * 3 * 3


def test_a_run_makes_every_call_and_journals_one_row_each():
    model, journal = ScriptedModel(), MemoryJournal()
    summary = RunMeter(model, journal).run(plan())
    assert (summary.calls_made, summary.calls_skipped, summary.interrupted) == (18, 0, False)
    assert len(journal.rows()) == 18
    assert len({r.key for r in journal.rows()}) == 18
```

- Defines the function `test_a_plan_covers_every_prompt_setting_and_repeat`.
- It takes no parameters.
- Checks that `len(plan_keys(plan())) == 2 * 3 * 3` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `*` is multiply.
  - `plan_keys` from the project's `token_meter.application.run_meter` (Every call the plan covers, in the order they are made.).
  - `plan`, a function of this file.
- Defines the function `test_a_run_makes_every_call_and_journals_one_row_each`.
- It takes no parameters.
- Stores a tuple of 2 item(s) under the name `(model, journal)`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `MemoryJournal` from the project's `tests.conftest` (An in-memory journal with the same contract as the CSV one.).
- Stores the result of calling `RunMeter(model, journal).run` under the name `summary`.
  - The method `run` of the project's `RunMeter` (Refuse above the budget before any call, then make the missing calls, one journal row each.).
  - `plan`, a function of this file.
  - `RunMeter` from the project's `token_meter.application.run_meter` (Calls the model once per (prompt, setting, repeat) that the journal does not hold yet.).
- Checks that `(summary.calls_made, summary.calls_skipped, summary.interrupted) == (18, 0, F...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `len(journal.rows()) == 18` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - The method `rows` of `journal`.
- Checks that `len({r.key for r in journal.rows()}) == 18` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `rows` of `journal`.

`tests/unit/application/test_run_meter.py`, lines 42 to 53:

```python
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
```

- Defines the function `test_the_output_cap_is_the_same_for_every_setting_and_only_sampling_changes`.
- It takes no parameters.
- Stores the result of calling `ScriptedModel` under the name `model`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
- Calls the method `run` of the project's `RunMeter` (Refuse above the budget before any call, then make the missing calls, one journal row each.) with 1 argument(s); the result is not kept.
  - The method `run` of the project's `RunMeter` (Refuse above the budget before any call, then make the missing calls, one journal row each.).
  - `plan`, a function of this file.
  - `RunMeter` from the project's `token_meter.application.run_meter` (Calls the model once per (prompt, setting, repeat) that the journal does not hold yet.).
  - `MemoryJournal` from the project's `tests.conftest` (An in-memory journal with the same contract as the CSV one.).
- Checks that `{r.max_output_tokens for r in model.requests} == {50}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Checks that `{(r.temperature, r.top_p) for r in model.requests} == {(0.0, None), (0.7, Non...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Defines the function `test_every_request_carries_a_unique_tag`.
- It takes no parameters.
- Stores the result of calling `ScriptedModel` under the name `model`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
- Calls the method `run` of the project's `RunMeter` (Refuse above the budget before any call, then make the missing calls, one journal row each.) with 1 argument(s); the result is not kept.
  - The method `run` of the project's `RunMeter` (Refuse above the budget before any call, then make the missing calls, one journal row each.).
  - `plan`, a function of this file.
  - `RunMeter` from the project's `token_meter.application.run_meter` (Calls the model once per (prompt, setting, repeat) that the journal does not hold yet.).
  - `MemoryJournal` from the project's `tests.conftest` (An in-memory journal with the same contract as the CSV one.).
- Checks that `len({r.tag for r in model.requests}) == 18` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Checks that `model.requests[0].tag == 'a/t0/0'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/application/test_run_meter.py`, lines 56 to 67:

```python
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
```

- Defines the function `test_the_estimate_is_checked_against_the_budget_before_the_first_call`.
- It takes no parameters.
- Stores a tuple of 2 item(s) under the name `(model, journal)`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `MemoryJournal` from the project's `tests.conftest` (An in-memory journal with the same contract as the CSV one.).
- A `with` block: it sets up `pytest.raises(BudgetExceeded)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `run` of the project's `RunMeter` (Refuse above the budget before any call, then make the missing calls, one journal row each.) with 1 argument(s); the result is not kept.
  - The method `run` of the project's `RunMeter` (Refuse above the budget before any call, then make the missing calls, one journal row each.).
  - `plan`, a function of this file.
  - `RunMeter` from the project's `token_meter.application.run_meter` (Calls the model once per (prompt, setting, repeat) that the journal does not hold yet.).
  - `Decimal` from the standard library module `decimal`.
- Checks that `model.requests == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `journal.rows() == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `rows` of `journal`.
- Defines the function `test_a_restart_skips_calls_the_journal_already_holds`.
- It takes no parameters.
- Stores the result of calling `MemoryJournal` under the name `journal`.
  - `MemoryJournal` from the project's `tests.conftest` (An in-memory journal with the same contract as the CSV one.).
  - `row` from the project's `tests.conftest`.
- Stores the result of calling `ScriptedModel` under the name `model`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
- Stores the result of calling `RunMeter(model, journal).run` under the name `summary`.
  - The method `run` of the project's `RunMeter` (Refuse above the budget before any call, then make the missing calls, one journal row each.).
  - `plan`, a function of this file.
  - `RunMeter` from the project's `token_meter.application.run_meter` (Calls the model once per (prompt, setting, repeat) that the journal does not hold yet.).

`tests/unit/application/test_run_meter.py`, lines 68 to 81:

```python
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
```

- Checks that `(summary.calls_made, summary.calls_skipped) == (16, 2)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `'a/t0/0' not in {r.tag for r in model.requests}` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Checks that `len({r.key for r in journal.rows()}) == len(journal.rows()) == 18` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `rows` of `journal`.
- Defines the function `test_the_estimate_only_counts_the_calls_still_to_make`.
- It takes no parameters.
- Stores the result of calling `MemoryJournal` under the name `journal`.
  - `MemoryJournal` from the project's `tests.conftest` (An in-memory journal with the same contract as the CSV one.).
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `row` from the project's `tests.conftest`.
  - `range` makes the numbers from 0 up to (not including) the given one.
- Stores the result of calling `estimate_pending` under the name `estimate`.
  - `estimate_pending` from the project's `token_meter.application.run_meter` (The cost of the calls the journal does not hold yet, estimated before the first one.).
  - `plan`, a function of this file.
  - The method `done_keys` of `journal`.
- Checks that `estimate.calls == 9` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `estimate.input_tokens == 20 * 9` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `*` is multiply.
- Checks that `estimate.output_tokens == 9 * 50` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `*` is multiply.
- Defines the function `test_a_stop_request_ends_the_run_cleanly_between_calls`.
- It takes no parameters.

`tests/unit/application/test_run_meter.py`, lines 82 to 95:

```python
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
```

- Stores the result of calling `iter` under the name `stops`.
  - `iter` makes an iterator over a collection.
- Stores the result of calling `RunMeter(ScriptedModel(), MemoryJournal(), stop...` under the name `summary`.
  - The method `run` of the project's `RunMeter` (Refuse above the budget before any call, then make the missing calls, one journal row each.).
  - `plan`, a function of this file.
  - `RunMeter` from the project's `token_meter.application.run_meter` (Calls the model once per (prompt, setting, repeat) that the journal does not hold yet.).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `MemoryJournal` from the project's `tests.conftest` (An in-memory journal with the same contract as the CSV one.).
  - `lambda args: expression` is a small unnamed function written inline.
  - `next` takes the next item from an iterator.
- Checks that `summary.interrupted` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `summary.calls_made == 2` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_a_model_that_rejects_sampling_cannot_run_the_three_settings`.
- It takes no parameters.
- Stores the result of calling `ScriptedModel` under the name `model`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
- A `with` block: it sets up `pytest.raises(UnsupportedParameter, match='does not accep...`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `run` of the project's `RunMeter` (Refuse above the budget before any call, then make the missing calls, one journal row each.) with 1 argument(s); the result is not kept.
  - The method `run` of the project's `RunMeter` (Refuse above the budget before any call, then make the missing calls, one journal row each.).
  - `plan`, a function of this file.
  - `RunMeter` from the project's `token_meter.application.run_meter` (Calls the model once per (prompt, setting, repeat) that the journal does not hold yet.).
  - `MemoryJournal` from the project's `tests.conftest` (An in-memory journal with the same contract as the CSV one.).
- Checks that `model.requests == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_throttling_pauses_after_each_call`.
- It takes no parameters.

`tests/unit/application/test_run_meter.py`, lines 96 to 98:

```python
    pauses: list[float] = []
    RunMeter(ScriptedModel(), MemoryJournal(), sleep=pauses.append).run(plan(throttle_seconds=0.2, repeats=1))
    assert pauses == [0.2] * 6
```

- Declares `pauses` as a list of a decimal number and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Calls the method `run` of the project's `RunMeter` (Refuse above the budget before any call, then make the missing calls, one journal row each.) with 1 argument(s); the result is not kept.
  - The method `run` of the project's `RunMeter` (Refuse above the budget before any call, then make the missing calls, one journal row each.).
  - `plan`, a function of this file.
  - `RunMeter` from the project's `token_meter.application.run_meter` (Calls the model once per (prompt, setting, repeat) that the journal does not hold yet.).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `MemoryJournal` from the project's `tests.conftest` (An in-memory journal with the same contract as the CSV one.).
- Checks that `pauses == [0.2] * 6` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `*` is multiply.

### `tests/unit/domain/test_analysis.py`

137 non-blank lines; it defines `test_the_naive_estimator_is_off_most_on_short_prompts`, `test_the_largest_gap_names_a_cause`, `test_the_measured_overhead_is_the_median_residual`, `test_with_the_overhead_added_the_total_error_nearly_vanishes`, `test_a_missing_setting_is_reported`, `test_explain_gap_picks_the_cause_from_the_kind_and_the_size`, `test_label_extraction_finds_the_first_category_word`, `test_spread_counts_distinct_answers_agreement_and_cost`, `test_a_setting_without_label_prompts_has_no_agreement_and_an_empty_journal_is_refused`, `test_calibration_measures_overhead_a_density_per_kind_and_answer_length`, `test_each_prompt_is_forecast_by_an_estimator_that_never_saw_it`, `test_an_outlier_prompt_leaves_a_visible_gap_even_when_the_totals_look_fine`, ....

`tests/unit/domain/test_analysis.py`, lines 1 to 6:

```python
from datetime import date
from decimal import Decimal

import pytest

from tests.conftest import prompt, row
```

- Brings in `date` from the standard library module `datetime`.
- Brings in `Decimal` from the standard library module `decimal`.
- Makes the module `pytest` (installed package) available.
- Brings in `prompt`, `row` from the project module `tests.conftest`.

`tests/unit/domain/test_analysis.py`, lines 7 to 20:

```python
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
```

- Brings in `NotEnoughData` (The journal does not hold the rows the analysis needs.), `calibrate` (Measure the overhead, the characters per token of each kind and the mean answer length per kind and setting.), `calibrate_overhead` (The median of billed minus estimated input tokens: the fixed cost every call carries.), `compare_estimates` (Join estimates to billed input tokens (one row per prompt at `setting`) and group by kind.), `explain_gap` (Name the cause of a gap from its size.), `extract_label` (The first category word in an answer, or `none` when it names no category.), `leave_one_out` (Estimate every prompt with an estimator that never saw it, so the error is an honest forecast error.), `measure_spread` (Count distinct answers per prompt and setting, label agreement, output length and cost per 1,000 calls.) from the project module `token_meter.domain.analysis`.
- Brings in `TokenEstimator` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.) from the project module `token_meter.domain.estimation`.
- Brings in `StopReason` (Why the model stopped writing.) from the project module `token_meter.domain.llm`.
- Brings in `PriceTable` (Price per 1,000 input and output tokens, with the day the numbers were read.) from the project module `token_meter.domain.pricing`.
- Brings in `Kind` (What a prompt is for; the report breaks every number out by kind.) from the project module `token_meter.domain.prompts`.

`tests/unit/domain/test_analysis.py`, lines 22 to 34:

```python
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
```

- Stores the result of calling `PriceTable` under the name `PRICES`.
  - `PriceTable` from the project's `token_meter.domain.pricing` (Price per 1,000 input and output tokens, with the day the numbers were read.).
  - `Decimal` from the standard library module `decimal`.
  - `date` from the standard library module `datetime`.
- Stores a list of 4 item(s) under the name `PROMPTS`.
  - `prompt` from the project's `tests.conftest`.
  - `*` is multiply.
- Stores a list of 4 item(s) under the name `T0`.
  - `row` from the project's `tests.conftest`.
- Defines the function `test_the_naive_estimator_is_off_most_on_short_prompts`.
- It takes no parameters.
- Stores the result of calling `compare_estimates` under the name `report`.
  - `compare_estimates` from the project's `token_meter.domain.analysis` (Join estimates to billed input tokens (one row per prompt at `setting`) and group by kind.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).

`tests/unit/domain/test_analysis.py`, lines 35 to 48:

```python
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
```

- Stores a dictionary built by looping under the name `errors`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Checks that `errors['short'] == pytest.approx(-28 / 38)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `pytest.approx` compares numbers with a small tolerance.
  - `/` is divide.
- Checks that `errors['long'] == pytest.approx(-28 / 128)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `pytest.approx` compares numbers with a small tolerance.
  - `/` is divide.
- Checks that `report.total.estimated == 130` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `report.total.billed == 248` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_the_largest_gap_names_a_cause`.
- It takes no parameters.
- Stores the `largest_gap` of `compare_estimates(PROMPTS, T0, TokenE...` under the name `gap`.
  - `compare_estimates` from the project's `token_meter.domain.analysis` (Join estimates to billed input tokens (one row per prompt at `setting`) and group by kind.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Checks that `gap.prompt_id == 'g'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `'template overhead' in gap.cause` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Defines the function `test_the_measured_overhead_is_the_median_residual`.
- It takes no parameters.

`tests/unit/domain/test_analysis.py`, lines 49 to 62:

```python
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
```

- Checks that `calibrate_overhead(PROMPTS, T0, TokenEstimator()) == 28` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `calibrate_overhead` from the project's `token_meter.domain.analysis` (The median of billed minus estimated input tokens: the fixed cost every call carries.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Defines the function `test_with_the_overhead_added_the_total_error_nearly_vanishes`.
- It takes no parameters.
- Stores the result of calling `compare_estimates` under the name `report`.
  - `compare_estimates` from the project's `token_meter.domain.analysis` (Join estimates to billed input tokens (one row per prompt at `setting`) and group by kind.).
  - The method `with_overhead` of the project's `TokenEstimator` (The same ratios with a different fixed overhead.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Checks that `abs(report.total.error) < 0.03` is true; if it is not, the test fails with an `AssertionError`.
  - `<` means less than.
  - `abs` gives the absolute value (the number without its sign).
- Checks that `report.largest_gap.kind is Kind.LANGUAGE` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `'tokens per character' in report.largest_gap.cause` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Defines the function `test_a_missing_setting_is_reported`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(NotEnoughData, match="'t0'")`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `compare_estimates` from the project's `token_meter.domain.analysis` (Join estimates to billed input tokens (one row per prompt at `setting`) and group by kind.) with 3 argument(s); the result is not kept.
  - `compare_estimates` from the project's `token_meter.domain.analysis` (Join estimates to billed input tokens (one row per prompt at `setting`) and group by kind.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
  - `row` from the project's `tests.conftest`.
- A `with` block: it sets up `pytest.raises(NotEnoughData)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.

`tests/unit/domain/test_analysis.py`, lines 63 to 63:

```python
        calibrate_overhead(PROMPTS, [], TokenEstimator())
```

- Calls `calibrate_overhead` from the project's `token_meter.domain.analysis` (The median of billed minus estimated input tokens: the fixed cost every call carries.) with 3 argument(s); the result is not kept.
  - `calibrate_overhead` from the project's `token_meter.domain.analysis` (The median of billed minus estimated input tokens: the fixed cost every call carries.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).

`tests/unit/domain/test_analysis.py`, lines 66 to 77:

```python
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
```

- Defines the function `test_explain_gap_picks_the_cause_from_the_kind_and_the_size`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `kind`.
    - `estimated`.
    - `billed`.
    - `missing`.
    - `fragment`.

`tests/unit/domain/test_analysis.py`, lines 78 to 87:

```python
    assert fragment in explain_gap(kind, estimated, billed, missing)


def test_label_extraction_finds_the_first_category_word():
    assert extract_label("Billing.") == "billing"
    assert extract_label("The category is shipping, not billing") == "shipping"
    assert extract_label("no idea") == "none"


def test_spread_counts_distinct_answers_agreement_and_cost():
```

- Checks that `fragment in explain_gap(kind, estimated, billed, missing)` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `explain_gap` from the project's `token_meter.domain.analysis` (Name the cause of a gap from its size.).
- Defines the function `test_label_extraction_finds_the_first_category_word`.
- It takes no parameters.
- Checks that `extract_label('Billing.') == 'billing'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `extract_label` from the project's `token_meter.domain.analysis` (The first category word in an answer, or `none` when it names no category.).
- Checks that `extract_label('The category is shipping, not billing') == 'shipping'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `extract_label` from the project's `token_meter.domain.analysis` (The first category word in an answer, or `none` when it names no category.).
- Checks that `extract_label('no idea') == 'none'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `extract_label` from the project's `token_meter.domain.analysis` (The first category word in an answer, or `none` when it names no category.).
- Defines the function `test_spread_counts_distinct_answers_agreement_and_cost`.
- It takes no parameters.

`tests/unit/domain/test_analysis.py`, lines 88 to 101:

```python
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
```

- Stores a list of 12 item(s) under the name `rows`.
  - `row` from the project's `tests.conftest`.

`tests/unit/domain/test_analysis.py`, lines 102 to 115:

```python
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
```

- Stores the result of calling `measure_spread` under the name `report`.
  - `measure_spread` from the project's `token_meter.domain.analysis` (Count distinct answers per prompt and setting, label agreement, output length and cost per 1,000 calls.).
- Stores the `settings` of `report` under the name `(t0, t10)`.
- Checks that `t0.setting == 't0'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `t0.mean_distinct_answers == 1.0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `t0.label_agreement == 1.0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `report.zero_temperature_identical` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `t10.mean_distinct_answers == 2.5` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `t10.label_agreement == pytest.approx(2 / 3)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `pytest.approx` compares numbers with a small tolerance.
  - `/` is divide.
- Checks that `t10.mean_output_tokens == 4.0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `t10.length_stop_share == pytest.approx(1 / 6)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `pytest.approx` compares numbers with a small tolerance.
  - `/` is divide.
- Checks that `t10.cost_per_1000 == (PRICES.cost(10, 6) * 3 + PRICES.cost(10, 2) * 3) / 6 * ...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `*` is multiply.
  - `/` is divide.
  - `+` is add.
  - The method `cost` of the project's `PriceTable` (Cost in dollars of a call with these token counts.).
- Defines the function `test_a_setting_without_label_prompts_has_no_agreement_and_an_empty_journal_is_refused`.
- It takes no parameters.

`tests/unit/domain/test_analysis.py`, lines 116 to 124:

```python
    report = measure_spread(PROMPTS, [row("s", "t07", 0, 1, 1)], PRICES)
    assert report.settings[0].label_agreement is None
    assert not report.zero_temperature_identical
    with pytest.raises(NotEnoughData):
        measure_spread(PROMPTS, [], PRICES)


def test_calibration_measures_overhead_a_density_per_kind_and_answer_length():
    fit = [prompt("s", Kind.SHORT, "a" * 40), prompt("s2", Kind.SHORT, "a" * 80), prompt("l", Kind.LONG, "a" * 300)]
```

- Stores the result of calling `measure_spread` under the name `report`.
  - `measure_spread` from the project's `token_meter.domain.analysis` (Count distinct answers per prompt and setting, label agreement, output length and cost per 1,000 calls.).
  - `row` from the project's `tests.conftest`.
- Checks that `report.settings[0].label_agreement is None` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `not report.zero_temperature_identical` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
- A `with` block: it sets up `pytest.raises(NotEnoughData)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `measure_spread` from the project's `token_meter.domain.analysis` (Count distinct answers per prompt and setting, label agreement, output length and cost per 1,000 calls.) with 3 argument(s); the result is not kept.
  - `measure_spread` from the project's `token_meter.domain.analysis` (Count distinct answers per prompt and setting, label agreement, output length and cost per 1,000 calls.).
- Defines the function `test_calibration_measures_overhead_a_density_per_kind_and_answer_length`.
- It takes no parameters.
- Stores a list of 3 item(s) under the name `fit`.
  - `prompt` from the project's `tests.conftest`.
  - `*` is multiply.

`tests/unit/domain/test_analysis.py`, lines 125 to 137:

```python
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
```

- Stores a list of 5 item(s) under the name `rows`.
  - `row` from the project's `tests.conftest`.
- Stores the result of calling `calibrate` under the name `calibration`.
  - `calibrate` from the project's `token_meter.domain.analysis` (Measure the overhead, the characters per token of each kind and the mean answer length per kind and setting.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Checks that `calibration.estimator.per_call_overhead == 28` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `calibration.estimator.by_kind[Kind.SHORT] == pytest.approx(4.0)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `pytest.approx` compares numbers with a small tolerance.
- Checks that `calibration.estimator.by_kind[Kind.LONG] == pytest.approx(3.0)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `pytest.approx` compares numbers with a small tolerance.
- Checks that `calibration.mean_output[Kind.SHORT, 't07'] == 20` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `calibration.estimator.tokens('a' * 30, kind=Kind.LONG) == 10 + 28` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `tokens` of the project's `TokenEstimator` (Estimated input tokens of one call that sends `text` (and `system`).).
  - `+` is add.
  - `*` is multiply.

`tests/unit/domain/test_analysis.py`, lines 140 to 151:

```python
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
```

- Defines the function `test_each_prompt_is_forecast_by_an_estimator_that_never_saw_it`.
- It takes no parameters.
- Stores a list built by looping under the name `prompts`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `prompt` from the project's `tests.conftest`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `*` is multiply.
  - `range` makes the numbers from 0 up to (not including) the given one.
  - `+` is add.
- Stores a list built by looping under the name `rows`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `row` from the project's `tests.conftest`.
  - `+` is add.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
  - `range` makes the numbers from 0 up to (not including) the given one.
- Stores the result of calling `leave_one_out` under the name `result`.
  - `leave_one_out` from the project's `token_meter.domain.analysis` (Estimate every prompt with an estimator that never saw it, so the error is an honest forecast error.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Checks that `result.cost.calls == 8` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `result.cost.within` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `abs(result.input_tokens.total.error) < 0.02` is true; if it is not, the test fails with an `AssertionError`.
  - `<` means less than.
  - `abs` gives the absolute value (the number without its sign).
- Checks that `result.cost.ceiling > result.cost.billed` is true; if it is not, the test fails with an `AssertionError`.
  - `>` means greater than.
- Defines the function `test_an_outlier_prompt_leaves_a_visible_gap_even_when_the_totals_look_fine`.
- It takes no parameters.
- Stores the result of `[prompt(f's{i}', Kind.SHORT, 'a' * 40) for i in range(3)]...` under the name `prompts`.
  - `+` is add.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `prompt` from the project's `tests.conftest`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `*` is multiply.
  - `range` makes the numbers from 0 up to (not including) the given one.

`tests/unit/domain/test_analysis.py`, lines 152 to 163:

```python
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
```

- Stores the result of `[row(p.id, 't0', 0, 38, 10) for p in prompts[:3]] + [row(...` under the name `rows`.
  - `+` is add.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `row` from the project's `tests.conftest`.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
- Stores the result of calling `leave_one_out` under the name `result`.
  - `leave_one_out` from the project's `token_meter.domain.analysis` (Estimate every prompt with an estimator that never saw it, so the error is an honest forecast error.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Stores the `largest_gap` of `result.input_tokens` under the name `gap`.
- Checks that `abs(gap.billed - gap.estimated) / gap.billed > 0.4` is true; if it is not, the test fails with an `AssertionError`.
  - `>` means greater than.
  - `/` is divide.
  - `abs` gives the absolute value (the number without its sign).
  - `-` is subtract.
- Checks that `abs(result.input_tokens.total.error) < 0.05` is true; if it is not, the test fails with an `AssertionError`.
  - `<` means less than.
  - `abs` gives the absolute value (the number without its sign).
- Defines the function `test_a_kind_with_one_prompt_borrows_the_answer_length_of_the_same_setting`.
- It takes no parameters.
- Stores a list of 2 item(s) under the name `prompts`.
  - `prompt` from the project's `tests.conftest`.
  - `*` is multiply.
- Stores a list of 2 item(s) under the name `rows`.
  - `row` from the project's `tests.conftest`.
- Stores the result of calling `leave_one_out` under the name `result`.
  - `leave_one_out` from the project's `token_meter.domain.analysis` (Estimate every prompt with an estimator that never saw it, so the error is an honest forecast error.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Checks that `result.cost.calls == 2` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/unit/domain/test_analysis.py`, lines 166 to 168:

```python
def test_leave_one_out_needs_two_prompts():
    with pytest.raises(NotEnoughData, match="at least two"):
        leave_one_out([prompt("a", Kind.SHORT, "x")], [row("a", "t0", 0, 1, 1)], TokenEstimator(), PRICES, 200)
```

- Defines the function `test_leave_one_out_needs_two_prompts`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(NotEnoughData, match='at least two')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `leave_one_out` from the project's `token_meter.domain.analysis` (Estimate every prompt with an estimator that never saw it, so the error is an honest forecast error.) with 5 argument(s); the result is not kept.
  - `leave_one_out` from the project's `token_meter.domain.analysis` (Estimate every prompt with an estimator that never saw it, so the error is an honest forecast error.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
  - `prompt` from the project's `tests.conftest`.
  - `row` from the project's `tests.conftest`.

### `tests/unit/domain/test_llm.py`

22 non-blank lines; it defines `request`, `test_the_same_request_always_has_the_same_fingerprint`, `test_the_model_name_is_not_part_of_the_fingerprint`, `test_the_tag_and_the_sampling_settings_are_part_of_the_fingerprint`, `test_tools_and_schemas_change_the_fingerprint`, `test_a_response_survives_a_json_round_trip_with_tool_calls`.

`tests/unit/domain/test_llm.py`, lines 1 to 14:

```python
from token_meter.domain.llm import ChatMessage, ChatRequest, ChatResponse, StopReason, ToolCall, ToolSpec, Usage


def request(**changes):
    base = {"messages": (ChatMessage.user("hello"),), "max_output_tokens": 50, "tag": "a"}
    return ChatRequest(**{**base, **changes})


def test_the_same_request_always_has_the_same_fingerprint():
    assert request().fingerprint() == request().fingerprint()


def test_the_model_name_is_not_part_of_the_fingerprint():
    assert request(model="a-model").fingerprint() == request(model="another").fingerprint()
```

- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.), `StopReason` (Why the model stopped writing.), `ToolCall` (A tool call the model asked for.), `ToolSpec` (A tool the model may call: a name, a description and a JSON Schema for the arguments.), `Usage` (Tokens the provider billed for one call, read from its usage block, never recomputed.) from the project module `token_meter.domain.llm`.
- Defines the function `request`.
- Its parameters:
    - `**changes` collects any extra named arguments into a dictionary.
- Stores a dictionary with 3 entries under the name `base`.
  - The method `user` of `ChatMessage`.
- Ends the function and gives back the result of calling `ChatRequest` to the caller.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `**name` inside a call passes every entry of a dictionary as a named argument.
- Defines the function `test_the_same_request_always_has_the_same_fingerprint`.
- It takes no parameters.
- Checks that `request().fingerprint() == request().fingerprint()` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Defines the function `test_the_model_name_is_not_part_of_the_fingerprint`.
- It takes no parameters.
- Checks that `request(model='a-model').fingerprint() == request(model='another').fingerprint()` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.

`tests/unit/domain/test_llm.py`, lines 17 to 27:

```python
def test_the_tag_and_the_sampling_settings_are_part_of_the_fingerprint():
    base = request().fingerprint()
    assert request(tag="b").fingerprint() != base
    assert request(temperature=0.7).fingerprint() != base
    assert request(top_p=0.9).fingerprint() != base


def test_tools_and_schemas_change_the_fingerprint():
    base = request().fingerprint()
    assert request(response_schema={"type": "object"}).fingerprint() != base
    assert request(tools=(ToolSpec("t", "d", {"type": "object"}),)).fingerprint() != base
```

- Defines the function `test_the_tag_and_the_sampling_settings_are_part_of_the_fingerprint`.
- It takes no parameters.
- Stores the result of calling `request().fingerprint` under the name `base`.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Checks that `request(tag='b').fingerprint() != base` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Checks that `request(temperature=0.7).fingerprint() != base` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Checks that `request(top_p=0.9).fingerprint() != base` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Defines the function `test_tools_and_schemas_change_the_fingerprint`.
- It takes no parameters.
- Stores the result of calling `request().fingerprint` under the name `base`.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Checks that `request(response_schema={'type': 'object'}).fingerprint() != base` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
- Checks that `request(tools=(ToolSpec('t', 'd', {'type': 'object'}),)).fingerprint() != base` is true; if it is not, the test fails with an `AssertionError`.
  - `!=` means not equal.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
  - `request`, a function of this file.
  - `ToolSpec` from the project's `token_meter.domain.llm` (A tool the model may call: a name, a description and a JSON Schema for the arguments.).

`tests/unit/domain/test_llm.py`, lines 30 to 34:

```python
def test_a_response_survives_a_json_round_trip_with_tool_calls():
    response = ChatResponse(
        "text", StopReason.TOOL_CALLS, Usage(5, 7), 1.25, "m", (ToolCall("c1", "lookup", {"id": 4}),)
    )
    assert ChatResponse.from_json(response.to_json()) == response
```

- Defines the function `test_a_response_survives_a_json_round_trip_with_tool_calls`.
- It takes no parameters.
- Stores the result of calling `ChatResponse` under the name `response`.
  - `ChatResponse` from the project's `token_meter.domain.llm` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.).
  - `Usage` from the project's `token_meter.domain.llm` (Tokens the provider billed for one call, read from its usage block, never recomputed.).
  - `ToolCall` from the project's `token_meter.domain.llm` (A tool call the model asked for.).
- Checks that `ChatResponse.from_json(response.to_json()) == response` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `from_json` of `ChatResponse`.
  - The method `to_json` of `response`.

### `tests/unit/domain/test_pricing_and_estimation.py`

42 non-blank lines; it defines `test_cost_uses_separate_input_and_output_prices`, `test_a_fresh_table_is_accepted_and_an_old_one_is_refused`, `test_a_table_dated_in_the_future_is_refused`, `test_the_estimator_divides_characters_and_adds_the_overhead`, `test_with_overhead_returns_a_new_estimator`, `test_a_run_estimate_counts_calls_tokens_and_cost`, `test_a_budget_below_the_estimate_refuses_and_no_budget_never_does`.

`tests/unit/domain/test_pricing_and_estimation.py`, lines 1 to 14:

```python
from datetime import date
from decimal import Decimal

import pytest

from tests.conftest import prompt
from token_meter.domain.estimation import BudgetExceeded, TokenEstimator, estimate_run, require_within_budget
from token_meter.domain.pricing import PriceTable, StalePrices
from token_meter.domain.prompts import Kind

PRICES = PriceTable("m", Decimal("0.00015"), Decimal("0.0006"), date(2026, 10, 26))


def test_cost_uses_separate_input_and_output_prices():
```

- Brings in `date` from the standard library module `datetime`.
- Brings in `Decimal` from the standard library module `decimal`.
- Makes the module `pytest` (installed package) available.
- Brings in `prompt` from the project module `tests.conftest`.
- Brings in `BudgetExceeded` (The estimate is above the budget, so the run must not start.), `TokenEstimator` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.), `estimate_run` (Estimate a run of `calls_per_prompt` calls for each prompt, each assumed to use the full output cap.), `require_within_budget` (Raise `BudgetExceeded` when a budget is set and the estimate is above it.) from the project module `token_meter.domain.estimation`.
- Brings in `PriceTable` (Price per 1,000 input and output tokens, with the day the numbers were read.), `StalePrices` (The price table was read too long ago to trust.) from the project module `token_meter.domain.pricing`.
- Brings in `Kind` (What a prompt is for; the report breaks every number out by kind.) from the project module `token_meter.domain.prompts`.
- Stores the result of calling `PriceTable` under the name `PRICES`.
  - `PriceTable` from the project's `token_meter.domain.pricing` (Price per 1,000 input and output tokens, with the day the numbers were read.).
  - `Decimal` from the standard library module `decimal`.
  - `date` from the standard library module `datetime`.
- Defines the function `test_cost_uses_separate_input_and_output_prices`.
- It takes no parameters.

`tests/unit/domain/test_pricing_and_estimation.py`, lines 15 to 27:

```python
    assert PRICES.cost(1000, 1000) == Decimal("0.00075")
    assert PRICES.cost(0, 0) == 0


def test_a_fresh_table_is_accepted_and_an_old_one_is_refused():
    PRICES.require_fresh(date(2026, 11, 20), 30)
    with pytest.raises(StalePrices, match="read on 2026-10-26, 36 days ago"):
        PRICES.require_fresh(date(2026, 12, 1), 30)


def test_a_table_dated_in_the_future_is_refused():
    with pytest.raises(StalePrices, match="after today"):
        PRICES.require_fresh(date(2026, 10, 1), 30)
```

- Checks that `PRICES.cost(1000, 1000) == Decimal('0.00075')` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `cost` of the project's `PriceTable` (Cost in dollars of a call with these token counts.).
  - `Decimal` from the standard library module `decimal`.
- Checks that `PRICES.cost(0, 0) == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `cost` of the project's `PriceTable` (Cost in dollars of a call with these token counts.).
- Defines the function `test_a_fresh_table_is_accepted_and_an_old_one_is_refused`.
- It takes no parameters.
- Calls the method `require_fresh` of the project's `PriceTable` (Raise `StalePrices` when the table is older than `max_age_days` (or dated in the future).) with 2 argument(s); the result is not kept.
  - The method `require_fresh` of the project's `PriceTable` (Raise `StalePrices` when the table is older than `max_age_days` (or dated in the future).).
  - `date` from the standard library module `datetime`.
- A `with` block: it sets up `pytest.raises(StalePrices, match='read on 2026-10-26, 36 ...`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `require_fresh` of the project's `PriceTable` (Raise `StalePrices` when the table is older than `max_age_days` (or dated in the future).) with 2 argument(s); the result is not kept.
  - The method `require_fresh` of the project's `PriceTable` (Raise `StalePrices` when the table is older than `max_age_days` (or dated in the future).).
  - `date` from the standard library module `datetime`.
- Defines the function `test_a_table_dated_in_the_future_is_refused`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(StalePrices, match='after today')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `require_fresh` of the project's `PriceTable` (Raise `StalePrices` when the table is older than `max_age_days` (or dated in the future).) with 2 argument(s); the result is not kept.
  - The method `require_fresh` of the project's `PriceTable` (Raise `StalePrices` when the table is older than `max_age_days` (or dated in the future).).
  - `date` from the standard library module `datetime`.

`tests/unit/domain/test_pricing_and_estimation.py`, lines 30 to 40:

```python
def test_the_estimator_divides_characters_and_adds_the_overhead():
    assert TokenEstimator().tokens("a" * 40) == 10
    assert TokenEstimator(per_call_overhead=28).tokens("a" * 40) == 38
    assert TokenEstimator().tokens("") == 1
    assert TokenEstimator().tokens("a" * 40, system="b" * 8) == 12


def test_with_overhead_returns_a_new_estimator():
    base = TokenEstimator()
    assert base.with_overhead(5).per_call_overhead == 5
    assert base.per_call_overhead == 0
```

- Defines the function `test_the_estimator_divides_characters_and_adds_the_overhead`.
- It takes no parameters.
- Checks that `TokenEstimator().tokens('a' * 40) == 10` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `tokens` of the project's `TokenEstimator` (Estimated input tokens of one call that sends `text` (and `system`).).
  - `*` is multiply.
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Checks that `TokenEstimator(per_call_overhead=28).tokens('a' * 40) == 38` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `tokens` of the project's `TokenEstimator` (Estimated input tokens of one call that sends `text` (and `system`).).
  - `*` is multiply.
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Checks that `TokenEstimator().tokens('') == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `tokens` of the project's `TokenEstimator` (Estimated input tokens of one call that sends `text` (and `system`).).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Checks that `TokenEstimator().tokens('a' * 40, system='b' * 8) == 12` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `tokens` of the project's `TokenEstimator` (Estimated input tokens of one call that sends `text` (and `system`).).
  - `*` is multiply.
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Defines the function `test_with_overhead_returns_a_new_estimator`.
- It takes no parameters.
- Stores the result of calling `TokenEstimator` under the name `base`.
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Checks that `base.with_overhead(5).per_call_overhead == 5` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `with_overhead` of the project's `TokenEstimator` (The same ratios with a different fixed overhead.).
- Checks that `base.per_call_overhead == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/unit/domain/test_pricing_and_estimation.py`, lines 43 to 54:

```python
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
```

- Defines the function `test_a_run_estimate_counts_calls_tokens_and_cost`.
- It takes no parameters.
- Stores a list of 2 item(s) under the name `prompts`.
  - `prompt` from the project's `tests.conftest`.
  - `*` is multiply.
- Stores the result of calling `estimate_run` under the name `estimate`.
  - `estimate_run` from the project's `token_meter.domain.estimation` (Estimate a run of `calls_per_prompt` calls for each prompt, each assumed to use the full output cap.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Checks that `estimate.calls == 18` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `estimate.input_tokens == (10 + 20) * 9` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `*` is multiply.
  - `+` is add.
- Checks that `estimate.output_tokens == 18 * 200` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `*` is multiply.
- Checks that `estimate.cost == PRICES.cost(270, 3600)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `cost` of the project's `PriceTable` (Cost in dollars of a call with these token counts.).
- Defines the function `test_a_budget_below_the_estimate_refuses_and_no_budget_never_does`.
- It takes no parameters.

`tests/unit/domain/test_pricing_and_estimation.py`, lines 55 to 59:

```python
    estimate = estimate_run([prompt("a", Kind.SHORT, "hi")], 1, 100, PRICES, TokenEstimator())
    with pytest.raises(BudgetExceeded, match="exceeds budget"):
        require_within_budget(estimate, Decimal("0.00001"))
    require_within_budget(estimate, Decimal("1"))
    require_within_budget(estimate, None)
```

- Stores the result of calling `estimate_run` under the name `estimate`.
  - `estimate_run` from the project's `token_meter.domain.estimation` (Estimate a run of `calls_per_prompt` calls for each prompt, each assumed to use the full output cap.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
  - `prompt` from the project's `tests.conftest`.
- A `with` block: it sets up `pytest.raises(BudgetExceeded, match='exceeds budget')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `require_within_budget` from the project's `token_meter.domain.estimation` (Raise `BudgetExceeded` when a budget is set and the estimate is above it.) with 2 argument(s); the result is not kept.
  - `require_within_budget` from the project's `token_meter.domain.estimation` (Raise `BudgetExceeded` when a budget is set and the estimate is above it.).
  - `Decimal` from the standard library module `decimal`.
- Calls `require_within_budget` from the project's `token_meter.domain.estimation` (Raise `BudgetExceeded` when a budget is set and the estimate is above it.) with 2 argument(s); the result is not kept.
  - `require_within_budget` from the project's `token_meter.domain.estimation` (Raise `BudgetExceeded` when a budget is set and the estimate is above it.).
  - `Decimal` from the standard library module `decimal`.
- Calls `require_within_budget` from the project's `token_meter.domain.estimation` (Raise `BudgetExceeded` when a budget is set and the estimate is above it.) with 2 argument(s); the result is not kept.
  - `require_within_budget` from the project's `token_meter.domain.estimation` (Raise `BudgetExceeded` when a budget is set and the estimate is above it.).

### `tests/unit/domain/test_prompts.py`

47 non-blank lines; it defines `small_spec`, `valid_set`, `test_a_set_that_matches_the_spec_is_accepted`, `test_the_lesson_spec_asks_for_fifty_prompts_in_five_kinds`, `test_repeated_ids_are_rejected_by_name`, `test_a_wrong_total_is_rejected`, `test_a_wrong_count_for_one_kind_is_rejected`, `test_a_set_with_no_long_prompt_is_rejected`, `test_a_row_missing_a_field_names_the_field`, `test_an_unknown_kind_is_rejected`, `test_a_label_prompt_needs_an_allowed_expected_label`, `test_only_label_prompts_keep_an_expected_label`.

`tests/unit/domain/test_prompts.py`, lines 1 to 11:

```python
import pytest

from tests.conftest import prompt
from token_meter.domain.prompts import InvalidPromptSet, Kind, PromptSetSpec, parse_prompt, validate_prompt_set


def small_spec(long_tokens: int = 10) -> PromptSetSpec:
    return PromptSetSpec({Kind.SHORT: 1, Kind.LONG: 1, Kind.LABEL: 1}, long_threshold_tokens=long_tokens)


def valid_set():
```

- Makes the module `pytest` (installed package) available.
- Brings in `prompt` from the project module `tests.conftest`.
- Brings in `InvalidPromptSet` (The prompt file breaks a rule of the lesson (row count, kinds, a long prompt, unique ids).), `Kind` (What a prompt is for; the report breaks every number out by kind.), `PromptSetSpec` (The shape the lesson asks for: counts per kind and one prompt over a token threshold.), `parse_prompt` (Build a record from one decoded JSON Lines row, naming the field that is wrong.), `validate_prompt_set` (Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken.) from the project module `token_meter.domain.prompts`.
- Defines the function `small_spec`. It returns the project type `PromptSetSpec`.
- Its parameters:
    - `long_tokens` holds a whole number; if the caller leaves it out it is the number `10`.
- Ends the function and gives back the result of calling `PromptSetSpec` to the caller.
  - `PromptSetSpec` from the project's `token_meter.domain.prompts` (The shape the lesson asks for: counts per kind and one prompt over a token threshold.).
- Defines the function `valid_set`.
- It takes no parameters.

`tests/unit/domain/test_prompts.py`, lines 12 to 24:

```python
    return [
        prompt("a", Kind.SHORT, "hi"),
        prompt("b", Kind.LONG, "x" * 400),
        prompt("c", Kind.LABEL, "classify", "billing"),
    ]


def test_a_set_that_matches_the_spec_is_accepted():
    validate_prompt_set(valid_set(), small_spec())


def test_the_lesson_spec_asks_for_fifty_prompts_in_five_kinds():
    assert sum(PromptSetSpec.lesson().counts.values()) == 50
```

- Ends the function and gives back a list of 3 item(s) to the caller.
  - `prompt` from the project's `tests.conftest`.
  - `*` is multiply.
- Defines the function `test_a_set_that_matches_the_spec_is_accepted`.
- It takes no parameters.
- Calls `validate_prompt_set` from the project's `token_meter.domain.prompts` (Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken.) with 2 argument(s); the result is not kept.
  - `validate_prompt_set` from the project's `token_meter.domain.prompts` (Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken.).
  - `valid_set`, a function of this file.
  - `small_spec`, a function of this file.
- Defines the function `test_the_lesson_spec_asks_for_fifty_prompts_in_five_kinds`.
- It takes no parameters.
- Checks that `sum(PromptSetSpec.lesson().counts.values()) == 50` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `sum` adds up all the numbers.
  - `.values(...)` gives the values of a dictionary.
  - The method `lesson` of `PromptSetSpec`.

`tests/unit/domain/test_prompts.py`, lines 27 to 38:

```python
def test_repeated_ids_are_rejected_by_name():
    items = [*valid_set(), prompt("a", Kind.SHORT, "again")]
    with pytest.raises(InvalidPromptSet, match=r"repeated: \['a'\]"):
        validate_prompt_set(items, small_spec())


def test_a_wrong_total_is_rejected():
    with pytest.raises(InvalidPromptSet, match="expected 3 prompts, found 2"):
        validate_prompt_set(valid_set()[:2], small_spec())


def test_a_wrong_count_for_one_kind_is_rejected():
```

- Defines the function `test_repeated_ids_are_rejected_by_name`.
- It takes no parameters.
- Stores a list of 2 item(s) under the name `items`.
  - `prompt` from the project's `tests.conftest`.
  - `valid_set`, a function of this file.
- A `with` block: it sets up `pytest.raises(InvalidPromptSet, match="repeated: \\['a'\\]")`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `validate_prompt_set` from the project's `token_meter.domain.prompts` (Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken.) with 2 argument(s); the result is not kept.
  - `validate_prompt_set` from the project's `token_meter.domain.prompts` (Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken.).
  - `small_spec`, a function of this file.
- Defines the function `test_a_wrong_total_is_rejected`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(InvalidPromptSet, match='expected 3 prompts...`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `validate_prompt_set` from the project's `token_meter.domain.prompts` (Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken.) with 2 argument(s); the result is not kept.
  - `validate_prompt_set` from the project's `token_meter.domain.prompts` (Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken.).
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - `small_spec`, a function of this file.
  - `valid_set`, a function of this file.
- Defines the function `test_a_wrong_count_for_one_kind_is_rejected`.
- It takes no parameters.

`tests/unit/domain/test_prompts.py`, lines 39 to 52:

```python
    items = [prompt("a", Kind.SHORT, "hi"), prompt("b", Kind.SHORT, "x" * 400), prompt("c", Kind.LABEL, "c", "other")]
    with pytest.raises(InvalidPromptSet, match="kind short"):
        validate_prompt_set(items, small_spec())


def test_a_set_with_no_long_prompt_is_rejected():
    with pytest.raises(InvalidPromptSet, match="over 1000 tokens"):
        validate_prompt_set(valid_set(), small_spec(long_tokens=1000))


@pytest.mark.parametrize("field", ["id", "kind", "text"])
def test_a_row_missing_a_field_names_the_field(field):
    row = {"id": "a", "kind": "short", "text": "hi"}
    del row[field]
```

- Stores a list of 3 item(s) under the name `items`.
  - `prompt` from the project's `tests.conftest`.
  - `*` is multiply.
- A `with` block: it sets up `pytest.raises(InvalidPromptSet, match='kind short')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `validate_prompt_set` from the project's `token_meter.domain.prompts` (Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken.) with 2 argument(s); the result is not kept.
  - `validate_prompt_set` from the project's `token_meter.domain.prompts` (Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken.).
  - `small_spec`, a function of this file.
- Defines the function `test_a_set_with_no_long_prompt_is_rejected`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(InvalidPromptSet, match='over 1000 tokens')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `validate_prompt_set` from the project's `token_meter.domain.prompts` (Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken.) with 2 argument(s); the result is not kept.
  - `validate_prompt_set` from the project's `token_meter.domain.prompts` (Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken.).
  - `valid_set`, a function of this file.
  - `small_spec`, a function of this file.
- Defines the function `test_a_row_missing_a_field_names_the_field`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `field`.
- Stores a dictionary with 3 entries under the name `row`.
- Removes `row[field]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/domain/test_prompts.py`, lines 53 to 64:

```python
    with pytest.raises(InvalidPromptSet, match=f"field '{field}'"):
        parse_prompt(row)


def test_an_unknown_kind_is_rejected():
    with pytest.raises(InvalidPromptSet, match="field 'kind'"):
        parse_prompt({"id": "a", "kind": "huge", "text": "hi"})


def test_a_label_prompt_needs_an_allowed_expected_label():
    with pytest.raises(InvalidPromptSet, match="expected_label"):
        parse_prompt({"id": "a", "kind": "label", "text": "hi", "expected_label": "spam"})
```

- A `with` block: it sets up `pytest.raises(InvalidPromptSet, match=f"field '{field}'")`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Calls `parse_prompt` from the project's `token_meter.domain.prompts` (Build a record from one decoded JSON Lines row, naming the field that is wrong.) with 1 argument(s); the result is not kept.
  - `parse_prompt` from the project's `token_meter.domain.prompts` (Build a record from one decoded JSON Lines row, naming the field that is wrong.).
- Defines the function `test_an_unknown_kind_is_rejected`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(InvalidPromptSet, match="field 'kind'")`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `parse_prompt` from the project's `token_meter.domain.prompts` (Build a record from one decoded JSON Lines row, naming the field that is wrong.) with 1 argument(s); the result is not kept.
  - `parse_prompt` from the project's `token_meter.domain.prompts` (Build a record from one decoded JSON Lines row, naming the field that is wrong.).
- Defines the function `test_a_label_prompt_needs_an_allowed_expected_label`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(InvalidPromptSet, match='expected_label')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `parse_prompt` from the project's `token_meter.domain.prompts` (Build a record from one decoded JSON Lines row, naming the field that is wrong.) with 1 argument(s); the result is not kept.
  - `parse_prompt` from the project's `token_meter.domain.prompts` (Build a record from one decoded JSON Lines row, naming the field that is wrong.).

`tests/unit/domain/test_prompts.py`, lines 65 to 72:

```python
    assert (
        parse_prompt({"id": "a", "kind": "label", "text": "hi", "expected_label": "billing"}).expected_label
        == "billing"
    )


def test_only_label_prompts_keep_an_expected_label():
    assert parse_prompt({"id": "a", "kind": "short", "text": "hi", "expected_label": "billing"}).expected_label is None
```

- Checks that `parse_prompt({'id': 'a', 'kind': 'label', 'text': 'hi', 'expected_label': 'bi...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `parse_prompt` from the project's `token_meter.domain.prompts` (Build a record from one decoded JSON Lines row, naming the field that is wrong.).
- Defines the function `test_only_label_prompts_keep_an_expected_label`.
- It takes no parameters.
- Checks that `parse_prompt({'id': 'a', 'kind': 'short', 'text': 'hi', 'expected_label': 'bi...` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - `parse_prompt` from the project's `token_meter.domain.prompts` (Build a record from one decoded JSON Lines row, naming the field that is wrong.).

### `tests/unit/infrastructure/test_anthropic_chat.py`

124 non-blank lines; it defines `message`, `adapter`, `test_text_usage_stop_reason_and_model_come_from_the_response`, `test_sampling_is_refused_because_the_messages_api_rejects_it`, `test_thinking_can_be_left_out_or_set_to_between_tools`, `test_a_schema_goes_into_output_config_format_not_a_forced_tool`, `test_tool_calls_and_tool_results_map_to_tool_use_and_tool_result_blocks`, `test_tool_use_blocks_in_the_response_become_tool_calls`, `test_other_stop_reasons_are_mapped`, `test_rate_limits_and_server_errors_are_transient`, `test_a_bad_request_is_permanent`, `test_a_dropped_connection_is_transient`, ....

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 1 to 13:

```python
import json

import anthropic
import httpx2
import pytest

from tests.conftest import FixedClock
from token_meter.domain.errors import PermanentModelError, TransientModelError, UnsupportedParameter
from token_meter.domain.llm import ChatMessage, ChatRequest, Role, StopReason, ToolCall, ToolSpec
from token_meter.infrastructure.anthropic_chat import AnthropicChatModel


def message(content, stop="end_turn", tokens_in=21, tokens_out=6):
```

- Makes the module `json` (standard library) available.
- Makes the module `anthropic` (installed package) available.
- Makes the module `httpx2` (installed package) available.
- Makes the module `pytest` (installed package) available.
- Brings in `FixedClock` (A clock that only moves when a test says so.) from the project module `tests.conftest`.
- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.), `UnsupportedParameter` (The adapter cannot honor a parameter the request asked for (for example sampling on Claude).) from the project module `token_meter.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `Role` (Who wrote a message.), `StopReason` (Why the model stopped writing.), `ToolCall` (A tool call the model asked for.), `ToolSpec` (A tool the model may call: a name, a description and a JSON Schema for the arguments.) from the project module `token_meter.domain.llm`.
- Brings in `AnthropicChatModel` (Calls Claude. Build the SDK client with your key from the environment; this class never reads it.) from the project module `token_meter.infrastructure.anthropic_chat`.
- Defines the function `message`.
- Its parameters:
    - `content`.
    - `stop`; if the caller leaves it out it is the text `end_turn`.
    - `tokens_in`; if the caller leaves it out it is the number `21`.
    - `tokens_out`; if the caller leaves it out it is the number `6`.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 14 to 26:

```python
    return httpx2.Response(
        200,
        json={
            "id": "msg_1",
            "type": "message",
            "role": "assistant",
            "model": "claude-haiku-5-5",
            "content": content,
            "stop_reason": stop,
            "stop_sequence": None,
            "usage": {"input_tokens": tokens_in, "output_tokens": tokens_out},
        },
    )
```

- Ends the function and gives back the result of calling `httpx2.Response` to the caller.
  - `httpx2.Response` from the installed package module `httpx2`.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 29 to 39:

```python
def adapter(handler, thinking="disabled"):
    client = anthropic.Anthropic(
        api_key="test-key-not-real",
        max_retries=0,
        http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler)),
    )
    return AnthropicChatModel(client, "claude-haiku-5-5", FixedClock(), thinking)


def test_text_usage_stop_reason_and_model_come_from_the_response():
    seen = {}
```

- Defines the function `adapter`.
- Its parameters:
    - `handler`.
    - `thinking`; if the caller leaves it out it is the text `disabled`.
- Stores the result of calling `anthropic.Anthropic` under the name `client`.
  - `anthropic.Anthropic` from the installed package module `anthropic`.
  - `anthropic.DefaultHttpxClient` from the installed package module `anthropic`.
  - `httpx2.MockTransport` from the installed package module `httpx2`.
- Ends the function and gives back the result of calling `AnthropicChatModel` to the caller.
  - `AnthropicChatModel` from the project's `token_meter.infrastructure.anthropic_chat` (Calls Claude. Build the SDK client with your key from the environment; this class never reads it.).
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so.).
- Defines the function `test_text_usage_stop_reason_and_model_come_from_the_response`.
- It takes no parameters.
- Stores an empty dictionary under the name `seen`.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 41 to 53:

```python
    def handler(request):
        seen["body"] = json.loads(request.content)
        return message([{"type": "text", "text": "hello"}])

    response = adapter(handler).complete(
        ChatRequest((ChatMessage.user("hi"),), system="be brief", max_output_tokens=40)
    )
    assert (response.text, response.usage.input_tokens, response.usage.output_tokens) == ("hello", 21, 6)
    assert response.stop_reason is StopReason.END
    assert response.model == "claude-haiku-5-5"
    assert seen["body"]["system"] == "be brief"
    assert seen["body"]["max_tokens"] == 40
    assert seen["body"]["thinking"] == {"type": "disabled"}
```

- Defines the function `handler`.
- Its parameters:
    - `request`.
- Stores the result of calling `json.loads` under the name `seen['body']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `json.loads` turns JSON text into Python data.
- Ends the function and gives back the result of calling `message` to the caller.
  - `message`, a function of this file.
- Stores the result of calling `adapter(handler).complete` under the name `response`.
  - The method `complete` of `adapter(handler)`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - The method `user` of `ChatMessage`.
- Checks that `(response.text, response.usage.input_tokens, response.usage.output_tokens) ==...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `response.stop_reason is StopReason.END` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `response.model == 'claude-haiku-5-5'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `seen['body']['system'] == 'be brief'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `seen['body']['max_tokens'] == 40` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `seen['body']['thinking'] == {'type': 'disabled'}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 54 to 67:

```python
    assert "temperature" not in seen["body"]
    assert "top_p" not in seen["body"]


def test_sampling_is_refused_because_the_messages_api_rejects_it():
    model = adapter(lambda r: message([]))
    assert not model.supports_sampling
    with pytest.raises(UnsupportedParameter, match="temperature"):
        model.complete(ChatRequest((ChatMessage.user("hi"),), temperature=0.0))
    with pytest.raises(UnsupportedParameter):
        model.complete(ChatRequest((ChatMessage.user("hi"),), top_p=0.9))


def test_thinking_can_be_left_out_or_set_to_between_tools():
```

- Checks that `'temperature' not in seen['body']` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `'top_p' not in seen['body']` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_sampling_is_refused_because_the_messages_api_rejects_it`.
- It takes no parameters.
- Stores the result of calling `adapter` under the name `model`.
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - `message`, a function of this file.
- Checks that `not model.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
- A `with` block: it sets up `pytest.raises(UnsupportedParameter, match='temperature')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model` with 1 argument(s); the result is not kept.
  - The method `complete` of `model`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
- A `with` block: it sets up `pytest.raises(UnsupportedParameter)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model` with 1 argument(s); the result is not kept.
  - The method `complete` of `model`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
- Defines the function `test_thinking_can_be_left_out_or_set_to_between_tools`.
- It takes no parameters.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 68 to 79:

```python
    assert "thinking" not in adapter(lambda r: message([]), "omit").build_payload(ChatRequest((ChatMessage.user("x"),)))
    payload = adapter(lambda r: message([]), "between_tools").build_payload(ChatRequest((ChatMessage.user("x"),)))
    assert payload["thinking"] == {"type": "between_tools"}


def test_a_schema_goes_into_output_config_format_not_a_forced_tool():
    schema = {"type": "object", "properties": {"a": {"type": "string"}}}
    payload = adapter(lambda r: message([])).build_payload(
        ChatRequest((ChatMessage.user("x"),), response_schema=schema)
    )
    assert payload["output_config"] == {"format": {"type": "json_schema", "schema": schema}}
    assert "tool_choice" not in payload
```

- Checks that `'thinking' not in adapter(lambda r: message([]), 'omit').build_payload(ChatRe...` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - The method `build_payload` of `adapter(lambda r: message([]), 'omit')`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `message`, a function of this file.
- Stores the result of calling `adapter(lambda r: message([]), 'between_tools')...` under the name `payload`.
  - The method `build_payload` of `adapter(lambda r: message([]), 'betwe...`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `message`, a function of this file.
- Checks that `payload['thinking'] == {'type': 'between_tools'}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_a_schema_goes_into_output_config_format_not_a_forced_tool`.
- It takes no parameters.
- Stores a dictionary with 2 entries under the name `schema`.
- Stores the result of calling `adapter(lambda r: message([])).build_payload` under the name `payload`.
  - The method `build_payload` of `adapter(lambda r: message([]))`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `message`, a function of this file.
- Checks that `payload['output_config'] == {'format': {'type': 'json_schema', 'schema': sche...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `'tool_choice' not in payload` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 82 to 93:

```python
def test_tool_calls_and_tool_results_map_to_tool_use_and_tool_result_blocks():
    history = (
        ChatMessage.user("book it"),
        ChatMessage(
            Role.ASSISTANT, "checking", (ToolCall("t1", "slots", {"day": "mon"}), ToolCall("t2", "get", {"id": 1}))
        ),
        ChatMessage(Role.TOOL, "free", tool_call_id="t1"),
        ChatMessage(Role.TOOL, "event", tool_call_id="t2"),
    )
    spec = ToolSpec("slots", "find slots", {"type": "object"})
    payload = adapter(lambda r: message([])).build_payload(ChatRequest(history, tools=(spec,)))
    assert payload["tools"] == [{"name": "slots", "description": "find slots", "input_schema": {"type": "object"}}]
```

- Defines the function `test_tool_calls_and_tool_results_map_to_tool_use_and_tool_result_blocks`.
- It takes no parameters.
- Stores a tuple of 4 item(s) under the name `history`.
  - The method `user` of `ChatMessage`.
  - `ChatMessage` from the project's `token_meter.domain.llm` (One message of a conversation. A tool result carries the id of the call it answers.).
  - `ToolCall` from the project's `token_meter.domain.llm` (A tool call the model asked for.).
- Stores the result of calling `ToolSpec` under the name `spec`.
  - `ToolSpec` from the project's `token_meter.domain.llm` (A tool the model may call: a name, a description and a JSON Schema for the arguments.).
- Stores the result of calling `adapter(lambda r: message([])).build_payload` under the name `payload`.
  - The method `build_payload` of `adapter(lambda r: message([]))`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - `message`, a function of this file.
- Checks that `payload['tools'] == [{'name': 'slots', 'description': 'find slots', 'input_sc...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 94 to 107:

```python
    assistant = payload["messages"][1]["content"]
    assert [b["type"] for b in assistant] == ["text", "tool_use", "tool_use"]
    results = payload["messages"][2]
    assert results["role"] == "user"
    assert [b["tool_use_id"] for b in results["content"]] == ["t1", "t2"]
    assert len(payload["messages"]) == 3


def test_tool_use_blocks_in_the_response_become_tool_calls():
    content = [
        {"type": "text", "text": "ok"},
        {"type": "tool_use", "id": "tu1", "name": "slots", "input": {"day": "tue"}},
    ]
    response = adapter(lambda r: message(content, "tool_use")).complete(ChatRequest((ChatMessage.user("x"),)))
```

- Stores the part of `payload['messages'][1]` picked by `'content'` under the name `assistant`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `[b['type'] for b in assistant] == ['text', 'tool_use', 'tool_use']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the part of `payload['messages']` picked by `2` under the name `results`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `results['role'] == 'user'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `[b['tool_use_id'] for b in results['content']] == ['t1', 't2']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `len(payload['messages']) == 3` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_tool_use_blocks_in_the_response_become_tool_calls`.
- It takes no parameters.
- Stores a list of 2 item(s) under the name `content`.
- Stores the result of calling `adapter(lambda r: message(content, 'tool_use'))...` under the name `response`.
  - The method `complete` of `adapter(lambda r: message(content, 't...`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `message`, a function of this file.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 108 to 120:

```python
    assert response.stop_reason is StopReason.TOOL_CALLS
    assert response.tool_calls == (ToolCall("tu1", "slots", {"day": "tue"}),)


@pytest.mark.parametrize(
    ("stop", "expected"),
    [("max_tokens", StopReason.LENGTH), ("refusal", StopReason.REFUSAL), ("pause_turn", StopReason.OTHER)],
)
def test_other_stop_reasons_are_mapped(stop, expected):
    response = adapter(lambda r: message([{"type": "text", "text": "x"}], stop)).complete(
        ChatRequest((ChatMessage.user("x"),))
    )
    assert response.stop_reason is expected
```

- Checks that `response.stop_reason is StopReason.TOOL_CALLS` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `response.tool_calls == (ToolCall('tu1', 'slots', {'day': 'tue'}),)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `ToolCall` from the project's `token_meter.domain.llm` (A tool call the model asked for.).
- Defines the function `test_other_stop_reasons_are_mapped`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `stop`.
    - `expected`.
- Stores the result of calling `adapter(lambda r: message([{'type': 'text', 'te...` under the name `response`.
  - The method `complete` of `adapter(lambda r: message([{'type': '...`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `message`, a function of this file.
- Checks that `response.stop_reason is expected` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 123 to 134:

```python
@pytest.mark.parametrize("status", [429, 500, 529])
def test_rate_limits_and_server_errors_are_transient(status):
    with pytest.raises(TransientModelError):
        adapter(
            lambda r: httpx2.Response(status, json={"type": "error", "error": {"type": "x", "message": "y"}})
        ).complete(ChatRequest((ChatMessage.user("x"),)))


def test_a_bad_request_is_permanent():
    body = {"type": "error", "error": {"type": "invalid_request_error", "message": "nope"}}
    with pytest.raises(PermanentModelError, match="HTTP 400"):
        adapter(lambda r: httpx2.Response(400, json=body)).complete(ChatRequest((ChatMessage.user("x"),)))
```

- Defines the function `test_rate_limits_and_server_errors_are_transient`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `status`.
- A `with` block: it sets up `pytest.raises(TransientModelError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `adapter(lambda r: httpx2.Response(sta...` with 1 argument(s); the result is not kept.
  - The method `complete` of `adapter(lambda r: httpx2.Response(sta...`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `httpx2.Response` from the installed package module `httpx2`.
- Defines the function `test_a_bad_request_is_permanent`.
- It takes no parameters.
- Stores a dictionary with 2 entries under the name `body`.
- A `with` block: it sets up `pytest.raises(PermanentModelError, match='HTTP 400')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `adapter(lambda r: httpx2.Response(400...` with 1 argument(s); the result is not kept.
  - The method `complete` of `adapter(lambda r: httpx2.Response(400...`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `httpx2.Response` from the installed package module `httpx2`.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 137 to 148:

```python
def test_a_dropped_connection_is_transient():
    def handler(request):
        raise httpx2.ConnectError("refused", request=request)

    with pytest.raises(TransientModelError):
        adapter(handler).complete(ChatRequest((ChatMessage.user("x"),)))


def test_count_tokens_asks_the_provider_without_generating():
    seen = {}

    def handler(request):
```

- Defines the function `test_a_dropped_connection_is_transient`.
- It takes no parameters.
- Defines the function `handler`.
- Its parameters:
    - `request`.
- Raises an error: the result of calling `httpx2.ConnectError`. Execution jumps out to the nearest matching `except`.
  - `httpx2.ConnectError` from the installed package module `httpx2`.
- A `with` block: it sets up `pytest.raises(TransientModelError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `adapter(handler)` with 1 argument(s); the result is not kept.
  - The method `complete` of `adapter(handler)`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - The method `user` of `ChatMessage`.
- Defines the function `test_count_tokens_asks_the_provider_without_generating`.
- It takes no parameters.
- Stores an empty dictionary under the name `seen`.
- Defines the function `handler`.
- Its parameters:
    - `request`.

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 149 to 157:

```python
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx2.Response(200, json={"input_tokens": 17})

    count = adapter(handler).count_tokens(ChatRequest((ChatMessage.user("hi"),), system="s"))
    assert count == 17
    assert seen["path"].endswith("/messages/count_tokens")
    assert "max_tokens" not in seen["body"]
    assert "thinking" not in seen["body"]
```

- Stores the `path` of `request.url` under the name `seen['path']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `json.loads` under the name `seen['body']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `json.loads` turns JSON text into Python data.
- Ends the function and gives back the result of calling `httpx2.Response` to the caller.
  - `httpx2.Response` from the installed package module `httpx2`.
- Stores the result of calling `adapter(handler).count_tokens` under the name `count`.
  - The method `count_tokens` of the project's `AnthropicChatModel` (Ask the provider how many input tokens a request would use (no generation, no charge).).
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `adapter`, a function of this file.
  - The method `user` of `ChatMessage`.
- Checks that `count == 17` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `seen['path'].endswith('/messages/count_tokens')` is true; if it is not, the test fails with an `AssertionError`.
  - `.endswith(...)` asks whether text ends with the given text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `'max_tokens' not in seen['body']` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `'thinking' not in seen['body']` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

### `tests/unit/infrastructure/test_csv_journal.py`

33 non-blank lines; it defines `test_a_new_journal_gets_one_header_and_no_rows`, `test_rows_survive_a_reopen_and_the_header_is_not_written_twice`, `test_a_torn_last_line_from_a_kill_is_cut_off_on_open`, `test_a_file_without_the_header_is_reported_not_misread`.

`tests/unit/infrastructure/test_csv_journal.py`, lines 1 to 14:

```python
import pytest

from tests.conftest import row
from token_meter.domain.llm import StopReason
from token_meter.infrastructure.csv_journal import COLUMNS, CsvJournal, JournalCorrupt


def test_a_new_journal_gets_one_header_and_no_rows(tmp_path):
    journal = CsvJournal(tmp_path / "out" / "j.csv")
    assert journal.rows() == []
    assert (tmp_path / "out" / "j.csv").read_text().strip() == ",".join(COLUMNS)


def test_rows_survive_a_reopen_and_the_header_is_not_written_twice(tmp_path):
```

- Makes the module `pytest` (installed package) available.
- Brings in `row` from the project module `tests.conftest`.
- Brings in `StopReason` (Why the model stopped writing.) from the project module `token_meter.domain.llm`.
- Brings in `COLUMNS`, `CsvJournal` (Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open.), `JournalCorrupt` (The journal file does not start with the expected header; delete it or restore it from a copy.) from the project module `token_meter.infrastructure.csv_journal`.
- Defines the function `test_a_new_journal_gets_one_header_and_no_rows`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `CsvJournal` under the name `journal`.
  - `CsvJournal` from the project's `token_meter.infrastructure.csv_journal` (Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open.).
  - `/` is divide.
- Checks that `journal.rows() == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `rows` of `journal`.
- Checks that `(tmp_path / 'out' / 'j.csv').read_text().strip() == ','.join(COLUMNS)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - `/` is divide.
- Defines the function `test_rows_survive_a_reopen_and_the_header_is_not_written_twice`.
- Its parameters:
    - `tmp_path`.

`tests/unit/infrastructure/test_csv_journal.py`, lines 15 to 28:

```python
    path = tmp_path / "j.csv"
    journal = CsvJournal(path)
    journal.append(row("a", "t0", 0, 30, 5, 'hello, "world"\nsecond line'))
    journal.append(row("a", "t0", 1, 30, 6, "ça va", StopReason.LENGTH))
    reopened = CsvJournal(path)
    assert [r.text for r in reopened.rows()] == ['hello, "world"\nsecond line', "ça va"]
    assert reopened.rows()[1].stop_reason is StopReason.LENGTH
    assert path.read_text().count("prompt_id,setting") == 1
    assert {k.repeat for k in reopened.done_keys()} == {0, 1}


def test_a_torn_last_line_from_a_kill_is_cut_off_on_open(tmp_path):
    path = tmp_path / "j.csv"
    journal = CsvJournal(path)
```

- Stores the result of `tmp_path / 'j.csv'` under the name `path`.
  - `/` is divide.
- Stores the result of calling `CsvJournal` under the name `journal`.
  - `CsvJournal` from the project's `token_meter.infrastructure.csv_journal` (Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open.).
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `row` from the project's `tests.conftest`.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `row` from the project's `tests.conftest`.
- Stores the result of calling `CsvJournal` under the name `reopened`.
  - `CsvJournal` from the project's `token_meter.infrastructure.csv_journal` (Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open.).
- Checks that `[r.text for r in reopened.rows()] == ['hello, "world"\nsecond line', 'ça va']` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `rows` of `reopened`.
- Checks that `reopened.rows()[1].stop_reason is StopReason.LENGTH` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `rows` of `reopened`.
- Checks that `path.read_text().count('prompt_id,setting') == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `.count(...)` counts how often an item appears.
  - `.read_text(...)` reads a whole file as text.
- Checks that `{k.repeat for k in reopened.done_keys()} == {0, 1}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `done_keys` of `reopened`.
- Defines the function `test_a_torn_last_line_from_a_kill_is_cut_off_on_open`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'j.csv'` under the name `path`.
  - `/` is divide.
- Stores the result of calling `CsvJournal` under the name `journal`.
  - `CsvJournal` from the project's `token_meter.infrastructure.csv_journal` (Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open.).

`tests/unit/infrastructure/test_csv_journal.py`, lines 29 to 42:

```python
    journal.append(row("a", "t0", 0, 30, 5))
    with path.open("a") as handle:
        handle.write("a,t0,1,30,")  # the process died in the middle of this row
    reopened = CsvJournal(path)
    assert len(reopened.rows()) == 1
    reopened.append(row("a", "t0", 1, 30, 5))
    assert len(CsvJournal(path).rows()) == 2


def test_a_file_without_the_header_is_reported_not_misread(tmp_path):
    path = tmp_path / "j.csv"
    path.write_text('a,t0,0,1,1,stop,0.1,"x"\n')
    with pytest.raises(JournalCorrupt, match="expected the header"):
        CsvJournal(path)
```

- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `row` from the project's `tests.conftest`.
- A `with` block: it sets up `path.open('a')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `path`.
- Calls `.write(...)` writes text or bytes to an open file with 1 argument(s); the result is not kept.
  - `.write(...)` writes text or bytes to an open file.
- Stores the result of calling `CsvJournal` under the name `reopened`.
  - `CsvJournal` from the project's `token_meter.infrastructure.csv_journal` (Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open.).
- Checks that `len(reopened.rows()) == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - The method `rows` of `reopened`.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `row` from the project's `tests.conftest`.
- Checks that `len(CsvJournal(path).rows()) == 2` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
  - The method `rows` of `CsvJournal(path)`.
  - `CsvJournal` from the project's `token_meter.infrastructure.csv_journal` (Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open.).
- Defines the function `test_a_file_without_the_header_is_reported_not_misread`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'j.csv'` under the name `path`.
  - `/` is divide.
- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
- A `with` block: it sets up `pytest.raises(JournalCorrupt, match='expected the header')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `CsvJournal` from the project's `token_meter.infrastructure.csv_journal` (Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open.) with 1 argument(s); the result is not kept.
  - `CsvJournal` from the project's `token_meter.infrastructure.csv_journal` (Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open.).

### `tests/unit/infrastructure/test_files_and_settings.py`

69 non-blank lines; it defines `test_prompts_are_read_one_per_line`, `test_one_bad_line_fails_with_its_line_number_and_not_the_whole_file`, `test_prices_carry_a_real_date_field`, `test_a_price_file_without_a_date_is_rejected`, `test_settings_default_to_the_lesson_values`, `test_settings_read_the_environment`, `test_bad_settings_name_the_variable`, `test_the_env_helpers_validate_numbers`.

`tests/unit/infrastructure/test_files_and_settings.py`, lines 1 to 14:

```python
from datetime import date
from decimal import Decimal

import pytest

from token_meter.domain.prompts import InvalidPromptSet, Kind
from token_meter.infrastructure import env
from token_meter.infrastructure.env import ConfigurationError
from token_meter.infrastructure.files import load_prices, load_prompts
from token_meter.infrastructure.settings import MeterSettings


def test_prompts_are_read_one_per_line(tmp_path):
    path = tmp_path / "p.jsonl"
```

- Brings in `date` from the standard library module `datetime`.
- Brings in `Decimal` from the standard library module `decimal`.
- Makes the module `pytest` (installed package) available.
- Brings in `InvalidPromptSet` (The prompt file breaks a rule of the lesson (row count, kinds, a long prompt, unique ids).), `Kind` (What a prompt is for; the report breaks every number out by kind.) from the project module `token_meter.domain.prompts`.
- Brings in `env` from the project module `token_meter.infrastructure`.
- Brings in `ConfigurationError` (An environment variable is missing or has an unusable value.) from the project module `token_meter.infrastructure.env`.
- Brings in `load_prices` (Read the price file. `read_date` is a real field so a script can refuse stale prices.), `load_prompts` (Read one prompt per line. A bad line is reported with its line number; the rest of the file is not lost.) from the project module `token_meter.infrastructure.files`.
- Brings in `MeterSettings` (Everything the programs read from the environment. See .env.example for each variable.) from the project module `token_meter.infrastructure.settings`.
- Defines the function `test_prompts_are_read_one_per_line`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'p.jsonl'` under the name `path`.
  - `/` is divide.

`tests/unit/infrastructure/test_files_and_settings.py`, lines 15 to 26:

```python
    path.write_text('{"id":"a","kind":"short","text":"hi"}\n\n{"id":"b","kind":"long","text":"yo"}\n')
    assert [(p.id, p.kind) for p in load_prompts(path)] == [("a", Kind.SHORT), ("b", Kind.LONG)]


def test_one_bad_line_fails_with_its_line_number_and_not_the_whole_file(tmp_path):
    path = tmp_path / "p.jsonl"
    path.write_text('{"id":"a","kind":"short","text":"hi"}\n{"id":"b","kind":"long",}\n')
    with pytest.raises(InvalidPromptSet, match=r"p\.jsonl:2: not valid JSON"):
        load_prompts(path)
    path.write_text('{"id":"a","kind":"short","text":"hi"}\n{"id":"b","kind":"nope","text":"x"}\n')
    with pytest.raises(InvalidPromptSet, match=r"p\.jsonl:2: field 'kind'"):
        load_prompts(path)
```

- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
- Checks that `[(p.id, p.kind) for p in load_prompts(path)] == [('a', Kind.SHORT), ('b', Kin...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `load_prompts` from the project's `token_meter.infrastructure.files` (Read one prompt per line. A bad line is reported with its line number; the rest of the file is not lost.).
- Defines the function `test_one_bad_line_fails_with_its_line_number_and_not_the_whole_file`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'p.jsonl'` under the name `path`.
  - `/` is divide.
- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
- A `with` block: it sets up `pytest.raises(InvalidPromptSet, match='p\\.jsonl:2: not v...`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `load_prompts` from the project's `token_meter.infrastructure.files` (Read one prompt per line. A bad line is reported with its line number; the rest of the file is not lost.) with 1 argument(s); the result is not kept.
  - `load_prompts` from the project's `token_meter.infrastructure.files` (Read one prompt per line. A bad line is reported with its line number; the rest of the file is not lost.).
- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
- A `with` block: it sets up `pytest.raises(InvalidPromptSet, match="p\\.jsonl:2: field...`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `load_prompts` from the project's `token_meter.infrastructure.files` (Read one prompt per line. A bad line is reported with its line number; the rest of the file is not lost.) with 1 argument(s); the result is not kept.
  - `load_prompts` from the project's `token_meter.infrastructure.files` (Read one prompt per line. A bad line is reported with its line number; the rest of the file is not lost.).

`tests/unit/infrastructure/test_files_and_settings.py`, lines 29 to 40:

```python
def test_prices_carry_a_real_date_field(tmp_path):
    path = tmp_path / "prices.json"
    path.write_text('{"model":"m","input_per_1k":"0.0001","output_per_1k":"0.0005","read_date":"2026-10-26"}')
    prices = load_prices(path)
    assert prices.read_date == date(2026, 10, 26)
    assert prices.input_per_1k == Decimal("0.0001")


def test_a_price_file_without_a_date_is_rejected(tmp_path):
    path = tmp_path / "prices.json"
    path.write_text('{"model":"m","input_per_1k":"0.0001","output_per_1k":"0.0005"}')
    with pytest.raises(ValueError, match="read_date"):
```

- Defines the function `test_prices_carry_a_real_date_field`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'prices.json'` under the name `path`.
  - `/` is divide.
- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
- Stores the result of calling `load_prices` under the name `prices`.
  - `load_prices` from the project's `token_meter.infrastructure.files` (Read the price file. `read_date` is a real field so a script can refuse stale prices.).
- Checks that `prices.read_date == date(2026, 10, 26)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `date` from the standard library module `datetime`.
- Checks that `prices.input_per_1k == Decimal('0.0001')` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `Decimal` from the standard library module `decimal`.
- Defines the function `test_a_price_file_without_a_date_is_rejected`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'prices.json'` under the name `path`.
  - `/` is divide.
- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
- A `with` block: it sets up `pytest.raises(ValueError, match='read_date')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.

`tests/unit/infrastructure/test_files_and_settings.py`, lines 41 to 54:

```python
        load_prices(path)


def test_settings_default_to_the_lesson_values():
    settings = MeterSettings.from_env({})
    assert (settings.max_output_tokens, settings.repeats, settings.price_max_age_days) == (200, 3, 30)
    assert settings.budget is None
    assert settings.throttle_seconds == 0.0


def test_settings_read_the_environment():
    settings = MeterSettings.from_env(
        {"BUDGET_USD": "0.25", "REPEATS": "2", "THROTTLE_SECONDS": "0.5", "LOG_LEVEL": "debug"}
    )
```

- Calls `load_prices` from the project's `token_meter.infrastructure.files` (Read the price file. `read_date` is a real field so a script can refuse stale prices.) with 1 argument(s); the result is not kept.
  - `load_prices` from the project's `token_meter.infrastructure.files` (Read the price file. `read_date` is a real field so a script can refuse stale prices.).
- Defines the function `test_settings_default_to_the_lesson_values`.
- It takes no parameters.
- Stores the result of calling `MeterSettings.from_env` under the name `settings`.
  - The method `from_env` of `MeterSettings`.
- Checks that `(settings.max_output_tokens, settings.repeats, settings.price_max_age_days) =...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `settings.budget is None` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `settings.throttle_seconds == 0.0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_settings_read_the_environment`.
- It takes no parameters.
- Stores the result of calling `MeterSettings.from_env` under the name `settings`.
  - The method `from_env` of `MeterSettings`.

`tests/unit/infrastructure/test_files_and_settings.py`, lines 55 to 57:

```python
    assert settings.budget == Decimal("0.25")
    assert settings.repeats == 2
    assert settings.throttle_seconds == 0.5
```

- Checks that `settings.budget == Decimal('0.25')` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `Decimal` from the standard library module `decimal`.
- Checks that `settings.repeats == 2` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `settings.throttle_seconds == 0.5` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/unit/infrastructure/test_files_and_settings.py`, lines 60 to 71:

```python
@pytest.mark.parametrize(
    ("environ", "fragment"),
    [
        ({"BUDGET_USD": "cheap"}, "BUDGET_USD"),
        ({"REPEATS": "0"}, "REPEATS"),
        ({"MAX_OUTPUT_TOKENS": "many"}, "MAX_OUTPUT_TOKENS"),
        ({"THROTTLE_SECONDS": "-1"}, "THROTTLE_SECONDS"),
        ({"LOG_LEVEL": "LOUD"}, "LOG_LEVEL"),
        ({"PROMPTS_PATH": "  "}, "PROMPTS_PATH"),
    ],
)
def test_bad_settings_name_the_variable(environ, fragment):
```

- Defines the function `test_bad_settings_name_the_variable`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `environ`.
    - `fragment`.

`tests/unit/infrastructure/test_files_and_settings.py`, lines 72 to 85:

```python
    with pytest.raises(ConfigurationError, match=fragment):
        MeterSettings.from_env(environ)


def test_the_env_helpers_validate_numbers():
    assert env.non_negative_int({"A": "0"}, "A", 5) == 0
    assert env.positive_float({"A": "1.5"}, "A", 1) == 1.5
    with pytest.raises(ConfigurationError):
        env.non_negative_int({"A": "-1"}, "A", 5)
    with pytest.raises(ConfigurationError):
        env.positive_float({"A": "0"}, "A", 1)
    with pytest.raises(ConfigurationError):
        env.positive_float({"A": "x"}, "A", 1)
    with pytest.raises(ConfigurationError):
```

- A `with` block: it sets up `pytest.raises(ConfigurationError, match=fragment)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `from_env` of `MeterSettings` with 1 argument(s); the result is not kept.
  - The method `from_env` of `MeterSettings`.
- Defines the function `test_the_env_helpers_validate_numbers`.
- It takes no parameters.
- Checks that `env.non_negative_int({'A': '0'}, 'A', 5) == 0` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `non_negative_int` of `env`.
- Checks that `env.positive_float({'A': '1.5'}, 'A', 1) == 1.5` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `positive_float` of `env`.
- A `with` block: it sets up `pytest.raises(ConfigurationError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `non_negative_int` of `env` with 3 argument(s); the result is not kept.
  - The method `non_negative_int` of `env`.
- A `with` block: it sets up `pytest.raises(ConfigurationError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `positive_float` of `env` with 3 argument(s); the result is not kept.
  - The method `positive_float` of `env`.
- A `with` block: it sets up `pytest.raises(ConfigurationError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `positive_float` of `env` with 3 argument(s); the result is not kept.
  - The method `positive_float` of `env`.
- A `with` block: it sets up `pytest.raises(ConfigurationError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.

`tests/unit/infrastructure/test_files_and_settings.py`, lines 86 to 87:

```python
        env.non_negative_float({"A": "x"}, "A", 1)
    assert env.optional_text({"A": " "}, "A") is None
```

- Calls the method `non_negative_float` of `env` with 3 argument(s); the result is not kept.
  - The method `non_negative_float` of `env`.
- Checks that `env.optional_text({'A': ' '}, 'A') is None` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - The method `optional_text` of `env`.

### `tests/unit/infrastructure/test_openai_compatible.py`

102 non-blank lines; it defines `model`, `ok`, `test_a_reply_becomes_text_usage_stop_reason_and_latency`, `test_unset_sampling_is_left_out_of_the_body`, `test_a_schema_becomes_a_json_schema_response_format`, `test_tool_specs_calls_and_results_use_the_function_calling_shape`, `test_tool_calls_in_the_reply_are_parsed_with_json_arguments`, `test_arguments_may_already_be_an_object_and_missing_ids_are_numbered`, `test_a_length_finish_reason_is_kept`, `test_rate_limits_and_server_errors_are_transient`, `test_a_client_error_is_permanent`, `test_a_dropped_connection_is_transient`, ....

`tests/unit/infrastructure/test_openai_compatible.py`, lines 1 to 14:

```python
import json
from typing import Any

import httpx
import pytest

from tests.conftest import FixedClock
from token_meter.domain.errors import PermanentModelError, TransientModelError
from token_meter.domain.llm import ChatMessage, ChatRequest, Role, StopReason, ToolCall, ToolSpec
from token_meter.infrastructure.openai_compatible import OpenAICompatibleChatModel


def model(handler, api_key=None):
    http = httpx.Client(transport=httpx.MockTransport(handler))
```

- Makes the module `json` (standard library) available.
- Brings in `Any` from the standard library module `typing`.
- Makes the module `httpx` (installed package) available.
- Makes the module `pytest` (installed package) available.
- Brings in `FixedClock` (A clock that only moves when a test says so.) from the project module `tests.conftest`.
- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.) from the project module `token_meter.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `Role` (Who wrote a message.), `StopReason` (Why the model stopped writing.), `ToolCall` (A tool call the model asked for.), `ToolSpec` (A tool the model may call: a name, a description and a JSON Schema for the arguments.) from the project module `token_meter.domain.llm`.
- Brings in `OpenAICompatibleChatModel` (Talks to any server that implements `POST {base_url}/chat/completions`.) from the project module `token_meter.infrastructure.openai_compatible`.
- Defines the function `model`.
- Its parameters:
    - `handler`.
    - `api_key`; if the caller leaves it out it is nothing (`None`).
- Stores the result of calling `httpx.Client` under the name `http`.
  - `httpx.Client` makes an HTTP client.
  - `httpx.MockTransport` from the installed package module `httpx`.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 15 to 21:

```python
    return OpenAICompatibleChatModel(http, "http://local/v1/", "small-model", FixedClock(), api_key)


def ok(content="hello", finish="stop", tool_calls=None, prompt_tokens=11, completion_tokens=3):
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
```

- Ends the function and gives back the result of calling `OpenAICompatibleChatModel` to the caller.
  - `OpenAICompatibleChatModel` from the project's `token_meter.infrastructure.openai_compatible` (Talks to any server that implements `POST {base_url}/chat/completions`.).
  - `FixedClock` from the project's `tests.conftest` (A clock that only moves when a test says so.).
- Defines the function `ok`.
- Its parameters:
    - `content`; if the caller leaves it out it is the text `hello`.
    - `finish`; if the caller leaves it out it is the text `stop`.
    - `tool_calls`; if the caller leaves it out it is nothing (`None`).
    - `prompt_tokens`; if the caller leaves it out it is the number `11`.
    - `completion_tokens`; if the caller leaves it out it is the number `3`.
- Stores a dictionary with 2 entries under the name `message`.
- Decision: the indented lines below run only when `tool_calls` is true.
- Stores the value named `tool_calls` under the name `message['tool_calls']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 22 to 35:

```python
    return httpx.Response(
        200,
        json={
            "model": "small-model-0",
            "choices": [{"message": message, "finish_reason": finish}],
            "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
        },
    )


def test_a_reply_becomes_text_usage_stop_reason_and_latency():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
```

- Ends the function and gives back the result of calling `httpx.Response` to the caller.
  - `httpx.Response` from the installed package module `httpx`.
- Defines the function `test_a_reply_becomes_text_usage_stop_reason_and_latency`.
- It takes no parameters.
- Declares `seen` as a dictionary from text to any value and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `handler`. It returns `httpx.Response`.
- Its parameters:
    - `request` holds `httpx.Request`.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 36 to 49:

```python
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers.get("authorization")
        return ok()  # type: ignore[no-any-return]

    response = model(handler, api_key="k").complete(
        ChatRequest((ChatMessage.user("hi"),), system="be brief", max_output_tokens=50, temperature=0.7, top_p=0.9)
    )
    assert (response.text, response.usage.input_tokens, response.usage.output_tokens) == ("hello", 11, 3)
    assert response.stop_reason is StopReason.END
    assert response.latency_seconds == 0.25
    assert response.model == "small-model-0"
    assert seen["url"] == "http://local/v1/chat/completions"
    assert seen["auth"] == "Bearer k"
```

- Stores the result of calling `str` under the name `seen['url']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `str` turns a value into text.
- Stores the result of calling `json.loads` under the name `seen['body']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `json.loads` turns JSON text into Python data.
- Stores the result of calling `request.headers.get` under the name `seen['auth']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Ends the function and gives back the result of calling `ok` to the caller.
  - `ok`, a function of this file.
- Stores the result of calling `model(handler, api_key='k').complete` under the name `response`.
  - The method `complete` of `model(handler, api_key='k')`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - The method `user` of `ChatMessage`.
- Checks that `(response.text, response.usage.input_tokens, response.usage.output_tokens) ==...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `response.stop_reason is StopReason.END` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `response.latency_seconds == 0.25` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `response.model == 'small-model-0'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `seen['url'] == 'http://local/v1/chat/completions'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `seen['auth'] == 'Bearer k'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 50 to 63:

```python
    assert seen["body"]["messages"][0] == {"role": "system", "content": "be brief"}
    assert (seen["body"]["max_tokens"], seen["body"]["temperature"], seen["body"]["top_p"]) == (50, 0.7, 0.9)


def test_unset_sampling_is_left_out_of_the_body():
    body = model(lambda r: ok()).build_payload(ChatRequest((ChatMessage.user("hi"),)))
    assert "temperature" not in body
    assert "top_p" not in body
    assert body["model"] == "small-model"


def test_a_schema_becomes_a_json_schema_response_format():
    schema = {"type": "object", "properties": {"a": {"type": "string"}}}
    body = model(lambda r: ok()).build_payload(ChatRequest((ChatMessage.user("hi"),), response_schema=schema))
```

- Checks that `seen['body']['messages'][0] == {'role': 'system', 'content': 'be brief'}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `(seen['body']['max_tokens'], seen['body']['temperature'], seen['body']['top_p...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_unset_sampling_is_left_out_of_the_body`.
- It takes no parameters.
- Stores the result of calling `model(lambda r: ok()).build_payload` under the name `body`.
  - The method `build_payload` of `model(lambda r: ok())`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.
- Checks that `'temperature' not in body` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
- Checks that `'top_p' not in body` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
- Checks that `body['model'] == 'small-model'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_a_schema_becomes_a_json_schema_response_format`.
- It takes no parameters.
- Stores a dictionary with 2 entries under the name `schema`.
- Stores the result of calling `model(lambda r: ok()).build_payload` under the name `body`.
  - The method `build_payload` of `model(lambda r: ok())`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 64 to 77:

```python
    assert body["response_format"]["json_schema"]["schema"] == schema
    assert body["response_format"]["type"] == "json_schema"


def test_tool_specs_calls_and_results_use_the_function_calling_shape():
    spec = ToolSpec("lookup", "find one", {"type": "object"})
    history = (
        ChatMessage.user("find 4"),
        ChatMessage(Role.ASSISTANT, "", (ToolCall("c1", "lookup", {"id": 4}),)),
        ChatMessage(Role.TOOL, '{"ok": true}', tool_call_id="c1"),
    )
    body = model(lambda r: ok()).build_payload(ChatRequest(history, tools=(spec,)))
    assert body["tools"][0]["function"]["name"] == "lookup"
    assert body["messages"][1]["tool_calls"][0]["function"]["arguments"] == '{"id": 4}'
```

- Checks that `body['response_format']['json_schema']['schema'] == schema` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `body['response_format']['type'] == 'json_schema'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_tool_specs_calls_and_results_use_the_function_calling_shape`.
- It takes no parameters.
- Stores the result of calling `ToolSpec` under the name `spec`.
  - `ToolSpec` from the project's `token_meter.domain.llm` (A tool the model may call: a name, a description and a JSON Schema for the arguments.).
- Stores a tuple of 3 item(s) under the name `history`.
  - The method `user` of `ChatMessage`.
  - `ChatMessage` from the project's `token_meter.domain.llm` (One message of a conversation. A tool result carries the id of the call it answers.).
  - `ToolCall` from the project's `token_meter.domain.llm` (A tool call the model asked for.).
- Stores the result of calling `model(lambda r: ok()).build_payload` under the name `body`.
  - The method `build_payload` of `model(lambda r: ok())`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - `ok`, a function of this file.
- Checks that `body['tools'][0]['function']['name'] == 'lookup'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `body['messages'][1]['tool_calls'][0]['function']['arguments'] == '{"id": 4}'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 78 to 91:

```python
    assert body["messages"][2] == {"role": "tool", "tool_call_id": "c1", "content": '{"ok": true}'}


def test_tool_calls_in_the_reply_are_parsed_with_json_arguments():
    calls = [{"id": "c9", "function": {"name": "lookup", "arguments": '{"id": 7}'}}]
    response = model(lambda r: ok(content=None, finish="stop", tool_calls=calls)).complete(
        ChatRequest((ChatMessage.user("x"),))
    )
    assert response.stop_reason is StopReason.TOOL_CALLS
    assert response.tool_calls == (ToolCall("c9", "lookup", {"id": 7}),)
    assert response.text == ""


def test_arguments_may_already_be_an_object_and_missing_ids_are_numbered():
```

- Checks that `body['messages'][2] == {'role': 'tool', 'tool_call_id': 'c1', 'content': '{"o...` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_tool_calls_in_the_reply_are_parsed_with_json_arguments`.
- It takes no parameters.
- Stores a list of 1 item(s) under the name `calls`.
- Stores the result of calling `model(lambda r: ok(content=None, finish='stop',...` under the name `response`.
  - The method `complete` of `model(lambda r: ok(content=None, fini...`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.
- Checks that `response.stop_reason is StopReason.TOOL_CALLS` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
- Checks that `response.tool_calls == (ToolCall('c9', 'lookup', {'id': 7}),)` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `ToolCall` from the project's `token_meter.domain.llm` (A tool call the model asked for.).
- Checks that `response.text == ''` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_arguments_may_already_be_an_object_and_missing_ids_are_numbered`.
- It takes no parameters.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 92 to 102:

```python
    calls = [{"function": {"name": "lookup", "arguments": {"id": 1}}}]
    response = model(lambda r: ok(tool_calls=calls)).complete(ChatRequest((ChatMessage.user("x"),)))
    assert response.tool_calls[0].id == "call_0"
    assert response.tool_calls[0].arguments == {"id": 1}


def test_a_length_finish_reason_is_kept():
    assert (
        model(lambda r: ok(finish="length")).complete(ChatRequest((ChatMessage.user("x"),))).stop_reason
        is StopReason.LENGTH
    )
```

- Stores a list of 1 item(s) under the name `calls`.
- Stores the result of calling `model(lambda r: ok(tool_calls=calls)).complete` under the name `response`.
  - The method `complete` of `model(lambda r: ok(tool_calls=calls))`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.
- Checks that `response.tool_calls[0].id == 'call_0'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `response.tool_calls[0].arguments == {'id': 1}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_a_length_finish_reason_is_kept`.
- It takes no parameters.
- Checks that `model(lambda r: ok(finish='length')).complete(ChatRequest((ChatMessage.user('...` is true; if it is not, the test fails with an `AssertionError`.
  - `is` means the very same object.
  - The method `complete` of `model(lambda r: ok(finish='length'))`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 105 to 116:

```python
@pytest.mark.parametrize("status", [429, 500, 503])
def test_rate_limits_and_server_errors_are_transient(status):
    with pytest.raises(TransientModelError, match=str(status)):
        model(lambda r: httpx.Response(status)).complete(ChatRequest((ChatMessage.user("x"),)))


def test_a_client_error_is_permanent():
    with pytest.raises(PermanentModelError, match="HTTP 400"):
        model(lambda r: httpx.Response(400, text="bad")).complete(ChatRequest((ChatMessage.user("x"),)))


def test_a_dropped_connection_is_transient():
```

- Defines the function `test_rate_limits_and_server_errors_are_transient`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `status`.
- A `with` block: it sets up `pytest.raises(TransientModelError, match=str(status))`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
  - `str` turns a value into text.
- Calls the method `complete` of `model(lambda r: httpx.Response(status))` with 1 argument(s); the result is not kept.
  - The method `complete` of `model(lambda r: httpx.Response(status))`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `httpx.Response` from the installed package module `httpx`.
- Defines the function `test_a_client_error_is_permanent`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(PermanentModelError, match='HTTP 400')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model(lambda r: httpx.Response(400, t...` with 1 argument(s); the result is not kept.
  - The method `complete` of `model(lambda r: httpx.Response(400, t...`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `httpx.Response` from the installed package module `httpx`.
- Defines the function `test_a_dropped_connection_is_transient`.
- It takes no parameters.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 117 to 129:

```python
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(TransientModelError, match="ConnectError"):
        model(handler).complete(ChatRequest((ChatMessage.user("x"),)))


def test_an_unexpected_shape_is_permanent():
    with pytest.raises(PermanentModelError, match="unexpected response shape"):
        model(lambda r: httpx.Response(200, json={"choices": []})).complete(ChatRequest((ChatMessage.user("x"),)))
    bad_args = [{"id": "c", "function": {"name": "t", "arguments": "[1]"}}]
    with pytest.raises(PermanentModelError):
        model(lambda r: ok(tool_calls=bad_args)).complete(ChatRequest((ChatMessage.user("x"),)))
```

- Defines the function `handler`. It returns `httpx.Response`.
- Its parameters:
    - `request` holds `httpx.Request`.
- Raises an error: the result of calling `httpx.ConnectError`. Execution jumps out to the nearest matching `except`.
  - `httpx.ConnectError` from the installed package module `httpx`.
- A `with` block: it sets up `pytest.raises(TransientModelError, match='ConnectError')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model(handler)` with 1 argument(s); the result is not kept.
  - The method `complete` of `model(handler)`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - The method `user` of `ChatMessage`.
- Defines the function `test_an_unexpected_shape_is_permanent`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(PermanentModelError, match='unexpected resp...`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model(lambda r: httpx.Response(200, j...` with 1 argument(s); the result is not kept.
  - The method `complete` of `model(lambda r: httpx.Response(200, j...`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `httpx.Response` from the installed package module `httpx`.
- Stores a list of 1 item(s) under the name `bad_args`.
- A `with` block: it sets up `pytest.raises(PermanentModelError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `model(lambda r: ok(tool_calls=bad_args))` with 1 argument(s); the result is not kept.
  - The method `complete` of `model(lambda r: ok(tool_calls=bad_args))`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `user` of `ChatMessage`.
  - `ok`, a function of this file.

`tests/unit/infrastructure/test_openai_compatible.py`, lines 132 to 135:

```python
def test_the_model_reports_its_name_and_that_it_accepts_sampling():
    adapter = model(lambda r: ok())
    assert adapter.name == "small-model"
    assert adapter.supports_sampling
```

- Defines the function `test_the_model_reports_its_name_and_that_it_accepts_sampling`.
- It takes no parameters.
- Stores the result of calling `model` under the name `adapter`.
  - `model`, a function of this file.
  - `lambda args: expression` is a small unnamed function written inline.
  - `ok`, a function of this file.
- Checks that `adapter.name == 'small-model'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `adapter.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.

### `tests/unit/infrastructure/test_recording.py`

45 non-blank lines; it defines `request`, `test_recording_then_replaying_returns_the_same_response`, `test_a_request_already_recorded_is_not_sent_again`, `test_an_unrecorded_request_names_the_tag_and_the_fix`, `test_the_note_about_what_produced_the_answer_is_kept_in_the_file`, `test_a_folder_of_recordings_is_loaded_as_one_store`, `test_the_recorder_reports_the_wrapped_models_name_and_sampling_support`.

`tests/unit/infrastructure/test_recording.py`, lines 1 to 12:

```python
import json

import pytest

from tests.conftest import ScriptedModel
from token_meter.domain.errors import RecordingMissing
from token_meter.domain.llm import ChatMessage, ChatRequest
from token_meter.infrastructure.recording import RecordedChatModel, RecordingChatModel, RecordingStore


def request(text="hi", tag="a"):
    return ChatRequest((ChatMessage.user(text),), max_output_tokens=10, tag=tag)
```

- Makes the module `json` (standard library) available.
- Makes the module `pytest` (installed package) available.
- Brings in `ScriptedModel` (Answers every request from a function, and remembers the requests it saw.) from the project module `tests.conftest`.
- Brings in `RecordingMissing` (The recorded adapter has no response for this request. Re-record with `make record`.) from the project module `token_meter.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.) from the project module `token_meter.domain.llm`.
- Brings in `RecordedChatModel` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.), `RecordingChatModel` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.), `RecordingStore` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.) from the project module `token_meter.infrastructure.recording`.
- Defines the function `request`.
- Its parameters:
    - `text`; if the caller leaves it out it is the text `hi`.
    - `tag`; if the caller leaves it out it is the text `a`.
- Ends the function and gives back the result of calling `ChatRequest` to the caller.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.

`tests/unit/infrastructure/test_recording.py`, lines 15 to 26:

```python
def test_recording_then_replaying_returns_the_same_response(tmp_path):
    path = tmp_path / "r.jsonl"
    live = ScriptedModel(lambda r: ("live answer", 12, 4))
    recorder = RecordingChatModel(live, RecordingStore(path), {"provider": "test"})
    first = recorder.complete(request())
    replay = RecordedChatModel(RecordingStore(path))
    assert replay.complete(request()) == first
    assert len(live.requests) == 1


def test_a_request_already_recorded_is_not_sent_again(tmp_path):
    live = ScriptedModel()
```

- Defines the function `test_recording_then_replaying_returns_the_same_response`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'r.jsonl'` under the name `path`.
  - `/` is divide.
- Stores the result of calling `ScriptedModel` under the name `live`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `lambda args: expression` is a small unnamed function written inline.
- Stores the result of calling `RecordingChatModel` under the name `recorder`.
  - `RecordingChatModel` from the project's `token_meter.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `RecordingStore` from the project's `token_meter.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
- Stores the result of calling `recorder.complete` under the name `first`.
  - The method `complete` of `recorder`.
  - `request`, a function of this file.
- Stores the result of calling `RecordedChatModel` under the name `replay`.
  - `RecordedChatModel` from the project's `token_meter.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
  - `RecordingStore` from the project's `token_meter.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
- Checks that `replay.complete(request()) == first` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `complete` of `replay`.
  - `request`, a function of this file.
- Checks that `len(live.requests) == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Defines the function `test_a_request_already_recorded_is_not_sent_again`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `ScriptedModel` under the name `live`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).

`tests/unit/infrastructure/test_recording.py`, lines 27 to 38:

```python
    recorder = RecordingChatModel(live, RecordingStore(tmp_path / "r.jsonl"), {})
    recorder.complete(request())
    recorder.complete(request())
    assert len(live.requests) == 1


def test_an_unrecorded_request_names_the_tag_and_the_fix(tmp_path):
    replay = RecordedChatModel(RecordingStore(tmp_path / "missing.jsonl"))
    with pytest.raises(RecordingMissing, match=r"tag='zzz'.*make record"):
        replay.complete(request(tag="zzz"))
    assert replay.name == "recorded"
    assert replay.supports_sampling
```

- Stores the result of calling `RecordingChatModel` under the name `recorder`.
  - `RecordingChatModel` from the project's `token_meter.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `RecordingStore` from the project's `token_meter.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
  - `/` is divide.
- Calls the method `complete` of `recorder` with 1 argument(s); the result is not kept.
  - The method `complete` of `recorder`.
  - `request`, a function of this file.
- Calls the method `complete` of `recorder` with 1 argument(s); the result is not kept.
  - The method `complete` of `recorder`.
  - `request`, a function of this file.
- Checks that `len(live.requests) == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Defines the function `test_an_unrecorded_request_names_the_tag_and_the_fix`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `RecordedChatModel` under the name `replay`.
  - `RecordedChatModel` from the project's `token_meter.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
  - `RecordingStore` from the project's `token_meter.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
  - `/` is divide.
- A `with` block: it sets up `pytest.raises(RecordingMissing, match="tag='zzz'.*make re...`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `replay` with 1 argument(s); the result is not kept.
  - The method `complete` of `replay`.
  - `request`, a function of this file.
- Checks that `replay.name == 'recorded'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `replay.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.

`tests/unit/infrastructure/test_recording.py`, lines 41 to 52:

```python
def test_the_note_about_what_produced_the_answer_is_kept_in_the_file(tmp_path):
    path = tmp_path / "r.jsonl"
    RecordingChatModel(ScriptedModel(), RecordingStore(path), {"provider": "test"}).complete(request())
    entry = json.loads(path.read_text().splitlines()[0])
    assert entry["recorded_with"] == {"provider": "test", "model": "scripted"}
    assert entry["tag"] == "a"


def test_a_folder_of_recordings_is_loaded_as_one_store(tmp_path):
    for name, text in (("one.jsonl", "q1"), ("two.jsonl", "q2")):
        RecordingChatModel(ScriptedModel(), RecordingStore(tmp_path / name), {}).complete(request(text))
    store = RecordingStore(tmp_path)
```

- Defines the function `test_the_note_about_what_produced_the_answer_is_kept_in_the_file`.
- Its parameters:
    - `tmp_path`.
- Stores the result of `tmp_path / 'r.jsonl'` under the name `path`.
  - `/` is divide.
- Calls the method `complete` of `RecordingChatModel(ScriptedModel(), R...` with 1 argument(s); the result is not kept.
  - The method `complete` of `RecordingChatModel(ScriptedModel(), R...`.
  - `request`, a function of this file.
  - `RecordingChatModel` from the project's `token_meter.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `RecordingStore` from the project's `token_meter.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
- Stores the result of calling `json.loads` under the name `entry`.
  - `json.loads` turns JSON text into Python data.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.splitlines(...)` cuts text into a list of lines.
  - `.read_text(...)` reads a whole file as text.
- Checks that `entry['recorded_with'] == {'provider': 'test', 'model': 'scripted'}` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `entry['tag'] == 'a'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `test_a_folder_of_recordings_is_loaded_as_one_store`.
- Its parameters:
    - `tmp_path`.
- Loop: the indented lines below run once for each item of `(('one.jsonl', 'q1'), ('two.jsonl', 'q2'))`; `(name, text)` names the current item.
- Calls the method `complete` of `RecordingChatModel(ScriptedModel(), R...` with 1 argument(s); the result is not kept.
  - The method `complete` of `RecordingChatModel(ScriptedModel(), R...`.
  - `request`, a function of this file.
  - `RecordingChatModel` from the project's `token_meter.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `RecordingStore` from the project's `token_meter.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
  - `/` is divide.
- Stores the result of calling `RecordingStore` under the name `store`.
  - `RecordingStore` from the project's `token_meter.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).

`tests/unit/infrastructure/test_recording.py`, lines 53 to 61:

```python
    assert len(store) == 2
    RecordedChatModel(store).complete(request("q1"))
    RecordedChatModel(store).complete(request("q2"))


def test_the_recorder_reports_the_wrapped_models_name_and_sampling_support(tmp_path):
    recorder = RecordingChatModel(ScriptedModel(sampling=False), RecordingStore(tmp_path / "r.jsonl"), {})
    assert recorder.name == "scripted"
    assert not recorder.supports_sampling
```

- Checks that `len(store) == 2` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Calls the method `complete` of `RecordedChatModel(store)` with 1 argument(s); the result is not kept.
  - The method `complete` of `RecordedChatModel(store)`.
  - `request`, a function of this file.
  - `RecordedChatModel` from the project's `token_meter.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
- Calls the method `complete` of `RecordedChatModel(store)` with 1 argument(s); the result is not kept.
  - The method `complete` of `RecordedChatModel(store)`.
  - `request`, a function of this file.
  - `RecordedChatModel` from the project's `token_meter.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
- Defines the function `test_the_recorder_reports_the_wrapped_models_name_and_sampling_support`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `RecordingChatModel` under the name `recorder`.
  - `RecordingChatModel` from the project's `token_meter.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `RecordingStore` from the project's `token_meter.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
  - `/` is divide.
- Checks that `recorder.name == 'scripted'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `not recorder.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.

## Try it yourself

1. List the tests of this group without running them: the last line is the count.

```bash
.venv/bin/python -m pytest tests/unit --collect-only -q -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
tests/unit/interfaces/test_cli.py::test_a_shutdown_request_ends_the_run_with_the_interrupted_code

137 tests collected in N.NNs
```

2. Run this group. A green run prints the number of passed tests.

```bash
.venv/bin/python -m pytest tests/unit -q -x -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
........................................................................ [ 52%]
.................................................................        [100%]
137 passed in N.NNs
```

3. The first test names, written as sentences.

```bash
.venv/bin/python -m pytest tests/unit -q -p no:cacheprovider --co 2>&1 | sed -n 1,5p
```

What you should see (captured from this repository):

```text
tests/unit/application/test_report_and_metered_model.py::test_the_report_finds_the_overhead_and_shows_the_error_shrink
tests/unit/application/test_report_and_metered_model.py::test_the_metered_model_logs_estimate_and_bill_without_the_prompt_text
tests/unit/application/test_report_and_metered_model.py::test_a_zero_billed_input_does_not_divide_by_zero
tests/unit/application/test_run_meter.py::test_a_plan_covers_every_prompt_setting_and_repeat
tests/unit/application/test_run_meter.py::test_a_run_makes_every_call_and_journals_one_row_each
```

## Mistakes people make

- **Tests that depend on each other.** Each test builds its own data, so they pass in any order.
- **Real files, real network, real time.** Tests use `tmp_path`, recorded answers, mock transports and a fake clock, so a result never depends on the machine.
- **Asserting on private details.** Tests call public functions and check results.
- **Sleeping to wait for a process.** The process tests poll with a deadline instead of sleeping a fixed time.

## Check yourself

1. What does `tests/unit/application/test_report_and_metered_model.py` test?

   *Answer:* It holds the tests for `report and metered model`.

2. What does `tests/unit/application/test_run_meter.py` test?

   *Answer:* It holds the tests for `run meter`.

3. What does `tests/unit/domain/test_analysis.py` test?

   *Answer:* It holds the tests for `analysis`.

4. What does `tests/unit/domain/test_llm.py` test?

   *Answer:* It holds the tests for `llm`.

5. What does `tests/unit/domain/test_pricing_and_estimation.py` test?

   *Answer:* It holds the tests for `pricing and estimation`.

## Further reading

- pytest documentation, https://docs.pytest.org/en/stable/ (pytest 9.1.1 is pinned; the per-statement explanations are generated from the code's structure).

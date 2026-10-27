# Python

## What it is

**Python** is a programming language. A **program** is a text file of instructions; a **programming language** is the set of rules for writing them. Python is easy to read: it uses indentation (spaces at the start of a line) to show which lines belong together, and plain words for most operations.

The program that reads and runs Python code is the **interpreter**, also called `python`. It reads the file, turns each line into simple internal steps (called *bytecode*), and carries them out one by one. You do not compile first.

Python code is split into **modules** (files ending in `.py`) and **packages** (folders of modules). A **variable** is a name for a value (`count = 3`). A **function** is named, reusable code (`def add(a, b): return a + b`). A **class** is a blueprint for objects that bundle data with behavior. A **type** says what kind of value something is: whole number (`int`), decimal number (`float`), text (`str`), true or false (`bool`), list, dictionary.

## Why this repository uses it

Python is the language of the AI ecosystem: the Claude SDK, the model-serving tools and the test tools are all Python libraries. It reads close to plain English, which suits a learning repository whose goal is that you understand the code.

The project asks for Python 3.12 or newer (`requires-python = ">=3.12"`). The Makefile uses 3.13 when it is installed. Newer syntax used here includes the `X | None` type form, `StrEnum` and `@dataclass(slots=True)`.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/token_meter/` | 32 Python files: the program itself |
| `tests/` | 17 Python files: automated tests |
| `scripts/` | 1 Python helper script(s) that generate the committed data files |
| `pyproject.toml` | declares the Python version and the command-line programs |
| `Makefile` | starts every Python program through `.venv/bin` |

## How it works underneath

**Objects everywhere.** Every value in Python is an *object*: a chunk of memory with a type and some data. A variable is a label attached to an object. `a = b` makes a second label on the same object; it does not copy.

**Mutable and immutable.** Numbers, strings, tuples and frozen dataclasses cannot be changed after creation (they are *immutable*). Lists, dictionaries and sets can (they are *mutable*). Code that shares data between threads or between layers prefers immutable objects.

**The import system.** `import a.b` looks for a folder `a` with a file `b.py` on the module search path `sys.path`, runs the file once, and keeps the result in `sys.modules` so later imports reuse it.

**Type hints are not checked at run time.** The interpreter ignores them. The separate tool mypy reads them and reports mismatches (see `mypy.md`).

**Exceptions and the call stack.** Each running function has a frame on the stack. When an exception is raised, Python unwinds the stack frame by frame until an `except` matches; if none does, the program ends and prints a *traceback*, the list of frames.

**Threads and the GIL.** The standard interpreter lets only one thread run Python bytecode at a time (the *global interpreter lock*). Threads are therefore good for waiting on the network, not for heavy calculation. The test helpers and servers here use them for waiting.

**Garbage collection.** Python counts the labels attached to each object and frees it when the count reaches zero.

## Walkthrough of this repository's use

### A first tour of the language (every snippet was run; the output is real)

#### Values, names and types

A **value** is a piece of data. A **name** (variable) is a label you attach to a value with `=`. Every value has a **type**: `int` (whole number), `float` (decimal number), `str` (text), `bool` (`True` or `False`). `print(...)` shows values on the screen; `type(x)` tells you the type.

```python
price = 12.5
name = "meter"
count = 3
print(name, price * count, type(count), type(price), type(name), count > 2)
```

It prints:

```text
meter 37.5 <class 'int'> <class 'float'> <class 'str'> True
```

#### Text

Text is written in quotes. An *f-string* (`f"..."`) fills in values written between braces. Text has methods you call with a dot.

```python
who = "world"
print(f"hello {who}, {len(who)} letters", who.upper(), who.replace("o", "0"))
```

It prints:

```text
hello world, 5 letters WORLD w0rld
```

#### Lists and loops

A **list** is an ordered collection in square brackets. `for item in list:` repeats the indented lines once for each item. A list comprehension builds a new list in one line.

```python
prompts = ["a", "bb", "ccc"]
for p in prompts:
    print(p, len(p))
print([len(p) for p in prompts])
```

It prints:

```text
a 1
bb 2
ccc 3
[1, 2, 3]
```

#### Dictionaries

A **dictionary** (dict) is a collection of `key: value` pairs in braces. You look a value up by its key; `.get(key, default)` gives a default when the key is missing instead of raising an error.

```python
row = {"id": "p01", "kind": "short"}
row["tokens"] = 12
print(row["id"], row.get("missing", "none"), list(row))
```

It prints:

```text
p01 none ['id', 'kind', 'tokens']
```

#### Decisions

`if`, `elif` and `else` choose which indented block runs. Indentation (four spaces) is the grammar: it marks what belongs to what.

```python
n = 7
if n < 5:
    print("small")
elif n < 10:
    print("medium")
else:
    print("large")
```

It prints:

```text
medium
```

#### Functions

`def name(parameters):` defines reusable code. `return` hands a value back. A function with a docstring (a text in triple quotes as its first line) documents itself.

```python
def cost(tokens, per_thousand):
    """Dollars for a number of tokens."""
    return tokens / 1000 * per_thousand
print(cost(2500, 0.0005), cost.__doc__)
```

It prints:

```text
0.00125 Dollars for a number of tokens.
```

#### Classes and dataclasses

A **class** bundles data with the functions that use it. A dataclass writes the boring parts for you.

```python
from dataclasses import dataclass
@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int
u = Usage(10, 4)
print(u, u.input_tokens + u.output_tokens)
```

It prints:

```text
Usage(input_tokens=10, output_tokens=4) 14
```

#### Errors

When something goes wrong Python *raises an exception*. `try`/`except` catches it so the program can respond instead of stopping.

```python
try:
    int("twelve")
except ValueError as error:
    print("caught:", error)
```

It prints:

```text
caught: invalid literal for int() with base 10: 'twelve'
```

### How the code is laid out

All code of the program lives in the package `token_meter` under `src/`. It has four sub-packages that form layers: `domain` (the core ideas, with no outside technology), `application` (the use cases that combine them), `infrastructure` (adapters to files, databases, networks and vendor SDKs) and `interfaces` (the command line, the web server). The rule is: outer layers may import inner ones, never the other way. `import-linter` enforces it (see `import-linter.md`).

| File | What the file says it is (its own first docstring line) |
| --- | --- |
| `scripts/make_prompts.py` | Write data/prompts.jsonl: 50 customer messages to a shop's support desk, in five kinds. |
| `src/token_meter/__init__.py` | token_meter: estimate, call, bill and compare, for a batch of model calls. |
| `src/token_meter/application/__init__.py` | Use cases and the ports they need. Depends on the domain only. |
| `src/token_meter/application/metered_model.py` | A decorator for services: estimate each request before it is sent and log estimate and bill side by side. |
| `src/token_meter/application/ports.py` | The boundaries the use cases depend on. Adapters in `infrastructure` implement them. |
| `src/token_meter/application/report.py` | Build the report from the journal: estimated against billed, calibration and spread. |
| `src/token_meter/application/run_meter.py` | The metering run: estimate first, refuse above the budget, call, and journal one row per call. |
| `src/token_meter/domain/__init__.py` | Pure domain logic. Depends on nothing outside the standard library. |
| `src/token_meter/domain/analysis.py` | Compare estimates with the bill, calibrate the estimator and measure the spread between answers. |
| `src/token_meter/domain/decoding.py` | The decoding settings the meter compares. |
| `src/token_meter/domain/errors.py` | Named errors. Callers catch these, never a vendor SDK's exception types. |
| `src/token_meter/domain/estimation.py` | Estimate tokens and cost before any call is made. |
| `src/token_meter/domain/journal.py` | One row per paid call: the unit of restartability. |
| `src/token_meter/domain/llm.py` | Vendor-neutral value objects for one chat-model call. No SDK is imported here. |
| `src/token_meter/domain/pricing.py` | The dated price table. Prices change, so a table older than the allowed age is refused. |
| `src/token_meter/domain/prompts.py` | The prompt set: 50 customer messages in five kinds, and the rules that make it a fair sample. |
| `src/token_meter/infrastructure/__init__.py` | Adapters that implement the ports: model clients, files, settings, logging. |
| `src/token_meter/infrastructure/anthropic_chat.py` | A chat model on the Anthropic Messages API, through the official SDK. |
| `src/token_meter/infrastructure/clock.py` | The real clock, behind the `Clock` port. |
| `src/token_meter/infrastructure/csv_journal.py` | The journal as a CSV file: append and flush one row per call, so a crash costs only unfinished calls. |
| `src/token_meter/infrastructure/env.py` | Helpers that read and validate environment variables (twelve-factor configuration). |
| `src/token_meter/infrastructure/files.py` | Readers for the prompt file (JSON Lines) and the price file (JSON). |
| `src/token_meter/infrastructure/logging.py` | Structured logging: one logfmt line per event (`ts=... level=... logger=... msg=... key=value`). |
| `src/token_meter/infrastructure/model_factory.py` | Builds the configured chat model from the environment: recorded, local server or Claude. |
| `src/token_meter/infrastructure/openai_compatible.py` | A chat model behind the OpenAI-compatible `/chat/completions` endpoint (Ollama, llama.cpp, vLLM, hosted). |
| `src/token_meter/infrastructure/recording.py` | Recorded responses: replay them in tests and demos, or record a live model's answers into fixtures. |
| `src/token_meter/infrastructure/resilient.py` | A decorator that retries transient model failures with backoff and jitter. |
| `src/token_meter/infrastructure/retry.py` | Retry with exponential backoff and jitter for calls that cross the network. |
| `src/token_meter/infrastructure/settings.py` | Configuration from the environment, validated once at startup (twelve-factor). |
| `src/token_meter/infrastructure/shutdown.py` | Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work. |
| `src/token_meter/interfaces/__init__.py` | Command-line programs. They wire adapters into use cases and own exit codes. |
| `src/token_meter/interfaces/cli.py` | The `meter` command: estimate, run, report. |
| `src/token_meter/interfaces/render.py` | Plain-text rendering of the estimate and the report (what the commands print). |

The tests under `tests/` use pytest (see `pytest.md`):

| Test file | What it contains |
| --- | --- |
| `tests/conftest.py` | Shared builders for tests: small prompt sets, a fixed clock and a scripted model. |
| `tests/e2e/test_lesson_scenario.py` | The lesson's scenario from the prompt file to the report, on the recorded model. 4 test functions, for example `test_step_1_the_prompt_file_has_fifty_rows_in_five_kinds_one_long_and_the_price_file_is_dated`, `test_step_2_the_estimate_is_printed_and_a_low_budget_stops_the_run`, `test_steps_3_to_6_the_run_fills_450_rows_and_the_report_answers_each_question`, .... |
| `tests/integration/test_cli_process.py` | The `meter` program as a real process: a hard kill in the middle of a run, then a restart. 3 test functions, for example `test_a_run_killed_with_sigkill_resumes_and_ends_with_exactly_450_rows_and_no_repeated_key`, `test_sigterm_finishes_the_call_in_flight_and_exits_with_the_interrupted_code`, `test_the_budget_refusal_happens_before_any_row_is_written`. |
| `tests/live/test_live_models.py` | Opt-in tests that call a real model. Run with `make test-live`; skipped in every other run. 2 test functions, for example `test_claude_answers_and_reports_billed_usage`, `test_the_local_model_returns_a_usage_block_and_obeys_temperature_zero`. |
| `tests/unit/application/test_report_and_metered_model.py` | 3 test functions, for example `test_the_report_finds_the_overhead_and_shows_the_error_shrink`, `test_the_metered_model_logs_estimate_and_bill_without_the_prompt_text`, `test_a_zero_billed_input_does_not_divide_by_zero`. |
| `tests/unit/application/test_run_meter.py` | 10 test functions, for example `test_a_plan_covers_every_prompt_setting_and_repeat`, `test_a_run_makes_every_call_and_journals_one_row_each`, `test_the_output_cap_is_the_same_for_every_setting_and_only_sampling_changes`, .... |
| `tests/unit/domain/test_analysis.py` | 14 test functions, for example `test_the_naive_estimator_is_off_most_on_short_prompts`, `test_the_largest_gap_names_a_cause`, `test_the_measured_overhead_is_the_median_residual`, .... |
| `tests/unit/domain/test_llm.py` | 5 test functions, for example `test_the_same_request_always_has_the_same_fingerprint`, `test_the_model_name_is_not_part_of_the_fingerprint`, `test_the_tag_and_the_sampling_settings_are_part_of_the_fingerprint`, .... |
| `tests/unit/domain/test_pricing_and_estimation.py` | 7 test functions, for example `test_cost_uses_separate_input_and_output_prices`, `test_a_fresh_table_is_accepted_and_an_old_one_is_refused`, `test_a_table_dated_in_the_future_is_refused`, .... |
| `tests/unit/domain/test_prompts.py` | 10 test functions, for example `test_a_set_that_matches_the_spec_is_accepted`, `test_the_lesson_spec_asks_for_fifty_prompts_in_five_kinds`, `test_repeated_ids_are_rejected_by_name`, .... |
| `tests/unit/infrastructure/test_anthropic_chat.py` | 11 test functions, for example `test_text_usage_stop_reason_and_model_come_from_the_response`, `test_sampling_is_refused_because_the_messages_api_rejects_it`, `test_thinking_can_be_left_out_or_set_to_between_tools`, .... |
| `tests/unit/infrastructure/test_csv_journal.py` | 4 test functions, for example `test_a_new_journal_gets_one_header_and_no_rows`, `test_rows_survive_a_reopen_and_the_header_is_not_written_twice`, `test_a_torn_last_line_from_a_kill_is_cut_off_on_open`, .... |
| `tests/unit/infrastructure/test_files_and_settings.py` | 8 test functions, for example `test_prompts_are_read_one_per_line`, `test_one_bad_line_fails_with_its_line_number_and_not_the_whole_file`, `test_prices_carry_a_real_date_field`, .... |
| `tests/unit/infrastructure/test_openai_compatible.py` | 12 test functions, for example `test_a_reply_becomes_text_usage_stop_reason_and_latency`, `test_unset_sampling_is_left_out_of_the_body`, `test_a_schema_becomes_a_json_schema_response_format`, .... |
| `tests/unit/infrastructure/test_recording.py` | 6 test functions, for example `test_recording_then_replaying_returns_the_same_response`, `test_a_request_already_recorded_is_not_sent_again`, `test_an_unrecorded_request_names_the_tag_and_the_fix`, .... |
| `tests/unit/infrastructure/test_resilience_logging_factory.py` | 15 test functions, for example `test_a_transient_failure_is_retried_with_backoff_and_then_succeeds`, `test_the_last_transient_failure_is_raised_after_the_attempts_run_out`, `test_a_permanent_failure_is_not_retried`, .... |
| `tests/unit/interfaces/test_cli.py` | 11 test functions, for example `test_estimate_prints_the_whole_run_and_calls_no_model`, `test_estimate_also_refuses_when_the_budget_is_below_it`, `test_a_budget_below_the_estimate_refuses_to_start_with_a_clear_message`, .... |

### The language features this code uses, with a real example of each

#### Imports

An *import* brings code from another file or package into this one. `import json` makes the module available as `json.something`. `from json import loads` brings in just the name `loads`. A **module** is one `.py` file; a **package** is a folder of modules with an `__init__.py` file. Imports that start with the project's own package name (for example `from token_meter.domain...`) are the project's own code; the rest come from the standard library or from installed packages.

From this repository, `src/token_meter/application/metered_model.py`, lines 7 to 10:

```python
from token_meter.application.ports import ChatModel
from token_meter.domain.estimation import TokenEstimator
from token_meter.domain.llm import ChatRequest, ChatResponse

```

#### `from __future__ import annotations`

Makes Python store type annotations as text instead of evaluating them when the function or class is defined. A class can then name itself in an annotation, and imports used only for types cost nothing at run time. Every module of this repository starts with it.

From this repository, `src/token_meter/application/metered_model.py`, lines 3 to 4:

```python
from __future__ import annotations

```

#### Functions with type hints

`def name(a: int, b: str = "x") -> bool:` defines a function. After each parameter, `: int` is a *type hint*: a note for people and for the mypy checker that says what kind of value is expected (Python itself does not enforce it). `= "x"` gives a *default value* used when the caller leaves the argument out. `-> bool` says what the function returns.

From this repository, `src/token_meter/application/run_meter.py`, lines 58 to 67:

```python
def estimate_pending(plan: RunPlan, done: set[CallKey]) -> RunEstimate:
    """The cost of the calls the journal does not hold yet, estimated before the first one."""
    by_prompt = {p.id: p for p in plan.prompts}
    pending = [k for k in plan_keys(plan) if k not in done]
    input_tokens = sum(
        plan.estimator.tokens(by_prompt[k.prompt_id].text, plan.system or "", by_prompt[k.prompt_id].kind)
        for k in pending
    )
    output_tokens = len(pending) * plan.max_output_tokens
    return RunEstimate(len(pending), input_tokens, output_tokens, plan.prices.cost(input_tokens, output_tokens))
```

#### Classes and `self`

A **class** is a blueprint for objects that bundle data and behavior. `__init__` runs when an object is created; its first parameter, `self`, is the object being built, and `self.x = value` stores data on it. A **method** is a function defined inside a class; every method receives `self` first.

From this repository, `tests/conftest.py`, lines 14 to 29:

```python
class FixedClock:
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
        return datetime(self._today.year, self._today.month, self._today.day, tzinfo=UTC)
```

#### Dataclasses

`@dataclass` is a *decorator* (a line starting with `@` above a definition that changes it). It reads the annotated names in the class body and writes `__init__`, `__repr__` and `__eq__` for you. `frozen=True` forbids changing an object after creation, so it can be shared safely and used as a dictionary key. `slots=True` stores fields in a compact fixed layout.

From this repository, `src/token_meter/application/report.py`, lines 24 to 36:

```python
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
```

#### Enums

An **enum** is a fixed set of named values. `StrEnum` makes each member also a string (`Role.USER == "user"`), which is convenient for JSON and logs.

From this repository, `src/token_meter/domain/llm.py`, lines 13 to 18:

```python
class Role(StrEnum):
    """Who wrote a message."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
```

#### Protocols (structural typing)

A `Protocol` lists methods an object must have. Any class that has those methods is accepted wherever the protocol is asked for, without inheriting from it. This repository uses protocols as *ports*: the use cases ask for a `ChatModel` or a `Clock`, and the real adapter, the recording adapter and a test fake all fit.

From this repository, `src/token_meter/application/ports.py`, lines 13 to 28:

```python
class ChatModel(Protocol):
    """One chat model behind one interface: a vendor, a local server or a recording."""

    @property
    def name(self) -> str:
        """The model id the responses come from."""
        ...

    @property
    def supports_sampling(self) -> bool:
        """False when the provider rejects `temperature` and `top_p` (the request then says so)."""
        ...

    def complete(self, request: ChatRequest) -> ChatResponse:
        """Send one request. Raises `TransientModelError` or `PermanentModelError`."""
        ...
```

#### Properties

`@property` turns a method into something read like a field: `model.name` instead of `model.name()`. The value is worked out each time.

From this repository, `src/token_meter/application/metered_model.py`, lines 21 to 23:

```python
    @property
    def name(self) -> str:
        return self._inner.name
```

#### Class methods

`@classmethod` defines a method that receives the class (`cls`) instead of an object. It is used here as a named constructor: `ChatMessage.user("hi")`.

From this repository, `src/token_meter/domain/llm.py`, lines 58 to 60:

```python
    @classmethod
    def user(cls, content: str) -> ChatMessage:
        return cls(Role.USER, content)
```

#### Exceptions: raise, try, except

An **exception** is an object that signals a problem and jumps out of the running code until something catches it. `raise X(...)` throws one. `try:` ... `except X:` runs the second block if the first threw an `X`. `raise Y from X` throws a new exception while keeping the original as its cause. `finally:` runs whatever happens.

From this repository, `src/token_meter/domain/prompts.py`, lines 58 to 62:

```python
    try:
        kind = Kind(row["kind"])
    except ValueError as error:
        raise InvalidPromptSet(f"field 'kind' must be one of {[k.value for k in Kind]}, got {row['kind']!r}") from error
    label = row.get("expected_label")
```

#### Custom exception classes

A class that inherits from `Exception` is a new kind of error. Giving errors their own names lets callers catch exactly the failures they know how to handle.

From this repository, `src/token_meter/domain/analysis.py`, lines 22 to 23:

```python
class NotEnoughData(DomainError):
    """The journal does not hold the rows the analysis needs."""
```

#### `try` / `except` blocks

Code that might fail is placed under `try:`; the matching `except` names the error it handles.

From this repository, `src/token_meter/domain/prompts.py`, lines 58 to 61:

```python
    try:
        kind = Kind(row["kind"])
    except ValueError as error:
        raise InvalidPromptSet(f"field 'kind' must be one of {[k.value for k in Kind]}, got {row['kind']!r}") from error
```

#### `with` blocks

`with thing as name:` is a *context manager*: it runs setup code on entry and cleanup code on exit, even if an error happens inside. Files, locks, database connections and temporary folders all use it.

From this repository, `src/token_meter/infrastructure/csv_journal.py`, lines 41 to 44:

```python
        with self._path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
```

#### f-strings

A string starting with `f"` can hold `{expression}` parts that are replaced by their values: `f"{count} rows"`. After the expression, `:` begins a format (`{price:.4f}` means four decimals).

From this repository, `src/token_meter/application/metered_model.py`, line 46:

```python
                    "error": f"{error:+.1%}",
```

#### List and dict comprehensions

`[x * 2 for x in items if x > 0]` builds a list by looping. `{k: v for k, v in pairs}` builds a dictionary. Written inside `sum(...)` or `any(...)` without brackets, it is a *generator expression* that produces values one at a time.

From this repository, `src/token_meter/application/run_meter.py`, line 61:

```python
    pending = [k for k in plan_keys(plan) if k not in done]
```

#### Lambdas

`lambda x: x + 1` is a small unnamed function written inline. It is used for a sort key or a callback.

From this repository, `src/token_meter/application/run_meter.py`, lines 77 to 78:

```python
        stop_requested: Callable[[], bool] = lambda: False,
        sleep: Callable[[float], None] = time.sleep,
```

#### Union types and `None`

`X | None` means "an X or nothing". `list[str]`, `dict[str, int]` and `tuple[int, ...]` describe collections and what is inside them. `Mapping`, `Sequence` and `Callable` (from `collections.abc`) describe *anything that behaves like* a dictionary, a list, or a function.

From this repository, `src/token_meter/application/run_meter.py`, line 33:

```python
    budget: Decimal | None = None
```

#### Decimal numbers

`float` numbers are binary approximations (0.1 + 0.2 is 0.30000000000000004). Money needs exact arithmetic, so prices use `Decimal`, which stores decimal digits exactly.

From this repository, `src/token_meter/domain/analysis.py`, lines 223 to 227:

```python
        by_prompt[row.key.prompt_id].append(row)
    estimates: dict[str, int] = {}
    estimated = billed = ceiling = Decimal(0)
    calls = 0
    for prompt in prompts:
```

#### Paths

`pathlib.Path` represents a file location as an object. The `/` operator joins parts (`root / "data" / "x.json"`), and methods such as `read_text()` read the file.

From this repository, `src/token_meter/infrastructure/files.py`, lines 31 to 33:

```python
    """Read the price file. `read_date` is a real field so a script can refuse stale prices."""
    data = json.loads(path.read_text(encoding="utf-8"))
    try:
```

#### `Literal` and `Final`

`Literal["a", "b"]` as a type says the value must be exactly one of those. `Final` says a name is assigned once and never changed.

From this repository, `src/token_meter/infrastructure/anthropic_chat.py`, lines 18 to 19:

```python
Thinking = Literal["omit", "disabled", "between_tools"]

```

#### `*args` and `**kwargs`

`*args` collects extra positional arguments into a tuple; `**kwargs` collects extra named arguments into a dictionary. They let a wrapper pass everything on to the function it wraps.

From this repository, `tests/unit/interfaces/test_cli.py`, lines 29 to 33:

```python


def scripted(monkeypatch, **kwargs):
    model = ScriptedModel(lambda request: ("billing", 40, 6), **kwargs)
    monkeypatch.setattr(cli, "build_chat_model", lambda *args, **kw: model)
```

#### `isinstance` and `getattr`

`isinstance(x, T)` asks whether `x` is a `T`. `getattr(obj, "name", default)` reads an attribute by a name held in a variable.

From this repository, `src/token_meter/domain/prompts.py`, lines 55 to 57:

```python
    for name in ("id", "kind", "text"):
        if not isinstance(row.get(name), str) or not row[name].strip():
            raise InvalidPromptSet(f"field {name!r} must be a non-empty string, got {row.get(name)!r}")
```

#### Threads

A **thread** is a second line of execution inside one program. Threads share memory, so code that changes shared data protects it with a *lock*. See `python-standard-library.md` for `threading`.

From this repository, `src/token_meter/infrastructure/recording.py`, lines 24 to 28:

```python
        self._path = path
        self._lock = threading.Lock()
        self._entries: dict[str, dict[str, Any]] = {}
        files = sorted(path.glob("*.jsonl")) if path.is_dir() else ([path] if path.exists() else [])
        for file in files:
```

#### Generic functions with type parameters (Python 3.12)

`def name[T](...)` declares a *type parameter*: a stand-in for "whatever type the caller uses", so a function can promise "returns the same kind of thing it was given". `**P` declares a *parameter specification*, which stands for a whole list of parameters, used with `Concatenate` to describe a decorator that adds one argument. This is syntax new in Python 3.12, which is why the project requires 3.12.

From this repository, `src/token_meter/infrastructure/retry.py`, lines 10 to 22:

```python
def retry[T](
    operation: Callable[[], T],
    *,
    attempts: int,
    base_delay_seconds: float,
    retry_on: tuple[type[BaseException], ...],
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    max_delay_seconds: float = 10.0,
    on_retry: Callable[[int, BaseException], None] | None = None,
) -> T:
    """Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.

```

#### `if __name__ == "__main__"`

When a file is run directly, Python sets the special variable `__name__` to `"__main__"`. The guard makes some code run only in that case and not when the file is imported.

From this repository, `src/token_meter/interfaces/cli.py`, lines 132 to 134:

```python
if __name__ == "__main__":
    sys.exit(main())

```

### Running the code

You never type `python src/...` in this repository. The Makefile calls the programs that pip installed into `.venv/bin`, such as `.venv/bin/meter`, or runs `.venv/bin/python -m pytest`. `python -m NAME` means "run the module called NAME as a program". The `[project.scripts]` table of `pyproject.toml` (see `pyproject-toml.md`) says which function each installed program calls.

## Try it yourself

1. Which Python the project uses.

```bash
.venv/bin/python --version
```

What you should see (captured from this repository):

```text
Python 3.13.12
```

2. Two names, one list: appending through `y` changes what `x` sees, because `y = x` copies the label, not the list.

```bash
.venv/bin/python -c "x = [1, 2, 3]; y = x; y.append(4); print(x, x is y)"
```

What you should see (captured from this repository):

```text
[1, 2, 3, 4] True
```

3. Why money uses `Decimal`: binary floating point cannot store 0.1 exactly.

```bash
.venv/bin/python -c "print(0.1 + 0.2); from decimal import Decimal; print(Decimal('0.1') + Decimal('0.2'))"
```

What you should see (captured from this repository):

```text
0.30000000000000004
0.3
```

4. Type hints are not enforced when the program runs. The error here comes from the `+`, not from the hint.

```bash
.venv/bin/python -c "def f(a: int) -> int: return a + 1
print(f('x'))" 2>&1 | tail -1
```

What you should see (captured from this repository):

```text
TypeError: can only concatenate str (not "int") to str
```

5. The project is an ordinary package that Python finds through the editable install.

```bash
.venv/bin/python -c "import token_meter; print(token_meter.__file__)"
```

What you should see (captured from this repository):

```text
src/token_meter/__init__.py
```

## Mistakes people make

- **Thinking `=` copies.** `b = a` makes a second label; changing a list through one name changes it for both. The code copies explicitly (`list(x)`, `dict(x)`, `dataclasses.replace`) when it needs a separate object.
- **Using `float` for money.** Prices here are `Decimal` so the totals add up exactly.
- **A mutable default argument.** `def f(x=[])` shares one list across all calls. Defaults here are `None` or immutable values.
- **Catching every exception.** A bare `except:` hides bugs. The code names the exceptions it can handle.
- **Confusing indentation.** Mixed spaces and tabs break Python. `.editorconfig` sets four spaces for `.py` files.
- **Importing the wrong direction.** An inner layer importing an outer one makes cycles and drags technology into the core. `import-linter` fails the build if that happens.

## Check yourself

1. What does `-> bool` after a function signature say?

   *Answer:* That the function returns a `bool`. It is a hint for tools and readers.

2. What does `@dataclass(frozen=True)` give you?

   *Answer:* A class with generated `__init__`, `__repr__` and `__eq__`, whose objects cannot be changed after creation.

3. Why is a `Protocol` used for `ChatModel`?

   *Answer:* So any class with the right methods (real adapter, recording, test fake) is accepted without inheriting from a base class.

4. What does `raise B from A` record?

   *Answer:* That `B` was caused by `A`, so the traceback shows both.

5. What does `if __name__ == "__main__":` do?

   *Answer:* Runs the indented code only when the file is run directly, not when imported.

## Further reading

- The Python Tutorial and Language Reference, https://docs.python.org/3.13/tutorial/ and https://docs.python.org/3.13/reference/ (the project requires Python 3.12 or newer; examples here were run on Python 3.13).

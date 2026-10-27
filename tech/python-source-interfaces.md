# Python source, the interfaces layer

## What it is

This note walks through every Python file of the `interfaces` layer of `token_meter`, line by line. Read `python.md` first for the language features; this note shows them at work.

The **interfaces** layer is the outermost: the command-line program and, where present, the HTTP service. It reads the command line or a request, builds the adapters, calls a use case and turns the result into output and an exit code.

## Why this repository uses it

It is the only layer allowed to know about everything below it, and nothing depends on it. That keeps start-up wiring in one place.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/token_meter/interfaces/__init__.py` | 1 non-blank lines |
| `src/token_meter/interfaces/cli.py` | 115 non-blank lines |
| `src/token_meter/interfaces/render.py` | 55 non-blank lines |

## How it works underneath

Every file here is a *module*: Python runs it from top to bottom the first time something imports it. Imports come first, then constants, then the definitions (classes and functions). Defining a function or class does not run its body; the body runs when it is called.

How to read the explanations below. Each quoted block is a run of consecutive lines from the file, with its file name and line numbers. Under it, one bullet explains each statement in order, in plain words. A bullet that mentions a function the project defines also gives that function's own description (its docstring). Indented bullets under a statement explain the pieces inside it: calls, comprehensions, comparisons and operators. A `def` bullet lists the parameters; `self` is the object a method works on.

The layering rule that decides what this layer may import is enforced by `import-linter.md`; the file list above is the whole layer.

## Walkthrough of this repository's use

### `src/token_meter/interfaces/__init__.py`

In its own words: "Command-line programs. They wire adapters into use cases and own exit codes."

1 non-blank lines.

`src/token_meter/interfaces/__init__.py`, lines 1 to 1:

```python
"""Command-line programs. They wire adapters into use cases and own exit codes."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

### `src/token_meter/interfaces/cli.py`

In its own words: "The `meter` command: estimate, run, report."

115 non-blank lines; it defines `build_parser`, `_load`, `_budget`, `run_command`, `report_command`, `main`.

`src/token_meter/interfaces/cli.py`, lines 1 to 14:

```python
"""The `meter` command: estimate, run, report."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation

from token_meter.application.ports import ChatModel
from token_meter.application.report import build_report
from token_meter.application.run_meter import RunMeter, RunPlan, estimate_pending
from token_meter.domain.decoding import DEFAULT_SETTINGS
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `argparse` (standard library) available.
- Makes the module `logging` (standard library) available.
- Makes the module `sys` (standard library) available.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Brings in `Decimal`, `InvalidOperation` from the standard library module `decimal`.
- Brings in `ChatModel` (One chat model behind one interface: a vendor, a local server or a recording.) from the project module `token_meter.application.ports`.
- Brings in `build_report` (Compare the naive estimator with the bill, add the measured overhead, then forecast each prompt leave-one-out.) from the project module `token_meter.application.report`.
- Brings in `RunMeter` (Calls the model once per (prompt, setting, repeat) that the journal does not hold yet.), `RunPlan` (Everything that defines a run besides the model and the journal.), `estimate_pending` (The cost of the calls the journal does not hold yet, estimated before the first one.) from the project module `token_meter.application.run_meter`.
- Brings in `DEFAULT_SETTINGS` from the project module `token_meter.domain.decoding`.

`src/token_meter/interfaces/cli.py`, lines 15 to 27:

```python
from token_meter.domain.errors import DomainError, UnsupportedParameter
from token_meter.domain.estimation import BudgetExceeded, TokenEstimator, require_within_budget
from token_meter.domain.pricing import PriceTable, StalePrices
from token_meter.domain.prompts import InvalidPromptSet, PromptRecord, PromptSetSpec, validate_prompt_set
from token_meter.infrastructure.clock import SystemClock
from token_meter.infrastructure.csv_journal import CsvJournal
from token_meter.infrastructure.env import ConfigurationError
from token_meter.infrastructure.files import load_prices, load_prompts
from token_meter.infrastructure.logging import configure_logging
from token_meter.infrastructure.model_factory import ModelSettings, build_chat_model
from token_meter.infrastructure.settings import MeterSettings
from token_meter.infrastructure.shutdown import ShutdownSignal
from token_meter.interfaces.render import render_estimate, render_report
```

- Brings in `DomainError` (Base class for every error this package raises on purpose.), `UnsupportedParameter` (The adapter cannot honor a parameter the request asked for (for example sampling on Claude).) from the project module `token_meter.domain.errors`.
- Brings in `BudgetExceeded` (The estimate is above the budget, so the run must not start.), `TokenEstimator` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.), `require_within_budget` (Raise `BudgetExceeded` when a budget is set and the estimate is above it.) from the project module `token_meter.domain.estimation`.
- Brings in `PriceTable` (Price per 1,000 input and output tokens, with the day the numbers were read.), `StalePrices` (The price table was read too long ago to trust.) from the project module `token_meter.domain.pricing`.
- Brings in `InvalidPromptSet` (The prompt file breaks a rule of the lesson (row count, kinds, a long prompt, unique ids).), `PromptRecord` (One prompt. `expected_label` is set only for label prompts.), `PromptSetSpec` (The shape the lesson asks for: counts per kind and one prompt over a token threshold.), `validate_prompt_set` (Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken.) from the project module `token_meter.domain.prompts`.
- Brings in `SystemClock` (Wall-clock and monotonic time from the operating system.) from the project module `token_meter.infrastructure.clock`.
- Brings in `CsvJournal` (Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open.) from the project module `token_meter.infrastructure.csv_journal`.
- Brings in `ConfigurationError` (An environment variable is missing or has an unusable value.) from the project module `token_meter.infrastructure.env`.
- Brings in `load_prices` (Read the price file. `read_date` is a real field so a script can refuse stale prices.), `load_prompts` (Read one prompt per line. A bad line is reported with its line number; the rest of the file is not lost.) from the project module `token_meter.infrastructure.files`.
- Brings in `configure_logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.) from the project module `token_meter.infrastructure.logging`.
- Brings in `ModelSettings` (Which model to call and how. See .env.example for every variable.), `build_chat_model` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.) from the project module `token_meter.infrastructure.model_factory`.
- Brings in `MeterSettings` (Everything the programs read from the environment. See .env.example for each variable.) from the project module `token_meter.infrastructure.settings`.
- Brings in `ShutdownSignal` (A flag that SIGINT and SIGTERM set, which work loops check between units of work.) from the project module `token_meter.infrastructure.shutdown`.
- Brings in `render_estimate` (The line printed before the first call.), `render_report` (The report: input-token error by kind at three stages, the cost check and the spread per setting.) from the project module `token_meter.interfaces.render`.

`src/token_meter/interfaces/cli.py`, lines 29 to 38:

```python
EXIT_OK, EXIT_ERROR, EXIT_CONFIG, EXIT_REFUSED, EXIT_INTERRUPTED = 0, 1, 2, 3, 4
_log = logging.getLogger("meter")


def build_parser() -> argparse.ArgumentParser:
    """The `meter` argument parser: estimate, run and report."""
    parser = argparse.ArgumentParser(
        prog="meter", description="Estimate, call, bill and compare a batch of model calls."
    )
    sub = parser.add_subparsers(dest="command", required=True)
```

- Stores a tuple of 5 item(s) under the name `(EXIT_OK, EXIT_ERROR, EXIT_CONFIG, EX...`.
- Stores the result of calling `logging.getLogger` under the name `_log`.
  - `logging.getLogger` gets the logger with the given name.
- Defines the function `build_parser`. It returns `argparse.ArgumentParser`. The author's own description: "The `meter` argument parser: estimate, run and report."
- It takes no parameters.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `argparse.ArgumentParser` under the name `parser`.
  - `argparse.ArgumentParser` from the standard library module `argparse`.
- Stores the result of calling `parser.add_subparsers` under the name `sub`.
  - The method `add_subparsers` of `parser`.

`src/token_meter/interfaces/cli.py`, lines 39 to 51:

```python
    for name, helptext in (
        ("estimate", "print the estimate and stop"),
        ("run", "estimate, then make the missing calls"),
    ):
        command = sub.add_parser(name, help=helptext)
        command.add_argument("--budget", help="refuse to start if the estimate is above this many dollars")
        command.add_argument(
            "--allow-stale-prices", action="store_true", help="run with a price table past its age limit"
        )
        if name == "run":
            command.add_argument("--throttle", type=float, help="seconds to pause between calls")
    sub.add_parser("report", help="estimated against billed, cost per 1,000 requests and the spread per setting")
    return parser
```

- Loop: the indented lines below run once for each item of `(('estimate', 'print the estimate and stop'), ('run', 'es...`; `(name, helptext)` names the current item.
- Stores the result of calling `sub.add_parser` under the name `command`.
  - The method `add_parser` of `sub`.
- Calls the method `add_argument` of `command` with 2 argument(s); the result is not kept.
  - The method `add_argument` of `command`.
- Calls the method `add_argument` of `command` with 3 argument(s); the result is not kept.
  - The method `add_argument` of `command`.
- Decision: the indented lines below run only when `name == 'run'` is true.
  - `==` means equal.
- Calls the method `add_argument` of `command` with 3 argument(s); the result is not kept.
  - The method `add_argument` of `command`.
- Calls the method `add_parser` of `sub` with 2 argument(s); the result is not kept.
  - The method `add_parser` of `sub`.
- Ends the function and gives back the value named `parser` to the caller.

`src/token_meter/interfaces/cli.py`, lines 54 to 65:

```python
def _load(settings: MeterSettings) -> tuple[list[PromptRecord], PriceTable]:
    prompts = load_prompts(settings.prompts_path)
    validate_prompt_set(prompts, PromptSetSpec.lesson())
    return prompts, load_prices(settings.prices_path)


def _budget(arg: str | None, settings: MeterSettings) -> Decimal | None:
    if arg is None:
        return settings.budget
    try:
        return Decimal(arg)
    except InvalidOperation as error:
```

- Defines the function `_load`. It returns a fixed list of a list of the project type `PromptRecord`, the project type `PriceTable`.
- Its parameters:
    - `settings` holds the project type `MeterSettings`.
- Stores the result of calling `load_prompts` under the name `prompts`.
  - `load_prompts` from the project's `token_meter.infrastructure.files` (Read one prompt per line. A bad line is reported with its line number; the rest of the file is not lost.).
- Calls `validate_prompt_set` from the project's `token_meter.domain.prompts` (Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken.) with 2 argument(s); the result is not kept.
  - `validate_prompt_set` from the project's `token_meter.domain.prompts` (Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken.).
  - The method `lesson` of `PromptSetSpec`.
- Ends the function and gives back a tuple of 2 item(s) to the caller.
  - `load_prices` from the project's `token_meter.infrastructure.files` (Read the price file. `read_date` is a real field so a script can refuse stale prices.).
- Defines the function `_budget`. It returns an exact decimal number, or nothing (None).
- Its parameters:
    - `arg` holds text, or nothing (None).
    - `settings` holds the project type `MeterSettings`.
- Decision: the indented lines below run only when `arg is None` is true.
  - `is` means the very same object.
- Ends the function and gives back the `budget` of `settings` to the caller.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Ends the function and gives back the result of calling `Decimal` to the caller.
  - `Decimal` from the standard library module `decimal`.
- `except` handler: it runs when the `try` block raised `InvalidOperation`; `error` names the error object.

`src/token_meter/interfaces/cli.py`, lines 66 to 77:

```python
        raise ConfigurationError(f"--budget must be a decimal number, got {arg!r}") from error


def run_command(
    args: argparse.Namespace, settings: MeterSettings, model: ChatModel | None, shutdown: ShutdownSignal
) -> int:
    """Print the estimate for the pending calls, then make them when a model is given."""
    prompts, prices = _load(settings)
    if not args.allow_stale_prices:
        prices.require_fresh(SystemClock().today(), settings.price_max_age_days)
    journal = CsvJournal(settings.journal_path)
    throttle = args.throttle if getattr(args, "throttle", None) is not None else settings.throttle_seconds
```

- Raises an error: the result of calling `ConfigurationError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError` from the project's `token_meter.infrastructure.env` (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the function `run_command`. It returns a whole number. The author's own description: "Print the estimate for the pending calls, then make them when a model is given."
- Its parameters:
    - `args` holds `argparse.Namespace`.
    - `settings` holds the project type `MeterSettings`.
    - `model` holds the project type `ChatModel`, or nothing (None).
    - `shutdown` holds the project type `ShutdownSignal`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `_load` under the name `(prompts, prices)`.
  - `_load`, a function of this file.
- Decision: the indented lines below run only when `not args.allow_stale_prices` is true.
  - `not` flips true and false.
- Calls the method `require_fresh` of the project's `PriceTable` (Raise `StalePrices` when the table is older than `max_age_days` (or dated in the future).) with 2 argument(s); the result is not kept.
  - The method `require_fresh` of the project's `PriceTable` (Raise `StalePrices` when the table is older than `max_age_days` (or dated in the future).).
  - The method `today` of `SystemClock()`.
  - `SystemClock` from the project's `token_meter.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Stores the result of calling `CsvJournal` under the name `journal`.
  - `CsvJournal` from the project's `token_meter.infrastructure.csv_journal` (Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open.).
- Stores one of two values, chosen by a condition under the name `throttle`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is not` means not the same object.
  - `getattr` reads an attribute whose name is held in a variable.

`src/token_meter/interfaces/cli.py`, lines 78 to 91:

```python
    plan = RunPlan(
        prompts,
        DEFAULT_SETTINGS,
        settings.repeats,
        settings.max_output_tokens,
        prices,
        TokenEstimator(),
        budget=_budget(args.budget, settings),
        throttle_seconds=throttle,
    )
    estimate = estimate_pending(plan, journal.done_keys())
    print(render_estimate(estimate), flush=True)
    if model is None:
        require_within_budget(estimate, plan.budget)
```

- Stores the result of calling `RunPlan` under the name `plan`.
  - `RunPlan` from the project's `token_meter.application.run_meter` (Everything that defines a run besides the model and the journal.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
  - `_budget`, a function of this file.
- Stores the result of calling `estimate_pending` under the name `estimate`.
  - `estimate_pending` from the project's `token_meter.application.run_meter` (The cost of the calls the journal does not hold yet, estimated before the first one.).
  - The method `done_keys` of `journal`.
- Calls `print` writes text to the screen with 2 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - `render_estimate` from the project's `token_meter.interfaces.render` (The line printed before the first call.).
- Decision: the indented lines below run only when `model is None` is true.
  - `is` means the very same object.
- Calls `require_within_budget` from the project's `token_meter.domain.estimation` (Raise `BudgetExceeded` when a budget is set and the estimate is above it.) with 2 argument(s); the result is not kept.
  - `require_within_budget` from the project's `token_meter.domain.estimation` (Raise `BudgetExceeded` when a budget is set and the estimate is above it.).

`src/token_meter/interfaces/cli.py`, lines 92 to 104:

```python
        return EXIT_OK
    summary = RunMeter(model, journal, stop_requested=lambda: shutdown.requested).run(plan)
    print(f"calls made now: {summary.calls_made}; skipped, already in the journal: {summary.calls_skipped}")
    print(f"journal: {settings.journal_path} ({len(journal.rows())} rows)")
    return EXIT_INTERRUPTED if summary.interrupted else EXIT_OK


def report_command(settings: MeterSettings) -> int:
    """Print the report for the journal."""
    prompts, prices = _load(settings)
    journal = CsvJournal(settings.journal_path)
    print(render_report(build_report(journal, prompts, prices, TokenEstimator(), settings.max_output_tokens)))
    return EXIT_OK
```

- Ends the function and gives back the value named `EXIT_OK` to the caller.
- Stores the result of calling `RunMeter(model, journal, stop_requested=lambda:...` under the name `summary`.
  - The method `run` of the project's `RunMeter` (Refuse above the budget before any call, then make the missing calls, one journal row each.).
  - `RunMeter` from the project's `token_meter.application.run_meter` (Calls the model once per (prompt, setting, repeat) that the journal does not hold yet.).
  - `lambda args: expression` is a small unnamed function written inline.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `len` counts the items in a collection (or the characters in text).
  - The method `rows` of `journal`.
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
- Defines the function `report_command`. It returns a whole number. The author's own description: "Print the report for the journal."
- Its parameters:
    - `settings` holds the project type `MeterSettings`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `_load` under the name `(prompts, prices)`.
  - `_load`, a function of this file.
- Stores the result of calling `CsvJournal` under the name `journal`.
  - `CsvJournal` from the project's `token_meter.infrastructure.csv_journal` (Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open.).
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - `render_report` from the project's `token_meter.interfaces.render` (The report: input-token error by kind at three stages, the cost check and the spread per setting.).
  - `build_report` from the project's `token_meter.application.report` (Compare the naive estimator with the bill, add the measured overhead, then forecast each prompt leave-one-out.).
  - `TokenEstimator` from the project's `token_meter.domain.estimation` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Ends the function and gives back the value named `EXIT_OK` to the caller.

`src/token_meter/interfaces/cli.py`, lines 107 to 118:

```python
def main(argv: Sequence[str] | None = None) -> int:
    """Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted)."""
    args = build_parser().parse_args(argv)
    try:
        settings = MeterSettings.from_env()
        configure_logging(settings.log_level)
        if args.command == "report":
            return report_command(settings)
        shutdown = ShutdownSignal()
        shutdown.install()
        model = None
        if args.command == "run":
```

- Defines the function `main`. It returns a whole number. The author's own description: "Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted)."
- Its parameters:
    - `argv` holds anything that behaves like a list of text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `build_parser().parse_args` under the name `args`.
  - The method `parse_args` of `build_parser()`.
  - `build_parser`, a function of this file (The `meter` argument parser: estimate, run and report.).
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `MeterSettings.from_env` under the name `settings`.
  - The method `from_env` of `MeterSettings`.
- Calls `configure_logging` from the project's `token_meter.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.) with 1 argument(s); the result is not kept.
  - `configure_logging` from the project's `token_meter.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.).
- Decision: the indented lines below run only when `args.command == 'report'` is true.
  - `==` means equal.
- Ends the function and gives back the result of calling `report_command` to the caller.
  - `report_command`, a function of this file (Print the report for the journal.).
- Stores the result of calling `ShutdownSignal` under the name `shutdown`.
  - `ShutdownSignal` from the project's `token_meter.infrastructure.shutdown` (A flag that SIGINT and SIGTERM set, which work loops check between units of work.).
- Calls the method `install` of the project's `ShutdownSignal` (Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close.); the result is not kept.
  - The method `install` of the project's `ShutdownSignal` (Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close.).
- Stores nothing (`None`) under the name `model`.
- Decision: the indented lines below run only when `args.command == 'run'` is true.
  - `==` means equal.

`src/token_meter/interfaces/cli.py`, lines 119 to 132:

```python
            model = build_chat_model(ModelSettings.from_env(), SystemClock())
        return run_command(args, settings, model, shutdown)
    except (ConfigurationError, InvalidPromptSet, UnsupportedParameter) as error:
        print(f"meter: {error}", file=sys.stderr)
        return EXIT_CONFIG
    except (BudgetExceeded, StalePrices) as error:
        print(f"REFUSING TO START: {error}", file=sys.stderr)
        return EXIT_REFUSED
    except DomainError as error:
        print(f"meter: {error}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
```

- Stores the result of calling `build_chat_model` under the name `model`.
  - `build_chat_model` from the project's `token_meter.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - The method `from_env` of `ModelSettings`.
  - `SystemClock` from the project's `token_meter.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Ends the function and gives back the result of calling `run_command` to the caller.
  - `run_command`, a function of this file (Print the estimate for the pending calls, then make them when a model is given.).
- `except` handler: it runs when the `try` block raised `(ConfigurationError, InvalidPromptSet, UnsupportedParameter)`; `error` names the error object.
- Calls `print` writes text to the screen with 2 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `EXIT_CONFIG` to the caller.
- `except` handler: it runs when the `try` block raised `(BudgetExceeded, StalePrices)`; `error` names the error object.
- Calls `print` writes text to the screen with 2 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `EXIT_REFUSED` to the caller.
- `except` handler: it runs when the `try` block raised the project type `DomainError`; `error` names the error object.
- Calls `print` writes text to the screen with 2 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `EXIT_ERROR` to the caller.
- Decision: the indented lines below run only when `__name__ == '__main__'` is true.
  - `==` means equal.

`src/token_meter/interfaces/cli.py`, lines 133 to 133:

```python
    sys.exit(main())
```

- Calls `sys.exit` from the standard library module `sys` with 1 argument(s); the result is not kept.
  - `sys.exit` from the standard library module `sys`.
  - `main`, a function of this file (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).

### `src/token_meter/interfaces/render.py`

In its own words: "Plain-text rendering of the estimate and the report (what the commands print)."

55 non-blank lines; it defines `render_estimate`, `_by_kind`, `render_report`.

`src/token_meter/interfaces/render.py`, lines 1 to 11:

```python
"""Plain-text rendering of the estimate and the report (what the commands print)."""

from __future__ import annotations

from token_meter.application.report import MeterReport
from token_meter.domain.analysis import EstimateReport
from token_meter.domain.estimation import RunEstimate


def render_estimate(estimate: RunEstimate) -> str:
    """The line printed before the first call."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `MeterReport` (Everything the `report` command prints.) from the project module `token_meter.application.report`.
- Brings in `EstimateReport` (Input-token error by kind and in total, and the largest single gap.) from the project module `token_meter.domain.analysis`.
- Brings in `RunEstimate` (What a run is expected to cost, before the first call.) from the project module `token_meter.domain.estimation`.
- Defines the function `render_estimate`. It returns text. The author's own description: "The line printed before the first call."
- Its parameters:
    - `estimate` holds the project type `RunEstimate`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/token_meter/interfaces/render.py`, lines 12 to 24:

```python
    return (
        f"Estimate before calling: calls={estimate.calls} input_tokens_est={estimate.input_tokens} "
        f"output_tokens_est={estimate.output_tokens} cost_est=${estimate.cost:.4f}"
    )


def _by_kind(title: str, report: EstimateReport) -> list[str]:
    lines = [f"--- {title} ---"]
    lines += [f"{k.kind:<9} est={k.estimated:>6} billed={k.billed:>6} error={k.error:+.1%}" for k in report.by_kind]
    lines.append(
        f"total     est={report.total.estimated:>6} billed={report.total.billed:>6} error={report.total.error:+.1%}"
    )
    gap = report.largest_gap
```

- Ends the function and gives back a text built from pieces (an f-string) to the caller.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the function `_by_kind`. It returns a list of text.
- Its parameters:
    - `title` holds text.
    - `report` holds the project type `EstimateReport`.
- Stores a list of 1 item(s) under the name `lines`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Updates `lines` in place: `+=` applies `+` with a list built by looping and stores the result back.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the `largest_gap` of `report` under the name `gap`.

`src/token_meter/interfaces/render.py`, lines 25 to 38:

```python
    lines.append(
        f"largest gap: {gap.prompt_id} ({gap.kind.value}) est={gap.estimated} billed={gap.billed}; cause: {gap.cause}"
    )
    return lines


def render_report(report: MeterReport) -> str:
    """The report: input-token error by kind at three stages, the cost check and the spread per setting."""
    lines = [f"calls in journal: {report.calls}   total billed cost: ${report.billed_cost_total}", ""]
    lines += _by_kind("1. estimate vs billed input tokens, by kind (t0 only), chars/4 only", report.naive)
    lines += ["", f"measured template overhead: {report.overhead} tokens per call (median of billed - chars/4)", ""]
    lines += _by_kind(f"2. same, with the measured overhead (chars/4 + {report.overhead})", report.with_overhead)
    ratios = ", ".join(f"{kind} {ratio}" for kind, ratio in report.ratios.items())
    lines += ["", f"measured characters per token (all prompts): {ratios}", ""]
```

- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `lines` to the caller.
- Defines the function `render_report`. It returns text. The author's own description: "The report: input-token error by kind at three stages, the cost check and the spread per setting."
- Its parameters:
    - `report` holds the project type `MeterReport`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores a list of 2 item(s) under the name `lines`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Updates `lines` in place: `+=` applies `+` with the result of calling `_by_kind` and stores the result back.
  - `_by_kind`, a function of this file.
- Updates `lines` in place: `+=` applies `+` with a list of 3 item(s) and stores the result back.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Updates `lines` in place: `+=` applies `+` with the result of calling `_by_kind` and stores the result back.
  - `_by_kind`, a function of this file.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of calling `', '.join` under the name `ratios`.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `.items(...)` gives the key and value pairs of a dictionary.
- Updates `lines` in place: `+=` applies `+` with a list of 3 item(s) and stores the result back.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

`src/token_meter/interfaces/render.py`, lines 39 to 52:

```python
    lines += _by_kind("3. leave-one-out: each prompt estimated by an estimator fitted on the others", report.forecast)
    check = report.cost_check
    verdict = "within 5%" if check.within else "NOT within 5%"
    lines += [
        "",
        f"--- cost of all {check.calls} calls, each forecast without its own prompt's data ---",
        f"estimated=${check.estimated:.6f} billed=${check.billed:.6f} error={check.error:+.1%} ({verdict});"
        f" ceiling with every call at the output cap=${check.ceiling:.6f}",
        "",
        "--- spread per setting ---",
        "setting  mean_distinct_answers  label_agreement  mean_output_tokens  length_stops  cost_per_1000_requests",
    ]
    for s in report.spread.settings:
        agreement = "n/a" if s.label_agreement is None else f"{s.label_agreement:.2f}"
```

- Updates `lines` in place: `+=` applies `+` with the result of calling `_by_kind` and stores the result back.
  - `_by_kind`, a function of this file.
- Stores the `cost_check` of `report` under the name `check`.
- Stores one of two values, chosen by a condition under the name `verdict`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
- Updates `lines` in place: `+=` applies `+` with a list of 6 item(s) and stores the result back.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Loop: the indented lines below run once for each item of `report.spread.settings`; `s` names the current item.
- Stores one of two values, chosen by a condition under the name `agreement`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is` means the very same object.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

`src/token_meter/interfaces/render.py`, lines 53 to 63:

```python
        lines.append(
            f"{s.setting:<8} {s.mean_distinct_answers:>21.2f}  {agreement:>15}  {s.mean_output_tokens:>18.1f}"
            f"  {s.length_stop_share:>11.0%}  ${s.cost_per_1000:>21.4f}"
        )
    lines.append("")
    lines.append(
        "temperature 0 gave identical answers on every repeat."
        if report.spread.zero_temperature_identical
        else "temperature 0 did NOT give identical answers on every repeat."
    )
    return "\n".join(lines)
```

- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `A if condition else B` gives A when the condition is true and B otherwise.
- Ends the function and gives back the result of calling `'\n'.join` to the caller.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.

## Try it yourself

1. Every module carries its own description in `__doc__`; this prints the first file's.

```bash
.venv/bin/python -c "import token_meter.interfaces.__init__; print(token_meter.interfaces.__init__.__doc__)"
```

What you should see (captured from this repository):

```text
Command-line programs. They wire adapters into use cases and own exit codes.
```

2. Count the top-level functions and classes in each file of this layer, by reading the code without running it.

```bash
.venv/bin/python - <<'EOF'
import ast, pathlib
files = sorted(pathlib.Path('src/token_meter/interfaces').glob('*.py'))
for f in files:
    tree = ast.parse(f.read_text())
    names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    print(f.name, len(names))
EOF
```

What you should see (captured from this repository):

```text
__init__.py 0
cli.py 6
render.py 3
```

3. The rule that keeps this layer in its place: both contracts must be KEPT.

```bash
.venv/bin/lint-imports --no-logo 2>&1 | grep -E 'KEPT|BROKEN'
```

What you should see (captured from this repository):

```text
Layers: interfaces on infrastructure on application on domain KEPT
Domain and application never import a vendor SDK or an HTTP client KEPT
```

## Mistakes people make

- **Common mistakes with this layer.** Putting rules in the command-line code, forgetting to return the right exit code, or printing instead of returning values so tests cannot check them. Here each command returns an exit code and prints through small render helpers.

## Check yourself

1. What is the job of `src/token_meter/interfaces/__init__.py`?

   *Answer:* Command-line programs. They wire adapters into use cases and own exit codes.

2. What is the job of `src/token_meter/interfaces/cli.py`?

   *Answer:* The `meter` command: estimate, run, report.

3. What is the job of `src/token_meter/interfaces/render.py`?

   *Answer:* Plain-text rendering of the estimate and the report (what the commands print).

4. Which layer is `src/token_meter/interfaces/`, and what may it import?

   *Answer:* The outermost layer; it may import everything below it.

5. Which layer is `src/token_meter/interfaces/`, and what may it import?

   *Answer:* The outermost layer; it may import everything below it.

## Further reading

- Python Language Reference, https://docs.python.org/3.13/reference/ (every statement kind explained here is defined there; the explanations in this note are generated from the code by a program that reads each statement's structure, so they describe what the statement does, not why the author chose it: for the why, read the file's own docstrings, which are quoted).

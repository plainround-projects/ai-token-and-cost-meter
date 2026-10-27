# Python source, the domain layer

## What it is

This note walks through every Python file of the `domain` layer of `token_meter`, line by line. Read `python.md` first for the language features; this note shows them at work.

The **domain** is the core of the program: plain Python objects and functions that hold the rules of the problem (prices, estimates, state changes, validation). It imports nothing from outside the standard library except small helpers, so it can be understood and tested without a network, a database or a web framework.

## Why this repository uses it

The domain is where the project's decisions live, and import-linter forbids it from importing a vendor SDK, an HTTP client, a web framework or a database driver. Reading it first shows what the program *means*; the other layers only connect it to the world.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/token_meter/__init__.py` | 2 non-blank lines |
| `src/token_meter/domain/__init__.py` | 1 non-blank lines |
| `src/token_meter/domain/analysis.py` | 243 non-blank lines |
| `src/token_meter/domain/decoding.py` | 14 non-blank lines |
| `src/token_meter/domain/errors.py` | 14 non-blank lines |
| `src/token_meter/domain/estimation.py` | 54 non-blank lines |
| `src/token_meter/domain/journal.py` | 19 non-blank lines |
| `src/token_meter/domain/llm.py` | 114 non-blank lines |
| `src/token_meter/domain/pricing.py` | 28 non-blank lines |
| `src/token_meter/domain/prompts.py` | 66 non-blank lines |

## How it works underneath

Every file here is a *module*: Python runs it from top to bottom the first time something imports it. Imports come first, then constants, then the definitions (classes and functions). Defining a function or class does not run its body; the body runs when it is called.

How to read the explanations below. Each quoted block is a run of consecutive lines from the file, with its file name and line numbers. Under it, one bullet explains each statement in order, in plain words. A bullet that mentions a function the project defines also gives that function's own description (its docstring). Indented bullets under a statement explain the pieces inside it: calls, comprehensions, comparisons and operators. A `def` bullet lists the parameters; `self` is the object a method works on.

The layering rule that decides what this layer may import is enforced by `import-linter.md`; the file list above is the whole layer.

## Walkthrough of this repository's use

### `src/token_meter/__init__.py`

In its own words: "token_meter: estimate, call, bill and compare, for a batch of model calls."

2 non-blank lines.

`src/token_meter/__init__.py`, lines 1 to 3:

```python
"""token_meter: estimate, call, bill and compare, for a batch of model calls."""

__version__ = "0.1.0"
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `0.1.0` under the name `__version__`.

### `src/token_meter/domain/__init__.py`

In its own words: "Pure domain logic. Depends on nothing outside the standard library."

1 non-blank lines.

`src/token_meter/domain/__init__.py`, lines 1 to 1:

```python
"""Pure domain logic. Depends on nothing outside the standard library."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

### `src/token_meter/domain/analysis.py`

In its own words: "Compare estimates with the bill, calibrate the estimator and measure the spread between answers."

243 non-blank lines; it defines `NotEnoughData`, `KindError`, `PromptGap`, `EstimateReport`, `_first_repeat_rows`, `explain_gap`, `_report`, `compare_estimates`, `calibrate_overhead`, `Calibration`, `calibrate`, `CostCheck`, ....

`src/token_meter/domain/analysis.py`, lines 1 to 14:

```python
"""Compare estimates with the bill, calibrate the estimator and measure the spread between answers."""

from __future__ import annotations

import re
import statistics
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

from token_meter.domain.errors import DomainError
from token_meter.domain.estimation import TokenEstimator
from token_meter.domain.journal import JournalRow
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `re` (standard library) available.
- Makes the module `statistics` (standard library) available.
- Brings in `Counter`, `defaultdict` from the standard library module `collections`.
- Brings in `Mapping`, `Sequence` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `Decimal` from the standard library module `decimal`.
- Brings in `DomainError` (Base class for every error this package raises on purpose.) from the project module `token_meter.domain.errors`.
- Brings in `TokenEstimator` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.) from the project module `token_meter.domain.estimation`.
- Brings in `JournalRow` (What one call cost and returned, as billed by the provider.) from the project module `token_meter.domain.journal`.

`src/token_meter/domain/analysis.py`, lines 15 to 28:

```python
from token_meter.domain.llm import StopReason
from token_meter.domain.pricing import PriceTable
from token_meter.domain.prompts import LABELS, Kind, PromptRecord

_WORD = re.compile(r"[a-z]+")


class NotEnoughData(DomainError):
    """The journal does not hold the rows the analysis needs."""


@dataclass(frozen=True, slots=True)
class KindError:
    """Estimated against billed input tokens for one kind of prompt. `error` is (estimated - billed) / billed."""
```

- Brings in `StopReason` (Why the model stopped writing.) from the project module `token_meter.domain.llm`.
- Brings in `PriceTable` (Price per 1,000 input and output tokens, with the day the numbers were read.) from the project module `token_meter.domain.pricing`.
- Brings in `LABELS`, `Kind` (What a prompt is for; the report breaks every number out by kind.), `PromptRecord` (One prompt. `expected_label` is set only for label prompts.) from the project module `token_meter.domain.prompts`.
- Stores the result of calling `re.compile` under the name `_WORD`.
  - `re.compile` prepares a regular expression.
- Defines the class `NotEnoughData`. It builds on the project's `DomainError` (Base class for every error this package raises on purpose.). The author's own description: "The journal does not hold the rows the analysis needs."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `KindError`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Estimated against billed input tokens for one kind of prompt. `error` is (estimated - billed) / billed."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/token_meter/domain/analysis.py`, lines 30 to 41:

```python
    kind: str
    estimated: int
    billed: int

    @property
    def error(self) -> float:
        return (self.estimated - self.billed) / self.billed if self.billed else 0.0


@dataclass(frozen=True, slots=True)
class PromptGap:
    """The prompt whose estimate is furthest from the bill, with the cause the numbers point to."""
```

- Declares `kind` as text; it has no default, so a value must be given when the object is made.
- Declares `estimated` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `billed` as a whole number; it has no default, so a value must be given when the object is made.
- Defines the method `error`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `/` is divide.
  - `-` is subtract.
- Defines the class `PromptGap`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "The prompt whose estimate is furthest from the bill, with the cause the numbers point to."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/token_meter/domain/analysis.py`, lines 43 to 55:

```python
    prompt_id: str
    kind: Kind
    estimated: int
    billed: int
    cause: str


@dataclass(frozen=True, slots=True)
class EstimateReport:
    """Input-token error by kind and in total, and the largest single gap."""

    by_kind: tuple[KindError, ...]
    total: KindError
```

- Declares `prompt_id` as text; it has no default, so a value must be given when the object is made.
- Declares `kind` as the project type `Kind`; it has no default, so a value must be given when the object is made.
- Declares `estimated` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `billed` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `cause` as text; it has no default, so a value must be given when the object is made.
- Defines the class `EstimateReport`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Input-token error by kind and in total, and the largest single gap."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `by_kind` as a fixed list of the project type `KindError` (any length); it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `total` as the project type `KindError`; it has no default, so a value must be given when the object is made.

`src/token_meter/domain/analysis.py`, lines 56 to 67:

```python
    largest_gap: PromptGap


def _first_repeat_rows(rows: Sequence[JournalRow], setting: str) -> dict[str, JournalRow]:
    chosen: dict[str, JournalRow] = {}
    for row in rows:
        if row.key.setting == setting and row.key.repeat == 0:
            chosen[row.key.prompt_id] = row
    return chosen


def explain_gap(kind: Kind, estimated: int, billed: int, missing_overhead: int) -> str:
```

- Declares `largest_gap` as the project type `PromptGap`; it has no default, so a value must be given when the object is made.
- Defines the function `_first_repeat_rows`. It returns a dictionary from text to the project type `JournalRow`.
- Its parameters:
    - `rows` holds anything that behaves like a list of the project type `JournalRow`.
    - `setting` holds text.
- Declares `chosen` as a dictionary from text to the project type `JournalRow` and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `rows`; `row` names the current item.
- Decision: the indented lines below run only when `row.key.setting == setting and row.key.repeat == 0` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `==` means equal.
- Stores the value named `row` under the name `chosen[row.key.prompt_id]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Ends the function and gives back the value named `chosen` to the caller.
- Defines the function `explain_gap`. It returns text. The author's own description: "Name the cause of a gap from its size."
- Its parameters:
    - `kind` holds the project type `Kind`.
    - `estimated` holds a whole number.
    - `billed` holds a whole number.
    - `missing_overhead` holds a whole number.

`src/token_meter/domain/analysis.py`, lines 68 to 81:

```python
    """Name the cause of a gap from its size.

    `missing_overhead` is the fixed per-call cost the estimate does not include yet (zero once it does).
    """
    shortfall = billed - estimated
    if missing_overhead and shortfall <= missing_overhead * 1.25 + 8:
        return "fixed chat-template overhead per call, which dominates short prompts"
    if shortfall < 0:
        return "the estimate is above the bill: this text tokenizes more compactly than the rule assumes"
    if kind is Kind.LANGUAGE:
        return "non-English text splits into more tokens per character than the characters-per-token rule assumes"
    if kind is Kind.CODE:
        return "code, JSON and symbols split into more tokens per character than prose does"
    if kind in (Kind.SHORT, Kind.LABEL):
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of `billed - estimated` under the name `shortfall`.
  - `-` is subtract.
- Decision: the indented lines below run only when `missing_overhead and shortfall <= missing_overhead * 1.25 + 8` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `<=` means less than or equal.
  - `+` is add.
  - `*` is multiply.
- Ends the function and gives back the text `fixed chat-template overhead per call, which do...` to the caller.
- Decision: the indented lines below run only when `shortfall < 0` is true.
  - `<` means less than.
- Ends the function and gives back the text `the estimate is above the bill: this text token...` to the caller.
- Decision: the indented lines below run only when `kind is Kind.LANGUAGE` is true.
  - `is` means the very same object.
- Ends the function and gives back the text `non-English text splits into more tokens per ch...` to the caller.
- Decision: the indented lines below run only when `kind is Kind.CODE` is true.
  - `is` means the very same object.
- Ends the function and gives back the text `code, JSON and symbols split into more tokens p...` to the caller.
- Decision: the indented lines below run only when `kind in (Kind.SHORT, Kind.LABEL)` is true.
  - `in` means is contained in.

`src/token_meter/domain/analysis.py`, lines 82 to 95:

```python
        return "rounding of the characters-per-token rule on very short text"
    return "text that tokenizes less compactly than the characters-per-token rule assumes"


def _report(
    prompts: Sequence[PromptRecord], billed_rows: Mapping[str, JournalRow], estimates: Mapping[str, int], missing: int
) -> EstimateReport:
    totals: dict[Kind, list[int]] = defaultdict(lambda: [0, 0])
    gaps: list[PromptGap] = []
    for prompt in prompts:
        row = billed_rows.get(prompt.id)
        if row is None:
            continue
        estimated = estimates[prompt.id]
```

- Ends the function and gives back the text `rounding of the characters-per-token rule on ve...` to the caller.
- Ends the function and gives back the text `text that tokenizes less compactly than the cha...` to the caller.
- Defines the function `_report`. It returns the project type `EstimateReport`.
- Its parameters:
    - `prompts` holds anything that behaves like a list of the project type `PromptRecord`.
    - `billed_rows` holds anything that behaves like a dictionary from text to the project type `JournalRow`.
    - `estimates` holds anything that behaves like a dictionary from text to a whole number.
    - `missing` holds a whole number.
- Declares `totals` as a dictionary from the project type `Kind` to a list of a whole number and sets it to the result of calling `defaultdict`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `defaultdict` from the standard library module `collections`.
  - `lambda args: expression` is a small unnamed function written inline.
- Declares `gaps` as a list of the project type `PromptGap` and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `prompts`; `prompt` names the current item.
- Stores the result of calling `billed_rows.get` under the name `row`.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Decision: the indented lines below run only when `row is None` is true.
  - `is` means the very same object.
- Skips the rest of this round of the loop and starts the next.
- Stores the part of `estimates` picked by `prompt.id` under the name `estimated`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/token_meter/domain/analysis.py`, lines 96 to 103:

```python
        totals[prompt.kind][0] += estimated
        totals[prompt.kind][1] += row.input_tokens
        cause = explain_gap(prompt.kind, estimated, row.input_tokens, missing)
        gaps.append(PromptGap(prompt.id, prompt.kind, estimated, row.input_tokens, cause))
    by_kind = tuple(KindError(kind.value, est, bill) for kind, (est, bill) in totals.items())
    total = KindError("total", sum(k.estimated for k in by_kind), sum(k.billed for k in by_kind))
    worst = max(gaps, key=lambda g: abs(g.billed - g.estimated) / g.billed)
    return EstimateReport(by_kind, total, worst)
```

- Updates `totals[prompt.kind][0]` in place: `+=` applies `+` with the value named `estimated` and stores the result back.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Updates `totals[prompt.kind][1]` in place: `+=` applies `+` with the `input_tokens` of `row` and stores the result back.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `explain_gap` under the name `cause`.
  - `explain_gap`, a function of this file (Name the cause of a gap from its size.).
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `PromptGap`, a class of this project (The prompt whose estimate is furthest from the bill, with the cause the numbers point to.).
- Stores the result of calling `tuple` under the name `by_kind`.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `KindError`, a class of this project (Estimated against billed input tokens for one kind of prompt. `error` is (estimated - billed) / billed.).
  - `.items(...)` gives the key and value pairs of a dictionary.
- Stores the result of calling `KindError` under the name `total`.
  - `KindError`, a class of this project (Estimated against billed input tokens for one kind of prompt. `error` is (estimated - billed) / billed.).
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Stores the result of calling `max` under the name `worst`.
  - `max` picks the largest value.
  - `lambda args: expression` is a small unnamed function written inline.
  - `/` is divide.
  - `abs` gives the absolute value (the number without its sign).
  - `-` is subtract.
- Ends the function and gives back the result of calling `EstimateReport` to the caller.
  - `EstimateReport`, a class of this project (Input-token error by kind and in total, and the largest single gap.).

`src/token_meter/domain/analysis.py`, lines 106 to 117:

```python
def compare_estimates(
    prompts: Sequence[PromptRecord],
    rows: Sequence[JournalRow],
    estimator: TokenEstimator,
    setting: str = "t0",
    known_overhead: int = 0,
) -> EstimateReport:
    """Join estimates to billed input tokens (one row per prompt at `setting`) and group by kind.

    `known_overhead` is the measured per-call overhead; it lets the report explain a gap that the estimator,
    which does not include the overhead yet, leaves open.
    """
```

- Defines the function `compare_estimates`. It returns the project type `EstimateReport`. The author's own description: "Join estimates to billed input tokens (one row per prompt at `setting`) and group by kind."
- Its parameters:
    - `prompts` holds anything that behaves like a list of the project type `PromptRecord`.
    - `rows` holds anything that behaves like a list of the project type `JournalRow`.
    - `estimator` holds the project type `TokenEstimator`.
    - `setting` holds text; if the caller leaves it out it is the text `t0`.
    - `known_overhead` holds a whole number; if the caller leaves it out it is the number `0`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/token_meter/domain/analysis.py`, lines 118 to 129:

```python
    billed_rows = _first_repeat_rows(rows, setting)
    if not billed_rows:
        raise NotEnoughData(f"no rows for setting {setting!r} in the journal")
    estimates = {p.id: estimator.tokens(p.text, kind=p.kind) for p in prompts}
    return _report(prompts, billed_rows, estimates, 0 if estimator.per_call_overhead else known_overhead)


def calibrate_overhead(
    prompts: Sequence[PromptRecord], rows: Sequence[JournalRow], base: TokenEstimator, setting: str = "t0"
) -> int:
    """The median of billed minus estimated input tokens: the fixed cost every call carries."""
    billed_rows = _first_repeat_rows(rows, setting)
```

- Stores the result of calling `_first_repeat_rows` under the name `billed_rows`.
  - `_first_repeat_rows`, a function of this file.
- Decision: the indented lines below run only when `not billed_rows` is true.
  - `not` flips true and false.
- Raises an error: the result of calling `NotEnoughData`. Execution jumps out to the nearest matching `except`.
  - `NotEnoughData`, a class of this project (The journal does not hold the rows the analysis needs.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores a dictionary built by looping under the name `estimates`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `tokens` of the project's `TokenEstimator` (Estimated input tokens of one call that sends `text` (and `system`).).
- Ends the function and gives back the result of calling `_report` to the caller.
  - `_report`, a function of this file.
  - `A if condition else B` gives A when the condition is true and B otherwise.
- Defines the function `calibrate_overhead`. It returns a whole number. The author's own description: "The median of billed minus estimated input tokens: the fixed cost every call carries."
- Its parameters:
    - `prompts` holds anything that behaves like a list of the project type `PromptRecord`.
    - `rows` holds anything that behaves like a list of the project type `JournalRow`.
    - `base` holds the project type `TokenEstimator`.
    - `setting` holds text; if the caller leaves it out it is the text `t0`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `_first_repeat_rows` under the name `billed_rows`.
  - `_first_repeat_rows`, a function of this file.

`src/token_meter/domain/analysis.py`, lines 130 to 142:

```python
    residuals = [
        billed_rows[p.id].input_tokens - base.with_overhead(0).tokens(p.text, kind=p.kind)
        for p in prompts
        if p.id in billed_rows
    ]
    if not residuals:
        raise NotEnoughData(f"no rows for setting {setting!r} in the journal")
    return round(statistics.median(residuals))


@dataclass(frozen=True, slots=True)
class Calibration:
    """What a pilot taught the estimator: overhead, a density per kind, and answer length per kind and setting."""
```

- Stores a list built by looping under the name `residuals`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `-` is subtract.
  - The method `tokens` of the project's `TokenEstimator` (Estimated input tokens of one call that sends `text` (and `system`).).
  - `in` means is contained in.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - The method `with_overhead` of the project's `TokenEstimator` (The same ratios with a different fixed overhead.).
- Decision: the indented lines below run only when `not residuals` is true.
  - `not` flips true and false.
- Raises an error: the result of calling `NotEnoughData`. Execution jumps out to the nearest matching `except`.
  - `NotEnoughData`, a class of this project (The journal does not hold the rows the analysis needs.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the result of calling `round` to the caller.
  - `round` rounds a number.
  - `statistics.median` the middle value.
- Defines the class `Calibration`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "What a pilot taught the estimator: overhead, a density per kind, and answer length per kind and setting."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/token_meter/domain/analysis.py`, lines 144 to 156:

```python
    estimator: TokenEstimator
    mean_output: Mapping[tuple[Kind, str], float]


def calibrate(
    prompts: Sequence[PromptRecord], rows: Sequence[JournalRow], base: TokenEstimator, setting: str = "t0"
) -> Calibration:
    """Measure the overhead, the characters per token of each kind and the mean answer length per kind and setting."""
    overhead = calibrate_overhead(prompts, rows, base, setting)
    billed_rows = _first_repeat_rows(rows, setting)
    chars: dict[Kind, int] = defaultdict(int)
    tokens: dict[Kind, int] = defaultdict(int)
    for prompt in prompts:
```

- Declares `estimator` as the project type `TokenEstimator`; it has no default, so a value must be given when the object is made.
- Declares `mean_output` as anything that behaves like a dictionary from a fixed list of the project type `Kind`, text to a decimal number; it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the function `calibrate`. It returns the project type `Calibration`. The author's own description: "Measure the overhead, the characters per token of each kind and the mean answer length per kind and setting."
- Its parameters:
    - `prompts` holds anything that behaves like a list of the project type `PromptRecord`.
    - `rows` holds anything that behaves like a list of the project type `JournalRow`.
    - `base` holds the project type `TokenEstimator`.
    - `setting` holds text; if the caller leaves it out it is the text `t0`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `calibrate_overhead` under the name `overhead`.
  - `calibrate_overhead`, a function of this file (The median of billed minus estimated input tokens: the fixed cost every call carries.).
- Stores the result of calling `_first_repeat_rows` under the name `billed_rows`.
  - `_first_repeat_rows`, a function of this file.
- Declares `chars` as a dictionary from the project type `Kind` to a whole number and sets it to the result of calling `defaultdict`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `defaultdict` from the standard library module `collections`.
- Declares `tokens` as a dictionary from the project type `Kind` to a whole number and sets it to the result of calling `defaultdict`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `defaultdict` from the standard library module `collections`.
- Loop: the indented lines below run once for each item of `prompts`; `prompt` names the current item.

`src/token_meter/domain/analysis.py`, lines 157 to 170:

```python
        if prompt.id in billed_rows:
            chars[prompt.kind] += len(prompt.text)
            tokens[prompt.kind] += max(1, billed_rows[prompt.id].input_tokens - overhead)
    kind_of = {p.id: p.kind for p in prompts}
    outputs: dict[tuple[Kind, str], list[int]] = defaultdict(list)
    for row in rows:
        if row.key.prompt_id in kind_of:
            outputs[(kind_of[row.key.prompt_id], row.key.setting)].append(row.output_tokens)
    estimator = base.with_overhead(overhead).with_ratios({kind: chars[kind] / tokens[kind] for kind in chars})
    return Calibration(estimator, {key: statistics.fmean(values) for key, values in outputs.items()})


@dataclass(frozen=True, slots=True)
class CostCheck:
```

- Decision: the indented lines below run only when `prompt.id in billed_rows` is true.
  - `in` means is contained in.
- Updates `chars[prompt.kind]` in place: `+=` applies `+` with the result of calling `len` and stores the result back.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `len` counts the items in a collection (or the characters in text).
- Updates `tokens[prompt.kind]` in place: `+=` applies `+` with the result of calling `max` and stores the result back.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `max` picks the largest value.
  - `-` is subtract.
- Stores a dictionary built by looping under the name `kind_of`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Declares `outputs` as a dictionary from a fixed list of the project type `Kind`, text to a list of a whole number and sets it to the result of calling `defaultdict`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `defaultdict` from the standard library module `collections`.
- Loop: the indented lines below run once for each item of `rows`; `row` names the current item.
- Decision: the indented lines below run only when `row.key.prompt_id in kind_of` is true.
  - `in` means is contained in.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `base.with_overhead(overhead).with_ratios` under the name `estimator`.
  - The method `with_ratios` of the project's `TokenEstimator` (The same overhead with measured characters-per-token ratios per kind.).
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `with_overhead` of the project's `TokenEstimator` (The same ratios with a different fixed overhead.).
  - `/` is divide.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Ends the function and gives back the result of calling `Calibration` to the caller.
  - `Calibration`, a class of this project (What a pilot taught the estimator: overhead, a density per kind, and answer length per kind and setting.).
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `statistics.fmean` from the standard library module `statistics`.
  - `.items(...)` gives the key and value pairs of a dictionary.
- Defines the class `CostCheck`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "A calibrated cost estimate against the bill, made without the answer it is judged on."

`src/token_meter/domain/analysis.py`, lines 171 to 184:

```python
    """A calibrated cost estimate against the bill, made without the answer it is judged on."""

    calls: int
    estimated: Decimal
    billed: Decimal
    ceiling: Decimal

    @property
    def error(self) -> float:
        return float((self.estimated - self.billed) / self.billed) if self.billed else 0.0

    @property
    def within(self) -> bool:
        return abs(self.error) <= 0.05
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `calls` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `estimated` as an exact decimal number; it has no default, so a value must be given when the object is made.
- Declares `billed` as an exact decimal number; it has no default, so a value must be given when the object is made.
- Declares `ceiling` as an exact decimal number; it has no default, so a value must be given when the object is made.
- Defines the method `error`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `float` turns a value into a decimal number.
  - `/` is divide.
  - `-` is subtract.
- Defines the method `within`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back whether `abs(self.error) <= 0.05` holds to the caller.
  - `<=` means less than or equal.
  - `abs` gives the absolute value (the number without its sign).

`src/token_meter/domain/analysis.py`, lines 187 to 198:

```python
@dataclass(frozen=True, slots=True)
class LeaveOneOut:
    """Each prompt estimated by an estimator calibrated on the other prompts: input tokens by kind, and cost."""

    input_tokens: EstimateReport
    cost: CostCheck


def _expected_output(calibration: Calibration, kind: Kind, setting: str) -> float:
    """Mean answer length for the kind and setting; the setting's mean over all kinds if the kind was never seen."""
    known = calibration.mean_output.get((kind, setting))
    if known is not None:
```

- Defines the class `LeaveOneOut`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Each prompt estimated by an estimator calibrated on the other prompts: input tokens by kind, and cost."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `input_tokens` as the project type `EstimateReport`; it has no default, so a value must be given when the object is made.
- Declares `cost` as the project type `CostCheck`; it has no default, so a value must be given when the object is made.
- Defines the function `_expected_output`. It returns a decimal number. The author's own description: "Mean answer length for the kind and setting; the setting's mean over all kinds if the kind was never seen."
- Its parameters:
    - `calibration` holds the project type `Calibration`.
    - `kind` holds the project type `Kind`.
    - `setting` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `calibration.mean_output.get` under the name `known`.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Decision: the indented lines below run only when `known is not None` is true.
  - `is not` means not the same object.

`src/token_meter/domain/analysis.py`, lines 199 to 211:

```python
        return known
    same_setting = [v for (_, name), v in calibration.mean_output.items() if name == setting]
    return statistics.fmean(same_setting) if same_setting else 0.0


def leave_one_out(
    prompts: Sequence[PromptRecord],
    rows: Sequence[JournalRow],
    base: TokenEstimator,
    prices: PriceTable,
    max_output_tokens: int,
    setting: str = "t0",
) -> LeaveOneOut:
```

- Ends the function and gives back the value named `known` to the caller.
- Stores a list built by looping under the name `same_setting`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.items(...)` gives the key and value pairs of a dictionary.
  - `==` means equal.
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `statistics.fmean` from the standard library module `statistics`.
- Defines the function `leave_one_out`. It returns the project type `LeaveOneOut`. The author's own description: "Estimate every prompt with an estimator that never saw it, so the error is an honest forecast error."
- Its parameters:
    - `prompts` holds anything that behaves like a list of the project type `PromptRecord`.
    - `rows` holds anything that behaves like a list of the project type `JournalRow`.
    - `base` holds the project type `TokenEstimator`.
    - `prices` holds the project type `PriceTable`.
    - `max_output_tokens` holds a whole number.
    - `setting` holds text; if the caller leaves it out it is the text `t0`.

`src/token_meter/domain/analysis.py`, lines 212 to 225:

```python
    """Estimate every prompt with an estimator that never saw it, so the error is an honest forecast error.

    Input uses the calibrated overhead and the density of the prompt's kind. Output uses the mean billed answer
    length of the same kind and setting. `ceiling` assumes every call fills the output cap, which is all the
    pre-run estimate can assume.
    """
    if len(prompts) < 2:
        raise NotEnoughData("leave-one-out needs at least two prompts")
    billed_rows = _first_repeat_rows(rows, setting)
    by_prompt: dict[str, list[JournalRow]] = defaultdict(list)
    for row in rows:
        by_prompt[row.key.prompt_id].append(row)
    estimates: dict[str, int] = {}
    estimated = billed = ceiling = Decimal(0)
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Decision: the indented lines below run only when `len(prompts) < 2` is true.
  - `<` means less than.
  - `len` counts the items in a collection (or the characters in text).
- Raises an error: the result of calling `NotEnoughData`. Execution jumps out to the nearest matching `except`.
  - `NotEnoughData`, a class of this project (The journal does not hold the rows the analysis needs.).
- Stores the result of calling `_first_repeat_rows` under the name `billed_rows`.
  - `_first_repeat_rows`, a function of this file.
- Declares `by_prompt` as a dictionary from text to a list of the project type `JournalRow` and sets it to the result of calling `defaultdict`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `defaultdict` from the standard library module `collections`.
- Loop: the indented lines below run once for each item of `rows`; `row` names the current item.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `estimates` as a dictionary from text to a whole number and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `Decimal` under the name `estimated`, `billed`, `ceiling`.
  - `Decimal` from the standard library module `decimal`.

`src/token_meter/domain/analysis.py`, lines 226 to 239:

```python
    calls = 0
    for prompt in prompts:
        if prompt.id not in by_prompt:
            continue
        calibration = calibrate([q for q in prompts if q.id != prompt.id], rows, base, setting)
        input_estimate = calibration.estimator.tokens(prompt.text, kind=prompt.kind)
        estimates[prompt.id] = input_estimate
        for row in by_prompt[prompt.id]:
            calls += 1
            expected_output = _expected_output(calibration, prompt.kind, row.key.setting)
            estimated += prices.cost(input_estimate, round(expected_output))
            ceiling += prices.cost(input_estimate, max_output_tokens)
            billed += prices.cost(row.input_tokens, row.output_tokens)
    covered = [p for p in prompts if p.id in estimates]
```

- Stores the number `0` under the name `calls`.
- Loop: the indented lines below run once for each item of `prompts`; `prompt` names the current item.
- Decision: the indented lines below run only when `prompt.id not in by_prompt` is true.
  - `not in` means is not contained in.
- Skips the rest of this round of the loop and starts the next.
- Stores the result of calling `calibrate` under the name `calibration`.
  - `calibrate`, a function of this file (Measure the overhead, the characters per token of each kind and the mean answer length per kind and setting.).
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `!=` means not equal.
- Stores the result of calling `calibration.estimator.tokens` under the name `input_estimate`.
  - The method `tokens` of the project's `TokenEstimator` (Estimated input tokens of one call that sends `text` (and `system`).).
- Stores the value named `input_estimate` under the name `estimates[prompt.id]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `by_prompt[prompt.id]`; `row` names the current item.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Updates `calls` in place: `+=` applies `+` with the number `1` and stores the result back.
- Stores the result of calling `_expected_output` under the name `expected_output`.
  - `_expected_output`, a function of this file (Mean answer length for the kind and setting; the setting's mean over all kinds if the kind was never seen.).
- Updates `estimated` in place: `+=` applies `+` with the result of calling `prices.cost` and stores the result back.
  - The method `cost` of the project's `PriceTable` (Cost in dollars of a call with these token counts.).
  - `round` rounds a number.
- Updates `ceiling` in place: `+=` applies `+` with the result of calling `prices.cost` and stores the result back.
  - The method `cost` of the project's `PriceTable` (Cost in dollars of a call with these token counts.).
- Updates `billed` in place: `+=` applies `+` with the result of calling `prices.cost` and stores the result back.
  - The method `cost` of the project's `PriceTable` (Cost in dollars of a call with these token counts.).
- Stores a list built by looping under the name `covered`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `in` means is contained in.

`src/token_meter/domain/analysis.py`, lines 240 to 252:

```python
    return LeaveOneOut(_report(covered, billed_rows, estimates, 0), CostCheck(calls, estimated, billed, ceiling))


@dataclass(frozen=True, slots=True)
class SettingSpread:
    """How much answers vary at one decoding setting, and what that costs."""

    setting: str
    mean_distinct_answers: float
    label_agreement: float | None
    mean_output_tokens: float
    cost_per_1000: Decimal
    length_stop_share: float
```

- Ends the function and gives back the result of calling `LeaveOneOut` to the caller.
  - `LeaveOneOut`, a class of this project (Each prompt estimated by an estimator calibrated on the other prompts: input tokens by kind, and cost.).
  - `_report`, a function of this file.
  - `CostCheck`, a class of this project (A calibrated cost estimate against the bill, made without the answer it is judged on.).
- Defines the class `SettingSpread`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "How much answers vary at one decoding setting, and what that costs."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `setting` as text; it has no default, so a value must be given when the object is made.
- Declares `mean_distinct_answers` as a decimal number; it has no default, so a value must be given when the object is made.
- Declares `label_agreement` as a decimal number, or nothing (None); it has no default, so a value must be given when the object is made.
  - `|` is or; in a type, "either".
- Declares `mean_output_tokens` as a decimal number; it has no default, so a value must be given when the object is made.
- Declares `cost_per_1000` as an exact decimal number; it has no default, so a value must be given when the object is made.
- Declares `length_stop_share` as a decimal number; it has no default, so a value must be given when the object is made.

`src/token_meter/domain/analysis.py`, lines 255 to 266:

```python
@dataclass(frozen=True, slots=True)
class SpreadReport:
    """One row per setting, and whether the first setting (temperature 0) repeated itself exactly."""

    settings: tuple[SettingSpread, ...]
    zero_temperature_identical: bool


def extract_label(answer: str) -> str:
    """The first category word in an answer, or `none` when it names no category."""
    for match in _WORD.finditer(answer.lower()):
        if match.group() in LABELS:
```

- Defines the class `SpreadReport`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "One row per setting, and whether the first setting (temperature 0) repeated itself exactly."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `settings` as a fixed list of the project type `SettingSpread` (any length); it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `zero_temperature_identical` as true or false; it has no default, so a value must be given when the object is made.
- Defines the function `extract_label`. It returns text. The author's own description: "The first category word in an answer, or `none` when it names no category."
- Its parameters:
    - `answer` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Loop: the indented lines below run once for each item of `_WORD.finditer(answer.lower())`; `match` names the current item.
  - `.finditer(...)` yields every match of a regular expression.
  - `.lower(...)` turns text into lower case.
- Decision: the indented lines below run only when `match.group() in LABELS` is true.
  - `in` means is contained in.
  - `.group(...)` reads a captured part of a regular-expression match.

`src/token_meter/domain/analysis.py`, lines 267 to 280:

```python
            return match.group()
    return "none"


def measure_spread(prompts: Sequence[PromptRecord], rows: Sequence[JournalRow], prices: PriceTable) -> SpreadReport:
    """Count distinct answers per prompt and setting, label agreement, output length and cost per 1,000 calls."""
    label_ids = {p.id for p in prompts if p.kind is Kind.LABEL}
    grouped: dict[str, dict[str, list[JournalRow]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[row.key.setting][row.key.prompt_id].append(row)
    if not grouped:
        raise NotEnoughData("the journal is empty")
    spreads: list[SettingSpread] = []
    for setting, by_prompt in grouped.items():
```

- Ends the function and gives back the result of calling `match.group` to the caller.
  - `.group(...)` reads a captured part of a regular-expression match.
- Ends the function and gives back the text `none` to the caller.
- Defines the function `measure_spread`. It returns the project type `SpreadReport`. The author's own description: "Count distinct answers per prompt and setting, label agreement, output length and cost per 1,000 calls."
- Its parameters:
    - `prompts` holds anything that behaves like a list of the project type `PromptRecord`.
    - `rows` holds anything that behaves like a list of the project type `JournalRow`.
    - `prices` holds the project type `PriceTable`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores a set built by looping under the name `label_ids`.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `is` means the very same object.
- Declares `grouped` as a dictionary from text to a dictionary from text to a list of the project type `JournalRow` and sets it to the result of calling `defaultdict`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `defaultdict` from the standard library module `collections`.
  - `lambda args: expression` is a small unnamed function written inline.
- Loop: the indented lines below run once for each item of `rows`; `row` names the current item.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `not grouped` is true.
  - `not` flips true and false.
- Raises an error: the result of calling `NotEnoughData`. Execution jumps out to the nearest matching `except`.
  - `NotEnoughData`, a class of this project (The journal does not hold the rows the analysis needs.).
- Declares `spreads` as a list of the project type `SettingSpread` and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `grouped.items()`; `(setting, by_prompt)` names the current item.
  - `.items(...)` gives the key and value pairs of a dictionary.

`src/token_meter/domain/analysis.py`, lines 281 to 287:

```python
        distinct = [len({r.text.strip() for r in group}) for group in by_prompt.values()]
        agreements = []
        for prompt_id in label_ids & by_prompt.keys():
            labels = Counter(extract_label(r.text) for r in by_prompt[prompt_id])
            agreements.append(labels.most_common(1)[0][1] / sum(labels.values()))
        all_rows = [r for group in by_prompt.values() for r in group]
        costs = [prices.cost(r.input_tokens, r.output_tokens) for r in all_rows]
```

- Stores a list built by looping under the name `distinct`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `len` counts the items in a collection (or the characters in text).
  - `.values(...)` gives the values of a dictionary.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
- Stores an empty list under the name `agreements`.
- Loop: the indented lines below run once for each item of `label_ids & by_prompt.keys()`; `prompt_id` names the current item.
  - `&` is and.
  - `.keys(...)` gives the keys of a dictionary.
- Stores the result of calling `Counter` under the name `labels`.
  - `Counter` from the standard library module `collections`.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `extract_label`, a function of this file (The first category word in an answer, or `none` when it names no category.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `/` is divide.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `sum` adds up all the numbers.
  - `.values(...)` gives the values of a dictionary.
  - `.most_common(...)` lists the most frequent items with their counts.
- Stores a list built by looping under the name `all_rows`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.values(...)` gives the values of a dictionary.
- Stores a list built by looping under the name `costs`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `cost` of the project's `PriceTable` (Cost in dollars of a call with these token counts.).

`src/token_meter/domain/analysis.py`, lines 288 to 299:

```python
        spreads.append(
            SettingSpread(
                setting,
                statistics.fmean(distinct),
                statistics.fmean(agreements) if agreements else None,
                statistics.fmean(r.output_tokens for r in all_rows),
                (sum(costs, Decimal(0)) / len(costs)) * 1000,
                sum(r.stop_reason is StopReason.LENGTH for r in all_rows) / len(all_rows),
            )
        )
    zero = next((s for s in spreads if s.setting == "t0"), None)
    return SpreadReport(tuple(spreads), zero is not None and zero.mean_distinct_answers == 1.0)
```

- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `SettingSpread`, a class of this project (How much answers vary at one decoding setting, and what that costs.).
  - `statistics.fmean` from the standard library module `statistics`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `*` is multiply.
  - `/` is divide.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `sum` adds up all the numbers.
  - `len` counts the items in a collection (or the characters in text).
  - `Decimal` from the standard library module `decimal`.
  - `is` means the very same object.
- Stores the result of calling `next` under the name `zero`.
  - `next` takes the next item from an iterator.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `==` means equal.
- Ends the function and gives back the result of calling `SpreadReport` to the caller.
  - `SpreadReport`, a class of this project (One row per setting, and whether the first setting (temperature 0) repeated itself exactly.).
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is not` means not the same object.
  - `==` means equal.

### `src/token_meter/domain/decoding.py`

In its own words: "The decoding settings the meter compares."

14 non-blank lines; it defines `DecodingSetting`.

`src/token_meter/domain/decoding.py`, lines 1 to 14:

```python
"""The decoding settings the meter compares."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DecodingSetting:
    """A named sampling configuration. `top_p` is None when it is left at the provider default."""

    name: str
    temperature: float
    top_p: float | None = None
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Defines the class `DecodingSetting`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "A named sampling configuration. `top_p` is None when it is left at the provider default."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `name` as text; it has no default, so a value must be given when the object is made.
- Declares `temperature` as a decimal number; it has no default, so a value must be given when the object is made.
- Declares `top_p` as a decimal number, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".

`src/token_meter/domain/decoding.py`, lines 17 to 21:

```python
DEFAULT_SETTINGS = (
    DecodingSetting("t0", 0.0),
    DecodingSetting("t07", 0.7),
    DecodingSetting("t10", 1.0, 0.9),
)
```

- Stores a tuple of 3 item(s) under the name `DEFAULT_SETTINGS`.
  - `DecodingSetting`, a class of this project (A named sampling configuration. `top_p` is None when it is left at the provider default.).

### `src/token_meter/domain/errors.py`

In its own words: "Named errors. Callers catch these, never a vendor SDK's exception types."

14 non-blank lines; it defines `DomainError`, `ModelError`, `TransientModelError`, `PermanentModelError`, `RecordingMissing`, `UnsupportedParameter`.

`src/token_meter/domain/errors.py`, lines 1 to 14:

```python
"""Named errors. Callers catch these, never a vendor SDK's exception types."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for every error this package raises on purpose."""


class ModelError(DomainError):
    """A model call failed."""


class TransientModelError(ModelError):
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Defines the class `DomainError`. It builds on `Exception` (the base of ordinary errors). The author's own description: "Base class for every error this package raises on purpose."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `ModelError`. It builds on the project's `DomainError` (Base class for every error this package raises on purpose.). The author's own description: "A model call failed."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `TransientModelError`. It builds on the project's `ModelError` (A model call failed.). The author's own description: "The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection."

`src/token_meter/domain/errors.py`, lines 15 to 27:

```python
    """The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection."""


class PermanentModelError(ModelError):
    """Repeating the call cannot help: a bad request, a bad key, a refusal to parse."""


class RecordingMissing(PermanentModelError):
    """The recorded adapter has no response for this request. Re-record with `make record`."""


class UnsupportedParameter(PermanentModelError):
    """The adapter cannot honor a parameter the request asked for (for example sampling on Claude)."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `PermanentModelError`. It builds on the project's `ModelError` (A model call failed.). The author's own description: "Repeating the call cannot help: a bad request, a bad key, a refusal to parse."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `RecordingMissing`. It builds on the project's `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.). The author's own description: "The recorded adapter has no response for this request. Re-record with `make record`."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `UnsupportedParameter`. It builds on the project's `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.). The author's own description: "The adapter cannot honor a parameter the request asked for (for example sampling on Claude)."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

### `src/token_meter/domain/estimation.py`

In its own words: "Estimate tokens and cost before any call is made."

54 non-blank lines; it defines `BudgetExceeded`, `TokenEstimator`, `RunEstimate`, `estimate_run`, `require_within_budget`.

`src/token_meter/domain/estimation.py`, lines 1 to 12:

```python
"""Estimate tokens and cost before any call is made."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal

from token_meter.domain.errors import DomainError
from token_meter.domain.pricing import PriceTable
from token_meter.domain.prompts import Kind, PromptRecord
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `math` (standard library) available.
- Brings in `Mapping`, `Sequence` from the standard library module `collections.abc`.
- Brings in `dataclass`, `field` from the standard library module `dataclasses`.
- Brings in `Decimal` from the standard library module `decimal`.
- Brings in `DomainError` (Base class for every error this package raises on purpose.) from the project module `token_meter.domain.errors`.
- Brings in `PriceTable` (Price per 1,000 input and output tokens, with the day the numbers were read.) from the project module `token_meter.domain.pricing`.
- Brings in `Kind` (What a prompt is for; the report breaks every number out by kind.), `PromptRecord` (One prompt. `expected_label` is set only for label prompts.) from the project module `token_meter.domain.prompts`.

`src/token_meter/domain/estimation.py`, lines 15 to 25:

```python
class BudgetExceeded(DomainError):
    """The estimate is above the budget, so the run must not start."""


@dataclass(frozen=True, slots=True)
class TokenEstimator:
    """Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.

    The overhead is zero and the ratio is 4 until you measure them: `calibrate` derives both from billed usage,
    with one ratio per kind of prompt because prose, code and other languages tokenize at different densities.
    """
```

- Defines the class `BudgetExceeded`. It builds on the project's `DomainError` (Base class for every error this package raises on purpose.). The author's own description: "The estimate is above the budget, so the run must not start."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `TokenEstimator`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/token_meter/domain/estimation.py`, lines 27 to 38:

```python
    chars_per_token: float = 4.0
    per_call_overhead: int = 0
    by_kind: Mapping[Kind, float] = field(default_factory=dict)

    def tokens(self, text: str, system: str = "", kind: Kind | None = None) -> int:
        """Estimated input tokens of one call that sends `text` (and `system`)."""
        ratio = self.by_kind.get(kind, self.chars_per_token) if kind else self.chars_per_token
        return max(1, math.ceil((len(text) + len(system)) / ratio)) + self.per_call_overhead

    def with_overhead(self, overhead: int) -> TokenEstimator:
        """The same ratios with a different fixed overhead."""
        return TokenEstimator(self.chars_per_token, overhead, self.by_kind)
```

- Declares `chars_per_token` as a decimal number and sets it to the number `4.0`.
- Declares `per_call_overhead` as a whole number and sets it to the number `0`.
- Declares `by_kind` as anything that behaves like a dictionary from the project type `Kind` to a decimal number and sets it to the result of calling `field`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `field` from the standard library module `dataclasses`.
- Defines the method `tokens`. It returns a whole number. The author's own description: "Estimated input tokens of one call that sends `text` (and `system`)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `text` holds text.
    - `system` holds text; if the caller leaves it out it is empty text.
    - `kind` holds the project type `Kind`, or nothing (None); if the caller leaves it out it is nothing (`None`).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores one of two values, chosen by a condition under the name `ratio`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `get` on the stored object `self.by_kind`: it reads a dictionary entry, giving a default when the key is missing.
- Ends the function and gives back the result of `max(1, math.ceil((len(text) + len(system)) / ratio)) + se...` to the caller.
  - `+` is add.
  - `max` picks the largest value.
  - `math.ceil` rounds up.
  - `/` is divide.
  - `len` counts the items in a collection (or the characters in text).
- Defines the method `with_overhead`. It returns the project type `TokenEstimator`. The author's own description: "The same ratios with a different fixed overhead."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `overhead` holds a whole number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back the result of calling `TokenEstimator` to the caller.
  - `TokenEstimator`, a class of this project (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).

`src/token_meter/domain/estimation.py`, lines 40 to 52:

```python
    def with_ratios(self, by_kind: Mapping[Kind, float]) -> TokenEstimator:
        """The same overhead with measured characters-per-token ratios per kind."""
        return TokenEstimator(self.chars_per_token, self.per_call_overhead, by_kind)


@dataclass(frozen=True, slots=True)
class RunEstimate:
    """What a run is expected to cost, before the first call."""

    calls: int
    input_tokens: int
    output_tokens: int
    cost: Decimal
```

- Defines the method `with_ratios`. It returns the project type `TokenEstimator`. The author's own description: "The same overhead with measured characters-per-token ratios per kind."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `by_kind` holds anything that behaves like a dictionary from the project type `Kind` to a decimal number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back the result of calling `TokenEstimator` to the caller.
  - `TokenEstimator`, a class of this project (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.).
- Defines the class `RunEstimate`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "What a run is expected to cost, before the first call."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `calls` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `input_tokens` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `output_tokens` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `cost` as an exact decimal number; it has no default, so a value must be given when the object is made.

`src/token_meter/domain/estimation.py`, lines 55 to 66:

```python
def estimate_run(
    prompts: Sequence[PromptRecord],
    calls_per_prompt: int,
    max_output_tokens: int,
    prices: PriceTable,
    estimator: TokenEstimator,
    system: str = "",
) -> RunEstimate:
    """Estimate a run of `calls_per_prompt` calls for each prompt, each assumed to use the full output cap."""
    input_tokens = sum(estimator.tokens(p.text, system, p.kind) for p in prompts) * calls_per_prompt
    calls = len(prompts) * calls_per_prompt
    output_tokens = calls * max_output_tokens
```

- Defines the function `estimate_run`. It returns the project type `RunEstimate`. The author's own description: "Estimate a run of `calls_per_prompt` calls for each prompt, each assumed to use the full output cap."
- Its parameters:
    - `prompts` holds anything that behaves like a list of the project type `PromptRecord`.
    - `calls_per_prompt` holds a whole number.
    - `max_output_tokens` holds a whole number.
    - `prices` holds the project type `PriceTable`.
    - `estimator` holds the project type `TokenEstimator`.
    - `system` holds text; if the caller leaves it out it is empty text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of `sum((estimator.tokens(p.text, system, p.kind) for p in pr...` under the name `input_tokens`.
  - `*` is multiply.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `tokens` of the project's `TokenEstimator` (Estimated input tokens of one call that sends `text` (and `system`).).
- Stores the result of `len(prompts) * calls_per_prompt` under the name `calls`.
  - `*` is multiply.
  - `len` counts the items in a collection (or the characters in text).
- Stores the result of `calls * max_output_tokens` under the name `output_tokens`.
  - `*` is multiply.

`src/token_meter/domain/estimation.py`, lines 67 to 73:

```python
    return RunEstimate(calls, input_tokens, output_tokens, prices.cost(input_tokens, output_tokens))


def require_within_budget(estimate: RunEstimate, budget: Decimal | None) -> None:
    """Raise `BudgetExceeded` when a budget is set and the estimate is above it."""
    if budget is not None and estimate.cost > budget:
        raise BudgetExceeded(f"estimated cost {estimate.cost:.4f} exceeds budget {budget}")
```

- Ends the function and gives back the result of calling `RunEstimate` to the caller.
  - `RunEstimate`, a class of this project (What a run is expected to cost, before the first call.).
  - The method `cost` of the project's `PriceTable` (Cost in dollars of a call with these token counts.).
- Defines the function `require_within_budget`. It returns nothing (None). The author's own description: "Raise `BudgetExceeded` when a budget is set and the estimate is above it."
- Its parameters:
    - `estimate` holds the project type `RunEstimate`.
    - `budget` holds an exact decimal number, or nothing (None).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Decision: the indented lines below run only when `budget is not None and estimate.cost > budget` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is not` means not the same object.
  - `>` means greater than.
- Raises an error: the result of calling `BudgetExceeded`. Execution jumps out to the nearest matching `except`.
  - `BudgetExceeded`, a class of this project (The estimate is above the budget, so the run must not start.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

### `src/token_meter/domain/journal.py`

In its own words: "One row per paid call: the unit of restartability."

19 non-blank lines; it defines `CallKey`, `JournalRow`.

`src/token_meter/domain/journal.py`, lines 1 to 14:

```python
"""One row per paid call: the unit of restartability."""

from __future__ import annotations

from dataclasses import dataclass

from token_meter.domain.llm import StopReason


@dataclass(frozen=True, slots=True)
class CallKey:
    """Identifies one call. A run never pays for the same key twice."""

    prompt_id: str
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `StopReason` (Why the model stopped writing.) from the project module `token_meter.domain.llm`.
- Defines the class `CallKey`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Identifies one call. A run never pays for the same key twice."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `prompt_id` as text; it has no default, so a value must be given when the object is made.

`src/token_meter/domain/journal.py`, lines 15 to 28:

```python
    setting: str
    repeat: int


@dataclass(frozen=True, slots=True)
class JournalRow:
    """What one call cost and returned, as billed by the provider."""

    key: CallKey
    input_tokens: int
    output_tokens: int
    stop_reason: StopReason
    latency_seconds: float
    text: str
```

- Declares `setting` as text; it has no default, so a value must be given when the object is made.
- Declares `repeat` as a whole number; it has no default, so a value must be given when the object is made.
- Defines the class `JournalRow`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "What one call cost and returned, as billed by the provider."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `key` as the project type `CallKey`; it has no default, so a value must be given when the object is made.
- Declares `input_tokens` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `output_tokens` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `stop_reason` as the project type `StopReason`; it has no default, so a value must be given when the object is made.
- Declares `latency_seconds` as a decimal number; it has no default, so a value must be given when the object is made.
- Declares `text` as text; it has no default, so a value must be given when the object is made.

### `src/token_meter/domain/llm.py`

In its own words: "Vendor-neutral value objects for one chat-model call. No SDK is imported here."

114 non-blank lines; it defines `Role`, `StopReason`, `ToolSpec`, `ToolCall`, `ChatMessage`, `Usage`, `ChatRequest`, `ChatResponse`.

`src/token_meter/domain/llm.py`, lines 1 to 14:

```python
"""Vendor-neutral value objects for one chat-model call. No SDK is imported here."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Role(StrEnum):
    """Who wrote a message."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `hashlib` (standard library) available.
- Makes the module `json` (standard library) available.
- Brings in `Mapping` from the standard library module `collections.abc`.
- Brings in `dataclass`, `field` from the standard library module `dataclasses`.
- Brings in `StrEnum` from the standard library module `enum`.
- Brings in `Any` from the standard library module `typing`.
- Defines the class `Role`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "Who wrote a message."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/token_meter/domain/llm.py`, lines 16 to 28:

```python
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class StopReason(StrEnum):
    """Why the model stopped writing."""

    END = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    REFUSAL = "refusal"
    OTHER = "other"
```

- Stores the text `user` under the name `USER`.
- Stores the text `assistant` under the name `ASSISTANT`.
- Stores the text `tool` under the name `TOOL`.
- Defines the class `StopReason`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "Why the model stopped writing."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `stop` under the name `END`.
- Stores the text `length` under the name `LENGTH`.
- Stores the text `tool_calls` under the name `TOOL_CALLS`.
- Stores the text `refusal` under the name `REFUSAL`.
- Stores the text `other` under the name `OTHER`.

`src/token_meter/domain/llm.py`, lines 31 to 42:

```python
@dataclass(frozen=True, slots=True)
class ToolSpec:
    """A tool the model may call: a name, a description and a JSON Schema for the arguments."""

    name: str
    description: str
    parameters: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ToolCall:
    """A tool call the model asked for."""
```

- Defines the class `ToolSpec`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "A tool the model may call: a name, a description and a JSON Schema for the arguments."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `name` as text; it has no default, so a value must be given when the object is made.
- Declares `description` as text; it has no default, so a value must be given when the object is made.
- Declares `parameters` as anything that behaves like a dictionary from text to any value; it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the class `ToolCall`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "A tool call the model asked for."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/token_meter/domain/llm.py`, lines 44 to 56:

```python
    id: str
    name: str
    arguments: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """One message of a conversation. A tool result carries the id of the call it answers."""

    role: Role
    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: str | None = None
```

- Declares `id` as text; it has no default, so a value must be given when the object is made.
- Declares `name` as text; it has no default, so a value must be given when the object is made.
- Declares `arguments` as anything that behaves like a dictionary from text to any value; it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the class `ChatMessage`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "One message of a conversation. A tool result carries the id of the call it answers."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `role` as the project type `Role`; it has no default, so a value must be given when the object is made.
- Declares `content` as text and sets it to empty text.
- Declares `tool_calls` as a fixed list of the project type `ToolCall` (any length) and sets it to a tuple of 0 item(s).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `tool_call_id` as text, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".

`src/token_meter/domain/llm.py`, lines 58 to 68:

```python
    @classmethod
    def user(cls, content: str) -> ChatMessage:
        return cls(Role.USER, content)


@dataclass(frozen=True, slots=True)
class Usage:
    """Tokens the provider billed for one call, read from its usage block, never recomputed."""

    input_tokens: int
    output_tokens: int
```

- Defines the method `user`. `@classmethod` makes it receive the class (`cls`) instead of an object; used as a named constructor. It returns the project type `ChatMessage`.
- Its parameters:
    - `cls` is the class itself (Python passes it automatically).
    - `content` holds text.
- Ends the function and gives back the result of calling `cls` to the caller.
  - `cls`, a function defined in this file or passed in.
- Defines the class `Usage`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Tokens the provider billed for one call, read from its usage block, never recomputed."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `input_tokens` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `output_tokens` as a whole number; it has no default, so a value must be given when the object is made.

`src/token_meter/domain/llm.py`, lines 71 to 82:

```python
@dataclass(frozen=True, slots=True)
class ChatRequest:
    """Everything that defines one call.

    `tag` names the call for recordings and logs (for example `p01/t07/2`); it is never sent to a vendor.
    `model` overrides the adapter's default model and is not part of the recording key.
    """

    messages: tuple[ChatMessage, ...]
    system: str | None = None
    max_output_tokens: int = 1024
    temperature: float | None = None
```

- Defines the class `ChatRequest`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Everything that defines one call."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `messages` as a fixed list of the project type `ChatMessage` (any length); it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `system` as text, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Declares `max_output_tokens` as a whole number and sets it to the number `1024`.
- Declares `temperature` as a decimal number, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".

`src/token_meter/domain/llm.py`, lines 83 to 90:

```python
    top_p: float | None = None
    response_schema: Mapping[str, Any] | None = None
    tools: tuple[ToolSpec, ...] = ()
    tag: str = ""
    model: str | None = None

    def fingerprint(self) -> str:
        """A stable hash of the request, used to find its recording. The model name is excluded."""
```

- Declares `top_p` as a decimal number, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Declares `response_schema` as anything that behaves like a dictionary from text to any value, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `tools` as a fixed list of the project type `ToolSpec` (any length) and sets it to a tuple of 0 item(s).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `tag` as text and sets it to empty text.
- Declares `model` as text, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Defines the method `fingerprint`. It returns text. The author's own description: "A stable hash of the request, used to find its recording. The model name is excluded."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/token_meter/domain/llm.py`, lines 91 to 108:

```python
        body = {
            "messages": [
                {
                    "role": m.role.value,
                    "content": m.content,
                    "tool_calls": [[c.id, c.name, dict(c.arguments)] for c in m.tool_calls],
                    "tool_call_id": m.tool_call_id,
                }
                for m in self.messages
            ],
            "system": self.system,
            "max_output_tokens": self.max_output_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "response_schema": self.response_schema,
            "tools": [[t.name, t.description, dict(t.parameters)] for t in self.tools],
            "tag": self.tag,
        }
```

- Stores a dictionary with 8 entries under the name `body`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `dict` makes a dictionary (a copy when given one).

`src/token_meter/domain/llm.py`, lines 109 to 122:

```python
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ChatResponse:
    """What came back: the text or the tool calls, why it stopped, the billed usage and the latency."""

    text: str
    stop_reason: StopReason
    usage: Usage
    latency_seconds: float
    model: str
    tool_calls: tuple[ToolCall, ...] = field(default=())
```

- Stores the result of calling `json.dumps` under the name `canonical`.
  - `json.dumps` turns Python data into JSON text.
- Ends the function and gives back the result of calling `hashlib.sha256(canonical.encode('utf-8')).hexdi...` to the caller.
  - `.hexdigest(...)` gives a hash as text of hexadecimal digits.
  - `hashlib.sha256` starts a SHA-256 hash.
  - `.encode(...)` turns text into bytes.
- Defines the class `ChatResponse`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "What came back: the text or the tool calls, why it stopped, the billed usage and the latency."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `text` as text; it has no default, so a value must be given when the object is made.
- Declares `stop_reason` as the project type `StopReason`; it has no default, so a value must be given when the object is made.
- Declares `usage` as the project type `Usage`; it has no default, so a value must be given when the object is made.
- Declares `latency_seconds` as a decimal number; it has no default, so a value must be given when the object is made.
- Declares `model` as text; it has no default, so a value must be given when the object is made.
- Declares `tool_calls` as a fixed list of the project type `ToolCall` (any length) and sets it to the result of calling `field`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `field` from the standard library module `dataclasses`.

`src/token_meter/domain/llm.py`, lines 124 to 135:

```python
    def to_json(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "stop_reason": self.stop_reason.value,
            "usage": {"input_tokens": self.usage.input_tokens, "output_tokens": self.usage.output_tokens},
            "latency_seconds": self.latency_seconds,
            "model": self.model,
            "tool_calls": [{"id": c.id, "name": c.name, "arguments": dict(c.arguments)} for c in self.tool_calls],
        }

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> ChatResponse:
```

- Defines the method `to_json`. It returns a dictionary from text to any value.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back a dictionary with 6 entries to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `dict` makes a dictionary (a copy when given one).
- Defines the method `from_json`. `@classmethod` makes it receive the class (`cls`) instead of an object; used as a named constructor. It returns the project type `ChatResponse`.
- Its parameters:
    - `cls` is the class itself (Python passes it automatically).
    - `data` holds anything that behaves like a dictionary from text to any value.

`src/token_meter/domain/llm.py`, lines 136 to 145:

```python
        return cls(
            text=str(data["text"]),
            stop_reason=StopReason(data["stop_reason"]),
            usage=Usage(int(data["usage"]["input_tokens"]), int(data["usage"]["output_tokens"])),
            latency_seconds=float(data["latency_seconds"]),
            model=str(data["model"]),
            tool_calls=tuple(
                ToolCall(str(c["id"]), str(c["name"]), dict(c["arguments"])) for c in data.get("tool_calls", [])
            ),
        )
```

- Ends the function and gives back the result of calling `cls` to the caller.
  - `cls`, a function defined in this file or passed in.
  - `str` turns a value into text.
  - `StopReason`, a class of this project (Why the model stopped writing.).
  - `Usage`, a class of this project (Tokens the provider billed for one call, read from its usage block, never recomputed.).
  - `float` turns a value into a decimal number.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `int` turns a value into a whole number.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `ToolCall`, a class of this project (A tool call the model asked for.).
  - `dict` makes a dictionary (a copy when given one).
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

### `src/token_meter/domain/pricing.py`

In its own words: "The dated price table. Prices change, so a table older than the allowed age is refused."

28 non-blank lines; it defines `StalePrices`, `PriceTable`.

`src/token_meter/domain/pricing.py`, lines 1 to 13:

```python
"""The dated price table. Prices change, so a table older than the allowed age is refused."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from token_meter.domain.errors import DomainError


class StalePrices(DomainError):
    """The price table was read too long ago to trust."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `date` from the standard library module `datetime`.
- Brings in `Decimal` from the standard library module `decimal`.
- Brings in `DomainError` (Base class for every error this package raises on purpose.) from the project module `token_meter.domain.errors`.
- Defines the class `StalePrices`. It builds on the project's `DomainError` (Base class for every error this package raises on purpose.). The author's own description: "The price table was read too long ago to trust."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/token_meter/domain/pricing.py`, lines 16 to 27:

```python
@dataclass(frozen=True, slots=True)
class PriceTable:
    """Price per 1,000 input and output tokens, with the day the numbers were read."""

    model: str
    input_per_1k: Decimal
    output_per_1k: Decimal
    read_date: date

    def cost(self, input_tokens: int, output_tokens: int) -> Decimal:
        """Cost in dollars of a call with these token counts."""
        return input_tokens * self.input_per_1k / 1000 + output_tokens * self.output_per_1k / 1000
```

- Defines the class `PriceTable`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Price per 1,000 input and output tokens, with the day the numbers were read."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `model` as text; it has no default, so a value must be given when the object is made.
- Declares `input_per_1k` as an exact decimal number; it has no default, so a value must be given when the object is made.
- Declares `output_per_1k` as an exact decimal number; it has no default, so a value must be given when the object is made.
- Declares `read_date` as a calendar date; it has no default, so a value must be given when the object is made.
- Defines the method `cost`. It returns an exact decimal number. The author's own description: "Cost in dollars of a call with these token counts."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `input_tokens` holds a whole number.
    - `output_tokens` holds a whole number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back the result of `input_tokens * self.input_per_1k / 1000 + output_tokens *...` to the caller.
  - `+` is add.
  - `/` is divide.
  - `*` is multiply.

`src/token_meter/domain/pricing.py`, lines 29 to 38:

```python
    def require_fresh(self, today: date, max_age_days: int) -> None:
        """Raise `StalePrices` when the table is older than `max_age_days` (or dated in the future)."""
        age = (today - self.read_date).days
        if age < 0:
            raise StalePrices(f"price table is dated {self.read_date}, which is after today ({today})")
        if age > max_age_days:
            raise StalePrices(
                f"price table was read on {self.read_date}, {age} days ago (limit {max_age_days}); "
                "read the current prices, update data/prices.json and its read_date"
            )
```

- Defines the method `require_fresh`. It returns nothing (None). The author's own description: "Raise `StalePrices` when the table is older than `max_age_days` (or dated in the future)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `today` holds a calendar date.
    - `max_age_days` holds a whole number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the `days` of `today - self.read_date` under the name `age`.
  - `-` is subtract.
- Decision: the indented lines below run only when `age < 0` is true.
  - `<` means less than.
- Raises an error: the result of calling `StalePrices`. Execution jumps out to the nearest matching `except`.
  - `StalePrices`, a class of this project (The price table was read too long ago to trust.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `age > max_age_days` is true.
  - `>` means greater than.
- Raises an error: the result of calling `StalePrices`. Execution jumps out to the nearest matching `except`.
  - `StalePrices`, a class of this project (The price table was read too long ago to trust.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

### `src/token_meter/domain/prompts.py`

In its own words: "The prompt set: 50 customer messages in five kinds, and the rules that make it a fair sample."

66 non-blank lines; it defines `InvalidPromptSet`, `Kind`, `PromptRecord`, `PromptSetSpec`, `parse_prompt`, `validate_prompt_set`.

`src/token_meter/domain/prompts.py`, lines 1 to 13:

```python
"""The prompt set: 50 customer messages in five kinds, and the rules that make it a fair sample."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from token_meter.domain.errors import DomainError

LABELS = ("billing", "shipping", "account", "other")
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Counter` from the standard library module `collections`.
- Brings in `Iterable`, `Mapping` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `StrEnum` from the standard library module `enum`.
- Brings in `Any` from the standard library module `typing`.
- Brings in `DomainError` (Base class for every error this package raises on purpose.) from the project module `token_meter.domain.errors`.
- Stores a tuple of 4 item(s) under the name `LABELS`.

`src/token_meter/domain/prompts.py`, lines 16 to 27:

```python
class InvalidPromptSet(DomainError):
    """The prompt file breaks a rule of the lesson (row count, kinds, a long prompt, unique ids)."""


class Kind(StrEnum):
    """What a prompt is for; the report breaks every number out by kind."""

    SHORT = "short"
    LONG = "long"
    CODE = "code"
    LANGUAGE = "language"
    LABEL = "label"
```

- Defines the class `InvalidPromptSet`. It builds on the project's `DomainError` (Base class for every error this package raises on purpose.). The author's own description: "The prompt file breaks a rule of the lesson (row count, kinds, a long prompt, unique ids)."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the class `Kind`. It builds on `StrEnum` (a fixed set of named values that are also text). The author's own description: "What a prompt is for; the report breaks every number out by kind."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the text `short` under the name `SHORT`.
- Stores the text `long` under the name `LONG`.
- Stores the text `code` under the name `CODE`.
- Stores the text `language` under the name `LANGUAGE`.
- Stores the text `label` under the name `LABEL`.

`src/token_meter/domain/prompts.py`, lines 30 to 41:

```python
@dataclass(frozen=True, slots=True)
class PromptRecord:
    """One prompt. `expected_label` is set only for label prompts."""

    id: str
    kind: Kind
    text: str
    expected_label: str | None = None


@dataclass(frozen=True, slots=True)
class PromptSetSpec:
```

- Defines the class `PromptRecord`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "One prompt. `expected_label` is set only for label prompts."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `id` as text; it has no default, so a value must be given when the object is made.
- Declares `kind` as the project type `Kind`; it has no default, so a value must be given when the object is made.
- Declares `text` as text; it has no default, so a value must be given when the object is made.
- Declares `expected_label` as text, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Defines the class `PromptSetSpec`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "The shape the lesson asks for: counts per kind and one prompt over a token threshold."

`src/token_meter/domain/prompts.py`, lines 42 to 55:

```python
    """The shape the lesson asks for: counts per kind and one prompt over a token threshold."""

    counts: Mapping[Kind, int]
    long_threshold_tokens: int = 1500
    chars_per_token: int = 4

    @classmethod
    def lesson(cls) -> PromptSetSpec:
        return cls({Kind.SHORT: 20, Kind.LONG: 15, Kind.CODE: 5, Kind.LANGUAGE: 5, Kind.LABEL: 5})


def parse_prompt(row: Mapping[str, Any]) -> PromptRecord:
    """Build a record from one decoded JSON Lines row, naming the field that is wrong."""
    for name in ("id", "kind", "text"):
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `counts` as anything that behaves like a dictionary from the project type `Kind` to a whole number; it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `long_threshold_tokens` as a whole number and sets it to the number `1500`.
- Declares `chars_per_token` as a whole number and sets it to the number `4`.
- Defines the method `lesson`. `@classmethod` makes it receive the class (`cls`) instead of an object; used as a named constructor. It returns the project type `PromptSetSpec`.
- Its parameters:
    - `cls` is the class itself (Python passes it automatically).
- Ends the function and gives back the result of calling `cls` to the caller.
  - `cls`, a function defined in this file or passed in.
- Defines the function `parse_prompt`. It returns the project type `PromptRecord`. The author's own description: "Build a record from one decoded JSON Lines row, naming the field that is wrong."
- Its parameters:
    - `row` holds anything that behaves like a dictionary from text to any value.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Loop: the indented lines below run once for each item of `('id', 'kind', 'text')`; `name` names the current item.

`src/token_meter/domain/prompts.py`, lines 56 to 69:

```python
        if not isinstance(row.get(name), str) or not row[name].strip():
            raise InvalidPromptSet(f"field {name!r} must be a non-empty string, got {row.get(name)!r}")
    try:
        kind = Kind(row["kind"])
    except ValueError as error:
        raise InvalidPromptSet(f"field 'kind' must be one of {[k.value for k in Kind]}, got {row['kind']!r}") from error
    label = row.get("expected_label")
    if kind is Kind.LABEL and label not in LABELS:
        raise InvalidPromptSet(f"field 'expected_label' of {row['id']} must be one of {LABELS}, got {label!r}")
    return PromptRecord(row["id"], kind, row["text"], label if kind is Kind.LABEL else None)


def validate_prompt_set(prompts: Iterable[PromptRecord], spec: PromptSetSpec) -> None:
    """Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken."""
```

- Decision: the indented lines below run only when `not isinstance(row.get(name), str) or not row[name].strip()` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `not` flips true and false.
  - `isinstance` asks whether a value is of a given type.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Raises an error: the result of calling `InvalidPromptSet`. Execution jumps out to the nearest matching `except`.
  - `InvalidPromptSet`, a class of this project (The prompt file breaks a rule of the lesson (row count, kinds, a long prompt, unique ids).).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `Kind` under the name `kind`.
  - `Kind`, a class of this project (What a prompt is for; the report breaks every number out by kind.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- `except` handler: it runs when the `try` block raised `ValueError`; `error` names the error object.
- Raises an error: the result of calling `InvalidPromptSet`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `InvalidPromptSet`, a class of this project (The prompt file breaks a rule of the lesson (row count, kinds, a long prompt, unique ids).).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `row.get` under the name `label`.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Decision: the indented lines below run only when `kind is Kind.LABEL and label not in LABELS` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is` means the very same object.
  - `not in` means is not contained in.
- Raises an error: the result of calling `InvalidPromptSet`. Execution jumps out to the nearest matching `except`.
  - `InvalidPromptSet`, a class of this project (The prompt file breaks a rule of the lesson (row count, kinds, a long prompt, unique ids).).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Ends the function and gives back the result of calling `PromptRecord` to the caller.
  - `PromptRecord`, a class of this project (One prompt. `expected_label` is set only for label prompts.).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is` means the very same object.
- Defines the function `validate_prompt_set`. It returns nothing (None). The author's own description: "Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken."
- Its parameters:
    - `prompts` holds anything you can loop over of the project type `PromptRecord`.
    - `spec` holds the project type `PromptSetSpec`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/token_meter/domain/prompts.py`, lines 70 to 83:

```python
    items = list(prompts)
    ids = Counter(p.id for p in items)
    repeated = sorted(i for i, n in ids.items() if n > 1)
    if repeated:
        raise InvalidPromptSet(f"prompt ids must be unique, repeated: {repeated}")
    total = sum(spec.counts.values())
    if len(items) != total:
        raise InvalidPromptSet(f"expected {total} prompts, found {len(items)}")
    by_kind = Counter(p.kind for p in items)
    for kind, wanted in spec.counts.items():
        if by_kind[kind] != wanted:
            raise InvalidPromptSet(f"expected {wanted} prompts of kind {kind.value}, found {by_kind[kind]}")
    longest = max(len(p.text) for p in items) // spec.chars_per_token
    if longest <= spec.long_threshold_tokens:
```

- Stores the result of calling `list` under the name `items`.
  - `list` makes a list (a copy when given a collection).
- Stores the result of calling `Counter` under the name `ids`.
  - `Counter` from the standard library module `collections`.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Stores the result of calling `sorted` under the name `repeated`.
  - `sorted` returns a new list with the items in order.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `.items(...)` gives the key and value pairs of a dictionary.
  - `>` means greater than.
- Decision: the indented lines below run only when `repeated` is true.
- Raises an error: the result of calling `InvalidPromptSet`. Execution jumps out to the nearest matching `except`.
  - `InvalidPromptSet`, a class of this project (The prompt file breaks a rule of the lesson (row count, kinds, a long prompt, unique ids).).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of calling `sum` under the name `total`.
  - `sum` adds up all the numbers.
  - `.values(...)` gives the values of a dictionary.
- Decision: the indented lines below run only when `len(items) != total` is true.
  - `!=` means not equal.
  - `len` counts the items in a collection (or the characters in text).
- Raises an error: the result of calling `InvalidPromptSet`. Execution jumps out to the nearest matching `except`.
  - `InvalidPromptSet`, a class of this project (The prompt file breaks a rule of the lesson (row count, kinds, a long prompt, unique ids).).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `len` counts the items in a collection (or the characters in text).
- Stores the result of calling `Counter` under the name `by_kind`.
  - `Counter` from the standard library module `collections`.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Loop: the indented lines below run once for each item of `spec.counts.items()`; `(kind, wanted)` names the current item.
  - `.items(...)` gives the key and value pairs of a dictionary.
- Decision: the indented lines below run only when `by_kind[kind] != wanted` is true.
  - `!=` means not equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Raises an error: the result of calling `InvalidPromptSet`. Execution jumps out to the nearest matching `except`.
  - `InvalidPromptSet`, a class of this project (The prompt file breaks a rule of the lesson (row count, kinds, a long prompt, unique ids).).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of `max((len(p.text) for p in items)) // spec.chars_per_token` under the name `longest`.
  - `//` is divide and drop the fraction.
  - `max` picks the largest value.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `len` counts the items in a collection (or the characters in text).
- Decision: the indented lines below run only when `longest <= spec.long_threshold_tokens` is true.
  - `<=` means less than or equal.

`src/token_meter/domain/prompts.py`, lines 84 to 86:

```python
        raise InvalidPromptSet(
            f"at least one prompt must be over {spec.long_threshold_tokens} tokens; the longest is about {longest}"
        )
```

- Raises an error: the result of calling `InvalidPromptSet`. Execution jumps out to the nearest matching `except`.
  - `InvalidPromptSet`, a class of this project (The prompt file breaks a rule of the lesson (row count, kinds, a long prompt, unique ids).).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

## Try it yourself

1. Every module carries its own description in `__doc__`; this prints the first file's.

```bash
.venv/bin/python -c "import token_meter.__init__; print(token_meter.__init__.__doc__)"
```

What you should see (captured from this repository):

```text
token_meter: estimate, call, bill and compare, for a batch of model calls.
```

2. Count the top-level functions and classes in each file of this layer, by reading the code without running it.

```bash
.venv/bin/python - <<'EOF'
import ast, pathlib
files = sorted(pathlib.Path('src/token_meter/domain').glob('*.py'))
for f in files:
    tree = ast.parse(f.read_text())
    names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    print(f.name, len(names))
EOF
```

What you should see (captured from this repository):

```text
__init__.py 0
analysis.py 19
decoding.py 1
errors.py 6
estimation.py 5
journal.py 2
llm.py 8
pricing.py 2
prompts.py 6
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

- **Common mistakes with this layer.** Importing a vendor library "just for a type" into the domain (the build fails: see `import-linter.md`), putting input/output (files, network) in a domain function, or letting a domain function read an environment variable. Here the domain takes everything it needs as arguments and returns values.

## Check yourself

1. What is the job of `src/token_meter/__init__.py`?

   *Answer:* token_meter: estimate, call, bill and compare, for a batch of model calls.

2. What is the job of `src/token_meter/domain/__init__.py`?

   *Answer:* Pure domain logic. Depends on nothing outside the standard library.

3. What is the job of `src/token_meter/domain/analysis.py`?

   *Answer:* Compare estimates with the bill, calibrate the estimator and measure the spread between answers.

4. What is the job of `src/token_meter/domain/decoding.py`?

   *Answer:* The decoding settings the meter compares.

5. What is the job of `src/token_meter/domain/errors.py`?

   *Answer:* Named errors. Callers catch these, never a vendor SDK's exception types.

## Further reading

- Python Language Reference, https://docs.python.org/3.13/reference/ (every statement kind explained here is defined there; the explanations in this note are generated from the code by a program that reads each statement's structure, so they describe what the statement does, not why the author chose it: for the why, read the file's own docstrings, which are quoted).

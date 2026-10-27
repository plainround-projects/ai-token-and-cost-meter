# Python source, the application layer

## What it is

This note walks through every Python file of the `application` layer of `token_meter`, line by line. Read `python.md` first for the language features; this note shows them at work.

The **application** layer holds the *use cases*: the steps that combine domain objects to do one job (run the meter, answer a question, resume an agent run). It talks to the outside only through *ports*, small interfaces (protocols) that the infrastructure layer implements.

## Why this repository uses it

Because use cases depend on ports and not on real services, the tests can run them with in-memory fakes, and the same use case works with a recorded model, a local model or Claude.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/token_meter/application/__init__.py` | 1 non-blank lines |
| `src/token_meter/application/metered_model.py` | 40 non-blank lines |
| `src/token_meter/application/ports.py` | 43 non-blank lines |
| `src/token_meter/application/report.py` | 54 non-blank lines |
| `src/token_meter/application/run_meter.py` | 121 non-blank lines |

## How it works underneath

Every file here is a *module*: Python runs it from top to bottom the first time something imports it. Imports come first, then constants, then the definitions (classes and functions). Defining a function or class does not run its body; the body runs when it is called.

How to read the explanations below. Each quoted block is a run of consecutive lines from the file, with its file name and line numbers. Under it, one bullet explains each statement in order, in plain words. A bullet that mentions a function the project defines also gives that function's own description (its docstring). Indented bullets under a statement explain the pieces inside it: calls, comprehensions, comparisons and operators. A `def` bullet lists the parameters; `self` is the object a method works on.

The layering rule that decides what this layer may import is enforced by `import-linter.md`; the file list above is the whole layer.

## Walkthrough of this repository's use

### `src/token_meter/application/__init__.py`

In its own words: "Use cases and the ports they need. Depends on the domain only."

1 non-blank lines.

`src/token_meter/application/__init__.py`, lines 1 to 1:

```python
"""Use cases and the ports they need. Depends on the domain only."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

### `src/token_meter/application/metered_model.py`

In its own words: "A decorator for services: estimate each request before it is sent and log estimate and bill side by side."

40 non-blank lines; it defines `MeteredChatModel`.

`src/token_meter/application/metered_model.py`, lines 1 to 14:

```python
"""A decorator for services: estimate each request before it is sent and log estimate and bill side by side."""

from __future__ import annotations

import logging

from token_meter.application.ports import ChatModel
from token_meter.domain.estimation import TokenEstimator
from token_meter.domain.llm import ChatRequest, ChatResponse

_log = logging.getLogger(__name__)


class MeteredChatModel:
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `logging` (standard library) available.
- Brings in `ChatModel` (One chat model behind one interface: a vendor, a local server or a recording.) from the project module `token_meter.application.ports`.
- Brings in `TokenEstimator` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.) from the project module `token_meter.domain.estimation`.
- Brings in `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.) from the project module `token_meter.domain.llm`.
- Stores the result of calling `logging.getLogger` under the name `_log`.
  - `logging.getLogger` gets the logger with the given name.
- Defines the class `MeteredChatModel`. The author's own description: "Wraps any `ChatModel`. Logs sizes only, never the prompt text."

`src/token_meter/application/metered_model.py`, lines 15 to 27:

```python
    """Wraps any `ChatModel`. Logs sizes only, never the prompt text."""

    def __init__(self, inner: ChatModel, estimator: TokenEstimator) -> None:
        self._inner = inner
        self._estimator = estimator

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def supports_sampling(self) -> bool:
        return self._inner.supports_sampling
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `inner` holds the project type `ChatModel`.
    - `estimator` holds the project type `TokenEstimator`.
- Stores the value named `inner` under the name `self._inner` (as an attribute of this object, so other methods can use it).
- Stores the value named `estimator` under the name `self._estimator` (as an attribute of this object, so other methods can use it).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `name` of this object to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `supports_sampling` of this object to the caller.

`src/token_meter/application/metered_model.py`, lines 29 to 38:

```python
    def estimate_input_tokens(self, request: ChatRequest) -> int:
        """The estimate for a request: its messages and system prompt."""
        text = "".join(m.content for m in request.messages)
        return self._estimator.tokens(text, request.system or "")

    def complete(self, request: ChatRequest) -> ChatResponse:
        estimated = self.estimate_input_tokens(request)
        response = self._inner.complete(request)
        billed = response.usage.input_tokens
        error = (estimated - billed) / billed if billed else 0.0
```

- Defines the method `estimate_input_tokens`. It returns a whole number. The author's own description: "The estimate for a request: its messages and system prompt."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `''.join` under the name `text`.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Ends the function and gives back the result of calling `self._estimator.tokens` to the caller.
  - The method `tokens` of the project's `TokenEstimator` (Estimated input tokens of one call that sends `text` (and `system`).).
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Stores the result of calling `self.estimate_input_tokens` under the name `estimated`.
  - The method `estimate_input_tokens` of this object (The estimate for a request: its messages and system prompt.).
- Stores the result of calling `self._inner.complete` under the name `response`.
  - The method `complete` of `self._inner`.
- Stores the `input_tokens` of `response.usage` under the name `billed`.
- Stores one of two values, chosen by a condition under the name `error`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `/` is divide.
  - `-` is subtract.

`src/token_meter/application/metered_model.py`, lines 39 to 51:

```python
        _log.info(
            "estimate against bill",
            extra={
                "fields": {
                    "tag": request.tag,
                    "estimated_input": estimated,
                    "billed_input": billed,
                    "error": f"{error:+.1%}",
                    "billed_output": response.usage.output_tokens,
                }
            },
        )
        return response
```

- Calls the method `info` of `_log` with 2 argument(s); the result is not kept.
  - The method `info` of `_log`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `response` to the caller.

### `src/token_meter/application/ports.py`

In its own words: "The boundaries the use cases depend on. Adapters in `infrastructure` implement them."

43 non-blank lines; it defines `ChatModel`, `Embedder`, `Clock`, `Journal`.

`src/token_meter/application/ports.py`, lines 1 to 14:

```python
"""The boundaries the use cases depend on. Adapters in `infrastructure` implement them."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from typing import Protocol

from token_meter.domain.journal import CallKey, JournalRow
from token_meter.domain.llm import ChatRequest, ChatResponse


class ChatModel(Protocol):
    """One chat model behind one interface: a vendor, a local server or a recording."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Brings in `date`, `datetime` from the standard library module `datetime`.
- Brings in `Protocol` from the standard library module `typing`.
- Brings in `CallKey` (Identifies one call. A run never pays for the same key twice.), `JournalRow` (What one call cost and returned, as billed by the provider.) from the project module `token_meter.domain.journal`.
- Brings in `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.) from the project module `token_meter.domain.llm`.
- Defines the class `ChatModel`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "One chat model behind one interface: a vendor, a local server or a recording."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/token_meter/application/ports.py`, lines 16 to 28:

```python
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

- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text. The author's own description: "The model id the responses come from."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false. The author's own description: "False when the provider rejects `temperature` and `top_p` (the request then says so)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `complete`. It returns the project type `ChatResponse`. The author's own description: "Send one request. Raises `TransientModelError` or `PermanentModelError`."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.

`src/token_meter/application/ports.py`, lines 31 to 42:

```python
class Embedder(Protocol):
    """Turns texts into vectors."""

    @property
    def name(self) -> str: ...

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """One vector per text, in order."""
        ...


class Clock(Protocol):
```

- Defines the class `Embedder`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "Turns texts into vectors."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `embed`. It returns a list of a list of a decimal number. The author's own description: "One vector per text, in order."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `texts` holds anything that behaves like a list of text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the class `Clock`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "Time, injected so tests are deterministic."

`src/token_meter/application/ports.py`, lines 43 to 56:

```python
    """Time, injected so tests are deterministic."""

    def monotonic(self) -> float: ...

    def today(self) -> date: ...

    def now(self) -> datetime: ...


class Journal(Protocol):
    """The append-only record of paid calls. Appending a row must survive a crash right after it."""

    def done_keys(self) -> set[CallKey]:
        """Keys of every call already paid for."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `monotonic`. It returns a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `today`. It returns a calendar date.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `now`. It returns a date and time.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the class `Journal`. It builds on `Protocol` (a list of methods an object must have; any class with them fits). The author's own description: "The append-only record of paid calls. Appending a row must survive a crash right after it."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `done_keys`. It returns a set of the project type `CallKey`. The author's own description: "Keys of every call already paid for."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/token_meter/application/ports.py`, lines 57 to 65:

```python
        ...

    def append(self, row: JournalRow) -> None:
        """Write one row and make it durable before returning."""
        ...

    def rows(self) -> list[JournalRow]:
        """Every row, in the order written."""
        ...
```

- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `append`. It returns nothing (None). The author's own description: "Write one row and make it durable before returning."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `row` holds the project type `JournalRow`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.
- Defines the method `rows`. It returns a list of the project type `JournalRow`. The author's own description: "Every row, in the order written."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `...` is a placeholder meaning "the body is not written here"; in a protocol it marks a method that implementations supply.

### `src/token_meter/application/report.py`

In its own words: "Build the report from the journal: estimated against billed, calibration and spread."

54 non-blank lines; it defines `MeterReport`, `build_report`.

`src/token_meter/application/report.py`, lines 1 to 8:

```python
"""Build the report from the journal: estimated against billed, calibration and spread."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from token_meter.application.ports import Journal
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Sequence` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `Journal` (The append-only record of paid calls. Appending a row must survive a crash right after it.) from the project module `token_meter.application.ports`.

`src/token_meter/application/report.py`, lines 9 to 21:

```python
from token_meter.domain.analysis import (
    CostCheck,
    EstimateReport,
    SpreadReport,
    calibrate,
    calibrate_overhead,
    compare_estimates,
    leave_one_out,
    measure_spread,
)
from token_meter.domain.estimation import TokenEstimator
from token_meter.domain.pricing import PriceTable
from token_meter.domain.prompts import PromptRecord
```

- Brings in `CostCheck` (A calibrated cost estimate against the bill, made without the answer it is judged on.), `EstimateReport` (Input-token error by kind and in total, and the largest single gap.), `SpreadReport` (One row per setting, and whether the first setting (temperature 0) repeated itself exactly.), `calibrate` (Measure the overhead, the characters per token of each kind and the mean answer length per kind and setting.), `calibrate_overhead` (The median of billed minus estimated input tokens: the fixed cost every call carries.), `compare_estimates` (Join estimates to billed input tokens (one row per prompt at `setting`) and group by kind.), `leave_one_out` (Estimate every prompt with an estimator that never saw it, so the error is an honest forecast error.), `measure_spread` (Count distinct answers per prompt and setting, label agreement, output length and cost per 1,000 calls.) from the project module `token_meter.domain.analysis`.
- Brings in `TokenEstimator` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.) from the project module `token_meter.domain.estimation`.
- Brings in `PriceTable` (Price per 1,000 input and output tokens, with the day the numbers were read.) from the project module `token_meter.domain.pricing`.
- Brings in `PromptRecord` (One prompt. `expected_label` is set only for label prompts.) from the project module `token_meter.domain.prompts`.

`src/token_meter/application/report.py`, lines 24 to 35:

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
```

- Defines the class `MeterReport`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Everything the `report` command prints."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `calls` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `billed_cost_total` as text; it has no default, so a value must be given when the object is made.
- Declares `naive` as the project type `EstimateReport`; it has no default, so a value must be given when the object is made.
- Declares `overhead` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `with_overhead` as the project type `EstimateReport`; it has no default, so a value must be given when the object is made.
- Declares `ratios` as a dictionary from text to a decimal number; it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `forecast` as the project type `EstimateReport`; it has no default, so a value must be given when the object is made.
- Declares `cost_check` as the project type `CostCheck`; it has no default, so a value must be given when the object is made.

`src/token_meter/application/report.py`, lines 36 to 49:

```python
    spread: SpreadReport


def build_report(
    journal: Journal,
    prompts: Sequence[PromptRecord],
    prices: PriceTable,
    naive: TokenEstimator,
    max_output_tokens: int,
) -> MeterReport:
    """Compare the naive estimator with the bill, add the measured overhead, then forecast each prompt leave-one-out."""
    rows = journal.rows()
    overhead = calibrate_overhead(prompts, rows, naive)
    full = calibrate(prompts, rows, naive)
```

- Declares `spread` as the project type `SpreadReport`; it has no default, so a value must be given when the object is made.
- Defines the function `build_report`. It returns the project type `MeterReport`. The author's own description: "Compare the naive estimator with the bill, add the measured overhead, then forecast each prompt leave-one-out."
- Its parameters:
    - `journal` holds the project type `Journal`.
    - `prompts` holds anything that behaves like a list of the project type `PromptRecord`.
    - `prices` holds the project type `PriceTable`.
    - `naive` holds the project type `TokenEstimator`.
    - `max_output_tokens` holds a whole number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `journal.rows` under the name `rows`.
  - The method `rows` of `journal`.
- Stores the result of calling `calibrate_overhead` under the name `overhead`.
  - `calibrate_overhead` from the project's `token_meter.domain.analysis` (The median of billed minus estimated input tokens: the fixed cost every call carries.).
- Stores the result of calling `calibrate` under the name `full`.
  - `calibrate` from the project's `token_meter.domain.analysis` (Measure the overhead, the characters per token of each kind and the mean answer length per kind and setting.).

`src/token_meter/application/report.py`, lines 50 to 62:

```python
    forecast = leave_one_out(prompts, rows, naive, prices, max_output_tokens)
    total = sum((prices.cost(r.input_tokens, r.output_tokens) for r in rows), start=prices.cost(0, 0))
    return MeterReport(
        calls=len(rows),
        billed_cost_total=f"{total:.6f}",
        naive=compare_estimates(prompts, rows, naive, known_overhead=overhead),
        overhead=overhead,
        with_overhead=compare_estimates(prompts, rows, naive.with_overhead(overhead)),
        ratios={kind.value: round(ratio, 2) for kind, ratio in full.estimator.by_kind.items()},
        forecast=forecast.input_tokens,
        cost_check=forecast.cost,
        spread=measure_spread(prompts, rows, prices),
    )
```

- Stores the result of calling `leave_one_out` under the name `forecast`.
  - `leave_one_out` from the project's `token_meter.domain.analysis` (Estimate every prompt with an estimator that never saw it, so the error is an honest forecast error.).
- Stores the result of calling `sum` under the name `total`.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `cost` of the project's `PriceTable` (Cost in dollars of a call with these token counts.).
- Ends the function and gives back the result of calling `MeterReport` to the caller.
  - `MeterReport`, a class of this project (Everything the `report` command prints.).
  - `len` counts the items in a collection (or the characters in text).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `compare_estimates` from the project's `token_meter.domain.analysis` (Join estimates to billed input tokens (one row per prompt at `setting`) and group by kind.).
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `measure_spread` from the project's `token_meter.domain.analysis` (Count distinct answers per prompt and setting, label agreement, output length and cost per 1,000 calls.).
  - The method `with_overhead` of the project's `TokenEstimator` (The same ratios with a different fixed overhead.).
  - `round` rounds a number.
  - `.items(...)` gives the key and value pairs of a dictionary.

### `src/token_meter/application/run_meter.py`

In its own words: "The metering run: estimate first, refuse above the budget, call, and journal one row per call."

121 non-blank lines; it defines `RunPlan`, `RunSummary`, `plan_keys`, `estimate_pending`, `RunMeter`.

`src/token_meter/application/run_meter.py`, lines 1 to 14:

```python
"""The metering run: estimate first, refuse above the budget, call, and journal one row per call."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal

from token_meter.application.ports import ChatModel, Journal
from token_meter.domain.decoding import DecodingSetting
from token_meter.domain.errors import UnsupportedParameter
from token_meter.domain.estimation import RunEstimate, TokenEstimator, require_within_budget
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `logging` (standard library) available.
- Makes the module `time` (standard library) available.
- Brings in `Callable`, `Sequence` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `Decimal` from the standard library module `decimal`.
- Brings in `ChatModel` (One chat model behind one interface: a vendor, a local server or a recording.), `Journal` (The append-only record of paid calls. Appending a row must survive a crash right after it.) from the project module `token_meter.application.ports`.
- Brings in `DecodingSetting` (A named sampling configuration. `top_p` is None when it is left at the provider default.) from the project module `token_meter.domain.decoding`.
- Brings in `UnsupportedParameter` (The adapter cannot honor a parameter the request asked for (for example sampling on Claude).) from the project module `token_meter.domain.errors`.
- Brings in `RunEstimate` (What a run is expected to cost, before the first call.), `TokenEstimator` (Characters divided by a characters-per-token ratio, plus a fixed per-call overhead for the chat template.), `require_within_budget` (Raise `BudgetExceeded` when a budget is set and the estimate is above it.) from the project module `token_meter.domain.estimation`.

`src/token_meter/application/run_meter.py`, lines 15 to 28:

```python
from token_meter.domain.journal import CallKey, JournalRow
from token_meter.domain.llm import ChatMessage, ChatRequest
from token_meter.domain.pricing import PriceTable
from token_meter.domain.prompts import PromptRecord

_log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RunPlan:
    """Everything that defines a run besides the model and the journal."""

    prompts: Sequence[PromptRecord]
    settings: Sequence[DecodingSetting]
```

- Brings in `CallKey` (Identifies one call. A run never pays for the same key twice.), `JournalRow` (What one call cost and returned, as billed by the provider.) from the project module `token_meter.domain.journal`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.) from the project module `token_meter.domain.llm`.
- Brings in `PriceTable` (Price per 1,000 input and output tokens, with the day the numbers were read.) from the project module `token_meter.domain.pricing`.
- Brings in `PromptRecord` (One prompt. `expected_label` is set only for label prompts.) from the project module `token_meter.domain.prompts`.
- Stores the result of calling `logging.getLogger` under the name `_log`.
  - `logging.getLogger` gets the logger with the given name.
- Defines the class `RunPlan`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Everything that defines a run besides the model and the journal."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `prompts` as anything that behaves like a list of the project type `PromptRecord`; it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Declares `settings` as anything that behaves like a list of the project type `DecodingSetting`; it has no default, so a value must be given when the object is made.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/token_meter/application/run_meter.py`, lines 29 to 42:

```python
    repeats: int
    max_output_tokens: int
    prices: PriceTable
    estimator: TokenEstimator
    budget: Decimal | None = None
    system: str | None = None
    throttle_seconds: float = 0.0


@dataclass(frozen=True, slots=True)
class RunSummary:
    """What a run did: calls paid now, calls skipped because the journal had them, and why it ended."""

    estimate: RunEstimate
```

- Declares `repeats` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `max_output_tokens` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `prices` as the project type `PriceTable`; it has no default, so a value must be given when the object is made.
- Declares `estimator` as the project type `TokenEstimator`; it has no default, so a value must be given when the object is made.
- Declares `budget` as an exact decimal number, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Declares `system` as text, or nothing (None) and sets it to nothing (`None`).
  - `|` is or; in a type, "either".
- Declares `throttle_seconds` as a decimal number and sets it to the number `0.0`.
- Defines the class `RunSummary`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "What a run did: calls paid now, calls skipped because the journal had them, and why it ended."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `estimate` as the project type `RunEstimate`; it has no default, so a value must be given when the object is made.

`src/token_meter/application/run_meter.py`, lines 43 to 55:

```python
    calls_made: int
    calls_skipped: int
    interrupted: bool


def plan_keys(plan: RunPlan) -> list[CallKey]:
    """Every call the plan covers, in the order they are made."""
    return [
        CallKey(prompt.id, setting.name, repeat)
        for prompt in plan.prompts
        for setting in plan.settings
        for repeat in range(plan.repeats)
    ]
```

- Declares `calls_made` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `calls_skipped` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `interrupted` as true or false; it has no default, so a value must be given when the object is made.
- Defines the function `plan_keys`. It returns a list of the project type `CallKey`. The author's own description: "Every call the plan covers, in the order they are made."
- Its parameters:
    - `plan` holds the project type `RunPlan`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `CallKey` from the project's `token_meter.domain.journal` (Identifies one call. A run never pays for the same key twice.).
  - `range` makes the numbers from 0 up to (not including) the given one.

`src/token_meter/application/run_meter.py`, lines 58 to 67:

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

- Defines the function `estimate_pending`. It returns the project type `RunEstimate`. The author's own description: "The cost of the calls the journal does not hold yet, estimated before the first one."
- Its parameters:
    - `plan` holds the project type `RunPlan`.
    - `done` holds a set of the project type `CallKey`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores a dictionary built by looping under the name `by_prompt`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Stores a list built by looping under the name `pending`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `plan_keys`, a function of this file (Every call the plan covers, in the order they are made.).
  - `not in` means is not contained in.
- Stores the result of calling `sum` under the name `input_tokens`.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `tokens` of the project's `TokenEstimator` (Estimated input tokens of one call that sends `text` (and `system`).).
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of `len(pending) * plan.max_output_tokens` under the name `output_tokens`.
  - `*` is multiply.
  - `len` counts the items in a collection (or the characters in text).
- Ends the function and gives back the result of calling `RunEstimate` to the caller.
  - `RunEstimate` from the project's `token_meter.domain.estimation` (What a run is expected to cost, before the first call.).
  - `len` counts the items in a collection (or the characters in text).
  - The method `cost` of the project's `PriceTable` (Cost in dollars of a call with these token counts.).

`src/token_meter/application/run_meter.py`, lines 70 to 81:

```python
class RunMeter:
    """Calls the model once per (prompt, setting, repeat) that the journal does not hold yet."""

    def __init__(
        self,
        model: ChatModel,
        journal: Journal,
        stop_requested: Callable[[], bool] = lambda: False,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._model = model
        self._journal = journal
```

- Defines the class `RunMeter`. The author's own description: "Calls the model once per (prompt, setting, repeat) that the journal does not hold yet."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `model` holds the project type `ChatModel`.
    - `journal` holds the project type `Journal`.
    - `stop_requested` holds a function; if the caller leaves it out it is a small function.
    - `sleep` holds a function; if the caller leaves it out it is the `sleep` of `time`.
- Stores the value named `model` under the name `self._model` (as an attribute of this object, so other methods can use it).
- Stores the value named `journal` under the name `self._journal` (as an attribute of this object, so other methods can use it).

`src/token_meter/application/run_meter.py`, lines 82 to 95:

```python
        self._stop_requested = stop_requested
        self._sleep = sleep

    def run(self, plan: RunPlan) -> RunSummary:
        """Refuse above the budget before any call, then make the missing calls, one journal row each."""
        if not self._model.supports_sampling:
            raise UnsupportedParameter(
                f"{self._model.name} does not accept temperature or top_p, "
                "so the three decoding settings cannot be compared"
            )
        estimate = estimate_pending(plan, self._journal.done_keys())
        require_within_budget(estimate, plan.budget)
        done = self._journal.done_keys()
        by_prompt = {p.id: p for p in plan.prompts}
```

- Stores the value named `stop_requested` under the name `self._stop_requested` (as an attribute of this object, so other methods can use it).
- Stores the value named `sleep` under the name `self._sleep` (as an attribute of this object, so other methods can use it).
- Defines the method `run`. It returns the project type `RunSummary`. The author's own description: "Refuse above the budget before any call, then make the missing calls, one journal row each."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `plan` holds the project type `RunPlan`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Decision: the indented lines below run only when `not self._model.supports_sampling` is true.
  - `not` flips true and false.
- Raises an error: the result of calling `UnsupportedParameter`. Execution jumps out to the nearest matching `except`.
  - `UnsupportedParameter` from the project's `token_meter.domain.errors` (The adapter cannot honor a parameter the request asked for (for example sampling on Claude).).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of calling `estimate_pending` under the name `estimate`.
  - `estimate_pending`, a function defined in this file or passed in.
  - The method `done_keys` of `self._journal`.
- Calls `require_within_budget` from the project's `token_meter.domain.estimation` (Raise `BudgetExceeded` when a budget is set and the estimate is above it.) with 2 argument(s); the result is not kept.
  - `require_within_budget` from the project's `token_meter.domain.estimation` (Raise `BudgetExceeded` when a budget is set and the estimate is above it.).
- Stores the result of calling `self._journal.done_keys` under the name `done`.
  - The method `done_keys` of `self._journal`.
- Stores a dictionary built by looping under the name `by_prompt`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.

`src/token_meter/application/run_meter.py`, lines 96 to 105:

```python
        by_setting = {s.name: s for s in plan.settings}
        made = skipped = 0
        for key in plan_keys(plan):
            if key in done:
                skipped += 1
                continue
            if self._stop_requested():
                _log.info("stop requested, leaving the rest for a restart", extra={"fields": {"made": made}})
                return RunSummary(estimate, made, skipped, interrupted=True)
            setting = by_setting[key.setting]
```

- Stores a dictionary built by looping under the name `by_setting`.
  - A comprehension builds a dictionary by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Stores the number `0` under the name `made`, `skipped`.
- Loop: the indented lines below run once for each item of `plan_keys(plan)`; `key` names the current item.
  - `plan_keys`, a function defined in this file or passed in.
- Decision: the indented lines below run only when `key in done` is true.
  - `in` means is contained in.
- Updates `skipped` in place: `+=` applies `+` with the number `1` and stores the result back.
- Skips the rest of this round of the loop and starts the next.
- Decision: the indented lines below run only when `self._stop_requested()` is true.
  - The method `_stop_requested` of `self`.
- Calls the method `info` of `_log` with 2 argument(s); the result is not kept.
  - The method `info` of `_log`.
- Ends the function and gives back the result of calling `RunSummary` to the caller.
  - `RunSummary`, a class of this project (What a run did: calls paid now, calls skipped because the journal had them, and why it ended.).
- Stores the part of `by_setting` picked by `key.setting` under the name `setting`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/token_meter/application/run_meter.py`, lines 106 to 114:

```python
            request = ChatRequest(
                messages=(ChatMessage.user(by_prompt[key.prompt_id].text),),
                system=plan.system,
                max_output_tokens=plan.max_output_tokens,
                temperature=setting.temperature,
                top_p=setting.top_p,
                tag=f"{key.prompt_id}/{key.setting}/{key.repeat}",
            )
            response = self._model.complete(request)
```

- Stores the result of calling `ChatRequest` under the name `request`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - The method `user` of `ChatMessage`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `self._model.complete` under the name `response`.
  - The method `complete` of `self._model`.

`src/token_meter/application/run_meter.py`, lines 115 to 125:

```python
            self._journal.append(
                JournalRow(
                    key,
                    response.usage.input_tokens,
                    response.usage.output_tokens,
                    response.stop_reason,
                    response.latency_seconds,
                    response.text,
                )
            )
            made += 1
```

- Calls `append` on the stored object `self._journal`: it adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `append` on the stored object `self._journal`: it adds one item at the end of a list.
  - `JournalRow` from the project's `token_meter.domain.journal` (What one call cost and returned, as billed by the provider.).
- Updates `made` in place: `+=` applies `+` with the number `1` and stores the result back.

`src/token_meter/application/run_meter.py`, lines 126 to 139:

```python
            _log.info(
                "call journaled",
                extra={
                    "fields": {
                        "tag": request.tag,
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                        "stop": response.stop_reason.value,
                    }
                },
            )
            if plan.throttle_seconds:
                self._sleep(plan.throttle_seconds)
        return RunSummary(estimate, made, skipped, interrupted=False)
```

- Calls the method `info` of `_log` with 2 argument(s); the result is not kept.
  - The method `info` of `_log`.
- Decision: the indented lines below run only when `plan.throttle_seconds` is true.
- Calls the method `_sleep` of `self` with 1 argument(s); the result is not kept.
  - The method `_sleep` of `self`.
- Ends the function and gives back the result of calling `RunSummary` to the caller.
  - `RunSummary`, a class of this project (What a run did: calls paid now, calls skipped because the journal had them, and why it ended.).

## Try it yourself

1. Every module carries its own description in `__doc__`; this prints the first file's.

```bash
.venv/bin/python -c "import token_meter.application.__init__; print(token_meter.application.__init__.__doc__)"
```

What you should see (captured from this repository):

```text
Use cases and the ports they need. Depends on the domain only.
```

2. Count the top-level functions and classes in each file of this layer, by reading the code without running it.

```bash
.venv/bin/python - <<'EOF'
import ast, pathlib
files = sorted(pathlib.Path('src/token_meter/application').glob('*.py'))
for f in files:
    tree = ast.parse(f.read_text())
    names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    print(f.name, len(names))
EOF
```

What you should see (captured from this repository):

```text
__init__.py 0
metered_model.py 1
ports.py 4
report.py 2
run_meter.py 5
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

- **Common mistakes with this layer.** Calling a concrete adapter directly from a use case (the layering contract would fail), hiding state in module-level variables, or doing slow input/output inside a loop without a way to stop it. Here the ports are protocols and long loops check a shutdown flag.

## Check yourself

1. What is the job of `src/token_meter/application/__init__.py`?

   *Answer:* Use cases and the ports they need. Depends on the domain only.

2. What is the job of `src/token_meter/application/metered_model.py`?

   *Answer:* A decorator for services: estimate each request before it is sent and log estimate and bill side by side.

3. What is the job of `src/token_meter/application/ports.py`?

   *Answer:* The boundaries the use cases depend on. Adapters in `infrastructure` implement them.

4. What is the job of `src/token_meter/application/report.py`?

   *Answer:* Build the report from the journal: estimated against billed, calibration and spread.

5. What is the job of `src/token_meter/application/run_meter.py`?

   *Answer:* The metering run: estimate first, refuse above the budget, call, and journal one row per call.

## Further reading

- Python Language Reference, https://docs.python.org/3.13/reference/ (every statement kind explained here is defined there; the explanations in this note are generated from the code by a program that reads each statement's structure, so they describe what the statement does, not why the author chose it: for the why, read the file's own docstrings, which are quoted).

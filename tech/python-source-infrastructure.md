# Python source, the infrastructure layer

## What it is

This note walks through every Python file of the `infrastructure` layer of `token_meter`, line by line. Read `python.md` first for the language features; this note shows them at work.

The **infrastructure** layer is the adapters: the code that touches the world. Files, databases, HTTP calls to a model server, the Claude SDK, the clock, signals, logging and settings all live here. Each adapter implements a port from the application layer.

## Why this repository uses it

Keeping every contact with the outside in one layer makes it easy to swap (recorded answers instead of a live model) and to test (a fake HTTP transport instead of a network).

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/token_meter/infrastructure/__init__.py` | 1 non-blank lines |
| `src/token_meter/infrastructure/anthropic_chat.py` | 102 non-blank lines |
| `src/token_meter/infrastructure/clock.py` | 12 non-blank lines |
| `src/token_meter/infrastructure/csv_journal.py` | 72 non-blank lines |
| `src/token_meter/infrastructure/env.py` | 53 non-blank lines |
| `src/token_meter/infrastructure/files.py` | 36 non-blank lines |
| `src/token_meter/infrastructure/logging.py` | 40 non-blank lines |
| `src/token_meter/infrastructure/model_factory.py` | 65 non-blank lines |
| `src/token_meter/infrastructure/openai_compatible.py` | 109 non-blank lines |
| `src/token_meter/infrastructure/recording.py` | 79 non-blank lines |
| `src/token_meter/infrastructure/resilient.py` | 48 non-blank lines |
| `src/token_meter/infrastructure/retry.py` | 33 non-blank lines |
| `src/token_meter/infrastructure/settings.py` | 47 non-blank lines |
| `src/token_meter/infrastructure/shutdown.py` | 20 non-blank lines |

## How it works underneath

Every file here is a *module*: Python runs it from top to bottom the first time something imports it. Imports come first, then constants, then the definitions (classes and functions). Defining a function or class does not run its body; the body runs when it is called.

How to read the explanations below. Each quoted block is a run of consecutive lines from the file, with its file name and line numbers. Under it, one bullet explains each statement in order, in plain words. A bullet that mentions a function the project defines also gives that function's own description (its docstring). Indented bullets under a statement explain the pieces inside it: calls, comprehensions, comparisons and operators. A `def` bullet lists the parameters; `self` is the object a method works on.

The layering rule that decides what this layer may import is enforced by `import-linter.md`; the file list above is the whole layer.

## Walkthrough of this repository's use

### `src/token_meter/infrastructure/__init__.py`

In its own words: "Adapters that implement the ports: model clients, files, settings, logging."

1 non-blank lines.

`src/token_meter/infrastructure/__init__.py`, lines 1 to 1:

```python
"""Adapters that implement the ports: model clients, files, settings, logging."""
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

### `src/token_meter/infrastructure/anthropic_chat.py`

In its own words: "A chat model on the Anthropic Messages API, through the official SDK."

102 non-blank lines; it defines `_messages_payload`, `AnthropicChatModel`.

`src/token_meter/infrastructure/anthropic_chat.py`, lines 1 to 14:

```python
"""A chat model on the Anthropic Messages API, through the official SDK.

The Messages API rejects `temperature`, `top_p` and `top_k` from API version 2026-10-21 on, so this adapter
reports `supports_sampling = False` and raises `UnsupportedParameter` if a request asks for them. Structured
output uses `output_config.format`; forced `tool_choice` is not used (newer models answer it with a 400).
"""

from __future__ import annotations

from typing import Any, Literal

import anthropic

from token_meter.application.ports import Clock
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Any`, `Literal` from the standard library module `typing`.
- Makes the module `anthropic` (installed package) available.
- Brings in `Clock` (Time, injected so tests are deterministic.) from the project module `token_meter.application.ports`.

`src/token_meter/infrastructure/anthropic_chat.py`, lines 15 to 26:

```python
from token_meter.domain.errors import PermanentModelError, TransientModelError, UnsupportedParameter
from token_meter.domain.llm import ChatMessage, ChatRequest, ChatResponse, Role, StopReason, ToolCall, Usage

Thinking = Literal["omit", "disabled", "between_tools"]

_STOP = {
    "end_turn": StopReason.END,
    "stop_sequence": StopReason.END,
    "max_tokens": StopReason.LENGTH,
    "tool_use": StopReason.TOOL_CALLS,
    "refusal": StopReason.REFUSAL,
}
```

- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.), `UnsupportedParameter` (The adapter cannot honor a parameter the request asked for (for example sampling on Claude).) from the project module `token_meter.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.), `Role` (Who wrote a message.), `StopReason` (Why the model stopped writing.), `ToolCall` (A tool call the model asked for.), `Usage` (Tokens the provider billed for one call, read from its usage block, never recomputed.) from the project module `token_meter.domain.llm`.
- Stores the part of `Literal` picked by `('omit', 'disabled', 'betwe...` under the name `Thinking`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores a dictionary with 5 entries under the name `_STOP`.

`src/token_meter/infrastructure/anthropic_chat.py`, lines 29 to 40:

```python
def _messages_payload(messages: tuple[ChatMessage, ...]) -> list[dict[str, Any]]:
    """Map neutral messages to Messages API turns; consecutive tool results share one user turn."""
    out: list[dict[str, Any]] = []
    for message in messages:
        if message.role is Role.TOOL:
            block = {"type": "tool_result", "tool_use_id": message.tool_call_id, "content": message.content}
            if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list):
                out[-1]["content"].append(block)
            else:
                out.append({"role": "user", "content": [block]})
        elif message.role is Role.ASSISTANT and message.tool_calls:
            blocks: list[dict[str, Any]] = [{"type": "text", "text": message.content}] if message.content else []
```

- Defines the function `_messages_payload`. It returns a list of a dictionary from text to any value. The author's own description: "Map neutral messages to Messages API turns; consecutive tool results share one user turn."
- Its parameters:
    - `messages` holds a fixed list of the project type `ChatMessage` (any length).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `out` as a list of a dictionary from text to any value and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Loop: the indented lines below run once for each item of `messages`; `message` names the current item.
- Decision: the indented lines below run only when `message.role is Role.TOOL` is true.
  - `is` means the very same object.
- Stores a dictionary with 3 entries under the name `block`.
- Decision: the indented lines below run only when `out and out[-1]['role'] == 'user' and isinstance(out[-1]['content']...` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `==` means equal.
  - `isinstance` asks whether a value is of a given type.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- `else:` — the indented lines below run when none of the conditions above were true.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Decision: the indented lines below run only when `message.role is Role.ASSISTANT and message.tool_calls` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is` means the very same object.
- Declares `blocks` as a list of a dictionary from text to any value and sets it to one of two values, chosen by a condition.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `A if condition else B` gives A when the condition is true and B otherwise.

`src/token_meter/infrastructure/anthropic_chat.py`, lines 41 to 54:

```python
            blocks.extend(
                {"type": "tool_use", "id": c.id, "name": c.name, "input": dict(c.arguments)} for c in message.tool_calls
            )
            out.append({"role": "assistant", "content": blocks})
        else:
            out.append({"role": message.role.value, "content": message.content})
    return out


class AnthropicChatModel:
    """Calls Claude. Build the SDK client with your key from the environment; this class never reads it."""

    def __init__(self, client: anthropic.Anthropic, model: str, clock: Clock, thinking: Thinking = "disabled") -> None:
        self._client = client
```

- Calls `.extend(...)` adds all the items of another collection to the end of a list with 1 argument(s); the result is not kept.
  - `.extend(...)` adds all the items of another collection to the end of a list.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `dict` makes a dictionary (a copy when given one).
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- `else:` — the indented lines below run when none of the conditions above were true.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Ends the function and gives back the value named `out` to the caller.
- Defines the class `AnthropicChatModel`. The author's own description: "Calls Claude. Build the SDK client with your key from the environment; this class never reads it."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `client` holds `anthropic.Anthropic`.
    - `model` holds text.
    - `clock` holds the project type `Clock`.
    - `thinking` holds `Thinking`; if the caller leaves it out it is the text `disabled`.
- Stores the value named `client` under the name `self._client` (as an attribute of this object, so other methods can use it).

`src/token_meter/infrastructure/anthropic_chat.py`, lines 55 to 68:

```python
        self._model = model
        self._clock = clock
        self._thinking = thinking

    @property
    def name(self) -> str:
        return self._model

    @property
    def supports_sampling(self) -> bool:
        return False

    def build_payload(self, request: ChatRequest) -> dict[str, Any]:
        """The keyword arguments for `messages.create` (public so tests can assert on them)."""
```

- Stores the value named `model` under the name `self._model` (as an attribute of this object, so other methods can use it).
- Stores the value named `clock` under the name `self._clock` (as an attribute of this object, so other methods can use it).
- Stores the value named `thinking` under the name `self._thinking` (as an attribute of this object, so other methods can use it).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `_model` of this object to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the value `False` to the caller.
- Defines the method `build_payload`. It returns a dictionary from text to any value. The author's own description: "The keyword arguments for `messages.create` (public so tests can assert on them)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/token_meter/infrastructure/anthropic_chat.py`, lines 69 to 82:

```python
        if request.temperature is not None or request.top_p is not None:
            raise UnsupportedParameter("the Messages API rejects temperature and top_p; leave them unset")
        payload: dict[str, Any] = {
            "model": request.model or self._model,
            "max_tokens": request.max_output_tokens,
            "messages": _messages_payload(request.messages),
        }
        if request.system:
            payload["system"] = request.system
        if self._thinking != "omit":
            payload["thinking"] = {"type": self._thinking}
        if request.response_schema is not None:
            payload["output_config"] = {"format": {"type": "json_schema", "schema": dict(request.response_schema)}}
        if request.tools:
```

- Decision: the indented lines below run only when `request.temperature is not None or request.top_p is not None` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `is not` means not the same object.
- Raises an error: the result of calling `UnsupportedParameter`. Execution jumps out to the nearest matching `except`.
  - `UnsupportedParameter` from the project's `token_meter.domain.errors` (The adapter cannot honor a parameter the request asked for (for example sampling on Claude).).
- Declares `payload` as a dictionary from text to any value and sets it to a dictionary with 3 entries.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `_messages_payload`, a function defined in this file or passed in.
- Decision: the indented lines below run only when `request.system` is true.
- Stores the `system` of `request` under the name `payload['system']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `self._thinking != 'omit'` is true.
  - `!=` means not equal.
- Stores a dictionary with 1 entry under the name `payload['thinking']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `request.response_schema is not None` is true.
  - `is not` means not the same object.
- Stores a dictionary with 1 entry under the name `payload['output_config']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `dict` makes a dictionary (a copy when given one).
- Decision: the indented lines below run only when `request.tools` is true.

`src/token_meter/infrastructure/anthropic_chat.py`, lines 83 to 96:

```python
            payload["tools"] = [
                {"name": t.name, "description": t.description, "input_schema": dict(t.parameters)}
                for t in request.tools
            ]
        return payload

    def complete(self, request: ChatRequest) -> ChatResponse:
        payload = self.build_payload(request)
        started = self._clock.monotonic()
        try:
            message = self._client.messages.create(**payload)
        except anthropic.APIConnectionError as error:
            raise TransientModelError(f"{type(error).__name__}: {error}") from error
        except anthropic.APIStatusError as error:
```

- Stores a list built by looping under the name `payload['tools']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `dict` makes a dictionary (a copy when given one).
- Ends the function and gives back the value named `payload` to the caller.
- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Stores the result of calling `self.build_payload` under the name `payload`.
  - The method `build_payload` of this object (The keyword arguments for `messages.create` (public so tests can assert on them).).
- Stores the result of calling `self._clock.monotonic` under the name `started`.
  - The method `monotonic` of `self._clock`.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `self._client.messages.create` under the name `message`.
  - The method `create` of `self._client.messages`.
  - `**name` inside a call passes every entry of a dictionary as a named argument.
- `except` handler: it runs when the `try` block raised `anthropic.APIConnectionError`; `error` names the error object.
- Raises an error: the result of calling `TransientModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `token_meter.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `type` gives the type (class) of a value.
- `except` handler: it runs when the `try` block raised `anthropic.APIStatusError`; `error` names the error object.

`src/token_meter/infrastructure/anthropic_chat.py`, lines 97 to 104:

```python
            if error.status_code in (408, 409, 429) or error.status_code >= 500:
                raise TransientModelError(f"HTTP {error.status_code}: {error.message}") from error
            raise PermanentModelError(f"HTTP {error.status_code}: {error.message}") from error
        elapsed = self._clock.monotonic() - started
        text = "".join(block.text for block in message.content if block.type == "text")
        calls = tuple(
            ToolCall(block.id, block.name, dict(block.input)) for block in message.content if block.type == "tool_use"
        )
```

- Decision: the indented lines below run only when `error.status_code in (408, 409, 429) or error.status_code >= 500` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `in` means is contained in.
  - `>=` means greater than or equal.
- Raises an error: the result of calling `TransientModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `token_meter.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Raises an error: the result of calling `PermanentModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `PermanentModelError` from the project's `token_meter.domain.errors` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores the result of `self._clock.monotonic() - started` under the name `elapsed`.
  - `-` is subtract.
  - The method `monotonic` of `self._clock`.
- Stores the result of calling `''.join` under the name `text`.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `==` means equal.
- Stores the result of calling `tuple` under the name `calls`.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `ToolCall` from the project's `token_meter.domain.llm` (A tool call the model asked for.).
  - `dict` makes a dictionary (a copy when given one).
  - `==` means equal.

`src/token_meter/infrastructure/anthropic_chat.py`, lines 105 to 118:

```python
        return ChatResponse(
            text=text,
            stop_reason=_STOP.get(message.stop_reason or "", StopReason.OTHER),
            usage=Usage(message.usage.input_tokens, message.usage.output_tokens),
            latency_seconds=round(elapsed, 4),
            model=message.model,
            tool_calls=calls,
        )

    def count_tokens(self, request: ChatRequest) -> int:
        """Ask the provider how many input tokens a request would use (no generation, no charge)."""
        payload = self.build_payload(request)
        for unused in ("max_tokens", "thinking", "output_config"):
            payload.pop(unused, None)
```

- Ends the function and gives back the result of calling `ChatResponse` to the caller.
  - `ChatResponse` from the project's `token_meter.domain.llm` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.).
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `Usage` from the project's `token_meter.domain.llm` (Tokens the provider billed for one call, read from its usage block, never recomputed.).
  - `round` rounds a number.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Defines the method `count_tokens`. It returns a whole number. The author's own description: "Ask the provider how many input tokens a request would use (no generation, no charge)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `self.build_payload` under the name `payload`.
  - The method `build_payload` of this object (The keyword arguments for `messages.create` (public so tests can assert on them).).
- Loop: the indented lines below run once for each item of `('max_tokens', 'thinking', 'output_config')`; `unused` names the current item.
- Calls `.pop(...)` removes and returns an item with 2 argument(s); the result is not kept.
  - `.pop(...)` removes and returns an item.

`src/token_meter/infrastructure/anthropic_chat.py`, lines 119 to 119:

```python
        return int(self._client.messages.count_tokens(**payload).input_tokens)
```

- Ends the function and gives back the result of calling `int` to the caller.
  - `int` turns a value into a whole number.
  - The method `count_tokens` of the project's `AnthropicChatModel` (Ask the provider how many input tokens a request would use (no generation, no charge).).
  - `**name` inside a call passes every entry of a dictionary as a named argument.

### `src/token_meter/infrastructure/clock.py`

In its own words: "The real clock, behind the `Clock` port."

12 non-blank lines; it defines `SystemClock`.

`src/token_meter/infrastructure/clock.py`, lines 1 to 13:

```python
"""The real clock, behind the `Clock` port."""

from __future__ import annotations

import time
from datetime import UTC, date, datetime


class SystemClock:
    """Wall-clock and monotonic time from the operating system."""

    def monotonic(self) -> float:
        return time.monotonic()
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `time` (standard library) available.
- Brings in `UTC`, `date`, `datetime` from the standard library module `datetime`.
- Defines the class `SystemClock`. The author's own description: "Wall-clock and monotonic time from the operating system."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `monotonic`. It returns a decimal number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `time.monotonic` to the caller.
  - `time.monotonic` a clock that never goes backwards, for measuring durations.

`src/token_meter/infrastructure/clock.py`, lines 15 to 19:

```python
    def today(self) -> date:
        return datetime.now(UTC).date()

    def now(self) -> datetime:
        return datetime.now(UTC)
```

- Defines the method `today`. It returns a calendar date.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `datetime.now(UTC).date` to the caller.
  - The method `date` of `datetime.now(UTC)`.
  - `datetime.now` the current date and time.
- Defines the method `now`. It returns a date and time.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `datetime.now` to the caller.
  - `datetime.now` the current date and time.

### `src/token_meter/infrastructure/csv_journal.py`

In its own words: "The journal as a CSV file: append and flush one row per call, so a crash costs only unfinished calls."

72 non-blank lines; it defines `JournalCorrupt`, `CsvJournal`.

`src/token_meter/infrastructure/csv_journal.py`, lines 1 to 13:

```python
"""The journal as a CSV file: append and flush one row per call, so a crash costs only unfinished calls."""

from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path

from token_meter.domain.errors import DomainError
from token_meter.domain.journal import CallKey, JournalRow
from token_meter.domain.llm import StopReason
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `csv` (standard library) available.
- Makes the module `io` (standard library) available.
- Makes the module `json` (standard library) available.
- Makes the module `os` (standard library) available.
- Brings in `Path` from the standard library module `pathlib`.
- Brings in `DomainError` (Base class for every error this package raises on purpose.) from the project module `token_meter.domain.errors`.
- Brings in `CallKey` (Identifies one call. A run never pays for the same key twice.), `JournalRow` (What one call cost and returned, as billed by the provider.) from the project module `token_meter.domain.journal`.
- Brings in `StopReason` (Why the model stopped writing.) from the project module `token_meter.domain.llm`.

`src/token_meter/infrastructure/csv_journal.py`, lines 16 to 27:

```python
class JournalCorrupt(DomainError):
    """The journal file does not start with the expected header; delete it or restore it from a copy."""


COLUMNS = ("prompt_id", "setting", "repeat", "input_tokens", "output_tokens", "stop_reason", "latency_s", "text")


class CsvJournal:
    """Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open."""

    def __init__(self, path: Path) -> None:
        self._path = path
```

- Defines the class `JournalCorrupt`. It builds on the project's `DomainError` (Base class for every error this package raises on purpose.). The author's own description: "The journal file does not start with the expected header; delete it or restore it from a copy."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores a tuple of 8 item(s) under the name `COLUMNS`.
- Defines the class `CsvJournal`. The author's own description: "Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `path` holds a file path.
- Stores the value named `path` under the name `self._path` (as an attribute of this object, so other methods can use it).

`src/token_meter/infrastructure/csv_journal.py`, lines 28 to 41:

```python
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.stat().st_size > 0:
            self._cut_torn_tail()
        else:
            self._write(self._line(COLUMNS))
        self._rows = self._read()

    def _line(self, values: tuple[object, ...]) -> str:
        buffer = io.StringIO()
        csv.writer(buffer, lineterminator="\n").writerow(values)
        return buffer.getvalue()

    def _write(self, text: str) -> None:
        with self._path.open("a", encoding="utf-8", newline="") as handle:
```

- Calls `.mkdir(...)` creates a folder with 2 argument(s); the result is not kept.
  - `.mkdir(...)` creates a folder.
- Decision: the indented lines below run only when `path.exists() and path.stat().st_size > 0` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `.exists(...)` asks whether the path exists.
  - `>` means greater than.
  - `.stat(...)` gets information about a file (size, times).
- Calls the method `_cut_torn_tail` of this object; the result is not kept.
  - The method `_cut_torn_tail` of this object.
- `else:` — the indented lines below run when none of the conditions above were true.
- Calls the method `_write` of this object with 1 argument(s); the result is not kept.
  - The method `_write` of this object.
  - The method `_line` of this object.
- Stores the result of calling `self._read` under the name `self._rows` (as an attribute of this object, so other methods can use it).
  - The method `_read` of this object.
- Defines the method `_line`. It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `values` holds a fixed list of any object (any length).
- Stores the result of calling `io.StringIO` under the name `buffer`.
  - `io.StringIO` from the standard library module `io`.
- Calls the method `writerow` of `csv.writer(buffer, lineterminator='\n')` with 1 argument(s); the result is not kept.
  - The method `writerow` of `csv.writer(buffer, lineterminator='\n')`.
  - `csv.writer` makes a writer of CSV rows.
- Ends the function and gives back the result of calling `buffer.getvalue` to the caller.
  - The method `getvalue` of `buffer`.
- Defines the method `_write`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `text` holds text.
- A `with` block: it sets up `self._path.open('a', encoding='utf-8', newline='')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `self._path`.

`src/token_meter/infrastructure/csv_journal.py`, lines 42 to 55:

```python
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())

    def _cut_torn_tail(self) -> None:
        data = self._path.read_bytes()
        if data.endswith(b"\n"):
            return
        self._path.write_bytes(data[: data.rfind(b"\n") + 1])

    def _read(self) -> list[JournalRow]:
        with self._path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != COLUMNS:
```

- Calls `.write(...)` writes text or bytes to an open file with 1 argument(s); the result is not kept.
  - `.write(...)` writes text or bytes to an open file.
- Calls `.flush(...)` pushes buffered output to the operating system; the result is not kept.
  - `.flush(...)` pushes buffered output to the operating system.
- Calls `os.fsync` forces the operating system to write a file to disk with 1 argument(s); the result is not kept.
  - `os.fsync` forces the operating system to write a file to disk.
  - `.fileno(...)` gives the file's descriptor number.
- Defines the method `_cut_torn_tail`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Stores the result of calling `self._path.read_bytes` under the name `data`.
  - `read_bytes` on the stored object `self._path`: it reads a whole file as bytes.
- Decision: the indented lines below run only when `data.endswith(b'\n')` is true.
  - `.endswith(...)` asks whether text ends with the given text.
- Ends the function and gives back nothing to the caller.
- Calls `write_bytes` on the stored object `self._path`: it writes bytes to a file, replacing it with 1 argument(s); the result is not kept.
  - `write_bytes` on the stored object `self._path`: it writes bytes to a file, replacing it.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - `+` is add.
  - The method `rfind` of `data`.
- Defines the method `_read`. It returns a list of the project type `JournalRow`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A `with` block: it sets up `self._path.open(encoding='utf-8', newline='')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `self._path`.
- Stores the result of calling `csv.DictReader` under the name `reader`.
  - `csv.DictReader` reads CSV rows as dictionaries.
- Decision: the indented lines below run only when `tuple(reader.fieldnames or ()) != COLUMNS` is true.
  - `!=` means not equal.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).

`src/token_meter/infrastructure/csv_journal.py`, lines 56 to 69:

```python
                raise JournalCorrupt(
                    f"{self._path}: expected the header {','.join(COLUMNS)}, found {reader.fieldnames}"
                )
            return [
                JournalRow(
                    CallKey(r["prompt_id"], r["setting"], int(r["repeat"])),
                    int(r["input_tokens"]),
                    int(r["output_tokens"]),
                    StopReason(r["stop_reason"]),
                    float(r["latency_s"]),
                    json.loads(r["text"]),
                )
                for r in reader
            ]
```

- Raises an error: the result of calling `JournalCorrupt`. Execution jumps out to the nearest matching `except`.
  - `JournalCorrupt`, a class of this project (The journal file does not start with the expected header; delete it or restore it from a copy.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Ends the function and gives back a list built by looping to the caller.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `JournalRow` from the project's `token_meter.domain.journal` (What one call cost and returned, as billed by the provider.).
  - `CallKey` from the project's `token_meter.domain.journal` (Identifies one call. A run never pays for the same key twice.).
  - `int` turns a value into a whole number.
  - `StopReason` from the project's `token_meter.domain.llm` (Why the model stopped writing.).
  - `float` turns a value into a decimal number.
  - `json.loads` turns JSON text into Python data.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/token_meter/infrastructure/csv_journal.py`, lines 71 to 74:

```python
    def done_keys(self) -> set[CallKey]:
        return {row.key for row in self._rows}

    def append(self, row: JournalRow) -> None:
```

- Defines the method `done_keys`. It returns a set of the project type `CallKey`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back a set built by looping to the caller.
  - A comprehension builds a set by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Defines the method `append`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `row` holds the project type `JournalRow`.

`src/token_meter/infrastructure/csv_journal.py`, lines 75 to 88:

```python
        values = (
            row.key.prompt_id,
            row.key.setting,
            row.key.repeat,
            row.input_tokens,
            row.output_tokens,
            row.stop_reason.value,
            f"{row.latency_seconds:.4f}",
            json.dumps(row.text, ensure_ascii=False),
        )
        self._write(self._line(values))
        self._rows.append(row)

    def rows(self) -> list[JournalRow]:
```

- Stores a tuple of 8 item(s) under the name `values`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `json.dumps` turns Python data into JSON text.
- Calls the method `_write` of this object with 1 argument(s); the result is not kept.
  - The method `_write` of this object.
  - The method `_line` of this object.
- Calls `append` on the stored object `self._rows`: it adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `append` on the stored object `self._rows`: it adds one item at the end of a list.
- Defines the method `rows`. It returns a list of the project type `JournalRow`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).

`src/token_meter/infrastructure/csv_journal.py`, lines 89 to 89:

```python
        return list(self._rows)
```

- Ends the function and gives back the result of calling `list` to the caller.
  - `list` makes a list (a copy when given a collection).

### `src/token_meter/infrastructure/env.py`

In its own words: "Helpers that read and validate environment variables (twelve-factor configuration)."

53 non-blank lines; it defines `ConfigurationError`, `text`, `optional_text`, `positive_int`, `non_negative_int`, `positive_float`, `non_negative_float`, `choice`.

`src/token_meter/infrastructure/env.py`, lines 1 to 14:

```python
"""Helpers that read and validate environment variables (twelve-factor configuration)."""

from __future__ import annotations

from collections.abc import Collection, Mapping


class ConfigurationError(ValueError):
    """An environment variable is missing or has an unusable value."""


def text(environ: Mapping[str, str], name: str, default: str) -> str:
    """A non-empty string, or `default` when the variable is unset."""
    value = environ.get(name, default).strip()
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Brings in `Collection`, `Mapping` from the standard library module `collections.abc`.
- Defines the class `ConfigurationError`. It builds on `ValueError`. The author's own description: "An environment variable is missing or has an unusable value."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the function `text`. It returns text. The author's own description: "A non-empty string, or `default` when the variable is unset."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, default).strip` under the name `value`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

`src/token_meter/infrastructure/env.py`, lines 15 to 28:

```python
    if not value:
        raise ConfigurationError(f"{name} must not be empty")
    return value


def optional_text(environ: Mapping[str, str], name: str) -> str | None:
    """The variable's text, or None when it is unset or blank."""
    value = environ.get(name, "").strip()
    return value or None


def positive_int(environ: Mapping[str, str], name: str, default: int) -> int:
    """An integer of 1 or more."""
    raw = environ.get(name, str(default)).strip()
```

- Decision: the indented lines below run only when `not value` is true.
  - `not` flips true and false.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `value` to the caller.
- Defines the function `optional_text`. It returns text, or nothing (None). The author's own description: "The variable's text, or None when it is unset or blank."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, '').strip` under the name `value`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Ends the function and gives back the result of combining conditions: `value or None` to the caller.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Defines the function `positive_int`. It returns a whole number. The author's own description: "An integer of 1 or more."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds a whole number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, str(default)).strip` under the name `raw`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `str` turns a value into text.

`src/token_meter/infrastructure/env.py`, lines 29 to 42:

```python
    if not raw.isdigit() or int(raw) < 1:
        raise ConfigurationError(f"{name} must be a positive integer, got {raw!r}")
    return int(raw)


def non_negative_int(environ: Mapping[str, str], name: str, default: int) -> int:
    """An integer of 0 or more."""
    raw = environ.get(name, str(default)).strip()
    if not raw.isdigit():
        raise ConfigurationError(f"{name} must be a non-negative integer, got {raw!r}")
    return int(raw)


def positive_float(environ: Mapping[str, str], name: str, default: float) -> float:
```

- Decision: the indented lines below run only when `not raw.isdigit() or int(raw) < 1` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `not` flips true and false.
  - `<` means less than.
  - `.isdigit(...)` asks whether text is only digits.
  - `int` turns a value into a whole number.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the result of calling `int` to the caller.
  - `int` turns a value into a whole number.
- Defines the function `non_negative_int`. It returns a whole number. The author's own description: "An integer of 0 or more."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds a whole number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, str(default)).strip` under the name `raw`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `str` turns a value into text.
- Decision: the indented lines below run only when `not raw.isdigit()` is true.
  - `not` flips true and false.
  - `.isdigit(...)` asks whether text is only digits.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the result of calling `int` to the caller.
  - `int` turns a value into a whole number.
- Defines the function `positive_float`. It returns a decimal number. The author's own description: "A number greater than zero."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds a decimal number.

`src/token_meter/infrastructure/env.py`, lines 43 to 56:

```python
    """A number greater than zero."""
    raw = environ.get(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError as error:
        raise ConfigurationError(f"{name} must be a number, got {raw!r}") from error
    if value <= 0:
        raise ConfigurationError(f"{name} must be greater than zero, got {raw!r}")
    return value


def non_negative_float(environ: Mapping[str, str], name: str, default: float) -> float:
    """A number of 0 or more."""
    raw = environ.get(name, str(default)).strip()
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, str(default)).strip` under the name `raw`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `str` turns a value into text.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `float` under the name `value`.
  - `float` turns a value into a decimal number.
- `except` handler: it runs when the `try` block raised `ValueError`; `error` names the error object.
- Raises an error: the result of calling `ConfigurationError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `value <= 0` is true.
  - `<=` means less than or equal.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `value` to the caller.
- Defines the function `non_negative_float`. It returns a decimal number. The author's own description: "A number of 0 or more."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds a decimal number.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `environ.get(name, str(default)).strip` under the name `raw`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `str` turns a value into text.

`src/token_meter/infrastructure/env.py`, lines 57 to 70:

```python
    try:
        value = float(raw)
    except ValueError as error:
        raise ConfigurationError(f"{name} must be a number, got {raw!r}") from error
    if value < 0:
        raise ConfigurationError(f"{name} must not be negative, got {raw!r}")
    return value


def choice(environ: Mapping[str, str], name: str, default: str, allowed: Collection[str]) -> str:
    """One of the `allowed` strings."""
    value = text(environ, name, default)
    if value not in allowed:
        raise ConfigurationError(f"{name} must be one of {sorted(allowed)}, got {value!r}")
```

- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `float` under the name `value`.
  - `float` turns a value into a decimal number.
- `except` handler: it runs when the `try` block raised `ValueError`; `error` names the error object.
- Raises an error: the result of calling `ConfigurationError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `value < 0` is true.
  - `<` means less than.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `value` to the caller.
- Defines the function `choice`. It returns text. The author's own description: "One of the `allowed` strings."
- Its parameters:
    - `environ` holds anything that behaves like a dictionary from text to text.
    - `name` holds text.
    - `default` holds text.
    - `allowed` holds a collection with a size of text.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `text` under the name `value`.
  - `text`, a function of this file (A non-empty string, or `default` when the variable is unset.).
- Decision: the indented lines below run only when `value not in allowed` is true.
  - `not in` means is not contained in.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError`, a class of this project (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `sorted` returns a new list with the items in order.

`src/token_meter/infrastructure/env.py`, lines 71 to 71:

```python
    return value
```

- Ends the function and gives back the value named `value` to the caller.

### `src/token_meter/infrastructure/files.py`

In its own words: "Readers for the prompt file (JSON Lines) and the price file (JSON)."

36 non-blank lines; it defines `load_prompts`, `load_prices`.

`src/token_meter/infrastructure/files.py`, lines 1 to 14:

```python
"""Readers for the prompt file (JSON Lines) and the price file (JSON)."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from token_meter.domain.pricing import PriceTable
from token_meter.domain.prompts import InvalidPromptSet, PromptRecord, parse_prompt


def load_prompts(path: Path) -> list[PromptRecord]:
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Brings in `date` from the standard library module `datetime`.
- Brings in `Decimal`, `InvalidOperation` from the standard library module `decimal`.
- Brings in `Path` from the standard library module `pathlib`.
- Brings in `PriceTable` (Price per 1,000 input and output tokens, with the day the numbers were read.) from the project module `token_meter.domain.pricing`.
- Brings in `InvalidPromptSet` (The prompt file breaks a rule of the lesson (row count, kinds, a long prompt, unique ids).), `PromptRecord` (One prompt. `expected_label` is set only for label prompts.), `parse_prompt` (Build a record from one decoded JSON Lines row, naming the field that is wrong.) from the project module `token_meter.domain.prompts`.
- Defines the function `load_prompts`. It returns a list of the project type `PromptRecord`. The author's own description: "Read one prompt per line. A bad line is reported with its line number; the rest of the file is not lost."
- Its parameters:
    - `path` holds a file path.

`src/token_meter/infrastructure/files.py`, lines 15 to 27:

```python
    """Read one prompt per line. A bad line is reported with its line number; the rest of the file is not lost."""
    prompts: list[PromptRecord] = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                prompts.append(parse_prompt(json.loads(line)))
            except json.JSONDecodeError as error:
                raise InvalidPromptSet(f"{path}:{number}: not valid JSON ({error.msg})") from error
            except InvalidPromptSet as error:
                raise InvalidPromptSet(f"{path}:{number}: {error}") from error
    return prompts
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `prompts` as a list of the project type `PromptRecord` and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- A `with` block: it sets up `path.open(encoding='utf-8')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `path`.
- Loop: the indented lines below run once for each item of `enumerate(handle, start=1)`; `(number, line)` names the current item.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
- Decision: the indented lines below run only when `not line.strip()` is true.
  - `not` flips true and false.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
- Skips the rest of this round of the loop and starts the next.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `parse_prompt` from the project's `token_meter.domain.prompts` (Build a record from one decoded JSON Lines row, naming the field that is wrong.).
  - `json.loads` turns JSON text into Python data.
- `except` handler: it runs when the `try` block raised `json.JSONDecodeError`; `error` names the error object.
- Raises an error: the result of calling `InvalidPromptSet`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `InvalidPromptSet` from the project's `token_meter.domain.prompts` (The prompt file breaks a rule of the lesson (row count, kinds, a long prompt, unique ids).).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- `except` handler: it runs when the `try` block raised the project type `InvalidPromptSet`; `error` names the error object.
- Raises an error: the result of calling `InvalidPromptSet`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `InvalidPromptSet` from the project's `token_meter.domain.prompts` (The prompt file breaks a rule of the lesson (row count, kinds, a long prompt, unique ids).).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Ends the function and gives back the value named `prompts` to the caller.

`src/token_meter/infrastructure/files.py`, lines 30 to 40:

```python
def load_prices(path: Path) -> PriceTable:
    """Read the price file. `read_date` is a real field so a script can refuse stale prices."""
    data = json.loads(path.read_text(encoding="utf-8"))
    try:
        return PriceTable(
            model=str(data["model"]),
            input_per_1k=Decimal(str(data["input_per_1k"])),
            output_per_1k=Decimal(str(data["output_per_1k"])),
            read_date=date.fromisoformat(data["read_date"]),
        )
    except (KeyError, ValueError, InvalidOperation) as error:
```

- Defines the function `load_prices`. It returns the project type `PriceTable`. The author's own description: "Read the price file. `read_date` is a real field so a script can refuse stale prices."
- Its parameters:
    - `path` holds a file path.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `json.loads` under the name `data`.
  - `json.loads` turns JSON text into Python data.
  - `.read_text(...)` reads a whole file as text.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Ends the function and gives back the result of calling `PriceTable` to the caller.
  - `PriceTable` from the project's `token_meter.domain.pricing` (Price per 1,000 input and output tokens, with the day the numbers were read.).
  - `str` turns a value into text.
  - `Decimal` from the standard library module `decimal`.
  - `date.fromisoformat` reads a date from ISO text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- `except` handler: it runs when the `try` block raised `(KeyError, ValueError, InvalidOperation)`; `error` names the error object.

`src/token_meter/infrastructure/files.py`, lines 41 to 43:

```python
        raise ValueError(
            f"{path}: price file needs model, input_per_1k, output_per_1k and an ISO read_date ({error!r})"
        ) from error
```

- Raises an error: the result of calling `ValueError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `ValueError` an error for a value that is the right type but unusable.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

### `src/token_meter/infrastructure/logging.py`

In its own words: "Structured logging: one logfmt line per event (`ts=... level=... logger=... msg=... key=value`)."

40 non-blank lines; it defines `_quote`, `LogfmtFormatter`, `fields`, `configure_logging`.

`src/token_meter/infrastructure/logging.py`, lines 1 to 13:

```python
"""Structured logging: one logfmt line per event (`ts=... level=... logger=... msg=... key=value`).

Prompt and completion text never goes into an INFO line. Log sizes, ids, hashes and counts; a DEBUG line may
carry text for a developer who asked for it.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any, TextIO
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Makes the module `logging` (standard library) available.
- Makes the module `sys` (standard library) available.
- Brings in `UTC`, `datetime` from the standard library module `datetime`.
- Brings in `Any`, `TextIO` from the standard library module `typing`.

`src/token_meter/infrastructure/logging.py`, lines 16 to 25:

```python
def _quote(value: object) -> str:
    text = str(value)
    return json.dumps(text) if not text or any(char in text for char in ' ="\n') else text


class LogfmtFormatter(logging.Formatter):
    """Format a log record as one logfmt line, with the record's extra fields as key=value pairs."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds")
```

- Defines the function `_quote`. It returns text.
- Its parameters:
    - `value` holds any object.
- Stores the result of calling `str` under the name `text`.
  - `str` turns a value into text.
- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `json.dumps` turns Python data into JSON text.
  - `not` flips true and false.
  - `any` is true if at least one item is true.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `in` means is contained in.
- Defines the class `LogfmtFormatter`. It builds on the logging `Formatter` (turns a record into text). The author's own description: "Format a log record as one logfmt line, with the record's extra fields as key=value pairs."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `format`. It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `record` holds `logging.LogRecord`.
- Stores the result of calling `datetime.fromtimestamp(record.created, tz=UTC)....` under the name `timestamp`.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - `datetime.fromtimestamp` from the standard library module `datetime`.

`src/token_meter/infrastructure/logging.py`, lines 26 to 39:

```python
        parts = [
            f"ts={timestamp}",
            f"level={record.levelname}",
            f"logger={record.name}",
            f"msg={_quote(record.getMessage())}",
        ]
        parts.extend(f"{key}={_quote(value)}" for key, value in getattr(record, "fields", {}).items())
        if record.exc_info:
            parts.append(f"exc={_quote(self.formatException(record.exc_info))}")
        return " ".join(parts)


def fields(**values: Any) -> dict[str, Any]:
    """Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs."""
```

- Stores a list of 4 item(s) under the name `parts`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `_quote`, a function defined in this file or passed in.
  - The method `getMessage` of `record`.
- Calls `.extend(...)` adds all the items of another collection to the end of a list with 1 argument(s); the result is not kept.
  - `.extend(...)` adds all the items of another collection to the end of a list.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `.items(...)` gives the key and value pairs of a dictionary.
  - `_quote`, a function defined in this file or passed in.
  - `getattr` reads an attribute whose name is held in a variable.
- Decision: the indented lines below run only when `record.exc_info` is true.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `_quote`, a function defined in this file or passed in.
  - The method `formatException` of `self`.
- Ends the function and gives back the result of calling `' '.join` to the caller.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Defines the function `fields`. It returns a dictionary from text to any value. The author's own description: "Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs."
- Its parameters:
    - `**values` collects any extra named arguments into a dictionary.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/token_meter/infrastructure/logging.py`, lines 40 to 52:

```python
    return {"fields": values}


def configure_logging(level: str, stream: TextIO | None = None) -> None:
    """Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice."""
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(LogfmtFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    quiet = max(logging.getLevelName(level), logging.WARNING)
    for noisy in ("httpx", "httpx2", "httpcore", "httpcore2", "anthropic"):
        logging.getLogger(noisy).setLevel(quiet)
```

- Ends the function and gives back a dictionary with 1 entry to the caller.
- Defines the function `configure_logging`. It returns nothing (None). The author's own description: "Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice."
- Its parameters:
    - `level` holds text.
    - `stream` holds an open text file, or nothing (None); if the caller leaves it out it is nothing (`None`).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores the result of calling `logging.StreamHandler` under the name `handler`.
  - `logging.StreamHandler` from the standard library module `logging`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Calls the method `setFormatter` of `handler` with 1 argument(s); the result is not kept.
  - The method `setFormatter` of `handler`.
  - `LogfmtFormatter`, a class of this project (Format a log record as one logfmt line, with the record's extra fields as key=value pairs.).
- Stores the result of calling `logging.getLogger` under the name `root`.
  - `logging.getLogger` gets the logger with the given name.
- Stores a list of 1 item(s) under the name `root.handlers[:]`.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
- Calls the method `setLevel` of `root` with 1 argument(s); the result is not kept.
  - The method `setLevel` of `root`.
- Stores the result of calling `max` under the name `quiet`.
  - `max` picks the largest value.
  - `logging.getLevelName` from the standard library module `logging`.
- Loop: the indented lines below run once for each item of `('httpx', 'httpx2', 'httpcore', 'httpcore2', 'anthropic')`; `noisy` names the current item.
- Calls the method `setLevel` of `logging.getLogger(noisy)` with 1 argument(s); the result is not kept.
  - The method `setLevel` of `logging.getLogger(noisy)`.
  - `logging.getLogger` gets the logger with the given name.

### `src/token_meter/infrastructure/model_factory.py`

In its own words: "Builds the configured chat model from the environment: recorded, local server or Claude."

65 non-blank lines; it defines `ModelSettings`, `build_chat_model`.

`src/token_meter/infrastructure/model_factory.py`, lines 1 to 14:

```python
"""Builds the configured chat model from the environment: recorded, local server or Claude."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import anthropic
import httpx

from token_meter.application.ports import ChatModel, Clock
from token_meter.infrastructure.anthropic_chat import AnthropicChatModel, Thinking
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `os` (standard library) available.
- Brings in `Mapping` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `Path` from the standard library module `pathlib`.
- Makes the module `anthropic` (installed package) available.
- Makes the module `httpx` (installed package) available.
- Brings in `ChatModel` (One chat model behind one interface: a vendor, a local server or a recording.), `Clock` (Time, injected so tests are deterministic.) from the project module `token_meter.application.ports`.
- Brings in `AnthropicChatModel` (Calls Claude. Build the SDK client with your key from the environment; this class never reads it.), `Thinking` from the project module `token_meter.infrastructure.anthropic_chat`.

`src/token_meter/infrastructure/model_factory.py`, lines 15 to 28:

```python
from token_meter.infrastructure.env import ConfigurationError, choice, optional_text, positive_float, positive_int, text
from token_meter.infrastructure.openai_compatible import OpenAICompatibleChatModel
from token_meter.infrastructure.recording import RecordedChatModel, RecordingChatModel, RecordingStore
from token_meter.infrastructure.resilient import RetryingChatModel

PROVIDERS = ("recorded", "anthropic", "openai-compatible")


@dataclass(frozen=True, slots=True)
class ModelSettings:
    """Which model to call and how. See .env.example for every variable."""

    provider: str
    model: str
```

- Brings in `ConfigurationError` (An environment variable is missing or has an unusable value.), `choice` (One of the `allowed` strings.), `optional_text` (The variable's text, or None when it is unset or blank.), `positive_float` (A number greater than zero.), `positive_int` (An integer of 1 or more.), `text` (A non-empty string, or `default` when the variable is unset.) from the project module `token_meter.infrastructure.env`.
- Brings in `OpenAICompatibleChatModel` (Talks to any server that implements `POST {base_url}/chat/completions`.) from the project module `token_meter.infrastructure.openai_compatible`.
- Brings in `RecordedChatModel` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.), `RecordingChatModel` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.), `RecordingStore` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.) from the project module `token_meter.infrastructure.recording`.
- Brings in `RetryingChatModel` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.) from the project module `token_meter.infrastructure.resilient`.
- Stores a tuple of 3 item(s) under the name `PROVIDERS`.
- Defines the class `ModelSettings`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Which model to call and how. See .env.example for every variable."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `provider` as text; it has no default, so a value must be given when the object is made.
- Declares `model` as text; it has no default, so a value must be given when the object is made.

`src/token_meter/infrastructure/model_factory.py`, lines 29 to 40:

```python
    recordings: Path
    record: bool
    openai_base_url: str
    openai_api_key: str | None
    anthropic_thinking: Thinking
    timeout_seconds: float
    attempts: int

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> ModelSettings:
        env = os.environ if environ is None else environ
        provider = choice(env, "MODEL_PROVIDER", "recorded", PROVIDERS)
```

- Declares `recordings` as a file path; it has no default, so a value must be given when the object is made.
- Declares `record` as true or false; it has no default, so a value must be given when the object is made.
- Declares `openai_base_url` as text; it has no default, so a value must be given when the object is made.
- Declares `openai_api_key` as text, or nothing (None); it has no default, so a value must be given when the object is made.
  - `|` is or; in a type, "either".
- Declares `anthropic_thinking` as `Thinking`; it has no default, so a value must be given when the object is made.
- Declares `timeout_seconds` as a decimal number; it has no default, so a value must be given when the object is made.
- Declares `attempts` as a whole number; it has no default, so a value must be given when the object is made.
- Defines the method `from_env`. `@classmethod` makes it receive the class (`cls`) instead of an object; used as a named constructor. It returns the project type `ModelSettings`.
- Its parameters:
    - `cls` is the class itself (Python passes it automatically).
    - `environ` holds anything that behaves like a dictionary from text to text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Stores one of two values, chosen by a condition under the name `env`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is` means the very same object.
- Stores the result of calling `choice` under the name `provider`.
  - `choice` from the project's `token_meter.infrastructure.env` (One of the `allowed` strings.).

`src/token_meter/infrastructure/model_factory.py`, lines 41 to 44:

```python
        default_model = {"recorded": "recorded", "anthropic": "claude-haiku-5-5", "openai-compatible": "qwen2.5:0.5b"}[
            provider
        ]
        thinking = choice(env, "ANTHROPIC_THINKING", "disabled", ("omit", "disabled", "between_tools"))
```

- Stores the part of `{'recorded': 'recorded', 'a...` picked by `provider` under the name `default_model`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `choice` under the name `thinking`.
  - `choice` from the project's `token_meter.infrastructure.env` (One of the `allowed` strings.).

`src/token_meter/infrastructure/model_factory.py`, lines 45 to 58:

```python
        return cls(
            provider=provider,
            model=text(env, "MODEL_NAME", default_model),
            recordings=Path(text(env, "RECORDINGS_PATH", "tests/fixtures/recordings")),
            record=choice(env, "RECORD", "off", ("on", "off")) == "on",
            openai_base_url=text(env, "OPENAI_BASE_URL", "http://localhost:11434/v1"),
            openai_api_key=optional_text(env, "OPENAI_API_KEY"),
            anthropic_thinking=thinking,  # type: ignore[arg-type]
            timeout_seconds=positive_float(env, "MODEL_TIMEOUT_SECONDS", 120.0),
            attempts=positive_int(env, "MODEL_ATTEMPTS", 3),
        )


def build_chat_model(settings: ModelSettings, clock: Clock, environ: Mapping[str, str] | None = None) -> ChatModel:
```

- Ends the function and gives back the result of calling `cls` to the caller.
  - `cls`, a function defined in this file or passed in.
  - `text` from the project's `token_meter.infrastructure.env` (A non-empty string, or `default` when the variable is unset.).
  - `Path` from the standard library module `pathlib`, which a file or folder location.
  - `==` means equal.
  - `optional_text` from the project's `token_meter.infrastructure.env` (The variable's text, or None when it is unset or blank.).
  - `positive_float` from the project's `token_meter.infrastructure.env` (A number greater than zero.).
  - `positive_int` from the project's `token_meter.infrastructure.env` (An integer of 1 or more.).
  - `choice` from the project's `token_meter.infrastructure.env` (One of the `allowed` strings.).
- Defines the function `build_chat_model`. It returns the project type `ChatModel`. The author's own description: "Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked."
- Its parameters:
    - `settings` holds the project type `ModelSettings`.
    - `clock` holds the project type `Clock`.
    - `environ` holds anything that behaves like a dictionary from text to text, or nothing (None); if the caller leaves it out it is nothing (`None`).

`src/token_meter/infrastructure/model_factory.py`, lines 59 to 72:

```python
    """Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked."""
    env = os.environ if environ is None else environ
    if settings.provider == "recorded":
        return RecordedChatModel(RecordingStore(settings.recordings))
    live: ChatModel
    if settings.provider == "anthropic":
        if not env.get("ANTHROPIC_API_KEY"):
            raise ConfigurationError("ANTHROPIC_API_KEY must be set in the environment to use the anthropic provider")
        client = anthropic.Anthropic(timeout=settings.timeout_seconds, max_retries=0)
        live = AnthropicChatModel(client, settings.model, clock, settings.anthropic_thinking)
    else:
        http = httpx.Client(timeout=settings.timeout_seconds)
        live = OpenAICompatibleChatModel(http, settings.openai_base_url, settings.model, clock, settings.openai_api_key)
    live = RetryingChatModel(live, attempts=settings.attempts)
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Stores one of two values, chosen by a condition under the name `env`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is` means the very same object.
- Decision: the indented lines below run only when `settings.provider == 'recorded'` is true.
  - `==` means equal.
- Ends the function and gives back the result of calling `RecordedChatModel` to the caller.
  - `RecordedChatModel` from the project's `token_meter.infrastructure.recording` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.).
  - `RecordingStore` from the project's `token_meter.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
- Declares `live` as the project type `ChatModel`.
- Decision: the indented lines below run only when `settings.provider == 'anthropic'` is true.
  - `==` means equal.
- Decision: the indented lines below run only when `not env.get('ANTHROPIC_API_KEY')` is true.
  - `not` flips true and false.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
- Raises an error: the result of calling `ConfigurationError`. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError` from the project's `token_meter.infrastructure.env` (An environment variable is missing or has an unusable value.).
- Stores the result of calling `anthropic.Anthropic` under the name `client`.
  - `anthropic.Anthropic` from the installed package module `anthropic`.
- Stores the result of calling `AnthropicChatModel` under the name `live`.
  - `AnthropicChatModel` from the project's `token_meter.infrastructure.anthropic_chat` (Calls Claude. Build the SDK client with your key from the environment; this class never reads it.).
- `else:` — the indented lines below run when none of the conditions above were true.
- Stores the result of calling `httpx.Client` under the name `http`.
  - `httpx.Client` makes an HTTP client.
- Stores the result of calling `OpenAICompatibleChatModel` under the name `live`.
  - `OpenAICompatibleChatModel` from the project's `token_meter.infrastructure.openai_compatible` (Talks to any server that implements `POST {base_url}/chat/completions`.).
- Stores the result of calling `RetryingChatModel` under the name `live`.
  - `RetryingChatModel` from the project's `token_meter.infrastructure.resilient` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.).

`src/token_meter/infrastructure/model_factory.py`, lines 73 to 76:

```python
    if settings.record:
        note = {"provider": settings.provider, "requested_model": settings.model}
        return RecordingChatModel(live, RecordingStore(settings.recordings), note)
    return live
```

- Decision: the indented lines below run only when `settings.record` is true.
- Stores a dictionary with 2 entries under the name `note`.
- Ends the function and gives back the result of calling `RecordingChatModel` to the caller.
  - `RecordingChatModel` from the project's `token_meter.infrastructure.recording` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.).
  - `RecordingStore` from the project's `token_meter.infrastructure.recording` (An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`.).
- Ends the function and gives back the value named `live` to the caller.

### `src/token_meter/infrastructure/openai_compatible.py`

In its own words: "A chat model behind the OpenAI-compatible `/chat/completions` endpoint (Ollama, llama.cpp, vLLM, hosted)."

109 non-blank lines; it defines `_message_payload`, `OpenAICompatibleChatModel`, `_arguments`.

`src/token_meter/infrastructure/openai_compatible.py`, lines 1 to 12:

```python
"""A chat model behind the OpenAI-compatible `/chat/completions` endpoint (Ollama, llama.cpp, vLLM, hosted)."""

from __future__ import annotations

import json
from typing import Any

import httpx

from token_meter.application.ports import Clock
from token_meter.domain.errors import PermanentModelError, TransientModelError
from token_meter.domain.llm import ChatMessage, ChatRequest, ChatResponse, Role, StopReason, ToolCall, Usage
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Brings in `Any` from the standard library module `typing`.
- Makes the module `httpx` (installed package) available.
- Brings in `Clock` (Time, injected so tests are deterministic.) from the project module `token_meter.application.ports`.
- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.) from the project module `token_meter.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.), `Role` (Who wrote a message.), `StopReason` (Why the model stopped writing.), `ToolCall` (A tool call the model asked for.), `Usage` (Tokens the provider billed for one call, read from its usage block, never recomputed.) from the project module `token_meter.domain.llm`.

`src/token_meter/infrastructure/openai_compatible.py`, lines 14 to 26:

```python
_FINISH = {
    "stop": StopReason.END,
    "length": StopReason.LENGTH,
    "tool_calls": StopReason.TOOL_CALLS,
    "content_filter": StopReason.REFUSAL,
}


def _message_payload(message: ChatMessage) -> dict[str, Any]:
    if message.role is Role.TOOL:
        return {"role": "tool", "tool_call_id": message.tool_call_id, "content": message.content}
    payload: dict[str, Any] = {"role": message.role.value, "content": message.content}
    if message.tool_calls:
```

- Stores a dictionary with 4 entries under the name `_FINISH`.
- Defines the function `_message_payload`. It returns a dictionary from text to any value.
- Its parameters:
    - `message` holds the project type `ChatMessage`.
- Decision: the indented lines below run only when `message.role is Role.TOOL` is true.
  - `is` means the very same object.
- Ends the function and gives back a dictionary with 3 entries to the caller.
- Declares `payload` as a dictionary from text to any value and sets it to a dictionary with 2 entries.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `message.tool_calls` is true.

`src/token_meter/infrastructure/openai_compatible.py`, lines 27 to 40:

```python
        payload["tool_calls"] = [
            {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": json.dumps(dict(c.arguments))}}
            for c in message.tool_calls
        ]
    return payload


class OpenAICompatibleChatModel:
    """Talks to any server that implements `POST {base_url}/chat/completions`."""

    def __init__(self, http: httpx.Client, base_url: str, model: str, clock: Clock, api_key: str | None = None) -> None:
        self._http = http
        self._base_url = base_url.rstrip("/")
        self._model = model
```

- Stores a list built by looping under the name `payload['tool_calls']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `json.dumps` turns Python data into JSON text.
  - `dict` makes a dictionary (a copy when given one).
- Ends the function and gives back the value named `payload` to the caller.
- Defines the class `OpenAICompatibleChatModel`. The author's own description: "Talks to any server that implements `POST {base_url}/chat/completions`."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `http` holds `httpx.Client`.
    - `base_url` holds text.
    - `model` holds text.
    - `clock` holds the project type `Clock`.
    - `api_key` holds text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Stores the value named `http` under the name `self._http` (as an attribute of this object, so other methods can use it).
- Stores the result of calling `base_url.rstrip` under the name `self._base_url` (as an attribute of this object, so other methods can use it).
  - `.rstrip(...)` removes spaces from the end of text.
- Stores the value named `model` under the name `self._model` (as an attribute of this object, so other methods can use it).

`src/token_meter/infrastructure/openai_compatible.py`, lines 41 to 54:

```python
        self._clock = clock
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    @property
    def name(self) -> str:
        return self._model

    @property
    def supports_sampling(self) -> bool:
        return True

    def build_payload(self, request: ChatRequest) -> dict[str, Any]:
        """The JSON body for a request (public so tests can assert on it)."""
        messages: list[dict[str, Any]] = []
```

- Stores the value named `clock` under the name `self._clock` (as an attribute of this object, so other methods can use it).
- Stores one of two values, chosen by a condition under the name `self._headers` (as an attribute of this object, so other methods can use it).
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `_model` of this object to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the value `True` to the caller.
- Defines the method `build_payload`. It returns a dictionary from text to any value. The author's own description: "The JSON body for a request (public so tests can assert on it)."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `messages` as a list of a dictionary from text to any value and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`src/token_meter/infrastructure/openai_compatible.py`, lines 55 to 68:

```python
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.extend(_message_payload(m) for m in request.messages)
        payload: dict[str, Any] = {
            "model": request.model or self._model,
            "messages": messages,
            "max_tokens": request.max_output_tokens,
            "stream": False,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.top_p is not None:
            payload["top_p"] = request.top_p
        if request.response_schema is not None:
```

- Decision: the indented lines below run only when `request.system` is true.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Calls `.extend(...)` adds all the items of another collection to the end of a list with 1 argument(s); the result is not kept.
  - `.extend(...)` adds all the items of another collection to the end of a list.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `_message_payload`, a function defined in this file or passed in.
- Declares `payload` as a dictionary from text to any value and sets it to a dictionary with 4 entries.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
- Decision: the indented lines below run only when `request.temperature is not None` is true.
  - `is not` means not the same object.
- Stores the `temperature` of `request` under the name `payload['temperature']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `request.top_p is not None` is true.
  - `is not` means not the same object.
- Stores the `top_p` of `request` under the name `payload['top_p']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Decision: the indented lines below run only when `request.response_schema is not None` is true.
  - `is not` means not the same object.

`src/token_meter/infrastructure/openai_compatible.py`, lines 69 to 81:

```python
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": dict(request.response_schema), "strict": True},
            }
        if request.tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {"name": t.name, "description": t.description, "parameters": dict(t.parameters)},
                }
                for t in request.tools
            ]
        return payload
```

- Stores a dictionary with 2 entries under the name `payload['response_format']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `dict` makes a dictionary (a copy when given one).
- Decision: the indented lines below run only when `request.tools` is true.
- Stores a list built by looping under the name `payload['tools']`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `dict` makes a dictionary (a copy when given one).
- Ends the function and gives back the value named `payload` to the caller.

`src/token_meter/infrastructure/openai_compatible.py`, lines 83 to 95:

```python
    def complete(self, request: ChatRequest) -> ChatResponse:
        started = self._clock.monotonic()
        try:
            reply = self._http.post(
                f"{self._base_url}/chat/completions", json=self.build_payload(request), headers=self._headers
            )
        except httpx.TransportError as error:
            raise TransientModelError(f"{type(error).__name__}: {error}") from error
        elapsed = self._clock.monotonic() - started
        if reply.status_code == 429 or reply.status_code >= 500:
            raise TransientModelError(f"HTTP {reply.status_code}")
        if reply.status_code >= 400:
            raise PermanentModelError(f"HTTP {reply.status_code}: {reply.text[:200]}")
```

- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Stores the result of calling `self._clock.monotonic` under the name `started`.
  - The method `monotonic` of `self._clock`.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the result of calling `self._http.post` under the name `reply`.
  - `post` on the stored object `self._http`: it sends an HTTP POST request.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - The method `build_payload` of this object (The JSON body for a request (public so tests can assert on it).).
- `except` handler: it runs when the `try` block raised `httpx.TransportError`; `error` names the error object.
- Raises an error: the result of calling `TransientModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `token_meter.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `type` gives the type (class) of a value.
- Stores the result of `self._clock.monotonic() - started` under the name `elapsed`.
  - `-` is subtract.
  - The method `monotonic` of `self._clock`.
- Decision: the indented lines below run only when `reply.status_code == 429 or reply.status_code >= 500` is true.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `==` means equal.
  - `>=` means greater than or equal.
- Raises an error: the result of calling `TransientModelError`. Execution jumps out to the nearest matching `except`.
  - `TransientModelError` from the project's `token_meter.domain.errors` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Decision: the indented lines below run only when `reply.status_code >= 400` is true.
  - `>=` means greater than or equal.
- Raises an error: the result of calling `PermanentModelError`. Execution jumps out to the nearest matching `except`.
  - `PermanentModelError` from the project's `token_meter.domain.errors` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.

`src/token_meter/infrastructure/openai_compatible.py`, lines 96 to 107:

```python
        return self._parse(reply.json(), elapsed)

    def _parse(self, body: dict[str, Any], elapsed: float) -> ChatResponse:
        try:
            choice = body["choices"][0]
            message = choice["message"]
            usage = body["usage"]
            calls = tuple(
                ToolCall(str(c.get("id", f"call_{i}")), c["function"]["name"], _arguments(c["function"]["arguments"]))
                for i, c in enumerate(message.get("tool_calls") or [])
            )
            stop = StopReason.TOOL_CALLS if calls else _FINISH.get(choice.get("finish_reason") or "", StopReason.OTHER)
```

- Ends the function and gives back the result of calling `self._parse` to the caller.
  - The method `_parse` of this object.
  - `.json(...)` reads the body of an HTTP answer as JSON.
- Defines the method `_parse`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `body` holds a dictionary from text to any value.
    - `elapsed` holds a decimal number.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores the part of `body['choices']` picked by `0` under the name `choice`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the part of `choice` picked by `'message'` under the name `message`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the part of `body` picked by `'usage'` under the name `usage`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `tuple` under the name `calls`.
  - `tuple` makes a tuple: a fixed list that cannot be changed.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `ToolCall` from the project's `token_meter.domain.llm` (A tool call the model asked for.).
  - `str` turns a value into text.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `_arguments`, a function defined in this file or passed in.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Stores one of two values, chosen by a condition under the name `stop`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).

`src/token_meter/infrastructure/openai_compatible.py`, lines 108 to 121:

```python
            return ChatResponse(
                text=message.get("content") or "",
                stop_reason=stop,
                usage=Usage(int(usage["prompt_tokens"]), int(usage["completion_tokens"])),
                latency_seconds=round(elapsed, 4),
                model=str(body.get("model", self._model)),
                tool_calls=calls,
            )
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise PermanentModelError(f"unexpected response shape: {error!r}") from error


def _arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
```

- Ends the function and gives back the result of calling `ChatResponse` to the caller.
  - `ChatResponse` from the project's `token_meter.domain.llm` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.).
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `Usage` from the project's `token_meter.domain.llm` (Tokens the provider billed for one call, read from its usage block, never recomputed.).
  - `round` rounds a number.
  - `str` turns a value into text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.
  - `int` turns a value into a whole number.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- `except` handler: it runs when the `try` block raised `(KeyError, IndexError, TypeError, ValueError)`; `error` names the error object.
- Raises an error: the result of calling `PermanentModelError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `PermanentModelError` from the project's `token_meter.domain.errors` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
- Defines the function `_arguments`. It returns a dictionary from text to any value.
- Its parameters:
    - `raw` holds any value.
- Decision: the indented lines below run only when `isinstance(raw, dict)` is true.
  - `isinstance` asks whether a value is of a given type.

`src/token_meter/infrastructure/openai_compatible.py`, lines 122 to 126:

```python
        return raw
    parsed = json.loads(raw) if raw else {}
    if not isinstance(parsed, dict):
        raise ValueError("tool arguments must be a JSON object")
    return parsed
```

- Ends the function and gives back the value named `raw` to the caller.
- Stores one of two values, chosen by a condition under the name `parsed`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `json.loads` turns JSON text into Python data.
- Decision: the indented lines below run only when `not isinstance(parsed, dict)` is true.
  - `not` flips true and false.
  - `isinstance` asks whether a value is of a given type.
- Raises an error: the result of calling `ValueError`. Execution jumps out to the nearest matching `except`.
  - `ValueError` an error for a value that is the right type but unusable.
- Ends the function and gives back the value named `parsed` to the caller.

### `src/token_meter/infrastructure/recording.py`

In its own words: "Recorded responses: replay them in tests and demos, or record a live model's answers into fixtures."

79 non-blank lines; it defines `RecordingStore`, `RecordedChatModel`, `RecordingChatModel`.

`src/token_meter/infrastructure/recording.py`, lines 1 to 13:

```python
"""Recorded responses: replay them in tests and demos, or record a live model's answers into fixtures.

A recording is a JSON Lines file. Each line holds the request fingerprint, the call's tag, a note about what
produced it and the response. Fixtures hold synthetic data only (no credentials, no personal data).
"""

from __future__ import annotations

import json
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Any
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Makes the module `threading` (standard library) available.
- Brings in `Mapping` from the standard library module `collections.abc`.
- Brings in `Path` from the standard library module `pathlib`.
- Brings in `Any` from the standard library module `typing`.

`src/token_meter/infrastructure/recording.py`, lines 15 to 27:

```python
from token_meter.application.ports import ChatModel
from token_meter.domain.errors import RecordingMissing
from token_meter.domain.llm import ChatRequest, ChatResponse


class RecordingStore:
    """An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._entries: dict[str, dict[str, Any]] = {}
        files = sorted(path.glob("*.jsonl")) if path.is_dir() else ([path] if path.exists() else [])
```

- Brings in `ChatModel` (One chat model behind one interface: a vendor, a local server or a recording.) from the project module `token_meter.application.ports`.
- Brings in `RecordingMissing` (The recorded adapter has no response for this request. Re-record with `make record`.) from the project module `token_meter.domain.errors`.
- Brings in `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.) from the project module `token_meter.domain.llm`.
- Defines the class `RecordingStore`. The author's own description: "An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `path` holds a file path.
- Stores the value named `path` under the name `self._path` (as an attribute of this object, so other methods can use it).
- Stores the result of calling `threading.Lock` under the name `self._lock` (as an attribute of this object, so other methods can use it).
  - `threading.Lock` makes a lock.
- Declares `self._entries` as a dictionary from text to a dictionary from text to any value and sets it to an empty dictionary.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores one of two values, chosen by a condition under the name `files`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.is_dir(...)` asks whether the path is a folder.
  - `sorted` returns a new list with the items in order.
  - `.glob(...)` finds files whose names match a pattern.
  - `.exists(...)` asks whether the path exists.

`src/token_meter/infrastructure/recording.py`, lines 28 to 41:

```python
        for file in files:
            with file.open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        entry = json.loads(line)
                        self._entries[entry["key"]] = entry
        self._append_to = path / "recorded.jsonl" if path.is_dir() else path

    def __len__(self) -> int:
        return len(self._entries)

    def get(self, key: str) -> ChatResponse | None:
        with self._lock:
            entry = self._entries.get(key)
```

- Loop: the indented lines below run once for each item of `files`; `file` names the current item.
- A `with` block: it sets up `file.open(encoding='utf-8')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `file`.
- Loop: the indented lines below run once for each item of `handle`; `line` names the current item.
- Decision: the indented lines below run only when `line.strip()` is true.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
- Stores the result of calling `json.loads` under the name `entry`.
  - `json.loads` turns JSON text into Python data.
- Stores the value named `entry` under the name `self._entries[entry['key']]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores one of two values, chosen by a condition under the name `self._append_to` (as an attribute of this object, so other methods can use it).
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `.is_dir(...)` asks whether the path is a folder.
  - `/` is divide.
- Defines the method `__len__`. It returns a whole number.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the result of calling `len` to the caller.
  - `len` counts the items in a collection (or the characters in text).
- Defines the method `get`. It returns the project type `ChatResponse`, or nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `key` holds text.
- A `with` block: it sets up `self._lock`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
- Stores the result of calling `self._entries.get` under the name `entry`.
  - `get` on the stored object `self._entries`: it reads a dictionary entry, giving a default when the key is missing.

`src/token_meter/infrastructure/recording.py`, lines 42 to 55:

```python
        return ChatResponse.from_json(entry["response"]) if entry else None

    def put(self, key: str, tag: str, response: ChatResponse, recorded_with: Mapping[str, Any]) -> None:
        entry = {"key": key, "tag": tag, "recorded_with": dict(recorded_with), "response": response.to_json()}
        with self._lock:
            self._entries[key] = entry
            self._append_to.parent.mkdir(parents=True, exist_ok=True)
            with self._append_to.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")
                handle.flush()


class RecordedChatModel:
    """Replays recorded responses. A request nobody recorded raises `RecordingMissing`."""
```

- Ends the function and gives back one of two values, chosen by a condition to the caller.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - The method `from_json` of `ChatResponse`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Defines the method `put`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `key` holds text.
    - `tag` holds text.
    - `response` holds the project type `ChatResponse`.
    - `recorded_with` holds anything that behaves like a dictionary from text to any value.
- Stores a dictionary with 4 entries under the name `entry`.
  - `dict` makes a dictionary (a copy when given one).
  - The method `to_json` of `response`.
- A `with` block: it sets up `self._lock`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
- Stores the value named `entry` under the name `self._entries[key]`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Calls `mkdir` on the stored object `self._append_to.parent`: it creates a folder with 2 argument(s); the result is not kept.
  - `mkdir` on the stored object `self._append_to.parent`: it creates a folder.
- A `with` block: it sets up `self._append_to.open('a', encoding='utf-8')` as `handle`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `open` of `self._append_to`.
- Calls `.write(...)` writes text or bytes to an open file with 1 argument(s); the result is not kept.
  - `.write(...)` writes text or bytes to an open file.
  - `+` is add.
  - `json.dumps` turns Python data into JSON text.
- Calls `.flush(...)` pushes buffered output to the operating system; the result is not kept.
  - `.flush(...)` pushes buffered output to the operating system.
- Defines the class `RecordedChatModel`. The author's own description: "Replays recorded responses. A request nobody recorded raises `RecordingMissing`."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/token_meter/infrastructure/recording.py`, lines 57 to 69:

```python
    def __init__(self, store: RecordingStore) -> None:
        self._store = store

    @property
    def name(self) -> str:
        return "recorded"

    @property
    def supports_sampling(self) -> bool:
        return True

    def complete(self, request: ChatRequest) -> ChatResponse:
        response = self._store.get(request.fingerprint())
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `store` holds the project type `RecordingStore`.
- Stores the value named `store` under the name `self._store` (as an attribute of this object, so other methods can use it).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the text `recorded` to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the value `True` to the caller.
- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Stores the result of calling `self._store.get` under the name `response`.
  - `get` on the stored object `self._store`: it reads a dictionary entry, giving a default when the key is missing.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).

`src/token_meter/infrastructure/recording.py`, lines 70 to 83:

```python
        if response is None:
            raise RecordingMissing(
                f"no recording for request tag={request.tag!r} fingerprint={request.fingerprint()[:12]}; "
                "run `make record` against a live model to refresh the fixtures"
            )
        return response


class RecordingChatModel:
    """Wraps a live model and writes each answer into a recording. A request already recorded is replayed."""

    def __init__(self, inner: ChatModel, store: RecordingStore, note: Mapping[str, Any]) -> None:
        self._inner = inner
        self._store = store
```

- Decision: the indented lines below run only when `response is None` is true.
  - `is` means the very same object.
- Raises an error: the result of calling `RecordingMissing`. Execution jumps out to the nearest matching `except`.
  - `RecordingMissing` from the project's `token_meter.domain.errors` (The recorded adapter has no response for this request. Re-record with `make record`.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `x[a:b]` takes the items from position a up to (not including) b; a missing end means the start or the end.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
- Ends the function and gives back the value named `response` to the caller.
- Defines the class `RecordingChatModel`. The author's own description: "Wraps a live model and writes each answer into a recording. A request already recorded is replayed."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `inner` holds the project type `ChatModel`.
    - `store` holds the project type `RecordingStore`.
    - `note` holds anything that behaves like a dictionary from text to any value.
- Stores the value named `inner` under the name `self._inner` (as an attribute of this object, so other methods can use it).
- Stores the value named `store` under the name `self._store` (as an attribute of this object, so other methods can use it).

`src/token_meter/infrastructure/recording.py`, lines 84 to 97:

```python
        self._note = dict(note)

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def supports_sampling(self) -> bool:
        return self._inner.supports_sampling

    def complete(self, request: ChatRequest) -> ChatResponse:
        key = request.fingerprint()
        cached = self._store.get(key)
        if cached is not None:
```

- Stores the result of calling `dict` under the name `self._note` (as an attribute of this object, so other methods can use it).
  - `dict` makes a dictionary (a copy when given one).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `name` of this object to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `supports_sampling` of this object to the caller.
- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Stores the result of calling `request.fingerprint` under the name `key`.
  - The method `fingerprint` of the project's `ChatRequest` (A stable hash of the request, used to find its recording. The model name is excluded.).
- Stores the result of calling `self._store.get` under the name `cached`.
  - `get` on the stored object `self._store`: it reads a dictionary entry, giving a default when the key is missing.
- Decision: the indented lines below run only when `cached is not None` is true.
  - `is not` means not the same object.

`src/token_meter/infrastructure/recording.py`, lines 98 to 101:

```python
            return cached
        response = self._inner.complete(request)
        self._store.put(key, request.tag, response, {**self._note, "model": response.model})
        return response
```

- Ends the function and gives back the value named `cached` to the caller.
- Stores the result of calling `self._inner.complete` under the name `response`.
  - The method `complete` of `self._inner`.
- Calls `put` on the stored object `self._store`: it sends an HTTP PUT request with 4 argument(s); the result is not kept.
  - `put` on the stored object `self._store`: it sends an HTTP PUT request.
- Ends the function and gives back the value named `response` to the caller.

### `src/token_meter/infrastructure/resilient.py`

In its own words: "A decorator that retries transient model failures with backoff and jitter."

48 non-blank lines; it defines `RetryingChatModel`.

`src/token_meter/infrastructure/resilient.py`, lines 1 to 14:

```python
"""A decorator that retries transient model failures with backoff and jitter."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable

from token_meter.application.ports import ChatModel
from token_meter.domain.errors import TransientModelError
from token_meter.domain.llm import ChatRequest, ChatResponse
from token_meter.infrastructure.logging import fields
from token_meter.infrastructure.retry import retry
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `logging` (standard library) available.
- Makes the module `random` (standard library) available.
- Makes the module `time` (standard library) available.
- Brings in `Callable` from the standard library module `collections.abc`.
- Brings in `ChatModel` (One chat model behind one interface: a vendor, a local server or a recording.) from the project module `token_meter.application.ports`.
- Brings in `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.) from the project module `token_meter.domain.errors`.
- Brings in `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.) from the project module `token_meter.domain.llm`.
- Brings in `fields` (Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs.) from the project module `token_meter.infrastructure.logging`.
- Brings in `retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.) from the project module `token_meter.infrastructure.retry`.

`src/token_meter/infrastructure/resilient.py`, lines 16 to 20:

```python
_log = logging.getLogger(__name__)


class RetryingChatModel:
    """Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once."""
```

- Stores the result of calling `logging.getLogger` under the name `_log`.
  - `logging.getLogger` gets the logger with the given name.
- Defines the class `RetryingChatModel`. The author's own description: "Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.

`src/token_meter/infrastructure/resilient.py`, lines 22 to 34:

```python
    def __init__(
        self,
        inner: ChatModel,
        *,
        attempts: int = 3,
        base_delay_seconds: float = 0.5,
        sleep: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
    ) -> None:
        self._inner = inner
        self._attempts = attempts
        self._base_delay = base_delay_seconds
        self._sleep = sleep
```

- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `inner` holds the project type `ChatModel`.
    - `attempts` holds a whole number; if the caller leaves it out it is the number `3`; it must be passed by name.
    - `base_delay_seconds` holds a decimal number; if the caller leaves it out it is the number `0.5`; it must be passed by name.
    - `sleep` holds a function; if the caller leaves it out it is the `sleep` of `time`; it must be passed by name.
    - `rng` holds `random.Random`, or nothing (None); if the caller leaves it out it is nothing (`None`); it must be passed by name.
- Stores the value named `inner` under the name `self._inner` (as an attribute of this object, so other methods can use it).
- Stores the value named `attempts` under the name `self._attempts` (as an attribute of this object, so other methods can use it).
- Stores the value named `base_delay_seconds` under the name `self._base_delay` (as an attribute of this object, so other methods can use it).
- Stores the value named `sleep` under the name `self._sleep` (as an attribute of this object, so other methods can use it).

`src/token_meter/infrastructure/resilient.py`, lines 35 to 46:

```python
        self._rng = rng

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def supports_sampling(self) -> bool:
        return self._inner.supports_sampling

    def complete(self, request: ChatRequest) -> ChatResponse:
        def log_retry(attempt: int, error: BaseException) -> None:
```

- Stores the value named `rng` under the name `self._rng` (as an attribute of this object, so other methods can use it).
- Defines the method `name`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns text.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `name` of this object to the caller.
- Defines the method `supports_sampling`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Ends the function and gives back the attribute `supports_sampling` of this object to the caller.
- Defines the method `complete`. It returns the project type `ChatResponse`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request` holds the project type `ChatRequest`.
- Defines the function `log_retry`. It returns nothing (None).
- Its parameters:
    - `attempt` holds a whole number.
    - `error` holds `BaseException`.

`src/token_meter/infrastructure/resilient.py`, lines 47 to 59:

```python
            _log.warning(
                "model call failed, retrying", extra=fields(tag=request.tag, attempt=attempt, error=str(error))
            )

        return retry(
            lambda: self._inner.complete(request),
            attempts=self._attempts,
            base_delay_seconds=self._base_delay,
            retry_on=(TransientModelError,),
            sleep=self._sleep,
            rng=self._rng,
            on_retry=log_retry,
        )
```

- Calls the method `warning` of `_log` with 2 argument(s); the result is not kept.
  - The method `warning` of `_log`.
  - `fields` from the project's `token_meter.infrastructure.logging` (Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs.).
  - `str` turns a value into text.
- Ends the function and gives back the result of calling `retry` to the caller.
  - `retry` from the project's `token_meter.infrastructure.retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.).
  - `lambda args: expression` is a small unnamed function written inline.
  - The method `complete` of `self._inner`.

### `src/token_meter/infrastructure/retry.py`

In its own words: "Retry with exponential backoff and jitter for calls that cross the network."

33 non-blank lines; it defines `retry`.

`src/token_meter/infrastructure/retry.py`, lines 1 to 7:

```python
"""Retry with exponential backoff and jitter for calls that cross the network."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `random` (standard library) available.
- Makes the module `time` (standard library) available.
- Brings in `Callable` from the standard library module `collections.abc`.

`src/token_meter/infrastructure/retry.py`, lines 10 to 20:

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
```

- Defines the function `retry`. It returns `T`. The author's own description: "Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`."
- Its parameters:
    - `operation` holds a function.
    - `attempts` holds a whole number; it must be passed by name.
    - `base_delay_seconds` holds a decimal number; it must be passed by name.
    - `retry_on` holds a fixed list of type of `BaseException` (any length); it must be passed by name.
    - `sleep` holds a function; if the caller leaves it out it is the `sleep` of `time`; it must be passed by name.
    - `rng` holds `random.Random`, or nothing (None); if the caller leaves it out it is nothing (`None`); it must be passed by name.
    - `max_delay_seconds` holds a decimal number; if the caller leaves it out it is the number `10.0`; it must be passed by name.
    - `on_retry` holds a function, or nothing (None); if the caller leaves it out it is nothing (`None`); it must be passed by name.

`src/token_meter/infrastructure/retry.py`, lines 21 to 34:

```python
    """Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.

    The pause is `base * 2**(attempt - 1)` capped at `max_delay_seconds`, then scaled by a random
    factor in [0.5, 1.0] so many clients do not retry in step. The last failure is raised.
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    jitter = rng or random.Random()
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except retry_on as error:
            if attempt == attempts:
                raise
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Decision: the indented lines below run only when `attempts < 1` is true.
  - `<` means less than.
- Raises an error: the result of calling `ValueError`. Execution jumps out to the nearest matching `except`.
  - `ValueError` an error for a value that is the right type but unusable.
- Stores the result of combining conditions: `rng or random.Random()` under the name `jitter`.
  - `and` is true only if both sides are true; `or` is true if either is (and gives the first true value).
  - `random.Random` makes a random-number generator that repeats for the same seed.
- Loop: the indented lines below run once for each item of `range(1, attempts + 1)`; `attempt` names the current item.
  - `range` makes the numbers from 0 up to (not including) the given one.
  - `+` is add.
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Ends the function and gives back the result of calling `operation` to the caller.
  - `operation`, a function defined in this file or passed in.
- `except` handler: it runs when the `try` block raised `retry_on`; `error` names the error object.
- Decision: the indented lines below run only when `attempt == attempts` is true.
  - `==` means equal.
- Raises an error again (the one being handled). Execution jumps out to the nearest matching `except`.

`src/token_meter/infrastructure/retry.py`, lines 35 to 38:

```python
            if on_retry:
                on_retry(attempt, error)
            sleep(min(max_delay_seconds, base_delay_seconds * 2 ** (attempt - 1)) * jitter.uniform(0.5, 1.0))
    raise AssertionError("unreachable")  # pragma: no cover
```

- Decision: the indented lines below run only when `on_retry` is true.
- Calls `on_retry`, a function defined in this file or passed in with 2 argument(s); the result is not kept.
  - `on_retry`, a function defined in this file or passed in.
- Calls `sleep`, a function defined in this file or passed in with 1 argument(s); the result is not kept.
  - `sleep`, a function defined in this file or passed in.
  - `*` is multiply.
  - `min` picks the smallest value.
  - The method `uniform` of `jitter`.
  - `**` is power.
  - `-` is subtract.
- Raises an error: the result of calling `AssertionError`. Execution jumps out to the nearest matching `except`.
  - `AssertionError` the error an `assert` raises.

### `src/token_meter/infrastructure/settings.py`

In its own words: "Configuration from the environment, validated once at startup (twelve-factor)."

47 non-blank lines; it defines `MeterSettings`.

`src/token_meter/infrastructure/settings.py`, lines 1 to 9:

```python
"""Configuration from the environment, validated once at startup (twelve-factor)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `os` (standard library) available.
- Brings in `Mapping` from the standard library module `collections.abc`.
- Brings in `dataclass` from the standard library module `dataclasses`.
- Brings in `Decimal`, `InvalidOperation` from the standard library module `decimal`.
- Brings in `Path` from the standard library module `pathlib`.

`src/token_meter/infrastructure/settings.py`, lines 11 to 20:

```python
from token_meter.infrastructure.env import (
    ConfigurationError,
    choice,
    non_negative_float,
    optional_text,
    positive_int,
    text,
)

_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")
```

- Brings in `ConfigurationError` (An environment variable is missing or has an unusable value.), `choice` (One of the `allowed` strings.), `non_negative_float` (A number of 0 or more.), `optional_text` (The variable's text, or None when it is unset or blank.), `positive_int` (An integer of 1 or more.), `text` (A non-empty string, or `default` when the variable is unset.) from the project module `token_meter.infrastructure.env`.
- Stores a tuple of 4 item(s) under the name `_LEVELS`.

`src/token_meter/infrastructure/settings.py`, lines 23 to 34:

```python
@dataclass(frozen=True, slots=True)
class MeterSettings:
    """Everything the programs read from the environment. See .env.example for each variable."""

    prompts_path: Path
    prices_path: Path
    journal_path: Path
    max_output_tokens: int
    repeats: int
    price_max_age_days: int
    throttle_seconds: float
    budget: Decimal | None
```

- Defines the class `MeterSettings`. `@dataclass` writes the boring parts of the class (the constructor, the text form, equality) from the annotated fields. `frozen=True` forbids changing an object after creation; `slots=True` stores fields compactly. The author's own description: "Everything the programs read from the environment. See .env.example for each variable."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Declares `prompts_path` as a file path; it has no default, so a value must be given when the object is made.
- Declares `prices_path` as a file path; it has no default, so a value must be given when the object is made.
- Declares `journal_path` as a file path; it has no default, so a value must be given when the object is made.
- Declares `max_output_tokens` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `repeats` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `price_max_age_days` as a whole number; it has no default, so a value must be given when the object is made.
- Declares `throttle_seconds` as a decimal number; it has no default, so a value must be given when the object is made.
- Declares `budget` as an exact decimal number, or nothing (None); it has no default, so a value must be given when the object is made.
  - `|` is or; in a type, "either".

`src/token_meter/infrastructure/settings.py`, lines 35 to 44:

```python
    log_level: str

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> MeterSettings:
        env = os.environ if environ is None else environ
        raw_budget = optional_text(env, "BUDGET_USD")
        try:
            budget = Decimal(raw_budget) if raw_budget else None
        except InvalidOperation as error:
            raise ConfigurationError(f"BUDGET_USD must be a decimal number, got {raw_budget!r}") from error
```

- Declares `log_level` as text; it has no default, so a value must be given when the object is made.
- Defines the method `from_env`. `@classmethod` makes it receive the class (`cls`) instead of an object; used as a named constructor. It returns the project type `MeterSettings`.
- Its parameters:
    - `cls` is the class itself (Python passes it automatically).
    - `environ` holds anything that behaves like a dictionary from text to text, or nothing (None); if the caller leaves it out it is nothing (`None`).
- Stores one of two values, chosen by a condition under the name `env`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `is` means the very same object.
- Stores the result of calling `optional_text` under the name `raw_budget`.
  - `optional_text` from the project's `token_meter.infrastructure.env` (The variable's text, or None when it is unset or blank.).
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Stores one of two values, chosen by a condition under the name `budget`.
  - `A if condition else B` gives A when the condition is true and B otherwise.
  - `Decimal` from the standard library module `decimal`.
- `except` handler: it runs when the `try` block raised `InvalidOperation`; `error` names the error object.
- Raises an error: the result of calling `ConfigurationError`, recording `error` as its cause. Execution jumps out to the nearest matching `except`.
  - `ConfigurationError` from the project's `token_meter.infrastructure.env` (An environment variable is missing or has an unusable value.).
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.

`src/token_meter/infrastructure/settings.py`, lines 45 to 55:

```python
        return cls(
            prompts_path=Path(text(env, "PROMPTS_PATH", "data/prompts.jsonl")),
            prices_path=Path(text(env, "PRICES_PATH", "data/prices.json")),
            journal_path=Path(text(env, "JOURNAL_PATH", "out/journal.csv")),
            max_output_tokens=positive_int(env, "MAX_OUTPUT_TOKENS", 200),
            repeats=positive_int(env, "REPEATS", 3),
            price_max_age_days=positive_int(env, "PRICE_MAX_AGE_DAYS", 30),
            throttle_seconds=non_negative_float(env, "THROTTLE_SECONDS", 0.0),
            budget=budget,
            log_level=choice({**env, "LOG_LEVEL": env.get("LOG_LEVEL", "INFO").upper()}, "LOG_LEVEL", "INFO", _LEVELS),
        )
```

- Ends the function and gives back the result of calling `cls` to the caller.
  - `cls`, a function defined in this file or passed in.
  - `Path` from the standard library module `pathlib`, which a file or folder location.
  - `positive_int` from the project's `token_meter.infrastructure.env` (An integer of 1 or more.).
  - `non_negative_float` from the project's `token_meter.infrastructure.env` (A number of 0 or more.).
  - `choice` from the project's `token_meter.infrastructure.env` (One of the `allowed` strings.).
  - `text` from the project's `token_meter.infrastructure.env` (A non-empty string, or `default` when the variable is unset.).
  - `.upper(...)` turns text into upper case.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

### `src/token_meter/infrastructure/shutdown.py`

In its own words: "Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work."

20 non-blank lines; it defines `ShutdownSignal`.

`src/token_meter/infrastructure/shutdown.py`, lines 1 to 14:

```python
"""Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work."""

from __future__ import annotations

import signal
import threading
from types import FrameType


class ShutdownSignal:
    """A flag that SIGINT and SIGTERM set, which work loops check between units of work."""

    def __init__(self) -> None:
        self._requested = threading.Event()
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `signal` (standard library) available.
- Makes the module `threading` (standard library) available.
- Brings in `FrameType` from the standard library module `types`.
- Defines the class `ShutdownSignal`. The author's own description: "A flag that SIGINT and SIGTERM set, which work loops check between units of work."
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Defines the method `__init__`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Stores the result of calling `threading.Event` under the name `self._requested` (as an attribute of this object, so other methods can use it).
  - `threading.Event` makes a flag shared between threads.

`src/token_meter/infrastructure/shutdown.py`, lines 16 to 28:

```python
    def install(self) -> None:
        """Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close."""
        for number in (signal.SIGINT, signal.SIGTERM):
            signal.signal(number, self._handle)

    def _handle(self, _number: int, _frame: FrameType | None) -> None:
        self.request()

    def request(self) -> None:
        self._requested.set()

    @property
    def requested(self) -> bool:
```

- Defines the method `install`. It returns nothing (None). The author's own description: "Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close."
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- Loop: the indented lines below run once for each item of `(signal.SIGINT, signal.SIGTERM)`; `number` names the current item.
- Calls `signal.signal` installs a function to run when a signal arrives with 2 argument(s); the result is not kept.
  - `signal.signal` installs a function to run when a signal arrives.
- Defines the method `_handle`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `_number` holds a whole number.
    - `_frame` holds a stack frame, or nothing (None).
- Calls the method `request` of this object; the result is not kept.
  - The method `request` of this object.
- Defines the method `request`. It returns nothing (None).
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
- Calls `set` on the stored object `self._requested`: it raises a flag (an Event); the result is not kept.
  - `set` on the stored object `self._requested`: it raises a flag (an Event).
- Defines the method `requested`. `@property` lets callers read the method like a field (`obj.name`, without parentheses). It returns true or false.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).

`src/token_meter/infrastructure/shutdown.py`, lines 29 to 29:

```python
        return self._requested.is_set()
```

- Ends the function and gives back the result of calling `self._requested.is_set` to the caller.
  - `is_set` on the stored object `self._requested`: it asks whether a flag is raised.

## Try it yourself

1. Every module carries its own description in `__doc__`; this prints the first file's.

```bash
.venv/bin/python -c "import token_meter.infrastructure.__init__; print(token_meter.infrastructure.__init__.__doc__)"
```

What you should see (captured from this repository):

```text
Adapters that implement the ports: model clients, files, settings, logging.
```

2. Count the top-level functions and classes in each file of this layer, by reading the code without running it.

```bash
.venv/bin/python - <<'EOF'
import ast, pathlib
files = sorted(pathlib.Path('src/token_meter/infrastructure').glob('*.py'))
for f in files:
    tree = ast.parse(f.read_text())
    names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    print(f.name, len(names))
EOF
```

What you should see (captured from this repository):

```text
__init__.py 0
anthropic_chat.py 2
clock.py 1
csv_journal.py 2
env.py 8
files.py 2
logging.py 4
model_factory.py 2
openai_compatible.py 3
recording.py 3
resilient.py 1
retry.py 1
...
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

- **Common mistakes with this layer.** Letting an adapter decide business rules (they belong in the domain), reading environment variables in many places instead of the one settings module, or swallowing errors. Adapters here turn vendor errors into the project's own named errors.

## Check yourself

1. What is the job of `src/token_meter/infrastructure/__init__.py`?

   *Answer:* Adapters that implement the ports: model clients, files, settings, logging.

2. What is the job of `src/token_meter/infrastructure/anthropic_chat.py`?

   *Answer:* A chat model on the Anthropic Messages API, through the official SDK.

3. What is the job of `src/token_meter/infrastructure/clock.py`?

   *Answer:* The real clock, behind the `Clock` port.

4. What is the job of `src/token_meter/infrastructure/csv_journal.py`?

   *Answer:* The journal as a CSV file: append and flush one row per call, so a crash costs only unfinished calls.

5. What is the job of `src/token_meter/infrastructure/env.py`?

   *Answer:* Helpers that read and validate environment variables (twelve-factor configuration).

## Further reading

- Python Language Reference, https://docs.python.org/3.13/reference/ (every statement kind explained here is defined there; the explanations in this note are generated from the code by a program that reads each statement's structure, so they describe what the statement does, not why the author chose it: for the why, read the file's own docstrings, which are quoted).

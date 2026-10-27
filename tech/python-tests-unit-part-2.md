# Python source, the unit tests (part 2 of 2)

## What it is

The **unit tests** check one small piece at a time (a function, a class) with in-memory fakes and mock transports. They run in a fraction of a second each and need no network, no service and no model.

This note walks through every file, line by line: 2 files with 26 test functions. Read `pytest.md` first for the test runner itself (fixtures, markers, parametrize); this note shows every test.

## Why this repository uses it

Every claim in a README ("a killed run resumes", "the estimate is within ...", "the same refund twice is refused") is backed by a test, and these files are those tests. Reading them is the most exact way to learn what the program promises.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/unit/infrastructure/test_resilience_logging_factory.py` | 134 non-blank lines |
| `tests/unit/interfaces/test_cli.py` | 90 non-blank lines |

## How it works underneath

A test is a function whose name starts with `test_`. pytest imports the file, finds those functions, calls each one, and reports it as passed unless an `assert` fails or an error escapes. Parameters of a test function are *fixtures*: pytest looks up a fixture with that name (in the file, in `conftest.py`, or built in) and passes in what it returns. A fixture that uses `yield` runs the code after the `yield` as cleanup.

Test names are written as sentences (`test_a_budget_below_the_estimate_refuses_to_start_with_a_clear_message`) so that the list of names reads like the specification.

How to read the explanations below is the same as in the source notes: a quoted block, then one bullet per statement, with indented bullets for the calls and operators inside it.

## Walkthrough of this repository's use

### `tests/unit/infrastructure/test_resilience_logging_factory.py`

134 non-blank lines; it defines `Flaky`, `test_a_transient_failure_is_retried_with_backoff_and_then_succeeds`, `test_the_last_transient_failure_is_raised_after_the_attempts_run_out`, `test_a_permanent_failure_is_not_retried`, `test_retry_needs_at_least_one_attempt_and_caps_the_delay`, `test_log_lines_are_logfmt_with_fields_and_quote_spaces`, `test_an_exception_is_logged_on_the_same_line`, `test_shutdown_flag_is_set_by_a_request_and_by_a_signal`, `test_the_system_clock_moves_forward`, `test_the_default_provider_is_the_recorded_model`, `test_the_local_provider_builds_a_retrying_openai_compatible_model`, `test_record_mode_wraps_a_live_model_in_a_recorder`, ....

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 1 to 14:

```python
import io
import logging
import random
import signal

import pytest

from token_meter.domain.errors import PermanentModelError, TransientModelError
from token_meter.domain.llm import ChatMessage, ChatRequest, ChatResponse, StopReason, Usage
from token_meter.infrastructure.clock import SystemClock
from token_meter.infrastructure.env import ConfigurationError
from token_meter.infrastructure.logging import configure_logging, fields
from token_meter.infrastructure.model_factory import ModelSettings, build_chat_model
from token_meter.infrastructure.recording import RecordedChatModel, RecordingChatModel
```

- Makes the module `io` (standard library) available.
- Makes the module `logging` (standard library) available.
- Makes the module `random` (standard library) available.
- Makes the module `signal` (standard library) available.
- Makes the module `pytest` (installed package) available.
- Brings in `PermanentModelError` (Repeating the call cannot help: a bad request, a bad key, a refusal to parse.), `TransientModelError` (The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection.) from the project module `token_meter.domain.errors`.
- Brings in `ChatMessage` (One message of a conversation. A tool result carries the id of the call it answers.), `ChatRequest` (Everything that defines one call.), `ChatResponse` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.), `StopReason` (Why the model stopped writing.), `Usage` (Tokens the provider billed for one call, read from its usage block, never recomputed.) from the project module `token_meter.domain.llm`.
- Brings in `SystemClock` (Wall-clock and monotonic time from the operating system.) from the project module `token_meter.infrastructure.clock`.
- Brings in `ConfigurationError` (An environment variable is missing or has an unusable value.) from the project module `token_meter.infrastructure.env`.
- Brings in `configure_logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.), `fields` (Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs.) from the project module `token_meter.infrastructure.logging`.
- Brings in `ModelSettings` (Which model to call and how. See .env.example for every variable.), `build_chat_model` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.) from the project module `token_meter.infrastructure.model_factory`.
- Brings in `RecordedChatModel` (Replays recorded responses. A request nobody recorded raises `RecordingMissing`.), `RecordingChatModel` (Wraps a live model and writes each answer into a recording. A request already recorded is replayed.) from the project module `token_meter.infrastructure.recording`.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 15 to 28:

```python
from token_meter.infrastructure.resilient import RetryingChatModel
from token_meter.infrastructure.retry import retry
from token_meter.infrastructure.shutdown import ShutdownSignal

REQUEST = ChatRequest((ChatMessage.user("hi"),), tag="r")


class Flaky:
    name = "flaky"
    supports_sampling = True

    def __init__(self, failures, error=TransientModelError):
        self.calls = 0
        self._failures = failures
```

- Brings in `RetryingChatModel` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.) from the project module `token_meter.infrastructure.resilient`.
- Brings in `retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.) from the project module `token_meter.infrastructure.retry`.
- Brings in `ShutdownSignal` (A flag that SIGINT and SIGTERM set, which work loops check between units of work.) from the project module `token_meter.infrastructure.shutdown`.
- Stores the result of calling `ChatRequest` under the name `REQUEST`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
- Defines the class `Flaky`.
- Stores the text `flaky` under the name `name`.
- Stores the value `True` under the name `supports_sampling`.
- Defines the method `__init__`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `failures`.
    - `error`; if the caller leaves it out it is the value named `TransientModelError`.
- Stores the number `0` under the name `self.calls` (as an attribute of this object, so other methods can use it).
- Stores the value named `failures` under the name `self._failures` (as an attribute of this object, so other methods can use it).

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 29 to 42:

```python
        self._error = error

    def complete(self, request):
        self.calls += 1
        if self.calls <= self._failures:
            raise self._error("boom")
        return ChatResponse("ok", StopReason.END, Usage(1, 1), 0.1, "flaky")


def test_a_transient_failure_is_retried_with_backoff_and_then_succeeds():
    pauses: list[float] = []
    flaky = Flaky(2)
    model = RetryingChatModel(flaky, attempts=3, base_delay_seconds=1.0, sleep=pauses.append, rng=random.Random(1))
    assert model.complete(REQUEST).text == "ok"
```

- Stores the value named `error` under the name `self._error` (as an attribute of this object, so other methods can use it).
- Defines the method `complete`.
- Its parameters:
    - `self` is the object the method works on (Python passes it automatically).
    - `request`.
- Updates `self.calls` in place: `+=` applies `+` with the number `1` and stores the result back.
- Decision: the indented lines below run only when `self.calls <= self._failures` is true.
  - `<=` means less than or equal.
- Raises an error: the result of calling `self._error`. Execution jumps out to the nearest matching `except`.
  - The method `_error` of `self`.
- Ends the function and gives back the result of calling `ChatResponse` to the caller.
  - `ChatResponse` from the project's `token_meter.domain.llm` (What came back: the text or the tool calls, why it stopped, the billed usage and the latency.).
  - `Usage` from the project's `token_meter.domain.llm` (Tokens the provider billed for one call, read from its usage block, never recomputed.).
- Defines the function `test_a_transient_failure_is_retried_with_backoff_and_then_succeeds`.
- It takes no parameters.
- Declares `pauses` as a list of a decimal number and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Stores the result of calling `Flaky` under the name `flaky`.
  - `Flaky`, a class of this project.
- Stores the result of calling `RetryingChatModel` under the name `model`.
  - `RetryingChatModel` from the project's `token_meter.infrastructure.resilient` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.).
  - `random.Random` makes a random-number generator that repeats for the same seed.
- Checks that `model.complete(REQUEST).text == 'ok'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `complete` of `model`.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 43 to 54:

```python
    assert flaky.calls == 3
    assert 0.5 <= pauses[0] <= 1.0
    assert 1.0 <= pauses[1] <= 2.0
    assert model.name == "flaky"
    assert model.supports_sampling


def test_the_last_transient_failure_is_raised_after_the_attempts_run_out():
    flaky = Flaky(9)
    with pytest.raises(TransientModelError):
        RetryingChatModel(flaky, attempts=2, sleep=lambda s: None).complete(REQUEST)
    assert flaky.calls == 2
```

- Checks that `flaky.calls == 3` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `0.5 <= pauses[0] <= 1.0` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `1.0 <= pauses[1] <= 2.0` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Checks that `model.name == 'flaky'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `model.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.
- Defines the function `test_the_last_transient_failure_is_raised_after_the_attempts_run_out`.
- It takes no parameters.
- Stores the result of calling `Flaky` under the name `flaky`.
  - `Flaky`, a class of this project.
- A `with` block: it sets up `pytest.raises(TransientModelError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `RetryingChatModel(flaky, attempts=2, ...` with 1 argument(s); the result is not kept.
  - The method `complete` of `RetryingChatModel(flaky, attempts=2, ...`.
  - `RetryingChatModel` from the project's `token_meter.infrastructure.resilient` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.).
  - `lambda args: expression` is a small unnamed function written inline.
- Checks that `flaky.calls == 2` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 57 to 67:

```python
def test_a_permanent_failure_is_not_retried():
    flaky = Flaky(9, PermanentModelError)
    with pytest.raises(PermanentModelError):
        RetryingChatModel(flaky, attempts=5, sleep=lambda s: None).complete(REQUEST)
    assert flaky.calls == 1


def test_retry_needs_at_least_one_attempt_and_caps_the_delay():
    with pytest.raises(ValueError, match=r"at least 1"):
        retry(lambda: 1, attempts=0, base_delay_seconds=1, retry_on=(ValueError,))
    pauses: list[float] = []
```

- Defines the function `test_a_permanent_failure_is_not_retried`.
- It takes no parameters.
- Stores the result of calling `Flaky` under the name `flaky`.
  - `Flaky`, a class of this project.
- A `with` block: it sets up `pytest.raises(PermanentModelError)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls the method `complete` of `RetryingChatModel(flaky, attempts=5, ...` with 1 argument(s); the result is not kept.
  - The method `complete` of `RetryingChatModel(flaky, attempts=5, ...`.
  - `RetryingChatModel` from the project's `token_meter.infrastructure.resilient` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.).
  - `lambda args: expression` is a small unnamed function written inline.
- Checks that `flaky.calls == 1` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_retry_needs_at_least_one_attempt_and_caps_the_delay`.
- It takes no parameters.
- A `with` block: it sets up `pytest.raises(ValueError, match='at least 1')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `retry` from the project's `token_meter.infrastructure.retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.) with 4 argument(s); the result is not kept.
  - `retry` from the project's `token_meter.infrastructure.retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.).
  - `lambda args: expression` is a small unnamed function written inline.
- Declares `pauses` as a list of a decimal number and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 69 to 81:

```python
    def fail() -> int:
        raise ValueError

    with pytest.raises(ValueError, match=r"^$"):
        retry(fail, attempts=6, base_delay_seconds=4, retry_on=(ValueError,), sleep=pauses.append, max_delay_seconds=5)
    assert max(pauses) <= 5


def test_log_lines_are_logfmt_with_fields_and_quote_spaces():
    stream = io.StringIO()
    configure_logging("INFO", stream)
    logging.getLogger("t").info("two words", extra=fields(count=3, note="a b", empty=""))
    line = stream.getvalue().strip()
```

- Defines the function `fail`. It returns a whole number.
- It takes no parameters.
- Raises an error: the value named `ValueError`. Execution jumps out to the nearest matching `except`.
- A `with` block: it sets up `pytest.raises(ValueError, match='^$')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `retry` from the project's `token_meter.infrastructure.retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.) with 6 argument(s); the result is not kept.
  - `retry` from the project's `token_meter.infrastructure.retry` (Call `operation` up to `attempts` times, doubling the pause after each failure in `retry_on`.).
- Checks that `max(pauses) <= 5` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
  - `max` picks the largest value.
- Defines the function `test_log_lines_are_logfmt_with_fields_and_quote_spaces`.
- It takes no parameters.
- Stores the result of calling `io.StringIO` under the name `stream`.
  - `io.StringIO` from the standard library module `io`.
- Calls `configure_logging` from the project's `token_meter.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.) with 2 argument(s); the result is not kept.
  - `configure_logging` from the project's `token_meter.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.).
- Calls the method `info` of `logging.getLogger('t')` with 2 argument(s); the result is not kept.
  - The method `info` of `logging.getLogger('t')`.
  - `logging.getLogger` gets the logger with the given name.
  - `fields` from the project's `token_meter.infrastructure.logging` (Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs.).
- Stores the result of calling `stream.getvalue().strip` under the name `line`.
  - `.strip(...)` removes spaces (or the given characters) from both ends of text.
  - The method `getvalue` of `stream`.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 82 to 95:

```python
    assert 'msg="two words"' in line
    assert "count=3" in line
    assert 'note="a b"' in line
    assert 'empty=""' in line
    assert line.startswith("ts=")


def test_an_exception_is_logged_on_the_same_line():
    stream = io.StringIO()
    configure_logging("INFO", stream)
    try:
        raise RuntimeError("bad")
    except RuntimeError:
        logging.getLogger("t").exception("failed")
```

- Checks that `'msg="two words"' in line` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'count=3' in line` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'note="a b"' in line` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'empty=""' in line` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `line.startswith('ts=')` is true; if it is not, the test fails with an `AssertionError`.
  - `.startswith(...)` asks whether text begins with the given text.
- Defines the function `test_an_exception_is_logged_on_the_same_line`.
- It takes no parameters.
- Stores the result of calling `io.StringIO` under the name `stream`.
  - `io.StringIO` from the standard library module `io`.
- Calls `configure_logging` from the project's `token_meter.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.) with 2 argument(s); the result is not kept.
  - `configure_logging` from the project's `token_meter.infrastructure.logging` (Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.).
- A `try` block: the indented lines run, and if one of them raises an error the matching `except` below handles it instead of stopping the program.
- Raises an error: the result of calling `RuntimeError`. Execution jumps out to the nearest matching `except`.
  - `RuntimeError` a general error raised while running.
- `except` handler: it runs when the `try` block raised `RuntimeError`.
- Calls the method `exception` of `logging.getLogger('t')` with 1 argument(s); the result is not kept.
  - The method `exception` of `logging.getLogger('t')`.
  - `logging.getLogger` gets the logger with the given name.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 96 to 109:

```python
    assert "exc=" in stream.getvalue()


def test_shutdown_flag_is_set_by_a_request_and_by_a_signal():
    shutdown = ShutdownSignal()
    assert not shutdown.requested
    shutdown.install()
    signal.raise_signal(signal.SIGTERM)
    assert shutdown.requested
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.default_int_handler)
    other = ShutdownSignal()
    other.request()
    assert other.requested
```

- Checks that `'exc=' in stream.getvalue()` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - The method `getvalue` of `stream`.
- Defines the function `test_shutdown_flag_is_set_by_a_request_and_by_a_signal`.
- It takes no parameters.
- Stores the result of calling `ShutdownSignal` under the name `shutdown`.
  - `ShutdownSignal` from the project's `token_meter.infrastructure.shutdown` (A flag that SIGINT and SIGTERM set, which work loops check between units of work.).
- Checks that `not shutdown.requested` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.
- Calls the method `install` of the project's `ShutdownSignal` (Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close.); the result is not kept.
  - The method `install` of the project's `ShutdownSignal` (Route SIGINT and SIGTERM to `request`, so in-flight work finishes and files close.).
- Calls `signal.raise_signal` from the standard library module `signal` with 1 argument(s); the result is not kept.
  - `signal.raise_signal` from the standard library module `signal`.
- Checks that `shutdown.requested` is true; if it is not, the test fails with an `AssertionError`.
- Calls `signal.signal` installs a function to run when a signal arrives with 2 argument(s); the result is not kept.
  - `signal.signal` installs a function to run when a signal arrives.
- Calls `signal.signal` installs a function to run when a signal arrives with 2 argument(s); the result is not kept.
  - `signal.signal` installs a function to run when a signal arrives.
- Stores the result of calling `ShutdownSignal` under the name `other`.
  - `ShutdownSignal` from the project's `token_meter.infrastructure.shutdown` (A flag that SIGINT and SIGTERM set, which work loops check between units of work.).
- Calls the method `request` of `other`; the result is not kept.
  - The method `request` of `other`.
- Checks that `other.requested` is true; if it is not, the test fails with an `AssertionError`.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 112 to 123:

```python
def test_the_system_clock_moves_forward():
    clock = SystemClock()
    assert clock.monotonic() <= clock.monotonic()
    assert clock.now().date() == clock.today()


def test_the_default_provider_is_the_recorded_model(tmp_path):
    settings = ModelSettings.from_env({"RECORDINGS_PATH": str(tmp_path)})
    assert isinstance(build_chat_model(settings, SystemClock(), {}), RecordedChatModel)


def test_the_local_provider_builds_a_retrying_openai_compatible_model():
```

- Defines the function `test_the_system_clock_moves_forward`.
- It takes no parameters.
- Stores the result of calling `SystemClock` under the name `clock`.
  - `SystemClock` from the project's `token_meter.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Checks that `clock.monotonic() <= clock.monotonic()` is true; if it is not, the test fails with an `AssertionError`.
  - `<=` means less than or equal.
  - The method `monotonic` of `clock`.
- Checks that `clock.now().date() == clock.today()` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - The method `date` of `clock.now()`.
  - The method `today` of `clock`.
  - The method `now` of `clock`.
- Defines the function `test_the_default_provider_is_the_recorded_model`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `ModelSettings.from_env` under the name `settings`.
  - The method `from_env` of `ModelSettings`.
  - `str` turns a value into text.
- Checks that `isinstance(build_chat_model(settings, SystemClock(), {}), RecordedChatModel)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
  - `build_chat_model` from the project's `token_meter.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `SystemClock` from the project's `token_meter.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Defines the function `test_the_local_provider_builds_a_retrying_openai_compatible_model`.
- It takes no parameters.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 124 to 135:

```python
    settings = ModelSettings.from_env({"MODEL_PROVIDER": "openai-compatible"})
    model = build_chat_model(settings, SystemClock(), {})
    assert isinstance(model, RetryingChatModel)
    assert model.name == "qwen2.5:0.5b"
    assert settings.openai_base_url == "http://localhost:11434/v1"


def test_record_mode_wraps_a_live_model_in_a_recorder(tmp_path):
    settings = ModelSettings.from_env(
        {"MODEL_PROVIDER": "openai-compatible", "RECORD": "on", "RECORDINGS_PATH": str(tmp_path / "r.jsonl")}
    )
    assert isinstance(build_chat_model(settings, SystemClock(), {}), RecordingChatModel)
```

- Stores the result of calling `ModelSettings.from_env` under the name `settings`.
  - The method `from_env` of `ModelSettings`.
- Stores the result of calling `build_chat_model` under the name `model`.
  - `build_chat_model` from the project's `token_meter.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `SystemClock` from the project's `token_meter.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Checks that `isinstance(model, RetryingChatModel)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
- Checks that `model.name == 'qwen2.5:0.5b'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `settings.openai_base_url == 'http://localhost:11434/v1'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Defines the function `test_record_mode_wraps_a_live_model_in_a_recorder`.
- Its parameters:
    - `tmp_path`.
- Stores the result of calling `ModelSettings.from_env` under the name `settings`.
  - The method `from_env` of `ModelSettings`.
  - `str` turns a value into text.
  - `/` is divide.
- Checks that `isinstance(build_chat_model(settings, SystemClock(), {}), RecordingChatModel)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
  - `build_chat_model` from the project's `token_meter.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `SystemClock` from the project's `token_meter.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 138 to 149:

```python
def test_the_anthropic_provider_refuses_to_start_without_a_key_in_the_environment():
    settings = ModelSettings.from_env({"MODEL_PROVIDER": "anthropic"})
    assert settings.model == "claude-haiku-5-5"
    with pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY"):
        build_chat_model(settings, SystemClock(), {})


def test_the_anthropic_provider_builds_when_a_key_is_present():
    settings = ModelSettings.from_env({"MODEL_PROVIDER": "anthropic", "ANTHROPIC_THINKING": "omit"})
    model = build_chat_model(settings, SystemClock(), {"ANTHROPIC_API_KEY": "present-but-not-real"})
    assert isinstance(model, RetryingChatModel)
    assert not model.supports_sampling
```

- Defines the function `test_the_anthropic_provider_refuses_to_start_without_a_key_in_the_environment`.
- It takes no parameters.
- Stores the result of calling `ModelSettings.from_env` under the name `settings`.
  - The method `from_env` of `ModelSettings`.
- Checks that `settings.model == 'claude-haiku-5-5'` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- A `with` block: it sets up `pytest.raises(ConfigurationError, match='ANTHROPIC_API_KEY')`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
- Calls `build_chat_model` from the project's `token_meter.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.) with 3 argument(s); the result is not kept.
  - `build_chat_model` from the project's `token_meter.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `SystemClock` from the project's `token_meter.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Defines the function `test_the_anthropic_provider_builds_when_a_key_is_present`.
- It takes no parameters.
- Stores the result of calling `ModelSettings.from_env` under the name `settings`.
  - The method `from_env` of `ModelSettings`.
- Stores the result of calling `build_chat_model` under the name `model`.
  - `build_chat_model` from the project's `token_meter.infrastructure.model_factory` (Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked.).
  - `SystemClock` from the project's `token_meter.infrastructure.clock` (Wall-clock and monotonic time from the operating system.).
- Checks that `isinstance(model, RetryingChatModel)` is true; if it is not, the test fails with an `AssertionError`.
  - `isinstance` asks whether a value is of a given type.
- Checks that `not model.supports_sampling` is true; if it is not, the test fails with an `AssertionError`.
  - `not` flips true and false.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 152 to 163:

```python
@pytest.mark.parametrize(
    "environ",
    [
        {"MODEL_PROVIDER": "carrier-pigeon"},
        {"RECORD": "maybe"},
        {"MODEL_ATTEMPTS": "0"},
        {"MODEL_TIMEOUT_SECONDS": "0"},
    ],
)
def test_bad_model_settings_name_the_variable(environ):
    with pytest.raises(ConfigurationError, match=next(iter(environ))):
        ModelSettings.from_env(environ)
```

- Defines the function `test_bad_model_settings_name_the_variable`. `@pytest.mark.parametrize` runs the test once for each row of values listed.
- Its parameters:
    - `environ`.
- A `with` block: it sets up `pytest.raises(ConfigurationError, match=next(iter(environ)))`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - `pytest.raises` passes if the code inside raises the given error.
  - `next` takes the next item from an iterator.
  - `iter` makes an iterator over a collection.
- Calls the method `from_env` of `ModelSettings` with 1 argument(s); the result is not kept.
  - The method `from_env` of `ModelSettings`.

`tests/unit/infrastructure/test_resilience_logging_factory.py`, lines 166 to 173:

```python
def test_info_logs_of_a_failed_call_never_carry_the_prompt_text(caplog):
    flaky = Flaky(1)
    secret = ChatRequest((ChatMessage.user("my card number is 4111"),), tag="p1/t0/0")
    with caplog.at_level(logging.INFO):
        RetryingChatModel(flaky, attempts=2, sleep=lambda s: None).complete(secret)
    assert caplog.records
    assert "4111" not in caplog.text
    assert "4111" not in " ".join(str(r.__dict__.get("fields", "")) for r in caplog.records)
```

- Defines the function `test_info_logs_of_a_failed_call_never_carry_the_prompt_text`.
- Its parameters:
    - `caplog`.
- Stores the result of calling `Flaky` under the name `flaky`.
  - `Flaky`, a class of this project.
- Stores the result of calling `ChatRequest` under the name `secret`.
  - `ChatRequest` from the project's `token_meter.domain.llm` (Everything that defines one call.).
  - The method `user` of `ChatMessage`.
- A `with` block: it sets up `caplog.at_level(logging.INFO)`, runs the indented lines, and then always cleans up (closes the file, releases the lock, commits or rolls back), even if an error happens inside.
  - The method `at_level` of `caplog`.
- Calls the method `complete` of `RetryingChatModel(flaky, attempts=2, ...` with 1 argument(s); the result is not kept.
  - The method `complete` of `RetryingChatModel(flaky, attempts=2, ...`.
  - `RetryingChatModel` from the project's `token_meter.infrastructure.resilient` (Repeats a call that failed with `TransientModelError`; a permanent failure is raised at once.).
  - `lambda args: expression` is a small unnamed function written inline.
- Checks that `caplog.records` is true; if it is not, the test fails with an `AssertionError`.
- Checks that `'4111' not in caplog.text` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
- Checks that `'4111' not in ' '.join((str(r.__dict__.get('fields', '')) for r in caplog.rec...` is true; if it is not, the test fails with an `AssertionError`.
  - `not in` means is not contained in.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `str` turns a value into text.
  - `.get(...)` reads a dictionary entry, giving a default when the key is missing.

### `tests/unit/interfaces/test_cli.py`

90 non-blank lines; it defines `workspace`, `scripted`, `test_estimate_prints_the_whole_run_and_calls_no_model`, `test_estimate_also_refuses_when_the_budget_is_below_it`, `test_a_budget_below_the_estimate_refuses_to_start_with_a_clear_message`, `test_a_run_fills_the_journal_and_a_second_run_pays_for_nothing`, `test_the_report_prints_every_section`, `test_stale_prices_stop_the_run_unless_allowed`, `test_a_budget_that_is_not_a_number_is_a_configuration_error`, `test_a_model_without_sampling_support_is_a_configuration_error`, `test_a_prompt_file_that_breaks_the_lesson_rules_is_reported`, `test_a_bad_environment_value_is_reported_before_anything_runs`, ....

`tests/unit/interfaces/test_cli.py`, lines 1 to 13:

```python
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
```

- Makes the module `json` (standard library) available.
- Brings in `UTC`, `datetime` from the standard library module `datetime`.
- Brings in `Path` from the standard library module `pathlib`.
- Makes the module `pytest` (installed package) available.
- Brings in `ScriptedModel` (Answers every request from a function, and remembers the requests it saw.) from the project module `tests.conftest`.
- Brings in `MeterSettings` (Everything the programs read from the environment. See .env.example for each variable.) from the project module `token_meter.infrastructure.settings`.
- Brings in `ShutdownSignal` (A flag that SIGINT and SIGTERM set, which work loops check between units of work.) from the project module `token_meter.infrastructure.shutdown`.
- Brings in `cli` from the project module `token_meter.interfaces`.
- Brings in `EXIT_CONFIG`, `EXIT_INTERRUPTED`, `EXIT_OK`, `EXIT_REFUSED`, `main` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).), `run_command` (Print the estimate for the pending calls, then make them when a model is given.) from the project module `token_meter.interfaces.cli`.
- Stores the part of `Path(__file__).resolve().pa...` picked by `3` under the name `REPO`.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
  - `.resolve(...)` turns a path into a full absolute path.
  - `Path` from the standard library module `pathlib`, which a file or folder location.

`tests/unit/interfaces/test_cli.py`, lines 16 to 27:

```python
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
```

- Defines the function `workspace`. `@pytest.fixture` marks a function that builds something tests ask for by naming it as a parameter.
- Its parameters:
    - `tmp_path`.
    - `monkeypatch`.
- Stores the result of calling `datetime.now(UTC).date().isoformat` under the name `today`.
  - `.isoformat(...)` writes a date or time as text in ISO form (`2026-11-03T10:00`).
  - The method `date` of `datetime.now(UTC)`.
  - `datetime.now` the current date and time.
- Stores the result of `tmp_path / 'prices.json'` under the name `prices`.
  - `/` is divide.
- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - `json.dumps` turns Python data into JSON text.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
  - `/` is divide.

`tests/unit/interfaces/test_cli.py`, lines 28 to 41:

```python
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
```

- Ends the function and gives back the value named `tmp_path` to the caller.
- Defines the function `scripted`.
- Its parameters:
    - `monkeypatch`.
    - `**kwargs` collects any extra named arguments into a dictionary.
- Stores the result of calling `ScriptedModel` under the name `model`.
  - `ScriptedModel` from the project's `tests.conftest` (Answers every request from a function, and remembers the requests it saw.).
  - `**name` inside a call passes every entry of a dictionary as a named argument.
  - `lambda args: expression` is a small unnamed function written inline.
- Calls the method `setattr` of `monkeypatch` with 3 argument(s); the result is not kept.
  - The method `setattr` of `monkeypatch`.
  - `lambda args: expression` is a small unnamed function written inline.
- Ends the function and gives back the value named `model` to the caller.
- Defines the function `test_estimate_prints_the_whole_run_and_calls_no_model`.
- Its parameters:
    - `workspace`.
    - `capsys`.
- Checks that `main(['estimate']) == EXIT_OK` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).
- Stores the `out` of `capsys.readouterr()` under the name `out`.
  - `.readouterr(...)` reads what a test captured from the screen.
- Checks that `'calls=450' in out` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Checks that `'cost_est=$' in out` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.

`tests/unit/interfaces/test_cli.py`, lines 44 to 53:

```python
def test_estimate_also_refuses_when_the_budget_is_below_it(workspace, capsys):
    assert main(["estimate", "--budget", "0.001"]) == EXIT_REFUSED
    assert "REFUSING TO START" in capsys.readouterr().err


def test_a_budget_below_the_estimate_refuses_to_start_with_a_clear_message(workspace, capsys, monkeypatch):
    model = scripted(monkeypatch)
    assert main(["run", "--budget", "0.001"]) == EXIT_REFUSED
    assert "REFUSING TO START: estimated cost" in capsys.readouterr().err
    assert model.requests == []
```

- Defines the function `test_estimate_also_refuses_when_the_budget_is_below_it`.
- Its parameters:
    - `workspace`.
    - `capsys`.
- Checks that `main(['estimate', '--budget', '0.001']) == EXIT_REFUSED` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).
- Checks that `'REFUSING TO START' in capsys.readouterr().err` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `.readouterr(...)` reads what a test captured from the screen.
- Defines the function `test_a_budget_below_the_estimate_refuses_to_start_with_a_clear_message`.
- Its parameters:
    - `workspace`.
    - `capsys`.
    - `monkeypatch`.
- Stores the result of calling `scripted` under the name `model`.
  - `scripted`, a function of this file.
- Checks that `main(['run', '--budget', '0.001']) == EXIT_REFUSED` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).
- Checks that `'REFUSING TO START: estimated cost' in capsys.readouterr().err` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `.readouterr(...)` reads what a test captured from the screen.
- Checks that `model.requests == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.

`tests/unit/interfaces/test_cli.py`, lines 56 to 67:

```python
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
```

- Defines the function `test_a_run_fills_the_journal_and_a_second_run_pays_for_nothing`.
- Its parameters:
    - `workspace`.
    - `capsys`.
    - `monkeypatch`.
- Stores the result of calling `scripted` under the name `model`.
  - `scripted`, a function of this file.
- Checks that `main(['run', '--budget', '0.05']) == EXIT_OK` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).
- Checks that `'calls made now: 450; skipped, already in the journal: 0' in capsys.readouter...` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `.readouterr(...)` reads what a test captured from the screen.
- Checks that `main(['run']) == EXIT_OK` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).
- Checks that `'calls made now: 0; skipped, already in the journal: 450' in capsys.readouter...` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `.readouterr(...)` reads what a test captured from the screen.
- Checks that `len(model.requests) == 450` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Defines the function `test_the_report_prints_every_section`.
- Its parameters:
    - `workspace`.
    - `capsys`.
    - `monkeypatch`.
- Calls `scripted`, a function of this file with 1 argument(s); the result is not kept.
  - `scripted`, a function of this file.
- Calls `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).) with 1 argument(s); the result is not kept.
  - `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).

`tests/unit/interfaces/test_cli.py`, lines 68 to 81:

```python
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
```

- Calls `.readouterr(...)` reads what a test captured from the screen; the result is not kept.
  - `.readouterr(...)` reads what a test captured from the screen.
- Checks that `main(['report']) == EXIT_OK` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).
- Stores the `out` of `capsys.readouterr()` under the name `out`.
  - `.readouterr(...)` reads what a test captured from the screen.
- Loop: the indented lines below run once for each item of `('by kind', 'measured template overhead', 'largest gap', ...`; `fragment` names the current item.
- Checks that `fragment in out` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
- Defines the function `test_stale_prices_stop_the_run_unless_allowed`.
- Its parameters:
    - `workspace`.
    - `capsys`.
    - `monkeypatch`.
- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - `json.dumps` turns Python data into JSON text.
  - `/` is divide.
- Stores the result of calling `scripted` under the name `model`.
  - `scripted`, a function of this file.
- Checks that `main(['run']) == EXIT_REFUSED` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).
- Checks that `'days ago' in capsys.readouterr().err` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `.readouterr(...)` reads what a test captured from the screen.

`tests/unit/interfaces/test_cli.py`, lines 82 to 95:

```python
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
```

- Checks that `main(['run', '--allow-stale-prices']) == EXIT_OK` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).
- Checks that `len(model.requests) == 450` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `len` counts the items in a collection (or the characters in text).
- Defines the function `test_a_budget_that_is_not_a_number_is_a_configuration_error`.
- Its parameters:
    - `workspace`.
    - `capsys`.
    - `monkeypatch`.
- Calls `scripted`, a function of this file with 1 argument(s); the result is not kept.
  - `scripted`, a function of this file.
- Checks that `main(['run', '--budget', 'cheap']) == EXIT_CONFIG` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).
- Checks that `'--budget' in capsys.readouterr().err` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `.readouterr(...)` reads what a test captured from the screen.
- Defines the function `test_a_model_without_sampling_support_is_a_configuration_error`.
- Its parameters:
    - `workspace`.
    - `capsys`.
    - `monkeypatch`.
- Calls `scripted`, a function of this file with 2 argument(s); the result is not kept.
  - `scripted`, a function of this file.
- Checks that `main(['run']) == EXIT_CONFIG` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).
- Checks that `'does not accept temperature' in capsys.readouterr().err` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `.readouterr(...)` reads what a test captured from the screen.

`tests/unit/interfaces/test_cli.py`, lines 98 to 109:

```python
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
```

- Defines the function `test_a_prompt_file_that_breaks_the_lesson_rules_is_reported`.
- Its parameters:
    - `workspace`.
    - `capsys`.
    - `monkeypatch`.
- Stores the result of `workspace / 'short.jsonl'` under the name `short`.
  - `/` is divide.
- Calls `.write_text(...)` writes text to a file, replacing it with 1 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
  - `str` turns a value into text.
- Checks that `main(['estimate']) == EXIT_CONFIG` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).
- Checks that `'expected 50 prompts' in capsys.readouterr().err` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `.readouterr(...)` reads what a test captured from the screen.
- Defines the function `test_a_bad_environment_value_is_reported_before_anything_runs`.
- Its parameters:
    - `workspace`.
    - `capsys`.
    - `monkeypatch`.
- Calls `.setenv(...)` sets an environment variable for one test with 2 argument(s); the result is not kept.
  - `.setenv(...)` sets an environment variable for one test.
- Checks that `main(['estimate']) == EXIT_CONFIG` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `main` from the project's `token_meter.interfaces.cli` (Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted).).
- Checks that `'REPEATS' in capsys.readouterr().err` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `.readouterr(...)` reads what a test captured from the screen.

`tests/unit/interfaces/test_cli.py`, lines 112 to 119:

```python
def test_a_shutdown_request_ends_the_run_with_the_interrupted_code(workspace, monkeypatch, capsys):
    model = scripted(monkeypatch)
    shutdown = ShutdownSignal()
    shutdown.request()
    args = cli.build_parser().parse_args(["run"])
    assert run_command(args, MeterSettings.from_env(), model, shutdown) == EXIT_INTERRUPTED
    assert model.requests == []
    assert "calls made now: 0" in capsys.readouterr().out
```

- Defines the function `test_a_shutdown_request_ends_the_run_with_the_interrupted_code`.
- Its parameters:
    - `workspace`.
    - `monkeypatch`.
    - `capsys`.
- Stores the result of calling `scripted` under the name `model`.
  - `scripted`, a function of this file.
- Stores the result of calling `ShutdownSignal` under the name `shutdown`.
  - `ShutdownSignal` from the project's `token_meter.infrastructure.shutdown` (A flag that SIGINT and SIGTERM set, which work loops check between units of work.).
- Calls the method `request` of `shutdown`; the result is not kept.
  - The method `request` of `shutdown`.
- Stores the result of calling `cli.build_parser().parse_args` under the name `args`.
  - The method `parse_args` of `cli.build_parser()`.
  - The method `build_parser` of `cli`.
- Checks that `run_command(args, MeterSettings.from_env(), model, shutdown) == EXIT_INTERRUPTED` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
  - `run_command` from the project's `token_meter.interfaces.cli` (Print the estimate for the pending calls, then make them when a model is given.).
  - The method `from_env` of `MeterSettings`.
- Checks that `model.requests == []` is true; if it is not, the test fails with an `AssertionError`.
  - `==` means equal.
- Checks that `'calls made now: 0' in capsys.readouterr().out` is true; if it is not, the test fails with an `AssertionError`.
  - `in` means is contained in.
  - `.readouterr(...)` reads what a test captured from the screen.

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

1. What does `tests/unit/infrastructure/test_resilience_logging_factory.py` test?

   *Answer:* It holds the tests for `resilience logging factory`.

2. What does `tests/unit/interfaces/test_cli.py` test?

   *Answer:* It holds the tests for `cli`.

3. What does a test function's name start with, and why?

   *Answer:* `test_`: pytest collects every function whose name starts with it.

4. What does a test function's name start with, and why?

   *Answer:* `test_`: pytest collects every function whose name starts with it.

5. What does a test function's name start with, and why?

   *Answer:* `test_`: pytest collects every function whose name starts with it.

## Further reading

- pytest documentation, https://docs.pytest.org/en/stable/ (pytest 9.1.1 is pinned; the per-statement explanations are generated from the code's structure).

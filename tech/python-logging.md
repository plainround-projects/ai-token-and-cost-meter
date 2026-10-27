# Python logging and logfmt

## What it is

A **log** is a running diary a program writes about what it is doing: "started", "retrying after a timeout", "refused the request". When something goes wrong at 3 a.m. the log is often the only evidence. Python's standard module **`logging`** handles this: your code asks a *logger* to record a *message* at a *level* (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`, in increasing seriousness); a *handler* decides where the record goes (the screen, a file); a *formatter* decides how it looks.

**logfmt** is a simple line format for logs: `key=value` pairs separated by spaces, one event per line, such as `ts=2026-10-27T11:00:00.000+00:00 level=INFO logger=x msg="run started" calls=450`. It is easy for people to read and easy for tools (`grep`, `awk`) to split. Values that contain spaces or quotes are put in double quotes.

## Why this repository uses it

Structured lines make runs searchable (`grep 'level=WARNING'`, `grep 'tag=p02'`), and fixed field names let a later tool count events without guessing. The repository logs **sizes, ids, hashes and counts, never the text of a prompt or an answer** at INFO level, so logs cannot leak customer content.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/token_meter/infrastructure/logging.py` | the formatter, the `fields()` helper and `configure_logging()` |
| `src/token_meter/interfaces/` | the command-line and server entry points call `configure_logging(...)` once at start-up |
| `env.example` | `LOG_LEVEL` |

## How it works underneath

`logging.getLogger(name)` returns a named logger; names form a tree separated by dots (`pkg.infrastructure.x`), and a logger passes each record up to its parent. The *root* logger at the top owns the handlers. A record carries the message, level, time, logger name and anything passed in `extra={...}`; `extra` entries become attributes of the record, which a formatter can read. A logger drops records below its level before any formatting happens, which is cheap.

Handlers are attached to the root logger by `configure_logging`. Python's default output for `logging` goes to *standard error* (descriptor 2), which keeps a program's real output on standard output clean.

## Walkthrough of this repository's use

`src/token_meter/infrastructure/logging.py`, function by function.

`src/token_meter/infrastructure/logging.py`, lines 16 to 18:

```python
def _quote(value: object) -> str:
    text = str(value)
    return json.dumps(text) if not text or any(char in text for char in ' ="\n') else text
```

`_quote` turns any value into text and puts it in double quotes (through `json.dumps`, which escapes quote characters and newlines) when the text is empty or contains a space, an equals sign, a double quote or a newline. Otherwise it returns the text unchanged. This keeps each `key=value` pair splittable.

`src/token_meter/infrastructure/logging.py`, lines 21 to 35:

```python
class LogfmtFormatter(logging.Formatter):
    """Format a log record as one logfmt line, with the record's extra fields as key=value pairs."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds")
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
```

`LogfmtFormatter` is a *formatter*: a subclass of `logging.Formatter` whose `format` method turns one record into one line. It writes the time (`record.created` is seconds since 1970; converted to an ISO-8601 UTC timestamp with milliseconds), the level name, the logger name and the message (`record.getMessage()` merges the message with any `%s` arguments). Then it adds every pair in the record's `fields` attribute (if none, an empty dictionary), and, if an exception is being handled (`record.exc_info`), an `exc=` entry with the traceback text. The parts are joined with single spaces.

`src/token_meter/infrastructure/logging.py`, lines 38 to 40:

```python
def fields(**values: Any) -> dict[str, Any]:
    """Use as `logger.info("message", extra=fields(prompt_id=...))` to attach key=value pairs."""
    return {"fields": values}
```

`fields(**values)` is a helper for call sites. `logger.info("msg", extra=fields(calls=3))` passes `extra={"fields": {"calls": 3}}`; Python copies the key `fields` onto the record, where the formatter finds it.

`src/token_meter/infrastructure/logging.py`, lines 43 to 52:

```python
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

`configure_logging(level, stream)` builds one `StreamHandler` writing to the stream (standard error by default), gives it the logfmt formatter, makes it the only handler of the root logger (so calling the function twice does not print every line twice), and sets the root level. It also raises the level of the HTTP and SDK libraries' loggers to at least WARNING, because they would otherwise print a line for every request.

Real calls in this repository:

- `src/token_meter/application/metered_model.py:39`: `_log.info(`
- `src/token_meter/application/run_meter.py:103`: `_log.info("stop requested, leaving the rest for a restart", extra={"fields": {"made": made}})`
- `src/token_meter/application/run_meter.py:126`: `_log.info(`

## Try it yourself

1. Configure logging to the screen and write one event. (The timestamp is replaced here so the output is the same every time.) Notice `msg="run started"` is quoted because it has a space, and `calls=450` is not.

```bash
.venv/bin/python -c "import sys; from token_meter.infrastructure.logging import configure_logging, fields; import logging; configure_logging('INFO', sys.stdout); logging.getLogger('demo').info('run started', extra=fields(calls=450, note='two words'))" | sed -E 's/ts=[^ ]+/ts=<time>/'
```

What you should see (captured from this repository):

```text
ts=<time> level=INFO logger=demo msg="run started" calls=450 note="two words"
```

2. At level `WARNING` an `INFO` event is dropped before it is formatted.

```bash
.venv/bin/python -c "import sys; from token_meter.infrastructure.logging import configure_logging; import logging; configure_logging('WARNING', sys.stdout); logging.getLogger('demo').info('hidden'); print('nothing was printed above')"
```

What you should see (captured from this repository):

```text
nothing was printed above
```

3. Where the program turns logging on.

```bash
grep -rn 'configure_logging' src | head -3
```

What you should see (captured from this repository):

```text
src/token_meter/infrastructure/logging.py:43:def configure_logging(level: str, stream: TextIO | None = None) -> None:
src/token_meter/interfaces/cli.py:23:from token_meter.infrastructure.logging import configure_logging
src/token_meter/interfaces/cli.py:112:        configure_logging(settings.log_level)
```

## Mistakes people make

- **Logging secrets or customer text.** INFO lines carry sizes, ids and hashes only.
- **Building the message with an f-string.** `logger.info("x %s", y)` skips the formatting when the level is off; here the structured values go in `extra=fields(...)`.
- **Calling `basicConfig` in a library.** Only the entry points configure logging.
- **Chatty third-party loggers.** `configure_logging` raises the level of `httpx`, `httpcore` and `anthropic` to WARNING so a request is not logged twice.
- **Unquoted values with spaces.** They break the `key=value` split; `_quote` quotes them.

## Check yourself

1. What are the five standard levels, from least to most serious?

   *Answer:* DEBUG, INFO, WARNING, ERROR, CRITICAL.

2. What is logfmt?

   *Answer:* One event per line as space-separated `key=value` pairs.

3. Why is prompt text kept out of INFO lines?

   *Answer:* To avoid leaking customer or user content into logs.

4. What does a handler do?

   *Answer:* Decides where a record goes (screen, file, network).

5. How does `extra=fields(...)` reach the formatter?

   *Answer:* `extra` entries become attributes of the log record; the formatter reads the `fields` attribute.

## Further reading

- Python `logging` documentation and HOWTO, https://docs.python.org/3/library/logging.html and https://docs.python.org/3/howto/logging.html; logfmt convention, https://brandur.org/logfmt (examples run on Python 3.13).

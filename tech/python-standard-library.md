# The Python standard library

## What it is

Python ships with a large collection of ready-made modules, called the **standard library**. You use one with `import name`. Because it comes with the interpreter, using it adds no dependency: nothing to install, pin or audit.

## Why this repository uses it

The project keeps outside dependencies to a minimum (see `pyproject-toml.md`: the runtime needs only a few packages). Most of what it needs is in the standard library: reading JSON and CSV, hashing, threads, signals, subprocesses, SQLite, dates, exact decimals. Sticking to the standard library keeps the install small and the behavior stable.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/token_meter/` | the program |
| `tests/` | tests use `subprocess`, `threading`, `signal`, `socket`, `tempfile` and others |
| `scripts/` | data generators use `random`, `json`, `csv` |

## How it works underneath

Most of the standard library is itself written in Python and lives in a folder next to the interpreter; some parts (`hashlib`, `zlib`, `sqlite3`, `socket`, `_json`) are compiled C code wrapped in a Python interface. `import x` finds the module through `sys.path`, runs it once, and caches it in `sys.modules`.

Modules that talk to the operating system (`os`, `signal`, `subprocess`, `socket`, `threading`, `time`) are thin layers over system calls, so their behavior can differ slightly between macOS, Linux and Windows. Where it matters, this repository's tests check the behavior on the platform they run on.

## Walkthrough of this repository's use

The **standard library** is the large set of modules that come with Python itself, with nothing to install. This repository imports 26 of them. Each one, in alphabetical order, with the names this repository actually uses and one real line:

#### `__future__`

A special module whose imports switch on language behavior early. `annotations` stores type hints as text.

- Imported in 29 file(s).
- What this repository uses from it: `annotations`.

#### `argparse`

Reads the command line (`meter run --budget 0.05`) into named values and prints help and errors. A *sub-command* (`run`, `report`) is added with sub-parsers.

- Imported in 1 file(s).
- What this repository uses from it: `argparse.ArgumentParser`, `argparse.Namespace`.
- Example: `src/token_meter/interfaces/cli.py:33`: `def build_parser() -> argparse.ArgumentParser:`

#### `collections`

Extra container types: `Counter` counts items, `defaultdict` makes a missing key start with a default, `deque` is a queue you can add to and remove from at both ends.

- Imported in 14 file(s).
- What this repository uses from it: `Counter`, `defaultdict`.
- Example: `src/token_meter/domain/analysis.py:89`: `totals: dict[Kind, list[int]] = defaultdict(lambda: [0, 0])`

#### `collections.abc`

Names for the *kinds* of containers (`Mapping`, `Sequence`, `Iterable`, `Callable`). Used in type hints.

- Imported in 14 file(s).
- What this repository uses from it: `Mapping`, `Sequence`, `Callable`, `Iterable`, `Collection`.
- Example: `src/token_meter/application/ports.py:37`: `def embed(self, texts: Sequence[str]) -> list[list[float]]:`

#### `csv`

Reads and writes comma-separated-value files, handling quotes and commas inside values.

- Imported in 2 file(s).
- What this repository uses from it: `csv.DictReader`, `csv.writer`.
- Example: `src/token_meter/infrastructure/csv_journal.py:37`: `csv.writer(buffer, lineterminator="\n").writerow(values)`

#### `dataclasses`

The `@dataclass` decorator, `field()` for per-field settings and `replace()` for making a changed copy of a frozen object.

- Imported in 11 file(s).
- What this repository uses from it: `dataclass`, `field`.
- Example: `src/token_meter/application/report.py:24`: `@dataclass(frozen=True, slots=True)`

#### `datetime`

Dates, times and durations (`date`, `datetime`, `timedelta`, `UTC`).

- Imported in 12 file(s).
- What this repository uses from it: `date`, `datetime`, `UTC`, `datetime.now`, `datetime.fromtimestamp`.
- Example: `src/token_meter/infrastructure/clock.py:16`: `return datetime.now(UTC).date()`

#### `decimal`

Exact decimal arithmetic for money. `ROUND_HALF_UP` is the school-book rounding rule.

- Imported in 12 file(s).
- What this repository uses from it: `Decimal`, `InvalidOperation`.
- Example: `src/token_meter/application/run_meter.py:33`: `budget: Decimal | None = None`

#### `enum`

Fixed sets of named values; `StrEnum` members are also strings.

- Imported in 2 file(s).
- What this repository uses from it: `StrEnum`.
- Example: `src/token_meter/domain/llm.py:13`: `class Role(StrEnum):`

#### `hashlib`

Hash functions. A hash turns any bytes into a short fixed-length fingerprint. `sha256` is used for fingerprints of requests and files.

- Imported in 1 file(s).
- What this repository uses from it: `hashlib.sha256`.
- Example: `src/token_meter/domain/llm.py:110`: `return hashlib.sha256(canonical.encode("utf-8")).hexdigest()`

#### `io`

In-memory file-like objects such as `StringIO`.

- Imported in 2 file(s).
- What this repository uses from it: `io.StringIO`.
- Example: `src/token_meter/infrastructure/csv_journal.py:36`: `buffer = io.StringIO()`

#### `json`

Reads and writes JSON text (`loads` text to Python objects, `dumps` the other way).

- Imported in 12 file(s).
- What this repository uses from it: `json.loads`, `json.dumps`, `json.JSONDecodeError`.
- Example: `src/token_meter/domain/llm.py:109`: `canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`

#### `logging`

Writes log messages with a level, a source name and extra fields.

- Imported in 7 file(s).
- What this repository uses from it: `logging.getLogger`, `logging.INFO`, `logging.Formatter`, `logging.LogRecord`, `logging.StreamHandler`, `logging.getLevelName`, `logging.WARNING`.
- Example: `src/token_meter/application/metered_model.py:11`: `_log = logging.getLogger(__name__)`

#### `math`

Mathematical functions (square root, rounding up, logarithms).

- Imported in 1 file(s).
- What this repository uses from it: `math.ceil`.
- Example: `src/token_meter/domain/estimation.py:34`: `return max(1, math.ceil((len(text) + len(system)) / ratio)) + self.per_call_overhead`

#### `os`

Operating-system services: environment variables (`os.environ`), file descriptors (`os.fsync`), process ids and more.

- Imported in 5 file(s).
- What this repository uses from it: `os.environ`, `os.fsync`.
- Example: `src/token_meter/infrastructure/csv_journal.py:44`: `os.fsync(handle.fileno())`

#### `pathlib`

File locations as objects (`Path`).

- Imported in 9 file(s).
- What this repository uses from it: `Path`.
- Example: `src/token_meter/infrastructure/csv_journal.py:26`: `def __init__(self, path: Path) -> None:`

#### `random`

Pseudo-random numbers. A `random.Random(seed)` object gives the same sequence every time for the same seed.

- Imported in 4 file(s).
- What this repository uses from it: `random.Random`.
- Example: `src/token_meter/infrastructure/resilient.py:29`: `rng: random.Random | None = None,`

#### `re`

Regular expressions: patterns that search and extract text.

- Imported in 1 file(s).
- What this repository uses from it: `re.compile`.
- Example: `src/token_meter/domain/analysis.py:19`: `_WORD = re.compile(r"[a-z]+")`

#### `signal`

Receives operating-system signals such as SIGTERM and SIGINT in a Python handler function.

- Imported in 3 file(s).
- What this repository uses from it: `signal.SIGTERM`, `signal.signal`, `signal.SIGINT`, `signal.SIGKILL`, `signal.raise_signal`, `signal.SIG_DFL`, `signal.default_int_handler`.
- Example: `src/token_meter/infrastructure/shutdown.py:18`: `for number in (signal.SIGINT, signal.SIGTERM):`

#### `statistics`

Mean, median and standard deviation.

- Imported in 1 file(s).
- What this repository uses from it: `statistics.fmean`, `statistics.median`.
- Example: `src/token_meter/domain/analysis.py:137`: `return round(statistics.median(residuals))`

#### `subprocess`

Starts another program from Python and reads its output and exit code.

- Imported in 1 file(s).
- What this repository uses from it: `subprocess.Popen`, `subprocess.PIPE`.

#### `sys`

The interpreter itself: command-line arguments (`sys.argv`), standard streams (`sys.stdout`, `sys.stderr`) and `sys.exit()`.

- Imported in 3 file(s).
- What this repository uses from it: `sys.stderr`, `sys.exit`, `sys.executable`.
- Example: `src/token_meter/infrastructure/logging.py:45`: `handler = logging.StreamHandler(stream or sys.stderr)`

#### `threading`

Threads, locks (`Lock`) and events (`Event`).

- Imported in 2 file(s).
- What this repository uses from it: `threading.Lock`, `threading.Event`.
- Example: `src/token_meter/infrastructure/recording.py:25`: `self._lock = threading.Lock()`

#### `time`

Clocks and sleeping: `time.monotonic()` is a clock that never goes backwards, good for measuring durations; `time.sleep()` pauses.

- Imported in 5 file(s).
- What this repository uses from it: `time.sleep`, `time.monotonic`.
- Example: `src/token_meter/application/run_meter.py:78`: `sleep: Callable[[float], None] = time.sleep,`

#### `types`

Names for built-in object types; `FrameType` appears in the signature of a signal handler.

- Imported in 1 file(s).
- What this repository uses from it: `FrameType`.
- Example: `src/token_meter/infrastructure/shutdown.py:21`: `def _handle(self, _number: int, _frame: FrameType | None) -> None:`

#### `typing`

Type-hint helpers: `Any`, `Protocol`, `Literal`, `Final`, `Annotated`, `Concatenate`, `TextIO`.

- Imported in 8 file(s).
- What this repository uses from it: `Any`, `Protocol`, `Literal`, `TextIO`.
- Example: `src/token_meter/application/ports.py:13`: `class ChatModel(Protocol):`

## Try it yourself

1. How many top-level modules this Python's standard library has.

```bash
.venv/bin/python -c "import sys; print(len(sys.stdlib_module_names), 'standard-library modules')"
```

What you should see (captured from this repository):

```text
290 standard-library modules
```

2. `hashlib`: the SHA-256 fingerprint of five bytes. Change one letter and every digit changes.

```bash
.venv/bin/python -c "import hashlib; print(hashlib.sha256(b'hello').hexdigest())"
```

What you should see (captured from this repository):

```text
2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
```

3. `decimal`: exact arithmetic.

```bash
.venv/bin/python -c "from decimal import Decimal; print(Decimal('0.1') + Decimal('0.2'))"
```

What you should see (captured from this repository):

```text
0.3
```

4. `json`: Python object to text and back.

```bash
.venv/bin/python -c "import json; s = json.dumps({'a': [1, 2]}); print(s, json.loads(s)['a'][1])"
```

What you should see (captured from this repository):

```text
{"a": [1, 2]} 2
```

5. `random`: two generators with the same seed give the same numbers.

```bash
.venv/bin/python -c "import random; a = random.Random(7); b = random.Random(7); print(a.random() == b.random())"
```

What you should see (captured from this repository):

```text
True
```

## Mistakes people make

- **Shadowing a module with your own file name.** A file named `json.py` in the project would hide the standard `json`. Module names here avoid the standard names.
- **Using `time.time()` to measure a duration.** The wall clock can jump. Durations use `time.monotonic()`.
- **Using `random` for secrets.** `random` is predictable. Here it only makes test data and jitter; it is not used for security.
- **Reading a whole huge file with `read_text()`.** Fine for these small data files; large files need streaming.
- **Trusting `os.environ` values to be set.** The settings code supplies defaults and checks values.

## Check yourself

1. Why can the project use `json` without adding it to `pyproject.toml`?

   *Answer:* It is part of the standard library, which comes with Python.

2. Which module measures durations safely and why?

   *Answer:* `time.monotonic()`, because it never jumps backwards.

3. What does `hashlib.sha256(data).hexdigest()` return?

   *Answer:* A 64-character hexadecimal fingerprint of the data.

4. What does a `ThreadPoolExecutor` do?

   *Answer:* Runs submitted functions on a fixed pool of worker threads.

5. What is `sys.argv`?

   *Answer:* The list of command-line words the program was started with.

## Further reading

- The Python Standard Library reference, https://docs.python.org/3.13/library/index.html (each module's page lists what it provides; examples above were run on Python 3.13).

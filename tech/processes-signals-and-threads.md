# Processes, signals and threads

## What it is

A **process** is one running program: its own memory, its own open files, and a number called the **process id** (pid). A process can start other processes (children) and can end with an **exit code**: `0` means success, anything else means a problem. A **signal** is a small message the operating system delivers to a process: `SIGTERM` politely asks it to stop, `SIGINT` is what Ctrl-C sends, `SIGKILL` removes it immediately and cannot be caught. A **thread** is a separate line of execution *inside* one process; threads share memory.

Three questions follow from these: how does a program stop cleanly when asked (signals), what happens to its data if it is killed mid-way (crash safety), and what goes wrong when two threads touch the same data (locks).

## Why this repository uses it

The repositories make promises about interruption: "a killed run resumes with no call paid twice", "the service finishes in-flight requests when stopped", "two processes racing on one order produce one refund". Those promises can only be tested with real processes, real signals and real threads, so the tests start the programs as subprocesses and kill them, and the code protects shared data with locks.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/token_meter/infrastructure/shutdown.py` | turns SIGINT and SIGTERM into a flag the loops check |
| `tests/integration/` | start real subprocesses, send signals, check the state afterwards |
| `Makefile` | `nohup ... &`, `kill`, `kill -0`, pid files (see `make.md`) |
| `src/token_meter/` | `threading` locks and events, thread pools where used |

## How it works underneath

**Signals are asynchronous.** The kernel interrupts the process at any point and calls the handler; Python runs it between two bytecode instructions of the main thread. That is why handlers only set a flag.

**SIGKILL and durability.** Because SIGKILL gives the program no chance to react, anything it had not yet written to disk is lost, and a file may end in a half-written row. Code that must survive this writes data in small durable steps (append one line, flush, `fsync`) and reads state back carefully on start.

**Exit codes.** A parent reads the child's exit code. Conventions here: 0 success, 2 bad settings, 3 refused before starting (budget), 4 interrupted (resume later), 5 waiting for approval (scheduling agent).

**Threads and the GIL.** In standard Python only one thread runs Python code at a time (the global interpreter lock), but a thread that waits for the network or the disk lets others run. So threads help with waiting, not with heavy calculation, and they still need locks around shared data, because a switch can happen between any two steps of `x = x + 1`.

**Deadlock.** If thread A waits for a lock that B holds while B waits for one A holds, both wait forever. The code takes one lock at a time and keeps critical sections short.

**Daemon-free shutdown.** A thread pool is closed with `with`; services close their connections after `uvicorn.run` returns.

## Walkthrough of this repository's use

### Telling a running program to stop: `src/token_meter/infrastructure/shutdown.py`

`src/token_meter/infrastructure/shutdown.py`, lines 1 to 29:

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
        return self._requested.is_set()
```

- `signal.signal(number, handler)` tells the operating system: when this process receives signal `number`, call `handler` instead of the default action. For `SIGINT` (Ctrl-C) the default is to stop at once; for `SIGTERM` (the polite stop request from `kill`) the default is also to stop at once. Here both are routed to `_handle`.
- `threading.Event()` is a thread-safe flag: `set()` raises it, `is_set()` reads it. A signal handler runs at an unpredictable moment between two lines of the main program, so it must do almost nothing; it only raises the flag.
- The work loops check `requested` between units of work (between two model calls, for example). So a stop request lets the **current call finish**, writes its result, and then the loop ends cleanly, closing files. The command-line program then returns a special exit code that says "interrupted, resume later" (the exit codes are listed below).
- `FrameType` is only a type hint for the second argument Python passes to a handler (the running code's stack frame); the handler ignores it (`_frame`).

### Proving it with a real process

The integration tests start the program as a **subprocess** and kill it.

`tests/integration/test_cli_process.py`, lines 43 to 63:

```python
def test_a_run_killed_with_sigkill_resumes_and_ends_with_exactly_450_rows_and_no_repeated_key(tmp_path):
    journal = tmp_path / "journal.csv"
    env = environment(journal, THROTTLE_SECONDS="0.01")
    first = meter("run", env=env)
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline and (not journal.exists() or len(journal.read_text().splitlines()) < 120):
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
    assert len(set(keys)) == 450
```

- `subprocess` starts another program from Python and gives back a handle (`Popen`) or a finished result (`run`). `env=` is the environment the child gets, `communicate()` waits for it and collects its output, and `returncode` is its exit code.
- `SIGKILL` (sent with `send_signal` or `os.kill`) removes the process at once: no handler runs, no file is closed, no cleanup. This is the **crash test**: after it the program must still be correct when restarted.
- `SIGTERM` tests the polite path: the process finishes what it is doing and exits with its "interrupted" exit code.

### Threads and locks

A **thread** is an independent line of execution inside one process; threads share memory. Two threads changing the same data at the same time can corrupt it, so shared state is guarded by a **lock**: only one thread at a time can hold it.

`src/token_meter/infrastructure/recording.py`, lines 23 to 27:

```python
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._entries: dict[str, dict[str, Any]] = {}
        files = sorted(path.glob("*.jsonl")) if path.is_dir() else ([path] if path.exists() else [])
```

A `Lock` is held with `with self._lock:`; other threads that reach the same line wait. An `RLock` (re-entrant) may be taken again by the thread that already holds it.

## Try it yourself

1. Signals are numbers: SIGINT is 2, SIGKILL is 9, SIGTERM is 15.

```bash
.venv/bin/python -c "import os, signal; print(os.getpid() > 0, signal.SIGTERM.value, signal.SIGINT.value, signal.SIGKILL.value)"
```

What you should see (captured from this repository):

```text
True 15 2 9
```

2. Start a background `sleep`, send it SIGTERM, and read its exit code: 143, which is 128 plus the signal number 15.

```bash
sh -c 'sleep 30 & echo $! > /dev/null; kill $!; wait $! 2>/dev/null; echo "exit code after SIGTERM: $?"'
```

What you should see (captured from this repository):

```text
exit code after SIGTERM: 143
```

3. Start a child process and read its exit code.

```bash
.venv/bin/python -c "import subprocess, sys; p = subprocess.run([sys.executable, '-c', 'import sys; sys.exit(7)']); print(p.returncode)"
```

What you should see (captured from this repository):

```text
7
```

4. Four threads each add 1 fifty thousand times to a shared counter under a lock: the total is exactly 200000.

```bash
.venv/bin/python - <<'EOF'
import threading
n = 0
lock = threading.Lock()
def work():
    global n
    for _ in range(50000):
        with lock:
            n += 1
ts = [threading.Thread(target=work) for _ in range(4)]
[t.start() for t in ts]
[t.join() for t in ts]
print(n)
EOF
```

What you should see (captured from this repository):

```text
200000
```

5. A process sends itself SIGTERM; because a handler is installed, it runs instead of stopping the process.

```bash
.venv/bin/python - <<'EOF'
import signal, os, time
seen = []
signal.signal(signal.SIGTERM, lambda n, f: seen.append(n))
os.kill(os.getpid(), signal.SIGTERM)
time.sleep(0.1)
print('handler ran, signal number', seen)
EOF
```

What you should see (captured from this repository):

```text
handler ran, signal number [15]
```

## Mistakes people make

- **Doing real work in a signal handler.** It can run in the middle of anything. The handler only sets a flag.
- **Assuming `kill` is instant.** SIGTERM is a request; the program stops after the current unit of work.
- **Trusting a file after `kill -9`.** It may end mid-row; readers cut a torn tail (see `csv.md`).
- **Sharing data between threads without a lock.** Updates can interleave and be lost.
- **Waiting forever.** `communicate(timeout=...)` and deadlines in the tests prevent a hung test run.
- **Leaving a child running.** The tests always kill or wait for the subprocesses they start.

## Check yourself

1. What is the difference between SIGTERM and SIGKILL?

   *Answer:* SIGTERM can be caught so the program can finish cleanly; SIGKILL cannot be caught.

2. Why does the handler only set an `Event`?

   *Answer:* A handler can run at any moment, so it must do almost nothing; the loop checks the flag at a safe point.

3. What does a lock protect?

   *Answer:* Shared data from being changed by two threads at once.

4. What does exit code 143 mean?

   *Answer:* The process was ended by signal 15 (SIGTERM): 128 plus 15.

5. Why are killed-process tests part of the suite?

   *Answer:* Crash safety can only be shown by actually crashing the program.

## Further reading

- Python `signal`, `subprocess`, `threading` and `concurrent.futures`, https://docs.python.org/3/library/signal.html, https://docs.python.org/3/library/subprocess.html, https://docs.python.org/3/library/threading.html, https://docs.python.org/3/library/concurrent.futures.html (examples run locally on Python 3.13 and macOS).

# pytest

## What it is

A **test** is a small program that runs a piece of your code and checks that it did what you expect. **pytest** is the program that finds those tests, runs them, and reports which passed and which failed. A test is an ordinary function whose name starts with `test_`; it uses `assert` to state a fact. If every assert holds, the test passes.

Automated tests matter because code changes. Running them after every change tells you at once if something that used to work has broken.

## Why this repository uses it

The repository's claims ("the estimate is within a few percent of the bill", "a killed process resumes without paying twice", "the refund cannot be applied twice") are only believable if a test proves each one. pytest keeps the tests short, shows clear failure messages, and has a rich set of fixtures for temporary folders, fake environments and captured output. Markers let the same suite hold fast offline tests, tests that start real processes, and opt-in tests that call a real model.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `tests/` | 125 test functions in unit, integration and end-to-end groups |
| `tests/conftest.py` | fixtures shared by every test |
| `pyproject.toml` | `[tool.pytest.ini_options]`: where tests live, default options and markers |
| `Makefile` | `test`, `test-integration`, `test-e2e`, `test-live` |
| `.github/workflows/ci.yml` | `make check` runs the whole offline suite |

## How it works underneath

**Collection.** pytest walks `testpaths`, imports every file named `test_*.py`, and collects every function named `test_*` (and methods of classes named `Test*`). It builds the list of tests before running any.

**Assertion rewriting.** When pytest imports a test file it rewrites the plain `assert` statements so that a failure shows the values on both sides. You write `assert a == b`; pytest prints what `a` and `b` were.

**Fixtures by name.** For each test pytest looks at the parameter names, finds fixtures with those names (in the test file, then `conftest.py` files from the nearest folder upward, then built-in and plugin fixtures), runs them, and passes the results in. A fixture with a `yield` runs the code after the `yield` as cleanup when the test ends.

**Exit codes.** pytest ends with 0 if all tests passed, 1 if some failed, 2 if the run was interrupted, 3 for an internal error, 4 for a usage error and 5 if no tests were collected. `make` stops on any non-zero code.

**Plugins.** pytest finds installed plugins by name; `pytest-cov` adds the `--cov` options (see `coverage.md`).

## Walkthrough of this repository's use

### The settings

The pytest table of `pyproject.toml` is explained line by line in `pyproject-toml.md`. In short: `testpaths` makes pytest look only in `tests/`; `addopts` is added to every run; here it is `-ra --strict-markers -m 'not live'`; `markers` declares the labels below. Because `--strict-markers` is on, a typo such as `@pytest.mark.integraton` is an error and not a silently ignored label.

### Markers (labels on tests)

A **marker** is a label put on a test with `@pytest.mark.NAME` (or on a whole file with `pytestmark = pytest.mark.NAME`). `-m EXPRESSION` selects tests by label. This repository declares:

- `integration`: runs the command-line program as a subprocess (no network, recorded model). Used by 1 test file(s).
- `e2e`: the lesson's scenario end to end with the recorded model. Used by 1 test file(s).
- `live`: calls a real model; needs a key or a local server, run by `make test-live` only. Used by 1 test file(s).

The Makefile uses them: `make test` runs with the default options above (the marker filter in `addopts` leaves out the labels it names); `make test-integration` runs `-m integration`; `make test-e2e` runs `-m e2e`; `make test-live` runs `-m live` and is never part of `make check`.

### How many tests there are

125 test functions (a parametrized test counts once here; pytest reports each parameter row as its own test), by folder:

| Folder | Test functions |
| --- | --- |
| `tests/e2e` | 4 |
| `tests/integration` | 3 |
| `tests/live` | 2 |
| `tests/unit/application` | 13 |
| `tests/unit/domain` | 36 |
| `tests/unit/infrastructure` | 56 |
| `tests/unit/interfaces` | 11 |

### Every kind of test construct used here, with a real example

#### A plain test

A test is a function whose name starts with `test_`. It sets something up, runs the code being tested, and uses `assert` to state what must be true. If an `assert` is false, pytest marks the test failed and prints both sides of the comparison.

From this repository, `tests/unit/application/test_run_meter.py`, lines 34 to 39:

```python
def test_a_run_makes_every_call_and_journals_one_row_each():
    model, journal = ScriptedModel(), MemoryJournal()
    summary = RunMeter(model, journal).run(plan())
    assert (summary.calls_made, summary.calls_skipped, summary.interrupted) == (18, 0, False)
    assert len(journal.rows()) == 18
    assert len({r.key for r in journal.rows()}) == 18
```

#### Fixtures

A **fixture** is a function marked `@pytest.fixture` that builds something tests need (a sample object, a temporary folder, a fake clock). A test asks for it by naming it as a parameter, and pytest calls the fixture and passes the result in. Fixtures defined in `conftest.py` are available to every test below that folder.

From this repository, `tests/unit/interfaces/test_cli.py`, lines 16 to 28:

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
    return tmp_path
```

#### Parametrized tests

`@pytest.mark.parametrize("names", [values...])` runs the same test function once for each row of values. Each run is reported as its own test.

From this repository, `tests/unit/domain/test_analysis.py`, lines 66 to 78:

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
    assert fragment in explain_gap(kind, estimated, billed, missing)
```

#### `tmp_path`: a private temporary folder

A built-in fixture. pytest creates a new empty folder for the test and passes it as a `Path`. Tests write their files there, so they never touch the real `data/` or `out/` folders.

From this repository, `tests/unit/infrastructure/test_csv_journal.py`, lines 8 to 11:

```python
def test_a_new_journal_gets_one_header_and_no_rows(tmp_path):
    journal = CsvJournal(tmp_path / "out" / "j.csv")
    assert journal.rows() == []
    assert (tmp_path / "out" / "j.csv").read_text().strip() == ",".join(COLUMNS)
```

#### `monkeypatch`: changing things for one test

A built-in fixture that can set environment variables, replace attributes and change the working folder, and puts everything back when the test ends.

From this repository, `tests/unit/interfaces/test_cli.py`, lines 49 to 53:

```python
def test_a_budget_below_the_estimate_refuses_to_start_with_a_clear_message(workspace, capsys, monkeypatch):
    model = scripted(monkeypatch)
    assert main(["run", "--budget", "0.001"]) == EXIT_REFUSED
    assert "REFUSING TO START: estimated cost" in capsys.readouterr().err
    assert model.requests == []
```

#### `capsys`: capturing what a program prints

A built-in fixture that records what is written to the screen, so a test can check it.

From this repository, `tests/unit/interfaces/test_cli.py`, lines 37 to 41:

```python
def test_estimate_prints_the_whole_run_and_calls_no_model(workspace, capsys):
    assert main(["estimate"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "calls=450" in out
    assert "cost_est=$" in out
```

#### `pytest.raises`: checking that an error is raised

`with pytest.raises(SomeError):` passes if the code inside raises that error and fails if it does not.

From this repository, `tests/unit/application/test_run_meter.py`, lines 58 to 59:

```python
    with pytest.raises(BudgetExceeded):
        RunMeter(model, journal).run(plan(budget=Decimal("0.000001")))
```

## Try it yourself

1. Which pytest is installed.

```bash
.venv/bin/python -m pytest --version
```

What you should see (captured from this repository):

```text
pytest 9.1.1
```

2. Collect without running: how many tests the default options select. The last line shows how many were left out by the marker filter.

```bash
.venv/bin/python -m pytest --collect-only -q 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
tests/unit/interfaces/test_cli.py::test_a_shutdown_request_ends_the_run_with_the_interrupted_code

144/146 tests collected (2 deselected) in N.NNs
```

3. The markers this project declares, as pytest prints them.

```bash
.venv/bin/python -m pytest --markers 2>&1 | grep -E '^@pytest.mark.(integration|e2e|live)'
```

What you should see (captured from this repository):

```text
@pytest.mark.integration: runs the command-line program as a subprocess (no network, recorded model)
@pytest.mark.e2e: the lesson's scenario end to end with the recorded model
@pytest.mark.live: calls a real model; needs a key or a local server, run by `make test-live` only
```

4. Run only the domain unit tests. `-q` is quiet, and the last line is the summary with the number of tests and the time.

```bash
.venv/bin/python -m pytest tests/unit/domain -q -p no:cacheprovider 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
...........................................                              [100%]
43 passed in N.NNs
```

5. The live tests exist but are deselected by default; with `-m live` they are collected.

```bash
.venv/bin/python -m pytest -m live --collect-only -q 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
tests/live/test_live_models.py::test_the_local_model_returns_a_usage_block_and_obeys_temperature_zero

2/146 tests collected (144 deselected) in N.NNs
```

## Mistakes people make

- **A test that depends on another test.** Tests may run in any order. Each test here builds its own data (fixtures, `tmp_path`).
- **Tests that touch the real files or network.** They would pass or fail by chance. The offline suite uses `tmp_path`, recorded answers and local ports.
- **Assertions that can never fail.** `assert x` on a non-empty list is always true. The tests compare exact values.
- **Typos in marker names.** `--strict-markers` turns them into errors.
- **Running live tests by accident.** `addopts` excludes them (`-m 'not live'`); only `make test-live` overrides it.
- **Testing implementation details.** Tests call the public functions and check results, so the code behind them can change.

## Check yourself

1. What makes a function a test for pytest?

   *Answer:* Its name starts with `test_` and it is in a file named `test_*.py` under `testpaths`.

2. How does a test get a fixture?

   *Answer:* By naming it as a parameter; pytest calls the fixture and passes the result.

3. What does `-m 'not live'` do?

   *Answer:* Skips every test marked `live`.

4. What does `tmp_path` give a test?

   *Answer:* A new empty temporary folder that is private to that test.

5. Why is `--strict-markers` on?

   *Answer:* So an unknown or misspelled marker is an error instead of being silently ignored.

## Further reading

- pytest documentation, https://docs.pytest.org/en/stable/ (pytest 9.1.1 is pinned in the lock file; the commands above were run with it).

# pyproject.toml

## What it is

`pyproject.toml` is the file at the top of a Python project that describes it. It is written in TOML (see `toml.md`). It has three jobs: `[build-system]` says how to build the project; `[project]` gives its name, version, Python version, dependencies and command-line programs; and `[tool.NAME]` tables hold the settings of tools such as ruff and pytest.

The layout is a Python standard, so pip, setuptools and many other tools know where to look.

## Why this repository uses it

Putting all configuration into one file means a reader opens one place to learn how the project builds, what it depends on and how it is checked. Without it, the same settings would be spread over `setup.py`, `setup.cfg`, `pytest.ini`, `mypy.ini`, `.coveragerc` and more.

It is also where the *architecture rules* live: two import-linter contracts that stop the core code from importing a vendor SDK or an HTTP client.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `pyproject.toml` | the file itself |
| `Makefile` | the stamp rule depends on it; `lint` and `test` rely on the settings in it |
| `requirements.lock, requirements-dev.lock` | compiled from its `dependencies` and `dev` group |

## How it works underneath

Each tool finds `pyproject.toml` by looking in the current folder and the folders above it, then reads only its own table: ruff reads `[tool.ruff]`, mypy reads `[tool.mypy]`, pytest reads `[tool.pytest.ini_options]`, coverage reads `[tool.coverage.run]` and `[tool.coverage.report]`, and import-linter reads `[tool.importlinter]`. pip and setuptools read `[build-system]` and `[project]`.

**Version rules** use a small language: `==2.3.0` (exactly), `>=8,<10` (at least 8 and below 10), `>=5` (5 or newer). A rule on the project's own `dependencies` says what the program *needs*; the lock files say what is *installed*.

**Entry points.** An entry under `[project.scripts]` becomes an executable file when the project is installed.

## Walkthrough of this repository's use

`pyproject.toml`, the whole file, block by block. Under each block, every line is explained.

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"
```

- `[build-system]`: Starts the table that tells build tools how to build this project (see `setuptools.md`).
- `requires = ["setuptools>=75"]`: The packages needed to build: setuptools version 75 or newer.
- `build-backend = "setuptools.build_meta"`: The entry point pip calls to do the build.

```toml
[project]
name = "ai-token-and-cost-meter"
version = "0.1.0"
description = "meter: estimate the tokens and cost of a batch of model calls before sending it, then check the estimate against the bill."
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }
authors = [{ name = "Sumit Srivastava" }]
dependencies = [
    "anthropic==2.3.0",
    "httpx==0.28.1",
]
```

- `[project]`: Starts the table with the project's own description.
- `name = "ai-token-and-cost-meter"`: The name pip knows this project by (`pip show ai-token-and-cost-meter`). Distribution names use hyphens; the Python package inside uses underscores.
- `version = "0.1.0"`: The project version, as text.
- `description = "meter: estimate the tokens and cost of a batch of model calls before sending it, then check the estimate against the bill."`: A one-sentence description; pip stores it in the package metadata.
- `readme = "README.md"`: The file whose content becomes the long description.
- `requires-python = ">=3.12"`: The oldest Python allowed: 3.12 or newer. pip refuses to install on an older Python.
- `license = { text = "MIT" }`: The license, as an inline table with one key. MIT is a short permissive license (the full text is in the `LICENSE` file).
- `authors = [{ name = "Sumit Srivastava" }]`: A list with one author, written as an inline table.
- `dependencies = [`: Starts the list of packages the program needs to run. Each item is a *requirement*: a package name plus an optional version rule.
- `"anthropic==2.3.0",`: The package `anthropic`: exactly version 2.3.0. What it is: The official Python library for the anthropic API.
- `"httpx==0.28.1",`: The package `httpx`: exactly version 0.28.1. What it is: The next generation HTTP client.
- `]`: Closes the list.

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8,<10",
    "pytest-cov>=5",
    "ruff>=0.6",
    "mypy>=1.11",
    "import-linter>=2.0",
    "pip-audit>=2.7",
    "httpx2",
]
```

- `[project.optional-dependencies]`: Starts the table of optional groups of dependencies.
- `dev = [`: The group named `dev`: tools used only for developing the project (tests, checks). `make install` gets them through `requirements-dev.lock`, which was compiled with `--extra dev`.
- `"pytest>=8,<10",`: The package `pytest`: version 8 or newer, but older than 10. What it is: pytest: simple powerful testing with Python.
- `"pytest-cov>=5",`: The package `pytest-cov`: version 5 or newer. What it is: Pytest plugin for measuring coverage.
- `"ruff>=0.6",`: The package `ruff`: version 0.6 or newer. What it is: An extremely fast Python linter and code formatter, written in Rust.
- `"mypy>=1.11",`: The package `mypy`: version 1.11 or newer. What it is: Optional static typing for Python.
- `"import-linter>=2.0",`: The package `import-linter`: version 2.0 or newer. What it is: Lint your Python architecture.
- `"pip-audit>=2.7",`: The package `pip-audit`: version 2.7 or newer. What it is: A tool for scanning Python environments for known vulnerabilities.
- `"httpx2",`: The package `httpx2`: no version rule, so any version is allowed here; the lock file pins the exact one. What it is: The next generation HTTP client. It is listed here because the Claude SDK is built on it and the tests import it directly to fake the network (see `httpx.md`).
- `]`: Closes the list.

```toml
[project.scripts]
meter = "token_meter.interfaces.cli:main"
```

- `[project.scripts]`: Starts the table of command-line programs to create at install time.
- `meter = "token_meter.interfaces.cli:main"`: Creates a command called `meter`. When you run it, Python imports the module `token_meter.interfaces.cli` and calls its function `main`. pip writes the small launcher program into `.venv/bin/meter`.

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

- `[tool.setuptools.packages.find]`: Starts setuptools' package-finding settings.
- `where = ["src"]`: Look for packages inside the `src` folder.

```toml
[tool.ruff]
line-length = 120
target-version = "py312"
src = ["src", "tests"]
extend-exclude = ["tech"]
```

- `[tool.ruff]`: Starts the settings of ruff, the linter and formatter (see `ruff.md`).
- `line-length = 120`: Lines may be up to 120 characters; the formatter wraps longer lines and the linter reports them.
- `target-version = "py312"`: Check and format for Python 3.12: ruff may use 3.12 syntax and suggests upgrades to it.
- `src = ["src", "tests"]`: Where the project's own code lives, so ruff can tell project imports from third-party imports when it sorts them.
- `extend-exclude = ["tech"]`: Also leave the folder `tech/` out of ruff's checks, on top of what it skips by default. The technology notes in `tech/` are Markdown files that quote Python code exactly as it appears in the source; ruff 0.17 can format Python code blocks inside Markdown files, and it would flag every quoted snippet that is a piece of a longer file (for example an indented method) as unformatted. The notes are documentation, not code to format.

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "N", "C4", "RUF", "PT", "D100", "D101", "D103", "D104"]
ignore = ["N818"]
```

- `[tool.ruff.lint]`: Starts the linter's settings.
- `select = ["E", "F", "I", "B", "UP", "SIM", "N", "C4", "RUF", "PT", "D100", "D101", "D103", "D104"]`: The rule families that are switched on. Each code is a letter prefix; the lines below list them.
- `ignore = ["N818"]`: Switch off rule N818, which wants exception names to end in `Error`.

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["D", "E501"]
"scripts/**" = ["D", "E501"]
```

- `[tool.ruff.lint.per-file-ignores]`: Starts the list of rules that are switched off for certain files.
- `"tests/**" = ["D", "E501"]`: In every file under `tests/`, switch off these rules: `D` (all docstring rules, since test functions do not need docstrings), `E501` (line too long).
- `"scripts/**" = ["D", "E501"]`: The same relaxations for the helper scripts under `scripts/`.

```toml
[tool.mypy]
python_version = "3.12"
strict = true
files = ["src", "tests"]
```

- `[tool.mypy]`: Starts the settings of mypy, the type checker (see `mypy.md`).
- `python_version = "3.12"`: Check as if running Python 3.12.
- `strict = true`: Switch on mypy's strictest bundle of checks (every function must be annotated, no untyped calls, and more).
- `files = ["src", "tests"]`: Which folders to check when `mypy` is run with no arguments.

```toml
[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false
disallow_incomplete_defs = false
disallow_untyped_calls = false
```

- `[[tool.mypy.overrides]]`: Starts one entry in the list of per-module overrides.
- `module = ["tests.*"]`: This override applies to every module whose name starts with `tests.`.
- `disallow_untyped_defs = false`: For tests, a function without type annotations is allowed.
- `disallow_incomplete_defs = false`: For tests, a function with only some annotations is allowed.
- `disallow_untyped_calls = false`: For tests, calling a function that has no annotations is allowed.

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers -m 'not live'"
markers = [
    "integration: runs the command-line program as a subprocess (no network, recorded model)",
    "e2e: the lesson's scenario end to end with the recorded model",
    "live: calls a real model; needs a key or a local server, run by `make test-live` only",
]
```

- `[tool.pytest.ini_options]`: Starts pytest's settings (see `pytest.md`).
- `testpaths = ["tests"]`: Look for tests only in `tests/`.
- `addopts = "-ra --strict-markers -m 'not live'"`: Options added to every `pytest` run. `-ra` prints a summary line for everything that was not a plain pass (skips, failures). `--strict-markers` makes an unknown marker an error, which catches typos. `-m 'not live'` runs everything except tests marked `live` (they call a real model).
- `markers = [`: Declares the custom markers. Each item is `name: description`.
- `"integration: runs the command-line program as a subprocess (no network, recorded model)",`: Declares the marker `integration` (so `--strict-markers` accepts `@pytest.mark.integration`). Its description: runs the command-line program as a subprocess (no network, recorded model).
- `"e2e: the lesson's scenario end to end with the recorded model",`: Declares the marker `e2e` (so `--strict-markers` accepts `@pytest.mark.e2e`). Its description: the lesson's scenario end to end with the recorded model.
- `` "live: calls a real model; needs a key or a local server, run by `make test-live` only", ``: Declares the marker `live` (so `--strict-markers` accepts `@pytest.mark.live`). Its description: calls a real model; needs a key or a local server, run by `make test-live` only.
- `]`: Closes the list.

```toml
[tool.coverage.run]
source = ["token_meter"]
branch = true
```

- `[tool.coverage.run]`: Starts the settings for measuring coverage (see `coverage.md`).
- `source = ["token_meter"]`: Measure only the package `token_meter`, not the tests or libraries.
- `branch = true`: Measure *branch* coverage: whether both outcomes of every `if` were exercised, not just whether each line ran.

```toml
[tool.coverage.report]
show_missing = true
skip_covered = false
```

- `[tool.coverage.report]`: Starts the settings for the printed coverage table.
- `show_missing = true`: Add a column listing the line numbers that were never run.
- `skip_covered = false`: Keep fully covered files in the table (do not hide them).

```toml
[tool.importlinter]
root_package = "token_meter"
include_external_packages = true
```

- `[tool.importlinter]`: Starts import-linter's settings (see `import-linter.md`).
- `root_package = "token_meter"`: The package whose internal imports are checked: `token_meter`.
- `include_external_packages = true`: Also track imports of third-party packages, which the second contract needs.

```toml
[[tool.importlinter.contracts]]
name = "Layers: interfaces on infrastructure on application on domain"
type = "layers"
layers = ["token_meter.interfaces", "token_meter.infrastructure", "token_meter.application", "token_meter.domain"]
```

- `[[tool.importlinter.contracts]]`: Starts one contract: a rule about imports.
- `name = "Layers: interfaces on infrastructure on application on domain"`: The name pip knows this project by (`pip show Layers: interfaces on infrastructure on application on domain`). Distribution names use hyphens; the Python package inside uses underscores.
- `type = "layers"`: A *layers* contract: modules may import from layers below them, never from layers above.
- `layers = ["token_meter.interfaces", "token_meter.infrastructure", "token_meter.application", "token_meter.domain"]`: The layers from top to bottom: `interfaces` (the outside world) may import `infrastructure`, which may import `application`, which may import `domain` (the core). Never the other way.

```toml
[[tool.importlinter.contracts]]
name = "Domain and application never import a vendor SDK or an HTTP client"
type = "forbidden"
source_modules = ["token_meter.domain", "token_meter.application"]
forbidden_modules = ["anthropic", "httpx", "httpx2", "openai"]
```

- `[[tool.importlinter.contracts]]`: Starts one contract: a rule about imports.
- `name = "Domain and application never import a vendor SDK or an HTTP client"`: The name pip knows this project by (`pip show Domain and application never import a vendor SDK or an HTTP client`). Distribution names use hyphens; the Python package inside uses underscores.
- `type = "forbidden"`: A *forbidden* contract: the listed source modules must not import the listed forbidden modules.
- `source_modules = ["token_meter.domain", "token_meter.application"]`: The modules that are restricted: the core (`domain`) and the use cases (`application`).
- `forbidden_modules = ["anthropic", "httpx", "httpx2", "openai"]`: The modules they must not import, directly or through other modules: vendor SDKs, HTTP clients, web frameworks and database drivers. This keeps the core free of technology details.

## Try it yourself

1. The runtime dependencies as Python sees them.

```bash
.venv/bin/python -c "import tomllib; d = tomllib.load(open('pyproject.toml', 'rb')); print(d['project']['dependencies'])"
```

What you should see (captured from this repository):

```text
['anthropic==2.3.0', 'httpx==0.28.1']
```

2. The command-line programs the project installs.

```bash
.venv/bin/python -c "import tomllib; d = tomllib.load(open('pyproject.toml', 'rb')); print(d['project']['scripts'])"
```

What you should see (captured from this repository):

```text
{'meter': 'token_meter.interfaces.cli:main'}
```

3. pip's view of the same file after installation: name, version, summary.

```bash
.venv/bin/pip show ai-token-and-cost-meter | sed -n 1,4p
```

What you should see (captured from this repository):

```text
Name: ai-token-and-cost-meter
Version: 0.1.0
Summary: meter: estimate the tokens and cost of a batch of model calls before sending it, then check the estimate against the bill.
Home-page: 
```

4. Run the import contracts defined in this file. Both must be kept.

```bash
.venv/bin/lint-imports | tail -4
```

What you should see (captured from this repository):

```text
Layers: interfaces on infrastructure on application on domain KEPT
Domain and application never import a vendor SDK or an HTTP client KEPT

Contracts: 2 kept, 0 broken.
```

5. Ruff reports the settings it read from `[tool.ruff]`.

```bash
.venv/bin/ruff check --show-settings 2>/dev/null | grep -E 'line_length|target_version' | head -3
```

What you should see (captured from this repository):

```text
linter.unresolved_target_version = 3.12
linter.per_file_target_version = {}
linter.line_length = 120
```

## Mistakes people make

- **Loose version rules for runtime dependencies.** The program's runtime dependencies are pinned with `==` so the numbers in the README stay true.
- **Forgetting the lock file when a dependency changes.** The file `requirements-dev.lock` must be compiled again, otherwise the install will not match.
- **Declaring a marker in the wrong place.** Markers are declared in `[tool.pytest.ini_options]`; with `--strict-markers` an undeclared one fails the run.
- **Putting a tool's setting in the wrong table.** A misspelled table is silently ignored by the tool. Check with the commands above.
- **Skipping `requires-python`.** pip would install the project on a Python too old to run it.

## Check yourself

1. Which table lists the commands the project installs?

   *Answer:* `[project.scripts]`.

2. What does `>=8,<10` mean?

   *Answer:* Version 8 or newer, but older than 10.

3. Why is `dev` an optional group and not part of `dependencies`?

   *Answer:* The program does not need test tools to run; they are only for development.

4. What does `strict = true` do in `[tool.mypy]`?

   *Answer:* Switches on mypy's strictest set of checks.

5. Where do pip and setuptools look to learn the project name?

   *Answer:* In the `[project]` table of `pyproject.toml`.

## Further reading

- Python Packaging User Guide, https://packaging.python.org/en/latest/guides/writing-pyproject-toml/ (every table and key above was checked by loading the file with Python 3.13's `tomllib` and by running each tool, which read its own table).

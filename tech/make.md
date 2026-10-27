# Make and the Makefile

## What it is

**make** is a program that runs named recipes. You give it a file called `Makefile`. In that file you write *targets* (a name, followed by a colon), the *prerequisites* the target needs (other targets or files), and a *recipe* (the shell commands that make the target). When you type `make test` in a terminal, make finds the target `test`, first brings its prerequisites up to date, then runs its commands one by one.

A **terminal** is the text window where you type commands. A **shell** is the program inside the terminal that reads what you type and starts other programs. A **command** is one line you give the shell. A **target** is the thing you ask make to produce, such as `test`. A **recipe** is the list of commands under a target. A **prerequisite** is something that must exist or be current before the recipe runs.

make was written in 1976 to rebuild programs from source files, and it is still used because it is small and installed almost everywhere. In this repository it does not compile anything. It is a *menu of commands*: it gives every task a short, memorable name.

## Why this repository uses it

A new person cannot guess which ten commands to type, in which order, with which flags. The Makefile writes them down once, so `make up`, `make run`, `make test`, `make lint` and `make down` mean the same thing on every computer and in the continuous-integration job. It also encodes *order*: `make test` first makes sure the virtual environment exists, because the target depends on a stamp file; you cannot forget the install step.

The Makefile also keeps the long environment settings (which model to use, where recordings live, which port) in one place, so the commands in the README stay short.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Makefile` | the whole file: 20 targets that wrap every command in the project |
| `.github/workflows/ci.yml` | runs `make check` and `make audit` on every push |
| `.editorconfig` | tells editors to use real tab characters in the Makefile (`[Makefile]` section) |
| `README.md` | tells the reader to run `make up`, `make run`, `make test` |

## How it works underneath

**How make reads the file.** make reads the whole Makefile first. It builds a graph: each target points at its prerequisites. Then it walks the graph from the target you asked for. For a target that is the *name of a file*, it compares modification times: if the file exists and is newer than every prerequisite, nothing needs doing; if it is missing or older, the recipe runs. This is what the stamp rule in this repository uses: `.venv/.installed` is rebuilt only when `requirements-dev.lock` or `pyproject.toml` has changed since it was last touched.

**Phony targets.** `test`, `lint` and `down` are not files. The `.PHONY` line says so; make then always runs their recipes.

**Each recipe line is its own shell.** make starts a new `/bin/sh -c "..."` for every line of a recipe. A `cd` on one line is forgotten by the next line. That is why long jobs in this Makefile are written on one line with `;` or `&&` between the parts, or with a trailing backslash that joins physical lines.

**Variables.** `NAME = value` is looked up lazily every time it is used. `NAME := value` is worked out once, right away. `NAME ?= value` sets it only if it is not already set (from the command line or the environment). `$(NAME)` pastes the value. Inside a recipe a single `$` belongs to make, so a `$` meant for the shell is written `$$`.

**Special characters in front of a recipe line.** `@` means do not print the command before running it. `-` means ignore a failure and keep going.

**Exit codes.** Every program ends with a number: `0` means success, anything else means failure. make stops at the first recipe line that returns non-zero and returns failure itself, which is how `make check` makes a build go red.

**The required tab.** A recipe line must start with a real tab character, not spaces. If it does not, GNU Make says `missing separator`. This repository's `.editorconfig` has `[Makefile]` / `indent_style = tab` so editors keep the tabs.

## Walkthrough of this repository's use

`Makefile`, the whole file, block by block. Under each block, every line is explained.

```make
# make up | run | record | test | test-live | lint | down      (make help lists everything)
PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)
VENV := .venv
PY := $(VENV)/bin/python
STAMP := $(VENV)/.installed
LOCAL_MODEL ?= qwen2.5:0.5b
RECORDING := tests/fixtures/recordings/meter-qwen2.5-0.5b.jsonl
```

- `# make up | run | record | test | test-live | lint | down      (make help lists everything)`: A comment. make ignores everything after a `#`.
- `PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)`: Sets `PYTHON` to the Python program used to make the virtual environment. `?=` means "set this only if it is not already set", so you can override it (`make PYTHON=python3.12 up`). `$(shell ...)` runs a shell command while make reads the file and pastes in what it prints. `command -v NAME` prints the full path of `NAME` if it exists and prints nothing (and fails) if not. The `||` means "if the left side failed, try the right side", so the line tries Python 3.13, then 3.12, then plain `python3`.
- `VENV := .venv`: Sets `VENV` to the name of the virtual-environment folder. `:=` means "work out the value now, once".
- `PY := $(VENV)/bin/python`: Sets `PY` to the Python program inside the virtual environment. `$(VENV)` is replaced by `.venv`, so this is `.venv/bin/python`.
- `STAMP := $(VENV)/.installed`: Sets `STAMP` to `.venv/.installed`, an empty file that the install rule creates when it finishes. Its modification time records "the environment was installed at this moment".
- `LOCAL_MODEL ?= qwen2.5:0.5b`: Sets `LOCAL_MODEL` to `qwen2.5:0.5b` unless you already set it. This is the name of a small open-weight model that `ollama` can download (the part before the colon is the model family, the part after it is the size variant).
- `RECORDING := tests/fixtures/recordings/meter-qwen2.5-0.5b.jsonl`: Sets `RECORDING` to the path `tests/fixtures/recordings/meter-qwen2.5-0.5b.jsonl`. Naming a path once means every target that needs it uses the same text.

```make
-include .env
export
```

- `-include .env`: Reads the file `.env` if it exists (a plain `include` would stop with an error when it is missing; the leading `-` means "if it is missing, carry on"). The file holds `NAME=value` lines you copied from `env.example`.
- `export`: Passes every make variable to the programs that make starts, as environment variables. Together with the line above, a value written in `.env` reaches the Python program.

```make
.PHONY: help install up models run run-resume estimate report record record-fresh lint format typecheck test test-integration test-e2e \
        test-live audit check down clean
```

- `.PHONY: help install up models run run-resume estimate report record record-fresh lint format typecheck test test-integration test-e2e test-live audit check down clean`: Declares these names "phony": they are the names of actions, not of files. Without this, a file or folder that happens to be called `test` or `clean` would make make think the target was already up to date and skip it.

```make
help: ## list the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort
```

- `help: ## list the targets`: Defines the target `help`. It has no prerequisites. The text after `##` (`list the targets`) is the help text that `make help` prints.
- `grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort`: The leading `@` tells make not to print the command before running it. Prints the help list. `grep -E` searches for lines matching a pattern: here, lines that start with a target name made of lowercase letters and hyphens, then a colon, and contain `## `. `$(MAKEFILE_LIST)` is the name of this Makefile. The `|` (pipe) hands grep's output to `sed -E 's/:.*## /\t/'`, which replaces everything from the colon through `## ` with a tab character, leaving `target<TAB>help text`. The next `|` hands that to `sort`, which puts the lines in alphabetical order.

```make
$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@
```

- `$(STAMP): requirements-dev.lock pyproject.toml`: Defines a rule whose target is a file, the stamp (`.venv/.installed`). Its prerequisites, which make brings up to date before running the recipe: the file `requirements-dev.lock`; the file `pyproject.toml`. If the stamp is missing, or older than either file, make runs the recipe below; otherwise it does nothing, which makes every later `make` command start fast.
- `$(PYTHON) -m venv $(VENV)`: Creates the virtual environment: a private folder `.venv` holding its own copy of the Python program and its own empty place for installed packages. `-m venv` means "run the module named `venv` that ships with Python".
- `$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock`: Installs every package named in `requirements-dev.lock` into the virtual environment. `-q` is quiet. `--require-hashes` makes pip refuse any file whose fingerprint (a sha256 hash) is not listed in the lock file, and also refuse any package that is not pinned to an exact version. `-r FILE` means "read the list of packages from this file".
- `$(VENV)/bin/pip install -q --no-deps -e .`: Installs this project itself. `.` means "the project in this folder". `-e` (editable) links the code in `src/` instead of copying it, so editing a file takes effect at once. `--no-deps` stops pip from looking for dependencies again: the lock file already installed exactly the versions wanted.
- `touch $@`: Creates the stamp file, or updates its modification time. `$@` is make's automatic name for "the target of this rule", here `.venv/.installed`. The stamp is only touched if every line above succeeded, because make stops at the first failing line.

```make
install: $(STAMP) ## create .venv from the lock file
```

- `install: $(STAMP) ## create .venv from the lock file`: Defines the target `install`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`create .venv from the lock file`) is the help text that `make help` prints.

```make
up: $(STAMP) ## prepare everything a run needs (no service to start: the recorded model runs in-process)
	@echo "ready: recorded model, $$(wc -l < data/prompts.jsonl | tr -d ' ') prompts, prices read $$(sed -n 's/.*read_date": "\([^"]*\)".*/\1/p' data/prices.json)"
```

- `up: $(STAMP) ## prepare everything a run needs (no service to start: the recorded model runs in-process)`: Defines the target `up`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`prepare everything a run needs (no service to start: the recorded model runs in-process)`) is the help text that `make help` prints.
- `echo "ready: recorded model, $$(wc -l < data/prompts.jsonl | tr -d ' ') prompts, prices read $$(sed -n 's/.*read_date": "\([^"]*\)".*/\1/p' data/prices.json)"`: The leading `@` tells make not to print the command before running it. Prints one line saying everything is ready. The text between `$$(` and `)` is a shell command whose output is pasted in (make turns `$$` into a single `$` for the shell). `wc -l < data/prompts.jsonl` counts the lines of the prompts file (`<` feeds the file to the command); `tr -d ' '` deletes the spaces `wc` prints around the number. `sed -n 's/.../\1/p'` prints only the part of `data/prices.json` that matches `"read_date": "..."` and keeps what was inside the quotes: the date the price table was read.

```make
models: ## download the pinned small open-weight model for recording and live-local runs (needs ollama)
	scripts/pull_model.sh $(LOCAL_MODEL)
```

- `models: ## download the pinned small open-weight model for recording and live-local runs (needs ollama)`: Defines the target `models`. It has no prerequisites. The text after `##` (`download the pinned small open-weight model for recording and live-local runs (needs ollama)`) is the help text that `make help` prints.
- `scripts/pull_model.sh $(LOCAL_MODEL)`: Runs the shell script `scripts/pull_model.sh` with the model name as its first argument. The script downloads the model through ollama (see `bash.md`).

```make
estimate: up ## print the estimate for the whole run and stop (BUDGET_USD=0.001 shows the refusal)
	$(VENV)/bin/meter estimate
```

- `estimate: up ## print the estimate for the whole run and stop (BUDGET_USD=0.001 shows the refusal)`: Defines the target `estimate`. Its prerequisites, which make brings up to date before running the recipe: the target `up`, so everything a run needs is ready first. The text after `##` (`print the estimate for the whole run and stop (BUDGET_USD=0.001 shows the refusal)`) is the help text that `make help` prints.
- `$(VENV)/bin/meter estimate`: Runs the project's `meter` program with the word `estimate`: it prints the estimated token count and cost for the whole run and stops.

```make
# Replays the 450 recorded calls from tests/fixtures; no network, no key, same numbers every time.
run: up ## the lesson's run with the recorded model: estimate, 450 calls, report
	rm -f out/journal.csv
	MODEL_PROVIDER=recorded RECORDINGS_PATH=tests/fixtures/recordings $(VENV)/bin/meter run --budget 0.05
	$(VENV)/bin/meter report
```

- `# Replays the 450 recorded calls from tests/fixtures; no network, no key, same numbers every time.`: A comment. make ignores everything after a `#`.
- `run: up ## the lesson's run with the recorded model: estimate, 450 calls, report`: Defines the target `run`. Its prerequisites, which make brings up to date before running the recipe: the target `up`, so everything a run needs is ready first. The text after `##` (`the lesson's run with the recorded model: estimate, 450 calls, report`) is the help text that `make help` prints.
- `rm -f out/journal.csv`: Deletes the old journal so the run starts clean. `rm` removes files; `-f` means "no error if it does not exist".
- `MODEL_PROVIDER=recorded RECORDINGS_PATH=tests/fixtures/recordings $(VENV)/bin/meter run --budget 0.05`: Runs `meter run` with a 0.05 US dollar budget: the program refuses to start if its estimate is higher. The words of the form NAME=value in front of the program name set environment variables for that one command only: MODEL_PROVIDER (which model answers: `recorded` replays saved answers, `openai-compatible` calls a local server such as ollama, `anthropic` calls Claude, `scripted` is the fixed stand-in model used by the demos); RECORDINGS_PATH (the file or folder holding the recorded model answers (files under `tests/fixtures/recordings`)).
- `$(VENV)/bin/meter report`: Runs `meter report`, which reads the journal and prints the totals and the comparison with the estimate.

```make
run-resume: up ## continue an interrupted run: finished calls are skipped
	MODEL_PROVIDER=recorded RECORDINGS_PATH=tests/fixtures/recordings $(VENV)/bin/meter run --budget 0.05
```

- `run-resume: up ## continue an interrupted run: finished calls are skipped`: Defines the target `run-resume`. Its prerequisites, which make brings up to date before running the recipe: the target `up`, so everything a run needs is ready first. The text after `##` (`continue an interrupted run: finished calls are skipped`) is the help text that `make help` prints.
- `MODEL_PROVIDER=recorded RECORDINGS_PATH=tests/fixtures/recordings $(VENV)/bin/meter run --budget 0.05`: Runs `meter run` with a 0.05 US dollar budget: the program refuses to start if its estimate is higher. The words of the form NAME=value in front of the program name set environment variables for that one command only: MODEL_PROVIDER (which model answers: `recorded` replays saved answers, `openai-compatible` calls a local server such as ollama, `anthropic` calls Claude, `scripted` is the fixed stand-in model used by the demos); RECORDINGS_PATH (the file or folder holding the recorded model answers (files under `tests/fixtures/recordings`)).

```make
report: up ## print the report for out/journal.csv
	$(VENV)/bin/meter report
```

- `report: up ## print the report for out/journal.csv`: Defines the target `report`. Its prerequisites, which make brings up to date before running the recipe: the target `up`, so everything a run needs is ready first. The text after `##` (`print the report for out/journal.csv`) is the help text that `make help` prints.
- `$(VENV)/bin/meter report`: Runs `meter report`, which reads the journal and prints the totals and the comparison with the estimate.

```make
# Calls the local model for real and writes its answers into tests/fixtures (needs ollama and make models).
# A request already in the file is replayed, so an interrupted recording resumes where it stopped.
record: up ## record the 450 calls against the local model into the fixtures (resumes if interrupted)
	rm -f out/record-journal.csv
	MODEL_PROVIDER=openai-compatible MODEL_NAME=$(LOCAL_MODEL) RECORD=on RECORDINGS_PATH=$(RECORDING) \
	  JOURNAL_PATH=out/record-journal.csv $(VENV)/bin/meter run --budget 0.05
```

- `# Calls the local model for real and writes its answers into tests/fixtures (needs ollama and make models).`: A comment. make ignores everything after a `#`.
- `# A request already in the file is replayed, so an interrupted recording resumes where it stopped.`: A comment. make ignores everything after a `#`.
- `record: up ## record the 450 calls against the local model into the fixtures (resumes if interrupted)`: Defines the target `record`. Its prerequisites, which make brings up to date before running the recipe: the target `up`, so everything a run needs is ready first. The text after `##` (`record the 450 calls against the local model into the fixtures (resumes if interrupted)`) is the help text that `make help` prints.
- `rm -f out/record-journal.csv`: Deletes the journal of the previous recording run.
- `MODEL_PROVIDER=openai-compatible MODEL_NAME=$(LOCAL_MODEL) RECORD=on RECORDINGS_PATH=$(RECORDING) JOURNAL_PATH=out/record-journal.csv $(VENV)/bin/meter run --budget 0.05`: Runs the program against the real local model and records each answer (the recipe line continues on the next line because the first ends in a backslash). The words of the form NAME=value in front of the program name set environment variables for that one command only: MODEL_PROVIDER (which model answers: `recorded` replays saved answers, `openai-compatible` calls a local server such as ollama, `anthropic` calls Claude, `scripted` is the fixed stand-in model used by the demos); MODEL_NAME (the model id to ask for (for example `qwen2.5:0.5b`); each provider has a default); RECORD (`on` makes every live answer also get written into the recordings file, so the next run can replay it); RECORDINGS_PATH (the file or folder holding the recorded model answers (files under `tests/fixtures/recordings`)); JOURNAL_PATH (the CSV file where each paid call is appended).

```make
record-fresh: ## delete the recording and record all 450 calls again
	rm -f $(RECORDING)
	$(MAKE) record
```

- `record-fresh: ## delete the recording and record all 450 calls again`: Defines the target `record-fresh`. It has no prerequisites. The text after `##` (`delete the recording and record all 450 calls again`) is the help text that `make help` prints.
- `rm -f $(RECORDING)`: Deletes the recording file so every call is made again.
- `$(MAKE) record`: Runs make again, from inside make, for the target `record`. `$(MAKE)` is make's own name for itself, so any options you gave are passed on.

```make
lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/mypy
	$(VENV)/bin/lint-imports
```

- `lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter`: Defines the target `lint`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`ruff check, ruff format check, mypy, import-linter`) is the help text that `make help` prints.
- `$(VENV)/bin/ruff check .`: Runs the ruff linter on every Python file under the current folder (`.`). A linter reads code without running it and reports mistakes and style problems. Exit code 0 means no problems.
- `$(VENV)/bin/ruff format --check .`: Asks ruff's formatter whether every file is already formatted the way it would format it. `--check` means "report, do not change anything"; a file that would change makes the command fail.
- `$(VENV)/bin/mypy`: Runs the mypy type checker. It needs no arguments because `pyproject.toml` lists the folders to check (`files = ["src", "tests"]`).
- `$(VENV)/bin/lint-imports`: Runs import-linter, which reads the contracts in `pyproject.toml` and fails if any module imports something it must not.

```make
format: $(STAMP) ## apply ruff's formatting and safe fixes
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .
```

- `format: $(STAMP) ## apply ruff's formatting and safe fixes`: Defines the target `format`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`apply ruff's formatting and safe fixes`) is the help text that `make help` prints.
- `$(VENV)/bin/ruff check --fix .`: Runs the linter and lets it repair the problems that have a safe automatic fix (`--fix`).
- `$(VENV)/bin/ruff format .`: Rewrites every Python file into ruff's standard layout.

```make
# Offline and deterministic: unit tests plus the subprocess and end-to-end tests, all on the recorded model.
test: $(STAMP) ## every offline test, with coverage (domain and application must stay at 95% or more)
	$(PY) -m pytest --cov=token_meter --cov-report=term
	$(PY) -m coverage report --include='src/token_meter/domain/*,src/token_meter/application/*' --fail-under=95
```

- `# Offline and deterministic: unit tests plus the subprocess and end-to-end tests, all on the recorded model.`: A comment. make ignores everything after a `#`.
- `test: $(STAMP) ## every offline test, with coverage (domain and application must stay at 95% or more)`: Defines the target `test`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`every offline test, with coverage (domain and application must stay at 95% or more)`) is the help text that `make help` prints.
- `$(PY) -m pytest --cov=token_meter --cov-report=term`: Runs pytest as a module of the project's Python. `--cov=token_meter` turns on coverage measurement for the package `token_meter` and `--cov-report=term` prints the table in the terminal.
- `$(PY) -m coverage report --include='src/token_meter/domain/*,src/token_meter/application/*' --fail-under=95`: Prints the coverage table again, but only for the `domain` and `application` folders, and fails (non-zero exit code) if the total is under 95 percent. The quotes stop the shell from expanding the `*` itself.

```make
test-integration: $(STAMP) ## the command-line program as a subprocess, including a real kill -9 and restart
	$(PY) -m pytest tests/integration -m integration
```

- `test-integration: $(STAMP) ## the command-line program as a subprocess, including a real kill -9 and restart`: Defines the target `test-integration`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`the command-line program as a subprocess, including a real kill -9 and restart`) is the help text that `make help` prints.
- `$(PY) -m pytest tests/integration -m integration`: Runs only the tests in `tests/integration`, and only those marked `integration` (`-m` selects by marker).

```make
test-e2e: $(STAMP) ## the lesson's scenario from the prompt file to the report
	$(PY) -m pytest tests/e2e -m e2e
```

- `test-e2e: $(STAMP) ## the lesson's scenario from the prompt file to the report`: Defines the target `test-e2e`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`the lesson's scenario from the prompt file to the report`) is the help text that `make help` prints.
- `$(PY) -m pytest tests/e2e -m e2e`: Runs only the tests in `tests/e2e`, and only those marked `e2e` (`-m` selects by marker).

```make
test-live: $(STAMP) ## opt in: call a real model (needs ANTHROPIC_API_KEY, or a local ollama with make models)
	$(PY) -m pytest tests/live -m live -o addopts="-ra --strict-markers"
```

- `test-live: $(STAMP) ## opt in: call a real model (needs ANTHROPIC_API_KEY, or a local ollama with make models)`: Defines the target `test-live`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`opt in: call a real model (needs ANTHROPIC_API_KEY, or a local ollama with make models)`) is the help text that `make help` prints.
- `$(PY) -m pytest tests/live -m live -o addopts="-ra --strict-markers"`: Runs only the live tests, which call a real model. The default options exclude them (`-m 'not live'`), so `-o addopts="..."` replaces the default options for this run.

```make
audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock
```

- `audit: $(STAMP) ## check the locked dependencies for known vulnerabilities`: Defines the target `audit`. Its prerequisites, which make brings up to date before running the recipe: the stamp file, so the virtual environment is installed first. The text after `##` (`check the locked dependencies for known vulnerabilities`) is the help text that `make help` prints.
- `$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock`: Checks every locked package against a database of known security problems. `--no-deps` means "do not work out dependencies again, trust the file"; `--disable-pip` means "do not run pip in a temporary environment"; `-r FILE` names the list to check.

```make
check: lint test ## format check, lint, types, import rules and every offline test
```

- `check: lint test ## format check, lint, types, import rules and every offline test`: Defines the target `check`. Its prerequisites, which make brings up to date before running the recipe: the target `lint`; the target `test`. The text after `##` (`format check, lint, types, import rules and every offline test`) is the help text that `make help` prints.

```make
down: ## remove the run output (out/)
	rm -rf out
```

- `down: ## remove the run output (out/)`: Defines the target `down`. It has no prerequisites. The text after `##` (`remove the run output (out/)`) is the help text that `make help` prints.
- `rm -rf out`: Deletes the `out` folder and everything in it. `-r` means "including folders", `-f` means "no error if it is missing".

```make
clean: down
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .coverage
```

- `clean: down`: Defines the target `clean`. Its prerequisites, which make brings up to date before running the recipe: the target `down`.
- `rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .coverage`: Deletes the virtual environment and the cache files the tools wrote. Everything here can be built again.

## Try it yourself

1. List every target with its help text. This prints the `##` comments; nothing is run.

```bash
make help
```

What you should see (captured from this repository):

```text
audit	check the locked dependencies for known vulnerabilities
check	format check, lint, types, import rules and every offline test
down	remove the run output (out/)
estimate	print the estimate for the whole run and stop (BUDGET_USD=0.001 shows the refusal)
format	apply ruff's formatting and safe fixes
help	list the targets
install	create .venv from the lock file
lint	ruff check, ruff format check, mypy, import-linter
models	download the pinned small open-weight model for recording and live-local runs (needs ollama)
record	record the 450 calls against the local model into the fixtures (resumes if interrupted)
record-fresh	delete the recording and record all 450 calls again
report	print the report for out/journal.csv
run	the lesson's run with the recorded model: estimate, 450 calls, report
run-resume	continue an interrupted run: finished calls are skipped
test	every offline test, with coverage (domain and application must stay at 95% or more)
test-integration	the command-line program as a subprocess, including a real kill -9 and restart
test-live	opt in: call a real model (needs ANTHROPIC_API_KEY, or a local ollama with make models)
up	prepare everything a run needs (no service to start: the recorded model runs in-process)
```

2. Dry run. `-n` prints the commands make *would* run for `make check`, without running any of them. Use it whenever you are not sure what a target does.

```bash
make -n check
```

What you should see (captured from this repository):

```text
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy
.venv/bin/lint-imports
.venv/bin/python -m pytest --cov=token_meter --cov-report=term
.venv/bin/python -m coverage report --include='src/token_meter/domain/*,src/token_meter/application/*' --fail-under=95
```

3. Shows what the install rule would do. If the stamp file is already up to date make prints nothing, which proves the stamp logic works.

```bash
make -n install
```

What you should see (captured from this repository):

```text
make: Nothing to be done for `install'.
```

4. Shows which make you have. macOS ships GNU Make 3.81; the Makefile only uses features that exist in 3.81, so it works there and on newer versions.

```bash
make --version | head -1
```

What you should see (captured from this repository):

```text
GNU Make 3.81
```

## Mistakes people make

- **Spaces instead of a tab.** A recipe line indented with spaces gives `*** missing separator. Stop.` The repository's `.editorconfig` forces tabs for this file.
- **Forgetting `.PHONY`.** If someone creates a folder named `test`, `make test` would say "nothing to be done". Every action target is listed under `.PHONY`.
- **Writing `$` where `$$` is needed.** `$(wc -l < file)` is read by make as a make variable and comes out empty. Shell substitutions in recipes are written `$$(wc -l < file)`.
- **Expecting `cd` to carry over.** Each line is a fresh shell. This Makefile never uses `cd`; it passes paths instead.
- **Re-running slow setup every time.** Installing packages on every `make test` would be slow. The stamp file `.venv/.installed` makes the install run only when the lock file or `pyproject.toml` changed.
- **Hiding failures.** `-` in front of a command ignores its failure. It is used only where failure is expected and harmless, and the walkthrough above says where.

## Check yourself

1. What is the difference between `A = 1`, `A := 1` and `A ?= 1`?

   *Answer:* `=` is looked up each time it is used, `:=` is computed once when make reads the line, `?=` only sets the variable if nothing set it before.

2. Why does the Makefile write `$$(cat out/x.pid)` instead of `$(cat out/x.pid)`?

   *Answer:* make reads `$(...)` as its own syntax. `$$` becomes a single `$`, so the shell sees `$(cat out/x.pid)` and runs the command.

3. What does `touch $@` do at the end of the install rule, and why is it the last line?

   *Answer:* It creates or refreshes the stamp file, so make remembers the install finished. It is last so that a failure in an earlier line leaves no stamp and the install runs again next time.

4. What would happen if `test` were not listed under `.PHONY` and a folder named `test` existed?

   *Answer:* make would see a file called `test` with no newer prerequisites and would say "`test` is up to date" without running the recipe.

5. How can you see what `make down` would do without doing it?

   *Answer:* `make -n down` prints the commands without running them.

## Further reading

- GNU Make manual, https://www.gnu.org/software/make/manual/make.html (checked locally against GNU Make 3.81 with `make -n` and `make help`; the manual describes the newest release).

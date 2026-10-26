# make up | run | record | test | test-live | lint | down      (make help lists everything)
PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)
VENV := .venv
PY := $(VENV)/bin/python
STAMP := $(VENV)/.installed
LOCAL_MODEL ?= qwen2.5:0.5b
RECORDING := tests/fixtures/recordings/meter-qwen2.5-0.5b.jsonl

-include .env
export

.PHONY: help install up models run run-resume estimate report record record-fresh lint format typecheck test test-integration test-e2e \
        test-live audit check down clean

help: ## list the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort

$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@

install: $(STAMP) ## create .venv from the lock file

up: $(STAMP) ## prepare everything a run needs (no service to start: the recorded model runs in-process)
	@echo "ready: recorded model, $$(wc -l < data/prompts.jsonl | tr -d ' ') prompts, prices read $$(sed -n 's/.*read_date": "\([^"]*\)".*/\1/p' data/prices.json)"

models: ## download the pinned small open-weight model for recording and live-local runs (needs ollama)
	scripts/pull_model.sh $(LOCAL_MODEL)

estimate: up ## print the estimate for the whole run and stop (BUDGET_USD=0.001 shows the refusal)
	$(VENV)/bin/meter estimate

# Replays the 450 recorded calls from tests/fixtures; no network, no key, same numbers every time.
run: up ## the lesson's run with the recorded model: estimate, 450 calls, report
	rm -f out/journal.csv
	MODEL_PROVIDER=recorded RECORDINGS_PATH=tests/fixtures/recordings $(VENV)/bin/meter run --budget 0.05
	$(VENV)/bin/meter report

run-resume: up ## continue an interrupted run: finished calls are skipped
	MODEL_PROVIDER=recorded RECORDINGS_PATH=tests/fixtures/recordings $(VENV)/bin/meter run --budget 0.05

report: up ## print the report for out/journal.csv
	$(VENV)/bin/meter report

# Calls the local model for real and writes its answers into tests/fixtures (needs ollama and make models).
# A request already in the file is replayed, so an interrupted recording resumes where it stopped.
record: up ## record the 450 calls against the local model into the fixtures (resumes if interrupted)
	rm -f out/record-journal.csv
	MODEL_PROVIDER=openai-compatible MODEL_NAME=$(LOCAL_MODEL) RECORD=on RECORDINGS_PATH=$(RECORDING) \
	  JOURNAL_PATH=out/record-journal.csv $(VENV)/bin/meter run --budget 0.05

record-fresh: ## delete the recording and record all 450 calls again
	rm -f $(RECORDING)
	$(MAKE) record

lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/mypy
	$(VENV)/bin/lint-imports

format: $(STAMP) ## apply ruff's formatting and safe fixes
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .

# Offline and deterministic: unit tests plus the subprocess and end-to-end tests, all on the recorded model.
test: $(STAMP) ## every offline test, with coverage (domain and application must stay at 95% or more)
	$(PY) -m pytest --cov=token_meter --cov-report=term
	$(PY) -m coverage report --include='src/token_meter/domain/*,src/token_meter/application/*' --fail-under=95

test-integration: $(STAMP) ## the command-line program as a subprocess, including a real kill -9 and restart
	$(PY) -m pytest tests/integration -m integration

test-e2e: $(STAMP) ## the lesson's scenario from the prompt file to the report
	$(PY) -m pytest tests/e2e -m e2e

test-live: $(STAMP) ## opt in: call a real model (needs ANTHROPIC_API_KEY, or a local ollama with make models)
	$(PY) -m pytest tests/live -m live -o addopts="-ra --strict-markers"

audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock

check: lint test ## format check, lint, types, import rules and every offline test

down: ## remove the run output (out/)
	rm -rf out

clean: down
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .coverage

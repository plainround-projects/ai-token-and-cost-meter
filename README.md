# ai-token-and-cost-meter

`meter` is a small command-line tool that reads 50 support-desk prompts, estimates the tokens and cost of the whole run before the first call, calls a model at three decoding settings, and reports how far the estimate was from the bill and how much the answers vary.

| | |
| --- | --- |
| **Lesson** | `/prep/ai/project-token-and-cost-meter`, "Build a token and cost meter" (`data-structure-explainer/src/content/tracks/ai/95-project-token-and-cost-meter.md` in the Plainround app) |
| **Planned hours** | 6 |
| **Level** | Beginner |
| **Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md), decisions in [docs/adr](docs/adr) |

## Prerequisites

| Tool | Version | Used for |
| --- | --- | --- |
| Python | 3.12 or 3.13 (tested with 3.13; CI uses 3.12) | the program and the tests |
| GNU Make | 3.81 or newer (the one on macOS works) | every command below |
| Python packages | `anthropic` 2.3.0 and `httpx` 0.28.1 at run time; pytest, pytest-cov, ruff, mypy, import-linter, pip-audit for development. All pinned with hashes in `requirements.lock` and `requirements-dev.lock`; `make` installs them into `.venv/` | everything |
| ollama (optional) | any recent version, with `qwen2.5:0.5b` | only for `make record` and `make test-live`; the recorded fixtures make it unnecessary for everything else |
| Anthropic API key (optional) | none needed for any default command | only for the opt-in Claude live test |

No Docker, no cloud account, no secrets. A key is read from your shell's `ANTHROPIC_API_KEY` and nowhere else; no file in this repository holds one.

## Setup, run, test, stop

```bash
make up              # create .venv from the lock file; nothing else to start (the recorded model runs in-process)
make estimate        # print the estimate for the 450 calls and stop
make run             # estimate, 450 recorded calls into out/journal.csv, then the report
make test            # every offline test (unit, subprocess incl. kill -9, end to end) with coverage
make lint            # ruff check, ruff format check, mypy --strict, import-linter
make audit           # known-vulnerability check of the locked dependencies
make down            # remove out/
```

`make help` lists every target. `make run` replays the 450 answers stored in `tests/fixtures/recordings/`, so it needs no network and prints the same numbers every time. To run the tool against a real model instead:

```bash
make models          # ollama pull qwen2.5:0.5b (the weights stay in ollama's store, never in this repo)
make record          # call the local model for real and rewrite the fixtures (resumes if interrupted)
make test-live       # opt in: calls the local model, and Claude if ANTHROPIC_API_KEY is set; skipped by default
```

Variables are listed in `env.example` (copy it to `.env`). The ones you will touch: `MODEL_PROVIDER` (`recorded`, `openai-compatible`, `anthropic`), `BUDGET_USD`, `PRICE_MAX_AGE_DAYS`, `THROTTLE_SECONDS`.

What `make run` prints (abridged; the numbers are those of the recorded run):

```text
Estimate before calling: calls=450 input_tokens_est=48879 output_tokens_est=90000 cost_est=$0.0499
calls made now: 450; skipped, already in the journal: 0

--- 1. estimate vs billed input tokens, by kind (t0 only), chars/4 only ---
short     est=   177 billed=   735 error=-75.9%
long      est=  4707 billed=  6965 error=-32.4%
code      est=   233 billed=   409 error=-43.0%
language  est=   116 billed=   280 error=-58.6%
label     est=   198 billed=   301 error=-34.2%
total     est=  5431 billed=  8690 error=-37.5%
largest gap: p03 (short) est=6 billed=35; cause: fixed chat-template overhead per call, which dominates short prompts

measured template overhead: 29 tokens per call (median of billed - chars/4)
--- 2. same, with the measured overhead (chars/4 + 29) ---   total error=-20.8%   (long prompts: -26.2%)
--- 3. leave-one-out: each prompt estimated by an estimator fitted on the others ---   total error=-1.0%
--- cost of all 450 calls, each forecast without its own prompt's data ---
estimated=$0.033820 billed=$0.033896 error=-0.2% (within 5%); ceiling with every call at the output cap=$0.052739

setting  mean_distinct_answers  label_agreement  mean_output_tokens  length_stops  cost_per_1000_requests
t0                        1.02             1.00               104.4          30%  $               0.0696
t07                       2.92             0.80               115.1          31%  $               0.0749
t10                       2.96             0.60               128.1          36%  $               0.0814
temperature 0 did NOT give identical answers on every repeat.
```

Logs are one logfmt line per event on standard error (`ts=... level=INFO logger=... msg=... key=value`). They carry ids, sizes and token counts, never prompt or answer text at INFO level (a test asserts it). Results go to standard output.

## Done when: the lesson's checklist and the proof for each line

| # | Done when (from the lesson) | Command | What proves it |
| --- | --- | --- | --- |
| 1 | The file has 50 rows across the five kinds, at least one prompt is over 1,500 tokens, and the price file carries a date. | `make test` (`tests/e2e`, step 1); `scripts/make_prompts.py` regenerates the file | `validate_prompt_set` accepts `data/prompts.jsonl`: 20 short, 15 long, 5 code, 5 language, 5 label, unique ids, the longest prompt about 1,537 tokens by chars/4 (6,147 characters; the local tokenizer bills it at 2,417). `data/prices.json` has a real `read_date` field, and the tool refuses a table older than `PRICE_MAX_AGE_DAYS` (30). |
| 2 | The tool prints a total estimate and stops with a clear message when you pass a budget lower than that estimate. | `make estimate`; `BUDGET_USD=0.001 make estimate` or `meter run --budget 0.001` | The first prints `Estimate before calling: calls=450 ... cost_est=$0.0499`. With a lower budget the run exits with code 3 and `REFUSING TO START: estimated cost 0.0499 exceeds budget 0.001` before any call or journal row (`tests/integration/test_cli_process.py::test_the_budget_refusal_happens_before_any_row_is_written`). |
| 3 | The CSV has 450 rows (50 prompts, three settings, three repeats), each with billed input and output tokens and a stop reason. | `make run`, then `wc -l out/journal.csv` (451 lines with the header) | `tests/e2e` asserts 450 rows, three settings, every row with input tokens, output tokens and a stop reason. The tokens come from the model's usage block (`ChatResponse.usage`); no tokenizer is imported anywhere. The output cap is 200 for every setting (a unit test asserts it); only `temperature` and `top_p` differ. |
| 4 | You kill the run halfway, start it again, and the finished CSV still has exactly 450 rows with no key repeated. | `make test-integration` | `test_a_run_killed_with_sigkill_resumes_and_ends_with_exactly_450_rows_and_no_repeated_key` starts the program, sends a real `SIGKILL` after about 120 rows, restarts it, and checks 450 rows and 450 distinct `(prompt_id, setting, repeat)` keys. A second test sends `SIGTERM`: the call in flight finishes and the exit code is 4. The CSV header is written once; a torn last line is cut off on open. |
| 5 | The total estimated cost is within 5% of the cost computed from billed tokens, and the report names the cause of the largest single gap. | `make run` | Stage 1 shows chars/4 alone is 37.5% low in total and 75.9% low on the short prompts; the largest gap is `p03`, caused by the fixed chat-template overhead (29 tokens per call, the median of billed minus estimated). Stage 2 adds the overhead and is still 20.8% low, because the long prompts tokenize at 2.8 characters per token, not 4; its largest gap is `p35` (est 1,566, billed 2,417). Stage 3 fits one characters-per-token ratio per kind and forecasts each prompt leave-one-out (fitted on the other 49): input tokens -1.0%, and the cost of all 450 calls **-0.2%** against the bill. The pre-run ceiling (every call at the output cap) is 55.6% above the bill, and the report prints it next to the forecast. |
| 6 | The report has one table with, per setting, the mean distinct answers per prompt, label agreement, mean output tokens and cost per 1,000 requests; and it says plainly whether temperature 0 gave identical answers every time. | `make run` | The "spread per setting" table has all four numbers plus the share of calls that stopped on the length limit. It ends with `temperature 0 did NOT give identical answers on every repeat.`: one prompt (`p38`) gave two different answers at temperature 0 on this local server, so the mean is 1.02, not 1.00. Temperature 0.7 and 1.0 gave 2.92 and 2.96 distinct answers out of 3. |
| 7 | The billed input tokens of the Java and Python variants match for every prompt. | not built | See "Stretch goals and what is not built". |

## Stretch goals and what is not built

| Item (from the lesson) | Built? |
| --- | --- |
| The Java variant on Spring AI, run on the same prompt file and writing the same CSV columns (the lesson's "build it twice" and its step 7) | **No.** The Python tool is the whole build. The prompt file (JSON Lines) and the CSV columns are language-neutral, so a Java client can read and write them unchanged. Step 7 compares what a provider bills two clients for the same request, which needs a live provider; no model key is available to this build, and the Spring AI version the track pins is not downloaded here. |
| Prompt caching with a long shared instruction, reporting the cached share and the saving | No. The estimator would need the cached-token fields from the usage block; [ARCHITECTURE.md](ARCHITECTURE.md#how-to-extend-it) says where they go. |
| A fourth setting with a lower output cap, counting answers that stop on the length limit | Partly. The report already counts length stops per setting (30%, 31% and 36% at the 200-token cap). A fourth setting is one line in `DEFAULT_SETTINGS`. |
| The estimator as a library function that a service calls before every request, logging estimate and bill side by side | **Yes.** `application.metered_model.MeteredChatModel` wraps any `ChatModel` and logs `estimated_input`, `billed_input` and the error for every call, without the prompt text. Unit-tested. |

## What is simplified for teaching

Only what the lesson scopes out, plus where this build differs from the lesson's text:

- The model that produced the recordings is `qwen2.5:0.5b` on a local ollama server, so the billed token counts, the 29-token overhead and the densities are that model's, not Claude's. The lesson used the same family of model. Prices in `data/prices.json` are `claude-haiku-5-5` list prices ($0.10 and $0.50 per million tokens, copied on the read date), so the dollar figures answer "what would these exact token counts cost at that price". Update the file and its `read_date` before trusting a dollar figure.
- The lesson's own sample numbers (overhead 28, total error -49.6% then -1.2%) came from its prompts. This prompt set is different, so the numbers differ: overhead 29, naive error -37.5%, and chars/4 plus the overhead still leaves -20.8% because this set has long, number-heavy messages. The report shows the extra step that closes it (a density per kind, forecast leave-one-out), which is the lesson's "fix the estimator" taken one step further.
- The lesson's step 5 estimates cost with a fixed output cap. That bound is kept as the pre-run `ceiling`; the within-5% check uses the mean answer length per kind and setting from the other prompts, because the cap overstates by 55%.
- The Claude adapter cannot run the three-setting experiment. The current Messages API rejects `temperature` and `top_p` ([ADR 0002](docs/adr/0002-claude-is-not-asked-for-sampling.md)), so `meter run` with `MODEL_PROVIDER=anthropic` stops with a configuration error that says so. The adapter is verified offline against a mock transport and by an opt-in live test.
- The journal is a CSV file in `out/`, not a database.

## Project structure

```text
src/token_meter/
  domain/            prompts (kinds, rules), pricing (dated table), estimation, analysis (by kind, calibration,
                     leave-one-out, spread), llm value objects, named errors.
                     Depends on nothing outside the standard library.
  application/       the run (estimate, budget, restartable calls), the report, the MeteredChatModel decorator,
                     and the ports (ChatModel, Embedder, Clock, Journal). Depends on domain only.
  infrastructure/    adapters: recorded/recording model, OpenAI-compatible and Claude clients, retry, the CSV journal,
                     file readers, validated settings, logfmt logging, signals. Depends on application and domain.
  interfaces/        the `meter` command (estimate, run, report), exit codes, text rendering.
                     Depends on everything below; nothing depends on it.
tests/
  unit/              domain, application (with in-memory fakes), infrastructure (mock HTTP transports), CLI.
  integration/       the program as a subprocess: SIGKILL and restart, SIGTERM, budget refusal.
  e2e/               the lesson's scenario on the 450 recorded calls.
  live/              opt-in tests against a real model (make test-live).
  fixtures/recordings/   450 recorded answers of qwen2.5:0.5b (about 450 KB).
data/                prompts.jsonl (50 prompts), prices.json (dated).
scripts/             make_prompts.py (regenerates the prompt file), pull_model.sh.
docs/adr/            decision records.
pyproject.toml       project metadata and every tool's configuration.
requirements*.lock   hash-pinned dependencies (runtime, and runtime plus development tools).
Makefile             the only commands a reader needs (make help).
```

The dependency rule (domain depends on nothing; application on domain; infrastructure and interfaces on both; nothing on interfaces) is enforced by `make lint` through import-linter. A second contract forbids `domain` and `application` from importing `anthropic`, `httpx`, `httpx2` or `openai`.

## Troubleshooting

- **`RecordingMissing: no recording for request tag=...`:** a prompt, the output cap or a setting changed, so the stored answers no longer match. Run `make record` with ollama serving `qwen2.5:0.5b`.
- **`REFUSING TO START: price table was read on ... days ago`:** read the current prices, update `data/prices.json` and its `read_date`, or pass `--allow-stale-prices` for a run you accept.
- **`JournalCorrupt`:** `out/journal.csv` lost its header (for example it was deleted while a run was writing). Delete it and rerun; finished work is in the file only if the header is there.
- **Slow tests on a busy machine:** building an HTTP client loads the certificate bundle; the unit suite builds a few.

## Author and license

Written by Sumit Srivastava. Released under the MIT License, see [LICENSE](LICENSE). Changes are in [CHANGELOG.md](CHANGELOG.md).

# Technology notes for ai-token-and-cost-meter

These notes teach every technology this repository uses, from zero. Each note explains the technology in plain words, shows where this repository uses it, walks through the real files line by line, gives commands you can run (with the output captured from this repository), lists the usual mistakes, and ends with five questions.

You do not need to know any of these technologies beforehand. If a word is new, it is explained the first time it appears in the note where it matters.

## Before you start

A **terminal** is a window where you type a command and press Return; the computer runs it and prints the answer. Open the Terminal app (macOS) or any terminal program, and move to this repository's folder with `cd` followed by the folder's path. `ls` lists the files in the folder you are in.

Run `make install` once. It builds a private Python environment in a folder called `.venv`; most commands in the notes start with `.venv/bin/...` and are meant to be run from the repository's top folder after that. Commands that only need tools every computer has (`ls`, `cat`, `grep`, `sed`, `git`) run without `make install`.

Code blocks marked `bash` are commands you type. Blocks marked `text` are what the computer printed. A note's "Walkthrough" quotes real lines from this repository's files, with the file name and line numbers above each quote.

There are 33 notes.

## Read these three first (about ten minutes)

1. [python](python.md): the language: how the code is laid out and every language feature used, with real examples.
2. [make](make.md): the Makefile: every target and every line of every recipe.
3. [csv](csv.md): the CSV journal and how it survives a crash.

## Reading order

Read the language first, then the tools that build and run the project, then the pieces that run when it works, then the tests and checks. The data formats can be read whenever a file name sends you there.

### Language

| # | Note | What it covers |
| --- | --- | --- |
| 1 | [python](python.md) | the language: how the code is laid out and every language feature used, with real examples |
| 2 | [python-standard-library](python-standard-library.md) | every standard-library module the code imports and what it uses from each |
| 3 | [regular-expressions](regular-expressions.md) | every text pattern in the code and data, taken apart piece by piece |

### Build and run

| # | Note | What it covers |
| --- | --- | --- |
| 4 | [make](make.md) | the Makefile: every target and every line of every recipe |
| 5 | [bash](bash.md) | the shell script and the shell commands inside the Makefile |
| 6 | [git](git.md) | version control and the .gitignore file |
| 7 | [pip-and-venv](pip-and-venv.md) | virtual environments and how packages are installed |
| 8 | [uv](uv.md) | the tool that produced the lock files |
| 9 | [requirements-lock-files](requirements-lock-files.md) | the two lock files and every package in them |
| 10 | [setuptools](setuptools.md) | the build backend that installs the project |
| 11 | [toml](toml.md) | the TOML file format |
| 12 | [pyproject-toml](pyproject-toml.md) | every table and key of pyproject.toml |
| 13 | [environment-variables](environment-variables.md) | settings in the environment: env.example, the readers, the Makefile |
| 14 | [editorconfig](editorconfig.md) | the editor settings file |

### Runtime pieces

| # | Note | What it covers |
| --- | --- | --- |
| 15 | [processes-signals-and-threads](processes-signals-and-threads.md) | processes, signals, exit codes, threads and locks, and the tests that kill programs |
| 16 | [python-logging](python-logging.md) | structured logfmt logging |
| 17 | [curl-and-http](curl-and-http.md) | HTTP requests and answers, and the curl command |
| 18 | [httpx](httpx.md) | the HTTP client library, and how tests fake the network |
| 19 | [anthropic-sdk](anthropic-sdk.md) | the Claude SDK adapter |
| 20 | [ollama](ollama.md) | local models, the OpenAI-compatible API and embeddings |

### Data formats

| # | Note | What it covers |
| --- | --- | --- |
| 21 | [json](json.md) | the JSON files, key by key |
| 22 | [jsonl](jsonl.md) | JSON Lines files, recordings and embeddings |
| 23 | [csv](csv.md) | the CSV journal and how it survives a crash |
| 24 | [yaml](yaml.md) | the YAML file format |
| 25 | [markdown](markdown.md) | the Markdown files and what each is for |
| 26 | [mermaid](mermaid.md) | the architecture diagram, line by line |

### Tests and checks

| # | Note | What it covers |
| --- | --- | --- |
| 27 | [pytest](pytest.md) | the test runner, markers, fixtures and every test construct used |
| 28 | [coverage](coverage.md) | measuring how much code the tests run, and the 95 percent gate |
| 29 | [ruff](ruff.md) | the linter and formatter, and every rule family switched on |
| 30 | [mypy](mypy.md) | the type checker and what strict mode requires |
| 31 | [import-linter](import-linter.md) | the architecture rules that fail the build |
| 32 | [pip-audit](pip-audit.md) | the check for known vulnerabilities in the locked packages |
| 33 | [github-actions](github-actions.md) | the CI workflow, line by line |

## How each note is built

Every note has the same nine parts, in this order: what it is; why this repository uses it; where it appears; how it works underneath; a walkthrough of this repository's use; commands to try; mistakes people make; five questions with answers; further reading.

The commands under "Try it yourself" were run in this repository and the text shown is what they printed (times are replaced by `N.NNs`). A command marked as not run needs a service that was not available while the notes were written; the note says why.

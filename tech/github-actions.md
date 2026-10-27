# GitHub Actions

## What it is

**Continuous integration (CI)** means that every time someone pushes a change, a server automatically builds the project and runs the checks, then reports pass or fail. **GitHub Actions** is GitHub's CI service. You describe what to do in a **workflow file**: a YAML file under `.github/workflows/`. GitHub starts a fresh virtual machine, runs your **jobs** (each a list of **steps**), and shows a green tick or a red cross next to the commit.

## Why this repository uses it

"It works on my machine" is not evidence. CI runs the same `make` targets on a clean machine on every push, so a missing file, a forgotten lock-file update or a failing test is visible to everyone. The workflow is deliberately thin: it installs Python and calls `make`, so the rules live in one place (the Makefile) and the CI cannot drift from what you run locally.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `.github/workflows/ci.yml` | the only workflow; it has the jobs: `check`, `audit` |
| `Makefile` | the targets that the workflow calls |

## How it works underneath

GitHub watches the repository for the events named in `on:`. When one happens it reads the workflow file from that commit, schedules each job on a runner (a virtual machine from GitHub's pool; `ubuntu-latest` is a Linux image), and runs the steps in order. A step is either `uses:` (run a reusable action, which is a packaged piece of code identified as `owner/name@version`) or `run:` (run shell commands). The step's exit code decides success: zero passes, anything else fails the job. Jobs run in parallel unless one lists another under `needs:`.

The machine is created for the job and destroyed afterwards, so nothing carries over from one run to the next; every run starts with the repository checked out and nothing installed.

## Walkthrough of this repository's use

`.github/workflows/ci.yml`, the whole file, block by block. Under each block, every line is explained.

```yaml
name: ci
```

- `name: ci`: The workflow's name, shown in the Actions tab of the repository.

```yaml
on: [push, pull_request]
```

- `on: [push, pull_request]`: When to run: on every `push` (new commits arrive) and every `pull_request` (a proposed change is opened or updated). The square brackets make a YAML list of two events.

```yaml
jobs:
  check:
    name: Format, lint, types, import rules, offline tests with coverage
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: make check
```

- `jobs:`: Starts the mapping of jobs. A **job** is a group of steps that runs on one fresh machine. Jobs with no dependency between them run at the same time.
- `check:`: A job whose id is `check`. The id is how other jobs and the logs refer to it.
- `name: Format, lint, types, import rules, offline tests with coverage`: The job's display name in the GitHub page. Format, lint, types, import rules, offline tests with coverage
- `runs-on: ubuntu-latest`: Which kind of machine runs the job: GitHub's current Ubuntu Linux image, a clean virtual machine created for this job and thrown away after.
- `steps:`: Starts the list of steps. Steps run in order on the same machine; if one fails, the job stops and is marked failed.
- `- uses: actions/checkout@v4`: Runs a ready-made action: `actions/checkout` copies this repository's files onto the machine (the machine starts empty). `@v4` picks version 4 of the action.
- `- uses: actions/setup-python@v5`: Runs the action that installs Python on the machine.
- `with:`: The inputs passed to the action above (a mapping).
- `python-version: "3.12"`: Install Python 3.12, the oldest version the project supports. The quotes matter: unquoted, YAML would read `3.12` as the number 3.12 and `3.10` as 3.1.
- `- run: make check`: Runs a shell command on the machine: `make check`. `make check` runs lint (ruff, mypy, import-linter) and the offline tests with coverage.

```yaml
  audit:
    name: Dependency audit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: make audit
```

- `audit:`: A job whose id is `audit`. The id is how other jobs and the logs refer to it.
- `name: Dependency audit`: The job's display name in the GitHub page. Dependency audit
- `runs-on: ubuntu-latest`: Which kind of machine runs the job: GitHub's current Ubuntu Linux image, a clean virtual machine created for this job and thrown away after.
- `steps:`: Starts the list of steps. Steps run in order on the same machine; if one fails, the job stops and is marked failed.
- `- uses: actions/checkout@v4`: Runs a ready-made action: `actions/checkout` copies this repository's files onto the machine (the machine starts empty). `@v4` picks version 4 of the action.
- `- uses: actions/setup-python@v5`: Runs the action that installs Python on the machine.
- `with:`: The inputs passed to the action above (a mapping).
- `python-version: "3.12"`: Install Python 3.12, the oldest version the project supports. The quotes matter: unquoted, YAML would read `3.12` as the number 3.12 and `3.10` as 3.1.
- `- run: make audit`: Runs a shell command on the machine: `make audit`. `make audit` checks the locked packages for known vulnerabilities.

## Try it yourself

1. The workflow files.

```bash
ls .github/workflows
```

What you should see (captured from this repository):

```text
ci.yml
```

2. A rough count of the jobs and keys at job level.

```bash
grep -c '^  [a-z]*:$' .github/workflows/ci.yml
```

What you should see (captured from this repository):

```text
2
```

3. Parse the YAML with Ruby (shipped with macOS) and list the job ids: proof the file is valid YAML.

```bash
ruby -ryaml -e 'y = YAML.load_file(".github/workflows/ci.yml"); puts y["jobs"].keys.inspect' 2>&1 | head -2
```

What you should see (captured from this repository):

```text
["check", "audit"]
```

4. The commands the `check` job will run (as a dry run).

```bash
make -n check | head -3
```

What you should see (captured from this repository):

```text
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy
```

## Mistakes people make

- **Unquoted values that YAML reinterprets.** `python-version: 3.10` becomes the number 3.1. The file quotes `"3.12"`. A job name that contains `: ` must be quoted too, or the whole file is invalid.
- **Putting logic in the workflow.** The rules live in the Makefile so that you can run the same thing locally.
- **Pinning nothing.** `actions/checkout@v4` pins a major version. For stricter supply-chain safety one can pin a full commit hash; this project accepts the major tag.
- **Tabs in YAML.** YAML forbids tab characters for indentation. `.editorconfig` sets two spaces for `*.yml`.
- **Relying on state between runs.** Every run starts from a clean machine; install steps must run each time.

## Check yourself

1. What starts a workflow?

   *Answer:* The events listed under `on:` (here a push or a pull request).

2. What is the difference between a job and a step?

   *Answer:* A job runs on one machine and holds an ordered list of steps; steps are single actions or commands.

3. What does `uses: actions/checkout@v4` do?

   *Answer:* Copies the repository's files onto the runner.

4. Why does the workflow call `make check` instead of listing every tool?

   *Answer:* So the CI and your local run execute exactly the same commands.

5. How does GitHub decide a step failed?

   *Answer:* The command exits with a non-zero code.

## Further reading

- GitHub Actions documentation, workflow syntax, https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions (cannot be run locally; the workflow file was checked to be valid YAML with Ruby's YAML parser and its `make` commands were run locally).

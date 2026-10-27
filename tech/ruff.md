# ruff

## What it is

A **linter** reads source code *without running it* and reports mistakes and bad habits: an unused variable, an import that is not needed, a name in the wrong style. A **formatter** rewrites code into one standard layout so that nobody argues about spaces and line breaks. **ruff** does both. It is written in Rust, so it checks a whole project in a fraction of a second.

## Why this repository uses it

Style and small-bug checks should be automatic, not part of code review. With ruff in `make lint` and in CI, a missing docstring, an unsorted import or a mutable default argument fails the build before a person has to notice it. The formatter makes every file in the six sibling repositories look the same, which makes the code easier to read when you are learning from it.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `pyproject.toml` | `[tool.ruff]`, `[tool.ruff.lint]` and `per-file-ignores` |
| `Makefile` | `lint` (check and format check) and `format` (apply) |
| `.github/workflows/ci.yml` | `make check` runs lint |
| `.gitignore` | lists `.ruff_cache/` |

## How it works underneath

ruff parses each Python file into a *syntax tree* (a structured picture of the code) and runs rule checks over the tree. Each rule looks for a pattern, such as "a function definition whose default value is a list". Rules that have a mechanical repair come with a *fix*, which is what `--fix` applies. Fixes are labelled *safe* (cannot change what the program does) or *unsafe* (might); plain `--fix` applies only safe ones.

The formatter prints the syntax tree back out in a canonical layout, so the result does not depend on how you typed it. It is designed to match the widely used Black style, with a wrapping width set by `line-length`.

ruff caches results in `.ruff_cache/` so unchanged files are skipped.

## Walkthrough of this repository's use

### The two Makefile targets

`Makefile`, lines 58 to 63:

```make
lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/mypy
	$(VENV)/bin/lint-imports

```

`Makefile`, lines 64 to 66:

```make
format: $(STAMP) ## apply ruff's formatting and safe fixes
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .
```

- `ruff check .` runs the **linter** over every Python file from the current folder down. It prints each problem as `file:line:column: CODE message` and exits with 1 if it found any.
- `ruff format --check .` runs the **formatter** in checking mode. The formatter has one opinion about how Python should be laid out (line breaks, quotes, spacing, trailing commas). With `--check` it changes nothing and fails if any file would change. In CI this catches an unformatted commit.
- `ruff check --fix .` repairs the problems that have an automatic *safe* fix, such as removing an unused import or sorting imports.
- `ruff format .` rewrites the files into the standard layout.

### The settings

Explained line by line in `pyproject-toml.md`: `line-length = 120`, `target-version = "py312"`, `src = ["src", "tests"]`, the `select` list of rule families, `ignore = ["N818"]`, and `per-file-ignores` that relax docstring and line-length rules for tests and scripts.

### What each selected rule family catches

Every rule has a code (a letter prefix and a number). `select` turns on whole families by prefix. Each row names a family and one code from it that ruff really reported for the sample file in "Try it yourself" (or, where the sample does not trigger it, one that `ruff rule CODE` documents).

| Prefix | Family | Example code | What it catches |
| --- | --- | --- | --- |
| `E` | pycodestyle errors | `E501` | a line longer than the limit (120 here) |
| `F` | Pyflakes | `F401`, `F841` | an import that is never used; a local variable assigned and never used |
| `I` | isort | `I001` | imports not sorted into the standard groups and order |
| `B` | flake8-bugbear | `B006`, `B904` | a mutable default argument (`def f(x=[])`); `raise` inside `except` without `from` |
| `UP` | pyupgrade | `UP035` | old-style imports and syntax (`typing.List` instead of `list`) |
| `SIM` | flake8-simplify | `SIM102` | nested `if` statements that could be one |
| `N` | pep8-naming | `N802` | a function name that is not lowercase_with_underscores |
| `C4` | flake8-comprehensions | `C416`, `C410` | a comprehension or call that does nothing useful |
| `RUF` | ruff-specific | `RUF005` | `a + [3]` where `[*a, 3]` is clearer |
| `PT` | flake8-pytest-style | `PT018` | an `assert` with several conditions joined by `and`; use separate asserts |
| `D100`, `D101`, `D103`, `D104` | pydocstyle (four codes only) | `D103` | a public module, class, function or package with no docstring |

Ignored on purpose: `N818` (exception class names must end in `Error`), because some domain exceptions are named for the situation (for example `VersionConflict`).

Per-file: tests and scripts skip all `D` rules (no docstrings needed) and `E501` (long literal data lines are fine). In some repositories tests also skip `PT018`.

## Try it yourself

1. The installed ruff.

```bash
.venv/bin/ruff --version
```

What you should see (captured from this repository):

```text
ruff 0.17.2
```

2. Lint the whole project. `All checks passed!` is the goal.

```bash
.venv/bin/ruff check . 2>&1 | tail -2
```

What you should see (captured from this repository):

```text
All checks passed!
```

3. The formatter's check mode: how many files are already formatted.

```bash
.venv/bin/ruff format --check . 2>&1 | tail -2
```

What you should see (captured from this repository):

```text
66 files already formatted
```

4. Ask ruff what a rule means. This prints its name, why it is a problem and an example.

```bash
.venv/bin/ruff rule B006 | head -12
```

What you should see (captured from this repository):

```text
# mutable-argument-default (B006)

Derived from the **flake8-bugbear** linter.

Fix is sometimes available.

## What it does
Checks for uses of mutable objects as function argument defaults.

## Why is this bad?
Function defaults are evaluated once, when the function is defined.
```

5. Make a small file with problems in an ignored folder, lint it, and delete it. Each line is one rule from the families above.

```bash
mkdir -p out/demo && cat > out/demo/sample.py <<'EOF'
import os
from typing import List


def total(values=[]):
    result = 0
    for v in values:
        result = result + v
    unused = 3
    return result


def Bad_Name(x):
    if x:
        if x > 1:
            return [i for i in x]
    try:
        pass
    except ValueError:
        raise RuntimeError("no")
    a = list([1, 2])
    return a + [3]
EOF
.venv/bin/ruff check --no-cache --output-format concise out/demo/sample.py; rm -rf out/demo
```

What you should see (captured from this repository):

```text
out/demo/sample.py:1:1: D100 Missing docstring in public module
out/demo/sample.py:1:8: F401 [*] `os` imported but unused
out/demo/sample.py:2:1: UP035 `typing.List` is deprecated, use `list` instead
out/demo/sample.py:2:20: F401 [*] `typing.List` imported but unused
out/demo/sample.py:5:5: D103 Missing docstring in public function
out/demo/sample.py:5:18: B006 Do not use mutable data structures for argument defaults
out/demo/sample.py:9:5: F841 Local variable `unused` is assigned to but never used
out/demo/sample.py:13:5: N802 Function name `Bad_Name` should be lowercase
out/demo/sample.py:13:5: D103 Missing docstring in public function
out/demo/sample.py:14:5: SIM102 Use a single `if` statement instead of nested `if` statements
out/demo/sample.py:16:20: C416 Unnecessary list comprehension (rewrite using `list()`)
out/demo/sample.py:20:9: B904 Within an `except` clause, raise exceptions with `raise ... from err` or `raise ... from None` to distinguish them from errors in exception handling
out/demo/sample.py:21:9: C410 Unnecessary list literal passed to `list()` (remove the outer call to `list()`)
out/demo/sample.py:22:12: RUF005 Consider `[*a, 3]` instead of concatenation
Found 14 errors.
[*] 2 fixable with `--fix` (6 unsafe fixes available with `--fix --unsafe-fixes`).
```

## Mistakes people make

- **Silencing a rule with `# noqa` everywhere.** Rules are turned off only for whole file groups (tests, scripts) in `pyproject.toml`, so the exceptions are visible in one place.
- **Fighting the formatter.** Run `make format` and accept its layout; do not hand-wrap.
- **Applying unsafe fixes blindly.** Only safe fixes are applied by `make format`.
- **Selecting every rule.** `select` lists chosen families; turning on everything produces noise people learn to ignore.
- **Forgetting the second ruff command.** `ruff check` does not check formatting; `ruff format --check` does. `make lint` runs both.

## Check yourself

1. What is the difference between a linter and a formatter?

   *Answer:* A linter reports mistakes and bad habits; a formatter rewrites the layout of the code.

2. What does `ruff check --fix` change?

   *Answer:* Only problems that have a safe automatic fix, such as removing an unused import.

3. What does `select = ["E", "F"]` mean?

   *Answer:* Turn on every rule whose code starts with `E` or `F`.

4. Why does `ruff format --check .` exist when `ruff check .` does?

   *Answer:* They check different things: lint rules versus layout.

5. Which rule did the sample's `def Bad_Name(x):` trigger?

   *Answer:* `N802`, function name should be lowercase.

## Further reading

- ruff documentation, https://docs.astral.sh/ruff/ (ruff 0.17.2 is pinned in the lock file; rule codes in the table were checked with `ruff rule` and by linting the sample file).

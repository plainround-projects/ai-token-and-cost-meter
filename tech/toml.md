# TOML

## What it is

**TOML** (Tom's Obvious Minimal Language) is a plain-text format for settings. It is built from `key = value` lines, grouped under headings in square brackets called **tables**. It is made to be easy for people to read and for programs to parse into a dictionary (a collection of named values).

Values can be strings (`"text"`), integers (`120`), booleans (`true`, `false`), arrays (`[1, 2, 3]`), dates, and tables. A line that starts with `#` is a comment.

## Why this repository uses it

Python's packaging standard chose TOML for `pyproject.toml`, and nearly every tool this project uses (ruff, mypy, pytest, coverage, import-linter, setuptools) reads its settings from it. That puts the whole project's configuration in one file with one syntax.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `pyproject.toml` | the only TOML file; it holds the project metadata and every tool's settings |
| `.editorconfig` | sets two-space indentation for `*.toml` |

## How it works underneath

A TOML parser reads the file top to bottom and builds nested dictionaries. `[tool.ruff.lint]` creates `{"tool": {"ruff": {"lint": {...}}}}`. Python 3.11 and newer include the parser in the standard library as the module `tomllib`; it returns plain `dict`, `list`, `str`, `int` and `bool` objects. Tools such as pip and mypy read the file the same way.

Keys that contain characters other than letters, digits, `-` and `_` must be quoted, which is why the glob in `"tests/**" = ["D", "E501"]` is in quotes.

## Walkthrough of this repository's use

`pyproject.toml` uses every kind of TOML value. One example of each, from this file:

- A **table header** in square brackets starts a section: line 5: `[project]`. Every `key = value` line after it, up to the next header, belongs to that table.
- A **string** is text in double quotes: line 6: `name = "ai-token-and-cost-meter"`.
- A **string version number** is still a string: line 7: `version = "0.1.0"`.
- An **array** is a list in square brackets, which may span lines: line 13: `dependencies = [` followed by one quoted item per line and a closing `]`. A trailing comma after the last item is allowed.
- An **inline table** is a small table in curly braces on one line: line 11: `license = { text = "MIT" }`.
- An **integer** has no quotes: line 36: `line-length = 120`.
- A **boolean** is `true` or `false`, lowercase: line 51: `strict = true`.
- A **nested table** has a dotted header: line 45: `[tool.ruff.lint.per-file-ignores]` means the table `per-file-ignores` inside `lint` inside `ruff` inside `tool`.
- An **array of tables** has double brackets: line 54: `[[tool.mypy.overrides]]`. Each occurrence adds one more entry to a list named `tool.mypy.overrides`.
- A **comment** starts with `#` and runs to the end of the line.

Reading the file as data gives the structure that tools see. Try the first command below to see it.

## Try it yourself

1. Load the file with Python's built-in parser and print the top-level keys.

```bash
.venv/bin/python -c "import tomllib; d = tomllib.load(open('pyproject.toml', 'rb')); print(list(d))"
```

What you should see (captured from this repository):

```text
['build-system', 'project', 'tool']
```

2. Pick one value out of a table.

```bash
.venv/bin/python -c "import tomllib; d = tomllib.load(open('pyproject.toml', 'rb')); print(d['project']['name'], d['project']['version'])"
```

What you should see (captured from this repository):

```text
ai-token-and-cost-meter 0.1.0
```

3. A value from a nested table: `[tool.ruff]` becomes `d['tool']['ruff']`.

```bash
.venv/bin/python -c "import tomllib; d = tomllib.load(open('pyproject.toml', 'rb')); print(d['tool']['ruff']['line-length'])"
```

What you should see (captured from this repository):

```text
120
```

4. What a syntax error looks like: two values on one line are rejected.

```bash
.venv/bin/python -c "import tomllib; tomllib.loads('a = 1 b = 2')" 2>&1 | tail -1
```

What you should see (captured from this repository):

```text
tomllib.TOMLDecodeError: Expected newline or end of document after a statement (at line 1, column 7)
```

## Mistakes people make

- **Forgetting quotes around strings.** `name = my-project` is an error; strings need double quotes.
- **Writing a table header twice.** Defining `[project]` twice is an error; put all of a table's keys together.
- **Mixing up `[table]` and `[[array of tables]]`.** One makes a single table; the other appends to a list.
- **Using tabs for indentation inside arrays and expecting meaning.** Indentation is optional in TOML; only the brackets matter.
- **Keys with dots or glob characters unquoted.** Quote them: `"tests/**" = [...]`.

## Check yourself

1. What does `[tool.ruff.lint]` create?

   *Answer:* A table named `lint` inside `ruff` inside `tool`.

2. What is the difference between `[x]` and `[[x]]`?

   *Answer:* `[x]` is one table; `[[x]]` adds one more entry to a list of tables named `x`.

3. How do you write a boolean?

   *Answer:* `true` or `false`, lowercase and unquoted.

4. Which Python module parses TOML?

   *Answer:* `tomllib` (Python 3.11 and newer).

5. Why is `"tests/**"` quoted?

   *Answer:* It contains characters (`/`, `*`) not allowed in a bare key.

## Further reading

- TOML specification v1.0.0, https://toml.io/en/v1.0.0 and Python `tomllib`, https://docs.python.org/3/library/tomllib.html (examples above were run locally with Python 3.13).

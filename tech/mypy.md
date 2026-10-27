# mypy

## What it is

In Python you can write `price: Decimal = 3` or call a function with the wrong kind of value, and the interpreter will not complain until the line actually runs. A **type checker** reads the *type hints* in the code (`x: int`, `-> str`) and reports contradictions without running anything. **mypy** is the most widely used type checker for Python.

A **type** names a kind of value: `int`, `str`, `list[str]`, `Decimal`, or your own class. A hint is a promise; mypy checks that the whole program keeps it.

## Why this repository uses it

This repository has strict layering and ports (protocols) that adapters must satisfy. mypy checks that every adapter really has the methods its port requires, that money stays `Decimal`, and that a function that returns `X | None` is never used as if it returned `X`. With `strict = true`, hints are required everywhere, so the checker sees the whole program.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `pyproject.toml` | `[tool.mypy]` and the `[[tool.mypy.overrides]]` for tests |
| `Makefile` | `mypy` inside the `lint` target |
| `src/, tests/` | every file is checked |
| `.gitignore` | lists `.mypy_cache/` |

## How it works underneath

mypy parses each file, builds a symbol table of every name and its declared type, then walks each function body and checks that every expression's type fits where it is used. For a call it compares the argument types with the parameter types; for a return it compares with the declared return type. When two types are not the same it asks whether one is a *subtype* of the other (a `bool` is a kind of `int`; any class with the methods a `Protocol` lists is a subtype of that protocol).

It does not run the program, so it cannot know values, only types. It saves results in `.mypy_cache/`, which makes the second run much faster. It also reads third-party packages' type information (the `py.typed` marker and bundled stubs).

## Walkthrough of this repository's use

### The settings

`pyproject.toml`, lines 48 to 52:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
files = ["src", "tests"]

```

Each line is explained in `pyproject-toml.md`. The key idea: `strict = true` is a bundle. mypy itself lists what the bundle contains (read from `mypy --help` of the pinned version, 2.4.0 at the time of writing):

| Flag | What it requires |
| --- | --- |
| `--disallow-any-generics` | a generic type such as `list` must say what it holds (`list[str]`) |
| `--disallow-subclassing-any` | do not inherit from a class whose type is unknown |
| `--disallow-untyped-calls` | do not call a function that has no type hints from one that does |
| `--disallow-untyped-defs` | every function must have type hints on all parameters and its return |
| `--disallow-incomplete-defs` | a function may not annotate only some of its parameters |
| `--check-untyped-defs` | check the body of a function even if it has no hints |
| `--disallow-untyped-decorators` | a decorator must have type hints so it does not erase the types of what it wraps |
| `--warn-redundant-casts` | report a `cast` that changes nothing |
| `--warn-unused-ignores` | report a `# type: ignore` comment that is no longer needed |
| `--warn-return-any` | report a function that is declared to return a precise type but returns a value of unknown type |
| `--no-implicit-reexport` | a name imported into a module is not public unless re-exported explicitly |
| `--strict-equality` | report comparing values of types that can never be equal |
| `--extra-checks` | a few additional, stricter checks |

### The override for tests

`pyproject.toml`, lines 53 to 58:

```toml
[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false
disallow_incomplete_defs = false
disallow_untyped_calls = false

```

`[[tool.mypy.overrides]]` is an array-of-tables entry (see `toml.md`): settings that apply only to the modules matching `module`. Tests may omit hints on their small helper functions.

### The Makefile line

`$(VENV)/bin/mypy` inside the `lint` target. With no file arguments mypy uses `files = ["src", "tests"]`. It prints `Success: no issues found in N source files` and returns 0, or lists errors as `file:line: error: message  [code]` and returns 1.

### A sample type error

The "Try it yourself" section writes `x: int = "a"` into a throwaway file; mypy reports `Incompatible types in assignment (expression has type "str", variable has type "int")  [assignment]`. That is the sort of mistake it catches before the program runs.

## Try it yourself

1. The installed mypy.

```bash
.venv/bin/mypy --version
```

What you should see (captured from this repository):

```text
mypy 2.4.0 (compiled: yes)
```

2. Check the whole project with the settings from `pyproject.toml`.

```bash
.venv/bin/mypy 2>&1 | tail -2
```

What you should see (captured from this repository):

```text
Success: no issues found in 58 source files
```

3. Make a one-line file with a type mistake. mypy reports the contradiction without running the file.

```bash
mkdir -p out && printf 'x: int = "a"\n' > out/demo.py && .venv/bin/mypy out/demo.py 2>&1 | tail -2; rm -f out/demo.py
```

What you should see (captured from this repository):

```text
out/demo.py:1: error: Incompatible types in assignment (expression has type "str", variable has type "int")  [assignment]
Found 1 error in 1 file (checked 1 source file)
```

4. mypy's own description of strict mode.

```bash
.venv/bin/mypy --help | grep -A1 -E '^  --strict ' | head -3
```

What you should see (captured from this repository):

```text
  --strict                  Strict mode; enables the following flags:
                            --disallow-any-generics, --disallow-subclassing-
```

## Mistakes people make

- **Believing hints are enforced at run time.** They are not; only mypy checks them.
- **Using `Any` to make errors go away.** `Any` switches checking off for that value. `strict` complains about implicit `Any`.
- **Adding `# type: ignore` freely.** `warn_unused_ignores` (part of strict) reports an ignore that is no longer needed.
- **Checking only `src`.** Tests are checked too, with a relaxed override, so the test helpers stay consistent with the code.
- **Skipping the cache.** Deleting `.mypy_cache/` just makes the next run slower.

## Check yourself

1. What does mypy do that the Python interpreter does not?

   *Answer:* It checks type hints against each other without running the program.

2. What is `strict = true`?

   *Answer:* A bundle of flags that requires hints everywhere and forbids silent `Any`.

3. Why does a test module get an override?

   *Answer:* Small test helpers do not need full hints; the override relaxes three flags for `tests.*`.

4. What is a subtype of a `Protocol`?

   *Answer:* Any class that has the methods and attributes the protocol lists.

5. Does a passing mypy run prove the program is correct?

   *Answer:* No. It proves the types are consistent, not that the values are right.

## Further reading

- mypy documentation, https://mypy.readthedocs.io/en/stable/ (mypy 2.4.0 is pinned in the lock file; the strict flag list above was read from its `--help`).

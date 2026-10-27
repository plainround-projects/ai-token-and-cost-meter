# setuptools (the build backend)

## What it is

To install a Python project, pip must turn the source folder into an installable form. The program that does this is the **build backend**. **setuptools** is the oldest and most common one. A **build frontend** (here, pip) reads `pyproject.toml`, installs the backend, and asks it to build. The two talk through a fixed set of function names, so a frontend does not need to know how any specific backend works.

## Why this repository uses it

Every project that can be installed needs a backend. setuptools is available everywhere, handles the `src/` layout with one line, and reads all the project's metadata from `pyproject.toml`, so there is no separate `setup.py` file.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `pyproject.toml` | `[build-system]` and `[tool.setuptools.packages.find]` |
| `Makefile` | `pip install -e .` triggers the build |
| `.gitignore` | `*.egg-info/`, `build/` and `dist/` hold what the build creates |

## How it works underneath

`pip install -e .` runs these steps: read `[build-system]`; create a temporary *isolated* environment; install the packages in `requires` into it (from the network, using whatever version satisfies the range); call `setuptools.build_meta.build_editable` in that environment; take the editable wheel it returns; install it into the real environment. Because the build environment is isolated, the build cannot depend on whatever happens to be installed in `.venv`.

Note what the lock file does **not** cover: `requires = ["setuptools>=75"]` is a range and is resolved at install time, so the build tool itself is not pinned or hash-checked. The packages that run in your program are. This repository accepts that for the build step because the output of the build is only an editable link to `src/`.

## Walkthrough of this repository's use

Two tables of `pyproject.toml` talk to setuptools.

`pyproject.toml`, lines 1 to 3:

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"
```

- `[build-system]` is the table every Python build tool reads first; it says how to build this project.
- `requires = ["setuptools>=75"]`: before building, pip creates a temporary environment and installs these packages into it. `>=75` means version 75 or newer.
- `build-backend = "setuptools.build_meta"`: the module and object pip calls to do the build. `setuptools.build_meta` is setuptools' standard entry point.

`pyproject.toml`, lines 32 to 33:

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

- `[tool.setuptools.packages.find]` configures how setuptools finds the Python packages to include.
- `where = ["src"]` means "look inside the folder `src`". The code lives in `src/token_meter/`, so the importable package is `token_meter`. This arrangement is called the *src layout*.

What setuptools does when `pip install -e .` runs: it reads `[project]` (name, version, dependencies, `[project.scripts]`), finds the package `token_meter` under `src`, and returns to pip an *editable wheel* that points back at `src/`. It also creates the folder `src/*.egg-info` (listed in `.gitignore`), where it keeps the project's metadata while it works.

## Try it yourself

1. The three lines that name the backend.

```bash
grep -A2 '^\[build-system\]' pyproject.toml
```

What you should see (captured from this repository):

```text
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"
```

2. The `src` folder holds the package; `where = ["src"]` points at it.

```bash
ls src
```

What you should see (captured from this repository):

```text
ai_token_and_cost_meter.egg-info
token_meter
```

3. pip's record of the editable install: name, version, location and the files it created.

```bash
.venv/bin/pip show -f ai-token-and-cost-meter | sed -n 1,14p
```

What you should see (captured from this repository):

```text
Name: ai-token-and-cost-meter
Version: 0.1.0
Summary: meter: estimate the tokens and cost of a batch of model calls before sending it, then check the estimate against the bill.
Home-page: 
Author: Sumit Srivastava
Author-email: 
License: MIT
Location: .venv/lib/python3.13/site-packages
Editable project location: .
Requires: anthropic, httpx
Required-by: 
Files:
  ../../../bin/meter
  __editable__.ai_token_and_cost_meter-0.1.0.pth
```

4. The metadata folder setuptools created (ignored by git).

```bash
ls src/*.egg-info
```

What you should see (captured from this repository):

```text
PKG-INFO
SOURCES.txt
dependency_links.txt
entry_points.txt
requires.txt
top_level.txt
```

## Mistakes people make

- **Putting code outside `src` and forgetting `where`.** setuptools would not find the package and `import` would fail after install.
- **Expecting `build_meta` to be locked.** It is not; see the note above.
- **Committing `*.egg-info`.** It is generated; it is in `.gitignore`.
- **Mixing `setup.py` and `pyproject.toml`.** This repository has only `pyproject.toml`, so there is one place to look.

## Check yourself

1. What is a build backend?

   *Answer:* The program that turns a source folder into an installable package.

2. Where does pip learn which backend to use?

   *Answer:* From `[build-system]` in `pyproject.toml`.

3. What does `where = ["src"]` do?

   *Answer:* Tells setuptools to look for packages inside `src`.

4. Is setuptools pinned by the lock file?

   *Answer:* No; it is resolved from the range `>=75` in an isolated build environment.

5. What does an editable wheel contain?

   *Answer:* No code, only a pointer to the project's `src` folder.

## Further reading

- setuptools documentation on `pyproject.toml` configuration, https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html and PEP 517/660 (checked locally by reading `pip show -f` for the editable install).

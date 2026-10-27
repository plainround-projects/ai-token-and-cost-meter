# pip, venv and Python packages

## What it is

A **package** is a bundle of Python code (plus a name, a version and a list of the other packages it needs) that other people can install. **PyPI**, the Python Package Index, is the public website that stores them. **pip** is the program that downloads a package from PyPI and installs it. Version numbers such as `0.28.1` identify one exact release.

A **virtual environment** (venv) is a private folder that holds its own copy of the Python program and its own set of installed packages. Without one, `pip install` puts packages into the single Python of your computer, where two projects that need different versions of the same package would break each other. With one, each project has its own shelf.

A **wheel** is the file format pip prefers: a zip file (extension `.whl`) that already contains the finished code of a package, so installing is just unpacking. The **interpreter** is the program named `python` that reads and runs Python code.

## Why this repository uses it

The repository must run the same on your laptop, on a teammate's, and on the CI machine. Three decisions make that true. First, a private `.venv` per project, so nothing depends on what else is installed. Second, every package pinned to an exact version with its hash, so tomorrow's release of some library cannot change today's result and a poisoned download is detected. Third, the project itself installed in editable mode, so the code you read in `src/` is the code that runs.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Makefile` | the stamp rule creates `.venv` and runs the two `pip install` commands; every other target calls programs inside `.venv/bin` |
| `requirements.lock, requirements-dev.lock` | the exact package lists that `pip install -r` reads |
| `pyproject.toml` | `requires-python`, the dependencies, and the `[project.scripts]` commands that pip installs |
| `.gitignore` | keeps `.venv/` out of git |
| `.github/workflows/ci.yml` | installs Python 3.12 on the CI machine before `make` builds the same `.venv` |

## How it works underneath

**What `python -m venv` makes.** The folder has a file `pyvenv.cfg` that says which real Python it was made from. `.venv/bin/python` is a link to that Python. When Python starts, it looks for `pyvenv.cfg` in the folder of the program it was started as, or in the folder above it; if found, it knows it is inside a virtual environment and adds `.venv/lib/pythonX.Y/site-packages` to the list of places it searches for modules (`sys.path`). That is the whole trick: nothing is "activated" inside Python. The `activate` scripts only change your shell's search path so that typing `python` finds `.venv/bin/python`. This repository never needs them because every command uses `.venv/bin/...` explicitly.

**What `pip install` does.** pip reads each requirement (a name and a version rule), asks PyPI for a matching file, downloads it (a wheel, or a source archive that it must build first), checks its hash in hash-checking mode, unpacks it into `site-packages`, and writes a small `.dist-info` folder that records what was installed. The `.dist-info/METADATA` file holds the package's name, version, summary and requirements.

**What an editable install is.** pip builds a tiny wheel containing no code, only a marker that points at the project's `src/` folder. Importing `token_meter` then finds the code in your working copy.

**Console scripts.** For each entry in `[project.scripts]`, pip writes a small program into `.venv/bin` (for example `.venv/bin/meter`). It starts Python, imports the named module and calls the named function.

## Walkthrough of this repository's use

The whole install is one rule in the `Makefile`:

`Makefile`, lines 18 to 22:

```make
$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@
```

**Line 1 of the recipe: `$(PYTHON) -m venv $(VENV)`.**

- `$(PYTHON)` is the first of `python3.13`, `python3.12`, `python3` that exists on your computer.
- `-m venv` runs Python's built-in `venv` module. It creates the folder `.venv` and puts in it: a `bin/` folder with a `python` program (a link to the real one), a `pip` program, scripts to "activate" the environment, a `lib/pythonX.Y/site-packages/` folder (the place packages are installed) and a small settings file `pyvenv.cfg`.
- If `.venv` already exists the command leaves existing packages alone.

**Line 2: `$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock`.**

- `.venv/bin/pip` is the pip that belongs to this environment. Calling it by its path means the packages land in `.venv`, so there is no need to "activate" anything.
- `install` is the pip sub-command that downloads and installs.
- `-q` (quiet) hides the progress text.
- `-r requirements-dev.lock` reads the package list from a file. The file lists every package, including packages that packages need, each with an exact version and the hashes of its files (see `requirements-lock-files.md`).
- `--require-hashes` turns on hash-checking mode. In this mode pip refuses to install anything unless **every** line has an exact `==` version and at least one `--hash`. For each file it downloads, pip computes the SHA-256 hash and compares it with the list. A changed or tampered file is rejected.

**Line 3: `$(VENV)/bin/pip install -q --no-deps -e .`.**

- `.` is "the project in the current folder", described in `pyproject.toml`.
- `-e` (editable) installs the project by *linking* to `src/` instead of copying: Python imports the code in the folder you edit, so a change takes effect without reinstalling. This also registers the command-line program(s) listed under `[project.scripts]`.
- `--no-deps` tells pip not to look at the project's `dependencies` again. Lines 2 already installed exact, hash-checked versions of all of them; resolving again could pick a different version.

**Line 4: `touch $@`** records that all this finished. See `make.md`.

The CI file does not use `.venv` directly. `actions/setup-python@v5` installs Python 3.12 on the CI machine, and then `make check` runs the same install rule.

## Try it yourself

1. The Python inside the environment.

```bash
.venv/bin/python --version
```

What you should see (captured from this repository):

```text
Python 3.13.12
```

2. The settings file venv wrote. `home` is the real Python it was made from.

```bash
cat .venv/pyvenv.cfg
```

What you should see (captured from this repository):

```text
home = /opt/homebrew/opt/python@3.13/bin
include-system-site-packages = false
version = 3.13.12
executable = /opt/homebrew/Cellar/python@3.13/3.13.12_1/Frameworks/Python.framework/Versions/3.13/bin/python3.13
command = /opt/homebrew/opt/python@3.13/bin/python3.13 -m venv .venv
```

3. pip tells you which environment it will install into.

```bash
.venv/bin/pip --version
```

What you should see (captured from this repository):

```text
pip 26.2.2 from .venv/lib/python3.13/site-packages/pip (python 3.13)
```

4. The first packages installed in this environment.

```bash
.venv/bin/pip list 2>/dev/null | sed -n 1,8p
```

What you should see (captured from this repository):

```text
Package                 Version    Editable project location
----------------------- ---------- -----------------------------------------------------------------------
ai-token-and-cost-meter 0.1.0      .
annotated-types         0.8.0
anthropic               2.3.0
anyio                   4.15.1
ast_serialize           0.13.1
boolean.py              5.0
```

5. Where Python finds this project's code. The path points into `src/`, which proves the install is editable.

```bash
.venv/bin/python -c "import token_meter; print(token_meter.__file__)"
```

What you should see (captured from this repository):

```text
src/token_meter/__init__.py
```

## Mistakes people make

- **Installing into the system Python.** Commands like `pip install x` outside a venv can break other projects. This repository always calls `.venv/bin/pip`.
- **Using a version range where a pin is needed.** `httpx>=0.28` today and `httpx>=0.28` next month may install different code. The lock file names exact versions.
- **Skipping `--require-hashes`.** Without it, pip trusts whatever the index serves. With it, a changed file is rejected.
- **Re-resolving dependencies for the project itself.** Without `--no-deps`, pip could move a package away from the locked version. The Makefile passes `--no-deps`.
- **Committing `.venv`.** It is large and tied to one computer. It is in `.gitignore`.
- **Assuming the build tool is locked too.** Installing the project (`-e .`) makes pip fetch the build backend named in `pyproject.toml` into a temporary isolated environment (see `setuptools.md`). That one piece is not covered by the lock file.

## Check yourself

1. Why is `.venv/bin/pip` used instead of plain `pip`?

   *Answer:* Because the path chooses the environment, so packages go into `.venv` and not into the system Python.

2. What does `--require-hashes` guarantee?

   *Answer:* Every installed file matches a SHA-256 hash in the lock file, and every package is pinned to an exact version.

3. What does `-e` change?

   *Answer:* The project is linked, not copied, so edits in `src/` take effect at once.

4. What is in `site-packages`?

   *Answer:* The installed packages (and their `.dist-info` folders) of this environment.

5. Why does `--no-deps` appear on the second install?

   *Answer:* The first install already placed every dependency at its locked version; the second must not change them.

## Further reading

- Python `venv` module, https://docs.python.org/3/library/venv.html; pip user guide, https://pip.pypa.io/en/stable/user_guide/ (the flags above were checked locally against pip 26.2.2 and Python 3.13 with `pip --version` and `pip list`).

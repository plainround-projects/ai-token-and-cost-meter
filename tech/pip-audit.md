# pip-audit

## What it is

Public databases list software versions that have **known vulnerabilities**: security weaknesses someone found, reported and assigned an identifier (a CVE number or similar). **pip-audit** takes a list of Python packages with exact versions, looks each one up in such a database, and tells you if any version you use is on the list.

## Why this repository uses it

A project that pins every dependency (see `requirements-lock-files.md`) does not get silent updates, which means it also does not get silent security fixes. The audit closes that gap: it tells you when a pinned version has become known to be unsafe, so you can compile the lock file again with a fixed version.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Makefile` | the `audit` target |
| `.github/workflows/ci.yml` | the separate `audit` job runs `make audit` |
| `requirements-dev.lock` | the list of packages and versions that it checks |

## How it works underneath

pip-audit sends the package name and version to a vulnerability service and compares the answer with its list of advisories. It needs a network connection for that. It does not look at your own code, only at which versions of other people's code you use. A clean result means "no advisory is *known* for these versions today"; it says nothing about unknown problems.

## Walkthrough of this repository's use

### The Makefile target

`Makefile`, lines 82 to 83:

```make
audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock
```

- `$(VENV)/bin/pip-audit`: the program, from the virtual environment.
- `-r requirements-dev.lock`: read the packages to check from this file instead of from the installed environment. Each line `name==version` is one package at one version.
- `--no-deps`: do not work out dependencies. The lock file already contains all of them, pinned, so the extra step is not needed.
- `--disable-pip`: do not start pip in a temporary environment. With `--no-deps` this is safe, and it makes the check faster and avoids installing anything.

For every package and version pair, pip-audit asks a vulnerability database for known security advisories and prints a table if it finds any. Otherwise it prints `No known vulnerabilities found` and exits 0. Any finding makes it exit 1, so `make audit` fails.

### Two warning lines

`pip-audit` prints two warnings when `--no-deps` is used: it supports the option but "encourages" hashed pins, and it suggests `pip-compile`. The file is already fully pinned with hashes (see `requirements-lock-files.md`), so the warnings are informational here.

### In CI

The workflow has a separate job named `audit` that only runs `make audit`. It is separate from the `check` job so a new vulnerability published tomorrow shows up as its own red job and does not hide whether the code itself is healthy.

## Try it yourself

1. The installed pip-audit.

```bash
.venv/bin/pip-audit --version
```

What you should see (captured from this repository):

```text
pip-audit 2.10.1
```

2. The audit itself. It needs the network. Today's answer will be the one you see here unless a new advisory was published.

```bash
.venv/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock 2>&1 | tail -3
```

What you should see (captured from this repository):

```text
WARNING:pip_audit._cli:--no-deps is supported, but users are encouraged to fully hash their pinned dependencies
WARNING:pip_audit._cli:Consider using a tool like `pip-compile`: https://pip-tools.readthedocs.io/en/latest/#using-hashes
No known vulnerabilities found
```

3. The usage line and the first options.

```bash
.venv/bin/pip-audit --help | sed -n '1,6p'
```

What you should see (captured from this repository):

```text
usage: pip-audit [-h] [-V] [-l] [-r REQUIREMENT] [--locked] [-f FORMAT]
                 [-s SERVICE] [--osv-url OSV_URL] [-d] [-S]
                 [--desc [{on,off,auto}]] [--aliases [{on,off,auto}]]
                 [--cache-dir CACHE_DIR] [--progress-spinner {on,off}]
                 [--timeout TIMEOUT] [--path PATH] [-v] [--fix]
                 [--require-hashes] [--index-url INDEX_URL]
```

## Mistakes people make

- **Treating a clean audit as proof of safety.** It only reports advisories that are already public.
- **Auditing only direct dependencies.** Most vulnerable packages are indirect. The lock lists all of them, and the audit reads the lock.
- **Running the audit only when you remember.** CI runs it as its own job on every push.
- **Fixing by editing the lock by hand.** The hashes would no longer match. Raise the version in `pyproject.toml` or compile again.

## Check yourself

1. What does pip-audit compare?

   *Answer:* Each pinned package and version against a database of known vulnerabilities.

2. Why does `make audit` pass `--no-deps`?

   *Answer:* The lock file already lists every dependency, so pip-audit need not resolve them again.

3. Does it need a network?

   *Answer:* Yes, to look up advisories.

4. What does exit code 1 mean here?

   *Answer:* At least one known vulnerability was found.

5. Why is the audit a separate CI job?

   *Answer:* So a new advisory is visible on its own, apart from whether the tests pass.

## Further reading

- pip-audit on PyPI and GitHub, https://pypi.org/project/pip-audit/ (pip-audit 2.10.1 is pinned in the lock file; the output above was captured by running it).

# Git and the .gitignore file

## What it is

**Git** is a version-control tool: it remembers every saved state of a project. A **repository** (repo) is a project folder plus a hidden folder named `.git` where git keeps that history. A **commit** is one saved state: the full contents of every tracked file at that moment, a message that says why, the author, the time, and a pointer to the previous commit. Commits form a chain, so you can see what changed, when, and go back.

Git does not save files by name. It computes a **hash** for each piece of content: a long string of letters and digits (SHA-1 or SHA-256) produced from the content itself. Two files with the same content get the same hash; one changed letter gives a completely different hash. A commit stores the hash of the folder tree it captured and the hash of its parent commit, so any change to history changes every later hash.

A **`.gitignore`** file lists patterns for files git must not track, such as caches and secrets.

## Why this repository uses it

This repository is delivered as a git history: each commit is a step of the build, and `git log` shows how the code grew. The `.gitignore` keeps out everything that is big, rebuildable or private: the virtual environment, caches, the `out/` folder and the `.env` file that may hold a key. Because `.venv/`, model files and run output are never committed, a fresh `git clone` followed by `make up` rebuilds the same project on any computer.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `.gitignore` | the list of patterns git must not track |
| `.github/workflows/ci.yml` | `actions/checkout@v4` makes the CI machine clone this repository |
| `env.example` | is committed because it holds no secret; `.env`, its filled-in copy, is ignored |
| `.git/` | the history itself (not a file you edit) |

## How it works underneath

**Three places.** Git works with your *working folder* (the files you edit), the *index* or *staging area* (the exact set of changes you chose for the next commit; `git add` fills it), and the *history* (committed snapshots). `git commit` takes what is staged and records it.

**Objects.** Inside `.git` git stores four kinds of object, each named by its hash: a *blob* (the bytes of a file), a *tree* (a folder: a list of names pointing at blobs and other trees), a *commit* (a pointer to a tree plus a parent commit, author and message) and a *tag*. A *branch* is just a movable name pointing at one commit.

**Ignore rules.** Git reads `.gitignore` from top to bottom. A pattern ending in `/` matches only folders. `*` matches any run of characters except `/`. A pattern with no slash matches at any depth. A line starting with `#` is a comment. Ignoring only affects files that are not yet tracked: a file already committed stays tracked even if you add it to `.gitignore` later.

## Walkthrough of this repository's use

`.gitignore`, the whole file, block by block. Under each block, every line is explained.

```gitignore
.venv/
__pycache__/
*.pyc
*.egg-info/
build/
dist/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
.env
.DS_Store
logs/
out/
.omc/
```

- `.venv/`: Ignore the folder `.venv`. The trailing slash means "only match a folder". It is the virtual environment: large, specific to your computer, and rebuilt by `make install`.
- `__pycache__/`: Ignore the `__pycache__` folders Python creates to store compiled copies of modules.
- `*.pyc`: Ignore every file ending in `.pyc` (compiled Python). `*` matches any run of characters.
- `*.egg-info/`: Ignore the `*.egg-info` folder that installing the project in editable mode creates.
- `build/`: Ignore the `build` folder made by packaging tools.
- `dist/`: Ignore the `dist` folder made by packaging tools.
- `.pytest_cache/`: Ignore pytest's cache folder.
- `.mypy_cache/`: Ignore mypy's cache folder.
- `.ruff_cache/`: Ignore ruff's cache folder.
- `.coverage`: Ignore the `.coverage` data file that coverage measurement writes.
- `.env`: Ignore `.env`. This is the file where you put your own settings; it could hold a secret, so it must never be committed.
- `.DS_Store`: Ignore the hidden `.DS_Store` files that the macOS Finder creates.
- `logs/`: Ignore a `logs` folder.
- `out/`: Ignore the `out` folder where a run writes its output (journals, databases, logs). It can always be rebuilt.
- `.omc/`: Ignore the `.omc` folder, a working folder of an editor tool.

## Try it yourself

1. Show the git version.

```bash
git --version
```

What you should see (captured from this repository):

```text
git version 2.50.1 (Apple Git-155)
```

2. The five most recent commits, one per line: a short hash, then the message.

```bash
git log --oneline | head -5
```

What you should see (captured from this repository):

```text
c922cd0 chore: remove .dockerignore (this repository has no Dockerfile)
6d05e12 docs: verification notes (load during timing, Docker status)
4541995 docs: add README, ARCHITECTURE, decision records and CHANGELOG
6af7fa8 ci: run lint, types, import rules, offline tests and the dependency audit
010022c test: add unit, subprocess (SIGKILL restart), end-to-end and opt-in live tests
```

3. How many files have uncommitted changes. `0` means a clean working tree.

```bash
git status --short | wc -l
```

What you should see (captured from this repository):

```text
       0
```

4. Ask git why a path is ignored: it prints the file, line number and pattern that matched.

```bash
git check-ignore -v .venv out
```

What you should see (captured from this repository):

```text
.gitignore:1:.venv/	.venv
.gitignore:14:out/	out
```

5. The first eight files git tracks. Notice that `.venv` is not among them.

```bash
git ls-files | head -8
```

What you should see (captured from this repository):

```text
.editorconfig
.github/workflows/ci.yml
.gitignore
ARCHITECTURE.md
CHANGELOG.md
LICENSE
Makefile
README.md
```

## Mistakes people make

- **Committing a secret.** Once a key is in history it is hard to remove. `.env` is ignored, and `env.example` documents every setting with no real value.
- **Adding a pattern after the file was committed.** The file stays tracked. You must run `git rm --cached FILE` to stop tracking it.
- **Committing generated files.** They make diffs noisy and go stale. `out/`, `.venv/` and the caches are ignored.
- **Committing large model files.** Weights live in ollama's own store, never in this repository.
- **Using `git add .` blindly.** It stages everything not ignored. Check `git status` first. The ignore file is what makes `git add .` safe here.

## Check yourself

1. What is a commit?

   *Answer:* A saved snapshot of all tracked files, with a message, an author, a time and a pointer to the previous commit.

2. Why is `.env` ignored but `env.example` committed?

   *Answer:* `.env` is your private copy and may hold keys; `env.example` is the documented template with no secrets.

3. What does a trailing slash in `out/` mean?

   *Answer:* The pattern matches only folders named `out`.

4. Does adding a name to `.gitignore` untrack a file that is already committed?

   *Answer:* No. Run `git rm --cached` to untrack it.

5. What does `git check-ignore -v PATH` show?

   *Answer:* The ignore rule (file, line and pattern) that matched PATH.

## Further reading

- Pro Git book, https://git-scm.com/book/en/v2 and the gitignore manual, https://git-scm.com/docs/gitignore (checked locally against git 2.50 with `git check-ignore -v`).

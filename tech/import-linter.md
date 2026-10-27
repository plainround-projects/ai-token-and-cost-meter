# import-linter

## What it is

An **import** is how one Python file uses code from another. The set of all imports in a project is its **dependency graph**: an arrow from each file to the files it imports. **import-linter** checks that graph against rules you write, called **contracts**, and fails if a rule is broken.

## Why this repository uses it

Good structure decays quietly: one convenient import of an HTTP client into the pricing code, and the core now depends on the network. The repository's design relies on a core (`domain`, `application`) that never touches vendors, databases or web frameworks, which is why it can be tested without any of them. import-linter turns that design rule into a failing build, so it survives the next contributor.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `pyproject.toml` | `[tool.importlinter]` and the two `[[tool.importlinter.contracts]]` entries |
| `Makefile` | `lint-imports` in the `lint` target |
| `src/token_meter/` | the four layers it analyzes |
| `.import_linter_cache/` | its cache (ignored by git) |

## How it works underneath

import-linter uses a library called `grimp` to build the import graph. It parses each module's syntax tree and records `import x` and `from x import y` statements, including those inside functions. For a `layers` contract it checks that no path of imports leads from a lower layer up to a higher one. For a `forbidden` contract it searches for any chain of imports from a source module to a forbidden one, so indirect violations are found too.

Because it works on the text of the imports, it needs no running code and is fast. Cached graphs are reused when no file changed.

## Walkthrough of this repository's use

### The configuration

`pyproject.toml`, lines 77 to 80:

```toml
[tool.importlinter]
root_package = "token_meter"
include_external_packages = true

```

`pyproject.toml`, lines 81 to 85:

```toml
[[tool.importlinter.contracts]]
name = "Layers: interfaces on infrastructure on application on domain"
type = "layers"
layers = ["token_meter.interfaces", "token_meter.infrastructure", "token_meter.application", "token_meter.domain"]

```

`pyproject.toml`, lines 86 to 90:

```toml
[[tool.importlinter.contracts]]
name = "Domain and application never import a vendor SDK or an HTTP client"
type = "forbidden"
source_modules = ["token_meter.domain", "token_meter.application"]
forbidden_modules = ["anthropic", "httpx", "httpx2", "openai"]
```

- `root_package = "token_meter"`: the package to analyze. import-linter reads every file in it, finds every `import` statement, and builds a graph with an arrow from the importing module to the imported one.
- `include_external_packages = true`: also put packages outside the project (`httpx`, `anthropic`, ...) into the graph. The second contract needs this to forbid them.
- **Contract 1, type `layers`.** The list is ordered from the top layer to the bottom. A module may import from layers *below* it (earlier in the list means higher). `interfaces` may use `infrastructure`, which may use `application`, which may use `domain`. A module in `domain` importing from `application` is a violation. The idea: the core must not know about the outside.
- **Contract 2, type `forbidden`.** `source_modules` (the domain and the application) must not import anything in `forbidden_modules`: `anthropic`, `httpx`, `httpx2`, `openai`. Imports are checked *indirectly* too: if domain code imports a helper that imports `httpx`, that is still a violation. The effect: all contact with vendors, networks, web frameworks and databases is in `infrastructure` and `interfaces`.

### The Makefile line

`$(VENV)/bin/lint-imports` in the `lint` target. It prints each contract as `KEPT` or `BROKEN` and exits 1 if any contract is broken. The first run builds the graph; later runs reuse a cache in `.import_linter_cache/` (git ignores it).

### What a broken contract looks like

The last "Try it" command adds a throwaway file in the domain package that does `import httpx`, runs the checker, and deletes the file. The second contract reports `BROKEN` and prints the offending import chain.

## Try it yourself

1. The installed import-linter.

```bash
.venv/bin/lint-imports --version
```

What you should see (captured from this repository):

```text
import-linter 2.15
```

2. Check the project's contracts. Each contract prints KEPT or BROKEN.

```bash
.venv/bin/lint-imports --no-logo 2>&1 | tail -6
```

What you should see (captured from this repository):

```text
------------------------------------

Layers: interfaces on infrastructure on application on domain KEPT
Domain and application never import a vendor SDK or an HTTP client KEPT

Contracts: 2 kept, 0 broken.
```

3. The four layer folders the contract names, plus the package file.

```bash
ls src/token_meter
```

What you should see (captured from this repository):

```text
__init__.py
application
domain
infrastructure
interfaces
```

4. Break the rule on purpose with a throwaway file, and see the report. The file is deleted afterwards.

```bash
printf 'import httpx\n' > src/token_meter/domain/zz_demo.py; .venv/bin/lint-imports --no-cache --no-logo 2>&1 | grep -E 'KEPT|BROKEN|is not allowed|->'; rm -f src/token_meter/domain/zz_demo.py
```

What you should see (captured from this repository):

```text
Layers: interfaces on infrastructure on application on domain KEPT
Domain and application never import a vendor SDK or an HTTP client BROKEN
token_meter.domain is not allowed to import httpx:
-   token_meter.domain.zz_demo -> httpx (l.1)
```

## Mistakes people make

- **Using a layers contract where a forbidden contract is needed.** Layers say who may import whom inside the project; they do not forbid outside packages. The second contract does that.
- **Importing a vendor SDK "just for a type" into domain code.** The contract counts every import, including those used only for type hints. Use a protocol in `application/ports.py` instead.
- **Forgetting `include_external_packages`.** Without it, imports of outside packages are not in the graph and the forbidden contract can never fail.
- **Reading BROKEN as the end.** The report names the exact import chain; fix the direction of the dependency.

## Check yourself

1. What is the dependency graph?

   *Answer:* A map with an arrow from each module to every module it imports.

2. Which direction may imports go in the layers contract?

   *Answer:* From a layer to layers listed after it (below it): interfaces to infrastructure to application to domain.

3. Why does the forbidden contract also catch indirect imports?

   *Answer:* Because a chain of imports still pulls the vendor code into the core.

4. Where do vendor SDK imports live in this repository?

   *Answer:* In `infrastructure` and `interfaces`, never in `domain` or `application`.

5. What does a ports-and-adapters design buy?

   *Answer:* The core can be tested without any outside technology, because it only knows interfaces.

## Further reading

- import-linter documentation, https://import-linter.readthedocs.io/ (import-linter 2.15 and grimp 3.18 are pinned in the lock file; the report was produced by running them).

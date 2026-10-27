# YAML

## What it is

**YAML** is a text format for structured data, made to be readable by people. It describes the same things as JSON and TOML (named values, lists, nested groups) but uses indentation and short punctuation instead of braces. Many tools use it for configuration: GitHub Actions, Docker Compose, Kubernetes.

The basic rule: a **mapping** is `name: value` lines, a **sequence** (list) is lines that start with `- `, and a deeper indent means "inside".

## Why this repository uses it

GitHub Actions and Docker Compose both require YAML, so there is no choice. Everything else in the repository uses TOML (settings) or JSON (data), whose syntax is stricter and harder to get subtly wrong. The YAML files are kept short and checked with a parser.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `.github/workflows/ci.yml` | workflow definition |
| `.editorconfig` | sets two-space indentation for `*.yml` and `*.yaml` |

## How it works underneath

A YAML parser reads the file line by line, tracks the indentation of each line, and builds nested dictionaries and lists. Because indentation carries the structure, one extra or missing space changes the meaning. The parser also decides a type for each plain value: `true` is a boolean, `3.12` a number, `null` or `~` nothing, anything else text. This is called *implicit typing* and is the main source of surprises; quoting a value forces it to be text.

YAML is a superset of JSON: any valid JSON file is also valid YAML.

## Walkthrough of this repository's use

YAML files in this repository: `.github/workflows/ci.yml`.

The building blocks, each shown with a real line from `.github/workflows/ci.yml`:

- **Mapping** (a dictionary: names with values). `key: value`, one per line. Nesting is done by indentation with spaces. From the workflow: `name: ci`.
- **Sequence** (a list). Each item starts with `- `, or the whole list is written in square brackets. From the workflow: `on: [push, pull_request]` (a list of two names) and the `steps:` list whose items start with `- uses:` or `- run:`.
- **Scalars** (single values): text, numbers, `true`/`false`, `null`. Text usually needs no quotes, but quote it when it could be mistaken for something else (a version like `"3.12"`) or when it contains `: ` or ` #`.
- **Multi-line text.** `|` keeps the line breaks of the indented block; `>` joins the lines with spaces; adding `-` after either removes the final newline. This workflow does not use multi-line text.
- **Comments** start with `#`.
- **Indentation is meaning.** Two lines at the same indent are siblings; a more indented line belongs to the line above it. Tabs are not allowed for indentation.

Why quoting matters here: a YAML value that contains the two characters `: ` is read as a new mapping key. That is why a job name such as `The service as a real process: flag flips` must be written in quotes, and why this repository's workflows are checked with a YAML parser (see "Try it yourself").

## Try it yourself

1. Parse the workflow with Ruby's YAML parser. The `on` key becomes a list (Ruby shows it with the key `true` because YAML reads a bare `on` as a boolean; GitHub treats it as the event list).

```bash
ruby -ryaml -e 'p YAML.load_file(".github/workflows/ci.yml")["on"]' 2>&1 | head -2
```

What you should see (captured from this repository):

```text
nil
```

2. Why version numbers are quoted: unquoted `3.12` is a number (Float), quoted it is text (String).

```bash
ruby -ryaml -e 'p YAML.load("a: 3.12")["a"].class, YAML.load(%q(a: "3.12"))["a"].class' 2>&1 | head -2
```

What you should see (captured from this repository):

```text
Float
String
```

3. What an unquoted `: ` inside a value does: a syntax error (the message names the line and column).

```bash
ruby -ryaml -e 'begin; YAML.load("name: a: b"); rescue => e; puts e.message; end'
```

What you should see (captured from this repository):

```text
(<unknown>): mapping values are not allowed in this context at line 1 column 8
```

4. Literal `|` keeps the line break; folded `>-` joins lines with a space and drops the final newline.

```bash
ruby -ryaml -e 'puts YAML.load("t: |\n  one\n  two\n")["t"].inspect; puts YAML.load("t: >-\n  one\n  two\n")["t"].inspect'
```

What you should see (captured from this repository):

```text
"one\ntwo\n"
"one two"
```

## Mistakes people make

- **Tabs for indentation.** Not allowed; use spaces.
- **Unquoted special values.** `on`, `yes`, `no`, `3.10`, and text with `: ` are read as something other than the text you meant.
- **Inconsistent indentation.** Siblings must have exactly the same indent.
- **Duplicate keys.** Many parsers keep only the last. Keep each key once.
- **Trusting an editor's look.** Parse the file with a tool before you push.

## Check yourself

1. How do you write a list in YAML?

   *Answer:* Lines starting with `- `, or items in square brackets.

2. What does `>-` do after a key?

   *Answer:* Starts a folded text block: lines are joined with spaces and the final newline is dropped.

3. Why is `"3.12"` quoted?

   *Answer:* Unquoted it is a number; as a version it must stay text.

4. What makes `name: a: b` an error?

   *Answer:* The second `: ` starts a mapping where text is expected; quote the value.

5. Is JSON valid YAML?

   *Answer:* Yes: YAML is a superset of JSON.

## Further reading

- YAML 1.2.2 specification, https://yaml.org/spec/1.2.2/ (examples run with Ruby's YAML parser, which ships with macOS).

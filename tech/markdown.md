# Markdown

## What it is

**Markdown** is a way to write formatted text using only plain characters. You type `# Title` and a viewer shows a big heading; you type `**word**` and it shows bold. Because the source is plain text, it is easy to write, easy to compare in version control, and readable even when nothing renders it. The dialect used by GitHub is called GitHub-Flavored Markdown (GFM) and adds tables, task lists and fenced code blocks.

## Why this repository uses it

Everything a human reads in this repository is Markdown: the README, the architecture notes, decision records, the changelog, the prompts and these technology notes. One simple format means one set of tools and nothing to install to read them.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `*.md` | 7 files outside `tech/`; the table below lists them all |

## How it works underneath

A Markdown viewer parses the text line by line. Blank lines end paragraphs. Lines starting with `#`, `-`, `1.`, `>` or a table pipe are recognized as block elements; text inside backticks is turned into code. The result is converted to HTML for display. The rules for every element are in the specification, which is why different viewers show nearly the same page.

Markdown is not a programming language: it has no variables or loops. Anything dynamic (the measured numbers in a report) is produced by a program and written into the file.

## Walkthrough of this repository's use

### The first lines of this repository's `README.md`

```markdown
# ai-token-and-cost-meter

`meter` is a small command-line tool that reads 50 support-desk prompts, estimates the tokens and cost of the whole run before the first call, calls a model at three decoding settings, and reports how far the estimate was from the bill and how much the answers vary.

| | |
| --- | --- |
| **Lesson** | `/prep/ai/project-token-and-cost-meter`, "Build a token and cost meter" (`data-structure-explainer/src/content/tracks/ai/95-project-token-and-cost-meter.md` in the Plainround app) |
| **Planned hours** | 6 |
| **Level** | Beginner |
| **Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md), decisions in [docs/adr](docs/adr) |
| **Technology notes** | [tech/README.md](tech/README.md), 33 notes that teach every technology used here from zero |

```

- `# Title` (one `#` and a space) is a first-level heading, the title of the page. `##` is second level, `###` third, down to `######` for sixth level.
- A blank line separates paragraphs. A line that begins with `- ` or `* ` is a bullet; `1. ` begins a numbered list item.
- `**bold**` and `*italic*` (or `_italic_`) mark emphasis. A word between backticks, `like this`, is code. Three backticks on a line of their own open and close a **code fence**; a language name after the opening fence (```` ```bash ````) lets the viewer color it.
- A link is `[text](address)`. An image is `![alt](address)`.
- A table is rows of cells separated by `|`, with a second row of dashes (`| --- | --- |`) under the header.
- A quote starts with `>`.

### Every Markdown file in this repository

7 files. The second column is each file's own first heading.

| File | First heading |
| --- | --- |
| `ARCHITECTURE.md` | Architecture: ai-token-and-cost-meter |
| `CHANGELOG.md` | Changelog |
| `README.md` | ai-token-and-cost-meter |
| `docs/adr/0001-the-model-is-a-port-with-three-adapters.md` | 0001. The model is a port with recorded, local and Claude adapters |
| `docs/adr/0002-claude-is-not-asked-for-sampling.md` | 0002. The Claude adapter does not send temperature or top_p |
| `docs/adr/0003-estimate-calibrate-then-check-on-held-out-rows.md` | 0003. Calibrate the estimator on a pilot, check it on the rest |
| `docs/adr/0004-csv-journal-with-fsync-and-a-torn-tail-rule.md` | 0004. One CSV row per call, fsynced, with a torn-tail rule |

### Special uses here

- `README.md` is shown automatically on the repository's front page by GitHub.
- `CHANGELOG.md` records what changed in each version, newest first.
- `docs/adr/*.md` (where present) are *architecture decision records*: one short file per important decision, saying the context, the decision and its consequences. Their names start with a number so they sort in the order they were made.
- `prompts/**/*.md` are the prompts sent to models. Each starts with a small block between `---` lines, the *front matter* (`version: v1`), which the program reads to learn the prompt's version; the rest of the file is the prompt text. Storing prompts as versioned files keeps them reviewable and lets an evaluation name the exact prompt it used.
- `ARCHITECTURE.md` contains diagrams written as Mermaid text inside ```` ```mermaid ```` fences. GitHub draws them as pictures.
- Pages under `data/` (where present) are the help-center articles that the program searches.
- Reports under `evals/` and `migration/` are written by the program (`.md` files that are generated from measurements); they are committed so you can read the results without running anything.

## Try it yourself

1. The title and first paragraph of the README, as plain text.

```bash
head -5 README.md
```

What you should see (captured from this repository):

```text
# ai-token-and-cost-meter

`meter` is a small command-line tool that reads 50 support-desk prompts, estimates the tokens and cost of the whole run before the first call, calls a model at three decoding settings, and reports how far the estimate was from the bill and how much the answers vary.

| | |
```

2. How many second-level sections the README has.

```bash
grep -c '^## ' README.md
```

What you should see (captured from this repository):

```text
9
```

3. Code fences are lines of three backticks: they come in pairs.

```bash
grep -n '^```' README.md | head -4
```

What you should see (captured from this repository):

```text
26:```bash
34:```
38:```bash
42:```
```

4. The Markdown files at the top of the repository.

```bash
ls *.md
```

What you should see (captured from this repository):

```text
ARCHITECTURE.md
CHANGELOG.md
README.md
```

## Mistakes people make

- **Forgetting the blank line before a list or table.** Many viewers then run the list into the paragraph above it.
- **Unbalanced code fences.** A missing closing fence turns the rest of the page into code.
- **Using Markdown for generated numbers by hand.** Numbers in reports come from the program, so they cannot drift from the code.
- **Trailing-space line breaks lost by editors.** `.editorconfig` keeps trailing whitespace in `.md` files.
- **Pipes inside table cells.** A `|` ends the cell; write `\|` to show one.

## Check yourself

1. How do you make a second-level heading?

   *Answer:* Start a line with `## ` (two hash signs and a space).

2. What marks a block of code?

   *Answer:* A fence of three backticks above and below, or four spaces of indent.

3. Why are prompts stored as Markdown files with front matter?

   *Answer:* So each prompt is versioned and reviewable, and the program can read its version.

4. What is an ADR?

   *Answer:* An architecture decision record: a short note of one decision, why it was made and what follows.

5. What is front matter?

   *Answer:* A block between two `---` lines at the top of a file that holds settings such as `version: v1`.

## Further reading

- CommonMark specification, https://spec.commonmark.org/ and the GitHub Flavored Markdown spec, https://github.github.com/gfm/ (the element list above was checked against how this repository's own files are written).

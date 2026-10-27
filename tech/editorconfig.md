# EditorConfig

## What it is

Different people use different code editors, and editors have different defaults: tabs or spaces, Windows or Unix line endings, a final newline or none. **EditorConfig** is a tiny standard: a file named `.editorconfig` that lists these settings, and a plug-in (or built-in support) in your editor that reads it and applies it. The file is plain text in an INI style: `[pattern]` section headers and `key = value` lines.

## Why this repository uses it

Without it, one person's editor saves a file with tabs and another's with spaces, and the version history fills with changes that only move whitespace. The file also protects the one file where whitespace is not optional: a Makefile needs real tabs (see `make.md`).

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `.editorconfig` | the file itself |

## How it works underneath

When you open a file, the editor looks for `.editorconfig` in that file's folder and then in each parent folder, until a file with `root = true`. It reads the sections whose pattern matches the file's path, from top to bottom; if two sections set the same key, the later one wins. The editor then applies the settings when you type and save. Nothing in the project's build reads the file: it only affects editors. (`ruff format` and `make lint` enforce the Python layout independently.)

Patterns: `*` matches any run of characters except `/`, `**` matches anything including `/`, `{a,b}` matches either, and a plain name such as `Makefile` matches that file name.

## Walkthrough of this repository's use

`.editorconfig`, the whole file, block by block. Under each block, every line is explained.

```ini
root = true
```

- `root = true`: Marks this as the top-level `.editorconfig`. Editors look for this file in the current folder and in every folder above it; `root = true` says "stop looking further up".

```ini
[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 4
```

- `[*]`: A section header. The text in brackets is a file pattern; `*` matches every file. Settings below it apply to all files unless a later section overrides them.
- `charset = utf-8`: Save files in UTF-8, the encoding that can hold every language's letters and symbols.
- `end_of_line = lf`: End each line with a single line-feed character (`LF`, the Linux and macOS convention), not the Windows pair `CR LF`.
- `insert_final_newline = true`: End every file with a newline character, so tools that read line by line see a complete last line.
- `trim_trailing_whitespace = true`: Remove spaces at the end of lines when saving.
- `indent_style = space`: Indent with spaces, not tab characters.
- `indent_size = 4`: One level of indentation is four spaces. (Python's standard.)

```ini
[*.{yml,yaml,json,toml}]
indent_size = 2
```

- `[*.{yml,yaml,json,toml}]`: A section for files whose names end in `.yml`, `.yaml`, `.json` or `.toml`. The braces list alternatives.
- `indent_size = 2`: For those file types, one level is two spaces.

```ini
[Makefile]
indent_style = tab
```

- `[Makefile]`: A section for the file named `Makefile`.
- `indent_style = tab`: A Makefile recipe line must start with a tab character, so tabs are required here (see `make.md`).

```ini
[*.md]
trim_trailing_whitespace = false
```

- `[*.md]`: A section for Markdown files.
- `trim_trailing_whitespace = false`: Do not remove trailing spaces in Markdown: two spaces at the end of a line mean "line break" in Markdown.

## Try it yourself

1. The whole file.

```bash
cat .editorconfig
```

What you should see (captured from this repository):

```text
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 4

[*.{yml,yaml,json,toml}]
indent_size = 2

[Makefile]
indent_style = tab

[*.md]
trim_trailing_whitespace = false
```

2. Count the Makefile lines that start with or contain a tab character: the file really uses tabs.

```bash
grep -c "$(printf '\t')" Makefile
```

What you should see (captured from this repository):

```text
32
```

3. The TOML file has no tabs (spaces only), matching `indent_style = space`.

```bash
grep -c "$(printf '\t')" pyproject.toml
```

What you should see (captured from this repository):

```text
0
```

4. The last byte of a Markdown file is a newline (`\n`), which `insert_final_newline` asks for.

```bash
tail -c 1 README.md | od -c | head -1
```

What you should see (captured from this repository):

```text
0000000   \n                                                            
```

## Mistakes people make

- **Expecting EditorConfig to reformat existing files.** It only applies when you edit and save in an editor that supports it. `make format` is what reformats Python.
- **Forgetting the Makefile section.** Tabs turned into spaces break the Makefile with `missing separator`.
- **Trimming trailing spaces in Markdown.** Two trailing spaces can mean a line break, so the Markdown section turns trimming off.
- **Windows line endings in a Unix project.** `end_of_line = lf` keeps every file the same.

## Check yourself

1. What does `root = true` do?

   *Answer:* It stops the editor from looking in parent folders for more `.editorconfig` files.

2. Which setting protects the Makefile?

   *Answer:* `indent_style = tab` in the `[Makefile]` section.

3. What does `[*.{yml,yaml,json,toml}]` match?

   *Answer:* Files ending in `.yml`, `.yaml`, `.json` or `.toml`.

4. If two sections set the same key, which wins?

   *Answer:* The one that appears later in the file.

5. Does `make` read `.editorconfig`?

   *Answer:* No. Only editors do.

## Further reading

- EditorConfig specification, https://spec.editorconfig.org/ (the file here uses only keys defined in the specification).

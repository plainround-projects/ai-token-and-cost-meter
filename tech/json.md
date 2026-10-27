# JSON

## What it is

**JSON** (JavaScript Object Notation) is a text format for data. It has six kinds of value: **text** in double quotes (`"hello"`), **numbers** (`3`, `0.5`), **true** and **false**, **null** (nothing), **arrays** (ordered lists in square brackets, `[1, 2, 3]`) and **objects** (collections of `"name": value` pairs in curly braces, `{"id": "p01", "kind": "short"}`). Values nest freely. There are no comments and no trailing commas.

Almost every programming language can read and write JSON, which makes it the common way for programs to exchange data: web services speak it, model APIs speak it, and so do the data files in this repository.

## Why this repository uses it

The repository's data (prices, thresholds, decision rules, tool definitions, reports) must be readable by people, comparable in version control and loadable without extra libraries. JSON meets all three: Python's standard library reads it, a diff shows exactly which number changed, and the same format is used on the wire to the model servers. Money amounts are written as **text** (`"0.0001"`) rather than numbers so they are read as exact decimals, not binary floating-point approximations.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `data/prices.json` | data or configuration file |

## How it works underneath

A JSON parser reads the characters from left to right and builds objects in memory: an object becomes a dictionary, an array a list, text a string. Python's `json.loads(text)` does this and `json.dumps(obj)` writes it back. Rules that surprise people: keys are always text; the order of keys is kept by Python but carries no meaning in the format; a number has no size or type (the reader decides; `1` and `1.0` are both numbers); and strings are Unicode, with `\n` and `\"` as escapes for a newline and a quote.

`sort_keys` and a fixed indent produce *canonical* output: the same data always gives the same bytes. The repository writes its reports that way so that a rerun gives an identical file, and a change in the file means a change in the data.

## Walkthrough of this repository's use

### Every `.json` file in this repository

| File | Shape | Keys (first ones) |
| --- | --- | --- |
| `data/prices.json` | one object, 5 top-level keys | `model`, `input_per_1k`, `output_per_1k`, `read_date`, `source` |

### The files, key by key

`data/prices.json`:

```json
{
  "model": "claude-haiku-5-5",
  "input_per_1k": "0.0001",
  "output_per_1k": "0.0005",
  "read_date": "2026-10-26",
  "source": "Anthropic list price for claude-haiku-5-5 ($0.10 and $0.50 per million..."
}
```

What each key means:

- `model` (text): the model id (a name the provider or the local server knows).
- `input_per_1k` (text): price in US dollars for 1,000 input tokens, written as text so no rounding error creeps in (it is read as a `Decimal`).
- `output_per_1k` (text): price in US dollars for 1,000 output tokens, as text.
- `read_date` (text): the day the prices were copied from the price list; a table older than the allowed age is refused.
- `source` (text): where the numbers came from, in words.

## Try it yourself

1. Python data to JSON text: `None` becomes `null`, `True` becomes `true`, keys are sorted.

```bash
.venv/bin/python -c "import json; print(json.dumps({'b': 1, 'a': [1.5, None, True]}, sort_keys=True))"
```

What you should see (captured from this repository):

```text
{"a": [1.5, null, true], "b": 1}
```

2. A price stored as text and read as an exact `Decimal`.

```bash
.venv/bin/python -c "import json; d = json.loads('{\"price\": \"0.0001\"}'); from decimal import Decimal; print(Decimal(d['price']) * 3)"
```

What you should see (captured from this repository):

```text
0.0003
```

3. A trailing comma is not allowed in JSON; this is the error.

```bash
.venv/bin/python -c "import json; json.loads('{\"a\": 1,}')" 2>&1 | tail -1
```

What you should see (captured from this repository):

```text
json.decoder.JSONDecodeError: Illegal trailing comma before end of object: line 1 column 8 (char 7)
```

4. How many JSON files the repository tracks and generates, outside the tool caches.

```bash
find . -name '*.json' -not -path './.venv/*' -not -path './.mypy_cache/*' -not -path './.ruff_cache/*' -not -path './.import_linter_cache/*' | wc -l
```

What you should see (captured from this repository):

```text
       9
```

5. Python's built-in pretty printer (`json.tool`) reformats any JSON text.

```bash
.venv/bin/python -m json.tool data/prices.json | sed -n 1,6p
```

What you should see (captured from this repository):

```text
{
    "model": "claude-haiku-5-5",
    "input_per_1k": "0.0001",
    "output_per_1k": "0.0005",
    "read_date": "2026-10-26",
    "source": "Anthropic list price for claude-haiku-5-5 ($0.10 and $0.50 per million tokens, prompts up to 100K tokens), copied on read_date. Prices change: read the current ones and update read_date before a real run."
```

## Mistakes people make

- **Comments or trailing commas.** JSON allows neither; the parser raises an error.
- **Storing money as a number.** `0.1 + 0.2` is not `0.3` in binary floating point. Prices are text, read with `Decimal`.
- **Assuming key order means something.** Order is not part of the format.
- **Single quotes.** JSON strings use double quotes only.
- **Hand-editing a generated file.** Reports are written by the program; edit the code or data and rerun.

## Check yourself

1. What are the six JSON value kinds?

   *Answer:* Text, number, true/false, null, array, object.

2. Why are prices stored as text?

   *Answer:* So they can be read as exact decimals instead of floating-point numbers.

3. Can a JSON file hold a comment?

   *Answer:* No.

4. What does `json.loads` return for an object?

   *Answer:* A Python dictionary.

5. Why write JSON with sorted keys?

   *Answer:* So the same data always produces the same bytes and the file diff shows real changes only.

## Further reading

- ECMA-404 / RFC 8259, https://www.rfc-editor.org/rfc/rfc8259 and Python `json`, https://docs.python.org/3/library/json.html (examples run on Python 3.13).

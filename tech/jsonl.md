# JSON Lines (JSONL)

## What it is

**JSON Lines** is JSON with one rule added: a file holds **one complete JSON value per line** (almost always an object), with no commas between lines and no enclosing brackets. A file of 450 records is simply 450 lines. A reader can process it one line at a time without loading the whole file.

## Why this repository uses it

Two properties matter here. First, **appending is safe**: adding a record is writing one line at the end, so a recording that is interrupted keeps every complete line, and a restarted recording resumes from there. Second, **diffs and tools work line by line**: `wc -l` counts records and `grep` finds one. The recordings (answers saved from a real local model so that tests and demos can replay them) are JSON Lines for exactly this reason.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `data/prompts.jsonl` | records, one per line |
| `tests/fixtures/recordings/meter-qwen2.5-0.5b.jsonl` | records, one per line |

## How it works underneath

To read a JSON Lines file, split the text on newline characters and parse each non-empty line with an ordinary JSON parser. To write one, serialize each record with no line breaks inside (JSON escapes a newline inside text as `\n`, so a record never spans lines) and add one newline. If a process dies in the middle of writing a line, the last line is incomplete; a careful reader skips or cuts it. The CSV journal in `csv.md` does exactly that.

A **recording** here is keyed by a SHA-256 fingerprint of the request (model, messages, settings). Replaying means: compute the fingerprint of the new request, look it up, and return the saved answer. The same request therefore always gets the same answer, offline, which is what makes the test numbers repeatable.

## Walkthrough of this repository's use

### Every JSON Lines file in this repository

| File | Shape | Keys (first ones) |
| --- | --- | --- |
| `data/prompts.jsonl` | one JSON object per line, 50 lines | `id`, `kind`, `text` |
| `tests/fixtures/recordings/meter-qwen2.5-0.5b.jsonl` | one JSON object per line, 450 lines | `key`, `tag`, `recorded_with`, `response` |

### The files, key by key

`data/prompts.jsonl`, record 1 (one line of the file, laid out over several lines here, long text shortened):

```json
{
  "id": "p01",
  "kind": "short",
  "text": "How do I reset my password?"
}
```

What each key means:

- `id` (text): a short unique id for this record.
- `kind` (text): which group the record belongs to.
- `text` (text): the text of the record.

`tests/fixtures/recordings/meter-qwen2.5-0.5b.jsonl`, record 1 (one line of the file, laid out over several lines here, long text shortened):

```json
{
  "key": "e7af80f0f5b4433321260b5dc01dd196516a0859af1e111d493080144f22d8c7",
  "tag": "p02/t10/2",
  "recorded_with": {
    "provider": "openai-compatible",
    "requested_model": "qwen2.5:0.5b",
    "model": "qwen2.5:0.5b"
  },
  "response": {
    "text": "In Alibaba Cloud's Service, there are two ways to manage past orders: ...",
    "stop_reason": "length",
    "usage": {
      "input_tokens": 37,
      "output_tokens": 200
    },
    "latency_seconds": 3.9084,
    "model": "qwen2.5:0.5b",
    "tool_calls": []
  }
}
```

What each key means:

- `key` (text): a fingerprint (SHA-256) of the request, used to look the answer up.
- `tag` (text): an id for the call, used to find the same call in a recording.
- `recorded_with` (object): which provider and model produced the answer.
- `recorded_with.provider` (text): the kind of provider (`openai-compatible` for a local server).
- `recorded_with.requested_model` (text): the model name the request asked for.
- `recorded_with.model` (text): the model id (a name the provider or the local server knows).
- `response` (object): the recorded answer.
- `response.text` (text): the text of the record.
- `response.stop_reason` (text): why the model stopped (`stop`, `length`, ...).
- `response.usage` (object): the token counts the provider reported.
- `response.usage.input_tokens` (whole number): tokens sent to the model.
- `response.usage.output_tokens` (whole number): tokens the model produced.
- `response.latency_seconds` (decimal number): how long the call took.
- `response.model` (text): the model id (a name the provider or the local server knows).
- `response.tool_calls` (list): how many tool calls were made.

## Try it yourself

1. A JSON Lines file's record count is its line count.

```bash
wc -l data/prompts.jsonl
```

What you should see (captured from this repository):

```text
      50 data/prompts.jsonl
```

2. The first record, as stored: one line.

```bash
head -c 300 data/prompts.jsonl
```

What you should see (captured from this repository):

```text
{"id": "p01", "kind": "short", "text": "How do I reset my password?"}
{"id": "p02", "kind": "short", "text": "Where can I see my past orders?"}
{"id": "p03", "kind": "short", "text": "Do you ship to Canada?"}
{"id": "p04", "kind": "short", "text": "Can I change the delivery address after I order?"}
```

3. Parse every line and list the keys of the first record.

```bash
.venv/bin/python -c "import json; rows = [json.loads(x) for x in open('data/prompts.jsonl') if x.strip()]; print(len(rows), sorted(rows[0]))"
```

What you should see (captured from this repository):

```text
50 ['id', 'kind', 'text']
```

4. A well-formed file ends with a newline.

```bash
tail -c 1 data/prompts.jsonl | od -c | head -1
```

What you should see (captured from this repository):

```text
0000000   \n                                                            
```

## Mistakes people make

- **Wrapping the records in `[ ]` or adding commas.** That is plain JSON, not JSON Lines.
- **A record with a real line break inside.** JSON escapes it as `\n`; a writer must use a JSON serializer, never hand-built text.
- **Assuming the last line is complete.** After a crash it may be cut off.
- **Re-sorting a recording.** Order does not matter to the replay, but a changed order makes a diff noisy.
- **Loading a huge file at once.** Read it line by line.

## Check yourself

1. What distinguishes JSON Lines from JSON?

   *Answer:* One complete JSON value per line; no commas or outer brackets.

2. Why does append-only suit recordings?

   *Answer:* An interrupted run keeps every finished line and can resume.

3. How is a request matched to its recorded answer?

   *Answer:* By a SHA-256 fingerprint of the request.

4. How are embedding vectors stored here?

   *Answer:* As base64 text of 32-bit floats.

5. How do you count the records?

   *Answer:* Count the lines (`wc -l`).

## Further reading

- JSON Lines, https://jsonlines.org/ (the format is a convention on top of RFC 8259 JSON; examples were run locally).

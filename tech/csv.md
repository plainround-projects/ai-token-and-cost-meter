# CSV

## What it is

**CSV** (comma-separated values) is a plain-text format for tables. The first line is a **header** naming the columns; every following line is one **row**, with values separated by commas. A value that contains a comma, a double quote or a line break is wrapped in double quotes, and a double quote inside is written twice (`""`). Spreadsheets, databases and Python all read it.

## Why this repository uses it

The meter's journal is a table: one row per model call with the prompt, the setting, the repeat number, the token counts and the answer. CSV opens in any spreadsheet for inspection, appends cheaply (one line per call), and a half-written last row is easy to detect and cut off. That makes it a good fit for the one requirement that matters here: *a crash must cost at most the call that was in flight*.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/token_meter/infrastructure/csv_journal.py` | the journal: header, append with fsync, repair of a torn tail, read back |
| `out/journal.csv` | the file it writes (ignored by git) |
| `src/token_meter/application/report.py` | reads the journal to build the report |

## How it works underneath

Plain text hides a problem: a file is not written all at once. Python's `write` fills a buffer in the program; `flush` pushes it to the operating system; the operating system keeps it in memory and writes it to disk later. A crash between those steps loses data. `os.fsync` forces the last step. A related problem is the **torn write**: if the process dies halfway through a row, the file ends mid-line. Because every complete row ends with a newline, a missing final newline means "torn".

The `csv` module handles quoting rules so that values containing commas or line breaks survive a round trip. Always use it instead of splitting on commas yourself.

## Walkthrough of this repository's use

The journal is the file `out/journal.csv`: one row per paid model call, so an interrupted run can skip the calls it already paid for. It is written by `src/token_meter/infrastructure/csv_journal.py`.

The header, `COLUMNS`:

`src/token_meter/infrastructure/csv_journal.py`, line 20:

```python
COLUMNS = ("prompt_id", "setting", "repeat", "input_tokens", "output_tokens", "stop_reason", "latency_s", "text")
```

A real journal written by `make run` (long text shortened):

```text
prompt_id,setting,repeat,input_tokens,output_tokens,stop_reason,latency_s,text
p01,t0,0,36,185,stop,5.9261,"""To reset your password, you can follow these steps:\n\n1. Log in to the website or application where you registered your account.\n\n2. Click on the \""Forgot Password\"" or \""Reset Pas...
p01,t0,1,36,185,stop,6.3255,"""To reset your password, you can follow these steps:\n\n1. Log in to the website or application where you registered your account.\n\n2. Click on the \""Forgot Password\"" or \""Reset Pas...
```

The class `CsvJournal`, method by method.

**Making the line (`_line`).**

`src/token_meter/infrastructure/csv_journal.py`, lines 35 to 38:

```python
    def _line(self, values: tuple[object, ...]) -> str:
        buffer = io.StringIO()
        csv.writer(buffer, lineterminator="\n").writerow(values)
        return buffer.getvalue()
```

`csv.writer` puts commas between the values and, when a value contains a comma, a quote or a newline, wraps it in double quotes and doubles any inner quotes. `lineterminator="\n"` fixes the line ending (the module's default is `\r\n`). Writing into an in-memory `StringIO` gives back the exact text of one row.

**Making it durable (`_write`).**

`src/token_meter/infrastructure/csv_journal.py`, lines 40 to 44:

```python
    def _write(self, text: str) -> None:
        with self._path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
```

- `self._path.open("a", ...)`: open the file for **a**ppending. `newline=""` stops Python from translating line endings (the csv module wants to control them).
- `with ... as handle`: the file is closed when the block ends, even after an error.
- `handle.write(text)` puts the row into Python's buffer; `handle.flush()` hands the buffer to the operating system; `os.fsync(handle.fileno())` asks the operating system to write it from its own cache onto the disk. Only after `fsync` returns is the row safe against a power cut or a `kill -9`. This is the cost of crash safety: one disk sync per call.

**Healing a torn file (`_cut_torn_tail`).**

`src/token_meter/infrastructure/csv_journal.py`, lines 46 to 50:

```python
    def _cut_torn_tail(self) -> None:
        data = self._path.read_bytes()
        if data.endswith(b"\n"):
            return
        self._path.write_bytes(data[: data.rfind(b"\n") + 1])
```

If the process was killed in the middle of writing a row, the file ends without a newline. This method reads the bytes; if the last byte is a newline, all is well; otherwise it cuts the file back to just after the last complete newline. The incomplete row is dropped, and that call is simply made again.

**Reading it back (`_read`).**

`src/token_meter/infrastructure/csv_journal.py`, lines 52 to 69:

```python
    def _read(self) -> list[JournalRow]:
        with self._path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != COLUMNS:
                raise JournalCorrupt(
                    f"{self._path}: expected the header {','.join(COLUMNS)}, found {reader.fieldnames}"
                )
            return [
                JournalRow(
                    CallKey(r["prompt_id"], r["setting"], int(r["repeat"])),
                    int(r["input_tokens"]),
                    int(r["output_tokens"]),
                    StopReason(r["stop_reason"]),
                    float(r["latency_s"]),
                    json.loads(r["text"]),
                )
                for r in reader
            ]
```

`csv.DictReader` reads each row as a dictionary keyed by the header. The check on `fieldnames` refuses a file whose header differs from `COLUMNS` (raising `JournalCorrupt`), so a wrong file is never silently mixed in. Each text field is turned back into a number or an enum value. The `text` column holds the answer as JSON text (see `json.md`), because an answer can contain commas, quotes and line breaks.

## Try it yourself

1. How the csv module quotes a comma and a quote.

```bash
.venv/bin/python -c "import csv, io; b = io.StringIO(); csv.writer(b, lineterminator='\n').writerow(['a,b', 'say \"hi\"', 3]); print(b.getvalue(), end='')"
```

What you should see (captured from this repository):

```text
"a,b","say ""hi""",3
```

2. Reading it back: the quoted value with a comma stays one value.

```bash
.venv/bin/python -c "import csv, io; print(list(csv.DictReader(io.StringIO('x,y\n1,\"a,b\"\n'))))"
```

What you should see (captured from this repository):

```text
[{'x': '1', 'y': 'a,b'}]
```

3. The journal from your last `make run` (run `make run` first if the file is missing).

```bash
head -c 400 out/journal.csv
```

What you should see (captured from this repository):

```text
prompt_id,setting,repeat,input_tokens,output_tokens,stop_reason,latency_s,text
p01,t0,0,36,185,stop,5.9261,"""To reset your password, you can follow these steps:\n\n1. Log in to the website or application where you registered your account.\n\n2. Click on the \""Forgot Password\"" or \""Reset Password\"" option.\n\n3. Enter your email address or username associated with your account.\n\n4. Follow t
```

4. Lines in the journal: one header line plus one per paid call.

```bash
wc -l out/journal.csv
```

What you should see (captured from this repository):

```text
     451 out/journal.csv
```

## Mistakes people make

- **Splitting a line on commas.** A value may contain a comma. Use the `csv` module.
- **Forgetting `newline=""` when opening.** Python would translate line endings and break quoted line breaks.
- **Skipping `fsync`.** A power cut or `kill -9` could lose rows that the program believed were saved.
- **Ignoring a torn last line.** The file would fail to parse or count a half row; the journal cuts it off on open.
- **Mixing files with different headers.** The journal checks the header and refuses a mismatch.

## Check yourself

1. Why is a value with a comma wrapped in quotes?

   *Answer:* So a reader knows the comma is part of the value, not a separator.

2. What does `os.fsync` add after `flush`?

   *Answer:* It forces the operating system to write the data to disk.

3. How does the journal detect a torn row?

   *Answer:* The file does not end with a newline.

4. Why does the journal check its header?

   *Answer:* To refuse a file that is not a journal.

5. What is stored in the `text` column and in what format?

   *Answer:* The model's answer, as JSON text.

## Further reading

- Python `csv` module, https://docs.python.org/3/library/csv.html and RFC 4180, https://www.rfc-editor.org/rfc/rfc4180 (examples run locally).

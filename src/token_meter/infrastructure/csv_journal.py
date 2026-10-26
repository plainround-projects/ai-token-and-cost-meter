"""The journal as a CSV file: append and flush one row per call, so a crash costs only unfinished calls."""

from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path

from token_meter.domain.errors import DomainError
from token_meter.domain.journal import CallKey, JournalRow
from token_meter.domain.llm import StopReason


class JournalCorrupt(DomainError):
    """The journal file does not start with the expected header; delete it or restore it from a copy."""


COLUMNS = ("prompt_id", "setting", "repeat", "input_tokens", "output_tokens", "stop_reason", "latency_s", "text")


class CsvJournal:
    """Header written once, rows appended with fsync. A torn last line (a kill during a write) is cut off on open."""

    def __init__(self, path: Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.stat().st_size > 0:
            self._cut_torn_tail()
        else:
            self._write(self._line(COLUMNS))
        self._rows = self._read()

    def _line(self, values: tuple[object, ...]) -> str:
        buffer = io.StringIO()
        csv.writer(buffer, lineterminator="\n").writerow(values)
        return buffer.getvalue()

    def _write(self, text: str) -> None:
        with self._path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())

    def _cut_torn_tail(self) -> None:
        data = self._path.read_bytes()
        if data.endswith(b"\n"):
            return
        self._path.write_bytes(data[: data.rfind(b"\n") + 1])

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

    def done_keys(self) -> set[CallKey]:
        return {row.key for row in self._rows}

    def append(self, row: JournalRow) -> None:
        values = (
            row.key.prompt_id,
            row.key.setting,
            row.key.repeat,
            row.input_tokens,
            row.output_tokens,
            row.stop_reason.value,
            f"{row.latency_seconds:.4f}",
            json.dumps(row.text, ensure_ascii=False),
        )
        self._write(self._line(values))
        self._rows.append(row)

    def rows(self) -> list[JournalRow]:
        return list(self._rows)

"""Shared builders for tests: small prompt sets, a fixed clock and a scripted model."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from token_meter.domain.journal import CallKey, JournalRow
from token_meter.domain.llm import ChatRequest, ChatResponse, StopReason, Usage
from token_meter.domain.prompts import Kind, PromptRecord


class FixedClock:
    """A clock that only moves when a test says so."""

    def __init__(self, today: date = date(2026, 10, 26)) -> None:
        self._today = today
        self._ticks = 0.0

    def monotonic(self) -> float:
        self._ticks += 0.25
        return self._ticks

    def today(self) -> date:
        return self._today

    def now(self) -> datetime:
        return datetime(self._today.year, self._today.month, self._today.day, tzinfo=UTC)


class ScriptedModel:
    """Answers every request from a function, and remembers the requests it saw."""

    def __init__(self, answer=None, sampling: bool = True) -> None:
        self.requests: list[ChatRequest] = []
        self._answer = answer or (lambda request: ("ok", 10, 3))
        self._sampling = sampling

    @property
    def name(self) -> str:
        return "scripted"

    @property
    def supports_sampling(self) -> bool:
        return self._sampling

    def complete(self, request: ChatRequest) -> ChatResponse:
        self.requests.append(request)
        text, tokens_in, tokens_out = self._answer(request)
        return ChatResponse(text, StopReason.END, Usage(tokens_in, tokens_out), 0.5, "scripted")


class MemoryJournal:
    """An in-memory journal with the same contract as the CSV one."""

    def __init__(self, rows: list[JournalRow] | None = None) -> None:
        self._rows = list(rows or [])

    def done_keys(self) -> set[CallKey]:
        return {r.key for r in self._rows}

    def append(self, row: JournalRow) -> None:
        self._rows.append(row)

    def rows(self) -> list[JournalRow]:
        return list(self._rows)


def prompt(id_: str, kind: Kind, text: str, label: str | None = None) -> PromptRecord:
    return PromptRecord(id_, kind, text, label)


def row(
    prompt_id: str, setting: str, repeat: int, tokens_in: int, tokens_out: int, text: str = "a", stop=StopReason.END
):
    return JournalRow(CallKey(prompt_id, setting, repeat), tokens_in, tokens_out, stop, 0.1, text)


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()

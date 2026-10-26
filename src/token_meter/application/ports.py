"""The boundaries the use cases depend on. Adapters in `infrastructure` implement them."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from typing import Protocol

from token_meter.domain.journal import CallKey, JournalRow
from token_meter.domain.llm import ChatRequest, ChatResponse


class ChatModel(Protocol):
    """One chat model behind one interface: a vendor, a local server or a recording."""

    @property
    def name(self) -> str:
        """The model id the responses come from."""
        ...

    @property
    def supports_sampling(self) -> bool:
        """False when the provider rejects `temperature` and `top_p` (the request then says so)."""
        ...

    def complete(self, request: ChatRequest) -> ChatResponse:
        """Send one request. Raises `TransientModelError` or `PermanentModelError`."""
        ...


class Embedder(Protocol):
    """Turns texts into vectors."""

    @property
    def name(self) -> str: ...

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """One vector per text, in order."""
        ...


class Clock(Protocol):
    """Time, injected so tests are deterministic."""

    def monotonic(self) -> float: ...

    def today(self) -> date: ...

    def now(self) -> datetime: ...


class Journal(Protocol):
    """The append-only record of paid calls. Appending a row must survive a crash right after it."""

    def done_keys(self) -> set[CallKey]:
        """Keys of every call already paid for."""
        ...

    def append(self, row: JournalRow) -> None:
        """Write one row and make it durable before returning."""
        ...

    def rows(self) -> list[JournalRow]:
        """Every row, in the order written."""
        ...

"""Recorded responses: replay them in tests and demos, or record a live model's answers into fixtures.

A recording is a JSON Lines file. Each line holds the request fingerprint, the call's tag, a note about what
produced it and the response. Fixtures hold synthetic data only (no credentials, no personal data).
"""

from __future__ import annotations

import json
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from token_meter.application.ports import ChatModel
from token_meter.domain.errors import RecordingMissing
from token_meter.domain.llm import ChatRequest, ChatResponse


class RecordingStore:
    """An in-memory index over one recording file (or every `*.jsonl` in a folder), appended to on `put`."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._entries: dict[str, dict[str, Any]] = {}
        files = sorted(path.glob("*.jsonl")) if path.is_dir() else ([path] if path.exists() else [])
        for file in files:
            with file.open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        entry = json.loads(line)
                        self._entries[entry["key"]] = entry
        self._append_to = path / "recorded.jsonl" if path.is_dir() else path

    def __len__(self) -> int:
        return len(self._entries)

    def get(self, key: str) -> ChatResponse | None:
        with self._lock:
            entry = self._entries.get(key)
        return ChatResponse.from_json(entry["response"]) if entry else None

    def put(self, key: str, tag: str, response: ChatResponse, recorded_with: Mapping[str, Any]) -> None:
        entry = {"key": key, "tag": tag, "recorded_with": dict(recorded_with), "response": response.to_json()}
        with self._lock:
            self._entries[key] = entry
            self._append_to.parent.mkdir(parents=True, exist_ok=True)
            with self._append_to.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")
                handle.flush()


class RecordedChatModel:
    """Replays recorded responses. A request nobody recorded raises `RecordingMissing`."""

    def __init__(self, store: RecordingStore) -> None:
        self._store = store

    @property
    def name(self) -> str:
        return "recorded"

    @property
    def supports_sampling(self) -> bool:
        return True

    def complete(self, request: ChatRequest) -> ChatResponse:
        response = self._store.get(request.fingerprint())
        if response is None:
            raise RecordingMissing(
                f"no recording for request tag={request.tag!r} fingerprint={request.fingerprint()[:12]}; "
                "run `make record` against a live model to refresh the fixtures"
            )
        return response


class RecordingChatModel:
    """Wraps a live model and writes each answer into a recording. A request already recorded is replayed."""

    def __init__(self, inner: ChatModel, store: RecordingStore, note: Mapping[str, Any]) -> None:
        self._inner = inner
        self._store = store
        self._note = dict(note)

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def supports_sampling(self) -> bool:
        return self._inner.supports_sampling

    def complete(self, request: ChatRequest) -> ChatResponse:
        key = request.fingerprint()
        cached = self._store.get(key)
        if cached is not None:
            return cached
        response = self._inner.complete(request)
        self._store.put(key, request.tag, response, {**self._note, "model": response.model})
        return response

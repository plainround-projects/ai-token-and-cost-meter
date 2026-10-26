"""One row per paid call: the unit of restartability."""

from __future__ import annotations

from dataclasses import dataclass

from token_meter.domain.llm import StopReason


@dataclass(frozen=True, slots=True)
class CallKey:
    """Identifies one call. A run never pays for the same key twice."""

    prompt_id: str
    setting: str
    repeat: int


@dataclass(frozen=True, slots=True)
class JournalRow:
    """What one call cost and returned, as billed by the provider."""

    key: CallKey
    input_tokens: int
    output_tokens: int
    stop_reason: StopReason
    latency_seconds: float
    text: str

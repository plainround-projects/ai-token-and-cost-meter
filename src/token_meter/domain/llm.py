"""Vendor-neutral value objects for one chat-model call. No SDK is imported here."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Role(StrEnum):
    """Who wrote a message."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class StopReason(StrEnum):
    """Why the model stopped writing."""

    END = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    REFUSAL = "refusal"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """A tool the model may call: a name, a description and a JSON Schema for the arguments."""

    name: str
    description: str
    parameters: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ToolCall:
    """A tool call the model asked for."""

    id: str
    name: str
    arguments: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """One message of a conversation. A tool result carries the id of the call it answers."""

    role: Role
    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: str | None = None

    @classmethod
    def user(cls, content: str) -> ChatMessage:
        return cls(Role.USER, content)


@dataclass(frozen=True, slots=True)
class Usage:
    """Tokens the provider billed for one call, read from its usage block, never recomputed."""

    input_tokens: int
    output_tokens: int


@dataclass(frozen=True, slots=True)
class ChatRequest:
    """Everything that defines one call.

    `tag` names the call for recordings and logs (for example `p01/t07/2`); it is never sent to a vendor.
    `model` overrides the adapter's default model and is not part of the recording key.
    """

    messages: tuple[ChatMessage, ...]
    system: str | None = None
    max_output_tokens: int = 1024
    temperature: float | None = None
    top_p: float | None = None
    response_schema: Mapping[str, Any] | None = None
    tools: tuple[ToolSpec, ...] = ()
    tag: str = ""
    model: str | None = None

    def fingerprint(self) -> str:
        """A stable hash of the request, used to find its recording. The model name is excluded."""
        body = {
            "messages": [
                {
                    "role": m.role.value,
                    "content": m.content,
                    "tool_calls": [[c.id, c.name, dict(c.arguments)] for c in m.tool_calls],
                    "tool_call_id": m.tool_call_id,
                }
                for m in self.messages
            ],
            "system": self.system,
            "max_output_tokens": self.max_output_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "response_schema": self.response_schema,
            "tools": [[t.name, t.description, dict(t.parameters)] for t in self.tools],
            "tag": self.tag,
        }
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ChatResponse:
    """What came back: the text or the tool calls, why it stopped, the billed usage and the latency."""

    text: str
    stop_reason: StopReason
    usage: Usage
    latency_seconds: float
    model: str
    tool_calls: tuple[ToolCall, ...] = field(default=())

    def to_json(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "stop_reason": self.stop_reason.value,
            "usage": {"input_tokens": self.usage.input_tokens, "output_tokens": self.usage.output_tokens},
            "latency_seconds": self.latency_seconds,
            "model": self.model,
            "tool_calls": [{"id": c.id, "name": c.name, "arguments": dict(c.arguments)} for c in self.tool_calls],
        }

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> ChatResponse:
        return cls(
            text=str(data["text"]),
            stop_reason=StopReason(data["stop_reason"]),
            usage=Usage(int(data["usage"]["input_tokens"]), int(data["usage"]["output_tokens"])),
            latency_seconds=float(data["latency_seconds"]),
            model=str(data["model"]),
            tool_calls=tuple(
                ToolCall(str(c["id"]), str(c["name"]), dict(c["arguments"])) for c in data.get("tool_calls", [])
            ),
        )

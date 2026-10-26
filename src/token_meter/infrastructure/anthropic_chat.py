"""A chat model on the Anthropic Messages API, through the official SDK.

The Messages API rejects `temperature`, `top_p` and `top_k` from API version 2026-10-21 on, so this adapter
reports `supports_sampling = False` and raises `UnsupportedParameter` if a request asks for them. Structured
output uses `output_config.format`; forced `tool_choice` is not used (newer models answer it with a 400).
"""

from __future__ import annotations

from typing import Any, Literal

import anthropic

from token_meter.application.ports import Clock
from token_meter.domain.errors import PermanentModelError, TransientModelError, UnsupportedParameter
from token_meter.domain.llm import ChatMessage, ChatRequest, ChatResponse, Role, StopReason, ToolCall, Usage

Thinking = Literal["omit", "disabled", "between_tools"]

_STOP = {
    "end_turn": StopReason.END,
    "stop_sequence": StopReason.END,
    "max_tokens": StopReason.LENGTH,
    "tool_use": StopReason.TOOL_CALLS,
    "refusal": StopReason.REFUSAL,
}


def _messages_payload(messages: tuple[ChatMessage, ...]) -> list[dict[str, Any]]:
    """Map neutral messages to Messages API turns; consecutive tool results share one user turn."""
    out: list[dict[str, Any]] = []
    for message in messages:
        if message.role is Role.TOOL:
            block = {"type": "tool_result", "tool_use_id": message.tool_call_id, "content": message.content}
            if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list):
                out[-1]["content"].append(block)
            else:
                out.append({"role": "user", "content": [block]})
        elif message.role is Role.ASSISTANT and message.tool_calls:
            blocks: list[dict[str, Any]] = [{"type": "text", "text": message.content}] if message.content else []
            blocks.extend(
                {"type": "tool_use", "id": c.id, "name": c.name, "input": dict(c.arguments)} for c in message.tool_calls
            )
            out.append({"role": "assistant", "content": blocks})
        else:
            out.append({"role": message.role.value, "content": message.content})
    return out


class AnthropicChatModel:
    """Calls Claude. Build the SDK client with your key from the environment; this class never reads it."""

    def __init__(self, client: anthropic.Anthropic, model: str, clock: Clock, thinking: Thinking = "disabled") -> None:
        self._client = client
        self._model = model
        self._clock = clock
        self._thinking = thinking

    @property
    def name(self) -> str:
        return self._model

    @property
    def supports_sampling(self) -> bool:
        return False

    def build_payload(self, request: ChatRequest) -> dict[str, Any]:
        """The keyword arguments for `messages.create` (public so tests can assert on them)."""
        if request.temperature is not None or request.top_p is not None:
            raise UnsupportedParameter("the Messages API rejects temperature and top_p; leave them unset")
        payload: dict[str, Any] = {
            "model": request.model or self._model,
            "max_tokens": request.max_output_tokens,
            "messages": _messages_payload(request.messages),
        }
        if request.system:
            payload["system"] = request.system
        if self._thinking != "omit":
            payload["thinking"] = {"type": self._thinking}
        if request.response_schema is not None:
            payload["output_config"] = {"format": {"type": "json_schema", "schema": dict(request.response_schema)}}
        if request.tools:
            payload["tools"] = [
                {"name": t.name, "description": t.description, "input_schema": dict(t.parameters)}
                for t in request.tools
            ]
        return payload

    def complete(self, request: ChatRequest) -> ChatResponse:
        payload = self.build_payload(request)
        started = self._clock.monotonic()
        try:
            message = self._client.messages.create(**payload)
        except anthropic.APIConnectionError as error:
            raise TransientModelError(f"{type(error).__name__}: {error}") from error
        except anthropic.APIStatusError as error:
            if error.status_code in (408, 409, 429) or error.status_code >= 500:
                raise TransientModelError(f"HTTP {error.status_code}: {error.message}") from error
            raise PermanentModelError(f"HTTP {error.status_code}: {error.message}") from error
        elapsed = self._clock.monotonic() - started
        text = "".join(block.text for block in message.content if block.type == "text")
        calls = tuple(
            ToolCall(block.id, block.name, dict(block.input)) for block in message.content if block.type == "tool_use"
        )
        return ChatResponse(
            text=text,
            stop_reason=_STOP.get(message.stop_reason or "", StopReason.OTHER),
            usage=Usage(message.usage.input_tokens, message.usage.output_tokens),
            latency_seconds=round(elapsed, 4),
            model=message.model,
            tool_calls=calls,
        )

    def count_tokens(self, request: ChatRequest) -> int:
        """Ask the provider how many input tokens a request would use (no generation, no charge)."""
        payload = self.build_payload(request)
        for unused in ("max_tokens", "thinking", "output_config"):
            payload.pop(unused, None)
        return int(self._client.messages.count_tokens(**payload).input_tokens)

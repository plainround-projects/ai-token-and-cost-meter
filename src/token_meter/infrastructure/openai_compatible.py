"""A chat model behind the OpenAI-compatible `/chat/completions` endpoint (Ollama, llama.cpp, vLLM, hosted)."""

from __future__ import annotations

import json
from typing import Any

import httpx

from token_meter.application.ports import Clock
from token_meter.domain.errors import PermanentModelError, TransientModelError
from token_meter.domain.llm import ChatMessage, ChatRequest, ChatResponse, Role, StopReason, ToolCall, Usage

_FINISH = {
    "stop": StopReason.END,
    "length": StopReason.LENGTH,
    "tool_calls": StopReason.TOOL_CALLS,
    "content_filter": StopReason.REFUSAL,
}


def _message_payload(message: ChatMessage) -> dict[str, Any]:
    if message.role is Role.TOOL:
        return {"role": "tool", "tool_call_id": message.tool_call_id, "content": message.content}
    payload: dict[str, Any] = {"role": message.role.value, "content": message.content}
    if message.tool_calls:
        payload["tool_calls"] = [
            {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": json.dumps(dict(c.arguments))}}
            for c in message.tool_calls
        ]
    return payload


class OpenAICompatibleChatModel:
    """Talks to any server that implements `POST {base_url}/chat/completions`."""

    def __init__(self, http: httpx.Client, base_url: str, model: str, clock: Clock, api_key: str | None = None) -> None:
        self._http = http
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._clock = clock
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    @property
    def name(self) -> str:
        return self._model

    @property
    def supports_sampling(self) -> bool:
        return True

    def build_payload(self, request: ChatRequest) -> dict[str, Any]:
        """The JSON body for a request (public so tests can assert on it)."""
        messages: list[dict[str, Any]] = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.extend(_message_payload(m) for m in request.messages)
        payload: dict[str, Any] = {
            "model": request.model or self._model,
            "messages": messages,
            "max_tokens": request.max_output_tokens,
            "stream": False,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.top_p is not None:
            payload["top_p"] = request.top_p
        if request.response_schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": dict(request.response_schema), "strict": True},
            }
        if request.tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {"name": t.name, "description": t.description, "parameters": dict(t.parameters)},
                }
                for t in request.tools
            ]
        return payload

    def complete(self, request: ChatRequest) -> ChatResponse:
        started = self._clock.monotonic()
        try:
            reply = self._http.post(
                f"{self._base_url}/chat/completions", json=self.build_payload(request), headers=self._headers
            )
        except httpx.TransportError as error:
            raise TransientModelError(f"{type(error).__name__}: {error}") from error
        elapsed = self._clock.monotonic() - started
        if reply.status_code == 429 or reply.status_code >= 500:
            raise TransientModelError(f"HTTP {reply.status_code}")
        if reply.status_code >= 400:
            raise PermanentModelError(f"HTTP {reply.status_code}: {reply.text[:200]}")
        return self._parse(reply.json(), elapsed)

    def _parse(self, body: dict[str, Any], elapsed: float) -> ChatResponse:
        try:
            choice = body["choices"][0]
            message = choice["message"]
            usage = body["usage"]
            calls = tuple(
                ToolCall(str(c.get("id", f"call_{i}")), c["function"]["name"], _arguments(c["function"]["arguments"]))
                for i, c in enumerate(message.get("tool_calls") or [])
            )
            stop = StopReason.TOOL_CALLS if calls else _FINISH.get(choice.get("finish_reason") or "", StopReason.OTHER)
            return ChatResponse(
                text=message.get("content") or "",
                stop_reason=stop,
                usage=Usage(int(usage["prompt_tokens"]), int(usage["completion_tokens"])),
                latency_seconds=round(elapsed, 4),
                model=str(body.get("model", self._model)),
                tool_calls=calls,
            )
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise PermanentModelError(f"unexpected response shape: {error!r}") from error


def _arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    parsed = json.loads(raw) if raw else {}
    if not isinstance(parsed, dict):
        raise ValueError("tool arguments must be a JSON object")
    return parsed

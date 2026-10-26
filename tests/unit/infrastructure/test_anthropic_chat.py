import json

import anthropic
import httpx2
import pytest

from tests.conftest import FixedClock
from token_meter.domain.errors import PermanentModelError, TransientModelError, UnsupportedParameter
from token_meter.domain.llm import ChatMessage, ChatRequest, Role, StopReason, ToolCall, ToolSpec
from token_meter.infrastructure.anthropic_chat import AnthropicChatModel


def message(content, stop="end_turn", tokens_in=21, tokens_out=6):
    return httpx2.Response(
        200,
        json={
            "id": "msg_1",
            "type": "message",
            "role": "assistant",
            "model": "claude-haiku-5-5",
            "content": content,
            "stop_reason": stop,
            "stop_sequence": None,
            "usage": {"input_tokens": tokens_in, "output_tokens": tokens_out},
        },
    )


def adapter(handler, thinking="disabled"):
    client = anthropic.Anthropic(
        api_key="test-key-not-real",
        max_retries=0,
        http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler)),
    )
    return AnthropicChatModel(client, "claude-haiku-5-5", FixedClock(), thinking)


def test_text_usage_stop_reason_and_model_come_from_the_response():
    seen = {}

    def handler(request):
        seen["body"] = json.loads(request.content)
        return message([{"type": "text", "text": "hello"}])

    response = adapter(handler).complete(
        ChatRequest((ChatMessage.user("hi"),), system="be brief", max_output_tokens=40)
    )
    assert (response.text, response.usage.input_tokens, response.usage.output_tokens) == ("hello", 21, 6)
    assert response.stop_reason is StopReason.END
    assert response.model == "claude-haiku-5-5"
    assert seen["body"]["system"] == "be brief"
    assert seen["body"]["max_tokens"] == 40
    assert seen["body"]["thinking"] == {"type": "disabled"}
    assert "temperature" not in seen["body"]
    assert "top_p" not in seen["body"]


def test_sampling_is_refused_because_the_messages_api_rejects_it():
    model = adapter(lambda r: message([]))
    assert not model.supports_sampling
    with pytest.raises(UnsupportedParameter, match="temperature"):
        model.complete(ChatRequest((ChatMessage.user("hi"),), temperature=0.0))
    with pytest.raises(UnsupportedParameter):
        model.complete(ChatRequest((ChatMessage.user("hi"),), top_p=0.9))


def test_thinking_can_be_left_out_or_set_to_between_tools():
    assert "thinking" not in adapter(lambda r: message([]), "omit").build_payload(ChatRequest((ChatMessage.user("x"),)))
    payload = adapter(lambda r: message([]), "between_tools").build_payload(ChatRequest((ChatMessage.user("x"),)))
    assert payload["thinking"] == {"type": "between_tools"}


def test_a_schema_goes_into_output_config_format_not_a_forced_tool():
    schema = {"type": "object", "properties": {"a": {"type": "string"}}}
    payload = adapter(lambda r: message([])).build_payload(
        ChatRequest((ChatMessage.user("x"),), response_schema=schema)
    )
    assert payload["output_config"] == {"format": {"type": "json_schema", "schema": schema}}
    assert "tool_choice" not in payload


def test_tool_calls_and_tool_results_map_to_tool_use_and_tool_result_blocks():
    history = (
        ChatMessage.user("book it"),
        ChatMessage(
            Role.ASSISTANT, "checking", (ToolCall("t1", "slots", {"day": "mon"}), ToolCall("t2", "get", {"id": 1}))
        ),
        ChatMessage(Role.TOOL, "free", tool_call_id="t1"),
        ChatMessage(Role.TOOL, "event", tool_call_id="t2"),
    )
    spec = ToolSpec("slots", "find slots", {"type": "object"})
    payload = adapter(lambda r: message([])).build_payload(ChatRequest(history, tools=(spec,)))
    assert payload["tools"] == [{"name": "slots", "description": "find slots", "input_schema": {"type": "object"}}]
    assistant = payload["messages"][1]["content"]
    assert [b["type"] for b in assistant] == ["text", "tool_use", "tool_use"]
    results = payload["messages"][2]
    assert results["role"] == "user"
    assert [b["tool_use_id"] for b in results["content"]] == ["t1", "t2"]
    assert len(payload["messages"]) == 3


def test_tool_use_blocks_in_the_response_become_tool_calls():
    content = [
        {"type": "text", "text": "ok"},
        {"type": "tool_use", "id": "tu1", "name": "slots", "input": {"day": "tue"}},
    ]
    response = adapter(lambda r: message(content, "tool_use")).complete(ChatRequest((ChatMessage.user("x"),)))
    assert response.stop_reason is StopReason.TOOL_CALLS
    assert response.tool_calls == (ToolCall("tu1", "slots", {"day": "tue"}),)


@pytest.mark.parametrize(
    ("stop", "expected"),
    [("max_tokens", StopReason.LENGTH), ("refusal", StopReason.REFUSAL), ("pause_turn", StopReason.OTHER)],
)
def test_other_stop_reasons_are_mapped(stop, expected):
    response = adapter(lambda r: message([{"type": "text", "text": "x"}], stop)).complete(
        ChatRequest((ChatMessage.user("x"),))
    )
    assert response.stop_reason is expected


@pytest.mark.parametrize("status", [429, 500, 529])
def test_rate_limits_and_server_errors_are_transient(status):
    with pytest.raises(TransientModelError):
        adapter(
            lambda r: httpx2.Response(status, json={"type": "error", "error": {"type": "x", "message": "y"}})
        ).complete(ChatRequest((ChatMessage.user("x"),)))


def test_a_bad_request_is_permanent():
    body = {"type": "error", "error": {"type": "invalid_request_error", "message": "nope"}}
    with pytest.raises(PermanentModelError, match="HTTP 400"):
        adapter(lambda r: httpx2.Response(400, json=body)).complete(ChatRequest((ChatMessage.user("x"),)))


def test_a_dropped_connection_is_transient():
    def handler(request):
        raise httpx2.ConnectError("refused", request=request)

    with pytest.raises(TransientModelError):
        adapter(handler).complete(ChatRequest((ChatMessage.user("x"),)))


def test_count_tokens_asks_the_provider_without_generating():
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx2.Response(200, json={"input_tokens": 17})

    count = adapter(handler).count_tokens(ChatRequest((ChatMessage.user("hi"),), system="s"))
    assert count == 17
    assert seen["path"].endswith("/messages/count_tokens")
    assert "max_tokens" not in seen["body"]
    assert "thinking" not in seen["body"]

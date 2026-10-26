import json
from typing import Any

import httpx
import pytest

from tests.conftest import FixedClock
from token_meter.domain.errors import PermanentModelError, TransientModelError
from token_meter.domain.llm import ChatMessage, ChatRequest, Role, StopReason, ToolCall, ToolSpec
from token_meter.infrastructure.openai_compatible import OpenAICompatibleChatModel


def model(handler, api_key=None):
    http = httpx.Client(transport=httpx.MockTransport(handler))
    return OpenAICompatibleChatModel(http, "http://local/v1/", "small-model", FixedClock(), api_key)


def ok(content="hello", finish="stop", tool_calls=None, prompt_tokens=11, completion_tokens=3):
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return httpx.Response(
        200,
        json={
            "model": "small-model-0",
            "choices": [{"message": message, "finish_reason": finish}],
            "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
        },
    )


def test_a_reply_becomes_text_usage_stop_reason_and_latency():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers.get("authorization")
        return ok()  # type: ignore[no-any-return]

    response = model(handler, api_key="k").complete(
        ChatRequest((ChatMessage.user("hi"),), system="be brief", max_output_tokens=50, temperature=0.7, top_p=0.9)
    )
    assert (response.text, response.usage.input_tokens, response.usage.output_tokens) == ("hello", 11, 3)
    assert response.stop_reason is StopReason.END
    assert response.latency_seconds == 0.25
    assert response.model == "small-model-0"
    assert seen["url"] == "http://local/v1/chat/completions"
    assert seen["auth"] == "Bearer k"
    assert seen["body"]["messages"][0] == {"role": "system", "content": "be brief"}
    assert (seen["body"]["max_tokens"], seen["body"]["temperature"], seen["body"]["top_p"]) == (50, 0.7, 0.9)


def test_unset_sampling_is_left_out_of_the_body():
    body = model(lambda r: ok()).build_payload(ChatRequest((ChatMessage.user("hi"),)))
    assert "temperature" not in body
    assert "top_p" not in body
    assert body["model"] == "small-model"


def test_a_schema_becomes_a_json_schema_response_format():
    schema = {"type": "object", "properties": {"a": {"type": "string"}}}
    body = model(lambda r: ok()).build_payload(ChatRequest((ChatMessage.user("hi"),), response_schema=schema))
    assert body["response_format"]["json_schema"]["schema"] == schema
    assert body["response_format"]["type"] == "json_schema"


def test_tool_specs_calls_and_results_use_the_function_calling_shape():
    spec = ToolSpec("lookup", "find one", {"type": "object"})
    history = (
        ChatMessage.user("find 4"),
        ChatMessage(Role.ASSISTANT, "", (ToolCall("c1", "lookup", {"id": 4}),)),
        ChatMessage(Role.TOOL, '{"ok": true}', tool_call_id="c1"),
    )
    body = model(lambda r: ok()).build_payload(ChatRequest(history, tools=(spec,)))
    assert body["tools"][0]["function"]["name"] == "lookup"
    assert body["messages"][1]["tool_calls"][0]["function"]["arguments"] == '{"id": 4}'
    assert body["messages"][2] == {"role": "tool", "tool_call_id": "c1", "content": '{"ok": true}'}


def test_tool_calls_in_the_reply_are_parsed_with_json_arguments():
    calls = [{"id": "c9", "function": {"name": "lookup", "arguments": '{"id": 7}'}}]
    response = model(lambda r: ok(content=None, finish="stop", tool_calls=calls)).complete(
        ChatRequest((ChatMessage.user("x"),))
    )
    assert response.stop_reason is StopReason.TOOL_CALLS
    assert response.tool_calls == (ToolCall("c9", "lookup", {"id": 7}),)
    assert response.text == ""


def test_arguments_may_already_be_an_object_and_missing_ids_are_numbered():
    calls = [{"function": {"name": "lookup", "arguments": {"id": 1}}}]
    response = model(lambda r: ok(tool_calls=calls)).complete(ChatRequest((ChatMessage.user("x"),)))
    assert response.tool_calls[0].id == "call_0"
    assert response.tool_calls[0].arguments == {"id": 1}


def test_a_length_finish_reason_is_kept():
    assert (
        model(lambda r: ok(finish="length")).complete(ChatRequest((ChatMessage.user("x"),))).stop_reason
        is StopReason.LENGTH
    )


@pytest.mark.parametrize("status", [429, 500, 503])
def test_rate_limits_and_server_errors_are_transient(status):
    with pytest.raises(TransientModelError, match=str(status)):
        model(lambda r: httpx.Response(status)).complete(ChatRequest((ChatMessage.user("x"),)))


def test_a_client_error_is_permanent():
    with pytest.raises(PermanentModelError, match="HTTP 400"):
        model(lambda r: httpx.Response(400, text="bad")).complete(ChatRequest((ChatMessage.user("x"),)))


def test_a_dropped_connection_is_transient():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(TransientModelError, match="ConnectError"):
        model(handler).complete(ChatRequest((ChatMessage.user("x"),)))


def test_an_unexpected_shape_is_permanent():
    with pytest.raises(PermanentModelError, match="unexpected response shape"):
        model(lambda r: httpx.Response(200, json={"choices": []})).complete(ChatRequest((ChatMessage.user("x"),)))
    bad_args = [{"id": "c", "function": {"name": "t", "arguments": "[1]"}}]
    with pytest.raises(PermanentModelError):
        model(lambda r: ok(tool_calls=bad_args)).complete(ChatRequest((ChatMessage.user("x"),)))


def test_the_model_reports_its_name_and_that_it_accepts_sampling():
    adapter = model(lambda r: ok())
    assert adapter.name == "small-model"
    assert adapter.supports_sampling

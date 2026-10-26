from token_meter.domain.llm import ChatMessage, ChatRequest, ChatResponse, StopReason, ToolCall, ToolSpec, Usage


def request(**changes):
    base = {"messages": (ChatMessage.user("hello"),), "max_output_tokens": 50, "tag": "a"}
    return ChatRequest(**{**base, **changes})


def test_the_same_request_always_has_the_same_fingerprint():
    assert request().fingerprint() == request().fingerprint()


def test_the_model_name_is_not_part_of_the_fingerprint():
    assert request(model="a-model").fingerprint() == request(model="another").fingerprint()


def test_the_tag_and_the_sampling_settings_are_part_of_the_fingerprint():
    base = request().fingerprint()
    assert request(tag="b").fingerprint() != base
    assert request(temperature=0.7).fingerprint() != base
    assert request(top_p=0.9).fingerprint() != base


def test_tools_and_schemas_change_the_fingerprint():
    base = request().fingerprint()
    assert request(response_schema={"type": "object"}).fingerprint() != base
    assert request(tools=(ToolSpec("t", "d", {"type": "object"}),)).fingerprint() != base


def test_a_response_survives_a_json_round_trip_with_tool_calls():
    response = ChatResponse(
        "text", StopReason.TOOL_CALLS, Usage(5, 7), 1.25, "m", (ToolCall("c1", "lookup", {"id": 4}),)
    )
    assert ChatResponse.from_json(response.to_json()) == response

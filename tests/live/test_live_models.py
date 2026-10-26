"""Opt-in tests that call a real model. Run with `make test-live`; skipped in every other run."""

import os

import httpx
import pytest

from token_meter.domain.llm import ChatMessage, ChatRequest, StopReason
from token_meter.infrastructure.clock import SystemClock
from token_meter.infrastructure.model_factory import ModelSettings, build_chat_model

pytestmark = pytest.mark.live


def local_server_up() -> bool:
    try:
        return httpx.get("http://localhost:11434/api/tags", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY is not set")
def test_claude_answers_and_reports_billed_usage():
    settings = ModelSettings.from_env(
        {"MODEL_PROVIDER": "anthropic", **{k: v for k, v in os.environ.items() if k.startswith("MODEL_")}}
    )
    model = build_chat_model(settings, SystemClock())
    response = model.complete(
        ChatRequest((ChatMessage.user("Reply with the single word: ready"),), max_output_tokens=64)
    )
    assert response.usage.input_tokens > 0
    assert response.usage.output_tokens > 0
    assert response.stop_reason in (StopReason.END, StopReason.LENGTH)


@pytest.mark.skipif(
    not local_server_up(), reason="no local OpenAI-compatible server on localhost:11434 (run make models)"
)
def test_the_local_model_returns_a_usage_block_and_obeys_temperature_zero():
    model = build_chat_model(ModelSettings.from_env({"MODEL_PROVIDER": "openai-compatible"}), SystemClock())
    request = ChatRequest((ChatMessage.user("How do I reset my password?"),), max_output_tokens=60, temperature=0.0)
    first, second = model.complete(request), model.complete(request)
    assert first.usage.input_tokens > 0
    assert first.text.strip() == second.text.strip()

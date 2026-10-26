"""Builds the configured chat model from the environment: recorded, local server or Claude."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import anthropic
import httpx

from token_meter.application.ports import ChatModel, Clock
from token_meter.infrastructure.anthropic_chat import AnthropicChatModel, Thinking
from token_meter.infrastructure.env import ConfigurationError, choice, optional_text, positive_float, positive_int, text
from token_meter.infrastructure.openai_compatible import OpenAICompatibleChatModel
from token_meter.infrastructure.recording import RecordedChatModel, RecordingChatModel, RecordingStore
from token_meter.infrastructure.resilient import RetryingChatModel

PROVIDERS = ("recorded", "anthropic", "openai-compatible")


@dataclass(frozen=True, slots=True)
class ModelSettings:
    """Which model to call and how. See .env.example for every variable."""

    provider: str
    model: str
    recordings: Path
    record: bool
    openai_base_url: str
    openai_api_key: str | None
    anthropic_thinking: Thinking
    timeout_seconds: float
    attempts: int

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> ModelSettings:
        env = os.environ if environ is None else environ
        provider = choice(env, "MODEL_PROVIDER", "recorded", PROVIDERS)
        default_model = {"recorded": "recorded", "anthropic": "claude-haiku-5-5", "openai-compatible": "qwen2.5:0.5b"}[
            provider
        ]
        thinking = choice(env, "ANTHROPIC_THINKING", "disabled", ("omit", "disabled", "between_tools"))
        return cls(
            provider=provider,
            model=text(env, "MODEL_NAME", default_model),
            recordings=Path(text(env, "RECORDINGS_PATH", "tests/fixtures/recordings")),
            record=choice(env, "RECORD", "off", ("on", "off")) == "on",
            openai_base_url=text(env, "OPENAI_BASE_URL", "http://localhost:11434/v1"),
            openai_api_key=optional_text(env, "OPENAI_API_KEY"),
            anthropic_thinking=thinking,  # type: ignore[arg-type]
            timeout_seconds=positive_float(env, "MODEL_TIMEOUT_SECONDS", 120.0),
            attempts=positive_int(env, "MODEL_ATTEMPTS", 3),
        )


def build_chat_model(settings: ModelSettings, clock: Clock, environ: Mapping[str, str] | None = None) -> ChatModel:
    """Wire the adapter the settings name. A live adapter is wrapped with retries, and with a recorder if asked."""
    env = os.environ if environ is None else environ
    if settings.provider == "recorded":
        return RecordedChatModel(RecordingStore(settings.recordings))
    live: ChatModel
    if settings.provider == "anthropic":
        if not env.get("ANTHROPIC_API_KEY"):
            raise ConfigurationError("ANTHROPIC_API_KEY must be set in the environment to use the anthropic provider")
        client = anthropic.Anthropic(timeout=settings.timeout_seconds, max_retries=0)
        live = AnthropicChatModel(client, settings.model, clock, settings.anthropic_thinking)
    else:
        http = httpx.Client(timeout=settings.timeout_seconds)
        live = OpenAICompatibleChatModel(http, settings.openai_base_url, settings.model, clock, settings.openai_api_key)
    live = RetryingChatModel(live, attempts=settings.attempts)
    if settings.record:
        note = {"provider": settings.provider, "requested_model": settings.model}
        return RecordingChatModel(live, RecordingStore(settings.recordings), note)
    return live

"""A decorator for services: estimate each request before it is sent and log estimate and bill side by side."""

from __future__ import annotations

import logging

from token_meter.application.ports import ChatModel
from token_meter.domain.estimation import TokenEstimator
from token_meter.domain.llm import ChatRequest, ChatResponse

_log = logging.getLogger(__name__)


class MeteredChatModel:
    """Wraps any `ChatModel`. Logs sizes only, never the prompt text."""

    def __init__(self, inner: ChatModel, estimator: TokenEstimator) -> None:
        self._inner = inner
        self._estimator = estimator

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def supports_sampling(self) -> bool:
        return self._inner.supports_sampling

    def estimate_input_tokens(self, request: ChatRequest) -> int:
        """The estimate for a request: its messages and system prompt."""
        text = "".join(m.content for m in request.messages)
        return self._estimator.tokens(text, request.system or "")

    def complete(self, request: ChatRequest) -> ChatResponse:
        estimated = self.estimate_input_tokens(request)
        response = self._inner.complete(request)
        billed = response.usage.input_tokens
        error = (estimated - billed) / billed if billed else 0.0
        _log.info(
            "estimate against bill",
            extra={
                "fields": {
                    "tag": request.tag,
                    "estimated_input": estimated,
                    "billed_input": billed,
                    "error": f"{error:+.1%}",
                    "billed_output": response.usage.output_tokens,
                }
            },
        )
        return response

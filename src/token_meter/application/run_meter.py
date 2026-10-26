"""The metering run: estimate first, refuse above the budget, call, and journal one row per call."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal

from token_meter.application.ports import ChatModel, Journal
from token_meter.domain.decoding import DecodingSetting
from token_meter.domain.errors import UnsupportedParameter
from token_meter.domain.estimation import RunEstimate, TokenEstimator, require_within_budget
from token_meter.domain.journal import CallKey, JournalRow
from token_meter.domain.llm import ChatMessage, ChatRequest
from token_meter.domain.pricing import PriceTable
from token_meter.domain.prompts import PromptRecord

_log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RunPlan:
    """Everything that defines a run besides the model and the journal."""

    prompts: Sequence[PromptRecord]
    settings: Sequence[DecodingSetting]
    repeats: int
    max_output_tokens: int
    prices: PriceTable
    estimator: TokenEstimator
    budget: Decimal | None = None
    system: str | None = None
    throttle_seconds: float = 0.0


@dataclass(frozen=True, slots=True)
class RunSummary:
    """What a run did: calls paid now, calls skipped because the journal had them, and why it ended."""

    estimate: RunEstimate
    calls_made: int
    calls_skipped: int
    interrupted: bool


def plan_keys(plan: RunPlan) -> list[CallKey]:
    """Every call the plan covers, in the order they are made."""
    return [
        CallKey(prompt.id, setting.name, repeat)
        for prompt in plan.prompts
        for setting in plan.settings
        for repeat in range(plan.repeats)
    ]


def estimate_pending(plan: RunPlan, done: set[CallKey]) -> RunEstimate:
    """The cost of the calls the journal does not hold yet, estimated before the first one."""
    by_prompt = {p.id: p for p in plan.prompts}
    pending = [k for k in plan_keys(plan) if k not in done]
    input_tokens = sum(
        plan.estimator.tokens(by_prompt[k.prompt_id].text, plan.system or "", by_prompt[k.prompt_id].kind)
        for k in pending
    )
    output_tokens = len(pending) * plan.max_output_tokens
    return RunEstimate(len(pending), input_tokens, output_tokens, plan.prices.cost(input_tokens, output_tokens))


class RunMeter:
    """Calls the model once per (prompt, setting, repeat) that the journal does not hold yet."""

    def __init__(
        self,
        model: ChatModel,
        journal: Journal,
        stop_requested: Callable[[], bool] = lambda: False,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._model = model
        self._journal = journal
        self._stop_requested = stop_requested
        self._sleep = sleep

    def run(self, plan: RunPlan) -> RunSummary:
        """Refuse above the budget before any call, then make the missing calls, one journal row each."""
        if not self._model.supports_sampling:
            raise UnsupportedParameter(
                f"{self._model.name} does not accept temperature or top_p, "
                "so the three decoding settings cannot be compared"
            )
        estimate = estimate_pending(plan, self._journal.done_keys())
        require_within_budget(estimate, plan.budget)
        done = self._journal.done_keys()
        by_prompt = {p.id: p for p in plan.prompts}
        by_setting = {s.name: s for s in plan.settings}
        made = skipped = 0
        for key in plan_keys(plan):
            if key in done:
                skipped += 1
                continue
            if self._stop_requested():
                _log.info("stop requested, leaving the rest for a restart", extra={"fields": {"made": made}})
                return RunSummary(estimate, made, skipped, interrupted=True)
            setting = by_setting[key.setting]
            request = ChatRequest(
                messages=(ChatMessage.user(by_prompt[key.prompt_id].text),),
                system=plan.system,
                max_output_tokens=plan.max_output_tokens,
                temperature=setting.temperature,
                top_p=setting.top_p,
                tag=f"{key.prompt_id}/{key.setting}/{key.repeat}",
            )
            response = self._model.complete(request)
            self._journal.append(
                JournalRow(
                    key,
                    response.usage.input_tokens,
                    response.usage.output_tokens,
                    response.stop_reason,
                    response.latency_seconds,
                    response.text,
                )
            )
            made += 1
            _log.info(
                "call journaled",
                extra={
                    "fields": {
                        "tag": request.tag,
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                        "stop": response.stop_reason.value,
                    }
                },
            )
            if plan.throttle_seconds:
                self._sleep(plan.throttle_seconds)
        return RunSummary(estimate, made, skipped, interrupted=False)

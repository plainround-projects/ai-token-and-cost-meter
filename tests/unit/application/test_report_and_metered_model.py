import logging
from datetime import date
from decimal import Decimal

from tests.conftest import MemoryJournal, ScriptedModel, prompt, row
from token_meter.application.metered_model import MeteredChatModel
from token_meter.application.report import build_report
from token_meter.domain.estimation import TokenEstimator
from token_meter.domain.llm import ChatMessage, ChatRequest
from token_meter.domain.pricing import PriceTable
from token_meter.domain.prompts import Kind

PRICES = PriceTable("m", Decimal("0.001"), Decimal("0.002"), date(2026, 10, 26))


def test_the_report_finds_the_overhead_and_shows_the_error_shrink():
    prompts = [
        prompt("s", Kind.SHORT, "a" * 40),
        prompt("s2", Kind.SHORT, "a" * 80),
        prompt("l", Kind.LONG, "a" * 400),
    ]
    rows = [
        row(p, s, r, tokens + 28, 10)
        for p, tokens in (("s", 10), ("s2", 20), ("l", 100))
        for s in ("t0", "t07")
        for r in range(2)
    ]
    report = build_report(MemoryJournal(rows), prompts, PRICES, TokenEstimator(), max_output_tokens=200)
    assert report.calls == 12
    assert report.overhead == 28
    assert report.naive.total.error < -0.2
    assert abs(report.with_overhead.total.error) < 0.01
    assert abs(report.forecast.total.error) < 0.05
    assert report.ratios == {"short": 4.0, "long": 4.0}
    assert report.cost_check.within


def test_the_metered_model_logs_estimate_and_bill_without_the_prompt_text(caplog):
    inner = ScriptedModel(lambda request: ("answer text", 40, 5))
    metered = MeteredChatModel(inner, TokenEstimator(per_call_overhead=28))
    request = ChatRequest((ChatMessage.user("secret customer words " * 2),), max_output_tokens=20, tag="t1")
    with caplog.at_level(logging.INFO):
        response = metered.complete(request)
    assert response.text == "answer text"
    assert metered.name == "scripted"
    assert metered.supports_sampling
    record = next(r for r in caplog.records if r.getMessage() == "estimate against bill")
    assert record.fields["billed_input"] == 40
    assert record.fields["estimated_input"] == 11 + 28
    assert "secret" not in caplog.text


def test_a_zero_billed_input_does_not_divide_by_zero(caplog):
    metered = MeteredChatModel(ScriptedModel(lambda request: ("x", 0, 0)), TokenEstimator())
    with caplog.at_level(logging.INFO):
        metered.complete(ChatRequest((ChatMessage.user("hi"),)))
    assert caplog.records[-1].fields["error"] == "+0.0%"

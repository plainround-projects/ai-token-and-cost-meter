import io
import logging
import random
import signal

import pytest

from token_meter.domain.errors import PermanentModelError, TransientModelError
from token_meter.domain.llm import ChatMessage, ChatRequest, ChatResponse, StopReason, Usage
from token_meter.infrastructure.clock import SystemClock
from token_meter.infrastructure.env import ConfigurationError
from token_meter.infrastructure.logging import configure_logging, fields
from token_meter.infrastructure.model_factory import ModelSettings, build_chat_model
from token_meter.infrastructure.recording import RecordedChatModel, RecordingChatModel
from token_meter.infrastructure.resilient import RetryingChatModel
from token_meter.infrastructure.retry import retry
from token_meter.infrastructure.shutdown import ShutdownSignal

REQUEST = ChatRequest((ChatMessage.user("hi"),), tag="r")


class Flaky:
    name = "flaky"
    supports_sampling = True

    def __init__(self, failures, error=TransientModelError):
        self.calls = 0
        self._failures = failures
        self._error = error

    def complete(self, request):
        self.calls += 1
        if self.calls <= self._failures:
            raise self._error("boom")
        return ChatResponse("ok", StopReason.END, Usage(1, 1), 0.1, "flaky")


def test_a_transient_failure_is_retried_with_backoff_and_then_succeeds():
    pauses: list[float] = []
    flaky = Flaky(2)
    model = RetryingChatModel(flaky, attempts=3, base_delay_seconds=1.0, sleep=pauses.append, rng=random.Random(1))
    assert model.complete(REQUEST).text == "ok"
    assert flaky.calls == 3
    assert 0.5 <= pauses[0] <= 1.0
    assert 1.0 <= pauses[1] <= 2.0
    assert model.name == "flaky"
    assert model.supports_sampling


def test_the_last_transient_failure_is_raised_after_the_attempts_run_out():
    flaky = Flaky(9)
    with pytest.raises(TransientModelError):
        RetryingChatModel(flaky, attempts=2, sleep=lambda s: None).complete(REQUEST)
    assert flaky.calls == 2


def test_a_permanent_failure_is_not_retried():
    flaky = Flaky(9, PermanentModelError)
    with pytest.raises(PermanentModelError):
        RetryingChatModel(flaky, attempts=5, sleep=lambda s: None).complete(REQUEST)
    assert flaky.calls == 1


def test_retry_needs_at_least_one_attempt_and_caps_the_delay():
    with pytest.raises(ValueError, match=r"at least 1"):
        retry(lambda: 1, attempts=0, base_delay_seconds=1, retry_on=(ValueError,))
    pauses: list[float] = []

    def fail() -> int:
        raise ValueError

    with pytest.raises(ValueError, match=r"^$"):
        retry(fail, attempts=6, base_delay_seconds=4, retry_on=(ValueError,), sleep=pauses.append, max_delay_seconds=5)
    assert max(pauses) <= 5


def test_log_lines_are_logfmt_with_fields_and_quote_spaces():
    stream = io.StringIO()
    configure_logging("INFO", stream)
    logging.getLogger("t").info("two words", extra=fields(count=3, note="a b", empty=""))
    line = stream.getvalue().strip()
    assert 'msg="two words"' in line
    assert "count=3" in line
    assert 'note="a b"' in line
    assert 'empty=""' in line
    assert line.startswith("ts=")


def test_an_exception_is_logged_on_the_same_line():
    stream = io.StringIO()
    configure_logging("INFO", stream)
    try:
        raise RuntimeError("bad")
    except RuntimeError:
        logging.getLogger("t").exception("failed")
    assert "exc=" in stream.getvalue()


def test_shutdown_flag_is_set_by_a_request_and_by_a_signal():
    shutdown = ShutdownSignal()
    assert not shutdown.requested
    shutdown.install()
    signal.raise_signal(signal.SIGTERM)
    assert shutdown.requested
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.default_int_handler)
    other = ShutdownSignal()
    other.request()
    assert other.requested


def test_the_system_clock_moves_forward():
    clock = SystemClock()
    assert clock.monotonic() <= clock.monotonic()
    assert clock.now().date() == clock.today()


def test_the_default_provider_is_the_recorded_model(tmp_path):
    settings = ModelSettings.from_env({"RECORDINGS_PATH": str(tmp_path)})
    assert isinstance(build_chat_model(settings, SystemClock(), {}), RecordedChatModel)


def test_the_local_provider_builds_a_retrying_openai_compatible_model():
    settings = ModelSettings.from_env({"MODEL_PROVIDER": "openai-compatible"})
    model = build_chat_model(settings, SystemClock(), {})
    assert isinstance(model, RetryingChatModel)
    assert model.name == "qwen2.5:0.5b"
    assert settings.openai_base_url == "http://localhost:11434/v1"


def test_record_mode_wraps_a_live_model_in_a_recorder(tmp_path):
    settings = ModelSettings.from_env(
        {"MODEL_PROVIDER": "openai-compatible", "RECORD": "on", "RECORDINGS_PATH": str(tmp_path / "r.jsonl")}
    )
    assert isinstance(build_chat_model(settings, SystemClock(), {}), RecordingChatModel)


def test_the_anthropic_provider_refuses_to_start_without_a_key_in_the_environment():
    settings = ModelSettings.from_env({"MODEL_PROVIDER": "anthropic"})
    assert settings.model == "claude-haiku-5-5"
    with pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY"):
        build_chat_model(settings, SystemClock(), {})


def test_the_anthropic_provider_builds_when_a_key_is_present():
    settings = ModelSettings.from_env({"MODEL_PROVIDER": "anthropic", "ANTHROPIC_THINKING": "omit"})
    model = build_chat_model(settings, SystemClock(), {"ANTHROPIC_API_KEY": "present-but-not-real"})
    assert isinstance(model, RetryingChatModel)
    assert not model.supports_sampling


@pytest.mark.parametrize(
    "environ",
    [
        {"MODEL_PROVIDER": "carrier-pigeon"},
        {"RECORD": "maybe"},
        {"MODEL_ATTEMPTS": "0"},
        {"MODEL_TIMEOUT_SECONDS": "0"},
    ],
)
def test_bad_model_settings_name_the_variable(environ):
    with pytest.raises(ConfigurationError, match=next(iter(environ))):
        ModelSettings.from_env(environ)


def test_info_logs_of_a_failed_call_never_carry_the_prompt_text(caplog):
    flaky = Flaky(1)
    secret = ChatRequest((ChatMessage.user("my card number is 4111"),), tag="p1/t0/0")
    with caplog.at_level(logging.INFO):
        RetryingChatModel(flaky, attempts=2, sleep=lambda s: None).complete(secret)
    assert caplog.records
    assert "4111" not in caplog.text
    assert "4111" not in " ".join(str(r.__dict__.get("fields", "")) for r in caplog.records)

from datetime import date
from decimal import Decimal

import pytest

from token_meter.domain.prompts import InvalidPromptSet, Kind
from token_meter.infrastructure import env
from token_meter.infrastructure.env import ConfigurationError
from token_meter.infrastructure.files import load_prices, load_prompts
from token_meter.infrastructure.settings import MeterSettings


def test_prompts_are_read_one_per_line(tmp_path):
    path = tmp_path / "p.jsonl"
    path.write_text('{"id":"a","kind":"short","text":"hi"}\n\n{"id":"b","kind":"long","text":"yo"}\n')
    assert [(p.id, p.kind) for p in load_prompts(path)] == [("a", Kind.SHORT), ("b", Kind.LONG)]


def test_one_bad_line_fails_with_its_line_number_and_not_the_whole_file(tmp_path):
    path = tmp_path / "p.jsonl"
    path.write_text('{"id":"a","kind":"short","text":"hi"}\n{"id":"b","kind":"long",}\n')
    with pytest.raises(InvalidPromptSet, match=r"p\.jsonl:2: not valid JSON"):
        load_prompts(path)
    path.write_text('{"id":"a","kind":"short","text":"hi"}\n{"id":"b","kind":"nope","text":"x"}\n')
    with pytest.raises(InvalidPromptSet, match=r"p\.jsonl:2: field 'kind'"):
        load_prompts(path)


def test_prices_carry_a_real_date_field(tmp_path):
    path = tmp_path / "prices.json"
    path.write_text('{"model":"m","input_per_1k":"0.0001","output_per_1k":"0.0005","read_date":"2026-10-26"}')
    prices = load_prices(path)
    assert prices.read_date == date(2026, 10, 26)
    assert prices.input_per_1k == Decimal("0.0001")


def test_a_price_file_without_a_date_is_rejected(tmp_path):
    path = tmp_path / "prices.json"
    path.write_text('{"model":"m","input_per_1k":"0.0001","output_per_1k":"0.0005"}')
    with pytest.raises(ValueError, match="read_date"):
        load_prices(path)


def test_settings_default_to_the_lesson_values():
    settings = MeterSettings.from_env({})
    assert (settings.max_output_tokens, settings.repeats, settings.price_max_age_days) == (200, 3, 30)
    assert settings.budget is None
    assert settings.throttle_seconds == 0.0


def test_settings_read_the_environment():
    settings = MeterSettings.from_env(
        {"BUDGET_USD": "0.25", "REPEATS": "2", "THROTTLE_SECONDS": "0.5", "LOG_LEVEL": "debug"}
    )
    assert settings.budget == Decimal("0.25")
    assert settings.repeats == 2
    assert settings.throttle_seconds == 0.5


@pytest.mark.parametrize(
    ("environ", "fragment"),
    [
        ({"BUDGET_USD": "cheap"}, "BUDGET_USD"),
        ({"REPEATS": "0"}, "REPEATS"),
        ({"MAX_OUTPUT_TOKENS": "many"}, "MAX_OUTPUT_TOKENS"),
        ({"THROTTLE_SECONDS": "-1"}, "THROTTLE_SECONDS"),
        ({"LOG_LEVEL": "LOUD"}, "LOG_LEVEL"),
        ({"PROMPTS_PATH": "  "}, "PROMPTS_PATH"),
    ],
)
def test_bad_settings_name_the_variable(environ, fragment):
    with pytest.raises(ConfigurationError, match=fragment):
        MeterSettings.from_env(environ)


def test_the_env_helpers_validate_numbers():
    assert env.non_negative_int({"A": "0"}, "A", 5) == 0
    assert env.positive_float({"A": "1.5"}, "A", 1) == 1.5
    with pytest.raises(ConfigurationError):
        env.non_negative_int({"A": "-1"}, "A", 5)
    with pytest.raises(ConfigurationError):
        env.positive_float({"A": "0"}, "A", 1)
    with pytest.raises(ConfigurationError):
        env.positive_float({"A": "x"}, "A", 1)
    with pytest.raises(ConfigurationError):
        env.non_negative_float({"A": "x"}, "A", 1)
    assert env.optional_text({"A": " "}, "A") is None

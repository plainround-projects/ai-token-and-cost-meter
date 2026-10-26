import pytest

from tests.conftest import prompt
from token_meter.domain.prompts import InvalidPromptSet, Kind, PromptSetSpec, parse_prompt, validate_prompt_set


def small_spec(long_tokens: int = 10) -> PromptSetSpec:
    return PromptSetSpec({Kind.SHORT: 1, Kind.LONG: 1, Kind.LABEL: 1}, long_threshold_tokens=long_tokens)


def valid_set():
    return [
        prompt("a", Kind.SHORT, "hi"),
        prompt("b", Kind.LONG, "x" * 400),
        prompt("c", Kind.LABEL, "classify", "billing"),
    ]


def test_a_set_that_matches_the_spec_is_accepted():
    validate_prompt_set(valid_set(), small_spec())


def test_the_lesson_spec_asks_for_fifty_prompts_in_five_kinds():
    assert sum(PromptSetSpec.lesson().counts.values()) == 50


def test_repeated_ids_are_rejected_by_name():
    items = [*valid_set(), prompt("a", Kind.SHORT, "again")]
    with pytest.raises(InvalidPromptSet, match=r"repeated: \['a'\]"):
        validate_prompt_set(items, small_spec())


def test_a_wrong_total_is_rejected():
    with pytest.raises(InvalidPromptSet, match="expected 3 prompts, found 2"):
        validate_prompt_set(valid_set()[:2], small_spec())


def test_a_wrong_count_for_one_kind_is_rejected():
    items = [prompt("a", Kind.SHORT, "hi"), prompt("b", Kind.SHORT, "x" * 400), prompt("c", Kind.LABEL, "c", "other")]
    with pytest.raises(InvalidPromptSet, match="kind short"):
        validate_prompt_set(items, small_spec())


def test_a_set_with_no_long_prompt_is_rejected():
    with pytest.raises(InvalidPromptSet, match="over 1000 tokens"):
        validate_prompt_set(valid_set(), small_spec(long_tokens=1000))


@pytest.mark.parametrize("field", ["id", "kind", "text"])
def test_a_row_missing_a_field_names_the_field(field):
    row = {"id": "a", "kind": "short", "text": "hi"}
    del row[field]
    with pytest.raises(InvalidPromptSet, match=f"field '{field}'"):
        parse_prompt(row)


def test_an_unknown_kind_is_rejected():
    with pytest.raises(InvalidPromptSet, match="field 'kind'"):
        parse_prompt({"id": "a", "kind": "huge", "text": "hi"})


def test_a_label_prompt_needs_an_allowed_expected_label():
    with pytest.raises(InvalidPromptSet, match="expected_label"):
        parse_prompt({"id": "a", "kind": "label", "text": "hi", "expected_label": "spam"})
    assert (
        parse_prompt({"id": "a", "kind": "label", "text": "hi", "expected_label": "billing"}).expected_label
        == "billing"
    )


def test_only_label_prompts_keep_an_expected_label():
    assert parse_prompt({"id": "a", "kind": "short", "text": "hi", "expected_label": "billing"}).expected_label is None

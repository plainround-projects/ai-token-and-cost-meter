"""The prompt set: 50 customer messages in five kinds, and the rules that make it a fair sample."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from token_meter.domain.errors import DomainError

LABELS = ("billing", "shipping", "account", "other")


class InvalidPromptSet(DomainError):
    """The prompt file breaks a rule of the lesson (row count, kinds, a long prompt, unique ids)."""


class Kind(StrEnum):
    """What a prompt is for; the report breaks every number out by kind."""

    SHORT = "short"
    LONG = "long"
    CODE = "code"
    LANGUAGE = "language"
    LABEL = "label"


@dataclass(frozen=True, slots=True)
class PromptRecord:
    """One prompt. `expected_label` is set only for label prompts."""

    id: str
    kind: Kind
    text: str
    expected_label: str | None = None


@dataclass(frozen=True, slots=True)
class PromptSetSpec:
    """The shape the lesson asks for: counts per kind and one prompt over a token threshold."""

    counts: Mapping[Kind, int]
    long_threshold_tokens: int = 1500
    chars_per_token: int = 4

    @classmethod
    def lesson(cls) -> PromptSetSpec:
        return cls({Kind.SHORT: 20, Kind.LONG: 15, Kind.CODE: 5, Kind.LANGUAGE: 5, Kind.LABEL: 5})


def parse_prompt(row: Mapping[str, Any]) -> PromptRecord:
    """Build a record from one decoded JSON Lines row, naming the field that is wrong."""
    for name in ("id", "kind", "text"):
        if not isinstance(row.get(name), str) or not row[name].strip():
            raise InvalidPromptSet(f"field {name!r} must be a non-empty string, got {row.get(name)!r}")
    try:
        kind = Kind(row["kind"])
    except ValueError as error:
        raise InvalidPromptSet(f"field 'kind' must be one of {[k.value for k in Kind]}, got {row['kind']!r}") from error
    label = row.get("expected_label")
    if kind is Kind.LABEL and label not in LABELS:
        raise InvalidPromptSet(f"field 'expected_label' of {row['id']} must be one of {LABELS}, got {label!r}")
    return PromptRecord(row["id"], kind, row["text"], label if kind is Kind.LABEL else None)


def validate_prompt_set(prompts: Iterable[PromptRecord], spec: PromptSetSpec) -> None:
    """Check the whole set against the spec; raises `InvalidPromptSet` naming the first rule broken."""
    items = list(prompts)
    ids = Counter(p.id for p in items)
    repeated = sorted(i for i, n in ids.items() if n > 1)
    if repeated:
        raise InvalidPromptSet(f"prompt ids must be unique, repeated: {repeated}")
    total = sum(spec.counts.values())
    if len(items) != total:
        raise InvalidPromptSet(f"expected {total} prompts, found {len(items)}")
    by_kind = Counter(p.kind for p in items)
    for kind, wanted in spec.counts.items():
        if by_kind[kind] != wanted:
            raise InvalidPromptSet(f"expected {wanted} prompts of kind {kind.value}, found {by_kind[kind]}")
    longest = max(len(p.text) for p in items) // spec.chars_per_token
    if longest <= spec.long_threshold_tokens:
        raise InvalidPromptSet(
            f"at least one prompt must be over {spec.long_threshold_tokens} tokens; the longest is about {longest}"
        )

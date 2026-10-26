"""Compare estimates with the bill, calibrate the estimator and measure the spread between answers."""

from __future__ import annotations

import re
import statistics
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

from token_meter.domain.errors import DomainError
from token_meter.domain.estimation import TokenEstimator
from token_meter.domain.journal import JournalRow
from token_meter.domain.llm import StopReason
from token_meter.domain.pricing import PriceTable
from token_meter.domain.prompts import LABELS, Kind, PromptRecord

_WORD = re.compile(r"[a-z]+")


class NotEnoughData(DomainError):
    """The journal does not hold the rows the analysis needs."""


@dataclass(frozen=True, slots=True)
class KindError:
    """Estimated against billed input tokens for one kind of prompt. `error` is (estimated - billed) / billed."""

    kind: str
    estimated: int
    billed: int

    @property
    def error(self) -> float:
        return (self.estimated - self.billed) / self.billed if self.billed else 0.0


@dataclass(frozen=True, slots=True)
class PromptGap:
    """The prompt whose estimate is furthest from the bill, with the cause the numbers point to."""

    prompt_id: str
    kind: Kind
    estimated: int
    billed: int
    cause: str


@dataclass(frozen=True, slots=True)
class EstimateReport:
    """Input-token error by kind and in total, and the largest single gap."""

    by_kind: tuple[KindError, ...]
    total: KindError
    largest_gap: PromptGap


def _first_repeat_rows(rows: Sequence[JournalRow], setting: str) -> dict[str, JournalRow]:
    chosen: dict[str, JournalRow] = {}
    for row in rows:
        if row.key.setting == setting and row.key.repeat == 0:
            chosen[row.key.prompt_id] = row
    return chosen


def explain_gap(kind: Kind, estimated: int, billed: int, missing_overhead: int) -> str:
    """Name the cause of a gap from its size.

    `missing_overhead` is the fixed per-call cost the estimate does not include yet (zero once it does).
    """
    shortfall = billed - estimated
    if missing_overhead and shortfall <= missing_overhead * 1.25 + 8:
        return "fixed chat-template overhead per call, which dominates short prompts"
    if shortfall < 0:
        return "the estimate is above the bill: this text tokenizes more compactly than the rule assumes"
    if kind is Kind.LANGUAGE:
        return "non-English text splits into more tokens per character than the characters-per-token rule assumes"
    if kind is Kind.CODE:
        return "code, JSON and symbols split into more tokens per character than prose does"
    if kind in (Kind.SHORT, Kind.LABEL):
        return "rounding of the characters-per-token rule on very short text"
    return "text that tokenizes less compactly than the characters-per-token rule assumes"


def _report(
    prompts: Sequence[PromptRecord], billed_rows: Mapping[str, JournalRow], estimates: Mapping[str, int], missing: int
) -> EstimateReport:
    totals: dict[Kind, list[int]] = defaultdict(lambda: [0, 0])
    gaps: list[PromptGap] = []
    for prompt in prompts:
        row = billed_rows.get(prompt.id)
        if row is None:
            continue
        estimated = estimates[prompt.id]
        totals[prompt.kind][0] += estimated
        totals[prompt.kind][1] += row.input_tokens
        cause = explain_gap(prompt.kind, estimated, row.input_tokens, missing)
        gaps.append(PromptGap(prompt.id, prompt.kind, estimated, row.input_tokens, cause))
    by_kind = tuple(KindError(kind.value, est, bill) for kind, (est, bill) in totals.items())
    total = KindError("total", sum(k.estimated for k in by_kind), sum(k.billed for k in by_kind))
    worst = max(gaps, key=lambda g: abs(g.billed - g.estimated) / g.billed)
    return EstimateReport(by_kind, total, worst)


def compare_estimates(
    prompts: Sequence[PromptRecord],
    rows: Sequence[JournalRow],
    estimator: TokenEstimator,
    setting: str = "t0",
    known_overhead: int = 0,
) -> EstimateReport:
    """Join estimates to billed input tokens (one row per prompt at `setting`) and group by kind.

    `known_overhead` is the measured per-call overhead; it lets the report explain a gap that the estimator,
    which does not include the overhead yet, leaves open.
    """
    billed_rows = _first_repeat_rows(rows, setting)
    if not billed_rows:
        raise NotEnoughData(f"no rows for setting {setting!r} in the journal")
    estimates = {p.id: estimator.tokens(p.text, kind=p.kind) for p in prompts}
    return _report(prompts, billed_rows, estimates, 0 if estimator.per_call_overhead else known_overhead)


def calibrate_overhead(
    prompts: Sequence[PromptRecord], rows: Sequence[JournalRow], base: TokenEstimator, setting: str = "t0"
) -> int:
    """The median of billed minus estimated input tokens: the fixed cost every call carries."""
    billed_rows = _first_repeat_rows(rows, setting)
    residuals = [
        billed_rows[p.id].input_tokens - base.with_overhead(0).tokens(p.text, kind=p.kind)
        for p in prompts
        if p.id in billed_rows
    ]
    if not residuals:
        raise NotEnoughData(f"no rows for setting {setting!r} in the journal")
    return round(statistics.median(residuals))


@dataclass(frozen=True, slots=True)
class Calibration:
    """What a pilot taught the estimator: overhead, a density per kind, and answer length per kind and setting."""

    estimator: TokenEstimator
    mean_output: Mapping[tuple[Kind, str], float]


def calibrate(
    prompts: Sequence[PromptRecord], rows: Sequence[JournalRow], base: TokenEstimator, setting: str = "t0"
) -> Calibration:
    """Measure the overhead, the characters per token of each kind and the mean answer length per kind and setting."""
    overhead = calibrate_overhead(prompts, rows, base, setting)
    billed_rows = _first_repeat_rows(rows, setting)
    chars: dict[Kind, int] = defaultdict(int)
    tokens: dict[Kind, int] = defaultdict(int)
    for prompt in prompts:
        if prompt.id in billed_rows:
            chars[prompt.kind] += len(prompt.text)
            tokens[prompt.kind] += max(1, billed_rows[prompt.id].input_tokens - overhead)
    kind_of = {p.id: p.kind for p in prompts}
    outputs: dict[tuple[Kind, str], list[int]] = defaultdict(list)
    for row in rows:
        if row.key.prompt_id in kind_of:
            outputs[(kind_of[row.key.prompt_id], row.key.setting)].append(row.output_tokens)
    estimator = base.with_overhead(overhead).with_ratios({kind: chars[kind] / tokens[kind] for kind in chars})
    return Calibration(estimator, {key: statistics.fmean(values) for key, values in outputs.items()})


@dataclass(frozen=True, slots=True)
class CostCheck:
    """A calibrated cost estimate against the bill, made without the answer it is judged on."""

    calls: int
    estimated: Decimal
    billed: Decimal
    ceiling: Decimal

    @property
    def error(self) -> float:
        return float((self.estimated - self.billed) / self.billed) if self.billed else 0.0

    @property
    def within(self) -> bool:
        return abs(self.error) <= 0.05


@dataclass(frozen=True, slots=True)
class LeaveOneOut:
    """Each prompt estimated by an estimator calibrated on the other prompts: input tokens by kind, and cost."""

    input_tokens: EstimateReport
    cost: CostCheck


def _expected_output(calibration: Calibration, kind: Kind, setting: str) -> float:
    """Mean answer length for the kind and setting; the setting's mean over all kinds if the kind was never seen."""
    known = calibration.mean_output.get((kind, setting))
    if known is not None:
        return known
    same_setting = [v for (_, name), v in calibration.mean_output.items() if name == setting]
    return statistics.fmean(same_setting) if same_setting else 0.0


def leave_one_out(
    prompts: Sequence[PromptRecord],
    rows: Sequence[JournalRow],
    base: TokenEstimator,
    prices: PriceTable,
    max_output_tokens: int,
    setting: str = "t0",
) -> LeaveOneOut:
    """Estimate every prompt with an estimator that never saw it, so the error is an honest forecast error.

    Input uses the calibrated overhead and the density of the prompt's kind. Output uses the mean billed answer
    length of the same kind and setting. `ceiling` assumes every call fills the output cap, which is all the
    pre-run estimate can assume.
    """
    if len(prompts) < 2:
        raise NotEnoughData("leave-one-out needs at least two prompts")
    billed_rows = _first_repeat_rows(rows, setting)
    by_prompt: dict[str, list[JournalRow]] = defaultdict(list)
    for row in rows:
        by_prompt[row.key.prompt_id].append(row)
    estimates: dict[str, int] = {}
    estimated = billed = ceiling = Decimal(0)
    calls = 0
    for prompt in prompts:
        if prompt.id not in by_prompt:
            continue
        calibration = calibrate([q for q in prompts if q.id != prompt.id], rows, base, setting)
        input_estimate = calibration.estimator.tokens(prompt.text, kind=prompt.kind)
        estimates[prompt.id] = input_estimate
        for row in by_prompt[prompt.id]:
            calls += 1
            expected_output = _expected_output(calibration, prompt.kind, row.key.setting)
            estimated += prices.cost(input_estimate, round(expected_output))
            ceiling += prices.cost(input_estimate, max_output_tokens)
            billed += prices.cost(row.input_tokens, row.output_tokens)
    covered = [p for p in prompts if p.id in estimates]
    return LeaveOneOut(_report(covered, billed_rows, estimates, 0), CostCheck(calls, estimated, billed, ceiling))


@dataclass(frozen=True, slots=True)
class SettingSpread:
    """How much answers vary at one decoding setting, and what that costs."""

    setting: str
    mean_distinct_answers: float
    label_agreement: float | None
    mean_output_tokens: float
    cost_per_1000: Decimal
    length_stop_share: float


@dataclass(frozen=True, slots=True)
class SpreadReport:
    """One row per setting, and whether the first setting (temperature 0) repeated itself exactly."""

    settings: tuple[SettingSpread, ...]
    zero_temperature_identical: bool


def extract_label(answer: str) -> str:
    """The first category word in an answer, or `none` when it names no category."""
    for match in _WORD.finditer(answer.lower()):
        if match.group() in LABELS:
            return match.group()
    return "none"


def measure_spread(prompts: Sequence[PromptRecord], rows: Sequence[JournalRow], prices: PriceTable) -> SpreadReport:
    """Count distinct answers per prompt and setting, label agreement, output length and cost per 1,000 calls."""
    label_ids = {p.id for p in prompts if p.kind is Kind.LABEL}
    grouped: dict[str, dict[str, list[JournalRow]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[row.key.setting][row.key.prompt_id].append(row)
    if not grouped:
        raise NotEnoughData("the journal is empty")
    spreads: list[SettingSpread] = []
    for setting, by_prompt in grouped.items():
        distinct = [len({r.text.strip() for r in group}) for group in by_prompt.values()]
        agreements = []
        for prompt_id in label_ids & by_prompt.keys():
            labels = Counter(extract_label(r.text) for r in by_prompt[prompt_id])
            agreements.append(labels.most_common(1)[0][1] / sum(labels.values()))
        all_rows = [r for group in by_prompt.values() for r in group]
        costs = [prices.cost(r.input_tokens, r.output_tokens) for r in all_rows]
        spreads.append(
            SettingSpread(
                setting,
                statistics.fmean(distinct),
                statistics.fmean(agreements) if agreements else None,
                statistics.fmean(r.output_tokens for r in all_rows),
                (sum(costs, Decimal(0)) / len(costs)) * 1000,
                sum(r.stop_reason is StopReason.LENGTH for r in all_rows) / len(all_rows),
            )
        )
    zero = next((s for s in spreads if s.setting == "t0"), None)
    return SpreadReport(tuple(spreads), zero is not None and zero.mean_distinct_answers == 1.0)

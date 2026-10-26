"""Plain-text rendering of the estimate and the report (what the commands print)."""

from __future__ import annotations

from token_meter.application.report import MeterReport
from token_meter.domain.analysis import EstimateReport
from token_meter.domain.estimation import RunEstimate


def render_estimate(estimate: RunEstimate) -> str:
    """The line printed before the first call."""
    return (
        f"Estimate before calling: calls={estimate.calls} input_tokens_est={estimate.input_tokens} "
        f"output_tokens_est={estimate.output_tokens} cost_est=${estimate.cost:.4f}"
    )


def _by_kind(title: str, report: EstimateReport) -> list[str]:
    lines = [f"--- {title} ---"]
    lines += [f"{k.kind:<9} est={k.estimated:>6} billed={k.billed:>6} error={k.error:+.1%}" for k in report.by_kind]
    lines.append(
        f"total     est={report.total.estimated:>6} billed={report.total.billed:>6} error={report.total.error:+.1%}"
    )
    gap = report.largest_gap
    lines.append(
        f"largest gap: {gap.prompt_id} ({gap.kind.value}) est={gap.estimated} billed={gap.billed}; cause: {gap.cause}"
    )
    return lines


def render_report(report: MeterReport) -> str:
    """The report: input-token error by kind at three stages, the cost check and the spread per setting."""
    lines = [f"calls in journal: {report.calls}   total billed cost: ${report.billed_cost_total}", ""]
    lines += _by_kind("1. estimate vs billed input tokens, by kind (t0 only), chars/4 only", report.naive)
    lines += ["", f"measured template overhead: {report.overhead} tokens per call (median of billed - chars/4)", ""]
    lines += _by_kind(f"2. same, with the measured overhead (chars/4 + {report.overhead})", report.with_overhead)
    ratios = ", ".join(f"{kind} {ratio}" for kind, ratio in report.ratios.items())
    lines += ["", f"measured characters per token (all prompts): {ratios}", ""]
    lines += _by_kind("3. leave-one-out: each prompt estimated by an estimator fitted on the others", report.forecast)
    check = report.cost_check
    verdict = "within 5%" if check.within else "NOT within 5%"
    lines += [
        "",
        f"--- cost of all {check.calls} calls, each forecast without its own prompt's data ---",
        f"estimated=${check.estimated:.6f} billed=${check.billed:.6f} error={check.error:+.1%} ({verdict});"
        f" ceiling with every call at the output cap=${check.ceiling:.6f}",
        "",
        "--- spread per setting ---",
        "setting  mean_distinct_answers  label_agreement  mean_output_tokens  length_stops  cost_per_1000_requests",
    ]
    for s in report.spread.settings:
        agreement = "n/a" if s.label_agreement is None else f"{s.label_agreement:.2f}"
        lines.append(
            f"{s.setting:<8} {s.mean_distinct_answers:>21.2f}  {agreement:>15}  {s.mean_output_tokens:>18.1f}"
            f"  {s.length_stop_share:>11.0%}  ${s.cost_per_1000:>21.4f}"
        )
    lines.append("")
    lines.append(
        "temperature 0 gave identical answers on every repeat."
        if report.spread.zero_temperature_identical
        else "temperature 0 did NOT give identical answers on every repeat."
    )
    return "\n".join(lines)

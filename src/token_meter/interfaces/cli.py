"""The `meter` command: estimate, run, report."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation

from token_meter.application.ports import ChatModel
from token_meter.application.report import build_report
from token_meter.application.run_meter import RunMeter, RunPlan, estimate_pending
from token_meter.domain.decoding import DEFAULT_SETTINGS
from token_meter.domain.errors import DomainError, UnsupportedParameter
from token_meter.domain.estimation import BudgetExceeded, TokenEstimator, require_within_budget
from token_meter.domain.pricing import PriceTable, StalePrices
from token_meter.domain.prompts import InvalidPromptSet, PromptRecord, PromptSetSpec, validate_prompt_set
from token_meter.infrastructure.clock import SystemClock
from token_meter.infrastructure.csv_journal import CsvJournal
from token_meter.infrastructure.env import ConfigurationError
from token_meter.infrastructure.files import load_prices, load_prompts
from token_meter.infrastructure.logging import configure_logging
from token_meter.infrastructure.model_factory import ModelSettings, build_chat_model
from token_meter.infrastructure.settings import MeterSettings
from token_meter.infrastructure.shutdown import ShutdownSignal
from token_meter.interfaces.render import render_estimate, render_report

EXIT_OK, EXIT_ERROR, EXIT_CONFIG, EXIT_REFUSED, EXIT_INTERRUPTED = 0, 1, 2, 3, 4
_log = logging.getLogger("meter")


def build_parser() -> argparse.ArgumentParser:
    """The `meter` argument parser: estimate, run and report."""
    parser = argparse.ArgumentParser(
        prog="meter", description="Estimate, call, bill and compare a batch of model calls."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, helptext in (
        ("estimate", "print the estimate and stop"),
        ("run", "estimate, then make the missing calls"),
    ):
        command = sub.add_parser(name, help=helptext)
        command.add_argument("--budget", help="refuse to start if the estimate is above this many dollars")
        command.add_argument(
            "--allow-stale-prices", action="store_true", help="run with a price table past its age limit"
        )
        if name == "run":
            command.add_argument("--throttle", type=float, help="seconds to pause between calls")
    sub.add_parser("report", help="estimated against billed, cost per 1,000 requests and the spread per setting")
    return parser


def _load(settings: MeterSettings) -> tuple[list[PromptRecord], PriceTable]:
    prompts = load_prompts(settings.prompts_path)
    validate_prompt_set(prompts, PromptSetSpec.lesson())
    return prompts, load_prices(settings.prices_path)


def _budget(arg: str | None, settings: MeterSettings) -> Decimal | None:
    if arg is None:
        return settings.budget
    try:
        return Decimal(arg)
    except InvalidOperation as error:
        raise ConfigurationError(f"--budget must be a decimal number, got {arg!r}") from error


def run_command(
    args: argparse.Namespace, settings: MeterSettings, model: ChatModel | None, shutdown: ShutdownSignal
) -> int:
    """Print the estimate for the pending calls, then make them when a model is given."""
    prompts, prices = _load(settings)
    if not args.allow_stale_prices:
        prices.require_fresh(SystemClock().today(), settings.price_max_age_days)
    journal = CsvJournal(settings.journal_path)
    throttle = args.throttle if getattr(args, "throttle", None) is not None else settings.throttle_seconds
    plan = RunPlan(
        prompts,
        DEFAULT_SETTINGS,
        settings.repeats,
        settings.max_output_tokens,
        prices,
        TokenEstimator(),
        budget=_budget(args.budget, settings),
        throttle_seconds=throttle,
    )
    estimate = estimate_pending(plan, journal.done_keys())
    print(render_estimate(estimate), flush=True)
    if model is None:
        require_within_budget(estimate, plan.budget)
        return EXIT_OK
    summary = RunMeter(model, journal, stop_requested=lambda: shutdown.requested).run(plan)
    print(f"calls made now: {summary.calls_made}; skipped, already in the journal: {summary.calls_skipped}")
    print(f"journal: {settings.journal_path} ({len(journal.rows())} rows)")
    return EXIT_INTERRUPTED if summary.interrupted else EXIT_OK


def report_command(settings: MeterSettings) -> int:
    """Print the report for the journal."""
    prompts, prices = _load(settings)
    journal = CsvJournal(settings.journal_path)
    print(render_report(build_report(journal, prompts, prices, TokenEstimator(), settings.max_output_tokens)))
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point: returns the exit code (0 ok, 2 configuration, 3 refused, 4 interrupted)."""
    args = build_parser().parse_args(argv)
    try:
        settings = MeterSettings.from_env()
        configure_logging(settings.log_level)
        if args.command == "report":
            return report_command(settings)
        shutdown = ShutdownSignal()
        shutdown.install()
        model = None
        if args.command == "run":
            model = build_chat_model(ModelSettings.from_env(), SystemClock())
        return run_command(args, settings, model, shutdown)
    except (ConfigurationError, InvalidPromptSet, UnsupportedParameter) as error:
        print(f"meter: {error}", file=sys.stderr)
        return EXIT_CONFIG
    except (BudgetExceeded, StalePrices) as error:
        print(f"REFUSING TO START: {error}", file=sys.stderr)
        return EXIT_REFUSED
    except DomainError as error:
        print(f"meter: {error}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())

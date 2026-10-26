"""Readers for the prompt file (JSON Lines) and the price file (JSON)."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from token_meter.domain.pricing import PriceTable
from token_meter.domain.prompts import InvalidPromptSet, PromptRecord, parse_prompt


def load_prompts(path: Path) -> list[PromptRecord]:
    """Read one prompt per line. A bad line is reported with its line number; the rest of the file is not lost."""
    prompts: list[PromptRecord] = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                prompts.append(parse_prompt(json.loads(line)))
            except json.JSONDecodeError as error:
                raise InvalidPromptSet(f"{path}:{number}: not valid JSON ({error.msg})") from error
            except InvalidPromptSet as error:
                raise InvalidPromptSet(f"{path}:{number}: {error}") from error
    return prompts


def load_prices(path: Path) -> PriceTable:
    """Read the price file. `read_date` is a real field so a script can refuse stale prices."""
    data = json.loads(path.read_text(encoding="utf-8"))
    try:
        return PriceTable(
            model=str(data["model"]),
            input_per_1k=Decimal(str(data["input_per_1k"])),
            output_per_1k=Decimal(str(data["output_per_1k"])),
            read_date=date.fromisoformat(data["read_date"]),
        )
    except (KeyError, ValueError, InvalidOperation) as error:
        raise ValueError(
            f"{path}: price file needs model, input_per_1k, output_per_1k and an ISO read_date ({error!r})"
        ) from error

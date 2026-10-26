"""The real clock, behind the `Clock` port."""

from __future__ import annotations

import time
from datetime import UTC, date, datetime


class SystemClock:
    """Wall-clock and monotonic time from the operating system."""

    def monotonic(self) -> float:
        return time.monotonic()

    def today(self) -> date:
        return datetime.now(UTC).date()

    def now(self) -> datetime:
        return datetime.now(UTC)

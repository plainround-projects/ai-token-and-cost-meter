# 0003. Calibrate the estimator on a pilot, check it on the rest

Date: 2026-10-26. Status: accepted.

## Context

Characters divided by four undercounts every call by the chat template's fixed overhead, and the pre-run estimate has to assume the output cap because the answer length is not known yet. A check that calibrates and evaluates on the same rows proves nothing.

## Decision

- The pre-run estimate is `chars / 4` per prompt plus a per-call overhead (zero until measured) and the full output cap for every call. It is an upper bound for output cost on purpose.
- `calibrate_overhead` takes the median of billed minus estimated input tokens over the temperature-0 calls. The median ignores the language prompts, whose extra gap is a second, separate error.
- `check_calibrated_cost` calibrates mean output length per kind and setting on repeat 0 only, then estimates the cost of repeats 1 and 2 and compares it with the bill. The report states whether that is within 5%, and shows the ceiling estimate beside it.

## Consequences

- The report can say "the estimate was wrong by X percent and here is why" and "the corrected estimate is within Y percent on calls it never saw".
- Output length varies by setting, so a calibration that ignores the setting would miss; the held-out check would show it.

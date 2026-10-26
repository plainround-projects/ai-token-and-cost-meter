# 0004. One CSV row per call, fsynced, with a torn-tail rule

Date: 2026-10-26. Status: accepted.

## Context

A run of 450 calls costs money and time. A crash must cost at most the call in flight, and a restart must never pay for a call twice. The lesson's check is a real `kill -9`.

## Decision

The journal is a CSV file. The header is written once, when the file is created. Each call appends one row and calls `fsync` before the next call starts. On open, if the file does not end in a newline the half-written last line is cut off, because a row that was not finished was not paid for in the journal's eyes. A file whose header is wrong raises `JournalCorrupt` instead of being misread. The restart key is `(prompt_id, setting, repeat)`.

## Consequences

- A kill between the provider's answer and the append loses that one answer; the rerun asks again. That is the cheapest honest failure: it costs one call, never a duplicate.
- CSV keeps the file readable in a spreadsheet and diffable. A database would add a service the lesson does not need.

# Changelog

All notable changes to this project are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Drawn architecture and flow figures in `docs/diagrams/`, light and dark, shown in the README.

## [0.1.0] - 2026-10-26

### Added

- `meter estimate | run | report`: estimate the tokens and cost of 450 calls before the first one, refuse above a budget or on a stale price table, call a model at three decoding settings, journal one CSV row per call, and report estimated against billed.
- A restartable run: rows are appended and fsynced one at a time, a torn last line is cut off on open, and a rerun skips every finished call.
- The estimator calibrates its per-call template overhead from billed usage and checks the calibrated cost on rows the calibration never saw.
- A model port with a recorded adapter (replay and record), an OpenAI-compatible adapter for local open-weight models and a Claude adapter on the official SDK.
- The 50-prompt sample set, the dated price file and 450 recorded calls from `qwen2.5:0.5b`.
- Layered package (`domain`, `application`, `infrastructure`, `interfaces`) with the dependency rule enforced by import-linter, unit, subprocess and end-to-end tests, ruff, mypy, hash-pinned dependency locks and a CI workflow.

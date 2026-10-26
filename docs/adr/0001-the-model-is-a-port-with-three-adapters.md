# 0001. The model is a port with recorded, local and Claude adapters

Date: 2026-10-26. Status: accepted.

## Context

The meter measures what a provider bills. A test suite that needs a provider to run is slow, costs money and gives different numbers every day. A tool that can only talk to one vendor cannot compare a local model with a hosted one.

## Decision

`application.ports.ChatModel` is the only thing the use cases know. Three adapters implement it in `infrastructure`:

- `RecordedChatModel` replays answers stored as JSON Lines under `tests/fixtures/recordings/`, found by a hash of the request (messages, system prompt, cap, sampling, schema, tools and a `tag` such as `p01/t07/2`; never the model name). A request nobody recorded raises `RecordingMissing`. `RecordingChatModel` wraps a live model and writes the file, so `make record` refreshes the fixtures.
- `OpenAICompatibleChatModel` speaks `/chat/completions`, which ollama, llama.cpp and vLLM all serve. It is the adapter for the small open-weight model that produced the fixtures.
- `AnthropicChatModel` uses the official SDK and reads no key itself: `model_factory` refuses to build it unless `ANTHROPIC_API_KEY` is in the environment.

A decorator, `RetryingChatModel`, adds backoff with jitter for `TransientModelError` only. `domain` and `application` never import an SDK or an HTTP client; import-linter fails the build if they do.

## Consequences

- Every offline test and `make run` replay exactly the same 450 answers, so the report is the same on every machine.
- Adding a provider is one new adapter and one line in the factory.
- Recordings go stale when a prompt changes. The error says so and names the fix.

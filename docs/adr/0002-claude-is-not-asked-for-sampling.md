# 0002. The Claude adapter does not send temperature or top_p

Date: 2026-10-26. Status: accepted.

## Context

The lesson compares three decoding settings (temperature 0, 0.7, and 1.0 with top-p 0.9). From Messages API version 2026-10-21 the API answers a request that carries `temperature`, `top_p` or `top_k` with a 400 on every model, and the current Python SDK no longer accepts them as arguments.

## Decision

`AnthropicChatModel.supports_sampling` is `False` and `build_payload` raises `UnsupportedParameter` if a request sets either value. `RunMeter.run` checks `supports_sampling` before the first call and stops with a configuration error that says why, instead of running three identical "settings" and reporting a spread of zero. The three-setting experiment runs on the local open-weight model, which accepts sampling.

## Consequences

- Pointing the meter at Claude still works for estimating and billing a single default setting through the library (`MeteredChatModel`), but not for the decoding comparison.
- If the API ever accepts sampling again, flipping `supports_sampling` and passing the two values through is a three-line change plus a test.

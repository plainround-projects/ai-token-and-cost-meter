# Anthropic Python SDK (Claude)

## What it is

**Claude** is a family of large language models made by Anthropic. You use it by sending a **request** to the **Messages API**, a web service: a list of messages (what the user said, what the assistant said earlier), optional instructions (**system** prompt), a limit on the answer length (`max_tokens`), and optionally **tools** the model may ask you to run. The service replies with the model's message, a **stop reason** (why it stopped) and a **usage** block that says how many **tokens** it read and wrote. A *token* is a piece of text, roughly a short word or part of a word; models read and bill in tokens.

The **Anthropic Python SDK** (the `anthropic` package) is the official library for this API. It builds the request, sends it over HTTP, checks the answer and raises named errors.

## Why this repository uses it

The six repositories compare, measure and test model behavior. The default is a *recorded* model so that everything runs offline and gives the same numbers every time; a person with a key can switch to Claude with `MODEL_PROVIDER=anthropic`. Using the official SDK (and not hand-written HTTP) keeps authentication, headers and error classes correct. The SDK is wrapped in one adapter class so the rest of the program depends on a small neutral interface (`ChatModel`), and swapping providers is one line.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/token_meter/infrastructure/anthropic_chat.py` | the only file that imports `anthropic`: request mapping, the call, error mapping, token counting |
| `src/token_meter/infrastructure/model_factory.py` | creates the SDK client when `MODEL_PROVIDER=anthropic` |
| `tests/unit/infrastructure/test_anthropic_chat.py` | tests the adapter against a fake transport |
| `tests/live/` | opt-in tests that call the real API (`make test-live`) |
| `pyproject.toml` | `anthropic==2.3.0` |
| `env.example` | `ANTHROPIC_API_KEY`, `ANTHROPIC_THINKING`, `MODEL_NAME` |

## How it works underneath

**One request.** `client.messages.create(...)` sends `POST https://api.anthropic.com/v1/messages` with the key in the `x-api-key` header, the API version in `anthropic-version`, and the JSON body. The SDK uses `httpx2`, the sibling of the library in `httpx.md`, for the transport. The answer is JSON; the SDK turns it into a typed `Message` object whose `content` is a list of blocks (`text`, `tool_use`, ...).

**Tools.** The model never runs code. When it wants a tool it answers with a `tool_use` block (a name and a JSON `input`) and stops with `stop_reason = "tool_use"`. Your program runs the tool and sends the result back as a `tool_result` block in the next user turn. This back-and-forth is the *agent loop*.

**Errors.** `APIConnectionError` is raised when no answer arrived. `APIStatusError` (with subclasses for 400, 401, 403, 404, 429 and 5xx) is raised for an error status. The SDK's own automatic retries are switched off in this project.

**Tokens and cost.** Cost is `input_tokens * input price + output_tokens * output price`. The usage block is the authoritative count.

**Secrets.** The SDK reads the key from the environment. It is never stored in a file in the repository.

## Walkthrough of this repository's use

All Claude access is in one file, `src/token_meter/infrastructure/anthropic_chat.py`; nothing else imports `anthropic` (import-linter enforces this, see `import-linter.md`).

### Creating the client

`src/token_meter/infrastructure/model_factory.py`, lines 64 to 69:

```python
    if settings.provider == "anthropic":
        if not env.get("ANTHROPIC_API_KEY"):
            raise ConfigurationError("ANTHROPIC_API_KEY must be set in the environment to use the anthropic provider")
        client = anthropic.Anthropic(timeout=settings.timeout_seconds, max_retries=0)
        live = AnthropicChatModel(client, settings.model, clock, settings.anthropic_thinking)
    else:
```

`anthropic.Anthropic(...)` creates the SDK client. With no `api_key` argument it reads `ANTHROPIC_API_KEY` from the environment (the factory first checks that the variable is set and refuses with a clear message otherwise). `timeout` is the per-request limit in seconds. `max_retries=0` turns off the SDK's own retries, because this project retries in one place of its own (`RetryingChatModel`), which logs each retry and applies the budget.

### Mapping the neutral request to the Messages API

The domain has its own neutral message types (`ChatMessage`, `ChatRequest`; see `python.md`). This function maps them to the shapes the Claude API expects:

`src/token_meter/infrastructure/anthropic_chat.py`, lines 29 to 47:

```python
def _messages_payload(messages: tuple[ChatMessage, ...]) -> list[dict[str, Any]]:
    """Map neutral messages to Messages API turns; consecutive tool results share one user turn."""
    out: list[dict[str, Any]] = []
    for message in messages:
        if message.role is Role.TOOL:
            block = {"type": "tool_result", "tool_use_id": message.tool_call_id, "content": message.content}
            if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list):
                out[-1]["content"].append(block)
            else:
                out.append({"role": "user", "content": [block]})
        elif message.role is Role.ASSISTANT and message.tool_calls:
            blocks: list[dict[str, Any]] = [{"type": "text", "text": message.content}] if message.content else []
            blocks.extend(
                {"type": "tool_use", "id": c.id, "name": c.name, "input": dict(c.arguments)} for c in message.tool_calls
            )
            out.append({"role": "assistant", "content": blocks})
        else:
            out.append({"role": message.role.value, "content": message.content})
    return out
```

- A message from the user or assistant becomes `{"role": ..., "content": text}`.
- A **tool result** becomes a content block `{"type": "tool_result", "tool_use_id": ..., "content": ...}` inside a *user* turn; consecutive results are merged into one turn, because the API wants all results for one assistant turn together.
- An assistant message that asked for tools becomes a list of blocks: optional text, then one `{"type": "tool_use", "id", "name", "input"}` block per call.

### Building the request body

`src/token_meter/infrastructure/anthropic_chat.py`, lines 67 to 87:

```python
    def build_payload(self, request: ChatRequest) -> dict[str, Any]:
        """The keyword arguments for `messages.create` (public so tests can assert on them)."""
        if request.temperature is not None or request.top_p is not None:
            raise UnsupportedParameter("the Messages API rejects temperature and top_p; leave them unset")
        payload: dict[str, Any] = {
            "model": request.model or self._model,
            "max_tokens": request.max_output_tokens,
            "messages": _messages_payload(request.messages),
        }
        if request.system:
            payload["system"] = request.system
        if self._thinking != "omit":
            payload["thinking"] = {"type": self._thinking}
        if request.response_schema is not None:
            payload["output_config"] = {"format": {"type": "json_schema", "schema": dict(request.response_schema)}}
        if request.tools:
            payload["tools"] = [
                {"name": t.name, "description": t.description, "input_schema": dict(t.parameters)}
                for t in request.tools
            ]
        return payload
```

- It refuses `temperature` and `top_p` (the docstring at the top of the file explains that the Messages API of the pinned version rejects them), by raising `UnsupportedParameter` before anything is sent.
- `model` (the request's override or the adapter's default), `max_tokens` (the cap on the answer, required by the API) and `messages` are always sent.
- `system` (the instructions that come before the conversation) is sent only if there is one.
- `thinking` is sent unless the setting is `omit`; the setting `ANTHROPIC_THINKING` chooses `disabled` or `between_tools`.
- A JSON Schema for structured output goes in `output_config.format`.
- Tools go in `tools` as `{name, description, input_schema}`, where `input_schema` is a JSON Schema for the arguments.

### Calling the API

`src/token_meter/infrastructure/anthropic_chat.py`, lines 89 to 112:

```python
    def complete(self, request: ChatRequest) -> ChatResponse:
        payload = self.build_payload(request)
        started = self._clock.monotonic()
        try:
            message = self._client.messages.create(**payload)
        except anthropic.APIConnectionError as error:
            raise TransientModelError(f"{type(error).__name__}: {error}") from error
        except anthropic.APIStatusError as error:
            if error.status_code in (408, 409, 429) or error.status_code >= 500:
                raise TransientModelError(f"HTTP {error.status_code}: {error.message}") from error
            raise PermanentModelError(f"HTTP {error.status_code}: {error.message}") from error
        elapsed = self._clock.monotonic() - started
        text = "".join(block.text for block in message.content if block.type == "text")
        calls = tuple(
            ToolCall(block.id, block.name, dict(block.input)) for block in message.content if block.type == "tool_use"
        )
        return ChatResponse(
            text=text,
            stop_reason=_STOP.get(message.stop_reason or "", StopReason.OTHER),
            usage=Usage(message.usage.input_tokens, message.usage.output_tokens),
            latency_seconds=round(elapsed, 4),
            model=message.model,
            tool_calls=calls,
        )
```

- `self._client.messages.create(**payload)` is the SDK call. It sends `POST /v1/messages` and returns a `Message` object.
- `anthropic.APIConnectionError` means the request could not reach the API. `anthropic.APIStatusError` means the API answered with an error status; its `.status_code` decides: 408, 409, 429 and 5xx are transient (retry), all others permanent.
- `message.content` is a list of blocks. The text blocks are joined; each `tool_use` block becomes a `ToolCall`.
- `message.usage.input_tokens` and `message.usage.output_tokens` are the tokens the provider **billed**. The project records these, never its own count (`Usage` docstring: "read from its usage block, never recomputed").
- `message.stop_reason` is mapped through this table, so the rest of the code never sees the vendor's words:

`src/token_meter/infrastructure/anthropic_chat.py`, lines 20 to 26:

```python
_STOP = {
    "end_turn": StopReason.END,
    "stop_sequence": StopReason.END,
    "max_tokens": StopReason.LENGTH,
    "tool_use": StopReason.TOOL_CALLS,
    "refusal": StopReason.REFUSAL,
}
```

### Counting tokens without generating

`src/token_meter/infrastructure/anthropic_chat.py`, lines 114 to 119:

```python
    def count_tokens(self, request: ChatRequest) -> int:
        """Ask the provider how many input tokens a request would use (no generation, no charge)."""
        payload = self.build_payload(request)
        for unused in ("max_tokens", "thinking", "output_config"):
            payload.pop(unused, None)
        return int(self._client.messages.count_tokens(**payload).input_tokens)
```

`messages.count_tokens` asks the API how many input tokens a request would use, without running the model and without charge. The meter uses it to calibrate its offline estimate.

### Testing without a network

`tests/unit/infrastructure/test_anthropic_chat.py`, lines 28 to 36:

```python

def adapter(handler, thinking="disabled"):
    client = anthropic.Anthropic(
        api_key="test-key-not-real",
        max_retries=0,
        http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler)),
    )
    return AnthropicChatModel(client, "claude-haiku-5-5", FixedClock(), thinking)

```

The SDK accepts an `http_client`; the test gives it a client whose transport is `httpx2.MockTransport(handler)`, so the real SDK code runs against a fake server written in the test.

## Try it yourself

1. The installed SDK.

```bash
.venv/bin/python -c "import anthropic; print(anthropic.__version__)"
```

What you should see (captured from this repository):

```text
2.3.0
```

2. The error class family: `APIStatusError` is an `APIError`, which is an `AnthropicError`, which is an `Exception`.

```bash
.venv/bin/python -c "import anthropic; print([c.__name__ for c in anthropic.APIStatusError.__mro__])"
```

What you should see (captured from this repository):

```text
['APIStatusError', 'APIError', 'AnthropicError', 'Exception', 'BaseException', 'object']
```

3. Build the request body for a tiny conversation, without any network call or key. This is exactly what would be sent as the JSON body.

```bash
.venv/bin/python -c "from token_meter.infrastructure.anthropic_chat import AnthropicChatModel; from token_meter.domain.llm import ChatMessage, ChatRequest; m = AnthropicChatModel(None, 'claude-haiku-5-5', None); import json; print(json.dumps(m.build_payload(ChatRequest((ChatMessage.user('Hello'),), system='Be brief.', max_output_tokens=50)), indent=2))"
```

What you should see (captured from this repository):

```text
{
  "model": "claude-haiku-5-5",
  "max_tokens": 50,
  "messages": [
    {
      "role": "user",
      "content": "Hello"
    }
  ],
  "system": "Be brief.",
  "thinking": {
    "type": "disabled"
  }
}
```

4. The SDK client has a `max_retries` parameter; the project sets it to 0.

```bash
.venv/bin/python -c "import anthropic, inspect; print(inspect.signature(anthropic.Anthropic.__init__).parameters['max_retries'])"
```

What you should see (captured from this repository):

```text
max_retries: 'int' = 2
```

## Mistakes people make

- **Putting the API key in a file.** It comes from the environment (`ANTHROPIC_API_KEY`) and the factory checks it is set.
- **Counting tokens yourself and calling it the bill.** The project reads `usage` from the response and treats its own count only as an estimate.
- **Letting two retry layers stack.** The SDK's retries are off (`max_retries=0`); `RetryingChatModel` is the single place.
- **Sending sampling settings the API rejects.** The adapter raises `UnsupportedParameter` before sending.
- **Importing `anthropic` in domain code.** `import-linter` fails the build.
- **Relying on remembered model details.** Model names, prices and rules change; `data/prices.json` carries a read date and a stale table is refused. Check the current documentation before a real run.

## Check yourself

1. What does the `usage` block contain?

   *Answer:* The number of input and output tokens the provider billed for the call.

2. Why is `max_retries=0` set?

   *Answer:* So the project's own retry decorator is the only place that retries, with logging and the budget.

3. How does a tool call travel?

   *Answer:* The model answers with a `tool_use` block; the program runs the tool and returns a `tool_result` block in the next user turn.

4. Which statuses are treated as transient?

   *Answer:* 408, 409, 429 and 5xx, plus connection errors.

5. Why is the SDK wrapped in an adapter?

   *Answer:* So the core depends on a neutral interface and providers can be swapped or replaced by a recording.

## Further reading

- Anthropic API and SDK documentation, https://docs.anthropic.com/ and the Python SDK repository, https://github.com/anthropics/anthropic-sdk-python (SDK 2.3.0 is pinned; this note was NOT checked against the live documentation, only against the installed SDK, the adapter's own tests and a request body built offline).

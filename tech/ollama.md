# Ollama and the OpenAI-compatible API

## What it is

An **open-weight model** is a language model whose learned numbers (the *weights*) are published, so anyone can download and run it. **Ollama** is a program that downloads such models and runs them on your own computer, then answers requests at a local web address (`http://localhost:11434`). A **server** is a program that waits for requests; `localhost` means "this computer"; `11434` is the **port**, a numbered door the server listens at.

The **OpenAI-compatible API** is a request format that began with OpenAI's chat service and that many other servers now copy: `POST /v1/chat/completions` with `model` and `messages`, and `POST /v1/embeddings` for vectors. Because ollama and llama.cpp speak it, one client works with both.

## Why this repository uses it

The repository needs a real model to record answers from, one that costs nothing, needs no key and runs on a laptop. Small Qwen 2.5 models through ollama are that model. Using the common OpenAI-compatible format keeps the adapter independent of the server: you can point `OPENAI_BASE_URL` at ollama, at llama.cpp's `llama-server`, or at a hosted service.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `scripts/pull_model.sh` | downloads a model with `ollama pull` |
| `Makefile` | `models` runs the script; `record` calls the live model |
| `src/token_meter/infrastructure/openai_compatible.py` | the adapter for `/chat/completions` |
| `src/token_meter/infrastructure/model_factory.py` | chooses this adapter for `MODEL_PROVIDER=openai-compatible` |
| `env.example` | `OPENAI_BASE_URL`, `MODEL_NAME`, `EMBED_MODEL` |
| `tests/fixtures/` | the answers recorded from the local model |

## How it works underneath

**Running a model.** The weights are a large file of numbers. For each request the program converts the text to tokens, runs them through the network of numbers to produce one next-token probability list, picks a token, appends it, and repeats until it stops or reaches `max_tokens`. Small models do this quickly on a CPU or a laptop GPU, at the cost of lower quality.

**Quantization.** To fit in memory the weights are usually stored with fewer bits per number (for example 4-bit). ollama's `qwen2.5:0.5b` is such a compressed build.

**Embeddings.** An embedding model reads a text and outputs a fixed-length vector. Texts about the same thing end up close together, measured by the angle between the vectors (cosine similarity). That is how search by meaning works.

**Ports and servers.** `ollama serve` binds port 11434 on your computer. Anything that can send HTTP to `http://localhost:11434` can use it, which is why `curl` works as a test (see `curl-and-http.md`).

**Where the model files live.** In ollama's own store under your home folder, never in this repository.

## Walkthrough of this repository's use

### Getting a model: `scripts/pull_model.sh`

`bash.md` explains the script line by line. The core of it is `ollama pull "$model"`, run by `make models` for these models: `qwen2.5:0.5b`.

- `qwen2.5:0.5b` and `qwen2.5:1.5b` are small open-weight chat models from the Qwen 2.5 family. The part after the colon is the size: 0.5 or 1.5 billion parameters (the numbers the model learned). Small models run on a laptop CPU.
- `nomic-embed-text` is an **embedding** model: it turns a text into a list of 768 numbers (a *vector*) so that texts with similar meaning have similar vectors.

### Calling it

The adapter `src/token_meter/infrastructure/openai_compatible.py` talks the **OpenAI-compatible** protocol, which ollama (listening on `http://localhost:11434/v1`) and llama.cpp's `llama-server` both speak. The base address comes from `OPENAI_BASE_URL`. Because many servers share the protocol, one adapter works for all of them.

Building the request body:

`src/token_meter/infrastructure/openai_compatible.py`, lines 52 to 81:

```python
    def build_payload(self, request: ChatRequest) -> dict[str, Any]:
        """The JSON body for a request (public so tests can assert on it)."""
        messages: list[dict[str, Any]] = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.extend(_message_payload(m) for m in request.messages)
        payload: dict[str, Any] = {
            "model": request.model or self._model,
            "messages": messages,
            "max_tokens": request.max_output_tokens,
            "stream": False,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.top_p is not None:
            payload["top_p"] = request.top_p
        if request.response_schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": dict(request.response_schema), "strict": True},
            }
        if request.tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {"name": t.name, "description": t.description, "parameters": dict(t.parameters)},
                }
                for t in request.tools
            ]
        return payload
```

- `model`, `messages` and `max_tokens` are the core fields; `"stream": False` asks for one complete answer rather than a stream of pieces.
- A system prompt is the first message with role `system` (unlike Claude's separate `system` field).
- `temperature` and `top_p` control randomness and are sent only if set. Temperature 0 makes the model pick its most likely word every time (nearly repeatable).
- `response_format` with `json_schema` asks the server to force the output to match a JSON Schema ("structured output").
- `tools` lists functions the model may call, in the form `{"type": "function", "function": {name, description, parameters}}`.

Reading the answer:

`src/token_meter/infrastructure/openai_compatible.py`, lines 98 to 117:

```python
    def _parse(self, body: dict[str, Any], elapsed: float) -> ChatResponse:
        try:
            choice = body["choices"][0]
            message = choice["message"]
            usage = body["usage"]
            calls = tuple(
                ToolCall(str(c.get("id", f"call_{i}")), c["function"]["name"], _arguments(c["function"]["arguments"]))
                for i, c in enumerate(message.get("tool_calls") or [])
            )
            stop = StopReason.TOOL_CALLS if calls else _FINISH.get(choice.get("finish_reason") or "", StopReason.OTHER)
            return ChatResponse(
                text=message.get("content") or "",
                stop_reason=stop,
                usage=Usage(int(usage["prompt_tokens"]), int(usage["completion_tokens"])),
                latency_seconds=round(elapsed, 4),
                model=str(body.get("model", self._model)),
                tool_calls=calls,
            )
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise PermanentModelError(f"unexpected response shape: {error!r}") from error
```

- `choices[0].message.content` is the text; `finish_reason` is mapped to the project's neutral stop reasons.
- `usage.prompt_tokens` and `usage.completion_tokens` are the server's own token counts (input and output).
- Tool calls arrive in `message.tool_calls`, with `function.arguments` as **JSON text** that `json.loads` parses.
- A body missing these fields raises `PermanentModelError("unexpected response shape")` instead of crashing later.

### Recording: why the repository does not need ollama to run

With `RECORD=on`, `RecordingChatModel` wraps the live adapter and writes each answer, keyed by a fingerprint of the request, into `tests/fixtures/...` (see `jsonl.md`). With `MODEL_PROVIDER=recorded`, `RecordedChatModel` returns the saved answer for the same fingerprint. So `make run` and `make test` never start ollama; only `make models` and `make record` need it.

## Try it yourself

1. The installed ollama (`ollama` is only needed for `make models` and `make record`).

```bash
ollama --version
```

What you should see (captured from this repository):

```text
ollama version is 0.40.6
```

2. Start the server (leave it running in a second terminal). Not run while this note was written.

```bash
ollama serve
```

3. Download the small chat model (a few hundred megabytes). Not run here; `make models` does the same.

```bash
ollama pull qwen2.5:0.5b
```

4. Talk to the server by hand with the OpenAI-compatible request. Not run here. You will see JSON with `choices[0].message.content` and a `usage` block.

```bash
curl -s http://localhost:11434/v1/chat/completions -H 'Content-Type: application/json' -d '{"model": "qwen2.5:0.5b", "messages": [{"role": "user", "content": "Say hi"}], "max_tokens": 20}'
```

5. Build the request body for a tiny conversation without any network: exactly what the adapter would send.

```bash
.venv/bin/python -c "from token_meter.infrastructure.openai_compatible import OpenAICompatibleChatModel as M; from token_meter.domain.llm import ChatMessage, ChatRequest; import json; m = M(None, 'http://localhost:11434/v1', 'qwen2.5:0.5b', None); print(json.dumps(m.build_payload(ChatRequest((ChatMessage.user('Hello'),), system='Be brief.', max_output_tokens=50, temperature=0.0)), indent=2))"
```

What you should see (captured from this repository):

```text
{
  "model": "qwen2.5:0.5b",
  "messages": [
    {
      "role": "system",
      "content": "Be brief."
    },
    {
      "role": "user",
      "content": "Hello"
    }
  ],
  "max_tokens": 50,
  "stream": false,
  "temperature": 0.0
}
```

## Mistakes people make

- **Assuming a small model is correct.** The 0.5-billion-parameter model is often wrong; the repository measures it instead of trusting it.
- **Committing model files.** Weights stay in ollama's store; `.gitignore` and the template forbid tracking them.
- **Forgetting `ollama serve`.** Without a running server the adapter gets "connection refused", which becomes a transient error and is retried.
- **Expecting identical text on every run.** Unless temperature is 0 and the model is the same build, answers vary; the recordings exist to freeze one set of answers.
- **Mixing embedding models.** Vectors from different models cannot be compared. The vector column and the recordings name the model (`nomic-embed-text`, 768 numbers).

## Check yourself

1. What is an open-weight model?

   *Answer:* A model whose learned numbers are published so anyone can run it.

2. Which port does ollama listen on by default?

   *Answer:* 11434.

3. What does OpenAI-compatible mean here?

   *Answer:* The server accepts `POST /v1/chat/completions` and `/v1/embeddings` in the format OpenAI popularized.

4. Why does `make run` work without ollama?

   *Answer:* It replays recorded answers keyed by a fingerprint of the request.

5. What is an embedding?

   *Answer:* A fixed-length list of numbers for a text; similar meanings give similar lists.

## Further reading

- Ollama documentation, https://github.com/ollama/ollama/blob/main/docs/api.md and https://github.com/ollama/ollama/blob/main/docs/openai.md; llama.cpp server, https://github.com/ggml-org/llama.cpp/tree/master/tools/server (ollama 0.40.6 is installed on the machine where this was written; the server commands were not run during the capacity freeze, the request body was built offline).

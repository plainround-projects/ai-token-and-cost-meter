# httpx

## What it is

**HTTP** is the language web programs use to talk: a client sends a **request** (a method such as GET or POST, an address, headers, an optional body) and the server sends back a **response** (a status number, headers, a body). **httpx** is a Python library that sends such requests. You call `client.post(url, json=data)` and get a response object with `.status_code` and `.json()`.

A **client** object keeps connections open and applies settings (timeouts, headers) to every request it sends.

## Why this repository uses it

Three jobs in this repository need HTTP: talking to a local model server (ollama or llama.cpp), talking to the other services the agents drive (calendar, orders), and the tests that start those servers and call them. httpx is a small, well-typed client with a built-in way to fake the network for tests (`MockTransport`), which is what makes the HTTP adapters testable offline. The Anthropic SDK (version 2.3.0) is built on `httpx2`, a sibling package with the same API; the project depends on `httpx` itself for its own HTTP calls.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/token_meter/infrastructure/openai_compatible.py` | the adapter that calls an OpenAI-compatible server |
| `src/token_meter/infrastructure/model_factory.py` | creates the one client at start-up |
| `tests/unit/infrastructure/` | tests fake the network with `httpx.MockTransport` |
| `pyproject.toml` | `httpx==0.28.1` is a runtime dependency; `httpx2` appears among the dev dependencies |
| `requirements.lock` | `httpx`, `httpcore`, `h11`, `anyio`, `certifi`, `idna`, `sniffio` come with it |

## How it works underneath

**What a request really is.** HTTP is plain text over a TCP connection (a reliable stream of bytes between two programs). A request looks like `POST /v1/chat/completions HTTP/1.1`, then header lines, a blank line, then the body. The response starts with `HTTP/1.1 200 OK`, headers, a blank line, then the body. For `https://` addresses the bytes are wrapped in TLS (encryption). httpx builds this for you.

**The layers.** `httpx` is the friendly API. Below it, `httpcore` manages connection pools and writes requests; `h11` is the pure-Python implementation of the HTTP/1.1 text rules; `anyio` provides the networking for async programs; `certifi` supplies the list of trusted certificate authorities for HTTPS; `idna` handles international domain names; `sniffio` detects which async library is in use. `pip` installed all of them because they are in the lock file.

**Timeouts.** A request can wait forever if the server is silent. httpx has separate timeouts for connect, write, read and the connection pool; a single number sets all four.

**Status codes.** 2xx success, 3xx redirect, 4xx the client's mistake, 5xx the server's mistake. 429 means "slow down". The adapters use them to decide whether to retry.

**`httpx2`.** The lock file also pins a package called `httpx2`. The Anthropic SDK in this project is built on it, and the test for the Claude adapter uses `httpx2.MockTransport`. Its API matches httpx. (`pyproject.toml` lists it as a dev dependency so the tests can import it directly.)

## Walkthrough of this repository's use

### Making the client once

`src/token_meter/infrastructure/model_factory.py`, lines 69 to 72:

```python
    else:
        http = httpx.Client(timeout=settings.timeout_seconds)
        live = OpenAICompatibleChatModel(http, settings.openai_base_url, settings.model, clock, settings.openai_api_key)
    live = RetryingChatModel(live, attempts=settings.attempts)
```

`httpx.Client(timeout=...)` creates a **client**: an object that holds a pool of open connections to servers, so a second request to the same server reuses the connection instead of opening a new one. `timeout=` is how many seconds to wait before giving up on connecting, sending or waiting for an answer. The number comes from the `MODEL_TIMEOUT_SECONDS` setting (see `environment-variables.md`). One client is created at start-up and passed in; nothing else creates one.

### Sending a request and mapping failures

`src/token_meter/infrastructure/openai_compatible.py`, lines 37 to 42:

```python
    def __init__(self, http: httpx.Client, base_url: str, model: str, clock: Clock, api_key: str | None = None) -> None:
        self._http = http
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._clock = clock
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
```

The constructor takes the client as a parameter (`http: httpx.Client`), the server address, the model name and a clock. Passing the client in (instead of creating it inside) lets the tests hand in a client that never touches the network.

`src/token_meter/infrastructure/openai_compatible.py`, lines 83 to 96:

```python
    def complete(self, request: ChatRequest) -> ChatResponse:
        started = self._clock.monotonic()
        try:
            reply = self._http.post(
                f"{self._base_url}/chat/completions", json=self.build_payload(request), headers=self._headers
            )
        except httpx.TransportError as error:
            raise TransientModelError(f"{type(error).__name__}: {error}") from error
        elapsed = self._clock.monotonic() - started
        if reply.status_code == 429 or reply.status_code >= 500:
            raise TransientModelError(f"HTTP {reply.status_code}")
        if reply.status_code >= 400:
            raise PermanentModelError(f"HTTP {reply.status_code}: {reply.text[:200]}")
        return self._parse(reply.json(), elapsed)
```

Line by line:

- `self._http.post(url, json=payload, headers=...)`: send an HTTP **POST** request. `json=payload` turns the Python dictionary into JSON text, sets the header `Content-Type: application/json` and uses it as the request body. `headers` adds the `Authorization: Bearer ...` header only when an API key was given.
- `except httpx.TransportError`: the base class for failures *before an answer arrived* (cannot connect, connection reset, timeout). The adapter converts them to its own `TransientModelError`, a failure that is worth retrying.
- `reply.status_code`: the number the server sent. `429` (too many requests) or any `5xx` (server broke) is transient; any other `4xx` (you sent something wrong) is permanent, because sending the same request again would fail again.
- `reply.text[:200]`: the body as text, cut to 200 characters for the error message.
- `reply.json()`: parses the body as JSON into Python data.

### Where else httpx is used

- `src/token_meter/infrastructure/model_factory.py:70`: `http = httpx.Client(timeout=settings.timeout_seconds)`

### Testing without a network: `MockTransport`

`tests/unit/infrastructure/test_openai_compatible.py`, lines 8 to 18:

```python
from token_meter.domain.errors import PermanentModelError, TransientModelError
from token_meter.domain.llm import ChatMessage, ChatRequest, Role, StopReason, ToolCall, ToolSpec
from token_meter.infrastructure.openai_compatible import OpenAICompatibleChatModel


def model(handler, api_key=None):
    http = httpx.Client(transport=httpx.MockTransport(handler))
    return OpenAICompatibleChatModel(http, "http://local/v1/", "small-model", FixedClock(), api_key)


def ok(content="hello", finish="stop", tool_calls=None, prompt_tokens=11, completion_tokens=3):
```

A **transport** is the part of httpx that really sends bytes. `httpx.MockTransport(handler)` is a stand-in: when a request is made, it calls `handler(request)` (a Python function you write) and uses the `httpx.Response` it returns. The test therefore exercises the adapter's real code, including JSON building and status handling, with no server and no network.

## Try it yourself

1. The installed httpx.

```bash
.venv/bin/python -c "import httpx; print(httpx.__version__)"
```

What you should see (captured from this repository):

```text
0.28.1
```

2. A complete request/response with no network: the handler echoes the path and the JSON body it received.

```bash
.venv/bin/python -c "import httpx; t = httpx.MockTransport(lambda req: httpx.Response(200, json={'path': req.url.path, 'got': req.read().decode()})); c = httpx.Client(transport=t); r = c.post('http://example.test/chat', json={'a': 1}); print(r.status_code, r.json())"
```

What you should see (captured from this repository):

```text
200 {'path': '/chat', 'got': '{"a":1}'}
```

3. A status of 429 is an error status; the adapter turns it into a retryable error.

```bash
.venv/bin/python -c "import httpx; t = httpx.MockTransport(lambda req: httpx.Response(429)); r = httpx.Client(transport=t).get('http://example.test/'); print(r.status_code, r.is_error)"
```

What you should see (captured from this repository):

```text
429 True
```

4. Connecting to a port nothing listens on raises `ConnectError` (a `TransportError`), the failure the adapter treats as transient.

```bash
.venv/bin/python -c "import httpx; httpx.Client(timeout=0.5).get('http://127.0.0.1:9')" 2>&1 | tail -1
```

What you should see (captured from this repository):

```text
httpx.ConnectError: [Errno 61] Connection refused
```

## Mistakes people make

- **No timeout.** A silent server would hang the program. The client always has one.
- **Retrying every error.** Only transport errors, 429 and 5xx are retried; a 400 would fail again.
- **Creating a client per request.** That throws away connection reuse. The client is made once.
- **Logging the request body.** It holds customer text. INFO logs carry sizes only, and httpx's own logger is raised to WARNING.
- **Calling `.json()` on an error page.** The adapter checks `status_code` first.

## Check yourself

1. What does a 429 status mean and how does the adapter treat it?

   *Answer:* Too many requests; it is transient, so it is retried.

2. What does `json=payload` do in `client.post`?

   *Answer:* Encodes the dictionary as JSON, sets the content type and sends it as the body.

3. Why is the client passed into the adapter?

   *Answer:* So tests can pass a client that uses a fake transport.

4. What is a `TransportError`?

   *Answer:* A failure before an answer arrived, such as a refused connection or a timeout.

5. What does `MockTransport` replace?

   *Answer:* The part of httpx that really sends bytes over the network.

## Further reading

- httpx documentation, https://www.python-httpx.org/ (httpx 0.28.1 is pinned in the lock file; examples were run locally with no network).

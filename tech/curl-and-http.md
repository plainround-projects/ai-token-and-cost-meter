# HTTP and curl

## What it is

**HTTP** (Hypertext Transfer Protocol) is the set of rules computers use to ask for things and answer over a network. A **client** sends a **request**; a **server** sends back a **response**. Both are plain text with a first line, some **headers** and an optional **body**. Every web page, API and service in this repository speaks it. **curl** is a command-line program that sends one HTTP request and prints the answer. It is the quickest way to try a service by hand.

An **address** (URL) such as `http://127.0.0.1:8090/health` has a **scheme** (`http`), a **host** (`127.0.0.1`, this computer), a **port** (`8090`, a numbered door a program listens at) and a **path** (`/health`).

## Why this repository uses it

The code talks HTTP in three ways: to a local model server (`ollama.md`), and from tests that fake the network.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `src/token_meter/infrastructure/` | HTTP clients (httpx; see `httpx.md`) |
| `Makefile` | (no curl here) |
| `tests/` | tests call services with httpx |

## How it works underneath

**Layers.** HTTP rides on **TCP**, which provides a reliable stream of bytes between two programs, and TCP rides on **IP**, which routes packets between computers. A program connects to `host:port`; the operating system finds the program listening there. `https://` adds **TLS**, which encrypts the stream and proves the server's identity with a certificate; the local addresses in this repository use plain `http` on `127.0.0.1`, which never leaves the computer.

**Loopback.** `127.0.0.1` (also `localhost`) is the computer talking to itself; traffic to it does not reach the network.

**Statelessness.** Each request is complete by itself; the server does not remember earlier ones unless you send an identifier (a key, a token).

**Timeouts and retries.** A request can fail without an answer (connection refused, timeout). Callers retry only operations that are safe to repeat, which is why writes carry idempotency keys.

**curl flags used.** `-s` silent (no progress meter); `-f` fail: exit with an error code when the status is 400 or above, instead of printing the error page; `-X POST` choose the method; `-H 'Name: value'` add a header; `-d 'body'` send a body.

## Walkthrough of this repository's use

### Requests this repository sends

- `src/token_meter/domain/analysis.py:92`: `row = billed_rows.get(prompt.id)`
- `src/token_meter/domain/analysis.py:197`: `known = calibration.mean_output.get((kind, setting))`
- `src/token_meter/domain/estimation.py:33`: `ratio = self.by_kind.get(kind, self.chars_per_token) if kind else self.chars_per_token`
- `src/token_meter/domain/llm.py:143`: `ToolCall(str(c["id"]), str(c["name"]), dict(c["arguments"])) for c in data.get("tool_calls", [])`
- `src/token_meter/domain/prompts.py:56`: `if not isinstance(row.get(name), str) or not row[name].strip():`
- `src/token_meter/domain/prompts.py:57`: `raise InvalidPromptSet(f"field {name!r} must be a non-empty string, got {row.get(name)!r}")`

### Requests the Makefile sends with curl

(none: this repository's Makefile does not call curl)

### The anatomy of one exchange

A request:

```text
POST /v1/chat/completions HTTP/1.1
Host: localhost:11434
Content-Type: application/json
Content-Length: 87

{"model": "qwen2.5:0.5b", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 20}
```

- The first line: the **method** (`POST`), the **path** (`/v1/chat/completions`) and the protocol version.
- **Headers** (`Name: value` lines) carry facts about the request: which host, what kind of body (`Content-Type`), how long (`Content-Length`).
- A blank line, then the **body**.

An answer:

```text
HTTP/1.1 200 OK
Content-Type: application/json

{"choices": [...], "usage": {"prompt_tokens": 12, "completion_tokens": 5}}
```

- The **status line**: protocol, a **status code** (200) and its reason phrase.
- Headers, a blank line, then the body.

**Methods used here.** `GET` reads (no body, no change). `POST` creates or acts. `PUT` replaces (the migration flag). **Status codes.** 2xx success (200 OK, 201 Created); 3xx redirect; 4xx the caller's mistake (400 bad request, 404 not found, 409 conflict, 422 invalid body, 429 too many requests); 5xx the server's mistake.

**Idempotency.** An operation is idempotent if doing it twice has the same effect as once. `GET` and `PUT` are by definition; a `POST` is not, so the write endpoints here accept an `Idempotency-Key` header and remember the key.

**Version check (`If-Match`).** A write can carry the version of the thing the caller last read; the server applies it only if that is still the current version, otherwise it answers 409.

## Try it yourself

1. The installed curl.

```bash
curl --version | head -1
```

What you should see (captured from this repository):

```text
curl 8.7.1 (x86_64-apple-darwin25.0) libcurl/8.7.1 (SecureTransport) LibreSSL/3.3.6 zlib/1.2.12 nghttp2/1.68.1
```

2. Ask a port with no server behind it. curl cannot connect, prints `000` as the status and exits non-zero.

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:9/ || echo "no server listening (exit code $?)"
```

What you should see (captured from this repository):

```text
000
no server listening (exit code 7)
```

3. A whole exchange with no network: a POST with a header and JSON body, and a 201 answer with a header and JSON body.

```bash
.venv/bin/python -c "import httpx; t = httpx.MockTransport(lambda req: httpx.Response(201, json={'ok': True}, headers={'x-demo': '1'})); r = httpx.Client(transport=t).post('http://example.test/events', json={'n': 1}, headers={'Idempotency-Key': 'abcdefgh'}); print(r.status_code, r.headers['x-demo'], r.json())"
```

What you should see (captured from this repository):

```text
201 1 {'ok': True}
```

4. Take an address apart: scheme, host, port, path and query.

```bash
.venv/bin/python -c "import urllib.parse as u; p = u.urlsplit('http://127.0.0.1:8090/free-slots?minutes=60&people=alice'); print(p.scheme, p.hostname, p.port, p.path, p.query)"
```

What you should see (captured from this repository):

```text
http 127.0.0.1 8090 /free-slots minutes=60&people=alice
```

## Mistakes people make

- **Retrying a POST blindly.** It may repeat the effect. The services use idempotency keys so a retry is safe.
- **Ignoring the status code.** A 4xx or 5xx body is an error message, not data. The adapters check the status first.
- **Using `localhost` and `127.0.0.1` interchangeably in containers.** Inside a container `localhost` is the container; the host's server is reached at `host.docker.internal`.
- **No timeout.** A silent server would hang the caller forever.
- **Sending secrets over plain `http` across a network.** Only loopback addresses use plain http here.

## Check yourself

1. What are the three parts of an HTTP request before the body?

   *Answer:* The request line (method, path, version), the headers, and a blank line.

2. What does status 409 mean here?

   *Answer:* A conflict, such as a taken slot, a stale version or a reused idempotency key with a different request.

3. What does `curl -f` do?

   *Answer:* Makes curl exit with an error when the server answers 400 or above.

4. What is `127.0.0.1`?

   *Answer:* The loopback address: this computer talking to itself.

5. Why do write endpoints take an idempotency key?

   *Answer:* So a retry cannot apply the same write twice.

## Further reading

- MDN HTTP overview, https://developer.mozilla.org/en-US/docs/Web/HTTP and curl documentation, https://curl.se/docs/manpage.html (curl 8.7.1 is installed on the machine where the commands were run).

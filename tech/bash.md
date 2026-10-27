# Bash and shell scripts

## What it is

A **shell** is a program that reads a line you type, finds the program you named, and starts it. **Bash** is the most widely used shell on Linux and the one this repository's script asks for. A **shell script** is a text file of such lines that you can run as one program.

Every program a shell starts is a **process**: a running copy of a program with its own memory and a number called the **process id** (pid). When a process ends it hands back a number called its **exit code**: `0` means "it worked", anything else means "it failed". The shell lets you join programs together: the output of one can be the input of the next (a *pipe*), or be saved in a file (a *redirection*).

Each process has three standard channels, called **file descriptors** (small numbers that name an open stream of bytes): `0` is *standard input* (where it reads), `1` is *standard output* (where it prints results), `2` is *standard error* (where it prints complaints). By default 1 and 2 both show on your screen, but they are separate channels, so you can capture one and not the other.

## Why this repository uses it

Starting a program, wiring programs together, and checking whether they worked is what a shell is for. The repository needs this in two places. First, one stand-alone script, `scripts/pull_model.sh`, which downloads a model and refuses politely when ollama is missing. Second, the `Makefile` recipes, which are shell lines: they wait for a server to answer, save a process id, test whether a file exists, and stop a server. The script uses `set -euo pipefail`, the three safety switches that make a bash script stop on the first mistake instead of continuing in a half-broken state.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `scripts/pull_model.sh` | the only stand-alone shell script: downloads a model through ollama |
| `Makefile` | every recipe line is a small shell program (see the table below) |
| `.github/workflows/ci.yml` | each `run:` line is run by bash on the CI machine |

## How it works underneath

**What happens when you type a command.** The shell splits the line into words, expands variables (`$name`) and command substitutions (`$(...)`), applies quoting rules, sets up redirections, then asks the operating system to start the program with those words as its arguments. The shell waits for the process to end, and stores its exit code in the special variable `$?`.

**Quoting.** Spaces separate words. To keep spaces inside one word, quote it. Inside double quotes `"..."` the shell still replaces `$variable` and `$(command)`. Inside single quotes `'...'` nothing is replaced: every character is literal. A common bug is leaving a variable unquoted: if `model="a b"`, then `ollama pull $model` passes two words.

**Exit codes drive control flow.** `if command; then ... fi` runs the `then` part when `command` exits with 0. `A && B` runs B only if A exited 0. `A || B` runs B only if A did not. `set -e` turns "any unhandled non-zero exit" into "stop the script".

**Signals.** A signal is a small message the operating system delivers to a process. `SIGTERM` (the default of `kill`) asks the process to finish cleanly. `SIGKILL` (`kill -9`) cannot be caught: the process is removed at once. `kill -0` delivers nothing and only reports whether the process exists.

**Background processes.** A trailing `&` starts a program without waiting for it. `$!` then holds its pid. `nohup` makes the program ignore the "hang up" signal that is sent when the terminal closes.

**Each Makefile line is separate.** `make` hands each recipe line to `/bin/sh` on its own. `sh` is the system's basic shell; on macOS it is bash running in a strict mode, on many Linux systems it is a smaller shell called dash. The Makefile lines therefore use only features that work in all of them. The script `pull_model.sh` asks for `bash` explicitly in its shebang line.

## Walkthrough of this repository's use

`scripts/pull_model.sh`, the whole file, block by block. Under each block, every line is explained.

```bash
#!/usr/bin/env bash
# Download a small open-weight model through ollama. The weights live in ollama's own store, never in this repository.
set -euo pipefail
model="${1:-qwen2.5:0.5b}"
if ! command -v ollama >/dev/null; then
  echo "ollama is not installed: https://ollama.com/download (or run llama.cpp's llama-server and set OPENAI_BASE_URL)" >&2
  exit 1
fi
ollama pull "$model"
echo "pulled $model; serve it with 'ollama serve' (the app does this) and set MODEL_PROVIDER=openai-compatible"
```

- `#!/usr/bin/env bash`: The first line of a script is the *shebang* (`#!`, called hash-bang). When you run the file as a program, the operating system reads this line to learn which interpreter should read the rest. `/usr/bin/env bash` means "find the program named `bash` on the search path and use that one", which works whether bash lives in `/bin` or `/opt/homebrew/bin`.
- `# Download a small open-weight model through ollama. The weights live in ollama's own store, never in this repository.`: A comment. The shell ignores everything after a `#`.
- `set -euo pipefail`: Turns on three safety switches. `-e` means "stop the script at the first command that fails" (without it, the shell would carry on after an error). `-u` means "using a variable that was never set is an error" (without it, a typo in a variable name silently becomes an empty string). `-o pipefail` means "a pipeline fails if any command in it fails, not just the last one".
- `model="${1:-qwen2.5:0.5b}"`: Creates a variable called `model`. `$1` is the first word you typed after the script name. `${1:-X}` means "use `$1`, but if it is missing or empty use `X` instead", so running the script with no arguments downloads qwen2.5:0.5b. The double quotes keep a value that contains special characters as one piece.
- `if ! command -v ollama >/dev/null; then`: Starts an `if`. `command -v ollama` asks the shell "where is the program `ollama`?"; it succeeds (exit code 0) if the program is installed. `!` flips the answer, so the `then` part runs when ollama is *missing*. `>/dev/null` throws the printed path away: `/dev/null` is a special file that discards everything written to it.
- `echo "ollama is not installed: https://ollama.com/download (or run llama.cpp's llama-server and set OPENAI_BASE_URL)" >&2`: Prints an explanation and where to download ollama. `>&2` sends the text to *standard error* (file descriptor 2, the channel meant for messages about problems) instead of standard output (descriptor 1), so a program reading this script's output does not mistake the message for results.
- `exit 1`: Ends the script now with exit code 1. Exit code 0 means success, any other number means failure; callers such as `make` stop when they see a non-zero code.
- `fi`: Ends the `if` block (`fi` is `if` spelled backwards).
- `ollama pull "$model"`: Runs `ollama pull` for the model. ollama downloads the model files into its own store on your computer (not into this repository). Because of `set -e`, if the download fails the script stops here with ollama's error code.
- `echo "pulled $model; serve it with 'ollama serve' (the app does this) and set MODEL_PROVIDER=openai-compatible"`: Prints a confirmation. Inside double quotes the shell replaces `$model` with the value. Single quotes inside the double-quoted text are plain characters, so the message can show the command `ollama serve` in quotes.

### The shell inside the Makefile and the CI file

The recipe lines of the `Makefile` are shell commands too. Each shell feature below appears in this repository; the last column is the first line that uses it.

| Feature | What it does | First line that uses it |
| --- | --- | --- |
| Pipe `\|` | connects the output of the program on the left to the input of the program on the right | `@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) \| sed -E 's/:.*## /\t/' \| sort` |
| Input redirection `<` | feeds a file to a program as its input | `@echo "ready: recorded model, $$(wc -l < data/prompts.jsonl \| tr -d ' ') prompts, prices read $$(sed -n 's/.*read_date": "\([^"]*\)".*/\1/p' data/p...` |
| Command substitution `$(...)` | runs a command and pastes its output into the line (make needs the dollar sign doubled) | `@echo "ready: recorded model, $$(wc -l < data/prompts.jsonl \| tr -d ' ') prompts, prices read $$(sed -n 's/.*read_date": "\([^"]*\)".*/\1/p' data/p...` |
| Environment variable prefix | `NAME=value command` gives that one command an extra environment variable | `MODEL_PROVIDER=recorded RECORDINGS_PATH=tests/fixtures/recordings $(VENV)/bin/meter run --budget 0.05` |

The programs those lines start:

| Program | What it does |
| --- | --- |
| `grep` | searches text for lines that match a pattern (`-E` means extended patterns, `-q` means print nothing and just set the exit code) |
| `sed` | edits a stream of text; `s/old/new/` replaces text, `-n` with `p` prints only the lines that changed |
| `sort` | puts lines in alphabetical order |
| `wc` | counts; `-l` counts lines |
| `tr` | translates or deletes single characters (`-d` deletes) |
| `rm` | deletes files (`-r` folders too, `-f` no complaint if missing) |
| `touch` | creates an empty file or updates a file's modification time |
| `echo` | prints its arguments |

Every recipe line is explained in full, one by one, in `make.md`.

## Try it yourself

1. Show which bash you have. (The script needs bash 3.2 or newer; macOS ships 3.2 and Homebrew ships 5.x.)

```bash
bash --version | head -1
```

What you should see (captured from this repository):

```text
GNU bash, version 5.3.9(1)-release (aarch64-apple-darwin25.1.0)
```

2. `-n` reads the script without running it. It prints nothing if the syntax is fine, so the `echo` proves it passed.

```bash
bash -n scripts/pull_model.sh && echo syntax ok
```

What you should see (captured from this repository):

```text
syntax ok
```

3. Run the script with a search path that cannot contain ollama. You see the complaint (sent to standard error) and exit code 1.

```bash
env PATH=/usr/bin:/bin /bin/bash scripts/pull_model.sh; echo "exit code: $?"
```

What you should see (captured from this repository):

```text
ollama is not installed: https://ollama.com/download (or run llama.cpp's llama-server and set OPENAI_BASE_URL)
exit code: 1
```

4. `false` is a program that always fails. Because of `set -e`, bash stops at once: `not reached` never prints, and the exit code is 1.

```bash
bash -c 'set -e; false; echo not reached'; echo "exit code: $?"
```

What you should see (captured from this repository):

```text
exit code: 1
```

5. A pipe: `echo` writes `hello`, `tr` turns lowercase letters into uppercase.

```bash
bash -c 'echo hello | tr a-z A-Z'
```

What you should see (captured from this repository):

```text
HELLO
```

## Mistakes people make

- **Forgetting `set -euo pipefail`.** Without it a failed download would be ignored and the script would print "pulled" anyway. The script starts with it.
- **Leaving variables unquoted.** `ollama pull $model` breaks if the value has a space. The script writes `"$model"`.
- **Printing errors to standard output.** A caller that reads the output would treat the complaint as a result. The script sends it to descriptor 2 with `>&2`.
- **Using `[[ ... ]]` or arrays in a Makefile line.** Make runs lines with `/bin/sh`, which may not be bash. The Makefile sticks to `[ ... ]`, `&&`, `||` and `for`.
- **Forgetting that `$` is special to make.** Shell variables and substitutions in recipes are written `$$`; see `make.md`.
- **Assuming `kill` is always immediate.** `kill PID` only *asks* the process to stop (SIGTERM). The Makefile uses it so that requests already being handled can finish.

## Check yourself

1. What does `set -e` change?

   *Answer:* The script stops at the first command that returns a non-zero exit code.

2. What is the difference between `"$model"` and `'$model'`?

   *Answer:* Double quotes replace the variable with its value; single quotes keep the characters `$model` literally.

3. What does `${1:-qwen2.5:0.5b}` mean?

   *Answer:* The first argument, or `qwen2.5:0.5b` when no first argument was given.

4. Why does the script write its complaint with `>&2`?

   *Answer:* To use standard error, the channel for problems, so that standard output stays clean for results.

5. What is `$?` right after `false`?

   *Answer:* 1, the exit code of the last command.

## Further reading

- GNU Bash Reference Manual, https://www.gnu.org/software/bash/manual/bash.html (checked locally against bash 5.3 with `bash -n` and the commands in "Try it yourself").

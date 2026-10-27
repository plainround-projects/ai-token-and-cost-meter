# Python source, the data-generating scripts

## What it is

The scripts under `scripts/` are small standalone Python programs. Each one **writes a data file** of the repository (prompts, emails, help-center pages, calendar or order seed data, tasks). They are not part of the installed package and the program never runs them; they exist so the data is reproducible and its rules are visible.

This note walks through every script line by line.

## Why this repository uses it

Synthetic data is only trustworthy when you can see how it was made. A fixed random seed and plain code mean the same command always writes the same file, so the data can be regenerated, audited and changed on purpose. The committed copies are the ones the tests and the measured numbers use.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `scripts/make_prompts.py` | 153 non-blank lines |

## How it works underneath

A script starts with its imports, defines the data it draws from (lists of names, templates, rules), builds the records with a *seeded* random generator (`random.Random(seed)`: the same seed gives the same sequence of numbers), checks the result against rules, and writes it with `json.dumps` or plain text. Because nothing depends on the date or the machine, the output is identical every time.

The explanations follow the same format as the source notes.

## Walkthrough of this repository's use

### `scripts/make_prompts.py`

In its own words: "Write data/prompts.jsonl: 50 customer messages to a shop's support desk, in five kinds."

153 non-blank lines; it defines `long_message`, `main`.

`scripts/make_prompts.py`, lines 1 to 12:

```python
"""Write data/prompts.jsonl: 50 customer messages to a shop's support desk, in five kinds.

20 short questions, 15 long messages with pasted order details (lengths vary on purpose, one over 1,500
tokens), 5 with a code or error message, 5 in a language other than English and 5 that ask for a one-word
category label. Deterministic: running it twice writes the same file.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
```

- A docstring: text in triple quotes as the first statement documents the module, class or function it belongs to; Python keeps it as `__doc__`.
- `from __future__ import annotations` stores type hints as text instead of evaluating them when the function or class is defined, so a type can name something defined later in the file.
- Makes the module `json` (standard library) available.
- Makes the module `random` (standard library) available.
- Brings in `Path` from the standard library module `pathlib`.

`scripts/make_prompts.py`, lines 14 to 35:

```python
SHORT = [
    "How do I reset my password?",
    "Where can I see my past orders?",
    "Do you ship to Canada?",
    "Can I change the delivery address after I order?",
    "What payment methods do you accept?",
    "How long does standard shipping take?",
    "Is there a way to track my package?",
    "Can I get an invoice for my last purchase?",
    "How do I delete my account?",
    "What is your return window?",
    "Do gift cards expire?",
    "Why was my card charged twice?",
    "Can I combine two orders into one shipment?",
    "How do I update my email address?",
    "Is express shipping available on weekends?",
    "Can I pay for one order with two cards?",
    "What happens if I am not home at delivery?",
    "Do you offer student discounts?",
    "How do I turn off marketing emails?",
    "Can you ship to a parcel locker?",
]
```

- Stores a list of 20 item(s) under the name `SHORT`.

`scripts/make_prompts.py`, lines 37 to 50:

```python
ITEMS = [
    ("blue backpack", 39.90),
    ("steel water bottle", 22.50),
    ("wireless mouse", 18.75),
    ("desk lamp", 44.00),
    ("notebook set", 12.40),
    ("phone stand", 9.99),
    ("canvas tote", 15.25),
    ("usb-c cable", 8.50),
    ("ceramic mug", 11.00),
    ("travel pillow", 27.80),
    ("headphones", 59.00),
    ("yoga mat", 31.60),
]
```

- Stores a list of 12 item(s) under the name `ITEMS`.

`scripts/make_prompts.py`, lines 51 to 56:

```python
OPENERS = [
    "Hi, I placed order #{order} on {date} and I am writing because something went wrong.",
    "Hello support team, order #{order} (placed {date}) has not gone the way I expected.",
    "Good morning. I am following up on order #{order} from {date}; here is everything I have so far.",
    "I have been a customer for years and this is the first time I need help. Order #{order}, {date}.",
]
```

- Stores a list of 4 item(s) under the name `OPENERS`.

`scripts/make_prompts.py`, lines 57 to 67:

```python
BODIES = [
    "The tracking page has said 'in transit' for {days} days now and nothing has moved. I called the carrier and they "
    "say the parcel was never scanned after leaving your warehouse.",
    "The package arrived with a crushed corner and one item was loose in the box. I took photos before opening it, "
    "and I can send them if that helps.",
    "I was charged {total} but the confirmation email shows a different total. Please check whether a coupon was applied.",
    "I changed my mind about one of the items and would like to return it, but the return form will not accept the "
    "order number from my email.",
    "My bank shows two pending charges for the same purchase. One of them should drop off, but I would like you to "
    "confirm that only one payment was taken.",
]
```

- Stores a list of 5 item(s) under the name `BODIES`.

`scripts/make_prompts.py`, lines 68 to 73:

```python
CLOSERS = [
    "Please let me know what you need from me. I am happy to send more details.",
    "I would appreciate a reply today, since I need this sorted before the weekend.",
    "If it is easier to call, tell me a time and a number to use.",
    "Thank you for your help; I have attached nothing, but can reply with photos or screenshots.",
]
```

- Stores a list of 4 item(s) under the name `CLOSERS`.

`scripts/make_prompts.py`, lines 74 to 90:

```python
LONG_SIZES = [
    2,
    2,
    3,
    3,
    4,
    4,
    5,
    5,
    6,
    7,
    8,
    9,
    10,
    12,
    46,
]  # order lines per message; the last is the 1,500+ token one
```

- Stores a list of 15 item(s) under the name `LONG_SIZES`.

`scripts/make_prompts.py`, lines 92 to 103:

```python
CODE = [
    'Getting this error when I call your API: {"error":"invalid_api_key","status":401}. I copied the key straight '
    "from the dashboard, any idea what's wrong?",
    "Your checkout page throws this in the console and the pay button stays grey: TypeError: Cannot read properties of "
    "undefined (reading 'total') at renderSummary (checkout.js:214:31). Chrome 126 on a Mac.",
    'curl -X POST https://api.example.test/v1/orders -H \'Content-Type: application/json\' -d \'{"sku": "BP-2231", '
    '"qty": 2}\' returns {"error":"missing_field","field":"address"}. The docs do not list address as required.',
    "My order export fails with: ERROR 1062 (23000): Duplicate entry 'ORD-48213' for key 'orders.order_ref' when I "
    "re-import the CSV. Do I need to delete the old rows first?",
    'The webhook for refunds keeps retrying. Response from my server: HTTP 500 {"detail": "signature mismatch"}. '
    "Header received: X-Signature: t=1730000000,v1=ab12cd34. Did the signing secret change?",
]
```

- Stores a list of 5 item(s) under the name `CODE`.

`scripts/make_prompts.py`, lines 104 to 111:

```python
LANGUAGE = [
    "Mi pedido llegó dañado, ¿cómo solicito un reembolso?",
    "Ich habe vor zehn Tagen bestellt und noch keine Versandbestätigung bekommen. Können Sie den Status prüfen?",
    "Bonjour, j'ai été débité deux fois pour la même commande. Pouvez-vous annuler le deuxième paiement ?",
    "Olá, não consigo entrar na minha conta depois de mudar o número de telefone. O que devo fazer?",
    "Buongiorno, vorrei cambiare l'indirizzo di consegna dell'ordine 51877 prima che venga spedito, è possibile?",
]
LABEL_Q = "Classify this customer message with exactly one word from billing, shipping, account, other. Message: {m}"
```

- Stores a list of 5 item(s) under the name `LANGUAGE`.
- Stores the text `Classify this customer message with exactly one...` under the name `LABEL_Q`.

`scripts/make_prompts.py`, lines 112 to 125:

```python
LABEL = [
    ("My card was declined twice for the same subscription renewal.", "billing"),
    ("The courier left my parcel at the wrong address.", "shipping"),
    ("I cannot log in since I changed my password this morning.", "account"),
    ("Do you have a store where I can try the headphones first?", "other"),
    ("I was charged for express shipping but chose standard.", "billing"),
]


def long_message(rng: random.Random, index: int, lines: int) -> str:
    order = 40000 + rng.randrange(9000)
    date = f"{rng.choice(['March', 'April', 'May', 'June'])} {rng.randrange(1, 28)}"
    parts = [rng.choice(OPENERS).format(order=order, date=date)]
    chosen = [rng.choice(ITEMS) for _ in range(lines)]
```

- Stores a list of 5 item(s) under the name `LABEL`.
- Defines the function `long_message`. It returns text.
- Its parameters:
    - `rng` holds `random.Random`.
    - `index` holds a whole number.
    - `lines` holds a whole number.
- Stores the result of `40000 + rng.randrange(9000)` under the name `order`.
  - `+` is add.
  - The method `randrange` of `rng`.
- Stores a text built from pieces (an f-string) under the name `date`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - The method `choice` of `rng`.
  - The method `randrange` of `rng`.
- Stores a list of 1 item(s) under the name `parts`.
  - `.format(...)` fills `{}` places in text with values.
  - The method `choice` of `rng`.
- Stores a list built by looping under the name `chosen`.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - The method `choice` of `rng`.
  - `range` makes the numbers from 0 up to (not including) the given one.

`scripts/make_prompts.py`, lines 126 to 136:

```python
    total = sum(price for _, price in chosen)
    parts.append("Order details as shown in my confirmation email:")
    for n, (name, price) in enumerate(chosen, start=1):
        parts.append(
            f"  {n}. {name}, quantity 1, ${price:.2f}, status: {rng.choice(['shipped', 'shipped', 'delayed', 'packed'])}"
        )
    parts.append(f"  Order total: ${total:.2f}, payment: card ending {rng.randrange(1000, 9999)}.")
    parts.append(rng.choice(BODIES).format(days=rng.randrange(4, 15), total=f"${total + 6.99:.2f}"))
    if lines > 8:
        parts.append("Timeline of what happened, as far as I can reconstruct it from my emails and the carrier site:")
        for step in range(lines):
```

- Stores the result of calling `sum` under the name `total`.
  - `sum` adds up all the numbers.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Loop: the indented lines below run once for each item of `enumerate(chosen, start=1)`; `(n, (name, price))` names the current item.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - The method `choice` of `rng`.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - The method `randrange` of `rng`.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - `.format(...)` fills `{}` places in text with values.
  - The method `choice` of `rng`.
  - The method `randrange` of `rng`.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `+` is add.
- Decision: the indented lines below run only when `lines > 8` is true.
  - `>` means greater than.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
- Loop: the indented lines below run once for each item of `range(lines)`; `step` names the current item.
  - `range` makes the numbers from 0 up to (not including) the given one.

`scripts/make_prompts.py`, lines 137 to 148:

```python
            parts.append(
                f"  - Day {step + 1}: {rng.choice(['label created', 'handed to carrier', 'arrived at depot', 'out for delivery', 'delivery attempted', 'rescheduled'])}"
                f" (reference {rng.randrange(10**8, 10**9)}); I {rng.choice(['checked the page', 'called the depot', 'emailed you', 'waited'])}."
            )
    parts.append(rng.choice(CLOSERS))
    return "\n".join(parts)


def main() -> None:
    rng = random.Random(2610)
    rows: list[dict[str, str]] = []
    rows += [{"id": f"p{len(rows) + i + 1:02d}", "kind": "short", "text": t} for i, t in enumerate(SHORT)]
```

- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `+` is add.
  - The method `choice` of `rng`.
  - The method `randrange` of `rng`.
  - `**` is power.
- Calls `.append(...)` adds one item at the end of a list with 1 argument(s); the result is not kept.
  - `.append(...)` adds one item at the end of a list.
  - The method `choice` of `rng`.
- Ends the function and gives back the result of calling `'\n'.join` to the caller.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
- Defines the function `main`. It returns nothing (None).
- It takes no parameters.
- Stores the result of calling `random.Random` under the name `rng`.
  - `random.Random` makes a random-number generator that repeats for the same seed.
- Declares `rows` as a list of a dictionary from text to text and sets it to an empty list.
  - `x[key]` reads the item at a position or the dictionary entry for a key.
- Updates `rows` in place: `+=` applies `+` with a list built by looping and stores the result back.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
  - `+` is add.
  - `len` counts the items in a collection (or the characters in text).

`scripts/make_prompts.py`, lines 149 to 161:

```python
    rows += [
        {"id": f"p{len(rows) + i + 1:02d}", "kind": "long", "text": long_message(rng, i, n)}
        for i, n in enumerate(LONG_SIZES)
    ]
    rows += [{"id": f"p{len(rows) + i + 1:02d}", "kind": "code", "text": t} for i, t in enumerate(CODE)]
    rows += [{"id": f"p{len(rows) + i + 1:02d}", "kind": "language", "text": t} for i, t in enumerate(LANGUAGE)]
    rows += [
        {"id": f"p{len(rows) + i + 1:02d}", "kind": "label", "text": LABEL_Q.format(m=m), "expected_label": lab}
        for i, (m, lab) in enumerate(LABEL)
    ]
    out = Path(__file__).resolve().parent.parent / "data" / "prompts.jsonl"
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"wrote {len(rows)} prompts to {out}")
```

- Updates `rows` in place: `+=` applies `+` with a list built by looping and stores the result back.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `long_message`, a function of this file.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
  - `+` is add.
  - `len` counts the items in a collection (or the characters in text).
- Updates `rows` in place: `+=` applies `+` with a list built by looping and stores the result back.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
  - `+` is add.
  - `len` counts the items in a collection (or the characters in text).
- Updates `rows` in place: `+=` applies `+` with a list built by looping and stores the result back.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
  - `+` is add.
  - `len` counts the items in a collection (or the characters in text).
- Updates `rows` in place: `+=` applies `+` with a list built by looping and stores the result back.
  - A comprehension builds a list by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `.format(...)` fills `{}` places in text with values.
  - `enumerate` pairs each item with its position number (0, 1, 2, ...).
  - `+` is add.
  - `len` counts the items in a collection (or the characters in text).
- Stores the result of `Path(__file__).resolve().parent.parent / 'data' / 'prompt...` under the name `out`.
  - `/` is divide.
  - `.resolve(...)` turns a path into a full absolute path.
  - `Path` from the standard library module `pathlib`, which a file or folder location.
- Calls `.write_text(...)` writes text to a file, replacing it with 2 argument(s); the result is not kept.
  - `.write_text(...)` writes text to a file, replacing it.
  - `.join(...)` glues the pieces of a collection into one text, with the given text between them.
  - A comprehension builds a generator expression (items made one at a time) by looping: `for ... in ...` names each item, an optional `if` keeps only some, and the expression in front says what to store.
  - `+` is add.
  - `json.dumps` turns Python data into JSON text.
- Calls `print` writes text to the screen with 1 argument(s); the result is not kept.
  - `print` writes text to the screen.
  - An f-string (text starting with `f`) fills the `{...}` places with the values of the expressions written inside them.
  - `len` counts the items in a collection (or the characters in text).

`scripts/make_prompts.py`, lines 164 to 165:

```python
if __name__ == "__main__":
    main()
```

- Decision: the indented lines below run only when `__name__ == '__main__'` is true.
  - `==` means equal.
- Calls `main`, a function of this file; the result is not kept.
  - `main`, a function of this file.

## Try it yourself

1. Check that `scripts/make_prompts.py` is valid Python without running it (running it rewrites a committed data file).

```bash
.venv/bin/python -m py_compile scripts/make_prompts.py && echo 'compiles: scripts/make_prompts.py'
```

What you should see (captured from this repository):

```text
compiles: scripts/make_prompts.py
```

## Mistakes people make

- **Editing a generated file by hand.** The next run of the script would overwrite it. Change the script and run it again.
- **Using unseeded randomness.** Two runs would differ. The scripts create `random.Random(seed)` objects.
- **Letting the script read the clock.** A date inside the output would change every day; the scripts use fixed dates.
- **Forgetting to commit the output.** The tests read the committed file, not a fresh one.

## Check yourself

1. What does `scripts/make_prompts.py` do?

   *Answer:* Write data/prompts.jsonl: 50 customer messages to a shop's support desk, in five kinds.

2. Why are the data files generated by scripts and then committed?

   *Answer:* So a reader can see exactly how they were made, and a rerun gives the same bytes; the committed copy is what the tests and the README numbers rely on.

3. Why are the data files generated by scripts and then committed?

   *Answer:* So a reader can see exactly how they were made, and a rerun gives the same bytes; the committed copy is what the tests and the README numbers rely on.

4. Why are the data files generated by scripts and then committed?

   *Answer:* So a reader can see exactly how they were made, and a rerun gives the same bytes; the committed copy is what the tests and the README numbers rely on.

5. Why are the data files generated by scripts and then committed?

   *Answer:* So a reader can see exactly how they were made, and a rerun gives the same bytes; the committed copy is what the tests and the README numbers rely on.

## Further reading

- Python `random` module, https://docs.python.org/3/library/random.html (Python 3.13).

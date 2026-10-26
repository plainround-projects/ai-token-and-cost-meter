"""Write data/prompts.jsonl: 50 customer messages to a shop's support desk, in five kinds.

20 short questions, 15 long messages with pasted order details (lengths vary on purpose, one over 1,500
tokens), 5 with a code or error message, 5 in a language other than English and 5 that ask for a one-word
category label. Deterministic: running it twice writes the same file.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

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
OPENERS = [
    "Hi, I placed order #{order} on {date} and I am writing because something went wrong.",
    "Hello support team, order #{order} (placed {date}) has not gone the way I expected.",
    "Good morning. I am following up on order #{order} from {date}; here is everything I have so far.",
    "I have been a customer for years and this is the first time I need help. Order #{order}, {date}.",
]
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
CLOSERS = [
    "Please let me know what you need from me. I am happy to send more details.",
    "I would appreciate a reply today, since I need this sorted before the weekend.",
    "If it is easier to call, tell me a time and a number to use.",
    "Thank you for your help; I have attached nothing, but can reply with photos or screenshots.",
]
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
LANGUAGE = [
    "Mi pedido llegó dañado, ¿cómo solicito un reembolso?",
    "Ich habe vor zehn Tagen bestellt und noch keine Versandbestätigung bekommen. Können Sie den Status prüfen?",
    "Bonjour, j'ai été débité deux fois pour la même commande. Pouvez-vous annuler le deuxième paiement ?",
    "Olá, não consigo entrar na minha conta depois de mudar o número de telefone. O que devo fazer?",
    "Buongiorno, vorrei cambiare l'indirizzo di consegna dell'ordine 51877 prima che venga spedito, è possibile?",
]
LABEL_Q = "Classify this customer message with exactly one word from billing, shipping, account, other. Message: {m}"
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


if __name__ == "__main__":
    main()

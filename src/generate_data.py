"""Generate reproducible event-level data for an e-commerce experiment."""

from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

START = datetime(2026, 1, 5, tzinfo=timezone.utc)
CHANNELS = ("organic", "paid_search", "social", "email", "referral")
DEVICES = ("mobile", "desktop", "tablet")
COUNTRIES = ("US", "CA", "GB", "IN")


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def generate(output_dir: Path, n_users: int = 12_000, seed: int = 42) -> dict[str, int]:
    """Create users, assignments, events, and orders with a known treatment lift."""
    rng = random.Random(seed)
    users: list[dict] = []
    assignments: list[dict] = []
    events: list[dict] = []
    orders: list[dict] = []
    event_id = 1
    order_id = 1

    for i in range(1, n_users + 1):
        user_id = f"U{i:06d}"
        signup = START + timedelta(minutes=rng.randint(0, 27 * 24 * 60))
        channel = rng.choices(CHANNELS, weights=(32, 25, 18, 15, 10), k=1)[0]
        device = rng.choices(DEVICES, weights=(62, 32, 6), k=1)[0]
        country = rng.choices(COUNTRIES, weights=(58, 12, 12, 18), k=1)[0]
        variant = "treatment" if rng.random() < 0.5 else "control"

        users.append({
            "user_id": user_id,
            "signup_at": signup.isoformat(),
            "acquisition_channel": channel,
            "device": device,
            "country": country,
        })
        assignments.append({
            "user_id": user_id,
            "experiment_id": "checkout_progress_v1",
            "variant": variant,
            "assigned_at": signup.isoformat(),
        })

        # Treatment improves checkout completion, especially on mobile.
        view_prob = 0.82
        cart_prob = 0.38 + (0.025 if variant == "treatment" else 0)
        checkout_prob = 0.61 + (0.055 if variant == "treatment" else 0)
        if device == "mobile":
            checkout_prob -= 0.08
            if variant == "treatment":
                checkout_prob += 0.035

        timestamp = signup + timedelta(minutes=rng.randint(1, 180))
        session_id = f"S{i:06d}"
        events.append({"event_id": event_id, "user_id": user_id, "session_id": session_id,
                       "event_name": "session_start", "event_at": timestamp.isoformat()})
        event_id += 1

        if rng.random() < view_prob:
            timestamp += timedelta(seconds=rng.randint(10, 120))
            events.append({"event_id": event_id, "user_id": user_id, "session_id": session_id,
                           "event_name": "product_view", "event_at": timestamp.isoformat()})
            event_id += 1
            if rng.random() < cart_prob:
                timestamp += timedelta(seconds=rng.randint(20, 240))
                events.append({"event_id": event_id, "user_id": user_id, "session_id": session_id,
                               "event_name": "add_to_cart", "event_at": timestamp.isoformat()})
                event_id += 1
                if rng.random() < checkout_prob:
                    timestamp += timedelta(seconds=rng.randint(30, 300))
                    events.append({"event_id": event_id, "user_id": user_id, "session_id": session_id,
                                   "event_name": "purchase", "event_at": timestamp.isoformat()})
                    event_id += 1
                    amount = round(max(12, rng.lognormvariate(3.75, 0.55)), 2)
                    orders.append({"order_id": f"O{order_id:06d}", "user_id": user_id,
                                   "ordered_at": timestamp.isoformat(), "revenue": amount})
                    order_id += 1

    for name, rows in (("users", users), ("assignments", assignments),
                       ("events", events), ("orders", orders)):
        _write(output_dir / f"{name}.csv", rows)
    return {"users": len(users), "assignments": len(assignments),
            "events": len(events), "orders": len(orders)}


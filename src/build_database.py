"""Load raw CSV files into SQLite and materialize analytics models."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

SCHEMA = {
    "users": "user_id TEXT PRIMARY KEY, signup_at TEXT, acquisition_channel TEXT, device TEXT, country TEXT",
    "assignments": "user_id TEXT, experiment_id TEXT, variant TEXT, assigned_at TEXT",
    "events": "event_id INTEGER PRIMARY KEY, user_id TEXT, session_id TEXT, event_name TEXT, event_at TEXT",
    "orders": "order_id TEXT PRIMARY KEY, user_id TEXT, ordered_at TEXT, revenue REAL",
}


def build(raw_dir: Path, db_path: Path, sql_dir: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    with sqlite3.connect(db_path) as conn:
        for table, definition in SCHEMA.items():
            conn.execute(f"CREATE TABLE {table} ({definition})")
            with (raw_dir / f"{table}.csv").open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            placeholders = ",".join("?" for _ in rows[0])
            conn.executemany(
                f"INSERT INTO {table} VALUES ({placeholders})",
                [tuple(row.values()) for row in rows],
            )
        conn.executescript((sql_dir / "01_data_quality.sql").read_text())
        conn.executescript((sql_dir / "02_funnel_model.sql").read_text())
        conn.executescript((sql_dir / "03_experiment_metrics.sql").read_text())


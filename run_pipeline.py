"""Run the complete local analytics workflow."""

from __future__ import annotations

import json
import csv
import sqlite3
from pathlib import Path

from src.build_database import build
from src.experiment import analyze
from src.generate_data import generate
from src.report import create_report

ROOT = Path(__file__).resolve().parent


def main() -> None:
    counts = generate(ROOT / "data/raw")
    db_path = ROOT / "data/product_analytics.db"
    build(ROOT / "data/raw", db_path, ROOT / "sql")
    result = analyze(db_path)
    report_path = ROOT / "reports/experiment_report.html"
    create_report(db_path, result, report_path)
    (ROOT / "reports/experiment_result.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    with sqlite3.connect(db_path) as conn:
        for view in ("experiment_summary", "funnel_summary", "segment_results", "daily_experiment_results"):
            cursor = conn.execute(f"SELECT * FROM {view}")
            destination = ROOT / "data/processed" / f"{view}.csv"
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow([column[0] for column in cursor.description])
                writer.writerows(cursor.fetchall())
    print(f"Generated: {counts}")
    print(f"Conversion lift: {result['relative_lift']:.1%} (p={result['p_value']:.4f})")
    print(f"Decision: {result['recommendation']}")
    print(f"SRM check: {'pass' if result['sample_ratio_mismatch']['passed'] else 'fail'}")
    print(f"Power check: {'pass' if result['adequately_powered'] else 'fail'}")
    print(f"Dashboard: {report_path}")


if __name__ == "__main__":
    main()

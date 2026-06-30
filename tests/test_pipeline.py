import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.build_database import build
from src.generate_data import generate


class PipelineTests(unittest.TestCase):
    def test_generated_users_have_one_assignment(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            generate(path, n_users=250, seed=7)
            with (path / "assignments.csv").open() as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 250)
            self.assertEqual(len({row["user_id"] for row in rows}), 250)

    def test_funnel_has_both_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw, db = root / "raw", root / "test.db"
            generate(raw, n_users=500, seed=9)
            build(raw, db, Path(__file__).parents[1] / "sql")
            with sqlite3.connect(db) as conn:
                variants = conn.execute("SELECT COUNT(*) FROM funnel_summary").fetchone()[0]
            self.assertEqual(variants, 2)


if __name__ == "__main__":
    unittest.main()

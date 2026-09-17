"""Existing public-CLI checks for the credits prototype."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CreditTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = str(Path(self.directory.name) / "ledger.sqlite")

    def credit(self, tenant, event, account, amount):
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "credit_cli.py"),
                "ingest",
                "--database",
                self.database,
                "--tenant",
                tenant,
                "--event",
                event,
                "--account",
                account,
                "--amount",
                str(amount),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_distinct_deliveries_persist_across_processes(self):
        first = self.credit("a", "one", "wallet", 10)
        second = self.credit("a", "two", "wallet", 5)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(second.stdout), {"balance": 15})

    def test_tenants_have_separate_balances(self):
        first = self.credit("a", "one", "wallet", 10)
        second = self.credit("b", "one", "wallet", 4)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(second.stdout), {"balance": 4})

    def test_negative_amount_is_rejected(self):
        result = self.credit("a", "one", "wallet", -1)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Amount must be a nonnegative integer", result.stderr)


if __name__ == "__main__":
    unittest.main()

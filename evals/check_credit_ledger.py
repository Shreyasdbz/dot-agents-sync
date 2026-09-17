"""Exercise a disposable candidate's credit boundaries, not its explanation quality."""

import argparse
import io
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import closing
from pathlib import Path


class CreditBoundaryTests(unittest.TestCase):
    """Check persisted credit behavior without sharing assertions with trial actors."""

    def __init__(self, methodName, *, candidate):
        super().__init__(methodName)
        self.candidate = candidate

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        self.database = self.root / "ledger.sqlite"
        self.env = {
            **{key: os.environ[key] for key in ("PATH", "SystemRoot", "WINDIR") if key in os.environ},
            "HOME": str(self.root),
            "TMPDIR": str(self.root),
            "TEMP": str(self.root),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
        }

    def command(self, tenant="a", event="one", account="wallet", amount=7):
        """Build one public CLI delivery targeting only the temporary database."""
        return [
            sys.executable,
            str(self.candidate / "credit_cli.py"),
            "ingest",
            "--database",
            str(self.database),
            "--tenant",
            tenant,
            "--event",
            event,
            "--account",
            account,
            "--amount",
            str(amount),
        ]

    def deliver(self, **values):
        """Execute a delivery in a fresh process without inherited user credentials."""
        return subprocess.run(
            self.command(**values),
            cwd=self.candidate,
            env=self.env,
            capture_output=True,
            text=True,
            timeout=15,
        )

    def accepted(self, expected, **values):
        """Require a successful public result with an independently expected balance."""
        result = self.deliver(**values)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"balance": expected})

    def snapshot(self):
        """Read durable rows without creating or modifying the candidate database."""
        with closing(sqlite3.connect(self.database.as_uri() + "?mode=ro", uri=True)) as connection:
            return (
                connection.execute("SELECT * FROM balances ORDER BY tenant, account").fetchall(),
                connection.execute("SELECT * FROM deliveries ORDER BY tenant, event").fetchall(),
            )

    def test_replay_after_restart(self):
        self.accepted(7)
        before = self.snapshot()
        self.accepted(7)
        self.assertEqual(self.snapshot(), before)
        self.accepted(10, event="two", amount=3)

    def test_tenant_isolation(self):
        self.accepted(7)
        self.accepted(4, tenant="b", amount=4)
        self.assertEqual(self.snapshot()[0], [("a", "wallet", 7), ("b", "wallet", 4)])

    def test_conflicting_event_payload(self):
        self.accepted(7)
        before = self.snapshot()
        for values in ({"amount": 8}, {"account": "other"}):
            with self.subTest(values=values):
                result = self.deliver(**values)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertEqual(self.snapshot(), before)

    def test_zero_and_invalid_amount(self):
        self.accepted(0, amount=0)
        before = self.snapshot()
        self.accepted(0, amount=0)
        for values in ({"amount": 1}, {"event": "negative", "amount": -1}):
            with self.subTest(values=values):
                result = self.deliver(**values)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertEqual(self.snapshot(), before)

    def test_delivery_rolls_back_with_balance_failure(self):
        self.accepted(7)
        before = self.snapshot()
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute(
                """
                CREATE TRIGGER reject_update BEFORE UPDATE ON balances
                BEGIN SELECT RAISE(ABORT, 'injected balance failure'); END
                """
            )
            connection.commit()
        result = self.deliver(event="two")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.snapshot(), before)
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("DROP TRIGGER reject_update")
            connection.commit()
        self.accepted(14, event="two")

    def test_concurrent_replay(self):
        processes = []
        try:
            for _ in range(8):
                processes.append(
                    subprocess.Popen(
                        self.command(),
                        cwd=self.candidate,
                        env=self.env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                )
            for process in processes:
                stdout, stderr = process.communicate(timeout=15)
                self.assertEqual(process.returncode, 0, stderr)
                self.assertEqual(json.loads(stdout), {"balance": 7})
            self.assertEqual(self.snapshot(), ([("a", "wallet", 7)], [("a", "one", "wallet", 7)]))
        finally:
            for process in processes:
                if process.poll() is None:
                    process.kill()
                    process.communicate()

    def test_shared_service_boundary(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                """
import json
import sys
from credit_service import apply_credit
from ledger_store import LedgerStore

store = LedgerStore(sys.argv[1])
try:
    apply_credit(store, "a", "one", "wallet", 7)
    print(json.dumps(apply_credit(store, "a", "one", "wallet", 7)))
finally:
    store.close()
""",
                str(self.database),
            ],
            cwd=self.candidate,
            env=self.env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), 7)

    def wait_for_markers(self, markers, processes, phase):
        """Bound each handshake and fail explicitly if a candidate exits before reaching it."""
        deadline = time.monotonic() + 10
        while not all(marker.exists() for marker in markers):
            if time.monotonic() >= deadline or any(process.poll() is not None for process in processes):
                self.fail(f"Candidate writers did not reach {phase}")
            time.sleep(0.01)

    def contended_deliveries(self, payloads):
        """Initialize clients first, then release their writes through a real SQLite lock."""
        self.accepted(0, event="seed", amount=0)
        processes = []
        writer = sqlite3.connect(self.database)
        start = self.root / "start-delivery"
        try:
            for index, (account, amount) in enumerate(payloads):
                processes.append(
                    subprocess.Popen(
                        [
                            sys.executable,
                            "-c",
                            """
import json
import sys
import time
from pathlib import Path
from credit_service import apply_credit
from ledger_store import LedgerStore

store = LedgerStore(sys.argv[1])
try:
    store.connection.execute("PRAGMA busy_timeout = 15000")
    def before_write(sql):
        if sql.lstrip().upper().startswith(("BEGIN", "INSERT", "UPDATE")):
            Path(sys.argv[2]).touch()
    store.connection.set_trace_callback(before_write)
    Path(sys.argv[3]).touch()
    deadline = time.monotonic() + 15
    while not Path(sys.argv[4]).exists():
        if time.monotonic() >= deadline:
            raise TimeoutError("Parent did not release the delivery start barrier")
        time.sleep(0.01)
    account, amount = json.loads(sys.argv[5])
    print(json.dumps(apply_credit(store, "a", "one", account, amount)))
finally:
    store.close()
""",
                            str(self.database),
                            str(self.root / f"ready-{index}"),
                            str(self.root / f"initialized-{index}"),
                            str(start),
                            json.dumps([account, amount]),
                        ],
                        cwd=self.candidate,
                        env=self.env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                )
            self.wait_for_markers(
                [self.root / f"initialized-{index}" for index in range(len(payloads))],
                processes,
                "completed store initialization",
            )
            writer.execute("BEGIN IMMEDIATE")
            start.touch()
            # Both writers reach their transaction boundary before the lock is released.
            # A read performed outside that boundary has now observed the same absent event.
            self.wait_for_markers(
                [self.root / f"ready-{index}" for index in range(len(payloads))],
                processes,
                "the observed SQLite write boundary",
            )
            writer.commit()
            results = []
            for process in processes:
                stdout, stderr = process.communicate(timeout=15)
                results.append((process.returncode, stdout, stderr))
            return results
        finally:
            writer.close()
            for process in processes:
                if process.poll() is None:
                    process.kill()
                    process.communicate()

    def test_contended_replay(self):
        for returncode, stdout, stderr in self.contended_deliveries([("wallet", 7), ("wallet", 7)]):
            self.assertEqual(returncode, 0, stderr)
            self.assertEqual(json.loads(stdout), 7)
        self.assertEqual(
            self.snapshot(),
            ([("a", "wallet", 7)], [("a", "one", "wallet", 7), ("a", "seed", "wallet", 0)]),
        )

    def assert_contended_conflict(self, payloads):
        """Require one winner, one rejection, and durable state containing only the winner."""
        results = self.contended_deliveries(payloads)
        winners = [index for index, (returncode, _, _) in enumerate(results) if returncode == 0]
        self.assertEqual(len(winners), 1, results)
        winner = winners[0]
        account, amount = payloads[winner]
        self.assertEqual(json.loads(results[winner][1]), amount)
        balances = {("a", "wallet"): 0, ("a", account): amount}
        self.assertEqual(
            self.snapshot(),
            (
                sorted((tenant, name, value) for (tenant, name), value in balances.items()),
                [("a", "one", account, amount), ("a", "seed", "wallet", 0)],
            ),
        )

    def test_contended_amount_conflict(self):
        self.assert_contended_conflict([("wallet", 7), ("wallet", 8)])

    def test_contended_account_conflict(self):
        self.assert_contended_conflict([("wallet", 7), ("other", 7)])


def check(candidate):
    """Run authorized candidate code against temporary databases; this is not an OS sandbox."""
    candidate = Path(candidate).resolve()
    if not (candidate / "credit_cli.py").is_file():
        raise ValueError("Candidate must contain the credit-ledger fixture")
    suite = unittest.TestSuite(
        CreditBoundaryTests(name, candidate=candidate)
        for name in unittest.TestLoader().getTestCaseNames(CreditBoundaryTests)
    )
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    return {
        "passed": result.wasSuccessful(),
        "tests_run": result.testsRun,
        "failures": [test.id().split(" ", 1)[0].rsplit(".", 1)[-1] for test, _ in result.failures],
        "errors": [test.id().split(" ", 1)[0].rsplit(".", 1)[-1] for test, _ in result.errors],
        "output": output.getvalue(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    if not (args.candidate / "credit_cli.py").is_file():
        parser.error("Candidate must contain the credit-ledger fixture")
    report = check(args.candidate)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)

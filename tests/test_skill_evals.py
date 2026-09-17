"""Validate deliberately incomplete evaluation fixtures, not model capability."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def credit_fixture(tmp_path):
    fixture = tmp_path / "credit-ledger"
    shutil.copytree(ROOT / "evals/fixtures/credit-ledger", fixture)
    home = tmp_path / "home"
    home.mkdir()
    env = {
        **{key: os.environ[key] for key in ("PATH", "SystemRoot", "WINDIR") if key in os.environ},
        "HOME": str(home),
        "TMPDIR": str(tmp_path),
        "TEMP": str(tmp_path),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
    }
    return fixture, env


@pytest.fixture
def credit_checker():
    spec = importlib.util.spec_from_file_location("credit_checks", ROOT / "evals/check_credit_ledger.py")
    checks = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checks)
    return checks


def test_discovery_fixture_baseline_passes(credit_fixture):
    fixture, env = credit_fixture
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=fixture,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_discovery_fixture_exposes_persisted_duplicate(credit_fixture):
    fixture, env = credit_fixture
    command = [
        sys.executable,
        "credit_cli.py",
        "ingest",
        "--database",
        str(fixture / "ledger.sqlite"),
        "--tenant",
        "tenant-a",
        "--event",
        "event-1",
        "--account",
        "wallet",
        "--amount",
        "7",
    ]
    balances = []
    for _ in range(2):
        result = subprocess.run(command, cwd=fixture, env=env, capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stderr
        balances.append(json.loads(result.stdout)["balance"])
    assert balances == [7, 14], "Keep the faulty input intact; repair only an isolated trial copy"


def test_boundary_checker_rejects_the_faulty_input(credit_fixture, credit_checker):
    result = credit_checker.check(credit_fixture[0])
    assert result["passed"] is False
    assert result["tests_run"] == 10
    assert not result["errors"], result["output"]
    assert set(result["failures"]) == {
        "test_replay_after_restart",
        "test_conflicting_event_payload",
        "test_zero_and_invalid_amount",
        "test_concurrent_replay",
        "test_shared_service_boundary",
        "test_contended_replay",
        "test_contended_amount_conflict",
        "test_contended_account_conflict",
    }


def replay_control(store, *, serialized):
    """Build a disposable replay control; serialization is the independently varied condition."""
    original = store.read_text()
    boundary = "        with self.connection:\n"
    assert original.count(boundary) == 1
    control = original.replace(
        boundary,
        boundary
        + """            self.connection.execute("BEGIN IMMEDIATE")
            existing = self.connection.execute(
                "SELECT account, amount FROM deliveries WHERE tenant = ? AND event = ?",
                (tenant, event),
            ).fetchone()
            if existing is not None:
                if existing != (account, amount):
                    raise ValueError("Conflicting event reuse")
                return self.balance(tenant, account)
""",
    ).replace("INSERT OR REPLACE INTO deliveries", "INSERT INTO deliveries")
    if not serialized:
        control = control.replace('            self.connection.execute("BEGIN IMMEDIATE")\n', "")
    return control


@pytest.mark.parametrize("serialized", [False, True])
def test_boundary_checker_distinguishes_actual_atomicity(credit_fixture, credit_checker, serialized):
    store = credit_fixture[0] / "ledger_store.py"
    control = replay_control(store, serialized=serialized)
    store.write_text(control)
    result = credit_checker.check(credit_fixture[0])
    if serialized:
        assert result["passed"], result["output"]
    else:
        assert result["passed"] is False
        assert "test_contended_replay" in result["failures"]
        assert set(result["failures"]) <= {"test_contended_replay", "test_concurrent_replay"}
        assert not result["errors"], result["output"]
    assert result["tests_run"] == 10
    assert store.read_text() == control


def test_boundary_checker_accepts_transactional_initialization(credit_fixture, credit_checker):
    store = credit_fixture[0] / "ledger_store.py"
    control = replay_control(store, serialized=True)
    control = control.replace(
        '            """\n            CREATE TABLE',
        '            """\n            BEGIN IMMEDIATE;\n            CREATE TABLE',
        1,
    ).replace('            """\n        )', '            COMMIT;\n            """\n        )', 1)
    store.write_text(control)
    result = credit_checker.check(credit_fixture[0])
    assert result["passed"], result["output"]
    assert store.read_text() == control


def test_boundary_checker_rejects_unchecked_losing_insert(credit_fixture, credit_checker):
    store = credit_fixture[0] / "ledger_store.py"
    control = replay_control(store, serialized=False)
    original = """            self.connection.execute(
                "INSERT INTO deliveries VALUES (?, ?, ?, ?)",
                (tenant, event, account, amount),
            )
"""
    replacement = """            inserted = self.connection.execute(
                "INSERT OR IGNORE INTO deliveries VALUES (?, ?, ?, ?)",
                (tenant, event, account, amount),
            )
            if inserted.rowcount == 0:
                return self.balance(tenant, account)
"""
    assert control.count(original) == 1
    control = control.replace(original, replacement)
    store.write_text(control)
    result = credit_checker.check(credit_fixture[0])
    assert result["passed"] is False, "A losing insert must verify the winner's payload"
    assert not result["errors"], result["output"]
    assert set(result["failures"]) == {
        "test_contended_amount_conflict",
        "test_contended_account_conflict",
    }
    assert store.read_text() == control

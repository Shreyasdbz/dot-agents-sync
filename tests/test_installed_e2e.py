"""Black-box journeys through a built wheel, outside the source checkout.

No source imports, real user config, or provider/model invocations. Crash cases
use the installed engine's explicit fault seam; other journeys use only the CLI.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def execute(args, *, cwd, env=None, expected=0):
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=120)
    assert result.returncode == expected, (args, result.returncode, result.stdout, result.stderr)
    return result


@pytest.fixture(scope="session")
def installed_binary(tmp_path_factory):
    root = tmp_path_factory.mktemp("installed-wheel")
    uv = shutil.which("uv")
    assert uv, "Installed-wheel acceptance requires uv (also used by CI)"
    execute([uv, "build", "--wheel", "--out-dir", str(root / "dist")], cwd=ROOT)
    wheels = list((root / "dist").glob("*.whl"))
    assert len(wheels) == 1
    venv = root / "venv"
    execute([uv, "venv", "--python", sys.executable, str(venv)], cwd=root)
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    execute([uv, "pip", "install", "--python", str(python), str(wheels[0])], cwd=root)
    binary = venv / ("Scripts/dasync.exe" if os.name == "nt" else "bin/dasync")
    imported = execute(
        [str(python), "-I", "-c", "import dasync; print(dasync.__file__)"], cwd=root
    ).stdout.strip()
    assert Path(imported).is_relative_to(venv)
    return binary


class Journey:
    def __init__(self, binary, root):
        self.binary, self.root = binary, root
        self.home, self.project, self.catalog = root / "home", root / "project with spaces", root / "catalog"
        self.home.mkdir()
        self.project.mkdir()
        for directory in ("packages", "profiles"):
            shutil.copytree(ROOT / directory, self.catalog / directory)
        self.env = {
            **{
                key: os.environ[key]
                for key in ("PATH", "SystemRoot", "WINDIR", "TMPDIR", "TEMP", "LANG")
                if key in os.environ
            },
            "DASYNC_HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.home / "xdg-config"),
            "XDG_STATE_HOME": str(self.home / "xdg-state"),
            "XDG_CACHE_HOME": str(self.home / "xdg-cache"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
        }
        self.env.pop("PYTHONPATH", None)
        self.log = []

    def run(self, *args, user=False, error=None, code=None):
        scope = ["--scope", "user"] if user else ["--scope", "project", "--path", str(self.project)]
        result = execute(
            [str(self.binary), *args, *scope, "--json", "--no-input"],
            cwd=self.root,
            env=self.env,
            expected=code if code is not None else 2 if error else 0,
        )
        assert not result.stderr, result.stderr
        envelope = json.loads(result.stdout)
        assert envelope["version"] == 1
        if error:
            assert envelope["ok"] is False
            assert envelope["error"]["code"] == error, envelope
        else:
            assert envelope["ok"] is True, envelope
        self.log.append(envelope)
        return envelope.get("result", envelope.get("error"))

    def setup(self, provider="codex", *extra, user=False):
        return self.run(
            "setup",
            "--source",
            str(self.catalog),
            "--source-kind",
            "local",
            "--provider",
            provider,
            "--enable",
            "skill.propose",
            "--trust-source",
            "--yes",
            *extra,
            user=user,
        )

    def snapshot(self):
        return {
            str(p.relative_to(self.project)): p.read_bytes() for p in self.project.rglob("*") if p.is_file()
        }

    def save(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value))
        return str(path)


@pytest.fixture
def journey(installed_binary, tmp_path):
    return Journey(installed_binary, tmp_path)


@pytest.mark.parametrize("provider", ["codex", "claude", "cursor"])
def test_installed_lifecycle(journey, provider):
    j = journey
    assert j.run("capabilities")
    assert "plan" in j.run("schema")
    assert not j.run("status")["configured"]
    plan = j.run(
        "plan",
        "setup",
        "--source",
        str(j.catalog),
        "--source-kind",
        "local",
        "--provider",
        provider,
        "--enable",
        "skill.propose",
        "--trust-source",
    )
    assert not j.snapshot(), "Planning must not materialize project files"
    saved = j.save("setup.json", {"version": 1, "ok": True, "result": plan})
    j.run("apply", "--plan", saved, error="CONFIRMATION_REQUIRED")
    j.run("apply", "--plan", saved, "--dry-run", "--yes")
    assert not j.snapshot()
    receipt = j.run("apply", "--plan", saved, "--yes")
    for op in plan["operations"]:
        if op["action"] == "write":
            assert hashlib.sha256(Path(op["path"]).read_bytes()).hexdigest() == op["hash"]
            assert Path(op["path"]).is_relative_to(j.project)
    assert j.run("doctor")["healthy"]
    assert j.run("explain", "skill.propose")["packages"]
    assert j.run("search", "trip")["packages"]
    before = j.snapshot()
    assert not j.run("sync", "--yes")["changed"]
    assert j.snapshot() == before
    j.run("configure", "--enable", "skill.trip-publish", "--yes")
    # Configure changes desired state only; provider bytes stay unchanged.
    assert {p: b for p, b in j.snapshot().items() if p != ".dasync.yaml"} == {
        p: b for p, b in before.items() if p != ".dasync.yaml"
    }
    assert not j.run("doctor", code=1)["healthy"]
    j.run("sync", "--yes")
    delivered = [p for p in j.project.rglob("trip.html")]
    assert delivered and all(
        p.read_bytes() == (j.catalog / "packages/templates/trip-publish/trip.html").read_bytes()
        for p in delivered
    )
    j.run("rollback", "--receipt", receipt["receipt"], "--yes")
    assert j.snapshot() == before
    assert j.run("doctor")["healthy"]


def test_installed_stale_plan_drift_repair_and_backup(journey):
    j = journey
    j.setup()
    plan = j.run("plan", "configure", "--enable", "skill.investigate", "--apply")
    saved = j.save("stale.json", plan)
    j.run("configure", "--enable", "skill.pr-review", "--yes")
    before = j.snapshot()
    j.run("apply", "--plan", saved, "--yes", error="PLAN_INVALIDATED")
    assert j.snapshot() == before
    j.run("sync", "--yes")
    target = next(p for p in j.project.rglob("SKILL.md") if "propose" in str(p))
    original = target.read_bytes()
    target.write_text("User edited this; preserve it.")
    j.run("sync", "--yes", error="DRIFT")
    status = j.run("doctor", code=1)
    assert not status["healthy"]
    assert any(f["status"] == "modified" for f in status["files"])
    fixed = j.run("repair", "--conflict", "overwrite", "--yes")
    assert target.read_bytes() == original
    j.run("rollback", "--receipt", fixed["receipt"], "--before", "--yes")
    assert target.read_text() == "User edited this; preserve it."
    # A missing managed file can be repaired without approving an overwrite.
    target.unlink()
    j.run("repair", "--yes")
    assert target.read_bytes() == original
    assert j.run("doctor")["healthy"]


def test_installed_local_pin_and_reviewed_update(journey):
    j = journey
    j.setup()
    before = j.snapshot()
    source = j.catalog / "packages/skills/propose/SKILL.md"
    source.write_text(source.read_text() + "\nE2E catalog revision marker.\n")
    j.run("sync", "--yes", error="SOURCE_INTEGRITY")
    assert j.snapshot() == before
    plan = j.run("plan", "update")
    assert j.snapshot() == before
    j.run("apply", "--plan", j.save("update.json", plan), "--yes")
    assert any(b"E2E catalog revision marker." in b for b in j.snapshot().values())
    assert j.run("doctor")["healthy"]


def test_installed_user_project_isolation(journey):
    j = journey
    j.setup(user=True)
    user_config = (j.home / "config/config.yaml").read_bytes()
    j.setup("codex", "--inherit-user", "--enable", "skill.trip-publish")
    other = j.root / "another project"
    other.mkdir()
    first_project = j.project
    first_snapshot = j.snapshot()
    j.project = other
    j.setup("claude")
    assert not list(other.rglob("trip.html"))
    j.run("configure", "--enable", "skill.pr-review", "--apply", "--yes")
    assert (j.home / "config/config.yaml").read_bytes() == user_config
    j.project = first_project
    assert j.snapshot() == first_snapshot
    assert j.run("doctor")["healthy"]


def test_installed_unmanaged_collision_and_reversible_setup(journey):
    j = journey
    target = j.project / "AGENTS.md"
    target.write_text("Existing project instructions.")
    before = j.snapshot()
    j.run(
        "setup",
        "--source",
        str(j.catalog),
        "--source-kind",
        "local",
        "--enable",
        "skill.propose",
        "--yes",
        error="TRUST_REQUIRED",
    )
    j.run(
        "setup",
        "--source",
        str(j.catalog),
        "--source-kind",
        "local",
        "--enable",
        "skill.propose",
        "--yes",
        "--trust-source",
        error="UNMANAGED_COLLISION",
    )
    assert j.snapshot() == before
    receipt = j.setup("codex", "--conflict", "overwrite")
    j.run("rollback", "--receipt", receipt["receipt"], "--before", "--yes")
    assert j.snapshot() == before
    assert not j.run("status")["configured"]


def test_installed_setup_config_only(journey):
    j = journey
    j.setup("codex", "--config-only")
    assert set(j.snapshot()) == {".dasync.yaml"}
    assert not j.run("doctor", code=1)["healthy"]
    j.run("sync", "--yes")
    assert j.run("doctor")["healthy"]


def test_installed_setup_executable_approval(journey):
    j = journey
    packages = j.run("list", "--source", str(j.catalog), "--source-kind", "local")["packages"]
    digest = next(p["digest"] for p in packages if p["id"] == "hook.credential-path-guard")
    j.setup("codex", "--enable", "hook.credential-path-guard", "--approve-executable", digest)
    assert (j.project / ".codex/hooks.json").is_file()
    assert j.run("doctor")["healthy"]


def test_installed_private_context_grants_and_no_leak(journey):
    j = journey
    j.setup(user=True)
    private = j.root / "private.md"
    sentinel = "PRIVATE-E2E-BODY-NOT-FOR-OUTPUT"
    private.write_text(sentinel)
    j.run(
        "configure",
        "--bind-context",
        f"context.design-preferences={private}",
        "--grant-project",
        "allowed-project",
        "--binding-provider",
        "codex",
        "--yes",
        user=True,
    )
    j.setup("codex", "--project", "allowed-project")
    j.run("configure", "--enable", "context.design-preferences", "--apply", "--yes", error="PRIVATE_CONTEXT")
    j.run(
        "configure",
        "--enable",
        "context.design-preferences",
        "--allow-context",
        "context.design-preferences",
        "--apply",
        "--yes",
    )
    before = json.dumps(j.log) + repr(j.snapshot())
    assert sentinel not in before
    assert str(private) not in repr(j.snapshot())
    j.run("context", "locate", "context.design-preferences", "--consumer", "skill.propose", error="USAGE")
    located = j.run(
        "context",
        "locate",
        "context.design-preferences",
        "--consumer",
        "skill.propose",
        "--allow-private-path",
    )
    assert located["path"] == str(private)
    other = j.root / "denied project"
    other.mkdir()
    j.project = other
    j.setup("codex", "--project", "denied-project")
    j.run(
        "configure",
        "--enable",
        "context.design-preferences",
        "--allow-context",
        "context.design-preferences",
        "--apply",
        "--yes",
        error="PRIVATE_CONTEXT",
    )


def test_installed_competing_applies_have_one_winner(journey):
    j = journey
    j.setup()
    plan = j.run("plan", "configure", "--enable", "skill.investigate", "--apply")
    saved = j.save("competing.json", plan)
    args = [
        str(j.binary),
        "apply",
        "--plan",
        saved,
        "--scope",
        "project",
        "--path",
        str(j.project),
        "--yes",
        "--json",
        "--no-input",
    ]
    processes = [
        subprocess.Popen(
            args, cwd=j.root, env=j.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        for _ in range(2)
    ]
    results = []
    try:
        for process in processes:
            stdout, stderr = process.communicate(timeout=120)
            assert not stderr
            results.append((process.returncode, json.loads(stdout)))
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait()
    assert sorted(code for code, _ in results) == [0, 2]
    failed = next(value for code, value in results if code == 2)
    assert failed["error"]["code"] in {"PLAN_INVALIDATED", "LOCKED"}
    assert j.run("doctor")["healthy"]


@pytest.mark.skipif(os.name == "nt", reason="Symlink creation requires separate Windows privilege handling")
def test_installed_symlink_output_preserves_target(journey):
    j = journey
    j.setup()
    target = next(p for p in j.project.rglob("SKILL.md"))
    outside = j.root / "unrelated.md"
    outside.write_text("Do not change this file")
    target.unlink()
    target.symlink_to(outside)
    j.run("sync", "--yes", error="UNSAFE_PATH")
    assert outside.read_text() == "Do not change this file"


@pytest.mark.parametrize("stage", ["before_write", "after_write", "before_receipt"])
def test_installed_crash_then_cli_recovery(journey, stage):
    j = journey
    receipt = j.setup()
    before = j.snapshot()
    plan = j.run("plan", "configure", "--enable", "skill.investigate", "--apply")
    saved = j.save("crash.json", plan)
    python = j.binary.parent / ("python.exe" if os.name == "nt" else "python")
    script = """
import json, os, sys
from pathlib import Path
from dasync.config import Environment, Scope
from dasync.engine import Engine
plan = json.loads(Path(sys.argv[1]).read_text())
env = Environment.current()
engine = Engine(env, Scope.get(env, "project", plan["root"]))
def fault(stage, index):
    if stage == sys.argv[2]:
        os._exit(91)
engine.apply(plan, fault)
"""
    execute([str(python), "-I", "-c", script, saved, stage], cwd=j.root, env=j.env, expected=91)
    assert j.run("doctor", code=1)["pending_recovery"]
    after_crash = j.snapshot()
    assert j.run("repair", "--recover", "--dry-run")["pending"]
    assert j.snapshot() == after_crash
    j.run("repair", "--recover", "--yes")
    assert j.snapshot() == before
    status = j.run("doctor")
    assert status["healthy"]
    assert status["receipt"] == receipt["receipt"]

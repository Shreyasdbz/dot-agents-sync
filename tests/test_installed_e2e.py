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
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


class RecipeJourney:
    """The recipe machine journey uses only a wheel-installed executable."""

    def __init__(self, binary, root):
        self.binary, self.root = binary, root
        self.home, self.project = root / "home", root / "project"
        self.home.mkdir()
        self.project.mkdir()
        self.env = {**os.environ, "DASYNC_HOME": str(self.home)}
        self.env.pop("PYTHONPATH", None)
        self.candidates = []
        for index in (1, 2):
            author = root / f"source-{index}"
            author.mkdir()
            request = self.save(
                f"author-{index}",
                {
                    "operation": "recipe.create",
                    "source_id": f"{str(index) * 8}-{str(index) * 4}-4{str(index) * 3}-8{str(index) * 3}-{str(index) * 12}",
                    "kind": "Skill",
                    "id": "skill.review",
                    "name": "Review",
                    "description": "Synthetic review workflow.",
                    "license": "LicenseRef-Synthetic",
                },
            )
            self.call(
                "recipe", "create", "--request", request, "--scope", "project", "--path", str(author), "--yes"
            )
            self.candidates.append(self.call("recipe", "prepare", "--source", str(author)))

    def save(self, name, value):
        path = self.root / (name + ".json")
        path.write_text(json.dumps(value))
        return str(path)

    def call(self, *args, code=0):
        result = execute(
            [str(self.binary), *args, "--json", "--no-input"], cwd=self.root, env=self.env, expected=code
        )
        payload = json.loads(result.stdout)
        assert payload["protocol"] == 1 and not result.stderr
        return payload["result"] if payload["ok"] else payload["error"]

    def scoped(self, *args, code=0):
        return self.call("recipe", *args, "--scope", "project", "--path", str(self.project), code=code)

    def install(self):
        request = self.save(
            "registration",
            {
                "operation": "recipe.configure",
                "registrations": [
                    {"candidate": row["candidate"], "alias": f"source-{index}"}
                    for index, row in enumerate(self.candidates, 1)
                ],
                "enable": ["source-1/skill.review", "source-2/skill.review"],
            },
        )
        assert self.scoped("plan", "--request", request, code=2)["code"] == "TRUST_REQUIRED"
        plan = self.scoped("plan", "--request", request, "--trust-source")
        assert self.call("recipe", "sources")["sources"] == []
        assert not self.project.joinpath(".dasync.yaml").exists()
        saved = self.save("install-plan", {"protocol": 1, "ok": True, "result": plan})
        assert self.scoped("apply", "--plan", saved, code=2)["code"] == "CONFIRMATION_REQUIRED"
        result = self.scoped("apply", "--plan", saved, "--yes")
        return plan, result


def test_installed_recipe_two_source_machine_journey(installed_binary, tmp_path):
    j = RecipeJourney(installed_binary, tmp_path)
    bootstrap = j.call("describe")
    assert bootstrap["experimental"] and bootstrap["protocols"] == [1]
    plan, result = j.install()
    assert len(plan["mapping"]) == 2 and len(set(plan["mapping"].values())) == 2
    assert len(list(j.project.glob(".agents/skills/*/SKILL.md"))) == 2
    assert j.scoped("doctor")["healthy"]
    assert j.scoped("sync", "--yes") == {"changed": False, "receipt": result["receipt"], "operations": 0}
    listing = j.scoped("list", "--limit", "1")
    assert len(listing["items"]) == 1 and listing["next_offset"] == 1
    explanation = j.scoped("explain", "source-1/skill.review")
    assert explanation["selected"][0]["reasons"] == [{"kind": "direct"}]
    update = j.save("remove", {"operation": "recipe.configure", "remove": ["source-2/skill.review"]})
    selected = j.scoped("plan", "--request", update)
    j.scoped("apply", "--plan", j.save("remove-plan", selected), "--yes")
    for index in (1, 2):
        shutil.rmtree(tmp_path / f"source-{index}")
    request = j.save("restore", {"operation": "recipe.restore", "receipt": result["receipt"]})
    restore = j.scoped("plan", "--request", request)
    j.scoped("apply", "--plan", j.save("restore-plan", restore), "--yes")
    assert j.scoped("doctor")["healthy"] and len(list(j.project.glob(".agents/skills/*/SKILL.md"))) == 2
    j.scoped("deny", j.candidates[1]["source_id"], "--yes")
    assert j.scoped("plan", "--request", request, code=2)["code"] == "AUTHORITY_DENIED"


@pytest.mark.parametrize("stage", ["before_write", "after_write", "before_receipt"])
def test_installed_recipe_process_death_and_recovery(installed_binary, tmp_path, stage):
    j = RecipeJourney(installed_binary, tmp_path)
    _, installed = j.install()
    request = j.save("remove", {"operation": "recipe.configure", "remove": ["source-2/skill.review"]})
    plan = j.scoped("plan", "--request", request)
    saved = j.save("crash-plan", plan)
    python = installed_binary.parent / ("python.exe" if os.name == "nt" else "python")
    script = """
import json, os, sys
from dasync.config import Environment, Scope
from dasync.engine import Engine
plan = json.load(open(sys.argv[1]))
env = Environment.current()
engine = Engine(env, Scope.get(env, plan['scope'], plan['root']))
def fault(stage, index):
    if stage == sys.argv[2]:
        os._exit(91)
engine.apply(plan, fault)
"""
    execute([str(python), "-I", "-c", script, saved, stage], cwd=tmp_path, env=j.env, expected=91)
    assert j.scoped("doctor", code=1)["pending_recovery"]
    assert j.scoped("recover", "--dry-run")["pending"]
    j.scoped("recover", "--yes")
    doctor = j.scoped("doctor")
    assert doctor["healthy"] and doctor["receipt"] == installed["receipt"]
    assert len(list(j.project.glob(".agents/skills/*/SKILL.md"))) == 2


def test_installed_recipe_competing_applies(installed_binary, tmp_path):
    j = RecipeJourney(installed_binary, tmp_path)
    _, installed = j.install()
    request = j.save("remove", {"operation": "recipe.configure", "remove": ["source-2/skill.review"]})
    saved = j.save("concurrent-plan", j.scoped("plan", "--request", request))
    argv = [
        str(j.binary),
        "recipe",
        "apply",
        "--plan",
        saved,
        "--scope",
        "project",
        "--path",
        str(j.project),
        "--json",
        "--no-input",
        "--yes",
    ]

    def attempt(_):
        return subprocess.run(argv, cwd=j.root, env=j.env, text=True, capture_output=True, timeout=120)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, range(2)))
    envelopes = [json.loads(result.stdout) for result in results]
    assert sum(response["ok"] for response in envelopes) == 1
    rejected = next(response["error"] for response in envelopes if not response["ok"])
    assert rejected["code"] in ("LOCKED", "PLAN_INVALIDATED", "DRIFT")
    doctor = j.scoped("doctor")
    assert doctor["healthy"] and doctor["receipt"] != installed["receipt"]


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


def test_installed_wheel_license_and_metadata(installed_binary, tmp_path):
    python = installed_binary.parent / ("python.exe" if os.name == "nt" else "python")
    result = execute(
        [
            str(python),
            "-I",
            "-c",
            """
import importlib.metadata
import json
from dasync import __version__

distribution = importlib.metadata.distribution("dot-agents-sync")
print(json.dumps({
    "version": distribution.version,
    "runtime_version": __version__,
    "license": distribution.metadata["License-Expression"],
    "license_text": distribution.read_text("licenses/LICENSE"),
    "urls": distribution.metadata.get_all("Project-URL"),
    "entrypoints": [
        entry.value for entry in distribution.entry_points
        if entry.group == "console_scripts" and entry.name == "dasync"
    ],
}))
""",
        ],
        cwd=tmp_path,
    )
    metadata = json.loads(result.stdout)
    assert metadata["version"] == metadata["runtime_version"]
    assert execute([str(installed_binary), "--version"], cwd=tmp_path).stdout.strip() == metadata["version"]
    assert metadata["license"] == "MIT"
    assert metadata["license_text"].startswith("MIT License\n")
    assert 'THE SOFTWARE IS PROVIDED "AS IS"' in metadata["license_text"]
    assert "Repository, https://github.com/Shreyasdbz/dot-agents-sync" in metadata["urls"]
    assert metadata["entrypoints"] == ["dasync.cli:main"]


def test_installed_wheel_operates_the_collected_recipes_outside_the_checkout(installed_binary, tmp_path):
    home, project = tmp_path / "home", tmp_path / "real collection project"
    home.mkdir()
    project.mkdir()
    env = {
        **{key: os.environ[key] for key in ("PATH", "LANG", "TMPDIR") if key in os.environ},
        "DASYNC_HOME": str(home),
    }

    def call(*args, scoped=True, expected=0):
        target = ["--scope", "project", "--path", str(project)] if scoped else []
        result = execute(
            [str(installed_binary), "recipe", *args, *target, "--json", "--no-input"],
            cwd=tmp_path,
            env=env,
            expected=expected,
        )
        envelope = json.loads(result.stdout)
        assert envelope["protocol"] == 1
        return envelope.get("result", envelope.get("error"))

    registrations = []
    for directory in sorted((ROOT / "recipes").iterdir()):
        if (directory / "recipe.yaml").exists():
            candidate = call("prepare", "--source", str(directory), scoped=False)
            registrations.append({"candidate": candidate["candidate"], "alias": directory.name})
    assert len(registrations) == 7
    request = {
        "operation": "recipe.configure",
        "registrations": registrations,
        "trust_source": True,
        "enable": [
            "starter/skill.propose",
            "starter/skill.plan-out",
            "starter/skill.do-it",
            "starter/skill.investigate",
            "engineering/agent.architecture-reviewer",
            "design/skill.ui-design",
            "travel/agent.travel-planner",
            "travel/skill.trip-publish",
            "music/skill.curate-am-playlist",
        ],
    }
    request_file = tmp_path / "configure.json"
    request_file.write_text(json.dumps(request))
    plan = call("plan", "--request", str(request_file))
    assert plan["adapter_version"] == "recipe-codex/2"
    assert len(plan["graph"]["items"]) > 18
    reviewed = tmp_path / "reviewed.json"
    reviewed.write_text(json.dumps(plan))
    result = call("apply", "--plan", str(reviewed), "--yes")
    assert result["changed"] and call("doctor")["healthy"]
    assert not call("sync", "--yes")["changed"]
    assert (project / "AGENTS.md").is_file()
    assert len(list((project / ".codex/agents").glob("*.toml"))) == 2
    assert any(p.name == "trip.html" for p in project.rglob("*"))
    request_file.write_text(
        json.dumps({"operation": "recipe.configure", "enable": ["hooks/hook.credential-path-guard"]})
    )
    refusal = call("plan", "--request", str(request_file), expected=2)
    assert refusal["code"] == "EXECUTABLE_TRUST_REQUIRED"
    assert refusal["required_approval"]["kind"] == "executable-digest"


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


@pytest.mark.parametrize("provider", ["codex", "claude", "copilot", "cursor"])
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
    workspace_context = "context.workspace-pr-review"
    j.run(
        "configure",
        "--bind-context",
        f"{workspace_context}={private}",
        "--grant-project",
        "allowed-project",
        "--binding-provider",
        "codex",
        "--yes",
        user=True,
    )
    j.run(
        "configure",
        "--enable",
        workspace_context,
        "--allow-context",
        workspace_context,
        "--apply",
        "--yes",
    )
    j.run(
        "context",
        "locate",
        workspace_context,
        "--consumer",
        "skill.do-it",
        "--allow-private-path",
        error="PRIVATE_CONTEXT",
    )
    located = j.run(
        "context",
        "locate",
        workspace_context,
        "--consumer",
        "skill.pr-review",
        "--allow-private-path",
    )
    assert located["path"] == str(private)
    assert sentinel not in json.dumps(j.log)
    assert str(private) not in repr(j.snapshot())
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
    j.run("sync", "--yes", error="DRIFT")
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


@pytest.mark.skipif(os.name != "posix", reason="This terminal-driver boundary uses POSIX PTYs")
@pytest.mark.parametrize("scope", ["user", "project"])
@pytest.mark.parametrize("no_color", [False, True])
def test_installed_recipe_terminal_launch_help_resize_and_exit(installed_binary, tmp_path, scope, no_color):
    """Actual terminal driver, built wheel and termios restoration; no autopilot event injection."""
    import fcntl
    import pty
    import select
    import signal
    import struct
    import termios

    home, project = tmp_path / "home", tmp_path / "project"
    home.mkdir()
    project.mkdir()
    master, slave = pty.openpty()
    original_attributes = termios.tcgetattr(slave)
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 32, 100, 0, 0))
    env = {
        **{key: os.environ[key] for key in ("PATH", "LANG", "TMPDIR") if key in os.environ},
        "DASYNC_HOME": str(home),
        "TERM": "xterm-256color",
    }
    if no_color:
        env["NO_COLOR"] = "1"

    def controlling_terminal():
        os.setsid()
        fcntl.ioctl(slave, termios.TIOCSCTTY, 0)

    # Darwin invalidates slave ioctls when its controlling session leader exits.
    # Keep that session alive until the real CLI has exited and we checked its
    # restored attributes. A private pipe releases the wrapper afterward.
    release_read, release_write = os.pipe()
    wrapper = """
import os, subprocess, sys
code = subprocess.call(sys.argv[2:])
os.write(1, ("\\nPTY_CHILD_EXIT=" + str(code) + "\\n").encode())
os.read(int(sys.argv[1]), 1)
raise SystemExit(code)
"""
    process = subprocess.Popen(
        [
            str(installed_binary.parent / "python"),
            "-I",
            "-c",
            wrapper,
            str(release_read),
            str(installed_binary),
            "tui",
            "--scope",
            scope,
            *(["--path", str(project)] if scope == "project" else []),
        ],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        cwd=tmp_path,
        env=env,
        preexec_fn=controlling_terminal,
        pass_fds=(release_read,),
    )
    os.close(release_read)
    output = bytearray()

    def read_until(needle, timeout=8):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if select.select([master], [], [], 0.05)[0]:
                try:
                    output.extend(os.read(master, 65536))
                except OSError:
                    break
                if needle in output:
                    return True
            if process.poll() is not None:
                break
        return needle in output

    try:
        assert read_until(b"Welcome."), "Installed workspace did not render"
        os.write(master, b"\x1bOP")  # F1, through the terminal parser.
        assert read_until(b"Make yourself at home"), "Help binding did not render"
        os.write(master, b"\x1b")  # Escape, closing Help.
        time.sleep(0.4)
        fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack("HHHH", 22, 70, 0, 0))
        os.killpg(process.pid, signal.SIGWINCH)
        os.write(master, b"\x1b[21~")  # F10 must close even when the search input has focus.
        assert read_until(b"Closed."), "Terminal workspace did not close"
        assert read_until(b"PTY_CHILD_EXIT=0"), "Installed CLI did not exit successfully"
        assert termios.tcgetattr(slave) == original_attributes
        os.write(release_write, b"x")
        assert process.wait(timeout=5) == 0
        assert b"Traceback" not in output
        assert not list(home.rglob("*")) and not list(project.rglob("*"))
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        os.close(release_write)
        os.close(master)
        os.close(slave)

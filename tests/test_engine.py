import copy
import json
import os
import sqlite3
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from dasync.catalog import Catalog
from dasync.config import Scope
from dasync.engine import Engine
from dasync.errors import DasyncError


def test_setup_offline_idempotent(installed):
    engine, _, first = installed
    plan, _ = engine.build({"operation": "sync"})
    assert all(op["action"] == "keep" for op in plan["operations"])
    result = engine.apply(plan)
    assert not result["changed"]
    assert result["receipt"] == first["receipt"]
    assert not (engine.scope.root / ".dasync").exists()
    assert engine.status()["pending_changes"] == 0


def test_dry_plan_is_read_only(workspace):
    engine, config = workspace
    engine.build({"operation": "setup", "config": config, "trust_source": True})
    assert list(engine.scope.root.iterdir()) == []
    assert not engine.state.path.exists()


def test_unmanaged_collision(workspace):
    engine, config = workspace
    (engine.scope.root / "AGENTS.md").write_text("user instructions")
    with pytest.raises(DasyncError, match="Protected output"):
        engine.build({"operation": "setup", "config": config, "trust_source": True})
    assert (engine.scope.root / "AGENTS.md").read_text() == "user instructions"


def test_plan_invalidated(installed):
    engine, _, _ = installed
    plan, _ = engine.build({"operation": "sync"})
    target = Path(next(o["path"] for o in plan["operations"] if o["package"] == "skill.propose"))
    target.unlink()
    with pytest.raises(DasyncError, match="Plan inputs changed"):
        engine.apply(plan)


def test_tampered_plan(installed, tmp_path):
    engine, _, _ = installed
    plan, _ = engine.build({"operation": "sync"})
    plan["operations"][0]["path"] = str(tmp_path / "victim")
    with pytest.raises(DasyncError):
        engine.apply(plan)
    assert not (tmp_path / "victim").exists()


@pytest.mark.parametrize("stage", ["before_write", "after_write", "before_receipt"])
def test_failure_restores_config_and_outputs(installed, stage):
    engine, config, first = installed
    changed = copy.deepcopy(config)
    changed["packages"].append("skill.investigate")
    before = {str(p): p.read_bytes() for p in engine.scope.root.rglob("*") if p.is_file()}
    plan, _ = engine.build({"operation": "configure", "config": changed, "config_only": False})

    def fault(point, index):
        if point == stage:
            raise RuntimeError("injected")

    with pytest.raises(RuntimeError, match="injected"):
        engine.apply(plan, fault=fault)
    after = {str(p): p.read_bytes() for p in engine.scope.root.rglob("*") if p.is_file()}
    assert before == after
    assert engine.state.head(engine.scope.key)["id"] == first["receipt"]
    assert not engine.state.pending()


def test_rollback_is_a_new_reversible_receipt(installed):
    engine, config, first = installed
    changed = copy.deepcopy(config)
    changed["packages"].append("skill.investigate")
    plan, _ = engine.build({"operation": "configure", "config": changed, "config_only": False})
    second = engine.apply(plan)
    plan, _ = engine.build({"operation": "rollback", "receipt": first["receipt"]})
    third = engine.apply(plan)
    assert len({first["receipt"], second["receipt"], third["receipt"]}) == 3
    assert json.loads(engine.scope.config.read_text())["packages"] == config["packages"]
    plan, _ = engine.build({"operation": "rollback", "receipt": second["receipt"]})
    engine.apply(plan)
    assert "skill.investigate" in json.loads(engine.scope.config.read_text())["packages"]


def test_lock_contention(installed):
    engine, _, _ = installed
    script = (
        "from dasync.state import State; from pathlib import Path; s=State(Path("
        + repr(str(engine.state.directory))
        + "));\nwith s.lock(): pass"
    )
    with engine.state.lock():
        p = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
    assert p.returncode != 0
    assert "Another dasync transaction" in p.stderr


def test_configure_only_retains_drift_for_sync(installed):
    engine, config, first = installed
    target = engine.scope.root / ".claude/skills/dasync-skill-propose/SKILL.md"
    target.write_text("user modification")
    changed = copy.deepcopy(config)
    changed["packages"].append("skill.investigate")
    plan, _ = engine.build({"operation": "configure", "config": changed})
    assert all(op["package"] == "@config" for op in plan["operations"])
    engine.apply(plan)
    assert target.read_text() == "user modification"
    with pytest.raises(DasyncError) as caught:
        engine.build({"operation": "sync"})
    assert caught.value.code == "DRIFT"


def test_equal_unmanaged_file_is_not_silently_adopted(workspace):
    engine, config = workspace
    request = {"operation": "setup", "config": config, "trust_source": True}
    plan, outputs = engine.build(request)
    target = next(Path(o["path"]) for o in plan["operations"] if o["package"] == "skill.propose")
    target.parent.mkdir(parents=True)
    target.write_bytes(outputs[str(target)])
    with pytest.raises(DasyncError) as caught:
        engine.build(request)
    assert caught.value.code == "UNMANAGED_COLLISION"


@pytest.mark.skipif(sys.platform == "win32", reason="Symlink replacement requires POSIX coverage")
def test_setup_replaces_provider_config_and_rollback_restores_symlinks(workspace, tmp_path):
    engine, config = workspace
    config["providers"] = ["codex", "claude"]
    legacy_skill = engine.scope.root / ".agents/skills/legacy/SKILL.md"
    legacy_skill.parent.mkdir(parents=True)
    legacy_skill.write_text("legacy codex skill")
    external = tmp_path / "legacy-claude-skills"
    external.mkdir()
    (external / "legacy.md").write_text("legacy claude skill")
    claude_skills = engine.scope.root / ".claude/skills"
    claude_skills.parent.mkdir()
    claude_skills.symlink_to(external)
    root_instructions = engine.scope.root / "AGENTS.md"
    root_instructions.write_text("legacy instructions")

    request = {
        "operation": "setup",
        "config": config,
        "trust_source": True,
        "conflict": "overwrite",
        "replace_provider_config": True,
    }
    plan, _ = engine.build(request)
    assert any(
        op["path"] == str(claude_skills) and op["action"] == "delete" and op["before"]["type"] == "symlink"
        for op in plan["operations"]
    )
    applied = engine.apply(plan)
    assert claude_skills.is_dir() and not claude_skills.is_symlink()
    assert not legacy_skill.exists()
    assert list(claude_skills.rglob("SKILL.md"))

    rollback, _ = engine.build(
        {"operation": "rollback", "receipt": applied["receipt"], "before_receipt": True}
    )
    engine.apply(rollback)
    assert claude_skills.is_symlink()
    assert claude_skills.resolve() == external
    assert legacy_skill.read_text() == "legacy codex skill"
    assert root_instructions.read_text() == "legacy instructions"
    assert not engine.scope.config.exists()


def test_user_replacement_removes_only_copilot_inline_hooks(workspace):
    project_engine, config = workspace
    engine = Engine(project_engine.env, Scope.get(project_engine.env, "user", None))
    config["project"] = "user"
    config["providers"] = ["copilot"]
    settings_path = engine.scope.root / ".copilot/settings.json"
    settings_path.parent.mkdir()
    original = b'{"model":"gpt-test","hooks":{"preToolUse":[]}}\n'
    settings_path.write_bytes(original)
    request = {
        "operation": "setup",
        "config": config,
        "trust_source": True,
        "conflict": "overwrite",
        "replace_provider_config": True,
    }
    plan, _ = engine.build(request)
    sanitized = next(op for op in plan["operations"] if op["path"] == str(settings_path))
    assert sanitized["package"] == "@preserved"
    applied = engine.apply(plan)
    assert json.loads(settings_path.read_text()) == {"model": "gpt-test"}
    assert str(settings_path) not in engine.state.head(engine.scope.key)["owned"]

    rollback, _ = engine.build(
        {"operation": "rollback", "receipt": applied["receipt"], "before_receipt": True}
    )
    engine.apply(rollback)
    assert settings_path.read_bytes() == original


@pytest.mark.skipif(sys.platform == "win32", reason="Symlink restoration requires POSIX coverage")
def test_rollback_before_restores_drifted_type_and_mode(installed, tmp_path):
    engine, _, _ = installed
    managed = [
        Path(path)
        for path, owner in engine.state.head(engine.scope.key)["owned"].items()
        if owner["package"] == "skill.propose"
    ]
    symlink_path, mode_path = managed[:2]
    external = tmp_path / "user-skill.md"
    external.write_text("user skill")
    symlink_path.unlink()
    symlink_path.symlink_to(external)
    mode_path.write_text("private user edit")
    mode_path.chmod(0o600)

    plan, _ = engine.build({"operation": "sync", "conflict": "overwrite"})
    overwritten = engine.apply(plan)
    rollback, _ = engine.build(
        {"operation": "rollback", "receipt": overwritten["receipt"], "before_receipt": True}
    )
    engine.apply(rollback)

    assert symlink_path.is_symlink()
    assert os.readlink(symlink_path) == str(external)
    assert mode_path.read_text() == "private user edit"
    assert stat.S_IMODE(mode_path.stat().st_mode) == 0o600
    with pytest.raises(DasyncError) as caught:
        engine.build({"operation": "sync"})
    assert caught.value.code == "UNMANAGED_COLLISION"


def test_project_copilot_replacement_covers_documented_sources(workspace):
    engine, config = workspace
    config["providers"] = ["copilot"]
    config["packages"] = ["hook.credential-path-guard"]
    package = Catalog(config["source"]).packages["hook.credential-path-guard"]
    config["approved_executables"] = [package.digest]
    old_paths = [
        engine.scope.root / "AGENTS.md",
        engine.scope.root / "CLAUDE.md",
        engine.scope.root / ".github/copilot-instructions.md",
    ]
    for path in old_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("legacy instructions")
    settings_paths = [
        engine.scope.root / ".github/copilot/settings.json",
        engine.scope.root / ".github/copilot/settings.local.json",
        engine.scope.root / ".claude/settings.json",
        engine.scope.root / ".claude/settings.local.json",
    ]
    for path in settings_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"model":"keep","hooks":{"preToolUse":[{"type":"command","bash":"old"}]}}')
    workflow = engine.scope.root / ".github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("name: keep")
    request = {
        "operation": "setup",
        "config": config,
        "trust_source": True,
        "conflict": "overwrite",
        "replace_provider_config": True,
    }
    plan, _ = engine.build(request)
    planned = {op["path"] for op in plan["operations"]}
    assert all(str(path) in planned for path in [*old_paths, *settings_paths])
    engine.apply(plan)
    assert all(not path.exists() for path in old_paths)
    assert all(json.loads(path.read_text()) == {"model": "keep"} for path in settings_paths)
    assert workflow.read_text() == "name: keep"
    hooks = json.loads((engine.scope.root / ".github/hooks/dasync-hooks.json").read_text())
    assert hooks["version"] == 1


def test_claude_settings_preserve_non_hook_values(workspace):
    project_engine, config = workspace
    engine = Engine(project_engine.env, Scope.get(project_engine.env, "user", None))
    config["project"] = "user"
    config["providers"] = ["claude"]
    config["packages"] = ["hook.credential-path-guard"]
    package = Catalog(config["source"]).packages["hook.credential-path-guard"]
    config["approved_executables"] = [package.digest]
    settings_path = engine.scope.root / ".claude/settings.json"
    settings_path.parent.mkdir()
    settings_path.write_text(
        '{"model":"keep","permissions":{"deny":["Read(./.env)"]},"hooks":{"Stop":[{"command":"old"}]}}'
    )
    request = {
        "operation": "setup",
        "config": config,
        "trust_source": True,
        "conflict": "overwrite",
        "replace_provider_config": True,
    }
    engine.apply(engine.build(request)[0])
    settings = json.loads(settings_path.read_text())
    assert settings["model"] == "keep"
    assert settings["permissions"] == {"deny": ["Read(./.env)"]}
    assert "PreToolUse" in settings["hooks"]
    assert all(op["action"] == "keep" for op in engine.build({"operation": "sync"})[0]["operations"])


def test_copilot_disabled_hooks_block_selected_hook(workspace):
    engine, config = workspace
    config["providers"] = ["copilot"]
    config["packages"] = ["hook.credential-path-guard"]
    package = Catalog(config["source"]).packages["hook.credential-path-guard"]
    config["approved_executables"] = [package.digest]
    settings = engine.scope.root / ".github/copilot/settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text('{"disableAllHooks":true}')
    with pytest.raises(DasyncError) as caught:
        engine.build(
            {
                "operation": "setup",
                "config": config,
                "trust_source": True,
                "conflict": "overwrite",
                "replace_provider_config": True,
            }
        )
    assert caught.value.code == "CAPABILITY_BLOCKED"


def test_custom_copilot_home_is_rejected_for_user_scope(workspace, monkeypatch, tmp_path):
    project_engine, config = workspace
    engine = Engine(project_engine.env, Scope.get(project_engine.env, "user", None))
    config["project"] = "user"
    config["providers"] = ["copilot"]
    monkeypatch.setenv("COPILOT_HOME", str(tmp_path / "custom-copilot"))
    with pytest.raises(DasyncError) as caught:
        engine.build({"operation": "setup", "config": config, "trust_source": True})
    assert caught.value.code == "SCOPE_INVALID"


def test_recreated_replacement_path_is_collision_protected(workspace):
    engine, config = workspace
    config["providers"] = ["claude"]
    legacy = engine.scope.root / ".claude/skills/legacy/SKILL.md"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("original")
    request = {
        "operation": "setup",
        "config": config,
        "trust_source": True,
        "conflict": "overwrite",
        "replace_provider_config": True,
    }
    applied = engine.apply(engine.build(request)[0])
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text("new user file")
    with pytest.raises(DasyncError) as caught:
        engine.build({"operation": "rollback", "receipt": applied["receipt"], "before_receipt": True})
    assert caught.value.code == "UNMANAGED_COLLISION"
    assert legacy.read_text() == "new user file"


def test_regular_file_discovery_root_is_replaced(workspace):
    engine, config = workspace
    config["providers"] = ["claude"]
    root = engine.scope.root / ".claude/skills"
    root.parent.mkdir()
    root.write_text("stray file")
    request = {
        "operation": "setup",
        "config": config,
        "trust_source": True,
        "conflict": "overwrite",
        "replace_provider_config": True,
    }
    plan, _ = engine.build(request)
    assert next(op for op in plan["operations"] if op["path"] == str(root))["action"] == "delete"
    engine.apply(plan)
    assert root.is_dir()
    assert list(root.rglob("SKILL.md"))


def test_engine_rejects_config_only_replacement(workspace):
    engine, config = workspace
    with pytest.raises(DasyncError) as caught:
        engine.build(
            {
                "operation": "setup",
                "config": config,
                "trust_source": True,
                "conflict": "overwrite",
                "replace_provider_config": True,
                "config_only": True,
            }
        )
    assert caught.value.code == "PLAN_INVALID"


def test_directory_at_managed_file_path_is_rejected(installed):
    engine, _, _ = installed
    target = Path(
        next(
            path
            for path, owner in engine.state.head(engine.scope.key)["owned"].items()
            if owner["package"] == "@policies"
        )
    )
    target.unlink()
    target.mkdir()
    (target / "keep.txt").write_text("user content")
    with pytest.raises(DasyncError) as caught:
        engine.build({"operation": "sync"})
    assert caught.value.code == "UNSAFE_PATH"
    status = engine.status()
    assert next(item for item in status["files"] if item["path"] == str(target))["status"] == "modified"
    assert (target / "keep.txt").read_text() == "user content"


def test_previous_receipt_observation_format_remains_rollback_compatible(installed):
    engine, _, receipt = installed
    with sqlite3.connect(engine.state.path) as db:
        payload = json.loads(
            db.execute("SELECT payload FROM receipts WHERE id=?", (receipt["receipt"],)).fetchone()[0]
        )
        for owner in payload["owned"].values():
            owner.pop("type", None)
        for backup in payload["backups"]:
            backup["before"].pop("type", None)
            backup["after"].pop("type", None)
        db.execute(
            "UPDATE receipts SET payload=? WHERE id=?",
            (json.dumps(payload), receipt["receipt"]),
        )
        db.commit()
    rollback, _ = engine.build(
        {"operation": "rollback", "receipt": receipt["receipt"], "before_receipt": True}
    )
    engine.apply(rollback)
    assert not engine.scope.config.exists()


def test_previous_journal_observation_format_remains_recovery_compatible(installed):
    engine, config, _ = installed
    changed = copy.deepcopy(config)
    changed["packages"].append("skill.investigate")
    plan, _ = engine.build({"operation": "configure", "config": changed, "config_only": False})

    def interrupt(stage, index):
        if stage == "before_write":
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        engine.apply(plan, fault=interrupt)
    with sqlite3.connect(engine.state.path) as db:
        row = db.execute("SELECT id, payload FROM journal").fetchone()
        payload = json.loads(row[1])
        for item in payload["files"]:
            item["before"].pop("type", None)
            item["after"].pop("type", None)
        db.execute("UPDATE journal SET payload=? WHERE id=?", (json.dumps(payload), row[0]))
        db.commit()
    recovered = engine.state.recover(engine.scope.key, engine._validate_target)
    assert recovered["recovered"] == [row[0]]
    assert not engine.state.pending()
    assert engine.status()["pending_changes"] == 0

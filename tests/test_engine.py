import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
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

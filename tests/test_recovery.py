import copy
import json
import os
import subprocess
import sys

import pytest
from dasync.errors import DasyncError


def test_overwrite_backup_is_recoverable(workspace):
    engine, config = workspace
    target = engine.scope.root / "AGENTS.md"
    target.write_text("original unmanaged instructions")
    plan, _ = engine.build(
        {"operation": "setup", "config": config, "trust_source": True, "conflict": "overwrite"}
    )
    result = engine.apply(plan)
    plan, _ = engine.build({"operation": "rollback", "receipt": result["receipt"], "before_receipt": True})
    engine.apply(plan)
    assert target.read_text() == "original unmanaged instructions"
    assert not engine.scope.config.exists()
    assert str(target) not in engine.state.head(engine.scope.key)["owned"]


def test_crash_recovery(installed, tmp_path):
    engine, config, first = installed
    config = copy.deepcopy(config)
    config["packages"].append("skill.investigate")
    plan, _ = engine.build({"operation": "configure", "config": config, "config_only": False})
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))
    script = """
import json, os, sys
from pathlib import Path
from dasync.config import Environment, Scope
from dasync.engine import Engine
env = Environment.current()
plan = json.loads(Path(sys.argv[1]).read_text())
engine = Engine(env, Scope.get(env, 'project', plan['root']))
def crash(stage, index):
    if stage == 'after_write': os._exit(91)
engine.apply(plan, crash)
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(path)],
        env={**os.environ, "DASYNC_HOME": str(engine.env.home)},
        capture_output=True,
    )
    assert result.returncode == 91, result.stderr
    assert engine.state.pending()
    engine.state.recover(engine.scope.key, engine._validate_target)
    assert not engine.state.pending()
    assert engine.state.head(engine.scope.key)["id"] == first["receipt"]
    assert engine.status()["pending_changes"] == 0


def test_conflicting_external_change_is_preserved(installed):
    engine, config, _ = installed
    config = copy.deepcopy(config)
    config["packages"].append("skill.investigate")
    plan, _ = engine.build({"operation": "configure", "config": config, "config_only": False})
    first_write = next(op for op in plan["operations"] if op["action"] != "keep")
    from pathlib import Path

    def edit(stage, index):
        if stage == "after_write":
            Path(first_write["path"]).write_text("external collaborator change")
            raise RuntimeError("external write")

    with pytest.raises(DasyncError) as caught:
        engine.apply(plan, edit)
    assert caught.value.code == "RECOVERY_CONFLICT"
    assert Path(first_write["path"]).read_text() == "external collaborator change"
    assert engine.state.pending()

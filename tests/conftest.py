from pathlib import Path

import pytest
from dasync.catalog import pin
from dasync.config import Environment, Scope, initial
from dasync.engine import Engine

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def workspace(tmp_path):
    home, project = tmp_path / "home", tmp_path / "project"
    home.mkdir()
    project.mkdir()
    env = Environment(home, home / "config/config.yaml", home / "state", home / "cache")
    scope = Scope.get(env, "project", str(project))
    config = initial(
        "example",
        pin(str(ROOT), "local"),
        ["codex", "claude", "copilot", "cursor"],
        ["skill.propose"],
    )
    return Engine(env, scope), config


@pytest.fixture
def installed(workspace):
    engine, config = workspace
    plan, _ = engine.build({"operation": "setup", "config": config, "trust_source": True})
    result = engine.apply(plan)
    return engine, config, result

import copy

import pytest
from dasync.catalog import Catalog
from dasync.config import Scope
from dasync.engine import Engine
from dasync.errors import DasyncError
from dasync.resolver import resolve


def test_user_project_separation_and_inheritance(workspace):
    project_engine, project = workspace
    env = project_engine.env
    user_engine = Engine(env, Scope.get(env, "user", None))
    user = copy.deepcopy(project)
    user["project"] = "user"
    user["packages"] = ["skill.investigate"]
    plan, _ = user_engine.build({"operation": "setup", "config": user, "trust_source": True})
    user_engine.apply(plan)
    user_bytes = env.config.read_bytes()
    project["inherit_user"] = True
    plan, _ = project_engine.build({"operation": "setup", "config": project, "trust_source": True})
    assert "skill.investigate" in plan["graph"]["inherited"]
    assert all(op["path"].startswith(str(project_engine.scope.root)) for op in plan["operations"])
    project_engine.apply(plan)
    assert env.config.read_bytes() == user_bytes
    assert user_engine.status()["pending_changes"] == 0


def test_different_inherited_pin_is_explicit_conflict(workspace):
    engine, config = workspace
    user = copy.deepcopy(config)
    user["source"]["revision"] = "a" * 40
    config["inherit_user"] = True
    with pytest.raises(DasyncError) as caught:
        resolve(Catalog(config["source"]), config, engine.scope, user)
    assert caught.value.code == "INHERITANCE_CONFLICT"

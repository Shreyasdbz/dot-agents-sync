"""Executable authority and aggregate policy ownership for the real collected content."""

import copy
import itertools
import shutil

import pytest
from dasync.collection import SOURCE_IDS
from dasync.config import Environment, Scope
from dasync.engine import Engine
from dasync.errors import DasyncError
from dasync.recipe_approvals import executable_state
from dasync.recipe_engine import deny, registry
from dasync.recipe_sources import Snapshots
from test_collection_recipes import HOOK, environment, hook_approval
from test_collection_recipes import collected as collected
from test_recipes import apply


def isolated_hook(tmp_path, collected):
    tmp_path.mkdir(parents=True, exist_ok=True)
    source = tmp_path / "hook-source"
    shutil.copytree(collected[0] / "hooks", source)
    home, project = tmp_path / "home", tmp_path / "project with spaces"
    home.mkdir()
    project.mkdir()
    env = Environment(home, home / "config/config.yaml", home / "state", tmp_path / "cache")
    engine = Engine(env, Scope.get(env, "project", str(project)))
    candidate = Snapshots(env.cache).prepare(source)
    request = {
        "operation": "recipe.configure",
        "registrations": [{"candidate": candidate["candidate"], "alias": "hooks"}],
        "trust_source": True,
        "enable": ["hooks/" + HOOK[1]],
        "approve_executables": [hook_approval(env.cache, candidate["candidate"])],
    }
    return engine, source, request


def snapshot_installation(engine):
    return (
        {
            str(path.relative_to(engine.scope.root)): (path.read_bytes(), path.stat().st_mode & 0o777)
            for path in engine.scope.root.rglob("*")
            if path.is_file()
        },
        copy.deepcopy(engine.state.head(engine.scope.key)),
        registry(engine),
        executable_state(engine),
    )


def test_hook_update_cannot_reuse_an_old_digest_or_change_runtime_through_the_launcher(
    tmp_path, collected, monkeypatch
):
    engine, source, request = isolated_hook(tmp_path, collected)
    plan, _ = apply(engine, request)
    original_runtime = plan["graph"]["hook_runtime"]
    with monkeypatch.context() as patch:
        patch.setattr("sys.executable", "/another/python")
        assert all(
            op["action"] == "keep" for op in engine.build({"operation": "recipe.sync"})[0]["operations"]
        )
    script = source / "items" / HOOK[1] / "guard.py"
    script.write_bytes(script.read_bytes() + b"\n# Reviewed revision\n")
    candidate = Snapshots(engine.env.cache).prepare(source)
    update = {
        "operation": "recipe.configure",
        "registrations": [{"candidate": candidate["candidate"], "alias": "hooks"}],
        "trust_source": True,
    }
    before = snapshot_installation(engine)
    with pytest.raises(DasyncError) as rejected:
        engine.build(update)
    assert rejected.value.code == "EXECUTABLE_TRUST_REQUIRED"
    with pytest.raises(DasyncError) as rejected:
        engine.build({**update, "approve_executables": request["approve_executables"]})
    assert rejected.value.code == "EXECUTABLE_APPROVAL_INVALID" and snapshot_installation(engine) == before
    plan, _ = apply(
        engine, {**update, "approve_executables": [hook_approval(engine.env.cache, candidate["candidate"])]}
    )
    assert plan["graph"]["hook_runtime"] == original_runtime


def test_offline_hook_restore_still_requires_current_approval_and_authority(tmp_path, collected):
    engine, source, request = isolated_hook(tmp_path, collected)
    _, installed = apply(engine, request)
    original = {
        str(p.relative_to(engine.scope.root)): p.read_bytes()
        for p in engine.scope.root.rglob("*")
        if p.is_file()
    }
    apply(engine, {"operation": "recipe.configure", "remove": ["hooks/" + HOOK[1]]})
    shutil.rmtree(engine.env.cache)
    shutil.rmtree(source)
    _, restored = apply(engine, {"operation": "recipe.restore", "receipt": installed["receipt"]})
    assert restored["changed"]
    assert {
        str(p.relative_to(engine.scope.root)): p.read_bytes()
        for p in engine.scope.root.rglob("*")
        if p.is_file()
    } == original
    # Simulate loss of local approval metadata; receipt bytes cannot recreate the grant.
    with engine.state.connect(write=True) as db:
        db.execute("DELETE FROM metadata WHERE name='recipe-executables'")
        db.commit()
    with pytest.raises(DasyncError) as rejected:
        engine.build({"operation": "recipe.restore", "receipt": installed["receipt"]})
    assert rejected.value.code == "EXECUTABLE_TRUST_REQUIRED"
    deny(engine, HOOK[0])
    with pytest.raises(DasyncError) as rejected:
        engine.build({"operation": "recipe.restore", "receipt": installed["receipt"]})
    assert rejected.value.code == "AUTHORITY_DENIED"


def test_all_hook_write_boundaries_keep_approval_and_registration_atomic(tmp_path, collected):
    probe, _, request = isolated_hook(tmp_path / "probe", collected)
    plan, _ = probe.build(request)
    writes = sum(op["action"] != "keep" for op in plan["operations"])
    for stage, position, interruption in itertools.product(
        ("before_write", "after_write", "before_receipt"), range(writes), (False, True)
    ):
        if stage == "before_receipt" and position:
            continue
        engine, _, request = isolated_hook(tmp_path / f"{stage}-{position}-{interruption}", collected)
        plan, _ = engine.build(request)
        before = snapshot_installation(engine)
        exception = KeyboardInterrupt if interruption else RuntimeError

        def fault(event, index):
            if event == stage and index == position:
                raise exception("Synthetic hook transaction interruption")

        with pytest.raises(exception):
            engine.apply(plan, fault)
        assert executable_state(engine)["generation"] == 0 and not registry(engine)["sources"]
        if interruption:
            assert engine.state.pending()
            engine.state.recover(engine.scope.key, engine._validate_target)
        assert not engine.state.pending() and snapshot_installation(engine) == before
        engine.apply(plan)
        assert engine.status()["pending_changes"] == 0


def test_native_policy_aggregate_preserves_unmanaged_originals_and_contributor_denial(tmp_path, collected):
    engine, request = environment(tmp_path, collected, groups=("starter", "engineering"))
    original = engine.scope.root / "AGENTS.md"
    original.write_text("Human-owned repository guidance\n")
    request["enable"] = ["engineering/agent.architecture-reviewer"]
    with pytest.raises(DasyncError) as rejected:
        engine.build(request)
    assert rejected.value.code == "UNMANAGED_COLLISION"
    request["conflict"] = "overwrite"
    plan, _ = engine.build(request)
    operation = next(op for op in plan["operations"] if op["path"] == str(original))
    assert len(operation["contributors"]) == 3

    def interrupted(stage, index):
        if stage == "before_receipt":
            raise RuntimeError("Rollback the complete aggregate")

    before = snapshot_installation(engine)
    with pytest.raises(RuntimeError):
        engine.apply(plan, interrupted)
    assert snapshot_installation(engine) == before
    result = engine.apply(plan)
    deny(engine, SOURCE_IDS["starter"] + "/policy.communication")
    with pytest.raises(DasyncError) as rejected:
        engine.build({"operation": "recipe.restore", "receipt": result["receipt"]})
    assert rejected.value.code == "AUTHORITY_DENIED"
    apply(engine, {"operation": "recipe.restore", "receipt": result["receipt"], "before_receipt": True})
    assert original.read_text() == "Human-owned repository guidance\n"


def test_recovery_cannot_recreate_lost_executable_approval(tmp_path, collected):
    engine, _, request = isolated_hook(tmp_path, collected)
    apply(engine, request)
    plan, _ = engine.build({"operation": "recipe.configure", "remove": ["hooks/" + HOOK[1]]})

    def interrupted(stage, index):
        if stage == "after_write" and index == 0:
            raise KeyboardInterrupt("Synthetic interrupted hook removal")

    with pytest.raises(KeyboardInterrupt):
        engine.apply(plan, interrupted)
    assert engine.state.pending()
    with engine.state.connect(write=True) as db:
        db.execute("DELETE FROM metadata WHERE name='recipe-executables'")
        db.commit()
    with pytest.raises(DasyncError) as rejected:
        engine.state.recover(engine.scope.key, engine._validate_target)
    assert rejected.value.code == "RECOVERY_BLOCKED" and engine.state.pending()

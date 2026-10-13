"""Modification, protection and fault-position matrices through the real Engine."""

import base64
import copy
import itertools
from pathlib import Path

import pytest
from dasync.config import Environment, Scope
from dasync.engine import Engine
from dasync.errors import DasyncError
from dasync.recipe_engine import registry
from dasync.recipe_sources import Snapshots
from test_recipes import A, B, apply, item, recipe


def fingerprint(engine):
    return (
        {
            path.relative_to(engine.scope.root).as_posix(): (path.read_bytes(), path.stat().st_mode & 0o777)
            for path in engine.scope.root.rglob("*")
            if path.is_file() and not path.is_symlink()
        },
        copy.deepcopy(engine.state.head(engine.scope.key)),
        copy.deepcopy(registry(engine)),
    )


def fixture(root):
    home, project = root / "home", root / "project"
    home.mkdir(parents=True)
    project.mkdir()
    env = Environment(home, home / "config/config.yaml", home / "state", home / "cache")
    engine = Engine(env, Scope.get(env, "project", str(project)))
    source = recipe(root / "source", specs=[item("skill.a"), item("skill.b")])
    prepared = Snapshots(env.cache).prepare(source)
    request = {
        "operation": "recipe.configure",
        "registrations": [{"candidate": prepared["candidate"], "alias": "source"}],
        "trust_source": True,
        "select_sources": ["source"],
    }
    return engine, source, request


@pytest.mark.parametrize("operation", ["install", "remove", "update", "restore"])
def test_every_write_boundary_rolls_back_or_recovers_exactly(tmp_path, operation):
    probe, source, request = fixture(tmp_path / "probe")
    if operation != "install":
        _, first = apply(probe, request)
    if operation == "remove":
        request = {"operation": "recipe.configure", "remove": ["source/skill.b"]}
    elif operation == "update":
        (source / "items/0/BODY.md").write_text("# Changed snapshot\n")
        request = {
            "operation": "recipe.configure",
            "registrations": [
                {"candidate": Snapshots(probe.env.cache).prepare(source)["candidate"], "alias": "source"}
            ],
            "trust_source": True,
        }
    elif operation == "restore":
        apply(probe, {"operation": "recipe.configure", "remove": ["source/skill.b"]})
        request = {"operation": "recipe.restore", "receipt": first["receipt"]}
    plan, _ = probe.build(request)
    writes = sum(op["action"] != "keep" for op in plan["operations"])
    assert writes
    for stage, index, interruption in itertools.product(
        ("before_write", "after_write"), range(writes), (False, True)
    ):
        engine, source, current_request = fixture(tmp_path / f"{stage}-{index}-{interruption}")
        if operation != "install":
            _, first = apply(engine, current_request)
        if operation == "remove":
            current_request = {"operation": "recipe.configure", "remove": ["source/skill.b"]}
        elif operation == "update":
            (source / "items/0/BODY.md").write_text("# Changed snapshot\n")
            current_request = {
                "operation": "recipe.configure",
                "registrations": [
                    {"candidate": Snapshots(engine.env.cache).prepare(source)["candidate"], "alias": "source"}
                ],
                "trust_source": True,
            }
        elif operation == "restore":
            apply(engine, {"operation": "recipe.configure", "remove": ["source/skill.b"]})
            current_request = {"operation": "recipe.restore", "receipt": first["receipt"]}
        reviewed, _ = engine.build(current_request)
        before = fingerprint(engine)
        exception = KeyboardInterrupt if interruption else RuntimeError

        def fail(event, position):
            if event == stage and position == index:
                raise exception("Injected boundary failure")

        with pytest.raises(exception):
            engine.apply(reviewed, fail)
        if interruption:
            assert engine.state.pending()
            engine.state.recover(engine.scope.key, engine._validate_target)
        assert fingerprint(engine) == before
        assert not engine.state.pending()
        engine.apply(reviewed)
        assert engine.status()["pending_changes"] == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("cli_version", "wrong"),
        ("adapter_version", "wrong"),
        ("mapping_version", 2),
        ("platform", "wrong"),
        ("root", "/wrong"),
        ("scope_key", "project:/wrong"),
        ("scope", "user"),
        ("previous_receipt", "wrong"),
        ("plan_hash", "f" * 64),
        ("protocol", 2),
        ("version", 3),
        ("request.operation", "recipe.restore"),
        ("inputs.registry", "f" * 64),
        ("inputs.authority", "f" * 64),
        ("inputs.config.hash", "f" * 64),
        ("graph.roots", []),
        ("graph.items", []),
        ("mapping", {}),
        ("project_lock", None),
        ("decisions", []),
        ("operations.0.action", "delete"),
        ("operations.0.hash", None),
        ("operations.0.mode", 0o777),
        ("operations.0.path", "/outside"),
        ("operations.0.contributors", []),
    ],
)
def test_tampering_each_plan_dimension_has_no_effect(tmp_path, field, value):
    engine, _, request = fixture(tmp_path)
    plan, _ = engine.build(request)
    target = plan
    parts = field.split(".")
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    part = int(parts[-1]) if isinstance(target, list) else parts[-1]
    if target[part] == value:
        pytest.skip("This value is already the reviewed value")
    target[part] = value
    before = fingerprint(engine)
    with pytest.raises(DasyncError):
        engine.apply(plan)
    assert fingerprint(engine) == before


@pytest.mark.parametrize("target_kind", ["content", "mode", "missing", "symlink", "directory"])
@pytest.mark.parametrize("overwrite", [False, True])
def test_managed_target_modification_matrix(tmp_path, target_kind, overwrite):
    engine, _, request = fixture(tmp_path)
    plan, _ = apply(engine, request)
    path = Path(next(op["path"] for op in plan["operations"] if op["path"].endswith("SKILL.md")))
    if target_kind == "content":
        path.write_text("independent edit")
    elif target_kind == "mode":
        path.chmod(0o600)
    else:
        path.unlink()
        if target_kind == "symlink":
            path.symlink_to("outside")
        elif target_kind == "directory":
            path.mkdir()
    request = {"operation": "recipe.configure", **({"conflict": "overwrite"} if overwrite else {})}
    protected = not overwrite or target_kind in ("symlink", "directory")
    if protected:
        before = fingerprint(engine)
        with pytest.raises(DasyncError) as rejected:
            engine.build(request)
        assert rejected.value.code in ("DRIFT", "UNSAFE_PATH")
        assert fingerprint(engine) == before
    else:
        _, result = apply(engine, request)
        receipt = engine.state.receipt(result["receipt"], engine.scope.key)
        backup = next(row for row in receipt["backups"] if row["path"] == str(path))
        if target_kind == "content":
            assert base64.b64decode(backup["data"]) == b"independent edit"
        if target_kind == "mode":
            assert backup["before"]["mode"] == 0o600
        assert engine.status()["pending_changes"] == 0


def test_removed_item_can_be_deselected_in_its_snapshot_update(tmp_path):
    engine, source, request = fixture(tmp_path)
    apply(engine, request)
    recipe(source, specs=[item("skill.a")])
    candidate = Snapshots(engine.env.cache).prepare(source)
    plan, _ = apply(
        engine,
        {
            "operation": "recipe.configure",
            "registrations": [{"candidate": candidate["candidate"], "alias": "source"}],
            "trust_source": True,
            "remove": [A + "/skill.b"],
        },
    )
    assert [row["item_id"] for row in plan["graph"]["items"]] == ["skill.a"]


def test_disabled_item_can_be_unblocked_without_becoming_a_root(tmp_path):
    engine, _, request = fixture(tmp_path)
    apply(engine, request)
    apply(engine, {"operation": "recipe.configure", "disable": ["source/skill.b"]})
    plan, _ = apply(engine, {"operation": "recipe.configure", "undisable": ["source/skill.b"]})
    assert plan["graph"]["roots"] == [{"source_id": A, "item_id": "skill.a"}]
    assert plan["request"]["operation"] == "recipe.configure"
    other = recipe(tmp_path / "other", B, specs=[item("skill.b")])
    candidate = Snapshots(engine.env.cache).prepare(other)
    apply(
        engine,
        {
            "operation": "recipe.configure",
            "registrations": [{"candidate": candidate["candidate"], "alias": "other"}],
            "trust_source": True,
            "disable": ["source/skill.b"],
        },
    )
    before = fingerprint(engine)
    with pytest.raises(DasyncError) as rejected:
        engine.build({"operation": "recipe.configure", "undisable": ["skill.b"]})
    assert rejected.value.code == "SELECTOR_AMBIGUOUS" and fingerprint(engine) == before
    apply(engine, {"operation": "recipe.configure", "undisable": ["source/skill.b"]})


def test_binding_an_inherited_source_requires_accepted_exact_pin(tmp_path):
    engine, _, request = fixture(tmp_path)
    other = recipe(tmp_path / "other", B)
    candidate = Snapshots(engine.env.cache).prepare(other)
    user = Engine(engine.env, Scope.get(engine.env, "user", None))
    apply(
        user,
        {
            "operation": "recipe.configure",
            "registrations": [{"candidate": candidate["candidate"], "alias": "personal"}],
            "trust_source": True,
            "enable": ["personal/skill.review"],
        },
    )
    plan, _ = apply(
        engine,
        {
            **request,
            "bind_sources": [{"source_id": B, "pin": candidate["pin"]}],
            "enable": [B + "/skill.review"],
        },
    )
    assert B in {source["source_id"] for source in plan["project_lock"]["sources"]}
    before = fingerprint(engine)
    with pytest.raises(DasyncError) as rejected:
        engine.build(
            {"operation": "recipe.configure", "bind_sources": [{"source_id": B, "pin": "sha256:" + "f" * 64}]}
        )
    assert rejected.value.code == "SOURCE_UNBOUND" and fingerprint(engine) == before

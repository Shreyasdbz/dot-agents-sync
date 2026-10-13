"""Experimental local recipes: disposable sources, scopes, state and fault journeys."""

import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from dasync.config import Environment, Scope, load_config
from dasync.contracts import SCHEMAS, validate
from dasync.engine import Engine
from dasync.errors import DasyncError
from dasync.io import canonical, parse
from dasync.recipe_adapters import name_mapping, native_name, render, render_references
from dasync.recipe_cli import describe
from dasync.recipe_contracts import key_text
from dasync.recipe_engine import authority, deny, load_sources, registry
from dasync.recipe_resolver import compose, project_lock, resolve
from dasync.recipe_sources import Snapshots, check_paths, read_source
from jsonschema import Draft202012Validator

A = "11111111-1111-4111-8111-111111111111"
B = "22222222-2222-4222-8222-222222222222"


def item(local_id="skill.review", **extra):
    return {
        "format": 1,
        "kind": "Skill",
        "id": local_id,
        "version": "1.0",
        "name": "Review",
        "description": "A synthetic code review workflow.",
        "license": "LicenseRef-Synthetic",
        "entry": "BODY.md",
        "files": ["BODY.md"],
        "scopes": ["user", "project"],
        "requires": {},
        **extra,
    }


def recipe(root, sid=A, specs=None, body="# Synthetic review\n"):
    root.mkdir(exist_ok=True, parents=True)
    specs = specs or [item()]
    paths = []
    for index, spec in enumerate(specs):
        folder = root / "items" / str(index)
        folder.mkdir(exist_ok=True, parents=True)
        (folder / "item.yaml").write_bytes(canonical(spec))
        for filename in spec["files"]:
            path = folder / filename
            path.parent.mkdir(exist_ok=True, parents=True)
            path.write_text(body if filename == spec["entry"] else "synthetic asset\n")
        paths.append(f"items/{index}/item.yaml")
    (root / "recipe.yaml").write_bytes(
        canonical(
            {
                "format": 1,
                "source_id": sid,
                "name": "synthetic",
                "description": "Synthetic test recipe",
                "requires_engine": ">=0.1.1,<1",
                "required_features": [],
                "items": paths,
                "imports": {},
            }
        )
    )
    return root


@pytest.fixture
def local(tmp_path):
    home, project = tmp_path / "home", tmp_path / "project"
    home.mkdir()
    project.mkdir()
    env = Environment(home, home / "config/config.yaml", home / "state", home / "cache")
    engine = Engine(env, Scope.get(env, "project", str(project)))
    a, b = recipe(tmp_path / "private-source-a"), recipe(tmp_path / "private-source-b", B)
    snapshots = Snapshots(env.cache)
    candidates = snapshots.prepare(a), snapshots.prepare(b)
    request = {
        "operation": "recipe.configure",
        "registrations": [
            {"candidate": candidates[0]["candidate"], "alias": "alpha"},
            {"candidate": candidates[1]["candidate"], "alias": "beta"},
        ],
        "trust_source": True,
        "enable": ["alpha/skill.review", "beta/skill.review"],
    }
    return engine, request, a, b, candidates


def apply(engine, request):
    plan, _ = engine.build(request)
    return plan, engine.apply(plan)


def test_all_schemas_offline_and_shared_item_contract():
    for schema in SCHEMAS.values():
        Draft202012Validator.check_schema(schema)
    assert SCHEMAS["local-item"]["$defs"]["ItemSpec"] is SCHEMAS["item-spec"]
    for field, value in [
        ("profiles", []),
        ("required_features", ["unknown"]),
        ("$ref", "https://invalid.example/schema"),
    ]:
        with pytest.raises(DasyncError, match="Invalid item-spec"):
            validate("item-spec", {**item(), field: value})
    validate(
        "recipe-slot",
        {
            "required": True,
            "cardinality": "one",
            "contract_id": A,
            "version": ">=1,<2",
            "content_format": "markdown",
        },
    )
    with pytest.raises(DasyncError):
        validate(
            "recipe-slot",
            {
                "required": True,
                "cardinality": "many",
                "contract_id": A,
                "version": "oops",
                "content_format": "markdown",
            },
        )


@pytest.mark.parametrize(
    "document", [b"format: 1\nformat: 2", b"x: &alias 1\ny: *alias", b"x: !!python/object:bad {}"]
)
def test_strict_authored_documents(document):
    with pytest.raises(DasyncError):
        parse(document)


def test_prepare_is_cache_only_and_retained_offline(local):
    engine, request, a, b, candidates = local
    assert not engine.scope.config.exists() and not engine.state.path.exists()
    assert registry(engine)["sources"] == {}
    first = candidates[0]
    (a / "items/0/BODY.md").write_text("changed\n")
    second = Snapshots(engine.env.cache).prepare(a)
    assert first["pin"] != second["pin"]
    assert Snapshots(engine.env.cache).candidate(first["candidate"])[1].pin == first["pin"]
    shutil.rmtree(a)
    shutil.rmtree(b)
    plan, result = apply(engine, request)
    assert result["changed"]
    assert len(plan["graph"]["items"]) == 2
    assert engine.status()["pending_changes"] == 0
    sync, _ = engine.build({"operation": "recipe.sync"})
    assert engine.apply(sync)["changed"] is False
    assert all(op["action"] == "keep" for op in sync["operations"])


def test_identity_alias_fork_and_inert_metadata(local):
    engine, request, a, _, candidates = local
    plan, result = apply(engine, request)
    names = plan["mapping"]
    assert names[key_text((A, "skill.review"))] != names[key_text((B, "skill.review"))]
    encoded = canonical(plan)
    assert str(a).encode() not in encoded and b"Synthetic review" not in encoded
    renamed = {
        "operation": "recipe.configure",
        "registrations": [{"candidate": candidates[0]["candidate"], "alias": "renamed"}],
        "trust_source": True,
    }
    rename_plan, _ = apply(engine, renamed)
    assert rename_plan["mapping"] == names
    copy_root = engine.scope.root.parent / "copied-uuid"
    shutil.copytree(a, copy_root)
    copied = Snapshots(engine.env.cache).prepare(copy_root)
    with pytest.raises(DasyncError) as rejected:
        engine.build(
            {
                "operation": "recipe.configure",
                "registrations": [{"candidate": copied["candidate"], "alias": "copy"}],
                "trust_source": True,
            }
        )
    assert rejected.value.code == "ORIGIN_CONFLICT"
    assert engine.state.receipt(result["receipt"], engine.scope.key)["recipe"]["plan"]["mapping"] == names


def test_ambiguous_selector_and_trust_fail_without_registration(local):
    engine, request, *_ = local
    for mutation, expected in [
        ({"enable": ["skill.review"]}, "SELECTOR_AMBIGUOUS"),
        ({"trust_source": False}, "TRUST_REQUIRED"),
    ]:
        with pytest.raises(DasyncError) as rejected:
            engine.build({**request, **mutation})
        assert rejected.value.code == expected
    assert registry(engine)["sources"] == {} and not engine.scope.config.exists()


@pytest.mark.parametrize("bad", ["../escape", "/absolute", "dir\\body", "con.md", "a./b", "a//b", "a\x01b"])
def test_source_paths_reject_unsafe_names(local, bad):
    _, _, a, *_ = local
    manifest = a / "items/0/item.yaml"
    value = parse(manifest.read_bytes())
    value["files"], value["entry"] = [bad], bad
    manifest.write_bytes(canonical(value))
    with pytest.raises(DasyncError) as rejected:
        read_source(a)
    assert rejected.value.code == "UNSAFE_PATH"


def test_source_symlinks_executables_size_and_identity_hash(local):
    _, _, a, *_ = local
    before = read_source(a).pin
    envelope = parse((a / "recipe.yaml").read_bytes())
    envelope["source_id"] = B
    (a / "recipe.yaml").write_bytes(canonical(envelope))
    assert read_source(a).pin != before
    extra = a / "undeclared.sh"
    extra.write_text("not executed")
    with pytest.raises(DasyncError) as rejected:
        read_source(a)
    assert rejected.value.code == "EXECUTABLE_UNSUPPORTED"
    extra.unlink()
    extra.symlink_to(a / "items/0/BODY.md")
    with pytest.raises(DasyncError) as rejected:
        read_source(a)
    assert rejected.value.code == "UNSAFE_PATH"
    extra.unlink()
    (a / "items/0/BODY.md").write_bytes(b"a" * (4 * 1024 * 1024 + 1))
    with pytest.raises(DasyncError):
        read_source(a)


def test_snapshot_missing_and_tampering_never_substitutes_checkout(local):
    engine, _, a, _, candidates = local
    cache = Snapshots(engine.env.cache)
    record, _ = cache.candidate(candidates[0]["candidate"])
    path = cache._path("snapshots", record["snapshot"])
    path.write_text("{}")
    with pytest.raises(DasyncError) as rejected:
        cache.candidate(candidates[0]["candidate"])
    assert rejected.value.code == "SOURCE_INTEGRITY"
    path.unlink()
    with pytest.raises(DasyncError) as rejected:
        cache.candidate(candidates[0]["candidate"])
    assert rejected.value.code == "SNAPSHOT_MISSING" and a.exists()


def test_undeclared_group_executable_is_rejected(local):
    _, _, a, *_ = local
    extra = a / "undeclared.txt"
    extra.write_text("not executed")
    extra.chmod(0o650)
    with pytest.raises(DasyncError) as rejected:
        read_source(a)
    assert rejected.value.code == "EXECUTABLE_UNSUPPORTED"


def test_malformed_retained_records_are_redacted_structured_errors(local):
    engine, _, *_ = local
    cache = Snapshots(engine.env.cache)
    token = cache._retain("snapshots", {"format": 1, "files": "PRIVATE_SENTINEL"})
    with pytest.raises(DasyncError) as rejected:
        cache.load(token, "sha256:" + "a" * 64)
    assert rejected.value.code == "SOURCE_INTEGRITY" and "PRIVATE_SENTINEL" not in str(rejected.value)
    with engine.state.connect(write=True) as db:
        db.execute("INSERT INTO metadata VALUES (?,?)", ("recipe-registry", '["PRIVATE_SENTINEL"]'))
        db.commit()
    with pytest.raises(DasyncError) as rejected:
        registry(engine)
    assert rejected.value.code == "STATE_UNSUPPORTED" and "PRIVATE_SENTINEL" not in str(rejected.value)


def test_bulk_selection_and_dependency_reasons_are_snapshot_scoped(local):
    engine, request, a, _, _ = local
    specs = [item(requires={"template.review": ">=1"}), item("template.review", kind="Template")]
    recipe(a, specs=specs)
    prepared = Snapshots(engine.env.cache).prepare(a)
    request["registrations"] = [{"candidate": prepared["candidate"], "alias": "alpha"}]
    request["enable"] = []
    request["select_sources"] = ["alpha"]
    plan, _ = apply(engine, request)
    dependency = next(row for row in plan["graph"]["items"] if row["item_id"] == "template.review")
    assert {reason["kind"] for reason in dependency["reasons"]} == {"direct", "dependency"}
    remove_plan, _ = apply(engine, {"operation": "recipe.configure", "remove": ["alpha/template.review"]})
    dependency = next(row for row in remove_plan["graph"]["items"] if row["item_id"] == "template.review")
    assert {reason["kind"] for reason in dependency["reasons"]} == {"dependency"}
    recipe(a, specs=[*specs, item("skill.new")])
    newer = Snapshots(engine.env.cache).prepare(a)
    updated, _ = apply(
        engine,
        {
            "operation": "recipe.configure",
            "registrations": [{"candidate": newer["candidate"], "alias": "alpha"}],
            "trust_source": True,
        },
    )
    assert "skill.new" not in {row["item_id"] for row in updated["graph"]["items"]}
    with pytest.raises(DasyncError) as rejected:
        engine.build({"operation": "recipe.configure", "disable": ["alpha/template.review"]})
    assert rejected.value.code == "DEPENDENCY_DISABLED"


@pytest.mark.parametrize(
    "requires,expected",
    [
        ({"skill.absent": ">=1"}, "ITEM_UNKNOWN"),
        ({"skill.review": ">=1"}, "DEPENDENCY_CYCLE"),
        ({"template.review": ">2"}, "VERSION_CONFLICT"),
    ],
)
def test_graph_failures_preserve_installation(local, requires, expected):
    engine, request, a, _, _ = local
    _, result = apply(engine, request)
    before = engine.scope.config.read_bytes()
    recipe(a, specs=[item(requires=requires), item("template.review", kind="Template")])
    prepared = Snapshots(engine.env.cache).prepare(a)
    with pytest.raises(DasyncError) as rejected:
        engine.build(
            {
                "operation": "recipe.configure",
                "registrations": [{"candidate": prepared["candidate"], "alias": "alpha"}],
                "trust_source": True,
            }
        )
    assert rejected.value.code == expected
    assert (
        engine.scope.config.read_bytes() == before
        and engine.state.head(engine.scope.key)["id"] == result["receipt"]
    )


def test_native_names_and_path_collisions(local, monkeypatch):
    _, _, a, b, _ = local
    sources = read_source(a), read_source(b)
    items = {
        (A, "skill.review"): sources[0].items["skill.review"],
        (B, "skill.review"): sources[1].items["skill.review"],
    }
    assert native_name((A, "skill.a-b")) != native_name((A, "skill.a.b"))
    assert name_mapping(items) == name_mapping(dict(reversed(list(items.items()))))
    for names in (["A", "a"], ["A/b", "a"], ["con.md"], ["long/" + "a" * 101]):
        with pytest.raises(DasyncError):
            check_paths(names)
    monkeypatch.setattr("dasync.recipe_adapters.native_name", lambda _: "collision")
    with pytest.raises(DasyncError) as rejected:
        name_mapping(items)
    assert rejected.value.code == "NAME_COLLISION"


def test_typed_references_literal_prose_and_qualified_nested_files(local):
    engine, request, a, _, _ = local
    body = """Literal dasync:dependency/template.review remains.
[asset](dasync:dependency/template.review/assets/example.md#heading)
`[code](dasync:dependency/skill.missing)`
\\[escaped](dasync:dependency/skill.missing)
```markdown
[example](dasync:dependency/skill.missing)
```
"""
    recipe(
        a,
        specs=[
            item(requires={"template.review": ">=1"}, default_prompt="Review.", invocations=[]),
            item("template.review", kind="Template", files=["BODY.md", "assets/example.md"]),
        ],
        body=body,
    )
    (a / "items/1/BODY.md").write_text("# Synthetic template\n")
    candidate = Snapshots(engine.env.cache).prepare(a)
    request["registrations"][0]["candidate"] = candidate["candidate"]
    plan, outputs = engine.build(request)
    skill = next(
        data.decode()
        for path, data in outputs.items()
        if "skill-review" in path and path.endswith("SKILL.md")
    )
    assert "Literal dasync:dependency/template.review remains." in skill
    assert "assets/example.md#heading)" in skill and "dasync:dependency/template.review/assets" not in skill
    assert (
        "`[code](dasync:dependency/skill.missing)`" in skill
        and "\\[escaped](dasync:dependency/skill.missing)" in skill
    )
    assert "[example](dasync:dependency/skill.missing)" in skill
    settings = next(
        data.decode()
        for path, data in outputs.items()
        if path.endswith("openai.yaml") and "skill-review" in path
    )
    assert "$" + plan["mapping"][key_text((A, "skill.review"))] in settings
    artifacts, _, _ = render(
        {
            (A, "skill.review"): read_source(a).items["skill.review"],
            (A, "template.review"): read_source(a).items["template.review"],
        }
    )
    assert (A, "template.review") in next(
        artifact for artifact in artifacts if artifact.relative.endswith("SKILL.md")
    ).contributors
    seen = []
    assert (
        render_references(
            "[x]: <dasync:dependency/template.review>\n<!-- [x](dasync:bad) -->\n",
            lambda value: seen.append(value) or "target",
        )
        == "[x]: <target>\n<!-- [x](dasync:bad) -->\n"
    )
    assert seen == ["dasync:dependency/template.review"]


@pytest.mark.parametrize(
    "extra,expected",
    [
        ({"required_capabilities": ["os.sandbox"]}, "CAPABILITY_UNSUPPORTED"),
        (
            {
                "slots": {
                    "workspace": {
                        "required": True,
                        "cardinality": "one",
                        "contract_id": A,
                        "version": ">=1",
                        "content_format": "markdown",
                    }
                }
            },
            "CONTEXT_MISSING",
        ),
    ],
)
def test_essential_semantics_fail_closed(local, extra, expected):
    engine, request, a, _, _ = local
    recipe(a, specs=[item(**extra)])
    request["registrations"][0]["candidate"] = Snapshots(engine.env.cache).prepare(a)["candidate"]
    with pytest.raises(DasyncError) as rejected:
        engine.build(request)
    assert rejected.value.code == expected


def test_private_dependency_closure_cannot_materialize(local):
    engine, request, a, _, _ = local
    recipe(
        a,
        specs=[
            item(requires={"context.private": ">=1"}),
            item(
                "context.private",
                kind="Context",
                context={"access": "inherit", "sensitivity": "private"},
                description="PRIVATE_SENTINEL",
            ),
        ],
    )
    request["registrations"][0]["candidate"] = Snapshots(engine.env.cache).prepare(a)["candidate"]
    with pytest.raises(DasyncError) as rejected:
        engine.build(request)
    assert rejected.value.code == "CONTEXT_DENIED" and "PRIVATE_SENTINEL" not in str(rejected.value)
    assert not engine.scope.config.exists()


def test_project_lock_excludes_personal_resolution_and_paths(local):
    engine, request, a, b, _ = local
    user_engine = Engine(engine.env, Scope.get(engine.env, "user", None))
    personal = copy.deepcopy(request)
    personal["registrations"] = personal["registrations"][1:]
    personal["enable"] = ["beta/skill.review"]
    apply(user_engine, personal)
    project = copy.deepcopy(request)
    project["registrations"] = project["registrations"][:1]
    project["enable"] = ["alpha/skill.review"]
    plan, _ = apply(engine, project)
    lock = canonical(plan["project_lock"])
    assert B.encode() not in lock and str(a).encode() not in lock and b"beta" not in lock
    assert len(plan["graph"]["items"]) == 2
    apply(user_engine, {"operation": "recipe.configure", "remove": ["beta/skill.review"]})
    sync, _ = engine.build({"operation": "recipe.sync"})
    assert canonical(sync["project_lock"]) == lock and len(sync["graph"]["items"]) == 1
    assert "global" in sync["graph"]["native_global_visibility"]
    assert b"mapping" not in lock and b"authority" not in lock


def test_two_homes_produce_identical_project_lock(local, tmp_path):
    engine, request, a, b, _ = local
    plan, _ = apply(engine, {**request, "enable": ["alpha/skill.review"]})
    home2 = tmp_path / "home2"
    home2.mkdir()
    env2 = Environment(home2, home2 / "config/config.yaml", home2 / "state", home2 / "cache")
    second = Engine(env2, engine.scope)
    candidates = Snapshots(env2.cache).prepare(a), Snapshots(env2.cache).prepare(b)
    registered_request = {
        "operation": "recipe.configure",
        "registrations": [
            {"candidate": row["candidate"], "alias": alias}
            for row, alias in zip(candidates, ("alpha", "beta"))
        ],
        "trust_source": True,
    }
    user2 = Engine(env2, Scope.get(env2, "user", None))
    apply(user2, {**registered_request, "enable": ["beta/skill.review"]})
    intent = load_config(second.scope.config)
    personal = load_config(env2.config)
    sources = load_sources(second, compose(intent, personal), registry(second))
    _, graph = resolve(sources, intent, "project", personal)
    assert plan["project_lock"] == project_lock(sources, intent)
    assert len(plan["graph"]["items"]) == 1 and len(graph["items"]) == 2


def test_conflicting_pins_and_inheritance_control(local):
    engine, request, a, _, _ = local
    user = Engine(engine.env, Scope.get(engine.env, "user", None))
    apply(user, request)
    (a / "items/0/BODY.md").write_text("new snapshot")
    next_candidate = Snapshots(engine.env.cache).prepare(a)
    project = {
        "operation": "recipe.configure",
        "registrations": [{"candidate": next_candidate["candidate"], "alias": "alpha"}],
        "trust_source": True,
        "enable": ["alpha/skill.review"],
    }
    with pytest.raises(DasyncError) as rejected:
        engine.build(project)
    assert rejected.value.code == "SNAPSHOT_CONFLICT"
    plan, _ = apply(engine, {**project, "inherit_user": False})
    assert plan["graph"]["resolver_inherits_personal"] is False


@pytest.mark.parametrize("change", ["authority", "target", "config", "lock", "receipt", "snapshot"])
def test_saved_plan_input_binding(local, change):
    engine, request, _, _, candidates = local
    apply(engine, request)
    plan, _ = engine.build({"operation": "recipe.configure", "remove": ["beta/skill.review"]})
    if change == "authority":
        deny(engine, B)
    elif change == "target":
        target = Path(next(op["path"] for op in plan["operations"] if op["path"].endswith("SKILL.md")))
        target.write_text("independent edit")
    elif change == "config":
        config = load_config(engine.scope.config)
        config["inherit_user"] = False
        engine.scope.config.write_bytes(canonical(config))
    elif change == "lock":
        (engine.scope.root / ".dasync.lock").write_text("independent lock edit")
    elif change == "receipt":
        apply(engine, {"operation": "recipe.configure", "remove": ["alpha/skill.review"]})
    else:
        cache = Snapshots(engine.env.cache)
        record, _ = cache.candidate(candidates[0]["candidate"])
        cache._path("snapshots", record["snapshot"]).write_text("tampered")
    before = {path: path.read_bytes() for path in engine.scope.root.rglob("*") if path.is_file()}
    with pytest.raises(DasyncError):
        engine.apply(plan)
    assert before == {path: path.read_bytes() for path in engine.scope.root.rglob("*") if path.is_file()}


def test_protected_unmanaged_output_and_offline_original_restore(local):
    engine, request, a, b, _ = local
    plan, _ = engine.build(request)
    path = Path(next(op["path"] for op in plan["operations"] if op["path"].endswith("SKILL.md")))
    path.parent.mkdir(parents=True)
    path.write_text("unmanaged original")
    with pytest.raises(DasyncError) as rejected:
        engine.build(request)
    assert rejected.value.code == "UNMANAGED_COLLISION"
    _, result = apply(engine, {**request, "conflict": "overwrite"})
    shutil.rmtree(a)
    shutil.rmtree(b)
    deny(engine, A)
    restore, _ = engine.build(
        {"operation": "recipe.restore", "receipt": result["receipt"], "before_receipt": True}
    )
    engine.apply(restore)
    assert path.read_text() == "unmanaged original"
    assert not engine.scope.config.exists()


def test_offline_managed_restore_checks_current_authority(local):
    engine, request, a, b, _ = local
    _, first = apply(engine, request)
    apply(engine, {"operation": "recipe.configure", "remove": ["beta/skill.review"]})
    shutil.rmtree(a)
    shutil.rmtree(b)
    restore, _ = engine.build({"operation": "recipe.restore", "receipt": first["receipt"]})
    engine.apply(restore)
    assert engine.status()["pending_changes"] == 0
    deny(engine, B)
    with pytest.raises(DasyncError) as rejected:
        engine.build({"operation": "recipe.restore", "receipt": first["receipt"]})
    assert rejected.value.code == "AUTHORITY_DENIED"
    engine.scope.config.unlink()
    with pytest.raises(DasyncError) as rejected:
        engine.build({"operation": "rollback", "receipt": first["receipt"]})
    assert rejected.value.code == "AUTHORITY_DENIED"


def test_personal_disable_cannot_silently_override_project_root(local):
    engine, request, *_ = local
    user = Engine(engine.env, Scope.get(engine.env, "user", None))
    apply(user, {**request, "enable": [], "disable": ["alpha/skill.review"]})
    with pytest.raises(DasyncError) as rejected:
        engine.build(request)
    assert rejected.value.code == "SELECTION_CONFLICT"


def test_receipts_restore_even_when_snapshot_cache_is_unavailable(local):
    engine, request, a, b, _ = local
    _, first = apply(engine, request)
    apply(engine, {"operation": "recipe.configure", "remove": ["beta/skill.review"]})
    shutil.rmtree(a)
    shutil.rmtree(b)
    shutil.rmtree(engine.env.cache)
    restore, _ = engine.build({"operation": "recipe.restore", "receipt": first["receipt"]})
    engine.apply(restore)
    assert len(list(engine.scope.root.glob(".agents/skills/*/SKILL.md"))) == 2
    assert engine.status()["diagnostic"]["code"] == "SNAPSHOT_MISSING"


def test_metadata_is_serialized_without_creating_native_frontmatter(local):
    engine, request, a, _, _ = local
    import yaml

    malicious = "---\nname: injected\n\x1b]0;inert\x07 $(not-executed)"
    recipe(a, specs=[item(description=malicious, name="Quoted: display", default_prompt=malicious)])
    request["registrations"][0]["candidate"] = Snapshots(engine.env.cache).prepare(a)["candidate"]
    plan, outputs = engine.build(request)
    native = next(
        data.decode()
        for path, data in outputs.items()
        if path.endswith("SKILL.md") and plan["mapping"][key_text((A, "skill.review"))] in path
    )
    frontmatter = yaml.safe_load(native.split("---\n", 2)[1])
    assert (
        frontmatter["description"] == malicious
        and frontmatter["name"] == plan["mapping"][key_text((A, "skill.review"))]
    )
    assert b"\x1b" not in canonical(plan)


def test_lock_and_source_metadata_limits_fail_before_registration(local, monkeypatch):
    engine, request, a, *_ = local
    import dasync.recipe_sources as source_module

    monkeypatch.setattr(source_module, "MAX_FILES", 1)
    with pytest.raises(DasyncError) as rejected:
        Snapshots(engine.env.cache).prepare(a)
    assert rejected.value.code == "SOURCE_LIMIT" and registry(engine)["sources"] == {}


@pytest.mark.parametrize("stage", ["before_write", "after_write", "before_receipt"])
def test_interrupted_registration_retains_journal_and_no_trust(local, stage):
    engine, request, *_ = local
    plan, _ = engine.build(request)

    def crash(event, _):
        if event == stage:
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        engine.apply(plan, crash)
    assert engine.state.pending() and registry(engine)["sources"] == {}
    with pytest.raises(DasyncError) as rejected:
        engine.apply(plan)
    assert rejected.value.code in ("RECOVERY_REQUIRED", "DRIFT", "PLAN_INVALIDATED", "UNMANAGED_COLLISION")
    engine.state.recover(engine.scope.key, engine._validate_target)
    assert not engine.state.pending() and not engine.scope.config.exists()
    apply(engine, request)


def test_deny_during_pending_recovery_blocks_reactivation_and_retains_evidence(local):
    engine, request, *_ = local
    first, _ = apply(engine, request)
    update, _ = engine.build({"operation": "recipe.configure", "remove": ["beta/skill.review"]})

    def crash(event, _):
        if event == "before_receipt":
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        engine.apply(update, crash)
    deny(engine, B)
    pending = engine.state.pending()
    assert pending and authority(engine)["denied"] == [B]
    with pytest.raises(DasyncError) as rejected:
        engine.state.recover(engine.scope.key, engine._validate_target)
    assert rejected.value.code == "RECOVERY_BLOCKED"
    assert engine.state.pending() == pending
    with pytest.raises(DasyncError):
        engine.apply(first)


def test_recovery_independent_edit_preserves_journal(local):
    engine, request, *_ = local
    plan, _ = engine.build(request)

    def crash(event, _):
        if event == "before_receipt":
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        engine.apply(plan, crash)
    engine.scope.config.write_text("independent edit")
    with pytest.raises(DasyncError) as rejected:
        engine.state.recover(engine.scope.key, engine._validate_target)
    assert rejected.value.code == "RECOVERY_CONFLICT"
    assert engine.scope.config.read_text() == "independent edit" and engine.state.pending()


def test_create_singleton_via_reviewed_engine_and_prepare(local, tmp_path):
    engine, _, *_ = local
    for kind in ("Skill", "Context"):
        root = tmp_path / kind
        root.mkdir()
        author = Engine(engine.env, Scope.get(engine.env, "project", str(root)))
        request = {
            "operation": "recipe.create",
            "source_id": A if kind == "Skill" else B,
            "kind": kind,
            "id": kind.lower() + ".local",
            "name": "Local",
            "description": "A synthetic local item.",
            "license": "LicenseRef-Synthetic",
        }
        plan, _ = author.build(request)
        assert not list(root.iterdir())
        author.apply(plan)
        prepared = Snapshots(engine.env.cache).prepare(root)
        assert prepared["kind"] == "item" and prepared["snapshot_kind"] == "local-tree"


def test_bootstrap_protocol_and_json_errors_without_environment(tmp_path):
    env = {
        **os.environ,
        "DASYNC_HOME": str(tmp_path / "missing-home"),
        "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "cli"),
    }
    result = subprocess.run(
        [sys.executable, "-m", "dasync.cli", "describe", "--json", "--no-input"],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
    )
    response = json.loads(result.stdout)
    assert response["protocol"] == 1 and response["ok"] and not result.stderr
    assert not (tmp_path / "missing-home").exists()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "dasync.cli",
            "recipe",
            "prepare",
            "--protocol",
            "999",
            "--json",
            "--no-input",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
    )
    assert json.loads(result.stdout)["error"]["code"] == "PROTOCOL_UNSUPPORTED"
    assert not (tmp_path / "missing-home").exists()
    assert describe()["schemas"]["item-spec"]["additionalProperties"] is False

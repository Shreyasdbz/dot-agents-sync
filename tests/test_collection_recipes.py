"""The preserved real collection, exercised through the recipe Engine, not a fixture facsimile."""

import asyncio
import itertools
import json
import re
import shlex
import subprocess
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest
from dasync.collection import GROUPS, SOURCE_IDS, STARTER_ROOTS, compile_collection
from dasync.config import Environment, Scope
from dasync.engine import Engine
from dasync.errors import DasyncError
from dasync.io import canonical, digest, parse, read
from dasync.recipe_adapters import native_name
from dasync.recipe_approvals import approved_pairs, executable_state
from dasync.recipe_contracts import key_record
from dasync.recipe_engine import registry
from dasync.recipe_resolver import resolve
from dasync.recipe_sources import RecipeSnapshot, Snapshots
from dasync.recipe_tui import Confirm, RecipeApp
from test_recipe_matrix import oracle
from test_recipes import apply, item
from textual.widgets import DataTable, Static

ROOT = Path(__file__).resolve().parents[1]
AUDIT = json.loads((ROOT / "recipes/collection-audit.json").read_text())
ITEMS = [(row["recipe"], row["id"], row["kind"]) for row in AUDIT["items"]]
HOOK = (SOURCE_IDS["hooks"], "hook.credential-path-guard")


@pytest.fixture(scope="module")
def collected(tmp_path_factory):
    root = tmp_path_factory.mktemp("collected-recipes")
    projected, _ = compile_collection(ROOT)
    sources, cache = root / "sources", root / "cache"
    for name, data in projected.items():
        path = sources / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    prepared = {group: Snapshots(cache).prepare(sources / group) for group in GROUPS}
    return sources, cache, prepared


def environment(tmp_path, collected, scope="project", groups=GROUPS):
    _, cache, prepared = collected
    home, project = tmp_path / "home", tmp_path / "project"
    home.mkdir(parents=True)
    project.mkdir()
    env = Environment(home, home / "config/config.yaml", home / "state", cache)
    engine = Engine(env, Scope.get(env, scope, str(project) if scope == "project" else None))
    request = {
        "operation": "recipe.configure",
        "registrations": [{"candidate": prepared[group]["candidate"], "alias": group} for group in groups],
        "trust_source": True,
    }
    return engine, request


def hook_approval(cache, candidate):
    _, source = Snapshots(cache).candidate(candidate)
    return {**key_record(HOOK), "digest": source.items[HOOK[1]].digest}


def test_projection_preserves_every_item_file_license_and_private_contract():
    outputs, report = compile_collection(ROOT)
    assert len(report["items"]) == len({row["id"] for row in report["items"]}) == 70
    assert len(report["starter_items"]) == 18
    assert set(STARTER_ROOTS) <= set(report["starter_items"])
    for name, data in outputs.items():
        assert (ROOT / "recipes" / name).read_bytes() == data
    for row in report["items"]:
        manifest = parse(read(ROOT / row["original_manifest"]))
        folder = ROOT / "recipes" / row["recipe"] / "items" / row["id"]
        spec = json.loads((folder / "item.yaml").read_text())
        assert spec["id"] == row["id"] and spec["kind"] == row["kind"]
        assert (folder / "LICENSE.dasync.txt").read_bytes() == (ROOT / "LICENSE").read_bytes()
        assert manifest["version"] == spec["version"] and manifest["license"] == spec["license"]
        for file in row["files"]:
            original = ROOT / Path(row["original_manifest"]).parent / file["path"]
            assert digest(original.read_bytes()) == file["original"]
            assert digest((folder / file["path"]).read_bytes()) == file["canonical"]
            if not file["transformed"]:
                assert original.read_bytes() == (folder / file["path"]).read_bytes()
        if row["recipe"] == "context-contracts":
            assert spec["context"]["sensitivity"] == "private"
            assert spec["context"]["binding"] == row["id"]
            assert spec["context"]["consumers"] == [
                {
                    "source_id": SOURCE_IDS[
                        next(item["recipe"] for item in report["items"] if item["id"] == consumer)
                    ],
                    "item_id": consumer,
                }
                for consumer in manifest["context"]["consumers"]
            ]
        if row["kind"] == "Skill":
            assert not (folder / spec["entry"]).read_text().startswith("---")
            assert "$dasync-" not in spec["default_prompt"]
    ui = ROOT / "recipes/design/items/skill.ui-design/LICENSE.fwc-swiftui-skills.txt"
    assert ui.read_bytes() == (ROOT / "packages/skills/ui-design/LICENSE.fwc-swiftui-skills.txt").read_bytes()


@pytest.mark.parametrize("scope", ["user", "project"])
@pytest.mark.parametrize("group,local_id,kind", ITEMS)
def test_every_collected_item_resolves_materializes_or_refuses_private_activation(
    tmp_path, collected, scope, group, local_id, kind
):
    groups, pending = {group}, [group]
    while pending:
        current = pending.pop()
        metadata = json.loads((collected[0] / current / "recipe.yaml").read_text())
        for imported in metadata["imports"].values():
            name = next(name for name, sid in SOURCE_IDS.items() if sid == imported["source_id"])
            if name not in groups:
                groups.add(name)
                pending.append(name)
    engine, request = environment(tmp_path, collected, scope, sorted(groups))
    request["enable"] = [group + "/" + local_id]
    if kind == "Hook":
        request["approve_executables"] = [hook_approval(engine.env.cache, collected[2]["hooks"]["candidate"])]
    if group == "context-contracts":
        with pytest.raises(DasyncError) as rejected:
            engine.build(request)
        assert rejected.value.code in ("CONTEXT_DENIED", "SCOPE_FORBIDDEN")
        assert not engine.scope.config.exists() and engine.state.head(engine.scope.key) is None
        return
    plan, result = apply(engine, request)
    assert result["changed"] and engine.status()["pending_changes"] == 0
    assert any(
        row["source_id"] == SOURCE_IDS[group] and row["item_id"] == local_id for row in plan["graph"]["items"]
    )
    assert all(row["source_id"] != SOURCE_IDS["context-contracts"] for row in plan["graph"]["items"])
    if kind == "Agent":
        value = tomllib.loads(
            (
                engine.scope.root / ".codex/agents" / (native_name((SOURCE_IDS[group], local_id)) + ".toml")
            ).read_text()
        )
        assert (
            "sandbox_mode" not in value and "## Selected dependencies" in value["developer_instructions"]
            if group == "engineering"
            else "sandbox_mode" not in value
        )
    if kind == "Policy":
        path = engine.scope.root / (".codex/AGENTS.md" if scope == "user" else "AGENTS.md")
        assert local_id in path.read_text() and "Apply the selected policy in" not in path.read_text()
    if kind == "Skill":
        path = engine.scope.root / ".agents/skills" / native_name((SOURCE_IDS[group], local_id)) / "SKILL.md"
        text = path.read_text()
        assert "name: " + json.dumps(native_name((SOURCE_IDS[group], local_id))) in text
        assert "## Selected dependencies" in text
    sync, _ = engine.build({"operation": "recipe.sync"})
    assert not engine.apply(sync)["changed"]


def test_starter_and_all_optional_public_items_share_one_qualified_healthy_graph(tmp_path, collected):
    engine, request = environment(tmp_path, collected)
    request["enable"] = ["starter/" + local_id for local_id in STARTER_ROOTS]
    plan, _ = apply(engine, request)
    assert {row["item_id"] for row in plan["graph"]["items"]} == set(AUDIT["starter_items"])
    assert {row["item_id"] for row in plan["graph"]["roots"]} == set(STARTER_ROOTS)
    plan, outputs = engine.build(
        {
            "operation": "recipe.configure",
            "enable": [
                group + "/" + local_id
                for group, local_id, kind in ITEMS
                if group != "context-contracts" and kind != "Hook"
            ],
        }
    )
    assert len(plan["graph"]["items"]) == 49
    engine.apply(plan)
    assert engine.status()["pending_changes"] == 0
    # Every visible Markdown link generated from a typed dependency reaches an actual output.
    for path, data in outputs.items():
        if not path.endswith((".md", ".toml")):
            continue
        text = (
            tomllib.loads(data.decode())["developer_instructions"]
            if path.endswith(".toml")
            else data.decode()
        )
        for destination in re.findall(r"\]\(([^\s()]+)\)", text):
            parts = urlsplit(destination)
            if parts.scheme or parts.netloc or not parts.path or parts.path.startswith("/"):
                continue
            if "dasync:dependency/" in destination:
                pytest.fail("Unrendered canonical reference")
            if ".codex/" in destination or "dasync-" in destination or "../" in destination:
                target = (Path(path).parent / unquote(parts.path)).resolve()
                assert str(target) in outputs, (path, destination)


def test_imports_require_explicit_trust_and_scope_binding_not_just_retained_bytes(tmp_path, collected):
    engine, request = environment(tmp_path, collected)
    request["registrations"] = [row for row in request["registrations"] if row["alias"] == "engineering"]
    request["enable"] = ["engineering/skill.pr-review"]
    with pytest.raises(DasyncError) as rejected:
        engine.build(request)
    assert rejected.value.code == "SOURCE_UNBOUND" and not registry(engine)["sources"]
    assert engine.state.head(engine.scope.key) is None
    registration = {**request, "enable": []}
    apply(engine, registration)
    with pytest.raises(DasyncError) as rejected:
        engine.build({"operation": "recipe.configure", "enable": ["engineering/skill.pr-review"]})
    assert rejected.value.code == "SOURCE_UNBOUND"
    apply(
        engine,
        {
            "operation": "recipe.configure",
            "registrations": [{"candidate": collected[2]["starter"]["candidate"], "alias": "my-label"}],
            "trust_source": True,
            "enable": ["engineering/skill.pr-review"],
        },
    )
    assert engine.status()["pending_changes"] == 0


def test_hook_approval_is_scope_and_digest_specific_and_never_implied_by_source_trust(tmp_path, collected):
    engine, request = environment(tmp_path, collected)
    request["enable"] = ["hooks/" + HOOK[1]]
    with pytest.raises(DasyncError) as rejected:
        engine.build(request)
    assert rejected.value.code == "EXECUTABLE_TRUST_REQUIRED"
    assert executable_state(engine)["generation"] == 0 and not registry(engine)["sources"]
    request["approve_executables"] = [hook_approval(engine.env.cache, collected[2]["hooks"]["candidate"])]
    plan, result = apply(engine, request)
    assert (HOOK, request["approve_executables"][0]["digest"]) in approved_pairs(
        executable_state(engine), engine.scope.key
    )
    assert "approve_executables" not in json.loads(engine.scope.config.read_text())
    assert "approve_executables" not in json.loads((engine.scope.root / ".dasync.lock").read_text())
    other = tmp_path / "other"
    other.mkdir()
    project = Engine(engine.env, Scope.get(engine.env, "project", str(other)))
    with pytest.raises(DasyncError) as rejected:
        project.build(
            {
                "operation": "recipe.configure",
                "bind_sources": [{"source_id": HOOK[0], "pin": collected[2]["hooks"]["pin"]}],
                "enable": ["hooks/" + HOOK[1]],
            }
        )
    assert rejected.value.code == "EXECUTABLE_TRUST_REQUIRED"
    # The installed hook can be invoked with synthetic stdin, independently of a provider/model session.
    settings = json.loads((engine.scope.root / ".codex/hooks.json").read_text())
    command = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    checked = subprocess.run(
        shlex.split(command),
        input=json.dumps({"tool_name": "Read", "tool_input": {"file_path": "/tmp/example/.aws/credentials"}}),
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert checked.returncode == 2
    assert engine.state.head(engine.scope.key)["id"] == result["receipt"]
    assert plan["operations"]


def test_tui_stages_the_real_collection_and_requires_a_separate_hook_approval(
    tmp_path, collected, monkeypatch
):
    monkeypatch.delenv("NO_COLOR", raising=False)
    engine, request = environment(tmp_path, collected)
    apply(engine, request)

    async def journey():
        app = RecipeApp(engine)
        async with app.run_test(size=(140, 42)) as pilot:
            assert app.query_one("#items", DataTable).row_count == 70
            assert sum(row["private"] for row in app.visible_rows) == 20
            app.session.toggle(HOOK)
            app.refresh_catalog()
            app.show_detail(HOOK)
            await app.action_review()
            assert app.session.plan is None and "EXECUTABLE_TRUST_REQUIRED" in str(
                app.query_one("#message", Static).render()
            )
            app.action_approve_hook()
            await pilot.pause()
            assert isinstance(app.screen, Confirm)
            await pilot.click("#cancel")
            assert not app.session.approvals and executable_state(engine)["generation"] == 0
            app.action_approve_hook()
            await pilot.pause()
            await pilot.click("#confirm")
            assert app.session.approvals and executable_state(engine)["generation"] == 0
            await app.action_review()
            assert app.session.plan["request"]["approve_executables"]
            assert executable_state(engine)["generation"] == 0

    asyncio.run(journey())


@pytest.mark.parametrize("edge_mask", range(64))
def test_exhaustive_three_source_import_graphs_roots_and_disables(edge_mask):
    sids = [SOURCE_IDS[group] for group in GROUPS[:3]]
    adjacency = [set() for _ in range(3)]
    for bit, (a, b) in enumerate(
        (pair for pair in itertools.product(range(3), repeat=2) if pair[0] != pair[1])
    ):
        if edge_mask & (1 << bit):
            adjacency[a].add(b)
    sources = {}
    for n, sid in enumerate(sids):
        metadata = {
            "format": 1,
            "source_id": sid,
            "name": "synthetic",
            "description": "Synthetic imported graph",
            "requires_engine": ">=0.1.1,<1",
            "required_features": ["imports"],
            "items": ["items/item.yaml"],
            "imports": {f"r{i}": {"source_id": value} for i, value in enumerate(sids)},
        }
        sources[sid] = RecipeSnapshot(
            {
                "recipe.yaml": canonical(metadata),
                "items/item.yaml": canonical(
                    item(requires={f"r{i}/skill.review": ">=1" for i in adjacency[n]})
                ),
                "items/BODY.md": b"# Synthetic",
            }
        )
    for roots_mask, disabled_mask in itertools.product(range(8), repeat=2):
        roots = {n for n in range(3) if roots_mask & 1 << n}
        disabled = {n for n in range(3) if disabled_mask & 1 << n}
        expected, blocker = oracle(adjacency, roots, disabled)
        intent = {
            "version": 2,
            "protocol": 1,
            "providers": ["codex"],
            "inherit_user": False,
            "sources": [{"source_id": sid, "pin": source.pin} for sid, source in sources.items()],
            "roots": [key_record((sids[n], "skill.review")) for n in roots],
            "disabled": [key_record((sids[n], "skill.review")) for n in disabled],
        }
        try:
            selected, graph = resolve(sources, intent, "project")
        except DasyncError as exc:
            assert blocker and exc.code in ("DEPENDENCY_DISABLED", "DEPENDENCY_CYCLE")
        else:
            assert blocker is None and set(selected) == {(sids[n], "skill.review") for n in expected}
            assert resolve(dict(reversed(list(sources.items()))), intent, "project")[1] == graph

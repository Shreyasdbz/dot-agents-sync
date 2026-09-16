import copy
import importlib.util
import json
import posixpath
import re
from pathlib import Path

import pytest
from dasync.adapters import capabilities, private_reference, render
from dasync.catalog import Catalog
from dasync.config import Scope
from dasync.contracts import validate
from dasync.errors import DasyncError
from dasync.io import parse
from dasync.resolver import resolve
from test_contracts import planning_context


def test_private_package_attachments_never_materialize(workspace, tmp_path):
    engine, config = workspace
    catalog = Catalog(config["source"])
    private = catalog.packages["context.design-preferences"]
    private.files["CONTEXT.md"] = b"PRIVATE PACKAGE BODY"
    private.files["notes.txt"] = b"PRIVATE AUXILIARY FILE"
    private.manifest["files"].append("notes.txt")
    skill = catalog.packages["skill.propose"]
    skill.manifest["requires"][private.id] = ">=1,<2"
    config["contexts"] = [private.id]
    source = tmp_path / "private.md"
    source.write_text("PRIVATE BINDING BODY")
    user = {
        "bindings": {
            private.id: {
                "path": str(source),
                "projects": [config["project"]],
                "providers": config["providers"],
            }
        }
    }
    selected, graph, bindings = resolve(catalog, config, engine.scope, user)
    artifacts, _ = render(selected, graph, bindings, config, engine.scope)
    for artifact in artifacts:
        assert b"PRIVATE PACKAGE BODY" not in artifact.content
        assert b"PRIVATE AUXILIARY FILE" not in artifact.content
        assert b"PRIVATE BINDING BODY" not in artifact.content
        assert str(source).encode() not in artifact.content
    lookup = private_reference(private, engine.scope, "skill.propose")
    assert "--consumer skill.propose" in lookup
    assert "--allow-private-path" in lookup


def test_skill_metadata_and_declared_references(workspace):
    catalog = Catalog(workspace[1]["source"])
    for package in catalog.packages.values():
        if package.manifest["kind"] != "Skill":
            continue
        body = package.files["SKILL.md"]
        metadata = parse(body.split(b"\n---\n", 1)[0][4:])
        assert metadata["description"] == package.manifest["description"]
        presentation = package.manifest["presentation"]
        assert 25 <= len(presentation["short_description"]) <= 64
        assert f"$dasync-{package.id.replace('.', '-')}" in presentation["default_prompt"]
        assert len(body) <= 4200
    assert "sizing.md" in catalog.packages["skill.plan-out"].files


def test_ui_design_profile_keeps_live_and_swiftui_guidance_bounded(workspace):
    catalog = Catalog(workspace[1]["source"])
    package = catalog.packages["skill.ui-design"]
    assert catalog.profiles["ui-design"]["packages"] == ["skill.ui-design"]
    assert package.manifest["prefers"] == ["mcp.ui-skills"]
    assert len(package.files["SKILL.md"]) < 3600
    assert len(package.files["swiftui.md"]) < 3000
    assert b"https://www.ui-skills.com/mcp" in package.files["SKILL.md"]
    assert b"c2454e6948175e25e61c107c6dc7ebf03e291dfe" in package.files["swiftui.md"]
    assert all("mcp.ui-skills" in value["conditional"] for value in capabilities().values())


def test_native_policy_dependencies_are_not_duplicated(workspace):
    engine, config = workspace
    catalog = Catalog(config["source"])
    selected, graph, bindings = resolve(catalog, config, engine.scope, None)
    artifacts, _ = render(selected, graph, bindings, config, engine.scope)
    assert not any("/references/policy." in artifact.relative for artifact in artifacts)
    assert any(artifact.relative == "AGENTS.md" for artifact in artifacts)
    assert any(artifact.relative.startswith(".claude/rules/") for artifact in artifacts)
    assert any(artifact.relative.startswith(".cursor/rules/") for artifact in artifacts)
    user_scope = Scope.get(engine.env, "user", None)
    config["providers"] = ["cursor"]
    selected, graph, bindings = resolve(catalog, config, user_scope, None)
    artifacts, _ = render(selected, graph, bindings, config, user_scope)
    assert any("/references/policy." in artifact.relative for artifact in artifacts)


def test_plan_context_task_cycle_and_parent_cycle():
    value = planning_context()
    phase = value["milestones"][0]["phases"][0]
    phase["tasks"][0]["dependencies"] = [phase["id"]]
    with pytest.raises(DasyncError, match="cycle"):
        validate("plan-context", value)
    phase["tasks"][0]["dependencies"] = ["missing"]
    with pytest.raises(DasyncError, match="elaborated"):
        validate("plan-context", value)


def test_offline_plan_preserves_external_identity():
    value = planning_context()
    value["authority_state"] = "unavailable"
    task = value["milestones"][0]["phases"][0]["tasks"][0]
    task.update(reference="INV-7", status="in-progress", scope="Existing parser work")
    validate("plan-context", value)


def test_capability_fallbacks_match_modes(workspace):
    engine, config = workspace
    catalog = Catalog(config["source"])
    for pid, missing in [
        ("skill.trip-plan", "web.search"),
        ("skill.pitch-deck", "browser.render"),
        ("skill.curate-am-playlist", "music.search"),
        ("skill.plan-out", "planning.tracker"),
    ]:
        current = copy.deepcopy(config)
        current["packages"] = [pid]
        selected, graph, bindings = resolve(catalog, current, engine.scope, None)
        _, decisions = render(selected, graph, bindings, current, engine.scope)
        assert all(missing in d["missing_preferred"] for d in decisions if d["package"] == pid)
        current["capabilities"] = catalog.packages[pid].manifest["prefers"]
        _, decisions = render(selected, graph, bindings, current, engine.scope)
        assert all(d["status"] == "supported" for d in decisions if d["package"] == pid)


def test_metrics_are_byte_counts_not_claimed_tokens():
    path = Path(__file__).resolve().parents[1] / "evals/catalog_metrics.py"
    spec = importlib.util.spec_from_file_location("catalog_metrics", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.measure()
    assert result["groups"]["Skill"]["packages"] == 10
    assert result["groups"]["Skill"]["entry_bytes"] == sum(
        p["entry_bytes"] for key, p in result["packages"].items() if key.startswith("skill.")
    )


def test_context_references_are_packaged_and_private_contracts_stay_bounded(workspace):
    catalog = Catalog(workspace[1]["source"])
    for package in catalog.packages.values():
        if package.manifest["kind"] != "Context":
            continue
        if package.manifest["context"]["sensitivity"] == "private":
            assert len(package.files[package.manifest["entry"]]) < 2400
        for name, body in package.files.items():
            if not name.endswith(".md"):
                continue
            for link in re.findall(r"\]\(([^)]+)\)", body.decode()):
                if "://" in link or link.startswith("#"):
                    continue
                target = posixpath.normpath(posixpath.join(posixpath.dirname(name), link.split("#")[0]))
                assert target in package.files, (package.id, name, link)


def test_all_behavioral_scenarios_reference_real_packages(workspace):
    catalog = Catalog(workspace[1]["source"])
    cases = json.loads((Path(__file__).resolve().parents[1] / "evals/cases.json").read_text())
    assert len({case["id"] for case in cases}) == len(cases)
    for case in cases:
        assert case["package"] in catalog.packages
        assert case["prompt"].strip()
        assertions = case["assertions"]
        assert assertions and len({item["id"] for item in assertions}) == len(assertions)
        assert all(item["text"].strip() for item in assertions)

import json
import posixpath
import re
import subprocess
import tomllib
from pathlib import Path

import pytest
from dasync.adapters import render
from dasync.catalog import Catalog
from dasync.contracts import validate
from dasync.errors import DasyncError
from dasync.resolver import resolve
from test_contracts import planning_context

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("profile", ["planning-github", "travel"])
def test_new_profiles_apply_and_sync_without_private_bindings(workspace, profile):
    engine, config = workspace
    config["packages"] = []
    config["profiles"] = [profile]
    plan, _ = engine.build({"operation": "setup", "config": config, "trust_source": True})
    first = engine.apply(plan)
    assert first["changed"]
    plan, _ = engine.build({"operation": "sync"})
    assert all(op["action"] == "keep" for op in plan["operations"])
    assert not engine.apply(plan)["changed"]
    assert engine.status()["pending_changes"] == 0


def test_github_profile_keeps_private_authority_optional(workspace):
    engine, config = workspace
    config["packages"] = []
    config["profiles"] = ["planning-github"]
    selected, graph, bindings = resolve(Catalog(config["source"]), config, engine.scope, None)
    assert {"skill.plan-out", "policy.github-planning", "context.github-planning"} <= selected.keys()
    assert not bindings
    assert "context.planning-authority" not in selected
    artifacts, _ = render(selected, graph, bindings, config, engine.scope)
    by_path = {a.relative: a.content for a in artifacts}
    for artifact in artifacts:
        if artifact.relative.endswith("/CONTEXT.md") and "github-planning" in artifact.relative:
            recipe = posixpath.join(posixpath.dirname(artifact.relative), "issue-bodies.md")
            assert recipe in by_path
    assert not any(p.manifest["kind"] == "Hook" for p in selected.values())


def test_github_projection_preserves_native_references():
    value = planning_context()
    value["authority"] = "github"
    value["reference"] = "https://github.com/orgs/example/projects/1"
    for index, milestone in enumerate(value["milestones"], 1):
        milestone["reference"] = f"https://github.com/example/mono/milestone/{index}"
        if "planning_task" in milestone:
            milestone["planning_task"]["reference"] = "https://github.com/example/mono/issues/20"
        for phase in milestone.get("phases", []):
            phase["reference"] = "https://github.com/example/mono/issues/10"
            for task in phase["tasks"]:
                task["reference"] = "https://github.com/example/mono/issues/11"
    validate("plan-context", value)
    assert json.loads(json.dumps(value)) == value


@pytest.mark.parametrize("provider", ["codex", "claude", "cursor"])
def test_travel_profile_and_agent_reference_links(workspace, provider):
    engine, config = workspace
    config["packages"] = []
    config["profiles"] = ["travel"]
    config["providers"] = [provider]
    catalog = Catalog(config["source"])
    selected, graph, bindings = resolve(catalog, config, engine.scope, None)
    assert {"agent.travel-planner", "skill.trip-publish"} <= selected.keys()
    assert "skill.trip-plan" not in selected
    assert "context.travel-preferences" not in selected
    assert not bindings
    artifacts, decisions = render(selected, graph, bindings, config, engine.scope)
    by_path = {a.relative: a.content for a in artifacts}
    native = {
        "codex": ".codex/agents/dasync-agent-travel-planner.toml",
        "claude": ".claude/agents/dasync-agent-travel-planner.md",
        "cursor": ".cursor/dasync-references/agent.travel-planner/AGENT.md",
    }[provider]
    body = by_path[native].decode()
    if provider == "codex":
        role = tomllib.loads(body)
        assert role["sandbox_mode"] == "read-only"
        body = role["developer_instructions"]
    links = re.findall(r"\]\(([^)]+)\)", body)
    assert links
    for link in links:
        target = posixpath.normpath(posixpath.join(posixpath.dirname(native), link))
        assert target in by_path
    decision = next(d for d in decisions if d["package"] == "agent.travel-planner")
    assert "web.search" in decision["missing_preferred"]
    if provider == "cursor":
        assert "agents.native" in decision["missing_preferred"]


def test_trip_plan_compatibility_resolves_to_agent(workspace):
    engine, config = workspace
    config["packages"] = ["skill.trip-plan"]
    selected, _, _ = resolve(Catalog(config["source"]), config, engine.scope, None)
    assert "agent.travel-planner" in selected
    assert len(selected["skill.trip-plan"].files["SKILL.md"]) < 1200


def test_communication_is_required_by_all_output_roles(workspace):
    catalog = Catalog(workspace[1]["source"])
    for package in catalog.packages.values():
        if package.manifest["kind"] in {"Skill", "Agent"}:
            assert "policy.communication" in package.manifest["requires"]


def test_private_travel_context_requires_binding_and_never_copies(workspace, tmp_path):
    engine, config = workspace
    config["packages"] = ["agent.travel-planner", "context.travel-preferences"]
    config["contexts"] = ["context.travel-preferences"]
    catalog = Catalog(config["source"])
    with pytest.raises(DasyncError) as caught:
        resolve(catalog, config, engine.scope, None)
    assert caught.value.code == "CONTEXT_MISSING"
    private = tmp_path / "traveler.md"
    private.write_text("PRIVATE TRAVEL SENTINEL")
    user = {
        "bindings": {
            "context.travel-preferences": {
                "path": str(private),
                "projects": [config["project"]],
                "providers": config["providers"],
            }
        }
    }
    selected, graph, bindings = resolve(catalog, config, engine.scope, user)
    artifacts, _ = render(selected, graph, bindings, config, engine.scope)
    assert not any(b"PRIVATE TRAVEL SENTINEL" in a.content for a in artifacts)
    assert not any(str(private).encode() in a.content for a in artifacts)


def test_local_context_directory_is_gitignored():
    result = subprocess.run(
        ["git", "check-ignore", "local-contexts/travel-preferences.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    tracked = subprocess.run(
        ["git", "ls-files", "--", "local-contexts"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert not tracked.stdout.strip()

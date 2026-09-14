import json
import posixpath
import re
from pathlib import Path

import pytest
from dasync.adapters import render
from dasync.catalog import Catalog
from dasync.config import Scope
from dasync.resolver import resolve

POLICIES = {"policy.engineering-platform", "policy.monorepo", "policy.ui-shadcn"}
EXPECTED = POLICIES | {"policy.coding", "policy.verification", "context.engineering-stack"}


def select_profile(config):
    config["packages"] = []
    config["profiles"] = ["engineering-cloudflare"]


def test_profile_is_optional_public_and_bounded(workspace):
    engine, config = workspace
    catalog = Catalog(config["source"])
    selected, _, _ = resolve(catalog, config, engine.scope, None)
    assert not POLICIES & selected.keys()
    for name, profile in catalog.profiles.items():
        if name != "engineering-cloudflare":
            assert not POLICIES & set(profile["packages"])
    select_profile(config)
    selected, _, bindings = resolve(catalog, config, engine.scope, None)
    assert set(selected) == EXPECTED
    assert not bindings
    assert sum(len(selected[pid].files["POLICY.md"]) for pid in POLICIES) < 7000
    assert len(selected["context.engineering-stack"].files["CONTEXT.md"]) < 6000
    operations = selected["context.engineering-stack"].files["operations.md"]
    assert 0 < len(operations) < 5000
    assert b"operations.md" in selected["context.engineering-stack"].files["CONTEXT.md"]
    assert all(p.manifest["kind"] in {"Policy", "Context"} for p in selected.values())


@pytest.mark.parametrize("provider", ["codex", "claude", "cursor"])
@pytest.mark.parametrize("scope_kind", ["user", "project"])
def test_policy_reference_links_resolve(workspace, provider, scope_kind):
    engine, config = workspace
    select_profile(config)
    config["providers"] = [provider]
    scope = engine.scope if scope_kind == "project" else Scope.get(engine.env, "user", None)
    catalog = Catalog(config["source"])
    selected, graph, bindings = resolve(catalog, config, scope, None)
    artifacts, decisions = render(selected, graph, bindings, config, scope)
    by_path = {a.relative: a.content for a in artifacts}
    matches = []
    for artifact in artifacts:
        for link in re.findall(r"\]\(([^)]+/CONTEXT.md)\)", artifact.content.decode()):
            target = posixpath.normpath(posixpath.join(posixpath.dirname(artifact.relative), link))
            assert target in by_path, (artifact.relative, link, target)
            assert by_path[target] == selected["context.engineering-stack"].files["CONTEXT.md"]
            matches.append(target)
    assert len(matches) == 1
    assert not any(a.relative.endswith("SKILL.md") for a in artifacts)
    platform = next(d for d in decisions if d["package"] == "policy.engineering-platform")
    assert platform["status"] == (
        "degraded" if provider == "cursor" and scope_kind == "user" else "supported"
    )


def test_profile_applies_and_sync_is_idempotent(workspace):
    engine, config = workspace
    select_profile(config)
    plan, _ = engine.build({"operation": "setup", "config": config, "trust_source": True})
    first = engine.apply(plan)
    assert first["changed"]
    assert "Cloudflare-first" in (engine.scope.root / "AGENTS.md").read_text()
    operations = list(engine.scope.root.rglob("references/context.engineering-stack/operations.md"))
    assert operations
    assert all(b"LOCAL" in path.read_bytes() for path in operations)
    plan, _ = engine.build({"operation": "sync"})
    assert all(op["action"] == "keep" for op in plan["operations"])
    second = engine.apply(plan)
    assert not second["changed"]
    assert first["receipt"] == second["receipt"]
    assert engine.status()["pending_changes"] == 0
    assert not (engine.scope.root / ".dasync").exists()


def test_engineering_cases_have_valid_targets_and_assertions(workspace):
    catalog = Catalog(workspace[1]["source"])
    cases = json.loads((Path(__file__).resolve().parents[1] / "evals/cases.json").read_text())
    assert len({case["id"] for case in cases}) == len(cases)
    engineering = [case for case in cases if case["id"].startswith("engineering-")]
    assert len(engineering) == 5
    for case in engineering:
        assert case["package"] in catalog.packages
        assert case["prompt"]
        assert len({a["id"] for a in case["assertions"]}) == len(case["assertions"])
        assert all(a["text"] for a in case["assertions"])

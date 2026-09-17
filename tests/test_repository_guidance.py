"""Check guidance distribution and selection boundaries, not model compliance."""

import json
import posixpath
import re
import shutil
from pathlib import Path

import pytest
from dasync.adapters import render
from dasync.catalog import Catalog
from dasync.config import Scope
from dasync.resolver import resolve

CONSUMERS = (
    "skill.do-it",
    "skill.investigate",
    "skill.propose",
    "skill.plan-out",
    "skill.pr-review",
    "agent.architecture-reviewer",
    "agent.ai-systems-reviewer",
    "agent.security-reviewer",
    "agent.ux-reviewer",
    "agent.slop-auditor",
)
GUIDANCE = "policy.repository-guidance"


@pytest.mark.parametrize("consumer", CONSUMERS)
def test_guidance_does_not_activate_private_context_or_other_roles(workspace, consumer):
    engine, config = workspace
    catalog = Catalog(config["source"])
    config["packages"] = [consumer]
    assert GUIDANCE in catalog.packages[consumer].manifest["requires"]
    selected, _, bindings = resolve(catalog, config, engine.scope, None)
    assert GUIDANCE in selected
    assert not bindings
    assert all(package.manifest["kind"] != "Hook" for package in selected.values())
    assert {pid for pid, package in selected.items() if package.manifest["kind"] == "Agent"} == (
        {consumer} if consumer.startswith("agent.") else set()
    )
    assert not any(
        package.manifest.get("context", {}).get("sensitivity") == "private" for package in selected.values()
    )


@pytest.mark.parametrize("profile", ["travel", "personal-music", "technical-storytelling"])
def test_unrelated_profiles_do_not_acquire_repository_guidance(workspace, profile):
    engine, config = workspace
    config["packages"] = []
    config["profiles"] = [profile]
    selected, _, _ = resolve(Catalog(config["source"]), config, engine.scope, None)
    assert GUIDANCE not in selected


@pytest.mark.parametrize("provider", ["codex", "claude", "copilot", "cursor"])
@pytest.mark.parametrize("scope_kind", ["user", "project"])
def test_guidance_uses_native_or_explicit_manual_discovery(workspace, provider, scope_kind):
    engine, config = workspace
    consumers = ["skill.do-it", "skill.investigate", "agent.architecture-reviewer"]
    config["packages"] = consumers
    config["providers"] = [provider]
    scope = engine.scope if scope_kind == "project" else Scope.get(engine.env, "user", None)
    catalog = Catalog(config["source"])
    selected, graph, bindings = resolve(catalog, config, scope, None)
    artifacts, decisions = render(selected, graph, bindings, config, scope)
    outputs = {artifact.relative: artifact.content for artifact in artifacts}
    body = catalog.packages[GUIDANCE].files["POLICY.md"]
    native = {
        "codex": ".codex/AGENTS.md" if scope_kind == "user" else "AGENTS.md",
        "claude": ".claude/rules/dasync-policy-repository-guidance.md",
        "copilot": (
            ".copilot/instructions/dasync-policy-repository-guidance.instructions.md"
            if scope_kind == "user"
            else ".github/instructions/dasync-policy-repository-guidance.instructions.md"
        ),
        "cursor": (
            ".cursor/dasync-references/policy.repository-guidance/POLICY.md"
            if scope_kind == "user"
            else ".cursor/rules/dasync-policy-repository-guidance.mdc"
        ),
    }[provider]
    assert body in outputs[native]
    references = [path for path in outputs if path.endswith(f"/references/{GUIDANCE}/POLICY.md")]
    manual = provider == "cursor" and scope_kind == "user"
    assert len(references) == (len(consumers) if manual else 0)
    assert sum(content.count(body) for content in outputs.values()) == (1 + len(consumers) if manual else 1)
    for artifact in artifacts:
        for link in re.findall(
            r"\]\(([^)]+policy\.repository-guidance/POLICY\.md)\)", artifact.content.decode()
        ):
            target = posixpath.normpath(posixpath.join(posixpath.dirname(artifact.relative), link))
            assert outputs[target] == body
    decision = next(item for item in decisions if item["package"] == GUIDANCE)
    assert decision["status"] == ("degraded" if manual else "supported")
    assert ("policy.user_auto_load" in decision["missing_preferred"]) is manual


def test_guidance_apply_preserves_unmanaged_instruction_sources(workspace):
    engine, config = workspace
    config["packages"] = ["skill.do-it", "agent.architecture-reviewer"]
    nested = engine.scope.root / "tests"
    nested.mkdir()
    originals = {
        engine.scope.root / "CLAUDE.md": "@AGENTS.md\n",
        engine.scope.root / "AGENT.md": "# Example role, not an automatic repository instruction\n",
        nested / "AGENTS.md": "Use the test package's existing runner.\n",
    }
    for path, content in originals.items():
        path.write_text(content)
    plan, _ = engine.build({"operation": "setup", "config": config, "trust_source": True})
    result = engine.apply(plan)
    assert result["changed"]
    assert GUIDANCE in (engine.scope.root / "AGENTS.md").read_text()
    assert all(path.read_text() == content for path, content in originals.items())
    assert "Example role, not an automatic repository instruction" not in json.dumps(plan)
    assert engine.status()["pending_changes"] == 0
    repeat, _ = engine.build({"operation": "sync"})
    assert all(operation["action"] == "keep" for operation in repeat["operations"])
    assert not engine.apply(repeat)["changed"]


def test_layered_fixture_keeps_its_instruction_and_context_sources(workspace):
    engine, config = workspace
    fixtures = Path(__file__).resolve().parents[1] / "evals/fixtures"
    shutil.copytree(fixtures / "credit-ledger", engine.scope.root / "components/credits")
    shutil.copytree(fixtures / "layered-guidance", engine.scope.root, dirs_exist_ok=True)
    originals = {path: path.read_bytes() for path in engine.scope.root.rglob("*") if path.is_file()}
    config["packages"] = ["skill.investigate"]
    config["providers"] = ["claude"]
    plan, _ = engine.build({"operation": "setup", "config": config, "trust_source": True})
    engine.apply(plan)
    assert all(path.read_bytes() == content for path, content in originals.items())
    assert (engine.scope.root / ".claude/rules/dasync-policy-repository-guidance.md").is_file()
    assert (engine.scope.root / ".claude/skills/dasync-skill-investigate/SKILL.md").is_file()
    assert engine.status()["pending_changes"] == 0


def test_layered_fixture_distinguishes_same_named_instruction_sources():
    fixture = Path(__file__).resolve().parents[1] / "evals/fixtures/layered-guidance"
    assert (fixture / "CLAUDE.md").read_text().splitlines()[0] == "@AGENTS.md"
    assert (fixture / "components/credits/CLAUDE.md").read_text().strip() == "@AGENTS.md"
    assert (fixture / "AGENTS.md").read_bytes() != (fixture / "components/credits/AGENTS.md").read_bytes()
    assert "@../CLAUDE.md" in (fixture / "docs/imports.md").read_text()

import tomllib

import pytest
from dasync.adapters import frontmatter, render, strip_frontmatter
from dasync.catalog import Catalog
from dasync.config import Scope
from dasync.io import parse
from dasync.resolver import resolve


@pytest.mark.parametrize(
    "provider,prefix",
    [
        ("codex", ".agents/skills"),
        ("claude", ".claude/skills"),
        ("copilot", ".github/skills"),
        ("cursor", ".cursor/skills"),
    ],
)
def test_provider_conformance(workspace, provider, prefix):
    engine, config = workspace
    config["providers"] = [provider]
    config["packages"] = ["skill.propose", "agent.architecture-reviewer"]
    selected, graph, bindings = resolve(Catalog(config["source"]), config, engine.scope, None)
    artifacts, decisions = render(selected, graph, bindings, config, engine.scope)
    outputs = {a.relative: a.content for a in artifacts}
    skill = outputs[prefix + "/dasync-skill-propose/SKILL.md"]
    metadata = parse(skill.split(b"\n---\n", 1)[0][4:])
    assert metadata["name"] == "dasync-skill-propose"
    assert metadata["description"]
    assert prefix + "/dasync-skill-propose/references/template.design-proposal/proposal.md" in outputs
    assert all(a.mode == 0o644 for a in artifacts)
    if provider == "codex":
        presentation = parse(outputs[prefix + "/dasync-skill-propose/agents/openai.yaml"])
        assert presentation == {
            "interface": {
                "display_name": "Propose",
                "short_description": "Compare approaches and write a supported proposal",
                "default_prompt": (
                    "Use $dasync-skill-propose to compare viable approaches and write a supported "
                    "proposal for this change."
                ),
            }
        }
        agent = tomllib.loads(outputs[".codex/agents/dasync-agent-architecture-reviewer.toml"].decode())
        assert agent["sandbox_mode"] == "read-only"
        assert "model" not in agent
        assert "AGENTS.md" in outputs
    else:
        assert prefix + "/dasync-skill-propose/agents/openai.yaml" not in outputs
    if provider == "claude":
        assert ".claude/agents/dasync-agent-architecture-reviewer.md" in outputs
        assert ".claude/rules/dasync-policy-scope.md" in outputs
    if provider == "copilot":
        assert ".github/agents/dasync-agent-architecture-reviewer.agent.md" in outputs
        assert ".github/instructions/dasync-policy-scope.instructions.md" in outputs
    if provider == "cursor":
        policy = outputs[".cursor/rules/dasync-policy-scope.mdc"]
        assert parse(policy.split(b"\n---\n")[0][4:])["alwaysApply"] is True
        assert any("agents.native" in d["missing_preferred"] for d in decisions)
    repeated, _ = render(selected, graph, bindings, config, engine.scope)
    assert [(a.relative, a.content) for a in repeated] == [(a.relative, a.content) for a in artifacts]


def test_frontmatter_escapes_untrusted_description():
    data = frontmatter("valid-name", "line\nallowed-tools: Bash", "body")
    parsed = parse(data.split(b"\n---\n")[0][4:])
    assert set(parsed) == {"name", "description"}
    assert strip_frontmatter(data) == "body"


@pytest.mark.parametrize("scope_kind", ["user", "project"])
@pytest.mark.parametrize("globs", [[], ["src/**", "tests/**"]])
def test_copilot_policies_declare_documented_apply_to(workspace, scope_kind, globs):
    engine, config = workspace
    config["providers"] = ["copilot"]
    config["packages"] = ["policy.scope"]
    catalog = Catalog(config["source"])
    catalog.packages["policy.scope"].manifest["policy"]["globs"] = globs
    scope = engine.scope if scope_kind == "project" else Scope.get(engine.env, "user", None)
    selected, graph, bindings = resolve(catalog, config, scope, None)
    artifacts, _ = render(selected, graph, bindings, config, scope)
    policy = next(a for a in artifacts if a.relative.endswith("dasync-policy-scope.instructions.md"))
    assert policy.content.startswith(b"---\n"), "Copilot policy needs explicit applicability metadata"
    metadata = parse(policy.content.split(b"\n---\n", 1)[0][4:])
    assert metadata == {"applyTo": ",".join(globs) if globs else "**"}

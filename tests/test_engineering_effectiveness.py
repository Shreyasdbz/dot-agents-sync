import copy
import json

import pytest
from dasync.adapters import render
from dasync.catalog import Catalog
from dasync.config import Scope, initial
from dasync.engine import Engine
from dasync.errors import DasyncError
from dasync.resolver import resolve
from test_cli import invoke

POLICY = "policy.engineering-effectiveness"
CONTEXT = "context.engineering-standards"
CONSUMERS = [
    "skill.do-it",
    "skill.propose",
    "skill.plan-out",
    "skill.investigate",
    "skill.pr-review",
    "agent.architecture-reviewer",
    "agent.security-reviewer",
    "agent.ai-systems-reviewer",
    "agent.ux-reviewer",
    "agent.slop-auditor",
]


@pytest.mark.parametrize("consumer", CONSUMERS)
def test_engineering_consumers_select_policy_without_private_context(workspace, consumer):
    engine, config = workspace
    config["packages"] = [consumer]
    selected, _, bindings = resolve(Catalog(config["source"]), config, engine.scope, None)
    assert POLICY in selected
    assert CONTEXT not in selected
    assert not bindings


def test_non_engineering_selection_does_not_add_engineering_workflow(workspace):
    engine, config = workspace
    config["packages"] = ["skill.curate-am-playlist"]
    selected, _, _ = resolve(Catalog(config["source"]), config, engine.scope, None)
    assert POLICY not in selected
    assert CONTEXT not in selected


def test_all_public_excludes_organization_context(workspace):
    engine, config = workspace
    catalog = Catalog(config["source"])
    config["all_public"] = True
    config["approved_executables"] = [p.digest for p in catalog.packages.values()]
    selected, _, bindings = resolve(catalog, config, engine.scope, None)
    assert POLICY in selected
    assert CONTEXT not in selected
    assert not bindings


@pytest.mark.parametrize("provider", ["codex", "claude", "copilot", "cursor"])
@pytest.mark.parametrize("scope_kind", ["user", "project"])
def test_private_standard_lookup_and_native_policy_distribution(workspace, tmp_path, provider, scope_kind):
    engine, config = workspace
    catalog = Catalog(config["source"])
    config["packages"] = [POLICY, CONTEXT]
    config["providers"] = [provider]
    config["contexts"] = [CONTEXT]
    private = tmp_path / "standard.md"
    private.write_text("PRIVATE ORGANIZATION STANDARD SENTINEL")
    binding = {"path": str(private), "projects": [config["project"]], "providers": [provider]}
    scope = engine.scope if scope_kind == "project" else Scope.get(engine.env, "user", None)
    if scope_kind == "user":
        config["bindings"] = {CONTEXT: binding}
    selected, graph, bindings = resolve(catalog, config, scope, {"bindings": {CONTEXT: binding}})
    artifacts, decisions = render(selected, graph, bindings, config, scope)
    policy = catalog.packages[POLICY].files["POLICY.md"]
    outputs = {a.relative: a.content for a in artifacts}
    assert sum(content.count(policy) for content in outputs.values()) == 1
    lookups = [body for path, body in outputs.items() if path.endswith(f"/{CONTEXT}/CONTEXT.md")]
    assert len(lookups) == 1
    assert b"context locate context.engineering-standards" in lookups[0]
    assert b"--scope " + scope_kind.encode() in lookups[0]
    assert all(private.read_bytes() not in a.content for a in artifacts)
    assert all(str(private).encode() not in a.content for a in artifacts)
    assert all(catalog.packages[CONTEXT].files["CONTEXT.md"] not in a.content for a in artifacts)
    decision = next(d for d in decisions if d["package"] == POLICY)
    assert decision["status"] == (
        "degraded" if provider == "cursor" and scope_kind == "user" else "supported"
    )


def test_standard_grants_apply_lookup_and_idempotence(workspace, tmp_path):
    engine, config = workspace
    config["packages"] = ["skill.do-it", CONTEXT]
    config["contexts"] = [CONTEXT]
    source = tmp_path / "organization.md"
    source.write_text("PRIVATE ORGANIZATION STANDARD SENTINEL")
    user = initial("user", config["source"], config["providers"])
    user["bindings"] = {
        CONTEXT: {
            "path": str(source),
            "projects": [config["project"]],
            "providers": config["providers"],
        }
    }
    catalog = Catalog(config["source"])
    with pytest.raises(DasyncError) as missing:
        resolve(catalog, config, engine.scope, None)
    assert missing.value.code == "CONTEXT_MISSING"
    denied = copy.deepcopy(user)
    denied["bindings"][CONTEXT]["projects"] = []
    with pytest.raises(DasyncError) as project_denied:
        resolve(catalog, config, engine.scope, denied)
    assert project_denied.value.code == "PRIVATE_CONTEXT"
    denied["bindings"][CONTEXT]["projects"] = [config["project"]]
    denied["bindings"][CONTEXT]["providers"] = []
    with pytest.raises(DasyncError) as provider_denied:
        resolve(catalog, config, engine.scope, denied)
    assert provider_denied.value.code == "PRIVATE_CONTEXT"

    user_engine = Engine(engine.env, Scope.get(engine.env, "user", None))
    user_plan, _ = user_engine.build({"operation": "setup", "config": user, "trust_source": True})
    user_engine.apply(user_plan)
    plan, _ = engine.build({"operation": "setup", "config": config, "trust_source": True})
    assert source.read_text() not in json.dumps(plan)
    first = engine.apply(plan)
    common = ["--scope", "project", "--path", str(engine.scope.root)]
    args = ["context", "locate", CONTEXT, *common, "--allow-private-path"]
    code, authorized = invoke(workspace, *args, "--consumer", POLICY)
    assert code == 0, authorized
    assert authorized["result"]["path"] == str(source)
    code, unauthorized = invoke(workspace, *args, "--consumer", "skill.curate-am-playlist")
    assert code == 2
    assert unauthorized["error"]["code"] == "PRIVATE_CONTEXT"
    code, doctor = invoke(workspace, "doctor", *common)
    assert code == 0 and doctor["result"]["healthy"]
    repeat, _ = engine.build({"operation": "sync"})
    assert all(operation["action"] == "keep" for operation in repeat["operations"])
    second = engine.apply(repeat)
    assert not second["changed"]
    assert second["receipt"] == first["receipt"]
    assert source.read_text() == "PRIVATE ORGANIZATION STANDARD SENTINEL"

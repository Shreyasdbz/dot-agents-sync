import pytest
from dasync.adapters import render
from dasync.catalog import Catalog
from dasync.contracts import validate
from dasync.errors import DasyncError
from dasync.resolver import resolve


@pytest.mark.parametrize("provider", ["codex", "claude", "copilot", "cursor"])
def test_entire_catalog_compiles(workspace, provider, tmp_path):
    engine, config = workspace
    catalog = Catalog(config["source"])
    config["providers"] = [provider]
    config["packages"] = sorted(catalog.packages)
    user = {"bindings": {}}
    private = tmp_path / "private-context.md"
    private.write_text("PRIVATE SENTINEL: never materialize this content")
    for pid, package in catalog.packages.items():
        validate("manifest", package.manifest)
        if package.manifest.get("context", {}).get("sensitivity") == "private":
            config["contexts"].append(pid)
            user["bindings"][pid] = {
                "path": str(private),
                "projects": [config["project"]],
                "providers": [provider],
            }
        if package.manifest.get("executable"):
            config["approved_executables"].append(package.digest)
    for profile in catalog.profiles.values():
        validate("profile", profile)
        assert set(profile["packages"]) <= catalog.packages.keys()
        assert not any(catalog.packages[pid].manifest["kind"] == "Hook" for pid in profile["packages"])
    selected, graph, bindings = resolve(catalog, config, engine.scope, user)
    artifacts, decisions = render(selected, graph, bindings, config, engine.scope)
    assert len(decisions) >= len(catalog.packages)
    assert len({a.relative.casefold() for a in artifacts}) == len(artifacts)
    assert not any(b"PRIVATE SENTINEL" in a.content for a in artifacts)
    assert not any(str(private).encode() in a.content for a in artifacts)


def test_backup_preparation_rejects_concurrent_edit(installed, monkeypatch):
    import dasync.state as state_module

    engine, config, _ = installed
    config["packages"].append("skill.pr-review")
    plan, _ = engine.build({"operation": "configure", "config": config, "config_only": False})
    original = state_module.snapshot_entry

    def changed_snapshot(path):
        if path == engine.scope.config:
            return b"externally changed", 0o644, "file"
        return original(path)

    monkeypatch.setattr(state_module, "snapshot_entry", changed_snapshot)
    with pytest.raises(DasyncError, match="preparing its backup"):
        engine.apply(plan)
    assert not engine.state.pending()

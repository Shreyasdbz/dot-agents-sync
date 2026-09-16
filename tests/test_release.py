import pytest
from dasync.adapters import render
from dasync.catalog import Catalog
from dasync.contracts import validate
from dasync.errors import DasyncError
from dasync.resolver import resolve


def test_catalog_declares_release_license(workspace):
    catalog = Catalog(workspace[1]["source"])
    assert {package.manifest["license"] for package in catalog.packages.values()} == {"MIT"}


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
    notice = catalog.packages["skill.ui-design"].files["LICENSE.fwc-swiftui-skills.txt"]
    assert b"Copyright (c) 2026 FloWritesCode" in notice
    assert any(
        artifact.relative.endswith("/LICENSE.fwc-swiftui-skills.txt") and artifact.content == notice
        for artifact in artifacts
    )


def test_all_public_selects_complete_safe_catalog(workspace):
    engine, config = workspace
    catalog = Catalog(config["source"])
    config["packages"] = []
    config["profiles"] = []
    config["all_public"] = True
    config["approved_executables"] = [
        package.digest for package in catalog.packages.values() if package.manifest.get("executable")
    ]
    selected, graph, bindings = resolve(catalog, config, engine.scope, None)
    expected = {
        package.id
        for package in catalog.packages.values()
        if engine.scope.kind in package.manifest["scopes"]
        and set(config["providers"]) <= set(package.manifest.get("providers", config["providers"]))
        and not (
            package.manifest["kind"] == "Context"
            and package.manifest.get("context", {}).get("sensitivity") == "private"
        )
    }
    assert set(selected) == expected
    assert not bindings
    assert all("all-public" in package["provenance"] for package in graph["packages"])


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

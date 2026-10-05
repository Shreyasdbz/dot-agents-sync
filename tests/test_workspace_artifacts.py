"""Workspace branding stays optional and respects private context grants."""

import copy

import pytest
from dasync.adapters import render
from dasync.catalog import Catalog
from dasync.errors import DasyncError
from dasync.resolver import resolve


def test_visual_artifacts_does_not_implicitly_select_private_brand(workspace):
    engine, config = workspace
    config["packages"] = ["skill.visual-artifacts"]
    config["all_public"] = True
    config["disabled"] = ["hook.credential-path-guard"]
    selected, _, bindings = resolve(Catalog(config["source"]), config, engine.scope, None)
    assert "context.workspace-artifacts" not in selected
    assert not bindings


def test_workspace_brand_requires_grants_and_never_copies_source(workspace, tmp_path):
    engine, config = workspace
    catalog = Catalog(config["source"])
    context_id = "context.workspace-artifacts"
    source = tmp_path / "brand.md"
    source.write_text("PRIVATE BRAND SENTINEL")
    config["packages"] = ["skill.visual-artifacts", context_id]
    config["contexts"] = [context_id]
    user = {
        "bindings": {
            context_id: {
                "path": str(source),
                "projects": [config["project"]],
                "providers": config["providers"],
            }
        }
    }
    selected, graph, bindings = resolve(catalog, config, engine.scope, user)
    artifacts, _ = render(selected, graph, bindings, config, engine.scope)
    assert context_id in bindings
    assert all(b"PRIVATE BRAND SENTINEL" not in artifact.content for artifact in artifacts)
    assert all(str(source).encode() not in artifact.content for artifact in artifacts)

    for grant in ["projects", "providers"]:
        denied = copy.deepcopy(user)
        denied["bindings"][context_id][grant] = []
        with pytest.raises(DasyncError) as caught:
            resolve(catalog, config, engine.scope, denied)
        assert caught.value.code == "PRIVATE_CONTEXT"

    config["contexts"] = []
    with pytest.raises(DasyncError) as caught:
        resolve(catalog, config, engine.scope, user)
    assert caught.value.code == "PRIVATE_CONTEXT"

    config["contexts"] = [context_id]
    catalog.packages["skill.do-it"].manifest["requires"][context_id] = ">=1,<2"
    config["packages"] = ["skill.do-it"]
    with pytest.raises(DasyncError) as caught:
        resolve(catalog, config, engine.scope, user)
    assert caught.value.code == "PRIVATE_CONTEXT"

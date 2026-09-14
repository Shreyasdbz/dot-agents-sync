import copy
from pathlib import Path

import pytest
from dasync.catalog import Catalog
from dasync.errors import DasyncError
from dasync.io import parse, safe_path
from dasync.resolver import resolve
from hypothesis import given
from hypothesis import strategies as st


@pytest.mark.parametrize("value", [b"a: 1\na: 2", b"a: &a [*a]", b"!!python/object:foo {}", b"a: .nan"])
def test_reject_unsafe_yaml(value):
    with pytest.raises(DasyncError):
        parse(value)


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1))
def test_traversal_never_accepted(segment):
    with pytest.raises(DasyncError):
        safe_path(Path("/tmp/catalog"), "../" + segment)


def test_symlink_output(installed, tmp_path):
    engine, _, _ = installed
    target = engine.scope.root / ".claude/skills/dasync-skill-propose/SKILL.md"
    target.unlink()
    victim = tmp_path / "victim"
    victim.write_text("untouched")
    target.symlink_to(victim)
    with pytest.raises(DasyncError):
        engine.build({"operation": "sync"})
    assert victim.read_text() == "untouched"


def test_private_context_needs_both_grants(workspace):
    engine, config = workspace
    config = copy.deepcopy(config)
    config["packages"] = ["context.design-preferences"]
    catalog = Catalog(config["source"])
    private = engine.env.home / "private-context.md"
    private.write_text("private preferences")
    user = {
        "bindings": {
            "context.design-preferences": {
                "path": str(private),
                "projects": ["example"],
                "providers": config["providers"],
            }
        }
    }
    with pytest.raises(DasyncError):
        resolve(catalog, config, engine.scope, user)
    config["contexts"] = ["context.design-preferences"]
    resolve(catalog, config, engine.scope, user)
    user["bindings"]["context.design-preferences"]["projects"] = []
    with pytest.raises(DasyncError):
        resolve(catalog, config, engine.scope, user)


def test_disabled_dependency_fails(workspace):
    engine, config = workspace
    config["disabled"] = ["template.design-proposal"]
    with pytest.raises(DasyncError):
        engine.build({"operation": "setup", "config": config, "trust_source": True})

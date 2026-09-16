import copy
import shutil
import subprocess
from pathlib import Path

import pytest
from dasync.catalog import Catalog, pin
from dasync.errors import DasyncError
from dasync.io import canonical, parse
from dasync.resolver import resolve

ROOT = Path(__file__).resolve().parents[1]


def repository(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    shutil.copytree(ROOT / "packages", root / "packages")
    shutil.copytree(ROOT / "profiles", root / "profiles")

    def git(*args):
        return (
            subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
            .stdout.decode()
            .strip()
        )

    git("init", "-b", "main")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "user.name", "Test Fixture")
    git("add", ".")
    git("commit", "-m", "fixture")
    return root, git


def test_git_reads_pinned_objects_not_worktree(tmp_path):
    root, git = repository(tmp_path)
    source = pin(str(root), "git")
    expected = Catalog(source).digest
    (root / "packages/skills/propose/SKILL.md").write_text("uncommitted edit")
    assert Catalog(source).digest == expected
    git("add", ".")
    git("commit", "-m", "changed")
    assert Catalog(source).digest == expected
    assert Catalog(pin(str(root), "git")).digest != expected


def test_bare_cache_works_with_explicit_only_global_policy(tmp_path, monkeypatch):
    root, _ = repository(tmp_path)
    mirror = tmp_path / "mirror.git"
    subprocess.run(["git", "clone", "--mirror", str(root), str(mirror)], check=True, capture_output=True)
    policy = tmp_path / "gitconfig"
    policy.write_text("[safe]\n\tbareRepository = explicit\n")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(policy))
    source = pin(str(mirror), "git")
    assert source["revision"]
    assert Catalog(source).packages


def test_local_pin_detects_mutation(tmp_path):
    root, _ = repository(tmp_path)
    source = pin(str(root), "local")
    (root / "packages/skills/propose/SKILL.md").write_text("modified")
    with pytest.raises(DasyncError) as caught:
        Catalog(source)
    assert caught.value.code == "SOURCE_INTEGRITY"


def test_update_pin_and_outputs_roll_back_together(workspace, tmp_path):
    engine, config = workspace
    root, git = repository(tmp_path)
    config["source"] = pin(str(root), "git")
    plan, _ = engine.build({"operation": "setup", "config": config, "trust_source": True})
    engine.apply(plan)
    previous = engine.scope.config.read_bytes()
    path = root / "packages/skills/propose/SKILL.md"
    path.write_text(path.read_text() + "\nNew canonical decision.\n")
    git("add", ".")
    git("commit", "-m", "new revision")
    changed = copy.deepcopy(config)
    changed["source"] = pin(str(root), "git")
    plan, _ = engine.build({"operation": "update", "config": changed})

    def fail(stage, index):
        if stage == "before_receipt":
            raise RuntimeError("injected")

    with pytest.raises(RuntimeError):
        engine.apply(plan, fail)
    assert engine.scope.config.read_bytes() == previous
    result = engine.apply(plan)
    assert result["changed"]
    assert parse(engine.scope.config.read_bytes())["source"] == changed["source"]


@pytest.mark.parametrize(
    "mutation,code",
    [
        (
            lambda c: c.packages["template.design-proposal"].manifest.update(
                requires={"skill.propose": ">=1"}
            ),
            "DEPENDENCY_CYCLE",
        ),
        (
            lambda c: c.packages["skill.propose"].manifest.update(
                requires={"template.design-proposal": ">=99"}
            ),
            "VERSION_CONFLICT",
        ),
        (
            lambda c: c.packages["skill.propose"].manifest.update(conflicts=["policy.scope"]),
            "PACKAGE_CONFLICT",
        ),
    ],
)
def test_invalid_graphs(workspace, mutation, code):
    engine, config = workspace
    catalog = Catalog(config["source"])
    mutation(catalog)
    with pytest.raises(DasyncError) as caught:
        resolve(catalog, config, engine.scope, None)
    assert caught.value.code == code


def test_deterministic_order_for_reordered_roots(workspace):
    engine, config = workspace
    catalog = Catalog(config["source"])
    config["packages"] = ["skill.propose", "skill.investigate"]
    _, first, _ = resolve(catalog, config, engine.scope, None)
    config["packages"].reverse()
    _, second, _ = resolve(catalog, config, engine.scope, None)
    assert canonical(first) == canonical(second)

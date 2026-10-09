import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from dasync.catalog import pin
from dasync.errors import DasyncError
from dasync.sources import repository as source_repository
from test_catalog import repository

ROOT = Path(__file__).resolve().parents[1]


def invoke(workspace, *arguments):
    engine, _ = workspace
    env = {**os.environ, "DASYNC_HOME": str(engine.env.home)}
    process = subprocess.run(
        [sys.executable, "-m", "dasync.cli", *arguments, "--json", "--no-input"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert "Traceback" not in process.stderr
    return process.returncode, json.loads(process.stdout)


def setup_args(workspace):
    engine, config = workspace
    return [
        "--scope",
        "project",
        "--path",
        str(engine.scope.root),
        "--source",
        config["source"]["location"],
        "--source-kind",
        "local",
        "--enable",
        "skill.propose",
        "--trust-source",
        "--yes",
    ]


def test_real_cli_plan_apply_doctor(workspace, tmp_path):
    engine, _ = workspace
    code, envelope = invoke(workspace, "plan", "setup", *setup_args(workspace))
    assert code == 0
    file = tmp_path / "plan.json"
    file.write_text(json.dumps(envelope))
    assert not engine.scope.config.exists()
    common = ["--scope", "project", "--path", str(engine.scope.root)]
    code, result = invoke(workspace, "apply", "--plan", str(file), *common, "--yes", "--dry-run")
    assert code == 0
    assert not engine.scope.config.exists()
    code, result = invoke(workspace, "apply", "--plan", str(file), *common, "--yes")
    assert code == 0, result
    assert result["result"]["changed"]
    code, result = invoke(workspace, "doctor", *common)
    assert code == 0, result
    assert result["result"]["healthy"]
    code, result = invoke(workspace, "sync", *common, "--yes")
    assert code == 0
    assert not result["result"]["changed"]


@pytest.mark.parametrize(
    "args,expected",
    [
        (["setup"], "SCOPE_REQUIRED"),
        (["status", "--scope", "project"], "PATH_REQUIRED"),
        (["schema", "missing"], "USAGE"),
        (["sync", "--enable", "skill.propose"], "USAGE"),
        (["setup", "--recover"], "USAGE"),
        (["configure", "--before"], "USAGE"),
    ],
)
def test_json_errors(workspace, args, expected):
    code, result = invoke(workspace, *args)
    assert code == 2
    assert result["error"]["code"] == expected


def test_yes_does_not_bypass_trust(workspace):
    args = setup_args(workspace)
    args.remove("--trust-source")
    code, result = invoke(workspace, "setup", *args)
    assert code == 2
    assert result["error"]["code"] == "TRUST_REQUIRED"


def test_list_source_defaults_to_git(workspace):
    code, result = invoke(workspace, "list", "--source", str(ROOT))
    assert code == 0, result
    assert any(package["id"] == "skill.propose" for package in result["result"]["packages"])


def test_relocate_git_source_preserves_selection_and_requires_trust(workspace, tmp_path):
    engine, _ = workspace
    source, _ = repository(tmp_path)
    old_source = str(source)
    common = ["--scope", "project", "--path", str(engine.scope.root)]
    setup = ["--source", old_source, "--enable", "skill.propose", "--trust-source", "--yes"]
    code, result = invoke(workspace, "plan", "setup", *common, *setup)
    assert code == 0, result
    setup_plan = tmp_path / "setup.json"
    setup_plan.write_text(json.dumps(result))
    code, result = invoke(workspace, "apply", *common, "--plan", str(setup_plan), "--yes")
    assert code == 0, result

    original = json.loads(engine.scope.config.read_text())
    assert original["source"] == pin(old_source, "git")
    relocated = tmp_path / "relocated-catalog"
    source.rename(relocated)
    assert not source.exists()

    code, result = invoke(workspace, "plan", "update", *common, "--source", str(relocated), "--yes")
    assert code == 2
    assert result["error"]["code"] == "TRUST_REQUIRED"

    code, result = invoke(workspace, "plan", "update", *common, "--source", str(relocated), "--trust-source")
    assert code == 0, result
    expected = {**original, "source": {**original["source"], "location": str(relocated)}}
    assert result["result"]["request"]["config"] == expected
    update_plan = tmp_path / "update.json"
    update_plan.write_text(json.dumps(result))

    code, result = invoke(workspace, "apply", *common, "--plan", str(update_plan), "--yes")
    assert code == 0, result
    assert json.loads(engine.scope.config.read_text()) == expected
    code, result = invoke(workspace, "doctor", *common)
    assert code == 0, result
    assert result["result"]["healthy"]

    untrusted = {"operation": "update", "config": {**expected, "source": original["source"]}}
    with pytest.raises(DasyncError, match="Source relocation requires explicit trust"):
        engine.build(untrusted)


@pytest.mark.parametrize("trust", [True, False])
def test_engine_update_cannot_change_source_kind(workspace, trust):
    engine, config = workspace
    plan, _ = engine.build({"operation": "setup", "config": config, "trust_source": True})
    engine.apply(plan)
    original = engine.scope.config.read_bytes()
    changed = {**config, "source": pin(str(ROOT), "git")}
    with pytest.raises(DasyncError) as caught:
        engine.build({"operation": "update", "config": changed, "trust_source": trust})
    assert caught.value.code == "SOURCE_INVALID"
    assert engine.scope.config.read_bytes() == original


def test_local_source_relocation_rejects_remote_before_fetch(workspace, monkeypatch):
    from dasync import cli

    engine, config = workspace
    plan, _ = engine.build({"operation": "setup", "config": config, "trust_source": True})
    engine.apply(plan)
    original = engine.scope.config.read_bytes()
    monkeypatch.setenv("DASYNC_HOME", str(engine.env.home))
    calls = []
    monkeypatch.setattr(cli, "fetch", lambda *args: calls.append(args))
    args = cli.parser().parse_args(
        [
            "update",
            "--scope",
            "project",
            "--path",
            str(engine.scope.root),
            "--source",
            "https://example.invalid/catalog.git",
            "--trust-source",
            "--yes",
            "--no-input",
            "--json",
        ]
    )
    with pytest.raises(DasyncError) as caught:
        cli.run(args)
    assert caught.value.code == "SOURCE_INVALID"
    assert not calls
    assert engine.scope.config.read_bytes() == original


@pytest.mark.parametrize(
    "revision,expected", [(None, "CONFIRMATION_REQUIRED"), ("main", "SOURCE_INVALID"), ("", "SOURCE_INVALID")]
)
def test_remote_relocation_checks_confirmation_and_revision_before_fetch(
    workspace, monkeypatch, revision, expected
):
    from dasync import cli

    engine, config = workspace
    config["source"] = pin(str(ROOT), "git")
    plan, _ = engine.build({"operation": "setup", "config": config, "trust_source": True})
    engine.apply(plan)
    original = engine.scope.config.read_bytes()
    monkeypatch.setenv("DASYNC_HOME", str(engine.env.home))
    calls = []
    monkeypatch.setattr(cli, "fetch", lambda *args: calls.append(args))
    arguments = [
        "update",
        "--scope",
        "project",
        "--path",
        str(engine.scope.root),
        "--source",
        "https://example.invalid/catalog.git",
        "--trust-source",
        "--no-input",
        "--json",
    ]
    if revision is not None:
        arguments.extend(["--revision", revision, "--yes"])
    with pytest.raises(DasyncError) as caught:
        cli.run(cli.parser().parse_args(arguments))
    assert caught.value.code == expected
    assert not calls
    assert engine.scope.config.read_bytes() == original


@pytest.mark.parametrize("approval", [False, "false", 1])
def test_engine_relocation_requires_boolean_approval(workspace, tmp_path, approval):
    engine, config = workspace
    plan, _ = engine.build({"operation": "setup", "config": config, "trust_source": True})
    engine.apply(plan)
    changed = {**config, "source": {**config["source"], "location": str(tmp_path / "untrusted-catalog")}}
    with pytest.raises(DasyncError) as caught:
        engine.build({"operation": "update", "config": changed, "trust_source": approval})
    assert caught.value.code == "TRUST_REQUIRED"


def test_local_relocation_preserves_pin_and_rejects_changed_tree(workspace, tmp_path):
    engine, config = workspace
    source = tmp_path / "catalog"
    source.mkdir()
    for folder in ("packages", "profiles"):
        shutil.copytree(ROOT / folder, source / folder)
    config["source"] = pin(str(source), "local")
    plan, _ = engine.build({"operation": "setup", "config": config, "trust_source": True})
    engine.apply(plan)
    original = json.loads(engine.scope.config.read_bytes())
    relocated = tmp_path / "relocated"
    source.rename(relocated)
    common = ["--scope", "project", "--path", str(engine.scope.root)]
    args = ["plan", "update", *common, "--source", str(relocated), "--trust-source"]
    code, result = invoke(workspace, *args)
    assert code == 0, result
    expected = {**original, "source": {**original["source"], "location": str(relocated)}}
    assert result["result"]["request"]["config"] == expected
    plan_file = tmp_path / "relocate.json"
    plan_file.write_text(json.dumps(result))
    policy = relocated / "packages/policies/scope/POLICY.md"
    before = policy.read_bytes()
    policy.write_bytes(before + b"\nChanged catalog content.\n")
    code, rejected = invoke(workspace, *args)
    assert code == 2
    assert rejected["error"]["code"] == "SOURCE_INTEGRITY"
    assert json.loads(engine.scope.config.read_bytes()) == original
    policy.write_bytes(before)
    code, result = invoke(workspace, "apply", *common, "--plan", str(plan_file), "--yes")
    assert code == 0, result
    assert json.loads(engine.scope.config.read_bytes()) == expected
    code, result = invoke(workspace, "doctor", *common)
    assert code == 0 and result["result"]["healthy"]


@pytest.mark.parametrize("cached", [False, True])
def test_remote_relocation_previews_never_fetch(workspace, tmp_path, monkeypatch, cached):
    from dasync import cli

    engine, config = workspace
    source, _ = repository(tmp_path)
    config["source"] = pin(str(source), "git")
    plan, _ = engine.build({"operation": "setup", "config": config, "trust_source": True})
    engine.apply(plan)
    original = engine.scope.config.read_bytes()
    remote = "https://example.invalid/catalog.git"
    cache = source_repository(remote, engine.env.cache)
    if cached:
        cache.parent.mkdir(parents=True)
        subprocess.run(["git", "clone", "--quiet", "--mirror", str(source), str(cache)], check=True)
        subprocess.run(["git", "-C", str(cache), "remote", "set-url", "origin", remote], check=True)
    monkeypatch.setenv("DASYNC_HOME", str(engine.env.home))
    calls = []
    monkeypatch.setattr(cli, "fetch", lambda *args: calls.append(args))
    common = [
        "--scope",
        "project",
        "--path",
        str(engine.scope.root),
        "--source",
        remote,
        "--trust-source",
        "--no-input",
        "--json",
    ]
    for operation in (["plan", "update"], ["update", "--dry-run"]):
        args = cli.parser().parse_args([*operation, *common])
        if cached:
            result = cli.run(args)
            assert result["request"]["config"] == {
                **config,
                "source": {**config["source"], "location": remote},
            }
        else:
            with pytest.raises(DasyncError) as caught:
                cli.run(args)
            assert caught.value.code == "SOURCE_UNAVAILABLE"
            assert not cache.exists()
        assert not calls
        assert engine.scope.config.read_bytes() == original


def test_remote_setup_rejects_invalid_revision_before_fetch(workspace, monkeypatch):
    from dasync import cli

    engine, _ = workspace
    monkeypatch.setenv("DASYNC_HOME", str(engine.env.home))
    calls = []
    monkeypatch.setattr(cli, "fetch", lambda *args: calls.append(args))
    args = cli.parser().parse_args(
        [
            "setup",
            "--scope",
            "project",
            "--path",
            str(engine.scope.root),
            "--source",
            "https://example.invalid/catalog.git",
            "--revision",
            "main",
            "--trust-source",
            "--yes",
            "--no-input",
            "--json",
        ]
    )
    with pytest.raises(DasyncError) as caught:
        cli.run(args)
    assert caught.value.code == "SOURCE_INVALID"
    assert not calls
    assert not engine.scope.config.exists()


def test_invalid_remote_urls_are_rejected_before_interactive_confirmation(workspace, monkeypatch, capsys):
    from dasync import cli

    engine, config = workspace
    monkeypatch.setenv("DASYNC_HOME", str(engine.env.home))
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _: "n")
    calls = []
    monkeypatch.setattr(cli, "fetch", lambda *args: calls.append(args))
    marker = "synthetic-secret-marker"
    sources = [
        f"https://user:{marker}@example.invalid/catalog.git",
        f"https://example.invalid/catalog.git?token={marker}",
        f"https://example.invalid/catalog.git#{marker}",
    ]
    common = ["--scope", "project", "--path", str(engine.scope.root), "--trust-source"]
    for operation in ("setup", "update"):
        if operation == "update":
            config["source"] = pin(str(ROOT), "git")
            plan, _ = engine.build({"operation": "setup", "config": config, "trust_source": True})
            engine.apply(plan)
        original = engine.scope.config.read_bytes() if engine.scope.config.exists() else None
        for source in sources:
            assert cli.main([operation, *common, "--source", source]) == 2
            output = capsys.readouterr()
            assert "SOURCE_INVALID" in output.err
            assert marker not in output.out + output.err
            assert not calls
            current = engine.scope.config.read_bytes() if engine.scope.config.exists() else None
            assert current == original

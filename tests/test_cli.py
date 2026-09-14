import json
import os
import subprocess
import sys

import pytest


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

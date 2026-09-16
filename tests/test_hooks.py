import json
import subprocess

import pytest
from dasync.catalog import Catalog
from dasync.errors import DasyncError


def test_hook_requires_exact_digest(workspace):
    engine, config = workspace
    config["packages"] = ["hook.credential-path-guard"]
    config["approved_executables"] = ["0" * 64]
    with pytest.raises(DasyncError, match="exact executable"):
        engine.build({"operation": "setup", "config": config, "trust_source": True})
    assert not engine.scope.config.exists()


@pytest.mark.parametrize("provider", ["codex", "claude", "copilot", "cursor"])
def test_generated_hook_executes_with_provider_payload(workspace, provider):
    engine, config = workspace
    config["providers"] = [provider]
    config["packages"] = ["hook.credential-path-guard"]
    package = Catalog(config["source"]).packages["hook.credential-path-guard"]
    config["approved_executables"] = [package.digest]
    plan, _ = engine.build({"operation": "setup", "config": config, "trust_source": True})
    engine.apply(plan)
    filename = {
        "claude": ".claude/settings.json",
        "copilot": ".github/hooks/dasync-hooks.json",
    }.get(provider, f".{provider}/hooks.json")
    native = json.loads((engine.scope.root / filename).read_text())
    if provider == "copilot":
        assert native["version"] == 1
        entry = native["hooks"]["preToolUse"][0]
        command = [entry["exec"], *entry["args"]]
    elif provider == "cursor":
        command = native["hooks"]["preToolUse"][0]["command"]
    else:
        command = native["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    # Execute exactly the generated command, including quoting and interpreter isolation.
    for tool_input, blocked in [
        ({"file_path": "src/app.py"}, False),
        ({"file_path": "/project/.env.local"}, True),
        ({"command": "cat ~/.aws/credentials"}, True),
        ({"command": "cat ~/.ssh/id_ed25519"}, True),
    ]:
        payload = (
            {"toolName": "bash", "toolArgs": json.dumps(tool_input)}
            if provider == "copilot"
            else {"tool_input": tool_input}
        )
        result = subprocess.run(
            command,
            shell=provider != "copilot",
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            cwd=engine.scope.root,
            timeout=10,
        )
        assert result.returncode == (0 if provider == "copilot" or not blocked else 2)
        if provider == "copilot" and blocked:
            assert json.loads(result.stdout)["permissionDecision"] == "deny"
        assert ".env.local" not in result.stdout + result.stderr
    malformed = subprocess.run(
        command,
        shell=provider != "copilot",
        input=json.dumps(["malformed"]),
        text=True,
        capture_output=True,
        cwd=engine.scope.root,
        timeout=10,
    )
    assert malformed.returncode == 2

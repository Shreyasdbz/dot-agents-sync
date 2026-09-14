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


@pytest.mark.parametrize("provider", ["codex", "claude", "cursor"])
def test_generated_hook_executes_with_provider_payload(workspace, provider):
    engine, config = workspace
    config["providers"] = [provider]
    config["packages"] = ["hook.credential-path-guard"]
    package = Catalog(config["source"]).packages["hook.credential-path-guard"]
    config["approved_executables"] = [package.digest]
    plan, _ = engine.build({"operation": "setup", "config": config, "trust_source": True})
    engine.apply(plan)
    filename = ".claude/settings.json" if provider == "claude" else f".{provider}/hooks.json"
    native = json.loads((engine.scope.root / filename).read_text())
    if provider == "cursor":
        command = native["hooks"]["preToolUse"][0]["command"]
    else:
        command = native["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    # Execute exactly the generated command, including quoting and interpreter isolation.
    for payload, expected in [
        ({"tool_input": {"file_path": "src/app.py"}}, 0),
        ({"tool_input": {"file_path": "/project/.env.local"}}, 2),
        ({"tool_input": {"command": "cat ~/.aws/credentials"}}, 2),
        ({"command": "cat ~/.ssh/id_ed25519"}, 2),
        (["malformed"], 2),
    ]:
        result = subprocess.run(
            command,
            shell=True,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            cwd=engine.scope.root,
            timeout=10,
        )
        assert result.returncode == expected
        assert ".env.local" not in result.stdout + result.stderr

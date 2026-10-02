"""Exercise quiz distribution through the real temporary Engine boundary."""

import pytest
from dasync.catalog import Catalog


@pytest.mark.parametrize(
    ("provider", "skill_root"),
    [
        ("codex", ".agents/skills"),
        ("claude", ".claude/skills"),
        ("copilot", ".github/skills"),
        ("cursor", ".cursor/skills"),
    ],
)
def test_change_quiz_installs_complete_offline_template(workspace, provider, skill_root):
    engine, config = workspace
    config["packages"] = ["skill.change-quiz"]
    config["providers"] = [provider]
    plan, _ = engine.build({"operation": "setup", "config": config, "trust_source": True})
    engine.apply(plan)
    root = engine.scope.root / skill_root / "dasync-skill-change-quiz"
    catalog = Catalog(config["source"])
    for package_id in ("template.change-quiz", "skill.visual-artifacts"):
        for name, content in catalog.packages[package_id].files.items():
            assert (root / "references" / package_id / name).read_bytes() == content
    for name in ("analysis.md", "questions.md", "research.md"):
        assert (root / name).read_bytes() == catalog.packages["skill.change-quiz"].files[name]
    repeated, _ = engine.build({"operation": "sync"})
    assert all(operation["action"] == "keep" for operation in repeated["operations"])

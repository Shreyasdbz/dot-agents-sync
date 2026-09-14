import importlib.util
import re
from pathlib import Path

from dasync.adapters import render
from dasync.catalog import Catalog
from dasync.resolver import resolve

ROOT = Path(__file__).resolve().parents[1]


def test_generated_templates_match_canonical_source():
    spec = importlib.util.spec_from_file_location("build_templates", ROOT / "scripts/build_templates.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for path, expected in module.render_all().items():
        assert path.read_text() == expected
        assert "{{" not in expected
        limit = 60000 if path.name == "trip.html" else 40000
        assert len(expected.encode()) < limit


def test_template_markdown_links_and_manifests(workspace):
    catalog = Catalog(workspace[1]["source"])
    for package in catalog.packages.values():
        if package.manifest["kind"] != "Template":
            continue
        for name, body in package.files.items():
            if not name.endswith(".md"):
                continue
            for link in re.findall(r"\]\(([^)]+)\)", body.decode()):
                if "://" in link or link.startswith("#"):
                    continue
                relative = (Path(name).parent / link).as_posix()
                assert relative in package.files, (package.id, name, relative)


def test_template_modules_reach_all_provider_skill_references(workspace):
    engine, config = workspace
    config["packages"] = ["skill.propose", "skill.trip-publish"]
    catalog = Catalog(config["source"])
    selected, graph, bindings = resolve(catalog, config, engine.scope, None)
    artifacts, _ = render(selected, graph, bindings, config, engine.scope)
    for provider in config["providers"]:
        paths = [a.relative for a in artifacts if a.provider == provider]
        assert any(path.endswith("template.design-proposal/sections/bug-fix.md") for path in paths)
        assert any(path.endswith("template.trip-publish/components.md") for path in paths)

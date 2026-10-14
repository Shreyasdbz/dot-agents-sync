"""Reproducible authoring projection of the collected catalog into owned recipes.

No provider writes, registration, network access or private binding lookup occurs here.
The legacy packages and template system remain the single editable content sources.
"""

import re
import uuid
from pathlib import Path

from .adapters import strip_frontmatter
from .contracts import validate
from .errors import DasyncError
from .io import canonical, digest, parse, read, safe_path
from .recipe_adapters import render_references

GROUPS = ("starter", "engineering", "design", "travel", "music", "context-contracts", "hooks")
SOURCE_IDS = {
    group: str(
        uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/Shreyasdbz/dot-agents-sync/recipes/" + group)
    )
    for group in GROUPS
}
STARTER_ROOTS = ("skill.propose", "skill.plan-out", "skill.do-it", "skill.investigate")


def compile_collection(root: Path):
    """Return recipe-relative bytes and a complete item/file provenance audit."""
    packages = {}
    for manifest in sorted((root / "packages").rglob("manifest.yaml")):
        spec = parse(read(manifest))
        validate("manifest", spec)
        if spec["id"] in packages:
            raise DasyncError("CATALOG_INVALID", "Duplicate collected item")
        packages[spec["id"]] = (manifest, spec)
    closure, visiting = set(), set()

    def visit(local_id):
        if local_id in visiting:
            raise DasyncError("DEPENDENCY_CYCLE", "Collected starter has a dependency cycle")
        if local_id in closure:
            return
        visiting.add(local_id)
        for dependency in packages[local_id][1].get("requires", {}):
            visit(dependency)
        visiting.remove(local_id)
        closure.add(local_id)

    for local_id in STARTER_ROOTS:
        visit(local_id)
    owners = {}
    for local_id, (_, spec) in packages.items():
        if local_id in closure:
            group = "starter"
        elif spec.get("context", {}).get("sensitivity") == "private":
            group = "context-contracts"
        elif spec["kind"] == "Hook":
            group = "hooks"
        elif local_id in (
            "skill.ui-design",
            "skill.pitch-deck",
            "template.pitch-deck",
            "policy.ui-shadcn",
            "context.design-editorial",
        ):
            group = "design"
        elif local_id in ("skill.curate-am-playlist", "template.playlist"):
            group = "music"
        elif local_id in (
            "agent.travel-planner",
            "agent.travel-researcher",
            "skill.trip-plan",
            "skill.trip-publish",
            "template.trip-plan",
            "template.trip-publish",
        ):
            group = "travel"
        else:
            group = "engineering"
        owners[local_id] = group

    def reference(consumer, dependency):
        if dependency not in owners:
            raise DasyncError("ITEM_UNKNOWN", "Collected dependency or consumer is missing")
        return dependency if owners[consumer] == owners[dependency] else owners[dependency] + "/" + dependency

    outputs, audit, manifests, imports, features = {}, [], {}, {}, {}
    for group in GROUPS:
        manifests[group], imports[group], features[group] = [], {}, set()
        outputs[group + "/LICENSE"] = read(root / "LICENSE")
        outputs[group + "/THIRD_PARTY_NOTICES.md"] = read(root / "THIRD_PARTY_NOTICES.md")
    for local_id, (manifest, old) in sorted(packages.items()):
        group = owners[local_id]
        requires = {}
        for dependency, constraint in old.get("requires", {}).items():
            ref = reference(local_id, dependency)
            requires[ref] = constraint
            if "/" in ref:
                owner = owners[dependency]
                imports[group][owner] = {"source_id": SOURCE_IDS[owner]}
                features[group].add("imports")
        spec = {
            "format": 1,
            "kind": old["kind"],
            "id": local_id,
            "version": old["version"],
            "name": old.get("presentation", {}).get("display_name", old["name"]),
            "description": old["description"],
            "license": old["license"],
            "entry": old["entry"],
            "files": [*old["files"], "LICENSE.dasync.txt"],
            "scopes": old["scopes"],
            "requires": requires,
            "required_capabilities": old.get("capabilities", []),
            "optional_capabilities": old.get("prefers", []),
            "extensions": {
                "dasync.dev/catalog-path": str(manifest.relative_to(root)),
                "dasync.dev/catalog-manifest-digest": digest(read(manifest)),
            },
        }
        if old.get("fallback"):
            spec["extensions"]["dasync.dev/optional-fallback"] = old["fallback"]
        spec["extensions"]["dasync.dev/token-budget"] = old["token_budget"]
        if old.get("outputs"):
            spec["extensions"]["dasync.dev/outputs"] = ",".join(old["outputs"])
        if old.get("suggests"):
            spec["extensions"]["dasync.dev/suggestions"] = ",".join(
                SOURCE_IDS[owners[dependency]] + "/" + dependency for dependency in old["suggests"]
            )
        if old["kind"] == "Skill":
            spec["short_description"] = old["presentation"]["short_description"]
            prompt = old["presentation"]["default_prompt"]
            spec["default_prompt"] = re.sub(r"^Use \$dasync-[a-z0-9-]+ to ", "", prompt)
            if "$dasync-" in spec["default_prompt"]:
                raise DasyncError("REFERENCE_INVALID", "Default prompt retains a legacy native name")
        if old["kind"] == "Policy":
            spec["policy"] = old["policy"]
            features[group].add("native-policies")
        if old["kind"] == "Agent":
            spec["agent"] = {"access": "inherit"}
            features[group].add("native-agents")
        if old["kind"] == "Hook":
            spec["executable"] = {"runtime": "python", **old["executable"]}
            features[group].add("python-hooks")
        if old["kind"] == "Context":
            context = old["context"]
            spec["context"] = {
                "sensitivity": context["sensitivity"],
                "access": context["access"],
                "contract_id": str(uuid.uuid5(uuid.UUID(SOURCE_IDS[group]), local_id)),
                "contract_version": old["version"],
                "content_format": "markdown",
                "consumers": [
                    {"source_id": SOURCE_IDS[owners[consumer]], "item_id": consumer}
                    for consumer in context["consumers"]
                ],
            }
            if "binding" in context:
                spec["context"]["binding"] = context["binding"]
            features[group].add("context-contracts")
        validate("item-spec", spec)
        folder = group + "/items/" + local_id
        manifests[group].append("items/" + local_id + "/item.yaml")
        outputs[folder + "/item.yaml"] = canonical(spec)
        files = []
        for filename in old["files"]:
            original = read(safe_path(manifest.parent, filename))
            data = original
            if filename.endswith((".md", ".markdown")):
                text = strip_frontmatter(data) if filename == old["entry"] else data.decode("utf-8")

                def translate(destination):
                    target, separator, resource = destination.removeprefix("references/").partition("/")
                    if target not in packages:
                        return destination
                    if (
                        target not in old.get("requires", {})
                        or not separator
                        or resource.split("#")[0] not in packages[target][1]["files"]
                    ):
                        raise DasyncError(
                            "REFERENCE_INVALID", "Collected link needs a declared dependency file"
                        )
                    return "dasync:dependency/" + reference(local_id, target) + "/" + resource

                text = render_references(text, translate, scheme="references/")
                data = text.encode()
            outputs[folder + "/" + filename] = data
            files.append(
                {
                    "path": filename,
                    "original": digest(original),
                    "canonical": digest(data),
                    "transformed": data != original,
                }
            )
        outputs[folder + "/LICENSE.dasync.txt"] = read(root / "LICENSE")
        audit.append(
            {
                "id": local_id,
                "kind": old["kind"],
                "recipe": group,
                "source_id": SOURCE_IDS[group],
                "original_manifest": str(manifest.relative_to(root)),
                "files": files,
            }
        )
    for group in GROUPS:
        metadata = {
            "format": 1,
            "source_id": SOURCE_IDS[group],
            "name": group,
            "description": "Collected dasync " + group + " workflows and references.",
            "requires_engine": ">=0.1.1,<1",
            "required_features": sorted(features[group]),
            "items": manifests[group],
            "imports": imports[group],
        }
        validate("recipe", metadata)
        outputs[group + "/recipe.yaml"] = canonical(metadata)
    report = {
        "format": 1,
        "starter_roots": list(STARTER_ROOTS),
        "starter_items": sorted(closure),
        "items": audit,
    }
    outputs["collection-audit.json"] = canonical(report)
    return outputs, report

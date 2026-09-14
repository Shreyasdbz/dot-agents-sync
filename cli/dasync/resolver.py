"""Deterministic graph resolution, provenance and context authorization."""

from pathlib import Path

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from .catalog import Catalog
from .config import Scope
from .errors import DasyncError


def resolve(catalog: Catalog, config: dict, scope: Scope, user: dict | None):
    roots = catalog.roots(config)
    inherited = set()
    if scope.kind == "project" and ("bindings" in config or "projects" in config):
        raise DasyncError("PRIVATE_CONTEXT", "Private bindings belong in the user configuration")
    if scope.kind == "project" and config["inherit_user"] and user:
        if user["source"] != config["source"]:
            raise DasyncError(
                "INHERITANCE_CONFLICT",
                "Inherited scopes must share the same catalog pin in v1; align pins or disable inheritance",
            )
        for pid, reason in catalog.roots(user).items():
            p = catalog.packages.get(pid)
            if not p:
                raise DasyncError("INHERITANCE_CONFLICT", f"Inherited package absent from project pin: {pid}")
            if p.manifest["kind"] == "Hook":
                continue
            if (
                p.manifest["kind"] == "Context"
                and p.manifest.get("context", {}).get("access", "explicit") != "inherit"
            ):
                continue
            if pid not in roots:
                roots[pid] = "inherited:" + reason
                inherited.add(pid)
    disabled = set(config["disabled"])
    roots = {p: reason for p, reason in roots.items() if p not in disabled}
    selected, visiting, provenance, edges, contexts = {}, set(), {}, [], {}
    local = (user or {}).get("projects", {}).get(config["project"], {})
    allowed_contexts = set(config.get("contexts", [])) | set(local.get("bindings", []))
    bindings = (config if scope.kind == "user" else user or {}).get("bindings", {})

    def visit(pid, reason, consumer=None):
        if pid in disabled:
            raise DasyncError("DEPENDENCY_DISABLED", f"Required package is disabled: {pid}")
        if pid not in catalog.packages:
            raise DasyncError("PACKAGE_UNKNOWN", f"Unknown package: {pid}")
        package = catalog.packages[pid]
        m = package.manifest
        executable_files = [
            name
            for name in package.files
            if name.endswith((".py", ".sh", ".ps1", ".bat", ".cmd", ".exe")) or name.startswith("scripts/")
        ]
        if executable_files and (
            not m.get("executable") or package.digest not in config.get("approved_executables", [])
        ):
            raise DasyncError(
                "EXECUTABLE_TRUST_REQUIRED", f"Review and approve the exact executable package digest: {pid}"
            )
        if scope.kind not in m["scopes"]:
            raise DasyncError("SCOPE_FORBIDDEN", f"Package is not allowed in {scope.kind} scope: {pid}")
        if m["kind"] == "Context":
            policy = m.get("context", {})
            if consumer and policy.get("consumers") and consumer not in policy["consumers"]:
                raise DasyncError("PRIVATE_CONTEXT", f"Context consumer is not authorized: {pid}")
            if scope.kind == "project":
                access = policy.get("access", "explicit")
                if access == "never" or (access == "explicit" and pid not in allowed_contexts):
                    raise DasyncError(
                        "PRIVATE_CONTEXT", f"Project access is not authorized for context: {pid}"
                    )
            if policy.get("sensitivity") == "private":
                binding = bindings.get(policy.get("binding", pid))
                if not binding:
                    raise DasyncError("CONTEXT_MISSING", f"Private context binding is missing: {pid}")
                private_path = Path(binding["path"])
                if not private_path.is_absolute() or not private_path.is_file():
                    raise DasyncError("CONTEXT_MISSING", f"Private context source is unavailable: {pid}")
                if scope.kind == "project" and config["project"] not in binding["projects"]:
                    raise DasyncError(
                        "PRIVATE_CONTEXT", f"User has not granted this project context access: {pid}"
                    )
                if set(config["providers"]) - set(binding["providers"]):
                    raise DasyncError(
                        "PRIVATE_CONTEXT", f"Provider access is not authorized for context: {pid}"
                    )
                contexts[pid] = binding
        provenance.setdefault(pid, [])
        if reason not in provenance[pid]:
            provenance[pid].append(reason)
        if pid in visiting:
            raise DasyncError("DEPENDENCY_CYCLE", f"Dependency cycle includes: {pid}")
        if pid in selected:
            return
        visiting.add(pid)
        for dependency, constraint in sorted(m.get("requires", {}).items()):
            dep = catalog.packages.get(dependency)
            if dep and Version(dep.manifest["version"]) not in SpecifierSet(constraint):
                raise DasyncError(
                    "VERSION_CONFLICT", f"Dependency version does not satisfy {pid}: {dependency}"
                )
            edges.append([pid, dependency])
            visit(dependency, "dependency:" + pid, pid)
        visiting.remove(pid)
        selected[pid] = package

    for pid, reason in sorted(roots.items()):
        visit(pid, reason)
    groups = {}
    for pid, package in selected.items():
        m = package.manifest
        if set(m.get("conflicts", [])) & selected.keys():
            raise DasyncError("PACKAGE_CONFLICT", f"Conflicting selection: {pid}")
        group = m.get("policy", {}).get("conflict_group")
        if group:
            if group in groups:
                raise DasyncError("POLICY_CONFLICT", f"Policies conflict in group: {group}")
            groups[group] = pid
    graph = {
        "packages": [
            {
                "id": pid,
                "version": p.manifest["version"],
                "digest": p.digest,
                "provenance": sorted(provenance[pid]),
            }
            for pid, p in selected.items()
        ],
        "edges": sorted(edges),
        "inherited": sorted(inherited & selected.keys()),
    }
    return selected, graph, contexts

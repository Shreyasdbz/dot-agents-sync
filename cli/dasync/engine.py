"""All mutation commands compile into the same deterministic plan."""

import base64
import copy
import os
import platform
from pathlib import Path

from . import __version__
from .adapters import ADAPTER_VERSION, provider_roots, render
from .catalog import Catalog
from .config import Environment, Scope, encode_config, load_config
from .contracts import validate
from .errors import DasyncError
from .io import canonical, digest, observe, parse_jsonc, read, read_leaf_target
from .resolver import resolve
from .state import State


class Engine:
    def __init__(self, env: Environment, scope: Scope):
        self.env, self.scope, self.state = env, scope, State(env.state)

    def build(self, request: dict):
        scope = self.scope
        operation = request["operation"]
        if operation not in ("setup", "configure", "sync", "update", "repair", "rollback"):
            raise DasyncError("PLAN_INVALID", "Unsupported operation")
        existing = load_config(scope.config, required=operation not in ("setup", "rollback"))
        user = load_config(self.env.config, required=False) if scope.kind == "project" else existing
        if operation == "setup" and existing:
            raise DasyncError("ALREADY_CONFIGURED", "Scope is already configured")
        current = self.state.head(scope.key)
        old_owned = current["owned"] if current else {}
        desired = copy.deepcopy(request.get("config", existing))
        graph, decisions, outputs, owners, sources = {}, [], {}, {}, {}
        replacement_paths = set()
        replacement_blockers = set()
        restoration_after = {}
        retain_outputs = False
        if operation == "rollback":
            receipt = self.state.receipt(request["receipt"], scope.key)
            outputs = {p: base64.b64decode(b) for p, b in receipt["files"].items()}
            owners = receipt["owned"]
            graph, decisions = receipt["graph"], receipt["decisions"]
            if request.get("before_receipt"):
                previous = self.state.receipt(receipt["previous"], scope.key) if receipt["previous"] else None
                outputs = {p: base64.b64decode(b) for p, b in (previous or {}).get("files", {}).items()}
                owners = copy.deepcopy((previous or {}).get("owned", {}))
                graph, decisions = (previous or {}).get("graph", {}), (previous or {}).get("decisions", [])
                for backup in receipt.get("backups", []):
                    path = backup["path"]
                    before = {
                        **backup["before"],
                        "type": backup["before"].get(
                            "type", "file" if backup["before"]["hash"] is not None else "missing"
                        ),
                    }
                    restoration_after[path] = {
                        **backup["after"],
                        "type": backup["after"].get(
                            "type", "file" if backup["after"]["hash"] is not None else "missing"
                        ),
                    }
                    if backup["data"] is None:
                        outputs.pop(path, None)
                        owners.pop(path, None)
                    else:
                        outputs[path] = base64.b64decode(backup["data"])
                        if path in owners:
                            expected = {
                                "hash": owners[path]["hash"],
                                "mode": owners[path]["mode"],
                                "type": owners[path].get("type", "file"),
                            }
                            if before == expected:
                                owners[path] = {
                                    **owners[path],
                                    "mode": before["mode"],
                                    "type": before["type"],
                                }
                            else:
                                owners[path] = {
                                    "mode": before["mode"],
                                    "type": before["type"],
                                    "provider": "dasync",
                                    "package": "@restored",
                                }
                        else:
                            owners[path] = {
                                "mode": before["mode"],
                                "type": before["type"],
                                "provider": "dasync",
                                "package": "@restored",
                            }
            # Receipt paths are not authority to write outside the recorded scope.
            for path in outputs:
                self._validate_target(Path(path))
        else:
            validate("config", desired)
            if operation in ("sync", "repair") and desired != existing:
                raise DasyncError("PLAN_INVALID", "Sync and repair cannot change desired state")
            if operation == "configure" and existing and desired["source"] != existing["source"]:
                raise DasyncError("SOURCE_INVALID", "Only update may advance the catalog pin")
            if operation == "setup" and not request.get("trust_source"):
                raise DasyncError("TRUST_REQUIRED", "Review the source and pass --trust-source explicitly")
            if scope.kind == "user" and "copilot" in desired["providers"]:
                copilot_home = os.environ.get("COPILOT_HOME")
                expected = scope.root / ".copilot"
                if copilot_home and Path(copilot_home).expanduser().absolute() != expected:
                    raise DasyncError(
                        "SCOPE_INVALID",
                        "COPILOT_HOME points outside the managed user provider root",
                        "Unset COPILOT_HOME; custom Copilot provider roots are not supported",
                    )
            if request.get("replace_provider_config"):
                if operation != "setup" or request.get("conflict", "protect") != "overwrite":
                    raise DasyncError(
                        "PLAN_INVALID",
                        "Provider configuration replacement requires setup with conflict overwrite",
                    )
                if request.get("config_only"):
                    raise DasyncError(
                        "PLAN_INVALID", "Provider configuration replacement cannot be config-only"
                    )
                replacement_paths, replacement_blockers = self._replacement_entries(desired["providers"])
            catalog = Catalog(desired["source"], self.env.cache)
            sources[desired["source"]["location"]] = catalog.digest
            selected, graph, bindings = resolve(catalog, desired, scope, user)
            artifacts, decisions = render(selected, graph, bindings, desired, scope)
            config_only = request.get("config_only", operation == "configure")
            if config_only:
                retain_outputs = True
            else:
                for artifact in artifacts:
                    path = str(scope.root.joinpath(*artifact.relative.split("/")))
                    self._validate_target(Path(path), replacement_blockers)
                    outputs[path] = artifact.content
                    owners[path] = {
                        "provider": artifact.provider,
                        "package": artifact.package,
                        "mode": artifact.mode,
                        "type": "file",
                    }
                self._preserve_settings(
                    desired["providers"],
                    outputs,
                    owners,
                    replacement_paths,
                    replacing=bool(request.get("replace_provider_config")),
                )
            config_data = encode_config(desired) if desired != existing else read(scope.config)
            outputs[str(scope.config)] = config_data
            owners[str(scope.config)] = {
                "provider": "dasync",
                "package": "@config",
                "mode": 0o600 if scope.kind == "user" else 0o644,
                "type": "file",
            }
        operations = []
        prior_paths = {p for p, o in old_owned.items() if not retain_outputs or o["package"] == "@config"}
        other_owners = self.state.other_owners(scope.key)
        desired_symlinks = {
            path for path, owner in owners.items() if path in outputs and owner.get("type") == "symlink"
        }
        for path in sorted(set(outputs) | prior_paths | replacement_paths):
            self._validate_target(Path(path), replacement_blockers)
            if path in other_owners:
                raise DasyncError("OWNERSHIP_CONFLICT", "Another scope owns a planned output")
            shadowed_by = next(
                (
                    ancestor
                    for ancestor in sorted(replacement_blockers, key=len, reverse=True)
                    if path.startswith(ancestor + os.sep)
                ),
                None,
            )
            hidden_by = next(
                (
                    ancestor
                    for ancestor in sorted(desired_symlinks, key=len, reverse=True)
                    if path.startswith(ancestor + os.sep)
                ),
                None,
            )
            before = {"hash": None, "mode": None, "type": "missing"} if shadowed_by else observe(Path(path))
            has_content = path in outputs
            content = outputs.get(path)
            target_hash = digest(content) if has_content else None
            owner = owners.get(
                path,
                old_owned.get(
                    path,
                    {"provider": "dasync", "package": "@replaced", "mode": None, "type": "missing"},
                ),
            )
            mode = owner["mode"] if has_content else None
            target_type = owner.get("type", "file") if has_content else "missing"
            desired_observed = {"hash": target_hash, "mode": mode, "type": target_type}
            tracked = old_owned.get(path)
            is_config = path == str(scope.config)
            if before["type"] == "directory" and has_content:
                allowed_container_restore = (
                    target_type in {"file", "symlink"}
                    and owner["package"] == "@restored"
                    and any(owned.startswith(path + os.sep) for owned in old_owned)
                )
                if not allowed_container_restore:
                    raise DasyncError("UNSAFE_PATH", f"Managed file path is occupied by a directory: {path}")
            else:
                allowed_container_restore = False
            expected_restoration_state = owner["package"] == "@restored" and before == restoration_after.get(
                path
            )
            collision = (
                not tracked
                and before["type"] != "missing"
                and not expected_restoration_state
                and not allowed_container_restore
            )
            if collision and not is_config and request.get("conflict", "protect") != "overwrite":
                raise DasyncError("UNMANAGED_COLLISION", f"Protected output: {Path(path).name}")
            if before == desired_observed:
                action = "keep"
            else:
                drift = (
                    tracked
                    and before["type"] != "missing"
                    and before
                    != {
                        "hash": tracked["hash"],
                        "mode": tracked["mode"],
                        "type": tracked.get("type", "file"),
                    }
                )
                if (
                    not is_config
                    and (drift or collision)
                    and request.get("conflict", "protect") != "overwrite"
                ):
                    raise DasyncError(
                        "DRIFT" if drift else "UNMANAGED_COLLISION",
                        f"Protected output: {Path(path).name}",
                        "Review with status; use --conflict overwrite only after reviewing a backup plan",
                    )
                action = "delete" if content is None else "write"
            operations.append(
                {
                    "path": path,
                    "action": action,
                    "before": before,
                    "hash": target_hash,
                    "mode": mode,
                    "target_type": target_type,
                    "provider": owner["provider"],
                    "package": owner["package"],
                    **({"shadowed_by": shadowed_by} if shadowed_by else {}),
                    **({"hidden_by": hidden_by} if hidden_by else {}),
                }
            )
        plan = {
            "version": 1,
            "cli_version": __version__,
            "adapter_version": ADAPTER_VERSION,
            "platform": platform.system(),
            "scope": scope.kind,
            "root": str(scope.root),
            "scope_key": scope.key,
            "request": request,
            "previous_receipt": current["id"] if current else None,
            "retain_outputs": retain_outputs,
            "inputs": {
                "config": observe(scope.config),
                "user_config": observe(self.env.config),
                "sources": sources,
            },
            "graph": graph,
            "decisions": decisions,
            "operations": operations,
        }
        return plan, outputs

    def _preserve_settings(self, providers, outputs, owners, replacement_paths, replacing):
        if not replacing and not any(
            path.endswith("/.claude/settings.json") and path in owners for path in outputs
        ):
            return
        paths = {}
        copilot_hooks = any(
            owner["provider"] == "copilot" and owner["package"].startswith("hook.")
            for owner in owners.values()
        )
        if "claude" in providers:
            paths[self.scope.root / ".claude/settings.json"] = "claude"
            if replacing:
                paths[self.scope.root / ".claude/settings.local.json"] = "claude"
        if "copilot" in providers:
            if self.scope.kind == "user":
                paths[self.scope.root / ".copilot/settings.json"] = "copilot"
            else:
                paths[self.scope.root / ".github/copilot/settings.json"] = "copilot"
                paths[self.scope.root / ".github/copilot/settings.local.json"] = "copilot"
                paths.setdefault(self.scope.root / ".claude/settings.json", "copilot")
                paths.setdefault(self.scope.root / ".claude/settings.local.json", "copilot")
        for settings_path, provider in paths.items():
            path = str(settings_path)
            existing_data = read_leaf_target(settings_path)
            managed_data = outputs.get(path)
            if existing_data is None:
                continue
            existing = parse_jsonc(existing_data)
            if provider == "copilot" and copilot_hooks and existing.get("disableAllHooks") is True:
                raise DasyncError(
                    "CAPABILITY_BLOCKED",
                    "Copilot disableAllHooks would disable the selected managed hook",
                    "Review and disable that setting before applying the hook package",
                )
            managed = parse_jsonc(managed_data) if managed_data is not None else {}
            had_hooks = bool(existing.get("hooks"))
            merged = {key: value for key, value in existing.items() if key != "hooks"}
            if managed.get("hooks"):
                merged["hooks"] = managed["hooks"]
            changed = merged != existing or managed_data is not None
            if not changed:
                replacement_paths.discard(path)
                continue
            observed = observe(settings_path)
            outputs[path] = canonical(merged)
            owners[path] = {
                "provider": provider,
                "package": "@hooks" if managed.get("hooks") else "@preserved",
                "mode": observed["mode"] if observed["type"] == "file" else 0o600,
                "type": "file",
            }
            if not had_hooks and not managed.get("hooks"):
                replacement_paths.discard(path)

    def _replacement_entries(self, providers):
        entries = set()
        blockers = set()
        roots = []
        files = []
        for provider in providers:
            declared = provider_roots(provider, self.scope.kind)
            roots.extend(declared["directories"])
            files.extend(declared["files"])
        for relative in sorted(set(roots)):
            root = self.scope.root.joinpath(*relative.split("/"))
            self._validate_target(root, {str(root)})
            if root.is_symlink() or root.is_file():
                entries.add(str(root))
                blockers.add(str(root))
                continue
            if not root.exists():
                continue
            stack = [root]
            while stack:
                directory = stack.pop()
                with os.scandir(directory) as children:
                    for child in children:
                        path = Path(child.path)
                        if child.is_symlink() or child.is_file(follow_symlinks=False):
                            self._validate_target(path)
                            entries.add(str(path))
                        elif child.is_dir(follow_symlinks=False):
                            stack.append(path)
                        else:
                            raise DasyncError(
                                "UNSAFE_PATH", "Provider discovery roots contain a special file"
                            )
        for relative in sorted(set(files)):
            path = self.scope.root.joinpath(*relative.split("/"))
            self._validate_target(path, {str(path)})
            if path.is_symlink() or path.is_file():
                entries.add(str(path))
        return entries, blockers

    def _validate_target(self, path, replacing=()):
        if path == self.scope.config:
            return
        try:
            relative = path.relative_to(self.scope.root).as_posix()
        except ValueError as exc:
            raise DasyncError("UNSAFE_PATH", "Plan target escapes scope") from exc
        allowed = (
            ".agents/skills/",
            ".codex/agents/",
            ".codex/dasync-references/",
            ".copilot/skills/",
            ".copilot/agents/",
            ".copilot/instructions/",
            ".copilot/dasync-references/",
            ".github/skills/",
            ".github/agents/",
            ".github/instructions/",
            ".github/dasync-references/",
            ".claude/skills/",
            ".claude/agents/",
            ".claude/rules/",
            ".claude/dasync-references/",
            ".cursor/skills/",
            ".cursor/rules/",
            ".cursor/dasync-references/",
            ".codex/hooks/",
            ".copilot/hooks/",
            ".github/hooks/",
            ".claude/hooks/",
            ".cursor/hooks/",
        )
        allowed_directories = tuple(prefix.removesuffix("/") for prefix in allowed)
        if (
            relative
            not in (
                "AGENTS.md",
                "CLAUDE.md",
                ".codex/AGENTS.md",
                ".codex/hooks.json",
                ".copilot/copilot-instructions.md",
                ".copilot/settings.json",
                ".github/copilot-instructions.md",
                ".github/copilot/settings.json",
                ".github/copilot/settings.local.json",
                ".claude/settings.json",
                ".claude/settings.local.json",
                ".claude/CLAUDE.md",
                ".cursor/hooks.json",
            )
            and relative not in allowed_directories
            and not relative.startswith(allowed)
        ):
            raise DasyncError("UNSAFE_PATH", "Plan target is outside adapter-owned roots")
        replacing = set(replacing)
        for parent in path.parents:
            if parent == self.scope.root.parent:
                break
            if parent.is_symlink() and str(parent) not in replacing:
                raise DasyncError("UNSAFE_PATH", "Symbolic links are not accepted in managed path parents")
            if parent.exists() and not parent.is_dir() and str(parent) not in replacing:
                raise DasyncError("UNSAFE_PATH", "A path ancestor is not a directory")

    def apply(self, plan, fault=None):
        validate("plan", plan)
        if plan.get("scope_key") != self.scope.key or plan.get("version") != 1:
            raise DasyncError("PLAN_INVALID", "Plan scope or schema does not match")
        fresh, outputs = self.build(plan["request"])
        if canonical(fresh) != canonical(plan):
            raise DasyncError("PLAN_INVALIDATED", "Plan inputs changed; regenerate and review the plan")
        return self.state.commit(plan, outputs, lambda: self.build(plan["request"]), fault)

    def status(self):
        receipt = self.state.head(self.scope.key)
        files = []
        if receipt:
            for path, owner in receipt["owned"].items():
                observed = observe(Path(path))
                state = (
                    "missing"
                    if observed["type"] == "missing"
                    else (
                        "clean"
                        if observed
                        == {
                            "hash": owner["hash"],
                            "mode": owner["mode"],
                            "type": owner.get("type", "file"),
                        }
                        else "modified"
                    )
                )
                files.append(
                    {
                        "path": path,
                        "status": state,
                        "package": owner["package"],
                        "provider": owner["provider"],
                    }
                )
        result = {
            "scope": self.scope.kind,
            "root": str(self.scope.root),
            "configured": self.scope.config.exists(),
            "receipt": receipt["id"] if receipt else None,
            "files": files,
            "pending_recovery": [j["id"] for j in self.state.pending()],
        }
        if result["configured"]:
            try:
                plan, _ = self.build({"operation": "sync"})
                result["pending_changes"] = sum(o["action"] != "keep" for o in plan["operations"])
                result["graph"], result["decisions"] = plan["graph"], plan["decisions"]
            except DasyncError as exc:
                result["diagnostic"] = exc.as_dict()
        return result

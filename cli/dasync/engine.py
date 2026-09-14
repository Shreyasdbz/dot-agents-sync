"""All mutation commands compile into the same deterministic plan."""

import base64
import copy
import platform
from pathlib import Path

from . import __version__
from .adapters import ADAPTER_VERSION, render
from .catalog import Catalog
from .config import Environment, Scope, encode_config, load_config
from .contracts import validate
from .errors import DasyncError
from .io import canonical, digest, observe, read, safe_path
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
                    if backup["data"] is None:
                        outputs.pop(path, None)
                        owners.pop(path, None)
                    else:
                        outputs[path] = base64.b64decode(backup["data"])
                        owners.setdefault(
                            path,
                            {"mode": backup["before"]["mode"], "provider": "dasync", "package": "@restored"},
                        )
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
            catalog = Catalog(desired["source"], self.env.cache)
            sources[desired["source"]["location"]] = catalog.digest
            selected, graph, bindings = resolve(catalog, desired, scope, user)
            artifacts, decisions = render(selected, graph, bindings, desired, scope)
            config_only = request.get("config_only", operation == "configure")
            if config_only:
                retain_outputs = True
            else:
                for artifact in artifacts:
                    path = str(safe_path(scope.root, artifact.relative))
                    outputs[path] = artifact.content
                    owners[path] = {
                        "provider": artifact.provider,
                        "package": artifact.package,
                        "mode": artifact.mode,
                    }
            config_data = encode_config(desired) if desired != existing else read(scope.config)
            outputs[str(scope.config)] = config_data
            owners[str(scope.config)] = {
                "provider": "dasync",
                "package": "@config",
                "mode": 0o600 if scope.kind == "user" else 0o644,
            }
        operations = []
        prior_paths = {p for p, o in old_owned.items() if not retain_outputs or o["package"] == "@config"}
        other_owners = self.state.other_owners(scope.key)
        for path in sorted(set(outputs) | prior_paths):
            self._validate_target(Path(path))
            if path in other_owners:
                raise DasyncError("OWNERSHIP_CONFLICT", "Another scope owns a planned output")
            before = observe(Path(path))
            content = outputs.get(path)
            target_hash = digest(content) if content is not None else None
            owner = owners.get(path, old_owned.get(path))
            mode = owner["mode"] if content is not None else None
            desired_observed = {"hash": target_hash, "mode": mode}
            tracked = old_owned.get(path)
            is_config = path == str(scope.config)
            collision = not tracked and before["hash"] is not None
            if collision and not is_config and request.get("conflict", "protect") != "overwrite":
                raise DasyncError("UNMANAGED_COLLISION", f"Protected output: {Path(path).name}")
            if before == desired_observed:
                action = "keep"
            else:
                drift = (
                    tracked
                    and before["hash"] is not None
                    and before != {"hash": tracked["hash"], "mode": tracked["mode"]}
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
                    "provider": owner["provider"],
                    "package": owner["package"],
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

    def _validate_target(self, path):
        if path == self.scope.config:
            return
        try:
            relative = path.relative_to(self.scope.root).as_posix()
        except ValueError as exc:
            raise DasyncError("UNSAFE_PATH", "Plan target escapes scope") from exc
        safe_path(self.scope.root, relative)
        allowed = (
            ".agents/skills/",
            ".codex/agents/",
            ".codex/dasync-references/",
            ".claude/skills/",
            ".claude/agents/",
            ".claude/rules/",
            ".claude/dasync-references/",
            ".cursor/skills/",
            ".cursor/rules/",
            ".cursor/dasync-references/",
            ".codex/hooks/",
            ".claude/hooks/",
            ".cursor/hooks/",
        )
        if relative not in (
            "AGENTS.md",
            ".codex/AGENTS.md",
            ".codex/hooks.json",
            ".claude/settings.json",
            ".cursor/hooks.json",
        ) and not relative.startswith(allowed):
            raise DasyncError("UNSAFE_PATH", "Plan target is outside adapter-owned roots")

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
                    if observed["hash"] is None
                    else (
                        "clean" if observed == {"hash": owner["hash"], "mode": owner["mode"]} else "modified"
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

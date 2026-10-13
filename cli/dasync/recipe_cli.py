"""Versioned machine discovery and thin recipe operations over Engine."""

from pathlib import Path

from .config import Environment, Scope, load_config
from .contracts import SCHEMAS, STR, obj, validate
from .engine import Engine
from .errors import DasyncError
from .io import canonical, parse, read
from .recipe_contracts import CREATE, ENGINE_VERSION, PIN, PROTOCOL, TOKEN, UUID, key_record, key_tuple
from .recipe_engine import authority, deny, load_sources, registry
from .recipe_resolver import compose, resolve, selector
from .recipe_sources import Snapshots

OPERATIONS = {
    "prepare": {
        "operation": "source.prepare",
        "effects": "immutable-cache-only",
        "scope": False,
        "approvals": [],
        "input": obj({"source": STR}, ("source",)),
        "output": obj(
            {
                "candidate": TOKEN,
                "source_id": UUID,
                "pin": PIN,
                "kind": {"enum": ["recipe", "item"]},
                "snapshot_kind": {"const": "local-tree"},
                "items": {"type": "array", "items": STR},
                "effects": {"const": "immutable-cache-only"},
            },
            ("candidate", "source_id", "pin", "kind", "snapshot_kind", "items", "effects"),
        ),
    },
    "create": {
        "operation": "item.create",
        "effects": "reviewed-author-files",
        "scope": True,
        "approvals": ["ordinary-confirmation"],
        "input": CREATE,
        "output": SCHEMAS["recipe-plan"],
    },
    "sources": {
        "operation": "source.list",
        "effects": "none",
        "scope": False,
        "approvals": [],
        "input": obj({}),
        "output": {"type": "object"},
    },
    "list": {
        "operation": "item.list",
        "effects": "none",
        "scope": True,
        "approvals": [],
        "input": obj(
            {
                "query": {"type": "string", "maxLength": 2048},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                "offset": {"type": "integer", "minimum": 0},
            }
        ),
        "output": {"type": "object"},
    },
    "explain": {
        "operation": "item.explain",
        "effects": "none",
        "scope": True,
        "approvals": [],
        "input": obj({"selector": STR}, ("selector",)),
        "output": {"type": "object"},
    },
    "plan": {
        "operation": "selection.plan",
        "effects": "none",
        "scope": True,
        "approvals": ["source-trust-for-registration"],
        "input": SCHEMAS["recipe-request"],
        "output": SCHEMAS["recipe-plan"],
    },
    "apply": {
        "operation": "plan.apply",
        "effects": "reviewed-registration-intent-lock-provider-files",
        "scope": True,
        "approvals": ["ordinary-confirmation", "reviewed-plan-approvals"],
        "input": SCHEMAS["recipe-plan"],
        "output": {"type": "object"},
    },
    "sync": {
        "operation": "sync",
        "effects": "reviewed-provider-files",
        "scope": True,
        "approvals": ["ordinary-confirmation"],
        "input": obj({}),
        "output": {"type": "object"},
    },
    "doctor": {
        "operation": "doctor",
        "effects": "none",
        "scope": True,
        "approvals": [],
        "input": obj({}),
        "output": {"type": "object"},
    },
    "recover": {
        "operation": "recover",
        "effects": "journal-restoration",
        "scope": True,
        "approvals": ["ordinary-confirmation"],
        "input": obj({}),
        "output": {"type": "object"},
    },
    "deny": {
        "operation": "authority.deny",
        "effects": "authority-only",
        "scope": True,
        "approvals": ["ordinary-confirmation"],
        "input": obj({"identity": STR}, ("identity",)),
        "output": {"type": "object"},
    },
}


def describe():
    operations = {command: {**definition} for command, definition in OPERATIONS.items()}
    receipt = obj(
        {
            "changed": {"type": "boolean"},
            "receipt": {"type": ["string", "null"]},
            "operations": {"type": "integer", "minimum": 0},
        },
        ("changed", "receipt", "operations"),
    )
    for command in ("create", "apply", "sync"):
        operations[command]["output"] = {"oneOf": [SCHEMAS["recipe-plan"], receipt]}
    commands = [
        {
            "argv": ["dasync", "recipe", command],
            **definition,
            "target": {"scope": ["user", "project"], "project_path": "absolute existing directory"}
            if definition["scope"]
            else None,
        }
        for command, definition in operations.items()
    ]
    commands.append(
        {
            "argv": ["dasync", "tui"],
            "operation": "workspace.open",
            "interactive": True,
            "effects": "reviewed-session",
            "scope": True,
            "approvals": ["source-trust", "reviewed-replacements", "ordinary-confirmation"],
            "input": obj({}),
            "output": {"type": "string"},
            "target": {"scope": ["user", "project"], "project_path": "absolute existing directory"},
        }
    )
    return {
        "bootstrap": "dasync describe --json",
        "protocols": [PROTOCOL],
        "experimental": True,
        "recipe_format": 1,
        "engine_version": ENGINE_VERSION,
        "plan_format": 2,
        "state_metadata_format": 1,
        "adapter": "recipe-codex/1",
        "mapping_version": 1,
        "commands": commands,
        "schemas": {
            name: {"$schema": "https://json-schema.org/draft/2020-12/schema", **schema}
            for name, schema in SCHEMAS.items()
            if name.startswith("recipe") or name in ("item-spec", "local-item")
        },
        "result_envelope": obj(
            {"protocol": {"const": PROTOCOL}, "version": {"const": 1}, "ok": {"const": True}, "result": {}},
            ("protocol", "version", "ok", "result"),
        ),
        "error_envelope": obj(
            {
                "protocol": {"const": PROTOCOL},
                "version": {"const": 1},
                "ok": {"const": False},
                "error": SCHEMAS["recipe-error"],
            },
            ("protocol", "version", "ok", "error"),
        ),
        "limits": {
            "items": 512,
            "depth": 64,
            "files": 2048,
            "snapshot_bytes": 134217728,
            "effective_source_bytes": 134217728,
            "cache_bytes": 536870912,
            "page_items": 200,
        },
        "unsupported": [
            "Git transport",
            "imports",
            "private context activation",
            "context slot binding",
            "hooks",
            "Agent/Policy adapters",
            "broader terminal/platform qualification of the TUI",
            "stable publication",
        ],
    }


def diagnostic(error, command):
    result = {
        **error.as_dict(),
        "origin": "engine",
        "effects": "none",
        "retryable": error.code in ("LOCKED", "SOURCE_UNAVAILABLE"),
    }
    if command == "prepare":
        result["effects"] = "immutable-cache-only"
    if error.code in (
        "RECOVERY_REQUIRED",
        "RECOVERY_CONFLICT",
        "RECOVERY_BLOCKED",
        "VERIFY_FAILED",
        "STATE_INVALID",
        "OPERATION_FAILED",
    ):
        result["effects"] = "inspect-recovery"
    approvals = {
        "CONFIRMATION_REQUIRED": "ordinary-confirmation",
        "TRUST_REQUIRED": "source-trust",
        "DRIFT": "overwrite",
        "UNMANAGED_COLLISION": "overwrite",
    }
    if error.code in approvals:
        result["required_approval"] = {"kind": approvals[error.code]}
    validate("recipe-error", result)
    return result


def _request(args):
    if not args.request_file:
        raise DasyncError("USAGE", "This recipe operation requires --request FILE")
    return parse(read(Path(args.request_file)))


def run(args, confirm):
    command = args.subject
    if command not in OPERATIONS:
        raise DasyncError("USAGE", "Unknown recipe operation; use dasync describe --json")
    if args.item and command not in ("explain", "deny"):
        raise DasyncError("USAGE", "Unexpected positional argument for this operation")
    if (args.query or args.limit != 50 or args.offset != 0) and command != "list":
        raise DasyncError("USAGE", "Pagination and query options require recipe list")
    if args.protocol != PROTOCOL:
        raise DasyncError("PROTOCOL_UNSUPPORTED", "Unsupported machine protocol; use dasync describe --json")
    if any(
        (
            args.enable,
            args.disable,
            args.profile,
            args.remove_profile,
            args.all_public is not None,
            args.provider,
            args.allow_context,
            args.capability,
            args.bind_context,
            args.approve_executable,
            args.inherit_user is not None,
            args.conflict != "protect",
            args.replace_provider_config,
            args.config_only,
            args.apply,
            args.receipt,
            args.before,
            args.recover,
            args.project,
            args.source_kind,
            args.revision,
            args.grant_project,
            args.binding_provider,
            args.effective,
            args.consumer,
            args.allow_private_path,
        )
    ):
        raise DasyncError(
            "USAGE", "Recipe operations use their declared request schema; legacy flags are unsupported"
        )
    if args.trust_source and command != "plan":
        raise DasyncError("USAGE", "Source trust is an explicit registration planning decision")
    if args.request_file and command not in ("plan", "create"):
        raise DasyncError("USAGE", "--request requires recipe plan or create")
    if args.source and command != "prepare":
        raise DasyncError("USAGE", "--source requires recipe prepare")
    if args.plan_file and command != "apply":
        raise DasyncError("USAGE", "--plan requires recipe apply")
    env = Environment.current()
    if command == "prepare":
        if not args.source or args.dry_run:
            raise DasyncError(
                "USAGE", "prepare requires --source ABSOLUTE_ROOT and explicitly retains cache bytes"
            )
        return Snapshots(env.cache).prepare(Path(args.source))
    if command == "sources":
        from .state import State

        state = State(env.state)
        entries = state.metadata("recipe-registry", {"format": 1, "generation": 0, "sources": {}})
        return {
            "generation": entries["generation"],
            "sources": [
                {
                    "source_id": sid,
                    "alias": entry["alias"],
                    "generation": entry["generation"],
                    "pins": sorted(entry["pins"]),
                }
                for sid, entry in sorted(entries["sources"].items())
            ],
        }
    scope = Scope.get(env, args.scope, args.path)
    engine = Engine(env, scope)
    if command in ("list", "explain"):
        intent = load_config(scope.config)
        if intent["version"] != 2:
            raise DasyncError("PROTOCOL_REQUIRED", "This operation requires a recipe scope")
        personal = load_config(env.config, required=False) if scope.kind == "project" else None
        if personal and personal["version"] != 2:
            personal = None
        registered = registry(engine)
        sources = load_sources(engine, compose(intent, personal), registered)
        diagnostic, graph = None, {"items": [], "edges": []}
        try:
            _, graph = resolve(sources, intent, scope.kind, personal, authority(engine)["denied"])
        except DasyncError as exc:
            diagnostic = exc.as_dict()
        if command == "explain":
            if not args.item:
                raise DasyncError("USAGE", "recipe explain requires a selector")
            key = selector(args.item, sources, registered["sources"])
            return {
                "item": key_record(key),
                "selected": [item for item in graph["items"] if key_tuple(item) == key],
                "reverse_dependents": [edge[0] for edge in graph["edges"] if key_tuple(edge[1]) == key],
                "diagnostic": diagnostic,
            }
        if not 1 <= args.limit <= 200 or args.offset < 0 or len(args.query) > 2048:
            raise DasyncError(
                "USAGE", "Bounded listing requires limit 1..200, nonnegative offset and a bounded query"
            )
        items = [
            {
                "source_id": sid,
                "item_id": local_id,
                "selector": registered["sources"][sid]["alias"] + "/" + local_id,
                "kind": item.spec["kind"],
                "selected": any(key_tuple(row) == item.key for row in graph["items"]),
            }
            for sid, source in sorted(sources.items())
            for local_id, item in sorted(source.items.items())
            if args.query.casefold() in local_id.casefold()
        ]
        return {
            "items": items[args.offset : args.offset + args.limit],
            "total": len(items),
            "next_offset": args.offset + args.limit if args.offset + args.limit < len(items) else None,
            "diagnostic": diagnostic,
        }
    if command == "doctor":
        result = engine.status()
        result["healthy"] = bool(
            result["configured"]
            and not result.get("diagnostic")
            and not result["pending_recovery"]
            and result.get("pending_changes", 0) == 0
        )
        return result
    if command == "deny":
        if not args.item:
            raise DasyncError("USAGE", "recipe deny requires a source UUID or authoritative UUID/item key")
        if args.dry_run:
            return {"identity": args.item, "effects": "none", "proposed": "authority-only-deny"}
        confirm(args, {"deny": args.item, "scope": scope.key})
        return deny(engine, args.item)
    if command == "recover":
        pending = [journal["id"] for journal in engine.state.pending() if journal["scope"] == scope.key]
        if args.dry_run:
            return {"pending": pending, "effects": "none"}
        confirm(args, {"recover": pending, "scope": scope.key})
        return engine.state.recover(scope.key, engine._validate_target)
    if command == "apply":
        if not args.plan_file:
            raise DasyncError("USAGE", "recipe apply requires --plan FILE")
        value = parse(read(Path(args.plan_file)))
        plan = value.get("result", value)
        validate("recipe-plan", plan)
        if args.dry_run:
            fresh, _ = engine.build(plan["request"])
            if canonical(fresh) != canonical(plan):
                raise DasyncError("PLAN_INVALIDATED", "Plan inputs changed; review a new plan")
            return plan
        confirm(args, plan)
        return engine.apply(plan)
    request = {"operation": "recipe.sync"} if command == "sync" else _request(args)
    if args.trust_source:
        request["trust_source"] = True
    if command == "create" and request.get("operation") != "recipe.create":
        raise DasyncError("USAGE", "create requires a recipe.create request")
    plan, _ = engine.build(request)
    if command == "plan" or args.dry_run:
        return plan
    confirm(args, plan)
    return engine.apply(plan)

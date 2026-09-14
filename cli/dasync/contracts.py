"""JSON schemas are also the runtime validation contracts."""

from jsonschema import Draft202012Validator

from .errors import DasyncError

ID = {"type": "string", "pattern": "^[a-z][a-z0-9-]*(\\.[a-z0-9-]+)*$", "maxLength": 120}
STR = {"type": "string", "minLength": 1, "maxLength": 2048}
IDS = {"type": "array", "items": ID, "uniqueItems": True}
STRS = {"type": "array", "items": STR, "uniqueItems": True}
PROVIDERS = {"type": "array", "items": {"enum": ["codex", "claude", "cursor"]}, "uniqueItems": True}


def obj(properties, required=()):
    return {
        "type": "object",
        "properties": properties,
        "required": list(required),
        "additionalProperties": False,
    }


SOURCE = obj(
    {"location": STR, "revision": STR, "kind": {"enum": ["git", "local"]}}, ("location", "revision", "kind")
)
BINDING = obj({"path": STR, "projects": IDS, "providers": PROVIDERS}, ("path", "projects", "providers"))
CONFIG = obj(
    {
        "version": {"const": 1},
        "project": ID,
        "source": SOURCE,
        "packages": IDS,
        "profiles": IDS,
        "disabled": IDS,
        "providers": PROVIDERS,
        "inherit_user": {"type": "boolean"},
        "contexts": IDS,
        "capabilities": STRS,
        "approved_executables": STRS,
        "bindings": {"type": "object", "additionalProperties": BINDING},
        "projects": {"type": "object", "additionalProperties": obj({"bindings": IDS, "capabilities": STRS})},
    },
    ("version", "project", "source", "packages", "profiles", "disabled", "providers", "inherit_user"),
)
DEPENDENCIES = {"type": "object", "propertyNames": ID, "additionalProperties": {"type": "string"}}
MANIFEST = obj(
    {
        "apiVersion": {"const": "dasync.dev/v1"},
        "kind": {"enum": ["Skill", "Agent", "Context", "Policy", "Template", "Hook"]},
        "id": ID,
        "name": STR,
        "version": STR,
        "description": STR,
        "license": STR,
        "entry": STR,
        "files": STRS,
        "tags": STRS,
        "requires": DEPENDENCIES,
        "suggests": IDS,
        "conflicts": IDS,
        "capabilities": STRS,
        "prefers": STRS,
        "fallback": STR,
        "scopes": {"type": "array", "items": {"enum": ["user", "project"]}, "minItems": 1},
        "providers": PROVIDERS,
        "outputs": STRS,
        "token_budget": {"type": "integer", "minimum": 1},
        "context": obj(
            {
                "access": {"enum": ["inherit", "explicit", "never"]},
                "sensitivity": {"enum": ["public", "private"]},
                "binding": ID,
                "consumers": IDS,
            },
            ("access", "sensitivity", "consumers"),
        ),
        "policy": obj(
            {"globs": STRS, "priority": {"type": "integer"}, "conflict_group": ID}, ("globs", "priority")
        ),
        "executable": obj(
            {
                "events": STRS,
                "permissions": STRS,
                "timeout": {"type": "integer", "minimum": 1, "maximum": 300},
            },
            ("events", "permissions", "timeout"),
        ),
    },
    (
        "apiVersion",
        "kind",
        "id",
        "name",
        "version",
        "description",
        "license",
        "entry",
        "files",
        "scopes",
        "token_budget",
    ),
)
PROFILE = obj({"id": ID, "description": STR, "packages": IDS}, ("id", "description", "packages"))
MANIFEST["allOf"] = [
    {"if": {"properties": {"kind": {"const": kind}}}, "then": {"required": [field]}}
    for kind, field in [("Context", "context"), ("Policy", "policy"), ("Hook", "executable")]
]
PLAN_CONTEXT = obj(
    {
        "version": {"const": 1},
        "authority": {"enum": ["local", "github", "ado", "linear", "jira", "notion"]},
        "reference": STR,
        "authority_state": {"enum": ["current", "snapshot", "unavailable"]},
        "active_milestone": ID,
        "design_references": STRS,
        "milestones": {
            "type": "array",
            "items": obj(
                {
                    "id": ID,
                    "outcome": STR,
                    "status": {"enum": ["future", "active", "complete"]},
                    "exit_criteria": STRS,
                    "dependencies": IDS,
                    "phases": {
                        "type": "array",
                        "items": obj(
                            {
                                "id": ID,
                                "outcome": STR,
                                "tasks": {
                                    "type": "array",
                                    "items": obj(
                                        {
                                            "id": ID,
                                            "outcome": STR,
                                            "reference": STR,
                                            "acceptance": STRS,
                                            "verification": STRS,
                                            "dependencies": IDS,
                                            "status": {
                                                "enum": [
                                                    "planned",
                                                    "in-progress",
                                                    "blocked",
                                                    "complete",
                                                    "unknown",
                                                ]
                                            },
                                            "scope": STR,
                                            "human_input": STR,
                                            "sizing_exception": STR,
                                        },
                                        ("id", "outcome", "acceptance", "verification"),
                                    ),
                                },
                                "reference": STR,
                                "dependencies": IDS,
                                "acceptance": STRS,
                                "rollback": STR,
                            },
                            ("id", "outcome", "tasks"),
                        ),
                    },
                    "planning_task": obj({"id": ID, "outcome": STR, "reference": STR}, ("id", "outcome")),
                    "scope": STR,
                    "risks": STRS,
                    "reference": STR,
                },
                ("id", "outcome", "status", "exit_criteria", "dependencies"),
            ),
        },
    },
    ("version", "authority", "reference", "active_milestone", "milestones"),
)
SCHEMAS = {"config": CONFIG, "manifest": MANIFEST, "profile": PROFILE, "plan-context": PLAN_CONTEXT}

HASH = {"type": ["string", "null"], "pattern": "^[a-f0-9]{64}$"}
OBSERVED = obj({"hash": HASH, "mode": {"type": ["integer", "null"]}}, ("hash", "mode"))
OPERATION = obj(
    {
        "path": STR,
        "action": {"enum": ["keep", "write", "delete"]},
        "before": OBSERVED,
        "hash": HASH,
        "mode": {"type": ["integer", "null"]},
        "provider": STR,
        "package": STR,
    },
    ("path", "action", "before", "hash", "mode", "provider", "package"),
)
SCHEMAS["plan"] = obj(
    {
        "version": {"const": 1},
        "cli_version": STR,
        "adapter_version": STR,
        "platform": STR,
        "scope": {"enum": ["user", "project"]},
        "root": STR,
        "scope_key": STR,
        "request": obj(
            {
                "operation": {"enum": ["setup", "configure", "sync", "update", "repair", "rollback"]},
                "config": CONFIG,
                "config_only": {"type": "boolean"},
                "trust_source": {"type": "boolean"},
                "conflict": {"enum": ["protect", "overwrite"]},
                "receipt": STR,
                "before_receipt": {"type": "boolean"},
            },
            ("operation",),
        ),
        "previous_receipt": {"type": ["string", "null"]},
        "retain_outputs": {"type": "boolean"},
        "inputs": obj(
            {
                "config": OBSERVED,
                "user_config": OBSERVED,
                "sources": {"type": "object", "additionalProperties": HASH},
            },
            ("config", "user_config", "sources"),
        ),
        "graph": {"type": "object"},
        "decisions": {"type": "array", "items": {"type": "object"}},
        "operations": {"type": "array", "items": OPERATION},
    },
    (
        "version",
        "cli_version",
        "adapter_version",
        "platform",
        "scope",
        "root",
        "scope_key",
        "request",
        "previous_receipt",
        "retain_outputs",
        "inputs",
        "graph",
        "decisions",
        "operations",
    ),
)
SCHEMAS["error"] = obj(
    {
        "version": {"const": 1},
        "ok": {"const": False},
        "error": obj(
            {"code": STR, "message": STR, "hint": {"type": ["string", "null"]}}, ("code", "message", "hint")
        ),
    },
    ("version", "ok", "error"),
)


def validate(name: str, value: dict):
    errors = sorted(Draft202012Validator(SCHEMAS[name]).iter_errors(value), key=lambda e: str(e.path))
    if errors:
        # jsonschema error messages can contain private instance values.
        e = errors[0]
        raise DasyncError(
            "SCHEMA_INVALID",
            f"Invalid {name}: {e.validator} constraint at {'/'.join(map(str, e.path)) or '/'}",
        )
    if name == "plan-context":
        milestones = value["milestones"]
        ids = [m["id"] for m in milestones]
        if len(set(ids)) != len(ids):
            raise DasyncError("SCHEMA_INVALID", "Milestone IDs must be unique")
        active = [m for m in milestones if m["status"] == "active"]
        if len(active) != 1 or active[0]["id"] != value["active_milestone"]:
            raise DasyncError("SCHEMA_INVALID", "Exactly one immediate milestone must be active")
        for milestone in milestones:
            if milestone["status"] == "future" and (
                "phases" in milestone or "planning_task" not in milestone
            ):
                raise DasyncError(
                    "SCHEMA_INVALID", "Future milestones require one planning task and no phases"
                )
            if milestone["status"] == "active" and (
                not milestone.get("phases") or "planning_task" in milestone
            ):
                raise DasyncError("SCHEMA_INVALID", "Active milestone requires elaborated phases")
            if set(milestone["dependencies"]) - set(ids) or milestone["id"] in milestone["dependencies"]:
                raise DasyncError("SCHEMA_INVALID", "Milestone dependencies must name other milestones")
        seen = set(ids)
        for milestone in milestones:
            children = [milestone["planning_task"]] if "planning_task" in milestone else []
            for phase in milestone.get("phases", []):
                if not phase["tasks"]:
                    raise DasyncError("SCHEMA_INVALID", "An elaborated phase must contain tasks")
                children.extend([phase, *phase["tasks"]])
            for child in children:
                if child["id"] in seen:
                    raise DasyncError("SCHEMA_INVALID", "Planning item IDs must be globally unique")
                seen.add(child["id"])
        remaining = {m["id"]: set(m["dependencies"]) for m in milestones}
        while remaining:
            ready = {key for key, dependencies in remaining.items() if not dependencies}
            if not ready:
                raise DasyncError("SCHEMA_INVALID", "Milestone dependencies contain a cycle")
            remaining = {
                key: dependencies - ready for key, dependencies in remaining.items() if key not in ready
            }
        children = [phase for m in milestones for phase in m.get("phases", [])]
        children += [task for phase in children[:] for task in phase.get("tasks", [])]
        child_ids = {child["id"] for child in children}
        graph = {child["id"]: set(child.get("dependencies", [])) for child in children}
        if any(deps - child_ids for deps in graph.values()):
            raise DasyncError("SCHEMA_INVALID", "Phase/task dependencies must name elaborated items")
        # A phase completes after its own tasks, even if that relationship is implicit in the document.
        for child in children:
            graph[child["id"]].update(task["id"] for task in child.get("tasks", []))
        while graph:
            ready = {key for key, dependencies in graph.items() if not dependencies}
            if not ready:
                raise DasyncError("SCHEMA_INVALID", "Phase/task dependencies contain a cycle")
            graph = {key: deps - ready for key, deps in graph.items() if key not in ready}

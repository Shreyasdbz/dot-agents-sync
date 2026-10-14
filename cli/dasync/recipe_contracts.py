"""Experimental, offline recipe protocol. No legacy profiles or native authorship."""

import uuid

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from . import __version__
from .errors import DasyncError
from .schema_types import ID, OBSERVED, OPERATION, STR, STRS, obj

PROTOCOL = 1
FORMAT = 1
ENGINE_VERSION = __version__
UUID = {"type": "string", "pattern": "^[a-f0-9]{8}(-[a-f0-9]{4}){3}-[a-f0-9]{12}$"}
PIN = {"type": "string", "pattern": "^sha256:[a-f0-9]{64}$"}
TOKEN = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
KEY = obj({"source_id": UUID, "item_id": ID}, ("source_id", "item_id"))
KEYS = {"type": "array", "items": KEY, "uniqueItems": True, "maxItems": 512}
FEATURES = {
    "type": "array",
    "items": {"enum": ["imports", "native-agents", "native-policies", "python-hooks", "context-contracts"]},
    "uniqueItems": True,
    "maxItems": 5,
}
DEPENDENCY = {
    "type": "string",
    "pattern": r"^[a-z][a-z0-9-]*(\.[a-z0-9-]+)*(/[a-z][a-z0-9-]*(\.[a-z0-9-]+)*)?$",
    "maxLength": 241,
}
EXTENSIONS = {
    "type": "object",
    "maxProperties": 32,
    "propertyNames": {"pattern": "^[a-z][a-z0-9.-]+/[a-z][a-z0-9.-]+$"},
    "additionalProperties": {"type": ["string", "number", "boolean", "null"], "maxLength": 2048},
}
SLOT = obj(
    {
        "required": {"type": "boolean"},
        "cardinality": {"const": "one"},
        "contract_id": UUID,
        "version": STR,
        "content_format": {"const": "markdown"},
    },
    ("required", "cardinality", "contract_id", "version", "content_format"),
)
ITEM_SPEC = obj(
    {
        "format": {"const": FORMAT},
        "kind": {"enum": ["Skill", "Agent", "Context", "Policy", "Template", "Hook"]},
        "id": ID,
        "version": STR,
        "name": {"type": "string", "minLength": 1, "maxLength": 80},
        "description": STR,
        "entry": STR,
        "files": {"type": "array", "items": STR, "minItems": 1, "maxItems": 128, "uniqueItems": True},
        "license": STR,
        "scopes": {
            "type": "array",
            "items": {"enum": ["user", "project"]},
            "minItems": 1,
            "uniqueItems": True,
        },
        "requires": {
            "type": "object",
            "propertyNames": DEPENDENCY,
            "additionalProperties": STR,
            "maxProperties": 128,
        },
        "required_capabilities": STRS,
        "optional_capabilities": STRS,
        "required_features": FEATURES,
        "default_prompt": STR,
        "short_description": {"type": "string", "minLength": 25, "maxLength": 64},
        "invocations": {
            "type": "array",
            "items": obj({"dependency": DEPENDENCY}, ("dependency",)),
            "maxItems": 128,
        },
        "policy": obj(
            {"globs": {"type": "array", "maxItems": 0}, "priority": {"type": "integer"}},
            ("globs", "priority"),
        ),
        "agent": obj({"access": {"enum": ["inherit", "read-only"]}}, ("access",)),
        "executable": obj(
            {
                "runtime": {"const": "python"},
                "events": {
                    "type": "array",
                    "items": {"enum": ["pre_tool", "session_start", "stop"]},
                    "minItems": 1,
                    "uniqueItems": True,
                },
                "permissions": {"type": "array", "items": {"const": "stdin.read"}, "uniqueItems": True},
                "timeout": {"type": "integer", "minimum": 1, "maximum": 300},
            },
            ("runtime", "events", "permissions", "timeout"),
        ),
        "slots": {"type": "object", "propertyNames": ID, "additionalProperties": SLOT, "maxProperties": 32},
        "context": obj(
            {
                "sensitivity": {"enum": ["public", "private"]},
                "access": {"enum": ["inherit", "explicit", "never"]},
                "contract_id": UUID,
                "contract_version": STR,
                "content_format": {"const": "markdown"},
                "binding": ID,
                "consumers": KEYS,
            },
            ("sensitivity", "access"),
        ),
        "extensions": EXTENSIONS,
    },
    ("format", "kind", "id", "version", "name", "description", "entry", "files", "license", "scopes"),
)
ITEM_SPEC["allOf"] = [
    {"if": {"properties": {"kind": {"const": "Context"}}}, "then": {"required": ["context"]}},
]
ITEM_SPEC["allOf"] += [
    {
        "if": {"properties": {"kind": {"const": kind}}},
        "then": {"required": [field]},
        "else": {"not": {"required": [field]}},
    }
    for kind, field in (("Agent", "agent"), ("Policy", "policy"), ("Hook", "executable"))
]
RECIPE = obj(
    {
        "format": {"const": FORMAT},
        "source_id": UUID,
        "name": ID,
        "description": STR,
        "requires_engine": STR,
        "required_features": FEATURES,
        "items": {"type": "array", "items": STR, "minItems": 1, "maxItems": 512, "uniqueItems": True},
        "imports": {
            "type": "object",
            "propertyNames": ID,
            "additionalProperties": obj({"source_id": UUID}, ("source_id",)),
            "maxProperties": 128,
        },
        "extensions": EXTENSIONS,
    },
    (
        "format",
        "source_id",
        "name",
        "description",
        "requires_engine",
        "required_features",
        "items",
        "imports",
    ),
)
LOCAL_ITEM = {
    **obj(
        {"format": {"const": FORMAT}, "source_id": UUID, "item": {"$ref": "#/$defs/ItemSpec"}},
        ("format", "source_id", "item"),
    ),
    "$defs": {"ItemSpec": ITEM_SPEC},
}
SOURCE_PIN = obj({"source_id": UUID, "pin": PIN}, ("source_id", "pin"))
INTENT = obj(
    {
        "version": {"const": 2},
        "protocol": {"const": PROTOCOL},
        "sources": {"type": "array", "items": SOURCE_PIN, "maxItems": 512, "uniqueItems": True},
        "roots": KEYS,
        "disabled": KEYS,
        "providers": {"const": ["codex"]},
        "inherit_user": {"type": "boolean"},
    },
    ("version", "protocol", "sources", "roots", "disabled", "providers", "inherit_user"),
)
REGISTRATION = obj({"candidate": TOKEN, "alias": ID}, ("candidate", "alias"))
EXECUTABLE_APPROVAL = obj({**KEY["properties"], "digest": TOKEN}, ("source_id", "item_id", "digest"))
CONFIGURE = obj(
    {
        "operation": {"const": "recipe.configure"},
        "registrations": {"type": "array", "items": REGISTRATION, "maxItems": 512},
        "bind_sources": {"type": "array", "items": SOURCE_PIN, "maxItems": 512, "uniqueItems": True},
        "trust_source": {"type": "boolean"},
        "approve_executables": {
            "type": "array",
            "items": EXECUTABLE_APPROVAL,
            "uniqueItems": True,
            "maxItems": 512,
        },
        "enable": STRS,
        "remove": STRS,
        "disable": STRS,
        "undisable": STRS,
        "select_sources": STRS,
        "inherit_user": {"type": "boolean"},
        "conflict": {"enum": ["protect", "overwrite"]},
    },
    ("operation",),
)
SYNC = obj({"operation": {"const": "recipe.sync"}}, ("operation",))
RESTORE = obj(
    {"operation": {"const": "recipe.restore"}, "receipt": STR, "before_receipt": {"type": "boolean"}},
    ("operation", "receipt"),
)
CREATE = obj(
    {
        "operation": {"const": "recipe.create"},
        "source_id": UUID,
        "kind": {"enum": ["Skill", "Context"]},
        "id": ID,
        "name": STR,
        "description": STR,
        "license": STR,
    },
    ("operation", "source_id", "kind", "id", "name", "description", "license"),
)
REQUEST = {"oneOf": [CONFIGURE, SYNC, RESTORE, CREATE]}
PLAN = obj(
    {
        "version": {"const": 2},
        "protocol": {"const": PROTOCOL},
        "cli_version": STR,
        "adapter_version": {"const": "recipe-codex/2"},
        "mapping_version": {"const": 1},
        "platform": STR,
        "scope": {"enum": ["user", "project"]},
        "root": STR,
        "scope_key": STR,
        "request": REQUEST,
        "previous_receipt": {"type": ["string", "null"]},
        "retain_outputs": {"const": False},
        "inputs": obj(
            {
                "config": OBSERVED,
                "user_config": OBSERVED,
                "lock": OBSERVED,
                "registry": TOKEN,
                "authority": TOKEN,
                "executables": TOKEN,
                "snapshots": {"type": "object", "additionalProperties": PIN},
            },
            ("config", "user_config", "lock", "registry", "authority", "executables", "snapshots"),
        ),
        "graph": {"type": "object"},
        "project_lock": {"type": ["object", "null"]},
        "mapping": {"type": "object"},
        "decisions": {"type": "array", "items": {"type": "object"}},
        "operations": {
            "type": "array",
            "items": {**OPERATION, "properties": {**OPERATION["properties"], "contributors": KEYS}},
        },
        "plan_hash": TOKEN,
    },
    (
        "version",
        "protocol",
        "cli_version",
        "adapter_version",
        "mapping_version",
        "platform",
        "scope",
        "root",
        "scope_key",
        "request",
        "previous_receipt",
        "retain_outputs",
        "inputs",
        "graph",
        "project_lock",
        "mapping",
        "decisions",
        "operations",
        "plan_hash",
    ),
)
LOCK = obj(
    {
        "format": {"const": FORMAT},
        "portable": {"const": False},
        "sources": {"type": "array", "items": SOURCE_PIN, "maxItems": 512},
        "roots": KEYS,
        "items": {
            "type": "array",
            "items": obj(
                {**KEY["properties"], "version": STR, "digest": TOKEN},
                ("source_id", "item_id", "version", "digest"),
            ),
        },
        "edges": {"type": "array", "items": {"type": "array", "items": KEY, "minItems": 2, "maxItems": 2}},
    },
    ("format", "portable", "sources", "roots", "items", "edges"),
)
SCHEMAS = {
    "recipe": RECIPE,
    "item-spec": ITEM_SPEC,
    "local-item": LOCAL_ITEM,
    "recipe-slot": SLOT,
    "recipe-intent": INTENT,
    "recipe-request": REQUEST,
    "recipe-plan": PLAN,
    "recipe-lock": LOCK,
    "recipe-error": obj(
        {
            "code": STR,
            "message": STR,
            "hint": {"type": ["string", "null"]},
            "origin": {"const": "engine"},
            "effects": {"enum": ["none", "immutable-cache-only", "inspect-recovery"]},
            "retryable": {"type": "boolean"},
            "details": {"type": "object"},
            "required_approval": obj(
                {
                    "kind": {
                        "enum": ["ordinary-confirmation", "source-trust", "overwrite", "executable-digest"]
                    }
                },
                ("kind",),
            ),
        },
        ("code", "message", "hint", "origin", "effects", "retryable"),
    ),
}


def semantic(name, value):
    """Checks that schema types alone cannot express; diagnostics never echo source values."""
    try:
        if name in ("recipe", "local-item"):
            if not uuid.UUID(value["source_id"]).int:
                raise ValueError
        if name == "recipe":
            if Version(ENGINE_VERSION) not in SpecifierSet(value["requires_engine"], prereleases=True):
                raise DasyncError(
                    "ENGINE_UNSUPPORTED", "Recipe requires an unsupported experimental engine version"
                )
            if any(not uuid.UUID(record["source_id"]).int for record in value["imports"].values()):
                raise ValueError
        if name == "local-item":
            semantic("item-spec", value["item"])
        if name == "item-spec":
            Version(value["version"])
            for constraint in value.get("requires", {}).values():
                SpecifierSet(constraint)
            if value["entry"] not in value["files"]:
                raise ValueError
            if value["kind"] == "Hook" and not value["entry"].endswith(".py"):
                raise ValueError
            for slot in value.get("slots", {}).values():
                semantic("recipe-slot", slot)
            context = value.get("context", {})
            if "contract_version" in context:
                Version(context["contract_version"])
            if ("contract_id" in context) != ("contract_version" in context):
                raise ValueError
        if name == "recipe-slot":
            SpecifierSet(value["version"])
            if not uuid.UUID(value["contract_id"]).int:
                raise ValueError
        if name == "recipe-intent":
            ids = [source["source_id"] for source in value["sources"]]
            if len(ids) != len(set(ids)):
                raise ValueError
            if any(key["source_id"] not in ids for key in value["roots"] + value["disabled"]):
                raise ValueError
            if {key_tuple(key) for key in value["roots"]} & {key_tuple(key) for key in value["disabled"]}:
                raise ValueError
    except (ValueError, InvalidVersion, InvalidSpecifier) as exc:
        raise DasyncError("SCHEMA_INVALID", f"Invalid {name} semantic contract") from exc


def key_tuple(key):
    return key["source_id"], key["item_id"]


def key_record(key):
    return {"source_id": key[0], "item_id": key[1]}


def key_text(key):
    return key[0] + "/" + key[1]

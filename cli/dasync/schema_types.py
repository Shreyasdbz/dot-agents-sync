"""Shared offline JSON Schema building blocks."""

ID = {"type": "string", "pattern": "^[a-z][a-z0-9-]*(\\.[a-z0-9-]+)*$", "maxLength": 120}
STR = {"type": "string", "minLength": 1, "maxLength": 2048}
IDS = {"type": "array", "items": ID, "uniqueItems": True}
STRS = {"type": "array", "items": STR, "uniqueItems": True}
PROVIDERS = {
    "type": "array",
    "items": {"enum": ["codex", "claude", "copilot", "cursor"]},
    "uniqueItems": True,
}


def obj(properties, required=()):
    return {
        "type": "object",
        "properties": properties,
        "required": list(required),
        "additionalProperties": False,
    }


HASH = {"type": ["string", "null"], "pattern": "^[a-f0-9]{64}$"}
OBSERVED = obj(
    {
        "hash": HASH,
        "mode": {"type": ["integer", "null"]},
        "type": {"enum": ["missing", "file", "symlink", "directory"]},
    },
    ("hash", "mode", "type"),
)
OPERATION = obj(
    {
        "path": STR,
        "action": {"enum": ["keep", "write", "delete"]},
        "before": OBSERVED,
        "hash": HASH,
        "mode": {"type": ["integer", "null"]},
        "target_type": {"enum": ["missing", "file", "symlink"]},
        "shadowed_by": STR,
        "hidden_by": STR,
        "provider": STR,
        "package": STR,
    },
    ("path", "action", "before", "hash", "mode", "target_type", "provider", "package"),
)

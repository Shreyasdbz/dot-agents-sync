"""Scope-local approval of exact executable item bytes; never portable authority."""

import copy

from .errors import DasyncError
from .recipe_contracts import key_record, key_tuple

EMPTY = {"format": 1, "generation": 0, "approvals": {}}


def executable_state(engine):
    return engine.state.metadata("recipe-executables", copy.deepcopy(EMPTY))


def approved_pairs(state, scope):
    return {(key_tuple(row), row["digest"]) for row in state["approvals"].get(scope, [])}


def propose(engine, request, sources):
    current = executable_state(engine)
    desired = copy.deepcopy(current)
    approved = approved_pairs(current, engine.scope.key)
    for record in request.get("approve_executables", []):
        key = key_tuple(record)
        source = sources.get(key[0])
        item = source.items.get(key[1]) if source else None
        if item is None or item.spec["kind"] != "Hook" or item.digest != record["digest"]:
            raise DasyncError(
                "EXECUTABLE_APPROVAL_INVALID",
                "Approval must identify an exact Hook digest at a bound accepted snapshot",
            )
        approved.add((key, item.digest))
    if approved != approved_pairs(current, engine.scope.key):
        desired["approvals"][engine.scope.key] = [
            {**key_record(key), "digest": digest} for key, digest in sorted(approved)
        ]
        desired["generation"] += 1
    return desired

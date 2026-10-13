"""Recipe planning uses the existing Engine/State transaction and file journal."""

import base64
import copy
import platform
from pathlib import Path

from . import __version__
from .config import encode_config, load_config
from .contracts import validate
from .errors import DasyncError
from .io import MAX_FILE, canonical, digest, observe, parse
from .recipe_adapters import ADAPTER_VERSION, MAPPING_VERSION, render
from .recipe_contracts import key_record, key_text, key_tuple
from .recipe_resolver import compose, project_lock, resolve, selector
from .recipe_sources import Snapshots

EMPTY_REGISTRY = {"format": 1, "generation": 0, "sources": {}}
EMPTY_AUTHORITY = {"format": 1, "generation": 0, "denied": []}


def registry(engine):
    return engine.state.metadata("recipe-registry", copy.deepcopy(EMPTY_REGISTRY))


def authority(engine):
    return engine.state.metadata("recipe-authority", copy.deepcopy(EMPTY_AUTHORITY))


def registrations(engine, request):
    current = registry(engine)
    desired = copy.deepcopy(current)
    candidates = request.get("registrations", [])
    if candidates and request.get("trust_source") is not True:
        raise DasyncError("TRUST_REQUIRED", "Registration requires a separate explicit source-trust decision")
    seen = set()
    for registration in candidates:
        record, _ = Snapshots(engine.env.cache).candidate(registration["candidate"])
        sid = record["source_id"]
        if sid in seen:
            raise DasyncError("SOURCE_CONFLICT", "Only one registration candidate per source is allowed")
        seen.add(sid)
        existing = desired["sources"].get(sid)
        if existing and existing["origin"] != record["origin"]:
            raise DasyncError(
                "ORIGIN_CONFLICT",
                "This UUID is registered at another root; UUID equality cannot transfer trust",
            )
        if sid in authority(engine)["denied"]:
            raise DasyncError(
                "AUTHORITY_DENIED", "This source was denied; registration cannot renew its authority"
            )
        entry = (
            copy.deepcopy(existing) if existing else {"origin": record["origin"], "generation": 0, "pins": {}}
        )
        entry["alias"] = registration["alias"]
        entry["pins"][record["pin"]] = record["snapshot"]
        if entry != existing:
            entry["generation"] += 1
            desired["sources"][sid] = entry
    aliases = [entry["alias"] for entry in desired["sources"].values()]
    if len(aliases) > 512:
        raise DasyncError("SOURCE_LIMIT", "Machine registry exceeds the source limit")
    if len(aliases) != len(set(aliases)):
        raise DasyncError(
            "ALIAS_CONFLICT", "Registration aliases must be unique; authoritative UUIDs are unchanged"
        )
    if desired != current:
        desired["generation"] += 1
    return desired


def metadata_updates(engine, request):
    if request["operation"] != "recipe.configure":
        return {}
    desired = registrations(engine, request)
    return {"recipe-registry": desired} if desired != registry(engine) else {}


def load_sources(engine, pins, registered):
    result = {}
    total_files, total_bytes = 0, 0
    snapshots = Snapshots(engine.env.cache)
    for sid, pin in sorted(pins.items()):
        entry = registered["sources"].get(sid)
        if entry is None or pin not in entry["pins"]:
            raise DasyncError(
                "SOURCE_UNBOUND", "Source/pin has no approved local registration", details={"source_id": sid}
            )
        source = snapshots.load(entry["pins"][pin], pin)
        if source.source_id != sid:
            raise DasyncError("SOURCE_INTEGRITY", "Registered source UUID differs from retained snapshot")
        total_files += len(source.files)
        total_bytes += sum(map(len, source.files.values()))
        if total_files > 5000 or total_bytes > 128 * 1024 * 1024:
            raise DasyncError("SOURCE_LIMIT", "Effective source set exceeds total file or byte limits")
        result[sid] = source
    return result


def initial():
    return {
        "version": 2,
        "protocol": 1,
        "sources": [],
        "roots": [],
        "disabled": [],
        "providers": ["codex"],
        "inherit_user": True,
    }


def _desired(engine, request, existing, registered):
    desired = copy.deepcopy(existing) if existing else initial()
    if "inherit_user" in request:
        desired["inherit_user"] = request["inherit_user"]
    pins = {record["source_id"]: record["pin"] for record in desired["sources"]}
    for record in request.get("bind_sources", []):
        sid, pin = record["source_id"], record["pin"]
        if any(other["source_id"] == sid and other["pin"] != pin for other in request["bind_sources"]):
            raise DasyncError("SNAPSHOT_CONFLICT", "A draft cannot bind competing pins for one source")
        pins[sid] = pin
    for registration in request.get("registrations", []):
        record, _ = Snapshots(engine.env.cache).candidate(registration["candidate"])
        if any(
            binding["source_id"] == record["source_id"] and binding["pin"] != record["pin"]
            for binding in request.get("bind_sources", [])
        ):
            raise DasyncError("SNAPSHOT_CONFLICT", "Registration and binding disagree on a source pin")
        pins[record["source_id"]] = record["pin"]
    sources = load_sources(engine, pins, registered)
    roots, disabled = {key_tuple(k) for k in desired["roots"]}, {key_tuple(k) for k in desired["disabled"]}
    for source_selector in request.get("select_sources", []):
        matches = [sid for sid in sources if source_selector in (sid, registered["sources"][sid]["alias"])]
        if len(matches) != 1:
            raise DasyncError("SOURCE_UNKNOWN", "Bulk selection requires exactly one intent source")
        sid = matches[0]
        current = {(sid, local) for local in sources[sid].items}
        roots |= current
        disabled -= current
    for value in request.get("enable", []):
        key = selector(value, sources, registered["sources"])
        roots.add(key)
        disabled.discard(key)
    for value in request.get("remove", []):
        try:
            key = selector(value, sources, registered["sources"])
        except DasyncError as exc:
            if exc.code != "ITEM_UNKNOWN":
                raise
            qualifier, separator, local_id = value.partition("/")
            if not separator:
                local_id, qualifier = qualifier, None
            candidates = [
                key
                for key in roots
                if key[1] == local_id
                and (qualifier is None or qualifier in (key[0], registered["sources"][key[0]]["alias"]))
            ]
            if len(candidates) != 1:
                raise DasyncError(
                    "SELECTOR_AMBIGUOUS" if candidates else "ITEM_UNKNOWN",
                    "Removing a missing item requires one existing qualified direct root",
                    details={"candidates": [key_record(key) for key in sorted(candidates)]},
                ) from exc
            key = candidates[0]
        roots.discard(key)
    for value in request.get("disable", []):
        key = selector(value, sources, registered["sources"])
        roots.discard(key)
        disabled.add(key)
    for value in request.get("undisable", []):
        try:
            key = selector(value, sources, registered["sources"])
        except DasyncError as exc:
            if exc.code != "ITEM_UNKNOWN":
                raise
        else:
            disabled.discard(key)
            continue
        matching = [
            key
            for key in disabled
            if value in (key_text(key), registered["sources"][key[0]]["alias"] + "/" + key[1])
            or value == key[1]
        ]
        if len(matching) > 1:
            raise DasyncError("SELECTOR_AMBIGUOUS", "Clearing a disable requires an unambiguous item key")
        if matching:
            disabled.discard(matching[0])
        else:
            selector(value, sources, registered["sources"])
    desired["sources"] = [{"source_id": sid, "pin": pin} for sid, pin in sorted(pins.items())]
    desired["roots"] = [key_record(k) for k in sorted(roots)]
    desired["disabled"] = [key_record(k) for k in sorted(disabled)]
    validate("recipe-intent", desired)
    return desired


def _operations(engine, request, outputs, owners, current, restoration=None):
    operations = []
    old_owned = (current or {}).get("owned", {})
    other = engine.state.other_owners(engine.scope.key)
    for name in sorted(set(outputs) | set(old_owned)):
        path = Path(name)
        engine._validate_target(path)
        if name in other:
            raise DasyncError("OWNERSHIP_CONFLICT", "Another scope owns a planned file")
        before = observe(path)
        if before["type"] in ("directory", "symlink"):
            raise DasyncError("UNSAFE_PATH", "Recipe output is occupied by a directory or symbolic link")
        tracked = old_owned.get(name)
        owner = owners.get(name, tracked)
        content = outputs.get(name)
        target = {
            "hash": digest(content) if content is not None else None,
            "mode": owner["mode"] if content is not None else None,
            "type": "file" if content is not None else "missing",
        }
        expected = (
            {"hash": tracked["hash"], "mode": tracked["mode"], "type": tracked.get("type", "file")}
            if tracked
            else None
        )
        # Recipe intent and locks are managed data too: never silently adopt manual edits.
        drift = tracked and before != expected
        collision = not tracked and before["type"] != "missing"
        reviewed_restore = restoration and before == restoration.get(name)
        if (
            (drift or collision)
            and not reviewed_restore
            and request.get("conflict", "protect") != "overwrite"
        ):
            raise DasyncError(
                "DRIFT" if drift else "UNMANAGED_COLLISION",
                "An observed recipe target is protected; review the edit before overwriting",
            )
        operations.append(
            {
                "path": name,
                "action": "keep" if before == target else "write" if content is not None else "delete",
                "before": before,
                "hash": target["hash"],
                "mode": target["mode"],
                "target_type": target["type"],
                "provider": owner["provider"],
                "package": owner["package"],
                "contributors": owner.get("contributors", []),
            }
        )
    return operations


def _restore(engine, request, registered):
    receipt = engine.state.receipt(request["receipt"], engine.scope.key)
    if "recipe" not in receipt or receipt["recipe"]["plan"]["request"]["operation"] == "recipe.create":
        raise DasyncError("RECEIPT_UNSUPPORTED", "Restore requires a recipe installation receipt")
    target = receipt
    if request.get("before_receipt"):
        target = engine.state.receipt(receipt["previous"], engine.scope.key) if receipt["previous"] else None
    outputs = {path: base64.b64decode(data) for path, data in (target or {}).get("files", {}).items()}
    owners = copy.deepcopy((target or {}).get("owned", {}))
    if any(digest(data) != owners.get(path, {}).get("hash") for path, data in outputs.items()):
        raise DasyncError("STATE_INVALID", "Retained receipt output does not match its recorded digest")
    restoration = {}
    if request.get("before_receipt"):
        for backup in receipt["backups"]:
            path = backup["path"]
            restoration[path] = backup["after"]
            if backup["data"] is None:
                outputs.pop(path, None)
                owners.pop(path, None)
            else:
                outputs[path] = base64.b64decode(backup["data"])
                expected = owners.get(path, {})
                if backup["before"]["hash"] != expected.get("hash"):
                    owners[path] = {
                        "package": "@restored",
                        "provider": "dasync",
                        "mode": backup["before"]["mode"],
                    }
    intent_data = outputs.get(str(engine.scope.config))
    if intent_data:
        intent = parse(intent_data)
        validate("recipe-intent", intent)
        # Old receipt bytes are evidence; reactivation still requires current registrations and deny checks.
        personal = load_config(engine.env.config, required=False) if engine.scope.kind == "project" else None
        if personal and personal["version"] != 2:
            personal = None
        pins = compose(intent, personal)
        graph = copy.deepcopy((target or {}).get("graph", {}))
        previous_plan = (target or {}).get("recipe", {}).get("plan", {})
        recorded_pins = {record["source_id"]: record["pin"] for record in graph.get("sources", [])}
        if pins != recorded_pins or (
            engine.scope.kind == "project"
            and intent["inherit_user"]
            and observe(engine.env.config) != previous_plan.get("inputs", {}).get("user_config")
        ):
            raise DasyncError(
                "RESTORE_INPUTS_CHANGED",
                "Current inheritance differs from the receipt; review a new configuration",
            )
        for sid, pin in pins.items():
            entry = registered["sources"].get(sid)
            if not entry or pin not in entry["pins"]:
                raise DasyncError(
                    "SOURCE_UNBOUND", "Receipt source pin no longer has a current approved registration"
                )
        denied = authority(engine)["denied"]
        for record in graph.get("items", []):
            if record["source_id"] in denied or key_text(key_tuple(record)) in denied:
                raise DasyncError(
                    "AUTHORITY_DENIED", "Receipt graph activation is denied by current authority"
                )
        if (
            previous_plan.get("adapter_version") != ADAPTER_VERSION
            or previous_plan.get("mapping_version") != MAPPING_VERSION
        ):
            raise DasyncError(
                "RESTORE_INPUTS_CHANGED", "Receipt adapter/mapping version requires a reviewed migration"
            )
        graph["sources"] = [
            {
                "source_id": sid,
                "pin": pin,
                "registration_generation": registered["sources"][sid]["generation"],
            }
            for sid, pin in sorted(pins.items())
        ]
    else:
        graph, pins = {}, {}
    for path, owner in owners.items():
        if owner["provider"] == "codex":
            identity = owner["package"]
            if (
                identity in authority(engine)["denied"]
                or identity.split("/")[0] in authority(engine)["denied"]
            ):
                raise DasyncError("AUTHORITY_DENIED", "Receipt activation is denied by current authority")
    previous_plan = (target or {}).get("recipe", {}).get("plan", {})
    return (
        outputs,
        owners,
        graph,
        pins,
        previous_plan.get("project_lock"),
        previous_plan.get("mapping", {}),
        previous_plan.get("decisions", []),
        restoration,
    )


def build(engine, request):
    validate("recipe-request", request)
    current = engine.state.head(engine.scope.key)
    registered, grants = registry(engine), authority(engine)
    existing = load_config(engine.scope.config, required=False)
    outputs, owners, graph, pins, lock, mapping, decisions, restoration = {}, {}, {}, {}, None, {}, [], None
    if request["operation"] == "recipe.create":
        if engine.scope.kind != "project" or existing or current:
            raise DasyncError(
                "AUTHOR_SCOPE_REQUIRED",
                "Create requires an unused disposable author directory in project scope",
            )
        kind, entry = request["kind"], "SKILL.md" if request["kind"] == "Skill" else "CONTEXT.md"
        spec = {
            "format": 1,
            "kind": kind,
            "id": request["id"],
            "version": "0.1.0",
            "name": request["name"],
            "description": request["description"],
            "license": request["license"],
            "entry": entry,
            "files": [entry],
            "scopes": ["user", "project"],
            "requires": {},
        }
        if kind == "Context":
            spec["context"] = {"sensitivity": "public", "access": "explicit"}
        envelope = {"format": 1, "source_id": request["source_id"], "item": spec}
        validate("local-item", envelope)
        for filename, content in {
            "item.yaml": canonical(envelope),
            entry: ("# " + request["name"] + "\n\nAuthor the canonical content here.\n").encode(),
        }.items():
            path = str(engine.scope.root / filename)
            outputs[path] = content
            owners[path] = {"package": "@author", "provider": "dasync", "mode": 0o644}
    elif request["operation"] == "recipe.restore":
        outputs, owners, graph, pins, lock, mapping, decisions, restoration = _restore(
            engine, request, registered
        )
    else:
        if existing and existing["version"] != 2:
            raise DasyncError(
                "FORMAT_MIGRATION_REQUIRED",
                "Legacy catalog configuration needs a separate reviewed migration; choose an unused scope",
            )
        if request["operation"] == "recipe.sync" and not existing:
            raise DasyncError("NOT_CONFIGURED", "Create and review a recipe.configure plan first")
        registered = registrations(engine, request)
        desired = (
            _desired(engine, request, existing, registered)
            if request["operation"] == "recipe.configure"
            else existing
        )
        personal = load_config(engine.env.config, required=False) if engine.scope.kind == "project" else None
        if personal and personal["version"] != 2:
            if desired["inherit_user"]:
                raise DasyncError(
                    "INHERITANCE_UNSUPPORTED",
                    "Legacy personal catalog cannot be composed; explicitly disable inheritance",
                )
            personal = None
        pins = compose(desired, personal)
        sources = load_sources(engine, pins, registered)
        selected, graph = resolve(sources, desired, engine.scope.kind, personal, grants["denied"])
        graph["sources"] = [
            {
                "source_id": sid,
                "pin": pin,
                "registration_generation": registered["sources"][sid]["generation"],
            }
            for sid, pin in sorted(pins.items())
        ]
        artifacts, decisions, mapping = render(selected)
        for artifact in artifacts:
            path = str(engine.scope.root / artifact.relative)
            outputs[path] = artifact.content
            owners[path] = {
                "package": key_text(artifact.owner),
                "provider": artifact.provider,
                "mode": artifact.mode,
                "contributors": [key_record(key) for key in artifact.contributors],
            }
        if engine.scope.kind == "project":
            lock = project_lock(sources, desired)
            validate("recipe-lock", lock)
            path = str(engine.scope.root / ".dasync.lock")
            outputs[path], owners[path] = (
                canonical(lock),
                {"package": "@lock", "provider": "dasync", "mode": 0o644},
            )
        path = str(engine.scope.config)
        outputs[path], owners[path] = (
            encode_config(desired),
            {
                "package": "@config",
                "provider": "dasync",
                "mode": 0o600 if engine.scope.kind == "user" else 0o644,
            },
        )
    plan = {
        "version": 2,
        "protocol": 1,
        "cli_version": __version__,
        "adapter_version": ADAPTER_VERSION,
        "mapping_version": MAPPING_VERSION,
        "platform": platform.system(),
        "scope": engine.scope.kind,
        "root": str(engine.scope.root),
        "scope_key": engine.scope.key,
        "request": request,
        "previous_receipt": current["id"] if current else None,
        "retain_outputs": False,
        "inputs": {
            "config": observe(engine.scope.config),
            "user_config": observe(engine.env.config),
            "lock": observe(engine.scope.root / ".dasync.lock"),
            "registry": digest(canonical(registry(engine))),
            "authority": digest(canonical(grants)),
            "snapshots": pins,
        },
        "graph": graph,
        "project_lock": lock,
        "mapping": mapping,
        "decisions": decisions,
        "operations": _operations(engine, request, outputs, owners, current, restoration),
    }
    plan["plan_hash"] = digest(canonical(plan))
    if len(canonical(plan)) > MAX_FILE:
        raise DasyncError("PLAN_LIMIT", "Reviewed plan exceeds the saved-document limit")
    validate("recipe-plan", plan)
    return plan, outputs


def deny(engine, identity):
    registered = registry(engine)
    sid, separator, local_id = identity.partition("/")
    if sid not in registered["sources"]:
        raise DasyncError("SOURCE_UNKNOWN", "Deny requires a registered authoritative UUID or UUID/item key")
    if separator:
        from jsonschema import Draft202012Validator

        from .contracts import ID

        if not Draft202012Validator(ID).is_valid(local_id):
            raise DasyncError("ITEM_UNKNOWN", "Invalid deny item key")
    return engine.state.deny(identity)

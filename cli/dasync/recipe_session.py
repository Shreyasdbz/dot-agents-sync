"""A disposable interaction draft; Engine alone resolves and persists installation."""

import copy
import os
import unicodedata
from pathlib import Path

from .config import load_config
from .errors import DasyncError
from .io import assert_safe, canonical, parent_fd
from .recipe_adapters import native_name
from .recipe_contracts import key_record, key_text, key_tuple
from .recipe_engine import authority, initial, load_sources, registrations, registry
from .recipe_resolver import compose, resolve
from .recipe_sources import Snapshots


def display_text(value, limit=2048):
    """Publisher text is literal, bounded and cannot emit terminal controls or bidi instructions."""
    text = str(value)
    return "".join(
        char if unicodedata.category(char)[0] != "C" or char == "\n" else f"\\u{ord(char):04x}"
        for char in text[:limit]
    )


class RecipeSession:
    def __init__(self, engine):
        self.engine = engine
        self.last_result = None
        self.reload()

    def reload(self):
        base = load_config(self.engine.scope.config, required=False)
        if base and base["version"] != 2:
            raise DasyncError(
                "PROTOCOL_REQUIRED", "This workspace requires a recipe scope; legacy scopes use configure"
            )
        self.base = copy.deepcopy(base or initial())
        self.roots = {key_tuple(key) for key in self.base["roots"]}
        self.disabled = {key_tuple(key) for key in self.base["disabled"]}
        self.inherit = self.base["inherit_user"]
        self.pending, self.bindings = {}, {}
        self.approvals = {}
        self.revision, self.reviewed_revision, self.plan = 0, None, None
        self.sources, self.labels, self.load_error = {}, {}, None
        self.graph, self.graph_error = {}, None
        try:
            self.refresh_sources()
        except DasyncError as exc:
            self.load_error = exc

    @property
    def dirty(self):
        return bool(
            self.pending
            or self.approvals
            or self.bindings
            or self.roots != {key_tuple(k) for k in self.base["roots"]}
            or self.disabled != {key_tuple(k) for k in self.base["disabled"]}
            or self.inherit != self.base["inherit_user"]
        )

    def touch(self):
        self.revision += 1
        self.plan, self.reviewed_revision = None, None
        self.update_graph()

    def update_graph(self):
        personal = (
            load_config(self.engine.env.config, required=False)
            if self.engine.scope.kind == "project"
            else None
        )
        if personal and personal["version"] != 2:
            personal = None
        desired = {
            **self.base,
            "inherit_user": self.inherit,
            "sources": [{"source_id": sid, "pin": pin} for sid, pin in sorted(self.own_pins().items())],
            "roots": [key_record(key) for key in sorted(self.roots)],
            "disabled": [key_record(key) for key in sorted(self.disabled)],
        }
        self.graph_error = None
        try:
            _, self.graph = resolve(
                self.sources, desired, self.engine.scope.kind, personal, authority(self.engine)["denied"]
            )
        except DasyncError as exc:
            self.graph, self.graph_error = {}, exc

    def refresh_sources(self):
        registered = registrations(
            self.engine,
            {
                "operation": "recipe.configure",
                "registrations": list(self.pending.values()),
                "trust_source": bool(self.pending),
            },
        )
        desired = {
            **self.base,
            "inherit_user": self.inherit,
            "sources": [{"source_id": sid, "pin": pin} for sid, pin in sorted(self.own_pins().items())],
        }
        personal = (
            load_config(self.engine.env.config, required=False)
            if self.engine.scope.kind == "project"
            else None
        )
        self.load_error = None
        if personal and personal["version"] != 2:
            if self.inherit:
                self.load_error = DasyncError(
                    "INHERITANCE_UNSUPPORTED", "Personal legacy catalog needs inheritance turned off"
                )
            personal = None
        try:
            pins = compose(desired, personal)
        except DasyncError as exc:
            self.load_error = exc
            # This is a browsing projection, not a resolution: review still rejects conflicting pins.
            pins = {source["source_id"]: source["pin"] for source in (personal or {}).get("sources", [])}
            pins.update(self.own_pins())
        self.sources = load_sources(self.engine, pins, registered)
        self.labels = {sid: entry["alias"] for sid, entry in registered["sources"].items()}
        self.update_graph()

    def own_pins(self):
        pins = {record["source_id"]: record["pin"] for record in self.base["sources"]}
        pins.update(self.bindings)
        for sid, registration in self.pending.items():
            record, _ = Snapshots(self.engine.env.cache).candidate(registration["candidate"])
            pins[sid] = record["pin"]
        return pins

    def stage(self, candidate, alias, trusted=False):
        if not trusted:
            raise DasyncError(
                "TRUST_REQUIRED", "Review and explicitly trust the prepared source before staging"
            )
        record, _ = Snapshots(self.engine.env.cache).candidate(candidate)
        pending = {**self.pending, record["source_id"]: {"candidate": candidate, "alias": alias}}
        from .contracts import validate

        request = {
            "operation": "recipe.configure",
            "registrations": list(pending.values()),
            "trust_source": True,
        }
        validate("recipe-request", request)
        registrations(self.engine, request)
        self.pending = pending
        self.approvals = {
            key: value for key, value in self.approvals.items() if key[0] != record["source_id"]
        }
        self.bindings.pop(record["source_id"], None)
        self.touch()
        self.refresh_sources()

    def bind(self, sid, pin):
        registered = registry(self.engine)
        if sid in authority(self.engine)["denied"]:
            raise DasyncError("AUTHORITY_DENIED", "This source is denied")
        load_sources(self.engine, {sid: pin}, registered)
        self.pending.pop(sid, None)
        self.approvals = {key: value for key, value in self.approvals.items() if key[0] != sid}
        self.bindings[sid] = pin
        self.touch()
        self.refresh_sources()

    def toggle(self, key):
        if key in self.roots:
            self.roots.remove(key)
        else:
            if key[0] not in self.own_pins():
                self.bindings[key[0]] = self.sources[key[0]].pin
            self.roots.add(key)
            self.disabled.discard(key)
        self.touch()

    def disable(self, key):
        if key[0] not in self.own_pins():
            self.bindings[key[0]] = self.sources[key[0]].pin
        self.roots.discard(key)
        self.disabled.symmetric_difference_update({key})
        self.touch()

    def set_inheritance(self, value):
        self.inherit = value
        self.touch()
        self.refresh_sources()

    def request(self, overwrite=False):
        base_roots = {key_tuple(key) for key in self.base["roots"]}
        # Enabling existing roots clears their old disables; missing removed roots are still qualified.
        request = {
            "operation": "recipe.configure",
            "enable": [key_text(k) for k in sorted(self.roots)],
            "remove": [key_text(k) for k in sorted(base_roots - self.roots)],
            "disable": [key_text(k) for k in sorted(self.disabled)],
            "inherit_user": self.inherit,
        }
        request["undisable"] = [
            key_text(k) for k in sorted({key_tuple(k) for k in self.base["disabled"]} - self.disabled)
        ]
        if self.pending:
            request.update(registrations=list(self.pending.values()), trust_source=True)
        if self.bindings:
            request["bind_sources"] = [
                {"source_id": sid, "pin": pin} for sid, pin in sorted(self.bindings.items())
            ]
        if self.approvals:
            request["approve_executables"] = [
                {**key_record(key), "digest": value} for key, value in sorted(self.approvals.items())
            ]
        if overwrite:
            request["conflict"] = "overwrite"
        return request

    def approve_hook(self, key, confirmed=False):
        if not confirmed:
            raise DasyncError(
                "EXECUTABLE_TRUST_REQUIRED", "Hook execution needs separate exact-digest approval"
            )
        source = self.sources.get(key[0])
        item = source.items.get(key[1]) if source else None
        if item is None or item.spec["kind"] != "Hook":
            raise DasyncError(
                "EXECUTABLE_APPROVAL_INVALID", "Select a Hook before approving executable bytes"
            )
        self.approvals[key] = item.digest
        self.touch()

    def review(self, overwrite=False, request=None):
        self.plan, self.reviewed_revision = None, None
        self.plan, _ = self.engine.build(request or self.request(overwrite))
        self.reviewed_revision = self.revision
        return self.plan

    def apply(self):
        if not self.plan or self.reviewed_revision != self.revision:
            raise DasyncError("PLAN_REQUIRED", "Review the current draft before applying")
        try:
            result = self.engine.apply(copy.deepcopy(self.plan))
        except Exception:
            self.plan, self.reviewed_revision = None, None
            raise
        self.last_result = result
        self.reload()
        return result

    def rows(self, query="", source=None):
        rows = []
        effective = {key_tuple(row): row for row in self.graph.get("items", [])}
        keys = {
            (sid, local_id) for sid, snapshot in self.sources.items() for local_id in snapshot.items
        } | self.roots
        for key in sorted(keys):
            if source and key[0] != source:
                continue
            spec_item = self.sources.get(key[0])
            spec_item = spec_item.items.get(key[1]) if spec_item else None
            spec = spec_item.spec if spec_item else {}
            private = spec.get("context", {}).get("sensitivity") == "private"
            label = self.labels.get(key[0], key[0][:8])
            name = "Private context" if private else spec.get("name", key[1])
            text = " ".join(
                [label, spec.get("kind", "missing"), name]
                + ([] if private else [key[1], spec.get("description", "")])
            )
            if query.casefold() not in text.casefold():
                continue
            status = "Direct" if key in self.roots else "Disabled" if key in self.disabled else "Available"
            if key in effective and key not in self.roots:
                reasons = effective[key]["reasons"]
                status = "Inherited" if any(r["kind"] == "inherited" for r in reasons) else "Dependency"
            rows.append(
                {
                    "key": key,
                    "source": label,
                    "id": "Private context" if private else key[1],
                    "name": name,
                    "kind": spec.get("kind", "Missing"),
                    "version": spec.get("version", "—"),
                    "status": status,
                    "private": private,
                    "missing": spec_item is None,
                }
            )
        return rows

    def detail(self, key, compact=False):
        source = self.sources.get(key[0])
        selected = source.items.get(key[1]) if source else None
        if not selected:
            return "Missing at this snapshot. Remove this direct root or choose another snapshot.", ""
        spec = selected.spec
        if spec.get("context", {}).get("sensitivity") == "private":
            return (
                "Private context is unavailable in this protocol. Its body and metadata are not displayed.",
                "",
            )
        lines = [
            spec["name"],
            "Publisher description: " + spec["description"],
            f"{spec['kind']} · version {spec['version']} · license {spec['license']}",
            "Source: " + self.labels[key[0]],
            "Item: " + key_text(key),
            "Snapshot: " + source.pin,
            "Native name: " + native_name(key),
            "Requires: " + (", ".join(spec.get("requires", {})) or "none"),
        ]
        if compact:
            lines = [
                spec["name"],
                spec["description"],
                f"{spec['kind']} · {spec['version']} · {spec['license']}",
                "Requires: " + (", ".join(spec.get("requires", {})) or "none"),
                "F4 for full identity and snapshot",
            ]
        if spec["kind"] == "Hook":
            lines.extend(
                [
                    "Executable digest: " + selected.digest,
                    "Events: " + ", ".join(spec["executable"]["events"]),
                    "Permissions: " + ", ".join(spec["executable"]["permissions"]),
                    "X: separately approve these exact bytes. Source trust and Apply do not approve execution.",
                ]
            )
        if spec["kind"] == "Agent":
            lines.append(
                "Role permissions inherit the parent session. This file cannot establish a read-only sandbox."
            )
        row = next((r for r in self.graph.get("items", []) if key_tuple(r) == key), None)
        if row:
            reasons = []
            for reason in row["reasons"]:
                if reason["kind"] == "dependency":
                    consumer = key_tuple(reason["consumer"])
                    reasons.append(f"Needed by {self.labels[consumer[0]]}/{consumer[1]}")
                else:
                    reasons.append("Direct pick" if reason["kind"] == "direct" else "Inherited personal pick")
            lines.append("Reasons: " + "; ".join(reasons))
        try:
            body = selected.files[spec["entry"]].decode("utf-8")
        except UnicodeError:
            body = "Preview unavailable: canonical content is not UTF-8."
        if len(body) > 8192:
            body = body[:8192] + "\n\n[Preview bounded to 8,192 characters]"
        return display_text("\n".join(lines), 4096), display_text(body, 8192)

    def health(self):
        return self.engine.status()

    def save_plan(self, path):
        if not self.plan or self.reviewed_revision != self.revision:
            raise DasyncError("PLAN_REQUIRED", "Review the current draft before saving")
        path = Path(path)
        if not path.is_absolute():
            raise DasyncError("PATH_REQUIRED", "Choose an absolute plan file path")
        assert_safe(path)
        if os.name == "nt":
            raise DasyncError(
                "CAPABILITY_UNSUPPORTED",
                "Safe TUI plan export requires the supported POSIX filesystem boundary",
            )
        data = canonical({"protocol": 1, "version": 1, "ok": True, "result": self.plan})
        try:
            with parent_fd(path) as parent:
                fd = os.open(
                    path.name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600, dir_fd=parent
                )
                with os.fdopen(fd, "wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.fsync(parent)
        except FileExistsError as exc:
            raise DasyncError("UNMANAGED_COLLISION", "Plan export never overwrites an existing file") from exc

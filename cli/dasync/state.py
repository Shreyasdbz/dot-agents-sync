"""Read-only inspection and serialized, journaled filesystem transactions."""

import base64
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from .errors import DasyncError
from .io import (
    assert_safe,
    atomic_write,
    canonical,
    digest,
    observe,
    remove_empty_tree,
    safe_symlink,
    safe_unlink,
    snapshot_entry,
)


class State:
    def __init__(self, directory: Path):
        self.directory = directory
        self.path = directory / "state.db"

    @contextmanager
    def connect(self, write=False):
        assert_safe(self.path)
        if not self.path.exists() and not write:
            yield None
            return
        if write:
            self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            conn = sqlite3.connect(
                str(self.path) if write else self.path.as_uri() + "?mode=ro", uri=not write
            )
            conn.row_factory = sqlite3.Row
            if write:
                os.chmod(self.path, 0o600)
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS receipts (
                      id TEXT PRIMARY KEY, scope TEXT NOT NULL, payload TEXT NOT NULL);
                    CREATE TABLE IF NOT EXISTS heads (scope TEXT PRIMARY KEY, receipt TEXT NOT NULL);
                    CREATE TABLE IF NOT EXISTS journal (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                """)
            try:
                yield conn
            finally:
                conn.close()
        except sqlite3.Error as exc:
            raise DasyncError("STATE_INVALID", "State database is unavailable or corrupt") from exc

    def head(self, scope: str):
        with self.connect() as db:
            if db is None:
                return None
            row = db.execute(
                "SELECT payload FROM receipts JOIN heads ON receipts.id=heads.receipt WHERE heads.scope=?",
                (scope,),
            ).fetchone()
            return self._normalize_payload(json.loads(row[0])) if row else None

    def receipt(self, receipt_id: str, scope: str):
        with self.connect() as db:
            row = (
                db.execute(
                    "SELECT payload FROM receipts WHERE id=? AND scope=?", (receipt_id, scope)
                ).fetchone()
                if db
                else None
            )
        if not row:
            raise DasyncError("RECEIPT_UNKNOWN", "No successful receipt with that ID in this scope")
        return self._normalize_payload(json.loads(row[0]))

    def pending(self):
        with self.connect() as db:
            return (
                [
                    self._normalize_payload(json.loads(row[0]))
                    for row in db.execute("SELECT payload FROM journal")
                ]
                if db
                else []
            )

    @staticmethod
    def _normalize_observed(value):
        return {
            **value,
            "type": value.get("type", "file" if value.get("hash") is not None else "missing"),
        }

    @classmethod
    def _normalize_payload(cls, value):
        for owner in value.get("owned", {}).values():
            owner.setdefault("type", "file")
        for item in value.get("backups", value.get("files", [])):
            if isinstance(item, dict) and "before" in item:
                item["before"] = cls._normalize_observed(item["before"])
                item["after"] = cls._normalize_observed(item["after"])
        return value

    def other_owners(self, scope):
        with self.connect() as db:
            if db is None:
                return {}
            rows = db.execute(
                "SELECT receipts.scope, payload FROM receipts JOIN heads ON receipts.id=heads.receipt WHERE receipts.scope != ?",
                (scope,),
            )
            return {path: row[0] for row in rows for path in json.loads(row[1])["owned"]}

    @contextmanager
    def lock(self):
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = self.directory / "transaction.lock"
        assert_safe(path)
        with path.open("a+b") as handle:
            try:
                if os.name == "nt":
                    import msvcrt

                    handle.seek(0)
                    if not handle.read(1):
                        handle.write(b"0")
                        handle.flush()
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise DasyncError(
                    "LOCKED", "Another dasync transaction holds the state lock; retry after it completes"
                ) from exc
            try:
                yield
            finally:
                if os.name == "nt":
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def recover(self, scope, validate_target):
        """Rollback incomplete journals only while the OS lock proves no writer is live."""
        with self.lock():
            pending = [j for j in self.pending() if j["scope"] == scope]
            for journal in pending:
                for item in journal["files"]:
                    validate_target(
                        Path(item["path"]),
                        {
                            ancestor
                            for ancestor in (item.get("shadowed_by"), item.get("hidden_by"))
                            if ancestor
                        },
                    )
                    current = self._journal_observe(item, journal)
                    if current not in (item["before"], item["after"]):
                        raise DasyncError(
                            "RECOVERY_CONFLICT",
                            "A journal target was independently changed; preserve it before recovery",
                        )
                self._restore(journal)
                with self.connect(write=True) as db:
                    db.execute("DELETE FROM journal WHERE id=?", (journal["id"],))
                    db.commit()
            return {"recovered": [j["id"] for j in pending]}

    @staticmethod
    def _journal_observe(item, journal):
        shadowed_children = [entry for entry in journal["files"] if entry.get("shadowed_by") == item["path"]]
        path = Path(item["path"])
        if shadowed_children and path.is_dir() and not path.is_symlink():
            return item["after"]
        shadowed_by = item.get("shadowed_by")
        if shadowed_by:
            ancestor = next(entry for entry in journal["files"] if entry["path"] == shadowed_by)
            ancestor_path = Path(shadowed_by)
            if ancestor_path.is_symlink() and observe(ancestor_path) == ancestor["before"]:
                return item["before"]
        hidden_by = item.get("hidden_by")
        if hidden_by:
            ancestor = next(entry for entry in journal["files"] if entry["path"] == hidden_by)
            ancestor_path = Path(hidden_by)
            if ancestor_path.is_symlink() and observe(ancestor_path) == ancestor["after"]:
                return item["after"]
        return observe(path)

    @staticmethod
    def _restore(journal):
        for item in reversed(journal["files"]):
            path = Path(item["path"])
            current = State._journal_observe(item, journal)
            if current == item["before"]:
                continue
            if current != item["after"]:
                raise DasyncError(
                    "RECOVERY_CONFLICT",
                    "A target changed independently; journal retained for manual recovery",
                )
            if item["before"]["type"] == "missing":
                safe_unlink(path)
            elif item["before"]["type"] == "symlink":
                if path.is_dir() and not path.is_symlink():
                    remove_empty_tree(path)
                else:
                    safe_unlink(path)
                safe_symlink(path, base64.b64decode(item["data"]).decode())
            elif item["before"]["type"] == "directory":
                safe_unlink(path)
                path.mkdir(parents=True, exist_ok=True, mode=item["before"]["mode"])
            else:
                if path.is_dir() and not path.is_symlink():
                    remove_empty_tree(path)
                atomic_write(path, base64.b64decode(item["data"]), item["before"]["mode"])

    def commit(self, plan, outputs, rebuild, fault=None):
        with self.lock():
            if self.pending():
                raise DasyncError("RECOVERY_REQUIRED", "An incomplete transaction requires repair --recover")
            fresh, fresh_outputs = rebuild()
            if canonical(fresh) != canonical(plan):
                raise DasyncError("PLAN_INVALIDATED", "Plan inputs changed; create and review a fresh plan")
            outputs = fresh_outputs
            changes = [op for op in plan["operations"] if op["action"] != "keep"]
            if not changes:
                return {"changed": False, "receipt": plan["previous_receipt"], "operations": 0}
            txid = str(uuid.uuid4())
            journal = {"id": txid, "scope": plan["scope_key"], "files": []}
            ordered_changes = sorted(
                changes,
                key=lambda op: (
                    op["before"]["type"] == "directory" and op["target_type"] in {"file", "symlink"},
                    op["path"],
                ),
            )
            for op in ordered_changes:
                path = Path(op["path"])
                if op.get("shadowed_by"):
                    data, mode, entry_type = None, None, "missing"
                else:
                    data, mode, entry_type = snapshot_entry(path)
                before = {
                    "hash": digest(data) if data is not None else None,
                    "mode": mode,
                    "type": entry_type,
                }
                if before != op["before"]:
                    raise DasyncError("PLAN_INVALIDATED", "A target changed while preparing its backup")
                journal["files"].append(
                    {
                        "path": str(path),
                        "before": before,
                        "after": {
                            "hash": op["hash"],
                            "mode": op["mode"],
                            "type": op["target_type"],
                        },
                        "data": base64.b64encode(data).decode() if data is not None else None,
                        **({"shadowed_by": op["shadowed_by"]} if op.get("shadowed_by") else {}),
                        **({"hidden_by": op["hidden_by"]} if op.get("hidden_by") else {}),
                    }
                )
            with self.connect(write=True) as db:
                db.execute("INSERT INTO journal VALUES (?,?)", (txid, canonical(journal).decode()))
                db.commit()
            try:
                for index, op in enumerate(ordered_changes):
                    if fault:
                        fault("before_write", index)
                    path = Path(op["path"])
                    if observe(path) != op["before"]:
                        raise DasyncError("PLAN_INVALIDATED", "A target changed during commit")
                    if op["action"] == "delete":
                        safe_unlink(path)
                    elif op["target_type"] == "symlink":
                        if path.is_dir() and not path.is_symlink():
                            remove_empty_tree(path)
                        else:
                            safe_unlink(path)
                        safe_symlink(path, outputs[op["path"]].decode())
                    else:
                        if op["before"]["type"] == "symlink":
                            safe_unlink(path)
                        elif op["before"]["type"] == "directory":
                            remove_empty_tree(path)
                        atomic_write(path, outputs[op["path"]], op["mode"])
                    if fault:
                        fault("after_write", index)
                for op in plan["operations"]:
                    path = Path(op["path"])
                    has_shadowed_children = any(
                        child.get("shadowed_by") == op["path"] for child in plan["operations"]
                    )
                    if has_shadowed_children and path.is_dir() and not path.is_symlink():
                        continue
                    if op.get("hidden_by") and Path(op["hidden_by"]).is_symlink():
                        continue
                    if observe(path) != {
                        "hash": op["hash"],
                        "mode": op["mode"],
                        "type": op["target_type"],
                    }:
                        raise DasyncError("VERIFY_FAILED", "Written file differs from planned content")
                previous = self.head(plan["scope_key"])
                owned = {
                    op["path"]: {
                        "hash": op["hash"],
                        "mode": op["mode"],
                        "type": op["target_type"],
                        "package": op["package"],
                        "provider": op["provider"],
                    }
                    for op in plan["operations"]
                    if op["hash"] is not None
                }
                saved_files = {p: base64.b64encode(b).decode() for p, b in outputs.items()}
                if plan.get("retain_outputs") and previous:
                    owned = {
                        **{p: o for p, o in previous["owned"].items() if o["package"] != "@config"},
                        **owned,
                    }
                    saved_files = {
                        **{
                            p: b
                            for p, b in previous["files"].items()
                            if previous["owned"][p]["package"] != "@config"
                        },
                        **saved_files,
                    }
                receipt = {
                    "id": txid,
                    "scope": plan["scope_key"],
                    "previous": plan["previous_receipt"],
                    "owned": owned,
                    "graph": plan["graph"],
                    "decisions": plan["decisions"],
                    "files": saved_files,
                    "plan_digest": digest(canonical(plan)),
                    "backups": journal["files"],
                }
                transient = {
                    op["path"] for op in plan["operations"] if op["package"] in {"@restored", "@preserved"}
                }
                for path in transient:
                    receipt["owned"].pop(path, None)
                    receipt["files"].pop(path, None)
                if fault:
                    fault("before_receipt", 0)
                with self.connect(write=True) as db:
                    db.execute(
                        "INSERT INTO receipts VALUES (?,?,?)",
                        (txid, plan["scope_key"], canonical(receipt).decode()),
                    )
                    db.execute("INSERT OR REPLACE INTO heads VALUES (?,?)", (plan["scope_key"], txid))
                    db.execute("DELETE FROM journal WHERE id=?", (txid,))
                    db.commit()
            except Exception:
                # Keep the journal if restoring fails, so doctor can prove incomplete state.
                self._restore(journal)
                with self.connect(write=True) as db:
                    db.execute("DELETE FROM journal WHERE id=?", (txid,))
                    db.commit()
                raise
            return {"changed": True, "receipt": txid, "operations": len(changes)}

"""Declared local files and retained, content-addressed recipe snapshots."""

import base64
import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .contracts import validate
from .errors import DasyncError
from .io import MAX_FILE, assert_safe, atomic_write, canonical, digest, parse, safe_path, snapshot

MAX_FILES = 2048
MAX_BYTES = 32 * MAX_FILE


def relative_path(name):
    """Portable file names, including directory/file and casefold checks, are protocol data."""
    path = PurePosixPath(name)
    if (
        not name
        or path.is_absolute()
        or str(path) != name
        or "\\" in name
        or any(part in (".", "..") for part in path.parts)
        or len(name) > 240
        or any(len(part) > 100 or part.endswith((".", " ")) for part in path.parts)
        or re.search(r'[\x00-\x1f\x7f<>:"|?*]', name)
        or any(
            part.split(".")[0].casefold()
            in {"con", "prn", "aux", "nul", *[f"com{i}" for i in range(10)], *[f"lpt{i}" for i in range(10)]}
            for part in path.parts
        )
    ):
        raise DasyncError("UNSAFE_PATH", "Expected a bounded portable relative file path")
    return path


def check_paths(names):
    names = list(names)
    folded = set()
    components = {}
    for name in sorted(names):
        relative_path(name)
        key = name.casefold()
        if key in folded:
            raise DasyncError("OUTPUT_COLLISION", "Exact or casefolded path collision")
        folded.add(key)
        for prefix in [name, *[str(parent) for parent in relative_path(name).parents if str(parent) != "."]]:
            prior = components.setdefault(prefix.casefold(), prefix)
            if prior != prefix:
                raise DasyncError("OUTPUT_COLLISION", "Casefolded directory spelling collision")
    for name in names:
        for parent in relative_path(name).parents:
            if str(parent) != "." and str(parent).casefold() in folded:
                raise DasyncError("OUTPUT_COLLISION", "File/directory path collision")


@dataclass(frozen=True)
class Item:
    source_id: str
    spec: dict
    files: dict[str, bytes]
    digest: str

    @property
    def key(self):
        return self.source_id, self.spec["id"]


class RecipeSnapshot:
    def __init__(self, files):
        if not files or len(files) > MAX_FILES or sum(map(len, files.values())) > MAX_BYTES:
            raise DasyncError("SOURCE_LIMIT", "Snapshot exceeds file or byte limits")
        check_paths(files)
        if "recipe.yaml" in files and "item.yaml" in files:
            raise DasyncError("SOURCE_INVALID", "Choose a recipe root or a singleton envelope, not both")
        if "recipe.yaml" in files:
            metadata = parse(files["recipe.yaml"])
            validate("recipe", metadata)
            self.kind, manifests = "recipe", metadata["items"]
        elif "item.yaml" in files:
            metadata = parse(files["item.yaml"])
            validate("local-item", metadata)
            self.kind, manifests = "item", ["item.yaml"]
        else:
            raise DasyncError("SOURCE_INVALID", "Source root requires recipe.yaml or item.yaml")
        self.source_id, self.metadata = metadata["source_id"], metadata
        self.items = {}
        declared = {"recipe.yaml"} if self.kind == "recipe" else set()
        for manifest in manifests:
            relative_path(manifest)
            if manifest not in files:
                raise DasyncError("SOURCE_INVALID", "Declared item manifest is missing")
            spec = parse(files[manifest]) if self.kind == "recipe" else metadata["item"]
            validate("item-spec", spec)
            folder = PurePosixPath(manifest).parent
            content = {}
            for name in spec["files"]:
                relative_path(name)
                full = (folder / name).as_posix()
                if full == manifest or full in declared:
                    raise DasyncError("SOURCE_INVALID", "Declared file ownership must be disjoint")
                if full not in files:
                    raise DasyncError("SOURCE_INVALID", "Declared item content is missing")
                content[name] = files[full]
                declared.add(full)
            declared.add(manifest)
            check_paths(content)
            if spec["id"] in self.items:
                raise DasyncError("SOURCE_INVALID", "Duplicate recipe-local item ID")
            item_digest = digest(
                canonical(spec) + canonical({n: digest(b) for n, b in sorted(content.items())})
            )
            self.items[spec["id"]] = Item(self.source_id, spec, content, item_digest)
        if set(files) != declared:
            raise DasyncError("SOURCE_INVALID", "Retained snapshot contains undeclared files")
        self.files = files
        self.pin = "sha256:" + digest(canonical({n: digest(b) for n, b in sorted(files.items())}))


def read_source(root):
    if not root.is_absolute() or ".." in root.parts:
        raise DasyncError("SOURCE_INVALID", "Local preparation requires an absolute source root")
    assert_safe(root)
    if not root.is_dir():
        raise DasyncError("SOURCE_UNAVAILABLE", "Local source root is unavailable")
    files = {}

    def declared(name):
        relative_path(name)
        path = safe_path(root, name)
        data, mode = snapshot(path)
        if data is None:
            raise DasyncError("SOURCE_UNAVAILABLE", "Declared source file is unavailable")
        if mode & 0o111 or name.endswith((".py", ".sh", ".ps1", ".bat", ".cmd", ".exe")):
            raise DasyncError(
                "EXECUTABLE_UNSUPPORTED", "Executable source content is not supported in the local milestone"
            )
        files[name] = data
        if len(files) > MAX_FILES or sum(map(len, files.values())) > MAX_BYTES:
            raise DasyncError("SOURCE_LIMIT", "Source exceeds file or byte limits")
        return parse(data)

    if (root / "recipe.yaml").exists() or (root / "recipe.yaml").is_symlink():
        metadata = declared("recipe.yaml")
        validate("recipe", metadata)
        if (root / "item.yaml").exists():
            raise DasyncError("SOURCE_INVALID", "Source root has two envelope types")
        manifests = metadata["items"]
    else:
        metadata = declared("item.yaml")
        validate("local-item", metadata)
        manifests = ["item.yaml"]
    for name in manifests:
        spec = metadata["item"] if name == "item.yaml" and "item" in metadata else declared(name)
        validate("item-spec", spec)
        for filename in spec["files"]:
            relative_path(filename)
            full = (PurePosixPath(name).parent / filename).as_posix()
            path = safe_path(root, full)
            data, mode = snapshot(path)
            if data is None:
                raise DasyncError("SOURCE_UNAVAILABLE", "Declared item file is unavailable")
            if mode & 0o111 or filename.endswith((".py", ".sh", ".ps1", ".bat", ".cmd", ".exe")):
                raise DasyncError(
                    "EXECUTABLE_UNSUPPORTED",
                    "Executable source content is not supported in the local milestone",
                )
            files[full] = data
            if len(files) > MAX_FILES or sum(map(len, files.values())) > MAX_BYTES:
                raise DasyncError("SOURCE_LIMIT", "Source exceeds file or byte limits")
    # Inspect entry types without reading undeclared files or traversing .git.
    stack = [root]
    entries = 0
    while stack:
        with os.scandir(stack.pop()) as children:
            for child in children:
                entries += 1
                if entries > MAX_FILES * 2:
                    raise DasyncError("SOURCE_LIMIT", "Source tree exceeds entry limits")
                if child.is_symlink():
                    raise DasyncError("UNSAFE_PATH", "Source tree contains a symbolic link")
                if child.is_dir(follow_symlinks=False):
                    if child.name == ".git":
                        continue
                    stack.append(Path(child.path))
                elif not child.is_file(follow_symlinks=False):
                    raise DasyncError("UNSAFE_PATH", "Source tree contains a special file")
                elif child.stat(follow_symlinks=False).st_mode & 0o111 or child.name.endswith(
                    (".py", ".sh", ".ps1", ".bat", ".cmd", ".exe")
                ):
                    raise DasyncError("EXECUTABLE_UNSUPPORTED", "Source tree contains executable content")
    return RecipeSnapshot(files)


class Snapshots:
    def __init__(self, cache):
        self.root = cache / "recipes-v1"

    def _path(self, category, token):
        if not re.fullmatch(r"[a-f0-9]{64}", token):
            raise DasyncError("SOURCE_INVALID", "Invalid immutable cache identifier")
        return self.root / category / (token + ".json")

    def _retain(self, category, value):
        data = canonical(value)
        if len(data) > MAX_BYTES * 2:
            raise DasyncError("SOURCE_LIMIT", "Encoded snapshot exceeds retention limit")
        token = digest(data)
        path = self._path(category, token)
        assert_safe(path)
        if path.exists():
            if self._read(category, token) != value:
                raise DasyncError("SOURCE_INTEGRITY", "Retained immutable record changed")
        else:
            retained = list(self.root.glob("*/*.json"))
            if (
                len(retained) >= 4096
                or sum(entry.stat().st_size for entry in retained) + len(data) > 128 * MAX_FILE
            ):
                raise DasyncError(
                    "CACHE_LIMIT", "Retention quota exceeded; no selected snapshot is automatically purged"
                )
            atomic_write(path, data, 0o600)
        return token

    def _read(self, category, token):
        # Records can be larger than ordinary documents; still bounded before decoding.
        path = self._path(category, token)
        assert_safe(path)
        if not path.exists():
            raise DasyncError(
                "SNAPSHOT_MISSING", "Retained immutable bytes are unavailable; prepare the exact source again"
            )
        import json

        data, _ = snapshot(path, max_bytes=MAX_BYTES * 2)
        if digest(data) != token:
            raise DasyncError("SOURCE_INTEGRITY", "Retained immutable bytes failed integrity validation")
        try:
            return json.loads(data)
        except (ValueError, UnicodeError) as exc:
            raise DasyncError("SOURCE_INTEGRITY", "Invalid retained record") from exc

    def prepare(self, root):
        from .state import State

        source = read_source(root)
        encoded = {name: base64.b64encode(data).decode() for name, data in source.files.items()}
        with State(self.root).lock():
            snapshot_token = self._retain("snapshots", {"format": 1, "files": encoded})
            record = {
                "format": 1,
                "source_id": source.source_id,
                "pin": source.pin,
                "snapshot": snapshot_token,
                "origin": str(root),
            }
            candidate = self._retain("candidates", record)
        return {
            "candidate": candidate,
            "source_id": source.source_id,
            "pin": source.pin,
            "kind": source.kind,
            "snapshot_kind": "local-tree",
            "items": sorted(source.items),
            "effects": "immutable-cache-only",
        }

    def candidate(self, token):
        record = self._read("candidates", token)
        if (
            not isinstance(record, dict)
            or set(record) != {"format", "source_id", "pin", "snapshot", "origin"}
            or record["format"] != 1
        ):
            raise DasyncError("SOURCE_INTEGRITY", "Invalid retained preparation record")
        if (
            not isinstance(record["origin"], str)
            or not Path(record["origin"]).is_absolute()
            or ".." in Path(record["origin"]).parts
        ):
            raise DasyncError("SOURCE_INTEGRITY", "Invalid retained local origin")
        source = self.load(record["snapshot"], record["pin"])
        if source.source_id != record["source_id"]:
            raise DasyncError("SOURCE_INTEGRITY", "Candidate identity differs from retained snapshot")
        return record, source

    def load(self, token, pin):
        record = self._read("snapshots", token)
        if not isinstance(record, dict) or record.get("format") != 1 or set(record) != {"format", "files"}:
            raise DasyncError("SOURCE_INTEGRITY", "Unsupported retained snapshot format")
        if not isinstance(record["files"], dict):
            raise DasyncError("SOURCE_INTEGRITY", "Invalid retained file map")
        try:
            files = {name: base64.b64decode(data, validate=True) for name, data in record["files"].items()}
        except (ValueError, TypeError) as exc:
            raise DasyncError("SOURCE_INTEGRITY", "Invalid retained file encoding") from exc
        if any(len(data) > MAX_FILE for data in files.values()):
            raise DasyncError("SOURCE_LIMIT", "Retained file exceeds size limit")
        source = RecipeSnapshot(files)
        if source.pin != pin:
            raise DasyncError("SOURCE_INTEGRITY", "Snapshot does not match accepted pin")
        return source

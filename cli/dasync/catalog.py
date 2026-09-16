"""Immutable Git objects and explicitly pinned local catalogs."""

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from .contracts import validate
from .errors import DasyncError
from .io import MAX_FILE, canonical, digest, parse, read, safe_path
from .sources import is_remote, repository


def git(root: Path, *args: str) -> bytes:
    repository_args = (
        ["--git-dir", str(root)]
        if (root / "HEAD").is_file() and (root / "objects").is_dir()
        else ["-C", str(root)]
    )
    try:
        p = subprocess.run(
            ["git", *repository_args, *args],
            capture_output=True,
            timeout=90,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DasyncError("SOURCE_UNAVAILABLE", "Git operation could not complete") from exc
    if p.returncode:
        raise DasyncError("SOURCE_UNAVAILABLE", "Git source or requested revision is unavailable")
    return p.stdout


def local_files(root: Path) -> dict[str, bytes]:
    result = {}
    for folder in ("packages", "profiles"):
        directory = safe_path(root, folder)
        if not directory.is_dir():
            raise DasyncError("CATALOG_INVALID", f"Catalog must contain {folder}/")
        for path in sorted(directory.rglob("*")):
            relative = path.relative_to(root).as_posix()
            safe_path(root, relative)
            if path.is_file():
                result[relative] = read(path)
    return result


def tree_digest(files: dict[str, bytes]) -> str:
    return digest(canonical({key: digest(data) for key, data in sorted(files.items())}))


def pin(location: str, kind: str, revision: str | None = None, cache: Path | None = None) -> dict:
    from .config import Environment

    cache = cache or Environment.current().cache
    root = repository(location, cache) if is_remote(location) else Path(location).absolute()
    if kind == "local":
        resolved = "sha256:" + tree_digest(local_files(root))
        if revision and revision != resolved:
            raise DasyncError("SOURCE_INTEGRITY", "Local catalog does not match the requested pin")
    else:
        if revision and not re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", revision):
            raise DasyncError("SOURCE_INVALID", "Use a full immutable Git commit ID")
        resolved = git(root, "rev-parse", "--verify", (revision or "HEAD") + "^{commit}").decode().strip()
    return {"location": location if is_remote(location) else str(root), "kind": kind, "revision": resolved}


@dataclass
class Package:
    manifest: dict
    files: dict[str, bytes]
    digest: str

    @property
    def id(self):
        return self.manifest["id"]


class Catalog:
    def __init__(self, source: dict, cache: Path | None = None):
        from .config import Environment

        self.source = source
        root, revision = (
            repository(source["location"], cache or Environment.current().cache),
            source["revision"],
        )
        if source["kind"] == "local":
            files = local_files(root)
            if revision != "sha256:" + tree_digest(files):
                raise DasyncError("SOURCE_INTEGRITY", "Local catalog changed; use update to accept a new pin")
        else:
            if not re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", revision):
                raise DasyncError("SOURCE_INVALID", "Git catalog revision is not an immutable commit ID")
            files = {}
            entries = git(root, "ls-tree", "-rz", revision, "--", "packages", "profiles").split(b"\0")
            for entry in filter(None, entries):
                metadata, name = entry.split(b"\t", 1)
                mode, kind, oid = metadata.split()
                if kind != b"blob" or mode not in (b"100644", b"100755"):
                    raise DasyncError("UNSAFE_PATH", "Catalog contains symlinks or submodules")
                path = name.decode("utf-8")
                safe_path(Path("/catalog-validation"), path)
                size = int(git(root, "cat-file", "-s", oid.decode()))
                if size > MAX_FILE:
                    raise DasyncError("CATALOG_INVALID", "Catalog file exceeds size limit")
                files[path] = git(root, "cat-file", "blob", oid.decode())
        if len(files) > 5000 or sum(map(len, files.values())) > 32 * MAX_FILE:
            raise DasyncError("CATALOG_INVALID", "Catalog exceeds resource limits")
        self.digest = tree_digest(files)
        self.packages, self.profiles = {}, {}
        for path, data in sorted(files.items()):
            if path.startswith("profiles/") and path.endswith((".yaml", ".json")):
                value = parse(data)
                validate("profile", value)
                if value["id"] in self.profiles:
                    raise DasyncError("CATALOG_INVALID", "Duplicate profile ID")
                self.profiles[value["id"]] = value
            if not path.startswith("packages/") or not path.endswith("/manifest.yaml"):
                continue
            m = parse(data)
            validate("manifest", m)
            try:
                Version(m["version"])
                for constraint in m.get("requires", {}).values():
                    SpecifierSet(constraint)
            except (InvalidVersion, InvalidSpecifier) as exc:
                raise DasyncError("CATALOG_INVALID", "Invalid version or dependency constraint") from exc
            folder = path.rsplit("/", 1)[0]
            included = {}
            for name in m["files"]:
                safe_path(Path("/catalog-validation"), name)
                key = folder + "/" + name
                if key not in files:
                    raise DasyncError("CATALOG_INVALID", f"Missing declared file in {m['id']}")
                included[name] = files[key]
            if m["entry"] not in included or m["id"] in self.packages:
                raise DasyncError("CATALOG_INVALID", "Missing entry point or duplicate package ID")
            if sum(len(b) for b in included.values()) // 4 > m["token_budget"]:
                raise DasyncError("TOKEN_BUDGET", f"Package {m['id']} exceeds its approximate token budget")
            pd = digest(canonical(m) + canonical({n: digest(b) for n, b in included.items()}))
            self.packages[m["id"]] = Package(m, included, pd)
        if not self.packages:
            raise DasyncError("CATALOG_INVALID", "No package manifests found")

    def roots(self, config):
        roots = {p: "direct" for p in config["packages"]}
        for name in config["profiles"]:
            if name not in self.profiles:
                raise DasyncError("PACKAGE_UNKNOWN", f"Unknown profile: {name}")
            for package in self.profiles[name]["packages"]:
                roots.setdefault(package, "profile:" + name)
        return roots

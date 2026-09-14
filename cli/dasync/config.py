"""Scope discovery and the two configuration surfaces."""

import os
import re
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_cache_path, user_config_path, user_state_path

from .contracts import validate
from .errors import DasyncError
from .io import assert_safe, canonical, parse, read


@dataclass(frozen=True)
class Environment:
    home: Path
    config: Path
    state: Path
    cache: Path

    @classmethod
    def current(cls):
        # One explicit sandbox switch supports demos/tests without touching real provider settings.
        sandbox = os.environ.get("DASYNC_HOME")
        if sandbox:
            root = Path(sandbox).absolute()
            return cls(root, root / "config/config.yaml", root / "state", root / "cache")
        return cls(
            Path.home(),
            user_config_path("dasync") / "config.yaml",
            user_state_path("dasync"),
            user_cache_path("dasync"),
        )


@dataclass(frozen=True)
class Scope:
    kind: str
    root: Path
    config: Path

    @property
    def key(self):
        return f"{self.kind}:{self.root}"

    @classmethod
    def get(cls, env: Environment, kind: str, path: str | None):
        if kind not in ("user", "project"):
            raise DasyncError("SCOPE_REQUIRED", "Specify --scope user or --scope project")
        if kind == "user":
            root = env.home
            if path and Path(path).absolute() != root:
                raise DasyncError("SCOPE_INVALID", "User scope path must match the configured home")
            config = env.config
        else:
            if not path or not Path(path).is_absolute():
                raise DasyncError("PATH_REQUIRED", "Project scope requires an absolute --path")
            root = Path(path)
            config = root / ".dasync.yaml"
        assert_safe(root)
        if not root.is_dir():
            raise DasyncError("SCOPE_INVALID", "Scope directory must already exist")
        return cls(kind, root, config)


def load_config(path: Path, required=True):
    data = read(path)
    if data is None:
        if required:
            raise DasyncError(
                "NOT_CONFIGURED", "Scope has no configuration", "Run dasync setup with an explicit scope"
            )
        return None
    value = parse(data)
    validate("config", value)
    return value


def encode_config(value: dict) -> bytes:
    validate("config", value)
    # JSON is valid YAML; stable serialization avoids lossy YAML round trips.
    return canonical(value)


def initial(project, source, providers, packages=(), profiles=()):
    return {
        "version": 1,
        "project": project,
        "source": source,
        "providers": list(providers),
        "packages": list(packages),
        "profiles": list(profiles),
        "disabled": [],
        "inherit_user": False,
        "contexts": [],
        "capabilities": [],
        "approved_executables": [],
    }


def default_project_id(root: Path) -> str:
    """Generate an editable identifier without making ordinary directory names invalid."""
    name = re.sub(r"[^a-z0-9-]+", "-", root.name.lower()).strip("-")[:100]
    return name if name and name[0].isalpha() else "project-" + (name or "local")

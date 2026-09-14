"""Explicit fetching and portable HTTPS Git source cache."""

import os
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from .errors import DasyncError
from .io import assert_safe, digest


def is_remote(location):
    return "://" in location


def repository(location: str, cache: Path) -> Path:
    if not is_remote(location):
        root = Path(location)
        if not root.is_absolute():
            raise DasyncError("SOURCE_INVALID", "Local source location must be absolute")
        assert_safe(root)
        return root
    url = urlsplit(location)
    if url.scheme != "https" or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise DasyncError(
            "SOURCE_INVALID",
            "Remote sources require an HTTPS URL without embedded credentials, query or fragment",
        )
    root = cache / "sources" / digest(location.encode())
    assert_safe(root)
    return root


def fetch(location: str, cache: Path):
    from .catalog import git

    root = repository(location, cache)
    if not is_remote(location):
        git(root, "fetch", "--no-tags", "origin")
        return git(root, "rev-parse", "FETCH_HEAD^{commit}").decode().strip()
    if not root.exists():
        root.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with tempfile.TemporaryDirectory(prefix="clone-", dir=root.parent) as directory:
            stage = Path(directory) / "repository"
            try:
                result = subprocess.run(
                    ["git", "clone", "--mirror", "--", location, str(stage)],
                    capture_output=True,
                    timeout=120,
                    env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise DasyncError("SOURCE_UNAVAILABLE", "Source fetch failed") from exc
            if result.returncode:
                raise DasyncError(
                    "SOURCE_UNAVAILABLE", "Source fetch failed; check authentication and network access"
                )
            try:
                os.rename(stage, root)
            except FileExistsError:
                pass  # Another writer populated the same immutable-source cache.
    else:
        if git(root, "remote", "get-url", "origin").decode().strip() != location:
            raise DasyncError("SOURCE_INTEGRITY", "Cached Git remote does not match configured source")
        git(root, "fetch", "--no-tags", "origin")
    return git(root, "rev-parse", "HEAD^{commit}").decode().strip()

"""Bounded document parsing and filesystem primitives."""

import hashlib
import json
import os
import stat
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

import yaml

from .errors import DasyncError

MAX_FILE = 4 * 1024 * 1024


class StrictLoader(yaml.SafeLoader):
    pass


def _mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str) or key in result:
            raise DasyncError("INVALID_DOCUMENT", "Mapping keys must be unique strings")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def parse(data: bytes) -> dict:
    if len(data) > MAX_FILE:
        raise DasyncError("INVALID_DOCUMENT", "Document exceeds 4 MiB")
    try:
        # Aliases add no value to public contracts and permit cyclic/exponential structures.
        if any(isinstance(t, (yaml.AliasToken, yaml.AnchorToken)) for t in yaml.scan(data)):
            raise DasyncError("INVALID_DOCUMENT", "YAML anchors and aliases are not supported")
        value = yaml.load(data, Loader=StrictLoader)
        if not isinstance(value, dict):
            raise DasyncError("INVALID_DOCUMENT", "Expected a mapping")
        json.dumps(value, allow_nan=False)
        return value
    except (yaml.YAMLError, UnicodeError, TypeError, ValueError, RecursionError) as exc:
        raise DasyncError("INVALID_DOCUMENT", "Invalid YAML/JSON document") from exc


def canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    parts = PurePosixPath(relative)
    if (
        not relative
        or parts.is_absolute()
        or "\\" in relative
        or ":" in relative
        or any(p in ("..", ".") for p in relative.split("/"))
    ):
        raise DasyncError("UNSAFE_PATH", "Path must be a confined relative file path")
    path = root.joinpath(*parts.parts)
    assert_safe(path)
    return path


def assert_safe(path: Path):
    for parent in [path, *path.parents]:
        if parent.is_symlink():
            raise DasyncError("UNSAFE_PATH", "Symbolic links are not accepted in managed paths")
        if parent.exists() and parent != path and not parent.is_dir():
            raise DasyncError("UNSAFE_PATH", "A path ancestor is not a directory")
    if path.exists() and not (path.is_file() or path.is_dir()):
        raise DasyncError("UNSAFE_PATH", "Special files are not accepted")


def read(path: Path) -> bytes | None:
    data, _ = snapshot(path)
    return data


@contextmanager
def parent_fd(path: Path, create=False):
    """Open each parent without following links; hold the directory through mutation."""
    path = path.absolute()
    fd = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            if create:
                try:
                    os.mkdir(part, mode=0o755, dir_fd=fd)
                except FileExistsError:
                    pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def snapshot(path: Path):
    assert_safe(path)
    if not path.exists():
        return None, None
    try:
        if os.name != "nt":
            with parent_fd(path) as directory:
                fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        else:
            fd = os.open(path, os.O_RDONLY | os.O_BINARY)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE:
                raise DasyncError("UNSAFE_PATH", "Expected a regular file under 4 MiB")
            data = stream.read(MAX_FILE + 1)
            if len(data) > MAX_FILE:
                raise DasyncError("UNSAFE_PATH", "File exceeds 4 MiB")
            return data, stat.S_IMODE(info.st_mode)
    except FileNotFoundError:
        return None, None


def observe(path: Path) -> dict:
    data, mode = snapshot(path)
    return {
        "hash": digest(data) if data is not None else None,
        "mode": mode,
    }


def atomic_write(path: Path, data: bytes, mode: int = 0o600):
    assert_safe(path)
    if os.name != "nt":
        with parent_fd(path, create=True) as directory:
            name = ".dasync-" + uuid.uuid4().hex
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode, dir_fd=directory)
            try:
                with os.fdopen(fd, "wb") as out:
                    out.write(data)
                    out.flush()
                    os.fchmod(out.fileno(), mode)
                    os.fsync(out.fileno())
                os.replace(name, path.name, src_dir_fd=directory, dst_dir_fd=directory)
                os.fsync(directory)
            finally:
                try:
                    os.unlink(name, dir_fd=directory)
                except FileNotFoundError:
                    pass
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    assert_safe(path)
    fd, temp = tempfile.mkstemp(prefix=".dasync-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(temp, mode)
        assert_safe(path)
        os.replace(temp, path)
        if os.name != "nt":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def safe_unlink(path: Path):
    assert_safe(path)
    if os.name != "nt":
        with parent_fd(path) as directory:
            os.unlink(path.name, dir_fd=directory)
            os.fsync(directory)
    else:
        path.unlink()

"""Measure source footprint, not model performance or exact tokenizer counts."""

import argparse
import json
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def measure(revision=None):
    if revision:
        revision = git("rev-parse", "--verify", revision + "^{commit}").decode().strip()
        names = git("ls-tree", "-r", "--name-only", revision, "--", "packages").decode().splitlines()

        def read(name):
            return git("show", f"{revision}:{name}")
    else:
        names = [p.relative_to(ROOT).as_posix() for p in (ROOT / "packages").rglob("manifest.yaml")]

        def read(name):
            return (ROOT / name).read_bytes()

    groups, entries = {}, {}
    for name in sorted(n for n in names if n.endswith("/manifest.yaml")):
        manifest = yaml.safe_load(read(name))
        folder = name.rsplit("/", 1)[0]
        entry = read(folder + "/" + manifest["entry"])
        content_bytes = sum(len(read(folder + "/" + file)) for file in manifest["files"])
        discovery = len((manifest["name"] + " " + manifest["description"]).encode())
        entries[manifest["id"]] = {
            "entry_bytes": len(entry),
            "content_bytes": content_bytes,
            "discovery_bytes": discovery,
            "files": len(manifest["files"]),
        }
        group = groups.setdefault(
            manifest["kind"],
            {"packages": 0, "entry_bytes": 0, "content_bytes": 0, "discovery_bytes": 0, "files": 0},
        )
        group["packages"] += 1
        for key, value in entries[manifest["id"]].items():
            group[key] += value
    return {
        "revision": revision or "working-tree",
        "groups": groups,
        "packages": entries,
        "notes": "UTF-8 bytes. Excludes manifest bytes, generated adapter text, and dependency copies. Not exact tokens, attention, latency or behavioral lift.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline")
    args = parser.parse_args()
    result = {"current": measure()}
    if args.baseline:
        result["baseline"] = measure(args.baseline)
    print(json.dumps(result, indent=2, sort_keys=True))

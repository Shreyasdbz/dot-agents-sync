"""Keyboard-driven selection; core resolution still owns dependencies and validation."""

from prompt_toolkit.shortcuts import checkboxlist_dialog

from .errors import DasyncError


def select(config, catalog):
    roots = catalog.roots(config)
    values = []
    for pid, package in sorted(catalog.packages.items()):
        m = package.manifest
        origin = roots.get(pid, "optional")
        suffix = " [private binding required]" if m.get("context", {}).get("sensitivity") == "private" else ""
        if m["kind"] == "Hook":
            suffix += " [executable approval required]"
        values.append((pid, f"{m['kind']}: {pid} ({origin}){suffix}"))
    chosen = checkboxlist_dialog(
        title="dasync — configure packages",
        text="Space toggles; arrows move; Tab selects OK/Cancel. Profiles expand below. Dependencies and provider effects appear in the final plan.",
        values=values,
        default_values=sorted(set(roots) - set(config["disabled"])),
    ).run()
    if chosen is None:
        raise DasyncError("CANCELLED", "No changes applied")
    # Preserve profiles but express removals as explicit tombstones.
    config["packages"] = sorted(set(chosen))
    config["disabled"] = sorted((set(config["disabled"]) | (set(roots) - set(chosen))) - set(chosen))
    return config

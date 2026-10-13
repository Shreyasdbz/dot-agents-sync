"""Pure Codex rendering and finite typed Markdown destinations."""

import json
import posixpath
import re
from dataclasses import dataclass
from urllib.parse import quote

import yaml

from .errors import DasyncError
from .io import canonical, digest
from .recipe_contracts import key_record, key_text
from .recipe_sources import check_paths, relative_path

ADAPTER_VERSION = "recipe-codex/1"
MAPPING_VERSION = 1


def native_name(key):
    readable = re.sub(r"[^a-z0-9-]", "-", key[1]).strip("-")[:28].rstrip("-")
    return readable + "-" + digest(canonical(key_record(key)))[:24]


def name_mapping(selected):
    mapping, names = {}, set()
    for key in sorted(selected):
        name = native_name(key)
        if name.casefold() in names or len(name) > 63:
            raise DasyncError(
                "NAME_COLLISION", "Stable native-name digest collision or provider length violation"
            )
        names.add(name.casefold())
        mapping[key_text(key)] = name
    return mapping


def file_mapping(selected, mapping):
    paths = {}
    for key, item in sorted(selected.items()):
        spec = item.spec
        if not spec["entry"].endswith((".md", ".markdown")):
            raise DasyncError("CONTENT_INVALID", "This adapter requires canonical Markdown entrypoints")
        if spec["kind"] not in ("Skill", "Template", "Context"):
            raise DasyncError(
                "CAPABILITY_UNSUPPORTED",
                "The experimental Codex adapter supports Skill, Template and public Context only",
            )
        missing = set(spec.get("required_capabilities", [])) - {"filesystem.read"}
        if missing:
            raise DasyncError(
                "CAPABILITY_UNSUPPORTED", "Essential capabilities cannot be preserved by this adapter"
            )
        if any(slot["required"] for slot in spec.get("slots", {}).values()):
            raise DasyncError(
                "CONTEXT_MISSING",
                "Required context slots need explicit binding in the later context milestone",
            )
        name = mapping[key_text(key)]
        prefix = ".agents/skills" if spec["kind"] == "Skill" else ".codex/dasync-references"
        for filename in item.files:
            native_file = "SKILL.md" if spec["kind"] == "Skill" and filename == spec["entry"] else filename
            paths[(key, filename)] = f"{prefix}/{name}/{native_file}"
    check_paths(paths.values())
    return paths


def _escaped(text, index):
    count = 0
    while index and text[index - 1] == "\\":
        count += 1
        index -= 1
    return count % 2 == 1


def _literal_mask(line):
    """Mark inline code and HTML comments so examples cannot become active references."""
    mask = [False] * len(line)
    for match in re.finditer(r"<!--.*?-->", line):
        mask[match.start() : match.end()] = [True] * (match.end() - match.start())
    index = 0
    while index < len(line):
        if line[index] == "`" and not _escaped(line, index):
            end = index
            while end < len(line) and line[end] == "`":
                end += 1
            marker = line[index:end]
            close = line.find(marker, end)
            while close >= 0 and (
                (close > 0 and line[close - 1] == "`")
                or (close + len(marker) < len(line) and line[close + len(marker)] == "`")
            ):
                close = line.find(marker, close + len(marker))
            if close >= 0:
                finish = close + len(marker)
                mask[index:finish] = [True] * (finish - index)
                index = finish
                continue
            index = end
        else:
            index += 1
    return mask


def render_references(text, translate):
    """Only inline Markdown links and reference definitions carry typed destinations.

    Fences, inline code, comments, escaped links and ordinary prose are literal.
    The experimental grammar requires a single-line label/destination; it is not a
    general Markdown parser or a template evaluator.
    """
    result, fence, comment = [], None, False
    for line in text.splitlines(keepends=True):
        mask = _literal_mask(line)
        if comment:
            close = line.find("-->")
            if close < 0:
                result.append(line)
                continue
            mask[: close + 3] = [True] * (close + 3)
            comment = False
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            if re.fullmatch(
                r" {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}[ \t]*(?:\r?\n)?", line
            ):
                fence = None
            result.append(line)
            continue
        if marker and not any(mask[: marker.end()]):
            fence = marker[1]
            result.append(line)
            continue
        if line.startswith(("    ", "\t")):
            result.append(line)
            continue
        start = 0
        while (begin := line.find("<!--", start)) >= 0:
            start = begin + 4
            if mask[begin]:
                continue
            close = line.find("-->", start)
            end = len(line) if close < 0 else close + 3
            mask[begin:end] = [True] * (end - begin)
            if close < 0:
                comment = True
                break
            start = end
        spans = []
        # Explicit destinations use no whitespace/parentheses; angle form is supported.
        for match in re.finditer(
            r"\[([^\[\]\n]*(?:\\.[^\[\]\n]*)*)\]\(<?(dasync:[^\s()<>]+)>?(?:\s+\"[^\"\n]*\")?\)", line
        ):
            start, end = match.span(2)
            if not _escaped(line, match.start()) and not any(mask[match.start() : match.end()]):
                spans.append((start, end, translate(match[2])))
        definition = re.match(r"^ {0,3}\[[^\]\n]+\]:\s*<?(dasync:[^\s<>]+)>?", line)
        if definition and not any(mask[: definition.end()]):
            spans.append((*definition.span(1), translate(definition[1])))
        for start, end, replacement in sorted(spans, reverse=True):
            line = line[:start] + replacement + line[end:]
        result.append(line)
    return "".join(result)


@dataclass(frozen=True)
class Artifact:
    relative: str
    content: bytes
    owner: tuple[str, str]
    contributors: tuple[tuple[str, str], ...]
    provider: str = "codex"
    mode: int = 0o644


def render(selected):
    mapping = name_mapping(selected)
    paths = file_mapping(selected, mapping)
    artifacts, decisions = [], []
    for key, item in sorted(selected.items()):
        spec = item.spec
        references = set()
        for invocation in spec.get("invocations", []):
            dependency = invocation["dependency"]
            target = (key[0], dependency)
            if dependency not in spec.get("requires", {}) or target not in selected:
                raise DasyncError(
                    "REFERENCE_INVALID", "Typed invocation must name a selected declared dependency"
                )
            if selected[target].spec["kind"] != "Skill":
                raise DasyncError("REFERENCE_INVALID", "Typed invocation target must be a Skill")
            references.add(target)

        for filename, data in sorted(item.files.items()):
            output_path = paths[(key, filename)]
            contributors = {key}

            def translate(destination):
                if destination.startswith("dasync:slot/"):
                    name = destination.removeprefix("dasync:slot/")
                    if name not in spec.get("slots", {}):
                        raise DasyncError("REFERENCE_INVALID", "Typed slot is not declared")
                    raise DasyncError(
                        "CONTEXT_MISSING", "A typed slot destination requires an explicit supported binding"
                    )
                if not destination.startswith("dasync:dependency/"):
                    raise DasyncError("REFERENCE_INVALID", "Unknown typed destination kind")
                local, _, resource = destination.removeprefix("dasync:dependency/").partition("/")
                local, separator, local_fragment = local.partition("#")
                resource, fragment_separator, fragment = resource.partition("#")
                fragment = fragment if fragment_separator else local_fragment if separator else ""
                if not re.fullmatch(r"[a-z][a-z0-9-]*(\.[a-z0-9-]+)*", local):
                    raise DasyncError("REFERENCE_INVALID", "Typed dependency identifier is malformed")
                target = (key[0], local)
                if local not in spec.get("requires", {}) or target not in selected:
                    raise DasyncError(
                        "REFERENCE_INVALID", "Typed destination must name a selected declared dependency"
                    )
                target_file = resource or selected[target].spec["entry"]
                relative_path(target_file)
                if (target, target_file) not in paths:
                    raise DasyncError("REFERENCE_INVALID", "Typed destination file is not declared")
                contributors.add(target)
                relative = posixpath.relpath(paths[(target, target_file)], posixpath.dirname(output_path))
                return quote(relative, safe="/.-_") + ("#" + quote(fragment, safe="-._~") if fragment else "")

            if filename.endswith((".md", ".markdown")):
                try:
                    text = data.decode("utf-8")
                except UnicodeError as exc:
                    raise DasyncError("CONTENT_INVALID", "Canonical Markdown must be UTF-8") from exc
                if filename == spec["entry"] and text.startswith("---"):
                    raise DasyncError(
                        "NATIVE_AUTHORSHIP", "Canonical entrypoints must not contain provider frontmatter"
                    )
                text = render_references(text, translate)
                if spec["kind"] == "Skill" and filename == spec["entry"]:
                    text = (
                        f"---\nname: {json.dumps(mapping[key_text(key)])}\ndescription: {json.dumps(spec['description'])}\n---\n\n"
                        + text
                    )
                    if references:
                        text += (
                            "\nDeclared skill invocations: "
                            + ", ".join("$" + mapping[key_text(target)] for target in sorted(references))
                            + "\n"
                        )
                    contributors |= references
                data = text.encode()
            artifacts.append(Artifact(output_path, data, key, tuple(sorted(contributors))))
        if spec["kind"] == "Skill" and spec.get("default_prompt"):
            prefix = posixpath.dirname(paths[(key, spec["entry"])])
            interface = {
                "interface": {
                    "display_name": spec["name"],
                    "default_prompt": "Use $" + mapping[key_text(key)] + " to " + spec["default_prompt"],
                }
            }
            artifacts.append(
                Artifact(
                    prefix + "/agents/openai.yaml",
                    yaml.safe_dump(interface, allow_unicode=True).encode(),
                    key,
                    (key,),
                )
            )
        decisions.append(
            {
                "item": key_record(key),
                "adapter": ADAPTER_VERSION,
                "essential_semantics": "preserved-format-only",
                "runtime_capabilities": "unverified",
                "optional_unverified": spec.get("optional_capabilities", []),
                "absent_optional_slots": sorted(
                    name for name, slot in spec.get("slots", {}).items() if not slot["required"]
                ),
            }
        )
    check_paths([artifact.relative for artifact in artifacts])
    if sum(len(artifact.content) for artifact in artifacts) > 128 * 1024 * 1024:
        raise DasyncError("OUTPUT_LIMIT", "Rendered output exceeds the resource limit")
    return artifacts, decisions, mapping

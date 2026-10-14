"""Bounded, source-qualified resolution with explicit roots and portable ownership."""

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from .errors import DasyncError
from .recipe_contracts import key_record, key_text, key_tuple


def dependency_key(item, reference):
    alias, separator, local_id = reference.partition("/")
    if not separator:
        return item.source_id, alias
    imported = item.imports.get(alias)
    if not imported:
        raise DasyncError(
            "REFERENCE_INVALID",
            "Dependency uses an undeclared import",
            details={"consumer": key_record(item.key), "import": alias},
        )
    return imported["source_id"], local_id


def selector(value, sources, registry):
    """Aliases are labels; neither iteration order nor source name chooses a winner."""
    qualifier, separator, local_id = value.partition("/")
    if not separator:
        local_id, qualifier = qualifier, None
    candidates = [
        (source_id, local_id)
        for source_id, source in sorted(sources.items())
        if local_id in source.items
        and (qualifier is None or qualifier in (source_id, registry[source_id]["alias"]))
    ]
    if len(candidates) != 1:
        raise DasyncError(
            "SELECTOR_AMBIGUOUS" if candidates else "ITEM_UNKNOWN",
            "Use an unambiguous registered alias/item or source UUID/item selector",
            details={"candidates": [key_record(key) for key in candidates]},
        )
    return candidates[0]


def compose(project, personal):
    sources = {}
    intents = [project]
    if project["inherit_user"] and personal:
        intents.append(personal)
    for intent in intents:
        for source in intent["sources"]:
            sid, pin = source["source_id"], source["pin"]
            if sid in sources and sources[sid] != pin:
                raise DasyncError(
                    "SNAPSHOT_CONFLICT",
                    "Personal and project pins disagree; align pins or disable inheritance",
                    details={"source_id": sid, "pins": sorted({sources[sid], pin})},
                )
            sources[sid] = pin
    return sources


def resolve(sources, intent, scope_kind, personal=None, denied=()):
    compose(intent, personal)
    roots = {key_tuple(key): [{"kind": "direct"}] for key in intent["roots"]}
    inherited = set()
    if scope_kind == "project" and intent["inherit_user"] and personal:
        for record in personal["roots"]:
            key = key_tuple(record)
            if key not in sources_items(sources):
                raise DasyncError(
                    "ITEM_UNKNOWN",
                    "Inherited root is absent from its accepted snapshot",
                    details={"item": record},
                )
            item = sources[key[0]].items[key[1]]
            if (
                item.spec["kind"] == "Hook"
                or item.spec.get("context", {}).get("access", "inherit") != "inherit"
            ):
                continue
            roots.setdefault(key, []).append({"kind": "inherited"})
            inherited.add(key)
    disabled = {key_tuple(key) for key in intent["disabled"]}
    if personal and intent["inherit_user"]:
        personal_disabled = {key_tuple(key) for key in personal["disabled"]}
        conflicts = personal_disabled & {key_tuple(key) for key in intent["roots"]}
        if conflicts:
            raise DasyncError(
                "SELECTION_CONFLICT",
                "Personal disable conflicts with a direct project root; reconcile intent or disable inheritance",
                details={"items": [key_record(key) for key in sorted(conflicts)]},
            )
        disabled |= personal_disabled
    roots = {key: reasons for key, reasons in roots.items() if key not in disabled}
    selected, reasons, edges, visiting = {}, {}, [], []

    def visit(key, reason, root):
        if key in disabled:
            raise DasyncError(
                "DEPENDENCY_DISABLED",
                "A required item is explicitly disabled",
                details={
                    "item": key_record(key),
                    "root": key_record(root),
                    "chain": [key_record(k) for k in visiting],
                },
            )
        source = sources.get(key[0])
        item = source.items.get(key[1]) if source else None
        if item is None:
            raise DasyncError(
                "ITEM_UNKNOWN",
                "A required item is absent from the accepted source snapshot",
                details={"item": key_record(key), "root": key_record(root)},
            )
        if key[0] in denied or key_text(key) in denied:
            raise DasyncError(
                "AUTHORITY_DENIED",
                "Current authority denies managed activation",
                details={"item": key_record(key)},
            )
        spec = item.spec
        if scope_kind not in spec["scopes"]:
            raise DasyncError(
                "SCOPE_FORBIDDEN", "Item does not permit this scope", details={"item": key_record(key)}
            )
        context = spec.get("context", {})
        if context.get("sensitivity") == "private" or context.get("access") == "never":
            raise DasyncError(
                "CONTEXT_DENIED", "Private/never context use requires the later context milestone"
            )
        if context.get("access") == "explicit" and key not in {key_tuple(k) for k in intent["roots"]}:
            raise DasyncError("CONTEXT_DENIED", "Context requires an explicit root in this scope")
        why = reasons.setdefault(key, [])
        if reason not in why:
            why.append(reason)
        if key in visiting:
            raise DasyncError(
                "DEPENDENCY_CYCLE",
                "Qualified dependency cycle",
                details={"cycle": [key_record(k) for k in visiting[visiting.index(key) :] + [key]]},
            )
        if key in selected:
            return
        if len(visiting) >= 64 or len(selected) + len(visiting) >= 512:
            raise DasyncError("GRAPH_LIMIT", "Recipe graph exceeds depth or item limits")
        visiting.append(key)
        for local_id, constraint in sorted(spec.get("requires", {}).items()):
            dependency = dependency_key(item, local_id)
            imported = sources.get(dependency[0])
            if imported is None:
                raise DasyncError(
                    "SOURCE_UNBOUND",
                    "Imported dependency needs an explicitly bound accepted snapshot",
                    details={
                        "source_id": dependency[0],
                        "consumer": key_record(key),
                        "root": key_record(root),
                    },
                )
            target = imported.items.get(dependency[1])
            if target and Version(target.spec["version"]) not in SpecifierSet(constraint):
                raise DasyncError(
                    "VERSION_CONFLICT",
                    "Dependency version violates the declared constraint",
                    details={
                        "consumer": key_record(key),
                        "dependency": key_record(dependency),
                        "root": key_record(root),
                    },
                )
            edges.append([key_record(key), key_record(dependency)])
            visit(dependency, {"kind": "dependency", "consumer": key_record(key)}, root)
        visiting.pop()
        selected[key] = item

    for root, why in sorted(roots.items()):
        for reason in why:
            visit(root, reason, root)
    graph = {
        "items": [
            {
                **key_record(key),
                "version": item.spec["version"],
                "kind": item.spec["kind"],
                "digest": item.digest,
                "reasons": sorted(reasons[key], key=str),
            }
            for key, item in sorted(selected.items())
        ],
        "roots": [key_record(key) for key in sorted(roots)],
        "edges": sorted(edges, key=str),
        "inherited": [key_record(key) for key in sorted(inherited & selected.keys())],
        "resolver_inherits_personal": scope_kind == "project" and intent["inherit_user"],
        "native_global_visibility": "unverified; disabling inheritance does not hide global provider files",
    }
    return selected, graph


def sources_items(sources):
    return {(sid, local_id) for sid, source in sources.items() for local_id in source.items}


def project_lock(sources, intent):
    # Resolve ONLY project-owned intent; no local origins, aliases, grants or native assignments.
    owned = {source["source_id"] for source in intent["sources"]}
    _, graph = resolve(
        {sid: source for sid, source in sources.items() if sid in owned},
        {**intent, "inherit_user": False},
        "project",
    )
    return {
        "format": 1,
        "portable": False,
        "sources": sorted(intent["sources"], key=lambda s: s["source_id"]),
        "roots": graph["roots"],
        "items": [
            {k: value for k, value in item.items() if k not in ("reasons", "kind")} for item in graph["items"]
        ],
        "edges": graph["edges"],
    }

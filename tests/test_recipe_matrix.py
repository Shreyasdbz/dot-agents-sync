"""Independent oracles, exhaustive small spaces and repeatable generated recipes."""

import copy
import itertools
import tempfile
from pathlib import Path

import pytest
from dasync.config import Environment, Scope
from dasync.engine import Engine
from dasync.errors import DasyncError
from dasync.io import canonical
from dasync.recipe_adapters import name_mapping, render_references
from dasync.recipe_contracts import key_record, key_tuple
from dasync.recipe_engine import initial, registry
from dasync.recipe_resolver import compose, resolve
from dasync.recipe_sources import Item, RecipeSnapshot, Snapshots, check_paths
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule
from test_recipes import A, B, apply, item, recipe

DETERMINISTIC = settings(max_examples=400, derandomize=True, database=None, deadline=None)


def snapshot(sid, adjacency):
    files = {}
    paths = []
    for node, dependencies in enumerate(adjacency):
        spec = item(f"skill.n{node}", requires={f"skill.n{other}": ">=1" for other in dependencies})
        name = f"items/{node}/item.yaml"
        paths.append(name)
        files[name] = canonical(spec)
        files[f"items/{node}/BODY.md"] = b"# Synthetic\n"
    files["recipe.yaml"] = canonical(
        {
            "format": 1,
            "source_id": sid,
            "name": "synthetic",
            "description": "Synthetic matrix",
            "requires_engine": ">=0.1.1,<1",
            "required_features": [],
            "items": paths,
            "imports": {},
        }
    )
    return RecipeSnapshot(files)


def intent(source, roots=(), disabled=()):
    return {
        **initial(),
        "inherit_user": False,
        "sources": [{"source_id": source.source_id, "pin": source.pin}],
        "roots": [key_record((source.source_id, f"skill.n{n}")) for n in roots],
        "disabled": [key_record((source.source_id, f"skill.n{n}")) for n in disabled],
    }


def oracle(adjacency, roots, disabled):
    """Breadth-first reachability, then Kahn elimination; independent of the DFS resolver."""
    reachable, pending = set(), set(roots) - set(disabled)
    while pending:
        node = pending.pop()
        if node in reachable:
            continue
        reachable.add(node)
        pending.update(set(adjacency[node]) - reachable)
    if reachable & set(disabled):
        return reachable, "DEPENDENCY_DISABLED"
    remaining = {node: set(adjacency[node]) & reachable for node in reachable}
    while remaining:
        leaves = {node for node, outgoing in remaining.items() if not outgoing}
        if not leaves:
            return reachable, "DEPENDENCY_CYCLE"
        remaining = {node: outgoing - leaves for node, outgoing in remaining.items() if node not in leaves}
    return reachable, None


@pytest.mark.parametrize("edge_mask", range(64))
def test_exhaustive_three_node_graphs_roots_and_disables(edge_mask):
    """64 directed graphs × 8 root sets × 8 disable sets = 4,096 deterministic cases."""
    edges = [(a, b) for a in range(3) for b in range(3) if a != b]
    adjacency = [set() for _ in range(3)]
    for bit, (a, b) in enumerate(edges):
        if edge_mask & (1 << bit):
            adjacency[a].add(b)
    source = snapshot(A, adjacency)
    for root_mask, disable_mask in itertools.product(range(8), repeat=2):
        roots = {n for n in range(3) if root_mask & (1 << n)}
        disabled = {n for n in range(3) if disable_mask & (1 << n)}
        reachable, expected = oracle(adjacency, roots, disabled)
        try:
            selected, graph = resolve({A: source}, intent(source, roots, disabled), "project")
        except DasyncError as exc:
            assert expected is not None
            # Where both exist, either causal blocker is valid; a successful graph is not.
            assert exc.code in ("DEPENDENCY_DISABLED", "DEPENDENCY_CYCLE")
            continue
        assert expected is None
        assert {int(key[1].removeprefix("skill.n")) for key in selected} == reachable
        assert {(key_tuple(a)[1], key_tuple(b)[1]) for a, b in graph["edges"]} == {
            (f"skill.n{a}", f"skill.n{b}") for a in reachable for b in adjacency[a]
        }
        for record in graph["items"]:
            n = int(record["item_id"].removeprefix("skill.n"))
            assert any(reason["kind"] == "direct" for reason in record["reasons"]) == (n in roots - disabled)
            consumers = {
                reason["consumer"]["item_id"]
                for reason in record["reasons"]
                if reason["kind"] == "dependency"
            }
            assert consumers == {f"skill.n{parent}" for parent in reachable if n in adjacency[parent]}


@st.composite
def graph_cases(draw):
    count = draw(st.integers(1, 8))
    edge_set = draw(
        st.sets(st.tuples(st.integers(0, count - 1), st.integers(0, count - 1)), max_size=count * count)
    )
    adjacency = [{b for a, b in edge_set if a == n} for n in range(count)]
    roots = draw(st.sets(st.integers(0, count - 1)))
    disabled = draw(st.sets(st.integers(0, count - 1)))
    return adjacency, roots, disabled


@DETERMINISTIC
@given(graph_cases())
def test_generated_graph_oracle_and_source_isolation(case):
    adjacency, roots, disabled = case
    source = snapshot(A, adjacency)
    other = snapshot(B, [set() for _ in adjacency])
    expected, blocker = oracle(adjacency, roots, disabled)
    config = intent(source, roots, disabled)
    config["sources"].append({"source_id": B, "pin": other.pin})
    config["roots"].append(key_record((B, "skill.n0")))
    try:
        selected, graph = resolve({A: source, B: other}, config, "project")
    except DasyncError as exc:
        assert blocker and exc.code in ("DEPENDENCY_CYCLE", "DEPENDENCY_DISABLED")
        return
    assert blocker is None
    assert set(selected) == {(A, f"skill.n{n}") for n in expected} | {(B, "skill.n0")}
    assert all(a["source_id"] == b["source_id"] for a, b in graph["edges"])
    reordered = copy.deepcopy(config)
    reordered["sources"].reverse()
    reordered["roots"].reverse()
    reordered["disabled"].reverse()
    assert resolve({B: other, A: source}, reordered, "project")[1] == graph
    assert name_mapping(dict(reversed(list(selected.items())))) == name_mapping(selected)


@pytest.mark.parametrize("project_choices", list(itertools.product(range(3), repeat=2)))
@pytest.mark.parametrize("personal_choices", list(itertools.product(range(3), repeat=2)))
@pytest.mark.parametrize("inherit", [False, True])
def test_exhaustive_two_source_pin_composition(project_choices, personal_choices, inherit):
    """Absent/old/new pin × two sources × two scopes × inheritance = 162 cases."""

    def config(choices):
        return {
            **initial(),
            "sources": [
                {"source_id": sid, "pin": "sha256:" + str(choice) * 64}
                for sid, choice in zip((A, B), choices)
                if choice
            ],
        }

    project, personal = config(project_choices), config(personal_choices)
    project["inherit_user"] = inherit
    conflict = inherit and any(a and b and a != b for a, b in zip(project_choices, personal_choices))
    if conflict:
        with pytest.raises(DasyncError) as rejected:
            compose(project, personal)
        assert rejected.value.code == "SNAPSHOT_CONFLICT"
    else:
        expected = {
            sid: "sha256:" + str(a or (b if inherit else 0)) * 64
            for sid, a, b in zip((A, B), project_choices, personal_choices)
            if a or (inherit and b)
        }
        assert compose(project, personal) == expected


@DETERMINISTIC
@given(
    st.lists(
        st.from_regex(r"skill\.[a-z][a-z0-9.-]{0,40}", fullmatch=True), min_size=1, max_size=60, unique=True
    )
)
def test_generated_native_names_and_permutations(ids):
    keys = [(sid, local_id) for sid in (A, B) for local_id in ids]
    selected = {key: Item(key[0], item(key[1]), {"BODY.md": b"# Synthetic"}, "a" * 64) for key in keys}
    mapping = name_mapping(selected)
    assert len(mapping) == len(set(mapping.values())) == len(keys)
    assert all(len(name) <= 63 and name.isascii() for name in mapping.values())
    assert mapping == name_mapping(dict(reversed(list(selected.items()))))


@pytest.mark.parametrize(
    "wrapper",
    [
        "`{}`",
        "`` {} ``",
        "```markdown\n{}\n```\n",
        "~~~\n{}\n~~~\n",
        "    {}",
        "\t{}",
        "<!-- {} -->",
        "<!--\n{}\n-->\n",
        r"\{}",
    ],
)
def test_reference_literal_wrappers_are_never_resolved(wrapper):
    text = wrapper.format("[literal](dasync:dependency/skill.missing)")

    def forbidden(_):
        pytest.fail("Literal content was treated as an active reference")

    assert render_references(text, forbidden) == text


@pytest.mark.parametrize(
    "paths",
    [
        ["A/x", "a/y"],
        ["x", "x/y"],
        ["e\u0301.md", "é.md"],
        ["dir/e\u0301/x", "dir/é/y"],
        ["CON.txt"],
        ["x."],
        ["x "],
    ],
)
def test_cross_platform_collision_matrix(paths):
    with pytest.raises(DasyncError):
        check_paths(paths)


@pytest.mark.parametrize("isolated", [510, 511])
def test_graph_budget_counts_nodes_currently_in_traversal(isolated):
    first = snapshot(A, [set() for _ in range(isolated)])
    second = snapshot(B, [{1}, set()])
    config = intent(first, range(isolated))
    config["sources"].append({"source_id": B, "pin": second.pin})
    config["roots"].append(key_record((B, "skill.n0")))
    if isolated == 510:
        selected, _ = resolve({A: first, B: second}, config, "project")
        assert len(selected) == 512
    else:
        with pytest.raises(DasyncError) as rejected:
            resolve({A: first, B: second}, config, "project")
        assert rejected.value.code == "GRAPH_LIMIT"


@pytest.mark.parametrize("kind,length", list(itertools.product(("`", "~"), (3, 4, 7))))
def test_fence_closers_with_info_cannot_activate_example_links(kind, length):
    marker = kind * length
    text = f"{marker}markdown\n{marker}still-example\n[x](dasync:dependency/skill.missing)\n{marker}\n"

    def forbidden(_):
        pytest.fail("Fence info accidentally ended a literal example")

    assert render_references(text, forbidden) == text


def test_comment_boundaries_preserve_literals_but_resolve_visible_links():
    text = "[a](dasync:dependency/skill.a) <!--\n```not-a-fence\n--> [b](dasync:dependency/skill.b)\n"
    seen = []
    output = render_references(text, lambda url: seen.append(url) or "target")
    assert seen == ["dasync:dependency/skill.a", "dasync:dependency/skill.b"]
    assert "```not-a-fence" in output and output.count("(target)") == 2


@pytest.mark.parametrize(
    "scope,sensitivity,access,scopes,direct",
    list(
        itertools.product(
            ("user", "project"),
            ("public", "private"),
            ("inherit", "explicit", "never"),
            (["user"], ["project"], ["user", "project"]),
            (False, True),
        )
    ),
)
def test_context_scope_access_and_directness_matrix(scope, sensitivity, access, scopes, direct):
    spec = item(
        "context.workspace",
        kind="Context",
        scopes=scopes,
        context={"sensitivity": sensitivity, "access": access},
    )
    skill = item("skill.review", requires={"context.workspace": ">=1"})
    files = {
        "recipe.yaml": canonical(
            {
                "format": 1,
                "source_id": A,
                "name": "synthetic",
                "description": "Synthetic",
                "requires_engine": ">=0.1.1,<1",
                "required_features": [],
                "imports": {},
                "items": ["context/item.yaml", "skill/item.yaml"],
            }
        ),
        "context/item.yaml": canonical(spec),
        "context/BODY.md": b"PRIVATE_SENTINEL" if sensitivity == "private" else b"Public synthetic context",
        "skill/item.yaml": canonical(skill),
        "skill/BODY.md": b"# Synthetic review",
    }
    source = RecipeSnapshot(files)
    config = {
        **initial(),
        "sources": [{"source_id": A, "pin": source.pin}],
        "roots": [
            key_record((A, "skill.review")),
            *([key_record((A, "context.workspace"))] if direct else []),
        ],
    }
    expected = (
        "SCOPE_FORBIDDEN"
        if scope not in scopes
        else "CONTEXT_DENIED"
        if (sensitivity == "private" or access == "never" or (access == "explicit" and not direct))
        else None
    )
    if expected:
        with pytest.raises(DasyncError) as rejected:
            resolve({A: source}, config, scope)
        assert rejected.value.code == expected and "PRIVATE_SENTINEL" not in str(rejected.value)
    else:
        selected, _ = resolve({A: source}, config, scope)
        assert len(selected) == 2


class RecipeLifecycle(RuleBasedStateMachine):
    """Real Engine transitions compared with a tiny independent direct-root model."""

    def __init__(self):
        super().__init__()
        self.temp = tempfile.TemporaryDirectory(prefix="dasync-sequence-")
        root = Path(self.temp.name)
        home, project = root / "home", root / "project"
        home.mkdir()
        project.mkdir()
        env = Environment(home, home / "config/config.yaml", home / "state", home / "cache")
        self.engine = Engine(env, Scope.get(env, "project", str(project)))
        self.source = recipe(root / "source", specs=[item(f"skill.n{n}") for n in range(4)])
        self.alias, self.roots = "source", set()
        self.candidate = Snapshots(env.cache).prepare(self.source)["candidate"]
        apply(
            self.engine,
            {
                "operation": "recipe.configure",
                "registrations": [{"candidate": self.candidate, "alias": self.alias}],
                "trust_source": True,
            },
        )

    @rule(node=st.integers(0, 3), select=st.booleans())
    def select_or_remove(self, node, select):
        key = f"{self.alias}/skill.n{node}"
        request = {"operation": "recipe.configure", "enable" if select else "remove": [key]}
        apply(self.engine, request)
        self.roots.add(node) if select else self.roots.discard(node)

    @rule(alias=st.sampled_from(["source", "renamed", "personal", "team"]))
    def rename(self, alias):
        apply(
            self.engine,
            {
                "operation": "recipe.configure",
                "registrations": [{"candidate": self.candidate, "alias": alias}],
                "trust_source": True,
            },
        )
        self.alias = alias

    @rule()
    def cancelled_proposal(self):
        before = self.engine.scope.config.read_bytes(), registry(self.engine)
        self.engine.build({"operation": "recipe.configure", "select_sources": [self.alias]})
        assert before == (self.engine.scope.config.read_bytes(), registry(self.engine))

    @rule()
    def sync(self):
        plan, _ = self.engine.build({"operation": "recipe.sync"})
        assert self.engine.apply(plan)["changed"] is False

    @rule(node=st.integers(0, 3))
    def edit_source_snapshot(self, node):
        body = self.source / "items" / str(node) / "BODY.md"
        body.write_text(body.read_text() + "\nAn explicit snapshot revision.\n")
        self.candidate = Snapshots(self.engine.env.cache).prepare(self.source)["candidate"]
        apply(
            self.engine,
            {
                "operation": "recipe.configure",
                "registrations": [{"candidate": self.candidate, "alias": self.alias}],
                "trust_source": True,
            },
        )

    @invariant()
    def receipt_matches_model_and_is_idempotent(self):
        plan, _ = self.engine.build({"operation": "recipe.sync"})
        assert {int(row["item_id"].removeprefix("skill.n")) for row in plan["graph"]["items"]} == self.roots
        assert all(op["action"] == "keep" for op in plan["operations"])
        assert not self.engine.state.pending()
        assert len(plan["mapping"]) == len(set(plan["mapping"].values()))

    def teardown(self):
        self.temp.cleanup()


TestRecipeLifecycle = RecipeLifecycle.TestCase
TestRecipeLifecycle.settings = settings(
    max_examples=20, stateful_step_count=35, derandomize=True, database=None, deadline=None
)

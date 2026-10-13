"""Draft/CLI parity and actual Textual keyboard, pointer, modal and resize journeys."""

import asyncio
import copy
import json
import sys
import threading
from pathlib import Path

import pytest
from dasync.config import Environment, Scope
from dasync.engine import Engine
from dasync.errors import DasyncError
from dasync.io import canonical
from dasync.recipe_engine import registry
from dasync.recipe_session import RecipeSession, display_text
from dasync.recipe_sources import Snapshots
from dasync.recipe_tui import Confirm, Help, Inspect, RecipeApp, RestoreDialog, SourceDialog
from test_recipes import A, B, apply, item, recipe
from textual.widgets import Button, Checkbox, DataTable, Input, Static, TabbedContent


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    home, project = tmp_path / "home", tmp_path / "project"
    home.mkdir()
    project.mkdir()
    env = Environment(home, home / "config/config.yaml", home / "state", home / "cache")
    engine = Engine(env, Scope.get(env, "project", str(project)))
    a = recipe(
        tmp_path / "a",
        A,
        specs=[
            item(
                requires={"template.notes": ">=1"},
                optional_capabilities=["network.fetch"],
                slots={
                    "workspace": {
                        "required": False,
                        "cardinality": "one",
                        "contract_id": A,
                        "version": ">=1",
                        "content_format": "markdown",
                    }
                },
            ),
            item("template.notes", kind="Template"),
        ],
    )
    b = recipe(tmp_path / "b", B)
    cache = Snapshots(env.cache)
    candidates = cache.prepare(a), cache.prepare(b)
    apply(
        engine,
        {
            "operation": "recipe.configure",
            "registrations": [
                {"candidate": record["candidate"], "alias": alias}
                for record, alias in zip(candidates, ("studio", "personal"))
            ],
            "trust_source": True,
        },
    )
    return engine, a, b


def test_session_drafts_and_machine_requests_are_identical(workspace):
    engine, *_ = workspace
    session = RecipeSession(engine)
    before = engine.scope.config.read_bytes(), registry(engine), engine.state.head(engine.scope.key)
    session.toggle((A, "skill.review"))
    session.toggle((B, "skill.review"))
    assert session.dirty
    assert next(row for row in session.rows() if row["id"] == "template.notes")["status"] == "Dependency"
    assert "Needed by studio/skill.review" in session.detail((A, "template.notes"))[0]
    assert before == (engine.scope.config.read_bytes(), registry(engine), engine.state.head(engine.scope.key))
    plan = session.review()
    machine, _ = engine.build(session.request())
    assert canonical(plan) == canonical(machine)
    result = session.apply()
    assert result["changed"] and not session.dirty and session.plan is None
    assert engine.status()["pending_changes"] == 0


def test_modified_draft_or_external_changes_cannot_apply_old_review(workspace):
    engine, *_ = workspace
    session = RecipeSession(engine)
    session.toggle((A, "skill.review"))
    session.review()
    session.toggle((B, "skill.review"))
    with pytest.raises(DasyncError) as rejected:
        session.apply()
    assert rejected.value.code == "PLAN_REQUIRED"
    plan = session.review()
    target = Path(next(op["path"] for op in plan["operations"] if op["path"].endswith("SKILL.md")))
    target.parent.mkdir(parents=True)
    target.write_text("unmanaged original")
    with pytest.raises(DasyncError) as rejected:
        session.apply()
    assert rejected.value.code == "UNMANAGED_COLLISION" and session.plan is None
    assert target.read_text() == "unmanaged original"
    target.unlink()
    session.review()
    with pytest.raises(DasyncError) as rejected:
        session.review(request={"operation": "recipe.restore", "receipt": "unknown"})
    assert rejected.value.code == "RECEIPT_UNKNOWN" and session.plan is None
    with pytest.raises(DasyncError) as rejected:
        session.apply()
    assert rejected.value.code == "PLAN_REQUIRED"


def test_safe_plan_export_is_machine_applicable_and_never_overwrites(workspace, tmp_path):
    engine, *_ = workspace
    session = RecipeSession(engine)
    session.toggle((A, "skill.review"))
    session.review()
    path = tmp_path / "reviewed.json"
    session.save_plan(path)
    value = json.loads(path.read_text())
    assert value["protocol"] == 1 and engine.apply(value["result"])["changed"]
    original = path.read_bytes()
    with pytest.raises(DasyncError) as rejected:
        session.save_plan(path)
    assert rejected.value.code == "UNMANAGED_COLLISION" and path.read_bytes() == original


def test_private_body_names_and_controls_are_not_displayed(workspace, tmp_path):
    engine, *_ = workspace
    c = "33333333-3333-4333-8333-333333333333"
    private = recipe(
        tmp_path / "private",
        c,
        specs=[
            item(
                "context.secret",
                kind="Context",
                name="PRIVATE_SENTINEL",
                description="PRIVATE_SENTINEL",
                context={"sensitivity": "private", "access": "explicit"},
            )
        ],
        body="PRIVATE_SENTINEL",
    )
    prepared = Snapshots(engine.env.cache).prepare(private)
    session = RecipeSession(engine)
    with pytest.raises(DasyncError):
        session.stage(prepared["candidate"], "private", trusted=False)
    session.stage(prepared["candidate"], "private", trusted=True)
    assert "PRIVATE_SENTINEL" not in str(session.rows())
    assert "PRIVATE_SENTINEL" not in str(session.detail((c, "context.secret")))
    assert session.rows("PRIVATE_SENTINEL") == []
    session.toggle((c, "context.secret"))
    with pytest.raises(DasyncError) as rejected:
        session.review()
    assert rejected.value.code == "CONTEXT_DENIED"
    assert c not in registry(engine)["sources"]
    assert "\x1b" not in display_text("\x1b]0;inert\x07\u202e")


@pytest.mark.parametrize("size", [(140, 42), (100, 32), (80, 24), (64, 20)])
def test_real_widget_browse_search_toggle_and_resize(workspace, size):
    engine, *_ = workspace

    async def journey():
        app = RecipeApp(engine)
        async with app.run_test(size=size) as pilot:
            await pilot.pause()
            assert app.query_one("#items", DataTable).row_count == 3
            await pilot.press("space")
            assert app.session.dirty and len(app.session.roots) == 1
            await pilot.press("/")
            app.query_one("#search", Input).value = "personal"
            await pilot.pause()
            assert app.query_one("#items", DataTable).row_count == 1
            app.query_one("#search", Input).value = "no matches"
            await pilot.pause()
            assert app.query_one("#items", DataTable).row_count == 0
            assert "No matches" in str(app.query_one("#detail-info", Static).render())
            app.query_one("#search", Input).value = ""
            await pilot.pause()
            await pilot.resize_terminal(70, 22)
            await pilot.pause()
            assert app.screen.has_class("narrow")
            assert app.query_one("#items", DataTable).size.height > 0
            assert not app.query_one("#detail").display
            await pilot.resize_terminal(140, 42)
            await pilot.pause()
            assert not app.screen.has_class("narrow")
            await pilot.press("f1")
            await pilot.pause()
            await pilot.press("escape")
            app.action_theme()
            assert app.theme == "catppuccin-latte"
        assert engine.status()["pending_changes"] == 0

    asyncio.run(journey())


def test_keyboard_enter_full_identity_and_dirty_exit_cancel(workspace):
    engine, *_ = workspace

    async def journey():
        app = RecipeApp(engine)
        async with app.run_test(size=(100, 32)) as pilot:
            await pilot.press("enter")
            await pilot.pause()
            assert len(app.session.roots) == 1  # Enter cannot toggle twice via RowSelected + binding.
            await pilot.press("f4")
            assert isinstance(app.screen, Inspect)
            await pilot.press("escape")
            await pilot.press("f1")
            assert isinstance(app.screen, Help)
            await pilot.press("f1")
            assert not isinstance(app.screen, Help)
            await pilot.press("/")
            await pilot.press("q", "r")
            assert app.query_one("#search", Input).value == "qr"
            assert not app._exit and app.session.plan is None
            await pilot.press("f10")
            assert isinstance(app.screen, Confirm)
            await pilot.press("escape")
            assert not app._exit and app.session.dirty
            assert engine.status()["pending_changes"] == 0

    asyncio.run(journey())


@pytest.mark.parametrize("before", [False, True])
def test_restore_dialog_reviews_exact_receipt_without_applying(workspace, before):
    engine, *_ = workspace
    _, first = apply(engine, {"operation": "recipe.configure", "enable": ["studio/skill.review"]})
    apply(engine, {"operation": "recipe.configure", "remove": ["studio/skill.review"]})
    head = engine.state.head(engine.scope.key)["id"]

    async def journey():
        app = RecipeApp(engine)
        async with app.run_test(size=(100, 32)) as pilot:
            app.action_restore()
            await pilot.pause()
            assert isinstance(app.screen, RestoreDialog)
            app.screen.query_one("#restore-receipt", Input).value = first["receipt"]
            if before:
                await pilot.click("#restore-before")
            await pilot.click("#review-restore")
            for _ in range(100):
                await pilot.pause(0.02)
                if app.session.plan and not app.busy:
                    break
            assert app.session.plan["request"] == {
                "operation": "recipe.restore",
                "receipt": first["receipt"],
                "before_receipt": before,
            }
            await pilot.pause()
            assert app.query_one("#workspace", TabbedContent).active == "review-tab"
            assert engine.state.head(engine.scope.key)["id"] == head

    asyncio.run(journey())


def test_registered_pin_choice_replaces_staged_update_and_bad_alias_is_atomic(workspace):
    engine, source, _ = workspace
    session = RecipeSession(engine)
    old_pin = session.sources[A].pin
    (source / "items/0/BODY.md").write_text("# Updated source")
    candidate = Snapshots(engine.env.cache).prepare(source)["candidate"]
    before = copy.deepcopy(registry(engine))
    with pytest.raises(DasyncError) as rejected:
        session.stage(candidate, "personal", trusted=True)
    assert rejected.value.code == "ALIAS_CONFLICT"
    assert not session.pending and not session.dirty and registry(engine) == before
    session.stage(candidate, "studio", trusted=True)
    assert session.sources[A].pin != old_pin
    session.bind(A, old_pin)
    assert A not in session.pending and session.sources[A].pin == old_pin
    assert "registrations" not in session.request()
    assert registry(engine) == before


def test_tui_drift_requires_separate_replacement_review_and_retains_original(workspace):
    engine, *_ = workspace
    plan, _ = apply(engine, {"operation": "recipe.configure", "enable": ["studio/skill.review"]})
    path = Path(next(op["path"] for op in plan["operations"] if op["path"].endswith("SKILL.md")))
    path.write_text("My independent edit")

    async def journey():
        app = RecipeApp(engine)
        async with app.run_test(size=(120, 36)) as pilot:
            await app.action_review()
            assert app.session.plan is None and path.read_text() == "My independent edit"
            assert "DRIFT" in str(app.query_one("#message", Static).render())
            app.query_one("#overwrite", Checkbox).value = True
            await pilot.pause()
            await app.action_review()
            assert app.session.plan["request"]["conflict"] == "overwrite"
            app.query_one("#overwrite", Checkbox).value = False
            await pilot.pause()
            assert app.session.plan is None and app.query_one("#effects", DataTable).row_count == 0
            app.query_one("#overwrite", Checkbox).value = True
            await pilot.pause()
            await app.action_review()
            app.action_apply()
            await pilot.pause()
            await pilot.click("#confirm")
            for _ in range(100):
                await pilot.pause(0.02)
                if app.session.last_result and not app.busy:
                    break
            assert app.session.last_result["changed"]
            receipt = app.session.last_result["receipt"]
            restore, _ = engine.build(
                {"operation": "recipe.restore", "receipt": receipt, "before_receipt": True}
            )
            engine.apply(restore)
            assert path.read_text() == "My independent edit"

    asyncio.run(journey())


def test_tui_recovery_is_confirmed_and_uses_shared_journal(workspace):
    engine, *_ = workspace
    head = engine.state.head(engine.scope.key)["id"]
    plan, _ = engine.build({"operation": "recipe.configure", "enable": ["studio/skill.review"]})

    def interrupted(stage, index):
        if stage == "after_write" and index == 0:
            raise KeyboardInterrupt("Synthetic interrupted write")

    with pytest.raises(KeyboardInterrupt):
        engine.apply(plan, interrupted)
    assert engine.state.pending()

    async def journey():
        app = RecipeApp(engine)
        async with app.run_test(size=(120, 36)) as pilot:
            await app.action_health()
            await pilot.pause()
            assert app.query_one("#workspace", TabbedContent).active == "health-tab"
            assert "Recovery journals: 1" in str(app.query_one("#health-info", Static).render())
            app.action_recover()
            await pilot.pause()
            await pilot.click("#cancel")
            assert engine.state.pending()
            app.action_recover()
            await pilot.pause()
            await pilot.click("#confirm")
            for _ in range(100):
                await pilot.pause(0.02)
                if not engine.state.pending() and not app.busy:
                    break
            assert not engine.state.pending() and engine.state.head(engine.scope.key)["id"] == head
            assert engine.status()["pending_changes"] == 0

    asyncio.run(journey())


def test_pointer_review_cancel_then_confirm_apply(workspace):
    engine, *_ = workspace

    async def journey():
        app = RecipeApp(engine)
        async with app.run_test(size=(140, 42)) as pilot:
            app.session.toggle((A, "skill.review"))
            app.session.toggle((B, "skill.review"))
            app.refresh_catalog()
            await pilot.click("#review")
            for _ in range(80):
                await pilot.pause(0.02)
                if app.session.plan and not app.busy:
                    break
            assert app.session.plan and app.query_one("#effects", DataTable).row_count > 0
            assert app.query_one("#workspace", TabbedContent).active == "review-tab"
            notes = str(app.query_one("#review-notes", Static).render())
            assert "network.fetch" in notes and "unbound optional slots: workspace" in notes
            assert any(
                "studio/skill.review" in str(value)
                for row in app.query_one("#effects", DataTable).rows
                for value in app.query_one("#effects", DataTable).get_row(row)
            )
            before = engine.scope.config.read_bytes()
            await pilot.click("#apply")
            assert isinstance(app.screen, Confirm)
            await pilot.click("#cancel")
            assert engine.scope.config.read_bytes() == before
            await pilot.click("#apply")
            await pilot.click("#confirm")
            for _ in range(100):
                await pilot.pause(0.02)
                if app.session.last_result and not app.busy:
                    break
            assert app.session.last_result["changed"]
            assert app.session.plan is None and not app.session.dirty
            assert len(list(engine.scope.root.glob(".agents/skills/*/SKILL.md"))) == 2
            assert engine.status()["pending_changes"] == 0

    asyncio.run(journey())


def test_source_modal_explicit_trust_and_cancel_are_cache_only(workspace, tmp_path):
    engine, *_ = workspace
    c = "33333333-3333-4333-8333-333333333333"
    source = recipe(tmp_path / "third", c)
    before = copy.deepcopy(registry(engine))

    async def journey():
        app = RecipeApp(engine)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.click("#add-source")
            assert isinstance(app.screen, SourceDialog)
            app.screen.query_one("#source-path", Input).value = str(source)
            app.screen.query_one("#source-alias", Input).value = "third"
            await pilot.click("#prepare-source")
            for _ in range(100):
                await pilot.pause(0.02)
                if app.screen.candidate:
                    break
            assert app.screen.candidate
            assert app.screen.query_one("#stage-source", Button).disabled
            await pilot.click("#source-trust")
            assert not app.screen.query_one("#stage-source", Button).disabled
            await pilot.click("#stage-source")
            await pilot.pause()
            assert c in app.session.pending and app.session.dirty
            assert registry(engine) == before
            app.action_reset()
            await pilot.pause()
            await pilot.click("#confirm")
            assert not app.session.dirty and c not in app.session.sources
        assert registry(engine) == before

    asyncio.run(journey())


def test_busy_apply_blocks_quit_and_reports_actual_receipt(workspace):
    engine, *_ = workspace

    async def journey():
        app = RecipeApp(engine)
        async with app.run_test(size=(120, 36)) as pilot:
            app.session.toggle((A, "skill.review"))
            app.session.review()
            started, release = threading.Event(), threading.Event()
            original = app.session.apply

            def held():
                started.set()
                release.wait(timeout=3)
                return original()

            app.session.apply = held
            worker = app.run_worker(app.apply_reviewed())
            for _ in range(80):
                await pilot.pause(0.01)
                if started.is_set():
                    break
            assert app.busy
            app.action_quit()
            assert not app._exit
            assert app.query_one("#apply", Button).disabled
            app.query_one("#search", Input).value = "personal"
            app.action_toggle()
            await pilot.pause()
            assert app.session.roots == {(A, "skill.review")}
            assert app.query_one("#items", DataTable).row_count == 3
            release.set()
            await worker.wait()
            assert app.session.last_result["receipt"] == engine.state.head(engine.scope.key)["id"]
            assert not app.busy
            assert app.query_one("#items", DataTable).row_count == 1

    asyncio.run(journey())


def test_no_input_tui_refuses_before_environment_access(tmp_path, monkeypatch, capsys):
    from dasync.cli import main

    home = tmp_path / "absent"
    monkeypatch.setenv("DASYNC_HOME", str(home))
    assert main(["tui", "--json", "--no-input"]) == 2
    value = json.loads(capsys.readouterr().out)
    assert value["error"]["code"] == "INTERACTIVE_REQUIRED" and not home.exists()


@pytest.mark.parametrize(
    "flags",
    [
        ["--yes"],
        ["--trust-source"],
        ["--enable", "skill.review"],
        ["--source-kind", "local"],
        ["--revision", "a" * 40],
        ["--project", "example"],
        ["--effective"],
        ["--consumer", "example"],
        ["--allow-private-path"],
        ["--query", "example"],
        ["--limit", "1"],
        ["--offset", "1"],
    ],
)
def test_tui_rejects_ignored_options_before_environment_access(monkeypatch, capsys, flags):
    from dasync.cli import main

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)

    def forbidden():
        pytest.fail("Environment read before rejecting incompatible launch options")

    monkeypatch.setattr(Environment, "current", forbidden)
    assert main(["tui", "--scope", "user", *flags]) == 2
    assert "USAGE:" in capsys.readouterr().err


def test_literal_recipe_query_does_not_change_legacy_protocol(tmp_path, monkeypatch, capsys):
    from dasync.cli import main

    monkeypatch.setenv("DASYNC_HOME", str(tmp_path / "absent"))
    assert main(["search", "--query", "recipe", "--json"]) == 2
    value = json.loads(capsys.readouterr().out)
    assert "protocol" not in value


def test_tui_launch_is_audited_as_interactive_in_discovery():
    from dasync.recipe_cli import describe

    command = next(command for command in describe()["commands"] if command["operation"] == "workspace.open")
    assert command["interactive"] is True and command["argv"] == ["dasync", "tui"]


def test_no_color_and_literal_metadata_have_no_terminal_escape_effects(workspace, monkeypatch):
    engine, *_ = workspace
    monkeypatch.setenv("NO_COLOR", "1")

    async def journey():
        app = RecipeApp(engine)
        async with app.run_test(size=(80, 24)) as pilot:
            assert app.theme == "dasync-mono"
            await pilot.press("f1")
            await pilot.pause()
            await pilot.press("escape")
            assert app.query_one("#items", DataTable).row_count == 3

    asyncio.run(journey())


def test_clearing_search_does_not_change_draft_or_review(workspace):
    engine, *_ = workspace

    async def journey():
        app = RecipeApp(engine)
        async with app.run_test(size=(120, 36)) as pilot:
            app.session.toggle((A, "skill.review"))
            plan = app.session.review()
            for query in ("review", "studio", "missing", "", "personal", ""):
                app.query_one("#search", Input).value = query
                await pilot.pause()
                assert app.session.plan == plan
                assert app.session.roots == {(A, "skill.review")}

    asyncio.run(journey())

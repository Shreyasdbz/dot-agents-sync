"""A searchable, draft-first Textual workspace over the recipe Engine."""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.theme import Theme
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)

from .errors import DasyncError
from .recipe_contracts import key_text
from .recipe_engine import registry
from .recipe_session import RecipeSession, display_text
from .recipe_sources import Snapshots


class Confirm(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, title, message, label="Confirm"):
        super().__init__()
        self.heading, self.message, self.label = title, message, label

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label(self.heading, classes="dialog-title", markup=False)
            yield Static(self.message, markup=False)
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button(self.label, id="confirm", variant="primary")

    @on(Button.Pressed, "#confirm")
    def confirmed(self):
        self.dismiss(True)

    @on(Button.Pressed, "#cancel")
    def action_cancel(self):
        self.dismiss(False)


class SourceDialog(ModalScreen[tuple[str, str] | None]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, cache):
        super().__init__()
        self.cache, self.candidate, self.preparing = cache, None, False

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label("Add a local recipe", classes="dialog-title")
            yield Static(
                "Prepare a snapshot, inspect it, then explicitly trust it. Registration waits for Apply."
            )
            yield Input(placeholder="Absolute source directory", id="source-path")
            yield Input(placeholder="A memorable alias, e.g. studio", id="source-alias")
            yield Static("No source prepared.", id="candidate", markup=False)
            yield Checkbox("I reviewed and trust this exact source", id="source-trust", disabled=True)
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel-source")
                yield Button("Prepare", id="prepare-source")
                yield Button("Stage source", id="stage-source", variant="primary", disabled=True)

    @on(Button.Pressed, "#prepare-source")
    async def prepare(self):
        if self.preparing:
            return
        self.preparing = True
        path_widget = self.query_one("#source-path", Input)
        path = path_widget.value
        path_widget.disabled = True
        self.candidate = None
        self.query_one("#stage-source", Button).disabled = True
        trust = self.query_one("#source-trust", Checkbox)
        trust.value, trust.disabled = False, True
        self.query_one("#candidate", Static).update("Preparing immutable local bytes…")
        try:
            result = await self.app.offload(Snapshots(self.cache).prepare, Path(path))
            if path_widget.value != path:
                self.query_one("#candidate", Static).update(
                    "Source path changed. Prepare its new bytes before trusting."
                )
                return
            self.candidate = result["candidate"]
            self.query_one("#candidate", Static).update(
                display_text(
                    f"Source {result['source_id']}\nSnapshot {result['pin']}\n{len(result['items'])} items · local tree · cache only"
                )
            )
            trust.disabled = False
        except DasyncError as exc:
            self.query_one("#candidate", Static).update(display_text(f"{exc.code}: {exc}"))
        except Exception as exc:
            self.query_one("#candidate", Static).update(
                f"Preparation failed ({type(exc).__name__}); nothing registered."
            )
        finally:
            self.preparing = False
            path_widget.disabled = False

    @on(Input.Changed, "#source-path")
    def path_changed(self):
        self.candidate = None
        self.query_one("#source-trust", Checkbox).value = False
        self.query_one("#source-trust", Checkbox).disabled = True
        self.query_one("#stage-source", Button).disabled = True

    @on(Checkbox.Changed, "#source-trust")
    def trust_changed(self, event):
        self.query_one("#stage-source", Button).disabled = not (self.candidate and event.value)

    @on(Button.Pressed, "#stage-source")
    def stage(self):
        if self.candidate and self.query_one("#source-trust", Checkbox).value:
            self.dismiss((self.candidate, self.query_one("#source-alias", Input).value))

    @on(Button.Pressed, "#cancel-source")
    def action_cancel(self):
        if not self.preparing:
            self.dismiss(None)


class RegisteredSourceDialog(ModalScreen[tuple[str, str] | None]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, registered):
        super().__init__()
        self.entries = registered["sources"]

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label("Use a registered snapshot", classes="dialog-title")
            yield Static(
                "Choose a source and its exact accepted pin. This adds a draft binding, not new trust."
            )
            yield Select(
                [(display_text(entry["alias"]), sid) for sid, entry in sorted(self.entries.items())],
                id="registered-source",
            )
            yield Select([], id="registered-pin", prompt="Choose an immutable pin")
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel-binding")
                yield Button("Use snapshot", id="use-binding", variant="primary")

    @on(Select.Changed, "#registered-source")
    def source_changed(self, event):
        pins = sorted(self.entries.get(event.value, {}).get("pins", {}))
        self.query_one("#registered-pin", Select).set_options([(pin, pin) for pin in pins])

    @on(Button.Pressed, "#use-binding")
    def use(self):
        sid = self.query_one("#registered-source", Select).value
        pin = self.query_one("#registered-pin", Select).value
        if sid is not Select.BLANK and pin is not Select.BLANK:
            self.dismiss((sid, pin))

    @on(Button.Pressed, "#cancel-binding")
    def action_cancel(self):
        self.dismiss(None)


class PathDialog(ModalScreen[str | None]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, title, placeholder):
        super().__init__()
        self.heading, self.placeholder = title, placeholder

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label(self.heading, classes="dialog-title")
            yield Input(placeholder=self.placeholder, id="dialog-path")
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel-path")
                yield Button("Continue", id="accept-path", variant="primary")

    @on(Button.Pressed, "#accept-path")
    def accept(self):
        self.dismiss(self.query_one("#dialog-path", Input).value)

    @on(Button.Pressed, "#cancel-path")
    def action_cancel(self):
        self.dismiss(None)


class Help(ModalScreen):
    BINDINGS = [Binding("escape,f1", "close", "Close")]

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label("Make yourself at home", classes="dialog-title")
            yield Static(
                "/  Find items\nSpace / Enter  Toggle direct selection\nD  Toggle an explicit disable\n"
                "A  Prepare a source\nB  Use a registered snapshot\nI  Toggle personal inheritance\n"
                "R  Review draft\nCtrl+Enter  Confirm reviewed apply\nCtrl+S  Save reviewed plan\n"
                "F3  Health and recovery\nF4  Inspect full identity\nX  Approve exact Hook bytes\nCtrl+R  Discard draft\nCtrl+T  Cycle themes\nQ / F10  Close\n\n"
                "Nothing is installed until you review and confirm Apply. Dependencies remain dependencies; "
                "source trust, file replacements and ordinary confirmation are separate decisions."
            )
            yield Button("Got it", id="close-help", variant="primary")

    @on(Button.Pressed, "#close-help")
    def action_close(self):
        self.dismiss()


class Inspect(ModalScreen):
    BINDINGS = [Binding("escape,f4", "close", "Close")]

    def __init__(self, metadata):
        super().__init__()
        self.metadata = metadata

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog inspect-dialog"):
            yield Label("Exact item identity", classes="dialog-title")
            yield TextArea(self.metadata, read_only=True, id="identity-preview")
            yield Button("Close", id="close-inspect", variant="primary")

    @on(Button.Pressed, "#close-inspect")
    def action_close(self):
        self.dismiss()


class RestoreDialog(ModalScreen[tuple[str, bool] | None]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label("Restore a receipt", classes="dialog-title")
            yield Static("Restore saved output or its original backups. Review every effect before Apply.")
            yield Input(placeholder="Full receipt ID from Health", id="restore-receipt")
            yield Checkbox("Restore the state BEFORE this receipt (including originals)", id="restore-before")
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel-restore")
                yield Button("Review restore", id="review-restore", variant="primary")

    @on(Button.Pressed, "#review-restore")
    def accept(self):
        receipt = self.query_one("#restore-receipt", Input).value.strip()
        if receipt:
            self.dismiss((receipt, self.query_one("#restore-before", Checkbox).value))

    @on(Button.Pressed, "#cancel-restore")
    def action_cancel(self):
        self.dismiss(None)


class RecipeApp(App[str]):
    TITLE = "dasync"
    SUB_TITLE = "Your workflow, in sync."
    CSS = """
    Screen { background: $background; }
    Header { background: $surface; color: $text; }
    #scope { height: 2; padding: 0 2; color: $text-muted; }
    #toolbar { height: 3; padding: 0 1; }
    #toolbar Button { min-width: 12; margin-right: 1; }
    #workspace { height: 1fr; margin: 0 1; }
    #browse-layout { height: 1fr; }
    #sources { width: 24; padding: 1; border: round $primary; margin-right: 1; }
    #source-filter { width: 1fr; margin-bottom: 1; }
    #source-info { height: 1fr; color: $text-muted; overflow-y: auto; }
    #catalog { width: 1fr; }
    #search { margin-bottom: 1; }
    #items { height: 1fr; }
    #detail { width: 44; margin-left: 1; border: round $accent; }
    #detail-info { padding: 1; height: auto; max-height: 14; overflow-y: auto; }
    #body-preview { height: 1fr; border: none; }
    #draft { height: 2; padding: 0 2; background: $surface; color: $accent; }
    #message { height: 2; padding: 0 2; color: $text-muted; }
    #review-summary { height: 4; padding: 1; }
    #review-notes { height: auto; max-height: 6; overflow-y: auto; padding: 0 1; color: $text-muted; }
    #overwrite { height: 3; }
    #effects { height: 1fr; }
    #health-info { height: 1fr; padding: 1; }
    .health-buttons { height: 3; }
    .health-buttons Button { margin-right: 1; }
    ModalScreen { align: center middle; background: $background 75%; }
    .dialog { width: 72; max-width: 95%; height: auto; max-height: 90%; overflow-y: auto; padding: 1 2; border: thick $primary; background: $surface; }
    .dialog-title { color: $accent; text-style: bold; margin-bottom: 1; }
    .dialog Input { margin-top: 1; }
    .dialog Static { height: auto; margin-bottom: 1; }
    .dialog-buttons { height: 3; margin-top: 1; align: right middle; }
    .dialog-buttons Button { margin-left: 1; min-width: 10; }
    .inspect-dialog { height: 80%; }
    #identity-preview { height: 1fr; margin-bottom: 1; }
    Screen.compact #sources { display: none; }
    Screen.compact #detail { width: 34; }
    Screen.narrow #browse-layout { layout: vertical; }
    Screen.narrow #catalog { height: 1fr; width: 1fr; }
    Screen.narrow #detail { height: 11; width: 1fr; margin: 1 0 0 0; }
    Screen.narrow #body-preview { display: none; }
    Screen.narrow #toolbar Button { min-width: 8; margin-right: 0; }
    Screen.narrow .dialog { width: 95%; }
    Screen.short #detail { display: none; }
    """
    BINDINGS = [
        Binding("slash", "find", "Search"),
        Binding("space,enter", "toggle", "Pick"),
        Binding("r", "review", "Review", priority=True),
        Binding("ctrl+enter", "apply", "Apply"),
        Binding("a", "add_source", "Add source"),
        Binding("q", "quit", "Close", priority=True),
        Binding("f10,ctrl+q", "force_quit", "Close", priority=True),
        Binding("f2", "add_source", "Add source", show=False, priority=True),
        Binding("f1", "help", "Help"),
        Binding("d", "disable", "Disable", show=False),
        Binding("b", "bind_source", "Use source", show=False),
        Binding("i", "inherit", "Inherit", show=False),
        Binding("ctrl+r", "reset", "Reset", show=False),
        Binding("ctrl+s", "save", "Save", show=False),
        Binding("f3", "health", "Health", show=False),
        Binding("f4", "inspect", "Inspect", show=False),
        Binding("x", "approve_hook", "Approve Hook", show=False),
        Binding("ctrl+t", "theme", "Theme", show=False),
        Binding("ctrl+c", "quit", "Close", show=False, priority=True),
    ]

    def __init__(self, engine):
        super().__init__()
        self.session = RecipeSession(engine)
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="dasync-workspace")
        self.busy, self.selected_key, self.visible_rows = False, None, []
        self.ready, self.source_options = False, None
        self.register_theme(
            Theme(
                name="dasync-mono",
                primary="#c8c8c8",
                secondary="#a0a0a0",
                accent="#ffffff",
                foreground="#f0f0f0",
                background="#151515",
                surface="#202020",
                panel="#282828",
                dark=True,
            )
        )
        self.theme = "dasync-mono" if os.environ.get("NO_COLOR") is not None else "catppuccin-mocha"

    def check_action(self, action, parameters):
        if action == "quit" and isinstance(self.focused, (Input, TextArea)):
            return False
        if action == "review" and isinstance(self.focused, Input):
            return False
        return True

    async def offload(self, function, *args):
        future = self.executor.submit(partial(function, *args))
        # Poll only while work is active; avoid platform-specific executor wakeup/shutdown races.
        while not future.done():
            await asyncio.sleep(0.02)
        return future.result()

    async def run_async(self, *args, **kwargs):
        try:
            return await super().run_async(*args, **kwargs)
        finally:
            # A UI cancellation is not transaction cancellation. Let started operations finish.
            self.executor.shutdown(wait=True, cancel_futures=False)

    @asynccontextmanager
    async def run_test(self, *args, **kwargs):
        try:
            async with super().run_test(*args, **kwargs) as pilot:
                yield pilot
        finally:
            self.executor.shutdown(wait=True, cancel_futures=False)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(
            display_text(
                f"{self.session.engine.scope.kind.upper()}  ·  {self.session.engine.scope.root}  ·  Codex"
            ),
            id="scope",
            markup=False,
        )
        with Horizontal(id="toolbar"):
            yield Button("+ Source", id="add-source")
            yield Button("Use saved", id="bind-source")
            yield Button("Review", id="review", variant="primary")
            yield Button("Apply", id="apply", variant="success", disabled=True)
        with TabbedContent(id="workspace"):
            with TabPane("Browse", id="browse"):
                with Horizontal(id="browse-layout"):
                    with Vertical(id="sources"):
                        yield Label("YOUR RECIPES")
                        yield Select(
                            [("All sources", "all")], value="all", allow_blank=False, id="source-filter"
                        )
                        yield Checkbox(
                            "Personal picks",
                            value=self.session.inherit,
                            id="inherit",
                            disabled=self.session.engine.scope.kind != "project",
                        )
                        yield Static("", id="source-info", markup=False)
                    with Vertical(id="catalog"):
                        yield Input(placeholder="Find a skill, source or idea…  /", id="search")
                        yield DataTable(id="items", cursor_type="row", zebra_stripes=True)
                    with Vertical(id="detail"):
                        yield Static("Pick an item to get acquainted.", id="detail-info", markup=False)
                        yield TextArea("", read_only=True, show_line_numbers=False, id="body-preview")
            with TabPane("Review", id="review-tab"):
                yield Static(
                    "Your draft is yours until you apply it. Press R to review.",
                    id="review-summary",
                    markup=False,
                )
                yield Checkbox("Allow these reviewed replacements; retain original backups", id="overwrite")
                yield Static("", id="review-notes", markup=False)
                yield DataTable(id="effects", cursor_type="row", zebra_stripes=True)
            with TabPane("Health", id="health-tab"):
                yield Static(
                    "Press Refresh to inspect the actual installation.", id="health-info", markup=False
                )
                with Horizontal(classes="health-buttons"):
                    yield Button("Refresh", id="refresh-health")
                    yield Button("Recover", id="recover")
                    yield Button("Restore receipt", id="restore")
        yield Static("", id="draft", markup=False)
        yield Static("Welcome. Pick the tools that feel like you.", id="message", markup=False)
        yield Footer()

    def on_mount(self):
        self.query_one("#items", DataTable).add_columns("Pick", "Source", "Item", "Kind", "Version", "Why")
        self.query_one("#effects", DataTable).add_columns("Action", "Target", "Owner", "Before", "After")
        self.ready = True
        self.refresh_catalog()
        self.query_one("#items", DataTable).focus()
        self.responsive()

    def on_resize(self, event):
        if self.ready:
            self.responsive(event.size.width, event.size.height)

    def responsive(self, width=None, height=None):
        width = width if width is not None else self.size.width
        height = height if height is not None else self.size.height
        for screen in self.screen_stack:
            screen.set_class(width < 112, "compact")
            screen.set_class(width < 82, "narrow")
            screen.set_class(height < 27, "short")

    def say(self, message):
        self.query_one("#message", Static).update(display_text(message))

    def editable(self):
        return not self.busy and not isinstance(self.screen, ModalScreen)

    def refresh_catalog(self):
        filter_widget = self.query_one("#source-filter", Select)
        old_filter = filter_widget.value
        choices = [
            ("All sources", "all"),
            *[(display_text(self.session.labels[sid]), sid) for sid in sorted(self.session.sources)],
        ]
        if choices != self.source_options:
            self.source_options = choices
            filter_widget.set_options(choices)
            filter_widget.value = old_filter if old_filter in {choice[1] for choice in choices} else "all"
        selected_source = None if filter_widget.value == "all" else filter_widget.value
        query = self.query_one("#search", Input).value
        self.visible_rows = self.session.rows(query, selected_source)
        table = self.query_one("#items", DataTable)
        old_key = self.selected_key
        table.clear()
        for row in self.visible_rows:
            status = row["status"]
            picked = "●" if status == "Direct" else "×" if status == "Disabled" else "○"
            table.add_row(
                Text(picked, style="bold cyan" if status == "Direct" else "dim"),
                Text(display_text(row["source"], 24)),
                Text(display_text(row["id"], 44)),
                row["kind"],
                row["version"],
                status,
                key=key_text(row["key"]),
            )
        if self.visible_rows:
            index = next((i for i, row in enumerate(self.visible_rows) if row["key"] == old_key), 0)
            table.move_cursor(row=index)
            self.show_detail(self.visible_rows[index]["key"])
        else:
            self.selected_key = None
            self.query_one("#detail-info", Static).update(
                "No matches. Clear your search or add a local recipe."
            )
            self.query_one("#body-preview", TextArea).load_text("")
        self.query_one("#source-info", Static).update(
            display_text(
                "\n\n".join(
                    f"{self.session.labels[sid]}\n{len(source.items)} items\n{source.pin[:19]}…"
                    for sid, source in sorted(self.session.sources.items())
                )
            )
        )
        plan = self.session.plan
        effects = self.query_one("#effects", DataTable)
        if not plan and effects.row_count:
            effects.clear()
            self.query_one("#review-notes", Static).update("")
            self.query_one("#review-summary", Static).update(
                "This review is out of date. Review the current draft before Apply."
            )
        self.query_one("#draft", Static).update(
            f"{len(self.session.roots)} direct picks  ·  {len(self.visible_rows)} visible  ·  "
            + (
                f"{len(plan['graph'].get('items', []))} resolved  ·  reviewed"
                if plan
                else "draft only — review before Apply"
            )
        )
        self.query_one("#apply", Button).disabled = not bool(plan) or self.busy
        if self.session.load_error:
            self.say(f"{self.session.load_error.code}: {self.session.load_error}")
        elif self.session.graph_error:
            self.say(f"Draft blocked · {self.session.graph_error.code}: {self.session.graph_error}")

    def show_detail(self, key):
        self.selected_key = key
        info, body = self.session.detail(key, compact=True)
        self.query_one("#detail-info", Static).update(info)
        self.query_one("#body-preview", TextArea).load_text(body)

    @on(DataTable.RowHighlighted, "#items")
    def highlighted(self, event):
        if self.busy:
            return
        key = next(
            (row["key"] for row in self.visible_rows if key_text(row["key"]) == str(event.row_key.value)),
            None,
        )
        if key:
            self.show_detail(key)

    @on(DataTable.RowSelected, "#items")
    def selected(self):
        self.action_toggle()

    @on(Input.Changed, "#search")
    def search_changed(self):
        if self.ready and not self.busy:
            self.refresh_catalog()

    @on(Select.Changed, "#source-filter")
    def filter_changed(self, event):
        if self.ready and not self.busy and event.value is not Select.BLANK:
            self.refresh_catalog()

    @on(Checkbox.Changed, "#inherit")
    def inheritance_changed(self, event):
        if self.ready and event.value != self.session.inherit and not self.busy:
            try:
                self.session.set_inheritance(event.value)
                self.refresh_catalog()
            except DasyncError as exc:
                self.say(f"{exc.code}: {exc}")

    @on(Checkbox.Changed, "#overwrite")
    def overwrite_changed(self):
        if self.ready and not self.busy:
            self.session.touch()
            self.refresh_catalog()
            self.say("Replacement decision changed. Review the resulting effects again.")

    @on(Button.Pressed)
    async def buttons(self, event):
        actions = {
            "add-source": self.action_add_source,
            "bind-source": self.action_bind_source,
            "review": self.action_review,
            "apply": self.action_apply,
            "refresh-health": self.action_health,
            "recover": self.action_recover,
            "restore": self.action_restore,
        }
        action = actions.get(event.button.id)
        if action:
            result = action()
            if asyncio.iscoroutine(result):
                await result

    def action_find(self):
        if self.editable():
            self.query_one("#workspace", TabbedContent).active = "browse"
            self.query_one("#search", Input).focus()

    def action_toggle(self):
        if self.editable() and self.selected_key:
            self.session.toggle(self.selected_key)
            self.refresh_catalog()

    def action_disable(self):
        if self.editable() and self.selected_key:
            self.session.disable(self.selected_key)
            self.refresh_catalog()

    def action_inherit(self):
        if self.editable() and self.session.engine.scope.kind == "project":
            self.query_one("#inherit", Checkbox).toggle()

    def action_add_source(self):
        if self.editable():

            def staged(result):
                if result:
                    try:
                        self.session.stage(*result, trusted=True)
                        self.refresh_catalog()
                        self.say("Source staged. Choose items, then review; nothing registered yet.")
                    except DasyncError as exc:
                        self.say(f"{exc.code}: {exc}")

            self.push_screen(SourceDialog(self.session.engine.env.cache), staged)

    def action_bind_source(self):
        if self.editable():

            def bound(result):
                if result:
                    try:
                        self.session.bind(*result)
                        self.refresh_catalog()
                    except DasyncError as exc:
                        self.say(f"{exc.code}: {exc}")

            self.push_screen(RegisteredSourceDialog(registry(self.session.engine)), bound)

    async def job(self, function, callback):
        if not self.editable():
            return
        self.busy = True
        self.query_one("#apply", Button).disabled = True
        self.query_one("#inherit", Checkbox).disabled = True
        self.query_one("#overwrite", Checkbox).disabled = True
        try:
            result = await self.offload(function)
            callback(result)
        except DasyncError as exc:
            self.say(f"{exc.code}: {exc}" + (f" · {exc.hint}" if exc.hint else ""))
        except Exception as exc:
            self.say(f"Operation could not finish ({type(exc).__name__}). Inspect Health before retrying.")
        finally:
            self.busy = False
            self.query_one("#inherit", Checkbox).disabled = self.session.engine.scope.kind != "project"
            self.query_one("#overwrite", Checkbox).disabled = False
            self.refresh_catalog()

    async def action_review(self):
        if self.editable():
            self.query_one("#workspace", TabbedContent).active = "review-tab"
            self.query_one("#effects", DataTable).focus()
            self.say("Resolving the draft and protecting observed files…")
            overwrite = self.query_one("#overwrite", Checkbox).value
            await self.job(lambda: self.session.review(overwrite), self.show_plan)

    def show_plan(self, plan):
        changes = [op for op in plan["operations"] if op["action"] != "keep"]
        self.query_one("#review-summary", Static).update(
            f"{len(plan['graph'].get('items', []))} resolved items · {len(changes)} file effects\n"
            f"Plan {plan['plan_hash'][:16]} · exact target {display_text(plan['root'])}"
        )
        table = self.query_one("#effects", DataTable)
        notes = []
        for decision in plan["decisions"]:
            if decision.get("agent_access"):
                notes.append(
                    decision["item"]["item_id"]
                    + " · role inherits parent permissions; no standalone sandbox override"
                )
            if decision.get("executable_digest"):
                notes.append(
                    decision["item"]["item_id"]
                    + " · separately approved Python hook · "
                    + decision["executable_digest"][:16]
                    + " · provider execution, no OS sandbox"
                )
            if decision.get("optional_unverified"):
                notes.append(
                    decision["item"]["item_id"]
                    + " · unverified optional capabilities: "
                    + ", ".join(decision["optional_unverified"])
                )
            if decision.get("absent_optional_slots"):
                notes.append(
                    decision["item"]["item_id"]
                    + " · unbound optional slots: "
                    + ", ".join(decision["absent_optional_slots"])
                )
        self.query_one("#review-notes", Static).update(display_text("\n".join(notes), 16000))
        table.clear()
        for op in plan["operations"]:
            path = Path(op["path"])
            try:
                target = str(path.relative_to(self.session.engine.scope.root))
            except ValueError:
                target = str(path)
            source_id, separator, local_id = op["package"].partition("/")
            owner = self.session.labels.get(source_id, source_id) + separator + local_id
            table.add_row(
                op["action"].upper(),
                Text(display_text(target)),
                Text(display_text(owner)),
                (op["before"]["hash"] or "missing")[:12],
                (op["hash"] or "remove")[:12],
            )
        self.say("Review every write and removal. Apply uses this exact plan; changes invalidate it.")

    def action_apply(self):
        if self.editable() and self.session.plan:
            plan = self.session.plan
            effects = sum(op["action"] != "keep" for op in plan["operations"])

            def confirmed(result):
                if result:
                    self.run_worker(self.apply_reviewed(), exclusive=True)

            self.push_screen(
                Confirm(
                    "Apply this reviewed plan?",
                    f"Target: {plan['root']}\n"
                    f"Plan: {plan['plan_hash'][:16]}\n{effects} file effects. Originals remain recoverable.",
                    "Apply",
                ),
                confirmed,
            )

    async def apply_reviewed(self):
        self.say("Applying reviewed effects. Please wait for the receipt…")

        def applied(result):
            self.say(
                f"{'Applied' if result['changed'] else 'Already in sync'} · {result['operations']} effects · receipt {result['receipt']}"
            )
            self.query_one("#effects", DataTable).clear()
            self.query_one("#review-summary", Static).update(
                "Receipt recorded. Make another draft whenever you like."
            )

        await self.job(self.session.apply, applied)

    async def action_health(self):
        if self.editable():
            self.query_one("#workspace", TabbedContent).active = "health-tab"
            self.query_one("#refresh-health", Button).focus()

            def inspected(status):
                lines = [
                    f"Receipt: {status['receipt'] or 'none'}",
                    f"Configured: {status['configured']}",
                    f"Recovery journals: {len(status['pending_recovery'])}",
                    f"Pending changes: {status.get('pending_changes', 'not configured' if not status['configured'] else 'blocked')}",
                ]
                if status.get("diagnostic"):
                    lines.append(status["diagnostic"]["code"] + ": " + status["diagnostic"]["message"])
                lines += [f"{row['status'].upper()}  {row['path']}" for row in status["files"]]
                self.query_one("#health-info", Static).update(display_text("\n".join(lines), 16000))

            await self.job(self.session.health, inspected)

    def action_recover(self):
        if self.editable():
            pending = [
                j for j in self.session.engine.state.pending() if j["scope"] == self.session.engine.scope.key
            ]

            def confirmed(result):
                if result:
                    self.run_worker(self.recover_reviewed(), exclusive=True)

            self.push_screen(
                Confirm(
                    "Recover interrupted writes?",
                    f"{len(pending)} pending journals. "
                    "Only recognized before/after states can be restored. Independent edits and denied activation remain blocked.",
                    "Recover",
                ),
                confirmed,
            )

    async def recover_reviewed(self):
        engine = self.session.engine

        def recovered(result):
            self.session.reload()
            self.say(f"Recovered {len(result['recovered'])} journals. Inspect Health for actual state.")

        await self.job(lambda: engine.state.recover(engine.scope.key, engine._validate_target), recovered)

    def action_restore(self):
        if self.editable():

            def requested(result):
                if result:
                    self.run_worker(self.review_restore(*result), exclusive=True)

            self.push_screen(
                RestoreDialog(),
                requested,
            )

    async def review_restore(self, receipt, before=False):
        self.query_one("#workspace", TabbedContent).active = "review-tab"
        self.query_one("#effects", DataTable).focus()
        await self.job(
            lambda: self.session.review(
                request={"operation": "recipe.restore", "receipt": receipt, "before_receipt": before}
            ),
            self.show_plan,
        )

    def action_save(self):
        if self.editable() and self.session.plan:

            def saved(path):
                if path:
                    try:
                        self.session.save_plan(path)
                        self.say("Reviewed plan saved. Existing files are never overwritten by export.")
                    except (DasyncError, OSError) as exc:
                        self.say(
                            f"{exc.code}: {exc}"
                            if isinstance(exc, DasyncError)
                            else "Cannot save at this path; existing files preserved."
                        )

            self.push_screen(PathDialog("Save reviewed plan", "Absolute new file path"), saved)

    def action_reset(self):
        if self.editable():

            def reset(result):
                if result:
                    self.session.reload()
                    self.refresh_catalog()
                    self.say(
                        "Draft discarded. Immutable prepared cache bytes may remain; nothing else saved."
                    )

            self.push_screen(
                Confirm(
                    "Discard this draft?",
                    "Applied receipts remain intact. Draft source and selection choices will be dropped.",
                    "Discard",
                ),
                reset,
            )

    def action_theme(self):
        themes = ["catppuccin-mocha", "catppuccin-latte", "dasync-mono"]
        self.theme = themes[(themes.index(self.theme) + 1) % len(themes)]

    def action_help(self):
        if self.editable():
            self.push_screen(Help())

    def action_inspect(self):
        if self.editable() and self.selected_key:
            self.push_screen(Inspect(self.session.detail(self.selected_key)[0]))

    def action_approve_hook(self):
        if not self.editable() or not self.selected_key:
            return
        key = self.selected_key
        item = self.session.sources[key[0]].items.get(key[1])
        if item is None or item.spec["kind"] != "Hook":
            self.say("Select a Hook and inspect its code before approving execution.")
            return

        def approved(result):
            if result:
                self.session.approve_hook(key, confirmed=True)
                self.refresh_catalog()
                self.say("Exact executable approval staged for this scope. Review and Apply to commit it.")

        self.push_screen(
            Confirm(
                "Approve these exact Python Hook bytes?",
                f"{key_text(key)}\nDigest: {item.digest}\nEvents: {', '.join(item.spec['executable']['events'])}\nPermissions: {', '.join(item.spec['executable']['permissions'])}\nThe hook runs in the provider's execution environment; this is not an OS sandbox. Approval is separate from source trust and final Apply.",
                "Approve",
            ),
            approved,
        )

    def action_quit(self):
        if self.busy:
            self.say(
                "An operation is running. Wait for its result; inspect Health if the process is interrupted."
            )
            return
        if isinstance(self.screen, ModalScreen):
            return

        def closed(result=True):
            if result:
                last = self.session.last_result
                self.exit(
                    f"Closed · receipt {last['receipt']} · {last['operations']} effects."
                    if last
                    else "Closed. Draft discarded; nothing installed."
                )

        if self.session.dirty:
            self.push_screen(
                Confirm(
                    "Leave this draft?", "Unapplied selections and registrations will be discarded.", "Leave"
                ),
                closed,
            )
        else:
            closed()

    def action_force_quit(self):
        self.action_quit()

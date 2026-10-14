# Deterministic recipe validation

The recipe workspace and machine commands share the real Engine/State boundary. Validation therefore checks graph meaning, stable identity, trust and privacy, exact file effects, persistent receipts and recovery, as well as the actual interactive controls. Every home, project and source is disposable; tests do not invoke provider accounts, models or external production services.

## Repeatable spaces and independent expectations

| Boundary | Finite space or sequence | Observable expectation |
| --- | --- | --- |
| Graph closure | All 64 directed three-node graphs without self edges × 8 root sets × 8 disable sets: **4,096 cases** | Independent breadth-first closure and Kahn cycle elimination agree with selected keys, edges and direct/dependency reasons; blockers never become a successful graph |
| Cross-recipe imports | Another **4,096 cases**, with one same-named item per source across three UUIDs and all graph/root/disable combinations | The independent oracle agrees; source order cannot change closure; declared imports preserve qualified identity across cycles and disabled edges |
| Generated graph permutations | **400 deterministic examples**, up to eight nodes, including self edges, cycles, disconnected nodes, roots/disables and a second source with matching IDs | Same closure oracle; dependencies stay recipe-local; reversed registry/root/disable order leaves graph and names identical |
| Generated native names | **400 deterministic examples**, up to 60 adversarial item IDs per source across two UUIDs | Bounded ASCII names remain unique and identical under insertion-order reversal |
| Personal/project pins | Absent/old/new pin × two sources × two scopes × inheritance: **162 cases** | Exactly one effective pin per UUID; conflicting inherited pins fail rather than pick a winner |
| Context closure | Scope × public/private × inherit/explicit/never access × allowed scopes × direct/dependency selection: **72 cases** | Scope denial, private/never denial and current-scope explicit selection are enforced before output; sentinel private bytes stay out of errors |
| Markdown literals | Nine code/comment/escape wrappers, six fence closer forms and one mixed comment/link boundary | Literal examples never request a dependency; visible typed links resolve correctly across comment boundaries |
| Path and graph limits | Seven case/Unicode/reserved/file-directory collisions and two 512-item boundary cases | Unsafe output names fail; nodes currently in DFS traversal count toward the total graph budget |
| Stateful recipe edits | **20 deterministic sequences**, each bounded to 35 actions | Select/remove, alias edits, accepted snapshot edits, cancelled proposals and repeat sync agree with an independent direct-root model; receipts match installed state |

These add **9,251 deterministic graph/name/composition/privacy/reference/boundary cases**, plus bounded stateful sequences and the real collection journeys below. The exhaustive claim applies to the stated small spaces only. Larger generated examples sample a fixed reproducible distribution; they do not prove all possible recipes or edit orders. Hypothesis uses `derandomize=True`, `database=None` and no timing deadline. A counterexample is minimized by the generator, and explicit regression fixtures preserve repaired boundaries. Replay the committed dependency lock to keep generator behavior stable.

The exhaustive graph oracle uses a different algorithm from the resolver: breadth-first reachability followed by Kahn elimination, compared against the engine's DFS. If a graph has both a cycle and a disabled required edge, either valid causal diagnostic may be reported, but successful resolution is forbidden. This avoids asserting one incidental traversal order as the contract.

## Transaction modifications and failures

`tests/test_recipe_transactions.py` covers install, removal, snapshot update and receipt restoration. For every resulting write position, it injects both ordinary exceptions and interruption before and after the write. Ordinary failures must roll back automatically; interruptions must retain a journal and recover to the exact prior bytes, modes, receipt and registration state. The same reviewed plan must then apply successfully. The test loops over the actual write count rather than assuming one artifact count remains forever.

The matrix also changes 25 independent plan fields, including versions, root/scope, previous receipt, authority/registry/config observations, graph, mapping, lock, decisions and target operations. Every tampered plan is rejected with an unchanged environment. Ten managed-target cases combine content edits, mode changes, missing files, symlinks and directories with protect/overwrite decisions. Protection preserves edits; approved replacements retain actual originals in receipt backups; symlinks/directories remain unsafe under overwrite.

Existing recipe and installed-wheel tests additionally cover two-home lock ownership, malformed contracts and cache bytes, origin conflicts, source trust, unsupported capabilities, required slots, denied reactivation, offline restoration, independent edits during recovery, real process death at write/receipt boundaries and concurrent apply processes. Authority generations and the monotonic deny ledger stay independent of historical receipt bytes.

## Interactive and distribution evidence

`tests/test_collection_recipes.py` validates all 70 collected items in both user and project scope: **140 real-item cases**, including explicit refusal of private/context scope violations. It checks the 18-item starter closure, all 49 public items together, native role TOML, unconditional policy aggregation, HTML/Markdown assets, typed imported links, provenance hashes and complete licensing. A headless workspace displays the 70-item collection, suppresses 20 private contracts and separately confirms or cancels exact Hook approval. Source imports require explicit trusted scope bindings even when bytes are already retained.

`tests/test_collection_transactions.py` checks every actual Hook write boundary and the receipt boundary with ordinary/interruption failures. Neither registration nor executable approval can commit early. It also checks changed-digest refusal, interpreter retention, approval separation across scopes, offline restore, lost approval blocking receipt/journal reactivation, contributor denial and rollback of an overwritten native policy aggregate to original human instructions. Native-role serialization cases cover non-BMP Unicode, quotes, backslashes, newlines and attempted configuration injection. Essential standalone read-only requests are refused in accordance with the current Codex role contract; a role file does not establish sandbox enforcement.

The stateful harness canonicalizes its own temporary directory. A symlinked ambient temp directory, common on macOS through /var, caused UNSAFE_PATH before any generated action in a local reproduction. A permanent regression verifies the harness fix without relaxing the engine's rejection of symlinked operator paths. Later hosted macOS logs identified four PTY harness failures after the CLI had exited successfully: the controlling session had ended before the restoration assertion, making slave ioctls unavailable. The terminal harness now retains its session leader through the assertion, then releases it through a private pipe; the real CLI, keys, resize, exit status and restored attributes are still checked on both platforms. Hosted results are recorded in the PR.

`tests/test_recipe_tui.py` uses Textual's real widgets with headless keyboard/pointer events at 140×42, 100×32, 80×24 and 64×20, plus resize transitions. It checks search/filter neutrality, direct/dependency selection, Enter event handling, full identity inspection, help, themes, NO_COLOR, dirty exit cancellation, explicit trust and cache-only source staging, atomic alias rejection, choosing an older accepted snapshot, plan invalidation/export, protected drift and separate replacement review, receipt restoration, recovery cancellation/confirmation and busy mutation shutdown. Machine and UI drafts produce byte-equivalent plans. Private sentinel content and terminal control/bidi text have separate redaction checks. Launch-option tests reject hidden/ignored choices before environment access.

Four wheel-installed POSIX PTY cases combine user/project scope with color/NO_COLOR. They execute outside the checkout with a credential-free environment allowlist, send real terminal key sequences, resize the terminal, open/close help, exit through F10 and verify termios restoration. A fresh browse-and-exit leaves the temporary home and project empty. These checks exercise the native terminal driver rather than injecting headless widget events. They are bounded smoke journeys; the larger mutation and cancellation matrix uses headless widgets and the shared real Engine.

The workspace uses literal, bounded metadata and read-only public previews, with dark/light/monochrome themes and responsive layout. [Browse](screenshots/recipe-workspace.png) and [review](screenshots/recipe-review.png) screenshots show synthetic fixture content. A visual inspection of these images is separate from deterministic behavior assertions.

The [collected-workflow view](screenshots/collected-recipes.png) uses the actual migrated public content and source metadata in a disposable environment. No provider files were installed for that screenshot. The installed-wheel collection journey also prepares all seven sources and installs the starter plus optional roles, design, travel, music and HTML assets outside the checkout, verifies doctor/idempotence and checks the machine executable-approval diagnostic.

## Reproduce and remaining limits

The collection transition passed a **903-test full-suite checkpoint** on Linux/Python 3.12, with all deterministic generator examples, stateful sequences and the installed-wheel collection journey successful. The final project-owned import-pin regression and related engine/transaction checks passed together (**55 tests**). The four terminal journeys are rerun after the session-lifetime harness fix; hosted platform results are recorded in the PR. This is structural and transaction evidence, not an authenticated model or provider-discovery run.

Local acceptance on 13 October 2026 used Python 3.12 on Linux: **682 tests passed** in the full suite, with Hypothesis reporting 400 successful graph examples, 400 successful name examples and 20 successful stateful sequences. After the final workspace and selector refinements, all **34 TUI checks**, **91 recipe/transaction checks** and **four wheel-installed PTY cases** were rerun successfully. Ruff lint/formatting and clean wheel/sdist builds are the separate submission gates. Timing is recorded as a run observation, not a performance guarantee.

```sh
uv sync --locked
uv run pytest tests/test_recipe_matrix.py --hypothesis-show-statistics -q
uv run pytest tests/test_recipe_transactions.py tests/test_recipe_tui.py -q
uv run pytest tests/test_installed_e2e.py -k recipe -q
uv run python scripts/build_recipes.py --check
uv run pytest -q
uv run ruff check cli tests packages/hooks evals scripts/build_templates.py scripts/build_recipes.py
uv run ruff format --check cli tests packages/hooks evals scripts/build_templates.py scripts/build_recipes.py
uv build
```

Wheel installation requires package-registry access or a populated uv cache. Set UV_CACHE_DIR to a writable location when needed. Safe plan export and the exercised path/lock/recovery boundary require POSIX. The repository CI declares Python 3.11/3.14 on Linux/macOS; a local passing run is not evidence that all hosted jobs passed. Terminal images are snapshots, not screenshot-diff acceptance baselines.

This evidence does not qualify native model invocation, provider precedence, prompt safety, authenticated host discovery, screen readers, all terminal emulators, long-duration resource stress, native Windows lifecycle or future protocols. Git transport, private context loading and enforced standalone agent sandbox restrictions remain unsupported. The 20 private contracts are preserved without transferring any bound facts or grants. Extend the finite matrix when adding a new kind, adapter, grant, source transport or transaction effect; preserve independent expectations and actual postcondition checks instead of adding tests that merely echo implementation internals.

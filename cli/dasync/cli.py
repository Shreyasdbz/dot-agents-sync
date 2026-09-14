"""Human and JSON interfaces over one plan/apply engine."""

import argparse
import copy
import sys
from pathlib import Path

from . import __version__
from .adapters import capabilities
from .catalog import Catalog, pin
from .config import Environment, Scope, default_project_id, initial, load_config
from .contracts import SCHEMAS, validate
from .engine import Engine
from .errors import DasyncError
from .io import canonical, parse, read
from .sources import fetch, is_remote

AI_INSTRUCTIONS = """Use dasync capabilities --json and dasync schema before choosing options.
Inspect status with --scope and an absolute --path. Use list and explain to inspect selections.
Preview changes with --dry-run --json or plan ACTION; inspect every operation and capability warning.
Apply only the reviewed plan using apply --plan FILE. Never edit generated provider output.
--yes accepts ordinary confirmation only; --trust-source and --conflict overwrite are separate decisions.
Keep private context bytes out of prompts, logs, plans and reports. Locate bindings only for authorized consumers.
Run doctor after applying. Report the actual receipt and diagnostics; do not claim native model behavior was tested by structural checks.
"""


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise DasyncError("USAGE", message)


def parser():
    p = Parser(prog="dasync", description="Portable AI workflow configuration")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument(
        "command",
        choices=[
            "setup",
            "configure",
            "sync",
            "update",
            "status",
            "doctor",
            "repair",
            "rollback",
            "plan",
            "apply",
            "list",
            "search",
            "explain",
            "diff",
            "capabilities",
            "schema",
            "ai",
            "context",
            "validate",
        ],
    )
    p.add_argument("subject", nargs="?")
    p.add_argument("item", nargs="?")
    p.add_argument("--scope", choices=["user", "project"])
    p.add_argument("--path")
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-input", action="store_true")
    p.add_argument("--yes", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--source", help="Local Git checkout or local catalog directory")
    p.add_argument("--source-kind", choices=["git", "local"], default="git")
    p.add_argument("--revision", help="Full immutable commit ID (Git sources)")
    p.add_argument("--trust-source", action="store_true")
    p.add_argument("--project", help="Stable portable project ID")
    p.add_argument("--provider", action="append", choices=["codex", "claude", "cursor"])
    p.add_argument("--enable", action="append", default=[])
    p.add_argument("--disable", action="append", default=[])
    p.add_argument("--profile", action="append", default=[])
    p.add_argument("--remove-profile", action="append", default=[])
    p.add_argument("--inherit-user", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--allow-context", action="append", default=[])
    p.add_argument("--capability", action="append", default=[])
    p.add_argument("--conflict", choices=["protect", "overwrite"], default="protect")
    p.add_argument("--config-only", action="store_true")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--plan", dest="plan_file")
    p.add_argument("--receipt")
    p.add_argument(
        "--before",
        action="store_true",
        help="Restore the state before the named receipt, including overwritten unmanaged backups",
    )
    p.add_argument("--recover", action="store_true")
    p.add_argument("--effective", action="store_true")
    p.add_argument("--consumer")
    p.add_argument("--allow-private-path", action="store_true")
    p.add_argument("--bind-context", action="append", default=[], metavar="ID=PATH")
    p.add_argument("--grant-project", action="append", default=[])
    p.add_argument("--binding-provider", action="append", choices=["codex", "claude", "cursor"], default=[])
    p.add_argument("--approve-executable", action="append", default=[], metavar="SHA256")
    return p


def emit(result, machine=False):
    if machine:
        print(canonical({"version": 1, "ok": True, "result": result}).decode(), end="")
    elif isinstance(result, str):
        print(result)
    else:
        print(canonical(result).decode(), end="")


def confirm(args, plan):
    if args.yes:
        return
    if args.no_input or args.json or not sys.stdin.isatty():
        raise DasyncError("CONFIRMATION_REQUIRED", "Review the plan and pass --yes to apply")
    print(canonical(plan).decode(), file=sys.stderr)
    if input("Apply these changes? [y/N] ").strip().lower() != "y":
        raise DasyncError("CANCELLED", "No changes applied")


def configure_interactive(config, catalog):
    from .tui import select

    return select(config, catalog)


def run(args):
    operation = args.subject if args.command == "plan" else args.command
    selection_flags = any(
        (
            args.enable,
            args.disable,
            args.profile,
            args.remove_profile,
            args.allow_context,
            args.capability,
            args.bind_context,
            args.grant_project,
            args.binding_provider,
            args.approve_executable,
            args.provider,
            args.project,
            args.inherit_user is not None,
        )
    )
    if selection_flags and operation not in ("setup", "configure"):
        raise DasyncError("USAGE", "Selection changes require setup or configure")
    if args.recover and operation != "repair":
        raise DasyncError("USAGE", "--recover is only valid with repair")
    if (args.before or args.receipt) and operation != "rollback":
        raise DasyncError("USAGE", "Receipt selection is only valid with rollback")
    if args.config_only and operation not in ("setup", "configure", "update"):
        raise DasyncError("USAGE", "--config-only requires setup, configure, or update")
    if args.command == "capabilities":
        return capabilities()
    if args.command == "schema":
        if args.subject is None:
            return sorted(SCHEMAS)
        if args.subject not in SCHEMAS:
            raise DasyncError("USAGE", "Unknown schema")
        return {"$schema": "https://json-schema.org/draft/2020-12/schema", **SCHEMAS[args.subject]}
    if args.command == "ai" and args.subject == "instructions":
        return AI_INSTRUCTIONS
    if args.command == "validate":
        if args.subject not in SCHEMAS or not args.path:
            raise DasyncError("USAGE", "Use validate SCHEMA --path FILE")
        validate(args.subject, parse(read(Path(args.path))))
        return {"valid": True, "schema": args.subject}
    env = Environment.current()
    if args.command in ("list", "search") and args.source:
        catalog = Catalog(pin(args.source, args.source_kind, args.revision))
    else:
        scope = Scope.get(env, args.scope, args.path)
        engine = Engine(env, scope)
        if args.command in ("list", "search", "explain"):
            catalog = Catalog(load_config(scope.config)["source"])
    if args.command in ("list", "search"):
        query = (args.subject or "").lower()
        return {
            "packages": [
                {
                    "id": p.id,
                    "digest": p.digest,
                    "kind": p.manifest["kind"],
                    "description": p.manifest["description"],
                    "requires": p.manifest.get("requires", {}),
                    "suggests": p.manifest.get("suggests", []),
                }
                for p in catalog.packages.values()
                if query
                in (
                    p.id + " " + p.manifest["description"] + " " + " ".join(p.manifest.get("tags", []))
                ).lower()
            ],
            "profiles": list(catalog.profiles.values()),
            "source_digest": catalog.digest,
        }
    if args.command in ("status", "doctor") or (args.command == "ai" and args.subject == "environment"):
        status = engine.status()
        if args.command == "doctor":
            status["healthy"] = (
                status["configured"]
                and not status.get("diagnostic")
                and not status["pending_recovery"]
                and status.get("pending_changes", 0) == 0
            )
        return status
    if args.command == "context":
        if args.subject != "locate" or not args.item or not args.allow_private_path:
            raise DasyncError(
                "USAGE", "Use context locate ID --consumer ID --allow-private-path with an explicit scope"
            )
        from .resolver import resolve

        config = load_config(scope.config)
        user = load_config(env.config, required=False)
        selected, _, bindings = resolve(Catalog(config["source"]), config, scope, user)
        if args.item not in bindings:
            raise DasyncError("CONTEXT_MISSING", "Private context is not selected and authorized")
        policy = selected[args.item].manifest["context"]
        if not args.consumer or (policy["consumers"] and args.consumer not in policy["consumers"]):
            raise DasyncError("PRIVATE_CONTEXT", "Context consumer must be explicitly authorized")
        path = Path(bindings[args.item]["path"])
        if not path.is_absolute() or not path.is_file():
            raise DasyncError("CONTEXT_MISSING", "Bound context path is unavailable")
        return {"id": args.item, "path": str(path), "consumer": args.consumer}
    if args.command == "explain":
        plan, _ = engine.build({"operation": "sync"})
        return {
            "packages": [p for p in plan["graph"]["packages"] if not args.subject or p["id"] == args.subject],
            "edges": plan["graph"]["edges"],
            "decisions": plan["decisions"],
        }
    if args.command == "repair" and args.recover:
        if args.dry_run:
            return {"pending": [j["id"] for j in engine.state.pending()]}
        confirm(args, {"recover": [j["id"] for j in engine.state.pending()]})
        return engine.state.recover(scope.key, engine._validate_target)
    if args.command == "apply":
        if not args.plan_file:
            raise DasyncError("USAGE", "apply requires --plan FILE")
        value = parse(read(Path(args.plan_file)))
        plan = value.get("result", value)
        if args.dry_run:
            fresh, _ = engine.build(plan["request"])
            if canonical(fresh) != canonical(plan):
                raise DasyncError("PLAN_INVALIDATED", "Plan inputs changed")
            return plan
        confirm(args, plan)
        return engine.apply(plan)
    operation = args.subject if args.command == "plan" else "sync" if args.command == "diff" else args.command
    request = {"operation": operation}
    if args.conflict != "protect":
        request["conflict"] = args.conflict
    if operation == "setup":
        if not args.source:
            raise DasyncError("USAGE", "setup requires --source CATALOG")
        if is_remote(args.source):
            if not args.trust_source:
                raise DasyncError("TRUST_REQUIRED", "Review the source and pass --trust-source")
            if not args.dry_run and args.command != "plan":
                if not args.yes:
                    confirm(args, {"fetch_source": args.source})
                fetch(args.source, env.cache)
        source = pin(args.source, args.source_kind, args.revision, env.cache)
        request["config"] = initial(
            args.project or ("user" if scope.kind == "user" else default_project_id(scope.root)),
            source,
            args.provider or ["codex"],
            args.enable,
            args.profile,
        )
        request["trust_source"] = args.trust_source
        request["config"]["inherit_user"] = bool(args.inherit_user)
    elif operation in ("configure", "update"):
        config = copy.deepcopy(load_config(scope.config))
        if operation == "update":
            source = config["source"]
            if source["kind"] == "git" and not args.revision:
                if args.dry_run or args.command == "plan":
                    raise DasyncError(
                        "REVISION_REQUIRED",
                        "An update preview requires --revision already present locally; it never fetches",
                    )
                revision = fetch(source["location"], env.cache)
            else:
                revision = args.revision
            config["source"] = pin(source["location"], source["kind"], revision, env.cache)
            request["config_only"] = args.config_only
        else:
            has_changes = any(
                (
                    args.enable,
                    args.disable,
                    args.profile,
                    args.remove_profile,
                    args.provider,
                    args.allow_context,
                    args.capability,
                    args.inherit_user is not None,
                    args.bind_context,
                    args.approve_executable,
                )
            )
            if not has_changes:
                if args.no_input or args.json or not sys.stdin.isatty():
                    raise DasyncError("USAGE", "configure requires explicit changes in machine mode")
                config = configure_interactive(config, Catalog(config["source"]))
            config["packages"] = sorted((set(config["packages"]) | set(args.enable)) - set(args.disable))
            config["disabled"] = sorted((set(config["disabled"]) | set(args.disable)) - set(args.enable))
            config["profiles"] = sorted(
                (set(config["profiles"]) | set(args.profile)) - set(args.remove_profile)
            )
            request["config_only"] = not args.apply
        if args.bind_context:
            if scope.kind != "user":
                raise DasyncError(
                    "PRIVATE_CONTEXT", "Bind private context in user scope, then allow its ID in the project"
                )
            for assignment in args.bind_context:
                key, separator, path = assignment.partition("=")
                if not separator or not Path(path).is_absolute():
                    raise DasyncError("USAGE", "Binding requires ID=absolute-path")
                config.setdefault("bindings", {})[key] = {
                    "path": path,
                    "projects": args.grant_project,
                    "providers": args.binding_provider,
                }
        if args.approve_executable:
            config["approved_executables"] = sorted(
                set(config.get("approved_executables", [])) | set(args.approve_executable)
            )
        if args.provider:
            config["providers"] = args.provider
        if args.inherit_user is not None:
            config["inherit_user"] = args.inherit_user
        config["contexts"] = sorted(set(config.get("contexts", [])) | set(args.allow_context))
        config["capabilities"] = sorted(set(config.get("capabilities", [])) | set(args.capability))
        request["config"] = config
    elif operation == "rollback":
        if not args.receipt:
            raise DasyncError("USAGE", "rollback requires --receipt ID")
        request["receipt"] = args.receipt
        if args.before:
            request["before_receipt"] = True
    if operation == "setup":
        request["config"]["capabilities"] = args.capability
        request["config"]["contexts"] = args.allow_context
    plan, _ = engine.build(request)
    if args.command in ("plan", "diff") or args.dry_run:
        return plan
    confirm(args, plan)
    return engine.apply(plan)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    machine = "--json" in argv
    try:
        result = run(parser().parse_args(argv))
        emit(result, machine)
        return 1 if isinstance(result, dict) and result.get("healthy") is False else 0
    except DasyncError as exc:
        if machine:
            print(canonical({"version": 1, "ok": False, "error": exc.as_dict()}).decode(), end="")
        else:
            print(f"{exc.code}: {exc}", file=sys.stderr)
            if exc.hint:
                print(exc.hint, file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        # No raw exception text: it may contain a private value or path.
        error = DasyncError("OPERATION_FAILED", f"Operation could not complete ({type(exc).__name__})")
        if machine:
            print(canonical({"version": 1, "ok": False, "error": error.as_dict()}).decode(), end="")
        else:
            print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

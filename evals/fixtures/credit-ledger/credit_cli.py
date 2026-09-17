"""Console boundary for registered credit operations."""

import argparse
import importlib
import json
import tomllib
from pathlib import Path

from ledger_store import LedgerStore


def main():
    """Dispatch one operation using the checked-in handler registration."""
    parser = argparse.ArgumentParser()
    parser.add_argument("operation")
    parser.add_argument("--database", required=True)
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--event", required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--amount", required=True, type=int)
    args = parser.parse_args()
    config = tomllib.loads(Path(__file__).with_name("pyproject.toml").read_text())
    module, name = config["tool"]["credits"]["handlers"][args.operation].split(":")
    handler = getattr(importlib.import_module(module), name)
    store = LedgerStore(args.database)
    try:
        balance = handler(store, args.tenant, args.event, args.account, args.amount)
        print(json.dumps({"balance": balance}))
    finally:
        store.close()


if __name__ == "__main__":
    main()

"""Build/check the canonical recipe projection from the preserved collected catalog."""

import argparse
from pathlib import Path

from dasync.collection import compile_collection

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs, report = compile_collection(ROOT)
    target = ROOT / "recipes"
    stale = []
    for name, content in outputs.items():
        path = target / name
        if args.check:
            if not path.is_file() or path.read_bytes() != content:
                stale.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    expected = set(outputs)
    # README is authored documentation; unexpected generated files are never silently purged.
    extras = {str(p.relative_to(target)) for p in target.rglob("*") if p.is_file()} - expected - {"README.md"}
    if stale or extras:
        raise SystemExit("Recipe projection differs: " + ", ".join(sorted([*stale, *extras])))
    print(
        f"{'Checked' if args.check else 'Built'} {len(report['items'])} items in 7 recipes; starter closure {len(report['starter_items'])}"
    )


if __name__ == "__main__":
    main()

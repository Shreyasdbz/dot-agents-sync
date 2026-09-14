"""Deterministically inline canonical UI assets. Emit an apply_patch patch; never edit sources."""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "proposal": "design-proposal/proposal.html",
    "review": "pr-review/report.html",
    "trip": "trip-publish/trip.html",
    "deck": "pitch-deck/deck.html",
}
FRAGMENTS = {
    "travel-expenses": "trip-publish/components/expenses.html",
    "travel-copy-details": "trip-publish/components/copy-details.html",
    "route-map": "trip-publish/components/route-map.html",
    "timeline": "trip-publish/components/timeline.html",
    "cost-summary": "trip-publish/components/cost-summary.html",
    "finding": "pr-review/components/finding.html",
    "comparison": "design-proposal/components/comparison.html",
    "travel-flight": "trip-publish/components/flight.html",
    "travel-transfer": "trip-publish/components/transfer.html",
    "travel-stay": "trip-publish/components/stay.html",
    "travelers": "trip-publish/components/travelers.html",
    "travel-activity": "trip-publish/components/activity.html",
    "travel-disruption": "trip-publish/components/disruption.html",
    "travel-rail": "trip-publish/components/rail.html",
    "travel-vehicle": "trip-publish/components/vehicle.html",
    "travel-rental": "trip-publish/components/rental-stay.html",
    "travel-family": "trip-publish/components/family-stay.html",
}
TECHNICAL_FRAGMENTS = ("chart", "line-chart", "data-flow", "entity-relationship", "sequence", "dense-context")


def render_all():
    base = ROOT / "template-system"
    css = (base / "ui.css").read_text()
    js = (base / "ui.js").read_text()
    icons = json.loads((base / "icons.json").read_text())

    def compose(source):
        content = re.sub(
            r"\{\{component:([a-z-]+)\}\}",
            lambda match: (base / "components" / (match[1] + ".html")).read_text(),
            source,
        )
        content = re.sub(
            r"\{\{icon:([a-z-]+)\}\}",
            lambda match: (
                '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
                + icons[match[1]]
                + "</svg>"
            ),
            content,
        )
        behavior = js.rsplit("})();", 1)[0]
        for marker, name in (
            ('class="slide', "deck"),
            ("data-sequence", "sequence"),
            ('class="travel"', "travel"),
        ):
            if marker in content:
                behavior += (base / "behaviors" / (name + ".js")).read_text()
        behavior += "})();"
        page_css = css
        if 'class="travel"' in content:
            page_css += (base / "travel.css").read_text()
        else:
            page_css += (base / "editorial.css").read_text()
        return content.replace("{{styles}}", page_css).replace("{{interactions}}", behavior)

    outputs = {
        ROOT / "packages/templates" / destination: compose((base / "pages" / (name + ".html")).read_text())
        for name, destination in PAGES.items()
    }
    outputs.update(
        {
            ROOT / "packages/templates" / destination: (base / "components" / (name + ".html")).read_text()
            for name, destination in FRAGMENTS.items()
        }
    )
    for package in ("pitch-deck", "design-proposal"):
        for name in TECHNICAL_FRAGMENTS:
            outputs[ROOT / "packages/templates" / package / "components" / (name + ".html")] = (
                base / "components" / (name + ".html")
            ).read_text()
    return outputs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--page", choices=PAGES)
    args = parser.parse_args()
    changes = [
        (path, content)
        for path, content in render_all().items()
        if not path.exists() or path.read_text() != content
    ]
    if args.page:
        package = Path(PAGES[args.page]).parts[0]
        changes = [
            (path, content)
            for path, content in changes
            if path.relative_to(ROOT / "packages/templates").parts[0] == package
        ]
    if args.check:
        for path, _ in changes:
            print("Stale generated template:", path.relative_to(ROOT))
        raise SystemExit(bool(changes))
    if changes:
        print("*** Begin Patch")
        for path, content in changes:
            if path.exists():
                print("*** Update File:", path)
                print("@@")
                for line in path.read_text().splitlines():
                    print("-" + line)
            else:
                print("*** Add File:", path)
            for line in content.splitlines():
                print("+" + line)
        print("*** End Patch")

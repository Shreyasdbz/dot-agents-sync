# Third-party notices

The root [MIT license](LICENSE) covers original dasync code and catalog content. It does not replace the licenses or ownership of third-party material.

## SwiftUI guidance

[`packages/skills/ui-design/swiftui.md`](packages/skills/ui-design/swiftui.md) adapts Liquid Glass and adaptive-layout guidance from [FloWritesCode/fwc-swiftui-skills](https://github.com/FloWritesCode/fwc-swiftui-skills/tree/c2454e6948175e25e61c107c6dc7ebf03e291dfe), pinned to commit `c2454e6948175e25e61c107c6dc7ebf03e291dfe`.

Copyright (c) 2026 FloWritesCode. Licensed under MIT; the [complete upstream notice](packages/skills/ui-design/LICENSE.fwc-swiftui-skills.txt) is declared in the skill manifest and travels with its provider-native output. Preserve that notice when redistributing the adapted guidance.

## Separately installed dependencies

Python runtime/development dependencies and browser-test dependencies retain their own licenses. They are installed separately, not relicensed by this repository's MIT declaration. `uv.lock` and `scripts/browser/package-lock.json` identify the resolved dependencies.

The CLI wheel does not bundle the workflow catalog, browser binaries, or dependency environments. Distributing a combined environment requires its own dependency-license review.

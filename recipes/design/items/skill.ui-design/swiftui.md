# SwiftUI design branch

Load only for SwiftUI or Apple-platform interface work.

## Adapt to space before hardware

Make layout follow the usable container, not `UIDevice`, `UIScreen.main.bounds`, model names, or orientation. Prefer system navigation and containers, adaptive grids, `ViewThatFits`, `AnyLayout`, size classes, and exact geometry in that order. A list-detail flow normally belongs in `NavigationSplitView`; repeated content normally uses `GridItem(.adaptive(minimum:))`.

Keep navigation, selection, editing, scroll, and playback state above layout choices so resizing does not become an application-state transition. Additional width should reveal useful hierarchy such as a detail pane or inspector, not produce longer text lines or empty stretching. Move fold- or safe-area-sensitive content locally. Use hinge state only for a genuinely physical interaction, never as a proxy for columns or navigation. Do not add device-exclusive APIs or guessed dimensions without the matching SDK and simulator evidence.

## Use native visual materials

Inspect the deployment target and installed SDK before choosing an API. On iOS 26+, use native Liquid Glass rather than reconstructing it with blur, material, stroke, and shadow stacks:

- Use `.buttonStyle(.glass)` for neutral actions and `.glassProminent` for the primary tinted action; shape buttons with `.buttonBorderShape()`.
- Apply layout and appearance modifiers before `.glassEffect`, and use `.interactive()` only on interactive surfaces.
- Group adjacent effects in `GlassEffectContainer`; keep glass out of scrolling rows and use it on stable controls or chrome.
- Prefer `.safeAreaBar` for fixed bottom chrome. Apply `.sharedBackgroundVisibility(.hidden)` to the `ToolbarItem`, not its inner label, when shared toolbar glass is unwanted.
- Gate iOS 26 APIs and provide native older-system fallbacks such as bordered button styles, material backgrounds, or `safeAreaInset`.

Verify resizing across narrow, intermediate, and wide containers. For device- or SDK-specific behavior, run the matching simulator when available; otherwise limit the change to general adaptability and mark the specialized behavior unverified.

Adapted from [fwc-swiftui-skills](https://github.com/FloWritesCode/fwc-swiftui-skills) at `c2454e6948175e25e61c107c6dc7ebf03e291dfe`; copyright (c) 2026 FloWritesCode. The [MIT license](LICENSE.fwc-swiftui-skills.txt) accompanies this reference.

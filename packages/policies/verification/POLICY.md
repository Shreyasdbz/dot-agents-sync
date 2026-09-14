# Testing and verification

Verify behavior at its source of truth. Use focused failing tests when they demonstrate the requested change. Distinguish static validation, mocked tests, local execution, and external outcomes. Report commands and evidence sufficient to reproduce material checks. Do not equate attempted actions with successful outcomes.

Unit tests cover expected results and adversarial behavior: invalid or boundary inputs, plausible failure paths and violated assumptions relevant to the changed contract. Use integration tests for affected boundaries and end-to-end checks for complete critical flows; mocks alone do not establish integration. Choose cases by actual risk, not speculative scale or a made-up coverage quota. Existing project gates still apply.

For UI, distinguish interactive browser inspection from maintained automated browser tests. Prefer a browser-driven build-and-check loop, using an available Playwright CLI or browser-control tool to inspect organization, layout, styles, flows and important viewport/states. Automated browser tests are not mandatory for every small UI edit; add or extend them for substantial changes such as multi-screen flows, shared navigation or broad interaction changes, and for critical regressions. A screenshot alone does not test interactions. If browser access is unavailable, state what remains visually unverified.

Start prototypes and new slices with working behavior and basic usable structure before visual polish. Keep initial checks light and focused, then expand failure-path, integration and end-to-end coverage as behavior stabilizes and before claiming the intended delivery standard. Prototype status does not waive safety or justify reporting untested behavior as verified.

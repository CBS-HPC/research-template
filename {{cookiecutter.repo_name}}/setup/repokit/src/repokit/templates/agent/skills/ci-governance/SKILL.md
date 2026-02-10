---
name: ci-governance
description: Keep CI aligned with project language and version-control mode, and enforce reproducibility checks.
---

# ci-governance

## Workflow
1. Enable or disable CI via repokit:
   - repokit ci-control --on
   - repokit ci-control --off
2. Verify workflow file reflects active toolchain.
3. Ensure checks include lint, tests, and (where configured) type checks.

## Verify
- CI config matches selected language and VC mode.
- Commands in CI are runnable from a clean environment.

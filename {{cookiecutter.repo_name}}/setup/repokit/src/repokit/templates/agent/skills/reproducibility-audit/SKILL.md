---
name: reproducibility-audit
description: Audit project reproducibility by checking environment, dependencies, provenance, and a small end-to-end run.
---

# reproducibility-audit

## Workflow
1. Verify dependency files are synchronized.
2. Verify DMP and dataset metadata are current.
3. Run a minimal pipeline/test command from a clean environment.
4. Record provenance details (versions, parameters, output paths).

## Verify
- Another user can reproduce a minimal run using documented steps.
- No hidden local assumptions remain in scripts or docs.

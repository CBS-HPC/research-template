---
name: project-hygiene
description: Run lint/type/test checks, auto-fix safe issues, and iterate until clean or blocked with a clear fix list.
---

# project-hygiene

## Workflow
1. Run baseline checks:
   - repokit lint
   - ruff check .
   - ruff format --check .
   - mypy src
   - pytest
2. Apply safe fixes:
   - ruff check --fix .
   - ruff format .
3. Re-run all checks.

## Completion
- All configured checks pass, or
- Remaining failures are documented with exact files and required code changes.

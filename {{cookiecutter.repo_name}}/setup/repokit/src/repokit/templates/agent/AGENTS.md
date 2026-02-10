---
purpose: " Primary agent memory file for Repokit\
version: 1.0.0
status: template
---
# AGENTS.md

## Operating principles

- Prefer small, reversible diffs and explicit acceptance criteria.
- Keep context lean: load only files needed for the current task.
- Treat research artifacts as first class outputs: data, code, metadata, and provenance.
- Do not add secrets or read .env files.
- Prefer package layouts (src/ + tests) over ad-hoc scripts.
- Default Python toolchain: uv + pytest + ruff + mypy/pyright.
- Use git actively: commit small, push regularly, and keep PRs focused.
- Data versioning: keep large data out of Git; use DVC or Datalad when needed.

## Session workflow

1. Read TASKS.md and AGENTS.md before coding.
2. Ask clarifying questions if requirements are unclear.
3. Propose a 3-5 step plan before editing.
4. Implement minimal change and run tests.
5. Update TASKS.md with plan, progress, and decisions.
6. Commit at natural breakpoints with focused messages.

## Research quality gates

- Data governance: document data sources, licenses, and access constraints.
- Provenance: record parameters, environment, and versions for outputs.
- Reproducibility: scripts should run from a clean environment.
- Traceability: link tasks to PRD FR/NFR IDs and record decisions.
- CI: lint, type-check, and tests must pass before merge.

## Guardrails

- No network calls unless PRD explicitly allows it.
- Do not write outside the repo.
- Prefer standard, well maintained libraries.

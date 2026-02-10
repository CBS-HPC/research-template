---
name: lint-language-profiles
description: Apply language-aware lint profiles for Python, R, Stata, and MATLAB projects.
---

# lint-language-profiles

## Python
- ruff check .
- ruff format --check .
- mypy src
- pytest

## R
- Run Rscript -e  lintr::lint_dir R  if R sources exist.
- Run project test command if present.

## Stata
- Run project lint script (src/linting.do) and inspect output logs.

## MATLAB
- Run project lint script (src/linting.m) and parse checkcode output.

## Mixed projects
- Run all relevant profiles and aggregate failures before fixing.

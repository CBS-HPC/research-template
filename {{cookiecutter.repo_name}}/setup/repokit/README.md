# repokit

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/CBS-HPC/repokit/actions/workflows/ci.yml/badge.svg)](https://github.com/CBS-HPC/repokit/actions/workflows/ci.yml)

Core utilities for the **Research Template** setup flow. `repokit` provides reusable setup helpers, CLI tools, and automation used by the cookiecutter template. It composes smaller, independent packages:

- **repokit-common**: shared utilities (env, prompts, paths, config helpers)
- **repokit-backup**: rclone-based backup tooling
- **repokit-dmp**: data management plan (DMP) tooling

## Highlights

- Setup automation for research projects
- CLI helpers for CI, dependencies, templates, repos, and README generation
- Integrates with `repokit-backup` and `repokit-dmp`

## Installation

From source:

```bash
git clone https://github.com/CBS-HPC/repokit.git
cd repokit
pip install -e .
```

If you cloned with submodules:

```bash
git submodule update --init --recursive
```

## CLI (selected)

```bash
ci-control --on
update-readme
update-dependencies
backup --help
set-dataset --help
dmp-update
```

## Development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest
ruff check .
```

## License

MIT

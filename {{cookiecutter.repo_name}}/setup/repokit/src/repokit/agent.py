from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from repokit_common import PROJECT_ROOT

DEFAULT_SOURCE = "https://github.com/kasperjunge/agent-resources"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates" / "agent"


def _find_platform_root(repo_root: Path, platform: str) -> Path:
    candidates = [
        repo_root / platform,
        repo_root / "platforms" / platform,
        repo_root / "templates" / platform,
        repo_root / "skills" / platform,
        repo_root / "agents" / platform,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return repo_root


def _platform_dir(dest: Path, platform: str) -> Path | None:
    if platform == "codex":
        return dest / ".codex"
    if platform == "claude":
        return dest / ".claude"
    if platform == "cursor":
        return dest / ".cursor"
    return None


def _skills_dest(dest: Path, platform: str) -> Path:
    platform_root = _platform_dir(dest, platform)
    if platform_root:
        return platform_root / "skills"
    return dest / "skills"


def _copy_tree(src: Path, dest: Path, force: bool) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dest / item.name
        if target.exists():
            if not force:
                continue
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


def _append_unique_lines(path: Path, lines: list[str]) -> None:
    existing = []
    if path.exists():
        existing = path.read_text(encoding="utf-8").splitlines()
    existing_set = {line.strip() for line in existing if line.strip()}
    to_add = [line for line in lines if line.strip() and line.strip() not in existing_set]
    if not to_add:
        return
    content = existing + ([""] if existing and existing[-1].strip() else []) + to_add + [""]
    path.write_text("\n".join(content), encoding="utf-8")


def _copy_template_file(name: str, dest: Path, force: bool) -> None:
    src = TEMPLATE_DIR / name
    if not src.exists():
        return
    target = dest / name
    if target.exists() and not force:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target)


def _copy_skills(dest: Path, platform: str, force: bool) -> None:
    skills_dir = TEMPLATE_DIR / "skills"
    if not skills_dir.exists():
        return
    _copy_tree(skills_dir, _skills_dest(dest, platform), force)


def _apply_local_templates(dest: Path, platform: str, force: bool) -> None:
    platform_root = _platform_dir(dest, platform)
    if platform_root:
        platform_root.mkdir(parents=True, exist_ok=True)

    _copy_template_file("AGENTS.md", dest, force)
    _copy_template_file("TASKS.md", dest, force)
    _copy_template_file(".codexignore", dest, force)
    _copy_template_file(".claudeignore", dest, force)
    _copy_template_file(".cursorignore", dest, force)

    if platform == "claude":
        _copy_template_file("CLAUDE.md", dest, force)

    gitignore_template = TEMPLATE_DIR / ".gitignore"
    if gitignore_template.exists():
        lines = gitignore_template.read_text(encoding="utf-8").splitlines()
        _append_unique_lines(dest / ".gitignore", lines)

    _copy_skills(dest, platform, force)


def _run_agr_init(dest: Path, guided: bool) -> None:
    agr = shutil.which("agr")
    if not agr:
        print("agr is not available on PATH; skipping agr init.")
        return

    cmd = [agr, "init"]
    if guided:
        cmd.append("-i")

    subprocess.run(cmd, check=True, cwd=dest)


def init_agent_resources(source: str, platform: str, dest: Path, force: bool, guided: bool) -> None:
    _apply_local_templates(dest, platform, force)
    with tempfile.TemporaryDirectory(prefix="repokit-agent-") as tmp:
        repo_root = Path(tmp) / "repo"
        subprocess.run(["git", "clone", "--depth", "1", source, str(repo_root)], check=True)
        platform_root = _find_platform_root(repo_root, platform)
        _copy_tree(platform_root, dest, force=force)

    _run_agr_init(dest, guided=guided)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="repokit agent", description="Initialize agent resources")
    parser.add_argument("action", choices=["init"])
    parser.add_argument("--platform", choices=["codex", "claude", "cursor"], default="codex")
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--dest", default=None)
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--agr-guided", action="store_true", help="Run agr init -i after scaffolding")

    ns, extra = parser.parse_known_args(argv)
    if extra:
        print(f"Unexpected arguments: {extra}", file=sys.stderr)
        sys.exit(2)

    dest = Path(ns.dest).resolve() if ns.dest else PROJECT_ROOT
    if ns.action == "init":
        init_agent_resources(ns.source, ns.platform, dest, ns.force, guided=ns.agr_guided)


if __name__ == "__main__":
    main()

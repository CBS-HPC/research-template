import os
import re
import shutil
import subprocess
import pathlib 
import yaml

from ..common import is_installed

# -------- helpers -------------------------------------------------------------

def _run(cmd: list[str], cwd: pathlib.Path, check: bool = True, capture: bool = False):
    return subprocess.run(
        cmd, cwd=str(cwd), check=check,
        capture_output=capture, text=True
    )


# DATALAD CLEANING UTILITIES

# ---------- .gitattributes cleanup -------------------------------------------

GLOB_META = set("*?[")

def _first_token(line: str) -> str | None:
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    m = re.match(r"(\S+)", s)
    return m.group(1) if m else None

def _non_wildcard_prefix(pathspec: str) -> str:
    ps = re.sub(r"/\*\*$", "/", pathspec)  # turn 'dir/**' → 'dir/'
    buf = []
    for ch in ps:
        if ch in GLOB_META:
            break
        buf.append(ch)
    return "".join(buf)

def _pathspec_exists(root: pathlib.Path, pathspec: str) -> bool:
    """Decide if a .gitattributes pathspec still points to anything on disk."""
    if pathspec == "*":
        return True  # keep global default rules
    # normalize to local FS
    local = pathspec.replace("/", os.sep)
    # No globs → exact file/dir check
    if not any(ch in GLOB_META for ch in pathspec):
        return (root / local).exists()
    # With globs → if the non-wildcard prefix exists, keep; else drop
    prefix = _non_wildcard_prefix(pathspec)
    if not prefix:
        # patterns like '*.csv' (root-level policy) → keep
        return True
    return (root / prefix.replace("/", os.sep)).exists()

def clean_gitattributes(project_root: pathlib.Path) -> int:
    """Remove .gitattributes lines whose pathspecs no longer exist."""
    ga = project_root / ".gitattributes"
    if not ga.exists():
        #print("[.gitattributes] not found — nothing to clean.")
        return 0

    original = ga.read_text(encoding="utf-8").splitlines(True)
    if not original:
        return 0

    # backup
    backup = ga.with_suffix(ga.suffix + ".bak")
    shutil.copy2(ga, backup)

    kept, removed = [], []
    for line in original:
        tok = _first_token(line)
        if tok is None:
            kept.append(line)  # comments/blank lines
            continue
        if _pathspec_exists(project_root, tok):
            kept.append(line)
        else:
            removed.append(line)

    if removed:
        ga.write_text("".join(kept), encoding="utf-8")

    # Delete backup file
    backup.unlink()

    return len(removed)
# ---------- subdataset cleanup -----------------------------------------------

def _list_absent_submodules_via_gitmodules(project_root: pathlib.Path) -> list[str]:
    """
    Fallback: parse .gitmodules for submodule paths and report those whose
    working tree dirs are missing.
    """
    gm = project_root / ".gitmodules"
    if not gm.exists():
        return []
    # Parse all submodule.<name>.path entries
    out = _run(["git", "config", "-f", ".gitmodules", "--get-regexp", r"^submodule\..*\.path$"],
               cwd=project_root, check=False, capture=True)
    absent = []
    for line in (out.stdout or "").splitlines():
        # line like: submodule.data/raw/ds1.path data/raw/ds1
        try:
            _key, path = line.split(None, 1)
        except ValueError:
            continue
        p = project_root / path
        if not p.exists():
            absent.append(path)
    return absent

def _git_unregister_submodule(project_root: pathlib.Path, rel_path: str) -> None:
    """
    Unregister a submodule from Git (dir may already be gone).
    Keeps worktree if present; removes gitlink and .gitmodules section.
    """
    # Remove gitlink from index (dir can be missing)
    _run(["git", "rm", "--cached", "-r", "--ignore-unmatch", rel_path],
         cwd=project_root, check=False)
    # Remove .gitmodules section if present
    _run(["git", "config", "-f", ".gitmodules", "--remove-section", f"submodule.{rel_path}"],
         cwd=project_root, check=False)
    # Stage .gitmodules change if it exists
    if (project_root / ".gitmodules").exists():
        _run(["git", "add", ".gitmodules"], cwd=project_root, check=False)

def clean_subdatasets(project_root: pathlib.Path) -> list[str]:
    """
    Unregister subdatasets that were manually deleted from disk.
    Prefers DataLad; falls back to plain Git submodule cleanup.
    Returns a list of paths that were cleaned.
    """

    cleaned: list[str] = []
    if is_installed("datalad"):
        # Ask DataLad for subdatasets that are absent on disk
        res = _run(
            ["datalad", "subdatasets", "--state", "absent", "--recursive", "--result-renderer", "json"],
            cwd=project_root, check=False, capture=True
        )
        missing: list[str] = []
        for line in (res.stdout or "").splitlines():
            # Cheap parse; each JSON line contains "path": "<abs path>"
            m = re.search(r'"path"\s*:\s*"([^"]+)"', line)
            if m:
                abs_path = pathlib.Path(m.group(1))
                try:
                    rel = abs_path.relative_to(project_root)
                    missing.append(rel.as_posix())
                except Exception:
                    pass

        for rel in missing:
            try:
                # Unregister gitlink; directory may be gone → use --nocheck
                _run(["datalad", "remove", "-d", ".", "-r", "--nocheck", rel],
                     cwd=project_root, check=True)
                # Record change in superdataset
                _run(["datalad", "save", "-m", f"Unregister removed subdataset {rel}", rel],
                     cwd=project_root, check=False)
                cleaned.append(rel)
            except subprocess.CalledProcessError:
                # Fall back to plain git if remove failed
                _git_unregister_submodule(project_root, rel)
                cleaned.append(rel)
    else:
        # No DataLad: inspect .gitmodules
        for rel in _list_absent_submodules_via_gitmodules(project_root):
            _git_unregister_submodule(project_root, rel)
            cleaned.append(rel)

    if cleaned:
        # Final commit/save using Git (works w/ or w/o datalad)
        try:
            _run(["git", "commit", "-m", f"Unregister {len(cleaned)} removed subdataset(s)"], cwd=project_root, check=False)
        except Exception:
            pass

    return cleaned

# ---------- entry point -------------------------------------------------------

def datalad_cleanning(project_root: str | pathlib.Path = ".") -> None:
    root = pathlib.Path(project_root).resolve()
    if not (root / ".git").is_dir():
        raise SystemExit(f"Not a Git repo: {root}")

    _ = clean_gitattributes(root)
    _ = clean_subdatasets(root)

# DVC CLEANING UTILITIES

def _load_dvc_file(p: pathlib.Path):
    """
    Load a .dvc file and return list of outs (as POSIX strings).
    Falls back to a simple parser if PyYAML isn't available.
    """
    txt = p.read_text(encoding="utf-8")

    data = yaml.safe_load(txt) or {}
    outs = data.get("outs") or []
    paths = []
    for item in outs:
        if isinstance(item, dict) and "path" in item and item["path"]:
            paths.append(str(item["path"]))
    return paths


def dvc_cleaning(project_root: str | os.PathLike = ".") -> list[str]:
    """
    Remove stale DVC-tracked datasets whose workspace content was deleted manually.

    Looks for *.dvc files (from `dvc add`) and, if *all* their declared outs are
    missing on disk, runs `dvc remove <file>.dvc` and commits the change.

    Returns a list of repo-relative .dvc paths that were removed.
    """
    root = pathlib.Path(project_root).resolve()
    if not (root / ".dvc").exists():
        #print("Not a DVC project (missing .dvc).")
        return []

    removed: list[str] = []
    dvc_files = [p for p in root.rglob("*.dvc") if p.name != "dvc.yaml"]  # safety

    for dvcf in sorted(dvc_files):
        # repo-relative POSIX paths
        rel_dvc = os.path.relpath(dvcf, root).replace("\\", "/")
        outs = _load_dvc_file(dvcf)

        if not outs:
            # Nothing to check; treat as stale tracker
            try:
                _run(["dvc", "remove", rel_dvc], cwd=root, check=True)
                removed.append(rel_dvc)
                continue
            except subprocess.CalledProcessError as e:
                continue

        # Check if all outs are missing
        all_missing = True
        for out in outs:
            wp = (dvcf.parent / out).resolve()
            if wp.exists():
                all_missing = False
                break

        if all_missing:
            try:
                _run(["dvc", "remove", rel_dvc], cwd=root, check=True)
                removed.append(rel_dvc)
            except subprocess.CalledProcessError as e:
                print(f"Failed to remove {rel_dvc}: {e}")

    if removed:
        try:
            # Stage and commit cleanup; be tolerant if nothing to commit
            _run(["git", "add", "-A"], cwd=root, check=False)
            _run(["git", "commit", "-m", f"Cleanup DVC: unregister {len(removed)} deleted dataset(s)"], cwd=root, check=False)
        except Exception:
            pass

    return removed

import os
import re
import shutil
import subprocess
from pathlib import Path


# -------- helpers -------------------------------------------------------------

def _is_installed(cmd: str) -> bool:
    return shutil.which(cmd) is not None

def _run(cmd: list[str], cwd: Path, check: bool = True, capture: bool = False):
    return subprocess.run(
        cmd, cwd=str(cwd), check=check,
        capture_output=capture, text=True
    )

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

def _pathspec_exists(root: Path, pathspec: str) -> bool:
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

def clean_gitattributes(project_root: Path) -> int:
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
        #print(f"[.gitattributes] removed {len(removed)} dangling rule(s). Backup at {backup}")
       # for ln in removed:
            #print("  -", (_first_token(ln) or ln.strip()))
    #else:
        #print("[.gitattributes] no dangling entries found.")
    return len(removed)

# ---------- subdataset cleanup -----------------------------------------------

def _list_absent_submodules_via_gitmodules(project_root: Path) -> list[str]:
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

def _git_unregister_submodule(project_root: Path, rel_path: str) -> None:
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

def clean_missing_subdatasets(project_root: Path) -> list[str]:
    """
    Unregister subdatasets that were manually deleted from disk.
    Prefers DataLad; falls back to plain Git submodule cleanup.
    Returns a list of paths that were cleaned.
    """


    
    cleaned: list[str] = []
    if _is_installed("datalad"):
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
                abs_path = Path(m.group(1))
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
        #print(f"[subdatasets] cleaned: {', '.join(cleaned)}")
    #else:
        #print("[subdatasets] no missing subdatasets to clean.")
    return cleaned

# ---------- entry point -------------------------------------------------------

def clean_project(project_root: str | Path = ".") -> None:
    root = Path(project_root).resolve()
    if not (root / ".git").is_dir():
        raise SystemExit(f"Not a Git repo: {root}")

    #print(f"== Cleaning project at {root}")
    removed_attr = clean_gitattributes(root)
    cleaned_subds = clean_missing_subdatasets(root)
    #print("== Done.")
    #if removed_attr or cleaned_subds:
        #print("Tip: push the changes when ready:")
        #print("  datalad push --to origin -r  # or: git push")



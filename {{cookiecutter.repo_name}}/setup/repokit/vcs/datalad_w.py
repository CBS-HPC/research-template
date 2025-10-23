import os
import pathlib
import shutil
import subprocess
import sys
import re


from ..common import PROJECT_ROOT, exe_to_path, is_installed, install_uv, _run


def _uv_installer(package_name:str = None):
    
    if not package_name:
            return False
    if not install_uv():
        return False
    try:
        subprocess.run(
            [sys.executable, "-m", "uv", "tool", "install", "git-annex"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        if e.stdout:
            print("--- stdout ---")
            print(e.stdout.strip())
        if e.stderr:
            print("--- stderr ---")
            print(e.stderr.strip())
        return False


def install_datalad():
    def _pip_installer():
        try:
            if not shutil.which("datalad-installer"):
                subprocess.check_call([sys.executable, "-m", "pip", "install", "datalad-installer"])
            subprocess.check_call([sys.executable, "-m", "pip", "install", "datalad"])
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "pyopenssl", "--upgrade"]
            )
            if not is_installed("datalad", "Datalad"):
                print("Error during datalad installation.")
                return False
            print("datalad installed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"An error occurred: {e}")
            return False
        except FileNotFoundError:
            print(
                "One of the required commands was not found. Please ensure Python, pip, and Git are installed and in your PATH."
            )
            return False

    if not is_installed("datalad", "Datalad"):

        if not _uv_installer(package_name="datalad"):
            return _pip_installer()

    return True


def install_git_annex():
    """
    Installs git-annex using datalad-installer if not already installed.
    Configures git to use the git-annex filter process.

    Returns
    -------
        str: The installation path of git-annex if installed successfully.
        None: If the installation fails.
    """
    def _is_windows():
        return os.name == "nt"  # or: sys.platform.startswith("win")
    
    def _windows_installer():
        
        if not _is_windows():
            return False
          
        try:
            # Ensure datalad-installer is available
            if not shutil.which("datalad-installer"):
                subprocess.check_call([sys.executable, "-m", "pip", "install", "datalad-installer"])

            # Install git-annex using datalad-installer and capture the output
            command = "echo y | datalad-installer git-annex -m datalad/git-annex:release"
            result = subprocess.run(command, shell=True, text=True, capture_output=True)

            if result.returncode != 0:
                print(f"Error during git-annex installation: {result.stderr}")
                return None

            # Parse the output for the installation path
            install_path = None
            for line in result.stderr.splitlines():
                if "git-annex is now installed at" in line:
                    install_path = line.split("at")[-1].strip()
                    break

            if not install_path:
                print("Could not determine git-annex installation path.")
                return False

            if not exe_to_path("git-annex", os.path.dirname(install_path)):
                # if not is_installed('git-annex', 'Git-Annex'):
                return False

            return True
        except subprocess.CalledProcessError as e:
            print(f"Error during git-annex installation: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

    # Check if git-annex is installed
    if not is_installed("git-annex", "Git-Annex"):
        installed = False

        # Try uv first (all platforms)
        if _uv_installer(package_name="git-annex"):
            installed = True
        else:
            # On Windows, try the Windows-specific installer as a fallback
            if _is_windows():
                installed = _windows_installer()

        if not installed:
            return False
        
    # Configure git to use the git-annex filter process
    try:
        subprocess.check_call(
            ["git", "config", "--global", "filter.annex.process", "git-annex filter-process"]
        )
        print("git-annex installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error configuring git-annex filter process: {e}")
        return False


def install_git_annex_remote_rclone(install_path):
    
    def clone_git_annex_remote_rclone(install_path):
        """Clone the git-annex-remote-rclone repository to the specified bin folder."""
        repo_url = "https://github.com/git-annex-remote-rclone/git-annex-remote-rclone.git"
        repo_name = os.path.basename(repo_url).replace(".git", "")
        #repo_path = os.path.join(install_path, repo_name)
        repo_path = str(pathlib.Path(install_path) / pathlib.Path(repo_name))


        # Create the bin folder if it doesn't exist
        install_path = str(PROJECT_ROOT / pathlib.Path(install_path))
        os.makedirs(install_path, exist_ok=True)

        # Check if the repository already exists
        if os.path.isdir(repo_path):
            print(f"The repository '{repo_name}' already exists in {install_path}.")
        else:
            subprocess.run(["git", "clone", repo_url, repo_path], check=True)
            print(f"Repository cloned successfully to {repo_path}.")

        repo_path = os.path.abspath(repo_path)  # Convert to absolute path
        return repo_path

    # Clone https://github.com/git-annex-remote-rclone/git-annex-remote-rclone.git

    if not is_installed("git-annex-remote-rclone", "git-annex-remote-rclone"):
        repo_path = clone_git_annex_remote_rclone(install_path)
        exe_to_path("git-annex-remote-rclone", repo_path)


def datalad_create():
    """
    Create a DataLad dataset (if missing) and configure .gitattributes so that:
      - All files are unlocked (stored in Git, not annexed)
      - Except anything under ./data/** which goes to annex
    """
    gitattributes = PROJECT_ROOT / ".gitattributes"

    def write_gitattributes():
        # Last matching rule wins; keep 'data/**' AFTER '*' to override it.
        lines = [
            "* annex.largefiles=nothing\n",       # default: don't annex (i.e., unlocked)
           # "data/** annex.largefiles=anything\n" # but annex everything under ./data
        ]
        # Write idempotently (avoid duplicate lines, preserve other attrs if any)
        existing = gitattributes.read_text().splitlines(True) if gitattributes.exists() else []
        wanted = []
        # Keep any non-annex.largefiles lines the user might already have
        for ln in existing:
            if "annex.largefiles=" not in ln:
                wanted.append(ln)
        # Append our two canonical lines
        wanted.extend(lines)
        gitattributes.write_text("".join(wanted))

    # Initialize a DataLad dataset if needed
    if not (PROJECT_ROOT / ".datalad").is_dir():
        subprocess.run(["datalad", "create", "--force"], check=True)

    # Ensure the attributes are set as requested
    write_gitattributes()

    # Save the state
    subprocess.run(["datalad", "save", "-m", "Configure annex: unlock everything except ./data"], check=True)
    print("DataLad dataset ready: unlocked all except ./data")


def datalad_deic_storage(repo_name):
    
    def git_annex_remote(remote_name, target, prefix):
        """
        Creates a git annex remote configuration for 'deic-storage' using rclone.
        """
        #remote_name = "deic-storage"
        #target = "dropbox-for-friends"  # Change this to your actual target as needed
        #prefix = "my_awesome_dataset"  # Change this to your desired prefix

        # Construct the command
        command = [
            "git",
            "annex",
            "initremote",
            remote_name,
            "type=external",
            "externaltype=rclone",
            "chunk=50MiB",
            "encryption=none",
            "target=" + target,
            "prefix=" + prefix,
        ]

        try:
            # Execute the command
            subprocess.run(command, check=True)
            print(f"Git annex remote '{remote_name}' created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to create git annex remote: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    # rclone_remote()
    git_annex_remote("deic-storage", "deic-storage", repo_name)


def datalad_local_storage(repo_name, remote_storage):
    def get_remote_path(repo_name):
        """
        Prompt the user to provide the path to a DVC remote storage folder.
        If `folder_path` already ends with `repo_name` and exists, an error is raised.
        Otherwise, if `folder_path` exists but does not end with `repo_name`,
        it appends `repo_name` to `folder_path` to create the required directory.

        Parameters
        ----------
        - repo_name (str): The name of the repository to ensure at the end of `folder_path`.

        Returns
        -------
        - str: Finalized path to DVC remote storage if valid, or None if an error occurs.
        """
        # Prompt the user for the folder path
        folder_path = input("Please enter the path to Datalad emote storage (ria):").strip()

        folder_path = os.path.abspath(folder_path)

        # Attempt to create folder_path if it does not exist
        if not os.path.isdir(folder_path):
            try:
                os.makedirs(folder_path, exist_ok=True)
                print(f"The path '{folder_path}' did not exist and was created.")
            except OSError as e:
                print(f"Failed to create the path '{folder_path}': {e}")
                return None

        # Check if folder_path already ends with repo_name
        if folder_path.endswith(repo_name):
            # Check if it already exists as a directory
            if os.path.isdir(folder_path):
                print(
                    f"The path '{folder_path}' already exists with '{repo_name}' as the final folder."
                )
                return None  # Error out if the path already exists
        else:
            # Append repo_name to folder_path if it doesn’t end with it
            folder_path = os.path.join(folder_path, repo_name)
            try:
                # Create the repo_name directory if it doesn't exist
                os.makedirs(folder_path, exist_ok=True)
                print(f"Created directory: {folder_path}")
            except OSError as e:
                print(f"Failed to create the path '{folder_path}': {e}")
                return None

        # Return the finalized path
        return folder_path

    datalad_remote = get_remote_path(repo_name)
    if datalad_remote:
        subprocess.run(
            [
                "datalad",
                "create-sibling-ria",
                "-s",
                repo_name,
                "--new-store-ok",
                f"ria+file//{remote_storage}",
            ],
            check=True,
        )


def _relposix(root: pathlib.Path, p: pathlib.Path) -> str:
    return os.path.relpath(p, root).replace("\\", "/")


def _is_registered_subdataset(root: pathlib.Path, rel_posix: str, abs_path: pathlib.Path) -> bool:
    """Return True if rel_posix is a registered subdataset of root."""
    # Prefer DataLad (accurate)
    try:
        out = _run(["datalad", "subdatasets", "--recursive", "--result-renderer", "json"],
                   cwd=root, check=False, capture=True).stdout or ""
        abs_posix = abs_path.as_posix()
        if any(f'"path": "{abs_posix}"' in line for line in out.splitlines()):
            return True
    except Exception:
        pass
    # Fallback: check .gitmodules listing
    gm = root / ".gitmodules"
    if gm.exists():
        out = _run(["git", "config", "-f", ".gitmodules", "--get-regexp", r"^submodule\..*\.path$"],
                   cwd=root, check=False, capture=True).stdout or ""
        for line in out.splitlines():
            try:
                _key, path = line.split(None, 1)
            except ValueError:
                continue
            if path.replace("\\", "/") == rel_posix:
                return True
    return False


def _ensure_attr_for_path(root: pathlib.Path, rel_posix: str, is_dir: bool) -> bool:
    """
    Ensure .gitattributes has a correct annex rule for rel_posix.

    Rules:
      - Use double quotes around the pattern if it contains spaces or tabs.
      - Remove any generic 'data/** annex.largefiles=anything' if present.
      - Remove any previous annex.largefiles rule for the same target.
      - Append our canonical rule and write back.
    Returns True if the file changed.
    """
    ga = root / ".gitattributes"

    # Normalize path to POSIX
    rel_posix = rel_posix.replace("\\", "/")
    pattern = f"{rel_posix}/**" if is_dir else rel_posix

    # Quote if contains whitespace
    if any(ch.isspace() for ch in pattern):
        pattern_fmt = f"\"{pattern}\""
    else:
        pattern_fmt = pattern

    rule = f"{pattern_fmt} annex.largefiles=anything\n"

    existing = ga.read_text(encoding="utf-8").splitlines(True) if ga.exists() else []

    def _norm(s: str) -> str:
        # collapse inner whitespace for comparisons
        return re.sub(r"\s+", " ", s.strip())

    changed = False
    kept: list[str] = []

    # If our exact rule already exists, no change needed
    rule_norm = _norm(rule)
    if any(_norm(ln) == rule_norm for ln in existing):
        return False

    for ln in existing:
        ln_norm = _norm(ln)

        # Drop the global 'data/** annex.largefiles=anything'
        if ln_norm == "data/** annex.largefiles=anything":
            changed = True
            continue

        # Remove any prior rule for this target (quoted or unquoted)
        tokens = ln.strip().split()
        if tokens:
            first = tokens[0]
            # acceptable prior "first token" variants for the same target
            same_target = first in {pattern, f"\"{pattern}\""}
            if same_target and any(tok.startswith("annex.largefiles=") for tok in tokens[1:]):
                changed = True
                continue

        kept.append(ln)

    kept.append(rule)
    ga.write_text("".join(kept), encoding="utf-8")
    return True


def set_datalad(path: str | os.PathLike) -> bool:
    """
    Track a file/dir in the superdataset (no subdatasets).
    SAFEGUARD: if the path is a registered subdataset, refuse.

    Returns True if something changed/saved, False if no-op or refused.
    """
    root = pathlib.Path(PROJECT_ROOT).resolve()
    if not (root / ".datalad").is_dir():
        return

    abs_path = (root / path).resolve()
    try:
        abs_path.relative_to(root)
    except ValueError:
        raise RuntimeError(f"Path is outside project: {abs_path}")
    if not abs_path.exists():
        raise FileNotFoundError(abs_path)

    rel_posix = _relposix(root, abs_path)
    is_dir = abs_path.is_dir()

    # --- SAFEGUARD: refuse if already a subdataset, unless explicit flatten allowed
    if _is_registered_subdataset(root, rel_posix, abs_path):
        return False

    changed = False

    # Ensure annex policy for this path
    if _ensure_attr_for_path(root, rel_posix, is_dir=is_dir):
        changed = True

        _run(["git", "add", "--", ".gitattributes"], cwd=root, check=False)

    # Stage the path itself (files or directory)
    #_run(["git", "add", "--", rel_posix], cwd=root, check=False)
    _run(["git", "-c", "core.safecrlf=false", "add", "--", rel_posix], cwd=root, check=False)

    # Save (non-fatal if nothing to save)
    _run(["datalad", "save", "-m", f"Track in superdataset: {rel_posix}", rel_posix],
         cwd=root, check=False)

    return changed


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


def datalad_cleaning(project_root: str | pathlib.Path = ".") -> None:
    root = pathlib.Path(project_root).resolve()
    if not (root / ".git").is_dir():
        raise SystemExit(f"Not a Git repo: {root}")

    _ = clean_gitattributes(root)
    _ = clean_subdatasets(root)



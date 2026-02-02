
import os
import pathlib
import subprocess
import sys
import yaml

from .git_w import git_commit
from ..common import PROJECT_ROOT, is_installed, install_uv, _run
from ..rdm.dmp import load_default_dataset_path
DEFAULT_DATASET_PATH, _= load_default_dataset_path()



def install_dvc():
    """
    Install DVC, preferring `uv pip install dvc` and falling back to `pip install dvc`.
    Returns True on success, False otherwise.
    """
    # If already present, we're done.
    if is_installed("dvc", "DVC"):
        return True

    def _run(desc, cmd, check=True):
        try:
            res = subprocess.run(cmd, check=check, capture_output=True, text=True)
            return True, res
        except subprocess.CalledProcessError as e:
            print(f"[{desc}] failed with exit code {e.returncode}")
            if e.stdout:
                print("--- stdout ---")
                print(e.stdout.strip())
            if e.stderr:
                print("--- stderr ---")
                print(e.stderr.strip())
            return False, e

    # 1) Try uv-based install first (if uv is available/installed)

    if install_uv() :
        ok, _ = _run(
            "uv pip install dvc",
            [sys.executable, "-m", "uv", "pip", "install", "dvc"]
            #[sys.executable, "-m", "uv", "pip", "install", "dvc[all]"]
        )
        if ok and is_installed("dvc", "DVC"):
            print("DVC has been installed successfully via uv.")
            return True
        else:
            print("uv-based install did not result in a working DVC; trying pip fallback…")
    else:
        print("uv not available; trying pip fallback…")

    # 2) Fallback: regular pip install
    ok, _ = _run(
        "pip install dvc",
        [sys.executable, "-m", "pip", "install", "dvc"]
    )
    if not ok or not is_installed("dvc", "DVC"):
        print("Error during DVC installation.")
        return False

    print("DVC has been installed successfully via pip.")
    return True


def dvc_init(remote_storage, code_repo, repo_name):
    # Initialize a Git repository if one does not already exist
    if not os.path.isdir(".git"):
        if code_repo.lower() in ["github", "codeberg"]:
            subprocess.run(["git", "config", "--global", "init.defaultBranch", "main"], check=True)

        subprocess.run(["git", "init"], check=True)

    # Init dvc
    if not os.path.isdir(".dvc"):
        subprocess.run(["dvc", "init"], check=True)
    else:
        print("I is already a DVC project")
        return

    # Add dvc remote storage
    if remote_storage == "Local Path":
        dvc_local_storage(repo_name)
    elif remote_storage == "Deic-Storage":
        dvc_deic_storage(repo_name)
    elif remote_storage == "Dropbox":
        print("Not implemented yet")


    #subprocess.run(["dvc", "add", DEFAULT_DATASET_PATH], check=True)
    
  
    _ = git_commit("Initial commit - Initialize DVC.")
    print("Created an initial commit.")


def dvc_deic_storage(remote_directory=None):
    email = input("Please enter email to Deic-Storage: ").strip()
    password = input("Please enter password to Deic-Storage: ").strip()

    # Use root directory if no path is provided
    remote_directory = remote_directory if remote_directory else ""

    # Construct the command to add the DVC SFTP remote
    add_command = [
        "dvc",
        "remote",
        "add",
        "-d",
        "deic_storage",
        f"ssh://'{email}'@sftp.storage.deic.dk:2222",
    ]
    # f"sftp://'{email}'@sftp.storage.deic.dk:2222/{remote_directory}"
    # Construct the command to set the password for the remote
    password_command = ["dvc", "remote", "modify", "deic_storage", "password", password]

    try:
        # Execute the add command
        subprocess.run(add_command, check=True)
        print("DVC remote 'deic_storage' added successfully.")

        # Execute the password command
        subprocess.run(password_command, check=True)
        print("Password for DVC remote 'deic_storage' set successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Failed to set up DVC remote: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def dvc_local_storage(repo_name):
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
        folder_path = input("Please enter the path to DVC remote storage:").strip()

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

    dvc_remote = get_remote_path(repo_name)
    if dvc_remote:
        subprocess.run(["dvc", "remote", "add", "-d", "remote_storage", dvc_remote], check=True)


def set_dvc(f: str | os.PathLike | None = None) -> bool:
    """
    Add a file or directory to DVC (dvc add <f>) with safeguards:
      - Requires a DVC-initialized repo (PROJECT_ROOT/.dvc exists).
      - Skips if <f>.dvc exists (already added).
      - Skips if any ancestor directory of <f> has an existing <ancestor>.dvc
        (meaning <f> is already covered by a directory out).
      - On success, stages typical DVC files for Git and makes a commit.
    Returns True if an add/commit happened (or was already tracked), False on error.
    """
    if f is None:
        print("No path provided.")
        return False
    
    root = pathlib.Path(PROJECT_ROOT).resolve()
    if not (root / ".dvc").exists():
        print("This is not a DVC project (missing .dvc). Skipping.")
        return False
    
    p = (root / f).resolve()
    try:
        p.relative_to(root)
    except ValueError:
        print(f"Path is outside the project: {p}")
        return False
    
    if not p.exists():
        print(f"Path does not exist: {p}")
        return False
    
    # Compute repo-relative POSIX path (what DVC expects)
    rel = os.path.relpath(p, root).replace("\\", "/")
    rel_dvc = root / f"{rel}.dvc"
    
    # --- Safeguard 1: exact path already added?
    if rel_dvc.exists():
        print(f"Already tracked by DVC: {rel}. (Found {rel}.dvc)")
        return True
    
    # --- Safeguard 2: covered by a parent directory out?
    ancestor = pathlib.Path(rel)
    for parent in [ancestor] + list(ancestor.parents):
        if parent == pathlib.Path("."):
            continue
        parent_dvc = root / f"{parent.as_posix()}.dvc"
        if parent_dvc.exists():
            print(f"Already tracked by DVC via parent: {parent.as_posix()}.dvc")
            return True
    
    # --- Safeguard 3: Check if .dvc file would be git-ignored
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-v", f"{rel}.dvc"],
            cwd=root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"ERROR: {rel}.dvc would be git-ignored.")
            print(f"Reason: {result.stdout.strip()}")
            return False
    except Exception:
        pass
    
    # Not tracked yet → dvc add
    try:
        result = subprocess.run(
            ["dvc", "add", rel], 
            cwd=root, 
            check=True,
            capture_output=True,
            text=True
        )
        
        # Stage DVC/Git metadata; some may not exist — that's fine.
        to_stage = [f"{rel}.dvc"]

        subprocess.run(["git", "add", "--"] + to_stage, cwd=root, check=False)
        
        # Make a commit (non-fatal if nothing staged for commit)
        subprocess.run(["git", "commit", "-m", f"Track with DVC: {rel}"], cwd=root, check=False)
        
        print(f"DVC added: {rel}")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"dvc add failed for {rel}:")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False
  

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
    # Filter out directories and dvc.yaml
    dvc_files = [p for p in root.rglob("*.dvc") 
                 if p.is_file() and p.name != "dvc.yaml"]
    
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
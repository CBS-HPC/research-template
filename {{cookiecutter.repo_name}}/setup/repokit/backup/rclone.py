"""
Rclone operations - Installation, execution, and transfer logic.
"""

import os
import pathlib
import subprocess
import tempfile


from ..common import (
    PROJECT_ROOT,
    change_dir,
    toml_ignore,
    load_from_env,
)
from ..vcs import git_commit, git_log_to_file, git_push, install_rclone
from .registry import update_sync_status, load_registry, load_all_registry

DEFAULT_TIMEOUT = 600  # seconds



def _rc_verbose_args(level: int) -> list[str]:
    """Convert verbosity level to rclone args."""
    return ["-" + "v" * min(max(level, 0), 3)] if level > 0 else []


def _rclone_commit(local_path: str, flag: bool = False, msg: str = "Rclone Backup Commit") -> bool:
    """Commit changes to git if applicable."""
    if not flag and (pathlib.Path(local_path).resolve() == PROJECT_ROOT.resolve()):
        flag = True
        if os.path.exists(".git") and not os.path.exists(".datalad") and not os.path.exists(".dvc"):
            with change_dir("./data"):
                _ = git_commit(msg=msg, path=os.getcwd())
                git_log_to_file(os.path.join(".gitlog"))
            git_push(load_from_env("CODE_REPO", ".cookiecutter") != "None", msg)
    return flag


def _rclone_transfer(
    remote_name: str,
    local_path: str,
    remote_path: str,
    action: str = "push",
    operation: str = "sync",
    exclude_patterns: list[str] = None,
    dry_run: bool = False,
    verbose: int = 0,
):
    """
    Transfer files using rclone.

    Args:
        remote_name: Name of the configured remote
        local_path: Local directory path
        remote_path: Remote directory path
        action: 'push' or 'pull'
        operation: 'sync', 'copy', or 'move'
        exclude_patterns: List of patterns to exclude
        dry_run: If True, show what would be done
        verbose: Verbosity level (0-3)
    """
    exclude_patterns = exclude_patterns or []
    operation = operation.lower().strip()

    if operation not in {"sync", "copy", "move"}:
        print("Error: 'operation' must be either 'sync', 'copy', or 'move'")
        return

    exclude_args = []
    for pattern in exclude_patterns:
        exclude_args.extend(["--exclude", pattern])

    if action == "push":
        if not os.path.exists(local_path):
            print(f"Error: The folder '{local_path}' does not exist.")
            return
        command = ["rclone", operation, local_path, remote_path]
    elif action == "pull":
        command = ["rclone", operation, remote_path, local_path]
    else:
        print(f"Error: Invalid action '{action}'")
        return

    command += _rc_verbose_args(verbose) + exclude_args
    if dry_run:
        command.append("--dry-run")

    try:
        subprocess.run(command, check=True, timeout=DEFAULT_TIMEOUT)

        verb = {
            "sync": "synchronized",
            "copy": "copied",
            "move": "moved (deleted at origin)"
        }.get(operation, operation)

        print(f"Folder '{local_path}' successfully {verb} to '{remote_path}'.")
        update_sync_status(remote_name, action=action, operation=operation, success=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to {operation} folder to remote: {e}")
        update_sync_status(remote_name, action=action, operation=operation, success=False)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        update_sync_status(remote_name, action=action, operation=operation, success=False)


def _exclude_patterns(local_path: str) -> list[str]:
    """Get exclude patterns from pyproject.toml if applicable."""
    if pathlib.Path(local_path).resolve() == PROJECT_ROOT.resolve():
        _, exclude_patterns = toml_ignore(
            folder=local_path,
            toml_path="pyproject.toml",
            ignore_filename=".rcloneignore",
            tool_name="rcloneignore",
            toml_key="patterns",
        )
        return exclude_patterns
    return []


def push_rclone(
    remote_name: str,
    new_path: str = None,
    operation: str = "sync",
    dry_run: bool = False,
    verbose: int = 0
):
    """Push local files to remote."""
    os.chdir(PROJECT_ROOT)

    if not install_rclone("./bin"):
        return

    if remote_name.lower() == "all":
        all_remotes = load_all_registry().keys()
    else:
        all_remotes = [remote_name]

    flag = False
    for remote_name in all_remotes:
        _remote_path, _local_path = load_registry(remote_name.lower())
        if not _remote_path:
            print(f"Remote has not been configured or not found in registry. "
                  f"Run 'backup add --remote {remote_name}' first.")
            continue

        if new_path is None:
            new_path = _remote_path

        flag = _rclone_commit(_local_path, flag, msg=f"Rclone Push from {_local_path} to {new_path}")
        exclude_patterns = _exclude_patterns(_local_path)

        _rclone_transfer(
            remote_name=remote_name.lower(),
            action="push",
            local_path=_local_path,
            remote_path=new_path,
            operation=operation,
            exclude_patterns=exclude_patterns,
            dry_run=dry_run,
            verbose=verbose
        )


def pull_rclone(
    remote_name: str,
    new_path: str = None,
    operation: str = "sync",
    dry_run: bool = False,
    verbose: int = 0
):
    """Pull files from remote to local."""
    if remote_name is None:
        print("Error: No remote specified for pulling backup.")
        return
    if remote_name.lower() == "all":
        print("Error: Pulling from 'all' remotes is not supported.")
        return

    os.chdir(PROJECT_ROOT)

    if not install_rclone("./bin"):
        return

    _remote_path, _local_path = load_registry(remote_name.lower())

    if not _remote_path:
        print(f"Remote has not been configured or not found in registry. "
              f"Run 'backup add --remote {remote_name}' first.")
        return

    if new_path is None:
        new_path = _local_path

    if not os.path.exists(new_path):
        os.makedirs(new_path)

    _ = _rclone_commit(new_path, False, msg=f"Rclone Pull from {_remote_path} to {new_path}")
    exclude_patterns = _exclude_patterns(_local_path)

    _rclone_transfer(
        remote_name=remote_name.lower(),
        action="pull",
        local_path=new_path,
        remote_path=_remote_path,
        operation=operation,
        exclude_patterns=exclude_patterns,
        dry_run=dry_run,
        verbose=verbose
    )


def rclone_diff_report(local_path: str, remote_path: str):
    """Quick diff between local folder and remote path."""
    import tempfile
    with tempfile.NamedTemporaryFile() as temp:
        command = [
            "rclone",
            "diff",
            local_path,
            remote_path,
            "--no-traverse",
            "--differ",
            "--missing-on-dst",
            "--missing-on-src",
            "--dry-run",
            "--output",
            temp.name,
        ]
        try:
            subprocess.run(command, check=True, timeout=DEFAULT_TIMEOUT)
            with open(temp.name) as f:
                diff_output = f.read()
            print(diff_output or "[No differences]")
        except subprocess.CalledProcessError as e:
            print(f"Failed to generate diff report: {e}")

def generate_diff_report(remote_name: str):
    """Generate diff report between local and remote using the reusable diff function."""

    def run_diff(remote: str):
        remote_path, local_path = load_registry(remote)
        if not remote_path or not local_path:
            print(f"No path found for remote '{remote}'.")
            return
        print(f"\n📊 Diff report for '{remote}':")
        rclone_diff_report(local_path, remote_path)

    if remote_name.lower() == "all":
        for remote in load_all_registry().keys():
            run_diff(remote)
    else:
        run_diff(remote_name)


def generate_diff_report_old(remote_name: str):
    """Generate diff report between local and remote."""
    def run_diff(remote: str):
        remote_path, local_path = load_registry(remote)
        if not remote_path:
            print(f"No path found for remote '{remote}'.")
            return
        with tempfile.NamedTemporaryFile() as temp:
            command = [
                "rclone",
                "diff",
                local_path,
                remote_path,
                "--dry-run",
                "--no-traverse",
                "--differ",
                "--missing-on-dst",
                "--missing-on-src",
                "--output",
                temp.name,
            ]
            try:
                subprocess.run(command, check=True, timeout=DEFAULT_TIMEOUT)
                with open(temp.name) as f:
                    diff_output = f.read()
                print(f"\n📊 Diff report for '{remote}':\n{diff_output or '[No differences]'}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to generate diff report for '{remote}': {e}")

    if remote_name.lower() == "all":
        for remote in load_all_registry().keys():
            run_diff(remote)
    else:
        run_diff(remote_name)


def transfer_between_remotes(
    source_remote: str,
    dest_remote: str,
    operation: str = "copy",
    dry_run: bool = True,
    verbose: int = 0,
):
    """
    Transfer data from one remote to another.

    Safeguard: Only allowed if both remotes share the same local_path.
    """
    all_remotes = load_all_registry()
    src_meta = all_remotes.get(source_remote)
    dst_meta = all_remotes.get(dest_remote)

    if not src_meta or not dst_meta:
        print(f"Error: One or both remotes not registered. Source: {source_remote}, Destination: {dest_remote}")
        return

    src_local = src_meta.get("local_path")
    dst_local = dst_meta.get("local_path")

    if not src_local or not dst_local:
        print("Error: One or both remotes do not have local paths configured.")
        return

    if os.path.abspath(src_local) != os.path.abspath(dst_local):
        print("Error: Cannot transfer between remotes with different local paths.")
        print(f"Source local path: {src_local}")
        print(f"Destination local path: {dst_local}")
        return

    src_path = src_meta.get("remote_path")
    dst_path = dst_meta.get("remote_path")

    print(f"\n🔁 Transfer from '{source_remote}' to '{dest_remote}'")
    print(f"Local path (shared): {src_local}")
    print(f"Remote paths: {src_path} → {dst_path}")
    print(f"Operation: {operation} | Dry run: {dry_run}\n")

    if operation not in {"copy", "sync"}:
        print("Error: Only 'copy' or 'sync' operations are allowed for remote-to-remote transfers.")
        return

    exclude_patterns = _exclude_patterns(src_local)

    _rclone_transfer(
        remote_name=f"{source_remote}->{dest_remote}",
        action="push",  # push from src to dst
        local_path=src_path,  # remote path treated as local in rclone syntax
        remote_path=dst_path,
        operation=operation,
        exclude_patterns=exclude_patterns,
        dry_run=dry_run,
        verbose=verbose,
    )

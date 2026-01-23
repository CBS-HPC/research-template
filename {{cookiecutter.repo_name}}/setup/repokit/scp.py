import sys
import argparse
import subprocess
import pathlib
import shutil
import shlex

from .common import (
    PROJECT_ROOT,
    ensure_correct_kernel,
    load_from_env,
)

from .backup import set_host_port, _ensure_repo_suffix

def scp_push(
    remote_name: str,
    local_path: str = None,
    remote_path: str = None,
    recursive: bool = True,
) -> None:
    """
    Copy local -> remote using scp.
    """
    repo_name = load_from_env("REPO_NAME", ".cookiecutter")
    host = load_from_env("HOST")
    port = int(load_from_env("PORT"))
    user = "ucloud"

    # Defaults
    if local_path is None:
        local_path = str(PROJECT_ROOT)

    # If remote_path not provided, prompt; otherwise use as-is
    if remote_path is None:
        default_base = f"work/rclone-backup/{repo_name}"
        remote_path = (input(f"Enter base folder for {remote_name} [{default_base}]: ").strip() or default_base)
    remote_path = _ensure_repo_suffix(remote_path, repo_name)

    # Normalize local path
    src_path = pathlib.Path(local_path).expanduser().resolve()
    if not src_path.exists():
        print(f"Error: The folder '{src_path}' does not exist.")
        return

    # Ensure ssh/scp exist
    if not shutil.which("ssh") or not shutil.which("scp"):
        raise RuntimeError("ssh/scp not found on PATH. Please install OpenSSH client.")

    # Sanitize remote path
    remote_path = (remote_path or "").strip()
    if not remote_path:
        raise ValueError("Remote path resolved to an empty string.")
    if not remote_path.startswith("/"):
        remote_path = "/" + remote_path
    if remote_path in {"/", "/.", "/.."}:
        raise ValueError(f"Refusing to operate on unsafe remote path: '{remote_path}'")

    # --- Remote command helpers ---
    def _q(s: str) -> str:
        return "'" + s.replace("'", "'\"'\"'") + "'"

    def _ssh_remote(cmd: list[str], *, capture: bool = True):
        return subprocess.run(
            cmd, check=False, capture_output=capture, text=True, timeout=DEFAULT_TIMEOUT,
        )

    def _remote_exists(path: str) -> bool:
        print(f"Checking if remote path exists: {path}")
        cmd = ["ssh", "-p", str(port), f"{user}@{host}", f"[ -e {_q(path)} ]"]
        res = _ssh_remote(cmd)
        return res.returncode == 0

    def _remote_mkdir_p(path: str) -> None:
        print(f"Ensuring remote directory exists: {path}")
        p = (path or "").strip()
        if not p:
            raise ValueError("remote mkdir received empty path")
        cmd = ["ssh", "-p", str(port), f"{user}@{host}", f"mkdir -p {_q(p)}"]
        res = _ssh_remote(cmd)
        if res.returncode != 0:
            raise RuntimeError(
                f"Remote mkdir failed (exit {res.returncode}).\n"
                f"STDERR:\n{res.stderr.strip() or '<empty>'}"
            )

    def _remote_rm_rf(path: str) -> None:
        print(f"Removing remote path: {path}")
        p = (path or "").strip()
        if not p or p in {"/", "/.", "/.."}:
            raise ValueError(f"Refusing to rm -rf unsafe path: '{p}'")
        cmd = ["ssh", "-p", str(port), f"{user}@{host}", f"rm -rf {_q(p)}"]
        res = _ssh_remote(cmd)
        if res.returncode != 0:
            raise RuntimeError(
                f"Remote remove failed (exit {res.returncode}).\n"
                f"STDERR:\n{res.stderr.strip() or '<empty>'}"
            )

    # Handle existing remote path if it already exists
    while _remote_exists(remote_path):
        choice = (
            input(
                f"Remote path '{remote_path}' exists.\n"
                "Overwrite (o), rename (n), or cancel (c)? [o/n/c]: "
            ).strip().lower()
        )
        if choice == "o":
            _remote_rm_rf(remote_path)
            break
        elif choice == "n":
            new_path = input("Enter new remote path: ").strip()
            if not new_path:
                continue
            if not new_path.startswith("/"):
                new_path = "/" + new_path
            new_path = _ensure_repo_suffix(new_path, repo_name)
            if new_path in {"/", "/.", "/.."}:
                print("Refusing unsafe path, try again.")
                continue
            remote_path = new_path
        else:
            print("Cancelled.")
            return

    # Ensure remote target dir
    _remote_mkdir_p(remote_path)

    # scp copy
    print(f"Starting scp copy to {user}@{host}:{remote_path} ...")
    scp_cmd = ["scp"]
    if recursive:
        scp_cmd.append("-r")
    scp_cmd += ["-P", str(port), str(src_path), f"{user}@{host}:{remote_path}"]

    try:
        subprocess.run(scp_cmd, check=True, timeout=DEFAULT_TIMEOUT)
        print(f"✅ Copied '{src_path}' → {user}@{host}:{remote_path}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"scp failed (exit {e.returncode}).\nCommand: {shlex.join(scp_cmd)}"
        ) from e


def scp_pull(
    remote_name: str,
    local_path: str | None = None,
    remote_path: str | None = None,
    recursive: bool = True,
) -> None:
    """
    Copy remote -> local using scp.
    """
    repo_name = load_from_env("REPO_NAME", ".cookiecutter")
    host = load_from_env("HOST")
    port = int(load_from_env("PORT"))
    user = "ucloud"

    # Defaults
    if local_path is None:
        local_path = str(PROJECT_ROOT)

    if not shutil.which("ssh") or not shutil.which("scp"):
        raise RuntimeError("ssh/scp not found on PATH. Please install OpenSSH client.")

    # --- Remote command helpers ---
    def _q(s: str) -> str:
        return "'" + s.replace("'", "'\"'\"'") + "'"

    def _ssh_remote(cmd: list[str], *, capture: bool = True):
        return subprocess.run(
            cmd, check=False, capture_output=capture, text=True, timeout=DEFAULT_TIMEOUT,
        )

    def _remote_exists(path: str) -> bool:
        print(f"Checking if remote path exists: {path}")
        cmd = ["ssh", "-p", str(port), f"{user}@{host}", f"[ -e {_q(path)} ]"]
        res = _ssh_remote(cmd)
        return res.returncode == 0

    # If remote_path not provided, prompt; otherwise use as-is
    if remote_path is None:
        default_base = f"work/rclone-backup/{repo_name}"
        remote_path = (input(
            f"Enter remote folder to pull from for {remote_name} [{default_base}]: "
        ).strip() or default_base)
    remote_path = _ensure_repo_suffix(remote_path, repo_name)

    # sanitize + ensure exists
    remote_path = (remote_path or "").strip()
    if not remote_path:
        raise ValueError("Remote path resolved to an empty string.")
    if not remote_path.startswith("/"):
        remote_path = "/" + remote_path
    if remote_path in {"/", "/.", "/.."}:
        raise ValueError(f"Refusing to operate on unsafe remote path: '{remote_path}'")
    if not _remote_exists(remote_path):
        raise FileNotFoundError(f"Remote path does not exist: {remote_path}")

    # prepare local destination
    dst_path = pathlib.Path(local_path).expanduser().resolve()
    if dst_path.exists():
        choice = (
            input(
                f"Local destination '{dst_path}' exists.\n"
                "Overwrite (o), rename (n), or cancel (c)? [o/n/c]: "
            ).strip().lower()
        )
        if choice == "o":
            if dst_path.is_file():
                dst_path.unlink()
            else:
                shutil.rmtree(dst_path)
        elif choice == "n":
            new_path = input("Enter new local path: ").strip()
            if not new_path:
                print("Cancelled.")
                return
            dst_path = pathlib.Path(new_path).expanduser().resolve()
        else:
            print("Cancelled.")
            return

    # ensure parent exists
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    # scp copy (remote -> local)
    print(f"Starting scp pull from {user}@{host}:{remote_path} ...")
    scp_cmd = ["scp"]
    if recursive:
        scp_cmd.append("-r")
    scp_cmd += ["-P", str(port), f"{user}@{host}:{remote_path}", str(dst_path)]

    try:
        subprocess.run(scp_cmd, check=True, timeout=DEFAULT_TIMEOUT)
        print(f"✅ Pulled '{user}@{host}:{remote_path}' → '{dst_path}'")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"scp failed (exit {e.returncode}).\nCommand: {shlex.join(scp_cmd)}"
        ) from e


@ensure_correct_kernel
def main():
    """
    Lightweight entry point to run SCP push/pull.
      - For push (default): --local-path is the local source, --remote-path is the remote destination.
      - For pull (--pull):  --remote-path is the remote source, --local-path is the local destination.
    """
    if not (shutil.which("ssh") and shutil.which("scp")):
        print("Error: OpenSSH ssh/scp not found in PATH.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="SCP copy/pull mini-CLI")
    parser.add_argument("--remote", required=True, help="Remote name (e.g., ucloud)")
    parser.add_argument("--local-path", help="Local path (source for push; destination for pull). Defaults to PROJECT_ROOT.")
    parser.add_argument("--remote-path", help="Remote path (destination for push; source for pull).")
    parser.add_argument("--no-recursive", action="store_true", help="Disable recursive scp.")
    parser.add_argument("--pull", action="store_true", help="Pull from remote to local instead of pushing.")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    args = parser.parse_args()

    remote = args.remote.strip().lower()

    # ensure host/port context is set
    set_host_port(remote)

    recursive = not args.no_recursive
    if args.pull:
        scp_pull(
            remote_name=remote,
            local_path=args.local_path or str(PROJECT_ROOT),
            remote_path=args.remote_path,
            recursive=recursive,
        )
    else:
        scp_push(
            remote_name=remote,
            local_path=args.local_path or str(PROJECT_ROOT),
            remote_path=args.remote_path,
            recursive=recursive,
        )



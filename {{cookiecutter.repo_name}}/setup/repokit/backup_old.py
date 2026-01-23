import sys
import argparse
import json
import os
import subprocess
import tempfile
from datetime import datetime
import getpass
import pathlib
import shutil

import shlex
from .common import (
    PROJECT_ROOT,
    change_dir,
    ensure_correct_kernel,
    load_from_env,
    save_to_env,
    toml_ignore,
    check_path_format,
)
from .vcs import git_commit, git_log_to_file, git_push, install_rclone


# --- new helpers ---
DEFAULT_TIMEOUT = 600  # seconds


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


def setup_ssh_agent_and_add_key(ssh_path: str) -> None:

    """
    Start/ensure an SSH agent, then `ssh-add` the provided key.
    This will prompt for the passphrase in the terminal if the key is encrypted.
    """

    def _parse_ssh_agent_exports(output: str) -> dict:
        """
        Parse `ssh-agent -s` output like:
        SSH_AUTH_SOCK=/tmp/ssh-XXXX/agent.1234; export SSH_AUTH_SOCK;
        SSH_AGENT_PID=1234; export SSH_AGENT_PID;
        """
        env = {}
        for line in output.splitlines():
            if "SSH_AUTH_SOCK=" in line:
                env["SSH_AUTH_SOCK"] = line.split("SSH_AUTH_SOCK=", 1)[1].split(";", 1)[0].strip()
            elif "SSH_AGENT_PID=" in line:
                env["SSH_AGENT_PID"] = line.split("SSH_AGENT_PID=", 1)[1].split(";", 1)[0].strip()
        return env

    def _ensure_ssh_agent_running() -> None:
        """
        Ensure an ssh-agent is available and (on Unix) exported into os.environ.
        On Windows, starts the OpenSSH 'ssh-agent' service if needed.
        """
        if sys.platform.startswith("win"):
            # Use Windows OpenSSH agent service
            sc = shutil.which("sc")
            if sc is None:
                raise RuntimeError("Windows 'sc' utility not found; cannot control ssh-agent service.")
            try:
                # Set service to auto start (best effort)
                subprocess.run([sc, "config", "ssh-agent", "start=", "auto"],
                            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # Start the service (idempotent)
                subprocess.run([sc, "start", "ssh-agent"],
                            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                raise RuntimeError(f"Failed to start Windows ssh-agent service: {e}") from e
        else:
            # macOS / Linux: if no agent in env, start one and export vars into this process
            if not os.environ.get("SSH_AUTH_SOCK"):
                ssh_agent = shutil.which("ssh-agent")
                if not ssh_agent:
                    raise RuntimeError("ssh-agent not found in PATH.")
                proc = subprocess.run([ssh_agent, "-s"], check=True, capture_output=True, text=True, timeout=DEFAULT_TIMEOUT)
                env = _parse_ssh_agent_exports(proc.stdout)
                if not env:
                    raise RuntimeError("Failed to parse ssh-agent output.")
                os.environ.update(env)

    
    
    key = pathlib.Path(ssh_path).expanduser()
    if not key.is_file():
        raise FileNotFoundError(f"SSH key not found: {key}")

    _ensure_ssh_agent_running()

    ssh_add = shutil.which("ssh-add")
    if not ssh_add:
        raise RuntimeError("ssh-add not found in PATH.")

    # Run ssh-add in the current console so it can prompt for passphrase if needed.
    # Inherit environment so SSH_AUTH_SOCK/SSH_AGENT_PID (on Unix) are seen.
    try:
        subprocess.run([ssh_add, str(key)], check=True, timeout=DEFAULT_TIMEOUT)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ssh-add failed: {e}") from e


def _rc_verbose_args(level: int):
    # rclone supports -v / -vv / -vvv
    return ["-" + "v" * min(max(level, 0), 3)] if level > 0 else []


def _atomic_write_json(path: str, data: dict):
    path = pathlib.Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


def _prompt_with_default(prompt_text: str, default_val: str) -> str:
    val = input(f"{prompt_text} [{default_val}]: ").strip()
    return val if val else default_val


def _detect_default_ssh_key() -> str:
    # 1) previously saved env wins (default to "" so .strip() is safe)
    existing = (load_from_env("SSH_PATH", "") or "").strip()
    if existing:
        return existing

    # 2) common key names in ~/.ssh
    home = pathlib.Path.home() / ".ssh"
    for name in ("id_ed25519", "id_rsa", "id_ecdsa"):
        p = home / name
        if p.exists():
            return str(p)

    # 3) sensible suggestion even if missing
    return str(home / "id_ed25519")


def set_host_port(remote_name):

    def _validate_port(port_str: str, default_val: str) -> str:
        try:
            p = int(port_str)
            if 1 <= p <= 65535:
                return str(p)
        except Exception:
            pass
        print(f"Invalid port '{port_str}'. Using default '{default_val}'.")
        return default_val
    
    # --- specific remotes ---
    if remote_name in ["deic-storage", "erda", "ucloud"]:
        if remote_name == "deic-storage":
            save_to_env("sftp.storage.deic.dk", "HOST")
            save_to_env("2222", "PORT")
            return

        elif remote_name == "erda":
            save_to_env("io.erda.dk", "HOST")
            save_to_env("22", "PORT")
            return

        elif remote_name == "ucloud":
            save_to_env("ssh.cloud.sdu.dk", "HOST")
            existing_port = load_from_env("PORT")
            port_input = _prompt_with_default("Port for ucloud", existing_port)
            port_final = _validate_port(port_input, existing_port)
            save_to_env(port_final, "PORT")
            return
        
        elif remote_name == "lumi-p":
            save_to_env("lumi.csc.fi", "HOST")
            save_to_env("", "PORT")
            return
        
        else:
            # --- generic SFTP/SSH or unknown name ---
            existing_host = load_from_env("HOST")
            default_host = existing_host or "example.com"
            host_final = _prompt_with_default("SFTP/SSH host", default_host)

            existing_port = load_from_env("PORT")
            port_input = _prompt_with_default("Port", existing_port)
            port_final = _validate_port(port_input, existing_port)

            save_to_env(host_final, "HOST")
            save_to_env(port_final, "PORT")
    

def _ensure_repo_suffix(folder, repo):
    folder = folder.strip().replace("\\", "/").rstrip("/")
    
    # Then ensure repo name is in the path
    if not folder.endswith(repo):
        folder = os.path.join(folder, repo).replace("\\", "/")
    
    # Check if folder is within PROJECT_ROOT
    project_root_normalized = os.path.normpath(str(PROJECT_ROOT))
    folder_normalized = os.path.normpath(folder)
    
    # Check if folder is inside or equal to PROJECT_ROOT
    if folder_normalized.startswith(project_root_normalized):
        folder = project_root_normalized + "_backup"

    return folder


def _remote_user_info(remote_name):
    """Prompt for remote login credentials and base folder path."""

    repo_name = load_from_env("REPO_NAME", ".cookiecutter")

    if remote_name.lower() == "deic-storage":
        email = load_from_env("DEIC_EMAIL")
        password = load_from_env("DEIC_PASS")
        base_folder = load_from_env("DEIC_BASE")

        if email and password and base_folder:
            base_folder = _ensure_repo_suffix(base_folder, repo_name)
            return remote_name, email, password, base_folder

        default_email = load_from_env("EMAIL", ".cookiecutter")
        default_base = f"rclone-backup/{repo_name}"
        base_folder = (
            input(f"Enter base folder for {remote_name} [{default_base}]: ").strip() or default_base
        )
        base_folder = _ensure_repo_suffix(base_folder, repo_name)

        email = password = None
        while not email or not password:
            email = (
                input(f"Please enter email to Deic-Storage [{default_email}]: ").strip()
                or default_email
            )
            password = getpass.getpass("Please enter password to Deic-Storage: ").strip()

            if not email or not password:
                print("Both email and password are required.\n")

        print(f"\nUsing email: {email}")
        print(f"Using base folder: {base_folder}\n")

        save_to_env(email, "DEIC_EMAIL")
        save_to_env(password, "DEIC_PASS")
        save_to_env(base_folder, "DEIC_BASE")

        return remote_name, email, password, base_folder
    
    elif remote_name.lower() == "ucloud":
        default_base = f"work/rclone-backup/{repo_name}"
        base_folder = (
            input(f"Enter base folder for {remote_name} [{default_base}]: ").strip() or default_base
        )
        base_folder = _ensure_repo_suffix(base_folder, repo_name)
        
        return remote_name, "ucloud", None, base_folder

    elif remote_name.lower() == "local":
        base_folder = (
            input("Please enter the local path for rclone: ")
            .strip()
            .replace("'", "")
            .replace('"', "")
        )
        base_folder = check_path_format(base_folder)
        if not os.path.isdir(base_folder):
            print(f"Error: The specified local path does not exist{base_folder}")
            return remote_name, None, None, None
        base_folder = _ensure_repo_suffix(base_folder, repo_name)
        return remote_name, None, None, base_folder

    elif "lumi" in remote_name.lower():
        remote_type = "public" if "public" in remote_name.lower() else "private"
        base_folder = load_from_env(f"LUMI_BASE_{remote_type.upper()}")
        if not base_folder:
            remote_name, base_folder, access_key, secret_key  = _handle_lumi_o_remote(remote_name)
        
        return remote_name, access_key, secret_key, base_folder
 
    elif remote_name.lower() != "none":
        default_base = f"rclone-backup/{repo_name}"
        base_folder = (
            input(f"Enter base folder for {remote_name} [{default_base}]: ").strip() or default_base
        )
        base_folder = _ensure_repo_suffix(base_folder, repo_name)
        return remote_name, None, None, base_folder

    else:
        return remote_name, None, None, None


def _lumi_o_remote_name(remote_name):
    project_id = load_from_env("LUMI_PROJECT_ID")
    remote_type = "public" if "public" in remote_name.lower() else "private"
    remote_name = f"lumi-{project_id}-{remote_type}"
    return remote_name


def _check_lumi_o_credentials(repo_name: str, command: str = "add"):
    project_id = load_from_env("LUMI_PROJECT_ID")

    if not project_id and command == "add":
        repo_name, _, _, _ = _handle_lumi_o_remote(repo_name)
        return repo_name
    elif not project_id and command != "add":
        print(f"{repo_name} remote not found. Please set up the remote first by running 'backup add --remote {repo_name}'.")
        return None
    elif project_id:
        remote_name = _lumi_o_remote_name(remote_name)
        return remote_name
    else:
        return None


def _handle_lumi_o_remote(remote_name):
    """Handle LUMI-O remote configuration and credentials."""
    
    remote_type = "public" if "public" in remote_name.lower() else "private"

    # Try to load existing credentials
    repo_name = load_from_env("REPO_NAME", ".cookiecutter")
    project_id = load_from_env("LUMI_PROJECT_ID")
    access_key = load_from_env("LUMI_ACCESS_KEY")
    secret_key = load_from_env("LUMI_SECRET_KEY")
    base_folder = load_from_env(f"LUMI_BASE_{remote_type.upper()}")
    
    if project_id and access_key and secret_key and base_folder:
        base_folder = _ensure_repo_suffix(base_folder, repo_name)
        remote_name = _lumi_o_remote_name(remote_name)
        return remote_name, base_folder, access_key, secret_key
    
    # Prompt for credentials
    default_base = f"rclone-backup/{repo_name}"
    base_folder = (
        input(f"Enter base folder for LUMI-O ({remote_type}) [{default_base}]: ").strip() 
        or default_base
    )
    base_folder = _ensure_repo_suffix(base_folder, repo_name)
    
    print("\nGet your LUMI-O credentials from: https://auth.lumidata.eu")
    
    project_id = access_key = secret_key = None
    while not project_id or not access_key or not secret_key:
        project_id = input("Please enter LUMI project ID (e.g., 465000001): ").strip()
        access_key = input("Please enter LUMI access key: ").strip()
        secret_key = getpass.getpass("Please enter LUMI secret key: ").strip()
        
        if not project_id or not access_key or not secret_key:
            print("All three fields (project ID, access key, secret key) are required.\n")
    
    print(f"\nUsing project ID: {project_id}")
    print(f"Using base folder: {base_folder}")
    print(f"Remote type: {remote_type}\n")
    
    # Save credentials
    save_to_env(project_id, "LUMI_PROJECT_ID")
    save_to_env(access_key, "LUMI_ACCESS_KEY")
    save_to_env(secret_key, "LUMI_SECRET_KEY")
    save_to_env(base_folder, f"LUMI_BASE_{remote_type.upper()}")
    
    remote_name = _lumi_o_remote_name(remote_name)

    return remote_name, base_folder, access_key, secret_key 


def _load_rclone_json(remote_name: str, json_path="./bin/rclone_remote.json") -> str:
    if not os.path.exists(json_path):
        print(f"No rclone registry found at {json_path}")
        return None
    try:
        with open(json_path) as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("Could not parse rclone registry file — it may be corrupted.")
        return None
    entry = data.get(remote_name)
    if isinstance(entry, dict):
        return entry.get("path")
    return entry


def _save_rclone_json(remote_name: str, folder_path: str, json_path="./bin/rclone_remote.json"):
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    data = {}
    if os.path.exists(json_path):
        with open(json_path) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print("Warning: JSON file was corrupted or empty, reinitializing.")
    data[remote_name] = {
        "path": f"{remote_name}:{folder_path}",
        "last_sync": None,
        "status": "initialized",
    }
    _atomic_write_json(json_path, data)
    print(f"Saved rclone path ({folder_path}) for '{remote_name}' to {json_path}")


def _load_all_rclone_json(json_path="./bin/rclone_remote.json"):
    if not os.path.exists(json_path):
        return {}
    try:
        with open(json_path) as f:
            return json.load(f)
    except Exception:
        return {}


def _update_last_sync(remote_name: str, success=True, json_path="./bin/rclone_remote.json"):
    if not os.path.exists(json_path):
        return
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
        if remote_name in data and isinstance(data[remote_name], dict):
            data[remote_name]["last_sync"] = datetime.now().isoformat()
            data[remote_name]["status"] = "ok" if success else "potentially corrupt"
        _atomic_write_json(json_path, data)
    except Exception as e:
        print(f"Failed to update sync status: {e}")


def _rclone_transfer(
    remote_name: str = None,
    folder_to_backup: str = None,
    operation: str = "sync",
    *,
    dry_run: bool = False,
    verbose: int = 0,
):
    """
    Transfer a folder to an rclone remote using either 'sync' or 'copy'.

    Args:
        remote_name: Name of the configured rclone remote (as used in _load_rclone_json).
        folder_to_backup: Local path to transfer. Defaults to PROJECT_ROOT.
        operation: 'sync' (mirror dest to source; deletes extras) or 'copy' (only upload/update).
    """
    operation = operation.lower().strip()
    if operation not in {"sync", "copy","move"}:
        print("Error: 'operation' must be either 'sync', 'copy', or 'move'")
        return

    rclone_repo = _load_rclone_json(remote_name)
    if not rclone_repo:
        print("remote has not been configured")
        return

    if folder_to_backup is None:
        folder_to_backup = str(PROJECT_ROOT)

    if not os.path.exists(folder_to_backup):
        print(f"Error: The folder '{folder_to_backup}' does not exist.")
        return

    _, exclude_patterns = toml_ignore(
        folder=folder_to_backup,
        toml_path="pyproject.toml",
        ignore_filename=".rcloneignore",
        tool_name="rcloneignore",
        toml_key="patterns",
    )

    exclude_args = []
    for pattern in exclude_patterns:
        exclude_args.extend(["--exclude", pattern])

    # Commit/log/push steps (kept from your original)
    if os.path.exists(".git") and not os.path.exists(".datalad") and not os.path.exists(".dvc"):
        with change_dir("./data"):
            _ = git_commit(msg="Running 'set-dataset'", path=os.getcwd())
            git_log_to_file(os.path.join(".gitlog"))

    git_push(load_from_env("CODE_REPO", ".cookiecutter") != "None", "Rclone Backup")

    # Build rclone command based on operation
    command = ["rclone", operation, folder_to_backup, rclone_repo] + _rc_verbose_args(verbose) + ["--verbose"] + exclude_args
    if dry_run:
        command.append("--dry-run")


    remote_short_name = rclone_repo.split(":")[0]

    try:
        subprocess.run(command, check=True, timeout=DEFAULT_TIMEOUT)
        verb = "synchronized" if operation == "sync" else "copied"
        print(f"Folder '{folder_to_backup}' successfully {verb} to '{rclone_repo}'.")
        _update_last_sync(remote_short_name, success=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to {operation} folder to remote: {e}")
        _update_last_sync(remote_short_name, success=False)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        _update_last_sync(remote_short_name, success=False)



def list_remotes():
    print("\n🔌 Rclone Remotes:")
    try:
        result = subprocess.run(["rclone", "listremotes"], check=True, stdout=subprocess.PIPE, timeout=DEFAULT_TIMEOUT)
        rclone_configured = set(r.rstrip(":") for r in result.stdout.decode().splitlines())
    except Exception as e:
        print(f"Failed to list remotes: {e}")
        rclone_configured = set()

    print("\n📁 Mapped Backup Folders:")
    paths = _load_all_rclone_json()
    if not paths:
        print("  No folders registered.")
    else:
        for remote, meta in paths.items():
            path = meta.get("path") if isinstance(meta, dict) else meta
            last_sync = meta.get("last_sync") if isinstance(meta, dict) else "-"
            status = meta.get("status") if isinstance(meta, dict) else "-"
            status_note = "✅" if remote in rclone_configured else "⚠️ missing in rclone config"
            print(f"  - {remote}: {path} | Last Sync: {last_sync} | Status: {status} {status_note}")


def check_rclone_remote(remote_name):
    try:
        result = subprocess.run(
            ["rclone", "listremotes"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=DEFAULT_TIMEOUT
        )
        remotes = result.stdout.decode("utf-8").splitlines()
        return f"{remote_name}:" in remotes
    except subprocess.CalledProcessError as e:
        print(f"Failed to check rclone remotes: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


def _add_remote(remote_name: str = None, login: str = None, pass_key: str = None):

    if remote_name in ["deic-storage", "erda", "ucloud"]:
        # Build the create command
        command = [
            "rclone", "config", "create",
            remote_name, "sftp",
            "host", load_from_env("HOST"),
            "port", load_from_env("PORT"),
            "user", login,
        ]

        if remote_name == "ucloud":
            # prompt for SSH key (ucloud only)
            default_key = _detect_default_ssh_key()
            ssh_path = _prompt_with_default("Path to SSH private key for ucloud", default_key).strip()
            ssh_path = str(pathlib.Path(ssh_path).expanduser())  # expand ~ on all OSes

            if ssh_path and os.path.isfile(ssh_path):
                # Start agent + add the key (will prompt for passphrase if needed)
                setup_ssh_agent_and_add_key(ssh_path)
                # Tell rclone to use the agent
                command += ["use_agent", "true"]
            else:
                return print(f"SSH key file not found: {ssh_path}")

        elif pass_key:
            # pass_key is a password
            command += ["pass", pass_key, "--obscure"]
        else:
            # last resort: rely on an SSH agent
            command += ["use_agent", "true"]

    elif "lumi" in remote_name.lower():

        # Determine remote type and ACL
        if "public" in remote_name.lower():
            acl = "public-read"
        else:
            acl = "private"

        # Create remote command (S3)
        command = [
            "rclone", "config", "create",
            remote_name, "s3",
            "provider", "Other",
            "endpoint", "https://lumidata.eu",
            "access_key_id", login,
            "secret_access_key", pass_key,
            "region", "other-v2-signature",
            "acl", acl,
        ]

    elif remote_name in ["dropbox", "onedrive", "local"]:
        if remote_name in ["dropbox", "onedrive"]:
            print(f"You will need to authorize rclone with {remote_name}")
        command = ["rclone", "config", "create", remote_name, remote_name]

    else:
        # Fetch all backend types from rclone
        output = list_supported_remote_types()
        backend_types = [
            line.split()[0]
            for line in output.splitlines()
            if line and not line.startswith(" ") and ":" in line
        ]

        if remote_name in backend_types:
            print(f"Running interactive config for backend '{remote_name}'...")
            command = ["rclone", "config", "create", remote_name, remote_name]
        else:
            print("Unsupported remote name.")
            return

    try:
        subprocess.run(command, check=True, timeout=DEFAULT_TIMEOUT)
        print(f"Rclone remote '{remote_name}' created successfully.")
    except Exception as e:
        print(f"Failed to create rclone remote: {e}")


def _add_folder(remote_name:str = None, base_folder:str = None):

    # Remove leading slash for cloud storage providers that don't use absolute paths
    if remote_name.lower() in ["dropbox", "onedrive"]:
        base_folder = base_folder.lstrip('/')
        command = ["rclone","lsd", f"{remote_name}:{base_folder}"]  # NO leading /
        mkdir_cmd = ["rclone","mkdir", f"{remote_name}:{base_folder}"]  # NO leading /

    elif "lumi" in remote_name.lower():
        command = ["rclone","lsd", f"{remote_name}:/{base_folder}"]
        mkdir_cmd = ["rclone","mkdir", f"{remote_name}:/{base_folder}"]
    else: # SFTP or Local
        command = ["rclone","lsf", f"{remote_name}:/{base_folder}"]
        mkdir_cmd = ["rclone","mkdir", f"{remote_name}:/{base_folder}"]

    while True:
        result = subprocess.run(command, capture_output=True, text=True, timeout=DEFAULT_TIMEOUT)
        if result.returncode == 0 and result.stdout.strip():
            choice = (
                input(
                    f"'{base_folder}' exists on '{remote_name}'. Overwrite (o), rename (n), cancel (c)? [o/n/c]: "
                )
                .strip()
                .lower()
            )
            if choice == "o":
                break
            elif choice == "n":
                base_folder = input("New folder name: ").strip()
                if remote_name.lower() in ["dropbox", "onedrive"]:
                    base_folder = base_folder.lstrip('/')
            else:
                print("Cancelled.")
                return
        else:
            break
    try:
        subprocess.run(mkdir_cmd, check=True, timeout=DEFAULT_TIMEOUT)
        _save_rclone_json(remote_name, base_folder)
    except Exception as e:
        print(f"Error creating folder: {e}")


def delete_remote(remote_name: str, json_path="./bin/rclone_remote.json", verbose: int = 0):
    
    
    # Step 1: Attempt to delete the actual remote directory if it exists
    remote_path = _load_rclone_json(remote_name, json_path)
    if remote_path:
        try:
            print(f"Attempting to purge remote folder at: {remote_path}")
            subprocess.run(["rclone","purge",remote_path] + _rc_verbose_args(verbose), check=True, timeout=DEFAULT_TIMEOUT)
            print(f"Successfully purged remote folder: {remote_path}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Warning: Could not purge remote folder '{remote_path}': {e}")
        except Exception as e:
            print(f"Unexpected error during purge: {e}")
    else:
        return
    # Step 2: Delete the remote from rclone config
    try:
        subprocess.run(["rclone","config","delete",remote_name] + _rc_verbose_args(verbose), check=True, timeout=DEFAULT_TIMEOUT)
        print(f"Rclone remote '{remote_name}' deleted from rclone configuration.")
    except subprocess.CalledProcessError as e:
        print(f"Error deleting remote from rclone: {e}")

    # Step 3: Remove entry from local JSON registry
    if os.path.exists(json_path):
        try:
            with open(json_path, "r+") as f:
                data = json.load(f)
                if remote_name in data:
                    del data[remote_name]
                    f.seek(0)
                    f.truncate()
                    json.dump(data, f, indent=2)
                    print(f"Removed '{remote_name}' entry from {json_path}.")
        except Exception as e:
            print(f"Error updating JSON config: {e}")


def setup_rclone(remote_name: str = None):
    if remote_name:
        remote_name, login_key, pass_key, base_folder = _remote_user_info(remote_name.lower())
        _add_remote(remote_name.lower(), login_key, pass_key)
        _add_folder(remote_name.lower(), base_folder)
    else:
        install_rclone("./bin")


def list_supported_remote_types():
    #if install_rclone("./bin"):
    try:
        result = subprocess.run(["rclone", "help", "backends"], check=True, stdout=subprocess.PIPE, text=True, timeout=DEFAULT_TIMEOUT)
        print("\n📦 Supported Rclone Remote Types:")
        print("\nRecommended: ['Deic-Storage','ERDA' ,'Dropbox', 'Onedrive', 'Local']\n")
        print("\nSupported by Rclone:\n")
        print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error fetching remote types: {e}")
        return ""


def generate_diff_report(remote_name):
    def run_diff(remote):
        remote_path = _load_rclone_json(remote)
        if not remote_path:
            print(f"No path found for remote '{remote}'.")
            return
        with tempfile.NamedTemporaryFile() as temp:
            command = [
                "rclone",
                "diff",
                ".",
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
        for remote in _load_all_rclone_json().keys():
            run_diff(remote)
    else:
        run_diff(remote_name)


def push_rclone(remote_name:str, operation:str = "sync", dry_run: bool = False, verbose: int = 0):

    os.chdir(PROJECT_ROOT)

    if not install_rclone("./bin"):
        return
    if remote_name.lower() == "all":
        all_remotes = _load_all_rclone_json()
        for remote_name in all_remotes:
            _rclone_transfer(remote_name.lower(), operation = operation, dry_run=dry_run, verbose=verbose)
    else:
        rclone_repo = _load_rclone_json(remote_name.lower())
        if not rclone_repo:
            remote_name, login_key, pass_key, base_folder = _remote_user_info(remote_name.lower())
            _add_remote(remote_name.lower(), login_key, pass_key)
            _add_folder(remote_name.lower(), base_folder)
        
        _rclone_transfer(remote_name.lower(), operation = operation, dry_run=dry_run, verbose=verbose)


def pull_rclone(remote_name: str = None, destination_folder: str = None , dry_run: bool = False, verbose: int = 0):

    if remote_name is None:
        print("Error: No remote specified for pulling backup.")
        return

    rclone_repo = _load_rclone_json(remote_name)
    if not rclone_repo:
        print("Remote has not been configured or not found in registry.")
        return

    if destination_folder is None:
        destination_folder = str(PROJECT_ROOT)

    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    _, exclude_patterns = toml_ignore(
        folder=destination_folder,
        toml_path="pyproject.toml",
        ignore_filename=".rcloneignore",
        tool_name="rcloneignore",
        toml_key="patterns",
    )

    exclude_args = []
    for pattern in exclude_patterns:
        exclude_args.extend(["--exclude", pattern])

    command = ["rclone", "sync", rclone_repo, destination_folder] + _rc_verbose_args(verbose) + ["--verbose"] + exclude_args
    if dry_run:
        command.append("--dry-run")

    try:
        subprocess.run(command, check=True, timeout=DEFAULT_TIMEOUT)
        print(f"Backup pulled from '{rclone_repo}' to '{destination_folder}' successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to pull backup from remote: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while pulling backup: {e}")


@ensure_correct_kernel
def scp_cli():
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
    if remote == "deic storage":
        remote = "deic-storage"

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


@ensure_correct_kernel
def rclone_cli():
    if not install_rclone("./bin"):
        print("Error: rclone installation/verification failed.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Backup manager CLI using rclone")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List rclone remotes and mapped folders")
    parser.add_argument("--dry-run", action="store_true", help="Do not modify remote; show actions.")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity (-v, -vv, -vvv).")


    copy = subparsers.add_parser("copy", help="Copy local folder to a remote (no deletes)")
    copy.add_argument("--remote", required=True)

    move = subparsers.add_parser("move", help="Moves local folder to a remote (deletes from source)")
    move.add_argument("--remote", required=True)

    add = subparsers.add_parser("add", help="Add a remote and folder mapping")
    add.add_argument("--remote", required=True)

    push = subparsers.add_parser("push", help="Push local folder to a remote")
    push.add_argument("--remote", required=True)

    delete = subparsers.add_parser("delete", help="Delete a remote and its mapping")
    delete.add_argument("--remote", required=True)

    diff = subparsers.add_parser("diff", help="Generate a diff report for a remote")
    diff.add_argument("--remote", required=True)

    pull = subparsers.add_parser("pull", help="Pull backup from a remote")
    pull.add_argument("--remote", required=True)
    pull.add_argument("--dest", required=True)

    args = parser.parse_args()

    # Normalize remote name when present
    if hasattr(args, "remote") and args.remote:
        remote = args.remote.strip().lower()
        if remote == "deic storage":
            remote = "deic-storage"
        elif "lumi" in remote:
            remote = _check_lumi_o_credentials(repo_name=remote, command=args.command)
            if remote is None:
                return
        elif remote == "ucloud":
            print("Ucloud remote only supports 'copy' commands at this point.")
            return

        # Only prompt/set host/port when the command actually needs to connect/create
        if args.command in {"add", "push", "pull","copy"}:
            set_host_port(remote)

        # Dispatch
        if args.command == "add":
            setup_rclone(remote)
        elif args.command == "push":
            push_rclone(remote_name = remote, operation ="sync", dry_run=args.dry_run, verbose=args.verbose)
        elif args.command == "copy":
                push_rclone(remote_name = remote, operation ="copy", dry_run=args.dry_run, verbose=args.verbose)
        elif args.command == "delete":
            delete_remote(remote_name = remote)
        elif args.command == "diff":
            generate_diff_report(remote_name = remote)
        elif args.command == "pull":
            pull_rclone(remote_name = remote,destination_folder= args.dest, dry_run=args.dry_run, verbose=args.verbose)

    else:
        # Commands without a remote
        if args.command == "list":
            list_remotes()
        elif args.command == "types":
            list_supported_remote_types()
        else:
            parser.print_help()
            sys.exit(2)


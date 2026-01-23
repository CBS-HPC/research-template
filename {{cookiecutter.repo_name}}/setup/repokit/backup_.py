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
import platform
import requests
import zipfile
import glob

from .common import (
    PROJECT_ROOT,
    change_dir,
    ensure_correct_kernel,
    load_from_env,
    save_to_env,
    toml_ignore,
    check_path_format,
    exe_to_path,
    is_installed,
)
from .vcs import git_commit, git_log_to_file, git_push


# --- new helpers ---
DEFAULT_TIMEOUT = 600  # seconds

def install_rclone(install_path):
    """Download and extract rclone to the specified bin folder."""

    def download_rclone(install_path="./bin"):
        os_type = platform.system().lower()

        # Set the URL and executable name based on the OS
        if os_type == "windows":
            url = "https://downloads.rclone.org/rclone-current-windows-amd64.zip"
            rclone_executable = "rclone.exe"
        elif os_type in ["linux", "darwin"]:  # "Darwin" is the system name for macOS
            url = (
                "https://downloads.rclone.org/rclone-current-linux-amd64.zip"
                if os_type == "linux"
                else "https://downloads.rclone.org/rclone-current-osx-amd64.zip"
            )
            rclone_executable = "rclone"
        else:
            print(f"Unsupported operating system: {os_type}. Please install rclone manually.")
            return None

        # Create the bin folder if it doesn't exist
        install_path = str(PROJECT_ROOT / pathlib.Path(install_path))
        os.makedirs(install_path, exist_ok=True)

        # Download rclone
        local_zip = os.path.join(install_path, "rclone.zip")
        print(f"Downloading rclone for {os_type} to {local_zip}...")
        response = requests.get(url)
        if response.status_code == 200:
            with open(local_zip, "wb") as file:
                file.write(response.content)
            print("Download complete.")
        else:
            print("Failed to download rclone. Please check the URL.")
            return None

        # Extract the rclone executable
        print("Extracting rclone...")
        with zipfile.ZipFile(local_zip, "r") as zip_ref:
            zip_ref.extractall(install_path)

        rclone_folder = glob.glob(os.path.join(install_path, "rclone-*"))

        if not rclone_folder or len(rclone_folder) > 1:
            print(f"More than one 'rclone-*' folder detected in {install_path}")
            return None

        # Clean up by deleting the zip file
        os.remove(local_zip)

        rclone_path = os.path.join(install_path, rclone_folder[0], rclone_executable)
        print(f"rclone installed successfully at {rclone_path}.")

        rclone_path = os.path.abspath(rclone_path)

        os.chmod(rclone_path, 0o755)
        return rclone_path

    if not is_installed("rclone", "Rclone"):
        rclone_path = download_rclone(install_path)
        return exe_to_path("rclone", os.path.dirname(rclone_path))
    return True


def rclone_commit(local_path, flag:bool=False, msg: str = "Rclone Backup Commit"):
    if not flag and(pathlib.Path(local_path).resolve() == PROJECT_ROOT.resolve()):
        flag = True
        if os.path.exists(".git") and not os.path.exists(".datalad") and not os.path.exists(".dvc"):
            with change_dir("./data"):
                _ = git_commit(msg=msg, path=os.getcwd())
                git_log_to_file(os.path.join(".gitlog"))
            git_push(load_from_env("CODE_REPO", ".cookiecutter") != "None", msg)

    return flag


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
    
    # Detect remote type
    remote_type = _detect_remote_type(remote_name)
    
    # Only set host/port for SFTP-based remotes
    if remote_type in ["erda", "ucloud"]:
        if remote_type == "erda":
            save_to_env("io.erda.dk", "HOST")
            save_to_env("22", "PORT")
            return

        elif remote_type == "ucloud":
            save_to_env("ssh.cloud.sdu.dk", "HOST")
            existing_port = load_from_env("PORT")
            port_input = _prompt_with_default("Port for ucloud", existing_port)
            port_final = _validate_port(port_input, existing_port)
            save_to_env(port_final, "PORT")
            return
    
    # For other types (dropbox, onedrive, etc.), no host/port needed
    # They use OAuth or other authentication methods


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


def _remote_user_info(remote_name: str, local_backup_path: str):
    repo_name = pathlib.Path(local_backup_path).name
    remote_type = _detect_remote_type(remote_name)

    handlers = {
        "ucloud": _ucloud_remote_info,
        "local": _local_remote_info,
        "dropbox": _oauth_remote_info,
        "onedrive": _oauth_remote_info,
        "drive": _oauth_remote_info,
    }

    if "lumi" in remote_type:
        return _lumi_remote_info(remote_name, repo_name)

    handler = handlers.get(remote_type, _generic_remote_info)
    return handler(remote_name, repo_name)

def _ucloud_remote_info(remote_name: str, repo_name: str):
    default_base = f"work/rclone-backup/{repo_name}"
    base_folder = input(
        f"Enter base folder for {remote_name} [{default_base}]: "
    ).strip() or default_base

    base_folder = _ensure_repo_suffix(base_folder, repo_name)
    return remote_name, "ucloud", None, base_folder

def _local_remote_info(remote_name: str, repo_name: str):
    base_folder = (
        input("Please enter the local path for rclone: ")
        .strip()
        .replace("'", "")
        .replace('"', "")
    )

    base_folder = check_path_format(base_folder)
    if not os.path.isdir(base_folder):
        print(f"Error: The specified local path does not exist: {base_folder}")
        return remote_name, None, None, None

    base_folder = _ensure_repo_suffix(base_folder, repo_name)
    return remote_name, None, None, base_folder

def _oauth_remote_info(remote_name: str, repo_name: str):
    default_base = f"rclone-backup/{repo_name}"
    base_folder = input(
        f"Enter base folder for {remote_name} [{default_base}]: "
    ).strip() or default_base

    base_folder = _ensure_repo_suffix(base_folder, repo_name)
    return remote_name, None, None, base_folder

def _lumi_remote_info(remote_name: str, repo_name: str):
    remote_type_suffix = "public" if "public" in remote_name.lower() else "private"
    base_folder = load_from_env(f"LUMI_BASE_{remote_type_suffix.upper()}")

    if not base_folder:
        return _handle_lumi_o_remote(remote_name)

    base_folder = _ensure_repo_suffix(base_folder, repo_name)
    return remote_name, None, None, base_folder

def _generic_remote_info(remote_name: str, repo_name: str):
    default_base = f"rclone-backup/{repo_name}"
    base_folder = input(
        f"Enter base folder for {remote_name} [{default_base}]: "
    ).strip() or default_base

    base_folder = _ensure_repo_suffix(base_folder, repo_name)
    return remote_name, None, None, base_folder


def _remote_user_info_old(remote_name:str = None, local_backup_path:str = None):
    """Prompt for remote login credentials and base folder path."""

    repo_name = str(pathlib.Path(local_backup_path).name)


    #repo_name = load_from_env("REPO_NAME", ".cookiecutter")
    remote_type = _detect_remote_type(remote_name)
    
    if remote_type == "ucloud":
        default_base = f"work/rclone-backup/{repo_name}"
        base_folder = (
            input(f"Enter base folder for {remote_name} [{default_base}]: ").strip() or default_base
        )
        base_folder = _ensure_repo_suffix(base_folder, repo_name)
        
        return remote_name, "ucloud", None, base_folder

    elif remote_type == "local":
        base_folder = (
            input("Please enter the local path for rclone: ")
            .strip()
            .replace("'", "")
            .replace('"', "")
        )
        base_folder = check_path_format(base_folder)
        if not os.path.isdir(base_folder):
            print(f"Error: The specified local path does not exist: {base_folder}")
            return remote_name, None, None, None
        base_folder = _ensure_repo_suffix(base_folder, repo_name)
        return remote_name, None, None, base_folder

    elif "lumi" in remote_type:
        remote_type_suffix = "public" if "public" in remote_name.lower() else "private"
        base_folder = load_from_env(f"LUMI_BASE_{remote_type_suffix.upper()}")
        if not base_folder:
            remote_name, base_folder, access_key, secret_key = _handle_lumi_o_remote(remote_name)
        
        return remote_name, access_key, secret_key, base_folder
    
    elif remote_type in ["dropbox", "onedrive", "drive"]:
        default_base = f"rclone-backup/{repo_name}"
        base_folder = (
            input(f"Enter base folder for {remote_name} [{default_base}]: ").strip() or default_base
        )
        base_folder = _ensure_repo_suffix(base_folder, repo_name)
        return remote_name, None, None, base_folder
 
    elif remote_name.lower() != "none":
        # Generic remote
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


def _check_lumi_o_credentials(remote_name: str, command: str = "add"):
    project_id = load_from_env("LUMI_PROJECT_ID")

    if not project_id and command == "add":
        remote_name, _, _, _ = _handle_lumi_o_remote(remote_name)
        return remote_name
    elif not project_id and command != "add":
        print(f"{remote_name} remote not found. Please set up the remote first by running 'backup add --remote {remote_name}'.")
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


def _load_rclone_json(
    remote_name: str,
    json_path: str = "./bin/rclone_remote.json",
) -> tuple[str | None, str | None]:
    """
    Load rclone remote mapping.

    Returns:
        (remote_path, local_path)
        Both values are None if the remote is not found or registry is invalid.
    """
    if not os.path.exists(json_path):
        print(f"No rclone registry found at {json_path}")
        return None, None

    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("Could not parse rclone registry file — it may be corrupted.")
        return None, None
    except OSError as e:
        print(f"Failed to read rclone registry: {e}")
        return None, None

    entry = data.get(remote_name)
    if not isinstance(entry, dict):
        return None, None

    return entry.get("remote_path"), entry.get("local_path")


def _save_rclone_json(remote_name: str, folder_path: str, local_backup_path: str = None, json_path="./bin/rclone_remote.json"):
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    data = {}
    if os.path.exists(json_path):
        with open(json_path) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print("Warning: JSON file was corrupted or empty, reinitializing.")
    
    # Detect and store remote type
    remote_type = _detect_remote_type(remote_name)
    
    data[remote_name] = {
        "remote_path": f"{remote_name}:{folder_path}",
        "local_path": local_backup_path,
        "remote_type": remote_type,
        "last_action": None,
        "last_operation": None,
        "timestamp": None,
        "status": "initialized",
    }
    _atomic_write_json(json_path, data)
    print(f"Saved rclone path ({folder_path}) for '{remote_name}' to {json_path}")
    print(f"Local backup source: {local_backup_path}")
    print(f"Remote type: {remote_type}")


def _load_all_rclone_json(json_path="./bin/rclone_remote.json"):
    if not os.path.exists(json_path):
        return {}
    try:
        with open(json_path) as f:
            return json.load(f)
    except Exception:
        return {}


def _update_last_sync(remote_name: str, action: str, operation: str, success=True, json_path="./bin/rclone_remote.json"):
    if not os.path.exists(json_path):
        return
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
        if remote_name in data and isinstance(data[remote_name], dict):
            data[remote_name]["last_action"] = action
            data[remote_name]["last_operation"] = operation
            data[remote_name]["timestamp"] = datetime.now().isoformat()
            data[remote_name]["status"] = "ok" if success else "potentially corrupt"
        _atomic_write_json(json_path, data)
    except Exception as e:
        print(f"Failed to update sync status: {e}")


def _detect_remote_type(remote_name: str) -> str:
    """
    Detect the remote type based on the remote name prefix.
    
    Args:
        remote_name: The full remote name (e.g., 'dropbox-dataset1', 'onedrive-work')
    
    Returns:
        The remote type (e.g., 'dropbox', 'onedrive', 'erda')
    """
    remote_lower = remote_name.lower()
    
    # Check for known prefixes
    known_types = [
        'dropbox', 'onedrive', 'googledrive', 'gdrive',
        'erda', 'ucloud', 
        'lumi', 'local', 's3', 'sftp'
    ]
    
    for remote_type in known_types:
        if remote_lower.startswith(remote_type):
            # Handle special cases
            if remote_type in ['googledrive', 'gdrive']:
                return 'drive'  # rclone uses 'drive' for Google Drive
            return remote_type
    
    # If no known prefix, assume it's a custom SFTP or generic remote
    return 'sftp'


def _get_base_remote_type(remote_name: str) -> str:
    """
    Get the base remote type for configuration purposes.
    Similar to _detect_remote_type but returns the exact string needed for rclone config.
    """
    remote_type = _detect_remote_type(remote_name)
    
    # Map to rclone backend names
    type_mapping = {
        'erda': 'sftp',
        'ucloud': 'sftp',
        'googledrive': 'drive',
        'gdrive': 'drive',
    }
    
    return type_mapping.get(remote_type, remote_type)


def _rclone_transfer(
    remote_name: str = None,
    local_path: str = None,
    remote_path: str = None,
    action: str = "push",
    operation: str = "sync",
    exclude_patterns: list[str] = None,
    *,
    dry_run: bool = False,
    verbose: int = 0,
):
    """
    Transfer a folder to an rclone remote using either 'sync' or 'copy'.

    Args:
        remote_name: Name of the configured rclone remote (as used in _load_rclone_json).

        operation: 'sync' (mirror dest to source; deletes extras) or 'copy' (only upload/update).
    """
    exclude_patterns = exclude_patterns or []

    operation = operation.lower().strip()
    if operation not in {"sync", "copy","move"}:
        print("Error: 'operation' must be either 'sync', 'copy', or 'move'")
        return


    exclude_args = []
    for pattern in exclude_patterns:
        exclude_args.extend(["--exclude", pattern])


    if action == "push":
        if not os.path.exists(local_path):
            print(f"Error: The folder '{local_path}' does not exist.")
            return
        # Build rclone command based on operation
        command = ["rclone", operation, local_path, remote_path] + _rc_verbose_args(verbose) + exclude_args

    elif action == "pull":
                # Build rclone command based on operation
        command = ["rclone", operation, remote_path, local_path] + _rc_verbose_args(verbose) + exclude_args
    
    if dry_run: 
        command.append("--dry-run")

    try:
        subprocess.run(command, check=True, timeout=DEFAULT_TIMEOUT)
        
        if operation == "sync": 
            verb = "synchronized"
        elif operation == "copy":
            verb = "copied"
        else:
            verb = "moved (deleted at origin)"

        print(f"Folder '{local_path}' successfully {verb} to '{remote_path}'.")
        _update_last_sync(remote_name, action=action, operation=operation, success=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to {operation} folder to remote: {e}")
        _update_last_sync(remote_name, action=action, operation=operation, success=False)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        _update_last_sync(remote_name, action=action, operation=operation, success=False)


def list_remotes():
    print("\n🔌 Rclone Remotes:")
    try:
        result = subprocess.run(["rclone", "listremotes"], check=True, stdout=subprocess.PIPE, timeout=DEFAULT_TIMEOUT)
        rclone_configured = set(r.rstrip(":") for r in result.stdout.decode().splitlines())
    except Exception as e:
        print(f"Failed to list remotes: {e}")
        rclone_configured = set()

    print("\n📁 Mapped Backup Folders:")
    all_remotes = _load_all_rclone_json()
    if not all_remotes:
        print("  No folders registered.")
    else:
        for remote, meta in all_remotes.items():
            remote_path = meta.get("remote_path") if isinstance(meta, dict) else meta
            local_path = meta.get("local_path", "Not specified") if isinstance(meta, dict) else "Not specified"
            remote_type = meta.get("remote_type", "unknown") if isinstance(meta, dict) else "unknown"
            action = meta.get("last_action") if isinstance(meta, dict) else "-"
            operation = meta.get("last_operation") if isinstance(meta, dict) else "-"
            timestamp = meta.get("timestamp") if isinstance(meta, dict) else "-"
            status = meta.get("status") if isinstance(meta, dict) else "-"
            status_note = "✅" if remote in rclone_configured else "⚠️ missing in rclone config"
            print(f"  - {remote} ({remote_type}):")
            print(f"      Remote: {remote_path}")
            print(f"      Local:  {local_path}")
            print(f"      Action: {action} | Operation: {operation} | Timestamp: {timestamp} | Status: {status} {status_note}")


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
    
    # Detect the base remote type
    remote_type = _detect_remote_type(remote_name)
    base_type = _get_base_remote_type(remote_name)
    
    if remote_type in ["erda", "ucloud"]:
        # Build the create command
        command = [
            "rclone", "config", "create",
            remote_name, "sftp",
            "host", load_from_env("HOST"),
            "port", load_from_env("PORT"),
            "user", login,
        ]

        if remote_type == "ucloud":
            # prompt for SSH key (ucloud only)
            default_key = _detect_default_ssh_key()
            ssh_path = _prompt_with_default("Path to SSH private key for ucloud", default_key).strip()
            ssh_path = str(pathlib.Path(ssh_path).expanduser())

            if ssh_path and os.path.isfile(ssh_path):
                setup_ssh_agent_and_add_key(ssh_path)
                command += ["use_agent", "true"]
            else:
                return print(f"SSH key file not found: {ssh_path}")

        elif pass_key:
            command += ["pass", pass_key, "--obscure"]
        else:
            command += ["use_agent", "true"]

    elif "lumi" in remote_type:
        # Determine remote type and ACL
        if "public" in remote_name.lower():
            acl = "public-read"
        else:
            acl = "private"

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

    elif remote_type in ["dropbox", "onedrive", "drive", "local"]:
        if remote_type in ["dropbox", "onedrive", "drive"]:
            print(f"You will need to authorize rclone with {remote_type}")
        command = ["rclone", "config", "create", remote_name, base_type]

    else:
        # Fetch all backend types from rclone
        output = list_supported_remote_types()
        backend_types = [
            line.split()[0]
            for line in output.splitlines()
            if line and not line.startswith(" ") and ":" in line
        ]

        if base_type in backend_types:
            print(f"Running interactive config for backend '{base_type}'...")
            command = ["rclone", "config", "create", remote_name, base_type]
        else:
            print(f"Unsupported remote type: {base_type}")
            return

    try:
        subprocess.run(command, check=True, timeout=DEFAULT_TIMEOUT)
        print(f"Rclone remote '{remote_name}' (type: {remote_type}) created successfully.")
    except Exception as e:
        print(f"Failed to create rclone remote: {e}")


def _add_folder(remote_name: str = None, base_folder: str = None, local_backup_path: str = None):
    
    # Detect remote type from name
    remote_type = _detect_remote_type(remote_name)
    
    # Remove leading slash for cloud storage providers that don't use absolute paths
    if remote_type in ["dropbox", "onedrive", "drive"]:
        base_folder = base_folder.lstrip('/')
        command = ["rclone", "lsd", f"{remote_name}:{base_folder}"]
        mkdir_cmd = ["rclone", "mkdir", f"{remote_name}:{base_folder}"]

    elif "lumi" in remote_type:
        command = ["rclone", "lsd", f"{remote_name}:/{base_folder}"]
        mkdir_cmd = ["rclone", "mkdir", f"{remote_name}:/{base_folder}"]
    else:  # SFTP or Local
        command = ["rclone", "lsf", f"{remote_name}:/{base_folder}"]
        mkdir_cmd = ["rclone", "mkdir", f"{remote_name}:/{base_folder}"]

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
                if remote_type in ["dropbox", "onedrive", "drive"]:
                    base_folder = base_folder.lstrip('/')
            else:
                print("Cancelled.")
                return
        else:
            break
    try:
        subprocess.run(mkdir_cmd, check=True, timeout=DEFAULT_TIMEOUT)
        _save_rclone_json(remote_name, base_folder, local_backup_path)
    except Exception as e:
        print(f"Error creating folder: {e}")


def delete_remote(remote_name: str, json_path="./bin/rclone_remote.json", verbose: int = 0):
    
    
    # Step 1: Attempt to delete the actual remote directory if it exists
    remote_path, _ = _load_rclone_json(remote_name, json_path)
    if remote_path:

        confirm = input(f"Really delete ALL data for '{remote_name}'? [y/N]: ")
        if confirm.lower() != "y":
            return
        
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


def setup_rclone(remote_name: str = None,local_path:str = None):

    # Default to PROJECT_ROOT if not specified
    if local_path is None:
        local_backup_path = str(PROJECT_ROOT)

    if remote_name:
        remote_name, login_key, pass_key, base_folder = _remote_user_info(remote_name.lower(),local_backup_path)
        _add_remote(remote_name.lower(), login_key, pass_key)
        _add_folder(remote_name.lower(), base_folder, local_backup_path)
    else:
        install_rclone("./bin")


def list_supported_remote_types():
    #if install_rclone("./bin"):
    try:
        result = subprocess.run(["rclone", "help", "backends"], check=True, stdout=subprocess.PIPE, text=True, timeout=DEFAULT_TIMEOUT)
        print("\n📦 Supported Rclone Remote Types:")
        print("\nRecommended: ['ERDA' ,'Dropbox', 'Onedrive', 'Local']\n")
        print("\nSupported by Rclone:\n")
        print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error fetching remote types: {e}")
        return ""


def generate_diff_report(remote_name):
    def run_diff(remote):
        remote_path, local_path = _load_rclone_json(remote) #FIX ME 
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
        for remote in _load_all_rclone_json().keys():
            run_diff(remote)
    else:
        run_diff(remote_name)


def exclude_rclone_patterns(local_path):
    exclude_patterns  = []
    if pathlib.Path(local_path).resolve() == PROJECT_ROOT.resolve():   
        _, exclude_patterns = toml_ignore(
            folder = local_path,
            toml_path="pyproject.toml",
            ignore_filename=".rcloneignore",
            tool_name="rcloneignore",
            toml_key="patterns",
        )
    return exclude_patterns


def push_rclone(remote_name:str, new_path: str = None, operation:str = "sync", dry_run: bool = False, verbose: int = 0):

    os.chdir(PROJECT_ROOT)

    if not install_rclone("./bin"):
        return
    if remote_name.lower() == "all":
        all_remotes = _load_all_rclone_json().keys()
    else:
        all_remotes = [remote_name]
    
    flag = False
    for remote_name in all_remotes:
        _remote_path, _local_path = _load_rclone_json(remote_name.lower())
        if not _remote_path:
            print(f"Remote has not been configured or not found in registry. Run 'backup add --remote {remote_name}' first.")
            continue

        if new_path is None:
            new_path = _remote_path

        flag = rclone_commit(_local_path, flag, msg=f"Rclone Push from {_local_path} to {new_path}")
        exclude_patterns = exclude_rclone_patterns(_local_path)

        _rclone_transfer(remote_name = remote_name.lower(), action = "push", local_path = _local_path ,remote_path = new_path, operation = operation, exclude_patterns = exclude_patterns, dry_run = dry_run, verbose=verbose)


def pull_rclone(remote_name:str, new_path: str = None, operation:str = "sync", dry_run: bool = False, verbose: int = 0):
    
    if remote_name is None:
        print("Error: No remote specified for pulling backup.")
        return
    if remote_name.lower() == "all":
        print("Error: Pulling from 'all' remotes is not supported.")
        return

    os.chdir(PROJECT_ROOT)

    if not install_rclone("./bin"):
        return

    _remote_path, _local_path = _load_rclone_json(remote_name.lower())
    
    if not _remote_path:
        print(f"Remote has not been configured or not found in registry. Run 'backup add --remote {remote_name}' first.")
        return

    if new_path is None:
        new_path = _local_path

    if not os.path.exists(new_path):
        os.makedirs(new_path)

    _ = rclone_commit(new_path, False, msg=f"Rclone Pull from {_remote_path} to {new_path}")
    exclude_patterns = exclude_rclone_patterns(_local_path)

    _rclone_transfer(remote_name = remote_name.lower(), action = "pull", local_path = new_path, remote_path = _remote_path, operation = operation, exclude_patterns = exclude_patterns, dry_run = dry_run, verbose=verbose)


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
    all_remotes = _load_all_rclone_json()
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

    exclude_patterns = exclude_rclone_patterns(src_local)

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



@ensure_correct_kernel
def main():
    if not install_rclone("./bin"):
        print("Error: rclone installation/verification failed.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Backup manager CLI using rclone")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Global arguments
    parser.add_argument("--dry-run", action="store_true", help="Do not modify remote; show actions.")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity (-v, -vv, -vvv).")

    # List command
    subparsers.add_parser("list", help="List rclone remotes and mapped folders")
    
    # Types command
    subparsers.add_parser("types", help="List supported remote types")

    # Add command
    add = subparsers.add_parser("add", help="Add a remote and folder mapping")
    add.add_argument("--remote", required=True, help="Remote name")
    add.add_argument("--local-path", help="Specific local path to backup")

    # Push command (unified with operation modes)
    push = subparsers.add_parser("push", help="Push/backup to remote")
    push.add_argument("--remote", required=True, help="Remote name")
    push.add_argument("--mode", choices=["sync", "copy", "move"], default="sync",
                     help="sync: mirror (default), copy: no deletes, move: delete source after")
    push.add_argument("--remote-path", help="remote path to backup")

    # Pull command (unified with operation modes)
    pull = subparsers.add_parser("pull", help="Pull/restore from remote")
    pull.add_argument("--remote", required=True, help="Remote name")
    pull.add_argument("--mode", choices=["sync", "copy", "move"], default="sync",
                     help="sync: mirror (default), copy: no deletes, move: delete source after")
    pull.add_argument("--local-path", help="Override destination path")

    # Delete command
    delete = subparsers.add_parser("delete", help="Delete a remote and its mapping")
    delete.add_argument("--remote", required=True, help="Remote name")

    # Diff command
    diff = subparsers.add_parser("diff", help="Generate a diff report for a remote")
    diff.add_argument("--remote", required=True, help="Remote name")

    args = parser.parse_args()

    # Handle commands
    if hasattr(args, "remote") and args.remote:
        remote = args.remote.strip().lower()
        
        # Handle LUMI credentials
        if "lumi" in remote:
            remote = _check_lumi_o_credentials(remote_name=remote, command=args.command)
            if remote is None:
                return

        # Set host/port for SFTP remotes
        if args.command in {"add", "push", "pull"}:
            remote_type = _detect_remote_type(remote)
            if remote_type in ["erda", "ucloud"]:
                set_host_port(remote)

        # Dispatch
        if args.command == "add":
            setup_rclone(remote, local_backup_path=args.local_path)
            
        elif args.command == "push":
            mode = getattr(args, "mode", "sync")
            push_rclone(
                remote_name=remote,
                new_path=args.remote_path,
                operation=mode,
                dry_run=args.dry_run,
                verbose=args.verbose
            )
            
        elif args.command == "pull":
            mode = getattr(args, "mode", "sync")
            pull_rclone(
                remote_name=remote,
                new_path=args.local_path,
                operation=mode,
                dry_run=args.dry_run,
                verbose=args.verbose
            )
            
        elif args.command == "delete":
            delete_remote(remote_name=remote, verbose=args.verbose)
            
        elif args.command == "diff":
            generate_diff_report(remote_name=remote)

    else:
        # Commands without a remote
        if args.command == "list":
            list_remotes()
        elif args.command == "types":
            list_supported_remote_types()
        else:
            parser.print_help()
            sys.exit(2)

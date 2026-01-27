"""
Remote management - Detection, configuration, and listing.
"""

import os
import pathlib
import subprocess
import getpass
import shutil
import sys
from ..vcs import install_rclone 
from ..common import PROJECT_ROOT, load_from_env, save_to_env, check_path_format
from .registry import save_registry, load_all_registry, delete_from_registry, load_registry
from .rclone import _rc_verbose_args, rclone_diff_report, _rclone_transfer, DEFAULT_TIMEOUT


def _detect_remote_type(remote_name: str) -> str:
    """
    Detect the remote type based on the remote name prefix.
    
    Args:
        remote_name: The full remote name (e.g., 'dropbox-dataset1', 'onedrive-work')
    
    Returns:
        The remote type (e.g., 'dropbox', 'onedrive', 'erda')
    """
    remote_lower = remote_name.lower()
    
    known_types = [
        'dropbox', 'onedrive', 'googledrive', 'gdrive',
        'erda', 'ucloud', 
        'lumi', 'local', 's3', 'sftp'
    ]
    
    for remote_type in known_types:
        if remote_lower.startswith(remote_type):
            if remote_type in ['googledrive', 'gdrive']:
                return 'drive'
            return remote_type
    
    return 'sftp'


def _get_base_remote_type(remote_name: str) -> str:
    """Get the base remote type for rclone config."""
    remote_type = _detect_remote_type(remote_name)
    
    type_mapping = {
        'erda': 'sftp',
        'ucloud': 'sftp',
        'googledrive': 'drive',
        'gdrive': 'drive',
    }
    
    return type_mapping.get(remote_type, remote_type)


def _prompt_with_default(prompt_text: str, default_val: str) -> str:
    """Prompt user with a default value."""
    val = input(f"{prompt_text} [{default_val}]: ").strip()
    return val if val else default_val


def _validate_port(port_str: str, default_val: str) -> str:
    """Validate port number."""
    try:
        p = int(port_str)
        if 1 <= p <= 65535:
            return str(p)
    except Exception:
        pass
    print(f"Invalid port '{port_str}'. Using default '{default_val}'.")
    return default_val


def _detect_default_ssh_key() -> str:
    """Detect default SSH key location."""
    existing = (load_from_env("SSH_PATH", "") or "").strip()
    if existing:
        return existing

    home = pathlib.Path.home() / ".ssh"
    for name in ("id_ed25519", "id_rsa", "id_ecdsa"):
        p = home / name
        if p.exists():
            return str(p)

    return str(home / "id_ed25519")


def _ensure_repo_suffix(folder: str, repo: str) -> str:
    """Ensure folder path ends with repo name and is not inside PROJECT_ROOT."""
    folder = folder.strip().replace("\\", "/").rstrip("/")
    
    if not folder.endswith(repo):
        folder = os.path.join(folder, repo).replace("\\", "/")
    
    project_root_normalized = os.path.normpath(str(PROJECT_ROOT))
    folder_normalized = os.path.normpath(folder)
    
    if folder_normalized.startswith(project_root_normalized):
        folder = project_root_normalized + "_backup"

    return folder


def set_host_port(remote_name: str):
    """Set host and port for SFTP-based remotes, and create/update ucloud rclone config."""
    remote_type = _detect_remote_type(remote_name)
    
    if remote_type not in ["erda", "ucloud"]:
        return  # Only needed for SFTP remotes

    # Default host and port
    if remote_type == "erda":
        host = "io.erda.dk"
        port = "22"
        save_to_env(host, "HOST")
        save_to_env(port, "PORT")
        return

    # --- ucloud specific ---
    if remote_type == "ucloud":
        host = "ssh.cloud.sdu.dk"
        existing_port = load_from_env("PORT")
        port_input = _prompt_with_default("Port for ucloud", existing_port)
        port_final = _validate_port(port_input, existing_port)
        save_to_env(host, "HOST")
        save_to_env(port_final, "PORT")

        # SSH key
        default_key = _detect_default_ssh_key()
        ssh_key_path = _prompt_with_default("Path to SSH private key for ucloud", default_key).strip()
        ssh_key_path = str(pathlib.Path(ssh_key_path).expanduser())

        if not os.path.isfile(ssh_key_path):
            print(f"⚠️ SSH key file not found: {ssh_key_path}")
            return

        # Ensure ./bin exists
        bin_folder = pathlib.Path("./bin").resolve()
        bin_folder.mkdir(parents=True, exist_ok=True)

        # Path for rclone config
        rclone_conf = bin_folder / "rclone_ucloud.conf"

        # Build rclone config content
        config_content = f"""[ucloud]
type = sftp
host = {host}
port = {port_final}
user = ucloud
key_file = {ssh_key_path}
"""
        # Write or update the file
        with open(rclone_conf, "w", encoding="utf-8") as f:
            f.write(config_content)

        print(f"✅ ucloud rclone config saved/updated at: {rclone_conf}")
        print(f"Host: {host}, Port: {port_final}, SSH key: {ssh_key_path}")


def set_host_port_old(remote_name: str):
    """Set host and port for SFTP-based remotes."""
    remote_type = _detect_remote_type(remote_name)
    
    if remote_type in ["erda", "ucloud"]:
        if remote_type == "erda":
            save_to_env("io.erda.dk", "HOST")
            save_to_env("22", "PORT")
        elif remote_type == "ucloud":
            save_to_env("ssh.cloud.sdu.dk", "HOST")
            existing_port = load_from_env("PORT")
            port_input = _prompt_with_default("Port for ucloud", existing_port)
            port_final = _validate_port(port_input, existing_port)
            save_to_env(port_final, "PORT")


def setup_ssh_agent_and_add_key(ssh_path: str):
    """Start/ensure an SSH agent and add the provided key."""
    
    def _parse_ssh_agent_exports(output: str) -> dict:
        env = {}
        for line in output.splitlines():
            if "SSH_AUTH_SOCK=" in line:
                env["SSH_AUTH_SOCK"] = line.split("SSH_AUTH_SOCK=", 1)[1].split(";", 1)[0].strip()
            elif "SSH_AGENT_PID=" in line:
                env["SSH_AGENT_PID"] = line.split("SSH_AGENT_PID=", 1)[1].split(";", 1)[0].strip()
        return env

    def _ensure_ssh_agent_running():
        if sys.platform.startswith("win"):
            sc = shutil.which("sc")
            if sc is None:
                raise RuntimeError("Windows 'sc' utility not found; cannot control ssh-agent service.")
            try:
                subprocess.run([sc, "config", "ssh-agent", "start=", "auto"],
                            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run([sc, "start", "ssh-agent"],
                            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                raise RuntimeError(f"Failed to start Windows ssh-agent service: {e}") from e
        else:
            if not os.environ.get("SSH_AUTH_SOCK"):
                ssh_agent = shutil.which("ssh-agent")
                if not ssh_agent:
                    raise RuntimeError("ssh-agent not found in PATH.")
                proc = subprocess.run([ssh_agent, "-s"], check=True, capture_output=True, 
                                    text=True, timeout=DEFAULT_TIMEOUT)
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

    try:
        subprocess.run([ssh_add, str(key)], check=True, timeout=DEFAULT_TIMEOUT)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ssh-add failed: {e}") from e


def _handle_lumi_o_remote(remote_name: str) -> tuple[str, str, str, str]:
    """Handle LUMI-O remote configuration and credentials."""
    remote_type = "public" if "public" in remote_name.lower() else "private"

    repo_name = load_from_env("REPO_NAME", ".cookiecutter")
    project_id = load_from_env("LUMI_PROJECT_ID")
    access_key = load_from_env("LUMI_ACCESS_KEY")
    secret_key = load_from_env("LUMI_SECRET_KEY")
    base_folder = load_from_env(f"LUMI_BASE_{remote_type.upper()}")
    
    if project_id and access_key and secret_key and base_folder:
        base_folder = _ensure_repo_suffix(base_folder, repo_name)
        remote_name = _lumi_o_remote_name(remote_name)
        return remote_name, base_folder, access_key, secret_key
    
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
    
    save_to_env(project_id, "LUMI_PROJECT_ID")
    save_to_env(access_key, "LUMI_ACCESS_KEY")
    save_to_env(secret_key, "LUMI_SECRET_KEY")
    save_to_env(base_folder, f"LUMI_BASE_{remote_type.upper()}")
    
    remote_name = _lumi_o_remote_name(remote_name)
    return remote_name, base_folder, access_key, secret_key


def _lumi_o_remote_name(remote_name: str) -> str:
    """Generate LUMI-O remote name."""
    project_id = load_from_env("LUMI_PROJECT_ID")
    remote_type = "public" if "public" in remote_name.lower() else "private"
    return f"lumi-{project_id}-{remote_type}"


def check_lumi_o_credentials(remote_name: str, command: str = "add") -> str | None:
    """Check and handle LUMI-O credentials."""
    project_id = load_from_env("LUMI_PROJECT_ID")

    if not project_id and command == "add":
        remote_name, _, _, _ = _handle_lumi_o_remote(remote_name)
        return remote_name
    elif not project_id and command != "add":
        print(f"{remote_name} remote not found. Please set up the remote first by "
              f"running 'backup add --remote {remote_name}'.")
        return None
    elif project_id:
        return _lumi_o_remote_name(remote_name)
    return None


def _remote_user_info(remote_name: str, local_backup_path: str) -> tuple[str, str | None, str | None, str]:
    """Get remote user information based on type."""
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


def _ucloud_remote_info(remote_name: str, repo_name: str) -> tuple[str, str, None, str]:
    """Get UCloud remote info."""
    default_base = f"work/rclone-backup/{repo_name}"
    base_folder = input(
        f"Enter base folder for {remote_name} [{default_base}]: "
    ).strip() or default_base
    base_folder = _ensure_repo_suffix(base_folder, repo_name)
    return remote_name, "ucloud", None, base_folder


def _local_remote_info(remote_name: str, repo_name: str) -> tuple[str, None, None, str | None]:
    """Get local remote info."""
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


def _oauth_remote_info(remote_name: str, repo_name: str) -> tuple[str, None, None, str]:
    """Get OAuth remote info (Dropbox, OneDrive, etc.)."""
    default_base = f"rclone-backup/{repo_name}"
    base_folder = input(
        f"Enter base folder for {remote_name} [{default_base}]: "
    ).strip() or default_base
    base_folder = _ensure_repo_suffix(base_folder, repo_name)
    return remote_name, None, None, base_folder


def _lumi_remote_info(remote_name: str, repo_name: str) -> tuple[str, None, None, str]:
    """Get LUMI remote info."""
    remote_type_suffix = "public" if "public" in remote_name.lower() else "private"
    base_folder = load_from_env(f"LUMI_BASE_{remote_type_suffix.upper()}")

    if not base_folder:
        return _handle_lumi_o_remote(remote_name)

    base_folder = _ensure_repo_suffix(base_folder, repo_name)
    return remote_name, None, None, base_folder


def _generic_remote_info(remote_name: str, repo_name: str) -> tuple[str, None, None, str]:
    """Get generic remote info."""
    default_base = f"rclone-backup/{repo_name}"
    base_folder = input(
        f"Enter base folder for {remote_name} [{default_base}]: "
    ).strip() or default_base
    base_folder = _ensure_repo_suffix(base_folder, repo_name)
    return remote_name, None, None, base_folder


def check_rclone_remote(remote_name: str) -> bool:
    """Check if rclone remote is configured."""
    try:
        result = subprocess.run(
            ["rclone", "listremotes"], check=True, stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, timeout=DEFAULT_TIMEOUT
        )
        remotes = result.stdout.decode("utf-8").splitlines()
        return f"{remote_name}:" in remotes
    except subprocess.CalledProcessError as e:
        print(f"Failed to check rclone remotes: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


def _add_erda_remote(remote_name: str, login: str, pass_key: str | None):
    command = [
        "rclone", "config", "create",
        remote_name, "sftp",
        "host", load_from_env("HOST"),
        "port", load_from_env("PORT"),
        "user", login,
    ]

    if pass_key:
        command += ["pass", pass_key, "--obscure"]
    else:
        command += ["use_agent", "true"]

    subprocess.run(command, check=True, timeout=DEFAULT_TIMEOUT)
    print(f"Rclone remote '{remote_name}' (erda) created.")



def _add_lumi_remote(remote_name: str, login: str, pass_key: str):
    acl = "public-read" if "public" in remote_name.lower() else "private"

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

    subprocess.run(command, check=True, timeout=DEFAULT_TIMEOUT)
    print(f"Rclone remote '{remote_name}' (lumi) created.")



def _add_simple_remote(remote_name: str, base_type: str):
    print(f"You will need to authorize rclone with {base_type}")
    command = ["rclone", "config", "create", remote_name, base_type]
    subprocess.run(command, check=True, timeout=DEFAULT_TIMEOUT)
    print(f"Rclone remote '{remote_name}' created.")



def _add_interactive_remote(remote_name: str, base_type: str):
    output = list_supported_remote_types()
    backend_types = [
        line.split()[0]
        for line in output.splitlines()
        if line and not line.startswith(" ") and ":" in line
    ]

    if base_type not in backend_types:
        raise RuntimeError(f"Unsupported remote type: {base_type}")

    print(f"Running interactive config for backend '{base_type}'...")
    command = ["rclone", "config", "create", remote_name, base_type]
    subprocess.run(command, check=True, timeout=DEFAULT_TIMEOUT)
    print(f"Rclone remote '{remote_name}' created.")



def _add_remote(remote_name: str, login: str = None, pass_key: str = None):
    """Add a new rclone remote or prepare runtime config."""
    remote_type = _detect_remote_type(remote_name)
    base_type = _get_base_remote_type(remote_name)

    try:
        if remote_type == "erda":
            _add_erda_remote(remote_name, login, pass_key)

        #elif remote_type == "ucloud":
        #    _add_ucloud_remote()

        elif "lumi" in remote_type:
            _add_lumi_remote(remote_name, login, pass_key)

        elif remote_type in {"dropbox", "onedrive", "drive", "local"}:
            _add_simple_remote(remote_name, base_type)

        else:
            _add_interactive_remote(remote_name, base_type)

    except Exception as e:
        print(f"Failed to add remote '{remote_name}': {e}")



def _add_folder(remote_name: str, base_folder: str, local_backup_path: str):
    """Add folder mapping for remote with overwrite/merge safeguard, using ucloud config if applicable."""
    remote_type = _detect_remote_type(remote_name)

    # Build list/mkdir commands
    if remote_type in ["dropbox", "onedrive", "drive"]:
        base_folder = base_folder.lstrip('/')
        list_cmd = ["rclone", "lsd", f"{remote_name}:{base_folder}"]
        mkdir_cmd = ["rclone", "mkdir", f"{remote_name}:{base_folder}"]
    elif "lumi" in remote_type:
        list_cmd = ["rclone", "lsd", f"{remote_name}:/{base_folder}"]
        mkdir_cmd = ["rclone", "mkdir", f"{remote_name}:/{base_folder}"]
    else:  # SFTP (ucloud, erda) or local
        list_cmd = ["rclone", "lsf", f"{remote_name}:/{base_folder}"]
        mkdir_cmd = ["rclone", "mkdir", f"{remote_name}:/{base_folder}"]

        # Use ucloud config if remote is ucloud
        if remote_name.lower() == "ucloud":
            rclone_conf = pathlib.Path("./bin/rclone_ucloud.conf").resolve()
            if rclone_conf.exists():
                list_cmd += ["--config", str(rclone_conf)]
                mkdir_cmd += ["--config", str(rclone_conf)]
            else:
                print("⚠️ ucloud rclone config not found in ./bin. Please run set_host_port first.")
                return

    # Check if remote folder exists
    result = subprocess.run(list_cmd, capture_output=True, text=True, timeout=DEFAULT_TIMEOUT)
    merge_only = False
    if result.returncode == 0 and result.stdout.strip():
        valid_choices = {"o": "overwrite", "s": "merge/sync", "n": "rename", "c": "cancel"}
        while True:
            choice = input(
                f"'{base_folder}' exists on '{remote_name}'. Overwrite (o), Merge/Sync (s), Rename (n), Cancel (c)? [o/s/n/c]: "
            ).strip().lower()
            if choice not in valid_choices:
                print(f"Invalid choice: {choice}. Please choose one of {', '.join(valid_choices.keys())}.")
                continue

            if choice == "o":
                print("⚠️ Warning: You chose to overwrite the remote folder.")
                subprocess.run(["rclone", "purge", f"{remote_name}:{base_folder}"] + (["--config", str(rclone_conf)] if remote_name.lower() == "ucloud" else []),
                               check=True, timeout=DEFAULT_TIMEOUT)
                break

            elif choice == "s":
                print("ℹ️ Will merge/sync differences only.")
                merge_only = True
                break

            elif choice == "n":
                base_folder = input("New folder name: ").strip()
                if remote_type in ["dropbox", "onedrive", "drive"]:
                    base_folder = base_folder.lstrip('/')
                result = subprocess.run(list_cmd, capture_output=True, text=True, timeout=DEFAULT_TIMEOUT)
                continue

            elif choice == "c":
                print("Cancelled.")
                return

    # Ensure remote folder exists
    try:
        subprocess.run(mkdir_cmd, check=True, timeout=DEFAULT_TIMEOUT)
    except Exception as e:
        print(f"Error creating folder: {e}")
        return

    # Save mapping
    save_registry(remote_name, base_folder, local_backup_path, remote_type)

    # Run merge if requested
    if merge_only:
        remote_full_path = f"{remote_name}:{base_folder}"
        print("\nRunning diff report before syncing...")
        rclone_diff_report(local_backup_path, remote_full_path)
        print("\nSyncing differences to merge local and remote...")
        _rclone_transfer(remote_name=remote_name,
                         local_path=local_backup_path,
                         remote_path=remote_full_path,
                         action="push",
                         operation="copy")  # copy to avoid deleting



def _add_remote_old(remote_name: str, login: str = None, pass_key: str = None):
    """Add a new rclone remote."""
    remote_type = _detect_remote_type(remote_name)
    base_type = _get_base_remote_type(remote_name)
    
    if remote_type == "erda":
        command = [
            "rclone", "config", "create",
            remote_name, "sftp",
            "host", load_from_env("HOST"),
            "port", load_from_env("PORT"),
            "user", login,
        ]

        if pass_key:
            command += ["pass", pass_key, "--obscure"]
        else:
            command += ["use_agent", "true"]

    if remote_type == "ucloud":
        
        default_key = _detect_default_ssh_key()
        ssh_path = _prompt_with_default("Path to SSH private key for ucloud", default_key).strip()
        ssh_path = str(pathlib.Path(ssh_path).expanduser())

        if ssh_path and os.path.isfile(ssh_path):
            
            setup_ssh_agent_and_add_key(ssh_path)

            command += ["use_agent", "true"]
        else:
            return print(f"SSH key file not found: {ssh_path}")
            
    elif "lumi" in remote_type:
        acl = "public-read" if "public" in remote_name.lower() else "private"
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



def _add_folder_old(remote_name: str, base_folder: str, local_backup_path: str):
    """Add folder mapping for remote with overwrite/merge safeguard."""
    remote_type = _detect_remote_type(remote_name)
    
    # Build remote command paths
    if remote_type in ["dropbox", "onedrive", "drive"]:
        base_folder = base_folder.lstrip('/')
        list_cmd = ["rclone", "lsd", f"{remote_name}:{base_folder}"]
        mkdir_cmd = ["rclone", "mkdir", f"{remote_name}:{base_folder}"]
    elif "lumi" in remote_type:
        list_cmd = ["rclone", "lsd", f"{remote_name}:/{base_folder}"]
        mkdir_cmd = ["rclone", "mkdir", f"{remote_name}:/{base_folder}"]
    else:  # SFTP or local
        list_cmd = ["rclone", "lsf", f"{remote_name}:/{base_folder}"]
        mkdir_cmd = ["rclone", "mkdir", f"{remote_name}:/{base_folder}"]

    # Check if remote folder exists
    result = subprocess.run(list_cmd, capture_output=True, text=True, timeout=DEFAULT_TIMEOUT)
    if result.returncode == 0 and result.stdout.strip():
        # Folder exists, ask user what to do
        valid_choices = {"o": "overwrite", "s": "merge/sync", "n": "rename", "c": "cancel"}
        while True:
            choice = input(
                f"'{base_folder}' exists on '{remote_name}'. Overwrite (o), Merge/Sync (s), Rename (n), Cancel (c)? [o/s/n/c]: "
            ).strip().lower()

            if choice not in valid_choices:
                print(f"Invalid choice: {choice}. Please choose one of {', '.join(valid_choices.keys())}.")
                continue

            if choice == "o":
                print("⚠️ Warning: You chose to overwrite the remote folder.")
                # purge remote folder before creating
                try:
                    subprocess.run(["rclone", "purge", f"{remote_name}:{base_folder}"], check=True, timeout=DEFAULT_TIMEOUT)
                    print(f"Remote folder '{base_folder}' purged.")
                except subprocess.CalledProcessError as e:
                    print(f"Failed to purge remote folder: {e}")
                break

            elif choice == "s":
                print("ℹ️ Will merge/sync differences only.")
                merge_only = True
                break

            elif choice == "n":
                base_folder = input("New folder name: ").strip()
                if remote_type in ["dropbox", "onedrive", "drive"]:
                    base_folder = base_folder.lstrip('/')
                # re-check if new folder exists
                result = subprocess.run(list_cmd, capture_output=True, text=True, timeout=DEFAULT_TIMEOUT)
                continue

            elif choice == "c":
                print("Cancelled.")
                return
    else:
        merge_only = False  # folder does not exist, normal creation

    # Ensure remote folder exists
    try:
        subprocess.run(mkdir_cmd, check=True, timeout=DEFAULT_TIMEOUT)
    except Exception as e:
        print(f"Error creating folder: {e}")
        return

    # Save mapping
    save_registry(remote_name, base_folder, local_backup_path, remote_type)

    # If merge_only is True, run a diff report and sync differences
    if 'merge_only' in locals() and merge_only:
        remote_path = f"{remote_name}:{base_folder}"
        print("\nRunning diff report before syncing...")
        rclone_diff_report(local_backup_path, remote_path)
        print("\nSyncing differences to merge local and remote...")
        _rclone_transfer(remote_name=remote_name, action="push",
                         local_path=local_backup_path,
                         remote_path=remote_path,
                         operation="copy")  # use copy to avoid deletion



def list_remotes():
    """List all configured remotes and their status."""
    print("\n🔌 Rclone Remotes:")
    try:
        result = subprocess.run(["rclone", "listremotes"], check=True, 
                              stdout=subprocess.PIPE, timeout=DEFAULT_TIMEOUT)
        rclone_configured = set(r.rstrip(":") for r in result.stdout.decode().splitlines())
    except Exception as e:
        print(f"Failed to list remotes: {e}")
        rclone_configured = set()

    print("\n📁 Mapped Backup Folders:")
    all_remotes = load_all_registry()
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


def setup_rclone(remote_name: str = None, local_backup_path: str = None):
    """Setup rclone remote and folder mapping."""
    if local_backup_path is None:
        local_backup_path = str(PROJECT_ROOT)

    if remote_name:
        remote_name, login_key, pass_key, base_folder = _remote_user_info(
            remote_name.lower(), local_backup_path
        )
        _add_remote(remote_name.lower(), login_key, pass_key)
        _add_folder(remote_name.lower(), base_folder, local_backup_path)
    else:
        install_rclone("./bin")


def delete_remote(remote_name: str, verbose: int = 0):
    """Delete remote and all its data."""
    remote_path, _ = load_registry(remote_name)
    if remote_path:
        confirm = input(f"Really delete ALL data for '{remote_name}'? [y/N]: ")
        if confirm.lower() != "y":
            return
        
        try:
            print(f"Attempting to purge remote folder at: {remote_path}")
            subprocess.run(
                ["rclone", "purge", remote_path] + _rc_verbose_args(verbose),
                check=True,
                timeout=DEFAULT_TIMEOUT
            )
            print(f"Successfully purged remote folder: {remote_path}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Warning: Could not purge remote folder '{remote_path}': {e}")
        except Exception as e:
            print(f"Unexpected error during purge: {e}")
    else:
        return

    try:
        subprocess.run(
            ["rclone", "config", "delete", remote_name] + _rc_verbose_args(verbose),
            check=True,
            timeout=DEFAULT_TIMEOUT
        )
        print(f"Rclone remote '{remote_name}' deleted from rclone configuration.")
    except subprocess.CalledProcessError as e:
        print(f"Error deleting remote from rclone: {e}")

    delete_from_registry(remote_name)


def list_supported_remote_types() -> str:
    """List all supported rclone backend types."""
    try:
        result = subprocess.run(
            ["rclone", "help", "backends"],
            check=True,
            stdout=subprocess.PIPE,
            text=True,
            timeout=DEFAULT_TIMEOUT
        )
        print("\n📦 Supported Rclone Remote Types:")
        print("\nRecommended: ['ERDA' ,'Dropbox', 'Onedrive', 'Local']\n")
        print("\nSupported by Rclone:\n")
        print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error fetching remote types: {e}")
        return ""
    


def _add_remote_old_old(remote_name: str, login: str = None, pass_key: str = None):
    """Add a new rclone remote."""
    remote_type = _detect_remote_type(remote_name)
    base_type = _get_base_remote_type(remote_name)
    
    if remote_type in ["erda", "ucloud"]:
        command = [
            "rclone", "config", "create",
            remote_name, "sftp",
            "host", load_from_env("HOST"),
            "port", load_from_env("PORT"),
            "user", login,
        ]

        if remote_type == "ucloud":
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
        acl = "public-read" if "public" in remote_name.lower() else "private"
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


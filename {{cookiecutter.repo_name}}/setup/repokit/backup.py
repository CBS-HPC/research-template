import argparse
import json
import os
import subprocess
import tempfile
from datetime import datetime
import getpass


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
        default_base = f"RClone_backup/{repo_name}"
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
            remote_name, base_folder = _handle_lumi_o_remote(remote_name)
        
        return remote_name, None, None, base_folder
 
    elif remote_name.lower() != "none":
        default_base = f"RClone_backup/{repo_name}"
        base_folder = (
            input(f"Enter base folder for {remote_name} [{default_base}]: ").strip() or default_base
        )
        base_folder = _ensure_repo_suffix(base_folder, repo_name)
        return remote_name, None, None, base_folder

    else:
        return remote_name, None, None, None


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
        # Update remote_name to actual format: lumi-{project_id}-{private|public}
        remote_name = f"lumi-{project_id}-{remote_type}"
        return remote_name, base_folder
    
    # Prompt for credentials
    default_base = f"RClone_backup/{repo_name}"
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
    
    # Update remote_name to actual format
    remote_name = f"lumi-{project_id}-{remote_type}"
    
    return remote_name, base_folder 


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
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
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
        with open(json_path, "r+") as f:
            data = json.load(f)
            if remote_name in data:
                if isinstance(data[remote_name], dict):
                    data[remote_name]["last_sync"] = datetime.now().isoformat()
                    data[remote_name]["status"] = "ok" if success else "potentially corrupt"
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Failed to update sync status: {e}")


def _rclone_sync(remote_name: str = None, folder_to_backup: str = None):
   
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

    
    if os.path.exists(".git") and not os.path.exists(".datalad") and not os.path.exists(".dvc"):
        with change_dir("./data"):
            _ = git_commit(msg="Running 'set-dataset'", path=os.getcwd())
            git_log_to_file(os.path.join(".gitlog"))
    
    git_push(load_from_env("CODE_REPO", ".cookiecutter") != "None", "Rclone Backup")

    command_sync = ["rclone", "sync", folder_to_backup, rclone_repo, "--verbose"] + exclude_args
    remote_name = rclone_repo.split(":")[0]
    try:
        subprocess.run(command_sync, check=True)
        print(f"Folder '{folder_to_backup}' successfully synchronized with '{rclone_repo}'.")
        _update_last_sync(remote_name, success=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to sync folder to remote: {e}")
        _update_last_sync(remote_name, success=False)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        _update_last_sync(remote_name, success=False)


def list_remotes():
    print("\n🔌 Rclone Remotes:")
    try:
        result = subprocess.run(["rclone", "listremotes"], check=True, stdout=subprocess.PIPE)
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
            ["rclone", "listremotes"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        remotes = result.stdout.decode("utf-8").splitlines()
        return f"{remote_name}:" in remotes
    except subprocess.CalledProcessError as e:
        print(f"Failed to check rclone remotes: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


def _add_remote(remote_name: str = None, email: str = None, password: str = None):
    remote_name = remote_name.lower()

    if remote_name in ["deic-storage", "erda"]:
        # SFTP configuration for DEIC Storage and ERDA
        if remote_name == "deic-storage":
            host = "sftp.storage.deic.dk"
            port = "2222"
        else:  # erda
            host = "io.erda.dk"
            port = "22"
        
        command = [
            "rclone",
            "config",
            "create",
            remote_name,
            "sftp",
            "host",
            host,
            "port",
            port,
            "user",
            email,
            "pass",
            password,
        ]

    elif "lumi" in remote_name.lower():

        access_key = load_from_env("LUMI_ACCESS_KEY")
        secret_key = load_from_env("LUMI_SECRET_KEY")

        # Determine remote type and ACL
        if "public" in remote_name.lower():
            acl = "public-read"
        else:
            acl = "private"
        
        # Create remote command
        command = [
            "rclone",
            "config",
            "create",
            remote_name,
            "s3",
            "provider",
            "Other",
            "endpoint",
            "https://lumidata.eu",
            "access_key_id",
            access_key,
            "secret_access_key",
            secret_key,
            "region",
            "other-v2-signature",
            "acl",
            acl,
        ]
                
    elif remote_name in ["dropbox", "onedrive","local"]:
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
        subprocess.run(command, check=True)
        print(f"Rclone remote '{remote_name}' created successfully.")
    except Exception as e:
        print(f"Failed to create rclone remote: {e}")


def _add_folder(remote_name:str = None, base_folder:str = None):
    
    if "lumi" in remote_name.lower():
        rclone_cmd = "lsd"
    else:
        rclone_cmd = "lsf"

    while True:
        #check_command = ["rclone", rclone_cmd, f"{remote_name}:/{base_folder}"]
        check_command = ["rclone", rclone_cmd, f"{remote_name}:{base_folder}"]
        result = subprocess.run(check_command, capture_output=True, text=True)
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
            else:
                print("Cancelled.")
                return None
        else:
            break
    try:
        subprocess.run(["rclone", "mkdir", f"{remote_name}:{base_folder}"], check=True)
        _save_rclone_json(remote_name, base_folder)
    except Exception as e:
        print(f"Error creating folder: {e}")


def delete_remote(remote_name: str, json_path="./bin/rclone_remote.json"):

    # Step 1: Attempt to delete the actual remote directory if it exists
    remote_path = _load_rclone_json(remote_name, json_path)
    if remote_path:
        try:
            print(f"Attempting to purge remote folder at: {remote_path}")
            subprocess.run(["rclone", "purge", remote_path], check=True)
            print(f"Successfully purged remote folder: {remote_path}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Warning: Could not purge remote folder '{remote_path}': {e}")
        except Exception as e:
            print(f"Unexpected error during purge: {e}")
    else:
        return
    # Step 2: Delete the remote from rclone config
    try:
        subprocess.run(["rclone", "config", "delete", remote_name], check=True)
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


def setup_backup(remote_name: str = None):
    if remote_name:
        remote_name, email, password, base_folder = _remote_user_info(remote_name.lower())
        _add_remote(remote_name.lower(), email, password)
        _add_folder(remote_name.lower(), base_folder)
    else:
        install_rclone("./bin")


def list_supported_remote_types():
    #if install_rclone("./bin"):
    try:
        result = subprocess.run(
            ["rclone", "help", "backends"], check=True, stdout=subprocess.PIPE, text=True
        )
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
                subprocess.run(command, check=True)
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


def push_backup(remote_name):

    os.chdir(PROJECT_ROOT)

    if not install_rclone("./bin"):
        return
    if remote_name.lower() == "all":
        all_remotes = _load_all_rclone_json()
        for remote_name in all_remotes:
            _rclone_sync(remote_name.lower())
    else:
        rclone_repo = _load_rclone_json(remote_name.lower())
        if not rclone_repo:
            remote_name, email, password, base_folder = _remote_user_info(remote_name.lower())
            _add_remote(remote_name.lower(), email, password)
            _add_folder(remote_name.lower(), base_folder)

        _rclone_sync(remote_name.lower())


def pull_backup(remote_name: str = None, destination_folder: str = None):
    import subprocess

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

    command_pull = ["rclone", "sync", rclone_repo, destination_folder, "--verbose"] + exclude_args

    try:
        subprocess.run(command_pull, check=True)
        print(f"Backup pulled from '{rclone_repo}' to '{destination_folder}' successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to pull backup from remote: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while pulling backup: {e}")


@ensure_correct_kernel
def main():
    if install_rclone("./bin"):
        parser = argparse.ArgumentParser(description="Backup manager CLI using rclone")
        subparsers = parser.add_subparsers(dest="command")

        subparsers.add_parser("list", help="List rclone remotes and mapped folders")

        add = subparsers.add_parser("add", help="Add a remote and folder mapping")
        add.add_argument("--remote", required=True)

        push = subparsers.add_parser("push", help="Push local folder to a remote")
        push.add_argument("--remote", required=True)

        delete = subparsers.add_parser("delete", help="Delete a remote and its mapping")
        delete.add_argument("--remote", required=True)

        diff = subparsers.add_parser("diff", help="Generate a diff report for a remote")
        diff.add_argument("--remote", required=True)

        types = subparsers.add_parser("types", help="List supported rclone remote types")

        pull = subparsers.add_parser("pull", help="Pull backup from a remote")
        pull.add_argument("--remote", required=True)
        pull.add_argument("--dest", default=None)

        args = parser.parse_args()

        if hasattr(args, 'remote') and args.remote:
            remote = args.remote.strip().lower()
            
            if remote == "deic storage":
                args.remote = "deic-storage"
            elif "lumi" in remote:
                args.remote, _ = _handle_lumi_o_remote(args.remote)
        
        if args.command == "list":
            list_remotes()
        elif args.command == "add":
            setup_backup(args.remote)
        elif args.command == "push":
            push_backup(args.remote)
        elif args.command == "delete":
            delete_remote(args.remote)
        elif args.command == "diff":
            generate_diff_report(args.remote)
        elif args.command == "types":
            list_supported_remote_types()
        elif args.command == "pull":
            pull_backup(args.remote, args.dest)
        else:
            parser.print_help()


if __name__ == "__main__":
    os.chdir(PROJECT_ROOT)
    main()

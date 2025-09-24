import os
import subprocess
import argparse
import json
from datetime import datetime
import tempfile

from .general_tools import *
from .versioning_tools import *
from .toml_tools import *


def load_rclone_json(remote_name: str, json_path="./bin/rclone_remote.json") -> str:
    
    if remote_name.strip().lower() == "deic storage":
        remote_name = "deic-storage"
    
    if not os.path.exists(json_path):
        print(f"No rclone registry found at {json_path}")
        return None
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("Could not parse rclone registry file — it may be corrupted.")
        return None
    entry = data.get(remote_name)
    if isinstance(entry, dict):
        return entry.get("path")
    return entry

def save_rclone_json(remote_name: str, folder_path: str, json_path="./bin/rclone_remote.json"):
    
    if remote_name.strip().lower() == "deic storage":
        remote_name = "deic-storage"

    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    data = {}
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print("Warning: JSON file was corrupted or empty, reinitializing.")
    data[remote_name] = {
        "path": f"{remote_name}:{folder_path}",
        "last_sync": None,
        "status": "initialized"
    }
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
        print(f"Saved rclone path for '{remote_name}' to {json_path}")

def load_all_rclone_json(json_path="./bin/rclone_remote.json"):
    if not os.path.exists(json_path):
        return {}
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def update_last_sync(remote_name: str, success=True, json_path="./bin/rclone_remote.json"):
    
    if remote_name.strip().lower() == "deic storage":
        remote_name = "deic-storage"

    if not os.path.exists(json_path):
        return
    try:
        with open(json_path, 'r+') as f:
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

def rclone_sync(remote_name: str = None, folder_to_backup: str = None):
    
    if remote_name.strip().lower() == "deic storage":
        remote_name = "deic-storage"

    rclone_repo = load_rclone_json(remote_name)

    if not rclone_repo:
        print("remote has not been configured")
        return

    if folder_to_backup is None:
        folder_to_backup = str(PROJECT_ROOT)

    if not os.path.exists(folder_to_backup):
        print(f"Error: The folder '{folder_to_backup}' does not exist.")
        return
    _ , exclude_patterns = read_toml_ignore(folder = folder_to_backup, toml_path = "pyproject.toml" ,  ignore_filename = ".rcloneignore",tool_name = "rcloneignore",toml_key = "patterns")

    exclude_args = []
    for pattern in exclude_patterns:
        exclude_args.extend(["--exclude", pattern])
    with change_dir("./data"):
        _ = git_commit(msg="Rclone Backup", path=os.getcwd())
        git_log_to_file(".gitlog")
    git_push(load_from_env("CODE_REPO", ".cookiecutter") != "None", "Rclone Backup")
    command_sync = ['rclone', 'sync', folder_to_backup, rclone_repo, '--verbose'] + exclude_args
    remote_name = rclone_repo.split(":")[0]
    try:
        subprocess.run(command_sync, check=True)
        print(f"Folder '{folder_to_backup}' successfully synchronized with '{rclone_repo}'.")
        update_last_sync(remote_name, success=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to sync folder to remote: {e}")
        update_last_sync(remote_name, success=False)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        update_last_sync(remote_name, success=False)

def list_remotes():
    print("\n🔌 Rclone Remotes:")
    try:
        result = subprocess.run(['rclone', 'listremotes'], check=True, stdout=subprocess.PIPE)
        rclone_configured = set(r.rstrip(':') for r in result.stdout.decode().splitlines())
    except Exception as e:
        print(f"Failed to list remotes: {e}")
        rclone_configured = set()

    print("\n📁 Mapped Backup Folders:")
    paths = load_all_rclone_json()
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
    if remote_name.strip().lower() == "deic storage":
        remote_name = "deic-storage"

    try:
        result = subprocess.run(['rclone', 'listremotes'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        remotes = result.stdout.decode('utf-8').splitlines()
        return f"{remote_name}:" in remotes
    except subprocess.CalledProcessError as e:
        print(f"Failed to check rclone remotes: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

def add_remote(remote_name: str = "deic-storage", email: str = None, password: str = None):
    
    remote_name = remote_name.lower()

    if remote_name.strip().lower() == "deic storage":
        remote_name = "deic-storage"

    if remote_name == "deic-storage":
        command = [
            'rclone', 'config', 'create', remote_name, 'sftp',
            'host', 'sftp.storage.deic.dk', 'port', '2222',
            'user', email, 'pass', password
        ]
    elif remote_name == "erda":
        command = [
            'rclone', 'config', 'create', remote_name, 'sftp',
            'host', 'io.erda.dk', 'port', '22',
            'user', email, 'pass', password
        ]
    elif remote_name in ["dropbox", "onedrive"]:
        print(f"You will need to authorize rclone with {remote_name}")
        command = ['rclone', 'config', 'create', remote_name, remote_name]
    elif remote_name == "local":
        command = ['rclone', 'config', 'create', remote_name, 'local']
    else:
            # Fetch all backend types from rclone
        output = list_supported_remote_types()
        backend_types = [line.split()[0] for line in output.splitlines() if line and not line.startswith(" ") and ":" in line]

        if remote_name in backend_types:
            print(f"Running interactive config for backend '{remote_name}'...")
            command = ['rclone', 'config', 'create', remote_name, remote_name]
        else:
            print("Unsupported remote name.")
            return
    try:
        subprocess.run(command, check=True)
        print(f"Rclone remote '{remote_name}' created successfully.")
    except Exception as e:
        print(f"Failed to create rclone remote: {e}")

def delete_remote(remote_name: str, json_path="./bin/rclone_remote.json"):
    if remote_name.strip().lower() == "deic storage":
        remote_name = "deic-storage"

    # Step 1: Attempt to delete the actual remote directory if it exists
    remote_path = load_rclone_json(remote_name, json_path)
    if remote_path:
        try:
            print(f"Attempting to purge remote folder at: {remote_path}")
            subprocess.run(['rclone', 'purge', remote_path], check=True)
            print(f"Successfully purged remote folder: {remote_path}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Warning: Could not purge remote folder '{remote_path}': {e}")
        except Exception as e:
            print(f"Unexpected error during purge: {e}")

    # Step 2: Delete the remote from rclone config
    try:
        subprocess.run(['rclone', 'config', 'delete', remote_name], check=True)
        print(f"Rclone remote '{remote_name}' deleted from rclone configuration.")
    except subprocess.CalledProcessError as e:
        print(f"Error deleting remote from rclone: {e}")

    # Step 3: Remove entry from local JSON registry
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r+') as f:
                data = json.load(f)
                if remote_name in data:
                    del data[remote_name]
                    f.seek(0)
                    f.truncate()
                    json.dump(data, f, indent=2)
                    print(f"Removed '{remote_name}' entry from {json_path}.")
        except Exception as e:
            print(f"Error updating JSON config: {e}")

def add_folder(remote_name, base_folder):
    
    if remote_name.strip().lower() == "deic storage":
        remote_name = "deic-storage"

    while True:
        check_command = ['rclone', 'lsf', f"{remote_name}:/{base_folder}"]
        result = subprocess.run(check_command, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            choice = input(f"'{base_folder}' exists on '{remote_name}'. Overwrite (o), rename (n), cancel (c)? [o/n/c]: ").strip().lower()
            if choice == 'o':
                break
            elif choice == 'n':
                base_folder = input("New folder name: ").strip()
            else:
                print("Cancelled.")
                return None
        else:
            break
    try:
        subprocess.run(['rclone', 'mkdir', f"{remote_name}:{base_folder}"], check=True)
        save_rclone_json(remote_name, base_folder)
    except Exception as e:
        print(f"Error creating folder: {e}")

def setup_remote_backup(remote_name:str = None):

    if remote_name:
        if remote_name.strip().lower() == "deic storage":
            remote_name = "deic-storage"
        
        email, password, base_folder = remote_user_info(remote_name.lower())
        if install_rclone("./bin"):
            add_remote(remote_name.lower(), email, password)
            add_folder(remote_name.lower(), base_folder)
    else:
        install_rclone("./bin")

def list_supported_remote_types():
    try:
        result = subprocess.run(['rclone', 'help', 'backends'], check=True, stdout=subprocess.PIPE, text=True)
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
        remote_path = load_rclone_json(remote)
        if not remote_path:
            print(f"No path found for remote '{remote}'.")
            return
        with tempfile.NamedTemporaryFile() as temp:
            command = [
                'rclone', 'diff', '.', remote_path,
                '--dry-run', '--no-traverse', '--differ', '--missing-on-dst', '--missing-on-src',
                '--output', temp.name
            ]
            try:
                subprocess.run(command, check=True)
                with open(temp.name, 'r') as f:
                    diff_output = f.read()
                print(f"\n📊 Diff report for '{remote}':\n{diff_output or '[No differences]'}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to generate diff report for '{remote}': {e}")

    if remote_name.strip().lower() == "deic storage":
        remote_name = "deic-storage"

    if remote_name.lower() == "all":
        for remote in load_all_rclone_json().keys():
            run_diff(remote)
    else:
        run_diff(remote_name)

def push_backup(remote_name):
    if remote_name.strip().lower() == "deic storage":
        remote_name = "deic-storage"

    os.chdir(PROJECT_ROOT)
    
    if not install_rclone("./bin"):
        return
    if remote_name.lower() == "all":
        all_remotes = load_all_rclone_json()
        for remote_name in all_remotes:
            rclone_sync(remote_name.lower())
    else:
        rclone_repo = load_rclone_json(remote_name.lower())
        if not rclone_repo:
            email, password, base_folder = remote_user_info(remote_name.lower())
            add_remote(remote_name.lower(), email, password)
            add_folder(remote_name.lower(), base_folder)
        
        rclone_sync(remote_name.lower())

def generate_diff_report(remote_name):

    def run_diff(remote):
        remote_path = load_rclone_json(remote)
        if not remote_path:
            print(f"No path found for remote '{remote}'.")
            return
        with tempfile.NamedTemporaryFile() as temp:
            command = [
                'rclone', 'diff', '.', remote_path,
                '--dry-run', '--no-traverse', '--differ', '--missing-on-dst', '--missing-on-src',
                '--output', temp.name
            ]
            try:
                subprocess.run(command, check=True)
                with open(temp.name, 'r') as f:
                    diff_output = f.read()
                print(f"\n📊 Diff report for '{remote}':\n{diff_output or '[No differences]'}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to generate diff report for '{remote}': {e}")

    if remote_name.strip().lower() == "deic storage":
        remote_name = "deic-storage"
        
    if remote_name.lower() == "all":
        for remote in load_all_rclone_json().keys():
            run_diff(remote)
    else:
        run_diff(remote_name)

def pull_backup(remote_name: str = None, destination_folder: str = None):
    import subprocess

    if remote_name is None:
        print("Error: No remote specified for pulling backup.")
        return

    if remote_name.strip().lower() == "deic storage":
        remote_name = "deic-storage"

    rclone_repo = load_rclone_json(remote_name)
    if not rclone_repo:
        print("Remote has not been configured or not found in registry.")
        return

    if destination_folder is None:
        destination_folder = str(PROJECT_ROOT)
 
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    _ , exclude_patterns = read_toml_ignore(folder = destination_folder, toml_path = "pyproject.toml" ,  ignore_filename = ".rcloneignore",tool_name = "rcloneignore",toml_key = "patterns")
  
    exclude_args = []
    for pattern in exclude_patterns:
        exclude_args.extend(["--exclude", pattern])

    command_pull = ['rclone', 'sync', rclone_repo, destination_folder, '--verbose'] + exclude_args

    try:
        subprocess.run(command_pull, check=True)
        print(f"Backup pulled from '{rclone_repo}' to '{destination_folder}' successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to pull backup from remote: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while pulling backup: {e}")

@ensure_correct_kernel
def main():
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

    if args.command == "list":
        list_remotes()
    elif args.command == "add":
        setup_remote_backup(args.remote)
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

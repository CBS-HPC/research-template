import os
import subprocess
import pathlib
import argparse
import json
from datetime import datetime
import tempfile

from .general_tools import *
from .versioning_tools import *

def load_rclone_json(remote_name: str, json_path="./bin/rclone_remote.json") -> str:
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
 
    rclone_repo = load_rclone_json(remote_name)

    if not rclone_repo:
        print("remote has not been configured")
        return

    if folder_to_backup is None:
        folder_to_backup = os.getcwd()
    if not os.path.exists(folder_to_backup):
        print(f"Error: The folder '{folder_to_backup}' does not exist.")
        return
    exclude_patterns = read_rcloneignore(folder_to_backup)
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
    if remote_name == "deic-storage":
        command = [
            'rclone', 'config', 'create', remote_name, 'sftp',
            'host', 'sftp.storage.deic.dk', 'port', '2222',
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
    import subprocess
    try:
        subprocess.run(['rclone', 'config', 'delete', remote_name], check=True)
        print(f"Rclone remote '{remote_name}' deleted from rclone configuration.")
    except subprocess.CalledProcessError as e:
        print(f"Error deleting remote from rclone: {e}")

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
        return f"{remote_name}:{base_folder}"
    except Exception as e:
        print(f"Error creating folder: {e}")
        return None

def read_rcloneignore(folder):
    path = os.path.join(folder, '.rcloneignore')
    if not os.path.exists(path): return []
    with open(path) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def setup_remote_backup(remote_name):
    if remote_name.lower() != "none":
        email, password, base_folder = remote_user_info(remote_name.lower())
        if install_rclone("./bin"):
            add_remote(remote_name.lower(), email, password)
            _ = add_folder(remote_name.lower(), base_folder)

def list_supported_remote_types():
    try:
        result = subprocess.run(['rclone', 'help', 'backends'], check=True, stdout=subprocess.PIPE, text=True)
        print("\n📦 Supported Rclone Remote Types:")
        print("\nRecommended by CBS: ['Deic-Storage', 'Dropbox', 'Onedrive', 'Local']\n")
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

    if remote_name.lower() == "all":
        for remote in load_all_rclone_json().keys():
            run_diff(remote)
    else:
        run_diff(remote_name)

@ensure_correct_kernel
def push_backup(remote_name):
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
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
            rclone_repo = add_folder(remote_name.lower(), base_folder)
        
        if rclone_repo:
            rclone_sync(rclone_repo)
        else:
            print(f"Failed to backup to {remote_name}")

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

    if remote_name.lower() == "all":
        for remote in load_all_rclone_json().keys():
            run_diff(remote)
    else:
        run_diff(remote_name)

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
    else:
        parser.print_help()

if __name__ == "__main__":
    os.chdir(pathlib.Path(__file__).resolve().parent.parent.parent)
    main()

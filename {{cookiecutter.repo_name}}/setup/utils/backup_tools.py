import os
import subprocess
import getpass
import pathlib
import argparse

from .general_tools import *
from .versioning_tools import *

# RClone:
def setup_remote_backup(remote_backups,repo_name):
    
    if remote_backups.lower() != "none":
        remote_backups= [item.strip() for item in remote_backups.split(",")]
        for remote_backup in remote_backups:
            email, password,base_folder = remote_user_info(remote_backup.lower(),repo_name)
            if install_rclone("./bin"):
                rclone_remote(remote_backup.lower(),email, password)
                _= rclone_folder(remote_backup.lower(), base_folder)


def remote_user_info(remote_name,repo_name):
    """Prompt for remote login credentials and base folder path."""

    # Handle base folder input (default from input value or fallback to home dir)
    default_base = 'RClone_backup/' + repo_name
    base_folder = input(f"Enter base folder for {remote_name} [{default_base}]: ").strip() or default_base

    if remote_name.lower() == "deic storage":
        default_email = load_from_env("EMAIL", ".cookiecutter")
        email = password = None

        while not email or not password:
            email = input(f"Please enter email to Deic Storage [{default_email}]: ").strip() or default_email
            password = getpass.getpass("Please enter password to Deic Storage: ").strip()

            if not email or not password:
                print("Both email and password are required.\n")

        print(f"\nUsing email: {email}")
        print(f"Using base folder: {base_folder}\n")
        return email, password, base_folder

    # Add other remote handlers here if needed
    return None, None, base_folder
  
def rclone_remote(remote_name: str = "deic storage",email:str = None, password:str = None ):
    """Create an rclone remote configuration for Deic Storage (SFTP) or Dropbox based on remote_name."""

    if remote_name == "deic storage":
        command = [
            'rclone', 'config', 'create', remote_name, 'sftp',
            'host', 'sftp.storage.deic.dk',
            'port', '2222',
            'user', email,
            'pass', password
        ]

    elif remote_name in ["dropbox", "onedrive"]:
        print(f"You will need to authorize rclone with {remote_name}")
        command = ['rclone', 'config', 'create', remote_name, remote_name]

    elif remote_name == "local":
        local_path = input("Please enter the local path for rclone: ").strip()
        local_path = local_path.replace("'", "").replace('"', '')
        local_path = check_path_format(local_path)

        if not os.path.isdir(local_path):
            print("Error: The specified local path does not exist.")
            return
        print(f"Setting up local path as rclone remote: {local_path}")
        command = ['rclone', 'config', 'create', remote_name, 'local', '--local-root', local_path]

    else:
        print("Unsupported remote name. Choose 'deic storage', 'dropbox', 'onedrive', or 'local'.")
        return

    try:
        subprocess.run(command, check=True)
        print(f"Rclone remote '{remote_name}' created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create rclone remote: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def rclone_folder(remote_name, base_folder):
    while True:
        # Check if folder exists
        check_command = ['rclone', 'lsf', f"{remote_name}:/{base_folder}"]
        folder_exists = subprocess.run(check_command, capture_output=True, text=True)
        
        if folder_exists.returncode == 0 and folder_exists.stdout.strip():
            print(f"The folder '{base_folder}' already exists on remote '{remote_name}'.")
            choice = input("Do you want to overwrite it (o), enter a new folder name (n), or cancel (c)? [o/n/c]: ").strip().lower()

            if choice == "o":
                print(f"Overwriting existing folder '{base_folder}' on remote '{remote_name}'...")
                break  # Proceed to mkdir (will not actually delete, but assume overwrite is fine)
            elif choice == "n":
                base_folder = input("Enter new base folder name: ").strip()
                continue  # Check again
            else:
                print("Operation cancelled by user.")
                return None

        else:
            # Folder doesn't exist, safe to proceed
            break

    # Create the folder
    rclone_repo = f'{remote_name}:{base_folder}'
    command = ['rclone', 'mkdir', rclone_repo]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Backup folder '{base_folder}' created successfully on remote '{remote_name}'.")
        save_to_env(rclone_repo, "RCLODE_REPO")
        return rclone_repo

    except subprocess.CalledProcessError as e:
        if "couldn't connect SSH: ssh: handshake failed" in e.stderr:
            if remote_name == "deic storage":
                print('Connection to "Deic Storage" failed. Please log in to https://storage.deic.dk/ with MFA.')
        else:
            print(f"Failed to create backup folder: {e.stderr.strip()}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return None

def read_rcloneignore(folder):
    """Read the .rcloneignore file from the specified folder and return the patterns."""
    rcloneignore_path = os.path.join(folder, '.rcloneignore')
    
    ignore_patterns = []
    if os.path.exists(rcloneignore_path):
        with open(rcloneignore_path, 'r') as f:
            for line in f:
                # Remove comments and strip any surrounding whitespace
                line = line.strip()
                if line and not line.startswith('#'):
                    ignore_patterns.append(line)
    return ignore_patterns

def rclone_sync(rclone_repo: str = None, folder_to_backup: str = None):
    """Synchronize a folder to a remote location using rclone."""
    if not rclone_repo:
        rclone_repo = load_from_env("RCLONE_REPO")

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
        _ = git_commit(msg = "Rclone Backup",path = os.getcwd())
        git_log_to_file(".gitlog")
    
    git_push(load_from_env("CODE_REPO",".cookiecutter")!= "None","Rclone Backup")

    
    command_sync = [
        'rclone', 'sync', folder_to_backup, rclone_repo, '--verbose'
    ] + exclude_args
    
    try:
        subprocess.run(command_sync, check=True)
        print(f"Folder '{folder_to_backup}' successfully synchronized with '{rclone_repo}'.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to sync folder to remote: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def check_rclone_remote(remote_name):
    """Check if a specific remote repository is configured in rclone."""
    try:
        # Run the rclone listremotes command to get all configured remotes
        result = subprocess.run(['rclone', 'listremotes'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Decode the output and split by lines
        remotes = result.stdout.decode('utf-8').splitlines()

        # Check if the given remote_name exists in the list (remotes end with ':')
        if f"{remote_name}:" in remotes:
            print(f"Remote '{remote_name}' is configured in rclone.")
            return True
        else:
            print(f"Remote '{remote_name}' is NOT configured in rclone.")
            return False

    except subprocess.CalledProcessError as e:
        print(f"Failed to check rclone remotes: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

@ensure_correct_kernel
def push_backup(remote_backups,repo_name):
    
    # Change to project root directory
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    
    if remote_backups.lower() != "none": 
        if install_rclone("./bin"):
            remote_backups= [item.strip() for item in remote_backups.split(",")]
            for remote_backup in remote_backups:
                rclone_repo = None
                if check_rclone_remote(remote_backup.lower()):
                    rclone_repo = load_from_env("RCLODE_REPO")
            
                if not rclone_repo:
                    email, password,base_folder = remote_user_info(remote_backup.lower(),repo_name)
                    rclone_remote(remote_backup.lower(),email, password)
                    rclone_repo = rclone_folder(remote_backup.lower(), base_folder)
            
                if rclone_repo:
                    rclone_sync(rclone_repo, folder_to_backup=None)
                else: 
                    print(f"Failed to backup to {remote_backup}")

def main():

    # Add command-line argument parsing
    parser = argparse.ArgumentParser(description="Run backup process")
    parser.add_argument('--repo_name', type=str, default=None, help="Repository name")
    parser.add_argument('--remote_backup', type=str, default=None, help="Comma separated remote backups")
    args = parser.parse_args()

    repo_name = args.repo_name or load_from_env("REPO_NAME", ".cookiecutter")
    remote_backup = args.remote_backup or load_from_env("REMOTE_BACKUP", ".cookiecutter")
    push_backup(remote_backup, repo_name)

if __name__ == "__main__":
    
    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)

    main()
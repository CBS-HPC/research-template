import os
import sys
import subprocess
import platform
import zipfile
import glob
import getpass
import pathlib

from .general_tools import *
from .versioning_tools import *

# RClone:
def setup_remote_backup(remote_backups,repo_name):
    
    if remote_backups.lower() != "none":
        remote_backups= [item.strip() for item in remote_backups.split(",")]
        for remote_backup in remote_backups:
            email, password = remote_user_info(remote_backup.lower())
            if install_rclone("./bin"):
                rclone_remote(remote_backup.lower(),email, password)
                _= rclone_folder(remote_backup.lower(), 'RClone_backup/' + repo_name)
       
def install_rclone2(install_path):
    """Download and extract rclone to the specified bin folder."""

    def download_rclone(install_path="./bin"):
        os_type = platform.system().lower()
        
        # Set the URL and executable name based on the OS
        if os_type == "windows":
            url = "https://downloads.rclone.org/rclone-current-windows-amd64.zip"
            rclone_executable = "rclone.exe"
        elif os_type in ["linux", "darwin"]:  # "Darwin" is the system name for macOS
            url = "https://downloads.rclone.org/rclone-current-linux-amd64.zip" if os_type == "linux" else "https://downloads.rclone.org/rclone-current-osx-amd64.zip"
            rclone_executable = "rclone"
        else:
            print(f"Unsupported operating system: {os_type}. Please install rclone manually.")
            return None

        # Create the bin folder if it doesn't exist
        install_path = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(install_path))
        os.makedirs(install_path, exist_ok=True)
    
        # Download rclone
        local_zip = os.path.join(install_path, "rclone.zip")
        print(f"Downloading rclone for {os_type} to {local_zip}...")
        response = requests.get(url)
        if response.status_code == 200:
            with open(local_zip, 'wb') as file:
                file.write(response.content)
            print("Download complete.")
        else:
            print("Failed to download rclone. Please check the URL.")
            return None

        # Extract the rclone executable
        print("Extracting rclone...")
        with zipfile.ZipFile(local_zip, 'r') as zip_ref:
            zip_ref.extractall(install_path)

        rclone_folder = glob.glob(os.path.join(install_path, 'rclone-*'))

        if not rclone_folder or len(rclone_folder) > 1:
            print(f"More than one 'rclone-*' folder detected in {install_path}")
            return None
         
        # Clean up by deleting the zip file
        os.remove(local_zip)

        rclone_path = os.path.join(install_path,rclone_folder[0] ,rclone_executable)
        print(f"rclone installed successfully at {rclone_path}.")

        rclone_path = os.path.abspath(rclone_path)

        os.chmod(rclone_path, 0o755)
        return rclone_path

    if not is_installed('rclone','Rclone'):
        rclone_path = download_rclone(install_path)
        return exe_to_path('rclone', os.path.dirname(rclone_path))
    return True

def remote_user_info(remote_name):
    email = None
    password = None
    
    if remote_name == "deic storage":
        default_email = load_from_env("EMAIL", ".cookiecutter")

        email = None
        password = None

        while not email or not password:
            email_prompt = f"Please enter email to Deic Storage [{default_email}]: "
            email = input(email_prompt).strip() or default_email
            #password = input("Please enter password to Deic Storage: ").strip()
            password = getpass.getpass("Please enter password to Deic Storage: ").strip()

            if not email or not password:
                print("Both email and password are required.\n")

        print(f"\nUsing email for Deic Storage: {email}\n")
    return email, password
    
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
    # Generate the rclone path
    rclone_repo = f'{remote_name}:{base_folder}'
    command = ['rclone', 'mkdir', rclone_repo]

    try:
        # Execute the command and capture output
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Backup folder '{base_folder}' created successfully on remote '{remote_name}'.")
        
        save_to_env(rclone_repo, "RCLODE_REPO")
        return rclone_repo

    except subprocess.CalledProcessError as e:
        # Check if the specific SSH error is in stderr
        if "couldn't connect SSH: ssh: handshake failed" in e.stderr:
            if remote_name == "deic storage":
                print('Connection to "Diec Storage" failed. Please log-on to "https://storage.deic.dk/" with MFA')
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
        #git_log_to_file(os.path.join(folder_to_backup, "data.gitlog"))
    
    _ = git_commit("Rclone Backup")
    
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

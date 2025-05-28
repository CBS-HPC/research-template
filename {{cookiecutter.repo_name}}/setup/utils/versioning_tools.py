import os
import subprocess
import sys
import platform
import shutil
import pathlib
import zipfile
import glob

from .general_tools import *

package_installer(required_libraries =  ['requests'])

import requests

# Version Control
def setup_version_control(version_control,remote_storage,code_repo,repo_name):
    """Handle repository creation and log-in based on selected platform."""
    if version_control.lower()  == "git":
        setup_git(version_control,code_repo)
    if version_control.lower() == "datalad":
        setup_datalad(version_control,remote_storage,code_repo,repo_name)
    elif version_control.lower() == "dvc":
        setup_dvc(version_control,remote_storage,code_repo,repo_name)
 
# Git Functions:
def setup_git(version_control,code_repo):

    if install_git("./bin/git"): 

        # Ensure that chdir is at project folder
        os.chdir(pathlib.Path(__file__).resolve().parent.parent.parent)
        
        flag, git_name, git_email = check_git_config()

        if not flag:
            flag, git_name, git_email = setup_git_config(version_control,git_name, git_email)
        
        if flag and version_control == "Git":  
            default_branch = "main" if code_repo.lower() in ["github", "codeberg"] else "master"           
            flag = git_init(msg = "Initial commit",branch_name = default_branch)
            # Creating its own git repo for "data"
            if flag:
                with change_dir("./data"):
                    flag = git_init(msg = "Initial commit", branch_name = "data", path = os.getcwd())
                    subprocess.run(["git", "config", "--global", "init.defaultBranch", default_branch], check=True)
                    git_log_to_file(os.path.join(".gitlog"))
        if flag:
            save_to_env(git_name,"GIT_USER") 
            save_to_env(git_email,"GIT_EMAIL")    
    
        return flag
    else:
        return False

def install_git(install_path=None):
    """
    Installs Git if it is not already installed.
    - For Windows: Downloads and installs Git to a specified path.
    - For Linux: Installs using 'sudo apt install git-all'.
    - For macOS: Installs via Xcode Command Line Tools.

    Parameters:
    - install_path (str, optional): The path where Git should be installed on Windows.

    Returns:
    - bool: True if installation is successful, False otherwise.
    """

    if is_installed('git', 'Git'):
        return True 
    
    try:
        os_type = platform.system().lower()

        if os_type == "windows":
            if not install_path:
                print("Please provide an install path for Windows installation.")
                return False

            install_path = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(install_path))

            # Download Git installer for Windows
            download_dir = os.path.dirname(install_path)
            installer_name = "Git-latest-64-bit.exe"
            installer_path = os.path.join(download_dir, installer_name)
            url = f"https://github.com/git-for-windows/git/releases/latest/download/{installer_name}"

            print(f"Downloading Git installer from {url} to {download_dir}...")
            urllib.request.urlretrieve(url, installer_path)
            print("Download complete.")

            # Run the silent installation
            subprocess.run([installer_path, "/VERYSILENT", f"/DIR={install_path}", "/NORESTART"], check=True)

            # Add Git to PATH
            exe_to_path('git',os.path.join(install_path, "bin"))
            
        elif os_type == "linux":
            # Install Git on Linux using apt
            print("Installing Git on Linux using 'sudo apt install git-all'...")
            subprocess.run(["sudo", "apt", "install", "-y", "git-all"], check=True)

        elif os_type == "darwin":
            # Attempt to install Git on macOS using Xcode Command Line Tools
            print("Installing Git on macOS using Xcode Command Line Tools...")
            try:
                subprocess.run(["git", "--version"], check=True)
                print("Git installation complete using Xcode Command Line Tools.")
                return True
            except subprocess.CalledProcessError:
                print("Xcode Command Line Tools installation failed or was canceled.")
                return False

        else:
            print("Unsupported operating system.")
            return False

        # Verify installation
        if is_installed('git', 'Git'):
            print("Git installation complete.")
            return True
        else:
            print("Failed to verify Git installation.")
            return False

    except Exception as e:
        print(f"Failed to install Git: {e}")
        return False

def check_git_config():
    """
    Check if Git is configured with user.name and user.email. If not, prompt the user for this information.

    Args:
    - check: Flag to indicate whether to check and configure Git.

    Returns:
    - bool: True if Git is configured, False otherwise.
    """
    try:
        # Check .env file
        env_name = load_from_env('GIT_USER')
        env_email= load_from_env('GIT_EMAIL')
    
        # Test
        if env_name and env_email:
            return False, env_name, env_email

        # Check the current Git user configuration
        current_name = subprocess.run(
            ["git", "config", "--global", "user.name"],
            capture_output=True, text=True, check=True)
        current_email = subprocess.run(
            ["git", "config", "--global", "user.email"],
            capture_output=True, text=True, check=True)
        
        # Handle potential UnicodeDecodeError
        try:
            current_name = current_name.stdout.strip()
            current_email = current_email.stdout.strip()
        except UnicodeDecodeError as e:
            print(f"Error decoding Git configuration output: {e}")
            return False, None, None  # Return False if we can't decode the output
        
        # Check if Git is properly configured
        if current_name and current_email:
            print(f"Git is configured with user.name: {current_name} and user.email: {current_email}")

            confirm = ask_yes_no(f"Do you want to keep the current Git user.name: {current_name} and user.email: {current_email} (yes/no): ")
            
            if confirm:
                return True, current_name, current_email # Return True if configured
            else: 
                return False, None, None   # Return False if Git is not fully configured
        else:
            print("Git is not fully configured.")
            return False, None, None   # Return False if Git is not fully configured

    except subprocess.CalledProcessError as e:
        print(f"Git configuration check failed: {e}")
        return False, None, None   # Return False if subprocess fails
    except Exception as e:    
        print(f"Unexpected error: {e}")
        return False, None, None   # Return False for any other unexpected errors

def setup_git_config(version_control,git_name,git_email):
    """
    Prompts the user for their name and email, then configures Git with these details.

    Returns:
    - bool: True if the configuration is successful, False otherwise.
    """
    try:
        if not git_name or not git_email:
            git_name,git_email = git_user_info(version_control)

        # Configure Git user name and email locally
        subprocess.run(["git", "config", "--global", "user.name", git_name], check=True)
        subprocess.run(["git", "config", "--global", "user.email", git_email], check=True)

        print(f"Git configured with name: {git_name} and email: {git_email}")
        return True,git_name,git_email
    except subprocess.CalledProcessError as e:
        print(f"Failed to configure Git: {e}")
        return False,git_name,git_email
      
def git_init(msg, branch_name, path: str =None):
    
    if not path: 
        path = str(pathlib.Path(__file__).resolve().parent.parent.parent)
    
    # Ensure the target path exists
    if not os.path.exists(path):
        os.makedirs(path)

    if branch_name:
        subprocess.run(["git", "config", "--global", "init.defaultBranch", branch_name], check=True)

    # Initialize a Git repository if one does not already exist
    if not os.path.isdir(os.path.join(path, ".git")):
        subprocess.run(["git", "init"], check=True, cwd=path)
        print(f"Initialized a new Git repository in {path}.")

        #if rename:
        #    subprocess.run(["git", "branch", "-m", "master", rename], check=True, cwd=path)

        _ = git_commit(msg, path)
        print(f"Created the following commit: {msg}")
        return True
    
    return False 
    
def git_commit(msg: str = "", path: str = None) -> str:
    """Commits changes to Git in the given path and returns the commit hash."""
    
    if not path: 
        path = str(pathlib.Path(__file__).resolve().parent.parent.parent)
    
    if os.path.isdir(os.path.join(path, ".git")):
        # Ensure Git is installed
        is_installed("git")

        try:
            # Stage all changes
            subprocess.run(["git", "add", "."], check=True, cwd=path)

            try:
                subprocess.run(["git", "commit", "-m", msg], check=True, cwd=path)
            except subprocess.CalledProcessError:
                print("No changes to commit.")

            # Extract commit hash
            commit_hash = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                cwd=path
            ).stdout.strip()

            return commit_hash

        except subprocess.CalledProcessError as e:
            print(f"An error occurred: {e}")
            return None

    return None

def git_push(flag: str, msg: str = "", path: str = None):
    def push_all(remote="origin", path: str =None):

        if not path: 
            path = str(pathlib.Path(__file__).resolve().parent.parent.parent)

        try:
            # Get the name of the current branch
            current_branch = subprocess.check_output(
                ["git", "branch", "--show-current"],
                text=True,
                cwd=path
            ).strip()

            # Get all local branches
            branches = subprocess.check_output(
                ["git", "branch"],
                text=True,
                cwd=path
            ).strip().splitlines()

            # Clean up branch names
            branches = [branch.strip().replace("* ", "") for branch in branches]

            # Filter out the current branch
            branches_to_push = [branch for branch in branches if branch != current_branch]

            # Push each branch except the current one
            for branch in branches_to_push:
                subprocess.run(["git", "push", remote, branch], check=True, cwd=path)

            print(f"Successfully pushed all branches except '{current_branch}'")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while pushing branches: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    if not path: 
        path = str(pathlib.Path(__file__).resolve().parent.parent.parent)
    try:
        
        if os.path.isdir(os.path.join(path, ".datalad")):
            # Ensure required tools are installed
            is_installed('git')
            is_installed('datalad')
            is_installed('git-annex')
            is_installed('rclone')

            subprocess.run(["datalad", "save", "-m", msg], check=True, cwd=path)
            push_all(path=path)

        elif os.path.isdir(os.path.join(path, ".git")):
            commit_hash = git_commit(msg, path=path)
            if commit_hash:
                if flag:
                    result = subprocess.run(
                        ["git", "branch", "--show-current"],
                        check=True,
                        capture_output=True,
                        text=True,
                        cwd=path
                    )
                    branch = result.stdout.strip()
                    if branch:
                        subprocess.run(["git", "push", "origin", branch], check=True, cwd=path)
                        print(f"Pushed current branch '{branch}' to origin.")
                    else:
                        subprocess.run(["git", "push", "--all"], check=True, cwd=path)
                        print("Pushed all branches to origin.")
            else:
                print("No commit created — nothing to push.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

def git_log_to_file(output_file_path):
    """
    Runs the 'git log' command with the specified output file path.

    Parameters:
    output_file_path (str): The full path to the output file where the Git log will be saved.
    """
    try:
        # Run the git log command with the specified output file
        command = f'git log --all --pretty=fuller --stat > "{output_file_path}"'
        subprocess.run(command, shell=True, check=True)
        print(f"Git log has been saved to {output_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

def get_git_hash(path):
    """
    Get the Git hash of a file or folder.
    For folders, the hashes of all files within the folder are combined.
    If any exception occurs, it returns None.
    """
    try:
        if not is_installed('git'):
            return None
        # Check if path is a file or directory
        if os.path.isfile(path):
            # Get the Git hash of the file
            result = subprocess.run(['git', 'hash-object', path], capture_output=True, text=True)
            return result.stdout.strip()
        elif os.path.isdir(path):
            # For directory, get the hash of each file inside it
            hashes = []
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    result = subprocess.run(['git', 'hash-object', file_path], capture_output=True, text=True)
                    hashes.append(result.stdout.strip())
            # Combine all file hashes into a single string and get its hash
            combined_hashes = "".join(hashes)
            result = subprocess.run(['git', 'hash-object', '-w', '--stdin'], input=combined_hashes, capture_output=True, text=True)
            return result.stdout.strip()
        else:
            raise ValueError(f"{path} does not exist or is not a valid file or directory.")
    except Exception as e:
        print(f"Error while calculating hash for {path}: {e}")
        return None

# DVC Setup Functions
def setup_dvc(version_control,remote_storage,code_repo,repo_name):

    # Install Git
    if not setup_git(version_control,code_repo):
        return
    
    # Install datalad
    if not install_dvc():
        return
    dvc_init(remote_storage,code_repo,repo_name)

def install_dvc():
    """
    Install DVC using pip.
    """

    if not is_installed('dvc','DVC'):
        try:
            # Install DVC via pip
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'dvc[all]'])
            if not is_installed('dvc','DVC'):
                print("Error during datalad installation.")
                return False
            print("DVC has been installed successfully.") 
        except subprocess.CalledProcessError as e:
            print(f"An error occurred during DVC installation: {e}")
            return False
        except FileNotFoundError:
            print("Python or pip was not found. Please ensure Python and pip are installed and in your PATH.")
            return False
    return True

def dvc_init(remote_storage,code_repo,repo_name):

    # Initialize a Git repository if one does not already exist
    if not os.path.isdir(".git"):

        if code_repo.lower() in ["github","codeberg"]:
            subprocess.run(["git", "config", "--global", "init.defaultBranch", "main"], check=True)

        subprocess.run(["git", "init"], check=True)

    # Init dvc
    if not os.path.isdir(".dvc"):
        subprocess.run(["dvc", "init"], check=True)
    else:
        print('I is already a DVC project')
        return 

    # Add dvc remote storage
    if remote_storage == "Local Path":
        dvc_local_storage(repo_name)
    elif remote_storage in ["Dropbox","Deic Storage"]:
        dvc_deic_storage(repo_name)

    folders = ["data","reports","docs"]
    for folder in folders:
        subprocess.run(["dvc", "add",folder], check=True)

    _= git_commit("Initial commit")
    print("Created an initial commit.")

def dvc_deic_storage(remote_directory =None):

    email = input("Please enter email to Deic Storage: ").strip()
    password = input("Please enter password to Deic Storage: ").strip()

    # Use root directory if no path is provided
    remote_directory = remote_directory if remote_directory else ''

    # Construct the command to add the DVC SFTP remote
    add_command = [
        'dvc', 'remote', 'add', '-d', 'deic_storage',
        f"ssh://'{email}'@sftp.storage.deic.dk:2222"
    ]
    #f"sftp://'{email}'@sftp.storage.deic.dk:2222/{remote_directory}"
    # Construct the command to set the password for the remote
    password_command = [
        'dvc', 'remote', 'modify', 'deic_storage', 'password', password
    ]
    
    try:
        # Execute the add command
        subprocess.run(add_command, check=True)
        print("DVC remote 'deic_storage' added successfully.")
        
        # Execute the password command
        subprocess.run(password_command, check=True)
        print("Password for DVC remote 'deic_storage' set successfully.")
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to set up DVC remote: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def dvc_local_storage(repo_name):

    def get_remote_path(repo_name):
        """
        Prompt the user to provide the path to a DVC remote storage folder. 
        If `folder_path` already ends with `repo_name` and exists, an error is raised.
        Otherwise, if `folder_path` exists but does not end with `repo_name`, 
        it appends `repo_name` to `folder_path` to create the required directory.

        Parameters:
        - repo_name (str): The name of the repository to ensure at the end of `folder_path`.

        Returns:
        - str: Finalized path to DVC remote storage if valid, or None if an error occurs.
        """
        # Prompt the user for the folder path
        folder_path = input("Please enter the path to DVC remote storage:").strip()
        
        folder_path = os.path.abspath(folder_path)

        # Attempt to create folder_path if it does not exist
        if not os.path.isdir(folder_path):
            try:
                os.makedirs(folder_path, exist_ok=True)
                print(f"The path '{folder_path}' did not exist and was created.")
            except OSError as e:
                print(f"Failed to create the path '{folder_path}': {e}")
                return None
        
        # Check if folder_path already ends with repo_name
        if folder_path.endswith(repo_name):
            # Check if it already exists as a directory
            if os.path.isdir(folder_path):
                print(f"The path '{folder_path}' already exists with '{repo_name}' as the final folder.")
                return None  # Error out if the path already exists
        else:
            # Append repo_name to folder_path if it doesn’t end with it
            folder_path = os.path.join(folder_path, repo_name)
            try:
                # Create the repo_name directory if it doesn't exist
                os.makedirs(folder_path, exist_ok=True)
                print(f"Created directory: {folder_path}")
            except OSError as e:
                print(f"Failed to create the path '{folder_path}': {e}")
                return None

        # Return the finalized path
        return folder_path

    dvc_remote = get_remote_path(repo_name)
    if dvc_remote:
        subprocess.run(["dvc", "remote","add","-d","remote_storage",dvc_remote], check=True)
    
# Datalad Setup Functions
def setup_datalad(version_control,remote_storage,code_repo,repo_name):

    # Install Git
    if not setup_git(version_control,code_repo):
        return
    # Install git-annex
    if not install_git_annex():
        return
    # Install datalad
    if not install_datalad():
        return
    
    # Install rclone git-annex-remote-rclone
    install_rclone("./bin")
    install_git_annex_remote_rclone("./bin")

    # Create datalad dataset
    datalad_create()

    if remote_storage == "Local Path":
        datalad_local_storage(repo_name)
    elif remote_storage in ["Dropbox", "Deic Storage"]:
        datalad_deic_storage(repo_name)

def install_datalad():   

        if not is_installed('datalad','Datalad'):
            try:
                if not shutil.which('datalad-installer'):
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'datalad-installer'])
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'datalad'])
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyopenssl','--upgrade']) 
                if not is_installed('datalad','Datalad'):
                    print("Error during datalad installation.")
                    return False
                print("datalad installed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"An error occurred: {e}")
                return False
            except FileNotFoundError:
                print("One of the required commands was not found. Please ensure Python, pip, and Git are installed and in your PATH.")
                return False           
        return True

def install_git_annex():
    """
    Installs git-annex using datalad-installer if not already installed.
    Configures git to use the git-annex filter process.
    
    Returns:
        str: The installation path of git-annex if installed successfully.
        None: If the installation fails.
    """
    # Check if git-annex is installed
    if not is_installed('git-annex', 'Git-Annex'):
        try:
            # Ensure datalad-installer is available
            if not shutil.which('datalad-installer'):
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'datalad-installer'])
            
            # Install git-annex using datalad-installer and capture the output
            command = "echo y | datalad-installer git-annex -m datalad/git-annex:release"
            result = subprocess.run(command, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                print(f"Error during git-annex installation: {result.stderr}")
                return None
            
            # Parse the output for the installation path
            install_path = None
            for line in result.stderr.splitlines():
                if "git-annex is now installed at" in line:
                    install_path = line.split("at")[-1].strip()
                    break
            
            if not install_path:
                print("Could not determine git-annex installation path.")
                return False
  
            if not exe_to_path('git-annex',os.path.dirname(install_path)):
            #if not is_installed('git-annex', 'Git-Annex'):    
                return False
            
        except subprocess.CalledProcessError as e:
            print(f"Error during git-annex installation: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
    # Configure git to use the git-annex filter process
    try:
        subprocess.check_call(['git', 'config', '--global', 'filter.annex.process', 'git-annex filter-process'])
        print(f"git-annex installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error configuring git-annex filter process: {e}")
        return False

def install_git_annex_remote_rclone(install_path):
        
    def clone_git_annex_remote_rclone(install_path):
        """Clone the git-annex-remote-rclone repository to the specified bin folder."""
        repo_url = "https://github.com/git-annex-remote-rclone/git-annex-remote-rclone.git"
        repo_name = os.path.basename(repo_url).replace('.git', '')
        repo_path = os.path.join(install_path, repo_name)

        # Create the bin folder if it doesn't exist
        install_path = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(install_path))
        #install_path = os.path.abspath(install_path or os.getcwd())
        os.makedirs(install_path, exist_ok=True)

        # Check if the repository already exists
        if os.path.isdir(repo_path):
            print(f"The repository '{repo_name}' already exists in {install_path}.")
        else:
            print(f"Cloning {repo_url} into {repo_path}...")
            subprocess.run(["git", "clone", repo_url, repo_path], check=True)

        repo_path = os.path.abspath(repo_path)  # Convert to absolute path
        print(f"Repository cloned successfully to {repo_path}.")
        return repo_path
    
    # Clone https://github.com/git-annex-remote-rclone/git-annex-remote-rclone.git
    
    if not is_installed('git-annex-remote-rclone','git-annex-remote-rclone'):
        repo_path = clone_git_annex_remote_rclone(install_path)
        exe_to_path('git-annex-remote-rclone',repo_path)

def datalad_create():

    def unlock_files(files_to_unlock):
        attributes_file = ".gitattributes"
        with open(attributes_file, "a") as f:
            for file in files_to_unlock:
                f.write(f"{file} annex.largefiles=nothing\n")

    # Initialize a Git repository if one does not already exist
    if not os.path.isdir(".datalad"):
        files_to_unlock = ["src/**","setup/**","docs/**","config/**","README.md", "LICENSE.txt","environment.yml","setup.py","setup.ps1","setup.sh","CITATION.cff","datasets.json","hardware_information.txt"] # FIX ME
        subprocess.run(["datalad", "create","--force"], check=True)
        unlock_files(files_to_unlock )
        subprocess.run(["datalad", "save", "-m", "Initial commit"], check=True)
    else:
        print('I is already a Datalad project')
        return 
    
def datalad_deic_storage(repo_name):

    def git_annex_remote(remote_name,target,prefix):
        """
        Creates a git annex remote configuration for 'deic storage' using rclone.
        """
        remote_name = "deic storage"
        target = "dropbox-for-friends"  # Change this to your actual target as needed
        prefix = "my_awesome_dataset"  # Change this to your desired prefix

        # Construct the command
        command = [
            'git', 'annex', 'initremote', remote_name,
            'type=external', 'externaltype=rclone',
            'chunk=50MiB', 'encryption=none',
            'target=' + target, 'prefix=' + prefix
        ]

        try:
            # Execute the command
            subprocess.run(command, check=True)
            print(f"Git annex remote '{remote_name}' created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to create git annex remote: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    rclone_remote()
    git_annex_remote("deic storage","deic storage",repo_name)

def datalad_local_storage(repo_name):

    def get_remote_path(repo_name):
        """
        Prompt the user to provide the path to a DVC remote storage folder. 
        If `folder_path` already ends with `repo_name` and exists, an error is raised.
        Otherwise, if `folder_path` exists but does not end with `repo_name`, 
        it appends `repo_name` to `folder_path` to create the required directory.

        Parameters:
        - repo_name (str): The name of the repository to ensure at the end of `folder_path`.

        Returns:
        - str: Finalized path to DVC remote storage if valid, or None if an error occurs.
        """
        # Prompt the user for the folder path
        folder_path = input("Please enter the path to Datalad emote storage (ria):").strip()
        
        folder_path = os.path.abspath(folder_path)

        # Attempt to create folder_path if it does not exist
        if not os.path.isdir(folder_path):
            try:
                os.makedirs(folder_path, exist_ok=True)
                print(f"The path '{folder_path}' did not exist and was created.")
            except OSError as e:
                print(f"Failed to create the path '{folder_path}': {e}")
                return None
        
        # Check if folder_path already ends with repo_name
        if folder_path.endswith(repo_name):
            # Check if it already exists as a directory
            if os.path.isdir(folder_path):
                print(f"The path '{folder_path}' already exists with '{repo_name}' as the final folder.")
                return None  # Error out if the path already exists
        else:
            # Append repo_name to folder_path if it doesn’t end with it
            folder_path = os.path.join(folder_path, repo_name)
            try:
                # Create the repo_name directory if it doesn't exist
                os.makedirs(folder_path, exist_ok=True)
                print(f"Created directory: {folder_path}")
            except OSError as e:
                print(f"Failed to create the path '{folder_path}': {e}")
                return None

        # Return the finalized path
        return folder_path

    datalad_remote = get_remote_path(repo_name)
    if datalad_remote:
        subprocess.run(["datalad", "create-sibling-ria","-s",repo_name,"--new-store-ok",f"ria+file//{remote_storage}"], check=True)

def install_rclone(install_path):
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


import os
import subprocess
import sys
import platform
import zipfile
import urllib.request
import importlib
import shutil

required_libraries = ['requests'] 
for lib in required_libraries:
    try:
        importlib.import_module(lib)
    except ImportError:
        print(f"Installing {lib}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])

import requests

def is_installed(executable: str = None, name: str = None):
    # Check if both executable and name are provided as strings
    if not isinstance(executable, str) or not isinstance(name, str):
        raise ValueError("Both 'executable' and 'name' must be strings.")
    
    # Check if the executable is on the PATH
    path = shutil.which(executable)
    if path:
        return True
    else: 
        print(f"{name} is not on Path")
        return False
  
def setup_version_control(version_control,remote_storage,repo_platform,repo_name):
    """Handle repository creation and log-in based on selected platform."""

    if version_control == None:
        return
    elif version_control == "Git":
        if not _setup_git(version_control,repo_platform):
            return
    if version_control == "Datalad":
        _setup_datalad(version_control,remote_storage,repo_platform,repo_name)
    elif version_control == "DVC":
        _setup_dvc(version_control,remote_storage,repo_platform,repo_name)

def _set_to_path(path_to_set):
    """Set the specified path to the user-level PATH, requesting admin privileges on Windows if needed."""

    if platform.system() == "Windows":
        try:
            # Command to check if the path is in the user PATH
            check_command = f'$currentPath = [System.Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::User); $currentPath -notlike "*{path_to_set}*"'
            is_not_in_path = subprocess.check_output(['powershell', '-Command', check_command], text=True).strip()
            
            # If the path is not in PATH, add it with admin privileges
            if is_not_in_path == "True":
                add_command = (
                    f"Start-Process powershell -Verb runAs -ArgumentList "
                    f"'[System.Environment]::SetEnvironmentVariable(\"Path\", "
                    f"[System.Environment]::GetEnvironmentVariable(\"Path\", "
                    f"[System.EnvironmentVariableTarget]::User) + \";{path_to_set}\", "
                    f"[System.EnvironmentVariableTarget]::User)'"
                )
                subprocess.run(['powershell', '-Command', add_command], check=True)
                print(f"Added {path_to_set} to user PATH with admin rights.")
            else:
                print(f"{path_to_set} is already in the user PATH.")
                
        except subprocess.CalledProcessError as e:
            print(f"Failed to update PATH on Windows: {e}")

    elif platform.system() in ["Linux", "Darwin"]:  # Darwin is macOS
        shell_config_file = os.path.expanduser("~/.bashrc")
        if os.path.exists(os.path.expanduser("~/.zshrc")):
            shell_config_file = os.path.expanduser("~/.zshrc")
        
        # Check if the PATH is already set
        with open(shell_config_file, "r") as file:
            lines = file.readlines()
        
        if f'export PATH="$PATH:{path_to_set}"' not in ''.join(lines):
            with open(shell_config_file, "a") as file:
                file.write(f'\nexport PATH="$PATH:{path_to_set}"\n')
            print(f"Added {path_to_set} to PATH in {shell_config_file}. Please run 'source {shell_config_file}' or restart your terminal to apply changes.")
        else:
            print(f"{path_to_set} is already in the user PATH in {shell_config_file}.")
    
    else:
        print("Unsupported operating system. PATH not modified.")

def _setup_git(version_control,repo_platform):
     
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
        if is_installed('git','Git'):
            return True 
        
        try:
            system = platform.system().lower()

            if system == "windows":
                if install_path is None:
                    print("Please provide an install path for Windows installation.")
                    return False
                
                # Define the installer download location one level up from the install_path
                download_dir = os.path.dirname(install_path)
                installer_name = "Git-latest-64-bit.exe"
                installer_path = os.path.join(download_dir, installer_name)

                # Download Git installer for Windows
                url = f"https://github.com/git-for-windows/git/releases/latest/download/{installer_name}"
                print(f"Downloading Git installer from {url} to {download_dir}...")
                urllib.request.urlretrieve(url, installer_path)
                print("Download complete.")

                # Silent installation command
                install_command = [
                    installer_path, "/VERYSILENT", f"/DIR={install_path}", "/NORESTART"
                ]

                # Run the installation
                subprocess.run(install_command, check=True)

                # Add Git to PATH
                git_bin_path = os.path.join(install_path, "bin")
                os.environ["PATH"] += os.pathsep + git_bin_path

    
                # Verify installation
                if is_installed('git','Git'):
                    print("Git installation complete and added to PATH.")
                    return True
                else:
                    print("Failed to verify Git installation.")
                    return False

            elif system == "linux":
                # Install Git on Linux using apt
                print("Installing Git on Linux using 'sudo apt install git-all'...")
                install_command = ["sudo", "apt", "install", "-y", "git-all"]

                # Run the installation
                subprocess.run(install_command, check=True)

                # Verify installation
                if is_installed('git','Git'):
                    print("Git installation complete.")
                    return True
                else:
                    print("Failed to verify Git installation.")
                    return False

            elif system == "darwin":  # macOS
                # Attempt to install Git using Xcode Command Line Tools
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

        except Exception as e:
            print(f"Failed to install Git: {e}")
            return False

        finally:
            # Clean up by removing the installer file on Windows
            if system == "windows" and 'installer_path' in locals() and os.path.exists(installer_path):
                os.remove(installer_path)
                print(f"Installer {installer_name} has been removed from {download_dir}.")

    def check_git_config():
        """
        Check if Git is configured with user.name and user.email. If not, prompt the user for this information.

        Args:
        - check: Flag to indicate whether to check and configure Git.

        Returns:
        - bool: True if Git is configured, False otherwise.
        """
        try:
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
                return True, current_name, current_email # Return True if configured
            else:
                print("Git is not fully configured.")
                return False, None, None   # Return False if Git is not fully configured

        except subprocess.CalledProcessError as e:
            print(f"Git configuration check failed: {e}")
            return False, None, None   # Return False if subprocess fails
        except Exception as e:    
            print(f"Unexpected error: {e}")
            return False, None, None   # Return False for any other unexpected errors

    def setup_git_config(git_name,git_email):
        """
        Prompts the user for their name and email, then configures Git with these details.

        Returns:
        - bool: True if the configuration is successful, False otherwise.
        """
        try:
            # Prompt user for name and email
            git_name = input("Enter your Git user name: ").strip()
            git_email = input("Enter your Git user email: ").strip()

            # Check if inputs are valid
            if not git_name or not git_email:
                print("Both name and email are required.")
                return False,git_name,git_email

            # Configure Git user name and email globally
            subprocess.run(["git", "config", "--global", "user.name", git_name], check=True)
            subprocess.run(["git", "config", "--global", "user.email", git_email], check=True)

            print(f"Git configured with name: {git_name} and email: {git_email}")
            return True,git_name,git_email
        except subprocess.CalledProcessError as e:
            print(f"Failed to configure Git: {e}")
            return False,git_name,git_email
            
    def git_init(repo_platform):
  
        # Initialize a Git repository if one does not already exist
        if not os.path.isdir(".git"):
            subprocess.run(["git", "init"], check=True)
            print("Initialized a new Git repository.")

        if repo_platform == "GitHub":
            # Rename branch to 'main' if it was initialized as 'master'
            subprocess.run(["git", "branch", "-m", "master", "main"], check=True)

        subprocess.run(["git", "add", "."], check=True)    
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
        print("Created an initial commit.")
        return True

    def git_to_env(git_name, git_email,env_file=".env"):
        """
        Adds Git username and email to the specified .env file. 
        Creates the file if it doesn't exist.
        
        Parameters:
        - env_file (str): The path to the .env file. Default is ".env".
        """ 
        if not git_name or not git_email:
            print("Failed to retrieve Git user information. Make sure Git is configured.")
            return
        
        # Check if .env file exists and create if not
        if not os.path.exists(env_file):
            print(f"{env_file} does not exist. Creating a new one.")
            with open(env_file, 'w') as file:
                file.write("# Created .env file for storing Git user credentials.\n")
        
        # Write the credentials to the .env file
        with open(env_file, 'a') as file:
            file.write(f"GIT_USER_NAME={git_name}\n")
            file.write(f"GIT_USER_EMAIL={git_email}\n")
        
        print(f"Git user information added to {env_file}")

    if install_git():  
        check, git_name, git_email = check_git_config()

        if not check:
            check, git_name, git_email = setup_git_config(git_name, git_email)
        
        if check and version_control == "Git":  
            check = git_init(repo_platform)
        
        if check:
            git_to_env(git_name, git_email)    
        
        return check
    else:
        return False
        
def _setup_dvc(version_control,remote_storage,repo_platform,repo_name):

    def install_dvc():
        """
        Install DVC using pip.
        """
        if is_installed('dvc','DVC'):
            return True
        try:
            # Install DVC via pip
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'dvc[all]'])
            print("DVC has been installed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"An error occurred during DVC installation: {e}")
            return False
        except FileNotFoundError:
            print("Python or pip was not found. Please ensure Python and pip are installed and in your PATH.")
            return False

    def dvc_init(remote_storage,repo_platform,repo_name):
    
        # Initialize a Git repository if one does not already exist
        if not os.path.isdir(".git"):
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
    
        if repo_platform == "GitHub":
            # Rename branch to 'main' if it was initialized as 'master'
            subprocess.run(["git", "branch", "-m", "master", "main"], check=True)

        subprocess.run(["git", "add", "."], check=True)    
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
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
    
    # Install Git
    if not _setup_git(version_control,repo_platform):
        return
    
    # Install datalad
    if not install_dvc():
        return
    dvc_init(remote_storage,repo_platform,repo_name)
    
def _setup_datalad(version_control,remote_storage,platform,repo_name):

    def install_datalad():   
            if not is_installed('datalad','Datalad'):
                try:
                    if not shutil.which('datalad-installer'):
                        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'datalad-installer'])
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'datalad'])
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyopenssl','--upgrade']) 
                except subprocess.CalledProcessError as e:
                    print(f"An error occurred: {e}")
                    return False
                except FileNotFoundError:
                    print("One of the required commands was not found. Please ensure Python, pip, and Git are installed and in your PATH.")
                    return False           
            return True
    def install_git_annex():
        if not is_installed('git-annex','Git-Annex'):
            try:
                if not shutil.which('datalad-installer'):
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'datalad-installer'])
                subprocess.check_call("echo y | datalad-installer git-annex -m datalad/git-annex:release", shell=True)
            except subprocess.CalledProcessError as e:
                print(f"Error during git-annex installation: {e}")
                return False
            except Exception as e:
                print(f"Unexpected error: {e}")
                return False 
        subprocess.check_call(['git', 'config', '--global', 'filter.annex.process', 'git-annex filter-process'])
        print("git-annex installed successfully.")
        return True
     
    def setup_rclone(bin_folder):
        """Download and extract rclone to the specified bin folder."""

        def download_rclone(bin_folder):
            system = platform.system()
            
            # Set the URL and executable name based on the OS
            if system == "Windows":
                url = "https://downloads.rclone.org/rclone-current-windows-amd64.zip"
                rclone_executable = "rclone.exe"
            elif system in ["Linux", "Darwin"]:  # "Darwin" is the system name for macOS
                url = "https://downloads.rclone.org/rclone-current-linux-amd64.zip" if system == "Linux" else "https://downloads.rclone.org/rclone-current-osx-amd64.zip"
                rclone_executable = "rclone"
            else:
                print(f"Unsupported operating system: {system}. Please install rclone manually.")
                return

            # Create the bin folder if it doesn't exist
            os.makedirs(bin_folder, exist_ok=True)

            # Download rclone
            local_zip = os.path.join(bin_folder, "rclone.zip")
            print(f"Downloading rclone for {system} to {local_zip}...")
            response = requests.get(url)
            if response.status_code == 200:
                with open(local_zip, 'wb') as file:
                    file.write(response.content)
                print("Download complete.")
            else:
                print("Failed to download rclone. Please check the URL.")
                return

            # Extract the rclone executable
            print("Extracting rclone...")
            with zipfile.ZipFile(local_zip, 'r') as zip_ref:
                zip_ref.extractall(bin_folder)

            # Clean up by deleting the zip file
            os.remove(local_zip)
            print(f"rclone installed successfully at {os.path.join(bin_folder, rclone_executable)}.")

            rclone_path = os.path.abspath(os.path.join(bin_folder, rclone_executable))

            return rclone_path

        def clone_git_annex_remote_rclone(bin_folder):
            """Clone the git-annex-remote-rclone repository to the specified bin folder."""
            repo_url = "https://github.com/git-annex-remote-rclone/git-annex-remote-rclone.git"
            repo_name = os.path.basename(repo_url).replace('.git', '')
            repo_path = os.path.join(bin_folder, repo_name)

            # Create the bin folder if it doesn't exist
            os.makedirs(bin_folder, exist_ok=True)

            # Check if the repository already exists
            if os.path.isdir(repo_path):
                print(f"The repository '{repo_name}' already exists in {bin_folder}.")
            else:
                print(f"Cloning {repo_url} into {repo_path}...")
                subprocess.run(["git", "clone", repo_url, repo_path], check=True)
                print(f"Repository cloned successfully to {repo_path}.")

            repo_path = os.path.abspath(repo_path)  # Convert to absolute path
            return repo_path
        
        if not is_installed('rclone','Rclone'):
            rclone_path = download_rclone(bin_folder)
            _set_to_path(rclone_path)

        # Clone https://github.com/git-annex-remote-rclone/git-annex-remote-rclone.git
        if not is_installed('git-annex-remote-rclone','git-annex-remote-rclone'):
            repo_path = clone_git_annex_remote_rclone(bin_folder)
            _set_to_path(repo_path)

    def datalad_create():

        def unlock_files(files_to_unlock):
            attributes_file = ".gitattributes"
            with open(attributes_file, "a") as f:
                for file in files_to_unlock:
                    f.write(f"{file} annex.largefiles=nothing\n")

        # Initialize a Git repository if one does not already exist
        if not os.path.isdir(".datalad"):
            files_to_unlock = ["README.md", "LICENSE", "hardware_information.txt"]
            subprocess.run(["datalad", "create","--force"], check=True)
            unlock_files(files_to_unlock )
            subprocess.run(["datalad", "save", "-m", "Initial commit"], check=True)
        else:
            print('I is already a Datalad project')
            return 
        
    def datalad_deic_storage(repo_name):

        def git_annex_remote(remote_name,target,prefix):
            """
            Creates a git annex remote configuration for 'deic-storage' using rclone.
            """
            remote_name = "deic-storage"
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

        def rclone_remote(email,password):

                # Construct the command
            command = [
                    'rclone', 'config', 'create', 'deic-storage', 'sftp',
                    'host', 'sftp.storage.deic.dk',
                    'port', '2222',
                    'user', email,
                    'pass', password
            ]
        
            try:
                # Execute the command
                subprocess.run(command, check=True)
                print("Rclone remote 'deic-storage' created successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Failed to create rclone remote: {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

        email = input("Please enter email to Deic Storage: ").strip()
        password = input("Please enter password to Deic Storage: ").strip()
  
        rclone_remote(email,password)
        git_annex_remote("deic-storage","deic-storage",repo_name)

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

    # Install Git
    if not _setup_git(version_control,platform):
        return
    
    # Install datalad
    if not install_datalad():
        return
    
    # Install git-annex
    if not install_git_annex():
        return

    datalad_create()

    if remote_storage == "Local Path":
        datalad_local_storage(repo_name)
    elif remote_storage in ["Dropbox", "Deic Storage"]:
        setup_rclone("bin")
        datalad_deic_storage(repo_name)

version_control = "{{cookiecutter.version_control}}"
repo_name = "{{ cookiecutter.repo_name }}"
repo_platform = "{{cookiecutter.repository_platform }}"
remote_storage = "{{cookiecutter.remote_storage}}"

# Setup Version Control
setup_version_control(version_control,remote_storage,repo_platform,repo_name)


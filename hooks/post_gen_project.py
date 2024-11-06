import os
import subprocess
import sys
import platform
import requests
import zipfile


def get_hardware_info():
    """
    Extract hardware information and save it to a file.
    Works on Windows, Linux, and macOS.
    """
    system = platform.system()
    command = ""

    if system == "Windows":
        command = "systeminfo"
    elif system == "Linux":
        command = "lshw -short"  # Alternative: "dmidecode"
    elif system == "Darwin":  # macOS
        command = "system_profiler SPHardwareDataType"
    else:
        print("Unsupported operating system.")
        return

    try:
        # Execute the command and capture the output
        hardware_info = subprocess.check_output(command, shell=True, text=True)

        # Save the hardware information to a file
        with open("hardware_information.txt", "w") as file:
            file.write(hardware_info)

        print("Hardware information saved to hardware_information.txt")

    except subprocess.CalledProcessError as e:
        print(f"Error retrieving hardware information: {e}")

def create_virtual_environment():
    """
    Create a virtual environment for Python or R based on the specified programming language.
    
    Parameters:
    - repo_name: str, name of the virtual environment.
    - programming_language: str, 'python' or 'R' to specify the language for the environment.
    """

    def get_file_path():
        """
        Prompt the user to provide the path to a .yml or .txt file and check if the file exists and is the correct format.
        
        Returns:
        - str: Validated file path if the file exists and has the correct extension.
        """

        # Prompt the user for the file path
        file_path = input("Please enter the path to a .yml or .txt file: ").strip()
            
        # Check if the file exists
        if not os.path.isfile(file_path):
            print("The file does not exist. Please try again.")
            return None
            
        # Check the file extension
        _, file_extension = os.path.splitext(file_path)
        if file_extension.lower() not in {'.yml', '.txt'}:
            print("Invalid file format. The file must be a .yml or .txt file.")
            return None
        
        # If both checks pass, return the valid file path
        return file_path
        
    def check_conda():
        """Check if conda is installed."""
        try:
            subprocess.run(['conda', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def create_conda_env(env_name, programming_language):
        """Create a conda environment."""
        subprocess.run(['conda', 'create', '--name', env_name, programming_language, '--yes'], check=True)
        print(f'Conda environment "{env_name}" for {programming_language} created successfully.')

    def create_from_yml(env_name=None,yml_file='environment.yml'):
        """
        Create a conda environment from an environment.yml file with a specified name.
        
        Parameters:
        - env_file: str, path to the environment YAML file. Defaults to 'environment.yml'.
        - env_name: str, optional name for the new environment. If provided, overrides the name in the YAML file.
        """
        try:
            # Construct the command
            command = ['conda', 'env', 'create', '-f', yml_file]
            if env_name:
                command.extend(['--name', env_name])  # Add the specified name

            # Run the command
            subprocess.run(command, check=True)
            print(f"Conda environment '{env_name or 'default name in YAML'}' created successfully from {yml_file}.")

        except subprocess.CalledProcessError as e:
            print(f"Failed to create conda environment: {e}")
        except FileNotFoundError:
            print("Conda is not installed or not found in the system path.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def generate_yml(env_name,requirements_path):
        """Generate an environment.yml file using a requirements.txt file."""
        yml_content = f"""
            name: {env_name}
            channels:
            - conda-forge
            dependencies:
            - python>=3.5
            - anaconda
            - pip
            - pip:
                - -r file:{requirements_path}
            """
        with open('environment.yml', 'w') as yml_file:
            yml_file.write(yml_content)
        print(f"Generated environment.yml file using {requirements_path}.")

    def create_venv_env(env_name):
        """Create a Python virtual environment using venv."""
        subprocess.run([sys.executable, '-m', 'venv', env_name], check=True)
        print(f'Venv environment "{repo_name}" for Python created successfully.')

    def create_virtualenv_env(env_name):
        """Create a Python virtual environment using virtualenv."""
        subprocess.run(['virtualenv', env_name], check=True)
        print(f'Virtualenv environment "{repo_name}" for Python created successfully.')

    def export_conda_env(env_name, output_file='environment.yml'):
        """
        Export the details of a conda environment to a YAML file.
        
        Parameters:
        - env_name: str, name of the conda environment to export.
        - output_file: str, name of the output YAML file. Defaults to 'environment.yml'.
        """
        try:
            # Use subprocess to run the conda export command
            with open(output_file, 'w') as f:
                subprocess.run(['conda', 'env', 'export', '-n', env_name], stdout=f, check=True)
            
            print(f"Conda environment '{env_name}' exported to {output_file}.")

        except subprocess.CalledProcessError as e:
            print(f"Failed to export conda environment: {e}")
        except FileNotFoundError:
            print("Conda is not installed or not found in the system path.")
        except Exception as e:
            print(f"An error occurred: {e}")
                

    repo_name = "{{ cookiecutter.repo_name }}"
    virtual_environment = "{{ cookiecutter.virtual_environment}}"

    if virtual_environment.lower() not in ['python','r','environment.yaml','requirements.txt']:
        return
    
    # Ask for user confirmation
    confirm = input(f"Do you want to create a virtual environment named '{repo_name}' for/from {virtual_environment}? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Virtual environment creation canceled.")
        return
    
    if virtual_environment.lower() in ['environment.yaml','requirements.txt']:
        env_file = get_file_path()
        if env_file is None:
            return

    if virtual_environment.lower() in ['python','r','environment.yaml','requirements.txt']:
        if check_conda():
            if virtual_environment.lower() in ['python','r']:
                create_conda_env(repo_name,virtual_environment)
            elif virtual_environment.lower() in ['environment.yaml']:
                create_from_yml(repo_name,env_file)
            elif virtual_environment.lower() in ['requirements.txt']:
                generate_yml(repo_name,env_file)
                create_from_yml(repo_name,env_file)
            export_conda_env(repo_name)
        elif virtual_environment.lower() == 'python':
            if subprocess.call(['which', 'virtualenv']) == 0:
                create_virtualenv_env(repo_name)
            else:
                create_venv_env(repo_name)
        elif virtual_environment.lower() == 'r': 
            print('Conda is not installed. Please install it to create an {programming_language}  environment.')

def install_requirements():
    """Install the required packages from requirements.txt."""
    # Get the directory of the current script (which is in hooks)
    hook_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_path = os.path.join(hook_dir, '..', 'requirements.txt')

    try:
        subprocess.run(["pip", "install", "-r", requirements_path], check=True)
    except FileNotFoundError:
        print("requirements.txt not found. Please ensure it is located in the project root directory.")
        exit(1)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while trying to install requirements: {e}")
        exit(1)

def create_repository():
    """Handle repository creation and log-in based on selected platform."""
     
    def github_login(username,privacy_setting,repo_name,description):
        
        # Login if necessary
        login_status = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
        if "You are not logged into any GitHub hosts" in login_status.stderr:
            print("Not logged into GitHub. Attempting login...")
            subprocess.run(["gh", "auth", "login"], check=True)

        # Create the GitHub repository
        subprocess.run([
            "gh", "repo", "create", f"{username}/{repo_name}",
            f"--{privacy_setting}", "--description", description, "--source", ".", "--push"
        ])

    def gitlab_login(username,privacy_setting,repo_name,description):  # FIX ME !! Not working

        # Login if necessary
        login_status = subprocess.run(["glab", "auth", "status"], capture_output=True, text=True)
        if "Not logged in" in login_status.stderr:
            print("Not logged into GitLab. Attempting login...")
            subprocess.run(["glab", "auth", "login"], check=True)

        # Create the GitLab repository
        subprocess.run([
            "glab", "repo", "create", f"{username}/{repo_name}",
            f"--{privacy_setting}", "--description", description, "--source", ".", "--push"
        ])
    
    repo_name = "{{ cookiecutter.repo_name }}"
    description = "{{ cookiecutter.description }}"
    platform = "{{ cookiecutter.repository_platform }}"
    version_control = "{{cookiecutter.version_control}}"

    if version_control == None or not os.path.isdir(".git"):
        return
    elif platform in ["GitHub", "GitLab"]:
        username = input(f"Enter your {platform} username: ").strip()
        privacy_setting = input("Select the repository visibility (private/public): ").strip().lower()
        
        if privacy_setting not in ["private", "public"]:
            print("Invalid choice. Defaulting to 'private'.")
            privacy_setting = "private"

        if platform == "GitHub":
            github_login(username,privacy_setting,repo_name,description)
        elif platform == "GitLab":
            gitlab_login(username,privacy_setting,repo_name,description)

def setup_version_control():
    """Handle repository creation and log-in based on selected platform."""

    platform = "{{cookiecutter.repository_platform }}"
    version_control = "{{cookiecutter.version_control}}"
    remote_storage = "{{cookiecutter.remote_storage}}"
    repo_name = "{{ cookiecutter.repo_name }}"
    
    if version_control == None:
        return
    elif version_control == "Git":
        check = setup_git(version_control,platform)
        if check is False:
            return
    if version_control == "Datalad":
        setup_datalad(version_control,remote_storage,platform,repo_name)
    elif version_control == "DVC":
        setup_dvc(version_control,remote_storage,platform,repo_name)
    
def setup_git(version_control,platform):
    
    def is_git_installed():
        try:
            # Run 'git --version' and capture the output
            output = subprocess.check_output(['git', '--version'], stderr=subprocess.STDOUT)
            # Decode the output from bytes to string and check if it contains 'git version'
            if 'git version' in output.decode('utf-8'):
                return True
        except FileNotFoundError:
            print("Git is not installed or not in the system PATH.")
        except subprocess.CalledProcessError:
            print("An error occurred while checking Git version.")
        return False
    
    def git_init(platform):
        # Initialize a Git repository if one does not already exist
        if not os.path.isdir(".git"):
            subprocess.run(["git", "init"], check=True)
            print("Initialized a new Git repository.")

        if platform == "GitHub":
            # Rename branch to 'main' if it was initialized as 'master'
            subprocess.run(["git", "branch", "-m", "master", "main"], check=True)

        subprocess.run(["git", "add", "."], check=True)    
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
        print("Created an initial commit.")

    check = is_git_installed()
    if check and version_control == "Git":
        git_init(platform)
        
    return check
    
def setup_dvc(version_control,remote_storage,platform,repo_name):

    def is_dvc_installed():
        """
        Check if DVC is installed on the system and return its version.

        Returns:
        str: DVC version if installed, otherwise an empty string.
        """
        try:
            # Run 'dvc --version' and capture the output
            results = subprocess.check_output(['dvc', '--version'], stderr=subprocess.STDOUT)
            return True
        except FileNotFoundError:
            print("DVC is not installed or not in the system PATH.")
        except subprocess.CalledProcessError:
            print("An error occurred while checking DVC version.")
        return False
    
    def install_dvc():
        """
        Install DVC using pip.
        """
        try:
            # Install DVC via pip
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'dvc','dvc-ssh'])
            print("DVC has been installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred during DVC installation: {e}")
        except FileNotFoundError:
            print("Python or pip was not found. Please ensure Python and pip are installed and in your PATH.")

    def dvc_init(remote_storage,platform,repo_name):
    
        # Initialize a Git repository if one does not already exist
        if not os.path.isdir(".git"):
            subprocess.run(["git", "init"], check=True)

        # Init dvc
        if not os.path.isdir(".dvc"):
            subprocess.run(["dvc", "init"], check=True)

        # Add dvc remote storage
        if remote_storage == "Local Path":
            dvc_local_storage(repo_name)
        elif remote_storage in ["Dropbox","Deic Storage"]:
            dvc_deic_storage(repo_name)

        folders = ["data","reports","docs"]
        for folder in folders:
            subprocess.run(["dvc", "add",folder], check=True)
    
        if platform == "GitHub":
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

    check = setup_git(version_control,platform)

    if check is False:
        return

    check = is_dvc_installed()

    if check is False:
            install_dvc()

    dvc_init(remote_storage,platform,repo_name)
    
def setup_datalad(version_control,remote_storage,platform,repo_name):

    def is_datalad_installed():
        try:
            # Run 'datalad --version' and capture the output
            output = subprocess.check_output(['datalad', '--version'], stderr=subprocess.STDOUT)
            # Decode the output from bytes to string and check if it contains 'datalad'
            if 'datalad' in output.decode('utf-8'):
                return True
        except FileNotFoundError:
            print("DataLad is not installed or not in the system PATH.")
        except subprocess.CalledProcessError:
            print("An error occurred while checking DataLad version.")
        return False

    def is_rclone_installed():
        """
        Check if rclone is installed on the system and return its version.

        Returns:
        str: rclone version if installed, otherwise an empty string.
        """
        try:
            # Run 'rclone --version' and capture the output
            result = subprocess.check_output(['rclone', '--version'], stderr=subprocess.STDOUT)
            return True
        except FileNotFoundError:
            print("rclone is not installed or not in the system PATH.")
        except subprocess.CalledProcessError as e:
            print("An error occurred while checking rclone version:")
        return False
    
    def is_git_annex_remote_rclone_installed():
        """
        Check if git-annex-remote-rclone is installed on the system.

        Returns:
        str: Confirmation message if installed, otherwise an empty string.
        """
        try:
            # Run 'git-annex-remote-rclone' and capture the output
            result = subprocess.check_output(['git-annex-remote-rclone'], stderr=subprocess.STDOUT)
            return True  # Decode bytes to string and strip whitespace
        except FileNotFoundError:
            print("git-annex-remote-rclone is not installed or not in the system PATH.")
        except subprocess.CalledProcessError as e:
            print("An error occurred while checking git-annex-remote-rclone:")
        return False
    
    def install_datalad():
            try:
                # Step 1: Install datalad-installer via pip
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'datalad-installer'])

                # Step 2: Install git-annex using datalad-installer
                subprocess.check_call(['datalad-installer', 'git-annex', '-m', 'datalad/git-annex:release'])

                # Step 3: Set recommended git-annex configuration for performance improvement
                subprocess.check_call(['git', 'config', '--global', 'filter.annex.process', 'git-annex filter-process'])

                # Step 4: Install DataLad with pip
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'datalad'])

            except subprocess.CalledProcessError as e:
                print(f"An error occurred: {e}")
            except FileNotFoundError:
                print("One of the required commands was not found. Please ensure Python, pip, and Git are installed and in your PATH.")           
    
    def setup_rclone(bin_folder):
        """Download and extract rclone to the specified bin folder."""

        # FIX ME !!
        def set_to_path(path_to_set):
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

        check = is_rclone_installed()
        if check is False:
            rclone_path = download_rclone(bin_folder)
            set_to_path(rclone_path)

        
        check = is_git_annex_remote_rclone_installed()
        # Clone https://github.com/git-annex-remote-rclone/git-annex-remote-rclone.git
        if check is False:
            repo_path = clone_git_annex_remote_rclone(bin_folder)
            set_to_path(repo_path)

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
                
    check = setup_git(version_control,platform)

    if check is False:
        return

    check = is_datalad_installed()

    if check is False:
            install_datalad()

    datalad_create()
    if remote_storage in ["Dropbox", "Deic Storage"]:
        print("hello")
        print(remote_storage)
        setup_rclone("bin")
        datalad_deic_storage(repo_name)


# Install requirements
#nstall_requirements()

# Create Virtual Environment
create_virtual_environment()

# Get Hardware information
get_hardware_info()

# Setup Version Control
setup_version_control()

# Create Remote Repository
create_repository()

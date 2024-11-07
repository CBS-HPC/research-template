import os
import subprocess
import sys
import platform
import requests
import zipfile
import urllib.request
import importlib


required_libraries = ['distro'] 
for lib in required_libraries:
    try:
        importlib.import_module(lib)
    except ImportError:
        print(f"Installing {lib}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])

import distro


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

def setup_virtual_environment():
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
   
    def create_venv_env(env_name):
        """Create a Python virtual environment using venv."""
        subprocess.run([sys.executable, '-m', 'venv', env_name], check=True)
        print(f'Venv environment "{repo_name}" for Python created successfully.')

    def create_virtualenv_env(env_name):
        """Create a Python virtual environment using virtualenv."""
        subprocess.run(['virtualenv', env_name], check=True)
        print(f'Virtualenv environment "{repo_name}" for Python created successfully.')
        
    repo_name = "{{ cookiecutter.repo_name }}"
    virtual_environment = "{{ cookiecutter.virtual_environment}}"

    if virtual_environment not in ['Python','R','environment.yaml','requirements.txt']:
        return
    
    # Ask for user confirmation
    confirm = input(f"Do you want to create a virtual environment named '{repo_name}' for/from {virtual_environment}? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Virtual environment creation canceled.")
        return
    
    if virtual_environment ['environment.yaml','requirements.txt']:
        env_file = get_file_path()
        if env_file is None:
            return

    if virtual_environment in ['Python','R','environment.yaml','requirements.txt']:
        check = setup_conda(virtual_environment,repo_name,env_file)

        if check is False and virtual_environment == 'Python':
            if subprocess.call(['which', 'virtualenv']) == 0:
                create_virtualenv_env(repo_name)
            else:
                create_venv_env(repo_name)
        elif virtual_environment == 'R': 
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

def setup_remote_repository():
    """Handle repository creation and log-in based on selected platform."""

    def is_gh_installed():
        try:
            # Attempt to run `gh --version` to check if GitHub CLI is installed
            result = subprocess.run(["gh", "--version"], check=True, capture_output=True, text=True)
            # If the command executes successfully, return True
            return True
        except FileNotFoundError:
            # If `gh` is not found in the system, it means GitHub CLI is not installed
            print("GitHub CLI (gh) is not installed.")
            return False
        except subprocess.CalledProcessError as e:
            # If the command fails with a non-zero exit code, return False
            print(f"Error occurred while checking GitHub CLI: {e}")
            return False
        except Exception as e:
            # Catch any unexpected errors
            print(f"Unexpected error: {e}")
            return False

    def install_gh(check):

        if check:
            return check 

        os_type = platform.system().lower()
        
        if os_type == "windows":
            installer_url = "https://github.com/cli/cli/releases/latest/download/gh_2.28.0_windows_amd64.msi"
            installer_name = "gh_installer.msi"
            try:
                # Download the installer
                subprocess.run(["curl", "-LO", installer_url], check=True)
                subprocess.run(["msiexec", "/i", installer_name, "/quiet", "/norestart"], check=True)
                print("GitHub CLI (gh) installed successfully.")
                return True
            except subprocess.CalledProcessError as e:
                print(f"Failed to install GitHub CLI: {e}")
                return False
            finally:
                if os.path.exists(installer_name):
                    os.remove(installer_name)
        
        elif os_type == "darwin":  # macOS
            try:
                # Using Homebrew to install GitHub CLI
                subprocess.run(["brew", "install", "gh"], check=True)
                print("GitHub CLI (gh) installed successfully on macOS.")
                return True
            except subprocess.CalledProcessError as e:
                print(f"Failed to install GitHub CLI on macOS: {e}")
                return False
        
        elif os_type == "linux":
            distro_name = distro.name().lower()
            if "ubuntu" in distro or "debian" in distro_name:
                command = ["sudo", "apt", "install", "gh"]
            elif "centos" in distro_name or "rhel" in distro_name:
                command = ["sudo", "yum", "install", "gh"]
            else:
                print(f"Unsupported Linux distribution: {distro_name}")
                return False
            try:
                subprocess.run(command, check=True)
                print("GitHub CLI (gh) installed successfully on Linux.")
                return True
            except subprocess.CalledProcessError as e:
                print(f"Failed to install GitHub CLI on Linux: {e}")
                return False
        else:
            print("Unsupported operating system.")
            return False

    def gh_login(check, username, privacy_setting, repo_name, description):
        if check:
            try:
                # Check if the user is logged in
                login_status = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, check=True)
                
                if "You are not logged into any GitHub hosts" in login_status.stderr:
                    print("Not logged into GitHub. Attempting login...")
                    subprocess.run(["gh", "auth", "login"], check=True)
                
                # Create the GitHub repository
                subprocess.run([
                    "gh", "repo", "create", f"{username}/{repo_name}",
                    f"--{privacy_setting}", "--description", description, "--source", ".", "--push"
                ], check=True)
                
                print(f"Repository {repo_name} created and pushed successfully.")
                return True  # Return True if everything is successful

            except subprocess.CalledProcessError as e:
                print(f"Error during GitHub CLI operation: {e}")
                print(f"Standard output: {e.stdout}")
                print(f"Standard error: {e.stderr}")
                return False  # Return False if an error occurs

            except Exception as e:
                print(f"Unexpected error: {e}")
                return False  # Return False for any unexpected errors
        else:
            print("Check flag is not set to True. Skipping GitHub login and repository creation.")
            return False  # Return False if the check flag is not True

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
    remote_repo = "{{ cookiecutter.repository_platform }}"
    version_control = "{{cookiecutter.version_control}}"

    if version_control == None or not os.path.isdir(".git"):
        return
    elif remote_repo in ["GitHub", "GitLab"]:
        username = input(f"Enter your {remote_repo} username: ").strip()
        privacy_setting = input("Select the repository visibility (private/public): ").strip().lower()
        
        if privacy_setting not in ["private", "public"]:
            print("Invalid choice. Defaulting to 'private'.")
            privacy_setting = "private"

        if remote_repo == "GitHub":
            check = is_gh_installed()
            check = install_gh(check)
            gh_login(check,username,privacy_setting,repo_name,description)
        elif remote_repo == "GitLab":
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

def setup_conda(virtual_environment,repo_name,env_file):
            
    def is_conda_installed(check = True):
        """Check if conda is installed."""
        
        if check is False:
            return check
        try:
            subprocess.run(['conda', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def install_miniconda(check,install_path):
        """
        Downloads and installs Miniconda to a specified location based on the operating system.
        
        Parameters:
        - install_path (str): The absolute path where Miniconda should be installed.

        Returns:
        - bool: True if installation is successful, False otherwise.
        """
        if check:
            return check
        
        system = platform.system().lower()
        installer_name = None
        download_dir = os.path.dirname(install_path)  # One level up from the install_path
        installer_path = None
        
        if system == "windows":
            installer_name = "Miniconda3-latest-Windows-x86_64.exe"
            url = f"https://repo.anaconda.com/miniconda/{installer_name}"
            installer_path = os.path.join(download_dir, installer_name)
            install_command = [installer_path, "/InstallationType=JustMe", f"/AddToPath=0", f"/RegisterPython=0", f"/S", f"/D={install_path}"]
            
        elif system == "darwin":  # macOS
            installer_name = "Miniconda3-latest-MacOSX-arm64.sh" if platform.machine() == "arm64" else "Miniconda3-latest-MacOSX-x86_64.sh"
            url = f"https://repo.anaconda.com/miniconda/{installer_name}"
            installer_path = os.path.join(download_dir, installer_name)
            install_command = ["bash", installer_path, "-b", "-p", install_path]
            
        elif system == "linux":
            installer_name = "Miniconda3-latest-Linux-x86_64.sh"
            url = f"https://repo.anaconda.com/miniconda/{installer_name}"
            installer_path = os.path.join(download_dir, installer_name)
            install_command = ["bash", installer_path, "-b", "-p", install_path]
            
        else:
            print("Unsupported operating system.")
            return False
        
        try:
            print(f"Downloading {installer_name} from {url} to {download_dir}...")
            urllib.request.urlretrieve(url, installer_path)
            print("Download complete.")
            
            print("Installing Miniconda...")
            subprocess.run(install_command, check=True)
            if installer_path and os.path.exists(installer_path):
                os.remove(installer_path)
            print("Miniconda installation complete.")
            return True
            
        except Exception as e:
            if installer_path and os.path.exists(installer_path):
                os.remove(installer_path)
            print(f"Failed to install Miniconda: {e}")
            return False

    def add_miniconda_to_path(check,install_path):
        """
        Adds Miniconda's bin (Linux/Mac) or Scripts (Windows) directory to the system PATH.

        Parameters:
        - install_path (str): The absolute path where Miniconda is installed.

        Returns:
        - bool: True if addition to PATH is successful, False otherwise.
        """
        if check:
            return check
    
        system = platform.system().lower()
        conda_bin_path = os.path.join(install_path, 'Scripts' if system == 'windows' else 'bin')
        
        try:
            if system == 'windows':
                subprocess.run(f'setx PATH "%PATH%;{conda_bin_path}"', shell=True, check=True)
                print("Miniconda path added to system PATH (permanent for Windows).")
            else:
                shell_profile = os.path.expanduser("~/.bashrc" if system == "linux" else "~/.zshrc")
                with open(shell_profile, "a") as file:
                    file.write(f'\n# Miniconda path\nexport PATH="{conda_bin_path}:$PATH"\n')
                os.environ["PATH"] = f"{conda_bin_path}:{os.environ['PATH']}"
                print(f"Miniconda path added to PATH. Please restart your terminal or source your {shell_profile} to apply.")
            return True
            
        except Exception as e:
            print(f"Failed to add Miniconda to PATH: {e}")
            return False

    def initialize_conda_shell(check):
        """
        Initializes Conda for the user's shell by running `conda init` and starting a new interactive shell session.

        Returns:
        - bool: True if Conda shell initialization is successful, False otherwise.
        """
        if check:
            return check
        system = platform.system().lower()

        try:
            subprocess.run(["conda", "init"], check=True)
            print("Conda shell initialization complete.")
            
            if system == "windows":
                print("Please restart your terminal to apply the changes.")
            elif system == "linux" or system == "darwin":
                print("Starting a new shell session to apply Conda setup...")
                subprocess.run(["bash", "-i"])
            return True

        except Exception as e:
            print(f"Failed to initialize Conda shell: {e}")
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
               

    install_path = "bin/miniconda"
    check = is_conda_installed()
    check = install_miniconda(check,install_path)
    check = add_miniconda_to_path(check,install_path)
    check = initialize_conda_shell(check,install_path)

    if check:
        if virtual_environment in ['Python','R']:
            create_conda_env(repo_name,virtual_environment)
        elif virtual_environment in ['environment.yaml']:
            create_from_yml(repo_name,env_file)
        elif virtual_environment in ['requirements.txt']:
            generate_yml(repo_name,env_file)
            create_from_yml(repo_name,env_file)
        export_conda_env(repo_name)
    
    return check

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
    
    def install_git(check,install_path=None):
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
        if check:
            return check 
        
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
                if is_git_installed():
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
                if is_git_installed():
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

    def check_git_config(check):
        """
        Check if Git is configured with user.name and user.email. If not, prompt the user for this information.

        Args:
        - check: Flag to indicate whether to check and configure Git.

        Returns:
        - bool: True if Git is configured, False otherwise.
        """
        if check:
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
                    return False  # Return False if we can't decode the output
                
                # Check if Git is properly configured
                if current_name and current_email:
                    print(f"Git is configured with user.name: {current_name} and user.email: {current_email}")
                    return True  # Return True if configured

                else:
                    print("Git is not fully configured.")
                    return False  # Return False if Git is not fully configured

            except subprocess.CalledProcessError as e:
                print(f"Git configuration check failed: {e}")
                return False  # Return False if subprocess fails
            except Exception as e:
                print(f"Unexpected error: {e}")
                return False  # Return False for any other unexpected errors
        else:
            print("Git configuration check skipped.")
            return False  # Return False if the check flag is not set to True
        
    def setup_git_config(check):
        """
        Prompts the user for their name and email, then configures Git with these details.

        Returns:
        - bool: True if the configuration is successful, False otherwise.
        """
        if check:
            return check
        try:
            # Prompt user for name and email
            user_name = input("Enter your Git user name: ").strip()
            user_email = input("Enter your Git user email: ").strip()

            # Check if inputs are valid
            if not user_name or not user_email:
                print("Both name and email are required.")
                return False

            # Configure Git user name and email globally
            subprocess.run(["git", "config", "--global", "user.name", user_name], check=True)
            subprocess.run(["git", "config", "--global", "user.email", user_email], check=True)

            print(f"Git configured with name: {user_name} and email: {user_email}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"Failed to configure Git: {e}")
            return False
            
    def git_init(check,version_control,platform):
        if check and version_control == "Git":  
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
    check = install_git(check,install_path=None)
    check = check_git_config(check)
    check = setup_git_config(check)
    git_init(check,version_control,platform)
        
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
            result = subprocess.check_output(["where",'git-annex-remote-rclone'], stderr=subprocess.STDOUT)
            #result = subprocess.check_output(['git-annex-remote-rclone'], stderr=subprocess.STDOUT)
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

                # Upgrading pyopenssl needed for datalad create siblings
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyopenssl','--upgrade']) 

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

    check = setup_git(version_control,platform)

    if check is False:
        return

    check = is_datalad_installed()

    if check is False:
            install_datalad()

    datalad_create()

    if remote_storage == "Local Path":
        datalad_local_storage(repo_name)
    elif remote_storage in ["Dropbox", "Deic Storage"]:
        setup_rclone("bin")
        datalad_deic_storage(repo_name)
        
# Install requirements
#nstall_requirements()

# Create Virtual Environment
setup_virtual_environment()

# Get Hardware information
get_hardware_info()

# Setup Version Control
setup_version_control()

# Create Remote Repository
setup_remote_repository()

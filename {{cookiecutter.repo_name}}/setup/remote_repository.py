import os
import subprocess
import sys
import platform
import importlib
import shutil

required_libraries = ['distro'] 
for lib in required_libraries:
    try:
        importlib.import_module(lib)
    except ImportError:
        print(f"Installing {lib}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])

import distro


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
 
    def install_gh_OLD(check):
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
            if "ubuntu" in distro_name or "debian" in distro_name:
                subprocess.run(["sudo", "apt", "update"], check=True)
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

    def install_gh(check, install_path=None):
        if check:
            return check
        
        os_type = platform.system().lower()
        
        # Function to check and create a custom install path
        def ensure_install_path(path):
            if path and not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
            return path or os.getcwd()  # Default to current directory if no install_path is given

        install_path = ensure_install_path(install_path)

        if os_type == "windows":
            installer_url = "https://github.com/cli/cli/releases/latest/download/gh_2.28.0_windows_amd64.msi"
            installer_name = "gh_installer.msi"
            try:
                # Download the installer
                subprocess.run(["curl", "-LO", installer_url], check=True)
                
                # Install and specify the custom directory
                subprocess.run(["msiexec", "/i", installer_name, "/quiet", "/norestart", f"INSTALLDIR={install_path}"], check=True)
                print(f"GitHub CLI (gh) installed successfully to {install_path}.")
                return True
            except subprocess.CalledProcessError as e:
                print(f"Failed to install GitHub CLI: {e}")
                return False
            finally:
                if os.path.exists(installer_name):
                    os.remove(installer_name)

        elif os_type == "darwin":  # macOS
            try:
                # Using Homebrew to install GitHub CLI with a custom install path
                subprocess.run(["brew", "install", "gh", "--prefix", install_path], check=True)
                print(f"GitHub CLI (gh) installed successfully on macOS to {install_path}.")
                return True
            except subprocess.CalledProcessError as e:
                print(f"Failed to install GitHub CLI on macOS: {e}")
                return False

        elif os_type == "linux":
            distro_name = distro.name().lower()
            
            # Install GitHub CLI using package manager
            if "ubuntu" in distro_name or "debian" in distro_name:
                subprocess.run(["sudo", "apt", "update"], check=True)
                command = ["sudo", "apt", "install", "-y", "gh"]
            elif "centos" in distro_name or "rhel" in distro_name:
                command = ["sudo", "yum", "install", "-y", "gh"]
            else:
                print(f"Unsupported Linux distribution: {distro_name}")
                return False
            
            try:
                subprocess.run(command, check=True)
                print(f"GitHub CLI (gh) installed successfully on Linux.")

                # Move the installed binary to the custom install path
                gh_location = shutil.which("gh")
                if gh_location:
                    shutil.copy(gh_location, install_path)
                    os.chmod(os.path.join(install_path, "gh"), 0o755)
                    print(f"GitHub CLI (gh) moved to {install_path}.")
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
                subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, check=True)
            except Exception as e:
                try:
                    subprocess.run(["gh", "auth", "login"], check=True)
                except Exception as e:
                    print(f"'gh auth login' failed: {e}")
                    return False, None, None  # Return False for any unexpected errors
            try:    
                # Create the GitHub repository
                subprocess.run([
                    "gh", "repo", "create", f"{username}/{repo_name}",
                    f"--{privacy_setting}", "--description", description, "--source", ".", "--push"
                ], check=True)
                
                print(f"Repository {repo_name} created and pushed successfully.")
                return True, username,repo_name   # Return True if everything is successful
            except Exception as e:
                print(f"Failed to create '{username}/{repo_name}' on Github")
                return False, None, None
        else:
            return False, None, None  

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
    
    def gh_to_env_file(check,username,repo_name, env_file=".env"):
        """
        Adds GitHub username and token from `gh auth status` to the .env file. If the file does not exist,
        it will be created.
        
        Parameters:
        - env_file (str): The path to the .env file. Default is ".env".
        """
        
        def get_gh_token():
            try:
                # Run the command to get the token
                result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
                return result.stdout.strip()  # Returns the token
            except subprocess.CalledProcessError as e:
                print(f"Failed to get GitHub token: {e}")
                return None
    
        if check:
    
            token = get_gh_token()
            
            if not username or not token:
                print("Failed to retrieve GitHub credentials. Make sure you're logged in to GitHub CLI.")
                return
            
            # Check if .env file exists
            if not os.path.exists(env_file):
                print(f"{env_file} does not exist. Creating a new one.")
            
            # Write the credentials to the .env file
            with open(env_file, 'a') as file:
                file.write(f"GITHUB_USERNAME={username}\n")
                file.write(f"GITHUB_REPO_NAME={repo_name}\n")
                if token:
                    file.write(f"GITHUB_TOKEN={token}\n")
        
        print(f"GitHub username and token added to {env_file}")

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
            check, username, repo_name = gh_login(check,username,privacy_setting,repo_name,description)
            gh_to_env_file(check,username,repo_name)

        elif remote_repo == "GitLab":
            gitlab_login(username,privacy_setting,repo_name,description)


# Create Remote Repository
setup_remote_repository()


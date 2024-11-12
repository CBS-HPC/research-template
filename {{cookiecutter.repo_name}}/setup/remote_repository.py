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

    def install_gh(install_path=None, check=False):
        """
        Install GitHub CLI (gh) on Windows, macOS, or Linux. Optionally, copy the `gh`
        binary to a custom install path if already installed and add it to the system PATH.

        Parameters:
        - install_path (str or None): Path to copy the `gh` binary. If None, it skips the copying process.
        - check (bool): If True, checks if `gh` is already installed and skips installation.
        """
        if check:
            return check

        os_type = platform.system().lower()
        
        # Function to copy the `gh` binary to a custom install path and add it to PATH
        def copy_gh_to_bin():
            gh_location = shutil.which("gh")
            
            if gh_location is None:
                print("GitHub CLI (gh) not found.")
                return False
            
            try:
                # Ensure the custom path exists
                os.makedirs(install_path, exist_ok=True)
                
                # Copy the gh binary to the custom path
                shutil.copy(gh_location, install_path)
                
                # Make the binary executable if not already
                os.chmod(os.path.join(install_path, "gh"), 0o755)
                
                # Add custom install path to PATH if not already present
                if install_path not in os.environ["PATH"]:
                    os.environ["PATH"] += os.pathsep + install_path
                
                print(f"GitHub CLI (gh) successfully copied to {install_path}.")
                return True
            except Exception as e:
                print(f"Failed to copy GitHub CLI: {e}")
                return False

        if install_path:
            # Try to copy `gh` to the specified path if it's already installed
            if not copy_gh_to_bin():
                print("Proceeding with installation...")
            return True

        # Install GitHub CLI based on the OS type
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
            command = []
            
            # Checking if `gh` is already installed using the package manager
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
                print("GitHub CLI (gh) installed successfully on Linux.")
                
                # After installation, ensure gh is added to PATH if necessary
                gh_location = shutil.which("gh")
                if gh_location:
                    print(f"GitHub CLI (gh) located at {gh_location}.")
                    # Optionally copy to a custom location if specified
                    if install_path:
                        copy_gh_to_bin()
                
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
                    return False  # Return False for any unexpected errors
            try:    
                # Create the GitHub repository
                subprocess.run([
                    "gh", "repo", "create", f"{username}/{repo_name}",
                    f"--{privacy_setting}", "--description", description, "--source", ".", "--push"
                ], check=True)
                
                print(f"Repository {repo_name} created and pushed successfully.")
                return True  # Return True if everything is successful
            except Exception as e:
                print(f"Failed to create '{username}/{repo_name}' on Github")
                return False  
        else:
            return False  

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


# Create Remote Repository
setup_remote_repository()


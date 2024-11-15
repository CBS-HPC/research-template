import os
import subprocess
import sys
import platform
import importlib
import shutil
import requests
import zipfile
import tarfile

required_libraries = ['distro'] 
for lib in required_libraries:
    try:
        importlib.import_module(lib)
    except ImportError:
        print(f"Installing {lib}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])

import distro


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
    
def setup_remote_repository(version_control,repo_platform,repo_name,description):
    """Handle repository creation and log-in based on selected platform."""

    if version_control == None or not os.path.isdir(".git"):
        return
    elif repo_platform in ["GitHub", "GitLab"]:
        username = input(f"Enter your {repo_platform} username: ").strip()
        privacy_setting = input("Select the repository visibility (private/public): ").strip().lower()
        
        if privacy_setting not in ["private", "public"]:
            print("Invalid choice. Defaulting to 'private'.")
            privacy_setting = "private"

        if repo_platform == "GitHub":
            _setup_gh(username,privacy_setting,repo_name,description)
        elif repo_platform == "GitLab":
           _setup_glab(username,privacy_setting,repo_name,description)

def repo_login(repo_platform,username, privacy_setting, repo_name, description):
    try:
        # Check if the user is logged in
        subprocess.run([repo_platform, "auth", "status"], capture_output=True, text=True, check=True)
    except Exception as e:
        try:
            subprocess.run([repo_platform, "auth", "login"], check=True)
        except Exception as e:
            print(f"{repo_platform} auth login' failed: {e}")
            return False, None, None  # Return False for any unexpected errors
    try:    
        # Create the GitHub repository
        subprocess.run([
            repo_platform, "repo", "create", f"{username}/{repo_name}",
            f"--{privacy_setting}", "--description", description, "--source", ".", "--push"
        ], check=True)
        
        print(f"Repository {repo_name} created and pushed successfully.")
        return True, username,repo_name   # Return True if everything is successful
    except Exception as e:
        print(f"Failed to create '{username}/{repo_name}' on Github")
        return False, None, None 

def repo_to_env_file(repo_platform,username,repo_name, env_file=".env"):
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

    if repo_platform == 'gh':
        token = get_gh_token()
        tag = "GITHUB"
        token  = None
      
    elif repo_platform == 'glab':
        tag = "GITLAB"

    if not username or not token:
        print("Failed to retrieve GitHub credentials. Make sure you're logged in to GitHub CLI.")
        return
    
    # Check if .env file exists
    if not os.path.exists(env_file):
        print(f"{env_file} does not exist. Creating a new one.")
    
    # Write the credentials to the .env file
    with open(env_file, 'a') as file:
        file.write(f"{tag}_USERNAME={username}\n")
        file.write(f"{tag}_REPO_NAME={repo_name}\n")
        file.write(f"{tag}_PATH={shutil.which(repo_platform)}\n")
        if token:
            file.write(f"{tag}_TOKEN={token}\n")
    
    print(f"{tag} username and token added to {env_file}")

def _setup_glab(username,privacy_setting,repo_name,description):


    def get_glab_version():
        url = "https://gitlab.com/api/v4/projects/gitlab-org%2Fcli/releases"
        try:
            response = requests.get(url)
            response.raise_for_status()
            latest_release = response.json()[0]  # Get the latest release
            version = latest_release["tag_name"]
            return version
        except requests.RequestException as e:
            print(f"Error retrieving the latest glab version: {e}")
            return None

    def add_to_path(bin_path):
        """
        Adds the path of the glab binary to the system PATH permanently.
        """
        if os.path.exists(bin_path):
            if platform.system() == "Windows":
                # Use setx to set the environment variable permanently in Windows
                subprocess.run(["setx", "PATH", f"{bin_path};%PATH%"], check=True)
            else:
                # On macOS/Linux, you can add the path to the shell profile file
                profile_file = os.path.expanduser("~/.bashrc")  # or ~/.zshrc depending on shell
                with open(profile_file, "a") as file:
                    file.write(f'\nexport PATH="{bin_path}:$PATH"')
                print(f"Added {bin_path} to PATH. Restart the terminal or source {profile_file} to apply.")
        else:
            print(f"glab binary not found in {bin_path}, unable to add to PATH.")

    def install_glab(install_path=None):
        os_type = platform.system().lower()
        install_path = os.path.abspath(install_path) or os.getcwd()  # Default to current directory if no install_path is provided
        os.makedirs(install_path, exist_ok=True)
        version = get_glab_version()
        nversion = version.lstrip("v")
        if not version:
            print("Could not retrieve the latest version of glab.")
            return False

        # Set URL and extraction method based on OS type
        if os_type == "windows":
            glab_url = f"https://gitlab.com/gitlab-org/cli/-/releases/{version}/downloads/glab_{nversion}_windows_amd64.zip"
            glab_path = os.path.join(install_path, f"glab_{nversion}_windows_amd64.zip")
            extract_method = lambda: zipfile.ZipFile(glab_path, 'r').extractall(install_path)

        elif os_type == "darwin":  # macOS
            glab_url = f"https://gitlab.com/gitlab-org/cli/-/releases/{version}/downloads/glab_{nversion}_darwin_amd64.tar.gz"
            glab_path = os.path.join(install_path, f"glab_{nversion}_darwin_amd64.tar.gz")
            extract_method = lambda: tarfile.open(glab_path, "r:gz").extractall(install_path)

        elif os_type == "linux":
            glab_url = f"https://gitlab.com/gitlab-org/cli/-/releases/{version}/downloads/glab_{nversion}_linux_amd64.tar.gz"
            glab_path = os.path.join(install_path, f"glab_{nversion}_linux_amd64.tar.gz")
            extract_method = lambda: tarfile.open(glab_path, "r:gz").extractall(install_path)

        else:
            print(f"Unsupported operating system: {os_type}")
            return False

        # Check if glab is already downloaded and extracted
        if os.path.exists(glab_path):
            print(f"{glab_path} already exists. Skipping download.")
        else:
            try:
                # Download the glab binary
                print(f"Downloading glab for {os_type} from {glab_url}...")
                response = requests.get(glab_url, stream=True)
                response.raise_for_status()
                with open(glab_path, "wb") as f:
                    shutil.copyfileobj(response.raw, f)
                print(f"glab downloaded successfully to {glab_path}")
            except requests.RequestException as e:
                print(f"Failed to download glab for {os_type}: {e}")
                return False

        # Extract the downloaded file
        print(f"Extracting {glab_path}...")
        extract_method()

        # Add the extracted glab to the system PATH
        add_to_path(os.path.join(install_path, "bin"))

        return True

    if install_glab("bin/glab"):
                check, username, repo_name = repo_login("glab",username,privacy_setting,repo_name,description)
                if check:
                    repo_to_env_file("glab",username,repo_name)

def _setup_gh(username,privacy_setting,repo_name,description):
    
    def install_gh(install_path=None):

        if is_installed('gh',"GitHub CLI (gh)"):
            return True
        
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

    def gh_login(username, privacy_setting, repo_name, description):
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

    def gh_to_env_file(username,repo_name, env_file=".env"):
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

    if install_gh():
                check, username, repo_name = repo_login("gh",username,privacy_setting,repo_name,description)
                if check:
                    repo_to_env_file("gh",username,repo_name)

repo_name = "{{ cookiecutter.repo_name }}"
description = "{{ cookiecutter.description }}"
version_control = "{{cookiecutter.version_control}}"
repo_platform = "{{ cookiecutter.repository_platform}}"

# Create Remote Repository
setup_remote_repository(version_control,repo_platform,repo_name,description)


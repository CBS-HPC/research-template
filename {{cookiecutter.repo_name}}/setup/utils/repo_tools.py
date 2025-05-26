import os
import sys
import subprocess
import platform
import shutil
import zipfile
import tarfile
import pathlib

from .general_tools import *
from .versioning_tools import *

pip_installer(required_libraries =  ['requests'])

import requests

# GitHub and Gitlad Functions

def get_login_credentials_old(code_repo,repo_name):
    """Returns the user, token, and command based on the code repository."""
    if code_repo.lower() == "github":
        user = load_from_env('GITHUB_USER')
        token = load_from_env('GH_TOKEN')
        hostname = load_from_env('GH_HOSTNAME') or "github.com"
        #command = ['gh', 'auth', 'login', '--with-token']
        command = ['gh', 'auth', 'login', '--hostname', hostname, '--with-token']
         #command = ['gh', 'auth', 'login', '--with-token']
        privacy_setting = load_from_env("GITHUB_PRIVACY")

    elif code_repo.lower() == "gitlab":
        user = load_from_env('GITLAB_USER')
        token = load_from_env('GL_TOKEN')
        hostname = load_from_env('GL_HOSTNAME') or "gitlab.com"
        #command = ['glab', 'auth', 'login','--token']
        command = ['glab', 'auth', 'login', '--hostname', hostname, '--token']
        privacy_setting = load_from_env("GITLAB_PRIVACY")
    else:
        return None, None, None, None, None
    
    if not user or not token or not privacy_setting:
        version_control = load_from_env("VERSION_CONTROL",".cookiecutter")
        user, privacy_setting, token, hostname = repo_user_info(version_control,repo_name,code_repo)

    return user, token, hostname, command, privacy_setting

def get_login_credentials(code_repo, repo_name):
    """Returns the user, token, hostname, CLI command, and privacy setting based on the code repository."""
    code_repo = code_repo.lower()

    if code_repo == "github":
        user = load_from_env('GITHUB_USER')
        token = load_from_env('GH_TOKEN')
        hostname = load_from_env('GH_HOSTNAME') or "github.com"
        command = ['gh', 'auth', 'login', '--hostname', hostname, '--with-token']
        privacy_setting = load_from_env("GITHUB_PRIVACY")

    elif code_repo == "gitlab":
        user = load_from_env('GITLAB_USER')
        token = load_from_env('GL_TOKEN')
        hostname = load_from_env('GL_HOSTNAME') or "gitlab.com"
        command = ['glab', 'auth', 'login', '--hostname', hostname, '--token']
        privacy_setting = load_from_env("GITLAB_PRIVACY")

    elif code_repo == "codeberg":
        user = load_from_env('CODEBERG_USER')
        token = load_from_env('CODEBERG_TOKEN')
        hostname = load_from_env('CODEBERG_HOSTNAME') or "codeberg.org"
        command = "Not needed" # No CLI login for Codeberg
        privacy_setting = load_from_env("CODEBERG_PRIVACY")

    else:
        return None, None, None, None, None

    # Fallback to repo_user_info if anything critical is missing
    if not user or not token or not privacy_setting:
        version_control = load_from_env("VERSION_CONTROL", ".cookiecutter")
        user, privacy_setting, token, hostname = repo_user_info(version_control, repo_name, code_repo)

    return user, token, hostname, command, privacy_setting

def repo_login_codeberg(version_control=None, repo_name=None, code_repo=None):
    def authenticate(command, token):
        """Attempts to authenticate using the provided command and token."""
        try:
            result = subprocess.run(command, input=token, text=True, capture_output=True)
            return result.returncode == 0
        except Exception:
            return False

    def authenticate_codeberg(token, hostname):
        """Authenticates with Codeberg by making an API call."""
        try:
            response = requests.get(
                f"https://{hostname}/api/v1/user",
                headers={"Authorization": f"token {token}"}
            )
            return response.status_code == 200
        except Exception:
            return False

    # Load from environment if not provided
    version_control = version_control or load_from_env("VERSION_CONTROL", ".cookiecutter")
    repo_name = repo_name or load_from_env("REPO_NAME", ".cookiecutter")
    code_repo = code_repo or load_from_env("CODE_REPO", ".cookiecutter")

    # Check that all values are now set
    if not all([version_control, repo_name, code_repo]):
        return False

    try:
        # Get login credentials
        user, token, hostname, command, _ = get_login_credentials(code_repo, repo_name)

        if not user or not token:
            user, _, token, _ = repo_user_info(version_control, repo_name, code_repo)

        if not token:
            return False

        code_repo = code_repo.lower()

        if code_repo == "codeberg":
            return authenticate_codeberg(token, hostname)

        if not command:
            return False

        # Authenticate using CLI for GitHub or GitLab
        return authenticate(command, token)

    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def repo_login(version_control = None, repo_name = None , code_repo = None):

    def authenticate(command, token):
        """Attempts to authenticate using the provided command and token."""
        if not token or not command:
            return False     
        try:
            result = subprocess.run(command, input=token, text=True, capture_output=True)
            print("dre")
            return result.returncode == 0
        except Exception:
            print("dre2")
            return False

    def authenticate_codeberg(token, hostname):
        """Authenticates with Codeberg by making an API call.""" 
        if not token or not hostname:
            return False        
        try:
            response = requests.get(
                f"https://{hostname}/api/v1/user",
                headers={"Authorization": f"token {token}"}
            )
            return response.status_code == 200
        except Exception:
            return False

    # Load from environment if not provided
    repo_name = repo_name or load_from_env("REPO_NAME", ".cookiecutter")
    code_repo = code_repo or load_from_env("CODE_REPO", ".cookiecutter")

    if not repo_name or not code_repo:
        print("dre3")
        return False
    
    try:
        # Get login details based on the repository type
        _, token, hostname, command, _ = get_login_credentials(code_repo, repo_name)

        if not command or not token or not hostname:
            version_control = version_control or load_from_env("VERSION_CONTROL", ".cookiecutter")
            _, _,_, _ = repo_user_info(version_control, repo_name, code_repo)
            _, token, hostname, command, _ =  get_login_credentials(code_repo,repo_name)

        # Attempt authentication if both user and token are provided
        if code_repo.lower() in ["github","gitlab"]:
            return authenticate(command, token)
        
        elif code_repo == "codeberg":
            return authenticate_codeberg(token, hostname)

        print("dre4")
        return False

    except Exception as e:
        print(f"An error occurred: {e}")
        print("dre5")
        return False
    
def repo_create(code_repo, repo_name, project_description):
    try:
        user, token, hostname, _, privacy_setting = get_login_credentials(code_repo,repo_name)

        def create_gh():
            try:
                subprocess.run(
                    ['gh', 'repo', 'view', f'{user}/{repo_name}'],
                    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                print(f"Repository '{user}/{repo_name}' already exists on GitHub.")
            except subprocess.CalledProcessError:
                subprocess.run(
                    ['gh', 'repo', 'create', f'{user}/{repo_name}',
                     f'--{privacy_setting}', "--description", project_description,
                     "--source", ".", "--push"],
                    check=True
                )
                print(f"Repository '{repo_name}' created and pushed successfully on GitHub.")

        def create_gl():
            try:
                subprocess.run(
                    ['glab', 'repo', 'view', f'{user}/{repo_name}'], #"--hostname", hostname
                    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                print(f"Repository '{user}/{repo_name}' already exists on GitLab.")
            except subprocess.CalledProcessError:
                subprocess.run(
                    ['glab', 'repo', 'create', f'--{privacy_setting}', "--description", project_description,
                     "--name", repo_name], #"--hostname", hostname
                    check=True
                )
                print(f"Repository '{repo_name}' created on GitLab.")

        def create_cb():
            api_url = f"https://{hostname}/api/v1/user/repos"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"token {token}"
            }
            payload = {
                "name": repo_name,
                "description": project_description,
                "private": (privacy_setting == "private"),
                "auto_init": True
            }
            response = requests.post(api_url, headers=headers, json=payload)
            if response.status_code == 201:
                print(f"Repository '{repo_name}' created successfully on Codeberg.")
            elif response.status_code == 409:
                print(f"Repository '{repo_name}' already exists on Codeberg.")
            else:
                raise Exception(f"Codeberg repo creation failed: {response.status_code} {response.text}")

        if not token:
            raise ValueError("Authentication token not found.")

        code_repo = code_repo.lower()
        if code_repo not in ["github", "gitlab", "codeberg"]:
            raise ValueError("Unsupported code repository. Choose 'github' or 'gitlab'.")

        # Use hostname from credentials (fallback already handled in get_login_credentials)
        default_branch = "main" if code_repo == "github" else "master"
        remote_url = f"https://{user}:{token}@{hostname}/{user}/{repo_name}.git"

        # Create or check the repo
        if code_repo == "github":
            create_gh()
        elif code_repo == "gitlab":
            create_gl()
        elif code_repo == "codeberg":
            create_cb()

        # Set the remote URL
        remotes = subprocess.run(["git", "remote"], capture_output=True, text=True)
        if "origin" not in remotes.stdout:
            subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
        else:
            subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=True)

        # Configure credentials and push
        subprocess.run(["git", "config", "--global", "credential.helper", "store"], check=True)
        subprocess.run(["git", "push", "-u", "origin", default_branch], check=True)
        print(f"Repository pushed to {hostname} on branch '{default_branch}'.")
        repo_to_env_file(code_repo,user,repo_name)
        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Failed to create '{user}/{repo_name}' on {code_repo.capitalize()}")
        return False

def repo_to_env_file(code_repo,username,repo_name, env_file=".env"):
    """
    Adds GitHub username and token from `gh auth status` to the .env file. If the file does not exist,
    it will be created.
    
    Parameters:
    - env_file (str): The path to the .env file. Default is ".env".
    """
    def get_glab_token():
        """
        Retrieves the GitLab token from the glab CLI config file,
        even if it is marked with '!!null'.

        Returns:
            str: The GitLab token, or None if not found.
        """
        config_path = os.path.expanduser("~/.config/glab-cli/config.yml")
        if not os.path.exists(config_path):
            print(f"Config file not found: {config_path}")
            return None

        try:
            with open(config_path, "r") as file:
                lines = file.readlines()

            # Look for the token line in the file
            for line in lines:
                if "token:" in line:
                    # Split the line to get the token after '!!null'
                    token_part = line.split("!!null")[-1].strip()
                    if token_part:  # If there's something after !!null
                        return token_part

            print("Token not found in the config file.")
            return None

        except Exception as e:
            print(f"Error reading config file: {e}")
            return None
        
    def get_glab_hostname():
        """
        Retrieves the GitLab hostname from the glab CLI config file.

        Returns:
            str: The GitLab hostname, or None if not found.
        """
        config_path = os.path.expanduser("~/.config/glab-cli/config.yml")

        if not os.path.exists(config_path):
            print(f"Config file not found: {config_path}")
            return None

        try:
            with open(config_path, "r") as file:
                lines = file.readlines()

            # Look for the hostname line in the file
            for line in lines:
                if "hostname:" in line:
                    # Extract the hostname value after 'hostname:'
                    hostname = line.split(":")[-1].strip()
                    return hostname

            print("Hostname not found in the config file.")
            return None

        except Exception as e:
            print(f"Error reading config file: {e}")
            return None
        
    def get_gh_token():
        try:
            # Run the command to get the token
            result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
            return result.stdout.strip()  # Returns the token
        except subprocess.CalledProcessError as e:
            print(f"Failed to get GitHub token: {e}")
            return None

    if code_repo.lower() == "github":
        token = get_gh_token()
        token_tag = "GH"
        hostname = None
   
    elif code_repo.lower() == "gitlab":
        token = get_glab_token()
        hostname = get_glab_hostname()
        token_tag = "GLAB"
  
    if not username and not token:
        print(f"Failed to retrieve {code_repo}. Make sure you're logged in to {code_repo}.")
        return
    
    save_to_env(username,f"{code_repo}_USER") 
    save_to_env(repo_name,f"{code_repo}_REPO")     

    if token:
        save_to_env(token,f"{token_tag}_TOKEN")    
    if hostname:
        save_to_env(hostname,f"{token_tag}_HOSTNAME")
    
    print(f"{code_repo} username and token added to {env_file}")

def setup_repo(version_control,code_repo,repo_name,project_description):
    if repo_login(version_control,repo_name,code_repo):
        print("dre6")
        return repo_create(code_repo, repo_name, project_description)
    else:
        return False 

def install_glab(install_path=None):
    
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

    if is_installed('glab',"GitLab CLI (glab)"):
        return True

    os_type = platform.system().lower()
    
    install_path = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(install_path))
    #install_path = os.path.abspath(install_path) or os.getcwd()  # Default to current directory if no install_path is provided

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

    return exe_to_path('glab',os.path.join(install_path, "bin"))
   
def install_gh(install_path=None):
    """
    Installs the GitHub CLI (gh) on Windows, macOS, or Linux.

    Parameters:
    - install_path (str, optional): The directory where GitHub CLI should be installed. Defaults to the current working directory.

    Returns:
    - bool: True if installation is successful, False otherwise.
    """
   
    if is_installed('gh', "GitHub CLI (gh)"):
        return True

    os_type = platform.system().lower()

    install_path = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path(install_path))
    #install_path = os.path.abspath(install_path or os.getcwd())

    os.makedirs(install_path, exist_ok=True)

    try:
        if os_type == "windows":
            installer_url = "https://github.com/cli/cli/releases/latest/download/gh_2.28.0_windows_amd64.msi"
            installer_name = os.path.join(install_path, "gh_installer.msi")
            
            # Download the installer
            subprocess.run(["curl", "-Lo", installer_name, installer_url], check=True)

            # Install GitHub CLI
            subprocess.run(["msiexec", "/i", installer_name, "/quiet", "/norestart", f"INSTALLDIR={install_path}"], check=True)
            print(f"GitHub CLI (gh) installed successfully to {install_path}.")
            return exe_to_path("gh",os.path.join(install_path, "bin"))

        elif os_type == "darwin":  # macOS
            # Using Homebrew to install GitHub CLI
            subprocess.run(["brew", "install", "gh", "--prefix", install_path], check=True)
            print(f"GitHub CLI (gh) installed successfully to {install_path}.")
            return exe_to_path("gh",os.path.join(install_path, "bin"))

        elif os_type == "linux":
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "gh"], check=True)
            print(f"GitHub CLI (gh) installed successfully.")

            # Move to "install_path"
            path = shutil.which("gh")
            if path:
                subprocess.run(["sudo", "mv", path, os.path.join(install_path,'gh','gh')], check=True)
                return exe_to_path("gh",os.path.dirname(os.path.abspath(install_path)))
            else:
                return False
        else:
            print("Unsupported operating system.")
            return False

    except subprocess.CalledProcessError as e:
        print(f"Failed to install GitHub CLI: {e}")
        return False

    finally:
        # Clean up installer on Windows
        if os_type == "windows" and 'installer_name' in locals() and os.path.exists(installer_name):
            os.remove(installer_name)
            print(f"Installer {installer_name} removed.")


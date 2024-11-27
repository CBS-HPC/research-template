import os
import subprocess
import sys
import platform
import importlib
import shutil
import requests
import zipfile
import tarfile


required_libraries = [] 
for lib in required_libraries:
    try:
        importlib.import_module(lib)
    except ImportError:
        print(f"Installing {lib}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])

# Add the directory to sys.path
script_dir = "setup"
if script_dir not in sys.path:
    sys.path.append(script_dir)

from utils import *

def setup_remote_repository(version_control,repo_platform,repo_name,description):
    """Handle repository creation and log-in based on selected platform."""

    if version_control == None or not os.path.isdir(".git"):
        return
    if repo_platform == "GitHub":
        check = install_gh("bin/gh")     
    elif repo_platform == "GitLab":
        check = install_glab("bin/glab")
    else:
        return    
    if check:    
        setup_repo(repo_platform,repo_name,description)      

def repo_details(repo_platform):
    username = load_from_env(f"{repo_platform.upper()}_USER")
    privacy_setting = load_from_env(f"{repo_platform.upper()}_PRIVACY")

    if not username  or not privacy_setting:
        username, privacy_setting = git_repo_user(repo_platform)

    return username, privacy_setting

def repo_login(repo_platform):

    try: 
        if repo_platform == "GitHub":
            user = load_from_env('GITHUB_USER')
            token = load_from_env('GH_TOKEN')
            command = ['gh', 'auth', 'login', '--with-token']
        
            # Check if both environment variables are set
            if user and token:
                # Run the gh auth login command with the token
                subprocess.run(command, input=token, text=True, capture_output=True)
                return True
            else:
                return False
        elif repo_platform == "GitLab":
            user = load_from_env('GITLAB_USER')
            token = load_from_env('GH_TOKEN')
            hostname = load_from_env('GH_HOSTNAME')
            
            if hostname:
                command = ['glab', 'auth', 'login', '--hostname', hostname, '--token'] 
            else: 
                return False
   

        # Check if both environment variables are set
        if user and token:
            # Run the gh auth login command with the token
            subprocess.run(command, input=token, text=True, capture_output=True)
            return True
        else:
            return False    
    
    except Exception as e:
        return False
  
def repo_init(repo_platform):    
    
    if repo_platform == "GitHub":
        exe = "gh"
    elif repo_platform == "GitLab":
        exe = "glab"
    else:
        return False
    
    try:
        # Check if the user is logged in
        subprocess.run([exe, "auth", "status"], capture_output=True, text=True, check=True)
        return True 
    except Exception as e:
        try:
            subprocess.run([exe, "auth", "login"], check=True)
            return True        
        except Exception as e:
            print(f"{exe} auth login failed: {e}")
            return False

def repo_create(repo_platform,username, privacy_setting, repo_name, description):
    
    try:
        if repo_platform ==  "GitHub":    
            # Create the GitHub repository
            subprocess.run([
                'gh', "repo", "create", f"{username}/{repo_name}",
                f"--{privacy_setting}", "--description", description, "--source", ".", "--push"
            ], check=True)
        elif repo_platform == "GitLab":
             subprocess.run([
                'glab', "repo", "create",
                f"--{privacy_setting}", "--description", description], check=True)
            
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

    if repo_platform == "GitHub":
        token = get_gh_token()
        tag = "GITHUB"
        token_tag = "GH"
        hostname = None
   
    elif repo_platform == "GitLab":
        token = get_glab_token()
        hostname = get_glab_hostname()
        tag = "GITLAB"
        token_tag = "GLAB"
  
    if not username and not token:
        print(f"Failed to retrieve {repo_platform}. Make sure you're logged in to {repo_platform}.")
        return
    
    # Check if .env file exists
    if not os.path.exists(env_file):
        print(f"{env_file} does not exist. Creating a new one.")
    
    # Write the credentials to the .env file
    with open(env_file, 'a') as file:
        file.write(f"{tag}_USER={username}\n")
        file.write(f"{tag}_REPO={repo_name}\n")
        if token:
            file.write(f"{token_tag}_TOKEN={token}\n")
        if hostname:
            file.write(f"{token_tag}_HOSTNAME={hostname}\n")
    
    print(f"{tag} username and token added to {env_file}")

def setup_repo(repo_platform,repo_name,description):
    
    if not repo_login(repo_platform):
        username,privacy_setting = repo_details(repo_platform)
        if repo_init(repo_platform):
            check, username, repo_name = repo_create(repo_platform,username,privacy_setting,repo_name,description)
            if check:
                repo_to_env_file(repo_platform,username,repo_name)
 
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

     # Set from .env file
    
    # Set from .env file
    if exe_from_env('glab'):
        return True
    
    if is_installed('glab',"GitLab CLI (glab)"):
        return True

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
    exe_to_path('GitLab CLI',os.path.join(install_path, "bin"))

    return True
   
def install_gh(install_path=None):
    """
    Installs the GitHub CLI (gh) on Windows, macOS, or Linux.

    Parameters:
    - install_path (str, optional): The directory where GitHub CLI should be installed. Defaults to the current working directory.

    Returns:
    - bool: True if installation is successful, False otherwise.
    """
    # Set from .env file
    if exe_from_env('gh'):
        return True

    if is_installed('gh', "GitHub CLI (gh)"):
        return True

    os_type = platform.system().lower()
    install_path = os.path.abspath(install_path or os.getcwd())
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

        elif os_type == "darwin":  # macOS
            # Using Homebrew to install GitHub CLI
            subprocess.run(["brew", "install", "gh", "--prefix", install_path], check=True)
            print(f"GitHub CLI (gh) installed successfully to {install_path}.")

        elif os_type == "linux":
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "gh"], check=True)
            print(f"GitHub CLI (gh) installed successfully.")
        else:
            print("Unsupported operating system.")
            return False

        # Add the extracted glab to the system PATH
        exe_to_path("GitHub CLI",os.path.join(install_path, "bin"))

        return True

    except subprocess.CalledProcessError as e:
        print(f"Failed to install GitHub CLI: {e}")
        return False

    finally:
        # Clean up installer on Windows
        if os_type == "windows" and 'installer_name' in locals() and os.path.exists(installer_name):
            os.remove(installer_name)
            print(f"Installer {installer_name} removed.")

repo_name = "{{ cookiecutter.repo_name }}"
description = "{{ cookiecutter.description }}"
version_control = "{{cookiecutter.version_control}}"
repo_platform = "{{ cookiecutter.repository_platform}}"
version_control = "{{cookiecutter.version_control}}"
project_name = "{{cookiecutter.project_name}}"
project_description = "{{cookiecutter.description}}"
author_name = "{{cookiecutter.author_name}}"

# Create Remote Repository
setup_remote_repository(version_control,repo_platform,repo_name,description)

# Updating environment.yaml
export_conda_env(repo_name)

# Updating README
creating_readme(repo_name,project_name, project_description,repo_platform,author_name)

# Pushing to Git 
git_push("environment.yaml updated and README.md added ")
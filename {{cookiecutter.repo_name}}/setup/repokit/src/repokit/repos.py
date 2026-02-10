import os
import pathlib
import platform
import shutil
import subprocess
import tarfile
import zipfile

import requests

from .ci import ci_config
from repokit_common import (
    PROJECT_ROOT,
    ensure_correct_kernel,
    exe_to_path,
    is_installed,
    load_from_env,
    save_to_env,
    repo_user_info,
    prompt_user,
)
from .vcs import setup_version_control
from .readme.template import create_citation_file

# GitHub, Gitlad and Codeberg Functions


def setup_repo(version_control, code_repo, repo_name, project_description):
    if repo_login(version_control, repo_name, code_repo):
        return repo_create(code_repo, repo_name, project_description, version_control)
    else:
        return False


def get_login_credentials(code_repo, repo_name):
    """Returns the user, token, hostname, CLI command, and privacy setting based on the code repository."""
    code_repo = code_repo.lower()

    if code_repo == "github":
        user = load_from_env("GITHUB_USER")
        token = load_from_env("GITHUB_TOKEN")
        hostname = load_from_env("GITHUB_HOSTNAME") or "github.com"
        privacy_setting = load_from_env("GITHUB_PRIVACY")

    elif code_repo == "gitlab":
        user = load_from_env("GITLAB_USER")
        token = load_from_env("GITLAB_TOKEN")
        hostname = load_from_env("GITLAB_HOSTNAME") or "gitlab.com"
        privacy_setting = load_from_env("GITLAB_PRIVACY")

    elif code_repo == "codeberg":
        user = load_from_env("CODEBERG_USER")
        token = load_from_env("CODEBERG_TOKEN")
        hostname = load_from_env("CODEBERG_HOSTNAME") or "codeberg.org"
        privacy_setting = load_from_env("CODEBERG_PRIVACY")

    else:
        return None, None, None, None

    # Fallback to repo_user_info if anything critical is missing
    if not user or not token or not privacy_setting:
        version_control = load_from_env("VERSION_CONTROL", ".cookiecutter")
        user, privacy_setting, token, hostname = repo_user_info(
            version_control, repo_name, code_repo
        )

    return user, token, hostname, privacy_setting


def repo_login(version_control=None, repo_name=None, code_repo=None):
    def authenticate_api(token, hostname, platform):
        """Authenticate by requesting user info via API."""
        if not token or not hostname:
            return False
        try:
            if platform == "github":
                url = "https://api.github.com/user"
                headers = {"Authorization": f"token {token}"}
            elif platform == "gitlab":
                url = f"https://{hostname}/api/v4/user"
                headers = {"PRIVATE-TOKEN": token}
            elif platform == "codeberg":
                url = f"https://{hostname}/api/v1/user"
                headers = {"Authorization": f"token {token}"}
            else:
                return False

            response = requests.get(url, headers=headers)
            return response.status_code == 200
        except Exception:
            return False

    # Load from environment if not provided
    repo_name = repo_name or load_from_env("REPO_NAME", ".cookiecutter")
    code_repo = code_repo or load_from_env("CODE_REPO", ".cookiecutter")

    if not repo_name or not code_repo:
        return False

    try:
        # Get login details based on the repository type
        _, token, hostname, _ = get_login_credentials(code_repo, repo_name)

        if not token or not hostname:
            version_control = version_control or load_from_env("VERSION_CONTROL", ".cookiecutter")
            _, _, _, _ = repo_user_info(version_control, repo_name, code_repo)
            _, token, hostname, _ = get_login_credentials(code_repo, repo_name)

        code_repo_lower = code_repo.lower()
        if code_repo_lower in ["github", "gitlab", "codeberg"]:
            return authenticate_api(token, hostname, code_repo_lower)

        return False

    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def repo_create(code_repo, repo_name, project_description, version_control):
    try:
        user, token, hostname, privacy_setting = get_login_credentials(code_repo, repo_name)
        if not token:
            raise ValueError("Authentication token not found.")

        code_repo_lower = code_repo.lower()
        if code_repo_lower not in ["github", "gitlab", "codeberg"]:
            raise ValueError(
                "Unsupported code repository. Choose 'github', 'gitlab', or 'codeberg'."
            )

        def create_github():
            api_url = "https://api.github.com/user/repos"
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            }
            payload = {
                "name": repo_name,
                "description": project_description,
                "private": (privacy_setting == "private"),
                "auto_init": False,
            }
            response = requests.post(api_url, headers=headers, json=payload)
            if response.status_code == 201:
                print(f"Repository '{repo_name}' created successfully on GitHub.")
            elif response.status_code == 422 and "already exists" in response.text.lower():
                print(f"Repository '{repo_name}' already exists on GitHub.")
            else:
                raise Exception(
                    f"GitHub repo creation failed: {response.status_code} {response.text}"
                )

        def create_gitlab():
            api_url = f"https://{hostname}/api/v4/projects"
            headers = {"PRIVATE-TOKEN": token}
            payload = {
                "name": repo_name,
                "description": project_description,
                "visibility": "private" if privacy_setting == "private" else "public",
                "initialize_with_readme": False,
            }
            response = requests.post(api_url, headers=headers, data=payload)
            if response.status_code == 201:
                print(f"Repository '{repo_name}' created successfully on GitLab.")
            elif response.status_code == 400 and "has already been taken" in response.text.lower():
                print(f"Repository '{repo_name}' already exists on GitLab.")
            else:
                raise Exception(
                    f"GitLab repo creation failed: {response.status_code} {response.text}"
                )

        def create_codeberg():
            api_url = f"https://{hostname}/api/v1/user/repos"
            headers = {"Content-Type": "application/json", "Authorization": f"token {token}"}
            payload = {
                "name": repo_name,
                "description": project_description,
                "private": (privacy_setting == "private"),
                "auto_init": False,
            }
            response = requests.post(api_url, headers=headers, json=payload)
            if response.status_code == 201:
                print(f"Repository '{repo_name}' created successfully on Codeberg.")
            elif response.status_code == 409:
                print(f"Repository '{repo_name}' already exists on Codeberg.")
            else:
                raise Exception(
                    f"Codeberg repo creation failed: {response.status_code} {response.text}"
                )

        # Create or check the repo
        if code_repo_lower == "github":
            create_github()
        elif code_repo_lower == "gitlab":
            create_gitlab()
        elif code_repo_lower == "codeberg":
            create_codeberg()

        # Setup remote URL and push
        default_branch = "main" if code_repo_lower in ["github", "codeberg"] else "master"
        remote_url = f"https://{user}:{token}@{hostname}/{user}/{repo_name}.git"

        remotes = subprocess.run(["git", "remote"], capture_output=True, text=True)
        if "origin" not in remotes.stdout:
            subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
        else:
            subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=True)

        # If using DataLad, add a sibling and push via DataLad
        if version_control.lower() == "datalad":
            # Register the Git host as a DataLad sibling
            # (idempotent: won't fail if already there)
            # subprocess.run(["datalad", "siblings", "add", "-s", "origin", "--url", remote_url], check=False)
            subprocess.run(
                ["datalad", "siblings", "configure", "-s", "origin", "--url", remote_url],
                check=False,
            )

            # Push Git history (and recursively subdatasets if any)
            subprocess.check_call(["datalad", "push", "--to", "origin", "-r"])
            print(f"Repository pushed via DataLad to '{hostname}' (sibling 'origin').")
        else:
            # Plain Git push (set upstream to origin/<branch>)
            subprocess.check_call(["git", "config", "--global", "credential.helper", "store"])
            subprocess.check_call(["git", "push", "-u", "origin", default_branch])
            print(f"Repository pushed to {hostname} on branch '{default_branch}'.")

        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Failed to create '{user}/{repo_name}' on {code_repo.capitalize()}")
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

    if is_installed("glab", "GitLab CLI (glab)"):
        return True

    os_type = platform.system().lower()

    install_path = str(PROJECT_ROOT / pathlib.Path(install_path))

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
        extract_method = lambda: zipfile.ZipFile(glab_path, "r").extractall(install_path)

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

    return exe_to_path("glab", os.path.join(install_path, "bin"))


def install_gh(install_path=None):
    """
    Installs the GitHub CLI (gh) on Windows, macOS, or Linux.

    Parameters
    ----------
    - install_path (str, optional): The directory where GitHub CLI should be installed. Defaults to the current working directory.

    Returns
    -------
    - bool: True if installation is successful, False otherwise.
    """
    if is_installed("gh", "GitHub CLI (gh)"):
        return True

    os_type = platform.system().lower()

    install_path = str(PROJECT_ROOT / pathlib.Path(install_path))

    os.makedirs(install_path, exist_ok=True)

    try:
        if os_type == "windows":
            installer_url = (
                "https://github.com/cli/cli/releases/latest/download/gh_2.28.0_windows_amd64.msi"
            )
            installer_name = os.path.join(install_path, "gh_installer.msi")

            # Download the installer
            subprocess.run(["curl", "-Lo", installer_name, installer_url], check=True)

            # Install GitHub CLI
            subprocess.run(
                [
                    "msiexec",
                    "/i",
                    installer_name,
                    "/quiet",
                    "/norestart",
                    f"INSTALLDIR={install_path}",
                ],
                check=True,
            )
            print(f"GitHub CLI (gh) installed successfully to {install_path}.")
            return exe_to_path("gh", os.path.join(install_path, "bin"))

        elif os_type == "darwin":  # macOS
            # Using Homebrew to install GitHub CLI
            subprocess.run(["brew", "install", "gh", "--prefix", install_path], check=True)
            print(f"GitHub CLI (gh) installed successfully to {install_path}.")
            return exe_to_path("gh", os.path.join(install_path, "bin"))

        elif os_type == "linux":
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "gh"], check=True)
            print("GitHub CLI (gh) installed successfully.")

            # Move to "install_path"
            path = shutil.which("gh")
            if path:
                subprocess.run(
                    ["sudo", "mv", path, os.path.join(install_path, "gh", "gh")], check=True
                )
                return exe_to_path("gh", os.path.dirname(os.path.abspath(install_path)))
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
        if os_type == "windows" and "installer_name" in locals() and os.path.exists(installer_name):
            os.remove(installer_name)
            print(f"Installer {installer_name} removed.")


@ensure_correct_kernel
def main():
    # Ensure the working directory is the project root
    os.chdir(PROJECT_ROOT)

    version_control = load_from_env("VERSION_CONTROL", ".cookiecutter")
    code_repo = load_from_env("CODE_REPO", ".cookiecutter")

    if version_control == "None":
        version_control = prompt_user(
            "Choose a version control:", ["Git", "Datalad", "DVC", "None"]
        )
        save_to_env(code_repo, "VERSION_CONTROL", ".cookiecutter")

    if version_control == "None":
        return

    if code_repo == "None":
        code_repo = prompt_user(
            "Choose a code repository host:", ["GitHub", "GitLab", "Codeberg", "None"]
        )

        save_to_env(code_repo, "CODE_REPO", ".cookiecutter")

    repo_name = load_from_env("REPO_NAME", ".cookiecutter")
    project_description = load_from_env("PROJECT_DESCRIPTION", ".cookiecutter")
    remote_storage = load_from_env("REMOTE_STORAGE", ".cookiecutter")
    project_name = load_from_env("PROJECT_NAME", ".cookiecutter")
    version = load_from_env("VERSION", ".cookiecutter")
    authors = load_from_env("AUTHORS", ".cookiecutter")
    orcids = load_from_env("ORCIDS", ".cookiecutter")

    setup_version_control(version_control, remote_storage, code_repo, repo_name)

    # Create Remote Repository
    if setup_repo(version_control, code_repo, repo_name, project_description):
        ci_config()

        create_citation_file(
            project_name, version, authors, orcids, code_repo, doi=None, release_date=None
        )


if __name__ == "__main__":
    main()

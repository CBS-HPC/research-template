import glob
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile
import requests

from .common import (
    PROJECT_ROOT,
    ask_yes_no,
    change_dir,
    exe_to_path,
    git_user_info,
    is_installed,
    load_from_env,
    save_to_env,
    install_uv,
)


# Version Control
def setup_version_control(version_control, remote_storage, code_repo, repo_name):
    """Handle repository creation and log-in based on selected platform."""
    if version_control.lower() == "git":
        setup_git(version_control, code_repo)
    if version_control.lower() == "datalad":
        setup_datalad(version_control, remote_storage, code_repo, repo_name)
    elif version_control.lower() == "dvc":
        setup_dvc(version_control, remote_storage, code_repo, repo_name)


# Git Functions:
def setup_git(version_control, code_repo):
    if install_git("./bin/git"):
        # Ensure that chdir is at project folder
        os.chdir(PROJECT_ROOT)

        flag, git_name, git_email = check_git_config()

        if not flag:
            flag, git_name, git_email = setup_git_config(version_control, git_name, git_email)

        if flag and version_control.lower() in ["git","datalad","dvc"]: 
            
            default_branch = "main" if code_repo.lower() in ["github", "codeberg"] else "master"
            
            flag = git_init(msg="Initial commit", branch_name=default_branch)
            # Creating its own git repo for "data"
            if version_control.lower() == "git" and flag:
                with change_dir("./data"):
                    flag = git_init(msg="Initial commit - /data git repo", branch_name="data", path=os.getcwd())
                    git_log_to_file(os.path.join(".gitlog"))
        if flag:
            save_to_env(git_name, "GIT_USER")
            save_to_env(git_email, "GIT_EMAIL")

        return flag
    else:
        return False


def install_git(install_path=None):
    """
    Installs Git if it is not already installed.
    - For Windows: Downloads and installs Git to a specified path.
    - For Linux: Installs using 'sudo apt install git-all'.
    - For macOS: Installs via Xcode Command Line Tools.

    Parameters
    ----------
    - install_path (str, optional): The path where Git should be installed on Windows.

    Returns
    -------
    - bool: True if installation is successful, False otherwise.
    """
    if is_installed("git", "Git"):
        return True

    try:
        os_type = platform.system().lower()

        if os_type == "windows":
            if not install_path:
                print("Please provide an install path for Windows installation.")
                return False

            install_path = str(PROJECT_ROOT / pathlib.Path(install_path))

            # Download Git installer for Windows
            download_dir = os.path.dirname(install_path)
            installer_name = "Git-latest-64-bit.exe"
            installer_path = os.path.join(download_dir, installer_name)
            url = (
                f"https://github.com/git-for-windows/git/releases/latest/download/{installer_name}"
            )

            print(f"Downloading Git installer from {url} to {download_dir}...")
            urllib.request.urlretrieve(url, installer_path)
            print("Download complete.")

            # Run the silent installation
            subprocess.run(
                [installer_path, "/VERYSILENT", f"/DIR={install_path}", "/NORESTART"], check=True
            )

            # Add Git to PATH
            exe_to_path("git", os.path.join(install_path, "bin"))

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
        if is_installed("git", "Git"):
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

    Returns
    -------
    - bool: True if Git is configured, False otherwise.
    """
    try:
        # Check .env file
        env_name = load_from_env("GIT_USER")
        env_email = load_from_env("GIT_EMAIL")

        # Test
        if env_name and env_email:
            return False, env_name, env_email

        # Check the current Git user configuration
        current_name = subprocess.run(
            ["git", "config", "--global", "user.name"], capture_output=True, text=True, check=True
        )
        current_email = subprocess.run(
            ["git", "config", "--global", "user.email"], capture_output=True, text=True, check=True
        )

        # Handle potential UnicodeDecodeError
        try:
            current_name = current_name.stdout.strip()
            current_email = current_email.stdout.strip()
        except UnicodeDecodeError as e:
            print(f"Error decoding Git configuration output: {e}")
            return False, None, None  # Return False if we can't decode the output

        # Check if Git is properly configured
        if current_name and current_email:
            print(
                f"Git is configured with user.name: {current_name} and user.email: {current_email}"
            )

            confirm = ask_yes_no(
                f"Do you want to keep the current Git user.name: {current_name} and user.email: {current_email} (yes/no): "
            )

            if confirm:
                return True, current_name, current_email  # Return True if configured
            else:
                return False, None, None  # Return False if Git is not fully configured
        else:
            print("Git is not fully configured.")
            return False, None, None  # Return False if Git is not fully configured

    except subprocess.CalledProcessError as e:
        print(f"Git configuration check failed: {e}")
        return False, None, None  # Return False if subprocess fails
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False, None, None  # Return False for any other unexpected errors


def setup_git_config(version_control, git_name, git_email):
    """
    Prompts the user for their name and email, then configures Git with these details.

    Returns
    -------
    - bool: True if the configuration is successful, False otherwise.
    """
    try:
        if not git_name or not git_email:
            git_name, git_email = git_user_info(version_control)

        # Configure Git user name and email locally
        subprocess.run(["git", "config", "--global", "user.name", git_name], check=True)
        subprocess.run(["git", "config", "--global", "user.email", git_email], check=True)

        print(f"Git configured with name: {git_name} and email: {git_email}")
        return True, git_name, git_email
    except subprocess.CalledProcessError as e:
        print(f"Failed to configure Git: {e}")
        return False, git_name, git_email


def git_init(msg, branch_name, path: str = None):
    if not path:
        path = str(PROJECT_ROOT)

    # Ensure the target path exists
    if not os.path.exists(path):
        os.makedirs(path)

    if branch_name:
        subprocess.run(["git", "config", "--global", "init.defaultBranch", branch_name], check=True)

    # Initialize a Git repository if one does not already exist
    if not os.path.isdir(os.path.join(path, ".git")):
        subprocess.run(["git", "init"], check=True, cwd=path)
        print(f"Initialized a new Git repository in {path}.")

        # if rename:
        #    subprocess.run(["git", "branch", "-m", "master", rename], check=True, cwd=path)

        _ = git_commit(msg, path)
        print(f"Created the following commit: {msg}")
        return True

    return False


def git_commit(msg: str = "", path: str | None = None, recursive: bool = True) -> bool:
    """
    Save/commit changes in `path`.
    - DataLad dataset: `datalad save` (recursive by default)
    - Plain Git repo:  `git add -A && git commit -m`
    Returns True on success or if there was nothing to commit; False on error.
    """
    path = str(path or PROJECT_ROOT)
    p = pathlib.Path(path)

    is_datalad = (p / ".datalad").is_dir() and is_installed("datalad")
    is_git = (p / ".git").is_dir() and is_installed("git")

    try:
        if is_datalad:
            # DataLad: save (recursively if requested)
            cmd = ["datalad", "save", "-m", msg] if msg else ["datalad", "save"]
            if recursive:
                cmd.insert(2, "-r")  # datalad save -r -m "..."
            try:
                subprocess.run(cmd, check=True, cwd=path)
            except subprocess.CalledProcessError:
                # Typically datalad returns success even when "notneeded",
                # but if it errs, treat "no changes" as non-fatal.
                print("No DataLad changes to save.")
            return True

        if is_git:
            # Git: stage everything and commit
            subprocess.run(["git", "add", "-A"], check=True, cwd=path)
            try:
                commit_cmd = ["git", "commit", "-m", msg] if msg else ["git", "commit", "--allow-empty", "-m", ""]
                subprocess.run(commit_cmd, check=True, cwd=path)
            except subprocess.CalledProcessError:
                print("No Git changes to commit.")
            return True

        print("Not a Git/DataLad repository at:", path)
        return False

    except subprocess.CalledProcessError as e:
        print(f"Commit/save failed: {e}")
        return False


def git_commit_old(msg: str = "", path: str = None) -> str:
    """Commits changes to Git in the given path and returns the commit hash."""
    if not path:
        path = str(PROJECT_ROOT)

    if os.path.isdir(os.path.join(path, ".git")) and is_installed("git"):
        try:
            # Stage all changes
            subprocess.run(["git", "add", "."], check=True, cwd=path)
            try:
                subprocess.run(["git", "commit", "-m", msg], check=True, cwd=path)
            except subprocess.CalledProcessError:
                print("No changes to commit.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"An error occurred: {e}")
            return False


def git_push(flag: str, msg: str = "", path: str = None):
    def push_all(remote="origin", path: str = None):
        if not path:
            path = str(PROJECT_ROOT)

        try:
            # Get the name of the current branch
            current_branch = subprocess.check_output(
                ["git", "branch", "--show-current"], text=True, cwd=path
            ).strip()

            # Get all local branches
            branches = (
                subprocess.check_output(["git", "branch"], text=True, cwd=path).strip().splitlines()
            )

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
        path = str(PROJECT_ROOT)
    try:
        if git_commit(msg, path=path):
            if flag and os.path.isdir(os.path.join(path, ".datalad")):
                push_all(path=path)
            elif flag and os.path.isdir(os.path.join(path, ".git")):
                result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=path,
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
            
            return True
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        return False


def git_log_to_file(output_file_path):
    """
    Runs the 'git log' command with the specified output file path.

    Parameters
    ----------
    output_file_path (str): The full path to the output file where the Git log will be saved.
    """
    try:
        # Run the git log command with the specified output file
        command = f'git log --all --pretty=fuller --stat > "{output_file_path}"'
        subprocess.run(command, shell=True, check=True)
        print(f"Git log has been saved to {output_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")


# DVC Setup Functions
def setup_dvc(version_control, remote_storage, code_repo, repo_name):
    # Install Git
    if not setup_git(version_control, code_repo):
        return

    # Install datalad
    if not install_dvc():
        return
    dvc_init(remote_storage, code_repo, repo_name)


def install_dvc():
    """
    Install DVC, preferring `uv pip install dvc` and falling back to `pip install dvc`.
    Returns True on success, False otherwise.
    """
    # If already present, we're done.
    if is_installed("dvc", "DVC"):
        return True

    def _run(desc, cmd, check=True):
        try:
            res = subprocess.run(cmd, check=check, capture_output=True, text=True)
            return True, res
        except subprocess.CalledProcessError as e:
            print(f"[{desc}] failed with exit code {e.returncode}")
            if e.stdout:
                print("--- stdout ---")
                print(e.stdout.strip())
            if e.stderr:
                print("--- stderr ---")
                print(e.stderr.strip())
            return False, e

    # 1) Try uv-based install first (if uv is available/installed)

    if install_uv() :
        ok, _ = _run(
            "uv pip install dvc",
            [sys.executable, "-m", "uv", "pip", "install", "dvc"]
            #[sys.executable, "-m", "uv", "pip", "install", "dvc[all]"]
        )
        if ok and is_installed("dvc", "DVC"):
            print("DVC has been installed successfully via uv.")
            return True
        else:
            print("uv-based install did not result in a working DVC; trying pip fallback…")
    else:
        print("uv not available; trying pip fallback…")

    # 2) Fallback: regular pip install
    ok, _ = _run(
        "pip install dvc",
        [sys.executable, "-m", "pip", "install", "dvc"]
    )
    if not ok or not is_installed("dvc", "DVC"):
        print("Error during DVC installation.")
        return False

    print("DVC has been installed successfully via pip.")
    return True


def install_dvc_old():
    """
    Install DVC using pip.
    """

    if not is_installed("dvc", "DVC"):
        try:
            # Install DVC via pip
            subprocess.check_call([sys.executable, "-m", "pip", "install", "dvc"])
            #subprocess.check_call([sys.executable, "-m", "pip", "install", "dvc[all]"])
            if not is_installed("dvc", "DVC"):
                print("Error during datalad installation.")
                return False
            print("DVC has been installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred during DVC installation: {e}")
            return False
        except FileNotFoundError:
            print(
                "Python or pip was not found. Please ensure Python and pip are installed and in your PATH."
            )
            return False
    return True


def dvc_init(remote_storage, code_repo, repo_name):
    # Initialize a Git repository if one does not already exist
    if not os.path.isdir(".git"):
        if code_repo.lower() in ["github", "codeberg"]:
            subprocess.run(["git", "config", "--global", "init.defaultBranch", "main"], check=True)

        subprocess.run(["git", "init"], check=True)

    # Init dvc
    if not os.path.isdir(".dvc"):
        subprocess.run(["dvc", "init"], check=True)
    else:
        print("I is already a DVC project")
        return

    # Add dvc remote storage
    if remote_storage == "Local Path":
        dvc_local_storage(repo_name)
    elif remote_storage == "Deic-Storage":
        dvc_deic_storage(repo_name)
    elif remote_storage == "Dropbox":
        print("Not implemented yet")


    subprocess.run(["dvc", "add", "data"], check=True)
    
    _ = git_commit("Initial commit - Initialize DVC repository with data folder.")
    print("Created an initial commit.")


def dvc_deic_storage(remote_directory=None):
    email = input("Please enter email to Deic-Storage: ").strip()
    password = input("Please enter password to Deic-Storage: ").strip()

    # Use root directory if no path is provided
    remote_directory = remote_directory if remote_directory else ""

    # Construct the command to add the DVC SFTP remote
    add_command = [
        "dvc",
        "remote",
        "add",
        "-d",
        "deic_storage",
        f"ssh://'{email}'@sftp.storage.deic.dk:2222",
    ]
    # f"sftp://'{email}'@sftp.storage.deic.dk:2222/{remote_directory}"
    # Construct the command to set the password for the remote
    password_command = ["dvc", "remote", "modify", "deic_storage", "password", password]

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

        Parameters
        ----------
        - repo_name (str): The name of the repository to ensure at the end of `folder_path`.

        Returns
        -------
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
                print(
                    f"The path '{folder_path}' already exists with '{repo_name}' as the final folder."
                )
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
        subprocess.run(["dvc", "remote", "add", "-d", "remote_storage", dvc_remote], check=True)


# Datalad Setup Functions
def setup_datalad(version_control, remote_storage, code_repo, repo_name):
    # Install Git
    if not setup_git(version_control, code_repo):
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

    # deactivate data/ in .gitignore
    gitignore = pathlib.Path(PROJECT_ROOT / ".gitignore")
    if gitignore.exists():
        lines = gitignore.read_text().splitlines()
        new_lines = [line.replace("data/", "#data/") if line.startswith("data/") else line for line in lines]
        gitignore.write_text("\n".join(new_lines) + "\n")

    # Create datalad dataset
    datalad_create()

    if remote_storage == "Local Path":
        datalad_local_storage(repo_name, remote_storage)
    elif remote_storage in ["Dropbox", "Deic-Storage"]:
        datalad_deic_storage(repo_name)


def _uv_installer(package_name:str = None):
    
    if not package_name:
            return False
    if not install_uv():
        return False
    try:
        subprocess.run(
            [sys.executable, "-m", "uv", "tool", "install", "git-annex"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        if e.stdout:
            print("--- stdout ---")
            print(e.stdout.strip())
        if e.stderr:
            print("--- stderr ---")
            print(e.stderr.strip())
        return False


def install_datalad():
    def _pip_installer():
        try:
            if not shutil.which("datalad-installer"):
                subprocess.check_call([sys.executable, "-m", "pip", "install", "datalad-installer"])
            subprocess.check_call([sys.executable, "-m", "pip", "install", "datalad"])
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "pyopenssl", "--upgrade"]
            )
            if not is_installed("datalad", "Datalad"):
                print("Error during datalad installation.")
                return False
            print("datalad installed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"An error occurred: {e}")
            return False
        except FileNotFoundError:
            print(
                "One of the required commands was not found. Please ensure Python, pip, and Git are installed and in your PATH."
            )
            return False

    if not is_installed("datalad", "Datalad"):

        if not _uv_installer(package_name="datalad"):
            return _pip_installer()

    return True


def install_git_annex():
    """
    Installs git-annex using datalad-installer if not already installed.
    Configures git to use the git-annex filter process.

    Returns
    -------
        str: The installation path of git-annex if installed successfully.
        None: If the installation fails.
    """
    def _is_windows():
        return os.name == "nt"  # or: sys.platform.startswith("win")
    
    def _windows_installer():
        
        if not _is_windows():
            return False
          
        try:
            # Ensure datalad-installer is available
            if not shutil.which("datalad-installer"):
                subprocess.check_call([sys.executable, "-m", "pip", "install", "datalad-installer"])

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

            if not exe_to_path("git-annex", os.path.dirname(install_path)):
                # if not is_installed('git-annex', 'Git-Annex'):
                return False

            return True
        except subprocess.CalledProcessError as e:
            print(f"Error during git-annex installation: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

    # Check if git-annex is installed
    if not is_installed("git-annex", "Git-Annex"):
        installed = False

        # Try uv first (all platforms)
        if _uv_installer(package_name="git-annex"):
            installed = True
        else:
            # On Windows, try the Windows-specific installer as a fallback
            if _is_windows():
                installed = _windows_installer()

        if not installed:
            return False
        
    # Configure git to use the git-annex filter process
    try:
        subprocess.check_call(
            ["git", "config", "--global", "filter.annex.process", "git-annex filter-process"]
        )
        print("git-annex installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error configuring git-annex filter process: {e}")
        return False


def install_git_annex_remote_rclone(install_path):
    
    def clone_git_annex_remote_rclone(install_path):
        """Clone the git-annex-remote-rclone repository to the specified bin folder."""
        repo_url = "https://github.com/git-annex-remote-rclone/git-annex-remote-rclone.git"
        repo_name = os.path.basename(repo_url).replace(".git", "")
        #repo_path = os.path.join(install_path, repo_name)
        repo_path = str(pathlib.Path(install_path) / pathlib.Path(repo_name))


        # Create the bin folder if it doesn't exist
        install_path = str(PROJECT_ROOT / pathlib.Path(install_path))
        os.makedirs(install_path, exist_ok=True)

        # Check if the repository already exists
        if os.path.isdir(repo_path):
            print(f"The repository '{repo_name}' already exists in {install_path}.")
        else:
            subprocess.run(["git", "clone", repo_url, repo_path], check=True)
            print(f"Repository cloned successfully to {repo_path}.")

        repo_path = os.path.abspath(repo_path)  # Convert to absolute path
        return repo_path

    # Clone https://github.com/git-annex-remote-rclone/git-annex-remote-rclone.git

    if not is_installed("git-annex-remote-rclone", "git-annex-remote-rclone"):
        repo_path = clone_git_annex_remote_rclone(install_path)
        exe_to_path("git-annex-remote-rclone", repo_path)


def datalad_create():
    """
    Create a DataLad dataset (if missing) and configure .gitattributes so that:
      - All files are unlocked (stored in Git, not annexed)
      - Except anything under ./data/** which goes to annex
    """
    gitattributes = PROJECT_ROOT / ".gitattributes"

    def write_gitattributes():
        # Last matching rule wins; keep 'data/**' AFTER '*' to override it.
        lines = [
            "* annex.largefiles=nothing\n",       # default: don't annex (i.e., unlocked)
            "data/** annex.largefiles=anything\n" # but annex everything under ./data
        ]
        # Write idempotently (avoid duplicate lines, preserve other attrs if any)
        existing = gitattributes.read_text().splitlines(True) if gitattributes.exists() else []
        wanted = []
        # Keep any non-annex.largefiles lines the user might already have
        for ln in existing:
            if "annex.largefiles=" not in ln:
                wanted.append(ln)
        # Append our two canonical lines
        wanted.extend(lines)
        gitattributes.write_text("".join(wanted))

    # Initialize a DataLad dataset if needed
    if not (PROJECT_ROOT / ".datalad").is_dir():
        subprocess.run(["datalad", "create", "--force"], check=True)

    # Ensure the attributes are set as requested
    write_gitattributes()

    # Save the state
    subprocess.run(["datalad", "save", "-m", "Configure annex: unlock everything except ./data"], check=True)
    print("DataLad dataset ready: unlocked all except ./data")


def datalad_deic_storage(repo_name):
    
    def git_annex_remote(remote_name, target, prefix):
        """
        Creates a git annex remote configuration for 'deic-storage' using rclone.
        """
        #remote_name = "deic-storage"
        #target = "dropbox-for-friends"  # Change this to your actual target as needed
        #prefix = "my_awesome_dataset"  # Change this to your desired prefix

        # Construct the command
        command = [
            "git",
            "annex",
            "initremote",
            remote_name,
            "type=external",
            "externaltype=rclone",
            "chunk=50MiB",
            "encryption=none",
            "target=" + target,
            "prefix=" + prefix,
        ]

        try:
            # Execute the command
            subprocess.run(command, check=True)
            print(f"Git annex remote '{remote_name}' created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to create git annex remote: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    # rclone_remote()
    git_annex_remote("deic-storage", "deic-storage", repo_name)


def datalad_local_storage(repo_name, remote_storage):
    def get_remote_path(repo_name):
        """
        Prompt the user to provide the path to a DVC remote storage folder.
        If `folder_path` already ends with `repo_name` and exists, an error is raised.
        Otherwise, if `folder_path` exists but does not end with `repo_name`,
        it appends `repo_name` to `folder_path` to create the required directory.

        Parameters
        ----------
        - repo_name (str): The name of the repository to ensure at the end of `folder_path`.

        Returns
        -------
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
                print(
                    f"The path '{folder_path}' already exists with '{repo_name}' as the final folder."
                )
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
        subprocess.run(
            [
                "datalad",
                "create-sibling-ria",
                "-s",
                repo_name,
                "--new-store-ok",
                f"ria+file//{remote_storage}",
            ],
            check=True,
        )


def _run(cmd, cwd, check=True, capture=False):
    return subprocess.run(
        cmd, cwd=str(cwd), check=check,
        capture_output=capture, text=True
    )

def _git_tracks_anything(root: pathlib.Path, rel: str) -> bool:
    # returns True if Git currently tracks any path under rel/
    p = _run(["git", "ls-files", "--stage", "--", rel], cwd=root, check=False, capture=True)
    return bool((p.stdout or "").strip())

def _ensure_initial_commit_and_annex(sub_path: pathlib.Path) -> None:
    """Make sure the subdataset has an initial commit AND a usable annex."""
    # 1) Do we have any commit?
    has_head = _run(["git", "rev-parse", "--verify", "HEAD"], cwd=sub_path, check=False).returncode == 0
    if not has_head:
        # datalad create should have committed .datalad/.gitattributes,
        # but if it failed, create a minimal initial commit now.
        # also ensure annex is initialized and annex.version is set
        # (git-annex init sets both uuid+version)
        _run(["git", "add", "-A"], cwd=sub_path, check=False)
        _run(["git", "commit", "--allow-empty", "-m", "Initial dataset"], cwd=sub_path, check=False)

    # 2) annex sanity: annex.version must exist
    out = _run(["git", "config", "--get", "annex.version"], cwd=sub_path, check=False, capture=True)
    if out.returncode != 0 or not (out.stdout or "").strip():
        # (re)init annex to set version/uuid
        _run(["git", "annex", "init"], cwd=sub_path, check=True)
        # ensure there is a commit recording annex config if needed
        _run(["git", "add", "-A"], cwd=sub_path, check=False)
        _run(["git", "commit", "--allow-empty", "-m", "Initialize annex"], cwd=sub_path, check=False)

def datalad_make_subdataset(target: str | os.PathLike,
                            base_dir: str | os.PathLike = "data") -> pathlib.Path:
    """
    Convert a *directory* into a DataLad subdataset (robust & idempotent).

    - Refuses files (single files stay in the superdataset).
    - If already a dataset:
        * If not registered: register it.
        * If registered: no-op.
    - If not yet a dataset:
        * Untrack from superdataset **only if** git currently tracks anything there.
        * datalad create --force
        * ensure initial commit & annex metadata
        * register & save
    """
    root = pathlib.Path(PROJECT_ROOT).resolve()
    if not (root / ".datalad").is_dir():
        raise RuntimeError(f"{root} is not a DataLad dataset (no .datalad/). Initialize it first.")

    t = pathlib.Path(target)
    # bare name → put under base_dir; otherwise keep given path
    if not t.is_absolute():
        sub_path = (root / (base_dir if len(t.parts) == 1 else "") / t).resolve()
    else:
        sub_path = t.resolve()

    # must be inside project
    sub_path.relative_to(root)

    if sub_path.exists() and sub_path.is_file():
        raise ValueError(f"{sub_path} is a file. Single-file datasets stay in the superdataset.")

    # ensure dir exists
    sub_path.mkdir(parents=True, exist_ok=True)
    rel = os.path.relpath(sub_path, start=root).replace("\\", "/")

    # --- already a dataset? just (re)register and return
    if (sub_path / ".datalad").is_dir():
        # check registration
        out = _run(
            ["datalad", "subdatasets", "--recursive", "--result-renderer", "json"],
            cwd=root, check=False, capture=True
        ).stdout or ""
        already_registered = any(f'"path": "{sub_path.as_posix()}"' in line for line in out.splitlines())
        if not already_registered:
            _run(["datalad", "subdatasets", "--add", rel], cwd=root, check=False)
            _run(["datalad", "save", "-d", str(root),
                  "-m", f"Register existing subdataset {rel}", rel],
                 cwd=root, check=False)
        return sub_path

    # --- fresh conversion path

    # 1) Untrack from superdataset index only if Git tracks anything there
    if _git_tracks_anything(root, rel):
        _run(["git", "rm", "-r", "--cached", "--ignore-unmatch", rel], cwd=root, check=True)
        # Save the untracking (don’t force a path-bound commit if Git had nothing)
        _run(["datalad", "save", "-d", str(root),
              "-m", f"Untrack contents before making subdataset {rel}"],
             cwd=root, check=False)

    # 2) Ensure .gitignore allows the directory entry (so gitlink can be committed)
    gi = root / ".gitignore"
    if gi.exists():
        lines = gi.read_text(encoding="utf-8").splitlines()
        top = rel.split("/", 1)[0]
        if f"{top}/" in lines and f"!{top}/" not in lines:
            lines.append(f"!{top}/")
            gi.write_text("\n".join(lines) + "\n", encoding="utf-8")
            _run(["datalad", "save", "-d", str(root),
                  "-m", f"Adjust .gitignore for subdataset {top}/"], cwd=root, check=False)

    # 3) Create the subdataset (works for non-empty dirs)
    _run(["datalad", "create", "-d", str(root), "-c", "yoda", "--force", rel],
         cwd=root, check=True)

    # 4) Ensure it actually has a commit and a sane annex state
    _ensure_initial_commit_and_annex(sub_path)

    # 5) (Re)register & save pointer in superdataset
    _run(["datalad", "subdatasets", "--add", rel], cwd=root, check=False)
    _run(["datalad", "-C", rel, "save", "-m", "Initialize/convert to subdataset"],
         cwd=root, check=False)
    _run(["datalad", "save", "-d", str(root), "-m", f"Register subdataset {rel}", rel],
         cwd=root, check=False)

    return sub_path


def datalad_make_subdataset_old(target: str | os.PathLike, base_dir: str | os.PathLike = "data") -> pathlib.Path:
    """
    Convert a *directory* into a DataLad subdataset.
    - Works when the directory is non-empty (uses --force).
    - Does NOT uninstall any annex; only untracks the path from the superdataset index.
    - Single files are refused (keep them in the superdataset).
    """
    root = pathlib.Path(PROJECT_ROOT).resolve()
    if not (root / ".datalad").is_dir():
        raise RuntimeError(f"{root} is not a DataLad dataset (no .datalad/). Initialize it first.")

    t = pathlib.Path(target)
    # Bare name → place under ./data/<name>; otherwise keep given relative/absolute Path
    if not t.is_absolute():
        sub_path = (root / (base_dir if len(t.parts) == 1 else "") / t).resolve()
    else:
        sub_path = t.resolve()

    # must be inside project
    sub_path.relative_to(root)

    if sub_path.exists() and sub_path.is_file():
        raise ValueError(f"{sub_path} is a file. Single-file datasets stay in the superdataset.")

    # ensure directory exists
    sub_path.mkdir(parents=True, exist_ok=True)

    rel = os.path.relpath(sub_path, start=root).replace("\\", "/")

    # 1) Untrack from superdataset index (but keep files on disk)
    #    This avoids any annex “uninstall/dead” logic on the root.
    subprocess.run(
        ["git", "rm", "-r", "--cached", "--ignore-unmatch", rel],
        cwd=root, check=False
    )

    # 2) Make sure .gitignore allows the directory entry so the gitlink can be committed
    gi = root / ".gitignore"
    if gi.exists():
        lines = gi.read_text(encoding="utf-8").splitlines()
        top = rel.split("/", 1)[0]
        if f"{top}/" in lines and f"!{top}/" not in lines:
            lines.append(f"!{top}/")
            gi.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 3) Create/register the subdataset (OK in non-empty dir thanks to --force)
    if not (sub_path / ".datalad").is_dir():
        subprocess.run(
            ["datalad", "create", "-d", str(root), "-c", "yoda", "--force", rel],
            cwd=root, check=True
        )
    else:
        subprocess.run(["datalad", "subdatasets", "--add", rel], cwd=root, check=False)

    # 4) Save inside subdataset and record pointer in superdataset
    subprocess.run(["datalad", "-C", rel, "save", "-m", "Initialize/convert to subdataset"], cwd=root, check=False)
    subprocess.run(["datalad", "save", "-d", str(root), "-m", f"Register subdataset {rel}", rel], cwd=root, check=False)

    return sub_path


def datalad_annex_for_file(file_path: pathlib.Path):
    """Make sure this specific file is annexed by the superdataset."""
    rel = os.path.relpath(file_path, PROJECT_ROOT).replace("\\", "/")
    ga = PROJECT_ROOT / ".gitattributes"
    line = f"{rel} annex.largefiles=anything\n"

    existing = ga.read_text(encoding="utf-8").splitlines(True) if ga.exists() else []
    if not any(l.strip() == line.strip() for l in existing):
        # keep other attrs, drop duplicate largefiles lines for the same file
        kept = [l for l in existing if not (l.startswith(rel) and "annex.largefiles=" in l)]
        kept.append(line)
        ga.write_text("".join(kept), encoding="utf-8")

    # save the attribute change + the file content in the superdataset
    subprocess.run(["datalad", "save", "-m", f"Annex policy for {rel}"], check=False, cwd=PROJECT_ROOT)


# rclone
def install_rclone(install_path):
    """Download and extract rclone to the specified bin folder."""

    def download_rclone(install_path="./bin"):
        os_type = platform.system().lower()

        # Set the URL and executable name based on the OS
        if os_type == "windows":
            url = "https://downloads.rclone.org/rclone-current-windows-amd64.zip"
            rclone_executable = "rclone.exe"
        elif os_type in ["linux", "darwin"]:  # "Darwin" is the system name for macOS
            url = (
                "https://downloads.rclone.org/rclone-current-linux-amd64.zip"
                if os_type == "linux"
                else "https://downloads.rclone.org/rclone-current-osx-amd64.zip"
            )
            rclone_executable = "rclone"
        else:
            print(f"Unsupported operating system: {os_type}. Please install rclone manually.")
            return None

        # Create the bin folder if it doesn't exist
        install_path = str(PROJECT_ROOT / pathlib.Path(install_path))
        os.makedirs(install_path, exist_ok=True)

        # Download rclone
        local_zip = os.path.join(install_path, "rclone.zip")
        print(f"Downloading rclone for {os_type} to {local_zip}...")
        response = requests.get(url)
        if response.status_code == 200:
            with open(local_zip, "wb") as file:
                file.write(response.content)
            print("Download complete.")
        else:
            print("Failed to download rclone. Please check the URL.")
            return None

        # Extract the rclone executable
        print("Extracting rclone...")
        with zipfile.ZipFile(local_zip, "r") as zip_ref:
            zip_ref.extractall(install_path)

        rclone_folder = glob.glob(os.path.join(install_path, "rclone-*"))

        if not rclone_folder or len(rclone_folder) > 1:
            print(f"More than one 'rclone-*' folder detected in {install_path}")
            return None

        # Clean up by deleting the zip file
        os.remove(local_zip)

        rclone_path = os.path.join(install_path, rclone_folder[0], rclone_executable)
        print(f"rclone installed successfully at {rclone_path}.")

        rclone_path = os.path.abspath(rclone_path)

        os.chmod(rclone_path, 0o755)
        return rclone_path

    if not is_installed("rclone", "Rclone"):
        rclone_path = download_rclone(install_path)
        return exe_to_path("rclone", os.path.dirname(rclone_path))
    return True

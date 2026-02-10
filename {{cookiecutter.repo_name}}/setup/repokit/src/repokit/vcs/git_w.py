import os
import pathlib
import platform
import subprocess
import urllib.request

from repokit_common import (
    PROJECT_ROOT,
    ask_yes_no,
    exe_to_path,
    git_user_info,
    is_installed,
    load_from_env,
)


# Git Functions:
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
                commit_cmd = (
                    ["git", "commit", "-m", msg]
                    if msg
                    else ["git", "commit", "--allow-empty", "-m", ""]
                )
                subprocess.run(commit_cmd, check=True, cwd=path)
            except subprocess.CalledProcessError:
                print("No Git changes to commit.")
            return True

        print("Not a Git/DataLad repository at:", path)
        return False

    except subprocess.CalledProcessError as e:
        print(f"Commit/save failed: {e}")
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

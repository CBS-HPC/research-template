import getpass
import os

from .base import PROJECT_ROOT
from .paths import check_path_format
from .secretstore import load_from_env, save_to_env


def split_multi(val: str | None) -> list[str]:
    if not val or not isinstance(val, str):
        return None
    raw = [p.strip() for p in val.replace(";", ",").split(",")]
    return [p for p in raw if p]


def ask_yes_no(question):
    """
    Prompt the user with a yes/no question and validate the input.

    Args:
        question (str): The question to display to the user.

    Returns
    -------
        bool: True if the user confirms (yes/y), False if the user declines (no/n).
    """
    while True:
        response = input(question).strip().lower()
        if response in {"yes", "y"}:
            return True
        elif response in {"no", "n"}:
            return False
        else:
            print("Invalid response. Please answer with 'yes' or 'no'.")


# Setting Options
def git_user_info(version_control):
    if version_control.lower() in ["git", "datalad", "dvc"]:
        # Load defaults

        default_names = split_multi(load_from_env("AUTHORS", ".cookiecutter"))
        default_emails = split_multi(load_from_env("EMAIL", ".cookiecutter"))

        git_name = None
        git_email = None

        while not git_name or not git_email:
            # Prompt with defaults
            name_prompt = f"Enter your Git user name [{default_names[0]}]: "
            email_prompt = f"Enter your Git user email [{default_emails[0]}]: "

            git_name = input(name_prompt).strip() or default_names[0]
            git_email = input(email_prompt).strip() or default_emails[0]

            # Check if inputs are valid
            if not git_name or not git_email:
                print("Both name and email are required.")

        print(f"\nUsing Git user name: {git_name}")
        print(f"Using Git user email: {git_email}\n")

        save_to_env(git_name, "GIT_USER")
        save_to_env(git_email, "GIT_EMAIL")
        return git_name, git_email
    else:
        return None, None


def repo_user_info(version_control, repo_name, code_repo):
    valid_repos = ["github", "gitlab", "codeberg"]
    valid_vcs = ["git", "datalad", "dvc"]

    if code_repo.lower() in valid_repos and version_control.lower() in valid_vcs:
        repo_user = None
        privacy_setting = None
        default_setting = "private"
        hostname = None
        default_host = {
            "github": "github.com",
            "gitlab": "gitlab.com",
            "codeberg": "codeberg.org",
        }.get(code_repo.lower())

        while not hostname or not repo_user or not privacy_setting:
            # hostname = input(f"Enter {code_repo} hostname [{default_host}]: ").strip() or default_host
            hostname = default_host
            repo_user = input(f"Enter your {code_repo} username: ").strip()
            privacy_setting = (
                input(f"Select the repository visibility (private/public) [{default_setting}]: ")
                .strip()
                .lower()
                or default_setting
            )

            if privacy_setting not in ["private", "public"]:
                print("Invalid choice. Defaulting to 'private'.")
                privacy_setting = None

        # Assign keys based on repository
        if code_repo.lower() == "github":
            token_env_key = "GITHUB_TOKEN"
            user_env_key = "GITHUB_USER"
            host_env_key = "GITHUB_HOSTNAME"
            repo_env_key = "GITHUB_REPO"
            privacy_env_key = "GITHUB_PRIVACY"
        elif code_repo.lower() == "gitlab":
            token_env_key = "GITLAB_TOKEN"
            user_env_key = "GITLAB_USER"
            host_env_key = "GITLAB_HOSTNAME"
            repo_env_key = "GITLAB_REPO"
            privacy_env_key = "GITLAB_PRIVACY"
        elif code_repo.lower() == "codeberg":
            token_env_key = "CODEBERG_TOKEN"
            user_env_key = "CODEBERG_USER"
            host_env_key = "CODEBERG_HOSTNAME"
            repo_env_key = "CODEBERG_REPO"
            privacy_env_key = "CODEBERG_PRIVACY"

        # Token retrieval
        token = load_from_env(token_env_key)
        if not token:
            while not token:
                token = getpass.getpass(f"Enter {code_repo} token: ").strip()

        # Save credentials and info
        save_to_env(repo_user, user_env_key)
        save_to_env(privacy_setting, privacy_env_key)
        save_to_env(repo_name, repo_env_key)
        save_to_env(token, token_env_key)
        save_to_env(hostname, host_env_key)

        return repo_user, privacy_setting, token, hostname
    else:
        return None, None, None, None


def remote_user_info(remote_name):
    """Prompt for remote login credentials and base folder path."""

    def ensure_repo_suffix(folder, repo):
        folder = folder.strip().replace("\\", "/").rstrip("/")
        
        # Normalize PROJECT_ROOT for comparison
        normalized_project_root = PROJECT_ROOT.replace("\\", "/").rstrip("/")
        
        # Check if paths are the same
        if os.path.normpath(folder) == os.path.normpath(normalized_project_root):
            folder = folder + "_backup"
        
        # Then ensure repo name is in the path
        if not folder.endswith(repo):
            folder = os.path.join(folder, repo).replace("\\", "/")
        
        return folder

    if remote_name.strip().lower() == "deic storage":
        remote_name = "deic-storage"

    repo_name = load_from_env("REPO_NAME", ".cookiecutter")

    if remote_name.lower() == "deic-storage":
        email = load_from_env("DEIC_EMAIL")
        password = load_from_env("DEIC_PASS")
        base_folder = load_from_env("DEIC_BASE")

        if email and password and base_folder:
            base_folder = ensure_repo_suffix(base_folder, repo_name)
            return email, password, base_folder

        default_email = load_from_env("EMAIL", ".cookiecutter")
        default_base = f"RClone_backup/{repo_name}"
        base_folder = (
            input(f"Enter base folder for {remote_name} [{default_base}]: ").strip() or default_base
        )
        base_folder = ensure_repo_suffix(base_folder, repo_name)

        email = password = None
        while not email or not password:
            email = (
                input(f"Please enter email to Deic-Storage [{default_email}]: ").strip()
                or default_email
            )
            password = getpass.getpass("Please enter password to Deic-Storage: ").strip()

            if not email or not password:
                print("Both email and password are required.\n")

        print(f"\nUsing email: {email}")
        print(f"Using base folder: {base_folder}\n")

        save_to_env(email, "DEIC_EMAIL")
        save_to_env(password, "DEIC_PASS")
        save_to_env(base_folder, "DEIC_BASE")

        return email, password, base_folder

    elif remote_name.lower() == "local":
        base_folder = (
            input("Please enter the local path for rclone: ")
            .strip()
            .replace("'", "")
            .replace('"', "")
        )
        base_folder = check_path_format(base_folder)
        if not os.path.isdir(base_folder):
            print(f"Error: The specified local path does not exist{base_folder}")
            return None, None, None
        base_folder = ensure_repo_suffix(base_folder, repo_name)
        return None, None, base_folder

    elif remote_name.lower() != "none":
        default_base = f"RClone_backup/{repo_name}"
        base_folder = (
            input(f"Enter base folder for {remote_name} [{default_base}]: ").strip() or default_base
        )
        base_folder = ensure_repo_suffix(base_folder, repo_name)
        return None, None, base_folder

    else:
        return None, None, None


def prompt_user(question, options):
    """
    Prompts the user with a question and a list of options to select from.

    Args:
        question (str): The question to display to the user.
        options (list): List of options to display.

    Returns
    -------
        str: The user's selected option.
    """
    print(question)
    for i, option in enumerate(options, start=1):
        print(f"{i}. {option}")

    while True:
        try:
            choice = int(input("Choose from above (enter number): "))
            if 1 <= choice <= len(options):
                selected_option = options[choice - 1]
                return selected_option
            else:
                print(f"Invalid choice. Please select a number between 1 and {len(options)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
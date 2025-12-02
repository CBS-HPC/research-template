import os
import pathlib
import platform
import re
import subprocess
import sys
import shutil



def run_bash(script_path, env_path=None, python_env_manager=None, main_setup=None):
    script_path = str(pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(script_path))
    env_path = str(pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(env_path))
    main_setup = str(pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(main_setup))

    # Make sure the script is executable
    os.chmod(script_path, 0o755)

    # Run the script with the additional paths as arguments
    subprocess.check_call(
        ["bash", "-i", script_path, env_path, python_env_manager.lower(), main_setup]
    )  # Pass repo_name and paths to the script
    print(f"Script {script_path} executed successfully.")


def run_powershell(script_path, env_path=None, python_env_manager=None, main_setup=None):
    script_path = str(pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(script_path))
    env_path = str(pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(env_path))
    main_setup = str(pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(main_setup))

    subprocess.check_call(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            script_path,
            env_path,
            python_env_manager,
            main_setup,
        ]
    )
    print(f"Script {script_path} executed successfully.")


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


def correct_format(programming_language, authors, orcids):
    if "(Pre-installation required)" in programming_language:
        programming_language = programming_language.replace(" (Pre-installation required)", "")

    if "Your Name(s) (multiple authors can be added by using a ';' or ',' delimiter)" in authors:
        authors = authors.replace(
            "Your Name(s) (multiple authors can be added by using a ';' or ',' delimiter)",
            "Not Provided",
        )
    if "Your Name(s) (multiple authors can be added by using a ';' or ',' delimiter)" in orcids:
        orcids = orcids.replace(
            "Your Name(s) (multiple authors can be added by using a ';' or ',' delimiter)",
            "Not Provided",
        )

    return programming_language, authors, orcids


def set_options(programming_language: str, version_control: str):
    """
    Ask the user for environment choices (Python & R), repo hosting, and optional
    remote storage. Returns a 7-tuple:
      (programming_language, python_env_manager, r_env_manager,
       code_repo, remote_storage, conda_r_version, conda_python_version)

    - python_env_manager ∈ {"Conda","Venv"}
    - r_env_manager ∈ {"Conda","Pre-installed R",""}  (empty string when not relevant)
    - *_version is None or a validated version string
    """

    # ---------------- helpers ----------------
    def is_valid_version(version: str, software: str) -> bool:
        patterns = {
            "r": r"^4(\.\d+){0,2}$",        # '4', '4.x', '4.x.y'
            "python": r"^3(\.\d+){0,2}$",   # '3', '3.x', '3.x.y'
        }
        key = software.lower()
        if key not in patterns:
            raise ValueError("software must be 'r' or 'python'")
        return version == "" or bool(re.fullmatch(patterns[key], version))

    def conda_label(kind: str) -> str:
        """kind: 'Python' or 'R' -> label that mentions Miniforge auto-install if conda missing."""
        has_conda = shutil.which("conda") is not None
        base = f"Conda (Choose {kind} version)"
        return base if has_conda else f"{base} — auto-installs Miniforge"

    def select_versions(r_mgr: str, py_mgr: str) -> tuple[str | None, str | None]:
        r_ver = None
        if r_mgr.lower() == "conda":
            r_ver = input(
                "Optional: specify R version for Conda (e.g. '4.4.3', '4.3', or '4'). "
                "Leave empty for Conda's default: "
            ).strip()
            if r_ver and not is_valid_version(r_ver, "r"):
                print("Invalid R version format. Using default.")
                r_ver = None

        py_ver = None
        if py_mgr.lower() == "conda":
            py_ver = input(
                "Optional: specify Python version for Conda (e.g. '3.12', '3.9.3', or '3'). "
                "Leave empty for Conda's default: "
            ).strip()
            if py_ver and not is_valid_version(py_ver, "python"):
                print("Invalid Python version format. Using default.")
                py_ver = None

        return r_ver, py_ver

    def normalize_env_choice(label: str | None, default: str = "Venv") -> str:
        """Map UI labels to canonical keys {'Conda','Venv'}."""
        if not label:
            return default
        lab = label.lower()
        if lab.startswith("conda"):
            return "Conda"
        if lab.startswith("uv"):  # "UV (venv backend) ..."
            return "Venv"
        return default
    # -----------------------------------------

    lang = (programming_language or "").strip()
    lang_l = lang.lower()

    # Python option labels
    py_version_label = subprocess.check_output([sys.executable, "--version"]).decode().strip()
    environment_opts = [
        f"UV (venv backend) ({py_version_label})",
        conda_label("Python"),
    ]

    # Decide R env manager (only relevant when primary language is R)
    if lang_l == "r":
        r_choice = prompt_user(
            "R environment: use Conda or pre-installed R?",
            [conda_label("R"), "Pre-installed R"]
        )
        r_env_manager = "Conda" if r_choice.lower().startswith("conda") else "Pre-installed R"

        # Python is still used for setup; prefer Conda if we already chose it for R
        python_env_manager = "Conda" if r_env_manager == "Conda" else None
        python_question = "Python is needed for setup. Create a Python environment using:"
    else:
        r_env_manager = ""  # not relevant
        python_env_manager = None
        python_question = (
            "Do you want to create a new Python environment using:"
            if lang_l == "python"
            else "Create a Python environment (used for project setup) using:"
        )

    # Force venv for languages where Conda isn't required/typical
    if lang_l in {"stata", "matlab", "sas"}:
        python_env_manager = "Venv"

    # If still undecided, ask the Python env question
    if python_env_manager is None:
        choice = prompt_user(python_question, environment_opts)
        python_env_manager = normalize_env_choice(choice)

    # Final normalization (safety)
    python_env_manager = normalize_env_choice(python_env_manager)

    # Ask for optional versions (only when Conda is chosen)
    conda_r_version, conda_python_version = select_versions(r_env_manager, python_env_manager)

    # Repo host (only if version control is used)
    vc_l = (version_control or "").strip().lower()
    if vc_l in {"git", "datalad", "dvc"}:
        code_repo = prompt_user(
            "Choose a code repository host:",
            ["GitHub", "GitLab", "Codeberg", "None"]
        )
    else:
        code_repo = "None"

    # Remote storage (only for DataLad/DVC)
    if vc_l in {"datalad", "dvc"}:
        remote_storage = prompt_user(
            f"Set up remote storage for your {version_control} repo:",
            ["Dropbox", "Local Path", "None"]
        )
    else:
        remote_storage = "None"

    return (
        programming_language,   # keep original casing
        python_env_manager,     # "Conda" | "Venv"
        r_env_manager,          # "Conda" | "Pre-installed R" | ""
        code_repo,
        remote_storage,
        conda_r_version,        # None or str
        conda_python_version,   # None or str
    )



main_setup = "./setup/main_setup.py"
setup_bash = "./run_setup.sh"
setup_powershell = "./run_setup.ps1"

project_name = "{{cookiecutter.project_name}}"
project_description = "Insert project description here"
authors = "{{cookiecutter.author_name}}"
orcids = "{{cookiecutter.orcid}}"
email = "{{cookiecutter.email}}"
version = "{{cookiecutter.version}}"
code_license = "{{cookiecutter.code_license}}"
doc_license = "{{cookiecutter.documentation_license}}"
data_license = "{{cookiecutter.data_license}}"
repo_name = "{{cookiecutter.repo_name}}"
version_control = "{{cookiecutter.version_control}}"
programming_language = "{{cookiecutter.programming_language}}"


programming_language, authors, orcids = correct_format(programming_language, authors, orcids)
(
    programming_language,
    python_env_manager,
    r_env_manager,
    code_repo,
    remote_storage,
    conda_r_version,
    conda_python_version,
) = set_options(programming_language, version_control)

from repokit.common import (
    ask_yes_no,
    check_path_format,
    git_user_info,
    repo_user_info,
    save_to_env,
    PROJECT_ROOT
)

if (
    str(doc_license).lower() == "none"
    and str(data_license).lower() == "none"
    and str(code_license).lower() != "none"
    ):
    license_path = PROJECT_ROOT / "LICENSE.md"

if license_path.exists():
    try:
        license_path.unlink()
        print(f"Deleted license file: {license_path}")
    except Exception as e:
        print(f"Failed to delete {license_path}: {e}")


def set_programming_language(programming_language, r_env_manager):
    def search_apps(app: str):
        """
        Search for executables matching partial app names in the system's PATH.

        Args:
            app (str): Partial name of the application to search for.

        Returns
        -------
            list: A list of paths matching the executable pattern.
        """
        found_paths = []
        system_paths = os.environ["PATH"].split(os.pathsep)  # Split PATH into directories

        # Check if the app is a single letter
        is_single_letter_app = len(app) == 1

        for directory in system_paths:
            if os.path.isdir(directory):  # Check if the PATH directory exists
                try:
                    for file in os.listdir(directory):
                        # Extract the filename without extension
                        filename_without_ext = os.path.splitext(os.path.basename(file))[0].lower()

                        # Match exactly if the app is a single letter, or partially if it's longer
                        if is_single_letter_app:
                            if filename_without_ext == app.lower():
                                full_path = os.path.join(directory, file)
                                if os.access(full_path, os.X_OK):  # Check if file is executable
                                    found_paths.append(full_path)
                        else:
                            if app.lower() in filename_without_ext:
                                full_path = os.path.join(directory, file)
                                if os.access(full_path, os.X_OK):  # Check if file is executable
                                    found_paths.append(full_path)

                except PermissionError:
                    continue  # Skip directories with permission issues

        if not found_paths:
            print(f"No executables found for app '{app}'.")

        found_paths = list(set(found_paths))

        return found_paths

    def choose_apps(app: str, found_apps: list):
        """
        Prompt the user to choose one path for each application pattern,
        with an option to select 'None'.

        Args:
            app (str): The application name to choose a path for.
            found_apps (list): List of matching paths for the application.

        Returns
        -------
            tuple: A tuple containing the filename without extension and the selected path.
                Returns (None, None) if 'Select None' is chosen.
        """
        if len(found_apps) == 0:
            return None, None

        print(f"\nChoose a path for '{app}':")
        # Add the 'Select None' option
        print("  [0] Select None")

        for i, path in enumerate(found_apps):
            print(f"  [{i + 1}] {path}")

        while True:
            try:
                choice = int(input(f"Enter your choice (0-{len(found_apps)}): "))

                if choice == 0:  # Select None option
                    print("No path selected.")
                    return None, None
                elif 1 <= choice <= len(found_apps):  # Valid path selection
                    selected_path = found_apps[choice - 1]
                    print(f"Selected: {selected_path}")

                    # Extract filename without extension
                    filename_with_extension = os.path.basename(selected_path)
                    filename = os.path.splitext(filename_with_extension)[0]

                    return filename, selected_path
                else:
                    print("Invalid choice. Please enter a number within the range.")
            except ValueError:
                print("Invalid input. Please enter a valid number.")
                return None, None

    def manual_apps():
        """
        Allow manual input of the executable path if no path is chosen
        and automatically resolve the application name. Re-prompts if the path
        contains single backslashes.

        Returns
        -------
            tuple: A tuple containing the resolved application name and selected path.
        """
        print("\nNo path was selected. Please input the executable path manually.")

        msg = (
            "Enter the full path to the executable e.g. 'C:/Program Files/Stata18/StataSE-64.exe':"
        )
        # Prompt the user to input the path to the executable
        while True:
            selected_path = input(msg).strip()
            selected_path = selected_path.replace("'", "").replace('"', "")
            selected_path = check_path_format(selected_path)

            if os.path.isfile(selected_path) and os.access(
                selected_path, os.X_OK
            ):  # Validate the path
                break  # Exit loop if the file exists and is executable
            else:
                answer = ask_yes_no("Invalid path. Do you want to input a new path? (yes/no)")

                if answer:
                    msg = "Enter the full path to the executable with forward slashes('/') e.g. 'C:/Program Files/Stata18/StataSE-64.exe':"
                    continue  # Re-prompt the user if single backslashes are detected
                else:
                    return None, None

        # Resolve the application name by extracting the filename without extension
        filename_with_extension = os.path.basename(selected_path)
        filename = os.path.splitext(filename_with_extension)[0]

        return filename, selected_path

    if programming_language.lower() in ["stata", "matlab", "sas"] or (
        programming_language.lower() == "r" and r_env_manager.lower() != "conda"
    ):
        found_apps = search_apps(programming_language)
        _, selected_path = choose_apps(programming_language, found_apps)

        if not selected_path:
            _, selected_path = manual_apps()

        if selected_path:
            save_to_env(selected_path, programming_language.upper())
            save_to_env(programming_language.lower(), "PROGRAMMING_LANGUAGE", ".cookiecutter")

            if programming_language.lower() == "r":
                r_dir = os.path.dirname(selected_path)
                rscript_path = os.path.join(r_dir, "Rscript.exe")
                if os.path.isfile(rscript_path) and os.access(rscript_path, os.X_OK):
                    save_to_env(rscript_path, "RSCRIPT")
        else:
            print(f"{programming_language} path has not been set")

    return programming_language


programming_language = set_programming_language(programming_language, r_env_manager)

# Set project info to .cookiecutter
save_to_env(project_name, "PROJECT_NAME", ".cookiecutter")
save_to_env(repo_name, "REPO_NAME", ".cookiecutter")
save_to_env(project_description, "PROJECT_DESCRIPTION", ".cookiecutter")
save_to_env(version, "VERSION", ".cookiecutter")
save_to_env(authors, "AUTHORS", ".cookiecutter")
save_to_env(orcids, "ORCIDS", ".cookiecutter")
save_to_env(email, "EMAIL", ".cookiecutter")
save_to_env(code_license, "CODE_LICENSE", ".cookiecutter")
save_to_env(doc_license, "DOC_LICENSE", ".cookiecutter")
save_to_env(data_license, "DATA_LICENSE", ".cookiecutter")
save_to_env(programming_language, "PROGRAMMING_LANGUAGE", ".cookiecutter")
save_to_env(python_env_manager, "PYTHON_ENV_MANAGER", ".cookiecutter")
save_to_env(version_control, "VERSION_CONTROL", ".cookiecutter")
save_to_env(remote_storage, "REMOTE_STORAGE", ".cookiecutter")
save_to_env(code_repo, "CODE_REPO", ".cookiecutter")

# Set git user info
git_user_info(version_control)

# Set git repo info
repo_user, _, _, _ = repo_user_info(version_control, repo_name, code_repo)



# Create Virtual Environment
from repokit.env import setup_virtual_environment

env_path = setup_virtual_environment(
    version_control,
    python_env_manager,
    r_env_manager,
    repo_name,
    conda_r_version,
    conda_python_version,
)

if not env_path:
    if python_env_manager.lower() == "conda":
        raise ValueError("Creating Conda Environment Failed")
    else:
        raise ValueError("Creating Venv Environment Failed")

if platform.system().lower() == "windows":
    run_powershell(setup_powershell, env_path, python_env_manager, main_setup)
elif platform.system().lower() == "darwin" or platform.system().lower() == "linux":
    os.chmod(
        str(pathlib.Path(__file__).resolve().parent.parent / pathlib.Path("./activate.sh")), 0o755
    )
    os.chmod(
        str(pathlib.Path(__file__).resolve().parent.parent / pathlib.Path("./deactivate.sh")), 0o755
    )
    run_bash(setup_bash, env_path, python_env_manager, main_setup)

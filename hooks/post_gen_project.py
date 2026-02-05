import subprocess
import pathlib
import sys
import platform
import os
import shutil
import json
import re

if sys.version_info < (3, 11):
    TOML_VERSION = "toml"
else:
    TOML_VERSION = "tomli-w"


def run_in_venv():
    if platform.system() == "Windows":
        cmd = r".venv\Scripts\activate.bat && python setup\project_setup.py"
        subprocess.run(
            cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    else:
        cmd = "source .venv/bin/activate && python setup/project_setup.py"
        subprocess.run(
            cmd,
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

def prompt_user(question, options):
    print(question)
    for i, option in enumerate(options, start=1):
        print(f"{i}. {option}")
    while True:
        try:
            choice = int(input("Choose from above (enter number): "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
            print(f"Invalid choice. Please select a number between 1 and {len(options)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def correct_format(programming_language, authors, orcids):
    if "(Pre-installation required)" in programming_language:
        programming_language = programming_language.replace(" (Pre-installation required)", "")
    if "Your Name(s)" in authors:
        authors = "Not Provided"
    if "Your Name(s)" in orcids:
        orcids = "Not Provided"
    return programming_language, authors, orcids


def set_options(programming_language: str, version_control: str):
    def is_valid_version(version: str, software: str) -> bool:
        patterns = {
            "r": r"^4(\.\d+){0,2}$",
            "python": r"^3(\.\d+){0,2}$",
        }
        key = software.lower()
        if key not in patterns:
            raise ValueError("software must be 'r' or 'python'")
        return version == "" or bool(re.fullmatch(patterns[key], version))

    def conda_label(kind: str) -> str:
        has_conda = shutil.which("conda") is not None
        base = f"Conda (Choose {kind} version)"
        return base if has_conda else f"{base} - auto-installs Miniforge"

    def select_versions(r_mgr: str, py_mgr: str):
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
        if not label:
            return default
        lab = label.lower()
        if lab.startswith("conda"):
            return "Conda"
        if lab.startswith("uv"):
            return "Venv"
        return default

    lang = (programming_language or "").strip()
    lang_l = lang.lower()

    py_version_label = subprocess.check_output([sys.executable, "--version"]).decode().strip()
    environment_opts = [
        f"UV (venv backend) ({py_version_label})",
        conda_label("Python"),
    ]

    if lang_l == "r":
        r_choice = prompt_user(
            "R environment: use Conda or pre-installed R?",
            [conda_label("R"), "Pre-installed R"],
        )
        r_env_manager = "Conda" if r_choice.lower().startswith("conda") else "Pre-installed R"
        python_env_manager = "Conda" if r_env_manager == "Conda" else None
        python_question = "Python is needed for setup. Create a Python environment using:"
    else:
        r_env_manager = ""
        python_env_manager = None
        python_question = (
            "Do you want to create a new Python environment using:"
            if lang_l == "python"
            else "Create a Python environment (used for project setup) using:"
        )

    if lang_l in {"stata", "matlab", "sas"}:
        python_env_manager = "Venv"

    if python_env_manager is None:
        choice = prompt_user(python_question, environment_opts)
        python_env_manager = normalize_env_choice(choice)

    python_env_manager = normalize_env_choice(python_env_manager)
    conda_r_version, conda_python_version = select_versions(r_env_manager, python_env_manager)

    vc_l = (version_control or "").strip().lower()
    if vc_l in {"git", "datalad", "dvc"}:
        code_repo = prompt_user(
            "Choose a code repository host:",
            ["GitHub", "GitLab", "Codeberg", "None"],
        )
    else:
        code_repo = "None"

    if vc_l in {"datalad", "dvc"}:
        remote_storage = prompt_user(
            f"Set up remote storage for your {version_control} repo:",
            ["Dropbox", "Local Path", "None"],
        )
    else:
        remote_storage = "None"

    return (
        programming_language,
        python_env_manager,
        r_env_manager,
        code_repo,
        remote_storage,
        conda_r_version,
        conda_python_version,
    )

def write_setup_config():
    project_root = pathlib.Path(__file__).resolve().parent.parent
    setup_dir = project_root / "setup"
    setup_dir.mkdir(exist_ok=True)
    programming_language = "{{cookiecutter.programming_language}}"
    version_control = "{{cookiecutter.version_control}}"
    authors = "{{cookiecutter.author_name}}"
    orcids = "{{cookiecutter.orcid}}"
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
    payload = {
        "programming_language": programming_language,
        "authors": authors,
        "orcids": orcids,
        "python_env_manager": python_env_manager,
        "r_env_manager": r_env_manager,
        "code_repo": code_repo,
        "remote_storage": remote_storage,
        "conda_r_version": conda_r_version,
        "conda_python_version": conda_python_version,
    }
    config_path = setup_dir / ".setup_config.json"
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(config_path)

def install_uv():
    """Ensure 'uv' is installed and usable."""
    try:
        subprocess.run(
            ["uv", "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "uv"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["uv", "--version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except subprocess.CalledProcessError:
            return False


def create_with_uv():
    """Create virtual environment using uv with UV_LINK_MODE=copy to avoid hardlink errors,
    then run setup with the interpreter from .venv (not `uv run`)."""

    env = os.environ.copy()
    env["UV_LINK_MODE"] = "copy"

    # Create venv and lock deps with uv
    subprocess.run(
        ["uv", "venv"],
        check=True,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["uv", "lock"],
        check=True,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        subprocess.run(
            [
                "uv",
                "add",
                "--upgrade",
                "uv",
                "pip",
                "setuptools",
                "wheel",
                "python-dotenv",
                "pathspec",
                "pyyaml",
                TOML_VERSION,
            ],
            check=True,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print("Failed to add packages with uv add --upgrade (even with link-mode=copy).")
        raise

    # Use the venv's python instead of `uv run` as it corrupts runn_setup.ps1/.sh
    python_exe = (
        os.path.join(".venv", "Scripts", "python.exe")
        if os.name == "nt"
        else os.path.join(".venv", "bin", "python")
    )
    if not os.path.exists(python_exe):
        raise FileNotFoundError(
            f"Python interpreter not found at {python_exe}. Did 'uv venv' succeed?"
        )

    config_path = write_setup_config()
    subprocess.run([python_exe, "setup/project_setup.py", "--config", config_path], check=True, env=env)


def create_with_pip():
    # Always bootstrap uv and then use the uv-based path
    subprocess.run(
        [sys.executable, "-m", "ensurepip", "--upgrade"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "uv"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    create_with_uv()


def main():
    env_path = pathlib.Path(".venv")
    if not env_path.exists():
        if install_uv():
            create_with_uv()
            return

    create_with_pip()
    return


if __name__ == "__main__":
    main()

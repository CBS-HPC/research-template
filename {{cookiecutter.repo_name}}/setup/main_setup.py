import os
import pathlib
import platform
import subprocess
import sys
import shutil
import stat

PROJECT_DIR = pathlib.Path(__file__).resolve().parent.parent
SETUP_DIR = pathlib.Path(__file__).resolve().parent
REPOKIT_DIR = SETUP_DIR / "repokit"
REPOKIT_EXTERNAL = REPOKIT_DIR / "external"
LOCAL_PACKAGES = [
    REPOKIT_DIR,
    REPOKIT_EXTERNAL / "repokit-common",
    REPOKIT_EXTERNAL / "repokit-backup",
    REPOKIT_EXTERNAL / "repokit-dmp",
]

# Add local package sources to sys.path so imports work without installing
_LOCAL_SRC_PATHS = [
    REPOKIT_DIR / "src",
    REPOKIT_EXTERNAL / "repokit-common" / "src",
    REPOKIT_EXTERNAL / "repokit-backup" / "src",
    REPOKIT_EXTERNAL / "repokit-dmp" / "src",
]
for _p in _LOCAL_SRC_PATHS:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def install_py_package(setup_path: str = "./setup", editable: bool = True) -> tuple[bool, str]:
    """
    Install the local package at `setup_path`, preferring uv and falling back to pip.

    Returns
    -------
        (ok: bool, method: str) where method is one of {"uv", "python -m uv", "pip"}.
    """
    setup_dir = pathlib.Path(setup_path).resolve()
    if not setup_dir.exists():
        raise FileNotFoundError(f"setup_path does not exist: {setup_dir}")

    # Build the args once
    editable_args = ["-e", "."] if editable else ["."]
    uv_mod_cmd = [sys.executable, "-m", "uv", "pip", "install", *editable_args]
    pip_cmd = [sys.executable, "-m", "pip", "install", *editable_args]

    # Do work in the target directory, but restore CWD afterwards
    cwd = os.getcwd()
    os.chdir(setup_dir)
    try:
        # 1) Try uv via current interpreter
        result = subprocess.run(uv_mod_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("Installation successful with uv.")
            return True, "uv"
        else:
            print(f"'uv' failed (exit {result.returncode}). stderr:\n{result.stderr.strip()}")

        # 2) Fallback to pip in the current interpreter
        try:
            subprocess.run(
                [sys.executable, "-m", "ensurepip", "--upgrade"],
                capture_output=True,
                text=True,
            )
        except Exception:
            pass

        result = subprocess.run(pip_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("Installation successful with pip.")
            return True, "pip"
        else:
            print(f"pip failed (exit {result.returncode}). stderr:\n{result.stderr.strip()}")

        return False, "pip"
    finally:
        os.chdir(cwd)


def install_local_packages(packages: list[pathlib.Path], editable: bool = True) -> None:
    missing = [p for p in packages if not p.exists()]
    if missing:
        raise FileNotFoundError(
            f"Local package not found: {missing[0]}. Did you init submodules?"
        )

    # Fast path: install all packages in one uv call (via current interpreter)
    uv_mod_cmd = [sys.executable, "-m", "uv", "pip", "install"]
    try:
        args = []
        for package_path in packages:
            args.extend(["-e", str(package_path.resolve())] if editable else [str(package_path.resolve())])
        result = subprocess.run(uv_mod_cmd + args, capture_output=True, text=True)
        if result.returncode == 0:
            print("Installation successful with uv.")
            return
        else:
            print(f"'uv' bulk install failed (exit {result.returncode}). stderr:\n{result.stderr.strip()}")
    except Exception:
        pass

    # Fallback: per-package install (pip fallback handled inside)
    for package_path in packages:
        ok, method = install_py_package(str(package_path), editable=editable)
        if not ok:
            raise RuntimeError(f"Failed to install {package_path} using {method}.")


def _on_rm_error(func, path, exc_info):
    # Make read-only files writable (Windows) then retry
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass
    func(path)


def delete_files(file_paths: list | None = None) -> dict:
    """
    Delete files or folders listed in `file_paths`.
    Returns {absolute_path: "Deleted file" | "Deleted folder" | "Not Found" | "Error: ..."}.
    Paths are resolved relative to the repo root two levels above this file (your original behavior).
    """
    if file_paths is None:
        file_paths = []

    results = {}
    base = pathlib.Path(__file__).resolve().parent.parent

    for raw in file_paths:
        p = (base / pathlib.Path(raw)).resolve()
        key = str(p)
        try:
            if p.is_symlink() or p.is_file():
                p.unlink()
            if p.is_dir():
                shutil.rmtree(p, onerror=_on_rm_error)
        except Exception as e:
            results[key] = f"Error: {e}"

    return results

# Installing packages:
install_local_packages(LOCAL_PACKAGES)

from repokit.ci import ci_config
from repokit_common import (
    load_from_env,
    save_to_env,
    set_program_path,
    set_packages,
    package_installer,
)
from repokit.deps import update_code_dependency, update_env_files, update_setup_dependency
from repokit.repos import setup_repo, setup_version_control
from repokit_dmp.dmp import main as dmp_update
from repokit.readme.template import create_citation_file, creating_readme
from repokit.templates.code import create_scripts
from repokit.vcs import git_push



def intro():
    def create_folders():    
        folders = [
            PROJECT_DIR / "data" / "00_raw",
            PROJECT_DIR / "data" / "01_interim",
            PROJECT_DIR / "data" / "02_processed",
            PROJECT_DIR / "data" / "03_external",
        ]

        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
            (folder / ".gitkeep").touch(exist_ok=True)

    # Ensure the working directory is the project root

    os.chdir(PROJECT_DIR)

    print('Running "Intro"')

    programming_language = load_from_env("PROGRAMMING_LANGUAGE", ".cookiecutter")
    version_control = load_from_env("VERSION_CONTROL", ".cookiecutter")
    code_repo = load_from_env("CODE_REPO", ".cookiecutter")
    project_name = load_from_env("PROJECT_NAME", ".cookiecutter")
    version = load_from_env("VERSION", ".cookiecutter")
    authors = load_from_env("AUTHORS", ".cookiecutter")
    orcids = load_from_env("ORCIDS", ".cookiecutter")


    # Install required packages
    package_installer(required_libraries=set_packages(version_control, programming_language))
    
    # Set to .env
    set_program_path(programming_language)

    # Create Data folders
    create_folders()

    # Create scripts and notebook
    create_scripts(programming_language)

    # Create a citation file
    if code_repo.lower() in ["github","gitlab","codeberg"]:
        create_citation_file(
            project_name, version, authors, orcids, code_repo, doi=None, release_date=None
        )

    # Creating README
    creating_readme(programming_language)

    # Init dmp.json
    dmp_update()


def version_setup():
    # Ensure the working directory is the project root
    os.chdir(PROJECT_DIR)

    print('Running "Version Control Setup"')

    version_control = load_from_env("VERSION_CONTROL", ".cookiecutter")
    repo_name = load_from_env("REPO_NAME", ".cookiecutter")
    code_repo = load_from_env("CODE_REPO", ".cookiecutter")
    remote_storage = load_from_env("REMOTE_STORAGE", ".cookiecutter")

    # Setup Version Control
    setup_version_control(version_control, remote_storage, code_repo, repo_name)


def remote_repo_setup():

    def setup_remote_repository(version_control, code_repo, repo_name, project_description):
        """Handle repository creation and login based on selected platform."""
        if not version_control or not os.path.isdir(".git") or not code_repo:
            return False

        if setup_repo(version_control, code_repo, repo_name, project_description):
            ci_config()
            return True
        
        save_to_env(None, "CODE_REPO", ".cookiecutter")
        return False

    # Ensure the working directory is the project root
    os.chdir(PROJECT_DIR)

    print('Running "Remote Repo Setup"')

    version_control = load_from_env("VERSION_CONTROL", ".cookiecutter")
    repo_name = load_from_env("REPO_NAME", ".cookiecutter")
    code_repo = load_from_env("CODE_REPO", ".cookiecutter")
    project_description = load_from_env("PROJECT_DESCRIPTION", ".cookiecutter")

    # Create Remote Repository
    _ = setup_remote_repository(version_control, code_repo, repo_name, project_description)

    print("Creating 'requirements.txt','environment.yml'")
    update_env_files()
    update_setup_dependency()
    update_code_dependency()

    # Pushing to Git

    #git_push(flag, " Created `requirements.txt`, `environment.yml`,`dependencies.txt` and updated in README.md")


def outro():

    # Ensure the working directory is the project root
    os.chdir(PROJECT_DIR)

    print('Running "Outro"')

    os_type = platform.system().lower()
    if os_type == "windows":
        activate_to_delete = "./activate.sh"
        deactivate_to_delete = "./deactivate.sh"
    elif os_type == "darwin" or os_type == "linux":
        activate_to_delete = "./activate.ps1"
        deactivate_to_delete = "./deactivate.ps1"

    files_to_remove = [
        "./setup/project_setup.py",
        "./run_setup.sh",
        "./run_setup.ps1",
        "./setup/main_setup.py",
        activate_to_delete,
        deactivate_to_delete,
    ]

    if load_from_env("PYTHON_ENV_MANAGER", ".cookiecutter").lower() == "conda":
        print("hello")
        print(load_from_env("PYTHON_ENV_MANAGER", ".cookiecutter").lower() )
        files_to_remove.append("./.venv")
        print(files_to_remove)
   

    # Deleting Setup scripts
    failed = delete_files(files_to_remove)

    # Updating README
    creating_readme(programming_language=load_from_env("PROGRAMMING_LANGUAGE", ".cookiecutter"))

    # Pushing to Git
    git_push(load_from_env("CODE_REPO", ".cookiecutter") != "None", " Created `requirements.txt`, `environment.yml`,`dependencies.txt`, files deleted and updated in README.md")


    print("Environment setup completed successfully.")

    if failed:
        print("The following files/folders need manual deletion:")
        for path, msg in failed.items():
            print(f"  - {path} -> {msg}")


if __name__ == "__main__":

    intro()

    version_setup()

    remote_repo_setup()

    outro()

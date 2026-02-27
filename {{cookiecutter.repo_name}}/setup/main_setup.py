import os
import pathlib
import platform
import shutil
import stat

from repokit_install import install_repokit_packages

PROJECT_DIR = pathlib.Path(__file__).resolve().parent.parent
SETUP_DIR = pathlib.Path(__file__).resolve().parent


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

# Install repokit packages according to [tool.repokit_install] policy.
if not install_repokit_packages(
    ["repokit-common", "repokit-backup", "repokit-dmp", "repokit"],
    PROJECT_DIR,
    SETUP_DIR,
):
    raise RuntimeError("Failed to install repokit packages from configured install sources.")

from repokit_common import (
    load_from_env,
    save_to_env,
    set_program_path,
    set_packages,
    package_installer
)
from repokit.ci import ci_config
from repokit.deps import update_code_dependency, update_env_files
from repokit.repos import setup_repo, setup_version_control
from repokit_dmp.dmp import main as dmp_update
from repokit.readme.template import create_citation_file, creating_readme
from repokit.templates.code import create_scripts
from repokit.vcs import git_push
from repokit_backup.rclone import install_rclone


def intro():
    def create_folders():    
        data_root = PROJECT_DIR / "data"
        folders = [
            data_root / "raw",
            data_root / "interim",
            data_root / "processed",
            data_root / "external",
            data_root / "proprietary",
            data_root / "sensitive",
        ]

        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
            (folder / ".gitkeep").touch(exist_ok=True)

        data_readme = """# Data Folder Structure

This folder contains project datasets and dataset-related metadata.

- `raw/`: Original, immutable input data.
- `interim/`: Intermediate data created during cleaning/transformation.
- `processed/`: Final analysis-ready datasets.
- `external/`: Third-party or externally sourced data.
- `proprietary/`: Data with legal/licensing/NDA/IP restrictions.
- `sensitive/`: Data with confidentiality/privacy restrictions.

For dataset-specific license and access terms, see the project root `dmp.json`.
"""


        readme_path = data_root / "README.md"
        if not readme_path.exists():
            readme_path.write_text(data_readme, encoding="utf-8")

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

    # Ensure rclone is installed for backup module
    install_rclone(install_path = "./bin")


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
        #"./setup/project_setup.py",
        "./run_setup.sh",
        "./run_setup.ps1",
        #"./setup/main_setup.py",
        #"./.setup_config.json",
        activate_to_delete,
        deactivate_to_delete,
        #"./setup/repokit",
        "./setup",
    ]

    if load_from_env("PYTHON_ENV_MANAGER", ".cookiecutter").lower() == "conda":
        files_to_remove.append("./.venv")

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


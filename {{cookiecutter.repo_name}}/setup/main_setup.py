import sys
import os
import pathlib
import subprocess
import platform
from typing import Tuple

PROJECT_DIR = pathlib.Path(__file__).resolve().parent.parent


def install_py_package(setup_path: str = "./setup", editable: bool = True) -> Tuple[bool, str]:
    """
    Install the local package at `setup_path`, preferring uv and falling back to pip.

    Returns:
        (ok: bool, method: str) where method is one of {"uv", "python -m uv", "pip"}.
    """
    setup_dir = pathlib.Path(setup_path).resolve()
    if not setup_dir.exists():
        raise FileNotFoundError(f"setup_path does not exist: {setup_dir}")

    # Build the args once
    editable_args = ["-e", "."] if editable else ["."]
    uv_cmd = ["uv", "pip", "install", *editable_args]
    uv_mod_cmd = [sys.executable, "-m", "uv", "pip", "install", *editable_args]
    pip_cmd = [sys.executable, "-m", "pip", "install", *editable_args]

    # Do work in the target directory, but restore CWD afterwards
    cwd = os.getcwd()
    os.chdir(setup_dir)
    try:
        # 1) Try uv CLI first
        try:
            result = subprocess.run(uv_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("Installation successful with uv.")
                return True, "uv"
            else:
                print(f"uv failed (exit {result.returncode}). stderr:\n{result.stderr.strip()}")
        except FileNotFoundError:
            # uv CLI not found
            pass

        # 2) Try `python -m uv` (if uv is importable as a module)
        try:
            result = subprocess.run(uv_mod_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("Installation successful with python -m uv.")
                return True, "python -m uv"
            else:
                print(f"'python -m uv' failed (exit {result.returncode}). stderr:\n{result.stderr.strip()}")
        except FileNotFoundError:
            # Very old Python envs can raise this if python isn't found, but unlikely.
            pass

        # 3) Fallback to pip
        result = subprocess.run(pip_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("Installation successful with pip.")
            return True, "pip"
        else:
            print(f"pip failed (exit {result.returncode}). stderr:\n{result.stderr.strip()}")
            return False, "pip"
    finally:
        os.chdir(cwd)

# Installing package:
install_py_package("./setup")

from repokit.common import load_from_env, set_program_path, save_to_env, package_installer,set_packages
from repokit.backup import setup_remote_backup
from repokit.readme.template import creating_readme, create_citation_file
from repokit.templates.code import create_scripts
from repokit.vcs import git_push
from repokit.git_remote import setup_version_control, setup_repo
from repokit.deps import update_env_files, update_setup_dependency, update_code_dependency
from repokit.ci import ci_config
from repokit.rdm.dmp import main as dmp_update


def intro():

    def create_folders():
        folders = [
            PROJECT_DIR/"data" / "00_raw",
            PROJECT_DIR/"data" / "01_interim",
            PROJECT_DIR/"data" / "02_processed",
            PROJECT_DIR/"data" / "03_external",
        ]

        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
            (folder / ".gitkeep").touch(exist_ok=True)
    
    # Ensure the working directory is the project root
  
    os.chdir(PROJECT_DIR)

    print('Running "Intro"')

    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")
    version_control = load_from_env("VERSION_CONTROL",".cookiecutter")
    project_name = load_from_env("PROJECT_NAME",".cookiecutter")
    version = load_from_env("VERSION",".cookiecutter")
    authors = load_from_env("AUTHORS",".cookiecutter")
    orcids = load_from_env("ORCIDS",".cookiecutter")

    # Install required libraries
    #if load_from_env("VENV_ENV_PATH") or load_from_env("CONDA_ENV_PATH"):
    #    package_installer(required_libraries = set_packages(load_from_env("VERSION_CONTROL",".cookiecutter"),load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")))

    
    # Set to .env
    set_program_path(programming_language)

    # Create Data folders
    create_folders()
    
    # Create scripts and notebook
    create_scripts(programming_language)
    
    # Create a citation file
    create_citation_file(project_name,version,authors,orcids,version_control,doi=None, release_date=None)

    # Creating README
    creating_readme(programming_language)

    # Init dmp.json
    dmp_update()
               
def version_setup():

    # Ensure the working directory is the project root
    os.chdir(PROJECT_DIR)

    print('Running "Version Control Setup"')

    version_control = load_from_env("VERSION_CONTROL",".cookiecutter")
    repo_name = load_from_env("REPO_NAME",".cookiecutter")
    code_repo = load_from_env("CODE_REPO",".cookiecutter")
    remote_storage = load_from_env("REMOTE_STORAGE",".cookiecutter")

    # Setup Version Control
    setup_version_control(version_control,remote_storage,code_repo,repo_name)

def remote_repo_setup():

    def setup_remote_repository(version_control, code_repo, repo_name, project_description):
        """Handle repository creation and login based on selected platform."""

        if not version_control or not os.path.isdir(".git"):
            return False
        
        if setup_repo(version_control, code_repo, repo_name, project_description):
            ci_config()
            return True
        save_to_env("None", "CODE_REPO", ".cookiecutter")
        return False
    

    # Ensure the working directory is the project root
    os.chdir(PROJECT_DIR)

    print('Running "Remote Repo Setup"')

    version_control = load_from_env("VERSION_CONTROL",".cookiecutter")
    repo_name = load_from_env("REPO_NAME",".cookiecutter")
    code_repo = load_from_env("CODE_REPO",".cookiecutter")
    project_description = load_from_env("PROJECT_DESCRIPTION",".cookiecutter")
 

    # Create Remote Repository
    flag = setup_remote_repository(version_control,code_repo,repo_name,project_description)

    print("Creating 'requirements.txt','environment.yml'")
    update_env_files()
    update_setup_dependency()
    update_code_dependency()

    # Pushing to Git
    push_msg = " Created `requirements.txt`, `environment.yml`,`dependencies.txt` and updated in README.md" 
    git_push(flag,push_msg)

def outro():
    def delete_files(file_paths:list=[]):
        """
        Deletes a list of files specified by their paths.

        Args:
            file_paths (list): A list of file paths to be deleted.

        Returns:
            dict: A dictionary with file paths as keys and their status as values.
                The status can be "Deleted", "Not Found", or an error message.
        """
        results = {}
        for file_path in file_paths:
            file_path = str(pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(file_path))
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    results[file_path] = "Deleted"
                else:
                    results[file_path] = "Not Found"
            except Exception as e:
                results[file_path] = f"Error: {e}"

        return results

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

    files_to_remove = ["network_analysis.ipynb","./setup/project_setup.py","./run_setup.sh","./run_setup.ps1","./setup/main_setup.py",activate_to_delete,deactivate_to_delete]

    # Deleting Setup scripts
    delete_files(files_to_remove)

    # Updating README
    creating_readme(programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter"))

    # Pushing to Git
    git_push(load_from_env("CODE_REPO",".cookiecutter")!= "None","README.md updated")
    
if __name__ == "__main__":

    setup_remote_backup()
    
    intro()

    version_setup()

    remote_repo_setup()

    outro()
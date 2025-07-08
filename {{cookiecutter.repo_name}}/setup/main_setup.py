import sys
import os
import pathlib
import subprocess
import platform

from utils.general_tools import *
from utils.backup_tools import *
from utils.readme_templates import *
from utils.code_templates import *
from utils.versioning_tools import *
from utils.repo_tools import *
from utils.get_dependencies import *
from utils.ci_tools import *

@ensure_correct_kernel
def intro():

    def create_folders():
        PROJECT_DIR = pathlib.Path(__file__).resolve().parent.parent

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
    project_root = pathlib.Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    print('Running "Intro"')

    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")
    version_control = load_from_env("VERSION_CONTROL",".cookiecutter")
    project_name = load_from_env("PROJECT_NAME",".cookiecutter")
    version = load_from_env("VERSION",".cookiecutter")
    authors = load_from_env("AUTHORS",".cookiecutter")
    orcids = load_from_env("ORCIDS",".cookiecutter")
    
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
               
    download_README_template(readme_file = "./DCAS template/README.md")

@ensure_correct_kernel
def version_setup():

    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    print('Running "Version Control Setup"')

    version_control = load_from_env("VERSION_CONTROL",".cookiecutter")
    repo_name = load_from_env("REPO_NAME",".cookiecutter")
    code_repo = load_from_env("CODE_REPO",".cookiecutter")
    remote_storage = load_from_env("REMOTE_STORAGE",".cookiecutter")

    # Setup Version Control
    setup_version_control(version_control,remote_storage,code_repo,repo_name)

@ensure_correct_kernel
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
    
    def install_py_package(setup_path:str="./setup"):

        # Change the current working directory to to setup folder
        os.chdir(setup_path)
    
        # Run "pip install -e ."
        result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-e', '.'],
                capture_output=True,
                text=True
            )

        if result.returncode == 0:
            print("Installation successful.")
        else:
            print(f"Error during installation: {result.stderr}")

    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent
    os.chdir(project_root)

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

    # Installing package:
    install_py_package("./setup")

    # Pushing to Git
    push_msg = " Created `requirements.txt`, `environment.yml`, and `dependencies.txt`, installed Setup package and updated in README.md" 
    git_push(flag,push_msg)

@ensure_correct_kernel
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
    
    project_root = pathlib.Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    print('Running "Outro"')
    print(project_root)

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
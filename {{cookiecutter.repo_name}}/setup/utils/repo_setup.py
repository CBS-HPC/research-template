import os
import sys
import subprocess
import pathlib

# Ensure project root is in sys.path when run directly
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from utils.repo_tools import *
from utils.virenv_tools import *
from utils.get_dependencies import get_setup_dependencies, setup_renv

def setup_remote_repository(version_control,code_repo,repo_name,description):
    """Handle repository creation and log-in based on selected platform."""

    # Change Dir to project_root
    os.chdir(str(pathlib.Path(__file__).resolve().parent.parent.parent))

    if version_control == None or not os.path.isdir(".git"):
        return False
    if code_repo and code_repo.lower() == "github":
        flag = install_gh("./bin/gh")     
    elif code_repo and code_repo.lower() == "gitlab":
        flag  = install_glab("./bin/glab")
    else:
        return False 
    if flag:    
        flag = setup_repo(version_control,code_repo,repo_name,description) 
    if not flag:
        save_to_env("None","CODE_REPO",".cookiecutter")
    return flag

def install_py_package():

    # Change the current working directory to to setup folder
    os.chdir(pathlib.Path(__file__).resolve().parent.parent)

    # Run "pip install -e ."
    result = subprocess.run(['pip', 'install', '-e', '.'], capture_output=True, text=True)

    if result.returncode == 0:
        print("Installation successful.")
    else:
        print(f"Error during installation: {result.stderr}")


@ensure_correct_kernel
def main():
    
    version_control = load_from_env("VERSION_CONTROL",".cookiecutter")
    repo_name = load_from_env("REPO_NAME",".cookiecutter")
    code_repo = load_from_env("CODE_REPO",".cookiecutter")
    project_description = load_from_env("PROJECT_DESCRIPTION",".cookiecutter")
    #python_env_manager = load_from_env("PYTHON_ENV_MANAGER",".cookiecutter")
    programming_language = load_from_env("PROGRAMMING_LANGUAGE",".cookiecutter")

    # Create Remote Repository
    flag = setup_remote_repository(version_control,code_repo,repo_name,project_description)

    requirements_file = load_from_env("REQUIREMENT_FILE",".cookiecutter")
    create_requirements_txt("requirements.txt")
    if requirements_file == "requirements.txt":
        create_conda_environment_yml(r_version = load_from_env("R_VERSION", ".cookiecutter") if programming_language.lower() == "r" else None)
    elif requirements_file == "environment.yml": 
        export_conda_env(repo_name)

    folder = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./setup"))
    file = str(pathlib.Path(__file__).resolve().parent.parent.parent / pathlib.Path("./setup/dependencies.txt"))
    
    get_setup_dependencies(folder_path = folder, file_name = file)
    
    setup_renv(programming_language,"renv project has been setup and a renv.lock file has been created")

    # Pushing to Git
    push_msg = f" `requirements.txt`, `environment.yml`, '' and '{file}' created and 'Requirements' section in README.md updated" 
    git_push(flag,push_msg)

    # Installing package:
    install_py_package()
    
if __name__ == "__main__":
    
    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    
    main()

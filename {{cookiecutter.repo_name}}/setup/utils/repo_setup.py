import os
import sys
import subprocess
import pathlib

# Ensure project root is in sys.path when run directly
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from utils.repo_tools import *
from utils.virenv_tools import *
from utils.get_dependencies import update_setup_dependency, update_src_dependency, update_env_files

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
 

    # Create Remote Repository
    flag = setup_remote_repository(version_control,code_repo,repo_name,project_description)

    print("Creating 'requirements.txt','environment.yml'")
    update_env_files()
    update_setup_dependency()
    update_src_dependency()

    # Installing package:
    install_py_package()

    # Pushing to Git
    push_msg = " Created `requirements.txt`, `environment.yml`, and `dependencies.txt` in `setup` and `src`, installed Setup package and updated in README.md" 
    git_push(flag,push_msg)

    
    
if __name__ == "__main__":
    
    # Ensure the working directory is the project root
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)
    
    main()

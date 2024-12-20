import os
import subprocess
import sys
import platform


sys.path.append('setup')
from utils import *
from code_templates import *
from readme_templates import *

def setup_virtual_environment(version_control,programming_language,environment_manager,code_repo,repo_name,install_path = "bin/miniconda3"):
    """
    Create a virtual environment for Python or R based on the specified programming language.

    Parameters:
    - repo_name: str, name of the virtual environment.
    - programming_language: str, 'python' or 'R' to specify the language for the environment.
    """    
    
    pip_packages = set_pip_packages(version_control,programming_language)

    if environment_manager.lower() == "conda":
        conda_packages = set_conda_packages(version_control,programming_language,code_repo)
        env_file = load_env_file()
        repo_name = setup_conda(install_path,repo_name,conda_packages,pip_packages,env_file)

    elif environment_manager.lower() == "venv":
        repo_name = create_venv_env(repo_name,pip_packages)    
    elif environment_manager.lower() == "virtualenv":
        repo_name = create_virtualenv_env(repo_name,pip_packages)
    
    if not repo_name or not environment_manager: 
        subprocess.run([sys.executable, '-m', 'pip', 'install'] + pip_packages, check=True)
        print(f'Packages {pip_packages} installed successfully in the current environment.')

    return repo_name

def run_bash_script(script_path, repo_name=None, environment_manager=None, setup_version_control_path=None, setup_remote_repository_path=None):
    try:
        # Make sure the script is executable
        os.chmod(script_path, 0o755)

        # Run the script with the additional paths as arguments
        subprocess.check_call(['bash', '-i', script_path, repo_name, environment_manager, setup_version_control_path, setup_remote_repository_path])  # Pass repo_name and paths to the script
        print(f"Script {script_path} executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the script: {e}")

def run_powershell_script(script_path, repo_name=None, environment_manager=None, setup_version_control_path=None, setup_remote_repository_path=None):
    try:
        # Prepare the command to execute the PowerShell script with arguments
        command = [
            "powershell", "-ExecutionPolicy", "Bypass", "-File", script_path
        ]

        # Append arguments if they are provided
        if repo_name:
            command.append(repo_name)
        if environment_manager:
            command.append(environment_manager)
        if setup_version_control_path:
            command.append(setup_version_control_path)
        if setup_remote_repository_path:
            command.append(setup_remote_repository_path)

        # Run the PowerShell script with the specified arguments
        subprocess.check_call(command)
        print(f"Script {script_path} executed successfully.")
    
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the script: {e}")

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
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                results[file_path] = "Deleted"
            else:
                results[file_path] = "Not Found"
        except Exception as e:
            results[file_path] = f"Error: {e}"

    return results

setup_version_control = "setup/version_control.py"
setup_remote_repository = "setup/remote_repository.py"
setup_bash = "setup/run_setup.sh"
setup_powershell = "setup/run_setup.ps1"
miniconda_path =  "bin/miniconda3"

programming_language = "{{cookiecutter.programming_language}}"
if "(Pre-installation required)" in programming_language:
    programming_language = programming_language.replace(" (Pre-installation required)", "")
environment_manager = "{{cookiecutter.environment_manager}}"
repo_name = "{{cookiecutter.repo_name}}"
code_repo = "{{cookiecutter.code_repository}}"
version_control = "{{cookiecutter.version_control}}"
remote_storage = "{{cookiecutter.remote_storage}}"
project_name = "{{cookiecutter.project_name}}"
project_description = "{{cookiecutter.description}}"
authors = "{{cookiecutter.author_name}}"
orcids = "{{cookiecutter.orcid}}"
version = "{{cookiecutter.version}}"
license = "{{cookiecutter.open_source_license}}"

# Create scripts and notebook
create_scripts(programming_language, "src")
create_notebooks(programming_language, "notebooks")

# Set project info to .cookiecutter
save_to_env(project_name,"PROJECT_NAME",".cookiecutter")
save_to_env(repo_name,"REPO_NAME",".cookiecutter")
save_to_env(project_description,"PROJECT_DESCRIPTION",".cookiecutter")
save_to_env(version,"VERSION",".cookiecutter")
save_to_env(authors,"AUTHORS",".cookiecutter")
save_to_env(orcids,"ORCIDS",".cookiecutter")
save_to_env(license,"LICENSE",".cookiecutter")
save_to_env(programming_language,"PROGRAMMING_LANGUAGE",".cookiecutter")
save_to_env(environment_manager,"ENVIRONMENT_MANAGER",".cookiecutter")
save_to_env(version_control,"VERSION_CONTROL",".cookiecutter")
save_to_env(remote_storage,"REMOTE_STORAGE",".cookiecutter")
save_to_env(code_repo,"CODE_REPO",".cookiecutter")

# Set to .env
save_to_env(os.getcwd(),"PROJECT_PATH")

# Set git user info
git_user_info(version_control)
git_repo_user(version_control,repo_name,code_repo)

# Create a citation file
create_citation_file(project_name,version,authors,orcids,version_control, doi=None, release_date=None)

# Create Virtual Environment
repo_name = setup_virtual_environment(version_control,programming_language,environment_manager,code_repo,repo_name,miniconda_path)

os_type = platform.system().lower()

if os_type == "windows":
    run_powershell_script(setup_powershell, repo_name, environment_manager, setup_version_control, setup_remote_repository)
elif os_type == "darwin" or os_type == "linux":
    run_bash_script(setup_bash, repo_name, environment_manager, setup_version_control, setup_remote_repository)

# Deleting Setup scripts
files_to_delete = [os.path.abspath(__file__),"setup/code_templates.py",setup_version_control,setup_remote_repository, setup_bash,setup_powershell]
delete_files(files_to_delete)
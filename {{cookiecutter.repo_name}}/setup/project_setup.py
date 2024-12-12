import os
import subprocess
import sys
import platform
import os

sys.path.append('setup/src')
from src.utils import *
from src.code_templates import *
from src.readme_templates import *

def setup_virtual_environment(version_control,programming_language,environment_manager,code_repo,repo_name,install_path = "bin/miniconda3"):
    """
    Create a virtual environment for Python or R based on the specified programming language.
    
    Parameters:
    - repo_name: str, name of the virtual environment.
    - programming_language: str, 'python' or 'R' to specify the language for the environment.
    """    
    if environment_manager is None:
        return
    
    # Ask for user confirmation
    confirm = ask_yes_no(f"Do you want to create a virtual environment named '{repo_name}' using {environment_manager}? (yes/no):")

    if not confirm:
        print("Virtual environment creation canceled.")
        return
    
    if environment_manager.lower == "conda":
        install_packages = set_packages(version_control,programming_language,code_repo)
        env_file = load_env_file()
        setup_conda(install_path,repo_name,install_packages,env_file)
    elif environment_manager.lower == "venv":
        create_venv_env(repo_name)    
    elif environment_manager.lower == "virtualenv":
        create_virtualenv_env(repo_name)

    return repo_name

def load_env_file():
    
    def get_file_path():
        """
        Prompt the user to provide the path to a .yml or .txt file and check if the file exists and is the correct format.
        
        Returns:
        - str: Validated file path if the file exists and has the correct extension.
        """

        # Prompt the user for the file path
        file_path = input("Please enter the path to a .yml or .txt file: ").strip()
            
        # Check if the file exists
        if not os.path.isfile(file_path):
            print("The file does not exist. Please try again.")
            return None
            
        # Check the file extension
        _, file_extension = os.path.splitext(file_path)
        if file_extension.lower() not in {'.yml', '.txt'}:
            print("Invalid file format. The file must be a .yml or .txt file.")
            return None
        
        # If both checks pass, return the valid file path
        return file_path

    confirm = ask_yes_no(f"Do you want to create a virtual environment from a pre-existing 'environment.yaml' or 'requirements.txt' file? (yes/no):")

    if confirm:
        env_file = get_file_path()
        if env_file is None:
            print("no 'environment.yaml' or 'requirements.txt' file was loaded")
        return env_file
    else:
        return None

def set_packages(version_control,programming_language,code_repo):
    os_type = platform.system().lower()    
    
    install_packages = ['python','python-dotenv']

    if programming_language == 'R':
        install_packages.extend(['r-base'])

    if version_control in ['Git','DVC','Datalad'] and not is_installed('git', 'Git'):
        install_packages.extend(['git'])   
    
    if version_control == 'Datalad':
        if not is_installed('rclone', 'Rclone'):    
            install_packages.extend(['rclone'])

        if os_type in ["darwin","linux"] and not is_installed('git-annex', 'git-annex'):
            install_packages.extend(['git-annex'])

    if code_repo == 'GitHub' and not is_installed('gh', 'GitHub Cli'):
        install_packages.extend(['gh']) 

    return  install_packages

def create_venv_env(env_name):
    """Create a Python virtual environment using venv."""
    subprocess.run([sys.executable, '-m', 'venv', env_name], check=True)
    print(f'Venv environment "{repo_name}" for Python created successfully.')

def create_virtualenv_env(env_name):
    """Create a Python virtual environment using virtualenv."""
    subprocess.run(['virtualenv', env_name], check=True)
    print(f'Virtualenv environment "{repo_name}" for Python created successfully.')

def run_bash_script(script_path, repo_name=None, setup_version_control_path=None, setup_remote_repository_path=None):
    try:
        # Make sure the script is executable
        os.chmod(script_path, 0o755)

        # Run the script with the additional paths as arguments
        subprocess.check_call(['bash', '-i', script_path, repo_name, setup_version_control_path, setup_remote_repository_path])  # Pass repo_name and paths to the script
        print(f"Script {script_path} executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the script: {e}")

def run_powershell_script(script_path, repo_name=None, setup_version_control_path=None, setup_remote_repository_path=None):
    try:
        # Prepare the command to execute the PowerShell script with arguments
        command = [
            "powershell", "-ExecutionPolicy", "Bypass", "-File", script_path
        ]

        # Append arguments if they are provided
        if repo_name:
            command.append(repo_name)
        if setup_version_control_path:
            command.append(setup_version_control_path)
        if setup_remote_repository_path:
            command.append(setup_remote_repository_path)

        # Run the PowerShell script with the specified arguments
        subprocess.check_call(command)
        print(f"Script {script_path} executed successfully.")
    
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the script: {e}")

setup_version_control = "setup/src/version_control.py"
setup_remote_repository = "setup/src/remote_repository.py"
setup_bash = "setup/src/setup_conda.sh"
setup_powershell = "setup/src/setup_conda.ps1"
miniconda_path =  "bin/miniconda3"


programming_language = "{{cookiecutter.programming_language}}"
programming_language.replace(" (Pre-installation required)", "")
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

print(programming_language)
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
git_user_info()
git_repo_user(repo_name,code_repo)

# Create a citation file
create_citation_file(project_name,version,authors,orcids,version_control, doi=None, release_date=None)

# Create Virtual Environment
repo_name = setup_virtual_environment(version_control,programming_language,environment_manager,code_repo,repo_name,miniconda_path)

os_type = platform.system().lower()

if os_type == "windows":
    run_powershell_script(setup_powershell, repo_name, setup_version_control, setup_remote_repository)
elif os_type == "darwin" or os_type == "linux":
    run_bash_script(setup_bash, repo_name, setup_version_control, setup_remote_repository)
import os
import subprocess
import sys
import platform
import os
from src.utils import *
from src.code_templates import *
from src.readme_templates import *

def setup_virtual_environment(version_control,virtual_environment,code_repo,repo_name,install_path = "bin/miniconda3"):
    """
    Create a virtual environment for Python or R based on the specified programming language.
    
    Parameters:
    - repo_name: str, name of the virtual environment.
    - programming_language: str, 'python' or 'R' to specify the language for the environment.
    """

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
   
    def create_venv_env(env_name):
        """Create a Python virtual environment using venv."""
        subprocess.run([sys.executable, '-m', 'venv', env_name], check=True)
        print(f'Venv environment "{repo_name}" for Python created successfully.')

    def create_virtualenv_env(env_name):
        """Create a Python virtual environment using virtualenv."""
        subprocess.run(['virtualenv', env_name], check=True)
        print(f'Virtualenv environment "{repo_name}" for Python created successfully.')

    os_type = platform.system().lower()    
    install_packages = ['python','python-dotenv']

    env_file  = None

    if virtual_environment not in ['Python','R','environment.yaml','requirements.txt']:
        return
    
    # Ask for user confirmation
   #confirm = input(f"Do you want to create a virtual environment named '{repo_name}' for/from {virtual_environment}? (yes/no): ").strip().lower()
    
    confirm = ask_yes_no(f"Do you want to create a virtual environment named '{repo_name}' for/from {virtual_environment}? (yes/no):")

    if not confirm:
        print("Virtual environment creation canceled.")
        return
    
    if virtual_environment in ['environment.yaml','requirements.txt']:
        env_file = get_file_path()
        if env_file is None:
            return None

    if virtual_environment in ['Python','R','environment.yaml','requirements.txt']:
        
        if virtual_environment == 'R':
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
            
        check = setup_conda(install_path,virtual_environment,repo_name,install_packages,env_file)

        if check is False and virtual_environment == 'Python':
            if subprocess.call(['which', 'virtualenv']) == 0:
                create_virtualenv_env(repo_name)
            else:
                create_venv_env(repo_name)
    
        return repo_name

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

virtual_environment = "{{ cookiecutter.virtual_environment}}"
repo_name = "{{cookiecutter.repo_name}}"
code_repo = "{{cookiecutter.code_repository}}"
data_repo = "{{cookiecutter.data_repository}}"
version_control = "{{cookiecutter.version_control}}"
remote_storage = "{{cookiecutter.remote_storage}}"
project_name = "{{cookiecutter.project_name}}"
project_description = "{{cookiecutter.description}}"
authors = "{{cookiecutter.author_name}}"
orcids = "{{cookiecutter.orcid}}"
version = "{{cookiecutter.version}}"
license = "{{cookiecutter.open_source_license}}"

# Create scripts and notebook
create_scripts(virtual_environment, "src")
create_notebooks(virtual_environment, "notebooks")

# Set project info to .cookiecutter
save_to_env(project_name,"PROJECT_NAME",".cookiecutter")
save_to_env(repo_name,"REPO_NAME",".cookiecutter")
save_to_env(project_description,"PROJECT_DESCRIPTION",".cookiecutter")
save_to_env(version,"VERSION",".cookiecutter")
save_to_env(authors,"AUTHORS",".cookiecutter")
save_to_env(orcids,"ORCIDS",".cookiecutter")
save_to_env(license,"LICENSE",".cookiecutter")
save_to_env(virtual_environment,"VIRTUAL_ENV",".cookiecutter")
save_to_env(version_control,"VERSION_CONTROL",".cookiecutter")
save_to_env(remote_storage,"REMOTE_STORAGE",".cookiecutter")
save_to_env(code_repo,"CODE_REPO",".cookiecutter")
save_to_env(data_repo,"DATA_REPO",".cookiecutter")

# Set to .env
save_to_env(os.getcwd(),"PROJECT_PATH")

# Set git user info
git_user_info()
git_repo_user(repo_name,code_repo)

# Create a citation file
create_citation_file(project_name,version,authors,orcids,version_control, doi=None, release_date=None)

# Create Virtual Environment
repo_name = setup_virtual_environment(version_control,virtual_environment,code_repo,repo_name,miniconda_path)

os_type = platform.system().lower()

if os_type == "windows":
    run_powershell_script(setup_powershell, repo_name, setup_version_control, setup_remote_repository)
elif os_type == "darwin" or os_type == "linux":
    run_bash_script(setup_bash, repo_name, setup_version_control, setup_remote_repository)
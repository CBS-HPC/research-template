import os
import stat
import subprocess
import sys
import platform
import re

from utils import *
from code_templates import *
from readme_templates import *

pip_installer(required_libraries = ['questionary'])
import questionary

ext_map = {
    "r": "Rscript",
    "python": "python",
    "matlab": "matlab -batch",
    "stata": "stata -b do",
    "sas": "sas"
}

file_ext_map = {
    "r": "R",
    "python": "py",
    "matlab": "m",
    "stata": "do",
    "sas": "sas"
}


def run_bash(script_path, env_path=None, python_env_manager=None, setup_version_control_path=None, setup_remote_repository_path=None):
    if not env_path:
        env_path = "Base Installation" 
    if not python_env_manager:
        python_env_manager = "Base Installation"    
    try:
        print(os.getcwd())
        # Make sure the script is executable
        os.chmod(script_path, 0o755)

        # Run the script with the additional paths as arguments
        subprocess.check_call(['bash', '-i', script_path, env_path, python_env_manager, setup_version_control_path, setup_remote_repository_path])  # Pass repo_name and paths to the script
        print(f"Script {script_path} executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the script: {e}")

def run_powershell(script_path, env_path=None, python_env_manager=None, setup_version_control_path=None, setup_remote_repository_path=None):
    if not env_path:
        env_path = "Base Installation" 
    if not python_env_manager:
        python_env_manager = "Base Installation"    
    
    try:
        subprocess.check_call( ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path,env_path,python_env_manager,setup_version_control_path,setup_remote_repository_path])
        print(f"Script {script_path} executed successfully.")
    
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the script: {e}")

def setup_virtual_environment(version_control, programming_language, python_env_manager, r_env_manager, code_repo,repo_name, conda_r_version, conda_python_version, install_path = "bin/miniconda3"):
    """
    Create a virtual environment for Python or R based on the specified programming language.

    Parameters:
    - repo_name: str, name of the virtual environment.
    - programming_language: str, 'python' or 'R' to specify the language for the environment.
    """    
    def create_command(activate_cmd :str=None ,step:int = 0):
        
        if step in [1,2]:
            install_cmd = load_from_env("INSTALL_CMD",".cookiecutter")
        if step == 1:
            activate_cmd = f"### Conda Installation\n"
            if programming_language.lower() != "python":
                activate_cmd += f"The conda environment is used for project setup functionalities in the './setup' folder\n"
            else:
                activate_cmd += f"The conda environment is used for project code ('./src' folder) and setup functionalities ('./setup' folder)\n"

            activate_cmd += "```\n"
            activate_cmd += f"{install_cmd}\n"
            activate_cmd = f"conda activate {env_name}\n"
            activate_cmd += "```"
        
        elif step == 2: 
            activate_cmd = f"### {python_version}\n"
            if programming_language.lower() != "python":
                activate_cmd += f"The venv environment is used for project setup functionalities in the './setup' folder\n"
            else:
                activate_cmd += f"The venv environment is used for project code ('./src' folder) and setup functionalities ('./setup' folder)\n"
          
            activate_cmd += "```\n"
            activate_cmd += f"python -m venv {env_name}\n"
            activate_cmd += f"./{env_name}/Scripts/activate\n"
            activate_cmd += "```\n"

            activate_cmd += "Install using requirements.txt for full environment\n"
            activate_cmd += "```\n"
            activate_cmd += f"{install_cmd}\n"
            activate_cmd += "```\n"

        elif step == 3:
            activate_cmd = f"### {python_version}\n"
            activate_cmd += f"The python environment is used for project setup functionalities in the './setup' folder\n"
            activate_cmd += "```\n"
            activate_cmd += f"python ./setup/install_dependencies.py\n"
            activate_cmd += "```\n"
            activate_cmd = activate_cmd.replace("\\", "/")

        elif step == 4:
            if activate_cmd and r_env_manager.lower() != "conda":
                if programming_language.lower() not in ["python","none"]:
                    software_version = get_version(programming_language)
                    activate_cmd += f"### {software_version}\n"  
                    activate_cmd += f"The environment is used for project code in the './src' folder\n"
                    activate_cmd += "```\n"
                    activate_cmd += f"{ext_map[programming_language.lower()]} ./src/install_dependencies.{file_ext_map[programming_language.lower()]}\n"
                    activate_cmd += "```\n"
                activate_cmd = activate_cmd.replace("\\", "/")

        return activate_cmd 
    
    pip_packages = set_pip_packages(version_control,programming_language)    
    activate_cmd = None
    env_name = None
  
    if python_env_manager.lower() == "conda" or r_env_manager.lower() == "conda":
    
        install_packages = []
        
        if python_env_manager.lower() == "conda":
            if conda_python_version:
                install_packages.extend([f'python={conda_python_version}'])
            else:
                install_packages.extend(['python'])

        if r_env_manager.lower() == "conda":
            if conda_r_version:
                install_packages.extend([f'r-base={conda_r_version}'])
            else:
                install_packages.extend(['r-base'])

        conda_packages = set_conda_packages(version_control,install_packages,code_repo)

        if python_env_manager and python_env_manager.lower() == "conda":
            env_name = setup_conda(install_path=install_path,repo_name=repo_name,conda_packages=conda_packages, pip_packages=pip_packages, env_file=None, conda_r_version=conda_r_version, conda_python_version=conda_python_version)
        else:
            env_name = setup_conda(install_path=install_path, repo_name=repo_name,conda_packages=conda_packages, pip_packages=None,env_file=None, conda_r_version=conda_r_version, conda_python_version=conda_python_version)
        
        if env_name:
            activate_cmd = create_command(activate_cmd=activate_cmd ,step = 1)

    elif python_env_manager.lower() in ["venv","virtualenv"]:
        if python_env_manager.lower() == "venv":
            env_name = create_venv_env(repo_name,pip_packages)
        elif python_env_manager.lower() == "virtualenv":
            env_name = create_virtualenv_env(repo_name,pip_packages)  
        if env_name:
            python_version = subprocess.check_output([sys.executable, '--version']).decode().strip()
            activate_cmd = create_command(activate_cmd=activate_cmd ,step = 2)
    else:
        python_version = subprocess.check_output([sys.executable, '--version']).decode().strip()
        activate_cmd = create_command(activate_cmd=activate_cmd ,step = 3)
    
    if env_name:
        env_name = env_name.replace("\\", "/")
    
    activate_cmd = create_command(activate_cmd=activate_cmd ,step = 4)

    if not env_name or not python_env_manager: 
        subprocess.run([sys.executable, '-m', 'pip', 'install'] + pip_packages, check=True)
        print(f'Packages {pip_packages} installed successfully in the current environment.')

    return env_name, activate_cmd

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

def prompt_user(question, options):
    """
    Prompts the user with a question and a list of options to select from.

    Args:
        question (str): The question to display to the user.
        options (list): List of options to display.

    Returns:
        str: The user's selected option.
    """
    print(question)
    for i, option in enumerate(options, start=1):
        print(f"{i}. {option}")

    while True:
        try:
            choice = int(input("Choose from above (enter number): "))
            if 1 <= choice <= len(options):
                selected_option = options[choice - 1]
                return selected_option
            else:
                print(f"Invalid choice. Please select a number between 1 and {len(options)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def correct_format(programming_language, authors, orcids):

    if "(Base installation required)" in programming_language:
            programming_language = programming_language.replace(" (Base installation required)", "")

    if "Your Name(s) (multiple authors can be added by using a ';' or ',' delimiter)" in authors:
            authors = authors.replace("Your Name(s) (multiple authors can be added by using a ';' or ',' delimiter)", "Not Provided")
    if "Your Name(s) (multiple authors can be added by using a ';' or ',' delimiter)" in orcids:
            orcids = orcids.replace("Your Name(s) (multiple authors can be added by using a ';' or ',' delimiter)", "Not Provided")

    return programming_language, authors, orcids

def set_options(programming_language,version_control):
    
    def is_valid_version(version: str, software: str) -> bool:
        """
        Validate if the inputted version follows the general versioning structure for R or Python.

        Args:
            version (str): The version string to validate.
            software (str): The software name ('r' or 'python').

        Returns:
            bool: True if the version is valid, False otherwise.
        """
        version_pattern = {
            "r": r"^4(\.\d+){0,2}$",  # Matches '4', '4.3', or '4.4.3' for R
            "python": r"^3(\.\d+){0,2}$"  # Matches '3', '3.9', '3.12', or '3.9.3' for Python
        }

        if software.lower() not in version_pattern:
            raise ValueError("Software must be 'r' or 'python'")

        return version == "" or bool(re.fullmatch(version_pattern[software.lower()], version))

    def select_version():
        r_version = None
        if r_env_manager.lower() == 'conda':
            r_version = input("Would you like to specify an R version (e.g., '4.4.3', '4.3', or '4') to be installed via conda? Leave empty for default: ").strip()
            if r_version and not is_valid_version(r_version, 'r'):
                print("Invalid R version format. Will be left empty.")
                r_version = None
        python_version = None
        if python_env_manager.lower() == 'conda':
            python_version = input("Would you like to specify a Python version (e.g., '3.9.3', '3.12', or '3') to be installed via conda? Leave empty for default: ").strip()
            if python_version and not is_valid_version(python_version, 'python'):
                print("Invalid Python version format. Will be left empty.")
                python_version = None
        
        return r_version, python_version


    python_version = f"({subprocess.check_output([sys.executable, '--version']).decode().strip()})"
    environment_opts = ["Conda",f"Venv {python_version}",f"Base Installation {python_version}"]
    python_env_manager = None
    if programming_language.lower() == 'r':
        question = "Do you want to create a new R environment using Conda or use Base Installation:"
        r_env_manager = prompt_user(question, ["Conda","Base Installation"])
        question = "Python is used to setup functionalities. Do you also want to create a new python environment using (recommended):"
        
        if r_env_manager.lower() =='conda':
            environment_opts = ["Conda",f"Base Installation {python_version}"]
            python_env_manager = "Conda"
            print("A new python environment will be created to facilitate the setup functionalities")

    else:
        r_env_manager = "Base Installation"

        if programming_language.lower() == 'python':
            question = "Do you want to create a new python environment using:"
        else:
            question = "Do you want to create a new python environment (used for project setup functions) using:"
    
    if not python_env_manager: 
        python_env_manager = prompt_user(question, environment_opts)

     # Set requirements file
    requirements_file = "requirements.txt"
    install_cmd = f"pip install -r {requirements_file}"

    if python_env_manager.lower() == "conda" or r_env_manager.lower() == "conda":
        
        requirements_file = "environment.yml"
        install_cmd =  f"conda env create -f {requirements_file}"
  
    save_to_env(install_cmd,"INSTALL_CMD",".cookiecutter")
    save_to_env(requirements_file,"REQUIREMENT_FILE",".cookiecutter")     


    if version_control in ["Git","Datalad","DVC"]:
        code_repo = prompt_user("Do you want to setup a code reposity at:", ["GitHub","GitLab","Codeberg","None"])
    else:
        code_repo = "None"

    if version_control in ["Datalad","DVC"]:
        remote_storage = prompt_user(f"Do you want to setup remote storage for your {version_control} repo:", ["Dropbox","Deic Storage","Local Path","None"])
    else:
        remote_storage = "None"

    if programming_language.lower() in ['stata','matlab','sas'] or (programming_language.lower() == 'r' and r_env_manager.lower() !='conda'):
        selected_app = set_programming_language(programming_language)
        if not selected_app: 
            print(f"{programming_language} path has not been set")

    python_env_manager = python_env_manager.replace(python_version,"") 

    conda_r_version, conda_python_version = select_version()

    return programming_language, python_env_manager,r_env_manager,code_repo, remote_storage, install_cmd, conda_r_version, conda_python_version 

def multiple_backups(remote_backup):
    if remote_backup == "Multiple":
        options = ["Deic Storage", "Dropbox", "Onedrive", "Local"]
        remote_backup = questionary.checkbox(
            "Select remote backups:",
            choices=options
        ).ask()
        if remote_backup:
            remote_backup = ", ".join(remote_backup)
        else:
            remote_backup = "None"
    return remote_backup

setup_version_control = "./setup/version_control.py"
setup_remote_repository = "./setup/remote_repository.py"
setup_bash = "./setup/run_setup.sh"
setup_powershell = "./setup/run_setup.ps1"
miniconda_path =  "bin/miniconda3"

os.chmod("./activate.sh", 0o755)
os.chmod("./deactivate.sh", 0o755)


project_name = "{{cookiecutter.project_name}}"
project_description = "{{cookiecutter.description}}"
authors = "{{cookiecutter.author_name}}"
orcids = "{{cookiecutter.orcid}}"
email = "{{cookiecutter.email}}"
version = "{{cookiecutter.version}}"
license = "{{cookiecutter.open_source_license}}"
repo_name = "{{cookiecutter.repo_name}}"
version_control = "{{cookiecutter.version_control}}"
programming_language = "{{cookiecutter.programming_language}}"
remote_backup = "{{cookiecutter.remote_backup}}"

remote_backup = multiple_backups(remote_backup)
programming_language, authors, orcids = correct_format(programming_language, authors, orcids)
programming_language, python_env_manager,r_env_manager,code_repo, remote_storage, install_cmd, conda_r_version, conda_python_version  = set_options(programming_language,version_control)

# Create scripts and notebook
if programming_language.lower() != "none":
    create_scripts(programming_language, "src")
    create_notebooks(programming_language, "notebooks")

# Set project info to .cookiecutter
save_to_env(project_name,"PROJECT_NAME",".cookiecutter")
save_to_env(repo_name,"REPO_NAME",".cookiecutter")
save_to_env(project_description,"PROJECT_DESCRIPTION",".cookiecutter")
save_to_env(version,"VERSION",".cookiecutter")
save_to_env(authors,"AUTHORS",".cookiecutter")
save_to_env(orcids,"ORCIDS",".cookiecutter")
save_to_env(email,"EMAIL",".cookiecutter")
save_to_env(license,"LICENSE",".cookiecutter")
save_to_env(programming_language,"PROGRAMMING_LANGUAGE",".cookiecutter")
save_to_env(python_env_manager,"PYTHON_ENV_MANAGER",".cookiecutter")
save_to_env(version_control,"VERSION_CONTROL",".cookiecutter")
save_to_env(remote_backup,"REMOTE_BACKUP",".cookiecutter")
save_to_env(remote_storage,"REMOTE_STORAGE",".cookiecutter")
save_to_env(code_repo,"CODE_REPO",".cookiecutter")

# Set to .env
save_to_env(os.getcwd(),"PROJECT_PATH")

# Set git user info
git_user_info(version_control)

# Set git repo info
repo_user,_,_ = git_repo_user(version_control,repo_name,code_repo)

# Setup RClone backup remote
setup_remote_backup(remote_backup,repo_name)

# Create a citation file
create_citation_file(project_name,version,authors,orcids,version_control,doi=None, release_date=None)

# Create Virtual Environment
env_path, activate_cmd = setup_virtual_environment(version_control,programming_language,python_env_manager,r_env_manager,code_repo,repo_name,conda_r_version, conda_python_version,miniconda_path)

# Creating README
creating_readme(repo_name= repo_name, 
                repo_user = repo_name, 
                project_name = project_name,
                project_description = project_description,
                code_repo = code_repo,
                programming_language = programming_language,
                authors = authors,
                orcids = orcids,
                emails = email,
                activate_cmd = activate_cmd)

download_README_template(local_file = "./DCAS template/README.md")

os_type = platform.system().lower()
if os_type == "windows":
    run_powershell(setup_powershell, env_path, python_env_manager, setup_version_control, setup_remote_repository)
    activate_to_delete = "activate.sh"
    deactivate_to_delete = "deactivate.sh"
elif os_type == "darwin" or os_type == "linux":
    run_bash(setup_bash, env_path, python_env_manager, setup_version_control, setup_remote_repository)
    activate_to_delete = "activate.ps1"
    deactivate_to_delete = "aeactivate.ps1"

# Deleting Setup scripts
delete_files([os.path.abspath(__file__),"./setup/code_templates.py",setup_version_control,setup_remote_repository, setup_bash,setup_powershell,activate_to_delete,deactivate_to_delete])

# Updating README
creating_readme()

# Pushing to Git
git_push(load_from_env("CODE_REPO",".cookiecutter")!= "None","README.md updated")
import os
import subprocess
import sys
import platform
import re
import pathlib

#from utils.general_tools import *
from utils.general_tools import save_to_env, git_user_info, repo_user_info, remote_user_info, set_programming_language

def run_bash(script_path, env_path=None, python_env_manager=None,main_setup=None):
    if not env_path:
        env_path = "Base Installation" 
    if not python_env_manager:
        python_env_manager = "Base Installation"    
    try:
        script_path = str(pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(script_path))
        env_path = str(pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(env_path))
        main_setup = str(pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(main_setup))
        
        # Make sure the script is executable
        os.chmod(script_path, 0o755)

        # Run the script with the additional paths as arguments
        subprocess.check_call(['bash', '-i', script_path, env_path, python_env_manager.lower(),main_setup])  # Pass repo_name and paths to the script
        print(f"Script {script_path} executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the script: {e}")

def run_powershell(script_path, env_path=None, python_env_manager=None, main_setup=None):
    if not env_path:
        env_path = "Base Installation" 
    if not python_env_manager:
        python_env_manager = "Base Installation"    
    
    try:
        script_path = str(pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(script_path))
        env_path = str(pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(env_path))
        main_setup = str(pathlib.Path(__file__).resolve().parent.parent / pathlib.Path(main_setup))
                                                                                       
        subprocess.check_call( ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path,env_path,python_env_manager,main_setup])
        print(f"Script {script_path} executed successfully.")
    
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the script: {e}")

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
    environment_opts = ["Conda",f"Venv {python_version}"]
    python_env_manager = None
    if programming_language.lower() == 'r':
        question = "Do you want to create a new R environment using Conda or use Base Installation:"
        r_env_manager = prompt_user(question, ["Conda","Base Installation"])
        question = "Python is used to setup functionalities. Do you also want to create a new python environment using (recommended):"
        
        if r_env_manager.lower() =='conda':
            environment_opts = ["Conda",f"Venv {python_version}"]
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

    if python_env_manager.lower() == "conda" or r_env_manager.lower() == "conda":
        requirements_file = "environment.yml"
       
    save_to_env(requirements_file,"REQUIREMENT_FILE",".cookiecutter")     

    if version_control in ["Git","Datalad","DVC"]:
        code_repo = prompt_user("Do you want to setup a code reposity at:", ["GitHub","GitLab","Codeberg","None"])
    else:
        code_repo = "None"

    if version_control in ["Datalad","DVC"]:
        remote_storage = prompt_user(f"Do you want to setup remote storage for your {version_control} repo:", ["Deic-Storage","Dropbox","Local Path","None"])
    else:
        remote_storage = "None"

    if programming_language.lower() in ['stata','matlab','sas'] or (programming_language.lower() == 'r' and r_env_manager.lower() !='conda'):
        selected_app = set_programming_language(programming_language)
        if not selected_app: 
            print(f"{programming_language} path has not been set")

    python_env_manager = python_env_manager.replace(python_version,"").strip()

    conda_r_version, conda_python_version = select_version()

    return programming_language, python_env_manager,r_env_manager,code_repo, remote_storage, conda_r_version, conda_python_version 

main_setup = "./setup/main_setup.py"
setup_bash = "./run_setup.sh"
setup_powershell = "./run_setup.ps1"
miniconda_path =  "./bin/miniconda3"

project_name = "{{cookiecutter.project_name}}"
project_description = "Insert project description here"
authors = "{{cookiecutter.author_name}}"
orcids = "{{cookiecutter.orcid}}"
email = "{{cookiecutter.email}}"
version = "{{cookiecutter.version}}"
code_license = "{{cookiecutter.code_license}}"
doc_license = "{{cookiecutter.documentation_license}}"
data_license = "{{cookiecutter.data_license}}"
repo_name = "{{cookiecutter.repo_name}}"
version_control = "{{cookiecutter.version_control}}"
programming_language = "{{cookiecutter.programming_language}}"
remote_backup = "{{cookiecutter.remote_backup}}"

programming_language, authors, orcids = correct_format(programming_language, authors, orcids)
programming_language, python_env_manager, r_env_manager, code_repo, remote_storage, conda_r_version, conda_python_version  = set_options(programming_language,version_control)

# Set project info to .cookiecutter
save_to_env(project_name,"PROJECT_NAME",".cookiecutter")
save_to_env(repo_name,"REPO_NAME",".cookiecutter")
save_to_env(project_description,"PROJECT_DESCRIPTION",".cookiecutter")
save_to_env(version,"VERSION",".cookiecutter")
save_to_env(authors,"AUTHORS",".cookiecutter")
save_to_env(orcids,"ORCIDS",".cookiecutter")
save_to_env(email,"EMAIL",".cookiecutter")
save_to_env(code_license,"CODE_LICENSE",".cookiecutter")
save_to_env(doc_license,"DOC_LICENSE",".cookiecutter")
save_to_env(data_license,"DATA_LICENSE",".cookiecutter")
save_to_env(programming_language,"PROGRAMMING_LANGUAGE",".cookiecutter")
save_to_env(python_env_manager,"PYTHON_ENV_MANAGER",".cookiecutter")
save_to_env(version_control,"VERSION_CONTROL",".cookiecutter")
save_to_env(remote_backup,"REMOTE_BACKUP",".cookiecutter")
save_to_env(remote_storage,"REMOTE_STORAGE",".cookiecutter")
save_to_env(code_repo,"CODE_REPO",".cookiecutter")

# Set git user info
git_user_info(version_control)

# Set git repo info
repo_user,_,_,_= repo_user_info(version_control,repo_name,code_repo)

# RClone remote login info
remote_user_info(remote_backup)

# Create Virtual Environment
from utils.virenv_tools import *
env_path = setup_virtual_environment(version_control,python_env_manager,r_env_manager,repo_name,conda_r_version, conda_python_version,miniconda_path)

if platform.system().lower() == "windows":
    run_powershell(setup_powershell, env_path, python_env_manager, main_setup)
elif platform.system().lower()== "darwin" or platform.system().lower() == "linux":
    os.chmod(str(pathlib.Path(__file__).resolve().parent.parent /  pathlib.Path("./activate.sh")), 0o755)
    os.chmod(str(pathlib.Path(__file__).resolve().parent.parent /  pathlib.Path("./deactivate.sh")), 0o755)
    run_bash(setup_bash, env_path, python_env_manager, main_setup)
    
